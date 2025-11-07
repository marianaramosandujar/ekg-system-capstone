"""Arrhythmia detection and waveform classification module."""

import numpy as np
from typing import Dict, List, Tuple
from enum import Enum


class ArrhythmiaType(Enum):
    """Types of arrhythmias that can be detected."""
    NORMAL = "Normal Sinus Rhythm"
    TACHYCARDIA = "Tachycardia"
    BRADYCARDIA = "Bradycardia"
    IRREGULAR = "Irregular Rhythm"
    PREMATURE_BEAT = "Premature Beat"
    PAUSE = "Pause/Block"


class WaveformType(Enum):
    """Types of EKG waveforms."""
    NORMAL = "Normal"
    WIDE_QRS = "Wide QRS"
    ELEVATED_ST = "ST Elevation"
    DEPRESSED_ST = "ST Depression"
    INVERTED_T = "T-wave Inversion"


class ArrhythmiaDetector:
    """Detect and classify arrhythmias in EKG data."""
    
    def __init__(self, sampling_rate: int = 1000):
        """
        Initialize arrhythmia detector.
        
        Args:
            sampling_rate: Sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
        # Typical mouse heart rate ranges (BPM)
        self.normal_hr_range = (400, 700)
        self.tachycardia_threshold = 700
        self.bradycardia_threshold = 400
        
    def analyze_rhythm(self, rr_intervals: np.ndarray) -> List[Tuple[ArrhythmiaType, int, str]]:
        """
        Analyze heart rhythm and detect arrhythmias.
        
        Args:
            rr_intervals: Array of RR intervals in samples
            
        Returns:
            List of tuples (arrhythmia_type, index, description)
        """
        arrhythmias = []
        
        # Convert RR intervals to heart rates
        heart_rates = 60.0 * self.sampling_rate / rr_intervals
        
        # Calculate variability metrics
        rr_mean = np.mean(rr_intervals)
        rr_std = np.std(rr_intervals)
        
        for i, (rr, hr) in enumerate(zip(rr_intervals, heart_rates)):
            # Check for tachycardia
            if hr > self.tachycardia_threshold:
                arrhythmias.append((
                    ArrhythmiaType.TACHYCARDIA,
                    i,
                    f"Heart rate: {hr:.1f} BPM (elevated)"
                ))
                
            # Check for bradycardia
            elif hr < self.bradycardia_threshold:
                arrhythmias.append((
                    ArrhythmiaType.BRADYCARDIA,
                    i,
                    f"Heart rate: {hr:.1f} BPM (reduced)"
                ))
                
            # Check for irregular beats (RR interval varies significantly)
            if abs(rr - rr_mean) > 2 * rr_std:
                arrhythmias.append((
                    ArrhythmiaType.IRREGULAR,
                    i,
                    f"RR interval deviation: {abs(rr - rr_mean) / rr_std:.2f} SD"
                ))
                
            # Check for premature beats (short RR interval followed by compensatory pause)
            if i < len(rr_intervals) - 1:
                if rr < 0.7 * rr_mean and rr_intervals[i + 1] > 1.3 * rr_mean:
                    arrhythmias.append((
                        ArrhythmiaType.PREMATURE_BEAT,
                        i,
                        "Premature beat detected with compensatory pause"
                    ))
                    
            # Check for pauses/blocks (unusually long RR interval)
            if rr > 1.5 * rr_mean:
                arrhythmias.append((
                    ArrhythmiaType.PAUSE,
                    i,
                    f"Pause detected: {rr / self.sampling_rate * 1000:.1f} ms"
                ))
                
        return arrhythmias
        
    def classify_waveform(self, waveform: np.ndarray, peak_idx: int) -> WaveformType:
        """
        Classify individual waveform characteristics.
        
        Args:
            waveform: EKG waveform segment
            peak_idx: Index of R-peak within waveform
            
        Returns:
            Waveform classification
        """
        if len(waveform) < peak_idx + 50:
            return WaveformType.NORMAL
            
        # Analyze QRS complex width (samples around R-peak)
        qrs_start = max(0, peak_idx - 30)
        qrs_end = min(len(waveform), peak_idx + 30)
        qrs_width = qrs_end - qrs_start
        
        # Wide QRS: > 30ms for mice (30 samples at 1000 Hz)
        if qrs_width > 40:
            return WaveformType.WIDE_QRS
            
        # Analyze ST segment (immediately after QRS)
        st_start = peak_idx + 30
        st_end = min(len(waveform), peak_idx + 60)
        
        if st_end > st_start:
            st_segment = waveform[st_start:st_end]
            baseline = np.mean(waveform[:max(1, peak_idx - 50)])
            st_elevation = np.mean(st_segment) - baseline
            
            # Check for ST elevation or depression
            if st_elevation > 0.1 * np.max(waveform):
                return WaveformType.ELEVATED_ST
            elif st_elevation < -0.1 * np.max(waveform):
                return WaveformType.DEPRESSED_ST
                
        # Analyze T-wave (after ST segment)
        t_start = peak_idx + 60
        t_end = min(len(waveform), peak_idx + 120)
        
        if t_end > t_start:
            t_wave = waveform[t_start:t_end]
            # Inverted T-wave (negative deflection)
            if np.mean(t_wave) < -0.05 * np.max(waveform):
                return WaveformType.INVERTED_T
                
        return WaveformType.NORMAL
        
    def generate_report(self, rr_intervals: np.ndarray, 
                       waveforms: List[np.ndarray],
                       peaks: np.ndarray) -> Dict:
        """
        Generate comprehensive arrhythmia analysis report.
        
        Args:
            rr_intervals: Array of RR intervals in samples
            waveforms: List of waveform segments
            peaks: Array of peak indices
            
        Returns:
            Dictionary containing analysis results
        """
        # Detect arrhythmias
        arrhythmias = self.analyze_rhythm(rr_intervals)
        
        # Classify waveforms
        waveform_classifications = []
        window_size = len(waveforms[0]) // 2 if waveforms else 100
        
        for i, waveform in enumerate(waveforms):
            wf_type = self.classify_waveform(waveform, window_size)
            if wf_type != WaveformType.NORMAL:
                waveform_classifications.append((i, wf_type))
                
        # Calculate heart rate statistics
        heart_rates = 60.0 * self.sampling_rate / rr_intervals
        
        # Count arrhythmia types
        arrhythmia_counts = {}
        for arr_type, _, _ in arrhythmias:
            arrhythmia_counts[arr_type.value] = arrhythmia_counts.get(arr_type.value, 0) + 1
            
        report = {
            'total_beats': len(peaks),
            'mean_heart_rate': np.mean(heart_rates),
            'hr_std': np.std(heart_rates),
            'min_heart_rate': np.min(heart_rates),
            'max_heart_rate': np.max(heart_rates),
            'arrhythmias_detected': len(arrhythmias),
            'arrhythmia_counts': arrhythmia_counts,
            'arrhythmia_details': [
                {
                    'type': arr[0].value,
                    'beat_number': arr[1],
                    'description': arr[2]
                }
                for arr in arrhythmias
            ],
            'abnormal_waveforms': len(waveform_classifications),
            'waveform_details': [
                {
                    'beat_number': idx,
                    'type': wf_type.value
                }
                for idx, wf_type in waveform_classifications
            ]
        }
        
        return report
        
    def label_beats(self, peaks: np.ndarray, rr_intervals: np.ndarray) -> List[str]:
        """
        Generate labels for each detected beat.
        
        Args:
            peaks: Array of peak indices
            rr_intervals: Array of RR intervals
            
        Returns:
            List of labels for each beat
        """
        labels = ['Normal'] * len(peaks)
        arrhythmias = self.analyze_rhythm(rr_intervals)
        
        for arr_type, idx, _ in arrhythmias:
            if idx < len(labels):
                labels[idx] = arr_type.value
                
        return labels
