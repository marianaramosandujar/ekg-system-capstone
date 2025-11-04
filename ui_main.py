import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel
)
from PySide6.QtCore import Qt
import pyqtgraph as pg

from ekg_system.processor import EKGProcessor
from ekg_system.arrhythmia_detector import ArrhythmiaDetector

# ✅ clinical plotting import
from clinical_plot import plot_clinical_ecg


class EKGApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EKG Analysis System")
        self.setGeometry(100, 100, 900, 600)

        # Core processor & detector
        self.processor = EKGProcessor(sampling_rate=1000)
        self.detector = ArrhythmiaDetector(sampling_rate=1000)
        self.data = None

        # Layout
        layout = QVBoxLayout()

        # Buttons
        self.load_btn = QPushButton("Load EKG File")
        self.load_btn.clicked.connect(self.load_file)
        layout.addWidget(self.load_btn)

        self.analyze_btn = QPushButton("Analyze EKG")
        self.analyze_btn.clicked.connect(self.analyze_signal)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)

        # ✅ Clinical button
        self.clinical_btn = QPushButton("Clinical EKG View")
        self.clinical_btn.setEnabled(False)
        self.clinical_btn.clicked.connect(self.show_clinical_view)
        layout.addWidget(self.clinical_btn)

        # Message label
        self.label = QLabel("Load an EKG file to begin.")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Plot area using pyqtgraph
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        layout.addWidget(self.plot_widget)

        self.setLayout(layout)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select EKG File", "", "CSV/TXT/NPY (*.csv *.txt *.npy)"
        )
        if not path:
            return

        try:
            # ✅ Let processor.py handle loading & parsing
            self.processor.load_data(path)
            self.data = self.processor.raw_data

            self.label.setText(f"Loaded file: {path}")
            self.analyze_btn.setEnabled(True)
            self.clinical_btn.setEnabled(True)  # ✅ enable clinical button

            # Plot raw signal
            self.plot_widget.clear()
            self.plot_widget.plot(self.data, pen='b')

        except Exception as e:
            self.label.setText(f"❌ Failed to load file: {e}")
            self.analyze_btn.setEnabled(False)
            self.clinical_btn.setEnabled(False)

    def analyze_signal(self):
        try:
            self.processor.filter_signal()
            self.processor.detect_r_peaks()

            rr = self.processor.peaks[1:] - self.processor.peaks[:-1]
            waveforms = self.processor.segment_waveforms()

            report = self.detector.generate_report(rr, waveforms, self.processor.peaks)

            bpm = report['mean_heart_rate']
            arr = report['arrhythmias_detected']

            self.label.setText(f"✅ HR: {bpm:.1f} BPM | Arrhythmias: {arr}")

            # Plot filtered signal + peaks
            self.plot_widget.clear()
            self.plot_widget.plot(self.processor.filtered_data, pen='b')
            self.plot_widget.plot(
                self.processor.peaks,
                self.processor.filtered_data[self.processor.peaks],
                pen=None,
                symbol='o',
                symbolBrush='r'
            )

        except Exception as e:
            self.label.setText(f"❌ Error: {e}")

    # ✅ Clinical EKG viewer
    def show_clinical_view(self):
        try:
            if self.data is None:
                self.label.setText("⚠️ Load data first.")
                return
            plot_clinical_ecg(self.data, fs=1000, seconds=10)
        except Exception as e:
            self.label.setText(f"❌ Clinical View Error: {e}")


if __name__ == "__main__":
    app = QApplication([])
    ui = EKGApp()
    ui.show()
    app.exec()
