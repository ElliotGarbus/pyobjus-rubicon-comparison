"""Section 6 measurements, run inside one library's Python process.

Usage: bench.py LIB FIXTURE MODE [ARG]

LIB is pyobjus, rubicon, pyobjc or none (Python only). MODE is one of:

- calibrate OP: per-call time of one timed operation, to choose N
- timing OP:N: one operation of C1 to C4 or CB1, with rounds of N calls
- first_use CLASS: C5, for S6Fresh5 or S6Fresh100
- memory KIND: M1 (import), M2 (held), M3 (alloc_init, new, copy, method,
  delegate) or M4 (steady). M4:CALLS sets the number of calls, which is
  1,000,000 by default, with 10 samples
- import: S1, timed inside the process

Prints one line, "S6RESULT " and JSON. On iOS, run() is called directly.

Each library is called the way its docs show. The harness's own helpers
(memory, autorelease pools, thermal state) use ctypes and the Objective-C
runtime directly, the same way for every library.
"""
import ctypes
import gc
import itertools
import json
import os
import statistics
import sys
import time

WARMUP, ROUNDS = 3, 30
TARGET_ROUND_NS = 20_000_000
HITS = [0]  # delegate calls received, for the value checks

# --- Library-neutral helpers --------------------------------------------------

_objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
_objc.objc_autoreleasePoolPush.restype = ctypes.c_void_p
_objc.objc_autoreleasePoolPop.argtypes = [ctypes.c_void_p]
_objc.objc_getClass.restype = ctypes.c_void_p
_objc.objc_getClass.argtypes = [ctypes.c_char_p]
_objc.sel_registerName.restype = ctypes.c_void_p
_objc.sel_registerName.argtypes = [ctypes.c_char_p]
_send_id = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
    ("objc_msgSend", _objc))
_send_long = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)(
    ("objc_msgSend", _objc))


class _TaskVMInfo(ctypes.Structure):
    _fields_ = [("virtual_size", ctypes.c_uint64), ("region_count", ctypes.c_int32),
                ("page_size", ctypes.c_int32)] + \
               [(name, ctypes.c_uint64) for name in (
                   "resident_size", "resident_size_peak", "device", "device_peak", "internal",
                   "internal_peak", "external", "external_peak", "reusable", "reusable_peak",
                   "purgeable_volatile_pmap", "purgeable_volatile_resident",
                   "purgeable_volatile_virtual", "compressed", "compressed_peak",
                   "compressed_lifetime", "phys_footprint")] + \
               [("_rest", ctypes.c_uint64 * 32)]


_libsys = ctypes.CDLL(None)
_libsys.mach_task_self.restype = ctypes.c_uint32
_TASK_VM_INFO = 22


