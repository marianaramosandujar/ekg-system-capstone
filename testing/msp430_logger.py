import serial
import csv
import time

PORT = "COM10"
BAUD = 115200
OUTFILE = "ekg_capture.csv"

SYNC = b"\xA5\x5A"
PACKET_LEN = 12  # 2 sync + 10 bytes payload

def s24_from_be3(b0, b1, b2):
    v = (b0 << 16) | (b1 << 8) | b2
    if v & 0x800000:
        v -= 1 << 24
    return v

print(f"Opening {PORT}...")
print(f"Saving to {OUTFILE}")
print("Press Ctrl+C to stop.\n")

ser = serial.Serial(PORT, BAUD, timeout=1)
ser.reset_input_buffer()

with open(OUTFILE, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "ch1", "ch2"])

    buf = bytearray()
    good = 0
    drops = 0

    start = time.time()

    first_sid = None
    last_sid = None
    expected_sid = None

    # For true Hz measurement
    last_rate_time = time.time()
    last_rate_sid = None

    try:
        while True:
            chunk = ser.read(4096)
            if chunk:
                buf.extend(chunk)

            while True:
                if len(buf) < PACKET_LEN:
                    break

                idx = buf.find(SYNC)
                if idx < 0:
                    # keep last 1 byte in case it's 0xA5
                    buf[:] = buf[-1:]
                    break

                if idx > 0:
                    del buf[:idx]

                if len(buf) < PACKET_LEN:
                    break

                pkt = buf[:PACKET_LEN]
                del buf[:PACKET_LEN]

                sid = pkt[2] | (pkt[3] << 8) | (pkt[4] << 16) | (pkt[5] << 24)

                if first_sid is None:
                    first_sid = sid
                    expected_sid = sid
                    last_rate_sid = sid
                    last_rate_time = time.time()

                # drop detection
                if expected_sid is not None and sid != expected_sid:
                    if sid > expected_sid:
                        drops += (sid - expected_sid)
                    expected_sid = sid

                expected_sid += 1
                last_sid = sid

                ch1 = s24_from_be3(pkt[6], pkt[7], pkt[8])
                ch2 = s24_from_be3(pkt[9], pkt[10], pkt[11])

                w.writerow([sid, ch1, ch2])
                good += 1

                if good % 1000 == 0:
                    now = time.time()
                    elapsed = now - start
                    wall_rate = good / elapsed if elapsed > 0 else 0

                    # True sample frequency from sid vs wall time over last 1000 samples
                    dt = now - last_rate_time
                    ds = sid - last_rate_sid if last_rate_sid is not None else 0
                    true_hz = (ds / dt) if dt > 0 else 0.0

                    last_rate_time = now
                    last_rate_sid = sid

                    print(
                        f"Captured {good}"f" true_hz: {true_hz:.1f} samp/s | drops: {drops}"
                    )

    except KeyboardInterrupt:
        print("\nStopping capture...")

ser.close()

end_time = time.time()

avg_hz = 0.0
if first_sid is not None and last_sid is not None and end_time > start:
    total_time = end_time - start
    total_samples = last_sid - first_sid
    avg_hz = total_samples / total_time

print(f"\nSaved {good} packets")
print(f"Average sampling rate: {avg_hz:.2f} samples/sec")
print(f"Drops: {drops}")