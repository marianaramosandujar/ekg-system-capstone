import matplotlib.pyplot as plt
import numpy as np

def plot_clinical_ecg(signal, fs=1000, seconds=10):
    t = np.arange(len(signal)) / fs

    fig, ax = plt.subplots(figsize=(14,4))
    ax.set_facecolor("#fffdfa")

    # ✅ Small 1mm grid (0.04s x 0.1mV)
    for x in np.arange(0, seconds, 0.04):
        ax.axvline(x, color="#ffcccc", linewidth=0.5)
    for y in np.arange(-2, 2, 0.1):
        ax.axhline(y, color="#ffcccc", linewidth=0.5)

    # ✅ Large 5mm grid (0.2s x 0.5mV)
    for x in np.arange(0, seconds, 0.2):
        ax.axvline(x, color="#ff6666", linewidth=1)
    for y in np.arange(-2, 2, 0.5):
        ax.axhline(y, color="#ff6666", linewidth=1)

    # ✅ Calibration pulse (1mV amplitude, 0.2s width)
    cal_x = [0,0,0.2,0.2,0]
    cal_y = [0,1,1,0,0]
    ax.plot(cal_x, cal_y, color="black", linewidth=2)

    # ✅ Plot ECG waveform
    ax.plot(t[:seconds*fs], signal[:seconds*fs], color="black", linewidth=1)

    # Formatting
    ax.set_xlim(0, seconds)
    ax.set_ylim(-2, 2)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.title("Clinical ECG View (25 mm/s, 10 mm/mV)")

    plt.show()
