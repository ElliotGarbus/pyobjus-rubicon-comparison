"""T5, calling step: call each sampled entry that's safe to call and check its result.

An entry is called only if that needs no hardware, permission, network or UI state,
and changes nothing outside this process and its own temporary folder. The reason
for leaving out each other entry is in EXCLUDED. Expected values come from
t5_truth.m, which makes the same calls in Objective-C.

Usage: t5_calls.py LIB INDEX. Prints one JSON line."""
import array
import ctypes
import json
import os
import shutil
import struct
import sys
import tempfile
import threading
from ctypes import CFUNCTYPE, byref, c_bool, c_double, c_float, c_long, c_ulong, c_void_p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapters import NotExpressible, load

NO_REQUEST = "needs a request or data only a real app or service has"
GEOCODER = "needs network access to Apple's geocoder"
LOCATION = "needs location permission"
NOTIFY = "needs notification permission, and changes the app's notification state"
WINDOW = "needs a window, a sheet or a running app"
TEXTKIT = "needs a laid-out TextKit 2 view"
INFORMAL = "informal protocol entry: nothing implements it on NSObject"
ABSTRACT = "abstract method: does nothing useful without an app-defined subclass"
EXCLUDED = {
    8: "runs a user script from a protected folder", 11: "needs an upload in progress over the network",
    12: "needs on-demand resources from an app bundle", 14: INFORMAL,
    18: "uses the network", 28: INFORMAL,
    58: WINDOW, 59: TEXTKIT, 60: WINDOW, 61: WINDOW, 62: TEXTKIT, 63: INFORMAL, 66: WINDOW, 67: INFORMAL,
    68: "needs a storyboard file", 69: INFORMAL, 70: INFORMAL, 71: WINDOW, 72: INFORMAL,
    73: "needs a drag in progress", 75: "moves a file to the user's Trash", 76: INFORMAL,
    77: "can show a paste permission prompt", 80: "needs a nib file", 84: "needs a live window resize",
    86: INFORMAL, 88: "launches another app", 89: ABSTRACT, 90: "needs a Core Data model",
    91: "the answer depends on the document types the host app declares, not on the bridge", 96: ABSTRACT,
    97: "needs a Core Data model", 100: LOCATION, 101: GEOCODER, 102: GEOCODER, 103: GEOCODER, 104: GEOCODER,
    105: LOCATION, 106: LOCATION, 107: LOCATION, 109: INFORMAL, 110: GEOCODER, 111: GEOCODER, 112: GEOCODER,
    113: LOCATION, 114: GEOCODER, 115: LOCATION, 116: LOCATION, 117: LOCATION, 118: LOCATION, 119: GEOCODER,
    121: NOTIFY, 125: INFORMAL, 126: NO_REQUEST, 127: "shows a permission prompt",
    128: INFORMAL, 129: NOTIFY, 130: NO_REQUEST,
}
ENTRIES = {}
L = None
TMP = tempfile.mkdtemp(prefix="s2t5")
TEXT_FILE = os.path.join(TMP, "t.txt")
open(TEXT_FILE, "w").write("hello")
MISSING = os.path.join(TMP, "missing")
KEEP = []


def entry(index):
    def wrap(f):
        ENTRIES[index] = f
        return f
    return wrap


class Out:
    """An out or in-out argument, of kind id, ulong, float, double, range, points3 or ulong3.
    required: the method needs somewhere to write, so nil can't be passed instead."""
    C = {"ulong": c_ulong, "float": c_float, "double": c_double}

    def __init__(self, kind, init=None, required=False):
        self.kind, self.init, self.required = kind, init, required


class In(Out):
    """A pointer to values the method only reads."""


class Fn:
    """A C function or block: restype and argument kinds, with objects converted."""

    def __init__(self, func, restype, *argtypes):
        self.func, self.restype, self.argtypes = func, restype, argtypes


# --- One small interface per library, for what adapters.py doesn't cover ---------

