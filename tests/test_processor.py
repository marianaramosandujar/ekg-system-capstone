"""Tests for EKG processor module."""

import unittest
import numpy as np
from ekg_system.processor import EKGProcessor


class TestEKGProcessor(unittest.TestCase):
    """Test cases for EKGProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = EKGProcessor(sampling_rate=1000)
        
        # Generate synthetic EKG-like signal
        duration = 5  # seconds
        samples = duration * 1000
        t = np.linspace(0, duration, samples)
        
        # Simulate heart rate of 600 BPM (10 Hz)
        self.synthetic_data = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(samples)
        
    def test_load_data(self):
        """Test loading data."""
        self.processor.load_data(self.synthetic_data)
        self.assertIsNotNone(self.processor.data)
        self.assertEqual(len(self.processor.data), len(self.synthetic_data))
        
    def test_filter_signal(self):
        """Test signal filtering."""
        self.processor.load_data(self.synthetic_data)
        filtered = self.processor.filter_signal()
        
        self.assertIsNotNone(filtered)
        self.assertEqual(len(filtered), len(self.synthetic_data))
        
    def test_detect_r_peaks(self):
        """Test R-peak detection."""
        self.processor.load_data(self.synthetic_data)
        self.processor.filter_signal()
        peaks = self.processor.detect_r_peaks()
        
        self.assertIsNotNone(peaks)
        self.assertGreater(len(peaks), 0)
        
    def test_calculate_heart_rate(self):
        """Test heart rate calculation."""
        self.processor.load_data(self.synthetic_data)
        self.processor.filter_signal()
        self.processor.detect_r_peaks()
        
        if len(self.processor.peaks) >= 2:
            hr_stats = self.processor.calculate_heart_rate()
            
            self.assertIn('mean', hr_stats)
            self.assertIn('std', hr_stats)
            self.assertIn('min', hr_stats)
            self.assertIn('max', hr_stats)
            self.assertGreater(hr_stats['mean'], 0)
        
    def test_segment_waveforms(self):
        """Test waveform segmentation."""
        self.processor.load_data(self.synthetic_data)
        self.processor.filter_signal()
        self.processor.detect_r_peaks()
        
        waveforms = self.processor.segment_waveforms(window_size=100)
        self.assertIsInstance(waveforms, list)
        
    def test_get_statistics(self):
        """Test statistics generation."""
        self.processor.load_data(self.synthetic_data)
        stats = self.processor.get_statistics()
        
        self.assertIn('duration_seconds', stats)
        self.assertIn('sampling_rate', stats)
        self.assertEqual(stats['sampling_rate'], 1000)


if __name__ == '__main__':
    unittest.main()
