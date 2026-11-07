"""The Section 3 cases written with pyobjus's public API, as its docs show.

Where pyobjus has no direct way but its own API gives an indirect one, such as
a protocol registered at runtime standing in for a method, the case uses it
and says so. Workarounds that need ctypes are separate `__ctypes` cases.
"""
import ctypes
import os
import threading
import time
from ctypes import CFUNCTYPE, Structure, Union, c_char, c_char_p, c_double, c_float, c_int, c_long, c_uint, \
    c_ulong, c_void_p

from pyobjus import autoclass, objc_arr, objc_i, objc_str, protocol, selector, symbol
from pyobjus.dylib_manager import load_dylib, load_framework
from pyobjus.objc_py_types import NSComparisonResult, NSPoint, NSRect, NSSize
from pyobjus.protocols import protocols

from cases import FRAMEWORKS, Check, NotApplicable, NotExpressible

CASES = {}


def case(fn):
    CASES[fn.__name__] = fn
    return fn


NSDate = autoclass("NSDate")
NSRunLoop = autoclass("NSRunLoop")
S3Caller = autoclass("S3Caller")
S3AppCaller = autoclass("S3AppCaller")


def types():
    return autoclass("S3Types").alloc().init()


def text(x):
    """A Python str from an NSString."""
    if x is None:
        return None
    s = x.UTF8String()
    return s.decode() if isinstance(s, bytes) else s


def prop(obj, name):
    """A zero-argument getter, which pyobjus exposes as a value or a method."""
    v = getattr(obj, name)
    return v() if callable(v) else v


def spin(done, timeout=5.0):
    end = time.monotonic() + timeout
    while not done() and time.monotonic() < end:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.01))
    return done()


def wait(done, timeout=5.0):
    end = time.monotonic() + timeout
    while not done() and time.monotonic() < end:
        time.sleep(0.01)
    return done()


def register(name, **encodings):
    """Register a protocol's type encodings at runtime, the pattern in claim 11."""
    protocols[name] = {sel: (enc, enc) for sel, enc in encodings.items()}


def read_ns(x):
    """This test's reader for Foundation values. pyobjus has no public
    conversion from Objective-C to Python, so a pyobjus user writes one."""
    if x is None or isinstance(x, (int, float, str, bool)):
        return x
    if hasattr(x, "UTF8String"):
        return text(x)
    if hasattr(x, "objectForKey_"):
        keys = x.allKeys()
        return {read_ns(keys.objectAtIndex_(i)): read_ns(x.objectForKey_(keys.objectAtIndex_(i)))
                for i in range(prop(keys, "count"))}
    if hasattr(x, "objectAtIndex_"):
        return [read_ns(x.objectAtIndex_(i)) for i in range(prop(x, "count"))]
    if hasattr(x, "objCType"):
        kind = prop(x, "objCType")
        kind = kind.decode() if isinstance(kind, bytes) else kind
        if kind == "c":
            return bool(prop(x, "boolValue"))
        if kind in "fd":
            return prop(x, "doubleValue")
        return prop(x, "longLongValue")
    return x


# Plain ctypes, for the workaround cases.
_objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")  # the name both macOS and iOS have
_objc.objc_getClass.restype = c_void_p
_objc.objc_getClass.argtypes = [c_char_p]
_objc.sel_registerName.restype = c_void_p
_objc.sel_registerName.argtypes = [c_char_p]


def _send(obj, sel, restype, argtypes, *args):
    f = ctypes.cast(_objc.objc_msgSend, CFUNCTYPE(restype, c_void_p, c_void_p, *argtypes))
    return f(obj, _objc.sel_registerName(sel), *args)


def _nsstring(s):
    return _send(_objc.objc_getClass(b"NSString"), b"stringWithUTF8String:", c_void_p, [c_char_p], s.encode())


def _pystring(p):
    return _send(p, b"UTF8String", c_char_p, []).decode()


def _foundation():
    return ctypes.CDLL("/System/Library/Frameworks/Foundation.framework/Foundation")


class S3Pair(Structure):
    _fields_ = [("a", c_int), ("b", c_float), ("c", c_char)]


class S3Union(Union):
    _fields_ = [("i", c_int), ("f", c_float)]


class S3Bits(Structure):
    _fields_ = [("a", c_uint, 3), ("b", c_uint, 5), ("c", c_uint, 8)]


