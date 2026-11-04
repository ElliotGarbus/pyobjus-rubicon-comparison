"""Check one T5 entry: does the library find the method, and what signature does
it report? Nothing is called here, because most of these APIs need real
arguments or state. Prints one JSON line."""
import ctypes
import json
import os
import sys

lib, fw, cls, sel, is_class, want = sys.argv[1:7]
is_class = is_class == "1"
ctypes.CDLL(f"/System/Library/Frameworks/{fw}.framework/{fw}")
py = sel.replace(":", "_")


def result(outcome, detail=""):
    print("S2RESULT " + json.dumps({"outcome": outcome, "detail": detail}), flush=True)
    os._exit(0)


def judge(encoding):
    if encoding is None:
        result("found, signature not readable")
    enc = encoding.decode() if isinstance(encoding, bytes) else str(encoding)
    # The runtime reports many structs as anonymous ({?=...}), so compare the
    # layout after the name rather than the name itself.
    layout = want.split("=", 1)[-1] if want.startswith("{") else want
    if layout and layout not in enc:
        result("found, signature differs", enc[:160])
    result("found, signature matches", enc[:160])


try:
    if lib == "pyobjus":
        from pyobjus import autoclass
        c = autoclass(cls, new_instance=not is_class)
        if not hasattr(c, py):
            result("not found")
        judge(None)
    elif lib == "rubicon":
        from rubicon.objc import ObjCClass
        from rubicon.objc.runtime import SEL, libobjc
        c = ObjCClass(cls)
        lookup = libobjc.class_getClassMethod if is_class else libobjc.class_getInstanceMethod
        method = lookup(c, SEL(sel))
        if not method:
            result("not found")
        judge(libobjc.method_getTypeEncoding(method))
    else:
        import objc
        m = getattr(objc.lookUpClass(cls), py, None)
        if m is None:
            result("not found")
        judge(getattr(m, "signature", None))
except Exception as e:
    result("python exception", f"{type(e).__name__}: {e}"[:200])
