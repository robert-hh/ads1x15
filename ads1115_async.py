import asyncio
import machine
from ads1x15 import (
    ADS1115,
    _GAINS,
    _CHANNELS,
    _RATES,
)

_REGISTER_CONVERT = const(0x00)
_REGISTER_CONFIG = const(0x01)
_REGISTER_LOWTHRESH = const(0x02)
_REGISTER_HITHRESH = const(0x03)

_OS_SINGLE = const(0x8000)
_MODE_SINGLE = const(0x0100)
_CMODE_TRAD = const(0x0000)
_CPOL_ACTVLOW = const(0x0000)
_CLAT_NONLAT = const(0x0000)
_CQUE_1CONV = const(0x0000)


class ADS1115Async(ADS1115):
    """ADS1115 driver with interrupt-driven async read.

    The ALERT/RDY pin must be connected and passed as ready_pin.
    """

    def __init__(self, i2c, address=0x48, gain=1, ready_pin=None):
        super().__init__(i2c, address, gain)
        if ready_pin is None:
            raise ValueError("ready_pin is required for ADS1115Async")
        self._ready_pin = ready_pin
        # ALERT/RDY is active-low; pull-up keeps the line stable between reads
        self._ready_pin.init(mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)
        # Thread-safe flag is the correct bridge between an IRQ and asyncio
        self._ready_flag = asyncio.ThreadSafeFlag()
        # Attach falling-edge IRQ (pin goes low when conversion is ready)
        self._ready_irq = self._ready_pin.irq(
            trigger=machine.Pin.IRQ_FALLING,
            handler=self._ready_callback,
        )
        # Enable conversion-ready mode on ALERT/RDY (datasheet §7.3.8).
        # Lo_thresh MSB = 0 and Hi_thresh MSB = 1 are the sentinel values.
        self._write_register(_REGISTER_LOWTHRESH, 0x0000)
        self._write_register(_REGISTER_HITHRESH, 0x8000)
        self._lock = asyncio.Lock()

    def _ready_callback(self, pin):
        """IRQ handler – must be minimal; only sets the flag."""
        self._ready_flag.set()

    def deinit(self):
        """Disable the IRQ and break the reference cycle."""
        if hasattr(self, "_ready_irq") and self._ready_irq is not None:
            try:
                self._ready_irq.disable()
            except Exception:
                pass
            try:
                self._ready_pin.irq(handler=None)
            except Exception:
                pass
            self._ready_irq = None

    def __del__(self):
        """Clean up resources when the object is reclaimed."""
        self.deinit()

    async def aioread(self, rate=4, channel1=0, channel2=None):
        """Start a single-shot conversion and wait for the ALERT/RDY interrupt."""
        async with self._lock:
            # Clear any previously set flag (e.g. from noise or previous reads)
            # before starting the conversion.
            self._ready_flag.clear()
            # Start single-shot conversion; CQUE_1CONV keeps ALERT/RDY enabled
            self._write_register(_REGISTER_CONFIG, (
                _CQUE_1CONV | _CLAT_NONLAT |
                _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                _MODE_SINGLE | _OS_SINGLE | _GAINS[self.gain] |
                _CHANNELS[(channel1, channel2)]
            ))
            # Block this coroutine until the IRQ fires; other coroutines run freely
            await self._ready_flag.wait()
            res = self._read_register(_REGISTER_CONVERT)

        return res if res < 32768 else res - 65536
