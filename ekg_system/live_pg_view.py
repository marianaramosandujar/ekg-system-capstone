import numpy as np
import pyqtgraph as pg
import queue

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt

from ekg_system.microcontroller import MSP430Interface


class LivePGView(QWidget):
    """
    Live View tab:
    - Start / Stop button
    - Detects MSP430 USB CDC automatically
    - Displays live data:
        CSV columns:
          1: sample_id
          2: timestamp
          3: status
          4: ch1
          5: ch2
      Plots:
        Plot 1: x=timestamp, y=ch1
        Plot 2: x=timestamp, y=ch2
    """

    def __init__(self, parent=None, fs=1000, window_sec=5):
        super().__init__(parent)

        # -------------------------
        # Buffer config (N samples)
        # -------------------------
        self.fs = fs
        self.n = int(fs * window_sec)

        # Ring buffers (timestamp + 2 channels)
        self.t_buf = np.full(self.n, np.nan, dtype=float)
        self.ch1_buf = np.full(self.n, np.nan, dtype=float)
        self.ch2_buf = np.full(self.n, np.nan, dtype=float)

        self._write_idx = 0
        self._filled = False

        # Thread-safe queue: serial thread -> GUI thread
        self._q = queue.SimpleQueue()

        # -------------------------
        # Hardware interface
        # -------------------------
        self.mcu = MSP430Interface()
        self.device_connected = False
        self.collecting = False
        self.want_collecting = False

        # -------------------------
        # Layout
        # -------------------------
        layout = QVBoxLayout(self)

        self.status = QLabel("Waiting for device…")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # Plot 1: ch1 vs timestamp
        self.plot1 = pg.PlotWidget()
        self.plot1.setBackground("w")
        self.plot1.showGrid(x=True, y=True)
        self.plot1.setLabel("bottom", "Timestamp (col 2)")
        self.plot1.setLabel("left", "CH1 (col 4)")
        self.curve1 = self.plot1.plot([], [], pen=pg.mkPen("k", width=1))
        layout.addWidget(self.plot1)

        # Plot 2: ch2 vs timestamp
        self.plot2 = pg.PlotWidget()
        self.plot2.setBackground("w")
        self.plot2.showGrid(x=True, y=True)
        self.plot2.setLabel("bottom", "Timestamp (col 2)")
        self.plot2.setLabel("left", "CH2 (col 5)")
        self.curve2 = self.plot2.plot([], [], pen=pg.mkPen("k", width=1))
        layout.addWidget(self.plot2)

        # Start / Stop button (ALWAYS enabled)
        self.button = QPushButton("Start Collecting")
        self.button.clicked.connect(self.toggle_collection)
        layout.addWidget(self.button)

        # -------------------------
        # Timers
        # -------------------------
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(30)

        self.detect_timer = QTimer(self)
        self.detect_timer.timeout.connect(self.check_device)
        self.detect_timer.start(1000)

    # --------------------------------------------------
    # Detect MSP430 USB CDC
    # --------------------------------------------------
    def check_device(self):
        if not self.device_connected:
            port = self.mcu.detect_port()
            if port:
                self.device_connected = True
                self.status.setText("MSP430 detected")

                if self.want_collecting and not self.collecting:
                    self.start_hardware()

    # --------------------------------------------------
    # Start / Stop button logic (intent-based)
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
    # --------------------------------------------------
    # Hardware control
    # --------------------------------------------------
    def start_hardware(self):
        if self.collecting:
            return
        try:
            self.mcu.start(self.on_serial_line)
            self.collecting = True
            self.status.setText("Collecting data…")
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
    # Push parsed data into queue; do NOT touch numpy buffers here.
    # --------------------------------------------------
    def on_serial_line(self, line: str):
        print("UI RX:", line)

        parts = line.split(",")
        if len(parts) < 5:
            return

        try:
            timestamp = float(parts[1].strip())
            ch1 = float(parts[3].strip())
            ch2 = float(parts[4].strip())
        except ValueError:
            return

        self._q.put((timestamp, ch1, ch2))

    # --------------------------------------------------
    # GUI timer: drain queue -> write ring buffers -> plot
    # --------------------------------------------------
    def update_plot(self):
        drained = 0
        while True:
            try:
                timestamp, ch1, ch2 = self._q.get_nowait()
            except Exception:
                break

            i = self._write_idx
            self.t_buf[i] = timestamp
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
            t = self.t_buf[:self._write_idx]
            y1 = self.ch1_buf[:self._write_idx]
            y2 = self.ch2_buf[:self._write_idx]

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