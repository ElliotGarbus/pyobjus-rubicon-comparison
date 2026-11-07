"""The Section 3 cases for the PyObjC control, on the Mac only. Results are
reported separately and aren't compared or scored. The fixture's blocks, out
parameters and C arrays are described with registerMetaDataForSelector, as
PyObjC documents for code without BridgeSupport metadata."""
import asyncio
import ctypes
import os
import threading
import time

import objc
import Foundation
from Foundation import NSArray, NSDate, NSDateFormatter, NSMakeRect, NSObject, NSRunLoop, NSString, NSTimeZone
from PyObjCTools.Conversion import pythonCollectionFromPropertyList

from cases import FRAMEWORKS, Check, NotApplicable, NotExpressible

CASES = {}


def case(fn):
    CASES[fn.__name__] = fn
    return fn


def reg(cls, sel, meta):
    objc.registerMetaDataForSelector(cls, sel, meta)


reg(b"S3Types", b"sumRect:", {"arguments": {2: {"type_modifier": b"n"}}})
reg(b"S3Types", b"fillRect:", {"arguments": {2: {"type_modifier": b"o"}}})
reg(b"S3Types", b"failWithError:", {"arguments": {2: {"type_modifier": b"o"}}})
reg(b"S3Notebook", b"noteAtIndex:error:", {"arguments": {3: {"type_modifier": b"o"}}})
reg(b"NSObject", b"appArray:count:", {"arguments": {2: {"type_modifier": b"n", "c_array_length_in_arg": 3}}})
reg(b"S3Types", b"sum:count:", {"arguments": {2: {"type_modifier": b"n", "c_array_length_in_arg": 3}}})
reg(b"S3Types", b"fillSquares:count:", {"arguments": {2: {"type_modifier": b"o", "c_array_length_in_arg": 3}}})
reg(b"S3Types", b"divide:by:quotient:", {"arguments": {4: {"type_modifier": b"o"}}})
reg(b"S3Async", b"square:completion:", {"arguments": {3: {"callable": {"retval": {"type": b"v"}, "arguments": {
    0: {"type": b"^v"}, 1: {"type": b"q"}, 2: {"type": b"@"}}}}}})
reg(b"S3Notebook", b"greetingWithCompletionHandler:", {"arguments": {2: {"callable": {"retval": {"type": b"v"},
    "arguments": {0: {"type": b"^v"}, 1: {"type": b"@"}}}}}})
reg(b"S3Notebook", b"failingGreetingWithCompletionHandler:", {"arguments": {2: {"callable": {
    "retval": {"type": b"v"}, "arguments": {0: {"type": b"^v"}, 1: {"type": b"@"}, 2: {"type": b"@"}}}}}})
reg(b"NSObject", b"appDecide:", {"arguments": {2: {"callable": {"retval": {"type": b"v"}, "arguments": {
    0: {"type": b"^v"}, 1: {"type": b"Z"}}}}}})

S3Types = objc.lookUpClass("S3Types")
S3Caller = objc.lookUpClass("S3Caller")
S3AppCaller = objc.lookUpClass("S3AppCaller")


def types():
    return S3Types.alloc().init()


def spin(done, timeout=5.0):
    end = time.monotonic() + timeout
    while not done() and time.monotonic() < end:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.01))
    return done()


# F1. Calling Objective-C and C

@case
def f1_1_class_method():
    return str(Foundation.NSURL.URLWithString_("https://kivy.org/a/b").absoluteString())


@case
def f1_1_multipart():
    return str(NSString.stringWithString_("a-b").stringByReplacingOccurrencesOfString_withString_("-", "+"))


@case
def f1_1_multipart_held():
    s, old, new = NSString.stringWithString_("a-b"), NSString.stringWithString_("-"), NSString.stringWithString_("+")
    return str(s.stringByReplacingOccurrencesOfString_withString_(old, new))


@case
def f1_2_property_attr():
    c = Foundation.NSURLComponents.alloc().init()
    c._.host = "kivy.org"
    return str(S3Caller.valueOf_forKey_(c, "host"))


@case
def f1_2_property_methods():
    c = Foundation.NSURLComponents.alloc().init()
    c.setHost_("kivy.org")
    return str(S3Caller.valueOf_forKey_(c, "host"))


@case
def f1_3_format():
    return str(NSString.stringWithFormat_("%ld-%@", 7, "x"))


@case
def f1_3_array_with_objects():
    return NSArray.arrayWithObjects_("a", "b", None).count()


@case
def f1_4_object_constant():
    return Check(str(Foundation.NSLocaleCountryCode), str(objc.lookUpClass("S3Info").localeCountryCodeKey()))


