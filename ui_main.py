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
from ekg_system.live_pg_view import LivePGView


class EKGApp(QWidget):
    # main UI app
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EKG Analysis System")
        self.setGeometry(100, 100, 1200, 800)

        # -----------------------------------------
        # Processing objects (file-based only)
        # -----------------------------------------
        self.processor = EKGProcessor(sampling_rate=1000)
        self.detector = ArrhythmiaDetector(sampling_rate=1000)
        self.data = None
        self.last_bpm = None

        main_layout = QVBoxLayout(self)

        # -----------------------------------------
        # Top control buttons
        # -----------------------------------------
        row = QHBoxLayout()

        self.live_btn = QPushButton("Live View")
        self.live_btn.setFixedSize(200, 50)
        self.live_btn.setEnabled(True)
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

        for btn in (
            self.live_btn,
            self.load_btn,
            self.analyze_btn,
            self.clinical_btn,
            self.reset_btn
        ):
            row.addWidget(btn)

        main_layout.addLayout(row)

        # -----------------------------------------
        # Status label
        # -----------------------------------------
        self.label = QLabel("Select Live View to begin live acquisition.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; padding: 8px;")
        main_layout.addWidget(self.label)

        # -----------------------------------------
        # Standard plot (file-based)
        # -----------------------------------------
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.setLabel("left", "Amplitude (mV)")
        main_layout.addWidget(self.plot_widget)

        # -----------------------------------------
        # Live View (created ONCE)
        # -----------------------------------------
        self.live_view = LivePGView(
            parent=self,
            fs=1000,
            window_sec=10
        )
        self.live_view.hide()
        main_layout.addWidget(self.live_view)

        # -----------------------------------------
        # Other pages
        # -----------------------------------------
        self.clinical_view = None

    # -----------------------------------------
    # Utility
    # -----------------------------------------
    def reset_zoom(self):
        if self.clinical_view and self.clinical_view.isVisible():
            self.clinical_view.reset_view()
        else:
            self.plot_widget.enableAutoRange()

    # -----------------------------------------
    # File loading
    # -----------------------------------------
    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select EKG File", "", "CSV/TXT/NPY (*.csv *.txt *.npy)"
        )
        if not path:
            return

        try:
            self.processor.load_data(path)
            self.data = self.processor.raw_data
            self.last_bpm = None

            filename = path.split("/")[-1]
            self.label.setText(f"Loaded: {filename}")

            self.analyze_btn.setEnabled(True)
            self.clinical_btn.setEnabled(True)

            if self.clinical_view:
                self.clinical_view.setParent(None)
                self.clinical_view = None

            self.show_standard_view()

        except Exception as e:
            self.label.setText(f"Error: {e}")

    # -----------------------------------------
    # Standard plot view
    # -----------------------------------------
    def show_standard_view(self):
        if self.clinical_view:
            self.clinical_view.hide()

        self.live_view.hide()
        self.plot_widget.show()
        self.label.show()

        if self.data is None:
            return

        fs = self.processor.sampling_rate
        t = np.arange(len(self.data)) / fs

        self.plot_widget.clear()
        self.plot_widget.plot(
            t,
            self.data,
            pen=pg.mkPen(color="black", width=1)
        )

    # -----------------------------------------
    # Analysis
    # -----------------------------------------
    def analyze_signal(self):
        if self.data is None:
            return

        self.live_view.hide()
        if self.clinical_view:
            self.clinical_view.hide()

        self.plot_widget.show()
        self.label.show()

        try:
            self.processor.filter_signal()
            self.processor.detect_r_peaks()

            rr = self.processor.peaks[1:] - self.processor.peaks[:-1]
            waves = self.processor.segment_waveforms()
            report = self.detector.generate_report(
                rr, waves, self.processor.peaks
            )

            self.last_bpm = report["mean_heart_rate"]
            arr = report["arrhythmias_detected"]

            self.label.setText(
                f"HR: {self.last_bpm:.1f} BPM | Arrhythmias: {arr}"
            )

            fs = self.processor.sampling_rate
            t = np.arange(len(self.processor.filtered_data)) / fs

            self.plot_widget.clear()
            self.plot_widget.plot(
                t,
                self.processor.filtered_data,
                pen=pg.mkPen(color="black", width=1)
            )

            self.plot_widget.plot(
                self.processor.peaks / fs,
                self.processor.filtered_data[self.processor.peaks],
                pen=None,
                symbol="o",
                symbolBrush="r",
                symbolSize=8
            )

        except Exception as e:
            self.label.setText(f"Error analyzing: {e}")

    # -----------------------------------------
    # Clinical View
    # -----------------------------------------
    def show_clinical_view(self):
        if self.data is None:
            return

        self.live_view.hide()
        self.plot_widget.hide()
        self.label.hide()

        if not self.clinical_view:
            self.clinical_view = ClinicalPGView(
                parent=self,
                signal=self.data,
                fs=self.processor.sampling_rate,
                window_sec=10
            )
            self.layout().addWidget(self.clinical_view)

        self.clinical_view.show()

    # -----------------------------------------
    # Live View
    # -----------------------------------------
    def show_live_view(self):
        if self.clinical_view:
            self.clinical_view.hide()

        self.plot_widget.hide()
        self.label.hide()

        self.live_view.show()

    # -----------------------------------------
    # Clean shutdown
    # -----------------------------------------
    def closeEvent(self, event):
        self.live_view.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    ui = EKGApp()
    ui.show()
    app.exec()
