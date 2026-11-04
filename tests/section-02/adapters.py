"""One adapter per library. Scenarios use only this interface, so the same
scenario runs against each. Only public, documented APIs are used."""
import ctypes
import sys
from ctypes import c_double, c_int, c_size_t, CFUNCTYPE, c_long, c_void_p


class NotExpressible(Exception):
    """The library has no public way to write this scenario."""


class Point(ctypes.Structure):
    _fields_ = [("x", c_double), ("y", c_double)]


class Size(ctypes.Structure):
    _fields_ = [("width", c_double), ("height", c_double)]


NESTED_ENC = b"{?={CGPoint=dd}{_NSRange=QQ}{?=id}}"


def rect_values(r):
    return (r.origin.x, r.origin.y, r.size.width, r.size.height)


def load_pyobjus():
    from pyobjus import autoclass, objc_str, protocol, convert_py_to_nsobject, selector
    from pyobjus.objc_py_types import NSPoint, NSRange, NSRect, NSSize

    class NSEdgeInsets(ctypes.Structure):
        _fields_ = [("top", c_double), ("left", c_double), ("bottom", c_double), ("right", c_double)]

    class Inner(ctypes.Structure):
        _fields_ = [("a", c_int), ("b", c_double)]

    class Nested(ctypes.Structure):
        _fields_ = [("origin", NSPoint), ("range", NSRange), ("inner", Inner)]

    class A:
        name = "pyobjus"
        version = __import__("pyobjus").__version__

        def cls(self, name):
            return autoclass(name)

        def nsstr(self, s):
            return objc_str(s)

        def to_py(self, x):
            if x is None or isinstance(x, (int, float, str, bytes, bool)):
                return x
            if hasattr(x, "UTF8String"):
                return x.UTF8String()
            if hasattr(x, "objectForKey_"):
                keys = x.allKeys()
                return {self.to_py(keys.objectAtIndex_(i)): self.to_py(x.objectForKey_(keys.objectAtIndex_(i)))
                        for i in range(keys.count())}
            if hasattr(x, "objectAtIndex_"):
                return [self.to_py(x.objectAtIndex_(i)) for i in range(x.count())]
            if hasattr(x, "longLongValue"):
                return x.longLongValue()
            return x

        def to_ns(self, x):
            return convert_py_to_nsobject(x)

        def rect(self, *v):
            return NSRect(NSPoint(v[0], v[1]), NSSize(v[2], v[3]))

        def range(self, a, b):
            return NSRange(a, b)

        def insets(self, *v):
            return NSEdgeInsets(*v)

        def nested(self):
            return Nested(NSPoint(1.5, 2.5), NSRange(3, 4), Inner(5, 6.5))

        def selector(self, name):
            return selector(name)

        def selector_name(self, s):
            return None

        def class_name(self, c):
            return None

        def class_arg(self, name):
            return autoclass(name).oclass()

        def delegate(self, handlers):
            ns = {}
            for selname, func in handlers.items():
                def wrap(f):
                    @protocol("S2Delegate")
                    def method(self, *args):
                        return f(*args)
                    return method
                ns[selname] = wrap(func)
            return type("PyDelegate", (object,), ns)()

        def state_delegate(self, state):
            class StateDelegate:
                @protocol("S2Delegate")
                def delegateFired(self):
                    return None
            d = StateDelegate()
            d.state = state
            return d

        def state_subclass(self, state):
            raise NotExpressible("pyobjus has no public API for subclassing an Objective-C class")

        def subclass(self, handlers):
            raise NotExpressible("pyobjus has no public API for subclassing an Objective-C class")

        def block(self, kind, func):
            raise NotExpressible("pyobjus has no public API for creating a block")

        def call_block(self, kind, block, *args):
            if not callable(block):
                raise NotExpressible("pyobjus returns a block as an object with no public way to call it")
            return block(*args)

        def function(self, kind, func):
            raise NotExpressible("pyobjus has no public way to pass a function pointer. Its pointer "
                                 "arguments pass the address of the value, so a ctypes callback "
                                 "or an address crashes when called")

    return A()


