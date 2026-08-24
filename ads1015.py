from ads1x15 import ADS1115


class ADS1015(ADS1115):
    def __init__(self, i2c, address=0x48, gain=1):
        super().__init__(i2c, address, gain)

    def raw_to_v(self, raw):
        return super().raw_to_v(raw << 4)

    def read(self, rate=4, channel1=0, channel2=None):
        return super().read(rate, channel1, channel2) >> 4

    def alert_start(self, rate=4, channel1=0, channel2=None, threshold_high=0x400,
                    threshold_low=0, latched=False):
        return super().alert_start(rate, channel1, channel2, threshold_high << 4,
                                   threshold_low << 4, latched)

    def alert_read(self):
        return super().alert_read() >> 4
