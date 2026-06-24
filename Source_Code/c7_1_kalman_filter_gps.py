# =====================================================
# STATIC GPS KALMAN FILTER
# AGROBEACON VERSION
# =====================================================

class KalmanFilterGPS:

    def __init__(self):

        # =============================================
        # INITIAL
        # =============================================

        self.estimate = 0.0

        self.error_estimate = 1.0

        self.initialized = False

        # =============================================
        # ULTRA STATIC FILTER
        # =============================================

        self.process_noise = 0.000000000005

        self.measurement_noise = 0.0000025

    # =================================================
    # UPDATE
    # =================================================

    def update(self, measurement):

        # =============================================
        # FIRST VALUE
        # =============================================

        if not self.initialized:

            self.estimate = measurement

            self.initialized = True

            return measurement

        # =============================================
        # PREDICTION
        # =============================================

        self.error_estimate += self.process_noise

        # =============================================
        # KALMAN GAIN
        # =============================================

        kalman_gain = (

            self.error_estimate

            /

            (
                self.error_estimate
                +
                self.measurement_noise
            )
        )

        # =============================================
        # UPDATE ESTIMATE
        # =============================================

        self.estimate = (

            self.estimate

            +

            kalman_gain
            *
            (
                measurement
                -
                self.estimate
            )
        )

        # =============================================
        # UPDATE ERROR
        # =============================================

        self.error_estimate = (

            (1 - kalman_gain)

            *

            self.error_estimate
        )

        return self.estimate