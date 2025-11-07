import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel
)
from PySide6.QtCore import Qt
import pyqtgraph as pg

from ekg_system.processor import EKGProcessor
import ekg_system.processor
print("Loaded processor from:", ekg_system.processor.__file__)

from ekg_system.arrhythmia_detector import ArrhythmiaDetector
from clinical_plot import plot_clinical_ecg


class EKGApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EKG Analysis System")
        self.setGeometry(100, 100, 1000, 700)

        # Core processor & detector
        self.processor = EKGProcessor(sampling_rate=1000)
        self.detector = ArrhythmiaDetector(sampling_rate=1000)
        self.data = None

        # === Main layout ===
        main_layout = QVBoxLayout()

        # === Button layout (HORIZONTAL) ===
        button_layout = QHBoxLayout()

        # Buttons with larger size
        self.load_btn = QPushButton("Load EKG File")
        self.load_btn.setFixedHeight(50)
        self.load_btn.setFixedWidth(200)
        self.load_btn.clicked.connect(self.load_file)

        self.analyze_btn = QPushButton("Analyze EKG")
        self.analyze_btn.setFixedHeight(50)
        self.analyze_btn.setFixedWidth(200)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self.analyze_signal)

        self.clinical_btn = QPushButton("Clinical EKG View")
        self.clinical_btn.setFixedHeight(50)
        self.clinical_btn.setFixedWidth(200)
        self.clinical_btn.setEnabled(False)
        self.clinical_btn.clicked.connect(self.show_clinical_view)

        # Reset zoom button
        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.setFixedHeight(50)
        self.reset_zoom_btn.setFixedWidth(200)
        self.reset_zoom_btn.clicked.connect(lambda: self.plot_widget.enableAutoRange('xy', True))

        # Add buttons side-by-side
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.clinical_btn)
        button_layout.addWidget(self.reset_zoom_btn)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        # === Message label ===
        self.label = QLabel("Load an EKG file to begin.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; padding: 10px;")
        main_layout.addWidget(self.label)

        # === Plot area ===
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange('xy', True)
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.setLabel('left', 'Amplitude', units='mV')
        

        main_layout.addWidget(self.plot_widget)
        self.setLayout(main_layout)

    # === FUNCTIONS ===

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select EKG File", "", "CSV/TXT/NPY (*.csv *.txt *.npy)"
        )
        if not path:
            return

        try:
            self.processor.load_data(path)
            self.data = self.processor.raw_data

            self.label.setText(f"Loaded file: {path.split('/')[-1]}")
            self.analyze_btn.setEnabled(True)
            self.clinical_btn.setEnabled(True)

            # Compute x-axis as time (seconds)
            fs = self.processor.sampling_rate
            time_axis = np.arange(len(self.data)) / fs

            # Plot raw signal
            self.plot_widget.clear()
            self.plot_widget.plot(time_axis, self.data, pen='b', name="Raw EKG")

        except Exception as e:
            self.label.setText(f" Failed to load file: {e}")
            self.analyze_btn.setEnabled(False)

    def analyze_signal(self):
        try:
            self.processor.filter_signal()
            self.processor.detect_r_peaks()

            rr = self.processor.peaks[1:] - self.processor.peaks[:-1]
            waveforms = self.processor.segment_waveforms()

            report = self.detector.generate_report(rr, waveforms, self.processor.peaks)

            bpm = report['mean_heart_rate']
            arr = report['arrhythmias_detected']

            self.label.setText(f" HR: {bpm:.1f} BPM | Arrhythmias: {arr}")

            # Plot filtered signal + peaks
            self.plot_widget.clear()
            fs = self.processor.sampling_rate
            time_axis = np.arange(len(self.processor.filtered_data)) / fs

            self.plot_widget.plot(time_axis, self.processor.filtered_data, pen='b', name="Filtered EKG")
            self.plot_widget.plot(
                self.processor.peaks / fs,
                self.processor.filtered_data[self.processor.peaks],
                pen=None,
                symbol='o',
                symbolBrush='r',
                name="R-peaks"
            )

        except Exception as e:
            self.label.setText(f"Error: {e}")

    def show_clinical_view(self):
        if self.data is None:
            self.label.setText("⚠️ Please load a file first.")
            return

        try:
            plot_clinical_ecg(self.data, fs=1000, seconds=10)
        except Exception as e:
            self.label.setText(f"Error showing clinical view: {e}")


if __name__ == "__main__":
    app = QApplication([])
    ui = EKGApp()
    ui.show()
    app.exec()
