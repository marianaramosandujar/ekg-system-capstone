"""Session management for saving and loading EKG analysis sessions."""

import json
import pickle
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd


class SessionManager:
    """Manage EKG analysis sessions - save, load, and export."""
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize session manager.
        
        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
    def save_session(self, session_name: str, 
                    data: np.ndarray,
                    filtered_data: Optional[np.ndarray] = None,
                    peaks: Optional[np.ndarray] = None,
                    heart_rate: Optional[Dict] = None,
                    arrhythmia_report: Optional[Dict] = None,
                    metadata: Optional[Dict] = None) -> str:
        """
        Save complete analysis session.
        
        Args:
            session_name: Name for the session
            data: Raw EKG data
            filtered_data: Filtered EKG data
            peaks: Detected R-peaks
            heart_rate: Heart rate statistics
            arrhythmia_report: Arrhythmia analysis report
            metadata: Additional metadata
            
        Returns:
            Path to saved session file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{session_name}_{timestamp}"
        session_file = self.sessions_dir / f"{session_id}.pkl"
        
        session_data = {
            'session_name': session_name,
            'timestamp': timestamp,
            'data': data,
            'filtered_data': filtered_data,
            'peaks': peaks,
            'heart_rate': heart_rate,
            'arrhythmia_report': arrhythmia_report,
            'metadata': metadata or {}
        }
        
        with open(session_file, 'wb') as f:
            pickle.dump(session_data, f)
            
        print(f"Session saved: {session_file}")
        return str(session_file)
        
    def load_session(self, session_file: str) -> Dict:
        """
        Load a saved session.
        
        Args:
            session_file: Path to session file
            
        Returns:
            Dictionary containing session data
        """
        with open(session_file, 'rb') as f:
            session_data = pickle.load(f)
            
        print(f"Session loaded: {session_file}")
        return session_data
        
    def list_sessions(self) -> list:
        """
        List all saved sessions.
        
        Returns:
            List of session file paths
        """
        sessions = list(self.sessions_dir.glob("*.pkl"))
        return [str(s) for s in sorted(sessions, reverse=True)]
        
    def export_report(self, session_file: str, 
                     output_format: str = "txt",
                     output_dir: str = "reports") -> str:
        """
        Export session report in various formats.
        
        Args:
            session_file: Path to session file
            output_format: Output format ('txt', 'json', 'csv', 'html')
            output_dir: Directory to save reports
            
        Returns:
            Path to exported report
        """
        # Load session
        session_data = self.load_session(session_file)
        
        # Create reports directory
        reports_path = Path(output_dir)
        reports_path.mkdir(exist_ok=True)
        
        # Generate base filename
        session_name = session_data['session_name']
        timestamp = session_data['timestamp']
        base_name = f"report_{session_name}_{timestamp}"
        
        if output_format == "txt":
            return self._export_txt(session_data, reports_path / f"{base_name}.txt")
        elif output_format == "json":
            return self._export_json(session_data, reports_path / f"{base_name}.json")
        elif output_format == "csv":
            return self._export_csv(session_data, reports_path / f"{base_name}.csv")
        elif output_format == "html":
            return self._export_html(session_data, reports_path / f"{base_name}.html")
        else:
            raise ValueError(f"Unsupported format: {output_format}")
            
    def _export_txt(self, session_data: Dict, output_path: Path) -> str:
        """Export session as text report."""
        with open(output_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write(f"EKG ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Session: {session_data['session_name']}\n")
            f.write(f"Date: {session_data['timestamp']}\n\n")
            
            # Metadata
            if session_data.get('metadata'):
                f.write("METADATA\n")
                f.write("-" * 60 + "\n")
                for key, value in session_data['metadata'].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
            
            # Heart rate statistics
            if session_data.get('heart_rate'):
                f.write("HEART RATE STATISTICS\n")
                f.write("-" * 60 + "\n")
                hr = session_data['heart_rate']
                f.write(f"Mean HR: {hr['mean']:.1f} BPM\n")
                f.write(f"Std Dev: {hr['std']:.1f} BPM\n")
                f.write(f"Min HR: {hr['min']:.1f} BPM\n")
                f.write(f"Max HR: {hr['max']:.1f} BPM\n\n")
            
            # Arrhythmia report
            if session_data.get('arrhythmia_report'):
                f.write("ARRHYTHMIA ANALYSIS\n")
                f.write("-" * 60 + "\n")
                report = session_data['arrhythmia_report']
                f.write(f"Total Beats: {report['total_beats']}\n")
                f.write(f"Arrhythmias Detected: {report['arrhythmias_detected']}\n")
                f.write(f"Abnormal Waveforms: {report['abnormal_waveforms']}\n\n")
                
                if report.get('arrhythmia_counts'):
                    f.write("Arrhythmia Types:\n")
                    for arr_type, count in report['arrhythmia_counts'].items():
                        f.write(f"  - {arr_type}: {count}\n")
                    f.write("\n")
                
                if report.get('arrhythmia_details'):
                    f.write("Detailed Arrhythmia Events:\n")
                    for detail in report['arrhythmia_details'][:20]:  # First 20
                        f.write(f"  Beat #{detail['beat_number']}: "
                               f"{detail['type']} - {detail['description']}\n")
                    if len(report['arrhythmia_details']) > 20:
                        f.write(f"  ... and {len(report['arrhythmia_details']) - 20} more\n")
            
            f.write("\n" + "=" * 60 + "\n")
            
        print(f"Text report exported: {output_path}")
        return str(output_path)
        
    def _export_json(self, session_data: Dict, output_path: Path) -> str:
        """Export session as JSON report."""
        # Convert numpy arrays to lists for JSON serialization
        export_data = {
            'session_name': session_data['session_name'],
            'timestamp': session_data['timestamp'],
            'metadata': session_data.get('metadata', {}),
            'heart_rate': session_data.get('heart_rate'),
            'arrhythmia_report': session_data.get('arrhythmia_report'),
        }
        
        # Add peaks as list if present
        if session_data.get('peaks') is not None:
            export_data['peaks'] = session_data['peaks'].tolist()
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        print(f"JSON report exported: {output_path}")
        return str(output_path)
        
    def _export_csv(self, session_data: Dict, output_path: Path) -> str:
        """Export session data as CSV."""
        # Create DataFrame with time series data
        data = session_data.get('data')
        filtered_data = session_data.get('filtered_data')
        
        df_data = {'sample': range(len(data))}
        df_data['raw_signal'] = data
        
        if filtered_data is not None:
            df_data['filtered_signal'] = filtered_data
            
        if session_data.get('peaks') is not None:
            # Create column marking R-peaks
            peak_markers = np.zeros(len(data))
            peak_markers[session_data['peaks']] = 1
            df_data['r_peak'] = peak_markers
        
        df = pd.DataFrame(df_data)
        df.to_csv(output_path, index=False)
        
        print(f"CSV data exported: {output_path}")
        return str(output_path)
        
    def _export_html(self, session_data: Dict, output_path: Path) -> str:
        """Export session as HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EKG Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>EKG Analysis Report</h1>
            <p><strong>Session:</strong> {session_data['session_name']}</p>
            <p><strong>Date:</strong> {session_data['timestamp']}</p>
        """
        
        # Heart rate section
        if session_data.get('heart_rate'):
            hr = session_data['heart_rate']
            html += """
            <h2>Heart Rate Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
            """
            html += f"<tr><td>Mean HR</td><td>{hr['mean']:.1f} BPM</td></tr>"
            html += f"<tr><td>Std Dev</td><td>{hr['std']:.1f} BPM</td></tr>"
            html += f"<tr><td>Min HR</td><td>{hr['min']:.1f} BPM</td></tr>"
            html += f"<tr><td>Max HR</td><td>{hr['max']:.1f} BPM</td></tr>"
            html += "</table>"
        
        # Arrhythmia section
        if session_data.get('arrhythmia_report'):
            report = session_data['arrhythmia_report']
            html += f"""
            <h2>Arrhythmia Analysis</h2>
            <p><span class="metric">Total Beats:</span> {report['total_beats']}</p>
            <p><span class="metric">Arrhythmias Detected:</span> {report['arrhythmias_detected']}</p>
            <p><span class="metric">Abnormal Waveforms:</span> {report['abnormal_waveforms']}</p>
            """
            
            if report.get('arrhythmia_counts'):
                html += "<h3>Arrhythmia Types</h3><table><tr><th>Type</th><th>Count</th></tr>"
                for arr_type, count in report['arrhythmia_counts'].items():
                    html += f"<tr><td>{arr_type}</td><td>{count}</td></tr>"
                html += "</table>"
        
        html += """
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html)
            
        print(f"HTML report exported: {output_path}")
        return str(output_path)
        
    def delete_session(self, session_file: str) -> None:
        """
        Delete a saved session.
        
        Args:
            session_file: Path to session file
        """
        Path(session_file).unlink()
        print(f"Session deleted: {session_file}")
