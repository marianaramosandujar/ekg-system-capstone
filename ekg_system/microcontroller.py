import serial
import threading
from serial.tools import list_ports
import os


class MSP430Interface:
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.port = os.getenv("EKG_PORT")  # manual override if set
        self.serial = None
        self.thread = None
        self.running = False
        self.callback = None

    # ---------------------------------------
    # Detect MSP430 USB CDC
    # ---------------------------------------
    def detect_port(self):
        for p in list_ports.comports():
            desc = (p.description or "").lower()
            if "usb serial" in desc or "msp" in desc or "ti" in desc:
                self.port = p.device
                return self.port
        return None

    # ---------------------------------------
    # Start serial streaming (single-open)
    # ---------------------------------------
    def start(self, callback):
        if self.serial and self.serial.is_open:
            return

        if not self.port:
            raise RuntimeError("No MSP430 port detected")

        self.serial = serial.Serial(self.port, self.baudrate, timeout=1)

        self.callback = callback
        self.running = True

        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        while self.running and self.serial and self.serial.is_open:
            try:
                line = self.serial.readline().decode(errors="ignore").strip()
                if line and self.callback:
                    self.callback(line)
            except Exception:
                self.running = False
                break

    def stop(self):
        self.running = False
        if self.serial:
            try:
                if self.serial.is_open:
                    self.serial.close()
            except Exception:
                pass
        self.serial = None