import numpy as np
import matplotlib.pyplot as plt


def plot_clinical_ecg(signal, fs=1000, seconds=10):
    """
    Display a clinical-style ECG plot with proper grid and interactive zoom/pan.
    - 25 mm/s paper speed
    - 10 mm/mV amplitude scale
    """
    # Compute time axis (in seconds)
    n_samples = min(len(signal), fs * seconds)
    time = np.arange(n_samples) / fs
    signal = signal[:n_samples]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(time, signal, color='black', linewidth=1.0)
    ax.set_title("Clinical ECG View (25 mm/s, 10 mm/mV)", fontsize=14)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (mV)")

    # === GRID (clinical ECG paper style) ===
    # Major grid: 0.2 s horizontally, 0.5 mV vertically
    major_x = 0.2
    major_y = 0.5
    ax.set_xticks(np.arange(0, time[-1] + major_x, major_x))
    ax.set_yticks(np.arange(np.min(signal), np.max(signal) + major_y, major_y))
    ax.grid(which="major", color="red", linewidth=0.8, alpha=0.4)

    # Minor grid: 0.04 s horizontally, 0.1 mV vertically
    minor_x = 0.04
    minor_y = 0.1
    ax.set_xticks(np.arange(0, time[-1] + minor_x, minor_x), minor=True)
    ax.set_yticks(np.arange(np.min(signal), np.max(signal) + minor_y, minor_y), minor=True)
    ax.grid(which="minor", color="red", linewidth=0.4, alpha=0.2)

    # === Enable zoom/pan toolbar ===
    plt.tight_layout()
    plt.show()
