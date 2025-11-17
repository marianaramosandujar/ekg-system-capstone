import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel
)
from PySide6.QtCore import Qt
import pyqtgraph as pg

from ekg_system.processor import EKGProcessor
from ekg_system.arrhythmia_detector import ArrhythmiaDetector
from ekg_system.clinical_pg_view import ClinicalPGView
from ekg_system.live_pg_view import LiveECGView


class EKGApp(QWidget):
    # main UI app
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EKG Analysis System")
        self.setGeometry(100, 100, 1200, 800)

        # main objects for analysis
        self.processor = EKGProcessor(sampling_rate=1000)
        self.detector = ArrhythmiaDetector(sampling_rate=1000)
        self.data = None
        self.last_bpm = None

        main_layout = QVBoxLayout(self)

        # top control buttons
        row = QHBoxLayout()

        self.live_btn = QPushButton("Live View")
        self.live_btn.setFixedSize(200, 50)
        self.live_btn.setEnabled(False)
        self.live_btn.clicked.connect(self.show_live_view)

        self.load_btn = QPushButton("Load EKG File")
        self.load_btn.setFixedSize(200, 50)
        self.load_btn.clicked.connect(self.load_file)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setFixedSize(200, 50)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self.analyze_signal)

        self.clinical_btn = QPushButton("Clinical View")
        self.clinical_btn.setFixedSize(200, 50)
        self.clinical_btn.setEnabled(False)
        self.clinical_btn.clicked.connect(self.show_clinical_view)

        self.reset_btn = QPushButton("Reset Zoom")
        self.reset_btn.setFixedSize(200, 50)
        self.reset_btn.clicked.connect(self.reset_zoom)

        # put them in the row
        for btn in (self.live_btn, self.load_btn, self.analyze_btn,
                    self.clinical_btn, self.reset_btn):
            row.addWidget(btn)

        main_layout.addLayout(row)

        # little message area
        self.label = QLabel("Load a file to begin.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; padding: 8px;")
        main_layout.addWidget(self.label)

        # default plot for raw and analyzed data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setLabel('left', 'Amplitude (mV)')
        main_layout.addWidget(self.plot_widget)

        # placeholders for other pages
        self.clinical_view = None
        self.live_view = None

    def reset_zoom(self):
        # whichever page is showing gets reset
        if self.clinical_view and self.clinical_view.isVisible():
            self.clinical_view.reset_view()
        else:
            self.plot_widget.enableAutoRange()

    def load_file(self):
        # pick a file to load
        path, _ = QFileDialog.getOpenFileName(
            self, "Select EKG File", "", "CSV/TXT/NPY (*.csv *.txt *.npy)"
        )
        if not path:
            return

        try:
            # data goes through processor
            self.processor.load_data(path)
            self.data = self.processor.raw_data
            self.last_bpm = None

            filename = path.split("/")[-1]
            self.label.setText(f"Loaded: {filename}")

            # turn on buttons once we have data
            self.analyze_btn.setEnabled(True)
            self.clinical_btn.setEnabled(True)
            self.live_btn.setEnabled(True)

            # clear old views if they existed
            if self.clinical_view:
                self.clinical_view.setParent(None)
                self.clinical_view = None
            if self.live_view:
                self.live_view.stop()
                self.live_view.setParent(None)
                self.live_view = None

            self.show_standard_view()

        except Exception as e:
            self.label.setText(f"Error: {e}")

    def show_standard_view(self):
        # show the regular plot view
        if self.clinical_view:
            self.clinical_view.hide()
        if self.live_view:
            self.live_view.hide()

        self.label.show()
        self.plot_widget.show()

        if self.data is None:
            return

        # plot raw signal
        fs = self.processor.sampling_rate
        t = np.arange(len(self.data)) / fs
        self.plot_widget.clear()
        self.plot_widget.plot(t, self.data, pen='b')

    def analyze_signal(self):
        if self.data is None:
            return

        # always swap back to the main plot
        if self.clinical_view:
            self.clinical_view.hide()
        if self.live_view:
            self.live_view.hide()
        self.plot_widget.show()
        self.label.show()

        try:
            # do filtering and peak detection
            self.processor.filter_signal()
            self.processor.detect_r_peaks()

            rr = self.processor.peaks[1:] - self.processor.peaks[:-1]
            waves = self.processor.segment_waveforms()
            report = self.detector.generate_report(rr, waves, self.processor.peaks)

            self.last_bpm = report["mean_heart_rate"]
            arr = report["arrhythmias_detected"]

            # show results at the top
            self.label.setText(f"HR: {self.last_bpm:.1f} BPM | Arrhythmias: {arr}")

            fs = self.processor.sampling_rate
            t = np.arange(len(self.processor.filtered_data)) / fs

            # plot filtered data + peaks
            self.plot_widget.clear()
            self.plot_widget.plot(t, self.processor.filtered_data, pen='b')
            self.plot_widget.plot(
                self.processor.peaks / fs,
                self.processor.filtered_data[self.processor.peaks],
                pen=None, symbol='o', symbolBrush='r'
            )

        except Exception as e:
            self.label.setText(f"Error analyzing: {e}")

    def show_clinical_view(self):
        if self.data is None:
            return

        if self.live_view:
            self.live_view.hide()

        self.plot_widget.hide()
        self.label.hide()

        # make clinical viewer if first time
        if not self.clinical_view:
            self.clinical_view = ClinicalPGView(
                parent=self,
                signal=self.data,
                fs=self.processor.sampling_rate,
                window_sec=10
            )
            self.layout().addWidget(self.clinical_view)

        self.clinical_view.show()

    def show_live_view(self):
        if self.data is None:
            return

        if self.clinical_view:
            self.clinical_view.hide()

        self.plot_widget.hide()
        self.label.hide()

        # wipe out old live view and make a new one
        if self.live_view:
            self.live_view.stop()
            self.live_view.setParent(None)
            self.live_view = None

        self.live_view = LiveECGView(
            parent=self,
            signal=self.data,
            fs=self.processor.sampling_rate,
            window_sec=10
        )
        self.layout().addWidget(self.live_view)


if __name__ == "__main__":
    app = QApplication([])
    ui = EKGApp()
    ui.show()
    app.exec()
