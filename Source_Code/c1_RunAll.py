# =========================================================
# AGROBEACON RUN ALL SYSTEM 
# =========================================================

import time
import socket
import subprocess
import board
import busio
import adafruit_ads1x15.ads1115 as ADS

# --- IMPORT MODUL SENSOR ---
from c3_DHT22 import read_dht
from c5_Soil import read_soil
from c4_pH import read_ph
from c7_GPS import read_gps
from c6_wind import read_wind

# --- IMPORT CLOUD MQTT ---
from c2_Cloud import connect_tb, send_data

# --- NETWORK UTILITIES ---
def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return 1
    except:
        return 0

def get_wifi_strength():
    try:
        result = subprocess.check_output("iwconfig wlan0", shell=True).decode()
        if "Signal level=" in result:
            signal = result.split("Signal level=")[1].split(" ")[0]
            signal = signal.replace("dBm", "")
            return int(signal)
        return 0
    except:
        return 0

def main():
    print("========================================")
    print("     AGROBEACON SYSTEM STARTED")
    print("========================================")

    # =========================================================
    # SINGLE I2C & ADS1115 INITIALIZATION (SHARED RESOURCE)
    # =========================================================
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1
        i2c_available = True
    except Exception as init_e:
        print(f"CRITICAL HARDWARE ERROR: Gagal initialize Master I2C: {init_e}")
        i2c_available = False

    # --- CONNECT TO CLOUD ---
    connect_tb()

    # --- INTERVAL SETTINGS ---
    DISPLAY_INTERVAL = 2
    CLOUD_INTERVAL = 5

    last_display_time = 0
    last_cloud_send = 0

    while True:
        try:
            current_time = time.time()
            telemetry = {"mode": "RUN MODE"}

            # =================================================
            # 1. READ DHT22 (SUHU UDARA)
            # =================================================
            dht_data = read_dht()
            if dht_data:
                telemetry.update(dht_data)

            # =================================================
            # 2. READ SOIL SENSOR VIA SHARED ADS
            # =================================================
            soil_failed = False
            if i2c_available:
                try:
                    soil_data = read_soil(ads) # Hantar objek ads tunggal
                    if soil_data:
                        telemetry.update(soil_data)
                except Exception as e:
                    print(f"SOIL ERROR: [Errno 5] Input/output error atau pin longgar -> {e}")
                    soil_failed = True
            else:
                soil_failed = True

            # Tambah delay mikro saat untuk mengelakkan pertembungan pembacaan I2C register
            time.sleep(0.1) 

            # =================================================
            # 3. READ pH SENSOR VIA SHARED ADS
            # =================================================
            ph_failed = False
            if i2c_available:
                try:
                    ph_data = read_ph(ads) # Hantar objek ads tunggal
                    if ph_data:
                        telemetry.update(ph_data)
                except Exception as e:
                    print(f"PH SENSOR ERROR: [Errno 5] Input/output error atau pin longgar -> {e}")
                    ph_failed = True
            else:
                ph_failed = True

            # =================================================
            # 4. READ GPS SENSOR (UART SERIAL)
            # =================================================
            gps_data = read_gps()
            if gps_data:
                telemetry.update(gps_data)

            # =================================================
            # 5. READ WIND SENSOR (GPIO PULSE)
            # =================================================
            wind_data = read_wind()
            if wind_data:
                telemetry.update(wind_data)

            # =================================================
            # 6. READ NETWORK STATUS
            # =================================================
            internet = check_internet()
            wifi_strength = get_wifi_strength()
            telemetry.update({
                "internet": internet,
                "wifi_strength": wifi_strength
            })

            # =================================================
            # DISPLAY LIVE TERMINAL DASHBOARD
            # =================================================
            if current_time - last_display_time >= DISPLAY_INTERVAL:
                print("\n========================================")
                print("         AGROBEACON LIVE DATA")
                print("========================================")

                print("\n----- AIR SENSOR -----")
                if "temperature" in telemetry:
                    print(f"Temperature : {telemetry['temperature']} °C")
                    print(f"Humidity    : {telemetry['humidity']} %RH")
                    print(f"Air Status  : {telemetry['air_status']}")
                else:
                    print("AIR SENSOR FAILED")

                print("\n----- SOIL SENSOR -----")
                if not soil_failed and "soil_voltage" in telemetry:
                    print(f"Voltage      : {telemetry['soil_voltage']} V")
                    print(f"Moisture     : {telemetry['soil_moisture']} %")
                    print(f"Soil Status  : {telemetry['soil_status']}")
                else:
                    print("SOIL SENSOR FAILED")

                print("\n----- PH SENSOR -----")
                if not ph_failed and "ph_voltage" in telemetry:
                    print(f"Voltage    : {telemetry['ph_voltage']} V")
                    print(f"pH Value   : {telemetry['ph']}")
                    print(f"pH Status  : {telemetry['ph_status']}")
                else:
                    print("PH SENSOR FAILED")

                print("\n----- GPS -----")
                if gps_data and gps_data.get("gps_fix"):
                    print(f"Latitude  : {telemetry.get('latitude')} N")
                    print(f"Longitude : {telemetry.get('longitude')} E")
                    print(f"Satellites: {telemetry.get('satellites')}")
                else:
                    print("Waiting GPS Fix...")

                print("\n----- WIND SENSOR -----")
                if "wind_pulses" in telemetry:
                    print(f"Pulses      : {telemetry['wind_pulses']}")
                    print(f"Frequency   : {telemetry['wind_frequency']} Hz")
                    print(f"Wind Speed  : {telemetry['wind_speed_ms']} m/s")
                    print(f"Wind Speed  : {telemetry['wind_speed_kmh']} km/h")
                    print(f"Wind Status : {telemetry['wind_status']}")

                print("\n----- NETWORK -----")
                print(f"Internet     : {'Connected' if internet else 'Disconnected'}")
                print(f"WiFi Signal  : {wifi_strength} dBm")
                print("========================================")

                last_display_time = current_time

            # =================================================
            # SEND DATA TO THINGSBOARD CLOUD
            # =================================================
            if current_time - last_cloud_send >= CLOUD_INTERVAL:
                print("\nSending Telemetry...")
                # Buat salinan payload untuk dihantar ke cloud
                cloud_payload = telemetry.copy()
                # Buang status teks jika tidak diperlukan dalam penjimatan data cloud
                status = send_data(cloud_payload)
                if status:
                    print("Telemetry Sent")
                else:
                    print("Telemetry Failed")
                last_cloud_send = current_time

            # Mengurangkan kelajuan kitaran loop utama untuk kestabilan pembacaan
            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nAGROBEACON SYSTEM STOPPED")
            break
        except Exception as loop_e:
            print(f"\nRUNALL LOOP ERROR: {loop_e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
