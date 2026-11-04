"""TH5: report whether the GIL is enabled before and after importing a library."""
import ctypes
import json
import sys

fixture, name = sys.argv[1:3]
before = sys._is_gil_enabled()
ctypes.CDLL(fixture)
if name == "pyobjus":
    from pyobjus import autoclass
    autoclass("S2Types").alloc().init().echoInt_(1)
elif name == "rubicon":
    from rubicon.objc import ObjCClass
    ObjCClass("S2Types").alloc().init().echoInt_(1)
else:
    import objc
    objc.lookUpClass("S2Types").alloc().init().echoInt_(1)
print(json.dumps({"library": name, "python": sys.version.split()[0], "gil_before": before,
                  "gil_after": sys._is_gil_enabled()}))
