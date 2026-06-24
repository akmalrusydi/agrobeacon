class KalmanFilterGPS:

    def __init__(self):

        # =====================
        # FILTER STATE
        # =====================
        self.estimate = 0.0

        self.error_estimate = 1.0

        # =====================
        # CALIBRATED FOR LC76G
        # =====================

        # super stable stationary
        self.process_noise_static = 0.00000003

        # responsive when moving
        self.process_noise_moving = 0.00001

        # trust previous estimate more
        self.measurement_noise = 0.00015

        # =====================
        # INITIALIZATION
        # =====================
        self.initialized = False

    # =====================
    # UPDATE FILTER
    # =====================
    def update(
        self,
        measurement,
        is_moving=False
    ):

        # =====================
        # FIRST INIT
        # =====================
        if not self.initialized:

            self.estimate = measurement

            self.initialized = True

        # =====================
        # PROCESS NOISE
        # =====================
        if is_moving:

            process_noise = \
                self.process_noise_moving

        else:

            process_noise = \
                self.process_noise_static

        # =====================
        # PREDICTION UPDATE
        # =====================
        self.error_estimate += process_noise

        # =====================
        # KALMAN GAIN
        # =====================
        kalman_gain = (
            self.error_estimate
            /
            (
                self.error_estimate
                +
                self.measurement_noise
            )
        )

        # =====================
        # CORRECTION UPDATE
        # =====================
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

        # =====================
        # ERROR UPDATE
        # =====================
        self.error_estimate = (
            (1 - kalman_gain)
            *
            self.error_estimate
        )

        return self.estimate

    # =====================
    # RESET FILTER
    # =====================
    def reset(self):

        self.initialized = False

        self.error_estimate = 1.0