class Pyobjus:
    unreadable = False

    def __init__(self):
        import pyobjus
        self.pyobjus = pyobjus

    def arg(self, a):
        """Returns what to pass and how to read it after the call."""
        if isinstance(a, Fn):
            raise NotExpressible("pyobjus has no public API for creating a block or passing a function pointer")
        if not isinstance(a, Out):
            return a, None
        if a.kind == "id":
            # pyobjus treats anything but nil for id* as a delegate to create, so the call
            # is made with nil, and what would be written there can't be read.
            if a.required:
                raise NotExpressible("pyobjus can pass only nil for an object out parameter")
            self.unreadable = True
            return None, lambda: None
        if a.kind == "range":
            v = self.pyobjus.NSRange(*(a.init or (0, 0)))
            return v, lambda: (v.location, v.length)
        if a.kind in ("points3", "ulong3"):
            raise NotExpressible("pyobjus has no public way to pass a C array as an out parameter")
        v = Out.C[a.kind](a.init or 0)
        return v, lambda: v.value

    def struct(self, fmt, *values):
        ctype = {"q": ctypes.c_longlong, "d": c_double}[fmt[0]]
        fields = [(f"f{i}", ctype) for i in range(len(values))]
        return type("S", (ctypes.Structure,), {"_fields_": fields})(*values)

    def values(self, s, fmt):
        return struct.unpack(fmt, bytes(s))

    def decimal(self, d):
        return decimal_from_bytes(bytes(d))

    def is_nil(self, x):
        return x is None

    def selector(self, name):
        return self.pyobjus.selector(name)


class Rubicon:
    unreadable = False

    def __init__(self):
        from rubicon import objc
        from rubicon.objc import runtime
        self.objc, self.runtime = objc, runtime

    def wrap(self, value):
        return self.objc.ObjCInstance(value) if value else None

    def ctype(self, kind):
        return {"id": self.objc.objc_id, "void": None, "long": c_long, "ulong": c_ulong, "double": c_double,
                "bool": c_bool, "boolptr": c_void_p, "ptr": c_void_p, "range": self.objc.NSRange}[kind]

    def callback(self, fn):
        def wrapped(*args):
            args = [self.wrap(a) if k == "id" else a for a, k in zip(args, fn.argtypes)]
            r = fn.func(*args)
            if fn.restype == "id":
                KEEP.append(r)
                return r.ptr.value if r is not None else None
            return r
        rest = c_void_p if fn.restype == "id" else self.ctype(fn.restype)
        return rest, [self.ctype(k) for k in fn.argtypes], wrapped

    def arg(self, a):
        if isinstance(a, Fn):
            if getattr(a, "c_function", False):
                rest, args, wrapped = self.callback(a)
                f = CFUNCTYPE(rest, *args)(wrapped)
                KEEP.append(f)
                return f, None
            rest, args, wrapped = self.callback(a)
            b = self.objc.Block(wrapped, rest, *args)
            KEEP.append(b)
            return b, None
        if not isinstance(a, Out):
            return a, None
        if a.kind == "id":
            v = self.objc.objc_id(a.init.ptr.value if a.init is not None else 0)
            return byref(v), lambda: self.wrap(v)
        if a.kind == "range":
            v = self.objc.NSRange(*(a.init or (0, 0)))
            return byref(v), lambda: (v.location, v.length)
        if a.kind == "points3":
            v = (self.objc.CGPoint * 3)()
            return v, lambda: [(p.x, p.y) for p in v]
        if a.kind == "ulong3":
            v = (c_ulong * 3)(*(a.init or (0, 0, 0)))
            return v, lambda: list(v)
        v = Out.C[a.kind](a.init or 0)
        return byref(v), lambda: v.value

    def struct(self, fmt, *values):
        return values

    def values(self, s, fmt):
        return struct.unpack(fmt, bytes(s))

    def decimal(self, d):
        return decimal_from_bytes(bytes(d))

    def is_nil(self, x):
        return x is None

    def selector(self, name):
        return self.objc.SEL(name)


class Pyobjc:
    returns_outs = True
    unreadable = False

    def __init__(self):
        import objc
        import AppKit  # noqa: F401
        import CoreLocation  # noqa: F401
        import Foundation  # noqa: F401
        import UserNotifications  # noqa: F401
        self.objc = objc

    def arg(self, a):
        if isinstance(a, Fn):
            if a.restype != "void" and "boolptr" in a.argtypes:
                # PyObjC leaves a block's out argument out of the call and takes it
                # back with the block's result.
                return (lambda *args: (a.func(*args, None), False)), None
            return a.func, None
        if isinstance(a, In):
            return a.init, None
        if not isinstance(a, Out):
            return a, None
        if a.kind == "ulong3":
            return array.array("L", a.init), "out"
        return a.init, "out"

    def struct(self, fmt, *values):
        return values

    def values(self, s, fmt):
        def flat(x):
            for i in x:
                if isinstance(i, tuple):
                    yield from flat(i)
                else:
                    yield i
        return tuple(flat(s))

    def decimal(self, d):
        return str(d)

    def is_nil(self, x):
        return x is None

    def selector(self, name):
        return name


def decimal_from_bytes(b):
    """A 1.5 NSDecimal has exponent -1 and mantissa 15. Each library's struct is read as raw bytes."""
    exponent = struct.unpack("b", b[:1])[0]
    return "1.5" if (exponent, struct.unpack("H", b[4:6])[0]) == (-1, 15) else repr(b)


