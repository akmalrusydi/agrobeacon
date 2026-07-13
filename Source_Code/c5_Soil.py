import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# =========================================================
# CALIBRATION VOLTAGE (Disesuaikan untuk Maker Soil 3.3V)
# =========================================================

DRY_VOLTAGE = 2.22  # Tukar ke 2.65V (Sebab pada 3.3V, open air biasanya sekitar ini)
WET_VOLTAGE = 1.44  # Nilai voltan apabila dimasukkan ke dalam air

def read_soil(ads):

    try:
        soil_sensor = AnalogIn(ads, 0)
        voltage = soil_sensor.voltage

        # Kira peratusan kelembapan (Skala Terbalik)
        moisture = ((DRY_VOLTAGE - voltage) / (DRY_VOLTAGE - WET_VOLTAGE)) * 100
        moisture = max(0, min(100, moisture)) # Hadkan range 0-100%

        if moisture < 20:
            status = "Dry"
        elif moisture < 40:
            status = "Moist"
        elif moisture < 70:
            status = "Wet"
        else:
            status = "Very Wet"

        return {
            "soil_voltage": round(voltage, 3),
            "soil_moisture": round(moisture, 1),
            "soil_status": status
        }
    except Exception as e:
        raise e
