# Quick Start Guide

Get started with the EKG System in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/mramosandujar/ekg-system.git
cd ekg-system

# Install dependencies
pip install -e .
```

## Basic Usage


### 1. Try the Demo

```bash
# Run the demonstration script
python examples/demo.py
```

This will showcase all features of the system with synthetic data.

### 2. Generate Sample Data

```bash
cd examples
python generate_sample_data.py
```

This creates sample EKG files you can use for testing.

### 3. Process Your First EKG File

```bash
# Process a sample file
ekg-system process examples/sample_ekg_normal.csv

# Process with visualization
ekg-system process examples/sample_ekg_normal.csv --visualize

# Process and save the session
ekg-system process examples/sample_ekg_normal.csv --save-session --session-name my_first_analysis
```

### 4. Analyze Arrhythmias

```bash
# Process file with arrhythmias and export report
ekg-system process examples/sample_ekg_arrhythmia.csv \
    --save-session \
    --session-name arrhythmia_test \
    --export-format html \
    --visualize
```

The HTML report will be saved in the `reports/` directory.

### 5. View Saved Sessions

```bash
# List all saved sessions
ekg-system list

# Export a session as JSON
ekg-system export sessions/my_session.pkl --format json
```

## Python API Quick Start

```python
from ekg_system import EKGProcessor, ArrhythmiaDetector
from ekg_system.visualizer import EKGVisualizer

# Load and process data
processor = EKGProcessor(sampling_rate=1000)
processor.load_from_file('ekg_data.csv')
processor.filter_signal()
processor.detect_r_peaks()

# Calculate heart rate
hr_stats = processor.calculate_heart_rate()
print(f"Mean HR: {hr_stats['mean']:.1f} BPM")

# Detect arrhythmias
detector = ArrhythmiaDetector(sampling_rate=1000)
waveforms = processor.segment_waveforms()
rr_intervals = processor.peaks[1:] - processor.peaks[:-1]
report = detector.generate_report(rr_intervals, waveforms, processor.peaks)

print(f"Arrhythmias detected: {report['arrhythmias_detected']}")

# Visualize
visualizer = EKGVisualizer(sampling_rate=1000)
visualizer.plot_signal(processor.filtered_data, processor.peaks)
```

## Live Data Acquisition

If you have a microcontroller connected:

```bash
# List available ports
ekg-system ports

# Record for 10 seconds
ekg-system live --port /dev/ttyUSB0 --duration 10 --visualize

# Record and save
ekg-system live --port COM3 --duration 30 --save-session --session-name live_recording
```

## Common Tasks

### Export Report in Different Formats

```bash
# Text report
ekg-system export sessions/my_session.pkl --format txt

# JSON report
ekg-system export sessions/my_session.pkl --format json

# CSV data export
ekg-system export sessions/my_session.pkl --format csv

# HTML report
ekg-system export sessions/my_session.pkl --format html
```

### Process Multiple Files

```bash
for file in data/*.csv; do
    ekg-system process "$file" --save-session --export-format json
done
```

### Custom Sampling Rate

```bash
# For data recorded at 500 Hz
ekg-system process my_data.csv --sampling-rate 500
```

## File Formats

The system supports:

- **CSV**: First column or 'ekg' column contains voltage readings
- **TXT**: One value per line
- **NPY**: NumPy binary format

Example CSV:
```csv
ekg
0.145
0.152
0.892
...
```

## Understanding Results

### Heart Rate
- Normal mouse HR: 400-700 BPM
- Tachycardia: > 700 BPM
- Bradycardia: < 400 BPM

### Arrhythmia Types
- **Tachycardia**: Elevated heart rate
- **Bradycardia**: Reduced heart rate
- **Irregular Rhythm**: Variable RR intervals
- **Premature Beat**: Early beat followed by pause
- **Pause/Block**: Unusually long RR interval

### Waveform Classifications
- **Normal**: Standard cardiac cycle
- **Wide QRS**: Prolonged ventricular depolarization
- **ST Elevation/Depression**: Myocardial issues
- **T-wave Inversion**: Repolarization abnormalities

## Next Steps

- Read the full [README](README.md) for detailed documentation
- Check out [CONTRIBUTING](CONTRIBUTING.md) to contribute
- See [examples/demo.py](examples/demo.py) for API usage examples
- Generate your own sample data with [examples/generate_sample_data.py](examples/generate_sample_data.py)

## Getting Help

- Check the [README](README.md) troubleshooting section
- Open an issue on GitHub
- Review existing issues for similar problems

## Tips

1. **Always visualize first** to verify data quality
2. **Save sessions** for later analysis
3. **Use appropriate sampling rate** for your data
4. **Check for noise** before processing
5. **Validate R-peak detection** visually

Happy analyzing! 🫀
