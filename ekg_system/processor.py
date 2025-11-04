"""EKG data processing module."""

import numpy as np
from scipy import signal
from typing import Dict, List, Optional, Tuple


class EKGProcessor:
    """Process and analyze EKG data for mice."""
    
    def __init__(self, sampling_rate: int = 1000):
        """
        Initialize EKG processor.
        
        Args:
            sampling_rate: Sampling rate in Hz (default: 1000 Hz for mice)
        """
        self.sampling_rate = sampling_rate
        self.data = None
        self.filtered_data = None
        self.peaks = None
        self.heart_rate = None
        
    def load_data(self, data: np.ndarray) -> None:
        """
        Load EKG data for processing.
        
        Args:
            data: 1D numpy array of EKG voltage readings
        """
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        self.data = data
        
    def load_from_file(self, filepath: str) -> None:
        """
        Load EKG data from a file.
        
        Args:
            filepath: Path to data file (supports .txt, .csv, .npy)
        """
        if filepath.endswith('.npy'):
            self.data = np.load(filepath)
        elif filepath.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(filepath)
            # Assume first column or 'ekg' column contains EKG data
            if 'ekg' in df.columns:
                self.data = df['ekg'].values
            else:
                self.data = df.iloc[:, 0].values
        else:
            # Assume text file with one value per line
            self.data = np.loadtxt(filepath)
            
    def filter_signal(self, lowcut: float = 0.5, highcut: float = 100.0) -> np.ndarray:
        """
        Apply bandpass filter to remove noise.
        
        Args:
            lowcut: Low frequency cutoff in Hz
            highcut: High frequency cutoff in Hz
            
        Returns:
            Filtered EKG signal
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
            
        nyquist = self.sampling_rate / 2
        low = lowcut / nyquist
        high = highcut / nyquist
        
        # Design Butterworth bandpass filter
        b, a = signal.butter(4, [low, high], btype='band')
        self.filtered_data = signal.filtfilt(b, a, self.data)
        
        return self.filtered_data
        
    def detect_r_peaks(self, height_threshold: Optional[float] = None, 
                       distance: Optional[int] = None) -> np.ndarray:
        """
        Detect R-peaks in the EKG signal.
        
        Args:
            height_threshold: Minimum peak height (auto if None)
            distance: Minimum distance between peaks in samples (auto if None)
            
        Returns:
            Array of peak indices
        """
        if self.filtered_data is None:
            self.filter_signal()
            
        # Auto-calculate threshold if not provided
        if height_threshold is None:
            height_threshold = np.mean(self.filtered_data) + 0.5 * np.std(self.filtered_data)
            
        # Auto-calculate minimum distance (typical mouse HR: 300-800 bpm)
        if distance is None:
            # Minimum distance based on maximum expected heart rate (800 bpm)
            distance = int(self.sampling_rate * 60 / 800 * 0.6)
            
        self.peaks, _ = signal.find_peaks(
            self.filtered_data,
            height=height_threshold,
            distance=distance
        )
        
        return self.peaks
        
    def calculate_heart_rate(self) -> Dict[str, float]:
        """
        Calculate heart rate statistics from detected peaks.
        
        Returns:
            Dictionary with mean, std, min, max heart rate in BPM
        """
        if self.peaks is None:
            self.detect_r_peaks()
            
        if len(self.peaks) < 2:
            raise ValueError("Not enough peaks detected to calculate heart rate")
            
        # Calculate RR intervals (time between consecutive R-peaks)
        rr_intervals = np.diff(self.peaks) / self.sampling_rate  # in seconds
        
        # Calculate instantaneous heart rates
        heart_rates = 60.0 / rr_intervals  # in BPM
        
        self.heart_rate = {
            'mean': np.mean(heart_rates),
            'std': np.std(heart_rates),
            'min': np.min(heart_rates),
            'max': np.max(heart_rates)
        }
        
        return self.heart_rate
        
    def segment_waveforms(self, window_size: int = 200) -> List[np.ndarray]:
        """
        Extract individual heartbeat waveforms centered on R-peaks.
        
        Args:
            window_size: Number of samples before and after R-peak
            
        Returns:
            List of waveform segments
        """
        if self.peaks is None:
            self.detect_r_peaks()
            
        waveforms = []
        for peak in self.peaks:
            start = max(0, peak - window_size)
            end = min(len(self.filtered_data), peak + window_size)
            
            # Only include complete waveforms
            if end - start == 2 * window_size:
                waveforms.append(self.filtered_data[start:end])
                
        return waveforms
        
    def get_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive statistics of the EKG recording.
        
        Returns:
            Dictionary containing various statistics
        """
        stats = {
            'duration_seconds': len(self.data) / self.sampling_rate if self.data is not None else 0,
            'sampling_rate': self.sampling_rate,
            'num_peaks': len(self.peaks) if self.peaks is not None else 0,
        }
        
        if self.heart_rate is not None:
            stats.update(self.heart_rate)
            
        return stats
