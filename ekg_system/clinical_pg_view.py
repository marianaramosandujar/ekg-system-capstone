import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt


class ClinicalPGView(QWidget):
    # display ECG like clinical paper, fixed time window
    def __init__(self, parent=None, signal=None, fs=1000, window_sec=30):
        super().__init__(parent)

        self.signal = signal
        self.fs = fs
        self.window_sec = window_sec

        layout = QVBoxLayout(self)

        # main waveform area
        self.plot = pg.PlotWidget()
        layout.addWidget(self.plot)

        self.plot.setBackground('w')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setMouseEnabled(x=True, y=False)  # only allow horizontal moving
        self.plot.setLabel('bottom', 'Time (s)')
        self.plot.setLabel('left', 'Amplitude (mV)')

        # create time axis for graph
        t = np.arange(len(signal)) / fs
        self.curve = self.plot.plot(t, signal, pen=pg.mkPen('k', width=1))

        # save limits so y doesn’t move around
        self.sig_min = float(np.min(signal))
        self.sig_max = float(np.max(signal))
        self.plot.setYRange(self.sig_min, self.sig_max)

        # start by showing the first section of the data
        self.duration = len(signal) / fs
        end = min(self.window_sec, self.duration)
        self.plot.setXRange(0, end)

        # keep graph from scrolling off data
        self.plot.sigRangeChanged.connect(self._fix_bounds)

        # bottom little control buttons to move around
        nav_layout = QHBoxLayout()
        layout.addLayout(nav_layout)

        btn_defs = [
            ("⏮", self.go_to_start),
            ("◀", self.pan_left),
            ("➖", self.zoom_out),
            ("Reset", self.reset_view),
            ("➕", self.zoom_in),
            ("▶", self.pan_right),
            ("⏭", self.go_to_end)
        ]

        for text, handler in btn_defs:
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.clicked.connect(handler)
            nav_layout.addWidget(btn)

        # double click resets view
        self.plot.scene().sigMouseClicked.connect(self._check_double_click)

    # stops people from scrolling past start/end
    def _fix_bounds(self, xmin=None, xmax=None):
        if xmin is None:
            xmin, xmax = self.plot.viewRange()[0]

        if xmin < 0:
            xmin = 0
        if xmax > self.duration:
            xmax = self.duration

        # don’t let zoom be too tiny
        if xmax - xmin < 0.05:
            xmax = xmin + 0.05

        # update ranges
        self.plot.blockSignals(True)
        self.plot.setXRange(xmin, xmax, padding=0)
        self.plot.setYRange(self.sig_min, self.sig_max)
        self.plot.blockSignals(False)

    # turn the view back to first window
    def reset_view(self):
        end = min(self.window_sec, self.duration)
        self.plot.setXRange(0, end)
        self.plot.setYRange(self.sig_min, self.sig_max)

    # zoom into center
    def zoom_in(self):
        xmin, xmax = self.plot.viewRange()[0]
        mid = (xmin + xmax) / 2
        span = (xmax - xmin) * 0.8
        self._fix_bounds(mid - span/2, mid + span/2)

    # zoom out view
    def zoom_out(self):
        xmin, xmax = self.plot.viewRange()[0]
        mid = (xmin + xmax) / 2
        span = (xmax - xmin) * 1.25
        self._fix_bounds(mid - span/2, mid + span/2)

    # slide left
    def pan_left(self):
        xmin, xmax = self.plot.viewRange()[0]
        shift = (xmax - xmin) * 0.2
        self._fix_bounds(xmin - shift, xmax - shift)

    # slide right
    def pan_right(self):
        xmin, xmax = self.plot.viewRange()[0]
        shift = (xmax - xmin) * 0.2
        self._fix_bounds(xmin + shift, xmax + shift)

    # jump to start
    def go_to_start(self):
        self._fix_bounds(0, self.window_sec)

    # jump to end of data
    def go_to_end(self):
        self._fix_bounds(self.duration - self.window_sec, self.duration)

    # quick reset with double click
    def _check_double_click(self, event):
        if event.double():
            self.reset_view()
