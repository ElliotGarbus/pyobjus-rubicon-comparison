"""E2, location updates, with Rubicon. From Toga's iOS location backend."""
import threading
from ctypes import Structure, c_double

from rubicon.objc import NSObject, ObjCClass, objc_method, objc_property
from rubicon.objc.runtime import load_library
from rubicon.objc.types import with_preferred_encoding

load_library("CoreLocation")
CLLocationManager = ObjCClass("CLLocationManager")


@with_preferred_encoding(b"{CLLocationCoordinate2D=dd}")
class CLLocationCoordinate2D(Structure):
    _fields_ = [("latitude", c_double), ("longitude", c_double)]


class LocationDelegate(NSObject):
    impl = objc_property(object, weak=True)

    @objc_method
    def locationManager_didUpdateLocations_(self, manager, locations) -> None:
        self.impl.on_main = threading.current_thread() is threading.main_thread()  # measure
        coordinate = locations[-1].coordinate
        self.impl.fix = (coordinate.latitude, coordinate.longitude)


class Location:
    def __init__(self):
        self.fix = None
        self.native = CLLocationManager.alloc().init()
        self.delegate = LocationDelegate.alloc().init()
        self.native.delegate = self.delegate
        self.delegate.impl = self

    def start(self):
        self.native.requestWhenInUseAuthorization()
        self.native.startUpdatingLocation()

    def stop(self):
        self.native.stopUpdatingLocation()


def run(wait):
    location = Location()
    location.start()
    wait(lambda: location.fix)
    location.stop()
    return {"fix": location.fix, "on_main": getattr(location, "on_main", None)}  # measure
