import ustruct
import time


_REGISTER_MASK = const(0x03)
_REGISTER_CONVERT = const(0x00)
_REGISTER_CONFIG = const(0x01)
_REGISTER_LOWTHRESH = const(0x02)
_REGISTER_HITHRESH = const(0x03)

_OS_MASK = const(0x8000)
_OS_SINGLE = const(0x8000)  # Write: Set to start a single-conversion
_OS_BUSY = const(0x0000)  # Read: Bit=0 when conversion is in progress
_OS_NOTBUSY = const(0x8000)  # Read: Bit=1 when device is not performing a conversion

_MUX_MASK = const(0x7000)
_MUX_DIFF_0_1 = const(0x0000)  # Differential P  =  AIN0, N  =  AIN1 (default)
_MUX_DIFF_0_3 = const(0x1000)  # Differential P  =  AIN0, N  =  AIN3
_MUX_DIFF_1_3 = const(0x2000)  # Differential P  =  AIN1, N  =  AIN3
_MUX_DIFF_2_3 = const(0x3000)  # Differential P  =  AIN2, N  =  AIN3
_MUX_SINGLE_0 = const(0x4000)  # Single-ended AIN0
_MUX_SINGLE_1 = const(0x5000)  # Single-ended AIN1
_MUX_SINGLE_2 = const(0x6000)  # Single-ended AIN2
_MUX_SINGLE_3 = const(0x7000)  # Single-ended AIN3

_PGA_MASK = const(0x0E00)
_PGA_6_144V = const(0x0000)  # +/-6.144V range  =  Gain 2/3
_PGA_4_096V = const(0x0200)  # +/-4.096V range  =  Gain 1
_PGA_2_048V = const(0x0400)  # +/-2.048V range  =  Gain 2 (default)
_PGA_1_024V = const(0x0600)  # +/-1.024V range  =  Gain 4
_PGA_0_512V = const(0x0800)  # +/-0.512V range  =  Gain 8
_PGA_0_256V = const(0x0A00)  # +/-0.256V range  =  Gain 16

_MODE_MASK = const(0x0100)
_MODE_CONTIN = const(0x0000)  # Continuous conversion mode
_MODE_SINGLE = const(0x0100)  # Power-down single-shot mode (default)

_DR_MASK = const(0x00E0)    # Values ADS1015/ADS1115
_DR_128SPS = const(0x0000)  # 128/8 samples per second
_DR_250SPS = const(0x0020)  # 250/16 samples per second
_DR_490SPS = const(0x0040)  # 490/32 samples per second
_DR_920SPS = const(0x0060)  # 920/64 samples per second
_DR_1600SPS = const(0x0080)  # 1600/128 samples per second (default)
_DR_2400SPS = const(0x00A0)  # 2400/250 samples per second
_DR_3300SPS = const(0x00C0)  # 3300/475 samples per second
_DR_860SPS  = const(0x00E0)  # - /860 samples per Second

_CMODE_MASK = const(0x0010)
_CMODE_TRAD = const(0x0000)  # Traditional comparator with hysteresis (default)
_CMODE_WINDOW = const(0x0010)  # Window comparator

_CPOL_MASK = const(0x0008)
_CPOL_ACTVLOW = const(0x0000)  # ALERT/RDY pin is low when active (default)
_CPOL_ACTVHI = const(0x0008)  # ALERT/RDY pin is high when active

_CLAT_MASK = const(0x0004)  # Determines if ALERT/RDY pin latches once asserted
_CLAT_NONLAT = const(0x0000)  # Non-latching comparator (default)
_CLAT_LATCH = const(0x0004)  # Latching comparator

_CQUE_MASK = const(0x0003)
_CQUE_1CONV = const(0x0000)  # Assert ALERT/RDY after one conversions
_CQUE_2CONV = const(0x0001)  # Assert ALERT/RDY after two conversions
_CQUE_4CONV = const(0x0002)  # Assert ALERT/RDY after four conversions
_CQUE_NONE = const(0x0003)  # Disable the comparator and put ALERT/RDY in high state (default)

