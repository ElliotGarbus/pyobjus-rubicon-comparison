"""The Section 3 cases written with Rubicon's public API, as its docs show."""
import asyncio
import ctypes
import os
import sys
import threading
import time
from ctypes import CFUNCTYPE, POINTER, Structure, Union, byref, c_bool, c_char, c_double, c_float, c_int, \
    c_long, c_uint, c_void_p, cast

from rubicon.objc import Block, CGPoint, CGRect, CGSize, NSInteger, NSObject, NSRange, NSUInteger, ObjCBlock, \
    ObjCClass, ObjCInstance, ObjCProtocol, SEL, at, ns_from_py, objc_classmethod, objc_const, objc_id, \
    objc_method, objc_property, py_from_ns, send_super
from rubicon.objc.runtime import libc, libobjc, load_library, objc_block, send_message
from rubicon.objc.types import register_encoding

from cases import FRAMEWORKS, Check, NotApplicable, NotExpressible

CASES = {}


def case(fn):
    CASES[fn.__name__] = fn
    return fn


NSArray = ObjCClass("NSArray")
NSDate = ObjCClass("NSDate")
NSRunLoop = ObjCClass("NSRunLoop")
NSString = ObjCClass("NSString")
NSURLComponents = ObjCClass("NSURLComponents")
S3Types = ObjCClass("S3Types")
S3Caller = ObjCClass("S3Caller")
S3AppCaller = ObjCClass("S3AppCaller")


def spin(done, timeout=5.0):
    """Run the current run loop until done() is true."""
    end = time.monotonic() + timeout
    while not done() and time.monotonic() < end:
        NSRunLoop.currentRunLoop.runUntilDate(NSDate.dateWithTimeIntervalSinceNow(0.01))
    return done()


def foundation():
    return load_library("Foundation")


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
    return str(ObjCClass("NSURL").URLWithString("https://kivy.org/a/b").absoluteString)


@case
def f1_1_multipart():
    return str(at("a-b").stringByReplacingOccurrencesOfString("-", withString="+"))


@case
def f1_1_multipart_held():
    s, old, new = at("a-b"), at("-"), at("+")
    return str(s.stringByReplacingOccurrencesOfString(old, withString=new))


@case
def f1_2_property_attr():
    c = NSURLComponents.alloc().init()
    c.host = "kivy.org"
    return str(S3Caller.valueOf(c, forKey="host"))


@case
def f1_2_property_methods():
    c = NSURLComponents.alloc().init()
    c.setHost("kivy.org")
    return str(S3Caller.valueOf(c, forKey="host"))


@case
def f1_3_format():
    r = send_message(NSString, "stringWithFormat:", at("%ld-%@"), restype=objc_id, argtypes=[objc_id],
                     varargs=[c_long(7), at("x")])
    return str(ObjCInstance(r))


@case
def f1_3_array_with_objects():
    r = send_message(NSArray, "arrayWithObjects:", at("a"), restype=objc_id, argtypes=[objc_id],
                     varargs=[at("b"), None])
    return len(ObjCInstance(r))


@case
def f1_4_object_constant():
    return Check(str(objc_const(foundation(), "NSLocaleCountryCode")),
                 str(ObjCClass("S3Info").localeCountryCodeKey()))


@case
def f1_4_scalar_constant():
    return Check(c_double.in_dll(foundation(), "NSFoundationVersionNumber").value,
                 ObjCClass("S3Info").foundationVersionNumber())


@case
def f1_5_function():
    f = foundation().NSStringFromClass
    f.restype = objc_id
    f.argtypes = [objc_id]
    return str(ObjCInstance(f(NSArray)))


@case
def f1_5_function_struct():
    f = foundation().NSRangeFromString
    f.restype = NSRange
    f.argtypes = [objc_id]
    r = f(at("{3, 4}"))
    return (r.location, r.length)


@case
def f1_6_framework():
    name, cls = next((n, c) for n, c in FRAMEWORKS if not libobjc.objc_getClass(c.encode()))
    load_library(name)
    return Check((name, ObjCClass(cls) is not None), (name, True))


