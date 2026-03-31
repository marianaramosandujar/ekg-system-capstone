import serial
import csv
import time

PORT = "COM10"
BAUD = 115200
OUTFILE = "ekg_capture.csv"

SYNC = b"\xA5\x5A"
PACKET_LEN = 12  # 2 sync + 10 bytes payload

VREF = 2.42
GAIN = 6          # set to 6 or 12 to match ADS config
FS = (2**23 - 1)

def s24_from_be3(b0, b1, b2):
    v = (b0 << 16) | (b1 << 8) | b2
    if v & 0x800000:
        v -= 1 << 24
    return v

def code_to_mv(code, vref=VREF, gain=GAIN):
    return (1000.0 * code * vref) / (gain * FS)

print(f"Opening {PORT}...")
print(f"Saving to {OUTFILE}")
print("Press Ctrl+C to stop.\n")

ser = serial.Serial(PORT, BAUD, timeout=1)
ser.reset_input_buffer()

with open(OUTFILE, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sample_id", "ch1_code", "ch2_code", "ch1_mv", "ch2_mv"])

    buf = bytearray()
    good = 0
    drops = 0

    start = time.time()

    first_sid = None
    last_sid = None
    expected_sid = None

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

                if expected_sid is not None and sid != expected_sid:
                    if sid > expected_sid:
                        drops += (sid - expected_sid)
                    expected_sid = sid

                expected_sid += 1
                last_sid = sid

                ch1_code = s24_from_be3(pkt[6], pkt[7], pkt[8])
                ch2_code = s24_from_be3(pkt[9], pkt[10], pkt[11])

                ch1_mv = code_to_mv(ch1_code)
                ch2_mv = code_to_mv(ch2_code)

                w.writerow([sid, ch1_code, ch2_code, ch1_mv, ch2_mv])
                good += 1

                if good % 1000 == 0:
                    now = time.time()
                    elapsed = now - start
                    wall_rate = good / elapsed if elapsed > 0 else 0

                    dt = now - last_rate_time
                    ds = sid - last_rate_sid if last_rate_sid is not None else 0
                    true_hz = (ds / dt) if dt > 0 else 0.0

                    last_rate_time = now
                    last_rate_sid = sid

                    print(
                        f"Captured {good} true_hz: {true_hz:.1f} samp/s | "
                        f"ch1={ch1_mv:.4f} mV | ch2={ch2_mv:.4f} mV | drops: {drops}"
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