class S3Quad(Structure):
    _fields_ = [("v", c_int * 4)]


# F1. Calling Objective-C and C

@case
def f1_1_class_method():
    return text(prop(autoclass("NSURL").URLWithString_(objc_str("https://kivy.org/a/b")), "absoluteString"))


@case
def f1_1_multipart():
    return text(objc_str("a-b").stringByReplacingOccurrencesOfString_withString_(objc_str("-"), objc_str("+")))


@case
def f1_1_multipart_held():
    s, old, new = objc_str("a-b"), objc_str("-"), objc_str("+")
    return text(s.stringByReplacingOccurrencesOfString_withString_(old, new))


@case
def f1_2_property_attr():
    c = autoclass("NSURLComponents").alloc().init()
    c.host = objc_str("kivy.org")
    return text(S3Caller.valueOf_forKey_(c, objc_str("host")))


@case
def f1_2_property_methods():
    c = autoclass("NSURLComponents").alloc().init()
    c.setHost_(objc_str("kivy.org"))
    return text(S3Caller.valueOf_forKey_(c, objc_str("host")))


@case
def f1_3_format():
    return text(autoclass("NSString").stringWithFormat_(objc_str("%ld-%@"), 7, objc_str("x")))


@case
def f1_3_array_with_objects():
    a = autoclass("NSArray").arrayWithObjects_(objc_str("a"), objc_str("b"), None)
    return prop(a, "count")


@case
def f1_4_object_constant():
    return Check(text(symbol("NSLocaleCountryCode", "NSString")),
                 text(autoclass("S3Info").localeCountryCodeKey()))


@case
def f1_4_scalar_constant():
    raise NotExpressible("pyobjus's symbol() reads only object constants")


@case
def f1_4_scalar_constant__ctypes():
    return Check(c_double.in_dll(_foundation(), "NSFoundationVersionNumber").value,
                 autoclass("S3Info").foundationVersionNumber())


@case
def f1_5_function():
    raise NotExpressible("pyobjus has no public way to call a C function")


@case
def f1_5_function__ctypes():
    f = _foundation().NSStringFromClass
    f.restype = c_void_p
    f.argtypes = [c_void_p]
    return _pystring(f(_objc.objc_getClass(b"NSArray")))


@case
def f1_5_function_struct():
    raise NotExpressible("pyobjus has no public way to call a C function")


@case
def f1_5_function_struct__ctypes():
    class Range(Structure):
        _fields_ = [("location", c_ulong), ("length", c_ulong)]
    f = _foundation().NSRangeFromString
    f.restype = Range
    f.argtypes = [c_void_p]
    r = f(_nsstring("{3, 4}"))
    return (r.location, r.length)


@case
def f1_6_framework():
    name, cls = next((n, c) for n, c in FRAMEWORKS if not _objc.objc_getClass(c.encode()))
    load_framework(f"/System/Library/Frameworks/{name}.framework")
    return Check((name, autoclass(cls) is not None), (name, True))


@case
def f1_6_dylib():
    load_dylib(os.environ["S3_EXTRA"], usr_path=False)
    return autoclass("S3Extra").answer()


@case
def f1_7_dir():
    return "host" in dir(autoclass("NSURLComponents").alloc().init())


# F2. Types

@case
def f2_1_user_struct():
    r = types().echoPair_(S3Pair(1, 2.5, b"c"))
    c = r.c
    return (r.a, r.b, ord(c) if isinstance(c, bytes) else c)


@case
def f2_1_struct_pointer_in():
    return types().sumRect_(NSRect(NSPoint(1, 2), NSSize(3, 4)))


@case
def f2_1_struct_pointer_out():
    r = NSRect(NSPoint(0, 0), NSSize(0, 0))
    types().fillRect_(r)
    return (r.origin.x, r.origin.y, r.size.width, r.size.height)


@case
def f2_2_union_arg():
    return types().unionInt_(S3Union(i=7))


@case
def f2_2_union_return():
    # pyobjus names an unknown type's fields a, b, ..., as its docs describe.
    return types().makeUnion_(7).a


@case
def f2_2_bitfield_arg():
    return types().bitsSum_(S3Bits(5, 17, 200))


@case
def f2_2_bitfield_return():
    b = types().makeBits()
    return (b.a, b.b, b.c)