def footprint():
    """phys_footprint in bytes, the measure iOS uses to end apps for memory."""
    info = _TaskVMInfo()
    count = ctypes.c_uint32(ctypes.sizeof(info) // 4)
    kr = _libsys.task_info(_libsys.mach_task_self(), _TASK_VM_INFO, ctypes.byref(info), ctypes.byref(count))
    if kr != 0:
        raise OSError("task_info failed: {}".format(kr))
    return info.phys_footprint


def pool_push():
    return _objc.objc_autoreleasePoolPush()


def pool_pop(pool):
    _objc.objc_autoreleasePoolPop(pool)


def thermal_state():
    """NSProcessInfo.thermalState: 0 nominal, 1 fair, 2 serious, 3 critical."""
    info = _send_id(_objc.objc_getClass(b"NSProcessInfo"), _objc.sel_registerName(b"processInfo"))
    return _send_long(info, _objc.sel_registerName(b"thermalState"))


_send_bool = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", _objc))


def low_power_mode():
    """NSProcessInfo.lowPowerModeEnabled."""
    info = _send_id(_objc.objc_getClass(b"NSProcessInfo"), _objc.sel_registerName(b"processInfo"))
    return bool(_send_bool(info, _objc.sel_registerName(b"isLowPowerModeEnabled")))


def item_counts():
    cls = _objc.objc_getClass(b"S6Item")
    return {"created": _send_long(cls, _objc.sel_registerName(b"createdCount")),
            "deallocated": _send_long(cls, _objc.sel_registerName(b"deallocCount"))}


def collect():
    gc.collect()
    pool_pop(pool_push())


# --- Libraries ----------------------------------------------------------------
# Each returns a namespace of objects, and statements written the library's
# usual way. A statement is None where the library can't express it.

def setup_pyobjus():
    from pyobjus import autoclass, protocol
    from pyobjus.objc_py_types import NSPoint, NSRect, NSSize
    autoclass("S6Caller").delegateProtocol()

    class Delegate:
        @protocol("S6Delegate")
        def delegateNoop(self):
            HITS[0] += 1

        @protocol("S6Delegate")
        def delegateInt_(self, v):
            return v

        @protocol("S6Delegate")
        def delegateObject_(self, v):
            HITS[0] += 1

    T = autoclass("S6Target")
    ns = {"T": T, "t": T.alloc().init(), "item": autoclass("S6Item").alloc().init(),
          "rect": NSRect(NSPoint(1, 2), NSSize(3, 4)), "caller": autoclass("S6Caller").alloc().init(),
          "Delegate": Delegate, "Item": autoclass("S6Item")}
    ns["d"] = Delegate()
    stmts = {
        "noop": "t.noop()",
        "int": "t.echoInt_(5)",
        "double": "t.echoDouble_(1.5)",
        "bool": "t.echoBool_(True)",
        "object": "t.echoObject_(item)",
        "rect": "t.echoRect_(rect)",
        "str10": "t.echoString_(s10).UTF8String()",
        "str10000": "t.echoString_(s10000).UTF8String()",
        "class_method": "T.classNoop()",
        "prop_read": "t.value",
        "prop_write": "t.value = 5",
        "bound_setup": {"noop": "t.noop", "int": "t.echoInt_", "double": "t.echoDouble_",
                        "bool": "t.echoBool_", "object": "t.echoObject_", "rect": "t.echoRect_",
                        "str10": "t.echoString_", "str10000": "t.echoString_"},
        "text": ".UTF8String()",
        "cb_noop": "caller.callNoop_times_(d, n)",
        "cb_int": "caller.callInt_times_(d, n)",
        "cb_object": "caller.callObject_argument_times_(d, item, n)",
        "new_delegate": "Delegate()",
        "use_delegate": "caller.useDelegate_(x)",
        "alloc_init": "Item.alloc().init()",
        "new": "Item.new()",
        "copy": "item.copy()",
        "method": "Item.item()",
        "make_item": "t.makeItem()",
        "fresh": "autoclass('{cls}').fresh()",
    }
    ns["autoclass"] = autoclass
    return ns, stmts


def setup_rubicon():
    from rubicon.objc import CGPoint, CGRect, CGSize, NSObject, ObjCClass, ObjCProtocol, objc_method

    class S6PyDelegate(NSObject, protocols=[ObjCProtocol("S6Delegate")]):
        @objc_method
        def delegateNoop(self) -> None:
            HITS[0] += 1

        @objc_method
        def delegateInt_(self, v: int) -> int:
            return v

        @objc_method
        def delegateObject_(self, v) -> None:
            HITS[0] += 1

    T = ObjCClass("S6Target")
    ns = {"T": T, "t": T.alloc().init(), "item": ObjCClass("S6Item").alloc().init(),
          "rect": CGRect(CGPoint(1, 2), CGSize(3, 4)), "caller": ObjCClass("S6Caller").alloc().init(),
          "Delegate": S6PyDelegate, "Item": ObjCClass("S6Item"), "ObjCClass": ObjCClass}
    ns["d"] = S6PyDelegate.alloc().init()
    stmts = {
        "noop": "t.noop()",
        "int": "t.echoInt(5)",
        "double": "t.echoDouble(1.5)",
        "bool": "t.echoBool(True)",
        "object": "t.echoObject(item)",
        "rect": "t.echoRect(rect)",
        "str10": "str(t.echoString(s10))",
        "str10000": "str(t.echoString(s10000))",
        "class_method": "T.classNoop()",
        "prop_read": "t.value",
        "prop_write": "t.value = 5",
        "bound_setup": {"noop": "t.noop", "int": "t.echoInt", "double": "t.echoDouble",
                        "bool": "t.echoBool", "object": "t.echoObject", "rect": "t.echoRect",
                        "str10": "t.echoString", "str10000": "t.echoString"},
        "text": "str",
        "cb_noop": "caller.callNoop(d, times=n)",
        "cb_int": "caller.callInt(d, times=n)",
        "cb_object": "caller.callObject(d, argument=item, times=n)",
        "new_delegate": "Delegate.alloc().init()",
        "use_delegate": "caller.useDelegate(x)",
        "alloc_init": "Item.alloc().init()",
        "new": "Item.new()",
        "copy": "item.copy()",
        "method": "Item.item()",
        "make_item": "t.makeItem()",
        "fresh": "ObjCClass('{cls}').fresh()",
    }
    return ns, stmts


def setup_pyobjc():
    import Foundation
    import objc

    proto = objc.protocolNamed("S6Delegate")

    class S6PyObjCDelegate(Foundation.NSObject, protocols=[proto]):
        def delegateNoop(self):
            HITS[0] += 1

        def delegateInt_(self, v):
            return v

        def delegateObject_(self, v):
            HITS[0] += 1

    T = objc.lookUpClass("S6Target")
    ns = {"T": T, "t": T.alloc().init(), "item": objc.lookUpClass("S6Item").alloc().init(),
          "rect": Foundation.NSMakeRect(1, 2, 3, 4), "caller": objc.lookUpClass("S6Caller").alloc().init(),
          "Delegate": S6PyObjCDelegate, "Item": objc.lookUpClass("S6Item"), "objc": objc}
    ns["d"] = S6PyObjCDelegate.alloc().init()
    stmts = {
        "noop": "t.noop()",
        "int": "t.echoInt_(5)",
        "double": "t.echoDouble_(1.5)",
        "bool": "t.echoBool_(True)",
        "object": "t.echoObject_(item)",
        "rect": "t.echoRect_(rect)",
        "str10": "t.echoString_(s10)",
        "str10000": "t.echoString_(s10000)",
        "class_method": "T.classNoop()",
        "prop_read": "t.value()",
        "prop_write": "t.setValue_(5)",
        "bound_setup": {"noop": "t.noop", "int": "t.echoInt_", "double": "t.echoDouble_",
                        "bool": "t.echoBool_", "object": "t.echoObject_", "rect": "t.echoRect_",
                        "str10": "t.echoString_", "str10000": "t.echoString_"},
        "text": "",
        "cb_noop": "caller.callNoop_times_(d, n)",
        "cb_int": "caller.callInt_times_(d, n)",
        "cb_object": "caller.callObject_argument_times_(d, item, n)",
        "fresh": "objc.lookUpClass('{cls}').fresh()",
    }
    return ns, stmts


SETUPS = {"pyobjus": setup_pyobjus, "rubicon": setup_rubicon, "pyobjc": setup_pyobjc}

ARGS = {"noop": "", "int": "5", "double": "1.5", "bool": "True", "object": "item", "rect": "rect",
        "str10": "s10", "str10000": "s10000"}


def operations(ns, stmts):
    """Name -> statement for every timed call (C1 to C4) and the reference."""
    ns["s10"] = "abcdefghij"
    ns["s10000"] = "abcdefghij" * 1000
    ops = {}
    for name in ("noop", "int", "double", "bool", "object", "rect", "str10", "str10000",
                 "class_method", "prop_read", "prop_write"):
        ops[name] = stmts[name]
    for name, getter in stmts["bound_setup"].items():
        key = "bound_" + name
        ns["f_" + name] = eval(getter, ns)
        call = "f_{}({})".format(name, ARGS[name])
        text = stmts["text"]
        if name.startswith("str"):
            call = "{}({})".format(text, call) if text and not text.startswith(".") else call + text
        ops[key] = call
    return ops


def _round_function(stmt, ns, names):
    """A function that runs stmt n times and returns the elapsed nanoseconds,
    with the objects bound as local defaults so lookup costs are the same."""
    params = "".join(", {0}={0}".format(k) for k in names)
    src = ("def _round(n, _repeat=_repeat, _clock=_clock{}):\n"
           "    t0 = _clock()\n"
           "    for _ in _repeat(None, n):\n"
           "        {}\n"
           "    return _clock() - t0\n").format(params, stmt)
    scope = dict(ns, _repeat=itertools.repeat, _clock=time.perf_counter_ns)
    exec(src, scope)
    return scope["_round"]


def _callback_function(stmt, ns, names):
    """CB1: one call into Objective-C makes n delegate calls."""
    params = "".join(", {0}={0}".format(k) for k in names)
    src = ("def _round(n, _clock=_clock{}):\n"
           "    t0 = _clock()\n"
           "    {}\n"
           "    return _clock() - t0\n").format(params, stmt)
    scope = dict(ns, _clock=time.perf_counter_ns)
    exec(src, scope)
    return scope["_round"]


def _names(ns):
    return [k for k in ns if k.isidentifier() and not k.startswith("_")]


def timed_rounds(fn, n, rounds, warmup):
    times, drains, thermal = [], [], [thermal_state()]
    for i in range(warmup + rounds):
        gc.collect()
        pool = pool_push()
        elapsed = fn(n)
        t0 = time.perf_counter_ns()
        pool_pop(pool)
        drain = time.perf_counter_ns() - t0
        if i >= warmup:
            times.append(elapsed)
            drains.append(drain)
    thermal.append(thermal_state())
    return {"n": n, "round_ns": times, "drain_ns": drains, "thermal": thermal,
            "per_call_ns_median": statistics.median(times) / n}


S10 = "abcdefghij"
EXPECTED = {"noop": None, "int": 5, "double": 1.5, "bool": True, "object": True,
            "rect": (1.0, 2.0, 3.0, 4.0), "str10": S10, "str10000": S10 * 1000, "class_method": None,
            "prop_read": 0, "prop_write": 5, "cb_noop": 10, "cb_int": 45, "cb_object": 10,
            "python_empty_call": None}


def _normalize(name, value):
    base = name[len("bound_"):] if name.startswith("bound_") else name
    if base == "rect":
        return (value.origin.x, value.origin.y, value.size.width, value.size.height)
    if base == "object":
        return value is not None
    return value


def check(name, stmt, ns, stmts):
    """Run the operation once and compare its result with the expected value."""
    base = name[len("bound_"):] if name.startswith("bound_") else name
    scope = dict(ns)
    try:
        if name.startswith("cb_"):
            before = HITS[0]
            scope["n"] = 10
            value = eval(stmt, scope)
            value = value if name == "cb_int" else HITS[0] - before
        elif name == "prop_write":
            exec(stmt, scope)
            value = eval(stmts["prop_read"], scope)
        else:
            value = _normalize(name, eval(stmt, scope))
    except Exception as e:
        return {"ok": False, "value": "{}: {}".format(type(e).__name__, e)[:200]}
    expected = EXPECTED[base]
    ok = value == expected and type(value) is type(expected) if isinstance(expected, str) else value == expected
    return {"ok": bool(ok), "value": repr(value)[:80], "type": type(value).__name__}


def suite(lib, only=None):
    """The timed operations for lib, as name -> (kind, function, check result).
    With only, just that one is set up and checked, so a crash in one
    operation doesn't affect the others."""
    if lib == "none":
        def empty():
            pass
        ns = {"empty": empty}
        return {"python_empty_call": ("call", _round_function("empty()", ns, _names(ns)),
                                      check("python_empty_call", "empty()", ns, {}))}
    ns, stmts = SETUPS[lib]()
    out = {}
    ops = operations(ns, stmts)
    names = _names(ns)
    for name, stmt in ops.items():
        if only in (None, name):
            out[name] = ("call", _round_function(stmt, ns, names), check(name, stmt, ns, stmts))
    for name in ("cb_noop", "cb_int", "cb_object"):
        if only in (None, name):
            out[name] = ("callback", _callback_function(stmts[name], ns, names),
                         check(name, stmts[name], ns, stmts))
    return out


def operation_names(lib):
    if lib == "none":
        return ["python_empty_call"]
    return ["noop", "int", "double", "bool", "object", "rect", "str10", "str10000", "class_method",
            "prop_read", "prop_write"] + ["bound_" + k for k in ARGS] + ["cb_noop", "cb_int", "cb_object"]


def calibrate(lib, only):
    """Per-call time of one operation, from a round sized to take about 20 ms."""
    result = {}
    for name, (kind, fn, checked) in suite(lib, only).items():
        n = 1
        while True:
            pool = pool_push()
            elapsed = fn(n)
            pool_pop(pool)
            if elapsed >= TARGET_ROUND_NS or n >= 10_000_000:
                break
            n = max(n * 2, int(n * TARGET_ROUND_NS / max(elapsed, 1) * 1.2))
        result[name] = {"per_call_ns": elapsed / n, "check": checked}
    return result


def timing(lib, only, n):
    out = {}
    for name, (kind, fn, checked) in suite(lib, only).items():
        try:
            out[name] = timed_rounds(fn, n, ROUNDS, WARMUP)
        except Exception as e:
            out[name] = {"error": "{}: {}".format(type(e).__name__, e)[:300]}
        out[name]["check"] = checked
    return out


def first_use(lib, cls):
    """C5: the library is imported and has wrapped NSObject already, so its own
    one-time setup isn't counted."""
    if lib == "pyobjus":
        from pyobjus import autoclass
        autoclass("NSObject")
        stmt = "autoclass('{}').fresh()".format(cls)
        ns = {"autoclass": autoclass}
    elif lib == "rubicon":
        from rubicon.objc import ObjCClass
        ObjCClass("NSObject")
        stmt = "ObjCClass('{}').fresh()".format(cls)
        ns = {"ObjCClass": ObjCClass}
    else:
        import objc
        objc.lookUpClass("NSObject")
        stmt = "objc.lookUpClass('{}').fresh()".format(cls)
        ns = {"objc": objc}
    code = compile(stmt, "<first_use>", "eval")
    t0 = time.perf_counter_ns()
    value = eval(code, ns)
    elapsed = time.perf_counter_ns() - t0
    return {"class": cls, "ns": elapsed, "value": value}


def import_time(lib):
    """S1, inside the process: from just before the import to after the first call."""
    t0 = time.perf_counter_ns()
    if lib == "pyobjus":
        from pyobjus import autoclass
        autoclass("NSObject").alloc().init()
    elif lib == "rubicon":
        from rubicon.objc import NSObject
        NSObject.alloc().init()
    else:
        import objc
        objc.lookUpClass("NSObject").alloc().init()
    return {"ns": time.perf_counter_ns() - t0}


def memory(lib, kind):
    import tracemalloc
    if kind == "M1":
        collect()
        tracemalloc.start()
        before = footprint()
        if lib == "pyobjus":
            from pyobjus import autoclass
            autoclass("NSObject")
        elif lib == "rubicon":
            from rubicon.objc import NSObject  # noqa: F401
        collect()
        return {"footprint_bytes": footprint() - before, "python_bytes": tracemalloc.get_traced_memory()[0]}
    ns, stmts = SETUPS[lib]()
    _send_id(_objc.objc_getClass(b"S6Item"), _objc.sel_registerName(b"resetCounts"))
    count = 1_000 if kind == "delegate" else 10_000
    if kind == "M2":
        create = compile(stmts["method"], "<create>", "eval")
        for _ in range(10):
            eval(create, ns)
        collect()
        tracemalloc.start()
        before, py_before = footprint(), tracemalloc.get_traced_memory()[0]
        pool = pool_push()
        held = [eval(create, ns) for _ in range(count)]
        pool_pop(pool)
        collect()
        result = {"count": count, "footprint_bytes": footprint() - before,
                  "python_bytes": tracemalloc.get_traced_memory()[0] - py_before}
        result["items"] = item_counts()
        del held
        return result
    if kind.startswith("M4"):
        per_sample = int(kind.split(":")[1]) // 10 if ":" in kind else 100_000
        make = compile(stmts["make_item"], "<make>", "eval")
        for _ in range(1000):
            eval(make, ns)
        collect()
        samples = [footprint()]
        for _ in range(10):
            pool = pool_push()
            for _ in range(per_sample):
                eval(make, ns)
            pool_pop(pool)
            collect()
            samples.append(footprint())
        return {"calls_per_sample": per_sample, "footprint_samples": samples, "items": item_counts()}
    # M3: create and drop.
    if kind == "delegate":
        new = compile(stmts["new_delegate"], "<new>", "eval")
        use = compile(stmts["use_delegate"], "<use>", "exec")

        def once():
            ns["x"] = eval(new, ns)
            exec(use, ns)
            del ns["x"]
    else:
        create = compile(stmts[kind], "<create>", "eval")

        def once():
            eval(create, ns)
    for _ in range(10):
        once()
    collect()
    tracemalloc.start()
    counts_before = item_counts()
    before, py_before = footprint(), tracemalloc.get_traced_memory()[0]
    for start in range(0, count, 1000):
        pool = pool_push()
        for _ in range(1000):
            once()
        pool_pop(pool)
    collect()
    after = item_counts()
    return {"count": count, "footprint_bytes": footprint() - before,
            "python_bytes": tracemalloc.get_traced_memory()[0] - py_before,
            "items_created": after["created"] - counts_before["created"],
            "items_deallocated": after["deallocated"] - counts_before["deallocated"]}


def version(lib):
    if lib == "pyobjus":
        import pyobjus
        return pyobjus.__version__
    if lib == "rubicon":
        import rubicon.objc
        return rubicon.objc.__version__
    if lib == "pyobjc":
        import objc
        return objc.__version__
    return None


def run(lib, mode, arg=None):
    start = {"thermal": thermal_state(), "low_power": low_power_mode()}
    if mode == "calibrate":
        result = calibrate(lib, arg)
    elif mode == "timing":
        name, n = arg.rsplit(":", 1)
        result = timing(lib, name, int(n))
    elif mode == "first_use":
        result = first_use(lib, arg)
    elif mode == "memory":
        result = memory(lib, arg)
    elif mode == "import":
        result = import_time(lib)
    elif mode == "version":
        result = version(lib)
    else:
        raise ValueError(mode)
    return {"lib": lib, "mode": mode, "arg": arg, "result": result,
            "thermal_start": start["thermal"], "thermal_end": thermal_state(),
            "low_power_mode": start["low_power"],
            "python": sys.version.split()[0], "platform": sys.platform}


def main():
    lib, fixture, mode = sys.argv[1:4]
    arg = sys.argv[4] if len(sys.argv) > 4 else None
    if mode not in ("import", "version") and not (mode == "memory" and arg == "M1"):
        ctypes.CDLL(fixture)
    out = run(lib, mode, arg)
    print("S6RESULT " + json.dumps(out), flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
