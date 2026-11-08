"""E3, barometer, with pyobjus. From plyer's iOS barometer facade, which reads
kivy-ios's Objective-C bridge class."""
from pyobjus import autoclass


class Barometer:
    def __init__(self):
        self.bridge = autoclass("bridge").alloc().init()

    def enable(self):
        self.bridge.startRelativeAltitude()

    def disable(self):
        self.bridge.stopRelativeAltitude()

    def get_pressure(self):
        # 1 kPa = 10 hPa
        return self.bridge.pressure * 10


def run(wait):
    barometer = Barometer()
    barometer.enable()
    wait(lambda: barometer.get_pressure())
    pressure = barometer.get_pressure()
    barometer.disable()
    # The handler runs in Objective-C on the bridge's queue, and Python polls.
    return {"pressure": pressure, "on_main": None}  # measure
