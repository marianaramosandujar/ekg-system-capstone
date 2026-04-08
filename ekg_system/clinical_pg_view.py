import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import QSize
import qtawesome as qta

class ClinicalPGView(QWidget):
    def __init__(self, parent=None, signal=None, fs=1000, window_sec=30):
        super().__init__(parent)
        
        print("Creating ClinicalPGView...")  # Debug
        
        self.fs = fs
        self.window_sec = window_sec
        self.duration = len(signal) / fs
        
        layout = QVBoxLayout(self)
        
        # Create plot
        self.plot = pg.PlotWidget()
        self.plot.setBackground("white")
        layout.addWidget(self.plot)
        
        # Downsample
        step = max(1, len(signal) // 20000)
        t = np.arange(0, len(signal), step) / fs
        y = signal[::step]
        
        # Plot
        self.plot.plot(t, y, pen=pg.mkPen(color="black", width=1.5))
        
        # Set initial view
        end = min(window_sec, self.duration)
        self.plot.setXRange(0, end)
        self.plot.setYRange(float(np.min(y)), float(np.max(y)))
        
        # Buttons
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)
        
        for icon, tip, func in [
            ("fa5s.backward", "Start", self.go_start),
            ("fa5s.arrow-left", "Left", self.pan_left),
            ("fa5s.search-minus", "Zoom Out", self.zoom_out),
            ("fa5s.sync", "Reset", self.reset),
            ("fa5s.search-plus", "Zoom In", self.zoom_in),
            ("fa5s.arrow-right", "Right", self.pan_right),
            ("fa5s.forward", "End", self.go_end),
        ]:
            btn = QPushButton()
            btn.setIcon(qta.icon(icon))
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(tip)
            btn.setFixedSize(42, 40)
            btn.clicked.connect(func)
            btn_layout.addWidget(btn)
    
    def get_range(self):
        return self.plot.viewRange()[0]
    
    def set_range(self, x1, x2):
        x1 = max(0, float(x1))
        x2 = min(self.duration, float(x2))
        if x2 - x1 < 0.01:
            x2 = x1 + 0.01
        self.plot.setXRange(x1, x2, padding=0)
    
    def reset(self):
        self.set_range(0, min(self.window_sec, self.duration))
    
    def zoom_in(self):
        x1, x2 = self.get_range()
        c = (x1 + x2) / 2
        w = (x2 - x1) * 0.8
        self.set_range(c - w/2, c + w/2)
    
    def zoom_out(self):
        x1, x2 = self.get_range()
        c = (x1 + x2) / 2
        w = (x2 - x1) * 1.25
        self.set_range(c - w/2, c + w/2)
    
    def pan_left(self):
        x1, x2 = self.get_range()
        w = x2 - x1
        self.set_range(x1 - w*0.2, x2 - w*0.2)
    
    def pan_right(self):
        x1, x2 = self.get_range()
        w = x2 - x1
        self.set_range(x1 + w*0.2, x2 + w*0.2)
    
    def go_start(self):
        self.set_range(0, min(self.window_sec, self.duration))
    
    def go_end(self):
        self.set_range(max(0, self.duration - self.window_sec), self.duration)