"""E3, barometer, with Rubicon. Written from Rubicon's docs."""
import threading

from rubicon.objc import ObjCClass, ObjCInstance, objc_id
from rubicon.objc.runtime import load_library

load_library("CoreMotion")
CMAltimeter = ObjCClass("CMAltimeter")
NSOperationQueue = ObjCClass("NSOperationQueue")


class Barometer:
    def __init__(self):
        self.pressure = None
        self.altimeter = CMAltimeter.alloc().init()
        self.queue = NSOperationQueue.alloc().init()

    def enable(self):
        def handler(data: objc_id, error: objc_id) -> None:
            self.on_main = threading.current_thread() is threading.main_thread()  # measure
            if data:
                # 1 kPa = 10 hPa
                self.pressure = ObjCInstance(data).pressure.doubleValue * 10

        if CMAltimeter.isRelativeAltitudeAvailable():
            self.altimeter.startRelativeAltitudeUpdatesToQueue(self.queue, withHandler=handler)

    def disable(self):
        self.altimeter.stopRelativeAltitudeUpdates()


def run(wait):
    barometer = Barometer()
    barometer.enable()
    wait(lambda: barometer.pressure)
    pressure = barometer.pressure
    barometer.disable()
    return {"pressure": pressure, "on_main": getattr(barometer, "on_main", None)}  # measure
