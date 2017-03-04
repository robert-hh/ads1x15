from machine import I2C, Pin, Timer
import ads1x15
from time import sleep_ms, ticks_ms, ticks_us
from array import array

addr = 72
gain = 1

_DR_MASK = const(0x00E0)    # Values ADS1115
_DR_8SPS = const(0x0000)    # 8 samples per second
_DR_16SPS = const(0x0020)   # 16 samples per second
_DR_32SPS = const(0x0040)   # 32 samples per second
_DR_64SPS = const(0x0060)   # 64 samples per second
_DR_128SPS = const(0x0080)  # 128 samples per second (default)
_DR_250SPS = const(0x00A0)  # 250 samples per second
_DR_475SPS = const(0x00C0)  # 475 samples per second
_DR_860SPS  = const(0x00E0) # 860 samples per Second

_BUFFERSIZE = const(512)
#
# Interrupt service routine zum messen
# diese wird vom Timer-interrupt aktiviert
#
#@micropython.native
def sample_auto(x):
    global index_put, ads, data, timestamp
    if index_put < _BUFFERSIZE:
        timestamp[index_put] = ticks_us()
        data[index_put] = ads.alert_read()
        index_put += 1

data = array("h", [0] * _BUFFERSIZE)
timestamp = array("L", [0] * _BUFFERSIZE)
irq_busy = False

index_put = 0

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
irq_pin = Pin(13, Pin.IN, Pin.PULL_UP)

ads = ads1x15.ADS1115(i2c, addr, gain)

ads.conversion_start(0, 5)

irq_pin.irq(trigger=Pin.IRQ_FALLING, handler=sample_auto)

while index_put < _BUFFERSIZE:
    pass

irq_pin.irq(handler=None)

for _ in range(1, _BUFFERSIZE):
    print(timestamp[_], timestamp[_] - timestamp[_-1], data[_], data[_] - data[_ - 1] )


def run(ADC_RATE):
    global index_put

    index_put = 0
    ads.set_conv(0, 7)
    ads.read_inv()
    sleep_ms(ADC_RATE)
    tim = Timer(-1)
    tim.init(period=ADC_RATE, mode=Timer.PERIODIC, callback=sample)

    while index_put < _BUFFERSIZE:
        pass

    tim.deinit()

    for _ in range(1, _BUFFERSIZE):
        print(timestamp[_], timestamp[_] - timestamp[_-1], data[_], data[_] - data[_ - 1] )


