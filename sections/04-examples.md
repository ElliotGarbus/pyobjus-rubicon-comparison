# 4. Side-by-side examples

**Status: draft for factual review.** Neither project has reviewed this section. Versions are in [the baseline](../results/baseline/2026-11-04.md). Metric IDs refer to the [approved definitions](../metrics/04-examples.md), which also list every change made after approval.

## Summary of findings

The examples show the block gap in practice. Core Motion's altimeter delivers readings only to a handler, so reading the barometer takes 31 lines of compiled Objective-C with pyobjus, a helper that kivy-ios's project template provides, and none with Rubicon. Calling a Swift `async` method takes 15 lines of Swift for pyobjus, which keep the result for Python to poll, and 7 for Rubicon. Where both libraries can do the task directly, the clipboard and location updates, the code is similar in size.

Kivy's own clipboard code, run with pyobjus, returns `bytes` instead of `str` for short ASCII text, at both pyobjus versions. pyobjus 1.2.4 also crashed in the location example, which its default branch handles. Every other example worked in both libraries, at both versions, in all 5 runs.

Rubicon's location version declares the coordinate struct's field names, as Toga does, because the runtime describes the struct without them. pyobjus `master` reads the same struct through the field names it generates, `a` and `b`.

Results also arrive differently. Rubicon runs Python callbacks on whatever thread the API uses: the main thread for location, and background threads for the barometer and the Swift call, whose results a Kivy app would pass to its main thread, for example with `Clock.schedule_once`. The pyobjus barometer and Swift versions have no callbacks. They poll from the main thread, which avoids switching threads but checks repeatedly for a result.

All figures are **Measured** unless labeled otherwise, in a test app without Kivy. This section makes no recommendation. "`master`" and "`main`" mean the default branches. The clipboard ran on a Mac, and the other examples on an iPhone, each 5 times in each of pyobjus 1.2.4 and `master`, and Rubicon 0.5.7 and `main`.

| Example | pyobjus | Rubicon |
|---|---|---|
| E1. Copy text to the clipboard and read it back (Mac) | Short text came back as `b'Kivy'`. 16 lines of Python | Correct. 13 lines |
| E2. Location updates through a delegate (iPhone) | Correct at `master`, crash at 1.2.4. 16 lines | Correct. 25 lines, including a struct declaration |
| E3. Read the barometer, a block-only API (iPhone) | Correct. 9 lines of Python and 31 of Objective-C, from kivy-ios's template | Correct. 20 lines |
| E4. Call a Swift `async` method (iPhone) | Correct. 13 lines of Python and 15 of Swift | Correct. 10 lines of Python and 7 of Swift |

Line counts leave out blank lines, comments, docstrings and imports, after formatting with `ruff format`. They're shown per example and not added up.

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Relevant data |
|---|---|
| 9. pyobjus can't create blocks, so APIs with completion handlers need Objective-C helper code | Confirmed in practice. E3 uses kivy-ios's Objective-C bridge, 31 lines here and 173 in the template, to receive the altimeter's handler calls and store the readings for Python to poll. E4 needs 15 lines of Swift to keep a completion handler's result for Python to poll. Rubicon passes a Python function in both. |

## Supporting facts

Raw results, test fixes and rerun steps are in [`results/section-04/2026-11-07`](../results/section-04/2026-11-07/README.md). The code below is each example as it ran, without the test's entry point and the lines that record which thread a result arrived on. The full files are in [`examples/section-04`](../examples/section-04).

### E1. Clipboard

Kivy's [`clipboard_nspaste.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/clipboard/clipboard_nspaste.py) is Kivy's own use of pyobjus. It was trimmed to the task, and the Rubicon version was written from Rubicon's docs. Both use a private pasteboard so the test doesn't replace what the user has copied, where Kivy uses the general pasteboard.

**pyobjus:**

```python
from pyobjus import autoclass
from pyobjus.dylib_manager import INCLUDE, load_framework

load_framework(INCLUDE.AppKit)
NSPasteboard = autoclass("NSPasteboard")


class Clipboard:
    def __init__(self):
        # Kivy uses generalPasteboard(). A private pasteboard keeps the test
        # from replacing what the user has copied.
        self._clipboard = NSPasteboard.pasteboardWithUniqueName()

    def get(self):
        data = self._clipboard.stringForType_("public.utf8-plain-text")
        if not data:
            return ""
        return data.UTF8String()

    def put(self, data):
        self._clipboard.clearContents()
        self._clipboard.setString_forType_(data, "public.utf8-plain-text")

    def get_types(self):
        types = self._clipboard.types
        return [types.objectAtIndex_(i).UTF8String() for i in range(types.count())]
```

**Rubicon:**

