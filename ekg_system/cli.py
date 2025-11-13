"""Command-line interface for EKG system."""

import argparse
import sys
import numpy as np
from pathlib import Path

from ekg_system.processor import EKGProcessor
from .arrhythmia_detector import ArrhythmiaDetector
from .visualizer import EKGVisualizer
from .session_manager import SessionManager
from .microcontroller import MicrocontrollerInterface


def process_file(args):
    """Process an EKG data file."""
    print(f"Processing file: {args.input}")
    
    # Initialize components
    processor = EKGProcessor(sampling_rate=args.sampling_rate)
    detector = ArrhythmiaDetector(sampling_rate=args.sampling_rate)
    visualizer = EKGVisualizer(sampling_rate=args.sampling_rate)
    
    # Load and process data
    processor.load_from_file(args.input)
    print(f"Loaded {len(processor.data)} samples")
    
    # Filter signal
    processor.filter_signal()
    print("Signal filtered")
    
    # Detect R-peaks
    processor.detect_r_peaks()
    print(f"Detected {len(processor.peaks)} R-peaks")
    
    # Calculate heart rate
    hr_stats = processor.calculate_heart_rate()
    print(f"Mean heart rate: {hr_stats['mean']:.1f} BPM")
    
    # Segment waveforms
    waveforms = processor.segment_waveforms()
    print(f"Extracted {len(waveforms)} waveforms")
    
    # Analyze arrhythmias
    rr_intervals = np.diff(processor.peaks)
    arrhythmia_report = detector.generate_report(rr_intervals, waveforms, processor.peaks)
    print(f"Arrhythmias detected: {arrhythmia_report['arrhythmias_detected']}")
    
    # Generate labels
    labels = detector.label_beats(processor.peaks, rr_intervals)
    
    # Save session if requested
    if args.save_session:
        session_manager = SessionManager()
        session_file = session_manager.save_session(
            session_name=args.session_name or Path(args.input).stem,
            data=processor.data,
            filtered_data=processor.filtered_data,
            peaks=processor.peaks,
            heart_rate=hr_stats,
            arrhythmia_report=arrhythmia_report,
            metadata={'source_file': args.input}
        )
        print(f"Session saved: {session_file}")
        
        # Export report if format specified
        if args.export_format:
            report_file = session_manager.export_report(
                session_file,
                output_format=args.export_format
            )
            print(f"Report exported: {report_file}")
    
    # Visualize if requested
    if args.visualize:
        print("Generating visualizations...")
        visualizer.plot_signal(processor.filtered_data, processor.peaks, 
                             title=f"EKG Signal - {Path(args.input).stem}")
        visualizer.plot_heart_rate(rr_intervals)
        visualizer.plot_arrhythmia_summary(arrhythmia_report)
        
    return 0


def live_mode(args):
    """Live data acquisition from microcontroller."""
    print(f"Starting live mode on port: {args.port}")
    
    # Initialize components
    mcu = MicrocontrollerInterface(
        port=args.port,
        baudrate=args.baudrate,
        sampling_rate=args.sampling_rate
    )
    visualizer = EKGVisualizer(sampling_rate=args.sampling_rate)
    
    # Connect to microcontroller
    if not mcu.connect():
        print("Failed to connect to microcontroller")
        return 1
    
    try:
        # Start streaming
        print(f"Recording for {args.duration} seconds...")
        mcu.start_streaming(duration=args.duration)
        
        # Wait for completion
        import time
        while mcu.is_streaming:
            time.sleep(0.5)
            
        # Get collected data
        data = mcu.get_buffer()
        print(f"Collected {len(data)} samples")
        
        if len(data) > 100:
            # Process the data
            processor = EKGProcessor(sampling_rate=args.sampling_rate)
            processor.load_data(data)
            processor.filter_signal()
            processor.detect_r_peaks()
            
            # Visualize
            if args.visualize:
                visualizer.plot_signal(processor.filtered_data, processor.peaks,
                                     title="Live EKG Recording")
            
            # Save if requested
            if args.save_session:
                hr_stats = processor.calculate_heart_rate()
                session_manager = SessionManager()
                session_file = session_manager.save_session(
                    session_name=args.session_name or "live_recording",
                    data=processor.data,
                    filtered_data=processor.filtered_data,
                    peaks=processor.peaks,
                    heart_rate=hr_stats,
                    metadata={'source': 'live', 'port': args.port}
                )
                print(f"Session saved: {session_file}")
        else:
            print("Not enough data collected")
            
    finally:
        mcu.disconnect()
    
    return 0


def list_sessions(args):
    """List saved sessions."""
    session_manager = SessionManager()
    sessions = session_manager.list_sessions()
    
    if not sessions:
        print("No saved sessions found")
    else:
        print(f"Found {len(sessions)} session(s):")
        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session}")
    
    return 0


def export_session(args):
    """Export a saved session."""
    session_manager = SessionManager()
    report_file = session_manager.export_report(
        args.session_file,
        output_format=args.format
    )
    print(f"Report exported: {report_file}")
    return 0


def list_ports(args):
    """List available serial ports."""
    ports = MicrocontrollerInterface.list_available_ports()
    
    if not ports:
        print("No serial ports found")
    else:
        print("Available serial ports:")
        for port in ports:
            print(f"  - {port}")
    
    return 0


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="EKG System - Process and analyze EKG data for mice"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Process file command
    process_parser = subparsers.add_parser('process', help='Process EKG data file')
    process_parser.add_argument('input', help='Input data file (txt, csv, or npy)')
    process_parser.add_argument('--sampling-rate', type=int, default=1000,
                               help='Sampling rate in Hz (default: 1000)')
    process_parser.add_argument('--save-session', action='store_true',
                               help='Save processed session')
    process_parser.add_argument('--session-name', help='Name for saved session')
    process_parser.add_argument('--export-format', choices=['txt', 'json', 'csv', 'html'],
                               help='Export report format')
    process_parser.add_argument('--visualize', action='store_true',
                               help='Generate visualizations')
    process_parser.set_defaults(func=process_file)
    
    # Live mode command
    live_parser = subparsers.add_parser('live', help='Live data acquisition')
    live_parser.add_argument('--port', required=True,
                            help='Serial port (e.g., COM3 or /dev/ttyUSB0)')
    live_parser.add_argument('--baudrate', type=int, default=115200,
                            help='Baud rate (default: 115200)')
    live_parser.add_argument('--sampling-rate', type=int, default=1000,
                            help='Sampling rate in Hz (default: 1000)')
    live_parser.add_argument('--duration', type=float, default=10.0,
                            help='Recording duration in seconds (default: 10)')
    live_parser.add_argument('--save-session', action='store_true',
                            help='Save recorded session')
    live_parser.add_argument('--session-name', help='Name for saved session')
    live_parser.add_argument('--visualize', action='store_true',
                            help='Generate visualizations')
    live_parser.set_defaults(func=live_mode)
    
    # List sessions command
    list_parser = subparsers.add_parser('list', help='List saved sessions')
    list_parser.set_defaults(func=list_sessions)
    
    # Export session command
    export_parser = subparsers.add_parser('export', help='Export session report')
    export_parser.add_argument('session_file', help='Path to session file')
    export_parser.add_argument('--format', choices=['txt', 'json', 'csv', 'html'],
                              default='txt', help='Export format (default: txt)')
    export_parser.set_defaults(func=export_session)
    
    # List ports command
    ports_parser = subparsers.add_parser('ports', help='List available serial ports')
    ports_parser.set_defaults(func=list_ports)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