@case
def f1_6_dylib():
    load_library(os.environ["S3_EXTRA"])
    return ObjCClass("S3Extra").answer()


@case
def f1_7_dir():
    return "host" in dir(NSURLComponents.alloc().init())


# F2. Types

@case
def f2_1_user_struct():
    register_encoding(b"{?=ifc}", S3Pair)
    r = S3Types.alloc().init().echoPair(S3Pair(1, 2.5, b"c"))
    return (r.a, r.b, ord(r.c))


@case
def f2_1_struct_pointer_in():
    r = CGRect(CGPoint(1, 2), CGSize(3, 4))
    return S3Types.alloc().init().sumRect(byref(r))


@case
def f2_1_struct_pointer_out():
    r = CGRect()
    S3Types.alloc().init().fillRect(byref(r))
    return (r.origin.x, r.origin.y, r.size.width, r.size.height)


@case
def f2_2_union_arg():
    register_encoding(b"(?=if)", S3Union)
    return S3Types.alloc().init().unionInt(S3Union(i=7))


@case
def f2_2_union_return():
    register_encoding(b"(?=if)", S3Union)
    return S3Types.alloc().init().makeUnion(7).i


@case
def f2_2_bitfield_arg():
    register_encoding(b"{?=b3b5b8}", S3Bits)
    return S3Types.alloc().init().bitsSum(S3Bits(5, 17, 200))


@case
def f2_2_bitfield_return():
    register_encoding(b"{?=b3b5b8}", S3Bits)
    b = S3Types.alloc().init().makeBits()
    return (b.a, b.b, b.c)


@case
def f2_3_fixed_array():
    return S3Types.alloc().init().sumFour((c_int * 4)(1, 2, 3, 4))


@case
def f2_3_pass_array():
    return S3Types.alloc().init().sum((c_int * 4)(1, 2, 3, 4), count=4)


@case
def f2_3_fill_array():
    buf = (c_int * 4)()
    S3Types.alloc().init().fillSquares(buf, count=4)
    return list(buf)


@case
def f2_3_struct_array_field():
    register_encoding(b"{?=[4i]}", S3Quad)
    q = S3Types.alloc().init().echoQuad(S3Quad((c_int * 4)(1, 2, 3, 4)))
    return list(q.v)


@case
def f2_4_scalar_out():
    q = NSInteger()
    ok = S3Types.alloc().init().divide(7, by=2, quotient=byref(q))
    return (ok, q.value)


@case
def f2_4_opaque_pointer():
    t = S3Types.alloc().init()
    return t.alphaOf(t.makeColor())


@case
def f2_4_error_out():
    err = objc_id()
    S3Types.alloc().init().failWithError(byref(err))
    e = ObjCInstance(err)
    return (str(e.domain), e.code)


@case
def f2_5_list_arg():
    return S3Types.alloc().init().countOf(["x", "y", "z"])


@case
def f2_5_dict_arg():
    return str(S3Types.alloc().init().valueIn({"k": "v"}, forKey="k"))


@case
def f2_5_to_py():
    return py_from_ns(S3Types.alloc().init().strings())


@case
def f2_5_from_py():
    return S3Types.alloc().init().countOf(ns_from_py(["a", 1]))


@case
def f2_5_bool_number():
    return py_from_ns(S3Types.alloc().init().booleans())


@case
def f2_6_len():
    return len(S3Types.alloc().init().strings())


@case
def f2_6_index():
    return str(S3Types.alloc().init().strings()[1])


@case
def f2_6_iter():
    return [str(s) for s in S3Types.alloc().init().strings()]


@case
def f2_6_in():
    return "one" in S3Types.alloc().init().mapping()


@case
def f2_6_dict_index():
    return S3Types.alloc().init().mapping()["two"]


@case
def f2_6_str_ops():
    s = at("hello")
    return (s == "hello", str(s.upper()))


@case
def f2_7_enum():
    raise NotApplicable("Rubicon ships no enum constants. A Python constant or enum.IntEnum is used instead")


# F3. Defining Objective-C behavior in Python

@case
def f3_1_instance_method():
    class S3PyValue(NSObject):
        @objc_method
        def s3Value(self) -> NSInteger:
            return 11
    return S3Caller.callInstance(S3PyValue.alloc().init())