def load_rubicon():
    import rubicon.objc as R
    from rubicon.objc import Block, CGPoint, CGRect, CGSize, NSObject, NSRange, ObjCBlock, ObjCClass, \
        ObjCProtocol, ns_from_py, objc_method, py_from_ns, objc_id, SEL
    from rubicon.objc.runtime import objc_block
    from rubicon.objc import types as rubicon_types
    from rubicon.objc.types import register_encoding

    class Inner(ctypes.Structure):
        _fields_ = [("a", c_int), ("b", c_double)]

    class Nested(ctypes.Structure):
        _fields_ = [("origin", CGPoint), ("range", NSRange), ("inner", Inner)]

    types = {"int": (c_long, c_long), "double": (c_double, c_double),
             "rect": (CGRect, CGRect), "rect_arg": (c_double, CGRect), "object": (c_void_p, objc_id)}
    counter = [0]
    state_classes = {}

    class A:
        name = "rubicon"
        version = R.__version__

        def cls(self, name):
            return ObjCClass(name)

        def nsstr(self, s):
            return ns_from_py(s)

        def to_py(self, x):
            if x is None or isinstance(x, (int, float, str, bytes, bool)):
                return x
            try:
                return py_from_ns(x)
            except TypeError:
                return x

        def to_ns(self, x):
            return ns_from_py(x)

        def rect(self, *v):
            return CGRect(CGPoint(v[0], v[1]), CGSize(v[2], v[3]))

        def range(self, a, b):
            return NSRange(a, b)

        def insets(self, *v):
            # The fixture uses each platform's own type, as Apple's frameworks do.
            name = "UIEdgeInsets" if sys.platform == "ios" else "NSEdgeInsets"
            return getattr(rubicon_types, name)(*v)

        def nested(self):
            return Nested(CGPoint(1.5, 2.5), NSRange(3, 4), Inner(5, 6.5))

        def register_nested(self, encoding):
            register_encoding(encoding, Nested)

        def selector(self, name):
            return SEL(name)

        def selector_name(self, s):
            return s.name.decode()

        def class_name(self, c):
            return c.name

        def class_arg(self, name):
            return ObjCClass(name)

        def _make(self, base, handlers, protocols):
            counter[0] += 1
            ns = {}
            sigs = {"delegateInt_": lambda f: self._m(f, int, int),
                    "delegateDouble_": lambda f: self._m(f, float, float),
                    "delegateObject_": lambda f: self._m(f, objc_id, objc_id, convert=True),
                    "delegateRect_": lambda f: self._m(f, CGRect, CGRect),
                    "delegateFired": lambda f: self._m(f, None),
                    "delegateTakeBlock_": lambda f: self._m(f, None, objc_block, block=True)}
            for selname, func in handlers.items():
                ns[selname] = sigs[selname](func)
            kwargs = {"protocols": protocols} if protocols else {}
            import types as _t
            return _t.new_class(f"PyS2_{counter[0]}", (base,), kwargs, lambda d: d.update(ns)).alloc().init()

        def _m(self, f, restype, argtype=None, convert=False, block=False):
            if argtype is None:
                def m(self) -> None:
                    f()
                return objc_method(m)
            if block:
                def m(self, b: objc_block) -> None:
                    f(b)
                return objc_method(m)
            if convert:
                from rubicon.objc import ObjCInstance
                def m(self, v) -> ObjCInstance:
                    return f(v)
                return objc_method(m)
            def m(self, v: argtype) -> restype:
                return f(v)
            return objc_method(m)

        def _state_class(self, base, protocols):
            key = base.name
            if key not in state_classes:
                import types as _t
                def fired(self) -> None:
                    pass
                kwargs = {"protocols": protocols} if protocols else {}
                state_classes[key] = _t.new_class(f"PyS2State_{key}", (base,), kwargs,
                                                  lambda d: d.update({"delegateFired": objc_method(fired)}))
            return state_classes[key]

        def state_delegate(self, state):
            o = self._state_class(NSObject, [ObjCProtocol("S2Delegate")]).alloc().init()
            o.state = state
            return o

        def state_subclass(self, state):
            o = self._state_class(ObjCClass("S2Overridable"), None).alloc().init()
            o.state = state
            return o

        def delegate(self, handlers):
            return self._make(NSObject, handlers, [ObjCProtocol("S2Delegate")])

        def subclass(self, handlers):
            return self._make(ObjCClass("S2Overridable"), handlers, None)

        def block(self, kind, func):
            restype, argtype = types[kind]
            if kind == "object":
                from rubicon.objc import ObjCInstance
                def f(v):
                    r = func(ObjCInstance(v))
                    return r.ptr.value if r is not None else None
                return Block(f, restype, argtype)
            return Block(func, restype, argtype)

        def void_block(self, func):
            return Block(func, None)

        def call_block(self, kind, block, *args):
            if not isinstance(block, ObjCBlock) and not callable(block):
                block = ObjCBlock(block)
            if kind == "object":
                from rubicon.objc import ObjCInstance
                r = block(*args)
                return ObjCInstance(r) if r else None
            return block(*args)

        def function(self, kind, func):
            kind = "int" if kind == "store_int" else kind
            restype, argtype = types[kind]
            if kind == "object":
                from rubicon.objc import ObjCInstance
                def f(v):
                    r = func(ObjCInstance(v))
                    return r.ptr.value if r is not None else None
                return CFUNCTYPE(restype, argtype)(f)
            return CFUNCTYPE(restype, argtype)(func)

    return A()


