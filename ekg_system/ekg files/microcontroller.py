"""Microcontroller connectivity for live EKG data acquisition."""

import serial
import numpy as np
import time
from typing import Optional, Callable
import threading


class MicrocontrollerInterface:
    """Interface for connecting to microcontroller for live EKG data."""
    
    def __init__(self, port: str, baudrate: int = 115200, sampling_rate: int = 1000):
        """
        Initialize microcontroller interface.
        
        Args:
            port: Serial port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: Serial communication baud rate
            sampling_rate: Expected sampling rate in Hz
        """
        self.port = port
        self.baudrate = baudrate
        self.sampling_rate = sampling_rate
        self.serial_conn = None
        self.is_connected = False
        self.is_streaming = False
        self.buffer = []
        self.stream_thread = None
        
    def connect(self) -> bool:
        """
        Establish connection to microcontroller.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)  # Wait for connection to stabilize
            self.is_connected = True
            print(f"Connected to microcontroller on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            self.is_connected = False
            return False
            
    def disconnect(self) -> None:
        """Close connection to microcontroller."""
        self.stop_streaming()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("Disconnected from microcontroller")
            
    def read_sample(self) -> Optional[float]:
        """
        Read a single EKG sample from microcontroller.
        
        Returns:
            EKG value as float, or None if read failed
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to microcontroller")
            
        try:
            line = self.serial_conn.readline().decode('utf-8').strip()
            if line:
                # Assume data is sent as numeric value
                return float(line)
        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error reading sample: {e}")
            return None
            
    def start_streaming(self, callback: Optional[Callable[[float], None]] = None,
                       duration: Optional[float] = None) -> None:
        """
        Start streaming EKG data from microcontroller.
        
        Args:
            callback: Optional function to call with each new sample
            duration: Optional duration in seconds (None for continuous)
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to microcontroller")
            
        if self.is_streaming:
            print("Already streaming")
            return
            
        self.is_streaming = True
        self.buffer = []
        
        def stream_worker():
            start_time = time.time()
            while self.is_streaming:
                if duration and (time.time() - start_time) >= duration:
                    break
                    
                sample = self.read_sample()
                if sample is not None:
                    self.buffer.append(sample)
                    if callback:
                        callback(sample)
                        
            self.is_streaming = False
            
        self.stream_thread = threading.Thread(target=stream_worker, daemon=True)
        self.stream_thread.start()
        print("Started streaming EKG data")
        
    def stop_streaming(self) -> np.ndarray:
        """
        Stop streaming and return collected data.
        
        Returns:
            Array of collected EKG samples
        """
        if self.is_streaming:
            self.is_streaming = False
            if self.stream_thread:
                self.stream_thread.join(timeout=2)
            print("Stopped streaming")
            
        return np.array(self.buffer)
        
    def get_buffer(self) -> np.ndarray:
        """
        Get current buffer contents without stopping stream.
        
        Returns:
            Array of collected EKG samples
        """
        return np.array(self.buffer)
        
    def clear_buffer(self) -> None:
        """Clear the data buffer."""
        self.buffer = []
        
    def send_command(self, command: str) -> Optional[str]:
        """
        Send command to microcontroller.
        
        Args:
            command: Command string to send
            
        Returns:
            Response from microcontroller, or None if failed
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to microcontroller")
            
        try:
            self.serial_conn.write(f"{command}\n".encode('utf-8'))
            time.sleep(0.1)
            response = self.serial_conn.readline().decode('utf-8').strip()
            return response
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
            
    @staticmethod
    def list_available_ports() -> list:
        """
        List available serial ports.
        
        Returns:
            List of available port names
        """
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
