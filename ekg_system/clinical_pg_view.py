import numpy as np
import pyqtgraph as pg

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import QSize

import qtawesome as qta


class ClinicalPGView(QWidget):

    def __init__(self, parent=None, signal=None, fs=1000, window_sec=30):
        super().__init__(parent)

        self.signal = signal
        self.fs = fs
        self.window_sec = window_sec

        layout = QVBoxLayout(self)

        self.plot = pg.PlotWidget()
        layout.addWidget(self.plot)

        self.plot.setBackground("w")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setMouseEnabled(x=True, y=False)

        self.plot.setLabel("bottom", "Time (s)")
        self.plot.setLabel("left", "Amplitude (mV)")

        t = np.arange(len(signal)) / fs
        self.curve = self.plot.plot(t, signal, pen=pg.mkPen("k", width=1))

        self.sig_min = float(np.min(signal))
        self.sig_max = float(np.max(signal))
        self.plot.setYRange(self.sig_min, self.sig_max)

        self.duration = len(signal) / fs
        end = min(self.window_sec, self.duration)

        self.plot.setXRange(0, end)

        self.plot.sigRangeChanged.connect(self._fix_bounds)

        nav_layout = QHBoxLayout()
        layout.addLayout(nav_layout)

        btn_defs = [
            ("fa5s.backward", "Start", self.go_to_start),
            ("fa5s.arrow-left", "Left", self.pan_left),
            ("fa5s.search-minus", "Zoom Out", self.zoom_out),
            ("fa5s.sync", "Reset", self.reset_view),
            ("fa5s.search-plus", "Zoom In", self.zoom_in),
            ("fa5s.arrow-right", "Right", self.pan_right),
            ("fa5s.forward", "End", self.go_to_end),
        ]

        for icon_name, tooltip, handler in btn_defs:

            btn = QPushButton()
            btn.setIcon(qta.icon(icon_name))
            btn.setIconSize(QSize(20,20))
            btn.setToolTip(tooltip)
            btn.setFixedSize(42,40)
            btn.clicked.connect(handler)

            nav_layout.addWidget(btn)

        self.plot.scene().sigMouseClicked.connect(self._check_double_click)

    def _fix_bounds(self, xmin=None, xmax=None):

        if xmin is None:
            xmin, xmax = self.plot.viewRange()[0]

        if xmin < 0:
            xmin = 0

        if xmax > self.duration:
            xmax = self.duration

        if xmax - xmin < 0.05:
            xmax = xmin + 0.05

        self.plot.blockSignals(True)

        self.plot.setXRange(xmin, xmax, padding=0)
        self.plot.setYRange(self.sig_min, self.sig_max)

        self.plot.blockSignals(False)

    def reset_view(self):

        end = min(self.window_sec, self.duration)

        self.plot.setXRange(0, end)
        self.plot.setYRange(self.sig_min, self.sig_max)

    def zoom_in(self):

        xmin, xmax = self.plot.viewRange()[0]
        mid = (xmin + xmax) / 2
        span = (xmax - xmin) * 0.8

        self._fix_bounds(mid - span/2, mid + span/2)

    def zoom_out(self):

        xmin, xmax = self.plot.viewRange()[0]
        mid = (xmin + xmax) / 2
        span = (xmax - xmin) * 1.25

        self._fix_bounds(mid - span/2, mid + span/2)

    def pan_left(self):

        xmin, xmax = self.plot.viewRange()[0]
        shift = (xmax - xmin) * 0.2

        self._fix_bounds(xmin - shift, xmax - shift)

    def pan_right(self):

        xmin, xmax = self.plot.viewRange()[0]
        shift = (xmax - xmin) * 0.2

        self._fix_bounds(xmin + shift, xmax + shift)

    def go_to_start(self):
        self._fix_bounds(0, self.window_sec)

    def go_to_end(self):
        self._fix_bounds(max(0, self.duration - self.window_sec), self.duration)

    def _check_double_click(self, event):
        if event.double():
            self.reset_view()