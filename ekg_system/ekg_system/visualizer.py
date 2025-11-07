"""Data visualization module for EKG signals."""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, List, Dict
import matplotlib.patches as mpatches


class EKGVisualizer:
    """Visualize EKG data and analysis results."""
    
    def __init__(self, sampling_rate: int = 1000):
        """
        Initialize visualizer.
        
        Args:
            sampling_rate: Sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
        
    def plot_signal(self, data: np.ndarray, 
                   peaks: Optional[np.ndarray] = None,
                   title: str = "EKG Signal",
                   show: bool = True,
                   save_path: Optional[str] = None) -> None:
        """
        Plot EKG signal with optional peak markers.
        
        Args:
            data: EKG signal data
            peaks: Optional array of peak indices
            title: Plot title
            show: Whether to display the plot
            save_path: Optional path to save figure
        """
        time_axis = np.arange(len(data)) / self.sampling_rate
        
        plt.figure(figsize=(12, 4))
        plt.plot(time_axis, data, 'b-', linewidth=0.5, label='EKG Signal')
        
        if peaks is not None:
            plt.plot(time_axis[peaks], data[peaks], 'ro', 
                    markersize=5, label='R-peaks')
        
        plt.xlabel('Time (seconds)')
        plt.ylabel('Amplitude (mV)')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            
        if show:
            plt.show()
        else:
            plt.close()
            
    def plot_heart_rate(self, rr_intervals: np.ndarray,
                       title: str = "Heart Rate Over Time",
                       show: bool = True,
                       save_path: Optional[str] = None) -> None:
        """
        Plot heart rate variability.
        
        Args:
            rr_intervals: Array of RR intervals in samples
            title: Plot title
            show: Whether to display the plot
            save_path: Optional path to save figure
        """
        heart_rates = 60.0 * self.sampling_rate / rr_intervals
        beat_times = np.cumsum(rr_intervals) / self.sampling_rate
        
        plt.figure(figsize=(12, 4))
        plt.plot(beat_times, heart_rates, 'b-', linewidth=1)
        plt.axhline(y=np.mean(heart_rates), color='r', linestyle='--', 
                   label=f'Mean: {np.mean(heart_rates):.1f} BPM')
        
        plt.xlabel('Time (seconds)')
        plt.ylabel('Heart Rate (BPM)')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            
        if show:
            plt.show()
        else:
            plt.close()
            
    def plot_waveforms(self, waveforms: List[np.ndarray],
                      labels: Optional[List[str]] = None,
                      max_waveforms: int = 10,
                      title: str = "EKG Waveforms",
                      show: bool = True,
                      save_path: Optional[str] = None) -> None:
        """
        Plot multiple EKG waveforms for comparison.
        
        Args:
            waveforms: List of waveform segments
            labels: Optional labels for each waveform
            max_waveforms: Maximum number of waveforms to display
            title: Plot title
            show: Whether to display the plot
            save_path: Optional path to save figure
        """
        n_plots = min(len(waveforms), max_waveforms)
        
        plt.figure(figsize=(12, 2 * n_plots))
        
        for i in range(n_plots):
            plt.subplot(n_plots, 1, i + 1)
            time_axis = np.arange(len(waveforms[i])) / self.sampling_rate * 1000  # ms
            plt.plot(time_axis, waveforms[i], 'b-', linewidth=1)
            
            label = labels[i] if labels and i < len(labels) else f"Beat {i+1}"
            plt.ylabel('Amplitude')
            plt.title(f"{label}")
            plt.grid(True, alpha=0.3)
            
        plt.xlabel('Time (ms)')
        plt.suptitle(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            
        if show:
            plt.show()
        else:
            plt.close()
            
    def plot_arrhythmia_summary(self, arrhythmia_report: Dict,
                               show: bool = True,
                               save_path: Optional[str] = None) -> None:
        """
        Create summary visualization of arrhythmia analysis.
        
        Args:
            arrhythmia_report: Report dictionary from ArrhythmiaDetector
            show: Whether to display the plot
            save_path: Optional path to save figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Heart rate statistics
        ax1 = axes[0, 0]
        hr_data = [
            arrhythmia_report['mean_heart_rate'],
            arrhythmia_report['min_heart_rate'],
            arrhythmia_report['max_heart_rate']
        ]
        ax1.bar(['Mean', 'Min', 'Max'], hr_data, color=['green', 'blue', 'red'])
        ax1.set_ylabel('Heart Rate (BPM)')
        ax1.set_title('Heart Rate Statistics')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Arrhythmia counts
        ax2 = axes[0, 1]
        arr_counts = arrhythmia_report.get('arrhythmia_counts', {})
        if arr_counts:
            ax2.bar(range(len(arr_counts)), list(arr_counts.values()))
            ax2.set_xticks(range(len(arr_counts)))
            ax2.set_xticklabels(list(arr_counts.keys()), rotation=45, ha='right')
            ax2.set_ylabel('Count')
            ax2.set_title('Arrhythmia Type Distribution')
        else:
            ax2.text(0.5, 0.5, 'No arrhythmias detected', 
                    ha='center', va='center', transform=ax2.transAxes)
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Summary metrics
        ax3 = axes[1, 0]
        ax3.axis('off')
        summary_text = f"""
        Total Beats: {arrhythmia_report['total_beats']}
        Mean HR: {arrhythmia_report['mean_heart_rate']:.1f} BPM
        HR Std: {arrhythmia_report['hr_std']:.1f} BPM
        Arrhythmias Detected: {arrhythmia_report['arrhythmias_detected']}
        Abnormal Waveforms: {arrhythmia_report['abnormal_waveforms']}
        """
        ax3.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                family='monospace')
        
        # Plot 4: Waveform classification
        ax4 = axes[1, 1]
        wf_details = arrhythmia_report.get('waveform_details', [])
        if wf_details:
            wf_types = {}
            for wf in wf_details:
                wf_type = wf['type']
                wf_types[wf_type] = wf_types.get(wf_type, 0) + 1
            
            ax4.pie(wf_types.values(), labels=wf_types.keys(), autopct='%1.1f%%')
            ax4.set_title('Abnormal Waveform Types')
        else:
            ax4.text(0.5, 0.5, 'All waveforms normal', 
                    ha='center', va='center', transform=ax4.transAxes)
        
        plt.suptitle('EKG Arrhythmia Analysis Summary', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            
        if show:
            plt.show()
        else:
            plt.close()
            
    def plot_live_data(self, data: np.ndarray, window_size: int = 5000) -> None:
        """
        Plot live streaming data (last N samples).
        
        Args:
            data: Current data buffer
            window_size: Number of recent samples to display
        """
        plt.clf()
        
        if len(data) > 0:
            display_data = data[-window_size:] if len(data) > window_size else data
            time_axis = np.arange(len(display_data)) / self.sampling_rate
            
            plt.plot(time_axis, display_data, 'b-', linewidth=0.5)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Amplitude (mV)')
            plt.title('Live EKG Data')
            plt.grid(True, alpha=0.3)
            
        plt.pause(0.01)