def load_pyobjc():
    import objc
    from Foundation import NSObject, NSMakeRect, NSMakeRange

    def reg(cls, sel, meta):
        objc.registerMetaDataForSelector(cls, sel, meta)

    _block = lambda t: {"callable": {"retval": {"type": t}, "arguments": {0: {"type": b"^v"}, 1: {"type": t}}}}
    for sel, t in ((b"callInt:value:", b"q"), (b"callDouble:value:", b"d"), (b"callObject:value:", b"@"),
                   (b"callRect:value:", b"{CGRect={CGPoint=dd}{CGSize=dd}}")):
        reg(b"S2Blocks", sel, {"arguments": {2: _block(t)}})
    reg(b"S2Blocks", b"callRectArg:value:", {"arguments": {2: {"callable": {"retval": {"type": b"d"}, "arguments": {
        0: {"type": b"^v"}, 1: {"type": b"{CGRect={CGPoint=dd}{CGSize=dd}}"}}}}}})
    reg(b"S2Functions", b"callRectArg:value:", {"arguments": {2: {"callable": {"retval": {"type": b"d"}, "arguments": {
        0: {"type": b"{CGRect={CGPoint=dd}{CGSize=dd}}"}}}}}})
    reg(b"S2Blocks", b"storeInt:", {"arguments": {2: _block(b"q")}})
    reg(b"S2Blocks", b"callOnPthreadAndWait:",
        {"arguments": {2: {"callable": {"retval": {"type": b"v"}, "arguments": {0: {"type": b"^v"}}}}}})
    for sel, t in ((b"makeIntBlock", b"q"), (b"makeDoubleBlock", b"d"), (b"makeObjectBlock", b"@"),
                   (b"makeRectBlock", b"{CGRect={CGPoint=dd}{CGSize=dd}}")):
        reg(b"S2Blocks", sel, {"retval": _block(t)})
    reg(b"S2Blocks", b"makeThrowingBlock",
        {"retval": {"callable": {"retval": {"type": b"v"}, "arguments": {0: {"type": b"^v"}}}}})
    _fn = lambda t: {"callable": {"retval": {"type": t}, "arguments": {0: {"type": t}}}}
    for sel, t in ((b"callInt:value:", b"q"), (b"callDouble:value:", b"d"), (b"callObject:value:", b"@"),
                   (b"callRect:value:", b"{CGRect={CGPoint=dd}{CGSize=dd}}")):
        reg(b"S2Functions", sel, {"arguments": {2: _fn(t)}})
    reg(b"S2Functions", b"storeInt:", {"arguments": {2: dict(_fn(b"q"), callable_retained=True)}})
    reg(b"S2Types", b"echoCString:", {"retval": {"c_array_delimited_by_null": True, "type": b"^t"},
                                       "arguments": {2: {"c_array_delimited_by_null": True, "type": b"n^t"}}})
    reg(b"NSObject", b"delegateTakeBlock:", {"arguments": {2: _block(b"q")}})
    counter = [0]
    state_classes = {}
    sigs = {"delegateInt_": b"q@:q", "delegateDouble_": b"d@:d", "delegateObject_": b"@@:@",
            "delegateRect_": b"{CGRect={CGPoint=dd}{CGSize=dd}}@:{CGRect={CGPoint=dd}{CGSize=dd}}",
            "delegateFired": b"v@:", "delegateTakeBlock_": b"v@:@?"}

    class A:
        name = "pyobjc"
        version = objc.__version__

        def cls(self, name):
            return objc.lookUpClass(name)

        def nsstr(self, s):
            return s

        def to_py(self, x):
            if x is None or isinstance(x, (int, float, bytes, bool)):
                return x
            if isinstance(x, str):
                return str(x)
            if hasattr(x, "allKeys"):
                return {self.to_py(k): self.to_py(x[k]) for k in x.allKeys()}
            if hasattr(x, "objectAtIndex_"):
                return [self.to_py(i) for i in x]
            return x

        def to_ns(self, x):
            return x

        def rect(self, *v):
            return NSMakeRect(*v)

        def range(self, a, b):
            return NSMakeRange(a, b)

        def insets(self, *v):
            return tuple(v)

        def nested(self):
            return ((1.5, 2.5), (3, 4), (5, 6.5))

        def selector(self, name):
            return name

        def selector_name(self, s):
            return s

        def class_name(self, c):
            return c.__name__

        def class_arg(self, name):
            return objc.lookUpClass(name)

        def _make(self, base, handlers, protos):
            counter[0] += 1
            ns = {}
            for selname, func in handlers.items():
                def wrap(f, n):
                    argc = sigs[n].count(b":")
                    if n == "delegateFired":
                        def m(self):
                            return f()
                    else:
                        def m(self, v):
                            return f(v)
                    return objc.selector(m, selector=n.replace("_", ":").encode(), signature=sigs[n])
                ns[selname] = wrap(func, selname)
            ns["__slots__"] = ()
            import types as _t
            kwargs = {"protocols": [objc.protocolNamed("S2Delegate")]} if protos else {}
            return _t.new_class(f"PyS2_{counter[0]}", (base,), kwargs, lambda d: d.update(ns)).alloc().init()

        def _state_class(self, base, protos):
            key = base.__name__
            if key not in state_classes:
                def fired(self):
                    return None
                ns = {"delegateFired": objc.selector(fired, selector=b"delegateFired", signature=b"v@:")}
                import types as _t
                kwargs = {"protocols": [objc.protocolNamed("S2Delegate")]} if protos else {}
                state_classes[key] = _t.new_class(f"PyS2State_{key}", (base,), kwargs, lambda d: d.update(ns))
            return state_classes[key]

        def state_delegate(self, state):
            o = self._state_class(NSObject, True).alloc().init()
            o.state = state
            return o

        def state_subclass(self, state):
            o = self._state_class(objc.lookUpClass("S2Overridable"), False).alloc().init()
            o.state = state
            return o

        def delegate(self, handlers):
            return self._make(NSObject, handlers, True)

        def subclass(self, handlers):
            return self._make(objc.lookUpClass("S2Overridable"), handlers, False)

        def block(self, kind, func):
            return func

        def void_block(self, func):
            return func

        def call_block(self, kind, block, *args):
            return block(*args)

        def function(self, kind, func):
            if kind == "store_int":
                return objc.callbackFor(objc.lookUpClass("S2Functions").storeInt_)(func)
            return func

    return A()


def load(name):
    return {"pyobjus": load_pyobjus, "rubicon": load_rubicon, "pyobjc": load_pyobjc}[name]()