@case
def f1_4_scalar_constant():
    return Check(Foundation.NSFoundationVersionNumber, objc.lookUpClass("S3Info").foundationVersionNumber())


@case
def f1_5_function():
    return str(Foundation.NSStringFromClass(NSArray))


@case
def f1_5_function_struct():
    r = Foundation.NSRangeFromString("{3, 4}")
    return (r.location, r.length)


@case
def f1_6_framework():
    name, cls = next((n, c) for n, c in FRAMEWORKS if not _class_exists(c))
    objc.loadBundle(name, {}, bundle_path=f"/System/Library/Frameworks/{name}.framework")
    return Check((name, _class_exists(cls)), (name, True))


def _class_exists(name):
    try:
        objc.lookUpClass(name)
        return True
    except objc.nosuchclass_error:
        return False


@case
def f1_6_dylib():
    ctypes.CDLL(os.environ["S3_EXTRA"])
    return objc.lookUpClass("S3Extra").answer()


@case
def f1_7_dir():
    return "host" in dir(Foundation.NSURLComponents.alloc().init())


# F2. Types

@case
def f2_1_user_struct():
    r = types().echoPair_((1, 2.5, b"c"))
    c = r[2]
    return (r[0], r[1], ord(c) if isinstance(c, bytes) else c)


@case
def f2_1_struct_pointer_in():
    return types().sumRect_(NSMakeRect(1, 2, 3, 4))


@case
def f2_1_struct_pointer_out():
    r = types().fillRect_(None)
    return (r.origin.x, r.origin.y, r.size.width, r.size.height)


@case
def f2_2_union_arg():
    return types().unionInt_(7)


@case
def f2_2_union_return():
    return types().makeUnion_(7)


@case
def f2_2_bitfield_arg():
    return types().bitsSum_((5, 17, 200))


@case
def f2_2_bitfield_return():
    return tuple(types().makeBits())


@case
def f2_3_fixed_array():
    return types().sumFour_((1, 2, 3, 4))


@case
def f2_3_pass_array():
    return types().sum_count_((1, 2, 3, 4), 4)


@case
def f2_3_fill_array():
    return list(types().fillSquares_count_(None, 4))


@case
def f2_3_struct_array_field():
    return list(types().echoQuad_(((1, 2, 3, 4),))[0])


@case
def f2_4_scalar_out():
    return tuple(types().divide_by_quotient_(7, 2, None))


@case
def f2_4_opaque_pointer():
    t = types()
    return t.alphaOf_(t.makeColor())


@case
def f2_4_error_out():
    value, err = types().failWithError_(None)
    return (str(err.domain()), err.code())


@case
def f2_5_list_arg():
    return types().countOf_(["x", "y", "z"])


@case
def f2_5_dict_arg():
    return str(types().valueIn_forKey_({"k": "v"}, "k"))


@case
def f2_5_to_py():
    return pythonCollectionFromPropertyList(types().strings())


@case
def f2_5_from_py():
    return types().countOf_(NSArray.arrayWithArray_(["a", 1]))


@case
def f2_5_bool_number():
    return pythonCollectionFromPropertyList(types().booleans())


@case
def f2_6_len():
    return len(types().strings())


@case
def f2_6_index():
    return str(types().strings()[1])


@case
def f2_6_iter():
    return [str(s) for s in types().strings()]


@case
def f2_6_in():
    return "one" in types().mapping()


@case
def f2_6_dict_index():
    return types().mapping()["two"]


@case
def f2_6_str_ops():
    s = NSString.stringWithString_("hello")
    return (s == "hello", str(s.upper()))


@case
def f2_7_enum():
    return NSString.stringWithString_("a").compare_("b") == Foundation.NSOrderedAscending


# F3. Defining Objective-C behavior in Python

@case
def f3_1_instance_method():
    class S3PyValue(NSObject):
        @objc.typedSelector(b"q@:")
        def s3Value(self):
            return 11
    return S3Caller.callInstance_(S3PyValue.alloc().init())


@case
def f3_1_class_method():
    def s3ClassValue(cls):
        return 12

    class S3PyClassValue(NSObject):
        locals()["s3ClassValue"] = objc.selector(s3ClassValue, selector=b"s3ClassValue", signature=b"q@:",
                                                 isClassMethod=True)
    return S3Caller.callClass_(S3PyClassValue)


def utc_formatter(cls):
    f = cls.alloc().init()
    f.setDateFormat_("yyyy-MM-dd")
    f.setTimeZone_(NSTimeZone.timeZoneForSecondsFromGMT_(0))
    return f