def call(target, sel, *args):
    """Returns (return value, [out values]) in every library."""
    method = getattr(target, sel.replace(":", "_"))
    passed, reads = [], []
    for a in args:
        value, read = X.arg(a)
        passed.append(value)
        reads.append(read)
    ret = method(*passed)
    if getattr(X, "returns_outs", False):
        count = sum(r == "out" for r in reads)
        if not count:
            return ret, []
        # A void method returns its one out value, or a tuple of several. Any other
        # method returns a tuple that starts with its return value.
        if method.__metadata__()["retval"]["type"] == b"v":
            return None, [ret] if count == 1 else list(ret)
        return ret[0], list(ret[1:])
    return ret, [r() for r in reads if r]


def attr(obj, name):
    v = getattr(obj, name)
    return v() if callable(v) and not isinstance(v, type) else v


def c(name):
    return L.cls(name)


def s(value):
    if isinstance(X, Pyobjc):
        return c("NSString").stringWithString_(value).nsstring()
    return L.nsstr(value)


def text(x):
    v = L.to_py(x)
    if isinstance(v, bytes):
        return v.decode()
    return v if isinstance(v, (str, type(None))) else str(v)


def ns_list(items):
    return c("NSArray").arrayWithArray_(items) if isinstance(X, Pyobjc) else L.to_ns(list(items))


def ns_dict(items):
    return c("NSDictionary").dictionaryWithDictionary_(items) if isinstance(X, Pyobjc) else L.to_ns(items)


def count(x):
    # Rubicon's array wrapper has Python's list.count, and pyobjus's wrapper has no len().
    return x.count() if isinstance(X, Pyobjus) else len(x)


def strings(x):
    return [text(x.objectAtIndex_(i)) for i in range(count(x))]


def nil_error(target, sel, *args):
    """Call a method whose last argument is an NSError** this entry doesn't test."""
    r = getattr(target, sel)(*args, None)
    return r[0] if isinstance(X, Pyobjc) else r


def file_url(path):
    return c("NSURL").fileURLWithPath_(s(path))


def run_loop(seconds=0.2):
    attr(c("NSRunLoop"), "currentRunLoop").runUntilDate_(c("NSDate").dateWithTimeIntervalSinceNow_(seconds))


def wait(event, seconds=5):
    deadline = 0
    while not event.is_set() and deadline < seconds:
        run_loop(0.05)
        deadline += 0.05
    return event.is_set()


def check(condition, detail):
    return ("correct" if condition else "wrong value"), str(detail)[:200]


def error_code(err):
    return attr(err, "code")


def expect_error(ret, err, code):
    nil = ret is None or ret is False or ret == 0
    if X.unreadable:
        return check(nil, f"returned {ret}")
    return check(nil and error_code(err) == code, f"returned {ret}, error code {error_code(err)}")


def decimal15():
    return c("NSDecimalNumber").decimalNumberWithString_(s("1.5"))


# --- Structs by value ------------------------------------------------------------

@entry(0)
def _0():
    v = X.decimal(attr(decimal15(), "decimalValue"))
    return check(v == "1.5", v)


@entry(1)
def _1():
    n = c("NSDecimalNumber").decimalNumberWithDecimal_(attr(decimal15(), "decimalValue"))
    return check(text(attr(n, "stringValue")) == "1.5", text(attr(n, "stringValue")))


@entry(2)
def _2():
    p = attr(c("NSProcessInfo"), "processInfo")
    a = p.isOperatingSystemAtLeastVersion_(X.struct("qqq", 10, 0, 0))
    b = p.isOperatingSystemAtLeastVersion_(X.struct("qqq", 9999, 0, 0))
    return check(bool(a) and not bool(b), (a, b))


@entry(3)
def _3():
    import platform
    v = X.values(attr(attr(c("NSProcessInfo"), "processInfo"), "operatingSystemVersion"), "qqq")
    return check(v[0] == int(platform.mac_ver()[0].split(".")[0]), v)


@entry(4)
def _4():
    t = c("NSAffineTransform").transform()
    t.setTransformStruct_(X.struct("dddddd", 1, 2, 3, 4, 5, 6))
    v = X.values(attr(t, "transformStruct"), "dddddd")
    return check(tuple(v) == (1, 2, 3, 4, 5, 6), v)


@entry(5)
def _5():
    n = c("NSDecimalNumber").alloc().initWithDecimal_(attr(decimal15(), "decimalValue"))
    return check(text(attr(n, "stringValue")) == "1.5", text(attr(n, "stringValue")))


@entry(6)
def _6():
    v = X.values(attr(c("NSAffineTransform").transform(), "transformStruct"), "dddddd")
    return check(tuple(v) == (1, 0, 0, 1, 0, 0), v)


