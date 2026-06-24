import serial
import time
from datetime import datetime
from pynmea2 import parse

from kalman_filter_gps import KalmanFilterGPS

import RPi.GPIO as GPIO

# ======================
# PPS
# ======================
PPS_PIN = 21

# ======================
# GPIO
# ======================
GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)

GPIO.setup(
    PPS_PIN,
    GPIO.IN,
    pull_up_down=GPIO.PUD_DOWN
)

last_pps = 0

# ======================
# GPS
# ======================
GPS_PORT = "/dev/serial0"
GPS_BAUD = 115200

gps_serial = serial.Serial(
    GPS_PORT,
    GPS_BAUD,
    timeout=1,
    exclusive=False
)

# ======================
# FILTER
# ======================
lat_filter = KalmanFilterGPS()
lon_filter = KalmanFilterGPS()

# ======================
# GPS QUALITY
# ======================
MIN_SATELLITES = 15
MAX_HDOP = 1.2

# ======================
# STATIC HOLD
# ======================
STATIC_DISTANCE = 0.000001
STATIC_TIME_SEC = 20

RAW_FILE = "gps_raw.txt"
FILTERED_FILE = "gps_filtered.txt"

# ======================
# VARIABLES
# ======================
gps_ready = False
static_mode = False

hold_lat = 0
hold_lon = 0

static_start_time = 0

latest_data = {}

# ======================
# STARTUP AVERAGING
# ======================
startup_samples = []
startup_complete = False

print("================================")
print("LC76G GPS + Kalman Filter")
print("Raspberry Pi 4B")
print("PPS GPIO21")
print("================================")

# ======================
# MAIN LOOP
# ======================
while True:

    # ======================
    # READ GPS
    # ======================
    try:

        if gps_serial.in_waiting:

            line = gps_serial.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            try:

                if line.startswith("$GNGGA"):

                    msg = parse(line)

                    latest_data["lat"] = msg.latitude
                    latest_data["lon"] = msg.longitude
                    latest_data["sats"] = msg.num_sats
                    latest_data["hdop"] = float(msg.horizontal_dil)
                    latest_data["alt"] = msg.altitude

                elif line.startswith("$GNRMC"):

                    msg = parse(line)

                    latest_data["speed"] = (
                        float(msg.spd_over_grnd or 0) * 1.852
                    )

            except:
                pass

    except Exception as e:

        print()
        print("================================")
        print("GPS SERIAL ERROR")
        print(e)
        print("RECONNECTING GPS...")
        print("================================")

        try:
            gps_serial.close()
        except:
            pass

        time.sleep(2)

        try:

            gps_serial = serial.Serial(
                GPS_PORT,
                GPS_BAUD,
                timeout=1,
                exclusive=False
            )

            print("GPS RECONNECTED")

        except Exception as reconnect_error:

            print("RECONNECT FAILED :", reconnect_error)

            time.sleep(5)

    # ======================
    # PPS POLLING
    # ======================
    current_pps = GPIO.input(PPS_PIN)

    # Rising edge detect
    if current_pps == 1 and last_pps == 0:

        if "lat" not in latest_data:

            last_pps = current_pps
            continue

        raw_lat = latest_data["lat"]
        raw_lon = latest_data["lon"]

        sats = int(latest_data.get("sats", 0))
        hdop = float(latest_data.get("hdop", 99))

        if sats < MIN_SATELLITES:

            print(f"LOW SATELLITES : {sats}")

            last_pps = current_pps
            continue

        if hdop > MAX_HDOP:

            print(f"HDOP TOO HIGH : {hdop}")

            last_pps = current_pps
            continue

        speed = float(latest_data.get("speed", 0))

        # More sensitive static detection
        moving = speed > 0.3

        # ======================
        # FILTER
        # ======================
        filtered_lat = lat_filter.update(
            raw_lat,
            moving
        )

        filtered_lon = lon_filter.update(
            raw_lon,
            moving
        )

        # ======================
        # STARTUP AVERAGING
        # ======================
        if not startup_complete:

            startup_samples.append(
                (filtered_lat, filtered_lon)
            )

            print(
                f"COLLECTING STARTUP SAMPLES : "
                f"{len(startup_samples)}/100"
            )

            if len(startup_samples) >= 100:

                avg_lat = sum(
                    x[0] for x in startup_samples
                ) / len(startup_samples)

                avg_lon = sum(
                    x[1] for x in startup_samples
                ) / len(startup_samples)

                hold_lat = avg_lat
                hold_lon = avg_lon

                filtered_lat = avg_lat
                filtered_lon = avg_lon

                startup_complete = True
                gps_ready = True

                print()
                print("================================")
                print("STARTUP GPS AVERAGING COMPLETE")
                print(f"AVG LAT : {avg_lat:.7f}")
                print(f"AVG LON : {avg_lon:.7f}")
                print("================================")

            last_pps = current_pps
            time.sleep(0.01)
            continue

        # ======================
        # STATIC DETECTION
        # ======================
        lat_diff = abs(filtered_lat - hold_lat)
        lon_diff = abs(filtered_lon - hold_lon)

        if (
            lat_diff < STATIC_DISTANCE and
            lon_diff < STATIC_DISTANCE and
            not moving
        ):

            if static_start_time == 0:
                static_start_time = time.time()

            if (
                time.time() - static_start_time >
                STATIC_TIME_SEC
            ):

                static_mode = True

        else:

            static_mode = False
            static_start_time = 0

            hold_lat = filtered_lat
            hold_lon = filtered_lon

        # ======================
        # HOLD POSITION
        # ======================
        if static_mode:

            filtered_lat = hold_lat
            filtered_lon = hold_lon

        else:

            hold_lat = filtered_lat
            hold_lon = filtered_lon

        # ======================
        # TIME
        # ======================
        now = datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        # ======================
        # DISPLAY
        # ======================
        print()
        print("=========== GPS DATA ===========")

        print(f"RAW LATITUDE       : {raw_lat:.7f}")
        print(f"RAW LONGITUDE      : {raw_lon:.7f}")

        print()

        print(f"FILTERED LATITUDE  : {filtered_lat:.7f}")
        print(f"FILTERED LONGITUDE : {filtered_lon:.7f}")

        print()

        print(f"SATELLITES         : {sats}")
        print(f"HDOP               : {hdop:.2f}")
        print(f"SPEED (km/h)       : {speed:.2f}")

        print(f"STATIC MODE        : {'YES' if static_mode else 'NO'}")

        print("================================")

        # ======================
        # SAVE RAW
        # ======================
        with open(RAW_FILE, "a") as f:

            f.write(
                f"{now},"
                f"{raw_lat:.7f},"
                f"{raw_lon:.7f},"
                f"{sats},"
                f"{hdop:.2f}\n"
            )

        # ======================
        # SAVE FILTERED
        # ======================
        with open(FILTERED_FILE, "a") as f:

            f.write(
                f"{now},"
                f"{filtered_lat:.7f},"
                f"{filtered_lon:.7f},"
                f"{sats},"
                f"{hdop:.2f},"
                f"{'STATIC' if static_mode else 'MOVING'}\n"
            )

    # Update PPS state
    last_pps = current_pps

    time.sleep(0.01)