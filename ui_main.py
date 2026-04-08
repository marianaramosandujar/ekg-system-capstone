import numpy as np
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel
)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg
import platform

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
    # main UI app
    def __init__(self):
        super().__init__()
        
        # macOS-specific optimizations
        if platform.system() == 'Darwin':
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        
        self.setWindowTitle("EKG Analysis System")
        self.setGeometry(100, 100, 1200, 800)

        self.processor = EKGProcessor(sampling_rate=1000)
        self.detector = ArrhythmiaDetector(sampling_rate=1000)
        self.data = None
        self.last_bpm = None
        self._analysis_pending = False

        main_layout = QVBoxLayout(self)

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

        self.label = QLabel("Welcome! Load an EKG file or click 'Live View' to start.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; padding: 8px;")
        main_layout.addWidget(self.label)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.setLabel("left", "Amplitude (mV)")
        style_ecg_plot(self.plot_widget)
        
        # Safe viewport update mode
        try:
            self.plot_widget.setViewportUpdateMode(pg.ViewportUpdateMode.FullViewportUpdate)
        except AttributeError:
            try:
                self.plot_widget.setViewportUpdateMode(3)
            except:
                pass
        
        main_layout.addWidget(self.plot_widget)

        # Lazy initialization - don't create views until needed
        self.live_view = None
        self.clinical_view = None

        # Show a blank/empty plot initially
        self._show_blank_plot()

    def _show_blank_plot(self):
        """Show a blank plot with a message"""
        self.plot_widget.clear()
        self.plot_widget.show()
        if self.live_view:
            self.live_view.hide()
        if self.clinical_view:
            self.clinical_view.hide()
        self.label.show()
        
        # Add a text item to the plot
        text = pg.TextItem("No data loaded. Click 'Load EKG File' to begin.", anchor=(0.5, 0.5))
        text.setPos(0.5, 0.5)
        self.plot_widget.addItem(text)
        
    def reset_zoom(self):
        if self.clinical_view and self.clinical_view.isVisible():
            self.clinical_view.reset_view()
        elif self.live_view and self.live_view.isVisible():
            self.live_view.reset_view()
        elif self.plot_widget.isVisible():
            self.plot_widget.enableAutoRange(x=True, y=True)
            self.plot_widget.autoRange()

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select EKG File", "", "CSV/TXT/NPY (*.csv *.txt *.npy)"
        )
        if not path:
            return

        try:
            # Use QTimer to prevent UI freezing during load
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # Process in steps to keep UI responsive
            def do_load():
                self.processor.load_data(path)
                self.data = self.processor.raw_data
                self.last_bpm = None

                filename = path.split("/")[-1]
                self.label.setText(f"Loaded: {filename} ({len(self.data)} samples)")

                self.analyze_btn.setEnabled(True)
                self.clinical_btn.setEnabled(True)

                if self.clinical_view:
                    self.clinical_view.setParent(None)
                    self.clinical_view = None

                self.show_standard_view()
                QApplication.restoreOverrideCursor()
            
            QTimer.singleShot(10, do_load)
            
        except Exception as e:
            self.label.setText(f"Error: {e}")
            QApplication.restoreOverrideCursor()

    def show_standard_view(self):
        # Clean up live view if it exists
        self._cleanup_live_view()
        
        if self.clinical_view:
            self.clinical_view.hide()
        self.plot_widget.show()
        self.label.show()

        if self.data is None:
            self._show_blank_plot()
            return

        # Downsample for display if needed
        max_display_points = 50000
        if len(self.data) > max_display_points:
            step = len(self.data) // max_display_points
            display_data = self.data[::step]
            fs = self.processor.sampling_rate
            t = np.arange(len(display_data)) * step / fs
        else:
            display_data = self.data
            fs = self.processor.sampling_rate
            t = np.arange(len(display_data)) / fs

        self.plot_widget.clear()
        self.plot_widget.plot(
            t,
            display_data,
            pen=pg.mkPen(color="black", width=1.5)
        )
        style_ecg_plot(self.plot_widget)

    def analyze_signal(self):
        if self.data is None or self._analysis_pending:
            return
        
        # Use QTimer to prevent UI freezing
        self._analysis_pending = True
        QTimer.singleShot(10, self._do_analysis)

    def _do_analysis(self):
        """Actual analysis work done in separate call to prevent UI freezing"""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # Clean up live view before analysis
            self._cleanup_live_view()
            
            if self.clinical_view:
                self.clinical_view.hide()

            self.plot_widget.show()
            self.label.show()

            # Process in chunks for large datasets
            if len(self.data) > 100000:
                self.label.setText("Filtering large signal...")
                QApplication.processEvents()
            
            self.processor.filter_signal()
            
            if len(self.data) > 100000:
                self.label.setText("Detecting peaks...")
                QApplication.processEvents()
                
            self.processor.detect_r_peaks()

            if len(self.processor.peaks) < 2:
                self.label.setText("Error: Not enough peaks detected")
                return

            rr = self.processor.peaks[1:] - self.processor.peaks[:-1]
            waves = self.processor.segment_waveforms()
            report = self.detector.generate_report(
                rr, waves, self.processor.peaks
            )

            self.last_bpm = report["mean_heart_rate"]
            arr = report["arrhythmias_detected"]

            self.label.setText(
                f"HR: {self.last_bpm:.1f} BPM | Arrhythmias: {arr} | Beats: {len(self.processor.peaks)}"
            )

            # Downsample for display
            max_display_points = 50000
            filtered = self.processor.filtered_data
            if len(filtered) > max_display_points:
                step = len(filtered) // max_display_points
                display_filtered = filtered[::step]
                peaks_display = self.processor.peaks // step
                fs = self.processor.sampling_rate
                t = np.arange(len(display_filtered)) * step / fs
            else:
                display_filtered = filtered
                peaks_display = self.processor.peaks
                fs = self.processor.sampling_rate
                t = np.arange(len(display_filtered)) / fs

            self.plot_widget.clear()
            self.plot_widget.plot(
                t,
                display_filtered,
                pen=pg.mkPen(color="black", width=1.5)
            )

            if len(peaks_display) > 0 and peaks_display[0] < len(display_filtered):
                valid_peaks = peaks_display[peaks_display < len(display_filtered)]
                if len(valid_peaks) > 0:
                    self.plot_widget.plot(
                        valid_peaks / fs,
                        display_filtered[valid_peaks],
                        pen=None,
                        symbol="o",
                        symbolBrush="r",
                        symbolSize=6
                    )

            style_ecg_plot(self.plot_widget)

        except Exception as e:
            self.label.setText(f"Error analyzing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            QApplication.restoreOverrideCursor()
            self._analysis_pending = False

    # -----------------------------------------
    # Clinical View
    # -----------------------------------------
    def show_clinical_view(self):
        if self.data is None:
            self.label.setText("Please load a file first")
            return

        # Clean up live view before showing clinical view
        self._cleanup_live_view()
        
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
    # Live View - With Proper Cleanup
    # -----------------------------------------
    def show_live_view(self):
        if self.clinical_view:
            self.clinical_view.hide()
        
        self.plot_widget.hide()
        self.label.hide()

        # Clean up existing live view if it exists
        self._cleanup_live_view()
        
        # Create fresh live view
        self._create_live_view()

    def _create_live_view(self):
        """Create the live view widget (called lazily)"""
        try:
            self.live_view = LivePGView(
                parent=self,
                fs=1000,
                window_sec=10
            )
            self.layout().addWidget(self.live_view)
            self.label.hide()
            self.live_view.show()
        except Exception as e:
            self.label.show()
            self.label.setText(f"Error creating live view: {e}")
            self.plot_widget.show()

    def _cleanup_live_view(self):
        """Properly cleanup and destroy live view to free resources"""
        if self.live_view is not None:
            # Stop all timers and hardware
            self.live_view.stop()
            
            # Remove from layout
            self.layout().removeWidget(self.live_view)
            
            # Delete the widget
            self.live_view.deleteLater()
            
            # Process events to ensure cleanup happens
            QApplication.processEvents()
            
            self.live_view = None

    def closeEvent(self, event):
        self._cleanup_live_view()
        if self.clinical_view:
            self.clinical_view.deleteLater()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    
    # Set application style for better performance
    app.setStyle('Fusion')
    
    ui = EKGApp()
    ui.show()
    app.exec()