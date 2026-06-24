import serial
import time
from pynmea2 import parse

from c7_1_kalman_filter_gps import KalmanFilterGPS

import RPi.GPIO as GPIO

# =====================================================
# PPS
# =====================================================

PPS_PIN = 21

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)

GPIO.setup(
    PPS_PIN,
    GPIO.IN,
    pull_up_down=GPIO.PUD_DOWN
)

# =====================================================
# GPS SERIAL
# =====================================================

GPS_PORT = "/dev/serial0"

GPS_BAUD = 115200

gps_serial = serial.Serial(
    GPS_PORT,
    GPS_BAUD,
    timeout=1,
    exclusive=False
)

# =====================================================
# FILTER
# =====================================================

lat_filter = KalmanFilterGPS()

lon_filter = KalmanFilterGPS()

# =====================================================
# SETTINGS
# =====================================================

MIN_SATELLITES = 10

MAX_HDOP = 1.2

STATIC_DISTANCE = 0.0000004

STATIC_TIME_SEC = 15

# =====================================================
# OUTLIER SETTINGS
# =====================================================

MAX_JUMP = 0.000008

# =====================================================
# VARIABLES
# =====================================================

gps_ready = False

static_mode = False

hold_lat = 0

hold_lon = 0

static_start_time = 0

latest_data = {}

# =====================================================
# STARTUP AVERAGING
# =====================================================

startup_samples = []

STARTUP_SAMPLE_TARGET = 40

startup_complete = False

# =====================================================
# EXTRA FILTER BUFFER
# =====================================================

lat_history = []

lon_history = []

FILTER_WINDOW = 8

# =====================================================
# OUTLIER MEMORY
# =====================================================

last_valid_lat = None

last_valid_lon = None

# =====================================================
# READ GPS FUNCTION
# =====================================================