@entry(7)
def _7():
    v = X.decimal(attr(c("NSNumber").numberWithDouble_(1.5), "decimalValue"))
    return check(v == "1.5", v)


# --- Blocks ----------------------------------------------------------------------

@entry(9)
def _9():
    fired = []
    t, _ = call(c("NSTimer"), "timerWithTimeInterval:repeats:block:", 0.001, False,
                Fn(lambda timer: fired.append(1), "void", "id"))
    attr(c("NSRunLoop"), "currentRunLoop").addTimer_forMode_(t, s("kCFRunLoopDefaultMode"))
    run_loop()
    return check(fired == [1], fired)


@entry(10)
def _10():
    done, got = threading.Event(), []

    def handler(a, b, d):
        got.extend(count(x) for x in (a, b, d))
        done.set()
    call(attr(c("NSURLSession"), "sharedSession"), "getTasksWithCompletionHandler:",
         Fn(handler, "void", "id", "id", "id"))
    return check(wait(done) and got == [0, 0, 0], got)


@entry(13)
def _13():
    done, got = threading.Event(), []

    def handler(expired):
        got.append(bool(expired))
        done.set()
    call(attr(c("NSProcessInfo"), "processInfo"), "performExpiringActivityWithReason:usingBlock:", s("s2"),
         Fn(handler, "void", "bool"))
    return check(wait(done) and got == [False], got)


@entry(15)
def _15():
    r, _ = call(ns_list(["a", "b", "c"]), "indexOfObjectWithOptions:passingTest:", 0,
                Fn(lambda o, i, stop: text(o) == "b", "bool", "id", "ulong", "boolptr"))
    return check(r == 1, r)


def reverse(a, b):
    x, y = text(a), text(b)
    return -1 if x > y else (1 if x < y else 0)


@entry(16)
def _16():
    o = c("NSOrderedSet").orderedSetWithArray_(ns_list(["a", "b", "c"]))
    r, _ = call(o, "sortedArrayWithOptions:usingComparator:", 0, Fn(reverse, "long", "id", "id"))
    return check(strings(r) == ["c", "b", "a"], strings(r))


@entry(17)
def _17():
    done, got = threading.Event(), []

    def handler(services, err):
        got.append(services is not None or err is not None)
        done.set()
    call(attr(c("NSFileManager"), "defaultManager"), "getFileProviderServicesForItemAtURL:completionHandler:",
         file_url(TEXT_FILE), Fn(handler, "void", "id", "id"))
    return check(wait(done) and got == [True], "completion handler ran")


@entry(19)
def _19():
    fired = []
    call(attr(c("NSRunLoop"), "currentRunLoop"), "performBlock:", Fn(lambda: fired.append(1), "void"))
    run_loop()
    return check(fired == [1], fired)


@entry(20)
def _20():
    done, got = threading.Event(), []

    def handler(data, err):
        got.append(None if data is None else text(c("NSString").alloc().initWithData_encoding_(data, 4)))
        done.set()
    call(c("NSItemProvider").alloc().initWithObject_(s("hello")),
         "loadDataRepresentationForTypeIdentifier:completionHandler:", s("public.utf8-plain-text"),
         Fn(handler, "void", "id", "id"))
    return check(wait(done) and got == ["hello"], got)


@entry(21)
def _21():
    answer = s("from provider")
    call(c("NSError"), "setUserInfoValueProviderForDomain:provider:", s("S2T5"),
         Fn(lambda err, key: answer if text(key) == "NSLocalizedDescription" else None, "id", "id", "id"))
    err = c("NSError").errorWithDomain_code_userInfo_(s("S2T5"), 1, None)
    v = text(attr(err, "localizedDescription"))
    return check(v == "from provider", v)


@entry(22)
def _22():
    tagger = c("NSLinguisticTagger").alloc().initWithTagSchemes_options_(ns_list(["TokenType"]), 0)
    tagger.setString_(s("a b"))
    got = []
    call(tagger, "enumerateTagsInRange:unit:scheme:options:usingBlock:", L.range(0, 3), 0, s("TokenType"), 0,
         Fn(lambda tag, rng, stop: got.append((text(tag), rng.location, rng.length)),
            "void", "id", "range", "boolptr"))
    return check(got == [("Word", 0, 1), ("Whitespace", 1, 1), ("Word", 2, 1)], got)


@entry(23)
def _23():
    got = []
    call(c("NSMetadataQuery").alloc().init(), "enumerateResultsUsingBlock:",
         Fn(lambda o, i, stop: got.append(i), "void", "id", "ulong", "boolptr"))
    return check(got == [], "query not started, block not called")