@case
def f3_1_class_method():
    class S3PyClassValue(NSObject):
        @objc_classmethod
        def s3ClassValue(cls) -> NSInteger:
            return 12
    return S3Caller.callClass(S3PyClassValue)


def utc_formatter(cls):
    f = cls.alloc().init()
    f.dateFormat = "yyyy-MM-dd"
    f.timeZone = ObjCClass("NSTimeZone").timeZoneForSecondsFromGMT(0)
    return f


@case
def f3_2_override_super():
    NSDateFormatter = ObjCClass("NSDateFormatter")

    class S3PyFormatter(NSDateFormatter):
        @objc_method
        def stringFromDate_(self, date) -> ObjCInstance:
            plain = send_super(__class__, self, "stringFromDate:", date, restype=objc_id, argtypes=[objc_id])
            return at(str(ObjCInstance(plain)) + "!")

    plain = str(utc_formatter(NSDateFormatter).stringFromDate(NSDate.dateWithTimeIntervalSince1970(0)))
    return Check(str(S3Caller.format(utc_formatter(S3PyFormatter))), plain + "!")


@case
def f3_3_property_kvc():
    class S3PyProperty(NSObject):
        count = objc_property(NSInteger)
    o = S3PyProperty.alloc().init()
    o.count = 5
    return py_from_ns(S3Caller.valueOf(o, forKey="count"))


@case
def f3_3_python_state():
    class S3PyState(NSObject):
        @objc_method
        def s3Value(self) -> NSInteger:
            return self.state
    o = S3PyState.alloc().init()
    o.state = 21
    return S3Caller.callInstance(o)


@case
def f3_4_apple_protocol():
    names = []

    class S3PyParserDelegate(NSObject, protocols=[ObjCProtocol("NSXMLParserDelegate")]):
        @objc_method
        def parser_didStartElement_namespaceURI_qualifiedName_attributes_(self, parser, name, uri, qname,
                                                                          attrs) -> None:
            names.append(str(name))

    data = at("<root><item/></root>").dataUsingEncoding(4)
    parser = ObjCClass("NSXMLParser").alloc().initWithData(data)
    delegate = S3PyParserDelegate.alloc().init()
    parser.delegate = delegate
    parser.parse()
    return names


def app_delegate(**methods):
    import types
    ns = {name: objc_method(f) for name, f in methods.items()}
    cls = types.new_class("S3PyApp", (NSObject,), {"protocols": [ObjCProtocol("S3AppProtocol")]},
                          lambda d: d.update(ns))
    return cls.alloc().init()


@case
def f3_5_app_protocol():
    def appValue_(self, v: NSInteger) -> NSInteger:
        return v * 2
    return S3AppCaller.value(app_delegate(appValue_=appValue_), of=4)


@case
def f3_5_app_protocol_registered():
    raise NotApplicable("Rubicon takes method types from annotations, so there's no protocol table to register")


@case
def f3_6_notification():
    got = []

    class S3PyObserver(NSObject):
        @objc_method
        def note_(self, n) -> None:
            got.append(str(n.name))

    center = ObjCClass("NSNotificationCenter").defaultCenter
    o = S3PyObserver.alloc().init()
    center.addObserver(o, selector=SEL("note:"), name="S3Note", object=None)
    center.postNotificationName("S3Note", object=None)
    center.removeObserver(o)
    return got[0] if got else None


@case
def f3_6_timer():
    fired = []

    class S3PyTimerTarget(NSObject):
        @objc_method
        def fire_(self, t) -> None:
            fired.append(True)

    o = S3PyTimerTarget.alloc().init()
    ObjCClass("NSTimer").scheduledTimerWithTimeInterval(0.01, target=o, selector=SEL("fire:"), userInfo=None,
                                                        repeats=False)
    return bool(spin(lambda: fired))


@case
def f3_7_union_arg():
    register_encoding(b"(?=if)", S3Union)

    def appUnion_(self, u: S3Union) -> c_int:
        return u.i
    return S3AppCaller.unionOf(app_delegate(appUnion_=appUnion_), value=9)


