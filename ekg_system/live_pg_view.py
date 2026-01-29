import numpy as np
import pyqtgraph as pg

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt

from ekg_system.microcontroller import MSP430Interface


class LivePGView(QWidget):
    """
    Live View tab:
    - Always shows Start / Stop button
    - Detects MSP430 USB CDC automatically
    - Sends START / STOP commands
    - Displays live ECG data
    """

    def __init__(self, parent=None, fs=1000, window_sec=5):
        super().__init__(parent)

        # -------------------------
        # Signal buffer
        # -------------------------
        self.fs = fs
        self.n = int(fs * window_sec)
        self.buffer = np.zeros(self.n)

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

        # Status label
        self.status = QLabel("Waiting for device…")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # Plot
        self.plot = pg.PlotWidget()
        self.plot.setBackground("w")
        self.plot.showGrid(x=True, y=True)
        self.curve = self.plot.plot(self.buffer, pen=pg.mkPen("k", width=1))
        layout.addWidget(self.plot)

        # Start / Stop button (ALWAYS enabled)
        self.button = QPushButton("Start Collecting")
        self.button.clicked.connect(self.toggle_collection)
        layout.addWidget(self.button)

        # -------------------------
        # Plot update timer
        # -------------------------
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(30)

        # -------------------------
        # Device detection timer
        # -------------------------
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

                # Auto-start if user already pressed Start
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
    def start_hardware(self):
        try:
            self.mcu.start(self.on_serial_line)
            self.collecting = True
            self.status.setText("Collecting data…")
        except Exception:
            self.status.setText("Waiting for device…")
            self.collecting = False

    def stop_hardware(self):
        if self.collecting:
            self.mcu.stop()

        self.collecting = False
        self.status.setText("Collection stopped")

    # --------------------------------------------------
    # Serial data callback
    # --------------------------------------------------
    def on_serial_line(self, line):
        try:
            # Accept "value" or "timestamp,value"
            value = float(line.split(",")[-1])

            self.buffer[:-1] = self.buffer[1:]
            self.buffer[-1] = value
        except ValueError:
            pass

    # --------------------------------------------------
    # Plot refresh
    # --------------------------------------------------
    def update_plot(self):
        self.curve.setData(self.buffer)

    # --------------------------------------------------
    # Cleanup when leaving Live View / closing app
    # --------------------------------------------------
    def stop(self):
        self.want_collecting = False
        self.stop_hardware()
        self.button.setText("Start Collecting")
        self.status.setText("Collection stopped")