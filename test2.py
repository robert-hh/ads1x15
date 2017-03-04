from machine import I2C, Pin, Timer
import ads1x15
from time import sleep_ms, ticks_ms, ticks_us
from array import array

addr = 72
gain = 1

_BUFFERSIZE = const(512)
#
# Interrupt service routine zum messen
# diese wird vom Timer-interrupt aktiviert
#
def sample(x):
    global index_put, ads, irq_busy, data, timestamp
    if irq_busy:
        return
    irq_busy = True
    if index_put < _BUFFERSIZE:
        timestamp[index_put] = ticks_us()
        data[index_put] = ads.alert_read()
        index_put += 1
    irq_busy = False

data = array("h", [0] * _BUFFERSIZE)
timestamp = array("L", [0] * _BUFFERSIZE)
irq_busy = False

index_put = 0
ADC_RATE = 5

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
ads = ads1x15.ADS1115(i2c, addr, gain)
# set the conversion rate tp 860 SPS = 1.16 ms; that leaves about
# 3 ms time for processing the data with a 5 ms timer
ads.set_conv(0, 7) # start the first conversion
ads.read_rev()
sleep_ms(ADC_RATE)
tim = Timer(-1)
tim.init(period=ADC_RATE, mode=Timer.PERIODIC, callback=sample)

while index_put < _BUFFERSIZE:
    pass

tim.deinit()

for _ in range(1, _BUFFERSIZE):
    print(timestamp[_], timestamp[_] - timestamp[_-1], data[_], data[_] - data[_ - 1] )

# at that point data contains the sampled values, and
# timestamp the timer ticks which correlate to the conversion time
#