@entry(24)
def _24():
    got = []
    call(c("NSIndexSet").indexSetWithIndexesInRange_(L.range(2, 3)), "enumerateRangesWithOptions:usingBlock:", 0,
         Fn(lambda rng, stop: got.append((rng.location, rng.length)), "void", "range", "boolptr"))
    return check(got == [(2, 3)], got)


@entry(25)
def _25():
    d = ns_dict({"a": "2", "b": "1"})
    r, _ = call(d, "keysSortedByValueWithOptions:usingComparator:", 0,
                Fn(lambda x, y: -reverse(x, y), "long", "id", "id"))
    return check(strings(r) == ["b", "a"], strings(r))


@entry(26)
def _26():
    center = attr(c("NSNotificationCenter"), "defaultCenter")
    got = []
    o, _ = call(center, "addObserverForName:object:queue:usingBlock:", s("S2T5"), None, None,
                Fn(lambda n: got.append(text(attr(n, "name"))), "void", "id"))
    center.postNotificationName_object_(s("S2T5"), None)
    center.removeObserver_(o)
    return check(got == ["S2T5"], got)


@entry(27)
def _27():
    got = []
    call(s("x\ny"), "enumerateLinesUsingBlock:", Fn(lambda line, stop: got.append(text(line)), "void", "id", "boolptr"))
    return check(got == ["x", "y"], got)


@entry(64)
def _64():
    fired = []
    call(c("NSTextContentStorage").alloc().init(), "performEditingTransactionUsingBlock:",
         Fn(lambda: fired.append(1), "void"))
    return check(fired == [1], fired)


@entry(65)
def _65():
    r, _ = call(c("NSTableViewDiffableDataSource").alloc(), "initWithTableView:cellProvider:",
                c("NSTableView").alloc().init(), Fn(lambda t, col, row, item: None, "id", "id", "id", "long", "id"))
    return check(r is not None, "created; the block isn't called until the table lays out")


@entry(74)
def _74():
    got = []
    call(c("NSTableView").alloc().init(), "enumerateAvailableRowViewsUsingBlock:",
         Fn(lambda view, row: got.append(row), "void", "id", "long"))
    return check(got == [], "empty table, block not called")


@entry(108)
def _108():
    queue = attr(attr(c("NSOperationQueue"), "mainQueue"), "underlyingQueue")
    r, _ = call(c("CLMonitorConfiguration"), "configWithMonitorName:queue:eventHandler:", s("s2"), queue,
                Fn(lambda m, e: None, "void", "id", "id"))
    return check(text(attr(r, "name")) == "s2", "created; the block isn't called until a monitor runs")


def notification_getter(sel):
    done, got = threading.Event(), []

    def handler(value):
        got.append(value is not None)
        done.set()
    center = attr(c("UNUserNotificationCenter"), "currentNotificationCenter")
    call(center, sel, Fn(handler, "void", "id"))
    return check(wait(done) and got == [True], "completion handler ran with a value")


@entry(120)
def _120():
    return notification_getter("getNotificationSettingsWithCompletionHandler:")


@entry(122)
def _122():
    return notification_getter("getDeliveredNotificationsWithCompletionHandler:")


@entry(123)
def _123():
    return notification_getter("getPendingNotificationRequestsWithCompletionHandler:")


@entry(124)
def _124():
    return notification_getter("getNotificationCategoriesWithCompletionHandler:")


# --- Out parameters --------------------------------------------------------------

@entry(29)
def _29():
    r, (value, err) = call(file_url("/System"), "getResourceValue:forKey:error:", Out("id", required=True),
                           s("NSURLIsDirectoryKey"), Out("id"))
    return check(bool(r) and bool(L.to_py(value)), (r, L.to_py(value)))


@entry(30)
def _30():
    r, (value, err) = call(c("NSPersonNameComponentsFormatter").alloc().init(),
                           "getObjectValue:forString:errorDescription:", Out("id", required=True), s("Ann Lee"), Out("id"))
    given = text(attr(value, "givenName"))
    return check(bool(r) and given == "Ann", (r, given))


@entry(31)
def _31():
    r, (err,) = call(c("NSString"), "stringWithContentsOfURL:encoding:error:", file_url(MISSING), 4, Out("id"))
    return expect_error(r, err, 260)


@entry(32)
def _32():
    # The path never exists, so nothing is removed.
    r, (err,) = call(attr(c("NSFileManager"), "defaultManager"), "removeItemAtPath:error:", s(MISSING), Out("id"))
    return expect_error(r, err, 4)


@entry(33)
def _33():
    r, (desc,) = call(c("NSPropertyListSerialization"), "dataFromPropertyList:format:errorDescription:",
                      c("NSObject").alloc().init(), 100, Out("id", required=True))
    return check(r is None and desc is not None and "Property list invalid" in text(desc), (r, text(desc)))