@case
def f3_7_array_arg():
    def appArray_count_(self, v: POINTER(c_int), n: NSUInteger) -> c_int:
        return sum(v[i] for i in range(n))
    return S3AppCaller.arraySumOf(app_delegate(appArray_count_=appArray_count_))


@case
def f3_7_bool_return():
    def appShouldContinue_(self, c: NSInteger) -> bool:
        return True
    return S3AppCaller.shouldContinue(app_delegate(appShouldContinue_=appShouldContinue_), count=1)


@case
def f3_7_object_return():
    def appLabel_(self, c: NSInteger) -> ObjCInstance:
        return at(f"label-{c}")
    return str(S3AppCaller.labelOf(app_delegate(appLabel_=appLabel_), count=3))


# F4. Blocks and function pointers

@case
def f4_1_sort_comparator():
    def compare(a: objc_id, b: objc_id) -> NSInteger:
        return ObjCInstance(a).compare(ObjCInstance(b))
    r = ns_from_py(["c", "a", "b"]).sortedArrayUsingComparator(compare)
    return [str(s) for s in r]


@case
def f4_1_enumerate_stop():
    seen = []

    def visit(obj: objc_id, idx: NSUInteger, stop: POINTER(c_bool)) -> None:
        seen.append(idx)
        if len(seen) == 2:
            stop[0] = True
    ns_from_py(["a", "b", "c", "d"]).enumerateObjectsUsingBlock(visit)
    return len(seen)


@case
def f4_1_completion():
    got = []

    def done(result: NSInteger, error: objc_id) -> None:
        got.append(result)
    ObjCClass("S3Async").alloc().init().square(7, completion=done)
    spin(lambda: got)
    return got[0] if got else None


@case
def f4_2_delegate_completion():
    def appDecide_(self, decision: objc_block) -> None:
        ObjCBlock(decision, None, c_bool)(True)
    return S3AppCaller.decisionOf(app_delegate(appDecide_=appDecide_))


class struct_dispatch_queue_s(Structure):
    pass


@case
def f4_3_dispatch_main():
    # Following Rubicon's C functions guide for dispatch_get_main_queue.
    libdispatch = load_library("System") if sys.platform != "ios" else libc
    main_q = struct_dispatch_queue_s.in_dll(libdispatch, "_dispatch_main_q")
    queue = ObjCInstance(cast(byref(main_q), objc_id))
    libdispatch.dispatch_async.restype = None
    libdispatch.dispatch_async.argtypes = [objc_id, objc_block]
    ran = []

    def work() -> None:
        ran.append(threading.current_thread() is threading.main_thread())
    libdispatch.dispatch_async(queue, Block(work, None))
    spin(lambda: ran)
    return ran[0] if ran else None


@case
def f4_4_sort_function():
    @CFUNCTYPE(NSInteger, objc_id, objc_id, c_void_p)
    def compare(a, b, context):
        return ObjCInstance(a).compare(ObjCInstance(b))
    r = ns_from_py(["c", "a", "b"]).sortedArrayUsingFunction(compare, context=None)
    return [str(s) for s in r]


# F5. Runtime services

@case
def f5_3_asyncio_cf():
    from rubicon.objc.eventloop import RubiconEventLoop
    fired = []

    class S3PyLoopTimerTarget(NSObject):
        @objc_method
        def fire_(self, t) -> None:
            fired.append(True)

    o = S3PyLoopTimerTarget.alloc().init()
    ObjCClass("NSTimer").scheduledTimerWithTimeInterval(0.05, target=o, selector=SEL("fire:"), userInfo=None,
                                                        repeats=False)
    loop = RubiconEventLoop()
    loop.run_until_complete(asyncio.sleep(0.5))
    return bool(fired)


@case
def f5_4_perform_on_main():
    ran = []

    class S3PyMainTarget(NSObject):
        @objc_method
        def onMain_(self, arg) -> None:
            ran.append(threading.current_thread() is threading.main_thread())

    o = S3PyMainTarget.alloc().init()
    t = threading.Thread(target=lambda: o.performSelectorOnMainThread(SEL("onMain:"), withObject=None,
                                                                      waitUntilDone=False))
    t.start()
    t.join()
    spin(lambda: ran)
    return ran[0] if ran else None


