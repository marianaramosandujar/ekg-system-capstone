"""
EKG signal processor module.
"""

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


class EKGProcessor:
    def __init__(self, sampling_rate: int = 1000):
        """
        Initialize EKG processor.
        Args:
            sampling_rate: Sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
        self.raw_data = None
        self.filtered_data = None
        self.peaks = None

    def load_data(self, data_or_path):
        """
        Load EKG data from file path or numpy array.

        Supports:
        - .txt (1 or 2 columns)
        - .csv (1 or 2 columns with or without headers)
        - .npy
        - raw numpy array already in memory
        """
        import pandas as pd

        if isinstance(data_or_path, np.ndarray):
            self.raw_data = data_or_path
            return

        path = str(data_or_path)

        # --- .npy files ---
        if path.endswith(".npy"):
            self.raw_data = np.load(path)
            return

        # --- CSV or TXT ---
        try:
            # Try with pandas (handles headers automatically)
            df = pd.read_csv(path, comment="#")  # ignore comment lines if present
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            if not numeric_cols:
                raise ValueError("No numeric columns found in file.")

            # ✅ If two columns (time, amplitude), use second
            if len(numeric_cols) >= 2:
                data = df[numeric_cols[1]].to_numpy(dtype=float)
            else:
                data = df[numeric_cols[0]].to_numpy(dtype=float)

            self.raw_data = data
            self.filtered_data = None
            self.peaks = None
            return

        except Exception as e:
            # Fallback to numpy only if pandas fails
            try:
                data = np.genfromtxt(path, delimiter=",", comments="#", skip_header=1)
                if data.ndim > 1 and data.shape[1] >= 2:
                    data = data[:, 1]
                self.raw_data = data
            except Exception as err:
                raise RuntimeError(f"Failed to load file: {err}")

        # Reset pipeline
        self.filtered_data = None
        self.peaks = None

    def butter_bandpass(self, lowcut, highcut, order=4):
        nyquist = 0.5 * self.sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        return butter(order, [low, high], btype='band')

    def filter_signal(self, lowcut=1.0, highcut=100.0):
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        b, a = self.butter_bandpass(lowcut, highcut)
        self.filtered_data = filtfilt(b, a, self.raw_data)

    def detect_r_peaks(self, height_factor=0.5, distance_ms=50):
        if self.filtered_data is None:
            raise ValueError("Signal not filtered. Call filter_signal() first.")

        distance_samples = int((distance_ms / 1000.0) * self.sampling_rate)
        threshold = np.max(self.filtered_data) * height_factor

        peaks, _ = find_peaks(self.filtered_data, height=threshold, distance=distance_samples)
        self.peaks = peaks
        return peaks

    def calculate_heart_rate(self):
        if self.peaks is None or len(self.peaks) < 2:
            raise ValueError("Not enough peaks to calculate heart rate.")

        rr_intervals = np.diff(self.peaks) / self.sampling_rate
        heart_rates = 60.0 / rr_intervals

        return {
            "mean": np.mean(heart_rates),
            "std": np.std(heart_rates),
            "min": np.min(heart_rates),
            "max": np.max(heart_rates)
        }

    def segment_waveforms(self, window_before=50, window_after=100):
        if self.peaks is None:
            raise ValueError("No peaks detected.")

        waveforms = []
        for peak in self.peaks:
            start = max(0, peak - window_before)
            end = min(len(self.raw_data), peak + window_after)
            waveforms.append(self.raw_data[start:end])
        return waveforms
