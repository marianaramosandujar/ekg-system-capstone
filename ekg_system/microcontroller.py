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

    def __init__(self, baudrate=115200, mode="binary"):
        self.baudrate = baudrate
        self.mode = mode  # currently only "binary" implemented here
        self.port = os.getenv("EKG_PORT")  # manual override if set

        self.serial = None
        self.thread = None
        self.running = False
        self.callback = None

        # internal buffer for packet framing
        self._buf = bytearray()

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
        try:
            self.serial.reset_input_buffer()
        except Exception:
            pass

        self.callback = callback
        self.running = True

        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    @staticmethod
    def _s24_from_be3(b0, b1, b2) -> int:
        v = (b0 << 16) | (b1 << 8) | b2
        if v & 0x800000:
            v -= 1 << 24
        return v

    def _read_loop(self):
        if self.mode != "binary":
            raise RuntimeError(f"Unsupported mode: {self.mode}")

        while self.running and self.serial and self.serial.is_open:
            try:
                chunk = self.serial.read(4096)
                if chunk:
                    self._buf.extend(chunk)

                # parse as many whole packets as possible
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

                    pkt = self._buf[:self.PACKET_LEN]
                    del self._buf[:self.PACKET_LEN]

                    sid = (
                        pkt[2]
                        | (pkt[3] << 8)
                        | (pkt[4] << 16)
                        | (pkt[5] << 24)
                    )
                    ch1 = self._s24_from_be3(pkt[6], pkt[7], pkt[8])
                    ch2 = self._s24_from_be3(pkt[9], pkt[10], pkt[11])

                    if self.callback:
                        self.callback(sid, ch1, ch2, time.time())

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