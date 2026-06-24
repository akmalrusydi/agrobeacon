# =========================================================
# AGROBEACON RUN ALL SYSTEM
# STABLE VERSION
# =========================================================

import time
import socket
import subprocess

# =========================================================
# IMPORT SENSOR MODULES
# =========================================================

from c3_DHT22 import read_dht
from c5_Soil import read_soil
from c4_pH import read_ph
from c7_GPS import read_gps
from c6_wind import read_wind

from c2_Cloud import connect_tb
from c2_Cloud import send_data

# =========================================================
# INTERNET STATUS
# =========================================================

def check_internet():

    try:

        socket.create_connection(
            ("8.8.8.8", 53),
            timeout=2
        )

        return 1

    except:

        return 0

# =========================================================
# WIFI SIGNAL STRENGTH
# =========================================================

def get_wifi_strength():

    try:

        result = subprocess.check_output(
            "iwconfig wlan0",
            shell=True
        ).decode()

        if "Signal level=" in result:

            signal = result.split(
                "Signal level="
            )[1].split(" ")[0]

            signal = signal.replace(
                "dBm",
                ""
            )

            return int(signal)

        return -100

    except:

        return -100

# =========================================================
# SYSTEM START
# =========================================================

print("========================================")
print("     AGROBEACON SYSTEM STARTED")
print("========================================")

# =========================================================
# CONNECT THINGSBOARD
# =========================================================

try:

    connect_tb()

    print("ThingBoard Connected")

except Exception as e:

    print("THINGBOARD ERROR:", e)

# =========================================================
# TIMER
# =========================================================

last_display_time = 0
last_cloud_send = 0
last_gps_read = 0
last_wind_read = 0

DISPLAY_INTERVAL = 2
CLOUD_INTERVAL = 5
GPS_INTERVAL = 2
WIND_INTERVAL = 1

# =========================================================
# CACHE DATA
# =========================================================

