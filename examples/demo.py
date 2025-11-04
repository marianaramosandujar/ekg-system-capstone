#!/usr/bin/env python3
"""Demo script showing EKG system capabilities."""

import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ekg_system import EKGProcessor, ArrhythmiaDetector, SessionManager
from ekg_system.visualizer import EKGVisualizer


def demo_basic_processing():
    """Demonstrate basic EKG processing."""
    print("=" * 60)
    print("DEMO: Basic EKG Processing")
    print("=" * 60)
    
    # Generate synthetic data
    duration = 10
    sampling_rate = 1000
    t = np.linspace(0, duration, duration * sampling_rate)
    
    # Simulate mouse heart rate of 600 BPM (10 Hz)
    hr_hz = 600 / 60.0
    ekg_signal = np.sin(2 * np.pi * hr_hz * t) + 0.3 * np.sin(2 * np.pi * hr_hz * t + 1.2)
    ekg_signal += 0.1 * np.random.randn(len(t))  # Add noise
    
    print(f"\nGenerated {len(ekg_signal)} samples at {sampling_rate} Hz")
    print(f"Duration: {duration} seconds")
    
    # Initialize processor
    processor = EKGProcessor(sampling_rate=sampling_rate)
    processor.load_data(ekg_signal)
    
    # Filter signal
    print("\nFiltering signal...")
    processor.filter_signal()
    
    # Detect R-peaks
    print("Detecting R-peaks...")
    peaks = processor.detect_r_peaks()
    print(f"Found {len(peaks)} R-peaks")
    
    # Calculate heart rate
    print("\nCalculating heart rate...")
    hr_stats = processor.calculate_heart_rate()
    print(f"  Mean HR: {hr_stats['mean']:.1f} BPM")
    print(f"  Std Dev: {hr_stats['std']:.1f} BPM")
    print(f"  Min HR:  {hr_stats['min']:.1f} BPM")
    print(f"  Max HR:  {hr_stats['max']:.1f} BPM")
    
    # Segment waveforms
    print("\nSegmenting waveforms...")
    waveforms = processor.segment_waveforms(window_size=100)
    print(f"Extracted {len(waveforms)} complete waveforms")
    
    return processor, hr_stats


def demo_arrhythmia_detection():
    """Demonstrate arrhythmia detection."""
    print("\n" + "=" * 60)
    print("DEMO: Arrhythmia Detection")
    print("=" * 60)
    
    # Generate data with arrhythmias
    duration = 15
    sampling_rate = 1000
    samples = duration * sampling_rate
    t = np.linspace(0, duration, samples)
    
    # Base signal with normal rhythm
    hr_hz = 600 / 60.0
    ekg_signal = np.sin(2 * np.pi * hr_hz * t) + 0.3 * np.sin(2 * np.pi * hr_hz * t + 1.2)
    
    # Add tachycardia section (faster rate)
    tachy_start = int(0.7 * samples)
    tachy_end = int(0.85 * samples)
    t_tachy = t[tachy_start:tachy_end] - t[tachy_start]
    fast_hr = 800 / 60.0
    ekg_signal[tachy_start:tachy_end] = 1.2 * np.sin(2 * np.pi * fast_hr * t_tachy)
    
    # Add noise
    ekg_signal += 0.1 * np.random.randn(samples)
    
    # Process
    processor = EKGProcessor(sampling_rate=sampling_rate)
    processor.load_data(ekg_signal)
    processor.filter_signal()
    processor.detect_r_peaks()
    
    print(f"\nProcessed {duration}s recording")
    print(f"Detected {len(processor.peaks)} R-peaks")
    
    # Detect arrhythmias
    detector = ArrhythmiaDetector(sampling_rate=sampling_rate)
    waveforms = processor.segment_waveforms()
    rr_intervals = np.diff(processor.peaks)
    
    print("\nAnalyzing arrhythmias...")
    report = detector.generate_report(rr_intervals, waveforms, processor.peaks)
    
    print(f"\nArrhythmia Report:")
    print(f"  Total beats: {report['total_beats']}")
    print(f"  Mean HR: {report['mean_heart_rate']:.1f} BPM")
    print(f"  HR variability: {report['hr_std']:.1f} BPM")
    print(f"  Arrhythmias detected: {report['arrhythmias_detected']}")
    print(f"  Abnormal waveforms: {report['abnormal_waveforms']}")
    
    if report['arrhythmia_counts']:
        print("\n  Arrhythmia breakdown:")
        for arr_type, count in report['arrhythmia_counts'].items():
            print(f"    - {arr_type}: {count}")
    
    return processor, report


