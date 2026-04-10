import os
import serial
import threading
import time
from serial.tools import list_ports


class MSP430Interface:
    """
    Reads MSP430 EKG data over USB CDC.

    Supports:
      - "binary" packets:
          SYNC = A5 5A
          PACKET_LEN = 12 bytes
          Layout:
            [0:2]   sync
            [2:6]   sample_id (uint32 LE)
            [6:9]   ch1 (24-bit BE signed)
            [9:12]  ch2 (24-bit BE signed)

    callback signature (binary):
        callback(sample_id: int, ch1: int, ch2: int, t_wall: float)
    """

    SYNC = b"\xA5\x5A"
    PACKET_LEN = 12

    VREF = 2.42
    GAIN = 6
    FS = (2**23 - 1)

    def __init__(self, baudrate=115200, mode="binary"):
        self.baudrate = baudrate
        self.mode = mode  # "binary"
        self.port = os.getenv("EKG_PORT")  # optional override

        self.serial = None
        self.thread = None
        self.running = False
        self.callback = None

        # internal buffer for packet framing
        self._buf = bytearray()

    def detect_port(self):
        """
        Try to find the MSP430 CDC device by opening candidate ports and
        checking which one is actually streaming valid packet sync bytes.
        """
        # If user manually set EKG_PORT, honor that first
        if self.port:
            return self.port

        ports = list(list_ports.comports())

        # First pass: prefer likely USB serial / TI / MSP430 devices
        preferred = []
        others = []

        for p in ports:
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()

            if (
                "usb serial" in desc
                or "msp" in desc
                or "ti" in desc
                or "texas instruments" in desc
                or "1cbe" in hwid
                or "2047" in hwid
            ):
                preferred.append(p)
            else:
                others.append(p)

        candidates = preferred + others

        for p in candidates:
            ser = None
            try:
                ser = serial.Serial(p.device, self.baudrate, timeout=0.25)

                try:
                    ser.reset_input_buffer()
                except Exception:
                    pass

                # Give device a brief moment to stream
                start = time.time()
                data = bytearray()

                while time.time() - start < 1.5:
                    chunk = ser.read(256)
                    if chunk:
                        data.extend(chunk)

                        idx = data.find(self.SYNC)
                        if idx >= 0 and len(data) - idx >= self.PACKET_LEN:
                            self.port = p.device
                            return self.port

                # No valid packet seen on this port
            except Exception:
                pass
            finally:
                if ser is not None:
                    try:
                        ser.close()
                    except Exception:
                        pass

        return None

    def start(self, callback):
        """Open port and start background reader thread."""
        if self.serial and self.serial.is_open:
            return

        if not self.port:
            self.port = self.detect_port()

        if not self.port:
            raise RuntimeError("No MSP430 port detected (and EKG_PORT not set)")

        self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
        try:
            self.serial.reset_input_buffer()
        except Exception:
            pass

        self.callback = callback
        self.running = True
        self._buf = bytearray()

        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    @staticmethod
    def _s24_from_be3(b0, b1, b2) -> int:
        """Convert signed 24-bit big-endian (3 bytes) to Python int."""
        v = (b0 << 16) | (b1 << 8) | b2
        if v & 0x800000:
            v -= 1 << 24
        return v

    @classmethod
    def code_to_mv(cls, code: int) -> float:
        """Convert ADS1292R ADC code to millivolts."""
        return (1000.0 * code * cls.VREF) / (cls.GAIN * cls.FS)

    def _read_loop(self):
        if self.mode != "binary":
            raise RuntimeError(f"Unsupported mode: {self.mode}")

        while self.running and self.serial and self.serial.is_open:
            try:
                chunk = self.serial.read(4096)
                if chunk:
                    self._buf.extend(chunk)

                while True:
                    if len(self._buf) < self.PACKET_LEN:
                        break

                    idx = self._buf.find(self.SYNC)
                    if idx < 0:
                        # keep last 1 byte in case it's 0xA5
                        self._buf[:] = self._buf[-1:]
                        break

                    if idx > 0:
                        del self._buf[:idx]

                    if len(self._buf) < self.PACKET_LEN:
                        break

                    pkt = self._buf[: self.PACKET_LEN]
                    del self._buf[: self.PACKET_LEN]

                    sid = (
                        pkt[2]
                        | (pkt[3] << 8)
                        | (pkt[4] << 16)
                        | (pkt[5] << 24)
                    )
                    ch1 = self._s24_from_be3(pkt[6], pkt[7], pkt[8])
                    ch2 = self._s24_from_be3(pkt[9], pkt[10], pkt[11])

                    # Optional mV conversions available for UI or debugging if needed
                    ch1_mv = self.code_to_mv(ch1)
                    ch2_mv = self.code_to_mv(ch2)

                    if self.callback:
                        self.callback(int(sid), int(ch1_mv), int(ch2_mv), time.time())

            except Exception:
                self.running = False
                break

    def stop(self):
        """Stop reader thread and close serial port."""
        self.running = False
        if self.serial:
            try:
                if self.serial.is_open:
                    self.serial.close()
            except Exception:
                pass
        self.serial = None