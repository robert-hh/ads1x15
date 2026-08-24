from ads1x15 import ADS1115


class ADS1114(ADS1115):
    def __init__(self, i2c, address=0x48, gain=1):
        super().__init__(i2c, address, gain)

    def raw_to_v(self, raw):
        return super().raw_to_v(raw)

    def read(self, rate=4):
        return super().read(rate, 0, 1)

    def alert_start(self, rate=4, threshold_high=0x4000, threshold_low=0, latched=False):
        return super().alert_start(rate, 0, 1, threshold_high,
                                   threshold_low, latched)

    def alert_read(self):
        return super().alert_read()
