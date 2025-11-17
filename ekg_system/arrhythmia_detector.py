# This file looks at RR intervals + waveform shape and tries to flag odd beats
# Used after Analyze button runs in the UI

import numpy as np
from typing import Dict, List, Tuple
from enum import Enum


class ArrhythmiaType(Enum):
    # general rhythm issues (based mostly on RR timing)
    NORMAL = "Normal Sinus Rhythm"
    TACHYCARDIA = "Tachycardia"
    BRADYCARDIA = "Bradycardia"
    IRREGULAR = "Irregular Rhythm"
    PREMATURE_BEAT = "Premature Beat"
    PAUSE = "Pause/Block"


class WaveformType(Enum):
    # waveform shape issues (ventricular or ST morphology changes)
    NORMAL = "Normal"
    WIDE_QRS = "Wide QRS"
    ELEVATED_ST = "ST Elevation"
    DEPRESSED_ST = "ST Depression"
    INVERTED_T = "T-wave Inversion"


class ArrhythmiaDetector:
    # simple arrhythmia rule checks tuned for mice (fast HR)
    def __init__(self, sampling_rate: int = 1000):
        self.sampling_rate = sampling_rate
        # mice beat way faster than humans — rough expected range
        self.normal_hr_range = (400, 700)
        self.tachycardia_threshold = 700
        self.bradycardia_threshold = 400
        
    def analyze_rhythm(self, rr_intervals: np.ndarray) -> List[Tuple[ArrhythmiaType, int, str]]:
        # checks beat-to-beat timing differences
        arrhythmias = []
        
        heart_rates = 60.0 * self.sampling_rate / rr_intervals

        rr_mean = np.mean(rr_intervals)
        rr_std = np.std(rr_intervals)
        
        for i, (rr, hr) in enumerate(zip(rr_intervals, heart_rates)):
            
            # faster than usual → tachycardia
            if hr > self.tachycardia_threshold:
                arrhythmias.append((
                    ArrhythmiaType.TACHYCARDIA,
                    i,
                    f"Heart rate: {hr:.1f} BPM (elevated)"
                ))
            
            # slower → bradycardia
            elif hr < self.bradycardia_threshold:
                arrhythmias.append((
                    ArrhythmiaType.BRADYCARDIA,
                    i,
                    f"Heart rate: {hr:.1f} BPM (reduced)"
                ))

            # really different timing from others → irregular
            if abs(rr - rr_mean) > 2 * rr_std:
                arrhythmias.append((
                    ArrhythmiaType.IRREGULAR,
                    i,
                    f"RR interval deviation: {abs(rr - rr_mean) / rr_std:.2f} SD"
                ))
            
            # quick beat followed by a long pause → premature beat pattern
            if i < len(rr_intervals) - 1:
                if rr < 0.7 * rr_mean and rr_intervals[i + 1] > 1.3 * rr_mean:
                    arrhythmias.append((
                        ArrhythmiaType.PREMATURE_BEAT,
                        i,
                        "Premature beat detected with compensatory pause"
                    ))
            
            # very long gap → possible conduction block
            if rr > 1.5 * rr_mean:
                arrhythmias.append((
                    ArrhythmiaType.PAUSE,
                    i,
                    f"Pause detected: {rr / self.sampling_rate * 1000:.1f} ms"
                ))
                
        return arrhythmias
        
    def classify_waveform(self, waveform: np.ndarray, peak_idx: int) -> WaveformType:
        # looks at shape near the R-peak: width, ST, T-wave
        if len(waveform) < peak_idx + 50:
            return WaveformType.NORMAL
            
        # width around R wave → wide QRS possibility
        qrs_start = max(0, peak_idx - 30)
        qrs_end = min(len(waveform), peak_idx + 30)
        qrs_width = qrs_end - qrs_start
        
        if qrs_width > 40:  # rough cutoff for mouse ECG
            return WaveformType.WIDE_QRS
            
        # ST segment amplitude shift
        st_start = peak_idx + 30
        st_end = min(len(waveform), peak_idx + 60)
        
        if st_end > st_start:
            st = waveform[st_start:st_end]
            baseline = np.mean(waveform[:max(1, peak_idx - 50)])
            st_shift = np.mean(st) - baseline
            
            if st_shift > 0.1 * np.max(waveform):
                return WaveformType.ELEVATED_ST
            elif st_shift < -0.1 * np.max(waveform):
                return WaveformType.DEPRESSED_ST
        
        # check if T-wave flips negative
        t_start = peak_idx + 60
        t_end = min(len(waveform), peak_idx + 120)
        
        if t_end > t_start:
            t = waveform[t_start:t_end]
            if np.mean(t) < -0.05 * np.max(waveform):
                return WaveformType.INVERTED_T
                
        return WaveformType.NORMAL
        
    def generate_report(self, rr_intervals: np.ndarray, waveforms: List[np.ndarray], peaks: np.ndarray) -> Dict:
        # bundles timing + waveform results into one report
        arrhythmias = self.analyze_rhythm(rr_intervals)
        
        # classify any unusual shapes
        waveform_classifications = []
        window_size = len(waveforms[0]) // 2 if waveforms else 100
        
        for i, wf in enumerate(waveforms):
            wf_type = self.classify_waveform(wf, window_size)
            if wf_type != WaveformType.NORMAL:
                waveform_classifications.append((i, wf_type))

        heart_rates = 60.0 * self.sampling_rate / rr_intervals
        
        # count how often each rhythm issue shows up
        arrhythmia_counts = {}
        for arr_type, _, _ in arrhythmias:
            arrhythmia_counts[arr_type.value] = arrhythmia_counts.get(arr_type.value, 0) + 1
            
        # build UI-friendly result dictionary
        return {
            "total_beats": len(peaks),
            "mean_heart_rate": np.mean(heart_rates),
            "hr_std": np.std(heart_rates),
            "min_heart_rate": np.min(heart_rates),
            "max_heart_rate": np.max(heart_rates),
            "arrhythmias_detected": len(arrhythmias),
            "arrhythmia_counts": arrhythmia_counts,
            "arrhythmia_details": [
                {"type": a[0].value, "beat_number": a[1], "description": a[2]}
                for a in arrhythmias
            ],
            "abnormal_waveforms": len(waveform_classifications),
            "waveform_details": [
                {"beat_number": idx, "type": wf.value}
                for idx, wf in waveform_classifications
            ]
        }
        
    def label_beats(self, peaks: np.ndarray, rr_intervals: np.ndarray) -> List[str]:
        # returns a simple string label per beat (helps for debugging/plots)
        labels = ["Normal"] * len(peaks)
        arrhythmias = self.analyze_rhythm(rr_intervals)
        
        for arr_type, idx, _ in arrhythmias:
            if idx < len(labels):
                labels[idx] = arr_type.value
                
        return labels
