import numpy as np
from scipy.signal import butter, filtfilt, find_peaks


class EKGProcessor:
    def __init__(self, sampling_rate: int = 1000):
        self.sampling_rate = sampling_rate
        self.raw_data = None
        self.filtered_data = None
        self.peaks = None

    def load_data(self, data_or_path):
        import pandas as pd
        import numpy as np

        if isinstance(data_or_path, np.ndarray):
            self.raw_data = data_or_path.astype(float)
            self.filtered_data = None
            self.peaks = None
            return

        path = str(data_or_path)

        if path.endswith(".npy"):
            self.raw_data = np.load(path).astype(float)
            self.filtered_data = None
            self.peaks = None
            return

        if path.endswith(".txt"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            values = []
            dash_count = 0
            data_started = False

            for line in lines:
                s = line.strip()
                if not s:
                    continue

                if s == "---":
                    dash_count += 1
                    if dash_count >= 2:
                        data_started = True
                    continue

                if not data_started:
                    continue

                try:
                    values.append(float(s))
                except ValueError:
                    continue

            if not values:
                raise RuntimeError("No numeric ECG samples found in TXT file")

            self.raw_data = np.array(values, dtype=float)
            self.filtered_data = None
            self.peaks = None
            return

        try:
            df = pd.read_csv(path, comment="#")
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

            if not numeric_cols:
                raise ValueError("No numeric columns found")

            if len(numeric_cols) >= 2:
                data = df[numeric_cols[1]].to_numpy(dtype=float)
            else:
                data = df[numeric_cols[0]].to_numpy(dtype=float)

            self.raw_data = data
            self.filtered_data = None
            self.peaks = None
            return

        except Exception:
            try:
                data = np.genfromtxt(path, delimiter=",", comments="#", skip_header=1)
                if data.ndim > 1 and data.shape[1] >= 2:
                    data = data[:, 1]
                self.raw_data = np.array(data, dtype=float)
            except Exception as err:
                raise RuntimeError(f"Failed to load file: {err}")

        self.filtered_data = None
        self.peaks = None

    def butter_bandpass(self, lowcut, highcut, order=4):
        nyquist = 0.5 * self.sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        return butter(order, [low, high], btype="band")

    def filter_signal(self, lowcut=1.0, highcut=100.0):
        if self.raw_data is None:
            raise ValueError("No data loaded")

        b, a = self.butter_bandpass(lowcut, highcut)
        self.filtered_data = filtfilt(b, a, self.raw_data)

    def detect_r_peaks(self, height_factor=1.2, distance_ms=80):
        if self.filtered_data is None:
            raise ValueError("Signal not filtered yet")

        signal = self.filtered_data.copy()

        limit = np.percentile(np.abs(signal), 99)
        signal[np.abs(signal) > limit] = 0

        if abs(np.min(signal)) > abs(np.max(signal)):
            signal = -signal

        signal_abs = np.abs(signal)
        threshold = np.mean(signal_abs) * height_factor
        distance_samples = int((distance_ms / 1000.0) * self.sampling_rate)

        peaks, _ = find_peaks(
            signal_abs,
            height=threshold,
            distance=distance_samples
        )

        self.peaks = peaks
        return peaks

    def calculate_heart_rate(self):
        if self.peaks is None or len(self.peaks) < 2:
            raise ValueError("Not enough peaks")

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
            raise ValueError("No peaks detected")

        waveforms = []
        for peak in self.peaks:
            start = max(0, peak - window_before)
            end = min(len(self.raw_data), peak + window_after)
            waveforms.append(self.raw_data[start:end])
        return waveforms