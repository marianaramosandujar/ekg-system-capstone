import numpy as np
from ekg_system.processor import EKGProcessor  # adjust if your path is different


def load_ground_truth_peaks(path):
    peaks = []
    data_started = False
    dash_count = 0

    with open(path, "r") as f:
        for line in f:
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
                peaks.append(int(s))
            except:
                continue

    return np.array(peaks)


def match_peaks(detected, truth, tolerance=10):
    detected = list(detected)
    truth = list(truth)

    matched = 0
    used = set()

    for t in truth:
        for i, d in enumerate(detected):
            if i in used:
                continue
            if abs(d - t) <= tolerance:
                matched += 1
                used.add(i)
                break

    return matched


def main():
    ecg_file = "r-peak test/electrography_Mouse_01.txt"
    peaks_file = "r-peak test/peaks_Mouse_01.txt"

    processor = EKGProcessor(sampling_rate=1000)

    processor.load_data(ecg_file)
    processor.filter_signal()
    detected_peaks = processor.detect_r_peaks()

    truth_peaks = load_ground_truth_peaks(peaks_file)

    # ---- Heart rate from ground truth ----
    rr_truth = np.diff(truth_peaks) / 1000.0
    expected_bpm = np.mean(60.0 / rr_truth)

    # ---- Heart rate from detected ----
    rr_detected = np.diff(detected_peaks) / 1000.0
    measured_bpm = np.mean(60.0 / rr_detected)

    percent_error = abs(measured_bpm - expected_bpm) / expected_bpm * 100

    # ---- Peak matching ----
    correct = match_peaks(detected_peaks, truth_peaks)
    accuracy = (correct / len(truth_peaks)) * 100

    # ---- Results ----
    print("EXPECTED BPM:", round(expected_bpm, 2))
    print("MEASURED BPM:", round(measured_bpm, 2))
    print("ERROR (%):", round(percent_error, 2))
    print("PEAK ACCURACY (%):", round(accuracy, 2))

    # ---- Pass / Fail ----
    if percent_error <= 5 and accuracy >= 90:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")


if __name__ == "__main__":
    main()