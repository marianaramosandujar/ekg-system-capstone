"""Tests for session manager module."""

import unittest
import numpy as np
import tempfile
import shutil
from pathlib import Path
from ekg_system.session_manager import SessionManager


class TestSessionManager(unittest.TestCase):
    """Test cases for SessionManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for sessions
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(sessions_dir=self.temp_dir)
        
        # Create synthetic test data
        self.test_data = np.random.randn(1000)
        self.test_peaks = np.array([100, 200, 300, 400])
        self.test_hr = {'mean': 600, 'std': 20, 'min': 580, 'max': 620}
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
    def test_save_session(self):
        """Test saving a session."""
        session_file = self.session_manager.save_session(
            session_name="test_session",
            data=self.test_data,
            peaks=self.test_peaks,
            heart_rate=self.test_hr
        )
        
        self.assertTrue(Path(session_file).exists())
        
    def test_load_session(self):
        """Test loading a session."""
        # First save a session
        session_file = self.session_manager.save_session(
            session_name="test_session",
            data=self.test_data,
            peaks=self.test_peaks,
            heart_rate=self.test_hr
        )
        
        # Then load it
        loaded_data = self.session_manager.load_session(session_file)
        
        self.assertIn('session_name', loaded_data)
        self.assertIn('data', loaded_data)
        self.assertEqual(len(loaded_data['data']), len(self.test_data))
        
    def test_list_sessions(self):
        """Test listing sessions."""
        # Save a couple of sessions
        self.session_manager.save_session(
            session_name="test1",
            data=self.test_data
        )
        self.session_manager.save_session(
            session_name="test2",
            data=self.test_data
        )
        
        sessions = self.session_manager.list_sessions()
        self.assertGreaterEqual(len(sessions), 2)
        
    def test_export_txt(self):
        """Test exporting as text."""
        session_file = self.session_manager.save_session(
            session_name="test_export",
            data=self.test_data,
            heart_rate=self.test_hr
        )
        
        report_file = self.session_manager.export_report(
            session_file,
            output_format="txt",
            output_dir=self.temp_dir
        )
        
        self.assertTrue(Path(report_file).exists())
        
    def test_export_json(self):
        """Test exporting as JSON."""
        session_file = self.session_manager.save_session(
            session_name="test_export",
            data=self.test_data,
            heart_rate=self.test_hr
        )
        
        report_file = self.session_manager.export_report(
            session_file,
            output_format="json",
            output_dir=self.temp_dir
        )
        
        self.assertTrue(Path(report_file).exists())
        
    def test_delete_session(self):
        """Test deleting a session."""
        session_file = self.session_manager.save_session(
            session_name="test_delete",
            data=self.test_data
        )
        
        self.assertTrue(Path(session_file).exists())
        
        self.session_manager.delete_session(session_file)
        self.assertFalse(Path(session_file).exists())


if __name__ == '__main__':
    unittest.main()
