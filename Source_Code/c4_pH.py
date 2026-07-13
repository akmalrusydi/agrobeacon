import time
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# =========================================================
# CONFIGURATION / CALIBRATION DATA
# =========================================================
PH_SLOPE = -19.67    
PH_OFFSET = 38.96   

def get_smoothed_voltage(ph_sensor, samples=10):
    total_voltage = 0
    for _ in range(samples):
        total_voltage += ph_sensor.voltage
        time.sleep(0.01)
    return total_voltage / samples

def read_ph(ads):

    try:
        ph_sensor = AnalogIn(ads, 1)
        voltage = get_smoothed_voltage(ph_sensor, samples=10)
        
        # Formula penukaran voltan ke nilai pH
        ph_value = (PH_SLOPE * voltage) + PH_OFFSET
        ph_value = max(0, min(14, ph_value))  # Hadkan julat pH 0-14

        if ph_value < 5.5:
            ph_status = "Strong Acidic (Sangat Asid)"
        elif ph_value < 6.5:
            ph_status = "Acidic (Asid)"
        elif ph_value <= 7.5:
            ph_status = "Neutral"
        elif ph_value <= 8.5:
            ph_status = "Alkaline (Alkali)"
        else:
            ph_status = "Strong Alkaline (Sangat Alkali)"

        return {
            "ph_voltage": round(voltage, 3),
            "ph": round(ph_value, 2),
            "ph_status": ph_status
        }
    except Exception as e:
        raise e
