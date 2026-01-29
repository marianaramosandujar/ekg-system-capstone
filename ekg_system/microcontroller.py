import serial
import serial.tools.list_ports
import threading


class MSP430Interface:
    """
    Handles:
    - Detecting MSP430 USB CDC
    - Sending START / STOP commands
    - Reading streamed CSV data
    """

    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.port = None
        self.ser = None
        self.collecting = False
        self.thread = None

    # ----------------------------------------
    # Detect MSP430 USB CDC device
    # ----------------------------------------
    def detect_port(self):
        for p in serial.tools.list_ports.comports():
            desc = (p.description or "").lower()
            manuf = (p.manufacturer or "").lower()

            if (
                "msp430" in desc
                or "usb cdc" in desc
                or "texas instruments" in manuf
            ):
                self.port = p.device
                return p.device
        return None

    # ----------------------------------------
    # Start data collection (send START)
    # ----------------------------------------
    def start(self, callback):
        if self.collecting:
            return

        if not self.port:
            raise RuntimeError("MSP430 not detected")

        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)

        # Tell MSP430 to begin streaming
        self.ser.write(b"START\n")

        self.collecting = True

        def read_loop():
            while self.collecting:
                try:
                    line = self.ser.readline().decode(errors="ignore").strip()
                    if line:
                        callback(line)
                except Exception:
                    break

        self.thread = threading.Thread(target=read_loop, daemon=True)
        self.thread.start()

    # ----------------------------------------
    # Stop data collection (send STOP)
    # ----------------------------------------
    def stop(self):
        self.collecting = False

        if self.ser:
            try:
                self.ser.write(b"STOP\n")
            except Exception:
                pass

            self.ser.close()
            self.ser = None
