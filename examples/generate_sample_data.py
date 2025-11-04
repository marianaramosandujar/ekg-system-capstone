#!/usr/bin/env python3
"""Generate synthetic EKG data for testing."""

import numpy as np
import matplotlib.pyplot as plt


def generate_synthetic_ekg(duration=10, sampling_rate=1000, heart_rate=600, 
                          noise_level=0.05, add_arrhythmia=True):
    """
    Generate synthetic EKG signal for mice.
    
    Args:
        duration: Duration in seconds
        sampling_rate: Sampling rate in Hz
        heart_rate: Base heart rate in BPM
        noise_level: Noise amplitude relative to signal
        add_arrhythmia: Whether to add arrhythmias
        
    Returns:
        time_axis, ekg_signal
    """
    samples = duration * sampling_rate
    t = np.linspace(0, duration, samples)
    
    # Convert heart rate to frequency
    hr_hz = heart_rate / 60.0
    
    # Generate basic signal with multiple harmonics for realistic waveform
    ekg = np.zeros(samples)
    
    # R-peak component (dominant)
    ekg += 1.0 * np.sin(2 * np.pi * hr_hz * t)
    
    # P-wave (small amplitude, phase shifted)
    ekg += 0.15 * np.sin(2 * np.pi * hr_hz * t - 0.3)
    
    # T-wave (medium amplitude, phase shifted)
    ekg += 0.3 * np.sin(2 * np.pi * hr_hz * t + 1.2)
    
    # Add some higher frequency components for QRS complex
    ekg += 0.1 * np.sin(2 * np.pi * hr_hz * 5 * t)
    
    # Baseline drift (low frequency)
    ekg += 0.1 * np.sin(2 * np.pi * 0.2 * t)
    
    # Add noise
    ekg += noise_level * np.random.randn(samples)
    
    if add_arrhythmia:
        # Add some premature beats (at 30% and 60% of duration)
        premature_indices = [int(0.3 * samples), int(0.6 * samples)]
        for idx in premature_indices:
            if idx < samples - 100:
                # Early beat
                ekg[idx:idx+50] += 0.5 * np.sin(np.linspace(0, 2*np.pi, 50))
        
        # Add a pause at 45% of duration
        pause_idx = int(0.45 * samples)
        pause_duration = int(0.15 * sampling_rate)  # 150 ms pause
        if pause_idx + pause_duration < samples:
            ekg[pause_idx:pause_idx+pause_duration] *= 0.3  # Reduced amplitude
        
        # Add tachycardia section (80-90% of recording)
        tachy_start = int(0.8 * samples)
        tachy_end = int(0.9 * samples)
        t_tachy = t[tachy_start:tachy_end] - t[tachy_start]
        fast_hr = 800 / 60.0  # 800 BPM
        ekg[tachy_start:tachy_end] = np.sin(2 * np.pi * fast_hr * t_tachy) + \
                                      0.3 * np.sin(2 * np.pi * fast_hr * t_tachy + 1.2)
    
    return t, ekg


def main():
    """Generate and save sample data."""
    print("Generating synthetic EKG data...")
    
    # Generate normal EKG
    t_normal, ekg_normal = generate_synthetic_ekg(
        duration=10, 
        heart_rate=600,
        add_arrhythmia=False
    )
    
    # Generate EKG with arrhythmias
    t_arrhythmia, ekg_arrhythmia = generate_synthetic_ekg(
        duration=15,
        heart_rate=600,
        add_arrhythmia=True
    )
    
    # Save data
    print("Saving data files...")
    np.savetxt('sample_ekg_normal.txt', ekg_normal)
    np.savetxt('sample_ekg_arrhythmia.txt', ekg_arrhythmia)
    np.save('sample_ekg_normal.npy', ekg_normal)
    np.save('sample_ekg_arrhythmia.npy', ekg_arrhythmia)
    
    # Save as CSV
    import pandas as pd
    pd.DataFrame({'ekg': ekg_normal}).to_csv('sample_ekg_normal.csv', index=False)
    pd.DataFrame({'ekg': ekg_arrhythmia}).to_csv('sample_ekg_arrhythmia.csv', index=False)
    
    # Plot and save visualization
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    axes[0].plot(t_normal, ekg_normal, 'b-', linewidth=0.5)
    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Amplitude (mV)')
    axes[0].set_title('Normal Sinus Rhythm (600 BPM)')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(t_arrhythmia, ekg_arrhythmia, 'r-', linewidth=0.5)
    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Amplitude (mV)')
    axes[1].set_title('EKG with Arrhythmias (Premature Beats, Pause, Tachycardia)')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('sample_ekg_data.png', dpi=150)
    print("Saved visualization: sample_ekg_data.png")
    
    print("\nGenerated files:")
    print("  - sample_ekg_normal.txt")
    print("  - sample_ekg_normal.csv")
    print("  - sample_ekg_normal.npy")
    print("  - sample_ekg_arrhythmia.txt")
    print("  - sample_ekg_arrhythmia.csv")
    print("  - sample_ekg_arrhythmia.npy")
    print("\nUse these files with: ekg-system process <filename>")


if __name__ == '__main__':
    main()
