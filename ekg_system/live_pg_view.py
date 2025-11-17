import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import QTimer


class LiveECGView(QWidget):
    # live scrolling ECG display using a moving data window
    def __init__(self, parent=None, signal=None, fs=1000, window_sec=10):
        super().__init__(parent)

        self.signal = np.asarray(signal, dtype=float)
        self.fs = fs
        self.window_sec = window_sec

        # number of samples that fit on screen at once
        self.n_window = int(self.fs * self.window_sec)
        self.idx = 0  # keeps track of where we are in the dataset

        main_layout = QVBoxLayout(self)

        # main plot widget for waveform only (no labels)
        self.plot = pg.PlotWidget()
        main_layout.addWidget(self.plot)

        self.plot.setBackground('w')
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setMenuEnabled(False)
        self.plot.enableAutoRange(False, False)

        p = self.plot.getPlotItem()
        p.hideAxis('bottom')
        p.hideAxis('left')

        # fixed time axis so time always moves forward left → right
        self.time_axis = np.linspace(0, self.window_sec, self.n_window, endpoint=False)
        self.plot.setXRange(0, self.window_sec, padding=0)

        # create circular buffer (what is shown on screen)
        self.buffer = np.zeros(self.n_window)
        initial = min(self.n_window, len(self.signal))

        # load the first chunk of data
        if initial > 0:
            self.buffer[-initial:] = self.signal[:initial]
            self.idx = initial

        # y-limits stay constant so it doesn’t bounce
        if len(self.signal) > 0:
            self.sig_min = float(np.min(self.signal))
            self.sig_max = float(np.max(self.signal))
        else:
            self.sig_min, self.sig_max = -1, 1

        self.plot.setYRange(self.sig_min, self.sig_max)

        # plot line object
        self.curve = self.plot.plot(
            self.time_axis,
            self.buffer,
            pen=pg.mkPen('k', width=1)
        )

        # live toggle button at bottom
        controls = QHBoxLayout()
        controls.addStretch()

        self.start_stop_btn = QPushButton("Start Live")
        self.start_stop_btn.setFixedHeight(36)
        self.start_stop_btn.clicked.connect(self.toggle_stream)

        controls.addWidget(self.start_stop_btn)
        main_layout.addLayout(controls)

        # timer calls update function ~50fps (20ms)
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self._update_stream)

    # pressing the button starts or stops the stream
    def toggle_stream(self):
        if self.timer.isActive():
            self.stop()
        else:
            self.start()

    def start(self):
        if not self.timer.isActive():
            self.timer.start()
            self.start_stop_btn.setText("Stop Live")

    def stop(self):
        if self.timer.isActive():
            self.timer.stop()
        self.start_stop_btn.setText("Start Live")

    # pulls next chunk of samples and shifts left
    def _update_stream(self):
        if len(self.signal) == 0:
            self.stop()
            return

        # how many samples to move each frame
        step = max(1, int(self.fs * (self.timer.interval() / 1000.0)))

        end = self.idx + step
        # wrap around if we hit the end (simulation loop)
        if end <= len(self.signal):
            new_samples = self.signal[self.idx:end]
            self.idx = end
        else:
            part1 = self.signal[self.idx:]
            remain = end - len(self.signal)
            part2 = self.signal[:remain]
            new_samples = np.concatenate([part1, part2])
            self.idx = remain

        # push old samples left, add new ones on right side
        self.buffer = np.roll(self.buffer, -len(new_samples))
        self.buffer[-len(new_samples):] = new_samples

        # update the visual graph
        self.curve.setData(self.time_axis, self.buffer)
        self.plot.setXRange(0, self.window_sec, padding=0)
        self.plot.setYRange(self.sig_min, self.sig_max)
