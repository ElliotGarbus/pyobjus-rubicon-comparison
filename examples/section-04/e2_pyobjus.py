"""E2, location updates, with pyobjus. From plyer's iOS GPS facade."""
import threading

from pyobjus import autoclass, protocol
from pyobjus.dylib_manager import load_framework

load_framework("/System/Library/Frameworks/CoreLocation.framework")
CLLocationManager = autoclass("CLLocationManager")


class Location:
    def __init__(self):
        self.fix = None
        self._location_manager = CLLocationManager.alloc().init()

    def start(self):
        self._location_manager.delegate = self
        self._location_manager.requestWhenInUseAuthorization()
        self._location_manager.startUpdatingLocation()

    def stop(self):
        self._location_manager.stopUpdatingLocation()

    @protocol("CLLocationManagerDelegate")
    def locationManager_didUpdateLocations_(self, manager, locations):
        self.on_main = threading.current_thread() is threading.main_thread()  # measure
        coordinate = locations.lastObject().coordinate
        # pyobjus names an unknown struct's fields a, b, ..., as its docs describe.
        self.fix = (coordinate.a, coordinate.b)


def run(wait):
    location = Location()
    location.start()
    wait(lambda: location.fix)
    location.stop()
    return {"fix": location.fix, "on_main": getattr(location, "on_main", None)}  # measure