_GAINS = (
    _PGA_6_144V, # 2/3x
    _PGA_4_096V, # 1x
    _PGA_2_048V, # 2x
    _PGA_1_024V, # 4x
    _PGA_0_512V, # 8x
    _PGA_0_256V  # 16x
)
_CHANNELS = (_MUX_SINGLE_0, _MUX_SINGLE_1, _MUX_SINGLE_2, _MUX_SINGLE_3)
_DIFFS = {
    (0, 1): _MUX_DIFF_0_1,
    (0, 3): _MUX_DIFF_0_3,
    (1, 3): _MUX_DIFF_1_3,
    (2, 3): _MUX_DIFF_2_3,
}


class ADS1115:
    def __init__(self, i2c, address=0x49, gain=0):
        self.i2c = i2c
        self.address = address
        self.gain = gain # 2/3 6.144V
        self.temp = bytearray(2)

    def _write_register(self, register, value):
        data = ustruct.pack('>BH', register, value)
        self.i2c.writeto(self.address, data)

    def _read_register(self, register):
        self.temp[0] = self.address << 1
        self.temp[1] = register
        self.i2c.start()
        self.i2c.write(self.temp)
        self.i2c.readfrom_into(self.address, self.temp)
        return (self.temp[0] << 8) | self.temp[1]

    def set_conv(self, channel, rate):
        """Read voltage between a channel and GND. Takes 1ms/10ms."""
        self.mode = (_CQUE_NONE | _CLAT_NONLAT |
            _CPOL_ACTVLOW | _CMODE_TRAD | rate | _MODE_SINGLE |
            _OS_SINGLE | _GAINS[self.gain] | _CHANNELS[channel])

    def read(self, channel):
        """Read voltage between a channel and GND. Takes 1ms/10ms."""
        self._write_register(_REGISTER_CONFIG, self.mode)
        while not self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
            time.sleep_ms(1)
        return self._read_register(_REGISTER_CONVERT)

    @micropython.native
    def read_inv(self):
        """Read voltage between a channel and GND. and then start the next conversion."""
        res = self._read_register(_REGISTER_CONVERT)
        self._write_register(_REGISTER_CONFIG, self.mode)
        return res

    def diff(self, channel1, channel2):
        """Read voltage between two channels. Takes 1ms/10ms."""
        self._write_register(_REGISTER_CONFIG, _CQUE_NONE | _CLAT_NONLAT |
            _CPOL_ACTVLOW | _CMODE_TRAD | _DR_2400SPS | _MODE_SINGLE |
            _OS_SINGLE | _GAINS[self.gain] | _DIFFS[(channel1, channel2)])
        while not self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
            time.sleep_ms(1)
        return self._read_register(_REGISTER_CONVERT)

    def alert_start(self, channel, rate, threshold = 0x8000):
        """Start continuous measurement, set ALERT pin on threshold."""
        self._write_register(_REGISTER_LOWTHRESH, 0)
        self._write_register(_REGISTER_HITHRESH, threshold)
        self._write_register(_REGISTER_CONFIG, _CQUE_1CONV | _CLAT_NONLAT |
            _CPOL_ACTVLOW | _CMODE_TRAD | rate |
            _MODE_CONTIN | _GAINS[self.gain] | _CHANNELS[channel])

    def alert_read(self):
        """Get the last reading from the continuous measurement."""
        return self._read_register(_REGISTER_CONVERT)


class ADS1015(ADS1115):
    def __init__(self, i2c, address=0x48):
        return super().__init__(i2c, address)

    def read(self, channel):
        return super().read(channel) >> 4

    def diff(self, channel1, channel2):
        return super().diff(channel1, channel2) >> 4

    def alert_start(self, channel, threshold):
        return super().alert_start(channel, threshold << 4)

    def alert_read(self):
        return super().alert_read() >> 4

