import pandas as pd
import matplotlib.pyplot as plt


def validate_firmware_csv(file_path):
    """
    Validates firmware CSV format:

    Column 1: Sample ID
    Column 2: Timestamp
    Column 3: Status
    Column 4: Channel 1
    Column 5: Channel 2
    """

    # Read raw CSV 
    df = pd.read_csv(file_path, header=None)

    if df.shape[1] < 5:
        raise ValueError("Firmware CSV does not contain 5 columns.")

    # Assign explicit column names
    df.columns = ["sample_id", "timestamp", "status", "ch1", "ch2"]
    time = df["timestamp"].astype(float)
    ch1 = df["ch1"].astype(float)
    ch2 = df["ch2"].astype(float)

    # channel 1
    plt.figure()
    plt.plot(time, ch1)
    plt.xlabel("Timestamp")
    plt.ylabel("Channel 1")
    plt.title("Firmware Validation: Channel 1")
    plt.grid(True)
    plt.show()

    # channel 2
    plt.figure()
    plt.plot(time, ch2)
    plt.xlabel("Timestamp")
    plt.ylabel("Channel 2")
    plt.title("Firmware Validation: Channel 2")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 firmware_csv_validator.py <path_to_csv>")
        sys.exit(1)

    validate_firmware_csv(sys.argv[1])
    