import board
import adafruit_dht
import time

# =========================================================
# DHT22 SETUP
# =========================================================

DHT_PIN = board.D22

dht = adafruit_dht.DHT22(
    DHT_PIN,
    use_pulseio=False
)

# =========================================================
# DHT TIMER
# =========================================================

last_read_time = 0

DHT_INTERVAL = 2

last_data = None

# =========================================================
# READ DHT22 FUNCTION
# =========================================================

def read_dht():

    global dht
    global last_read_time
    global last_data

    current_time = time.time()

    # =====================================================
    # LIMIT READ RATE
    # =====================================================

    if (
        current_time - last_read_time <
        DHT_INTERVAL
    ):

        return last_data

    last_read_time = current_time

    # =====================================================
    # RETRY READ
    # =====================================================

    for i in range(3):

        try:

            temperature = dht.temperature

            humidity = dht.humidity

            if (
                temperature is not None and
                humidity is not None
            ):

                # =========================================
                # AIR STATUS
                # =========================================

                if humidity < 40:

                    air_status = "Dry Air"

                elif humidity <= 60:

                    air_status = "Comfortable"

                elif humidity <= 80:

                    air_status = "Humid"

                else:

                    air_status = "Very Humid"

                # =========================================
                # SAVE DATA
                # =========================================

                last_data = {

                    "temperature":
                    round(temperature, 1),

                    "humidity":
                    round(humidity, 1),

                    "air_status":
                    air_status
                }

                return last_data

        # =================================================
        # DHT RUNTIME ERROR
        # =================================================

        except RuntimeError as error:

            print(
                "DHT Runtime Error:",
                error
            )

            # =============================================
            # RESET SENSOR
            # =============================================

            try:

                dht.exit()

            except:

                pass

            time.sleep(1)

            try:

                dht = adafruit_dht.DHT22(
                    DHT_PIN,
                    use_pulseio=False
                )

            except Exception as reset_error:

                print(
                    "DHT RESET ERROR:",
                    reset_error
                )

            time.sleep(1)

        # =================================================
        # OTHER ERROR
        # =================================================

        except Exception as error:

            print(
                "DHT ERROR:",
                error
            )

            return last_data

    # =====================================================
    # FAILED AFTER RETRY
    # =====================================================

    return last_data