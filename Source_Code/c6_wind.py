from gpiozero import Button
import time

# =========================================================
# CONFIGURATION
# =========================================================

WIND_PIN = 17

SPEED_FACTOR = 0.058

INTERVAL_SEC = 3.0

# =========================================================
# SENSOR SETUP
# =========================================================

wind_sensor = Button(
    WIND_PIN,
    pull_up=True,
    bounce_time=0.001
)

# =========================================================
# GLOBAL VARIABLES
# =========================================================

pulse_count = 0

filtered_speed = 0.0

last_read_time = time.time()

last_data = {

    "wind_pulses": 0,

    "wind_frequency": 0.0,

    "wind_speed_ms": 0.0,

    "wind_speed_kmh": 0.0,

    "wind_status": "No Wind"
}

# =========================================================
# PULSE CALLBACK
# =========================================================

def add_pulse():

    global pulse_count

    pulse_count += 1

wind_sensor.when_pressed = add_pulse

# =========================================================
# READ WIND FUNCTION
# =========================================================

def read_wind():

    global pulse_count
    global filtered_speed
    global last_read_time
    global last_data

    try:

        current_time = time.time()

        elapsed = (
            current_time
            -
            last_read_time
        )

        # =============================================
        # RETURN LAST DATA IF NOT READY
        # =============================================

        if elapsed < INTERVAL_SEC:

            return last_data

        # =============================================
        # CALCULATE FREQUENCY
        # =============================================

        freq = pulse_count / elapsed

        # =============================================
        # CALCULATE WIND SPEED
        # =============================================

        current_speed = (
            freq
            *
            SPEED_FACTOR
        )

        # =============================================
        # EMA FILTER
        # =============================================

        filtered_speed = (

            (0.7 * filtered_speed)

            +

            (0.3 * current_speed)
        )

        # =============================================
        # VERY LOW SPEED FIX
        # =============================================

        if filtered_speed < 0.05:

            filtered_speed = 0.0

        # =============================================
        # KM/H
        # =============================================

        speed_kmh = (
            filtered_speed
            *
            3.6
        )

        # =============================================
        # SAVE PULSE
        # =============================================

        total_pulse = pulse_count

        # =============================================
        # RESET
        # =============================================

        pulse_count = 0

        last_read_time = current_time

        # =============================================
        # WIND STATUS
        # =============================================

        if speed_kmh < 1:

            wind_status = "No Wind"

        elif speed_kmh < 5:

            wind_status = "Light Wind"

        elif speed_kmh < 15:

            wind_status = "Moderate Wind"

        else:

            wind_status = "Strong Wind"

        # =============================================
        # SAVE DATA
        # =============================================

        last_data = {

            "wind_pulses":
                total_pulse,

            "wind_frequency":
                round(freq, 2),

            "wind_speed_ms":
                round(filtered_speed, 2),

            "wind_speed_kmh":
                round(speed_kmh, 2),

            "wind_status":
                wind_status
        }

        return last_data

    except Exception as e:

        print("WIND ERROR:", e)

        return last_data