```python
from rubicon.objc import ObjCClass
from rubicon.objc.runtime import load_library

load_library("AppKit")
NSPasteboard = ObjCClass("NSPasteboard")


class Clipboard:
    def __init__(self):
        # A private pasteboard keeps the test from replacing what the user has
        # copied. An app would use generalPasteboard().
        self._clipboard = NSPasteboard.pasteboardWithUniqueName()

    def get(self):
        data = self._clipboard.stringForType("public.utf8-plain-text")
        return str(data) if data else ""

    def put(self, data):
        self._clipboard.clearContents()
        self._clipboard.setString(data, forType="public.utf8-plain-text")

    def get_types(self):
        return [str(t) for t in self._clipboard.types]
```

- **X1:** Rubicon was correct in all runs. pyobjus returned `"héllo, Kivy"` correctly but `b'Kivy'`, a `bytes` value, for the short ASCII string, in all runs at both versions. `UTF8String()` returns `bytes` for Apple's short-string class (`NSTaggedPointerString`) and `str` for others, which pyobjus issue [#207](https://github.com/kivy/pyobjus/issues/207) reports. Kivy's `get()` returns that value as it is.
- **X4:** neither needs anything beyond its public API.
- **Changes from Kivy's code:** the platform check and import guard, the `ClipboardBase` parent class and the MIME type arguments were left out. The text is passed as a Python `str`, which pyobjus converts, instead of building an `NSString` first. `get_types` reads the pasteboard's types, where Kivy's returns a fixed value.

### E2. Location updates

