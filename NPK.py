import hid
import time
from collections import deque

# =========================================================
# CRC FUNCTION
# =========================================================

def crc16(data):

    crc = 0xFFFF

    for b in data[:-2]:

        crc ^= b

        for _ in range(8):

            if crc & 1:

                crc = (crc >> 1) ^ 0xA001

            else:

                crc >>= 1

    return crc

# =========================================================
# HID SETUP
# =========================================================

VID = 0x0487
PID = 0x0007

h = hid.device()

h.open(VID, PID)

time.sleep(1)

# =========================================================
# COMMAND SETUP
# =========================================================

cmd = [0] * 64

cmd[0] = 0x55
cmd[1] = 0x01
cmd[2] = 0x22

crc = crc16(cmd)

cmd[62] = crc & 0xFF
cmd[63] = (crc >> 8) & 0xFF

# =========================================================
# FILTER BUFFER
# =========================================================

buffer = {

    "Temperature": deque(maxlen=5),

    "Moisture": deque(maxlen=5),

    "EC": deque(maxlen=5),

    "pH": deque(maxlen=5),

    "N": deque(maxlen=5),

    "P": deque(maxlen=5),

    "K": deque(maxlen=5),
}

# =========================================================
# SMOOTHING FUNCTION
# =========================================================

def smooth(key, val):

    buffer[key].append(val)

    return sum(buffer[key]) / len(buffer[key])

# =========================================================
# DECODE FUNCTION
# =========================================================

def decode_data(data):

    result = {}

    try:

        i = 0

        while i < len(data) - 6:

            if (

                data[i] == 0 and
                data[i + 2] == 4 and
                data[i + 3] == 0 and
                data[i + 4] == 2

            ):

                param_id = data[i + 1]

                raw = (
                    (data[i + 5] << 8)
                    |
                    data[i + 6]
                )

                # =========================================
                # PARAMETER MAPPING
                # =========================================

                if param_id == 0:

                    result["temperature"] = smooth(
                        "Temperature",
                        raw / 10
                    )

                elif param_id == 1:

                    result["moisture"] = smooth(
                        "Moisture",
                        raw / 10
                    )

                elif param_id == 2:

                    result["ec"] = smooth(
                        "EC",
                        raw
                    )

                elif param_id == 3:

                    result["ph"] = smooth(
                        "pH",
                        raw / 10
                    )

                elif param_id == 4:

                    result["nitrogen"] = smooth(
                        "N",
                        raw
                    )

                elif param_id == 5:

                    result["phosphorus"] = smooth(
                        "P",
                        raw
                    )

                elif param_id == 6:

                    result["potassium"] = smooth(
                        "K",
                        raw
                    )

                i += 7

            else:

                i += 1

    except Exception as e:

        print("NPK DECODE ERROR:", e)

    return result

# =========================================================
# READ NPK FUNCTION
# =========================================================

def read_npk():

    try:

        h.write([0x00] + cmd)

        time.sleep(0.2)

        data = h.read(64, 1000)

        if data:

            decoded = decode_data(data)

            return decoded

        else:

            return None

    except Exception as e:

        print("NPK ERROR:", e)

        return None