def read_gps():

    global gps_serial

    global gps_ready
    global static_mode

    global hold_lat
    global hold_lon

    global static_start_time

    global latest_data

    global startup_samples
    global startup_complete

    global lat_history
    global lon_history

    global last_valid_lat
    global last_valid_lon

    try:

        # =================================================
        # READ SERIAL
        # =================================================

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

                    latest_data["hdop"] = float(
                        msg.horizontal_dil or 99
                    )

                    latest_data["alt"] = float(
                        msg.altitude or 0
                    )

                elif line.startswith("$GNRMC"):

                    msg = parse(line)

                    latest_data["speed"] = (

                        float(
                            msg.spd_over_grnd or 0
                        )

                        *

                        1.852
                    )

            except:
                pass

        # =================================================
        # WAIT DATA
        # =================================================

        if "lat" not in latest_data:

            return None

        # =============================================
        # RAW DATA
        # =============================================

        raw_lat = latest_data["lat"]

        raw_lon = latest_data["lon"]

        sats = int(
            latest_data.get("sats", 0)
        )

        hdop = float(
            latest_data.get("hdop", 99)
        )

        altitude = float(
            latest_data.get("alt", 0)
        )

        speed = float(
            latest_data.get("speed", 0)
        )

        # =============================================
        # GPS FIX STATUS
        # =============================================

        gps_fix = True

        if sats < MIN_SATELLITES:

            gps_fix = False

        if hdop > MAX_HDOP:

            gps_fix = False

        # =============================================
        # DEBUG
        # =============================================

        print(
            f"GPS DEBUG | "
            f"SATS: {sats} | "
            f"HDOP: {hdop} | "
            f"FIX: {gps_fix}"
        )

        # =============================================
        # RETURN PARTIAL DATA
        # =============================================

        if not gps_fix:

            return {

                "gps_fix":
                    False,

                "satellites":
                    sats,

                "hdop":
                    round(hdop, 2),

                "altitude":
                    round(altitude, 2),

                "speed":
                    round(speed, 2),

                "startup_progress":
                    f"{len(startup_samples)}/{STARTUP_SAMPLE_TARGET}"
            }

        # =============================================
        # OUTLIER KILLER
        # =============================================

        if last_valid_lat is not None:

            lat_jump = abs(
                raw_lat - last_valid_lat
            )

            lon_jump = abs(
                raw_lon - last_valid_lon
            )

            if (

                lat_jump > MAX_JUMP

                or

                lon_jump > MAX_JUMP
            ):

                print(
                    "GPS OUTLIER REJECTED"
                )

                raw_lat = last_valid_lat

                raw_lon = last_valid_lon

        # =============================================
        # FILTER
        # =============================================

        filtered_lat = lat_filter.update(
            raw_lat
        )

        filtered_lon = lon_filter.update(
            raw_lon
        )

        # =============================================
        # EXTRA AVERAGING
        # =============================================

        lat_history.append(filtered_lat)

        lon_history.append(filtered_lon)

        if len(lat_history) > FILTER_WINDOW:

            lat_history.pop(0)

        if len(lon_history) > FILTER_WINDOW:

            lon_history.pop(0)

        filtered_lat = (

            sum(lat_history)

            /

            len(lat_history)
        )

        filtered_lon = (

            sum(lon_history)

            /

            len(lon_history)
        )

        # =============================================
        # SAVE VALID POSITION
        # =============================================

        last_valid_lat = filtered_lat

        last_valid_lon = filtered_lon

        # =============================================
        # STARTUP AVERAGING
        # =============================================

        if not startup_complete:

            startup_samples.append(
                (
                    filtered_lat,
                    filtered_lon
                )
            )

            print(
                f"GPS STARTUP : "
                f"{len(startup_samples)}"
                f"/{STARTUP_SAMPLE_TARGET}"
            )

            # =========================================
            # COMPLETE
            # =========================================

            if (
                len(startup_samples)
                >=
                STARTUP_SAMPLE_TARGET
            ):

                avg_lat = sum(

                    x[0]
                    for x in startup_samples

                ) / len(startup_samples)

                avg_lon = sum(

                    x[1]
                    for x in startup_samples

                ) / len(startup_samples)

                hold_lat = avg_lat

                hold_lon = avg_lon

                startup_complete = True

                gps_ready = True

                print(
                    "GPS STARTUP COMPLETE"
                )

            return {

                "gps_fix":
                    False,

                "satellites":
                    sats,

                "hdop":
                    round(hdop, 2),

                "altitude":
                    round(altitude, 2),

                "speed":
                    round(speed, 2),

                "startup_progress":
                    f"{len(startup_samples)}/{STARTUP_SAMPLE_TARGET}"
            }

        # =============================================
        # STATIC DETECTION
        # =============================================

        lat_diff = abs(
            filtered_lat - hold_lat
        )

        lon_diff = abs(
            filtered_lon - hold_lon
        )

        if (

            lat_diff < STATIC_DISTANCE

            and

            lon_diff < STATIC_DISTANCE
        ):

            if static_start_time == 0:

                static_start_time = time.time()

            if (

                time.time()
                -
                static_start_time

                >

                STATIC_TIME_SEC
            ):

                static_mode = True

        else:

            static_mode = False

            static_start_time = 0

            hold_lat = filtered_lat

            hold_lon = filtered_lon

        # =============================================
        # HOLD POSITION
        # =============================================

        if static_mode:

            filtered_lat = hold_lat

            filtered_lon = hold_lon

        else:

            hold_lat = (

                hold_lat * 0.95

                +

                filtered_lat * 0.05
            )

            hold_lon = (

                hold_lon * 0.95

                +

                filtered_lon * 0.05
            )

        # =============================================
        # FINAL DATA
        # =============================================

        return {

            "gps_fix":
                True,

            "latitude":
                round(filtered_lat, 7),

            "longitude":
                round(filtered_lon, 7),

            "satellites":
                sats,

            "hdop":
                round(hdop, 2),

            "altitude":
                round(altitude, 2),

            "speed":
                round(speed, 2),

            "moving":
                False,

            "static_mode":
                static_mode,

            "startup_progress":
                f"{STARTUP_SAMPLE_TARGET}/{STARTUP_SAMPLE_TARGET}"
        }

    except Exception as e:

        print("GPS ERROR :", e)

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

            print(
                "GPS RECONNECT FAILED :",
                reconnect_error
            )

        return None