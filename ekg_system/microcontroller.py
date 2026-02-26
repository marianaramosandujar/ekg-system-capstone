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
    # Detect MSP430 USB CDC (Windows-safe)
    # ---------------------------------------
def detect_port(self):
    TI_VID = 0x0451  # Texas Instruments vendor ID (common)

    candidates = []

    for p in list_ports.comports():
        desc = (p.description or "").lower()
        manuf = (getattr(p, "manufacturer", "") or "").lower()
        hwid = (p.hwid or "").lower()
        vid = getattr(p, "vid", None)

        score = 0

        # Strong signal
        if vid == TI_VID:
            score += 100

        if "msp" in desc or "msp" in manuf:
            score += 80

        if "texas instruments" in desc or "texas instruments" in manuf:
            score += 60

        if "ti" in desc or "ti" in manuf:
            score += 20

        # Generic USB CDC hints (cross-platform)
        if any(k in desc for k in ("usb", "acm", "serial", "uart")):
            score += 10

        if score > 0:
            candidates.append((score, p.device))

    if not candidates:
        return None

    # Prefer /dev/cu.* on macOS if present
    candidates.sort(reverse=True)

    for _, dev in candidates:
        if dev.startswith("/dev/cu."):
            self.port = dev
            return dev

    self.port = candidates[0][1]
    return self.port

    # ---------------------------------------
    # Start serial streaming (single-open)
    # ---------------------------------------
    def start(self, callback):
        # Prevent reopening the port
        if self.serial and self.serial.is_open:
            return

        if not self.port:
            raise RuntimeError("No MSP430 port detected")

        self.serial = serial.Serial(
            self.port,
            self.baudrate,
            timeout=1
        )

        self.callback = callback
        self.running = True

        self.thread = threading.Thread(
            target=self._read_loop,
            daemon=True
        )
        self.thread.start()

    # ---------------------------------------
    # Read loop
    # ---------------------------------------
def _read_loop(self):
    while self.running and self.serial and self.serial.is_open:
        try:
            line = self.serial.readline().decode(errors="ignore").strip()
            if line and self.callback:
                self.callback(line)
        except Exception:
            self.running = False
            break

    # ---------------------------------------
    # Stop streaming and close port
    # ---------------------------------------
    def stop(self):
        self.running = False

        if self.serial:
            try:
                if self.serial.is_open:
                    self.serial.close()
            except Exception:
                pass

        self.serial = None
