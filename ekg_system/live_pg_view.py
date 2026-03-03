import numpy as np
import pyqtgraph as pg
import queue

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt

from ekg_system.microcontroller import MSP430Interface


class LivePGView(QWidget):
    """
    Live View tab (binary stream):

      Packets:
        sample_id (uint32), ch1 (s24), ch2 (s24)

      Plots:
        Plot 1: x = time (seconds, derived from sample_id + fs), y = ch1
        Plot 2: x = time (seconds, derived from sample_id + fs), y = ch2
    """

    def __init__(self, parent=None, fs=1000, window_sec=5):
        super().__init__(parent)

        self.fs = fs
        self.n = int(fs * window_sec)

        # Ring buffers
        self.t_buf = np.full(self.n, np.nan, dtype=float)
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

        # For x-axis time reconstruction
        self._t0_wall = None
        self._sid0 = None

        # Layout
        layout = QVBoxLayout(self)

        self.status = QLabel("Waiting for device…")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # -------- Plot 1 (CH1) --------
        self.plot1 = pg.PlotWidget()
        self.plot1.setBackground("w")
        self.plot1.showGrid(x=True, y=True)
        self.plot1.setLabel("bottom", "Time (s)")
        self.plot1.setLabel("left", "CH1")
        self.plot1.enableAutoRange(axis="y", enable=True)
        self.curve1 = self.plot1.plot([], [], pen=pg.mkPen("r", width=2))
        layout.addWidget(self.plot1)

        # -------- Plot 2 (CH2) --------
        self.plot2 = pg.PlotWidget()
        self.plot2.setBackground("w")
        self.plot2.showGrid(x=True, y=True)
        self.plot2.setLabel("bottom", "Time (s)")
        self.plot2.setLabel("left", "CH2")
        self.plot2.enableAutoRange(axis="y", enable=True)
        self.curve2 = self.plot2.plot([], [], pen=pg.mkPen("r", width=2))
        layout.addWidget(self.plot2)

        # Button
        self.button = QPushButton("Start Collecting")
        self.button.clicked.connect(self.toggle_collection)
        layout.addWidget(self.button)

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
    # Hardware control
    # --------------------------------------------------
    def start_hardware(self):
        if self.collecting:
            return
        try:
            # callback now receives (sid, ch1, ch2, t_wall)
            self.mcu.start(self.on_sample)
            self.collecting = True
            self.status.setText("Collecting data…")

            # reset time base on start
            self._t0_wall = None
            self._sid0 = None
        except Exception as e:
            self.status.setText(f"Serial start failed: {e}")
            self.collecting = False

    def stop_hardware(self):
        if self.collecting:
            self.mcu.stop()
        self.collecting = False
        self.status.setText("Collection stopped")

    # --------------------------------------------------
    # Serial callback (background thread)
    # --------------------------------------------------
    def on_sample(self, sid: int, ch1: int, ch2: int, t_wall: float):
        # establish time base from first packet
        if self._sid0 is None:
            self._sid0 = sid
            self._t0_wall = t_wall

        # derive a stable time axis from sample_id and fs
        t = (sid - self._sid0) / float(self.fs)
        self._q.put((t, float(ch1), float(ch2)))

    # --------------------------------------------------
    # GUI timer (main thread)
    # --------------------------------------------------
    def update_plot(self):
        drained = 0

        while True:
            try:
                t, ch1, ch2 = self._q.get_nowait()
            except Exception:
                break

            i = self._write_idx
            self.t_buf[i] = t
            self.ch1_buf[i] = ch1
            self.ch2_buf[i] = ch2

            self._write_idx = (i + 1) % self.n
            if self._write_idx == 0:
                self._filled = True

            drained += 1

        if drained == 0:
            return

        if self._filled:
            idx = self._write_idx
            t = np.concatenate((self.t_buf[idx:], self.t_buf[:idx]))
            y1 = np.concatenate((self.ch1_buf[idx:], self.ch1_buf[:idx]))
            y2 = np.concatenate((self.ch2_buf[idx:], self.ch2_buf[:idx]))
        else:
            t = self.t_buf[: self._write_idx]
            y1 = self.ch1_buf[: self._write_idx]
            y2 = self.ch2_buf[: self._write_idx]

        mask = np.isfinite(t) & np.isfinite(y1) & np.isfinite(y2)
        t = t[mask]
        y1 = y1[mask]
        y2 = y2[mask]

        self.curve1.setData(t, y1)
        self.curve2.setData(t, y2)

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------
    def stop(self):
        self.want_collecting = False
        self.stop_hardware()
        self.button.setText("Start Collecting")
        self.status.setText("Collection stopped")