@case
def f2_3_fixed_array():
    return types().sumFour_((c_int * 4)(1, 2, 3, 4))


@case
def f2_3_pass_array():
    return types().sum_count_((c_int * 4)(1, 2, 3, 4), 4)


@case
def f2_3_fill_array():
    buf = (c_int * 4)()
    types().fillSquares_count_(buf, 4)
    return list(buf)


@case
def f2_3_struct_array_field():
    q = types().echoQuad_(S3Quad((c_int * 4)(1, 2, 3, 4)))
    return list(q.v)


@case
def f2_4_scalar_out():
    q = c_long(0)
    ok = types().divide_by_quotient_(7, 2, q)
    return (ok, q.value)


@case
def f2_4_opaque_pointer():
    t = types()
    return t.alphaOf_(t.makeColor())


@case
def f2_4_error_out():
    raise NotExpressible("pyobjus can pass only nil for an object out parameter")


@case
def f2_5_list_arg():
    return types().countOf_(["x", "y", "z"])


@case
def f2_5_dict_arg():
    return text(types().valueIn_forKey_({"k": "v"}, objc_str("k")))


@case
def f2_5_to_py():
    raise NotExpressible("pyobjus has no public function that converts Objective-C values to Python")


@case
def f2_5_from_py():
    return types().countOf_(objc_arr(objc_str("a"), objc_i(1)))


@case
def f2_5_bool_number():
    raise NotExpressible("pyobjus has no public function that converts Objective-C values to Python")


@case
def f2_6_len():
    return len(types().strings())


@case
def f2_6_index():
    return text(types().strings()[1])


@case
def f2_6_iter():
    return [text(s) for s in types().strings()]


@case
def f2_6_in():
    return "one" in types().mapping()


@case
def f2_6_dict_index():
    return types().mapping()["two"]


@case
def f2_6_str_ops():
    s = objc_str("hello")
    return (s == "hello", text(s.upper()))


@case
def f2_7_enum():
    # The strings are held in variables: inline temporaries give a wrong result
    # (f1_1_multipart), which isn't what this case tests.
    a, b = objc_str("a"), objc_str("b")
    return a.compare_(b) == NSComparisonResult.NSOrderedAscending


# F3. Defining Objective-C behavior in Python

@case
def f3_1_instance_method():
    # pyobjus can't subclass NSObject, but a delegate is an NSObject subclass it
    # creates, and registering a protocol gives it the method.
    register("S3PyValue", s3Value="q16@0:8")

    class Value:
        @protocol("S3PyValue")
        def s3Value(self):
            return 11
    return S3Caller.callInstance_(Value())


@case
def f3_1_class_method():
    raise NotExpressible("pyobjus has no public way to define a class method")


@case
def f3_2_override_super():
    raise NotExpressible("pyobjus has no public API for subclassing an Objective-C class")


@case
def f3_3_property_kvc():
    raise NotExpressible("pyobjus has no public way to declare a property on a delegate")


@case
def f3_3_python_state():
    register("S3PyState", s3Value="q16@0:8")

    class State:
        state = 0

        @protocol("S3PyState")
        def s3Value(self):
            return self.state
    o = State()
    o.state = 21
    return S3Caller.callInstance_(o)


@case
def f3_4_apple_protocol():
    names = []

    class ParserDelegate:
        @protocol("NSXMLParserDelegate")
        def parser_didStartElement_namespaceURI_qualifiedName_attributes_(self, parser, name, uri, qname, attrs):
            names.append(text(name))

    data = objc_str("<root><item/></root>").dataUsingEncoding_(4)
    parser = autoclass("NSXMLParser").alloc().initWithData_(data)
    delegate = ParserDelegate()
    parser.setDelegate_(delegate)
    parser.parse()
    return names


@case
def f3_5_app_protocol():
    class App:
        @protocol("S3AppProtocol")
        def appValue_(self, v):
            return v * 2
    return S3AppCaller.value_of_(App(), 4)


@case
def f3_5_app_protocol_registered():
    # A name the runtime doesn't know, so pyobjus uses the registered table.
    register("S3Registered", **{"appValue:": "q24@0:8q16"})

    class App:
        @protocol("S3Registered")
        def appValue_(self, v):
            return v * 2
    return S3AppCaller.value_of_(App(), 4)