plyer's [iOS GPS facade](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/platforms/ios/gps.py) uses pyobjus, and Toga's [iOS location backend](https://github.com/beeware/toga/blob/c7d1d4e75505d69554dd6f68da4fa12ed58eb80e/iOS/src/toga_iOS/hardware/location.py) uses Rubicon. Each was trimmed to receiving one location and reporting its latitude and longitude.

**pyobjus:**

```python
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
        coordinate = locations.lastObject().coordinate
        # pyobjus names an unknown struct's fields a, b, ..., as its docs describe.
        self.fix = (coordinate.a, coordinate.b)
```

**Rubicon:**

```python
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
```

- **X1:** both were correct in all runs at their default branches, and Rubicon 0.5.7 was too. Results record only that the coordinates were valid. pyobjus 1.2.4 crashed in all runs: the app ended with `unrecognized selector` for `locationManager:didUpdateLocations:`, which is how 1.2.4 responds to a second delegate call after an exception it didn't clear. Section 3 found that 1.2.4 raises when building a struct type it doesn't know, so the coordinate is the likely cause (**Inferred**).
- **X4:** pyobjus `master` reads the coordinate through the field names it generates for an unknown struct, `a` and `b`, as its [docs](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L506) describe. The Rubicon version declares the `CLLocationCoordinate2D` struct, as Toga does, with `with_preferred_encoding`, which Rubicon's [types reference](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-types.md#L93) describes. Field names aren't in the runtime's type information, so either library needs them declared to use the real names.
- **X5:** both delegates ran on the main thread.
- **Changes from plyer:** the authorization status callback, speed, course, altitude and accuracy were left out. The coordinate is read from the last location passed to the delegate, where plyer parses the text of `manager.location`'s description, a format Apple doesn't document. **From Toga:** permission requests, the failure callback, background updates and altitude were left out, and Toga's `libs` declaration of the struct was moved into the file.

### E3. Barometer

Core Motion's altimeter delivers readings only to a handler block. plyer's [barometer facade](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/platforms/ios/barometer.py) reads an Objective-C class named `bridge`, which kivy-ios's [project template](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/tools/templates/%7B%7B%20cookiecutter.project_name%20%7D%7D-ios/bridge.m) adds to every app it generates. pyobjus's [docs](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/pyobjus_ios.rst#L168) describe the same approach. The bridge was trimmed to the altimeter. The Rubicon version was written from Rubicon's docs.

**pyobjus:**

```python
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
```

```objc
// E3's helper for pyobjus: kivy-ios's project template bridge.h, trimmed to
// the altimeter.
#import <Foundation/Foundation.h>
#import <CoreMotion/CoreMotion.h>

@interface bridge : NSObject {
    NSOperationQueue *queue;
}

@property (nonatomic) double relative_altitude;
@property (nonatomic) double pressure;

@end
```

```objc
// E3's helper for pyobjus: kivy-ios's project template bridge.m, trimmed to
// the altimeter. Compiled with manual reference counting, as the template is.
#import "e3_bridge.h"

@implementation bridge

CMAltimeter *altimeterManager;

- (id) init {
    if(self = [super init]) {
        queue = [[NSOperationQueue alloc] init];
    }
    return self;
}

- (void)startRelativeAltitude {

    if ([CMAltimeter isRelativeAltitudeAvailable]) {
        altimeterManager = [[CMAltimeter alloc] init];
        [altimeterManager startRelativeAltitudeUpdatesToQueue:queue withHandler:^(CMAltitudeData *altitudeData, NSError *error) {
            self.relative_altitude = altitudeData.relativeAltitude.floatValue;
            self.pressure = altitudeData.pressure.floatValue;
        }];
    }
}

- (void) stopRelativeAltitude {
    [altimeterManager stopRelativeAltitudeUpdates];
}

- (void) dealloc {
    [queue release];
    [super dealloc];
}

@end
```

**Rubicon:**

```python
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
            if data:
                # 1 kPa = 10 hPa
                self.pressure = ObjCInstance(data).pressure.doubleValue * 10

        if CMAltimeter.isRelativeAltitudeAvailable():
            self.altimeter.startRelativeAltitudeUpdatesToQueue(self.queue, withHandler=handler)

    def disable(self):
        self.altimeter.stopRelativeAltitudeUpdates()
```

- **X1:** both were correct in all runs. Results record only that the pressure was plausible.
- **X3:** the pyobjus version needs 31 lines of Objective-C, compiled into the app. A kivy-ios app already has it, in a 173-line version that serves plyer's six motion facades. An app built another way has to add it.
- **X4:** the Rubicon version needs nothing beyond its public API.
- **X5:** the Rubicon handler ran on the operation queue it created, off the main thread. The bridge's handler runs on its own queue, and Python polls the stored value from the main thread.
- **Changes from plyer:** the facade's base class was left out and its `_enable`, `_disable` and `_get_pressure` methods were renamed without the underscore.

### E4. A Swift `async` method

The task calls a Swift method that awaits `UNUserNotificationCenter`'s settings and returns the authorization status. Both versions start from the [KivyForge guide](https://github.com/ElliotGarbus/kivyforge/blob/edaa3aa8c4eb2f1a4f9f1b42a7c7b7350ae55012/docs/guides/guides/ios/swift.md), which this comparison's author wrote. pyobjus can't pass a completion handler, so its Swift keeps the result for Python to poll.

**pyobjus:**

```python
from pyobjus import autoclass

PolledWork = autoclass("S4PolledWork")


class NotificationStatus:
    def __init__(self):
        self.value = None
        self.job = None

    def start(self):
        self.job = PolledWork.notificationStatus()

    def poll(self):
        result = self.job.result
        if result is None:
            return False
        self.value = result.integerValue()
        return True
```

```swift
// E4's Swift for pyobjus, which can't pass a completion handler: the same work,
// started on the main actor, with its one result for Python to poll.
import Foundation
import UserNotifications

@objc(S4PolledWork)
public final class PolledWork: NSObject {
    @objc public private(set) var result: NSNumber?

    @objc public static func notificationStatus() -> PolledWork {
        let work = PolledWork()
        Task { @MainActor in
            let settings =
                await UNUserNotificationCenter.current().notificationSettings()
            work.result = NSNumber(
                value: settings.authorizationStatus.rawValue
            )
        }
        return work
    }
}
```

**Rubicon:**

```python
from rubicon.objc import NSInteger, ObjCClass

Work = ObjCClass("S4Work")


class NotificationStatus:
    def __init__(self):
        self.value = None

    def start(self):
        def done(status: NSInteger) -> None:
            self.value = status

        Work.notificationStatusWithCompletionHandler(done)
```

```swift
// E4's Swift for Rubicon: an async method, which Objective-C sees as
// notificationStatusWithCompletionHandler:. From the KivyForge swift-bridge
// example's notificationSettings, trimmed to the authorization status.
import Foundation
import UserNotifications

@objc(S4Work)
public final class Work: NSObject {
    @objc public static func notificationStatus() async -> Int {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        return settings.authorizationStatus.rawValue
    }
}
```

- **X1:** both were correct in all runs.
- **X3:** 15 lines of Swift for pyobjus and 7 for Rubicon.
- **X5:** Rubicon's handler ran on a thread Swift created, so a Kivy app would schedule its work on the main thread. pyobjus polls from the main thread, and the Swift sets the result on the main thread.
- **Changes from the guide:** the pyobjus Swift keeps one result instead of the guide's job with progress, cancellation and errors, and both are trimmed to the authorization status.

## Limits of this section

- **Four examples don't make a usage profile.** They were chosen to show key differences, not to represent all of Apple's API.
- **The code starts from real projects but is trimmed.** Trimming changes length, and the original projects handle more than the task.
- **Line counts depend on style.** Both versions are formatted the same way, but plyer and Toga write differently. The code is shown so readers can judge.
- **The examples ran without Kivy.** X5 notes what a Kivy app would add.
- **One author wrote the comparison and the KivyForge guide E4 starts from.** Shorter or more idiomatic versions for either library are welcome, and a working one replaces the current version.