def keyed_archive():
    archiver = c("NSKeyedArchiver").alloc().initRequiringSecureCoding_(False)
    archiver.encodeBytes_length_forKey_(b"abc", 3, s("k"))
    archiver.finishEncoding()
    return attr(archiver, "encodedData")


@entry(34)
def _34():
    u = nil_error(c("NSKeyedUnarchiver").alloc(), "initForReadingFromData_error_", keyed_archive())
    r, (length,) = call(u, "decodeBytesForKey:returnedLength:", s("k"), Out("ulong"))
    if isinstance(r, bytes):
        return check(r[:3] == b"abc" and length == 3, (r, length))
    return check(length == 3, f"length {length}")


@entry(35)
def _35():
    r, (err,) = call(attr(c("NSFileManager"), "defaultManager"), "attributesOfItemAtPath:error:", s(MISSING), Out("id"))
    return expect_error(r, err, 260)


@entry(36)
def _36():
    r, (err,) = call(c("NSData").alloc(), "initWithContentsOfFile:options:error:", s(MISSING), 0, Out("id"))
    return expect_error(r, err, 260)


@entry(37)
def _37():
    r, (encoding, err) = call(c("NSString").alloc(), "initWithContentsOfFile:usedEncoding:error:", s(TEXT_FILE),
                              Out("ulong"), Out("id"))
    return check(text(r) == "hello" and encoding == 4, (text(r), encoding))


@entry(38)
def _38():
    r, _ = call(c("NSNumberFormatter").alloc().init(), "isPartialStringValid:newEditingString:errorDescription:",
                s("1"), Out("id", s("1"), required=True), Out("id"))
    return check(bool(r), r)


@entry(39)
def _39():
    r, (err,) = call(c("NSString").alloc(), "initWithContentsOfURL:encoding:error:", file_url(TEXT_FILE), 4, Out("id"))
    return check(text(r) == "hello" and err is None, text(r))


@entry(40)
def _40():
    r, _ = call(c("NSDateComponentsFormatter").alloc().init(), "getObjectValue:forString:errorDescription:",
                Out("id", required=True), s("1"), Out("id"))
    return check(not r, r)


@entry(41)
def _41():
    data = c("NSMutableData").data()
    archiver = c("NSArchiver").alloc().initForWritingWithMutableData_(data)
    archiver.encodeBytes_length_(b"abc", 3)
    u = c("NSUnarchiver").alloc().initForReadingWithData_(data)
    r, (length,) = call(u, "decodeBytesWithReturnedLength:", Out("ulong"))
    return check(length == 3, f"length {length}")


@entry(42)
def _42():
    r, (v,) = call(c("NSScanner").scannerWithString_(s("2.5")), "scanFloat:", Out("float"))
    return check(bool(r) and v == 2.5, (r, v))


@entry(43)
def _43():
    f = c("NSDateFormatter").alloc().init()
    f.setDateFormat_(s("yyyy"))
    r, (value, rng, err) = call(f, "getObjectValue:forString:range:error:", Out("id", required=True), s("2026"),
                                Out("range", (0, 4)), Out("id"))
    rng = tuple(rng)
    return check(bool(r) and value is not None and rng == (0, 4), (r, rng))


@entry(44)
def _44():
    # The streams are created and never opened, so nothing connects.
    _, (a, b) = call(c("NSStream"), "getStreamsToHost:port:inputStream:outputStream:",
                     c("NSHost").hostWithName_(s("localhost")), 9, Out("id", required=True), Out("id", required=True))
    return check(a is not None and b is not None, "both streams returned")


@entry(45)
def _45():
    r, (info,) = call(c("NSAppleScript").alloc(), "initWithContentsOfURL:error:", file_url(MISSING), Out("id"))
    return check(r is None and (X.unreadable or info is not None), f"returned {r}")


@entry(46)
def _46():
    doc = nil_error(c("NSXMLDocument").alloc(), "initWithXMLString_options_error_", s("<a/>"), 0)
    r, (err,) = call(doc, "objectByApplyingXSLTString:arguments:error:", s("not xslt"), None, Out("id"))
    return check(r is None and err is None, f"returned {r}, error {err}")


@entry(47)
def _47():
    _, v = call(s("ab\ncd"), "getParagraphStart:end:contentsEnd:forRange:", Out("ulong"), Out("ulong"), Out("ulong"),
                L.range(0, 1))
    return check(list(v) == [0, 3, 2], v)


@entry(78)
def _78():
    data = s("<p>hi</p>").dataUsingEncoding_(4)
    r, (attrs,) = call(c("NSAttributedString").alloc(), "initWithHTML:documentAttributes:", data, Out("id"))
    v = text(attr(r, "string")).strip()
    return check(v == "hi", v)


