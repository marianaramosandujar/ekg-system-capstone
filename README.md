# EKG System - Mouse Cardiac Data Analysis

A comprehensive Python application for processing and analyzing EKG (electrocardiogram) data from mice. This system provides automated arrhythmia detection, waveform classification, live data acquisition from microcontrollers, and session management with report generation.

## Features

- **EKG Data Processing**: Load and filter EKG signals with customizable parameters
- **Arrhythmia Detection**: Automatically identify and label different arrhythmia types:
  - Tachycardia
  - Bradycardia
  - Irregular rhythms
  - Premature beats
  - Pauses/blocks
- **Waveform Classification**: Classify individual heartbeat waveforms:
  - Normal sinus rhythm
  - Wide QRS complex
  - ST elevation/depression
  - T-wave inversion
- **Microcontroller Integration**: Optional live data acquisition via serial connection
- **Data Visualization**: Generate plots for EKG signals, heart rate, and analysis results
- **Session Management**: Save and load processed sessions
- **Report Export**: Export analysis reports in multiple formats (TXT, JSON, CSV, HTML)
- **Command-line Interface**: Easy-to-use CLI for all operations

## Installation

### Requirements

- Python 3.7 or higher
- pip

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/mramosandujar/ekg-system.git
cd ekg-system

# Install the package and dependencies
pip install -e .

# Or install requirements separately
pip install -r requirements.txt
```

## Usage

The EKG system provides a command-line interface with several commands:

### 1. Process EKG Data File

Process an existing EKG data file:

```bash
# Basic processing
ekg-system process data/ekg_recording.csv

# Process with visualization
ekg-system process data/ekg_recording.csv --visualize

# Process and save session
ekg-system process data/ekg_recording.csv --save-session --session-name my_mouse_001

# Process and export report
ekg-system process data/ekg_recording.csv --save-session --export-format html

# Custom sampling rate
ekg-system process data/ekg_recording.csv --sampling-rate 500
```

Supported file formats:
- `.npy` - NumPy binary format
- `.csv` - CSV file with EKG data in first column or 'ekg' column
- `.txt` - Text file with one value per line

### 2. Live Data Acquisition

Connect to a microcontroller for real-time data acquisition:

```bash
# List available serial ports
ekg-system ports

# Record from microcontroller
ekg-system live --port /dev/ttyUSB0 --duration 30 --visualize

# Record and save session
ekg-system live --port COM3 --duration 60 --save-session --session-name live_test

# Custom baudrate
ekg-system live --port /dev/ttyACM0 --baudrate 9600 --duration 20
```

### 3. Manage Sessions

List and export saved sessions:

```bash
# List all saved sessions
ekg-system list

# Export session report
ekg-system export sessions/my_mouse_001_20231104_123456.pkl --format html
ekg-system export sessions/my_mouse_001_20231104_123456.pkl --format json
```

## Python API

You can also use the EKG system as a Python library:

```python
import numpy as np
from ekg_system import EKGProcessor, ArrhythmiaDetector, SessionManager
from ekg_system.visualizer import EKGVisualizer

# Initialize components
processor = EKGProcessor(sampling_rate=1000)
detector = ArrhythmiaDetector(sampling_rate=1000)
visualizer = EKGVisualizer(sampling_rate=1000)

# Load and process data
processor.load_from_file('ekg_data.csv')
processor.filter_signal()
processor.detect_r_peaks()
hr_stats = processor.calculate_heart_rate()

print(f"Mean heart rate: {hr_stats['mean']:.1f} BPM")
print(f"Detected {len(processor.peaks)} heartbeats")

# Analyze arrhythmias
waveforms = processor.segment_waveforms()
rr_intervals = np.diff(processor.peaks)
report = detector.generate_report(rr_intervals, waveforms, processor.peaks)

print(f"Arrhythmias detected: {report['arrhythmias_detected']}")
print(f"Abnormal waveforms: {report['abnormal_waveforms']}")

# Visualize results
visualizer.plot_signal(processor.filtered_data, processor.peaks)
visualizer.plot_heart_rate(rr_intervals)
visualizer.plot_arrhythmia_summary(report)

# Save session
session_manager = SessionManager()
session_file = session_manager.save_session(
    session_name="my_analysis",
    data=processor.data,
    filtered_data=processor.filtered_data,
    peaks=processor.peaks,
    heart_rate=hr_stats,
    arrhythmia_report=report
)

# Export report
session_manager.export_report(session_file, output_format='html')
```

## Microcontroller Setup

For live data acquisition, your microcontroller should:

1. Send EKG voltage readings via serial (UART)
2. Format: One numeric value per line, terminated with newline
3. Default baudrate: 115200
4. Example Arduino code:

```cpp
void setup() {
  Serial.begin(115200);
  // Initialize your EKG sensor (e.g., AD8232)
}

void loop() {
  int ekgValue = analogRead(A0);  // Read from EKG sensor
  Serial.println(ekgValue);        // Send to computer
  delay(1);                        // 1ms = 1000 Hz sampling
}
```

## Data Format

EKG data should be:
- Time-series voltage measurements
- Typical sampling rate: 500-2000 Hz (default: 1000 Hz)
- For mice, typical heart rate: 300-800 BPM

### Example CSV Format

```csv
ekg
0.145
0.152
0.148
0.165
0.892  # R-peak
0.201
...
```

## Algorithm Details

### Signal Processing
- Bandpass filter: 0.5-100 Hz (Butterworth, 4th order)
- R-peak detection using adaptive thresholding
- Heart rate calculation from RR intervals

### Arrhythmia Detection
- **Tachycardia**: Heart rate > 700 BPM
- **Bradycardia**: Heart rate < 400 BPM
- **Irregular rhythm**: RR interval varies > 2 SD from mean
- **Premature beats**: Short RR followed by compensatory pause
- **Pause/Block**: RR interval > 1.5× mean

### Waveform Classification
- QRS width analysis
- ST segment elevation/depression detection
- T-wave morphology analysis

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_processor.py

# Run with coverage
python -m pytest tests/ --cov=ekg_system
```

Or use unittest:

```bash
python -m unittest discover tests
```

## Project Structure

```
ekg-system/
├── ekg_system/              # Main package
│   ├── __init__.py
│   ├── processor.py         # Signal processing
│   ├── arrhythmia_detector.py  # Arrhythmia detection
│   ├── microcontroller.py   # Hardware interface
│   ├── visualizer.py        # Data visualization
│   ├── session_manager.py   # Session management
│   └── cli.py              # Command-line interface
├── tests/                   # Test suite
│   ├── test_processor.py
│   ├── test_arrhythmia_detector.py
│   └── test_session_manager.py
├── requirements.txt         # Dependencies
├── setup.py                # Package setup
└── README.md               # This file
```

## Dependencies

- **numpy**: Numerical computations
- **scipy**: Signal processing algorithms
- **matplotlib**: Data visualization
- **pandas**: Data handling (CSV support)
- **pyserial**: Microcontroller communication

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Citation

If you use this software in your research, please cite:

```
EKG System - Mouse Cardiac Data Analysis
https://github.com/mramosandujar/ekg-system
```

## Troubleshooting

### Common Issues

**"No peaks detected"**
- Check your sampling rate matches the data
- Adjust height_threshold in detect_r_peaks()
- Verify signal quality

**"Serial port not found"**
- Run `ekg-system ports` to list available ports
- Check microcontroller connection
- Verify permissions (Linux: add user to dialout group)

**"Import error"**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version >= 3.7

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation
- Review example scripts

## Acknowledgments

Designed for cardiovascular research in mouse models. Suitable for educational and research purposes.