gps_data = None
wind_data = None

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        current_time = time.time()

        # =================================================
        # FAST SENSOR
        # =================================================

        dht_data = read_dht()

        soil_data = read_soil()

        ph_data = read_ph()

        # =================================================
        # GPS CONTROL
        # =================================================

        if (
            current_time - last_gps_read >=
            GPS_INTERVAL
        ):

            new_gps = read_gps()

            if new_gps:

                gps_data = new_gps

            last_gps_read = current_time

        # =================================================
        # WIND CONTROL
        # =================================================

        if (
            current_time - last_wind_read >=
            WIND_INTERVAL
        ):

            new_wind = read_wind()

            if new_wind:

                wind_data = new_wind

            last_wind_read = current_time

        # =================================================
        # NETWORK
        # =================================================

        internet_status = check_internet()

        wifi_strength = get_wifi_strength()

        # =================================================
        # TELEMETRY
        # =================================================

        telemetry = {

            "internet":
                internet_status,

            "wifi_strength":
                wifi_strength
        }

        # =================================================
        # ADD SENSOR DATA
        # =================================================

        if dht_data:

            telemetry.update(dht_data)

        if soil_data:

            telemetry.update(soil_data)

        if ph_data:

            telemetry.update(ph_data)

        if gps_data:

            telemetry.update(gps_data)

        if wind_data:

            telemetry.update(wind_data)

        # =================================================
        # DISPLAY
        # =================================================

        if (
            current_time - last_display_time >=
            DISPLAY_INTERVAL
        ):

            print()
            print("========================================")
            print("         AGROBEACON LIVE DATA")
            print("========================================")

            # =============================================
            # AIR SENSOR
            # =============================================

            print()
            print("----- AIR SENSOR -----")

            if dht_data:

                print(
                    "Temperature :",
                    dht_data["temperature"],
                    "°C"
                )

                print(
                    "Humidity    :",
                    dht_data["humidity"],
                    "%RH"
                )

                print(
                    "Air Status  :",
                    dht_data["air_status"]
                )

            else:

                print("DHT22 READ FAILED")

            # =============================================
            # SOIL SENSOR
            # =============================================

            print()
            print("----- SOIL SENSOR -----")

            if soil_data:

                print(
                    "Voltage      :",
                    soil_data["soil_voltage"],
                    "V"
                )

                print(
                    "Moisture     :",
                    soil_data["soil_moisture"],
                    "%"
                )

                print(
                    "Soil Status  :",
                    soil_data["soil_status"]
                )

            else:

                print("SOIL SENSOR FAILED")

            # =============================================
            # PH SENSOR
            # =============================================

            print()
            print("----- PH SENSOR -----")

            if ph_data:

                print(
                    "Voltage    :",
                    ph_data["ph_voltage"],
                    "V"
                )

                print(
                    "pH Value   :",
                    ph_data["ph"]
                )

                print(
                    "pH Status  :",
                    ph_data["ph_status"]
                )

            else:

                print("PH SENSOR FAILED")

            # =============================================
            # GPS
            # =============================================

            print()
            print("----- GPS -----")

            if (
                gps_data
                and
                gps_data.get("gps_fix")
            ):

                print(
                    "Latitude    :",
                    gps_data["latitude"]
                )

                print(
                    "Longitude   :",
                    gps_data["longitude"]
                )

                print(
                    "Satellites  :",
                    gps_data["satellites"]
                )

                print(
                    "HDOP        :",
                    gps_data["hdop"]
                )

                print(
                    "Altitude    :",
                    gps_data["altitude"]
                )

                print(
                    "Speed       :",
                    gps_data["speed"]
                )

                print(
                    "Moving      :",
                    gps_data["moving"]
                )

                print(
                    "Static Mode :",
                    gps_data["static_mode"]
                )

            else:

                if gps_data:

                    print(
                        "GPS STARTUP :",
                        gps_data.get(
                            "startup_progress",
                            "0/40"
                        )
                    )

                    print(
                        "Satellites  :",
                        gps_data.get(
                            "satellites",
                            0
                        )
                    )

                    print(
                        "HDOP        :",
                        gps_data.get(
                            "hdop",
                            99
                        )
                    )

                else:

                    print(
                        "GPS STARTUP : 0/40"
                    )

                print(
                    "Waiting GPS Fix..."
                )

            # =============================================
            # WIND
            # =============================================

            print()
            print("----- WIND SENSOR -----")

            if wind_data:

                print(
                    "Pulses      :",
                    wind_data["wind_pulses"]
                )

                print(
                    "Frequency   :",
                    wind_data["wind_frequency"],
                    "Hz"
                )

                print(
                    "Wind Speed  :",
                    wind_data["wind_speed_ms"],
                    "m/s"
                )

                print(
                    "Wind Speed  :",
                    wind_data["wind_speed_kmh"],
                    "km/h"
                )

                print(
                    "Wind Status :",
                    wind_data["wind_status"]
                )

            else:

                print("WIND SENSOR FAILED")

            # =============================================
            # NETWORK
            # =============================================

            print()
            print("----- NETWORK -----")

            print(
                "Internet     :",
                "Connected"
                if internet_status
                else "Offline"
            )

            print(
                "WiFi Signal  :",
                wifi_strength,
                "dBm"
            )

            print()
            print("========================================")

            last_display_time = current_time

        # =================================================
        # SEND CLOUD
        # =================================================

        if (
            current_time - last_cloud_send >=
            CLOUD_INTERVAL
        ):

            try:

                print()
                print("Sending Telemetry...")
                print(telemetry)

                status = send_data(
                    telemetry
                )

                if status:

                    print(
                        "Telemetry Sent"
                    )

                else:

                    print(
                        "Telemetry Failed"
                    )

            except Exception as cloud_error:

                print(
                    "CLOUD ERROR:",
                    cloud_error
                )

            last_cloud_send = current_time

        # =================================================
        # LOOP DELAY
        # =================================================

        time.sleep(0.2)

    except KeyboardInterrupt:

        print()
        print("AGROBEACON SYSTEM STOPPED")

        break

    except Exception as e:

        print()
        print("RUNALL ERROR:", e)

        time.sleep(1)