def demo_session_management():
    """Demonstrate session management."""
    print("\n" + "=" * 60)
    print("DEMO: Session Management")
    print("=" * 60)
    
    # Create test data
    sampling_rate = 1000
    duration = 5
    t = np.linspace(0, duration, duration * sampling_rate)
    hr_hz = 600 / 60.0
    ekg_signal = np.sin(2 * np.pi * hr_hz * t) + 0.1 * np.random.randn(len(t))
    
    # Process
    processor = EKGProcessor(sampling_rate=sampling_rate)
    processor.load_data(ekg_signal)
    processor.filter_signal()
    processor.detect_r_peaks()
    hr_stats = processor.calculate_heart_rate()
    
    # Arrhythmia analysis
    detector = ArrhythmiaDetector(sampling_rate=sampling_rate)
    waveforms = processor.segment_waveforms()
    rr_intervals = np.diff(processor.peaks)
    report = detector.generate_report(rr_intervals, waveforms, processor.peaks)
    
    # Save session
    print("\nSaving session...")
    session_manager = SessionManager(sessions_dir="/tmp/ekg_sessions")
    
    session_file = session_manager.save_session(
        session_name="demo_session",
        data=processor.data,
        filtered_data=processor.filtered_data,
        peaks=processor.peaks,
        heart_rate=hr_stats,
        arrhythmia_report=report,
        metadata={
            'subject': 'demo_mouse',
            'experiment': 'demo',
            'sampling_rate': sampling_rate
        }
    )
    
    print(f"Session saved: {session_file}")
    
    # List sessions
    print("\nListing sessions...")
    sessions = session_manager.list_sessions()
    print(f"Found {len(sessions)} session(s)")
    
    # Export report
    print("\nExporting report (text format)...")
    txt_report = session_manager.export_report(
        session_file,
        output_format='txt',
        output_dir='/tmp/ekg_reports'
    )
    print(f"Text report: {txt_report}")
    
    print("\nExporting report (JSON format)...")
    json_report = session_manager.export_report(
        session_file,
        output_format='json',
        output_dir='/tmp/ekg_reports'
    )
    print(f"JSON report: {json_report}")
    
    return session_file


def demo_visualization():
    """Demonstrate visualization capabilities."""
    print("\n" + "=" * 60)
    print("DEMO: Data Visualization")
    print("=" * 60)
    
    # Generate data
    sampling_rate = 1000
    duration = 5
    t = np.linspace(0, duration, duration * sampling_rate)
    hr_hz = 600 / 60.0
    ekg_signal = np.sin(2 * np.pi * hr_hz * t) + 0.3 * np.sin(2 * np.pi * hr_hz * t + 1.2)
    ekg_signal += 0.1 * np.random.randn(len(t))
    
    # Process
    processor = EKGProcessor(sampling_rate=sampling_rate)
    processor.load_data(ekg_signal)
    processor.filter_signal()
    processor.detect_r_peaks()
    
    # Generate visualizations
    visualizer = EKGVisualizer(sampling_rate=sampling_rate)
    
    print("\nGenerating visualizations...")
    print("  1. Signal plot with R-peaks")
    visualizer.plot_signal(
        processor.filtered_data,
        processor.peaks,
        title="Demo EKG Signal",
        show=False,
        save_path='/tmp/demo_signal.png'
    )
    print("     Saved to: /tmp/demo_signal.png")
    
    print("  2. Heart rate plot")
    rr_intervals = np.diff(processor.peaks)
    visualizer.plot_heart_rate(
        rr_intervals,
        show=False,
        save_path='/tmp/demo_heart_rate.png'
    )
    print("     Saved to: /tmp/demo_heart_rate.png")
    
    print("  3. Waveform comparison")
    waveforms = processor.segment_waveforms(window_size=100)
    visualizer.plot_waveforms(
        waveforms[:5],  # First 5 waveforms
        max_waveforms=5,
        show=False,
        save_path='/tmp/demo_waveforms.png'
    )
    print("     Saved to: /tmp/demo_waveforms.png")
    
    # Arrhythmia summary
    detector = ArrhythmiaDetector(sampling_rate=sampling_rate)
    report = detector.generate_report(rr_intervals, waveforms, processor.peaks)
    
    print("  4. Arrhythmia summary")
    visualizer.plot_arrhythmia_summary(
        report,
        show=False,
        save_path='/tmp/demo_arrhythmia_summary.png'
    )
    print("     Saved to: /tmp/demo_arrhythmia_summary.png")
    
    print("\nAll visualizations saved successfully!")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("EKG SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo showcases the capabilities of the EKG system:")
    print("  - Basic signal processing")
    print("  - Arrhythmia detection")
    print("  - Session management")
    print("  - Data visualization")
    print("\n")
    
    try:
        # Run demos
        demo_basic_processing()
        demo_arrhythmia_detection()
        demo_session_management()
        demo_visualization()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nNext steps:")
        print("  - Try processing your own EKG data")
        print("  - Use 'ekg-system --help' for CLI options")
        print("  - Check the documentation for API usage")
        print("  - Generate sample data: python examples/generate_sample_data.py")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