@entry(79)
def _79():
    path = c("NSBezierPath").bezierPath()
    path.moveToPoint_(point(1, 2))
    r, (points,) = call(path, "elementAtIndex:associatedPoints:", 0, Out("points3"))
    return check(r == 0 and tuple(points[0]) == (1.0, 2.0), (r, points[0]))


def point(x, y):
    return L.rect(x, y, 0, 0).origin if not isinstance(X, Pyobjc) else (x, y)


def size(w, h):
    return L.rect(0, 0, w, h).size if not isinstance(X, Pyobjc) else (w, h)


@entry(81)
def _81():
    r, (err,) = call(attr(c("NSDocumentController"), "sharedDocumentController"), "makeUntitledDocumentOfType:error:",
                     s("s2.none"), Out("id"))
    return check(r is None and (X.unreadable or err is not None), f"returned {r}")


@entry(82)
def _82():
    store = c("NSTextStorage").alloc().initWithString_(s("abc"))
    manager = c("NSLayoutManager").alloc().init()
    box = c("NSTextContainer").alloc().initWithSize_(size(100, 100))
    manager.addTextContainer_(box)
    store.addLayoutManager_(manager)
    manager.glyphRangeForTextContainer_(box)
    r, (count,) = call(manager, "rectArrayForCharacterRange:withinSelectedCharacterRange:inTextContainer:rectCount:",
                       L.range(0, 1), L.range(0x7fffffffffffffff, 0), box, Out("ulong"))
    return check(count == 1, f"rectCount {count}")


@entry(83)
def _83():
    rep = c("NSBitmapImageRep").alloc()
    rep = rep.initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, 1, 1, 8, 3, False, False, s("NSDeviceRGBColorSpace"), 0, 0)
    call(rep, "setPixel:atX:y:", In("ulong3", (10, 20, 30)), 0, 0)
    _, (v,) = call(rep, "getPixel:atX:y:", Out("ulong3", (0, 0, 0)), 0, 0)
    return check(list(v) == [10, 20, 30], v)


@entry(85)
def _85():
    _, (v,) = call(c("NSView").alloc().init(), "adjustPageHeightNew:top:bottom:limit:", Out("double"), 0.0, 100.0, 50.0)
    return check(v == 100.0, v)


@entry(87)
def _87():
    a = c("NSAttributedString").alloc().initWithString_(s("hi"))
    opts = ns_dict({"DocumentType": "NSRTF"})
    r, (err,) = call(a, "dataFromRange:documentAttributes:error:", L.range(0, 2), opts, Out("id"))
    v = text(c("NSString").alloc().initWithData_encoding_(r, 4))
    return check(v.startswith("{\\rtf"), v[:10])


@entry(92)
def _92():
    data = s("{\\rtf1 hi}").dataUsingEncoding_(4)
    r, (attrs,) = call(c("NSAttributedString").alloc(), "initWithRTF:documentAttributes:", data, Out("id"))
    v = text(attr(r, "string"))
    return check(v == "hi" and (X.unreadable or attrs is not None), v)


@entry(93)
def _93():
    _, v = call(c("NSCell").alloc().init(), "getPeriodicDelay:interval:", Out("float"), Out("float"))
    return check([round(x, 3) for x in v] == [0.2, 0.025], v)


@entry(94)
def _94():
    a = c("NSAttributedString").alloc().initWithString_(s("hi"))
    wrapper = a.RTFDFileWrapperFromRange_documentAttributes_(L.range(0, 2), ns_dict({}))
    r, (attrs,) = call(c("NSAttributedString").alloc(), "initWithRTFDFileWrapper:documentAttributes:", wrapper,
                       Out("id"))
    v = text(attr(r, "string"))
    return check(v == "hi", v)


@entry(95)
def _95():
    view = c("NSTextView").alloc().init()
    _, (before, after) = call(view, "smartInsertForString:replacingRange:beforeString:afterString:", s("x"),
                              L.range(0, 0), Out("id", required=True), Out("id", required=True))
    return check(before is None and after is None, (before, after))


# --- Function pointers -----------------------------------------------------------

def function(func, restype, *argtypes):
    f = Fn(func, restype, *argtypes)
    f.c_function = True
    return f


def read_back(setter, getter, restype, *argtypes):
    pf = c("NSPointerFunctions").pointerFunctionsWithOptions_(0)
    call(pf, setter, function(lambda *a: 0, restype, *argtypes))
    return check(bool(attr(pf, getter)), "set and read back, not called")


@entry(48)
def _48():
    return read_back("setIsEqualFunction:", "isEqualFunction", "bool", "ptr", "ptr", "ptr")