# F7. Swift

def notebook():
    return ObjCClass("S3Notebook").alloc().initWithTitle("Groceries")


@case
def f7_1_named_class():
    return notebook().addNote("apples")


@case
def f7_1_generated_name():
    return ObjCClass("_TtC7S3Swift7Unnamed").alloc().init().ping()


@case
def f7_2_string():
    return str(notebook().title)


@case
def f7_2_property_write():
    n = notebook()
    n.author = "Kivy"
    return str(S3Caller.valueOf(n, forKey="author"))


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
    n.addNote("x")
    return py_from_ns(n.notes)


@case
def f7_2_int_array():
    return py_from_ns(notebook().squares())


@case
def f7_2_nested_dict():
    return py_from_ns(notebook().summary())


@case
def f7_2_list_arg():
    return notebook().countOf(["a", "b", "c"])


@case
def f7_2_dict_arg():
    return str(notebook().valueIn({"author": "Swift"}, forKey="author"))


@case
def f7_3_success():
    n = notebook()
    n.addNote("x")
    err = objc_id()
    return str(n.noteAtIndex(0, error=byref(err)))


@case
def f7_3_failure_value():
    err = objc_id()
    return notebook().noteAtIndex(5, error=byref(err))


@case
def f7_3_read_error():
    err = objc_id()
    notebook().noteAtIndex(5, error=byref(err))
    return str(ObjCInstance(err).domain)


@case
def f7_4_completion():
    got = []

    def done(greeting: objc_id) -> None:
        got.append(str(ObjCInstance(greeting)))
    notebook().greetingWithCompletionHandler(done)
    spin(lambda: got)
    return got[0] if got else None


@case
def f7_4_throwing_completion():
    got = []

    def done(result: objc_id, error: objc_id) -> None:
        got.append((not result, bool(error)))
    notebook().failingGreetingWithCompletionHandler(done)
    spin(lambda: got)
    return got[0] if got else None


def metronome(raise_first=False):
    record = {"ticks": [], "main": [], "raised": False}

    class S3PyMetronomeDelegate(NSObject, protocols=[ObjCProtocol("S3MetronomeDelegate")]):
        @objc_method
        def metronome_didTick_(self, m, count: NSInteger) -> None:
            record["ticks"].append(count)
            record["main"].append(threading.current_thread() is threading.main_thread())
            if raise_first and not record["raised"]:
                record["raised"] = True
                raise RuntimeError("raised in a delegate method")

        @objc_method
        def metronome_shouldContinueAfter_(self, m, count: NSInteger) -> bool:
            return count < 3

        @objc_method
        def metronome_scaleFor_(self, m, count: NSInteger) -> NSInteger:
            return count * 10

        @objc_method
        def metronome_labelFor_(self, m, count: NSInteger) -> ObjCInstance:
            return at(f"t{count}")

    delegate = S3PyMetronomeDelegate.alloc().init()
    m = ObjCClass("S3Metronome").alloc().init()
    m.delegate = delegate
    return m, delegate, record


@case
def f7_5_tick_main():
    m, d, record = metronome()
    m.runTicks(3)
    return record["ticks"]


@case
def f7_5_bool_return():
    m, d, record = metronome()
    m.runTicks(3)
    return [bool(v) for v in py_from_ns(m.continueAnswers)]


@case
def f7_5_int_return():
    m, d, record = metronome()
    m.runTicks(3)
    return py_from_ns(m.scales)


@case
def f7_5_object_return():
    m, d, record = metronome()
    m.runTicks(3)
    return py_from_ns(m.labels)


@case
def f7_5_background():
    m, d, record = metronome()
    m.startTicksOnBackgroundThread(3)
    end = time.monotonic() + 5
    while not m.finished and time.monotonic() < end:
        time.sleep(0.01)
    return (record["ticks"], any(record["main"]))


@case
def f7_5_exception():
    m, d, record = metronome(raise_first=True)
    m.runTicks(3)
    first = m.ticks
    m.runTicks(3)
    return (first, m.ticks)
