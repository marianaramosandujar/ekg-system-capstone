import os
import csv
from datetime import datetime
import numpy as np
import pyqtgraph as pg
import queue

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices

from ekg_system.microcontroller import MSP430Interface


class LivePGView(QWidget):
    """
    Live View tab (binary stream):

      Packets:
        sample_id (uint32), ch1 (s24), ch2 (s24)

      Plots:
        Plot 1: x = sample_id, y = ch1
        Plot 2: x = sample_id, y = ch2

      CSV auto-save:
        Writes rows: sample_id, ch1, ch2
    """

    def __init__(self, parent=None, fs=1000, window_sec=10):
        super().__init__(parent)

        self.fs = fs
        self.window_sec = window_sec
        self.n = int(fs * window_sec)

        # Ring buffers (x-axis is sample_id)
        self.sid_buf = np.full(self.n, np.nan, dtype=float)
        self.ch1_buf = np.full(self.n, np.nan, dtype=float)
        self.ch2_buf = np.full(self.n, np.nan, dtype=float)
        self._write_idx = 0
        self._filled = False

        # Thread-safe queue (serial thread → GUI thread)
        self._q = queue.SimpleQueue()

        # Hardware interface (binary mode)
        self.mcu = MSP430Interface(mode="binary")
        self.device_connected = False
        self.collecting = False
        self.want_collecting = False

        # Follow mode (prevents zoom from "snapping back")
        self.auto_follow = True

        # CSV logging
        self.csv_path = None
        self._csv_f = None
        self._csv_w = None

        # Layout
        layout = QVBoxLayout(self)

        self.status = QLabel("Waiting for device…")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # -------- Plot 1 (CH1) --------
        self.plot1 = pg.PlotWidget()
        self.plot1.setBackground("w")
        self.plot1.showGrid(x=True, y=True)
        self.plot1.setLabel("bottom", "Sample ID")
        self.plot1.setLabel("left", "CH1")
        self.curve1 = self.plot1.plot([], [], pen=pg.mkPen("r", width=2))
        layout.addWidget(self.plot1)

        # -------- Plot 2 (CH2) --------
        self.plot2 = pg.PlotWidget()
        self.plot2.setBackground("w")
        self.plot2.showGrid(x=True, y=True)
        self.plot2.setLabel("bottom", "Sample ID")
        self.plot2.setLabel("left", "CH2")
        self.curve2 = self.plot2.plot([], [], pen=pg.mkPen("r", width=2))
        layout.addWidget(self.plot2)

        # Detect user zoom/pan and disable follow automatically
        self.plot1.getViewBox().sigXRangeChanged.connect(self._user_moved_view)
        self.plot1.getViewBox().sigYRangeChanged.connect(self._user_moved_view)
        self.plot2.getViewBox().sigXRangeChanged.connect(self._user_moved_view)
        self.plot2.getViewBox().sigYRangeChanged.connect(self._user_moved_view)

        # Controls row
        controls = QHBoxLayout()

        self.button = QPushButton("Start Collecting")
        self.button.clicked.connect(self.toggle_collection)
        controls.addWidget(self.button)

        self.follow_btn = QPushButton("Follow (Auto)")
        self.follow_btn.setCheckable(True)
        self.follow_btn.setChecked(True)
        self.follow_btn.toggled.connect(self.set_follow_mode)
        controls.addWidget(self.follow_btn)

        self.open_btn = QPushButton("Open File")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_csv_file)
        controls.addWidget(self.open_btn)

        layout.addLayout(controls)

        # Timers
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(30)

        self.detect_timer = QTimer(self)
        self.detect_timer.timeout.connect(self.check_device)
        self.detect_timer.start(1000)

        # If port manually set via EKG_PORT env variable
        if self.mcu.port:
            self.device_connected = True
            self.status.setText(f"MSP430 set to {self.mcu.port}")

    # --------------------------------------------------
    # Device detection
    # --------------------------------------------------
    def check_device(self):
        if not self.device_connected:
            port = self.mcu.detect_port()
            if port:
                self.device_connected = True
                self.status.setText(f"MSP430 detected ({port})")
                if self.want_collecting and not self.collecting:
                    self.start_hardware()

    # --------------------------------------------------
    # Follow mode / zoom behavior
    # --------------------------------------------------
    def set_follow_mode(self, checked: bool):
        self.auto_follow = checked
        self.follow_btn.setText("Follow (Auto)" if checked else "Follow (Off)")

    def _user_moved_view(self, *args, **kwargs):
        # If user zooms/pans while follow is on, turn follow off once.
        if self.auto_follow:
            self.auto_follow = False
            self.follow_btn.setChecked(False)

    def reset_view(self):
        """Called by parent Reset Zoom if you want."""
        self.auto_follow = True
        self.follow_btn.setChecked(True)
        self.plot1.enableAutoRange()
        self.plot2.enableAutoRange()

    # --------------------------------------------------
    # Start / Stop button
    # --------------------------------------------------
    def toggle_collection(self):
        self.want_collecting = not self.want_collecting

        if self.want_collecting:
            self.button.setText("Stop Collecting")
            self.status.setText("Waiting for device…")
            if self.device_connected:
                self.start_hardware()
        else:
            self.button.setText("Start Collecting")
            self.stop_hardware()

    # --------------------------------------------------
    # CSV helpers
    # --------------------------------------------------
    def _start_csv(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.abspath(f"ekg_capture_{ts}.csv")
        self._csv_f = open(self.csv_path, "w", newline="")
        self._csv_w = csv.writer(self._csv_f)
        self._csv_w.writerow(["sample_id", "ch1", "ch2"])
        self._csv_f.flush()
        self.open_btn.setEnabled(True)

    def _stop_csv(self):
        if self._csv_f is not None:
            try:
                self._csv_f.flush()
                self._csv_f.close()
            except Exception:
                pass
        self._csv_f = None
        self._csv_w = None

    def open_csv_file(self):
        if not self.csv_path:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.csv_path))

    # --------------------------------------------------
    # Hardware control
    # --------------------------------------------------
    def start_hardware(self):
        if self.collecting:
            return
        try:
            self._reset_buffers()

            # Start CSV logging
            self._start_csv()

            # callback receives (sid, ch1, ch2, t_wall)
            self.mcu.start(self.on_sample)

            self.collecting = True
            self.status.setText(f"Collecting… saving to {os.path.basename(self.csv_path)}")

            # default: follow on
            self.auto_follow = True
            self.follow_btn.setChecked(True)

        except Exception as e:
            self.status.setText(f"Serial start failed: {e}")
            self.collecting = False
            self._stop_csv()

    def stop_hardware(self):
        if self.collecting:
            self.mcu.stop()
        self.collecting = False

        # Close CSV
        self._stop_csv()

        if self.csv_path:
            self.status.setText(f"Stopped. Saved: {os.path.basename(self.csv_path)}")
        else:
            self.status.setText("Collection stopped")

    def _reset_buffers(self):
        self.sid_buf[:] = np.nan
        self.ch1_buf[:] = np.nan
        self.ch2_buf[:] = np.nan
        self._write_idx = 0
        self._filled = False

        # Clear queue quickly
        try:
            while True:
                self._q.get_nowait()
        except Exception:
            pass

    # --------------------------------------------------
    # Serial callback (background thread)
    # --------------------------------------------------
    def on_sample(self, sid: int, ch1: int, ch2: int, t_wall: float):
        # x-axis is sample_id
        self._q.put((int(sid), int(ch1), int(ch2)))

    # --------------------------------------------------
    # GUI timer (main thread)
    # --------------------------------------------------
    def update_plot(self):
        drained = 0

        while True:
            try:
                sid, ch1, ch2 = self._q.get_nowait()
            except Exception:
                break

            i = self._write_idx
            self.sid_buf[i] = sid
            self.ch1_buf[i] = ch1
            self.ch2_buf[i] = ch2

            self._write_idx = (i + 1) % self.n
            if self._write_idx == 0:
                self._filled = True

            # Write CSV on the GUI thread (simple + safe)
            if self._csv_w is not None:
                self._csv_w.writerow([sid, ch1, ch2])

            drained += 1

        if drained == 0:
            return

        # Flush occasionally (every update is fine at 1kHz; if you want faster UI,
        # change to flush every N updates)
        if self._csv_f is not None:
            try:
                self._csv_f.flush()
            except Exception:
                pass

        if self._filled:
            idx = self._write_idx
            x = np.concatenate((self.sid_buf[idx:], self.sid_buf[:idx]))
            y1 = np.concatenate((self.ch1_buf[idx:], self.ch1_buf[:idx]))
            y2 = np.concatenate((self.ch2_buf[idx:], self.ch2_buf[:idx]))
        else:
            x = self.sid_buf[: self._write_idx]
            y1 = self.ch1_buf[: self._write_idx]
            y2 = self.ch2_buf[: self._write_idx]

        mask = np.isfinite(x) & np.isfinite(y1) & np.isfinite(y2)
        x = x[mask]
        y1 = y1[mask]
        y2 = y2[mask]

        self.curve1.setData(x, y1)
        self.curve2.setData(x, y2)

        # Auto-follow keeps last window_sec visible, but only when follow is ON.
        if self.auto_follow and len(x) > 2:
            xmax = x[-1]
            xmin = max(xmax - (self.fs * self.window_sec), x[0])
            self.plot1.setXRange(xmin, xmax, padding=0)
            self.plot2.setXRange(xmin, xmax, padding=0)

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------
    def stop(self):
        self.want_collecting = False
        self.stop_hardware()
        self.button.setText("Start Collecting")