@case
def f3_2_override_super():
    class S3PyFormatter(NSDateFormatter):
        def stringFromDate_(self, date):
            return objc.super(S3PyFormatter, self).stringFromDate_(date) + "!"

    plain = str(utc_formatter(NSDateFormatter).stringFromDate_(NSDate.dateWithTimeIntervalSince1970_(0)))
    return Check(str(S3Caller.format_(utc_formatter(S3PyFormatter))), plain + "!")


@case
def f3_3_property_kvc():
    class S3PyProperty(NSObject):
        count = objc.object_property()
    o = S3PyProperty.alloc().init()
    o.count = 5
    return S3Caller.valueOf_forKey_(o, "count")


@case
def f3_3_python_state():
    class S3PyState(NSObject):
        @objc.typedSelector(b"q@:")
        def s3Value(self):
            return self.state
    o = S3PyState.alloc().init()
    o.state = 21
    return S3Caller.callInstance_(o)


@case
def f3_4_apple_protocol():
    names = []

    class S3PyParserDelegate(NSObject, protocols=[objc.protocolNamed("NSXMLParserDelegate")]):
        def parser_didStartElement_namespaceURI_qualifiedName_attributes_(self, parser, name, uri, qname, attrs):
            names.append(str(name))

    data = NSString.stringWithString_("<root><item/></root>").dataUsingEncoding_(4)
    parser = Foundation.NSXMLParser.alloc().initWithData_(data)
    delegate = S3PyParserDelegate.alloc().init()
    parser.setDelegate_(delegate)
    parser.parse()
    return names


def app_delegate(**methods):
    import types as _t
    ns = dict(methods)
    cls = _t.new_class("S3PyApp", (NSObject,), {"protocols": [objc.protocolNamed("S3AppProtocol")]},
                       lambda d: d.update(ns))
    return cls.alloc().init()


@case
def f3_5_app_protocol():
    def appValue_(self, v):
        return v * 2
    return S3AppCaller.value_of_(app_delegate(appValue_=appValue_), 4)


@case
def f3_5_app_protocol_registered():
    raise NotApplicable("PyObjC takes method types from the runtime protocol")


@case
def f3_6_notification():
    got = []

    class S3PyObserver(NSObject):
        def note_(self, n):
            got.append(str(n.name()))

    center = Foundation.NSNotificationCenter.defaultCenter()
    o = S3PyObserver.alloc().init()
    center.addObserver_selector_name_object_(o, b"note:", "S3Note", None)
    center.postNotificationName_object_("S3Note", None)
    center.removeObserver_(o)
    return got[0] if got else None


@case
def f3_6_timer():
    fired = []

    class S3PyTimerTarget(NSObject):
        def fire_(self, t):
            fired.append(True)

    o = S3PyTimerTarget.alloc().init()
    Foundation.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.01, o, b"fire:", None,
                                                                                        False)
    return bool(spin(lambda: fired))


@case
def f3_7_union_arg():
    def appUnion_(self, u):
        return u[0] if isinstance(u, tuple) else u
    return S3AppCaller.unionOf_value_(app_delegate(appUnion_=appUnion_), 9)


@case
def f3_7_array_arg():
    def appArray_count_(self, v, n):
        return sum(v[i] for i in range(n))
    return S3AppCaller.arraySumOf_(app_delegate(appArray_count_=appArray_count_))


@case
def f3_7_bool_return():
    def appShouldContinue_(self, c):
        return True
    return S3AppCaller.shouldContinue_count_(app_delegate(appShouldContinue_=appShouldContinue_), 1)


@case
def f3_7_object_return():
    def appLabel_(self, c):
        return f"label-{c}"
    return str(S3AppCaller.labelOf_count_(app_delegate(appLabel_=appLabel_), 3))


# F4. Blocks and function pointers

@case
def f4_1_sort_comparator():
    r = NSArray.arrayWithArray_(["c", "a", "b"]).sortedArrayUsingComparator_(lambda a, b: (a > b) - (a < b))
    return [str(s) for s in r]


@case
def f4_1_enumerate_stop():
    seen = []

    def visit(obj, idx, stop):
        seen.append(idx)
        return len(seen) == 2
    NSArray.arrayWithArray_(["a", "b", "c", "d"]).enumerateObjectsUsingBlock_(visit)
    return len(seen)


@case
def f4_1_completion():
    got = []

    def done(result, error):
        got.append(result)
    objc.lookUpClass("S3Async").alloc().init().square_completion_(7, done)
    spin(lambda: got)
    return got[0] if got else None


@case
def f4_2_delegate_completion():
    def appDecide_(self, decision):
        decision(True)
    return S3AppCaller.decisionOf_(app_delegate(appDecide_=appDecide_))