@case
def f3_6_notification():
    register("S3Observer", **{"note:": "v24@0:8@16"})
    got = []

    class Observer:
        @protocol("S3Observer")
        def note_(self, n):
            got.append(text(prop(n, "name")))

    center = autoclass("NSNotificationCenter").defaultCenter()
    o = Observer()
    center.addObserver_selector_name_object_(o, selector("note:"), objc_str("S3Note"), None)
    center.postNotificationName_object_(objc_str("S3Note"), None)
    center.removeObserver_(o)
    return got[0] if got else None


@case
def f3_6_timer():
    register("S3TimerTarget", **{"fire:": "v24@0:8@16"})
    fired = []

    class Target:
        @protocol("S3TimerTarget")
        def fire_(self, t):
            fired.append(True)

    o = Target()
    autoclass("NSTimer").scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        0.01, o, selector("fire:"), None, False)
    return bool(spin(lambda: fired))


def app(**methods):
    cls = type("S3PyApp", (object,), {name: protocol("S3AppProtocol")(f) for name, f in methods.items()})
    return cls()


@case
def f3_7_union_arg():
    def appUnion_(self, u):
        return u.i
    return S3AppCaller.unionOf_value_(app(appUnion_=appUnion_), 9)


@case
def f3_7_array_arg():
    def appArray_count_(self, v, n):
        return sum(v[i] for i in range(n))
    return S3AppCaller.arraySumOf_(app(appArray_count_=appArray_count_))


@case
def f3_7_bool_return():
    def appShouldContinue_(self, c):
        return True
    return S3AppCaller.shouldContinue_count_(app(appShouldContinue_=appShouldContinue_), 1)


@case
def f3_7_object_return():
    def appLabel_(self, c):
        return objc_str(f"label-{c}")
    return text(S3AppCaller.labelOf_count_(app(appLabel_=appLabel_), 3))


# F4. Blocks and function pointers

@case
def f4_1_sort_comparator():
    raise NotExpressible("pyobjus has no public API for creating a block")


@case
def f4_1_enumerate_stop():
    raise NotExpressible("pyobjus has no public API for creating a block")


@case
def f4_1_completion():
    raise NotExpressible("pyobjus has no public API for creating a block")


@case
def f4_1_completion__helper():
    got = []

    class HelperDelegate:
        @protocol("S3AsyncHelperDelegate")
        def helperFinished_(self, result):
            got.append(result)

    d = HelperDelegate()
    autoclass("S3AsyncHelper").square_delegate_(7, d)
    wait(lambda: got)
    return got[0] if got else None


@case
def f4_2_delegate_completion():
    seen = []

    def appDecide_(self, decision):
        seen.append(type(decision).__name__)
        decision(True)
    result = S3AppCaller.decisionOf_(app(appDecide_=appDecide_))
    if result == -1 and seen:
        raise NotExpressible(f"the block arrives as {seen[0]}, with no public way to call it")
    return result


@case
def f4_3_dispatch_main():
    raise NotExpressible("pyobjus has no public API for creating a block or calling a C function")


@case
def f4_4_sort_function():
    raise NotExpressible("pyobjus has no public way to pass a function pointer (Section 2, CB2)")


@case
def f4_4_sort_function__ctypes():
    @CFUNCTYPE(c_long, c_void_p, c_void_p, c_void_p)
    def compare(a, b, context):
        return _send(a, b"compare:", c_long, [c_void_p], b)

    items = [_nsstring(s) for s in ("c", "a", "b")]
    array = _send(_objc.objc_getClass(b"NSArray"), b"arrayWithObjects:count:", c_void_p,
                  [ctypes.POINTER(c_void_p), c_ulong], (c_void_p * 3)(*items), 3)
    r = _send(array, b"sortedArrayUsingFunction:context:", c_void_p, [c_void_p, c_void_p], compare, None)
    return [_pystring(_send(r, b"objectAtIndex:", c_void_p, [c_ulong], i)) for i in range(3)]


# F5. Runtime services

@case
def f5_3_asyncio_cf():
    raise NotExpressible("pyobjus has no integration with asyncio or the Core Foundation run loop")


