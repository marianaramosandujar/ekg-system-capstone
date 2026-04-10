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


def style_ecg_plot(plot_widget):
    plot_widget.setBackground("w")

    axis_pen = pg.mkPen(color="black", width=2)
    plot_widget.getAxis("bottom").setPen(axis_pen)
    plot_widget.getAxis("left").setPen(axis_pen)

    plot_widget.getAxis("bottom").setTextPen("black")
    plot_widget.getAxis("left").setTextPen("black")

    plot_widget.showGrid(x=True, y=True, alpha=0.12)


class EKGApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EKG Analysis System")
        self.setGeometry(100, 100, 1200, 800)

        self.processor = EKGProcessor(sampling_rate=1000)
        self.detector = ArrhythmiaDetector(sampling_rate=1000)

        self.data = None
        self.last_bpm = None

        main_layout = QVBoxLayout(self)

        row = QHBoxLayout()

        self.live_btn = QPushButton("Live View")
        self.live_btn.setFixedSize(200, 50)
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

        self.label = QLabel("Load an EKG file or select Live View.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; padding: 8px;")
        main_layout.addWidget(self.label)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.setLabel("left", "Amplitude (mV)")
        style_ecg_plot(self.plot_widget)
        main_layout.addWidget(self.plot_widget)

        self.live_view = None
        self.clinical_view = None

        self.show_standard_view()

    def show_standard_view(self):
        if self.live_view:
            self.live_view.hide()

        if self.clinical_view:
            self.clinical_view.hide()

        self.plot_widget.show()
        self.label.show()

        if self.data is None:
            self.plot_widget.clear()
            return

        fs = self.processor.sampling_rate
        t = np.arange(len(self.data)) / fs

        self.plot_widget.clear()
        self.plot_widget.plot(
            t,
            self.data,
            pen=pg.mkPen(color="black", width=1.2)
        )

        style_ecg_plot(self.plot_widget)
        self.plot_widget.setXRange(0, min(10, len(self.data) / fs), padding=0)
        self.plot_widget.enableAutoRange(axis="y")

    def show_live_view(self):
        if self.clinical_view:
            self.clinical_view.hide()

        if self.live_view is None:
            self.live_view = LivePGView(
                parent=self,
                fs=1000,
                window_sec=10
            )
            self.layout().addWidget(self.live_view)

        self.plot_widget.hide()
        self.label.hide()
        self.live_view.show()

    def show_clinical_view(self):
        if self.data is None:
            return

        if self.live_view:
            self.live_view.hide()

        if self.clinical_view:
            self.clinical_view.setParent(None)
            self.clinical_view.deleteLater()

        signal_to_show = (
            self.processor.filtered_data
            if self.processor.filtered_data is not None
            else self.data
        )

        self.clinical_view = ClinicalPGView(
            parent=self,
            signal=signal_to_show,
            fs=self.processor.sampling_rate,
            window_sec=10
        )

        self.layout().addWidget(self.clinical_view)

        self.plot_widget.hide()
        self.label.hide()
        self.clinical_view.show()

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

            self.show_standard_view()

        except Exception as e:
            self.label.setText(f"Error: {e}")

    def analyze_signal(self):
        if self.data is None:
            return

        if self.live_view:
            self.live_view.hide()

        if self.clinical_view:
            self.clinical_view.hide()

        self.plot_widget.show()
        self.label.show()

        try:
            self.processor.filter_signal()
            peaks = self.processor.detect_r_peaks()

            if peaks is None or len(peaks) < 2:
                raise RuntimeError("Not enough peaks detected to calculate BPM")

            rr = peaks[1:] - peaks[:-1]
            waves = self.processor.segment_waveforms()

            report = self.detector.generate_report(rr, waves, peaks)

            self.last_bpm = report["mean_heart_rate"]
            arr = report["arrhythmias_detected"]

            self.label.setText(
                f"HR: {self.last_bpm:.1f} BPM | Arrhythmias: {arr} | Peaks: {len(peaks)}"
            )

            fs = self.processor.sampling_rate
            signal = self.processor.filtered_data
            t = np.arange(len(signal)) / fs
            display_signal = signal

            self.plot_widget.clear()

            self.plot_widget.plot(
                t,
                display_signal,
                pen=pg.mkPen(color="black", width=1.2)
            )

            self.plot_widget.plot(
                peaks / fs,
                display_signal[peaks],
                pen=None,
                symbol="o",
                symbolBrush="r",
                symbolPen="r",
                symbolSize=5
            )

            style_ecg_plot(self.plot_widget)
            self.plot_widget.setXRange(0, min(10, len(signal) / fs), padding=0)
            self.plot_widget.enableAutoRange(axis="y")

        except Exception as e:
            self.label.setText(f"Error analyzing: {e}")

    def reset_zoom(self):
        if self.clinical_view and self.clinical_view.isVisible():
            self.clinical_view.reset_view()

        elif self.live_view and self.live_view.isVisible():
            self.live_view.reset_view()

        elif self.processor.filtered_data is not None:
            fs = self.processor.sampling_rate
            self.plot_widget.setXRange(
                0,
                min(10, len(self.processor.filtered_data) / fs),
                padding=0
            )
            self.plot_widget.enableAutoRange(axis="y")

        elif self.data is not None:
            fs = self.processor.sampling_rate
            self.plot_widget.setXRange(
                0,
                min(10, len(self.data) / fs),
                padding=0
            )
            self.plot_widget.enableAutoRange(axis="y")

        else:
            self.plot_widget.enableAutoRange(x=True, y=True)
            self.plot_widget.autoRange()

    def closeEvent(self, event):
        if self.live_view:
            self.live_view.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    ui = EKGApp()
    ui.show()
    app.exec()