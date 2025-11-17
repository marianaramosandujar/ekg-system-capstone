# Connects to the microcontroller and pulls live EKG values over serial
import serial
import numpy as np
import time
from typing import Optional, Callable
import threading


class MicrocontrollerInterface:
    # Handles serial connection + reading data for live mode
    def __init__(self, port: str, baudrate: int = 115200, sampling_rate: int = 1000):
        self.port = port
        self.baudrate = baudrate
        self.sampling_rate = sampling_rate
        self.serial_conn = None
        self.is_connected = False
        self.is_streaming = False
        self.buffer = []
        self.stream_thread = None
        
    def connect(self) -> bool:
        # tries to open the serial port
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)  # some boards need a moment before sending data
            self.is_connected = True
            print(f"Connected to microcontroller on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            self.is_connected = False
            return False
            
    def disconnect(self) -> None:
        # shut down the port cleanly
        self.stop_streaming()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("Disconnected from microcontroller")
            
    def read_sample(self) -> Optional[float]:
        # reads one value from serial, assumes the MCU sends plain numeric text
        if not self.is_connected:
            raise ConnectionError("Not connected to microcontroller")
            
        try:
            line = self.serial_conn.readline().decode('utf-8').strip()
            if line:
                return float(line)
        except (ValueError, UnicodeDecodeError):
            # sometimes bad characters come through → skip instead of crashing
            return None
            
    def start_streaming(self, callback: Optional[Callable[[float], None]] = None,
                       duration: Optional[float] = None) -> None:
        # pulls a continuous stream of samples
        if not self.is_connected:
            raise ConnectionError("Not connected to microcontroller")
            
        if self.is_streaming:
            print("Already streaming")
            return
            
        self.is_streaming = True
        self.buffer = []
        
        def stream_worker():
            # loop until time is up or user stops
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
            
        # thread lets UI stay responsive while samples come in
        self.stream_thread = threading.Thread(target=stream_worker, daemon=True)
        self.stream_thread.start()
        print("Started streaming EKG data")
        
    def stop_streaming(self) -> np.ndarray:
        # ends the thread and returns whatever data is collected so far
        if self.is_streaming:
            self.is_streaming = False
            if self.stream_thread:
                self.stream_thread.join(timeout=2)
            print("Stopped streaming")
            
        return np.array(self.buffer)
        
    def get_buffer(self) -> np.ndarray:
        # check current collected values without stopping
        return np.array(self.buffer)
        
    def clear_buffer(self) -> None:
        # resets live stream history
        self.buffer = []
        
    def send_command(self, command: str) -> Optional[str]:
        # sends a simple command to the MCU and waits for a reply
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
        # lists the COM ports so user can pick the right one
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