@case
def f4_3_dispatch_main():
    try:
        import dispatch
    except ImportError:
        raise NotApplicable("pyobjc-framework-libdispatch isn't installed in the control environment")
    ran = []
    dispatch.dispatch_async(dispatch.dispatch_get_main_queue(),
                            lambda: ran.append(threading.current_thread() is threading.main_thread()))
    spin(lambda: ran)
    return ran[0] if ran else None


@case
def f4_4_sort_function():
    def compare(a, b, context):
        return (a > b) - (a < b)
    r = NSArray.arrayWithArray_(["c", "a", "b"]).sortedArrayUsingFunction_context_(compare, None)
    return [str(s) for s in r]


# F5. Runtime services

@case
def f5_3_asyncio_cf():
    raise NotApplicable("the control isn't tested for event loop integration")


@case
def f5_4_perform_on_main():
    ran = []

    class S3PyMainTarget(NSObject):
        def onMain_(self, arg):
            ran.append(threading.current_thread() is threading.main_thread())

    o = S3PyMainTarget.alloc().init()
    t = threading.Thread(target=lambda: o.performSelectorOnMainThread_withObject_waitUntilDone_(b"onMain:", None,
                                                                                                False))
    t.start()
    t.join()
    spin(lambda: ran)
    return ran[0] if ran else None


# F7. Swift

def notebook():
    return objc.lookUpClass("S3Notebook").alloc().initWithTitle_("Groceries")


@case
def f7_1_named_class():
    return notebook().addNote_("apples")


@case
def f7_1_generated_name():
    return objc.lookUpClass("_TtC7S3Swift7Unnamed").alloc().init().ping()


@case
def f7_2_string():
    return str(notebook().title())


@case
def f7_2_property_write():
    n = notebook()
    n.setAuthor_("Kivy")
    return str(S3Caller.valueOf_forKey_(n, "author"))


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
    n.addNote_("x")
    return pythonCollectionFromPropertyList(n.notes())


@case
def f7_2_int_array():
    return pythonCollectionFromPropertyList(notebook().squares())


@case
def f7_2_nested_dict():
    return pythonCollectionFromPropertyList(notebook().summary())


@case
def f7_2_list_arg():
    return notebook().countOf_(["a", "b", "c"])


@case
def f7_2_dict_arg():
    return str(notebook().valueIn_forKey_({"author": "Swift"}, "author"))


@case
def f7_3_success():
    n = notebook()
    n.addNote_("x")
    value, err = n.noteAtIndex_error_(0, None)
    return str(value)


@case
def f7_3_failure_value():
    value, err = notebook().noteAtIndex_error_(5, None)
    return value


@case
def f7_3_read_error():
    value, err = notebook().noteAtIndex_error_(5, None)
    return str(err.domain())


@case
def f7_4_completion():
    got = []
    notebook().greetingWithCompletionHandler_(lambda s: got.append(str(s)))
    spin(lambda: got)
    return got[0] if got else None


@case
def f7_4_throwing_completion():
    got = []
    notebook().failingGreetingWithCompletionHandler_(lambda r, e: got.append((r is None, e is not None)))
    spin(lambda: got)
    return got[0] if got else None


def metronome(raise_first=False):
    record = {"ticks": [], "main": [], "raised": False}

    class S3PyMetronomeDelegate(NSObject, protocols=[objc.protocolNamed("S3MetronomeDelegate")]):
        def metronome_didTick_(self, m, count):
            record["ticks"].append(count)
            record["main"].append(threading.current_thread() is threading.main_thread())
            if raise_first and not record["raised"]:
                record["raised"] = True
                raise RuntimeError("raised in a delegate method")

        def metronome_shouldContinueAfter_(self, m, count):
            return count < 3

        def metronome_scaleFor_(self, m, count):
            return count * 10

        def metronome_labelFor_(self, m, count):
            return f"t{count}"

    delegate = S3PyMetronomeDelegate.alloc().init()
    m = objc.lookUpClass("S3Metronome").alloc().init()
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
    return pythonCollectionFromPropertyList(m.continueAnswers())


@case
def f7_5_int_return():
    m, d, record = metronome()
    m.runTicks_(3)
    return pythonCollectionFromPropertyList(m.scales())


@case
def f7_5_object_return():
    m, d, record = metronome()
    m.runTicks_(3)
    return pythonCollectionFromPropertyList(m.labels())


@case
def f7_5_background():
    m, d, record = metronome()
    m.startTicksOnBackgroundThread_(3)
    end = time.monotonic() + 5
    while not m.finished() and time.monotonic() < end:
        time.sleep(0.01)
    return (record["ticks"], any(record["main"]))


@case
def f7_5_exception():
    m, d, record = metronome(raise_first=True)
    try:
        m.runTicks_(3)
    except RuntimeError:
        pass
    first = m.ticks()
    m.runTicks_(3)
    return (first, m.ticks())