@entry(49)
def _49():
    return read_back("setRelinquishFunction:", "relinquishFunction", "void", "ptr", "ptr")


@entry(51)
def _51():
    return read_back("setHashFunction:", "hashFunction", "ulong", "ptr", "ptr")


@entry(52)
def _52():
    return read_back("setAcquireFunction:", "acquireFunction", "ptr", "ptr", "ptr", "bool")


@entry(56)
def _56():
    return read_back("setDescriptionFunction:", "descriptionFunction", "id", "ptr")


@entry(57)
def _57():
    return read_back("setSizeFunction:", "sizeFunction", "ulong", "ptr")


def ctx_reverse():
    return function(lambda a, b, ctx: reverse(a, b), "long", "id", "id", "ptr")


@entry(50)
def _50():
    r, _ = call(ns_list(["a", "b", "c"]), "sortedArrayUsingFunction:context:", ctx_reverse(), None)
    return check(strings(r) == ["c", "b", "a"], strings(r))


@entry(53)
def _53():
    o = c("NSObject").alloc().init()
    sel = X.selector("hash")
    inv = c("NSInvocation").invocationWithMethodSignature_(o.methodSignatureForSelector_(sel))
    inv.setTarget_(o)
    inv.setSelector_(sel)
    call(inv, "invokeUsingIMP:", function(lambda me, cmd: 7, "ulong", "id", "ptr"))
    _, (v,) = call(inv, "getReturnValue:", Out("ulong"))
    return check(v == 7, v)


@entry(54)
def _54():
    a = c("NSMutableArray").arrayWithArray_(ns_list(["a", "b", "c"]))
    call(a, "sortUsingFunction:context:", ctx_reverse(), None)
    return check(strings(a) == ["c", "b", "a"], strings(a))


@entry(55)
def _55():
    a = ns_list(["a", "b", "c"])
    r, _ = call(a, "sortedArrayUsingFunction:context:hint:", ctx_reverse(), None, attr(a, "sortedArrayHint"))
    return check(strings(r) == ["c", "b", "a"], strings(r))


@entry(98)
def _98():
    X.arg(function(reverse, "long", "id", "id", "ptr"))  # Checked first: the setup needs more of the library.
    view = c("NSView").alloc().init()
    for name in ("a", "b"):
        sub = c("NSView").alloc().init()
        sub.setIdentifier_(s(name))
        view.addSubview_(sub)

    def compare(x, y, ctx):
        return reverse(attr(x, "identifier"), attr(y, "identifier"))
    call(view, "sortSubviewsUsingFunction:context:", function(compare, "long", "id", "id", "ptr"), None)
    subs = attr(view, "subviews")
    names = [text(attr(subs.objectAtIndex_(i), "identifier")) for i in range(count(subs))]
    return check(names == ["b", "a"], names)


@entry(99)
def _99():
    X.arg(function(reverse, "long", "id", "id", "ptr"))  # Checked first: the setup needs more of the library.
    m = c("NSMatrix").alloc().initWithFrame_mode_cellClass_numberOfRows_numberOfColumns_(
        L.rect(0, 0, 10, 20), 0, c("NSActionCell"), 2, 1)
    m.cellAtRow_column_(0, 0).setTag_(1)
    m.cellAtRow_column_(1, 0).setTag_(2)

    def compare(x, y, ctx):
        return attr(y, "tag") - attr(x, "tag")
    call(m, "sortUsingFunction:context:", function(compare, "long", "id", "id", "ptr"), None)
    tags = [attr(m.cellAtRow_column_(i, 0), "tag") for i in range(2)]
    return check(tags == [2, 1], tags)


def main():
    global L, X
    lib, index = sys.argv[1], int(sys.argv[2])
    if index in EXCLUDED:
        outcome, detail = "excluded", EXCLUDED[index]
    else:
        ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
        ctypes.CDLL("/System/Library/Frameworks/CoreLocation.framework/CoreLocation")
        ctypes.CDLL("/System/Library/Frameworks/UserNotifications.framework/UserNotifications")
        L = load(lib)
        X = {"pyobjus": Pyobjus, "rubicon": Rubicon, "pyobjc": Pyobjc}[lib]()
        try:
            outcome, detail = ENTRIES[index]()
            if outcome == "correct" and X.unreadable:
                outcome = "correct, out object not readable"
        except NotExpressible as e:
            outcome, detail = "not expressible", str(e)
        except BaseException as e:
            outcome, detail = "python exception", f"{type(e).__name__}: {e}"[:300]
    shutil.rmtree(TMP, ignore_errors=True)
    print("S2RESULT " + json.dumps({"outcome": outcome, "detail": detail}), flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
