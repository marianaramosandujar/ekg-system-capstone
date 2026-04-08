# This file handles the actual EKG signal processing step-by-step
# Used by the UI when you hit Analyze

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
import warnings


class EKGProcessor:
    # holds the raw signal, filtered version, and detected peaks
    def __init__(self, sampling_rate: int = 1000):
        self.sampling_rate = sampling_rate
        self.raw_data = None
        self.filtered_data = None
        self.peaks = None
        self._filter_coefficients = None
        self._last_filter_params = None
        
    def load_data(self, data_or_path, chunk_size=10000):
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

        # csv/txt load using pandas with chunking for large files
        try:
            if path.endswith(".csv") and chunk_size:
                # Chunked loading for large CSV files
                chunks = pd.read_csv(path, comment="#", chunksize=chunk_size)
                data_chunks = []
                for chunk in chunks:
                    numeric_cols = chunk.select_dtypes(include=[np.number]).columns.tolist()
                    if not numeric_cols:
                        continue
                    
                    if len(numeric_cols) >= 2:
                        data_chunks.append(chunk[numeric_cols[1]].to_numpy(dtype=float))
                    else:
                        data_chunks.append(chunk[numeric_cols[0]].to_numpy(dtype=float))
                
                if data_chunks:
                    self.raw_data = np.concatenate(data_chunks)
                else:
                    raise ValueError("No numeric data found")
            else:
                # Standard loading for smaller files
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
        # Avoid invalid filter parameters
        if low <= 0 or high >= 1 or low >= high:
            low = max(0.001, low)
            high = min(0.999, high)
            if low >= high:
                high = low + 0.1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return butter(order, [low, high], btype='band')

    def filter_signal(self, lowcut=1.0, highcut=100.0):
        # apply a bandpass filter to remove noise + baseline drift
        if self.raw_data is None:
            raise ValueError("No data loaded")
        
        # Cache filter coefficients for performance
        current_params = (lowcut, highcut, 4)  # order is fixed at 4
        
        if (self._last_filter_params != current_params or 
            self._filter_coefficients is None):
            b, a = self.butter_bandpass(lowcut, highcut)
            self._filter_coefficients = (b, a)
            self._last_filter_params = current_params
        else:
            b, a = self._filter_coefficients
        
        # Process in chunks for large signals to save memory
        if len(self.raw_data) > 50000:
            chunk_size = 50000
            overlap = 1000
            filtered_chunks = []
            
            for i in range(0, len(self.raw_data), chunk_size - overlap):
                chunk = self.raw_data[i:i + chunk_size]
                filtered_chunk = filtfilt(b, a, chunk)
                if i > 0:
                    filtered_chunk = filtered_chunk[overlap:]
                filtered_chunks.append(filtered_chunk)
            
            self.filtered_data = np.concatenate(filtered_chunks)
        else:
            self.filtered_data = filtfilt(b, a, self.raw_data)

    def detect_r_peaks(self, height_factor=0.5, distance_ms=50):
        # basic peak picking using scipy's find_peaks
        if self.filtered_data is None:
            raise ValueError("Signal not filtered yet")

        distance_samples = int((distance_ms / 1000.0) * self.sampling_rate)
        threshold = np.max(self.filtered_data) * height_factor
        min_height = np.std(self.filtered_data) * 1.5

        # returns peak indices where heart beats occur
        peaks, properties = find_peaks(
            self.filtered_data,
            height=max(threshold, min_height),
            distance=distance_samples,
            prominence=np.std(self.filtered_data) * 0.3,
            wlen=int(self.sampling_rate * 0.1)
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