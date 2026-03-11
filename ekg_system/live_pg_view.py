import os
import csv
from datetime import datetime
import numpy as np
import pyqtgraph as pg
import queue

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer, Qt, QUrl, QSize
from PySide6.QtGui import QDesktopServices

import qtawesome as qta

from ekg_system.microcontroller import MSP430Interface


def style_ecg_plot(plot_widget):
    plot_widget.setBackground("w")

    axis_pen = pg.mkPen(color="black", width=2)
    plot_widget.getAxis("bottom").setPen(axis_pen)
    plot_widget.getAxis("left").setPen(axis_pen)

    plot_widget.getAxis("bottom").setTextPen("black")
    plot_widget.getAxis("left").setTextPen("black")

    plot_widget.showGrid(x=True, y=True, alpha=0.12)


class LivePGView(QWidget):

    def __init__(self, parent=None, fs=1000, window_sec=10):
        super().__init__(parent)

        self.fs = fs
        self.window_sec = window_sec
        self.display_samples = int(fs * window_sec)

        self.samples_seen = 0

        self.sid_data = []
        self.ch1_data = []
        self.ch2_data = []

        self._q = queue.SimpleQueue()

        self.mcu = MSP430Interface(mode="binary")
        self.device_connected = False
        self.collecting = False
        self.want_collecting = False

        self.csv_path = None
        self._csv_f = None
        self._csv_w = None

        layout = QVBoxLayout(self)

        self.status = QLabel("Waiting for device…")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # CH1 plot
        self.plot1 = pg.PlotWidget()
        self.plot1.setLabel("bottom", "Sample ID")
        self.plot1.setLabel("left", "CH1")
        style_ecg_plot(self.plot1)
        self.curve1 = self.plot1.plot([], [], pen=pg.mkPen(color="black", width=2))
        layout.addWidget(self.plot1)

        # CH2 plot
        self.plot2 = pg.PlotWidget()
        self.plot2.setLabel("bottom", "Sample ID")
        self.plot2.setLabel("left", "CH2")
        style_ecg_plot(self.plot2)
        self.curve2 = self.plot2.plot([], [], pen=pg.mkPen(color="black", width=2))
        layout.addWidget(self.plot2)

        controls = QHBoxLayout()

        self.button = QPushButton("Start Collecting")
        self.button.setIcon(qta.icon("fa5s.play"))
        self.button.setIconSize(QSize(18, 18))
        self.button.setFixedHeight(38)
        self.button.clicked.connect(self.toggle_collection)
        controls.addWidget(self.button)

        self.open_btn = QPushButton("Open Data File")
        self.open_btn.setIcon(qta.icon("fa5s.folder-open"))
        self.open_btn.setIconSize(QSize(18, 18))
        self.open_btn.setFixedSize(170, 38)
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_csv_file)
        controls.addWidget(self.open_btn)

        layout.addLayout(controls)

        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(40)

        self.detect_timer = QTimer(self)
        self.detect_timer.timeout.connect(self.check_device)
        self.detect_timer.start(1000)

    def reset_view(self):
        self.plot1.enableAutoRange(x=True, y=True)
        self.plot2.enableAutoRange(x=True, y=True)
        self.plot1.autoRange()
        self.plot2.autoRange()

    def check_device(self):
        if not self.device_connected:
            port = self.mcu.detect_port()

            if port:
                self.device_connected = True
                self.status.setText(f"MSP430 detected ({port})")

                if self.want_collecting:
                    self.start_hardware()

    def _update_collect_button(self):
        if self.want_collecting:
            self.button.setText("Stop Collecting")
            self.button.setIcon(qta.icon("fa5s.pause"))
        else:
            self.button.setText("Start Collecting")
            self.button.setIcon(qta.icon("fa5s.play"))

    def toggle_collection(self):
        self.want_collecting = not self.want_collecting
        self._update_collect_button()

        if self.want_collecting:
            if self.device_connected:
                self.start_hardware()
            else:
                self.status.setText("Waiting for device…")
        else:
            self.stop_hardware()

    def _start_csv(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.abspath(f"ekg_capture_{ts}.csv")

        self._csv_f = open(self.csv_path, "w", newline="")
        self._csv_w = csv.writer(self._csv_f)
        self._csv_w.writerow(["sample_id", "ch1", "ch2"])

        self.open_btn.setEnabled(True)

    def _stop_csv(self):
        if self._csv_f:
            self._csv_f.close()

        self._csv_f = None
        self._csv_w = None

    def open_csv_file(self):
        if self.csv_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.csv_path))

    def start_hardware(self):
        if self.collecting:
            return

        self._reset_buffers()
        self._start_csv()
        self.mcu.start(self.on_sample)
        self.collecting = True

    def stop_hardware(self):
        if self.collecting:
            self.mcu.stop()

        self.collecting = False
        self._stop_csv()

    def _reset_buffers(self):
        self.sid_data = []
        self.ch1_data = []
        self.ch2_data = []
        self.samples_seen = 0

        self.curve1.setData([], [])
        self.curve2.setData([], [])

        while not self._q.empty():
            self._q.get()

    def on_sample(self, sid, ch1, ch2, t_wall):
        self._q.put((sid, ch1, ch2))

    def update_plot(self):
        drained = 0

        while True:
            try:
                sid, ch1, ch2 = self._q.get_nowait()
            except Exception:
                break

            if self._csv_w:
                self._csv_w.writerow([sid, ch1, ch2])

            self.samples_seen += 1
            self.sid_data.append(sid)
            self.ch1_data.append(ch1)
            self.ch2_data.append(ch2)
            drained += 1

        if drained == 0:
            return

        x = np.asarray(self.sid_data)
        y1 = np.asarray(self.ch1_data)
        y2 = np.asarray(self.ch2_data)

        if len(x) > self.display_samples:
            x = x[-self.display_samples:]
            y1 = y1[-self.display_samples:]
            y2 = y2[-self.display_samples:]

        self.curve1.setData(x, y1)
        self.curve2.setData(x, y2)

        self.plot1.setXRange(x[0], x[-1], padding=0)
        self.plot2.setXRange(x[0], x[-1], padding=0)

        self.plot1.enableAutoRange(axis="y")
        self.plot2.enableAutoRange(axis="y")

        if self.csv_path:
            self.status.setText(f"Saving to {os.path.basename(self.csv_path)}")

    def stop(self):
        self.want_collecting = False
        self.stop_hardware()

        self.button.setText("Start Collecting")
        self.button.setIcon(qta.icon("fa5s.play"))
        self.status.setText("Collection stopped")