@case
def f5_4_perform_on_main():
    # pyobjus gives no handle on the Objective-C object behind a delegate, so the
    # delegate's method is reached through a timer added to the main run loop.
    register("S3MainTarget", **{"onMain:": "v24@0:8@16"})
    ran = []

    class Target:
        @protocol("S3MainTarget")
        def onMain_(self, t):
            ran.append(threading.current_thread() is threading.main_thread())

    o = Target()

    def from_thread():
        t = autoclass("NSTimer").timerWithTimeInterval_target_selector_userInfo_repeats_(
            0, o, selector("onMain:"), None, False)
        autoclass("NSRunLoop").mainRunLoop().addTimer_forMode_(t, objc_str("kCFRunLoopDefaultMode"))
    th = threading.Thread(target=from_thread)
    th.start()
    th.join()
    spin(lambda: ran)
    return ran[0] if ran else None


# F7. Swift

def notebook():
    return autoclass("S3Notebook").alloc().initWithTitle_(objc_str("Groceries"))


@case
def f7_1_named_class():
    return notebook().addNote_(objc_str("apples"))


@case
def f7_1_generated_name():
    return autoclass("_TtC7S3Swift7Unnamed").alloc().init().ping()


@case
def f7_2_string():
    return text(prop(notebook(), "title"))


@case
def f7_2_property_write():
    n = notebook()
    n.author = objc_str("Kivy")
    return text(S3Caller.valueOf_forKey_(n, objc_str("author")))


@case
def f7_2_scalars():
    n = notebook()
    return (n.ratio(), n.isReady())


@case
def f7_2_optional_nil():
    return notebook().missing()


@case
def f7_2_string_array():
    n = notebook()
    n.addNote_(objc_str("x"))
    return read_ns(prop(n, "notes"))


@case
def f7_2_int_array():
    return read_ns(notebook().squares())


@case
def f7_2_nested_dict():
    return read_ns(notebook().summary())


@case
def f7_2_list_arg():
    return notebook().countOf_(["a", "b", "c"])


@case
def f7_2_dict_arg():
    return text(notebook().valueIn_forKey_({"author": "Swift"}, objc_str("author")))


@case
def f7_3_success():
    n = notebook()
    n.addNote_(objc_str("x"))
    return text(n.noteAtIndex_error_(0, None))


@case
def f7_3_failure_value():
    return notebook().noteAtIndex_error_(5, None)


@case
def f7_3_read_error():
    raise NotExpressible("pyobjus can pass only nil for an object out parameter")


@case
def f7_4_completion():
    raise NotExpressible("pyobjus has no public API for creating a block")


@case
def f7_4_throwing_completion():
    raise NotExpressible("pyobjus has no public API for creating a block")


def metronome(raise_first=False):
    record = {"ticks": [], "main": [], "raised": False}

    class MetronomeDelegate:
        @protocol("S3MetronomeDelegate")
        def metronome_didTick_(self, m, count):
            record["ticks"].append(count)
            record["main"].append(threading.current_thread() is threading.main_thread())
            if raise_first and not record["raised"]:
                record["raised"] = True
                raise RuntimeError("raised in a delegate method")

        @protocol("S3MetronomeDelegate")
        def metronome_shouldContinueAfter_(self, m, count):
            return count < 3

        @protocol("S3MetronomeDelegate")
        def metronome_scaleFor_(self, m, count):
            return count * 10

        @protocol("S3MetronomeDelegate")
        def metronome_labelFor_(self, m, count):
            return objc_str(f"t{count}")

    delegate = MetronomeDelegate()
    m = autoclass("S3Metronome").alloc().init()
    m.setDelegate_(delegate)
    return m, delegate, record


@case
def f7_5_tick_main():
    m, d, record = metronome()
    m.runTicks_(3)
    return record["ticks"]


@case
def f7_5_bool_return():
    m, d, record = metronome()
    m.runTicks_(3)
    return read_ns(prop(m, "continueAnswers"))


@case
def f7_5_int_return():
    m, d, record = metronome()
    m.runTicks_(3)
    return read_ns(prop(m, "scales"))


@case
def f7_5_object_return():
    m, d, record = metronome()
    m.runTicks_(3)
    return read_ns(prop(m, "labels"))


@case
def f7_5_background():
    m, d, record = metronome()
    m.startTicksOnBackgroundThread_(3)
    wait(lambda: prop(m, "finished"))
    return (record["ticks"], any(record["main"]))


@case
def f7_5_exception():
    m, d, record = metronome(raise_first=True)
    m.runTicks_(3)
    first = prop(m, "ticks")
    m.runTicks_(3)
    return (first, prop(m, "ticks"))
