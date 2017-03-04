from machine import I2C, Pin, Timer
import ads1x15
from array import array

addr = 72
gain = 1

_BUFFERSIZE = const(512)
#
# Interrupt service routine zum messen
# diese wird vom Timer-interrupt aktiviert
#
def sample_auto(x):
    global index_put, ads, data
    if index_put < _BUFFERSIZE:
        data[index_put] = ads.alert_read()
        index_put += 1

data = array("h", [0] * _BUFFERSIZE)
index_put = 0

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
irq_pin = Pin(13, Pin.IN, Pin.PULL_UP)
ads = ads1x15.ADS1115(i2c, addr, gain)
ads.conversion_start(0, 5)

irq_pin.irq(trigger=Pin.IRQ_FALLING, handler=sample_auto)

while index_put < _BUFFERSIZE:
    pass

irq_pin.irq(handler=None)
#
# at that point data contains 512 samples acquired at the given rate
#

for _ in range(1, _BUFFERSIZE):
    print(data[_], data[_] - data[_ - 1] )
