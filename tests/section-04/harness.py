"""What the Mac and iPhone runners share: running one example and checking it.

`wait` spins the Core Foundation run loop through ctypes, the same way for
both libraries, so delegate and block callbacks on the main thread can arrive.

E2 reads the phone's real location, and E3 its air pressure, which hints at
altitude. Their checks run here, and only whether each value is valid is
reported, never the value itself.
"""
import ctypes
import importlib
import time
import traceback

EXAMPLES = {"e1": "Mac", "e2": "iPhone", "e3": "iPhone", "e4": "iPhone"}
TIMEOUT = 15.0

_cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
_cf.CFRunLoopRunInMode.restype = ctypes.c_int32
_cf.CFRunLoopRunInMode.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_bool]
_default_mode = ctypes.c_void_p.in_dll(_cf, "kCFRunLoopDefaultMode")


def wait(done, timeout=TIMEOUT):
    """Run the current run loop until done() is true or the timeout passes."""
    end = time.monotonic() + timeout
    while not done() and time.monotonic() < end:
        _cf.CFRunLoopRunInMode(_default_mode, 0.05, False)
    return done()


def check(example, result):
    """Returns (outcome, detail). The detail never includes a location."""
    if example == "e1":
        text, short, types = result["text"], result["short_text"], result["types"]
        ok = text == "héllo, Kivy" and short == "Kivy" and "public.utf8-plain-text" in types
        return ("correct" if ok else "wrong value"), repr(result)[:300]
    if example == "e2":
        fix = result["fix"]
        valid = (isinstance(fix, tuple) and len(fix) == 2 and all(isinstance(v, float) for v in fix)
                 and -90 <= fix[0] <= 90 and -180 <= fix[1] <= 180 and fix != (0.0, 0.0))
        detail = "valid latitude and longitude" if valid else f"not a valid fix ({type(fix).__name__})"
        return ("correct" if valid else "wrong value"), detail
    if example == "e3":
        # Pressure hints at altitude, so only whether it's plausible is reported.
        pressure = result["pressure"]
        ok = isinstance(pressure, float) and 300 < pressure < 1100
        return ("correct" if ok else "wrong value"), ("plausible pressure in hPa" if ok
                                                       else f"not a plausible pressure ({type(pressure).__name__})")
    if example == "e4":
        status = result["status"]
        ok = isinstance(status, int) and not isinstance(status, bool) and 0 <= status <= 4
        return ("correct" if ok else "wrong value"), repr(status)
    raise KeyError(example)


def run(example, lib):
    """Run one example in this process. Returns the result to report."""
    try:
        module = importlib.import_module(f"{example}_{lib}")
        result = module.run(wait)
        outcome, detail = check(example, result)
        return {"outcome": outcome, "detail": detail, "on_main": result.get("on_main")}
    except BaseException as e:
        traceback.print_exc()
        detail = f"{type(e).__name__}: {e}"[:300]
        if example in ("e2", "e3"):
            detail = type(e).__name__  # an exception message could include a location
        return {"outcome": "python exception", "detail": detail}
