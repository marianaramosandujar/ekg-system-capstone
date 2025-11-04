"""Tests for arrhythmia detector module."""

import unittest
import numpy as np
from ekg_system.arrhythmia_detector import ArrhythmiaDetector, ArrhythmiaType, WaveformType


class TestArrhythmiaDetector(unittest.TestCase):
    """Test cases for ArrhythmiaDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = ArrhythmiaDetector(sampling_rate=1000)
        
        # Generate synthetic RR intervals (normal rhythm ~600 BPM)
        self.normal_rr = np.full(50, 100)  # 100 samples = 100ms at 1000 Hz
        
        # RR intervals with tachycardia
        self.tachy_rr = np.full(50, 70)  # Faster rate
        
        # RR intervals with bradycardia
        self.brady_rr = np.full(50, 200)  # Slower rate
        
        # Irregular rhythm - more significant variation
        self.irregular_rr = np.array([100, 150, 60, 120, 80, 160] * 8)
        
    def test_analyze_normal_rhythm(self):
        """Test analysis of normal rhythm."""
        arrhythmias = self.detector.analyze_rhythm(self.normal_rr)
        self.assertIsInstance(arrhythmias, list)
        
    def test_analyze_tachycardia(self):
        """Test detection of tachycardia."""
        arrhythmias = self.detector.analyze_rhythm(self.tachy_rr)
        
        # Should detect elevated heart rate
        has_tachy = any(arr[0] == ArrhythmiaType.TACHYCARDIA for arr in arrhythmias)
        self.assertTrue(has_tachy)
        
    def test_analyze_bradycardia(self):
        """Test detection of bradycardia."""
        arrhythmias = self.detector.analyze_rhythm(self.brady_rr)
        
        # Should detect reduced heart rate
        has_brady = any(arr[0] == ArrhythmiaType.BRADYCARDIA for arr in arrhythmias)
        self.assertTrue(has_brady)
        
    def test_analyze_irregular_rhythm(self):
        """Test detection of irregular rhythm."""
        arrhythmias = self.detector.analyze_rhythm(self.irregular_rr)
        
        # Should detect some arrhythmias (irregular, premature, or pause)
        # Due to significant variation in RR intervals
        self.assertGreater(len(arrhythmias), 0, "Expected some arrhythmias in irregular rhythm")
        
    def test_classify_waveform(self):
        """Test waveform classification."""
        # Generate synthetic waveform
        waveform = np.sin(np.linspace(0, 2*np.pi, 200))
        peak_idx = 100
        
        wf_type = self.detector.classify_waveform(waveform, peak_idx)
        self.assertIsInstance(wf_type, WaveformType)
        
    def test_generate_report(self):
        """Test report generation."""
        # Create synthetic data
        peaks = np.array([100, 200, 300, 400, 500])
        waveforms = [np.sin(np.linspace(0, 2*np.pi, 200)) for _ in range(4)]
        rr_intervals = np.diff(peaks)
        
        report = self.detector.generate_report(rr_intervals, waveforms, peaks)
        
        self.assertIn('total_beats', report)
        self.assertIn('mean_heart_rate', report)
        self.assertIn('arrhythmias_detected', report)
        self.assertIn('abnormal_waveforms', report)
        
    def test_label_beats(self):
        """Test beat labeling."""
        peaks = np.array([100, 200, 300, 400, 500])
        rr_intervals = np.diff(peaks)
        
        labels = self.detector.label_beats(peaks, rr_intervals)
        
        self.assertEqual(len(labels), len(peaks))
        self.assertIsInstance(labels[0], str)


if __name__ == '__main__':
    unittest.main()
