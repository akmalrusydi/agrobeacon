import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# =========================================================
# I2C & ADS1115 SETUP
# =========================================================
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Tetapkan GAIN = 1 (Julat voltan: +/- 4.096V)
# Sesuai untuk kebanyakan sensor pH analog (0V - 5V, dibahagikan ke 3.3V)
ads.gain = 1 

# Sambungkan probe ke Channel 1 (A1)
ph_sensor = AnalogIn(ads, 1)

# =========================================================
# CONFIGURATION / CALIBRATION DATA
# =========================================================
# Sila update nilai ini selepas anda buat proses kalibrasi
PH_SLOPE = 3.97     
PH_OFFSET = -2.92   

# =========================================================
# FUNCTION: READ VOLTAGE WITH FILTER (SMOOTHING)
# =========================================================
def get_smoothed_voltage(samples=10):
    """Mengambil beberapa sampel voltan dan mengira purata untuk tapis noise"""
    total_voltage = 0
    for _ in range(samples):
        total_voltage += ph_sensor.voltage
        time.sleep(0.02)  # Selang masa kecil antara sampel
    return total_voltage / samples

# =========================================================
# MAIN FUNCTION
# =========================================================
def read_ph(mode="RUN"):
    try:
        # Ambil bacaan voltan yang telah ditapis (purata 15 sampel)
        voltage = get_smoothed_voltage(samples=15)

        if mode == "CALIBRATE":
            # Mod ini digunakan untuk anda cari nilai voltan cecair buffer
            return {
                "mode": "CALIBRATION MODE",
                "voltage": round(voltage, 3)
            }

        # Mod pembacaan sebenar (RUN)
        ph_value = (PH_SLOPE * voltage) + PH_OFFSET
        ph_value = max(0, min(14, ph_value))  # Hadkan julat pH 0-14

        # Penentuan status tanah/air
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
            "mode": "RUN MODE",
            "ph_voltage": round(voltage, 3),
            "ph": round(ph_value, 2),
            "ph_status": ph_status
        }

    except Exception as e:
        print("PH SENSOR ERROR:", e)
        return None

# =========================================================
# CONTOH CARA PENGGUNAAN
# =========================================================
if __name__ == "__main__":
    print("Memulakan bacaan sensor pH...")
    time.sleep(1)
    
    while True:
        # TUKAR KEPADA "CALIBRATE" JIKA MAHU KALIBRASI PROBE
        data = read_ph(mode="RUN") 
        
        if data:
            if data["mode"] == "RUN MODE":
                print(f"Voltan: {data['ph_voltage']}V | Nilai pH: {data['ph']} | Status: {data['ph_status']}")
            else:
                print(f"Mod Kalibrasi -> Voltan Semasa: {data['voltage']}V")
                
        time.sleep(2)  # Bacaan dikemas kini setiap 2 saat