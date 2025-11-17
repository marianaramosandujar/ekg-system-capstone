# This file handles the actual EKG signal processing step-by-step
# Used by the UI when you hit Analyze

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


class EKGProcessor:
    # holds the raw signal, filtered version, and detected peaks
    def __init__(self, sampling_rate: int = 1000):
        self.sampling_rate = sampling_rate
        self.raw_data = None
        self.filtered_data = None
        self.peaks = None

    def load_data(self, data_or_path):
        # loads data either from a filename or already-loaded numpy array
        import pandas as pd

        if isinstance(data_or_path, np.ndarray):
            self.raw_data = data_or_path
            return

        path = str(data_or_path)

        # faster loading for numpy saved files
        if path.endswith(".npy"):
            self.raw_data = np.load(path)
            return

        # csv/txt load using pandas (handles headers if present)
        try:
            df = pd.read_csv(path, comment="#")
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            if not numeric_cols:
                raise ValueError("No numeric columns found")

            # some datasets include time + amplitude → use the amplitude column
            if len(numeric_cols) >= 2:
                data = df[numeric_cols[1]].to_numpy(dtype=float)
            else:
                data = df[numeric_cols[0]].to_numpy(dtype=float)

            self.raw_data = data
            self.filtered_data = None
            self.peaks = None
            return

        except Exception:
            # fallback loader for messy csv/txt files
            try:
                data = np.genfromtxt(path, delimiter=",", comments="#", skip_header=1)
                if data.ndim > 1 and data.shape[1] >= 2:
                    data = data[:, 1]
                self.raw_data = data
            except Exception as err:
                raise RuntimeError(f"Failed to load file: {err}")

        self.filtered_data = None
        self.peaks = None

    # helper for making the filter coefficients
    def butter_bandpass(self, lowcut, highcut, order=4):
        nyquist = 0.5 * self.sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        return butter(order, [low, high], btype='band')

    def filter_signal(self, lowcut=1.0, highcut=100.0):
        # apply a bandpass filter to remove noise + baseline drift
        if self.raw_data is None:
            raise ValueError("No data loaded")

        b, a = self.butter_bandpass(lowcut, highcut)
        self.filtered_data = filtfilt(b, a, self.raw_data)

    def detect_r_peaks(self, height_factor=0.5, distance_ms=50):
        # basic peak picking using scipy's find_peaks
        if self.filtered_data is None:
            raise ValueError("Signal not filtered yet")

        distance_samples = int((distance_ms / 1000.0) * self.sampling_rate)
        threshold = np.max(self.filtered_data) * height_factor

        # returns peak indices where heart beats occur
        peaks, _ = find_peaks(
            self.filtered_data,
            height=threshold,
            distance=distance_samples
        )
        self.peaks = peaks
        return peaks

    def calculate_heart_rate(self):
        # uses time difference between peaks = RR intervals
        if self.peaks is None or len(self.peaks) < 2:
            raise ValueError("Not enough peaks")

        rr_intervals = np.diff(self.peaks) / self.sampling_rate
        heart_rates = 60.0 / rr_intervals  # convert seconds → bpm

        return {
            "mean": np.mean(heart_rates),
            "std": np.std(heart_rates),
            "min": np.min(heart_rates),
            "max": np.max(heart_rates)
        }

    def segment_waveforms(self, window_before=50, window_after=100):
        # extracts little windows around each beat to look for arrhythmias
        if self.peaks is None:
            raise ValueError("No peaks detected")

        waveforms = []
        for peak in self.peaks:
            start = max(0, peak - window_before)
            end = min(len(self.raw_data), peak + window_after)
            waveforms.append(self.raw_data[start:end])
        return waveforms
