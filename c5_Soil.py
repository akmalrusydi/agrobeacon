import board
import busio

import adafruit_ads1x15.ads1115 as ADS

from adafruit_ads1x15.analog_in import AnalogIn

# =========================================================
# I2C SETUP
# =========================================================

i2c = busio.I2C(
    board.SCL,
    board.SDA
)

# =========================================================
# ADS1115 SETUP
# =========================================================

ads = ADS.ADS1115(i2c)

# =========================================================
# SOIL SENSOR CHANNEL
# =========================================================

soil_sensor = AnalogIn(
    ads,
    0
)

# =========================================================
# CALIBRATION
# =========================================================

DRY_VOLTAGE = 2.30

WET_VOLTAGE = 1.65

# =========================================================
# READ SOIL FUNCTION
# =========================================================

def read_soil():

    try:

        voltage = soil_sensor.voltage

        # =============================================
        # CALCULATE MOISTURE %
        # =============================================

        moisture = (

            (DRY_VOLTAGE - voltage)

            /

            (DRY_VOLTAGE - WET_VOLTAGE)

        ) * 100

        # =============================================
        # LIMIT RANGE
        # =============================================

        moisture = max(
            0,
            min(100, moisture)
        )

        # =============================================
        # SOIL STATUS
        # =============================================

        if moisture < 20:

            status = "Dry"

        elif moisture < 40:

            status = "Moist"

        elif moisture < 70:

            status = "Wet"

        else:

            status = "Very Wet"

        # =============================================
        # RETURN DATA
        # =============================================

        return {

            "soil_voltage":
                round(voltage, 3),

            "soil_moisture":
                round(moisture, 1),

            "soil_status":
                status
        }

    except Exception as e:

        print("SOIL ERROR:", e)

        return None