"""Section 2 scenarios. Each returns (outcome, detail). Expected results are
written here before any run: 'ok' means the expected result was seen. M2
scenarios expect every created object to be deallocated."""
import ctypes
import gc
import threading
import time
import weakref

from adapters import NotExpressible

objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
objc.objc_autoreleasePoolPush.restype = ctypes.c_void_p
objc.objc_autoreleasePoolPop.argtypes = [ctypes.c_void_p]
N = 1000
SCENARIOS = {}


def scenario(fn):
    SCENARIOS[fn.__name__] = fn
    return fn


class Pool:
    def __enter__(self):
        self.p = objc.objc_autoreleasePoolPush()

    def __exit__(self, *a):
        objc.objc_autoreleasePoolPop(self.p)


def collect():
    for _ in range(3):
        gc.collect()


def check(got, want):
    return ("ok", repr(got)) if got == want else ("wrong value", f"got {got!r}, expected {want!r}")


def leaves(value):
    """Flatten a returned struct, whichever form the library returns it in."""
    if isinstance(value, (int, float)):
        return [value]
    if hasattr(value, "_fields_"):
        out = []
        for name, *_ in value._fields_:
            out += leaves(getattr(value, name))
        return out
    return [x for item in value for x in leaves(item)]


def judge(c, d, suffix=""):
    """Every created object should be freed. One object left is reported on its
    own: pyobjus's tests note that a class's methods hold the most recent
    wrapped instance until the next one."""
    detail = f"created {c}, deallocated {d}{suffix}"
    if c == d:
        return ("ok", detail)
    if c - d == 1:
        return ("ok, most recent object held", detail)
    return ("possible leak", detail) if d < c else ("possible over-release", detail)


def ctor(L, method):
    T = L.cls("S2Tracked")
    if method == "alloc_init":
        return T.alloc().init()
    if method == "new":
        return T.newTracked()
    if method == "convenience":
        return T.tracked()
    if method == "copy":
        with Pool():
            src = T.alloc().init()
            return src.copy()
    raise ValueError(method)


def counts(L):
    T = L.cls("S2Tracked")
    return T.createdCount(), T.deallocCount()


def types(L):
    return L.cls("S2Types").alloc().init()


# T2 conversions
@scenario
def t2_int(L):
    return check(types(L).echoInt_(-7), -7)

@scenario
def t2_float(L):
    return check(types(L).echoDouble_(2.5), 2.5)

@scenario
def t2_bool(L):
    return check(bool(types(L).echoBool_(True)), True)

@scenario
def t2_str(L):
    return check(L.to_py(types(L).echoObject_(L.nsstr("héllo"))), "héllo")

@scenario
def t2_bytes(L):
    r = types(L).echoCString_(b"abc")
    r = r.encode() if isinstance(r, str) else (b"".join(r) if isinstance(r, (tuple, list)) else r)
    return check(r, b"abc")

@scenario
def t2_none(L):
    return check(types(L).echoObject_(None), None)

@scenario
def t2_list(L):
    return check(L.to_py(types(L).echoObject_([1, 2, 3])), [1, 2, 3])

@scenario
def t2_dict(L):
    return check(L.to_py(types(L).echoObject_({"a": 1})), {"a": 1})

@scenario
def t2_class(L):
    c = L.class_arg("NSString")
    r = types(L).echoClass_(c)
    if r is None:
        return ("wrong value", "returned None")
    n = L.class_name(r)
    if n is None:
        return ("returned, no public way to read it", repr(r))
    return check(n, "NSString")

@scenario
def t2_class_usable(L):
    """A class passed as an argument can be told from its metaclass by the runtime."""
    r = L.cls("NSArray").isSubclassOfClass_(L.class_arg("NSObject"))
    return ("ok", str(bool(r))) if r else ("wrong value", "NSArray isn't a subclass of the NSObject passed")


@scenario
def t2_selector(L):
    r = types(L).echoSelector_(L.selector("description"))
    n = L.selector_name(r)
    if n is None:
        return ("returned, no public way to read it", repr(r)) if r is not None else ("wrong value", repr(r))
    return check(n, "description")

@scenario
def t2_pointer(L):
    buf = ctypes.create_string_buffer(8)
    addr = ctypes.addressof(buf)
    r = types(L).echoPointer_(ctypes.c_void_p(addr) if L.name == "rubicon" else addr)
    v = getattr(r, "arg_ref", getattr(r, "value", r))
    if hasattr(r, "__pointer__"):
        v = r.__pointer__
    try:
        return check(int(v), addr)
    except (TypeError, ValueError):
        return ("wrong value", repr(r))


# T3 structs
@scenario
def t3_rect(L):
    from adapters import rect_values
    return check(rect_values(types(L).echoRect_(L.rect(1.5, 2.5, 3.5, 4.5))), (1.5, 2.5, 3.5, 4.5))

@scenario
def t3_range(L):
    r = types(L).echoRange_(L.range(3, 4))
    return check((r.location, r.length), (3, 4))

@scenario
def t3_insets(L):
    r = types(L).echoInsets_(L.insets(1.0, 2.0, 3.0, 4.0))
    return check(leaves(r), [1.0, 2.0, 3.0, 4.0])

@scenario
def t3_nested(L):
    t = types(L)
    if hasattr(L, "register_nested"):
        L.register_nested(b"{?={CGPoint=dd}{_NSRange=QQ}{?=id}}")
    r = t.echoNested_(L.nested())
    return check(leaves(r), [1.5, 2.5, 3, 4, 5, 6.5])


# T4 wrong use: a Python exception is the expected result in each case.
def expect_exception(fn):
    try:
        r = fn()
    except NotExpressible:
        raise
    except BaseException as e:
        return ("ok", f"{type(e).__name__}: {e}"[:160])
    return ("wrong value", f"no exception; returned {r!r}"[:160])

@scenario
def t4_unknown_selector(L):
    return expect_exception(lambda: types(L).noSuchMethod_(1))

@scenario
def t4_wrong_type_scalar(L):
    return expect_exception(lambda: types(L).echoInt_("not a number"))

@scenario
def t4_wrong_type_object(L):
    return expect_exception(lambda: L.cls("S2Types").alloc().init().echoRect_("not a rect"))

@scenario
def t4_too_few_args(L):
    return expect_exception(lambda: types(L).echoInt_())

@scenario
def t4_too_many_args(L):
    return expect_exception(lambda: types(L).echoInt_(1, 2))

# Scenario source: PyObjC test_exceptions.py, TestExceptionsFromObjC.testSimple
@scenario
def t4_objc_exception(L):
    return expect_exception(lambda: types(L).raiseException())


# M2 object lifetime
def lifetime(L, method):
    L.cls("S2Tracked").resetCounts()
    with Pool():
        objs = [ctor(L, method) for _ in range(N)]
        del objs
        collect()
    collect()
    return judge(*counts(L))

@scenario
def m2_alloc_init(L): return lifetime(L, "alloc_init")
@scenario
def m2_alloc_init_manual_release(L):
    """A release from the caller after alloc and init. pyobjus's docs don't say whether
    this is needed. Rubicon's and PyObjC's say the library manages it, so it isn't run."""
    if L.name != "pyobjus":
        return ("not applicable", "the library's docs say it manages this")
    L.cls("S2Tracked").resetCounts()
    with Pool():
        objs = [ctor(L, "alloc_init") for _ in range(N)]
        for o in objs:
            o.release()
        del objs
        collect()
    collect()
    return judge(*counts(L))

@scenario
def m2_new(L): return lifetime(L, "new")
@scenario
def m2_copy(L): return lifetime(L, "copy")
@scenario
def m2_convenience(L): return lifetime(L, "convenience")

@scenario
def m2_container(L):
    L.cls("S2Tracked").resetCounts()
    H = L.cls("S2Holder")
    holders = []
    with Pool():
        for _ in range(N):
            h = H.alloc().init()
            o = L.cls("S2Tracked").alloc().init()
            h.hold_(o)
            del o
            holders.append(h)
        collect()
    collect()
    c, d = counts(L)
    if d != 0:
        return ("possible over-release", f"held objects freed early: created {c}, deallocated {d}")
    with Pool():
        for h in holders:
            h.releaseHeld()
        del holders, h
        collect()
    collect()
    c, d = counts(L)
    return judge(c, d)

@scenario
def m2_cycle(L):
    """Python-defined object holds a tracked object, which retains it back.
    The cycle crosses the bridge, so it is reported rather than judged: 'ok'
    means both sides were freed after the fixture's side of the cycle is cut."""
    L.cls("S2Tracked").resetCounts()
    with Pool():
        class State:
            pass
        state = State()
        d = L.state_delegate(state)
        t = L.cls("S2Tracked").alloc().init()
        state.t = t
        t.setStrongRef_(d)
        del t, d, state
        collect()
    collect()
    c, dd = counts(L)
    return ("freed", f"created {c}, deallocated {dd} with the cycle intact") if c == dd else ("not freed", f"created {c}, deallocated {dd} with the cycle intact")


# M3 autorelease pools
@scenario
def m3_no_pool_main(L):
    L.cls("S2Tracked").resetCounts()
    for _ in range(N):
        L.cls("S2Tracked").tracked()
    collect()
    c, d = counts(L)
    return ("freed", f"created {c}, deallocated {d}") if c - d <= 1 else ("not freed without a pool", f"created {c}, deallocated {d}")

@scenario
def m3_no_pool_background(L):
    L.cls("S2Tracked").resetCounts()
    T = L.cls("S2Tracked")

    def work():
        for _ in range(N):
            T.tracked()
        collect()
    t = threading.Thread(target=work)
    t.start()
    t.join()
    collect()
    c, d = counts(L)
    return ("freed", f"created {c}, deallocated {d} after the thread ended") if c - d <= 1 else ("not freed without a pool", f"created {c}, deallocated {d} after the thread ended")

# Scenario source: objc4 test/rr-autorelease.m (temporary objects freed by the pool)
@scenario
def m3_with_pool_loop(L):
    L.cls("S2Tracked").resetCounts()
    for _ in range(10):
        with Pool():
            for _ in range(N // 10):
                L.cls("S2Tracked").tracked()
            collect()
    collect()
    return judge(*counts(L))


# M4 delegates and Python-defined objects
def freed(L, make):
    L.cls("S2Tracked").resetCounts()
    H = L.cls("S2Holder").alloc().init()

    class State:
        pass
    refs = []
    with Pool():
        for _ in range(100):
            st = State()
            refs.append(weakref.ref(st))
            o = make(st)
            H.attachTrackerTo_(o)
            del o, st
        collect()
    collect()
    c, d = counts(L)
    alive = sum(1 for r in refs if r() is not None)
    detail = f"Objective-C objects: created {c}, deallocated {d}. Python state alive: {alive} of 100"
    return ("ok", detail) if c == d and alive == 0 else ("possible leak", detail)

@scenario
def m4_delegate(L):
    return freed(L, L.state_delegate)

@scenario
def m4_subclass(L):
    return freed(L, L.state_subclass)


# M5 stale references
@scenario
def m5_owner_released(L):
    H = L.cls("S2Holder").alloc().init()
    H.hold_(L.cls("S2Tracked").alloc().init())
    w = H.held()
    H.releaseHeld()
    collect()
    return check(w.value(), 42)

@scenario
def m5_weak_cleared(L):
    H = L.cls("S2Holder").alloc().init()
    with Pool():
        o = L.cls("S2Tracked").alloc().init()
        H.storeWeak_(o)
        first = H.loadWeak()
        ok = first is not None
        del first, o
        collect()
    collect()
    return ("ok", "nil after the object was freed") if ok and H.loadWeak() is None else ("wrong value", f"set={ok}, later={H.loadWeak()!r}")

@scenario
def m5_extra_release(L):
    """Manual misuse. No outcome is expected; the result is recorded."""
    o = L.cls("S2Tracked").alloc().init()
    with Pool():
        o.release()
    collect()
    try:
        return ("no crash", f"call returned {o.value()!r}")
    except Exception as e:
        return ("python exception", f"{type(e).__name__}: {e}"[:160])


# TH1 GIL during calls
@scenario
def th1_gil_released(L):
    """Compare another thread's progress during a blocking call with its
    progress during time.sleep, which releases the GIL."""
    t = types(L)
    n = [0]
    stop = threading.Event()

    def spin():
        while not stop.is_set():
            n[0] += 1
    th = threading.Thread(target=spin)
    th.start()
    time.sleep(0.05)
    start = n[0]
    time.sleep(0.5)
    control = n[0] - start
    start = n[0]
    t.sleepFor_(0.5)
    during = n[0] - start
    stop.set()
    th.join()
    share = during / control
    detail = f"other thread ran {during} iterations during the call, {control} during time.sleep ({share:.1%})"
    return ("released", detail) if share > 0.5 else ("held", detail)


# TH2 background threads
def run_thread(fn):
    box = {}

    def body():
        try:
            box["r"] = fn()
        except BaseException as e:
            box["r"] = ("python exception", f"{type(e).__name__}: {e}"[:160])
    t = threading.Thread(target=body)
    t.start()
    t.join()
    return box["r"]

@scenario
def th2_m2_alloc_init(L):
    L.cls("S2Tracked")
    return run_thread(lambda: lifetime(L, "alloc_init"))

@scenario
def th2_m2_convenience(L):
    L.cls("S2Tracked")
    return run_thread(lambda: lifetime(L, "convenience"))

@scenario
def th2_move_to_background(L):
    o = L.cls("S2Tracked").alloc().init()
    return run_thread(lambda: check(o.value(), 42))

@scenario
def th2_move_to_main(L):
    box = {}
    def make():
        box["o"] = L.cls("S2Tracked").alloc().init()
    t = threading.Thread(target=make); t.start(); t.join()
    return check(box["o"].value(), 42)

@scenario
def th2_concurrent_calls(L):
    """Eight threads, each with its own object, call the same method."""
    bad = []
    T = L.cls("S2Types")
    def work(i):
        o = T.alloc().init()
        for j in range(5000):
            v = i * 100000 + j
            r = o.echoInt_(v)
            if r != v:
                bad.append((v, r))
    th = [threading.Thread(target=work, args=(i,)) for i in range(8)]
    [t.start() for t in th]; [t.join() for t in th]
    return ("ok", "40000 calls") if not bad else ("wrong value", f"{len(bad)} of 40000 wrong; first {bad[0]}")


# TH3 foreign threads
def wait_fired(L, start):
    ev = threading.Event()
    d = L.delegate({"delegateFired": lambda: ev.set()})
    start(d)
    return ("ok", "callback ran") if ev.wait(5) else ("not called", "no callback within 5s")

@scenario
def th3_delegate_gcd(L):
    c = L.cls("S2Caller").alloc().init()
    return wait_fired(L, c.fireOnGCD_)

@scenario
def th3_delegate_pthread(L):
    c = L.cls("S2Caller").alloc().init()
    return wait_fired(L, c.fireOnPthread_)

@scenario
def th3_delegate_pthread_wait(L):
    """The Objective-C call blocks until the callback finishes on another
    thread. A bridge that holds the GIL during the call hangs here."""
    c = L.cls("S2Caller").alloc().init()
    return wait_fired(L, c.fireOnPthreadAndWait_)

@scenario
def th3_block_pthread_wait(L):
    b = L.cls("S2Blocks").alloc().init()
    ev = threading.Event()
    block = L.void_block(lambda: ev.set()) if hasattr(L, "void_block") else L.block("void", lambda: ev.set())
    b.callOnPthreadAndWait_(block)
    return ("ok", "callback ran") if ev.wait(5) else ("not called", "no callback within 5s")


# CB2 signatures, for each callback type
VALUES = {"int": (21, lambda x: x * 2, 42), "double": (1.5, lambda x: x * 2, 3.0)}

def cb_int(L, kind):
    return run_cb(L, kind, "int")

def run_cb(L, kind, vt):
    if vt == "rect":
        from adapters import rect_values
        arg = L.rect(1.0, 2.0, 3.0, 4.0)
        fn = lambda r: r
        conv = rect_values
        want = (1.0, 2.0, 3.0, 4.0)
    elif vt == "rect_arg":
        arg = L.rect(1.0, 2.0, 3.0, 4.0)
        fn = lambda r: r.size.width
        conv = lambda x: x
        want = 3.0
    elif vt == "object":
        arg = L.cls("S2Tracked").alloc().init()
        fn = lambda o: o
        conv = lambda o: o.value() if o is not None else None
        want = 42
    else:
        arg, fn, want = VALUES[vt]
        conv = lambda x: x
    method = {"int": "callInt_value_", "double": "callDouble_value_", "object": "callObject_value_", "rect": "callRect_value_", "rect_arg": "callRectArg_value_"}[vt]
    sel = {"int": "delegateInt_", "double": "delegateDouble_", "object": "delegateObject_", "rect": "delegateRect_"}.get(vt)
    if kind in ("delegate", "subclass"):
        target = getattr(L, kind)({sel: fn})
        caller = L.cls("S2Caller").alloc().init()
    elif kind == "block":
        target = L.block(vt, fn)
        caller = L.cls("S2Blocks").alloc().init()
    else:
        target = L.function(vt, fn)
        caller = L.cls("S2Functions").alloc().init()
    return check(conv(getattr(caller, method)(target, arg)), want)

for _k in ("delegate", "subclass", "block", "function"):
    for _v in ("int", "double", "object", "rect"):
        def _mk(k, v):
            def f(L):
                return run_cb(L, k, v)
            f.__name__ = f"cb2_{k}_{v}"
            return f
        SCENARIOS[f"cb2_{_k}_{_v}"] = _mk(_k, _v)
for _k in ("block", "function"):
    SCENARIOS[f"cb2_{_k}_rect_arg"] = _mk(_k, "rect_arg")


# CB3 exceptions raised in callbacks. Expected: no crash, and Objective-C
# receives zero. How the exception is reported is recorded in the raw output.
def boom(*a):
    raise ValueError("raised in callback")

def run_cb3(L, kind):
    if kind in ("delegate", "subclass"):
        target = getattr(L, kind)({"delegateInt_": boom})
        caller = L.cls("S2Caller").alloc().init()
    elif kind == "block":
        target = L.block("int", boom)
        caller = L.cls("S2Blocks").alloc().init()
    else:
        target = L.function("int", boom)
        caller = L.cls("S2Functions").alloc().init()
    try:
        r = caller.callInt_value_(target, 5)
    except ValueError as e:
        return ("propagated to Python", str(e))
    except Exception as e:
        return ("python exception", f"{type(e).__name__}: {e}"[:160])
    return ("swallowed, Objective-C got zero", f"returned {r!r}") if r == 0 else ("swallowed, other value", f"returned {r!r}")

for _k in ("delegate", "subclass", "block", "function"):
    def _mk3(k):
        def f(L):
            return run_cb3(L, k)
        return f
    SCENARIOS[f"cb3_{_k}"] = _mk3(_k)


# CB4 lifetime: Objective-C keeps the callback, Python drops its references.
def run_cb4(L, kind):
    if kind in ("delegate", "subclass"):
        c = L.cls("S2Caller").alloc().init()
        c.retainDelegate_(getattr(L, kind)({"delegateInt_": lambda x: x + 1}))
        collect()
        for _ in range(1000):
            bytearray(256)
        return check(c.callRetainedInt_(1), 2)
    if kind == "block":
        c = L.cls("S2Blocks").alloc().init()
        c.storeInt_(L.block("int", lambda x: x + 1))
    else:
        c = L.cls("S2Functions").alloc().init()
        c.storeInt_(L.function("store_int", lambda x: x + 1))
    collect()
    for _ in range(1000):
        bytearray(256)
    return check(c.callStoredInt_(1), 2)

for _k in ("delegate", "subclass", "block", "function"):
    def _mk4(k):
        def f(L):
            return run_cb4(L, k)
        return f
    SCENARIOS[f"cb4_{_k}"] = _mk4(_k)


# CB5 blocks
@scenario
def cb5a_create_and_pass(L):
    return run_cb(L, "block", "int")

# Scenario source: PyObjC test_blocks.py, test_block_is_collected
@scenario
def cb5a_block_collected(L):
    class S:
        pass
    st = S()
    r = weakref.ref(st)
    c = L.cls("S2Blocks").alloc().init()
    with Pool():
        c.storeInt_(L.block("int", lambda x, s=st: x))
        del st
        collect()
    c.dropStored()
    collect()
    return ("ok", "Python function freed after Objective-C dropped the block") if r() is None else ("possible leak", "Python function still alive after Objective-C dropped the block")

@scenario
def cb5b_receive_int(L):
    b = L.cls("S2Blocks").alloc().init().makeIntBlock()
    return check(L.call_block("int", b, 41), 42)

@scenario
def cb5b_receive_double(L):
    b = L.cls("S2Blocks").alloc().init().makeDoubleBlock()
    return check(L.call_block("double", b, 1.5), 3.0)

@scenario
def cb5b_receive_object(L):
    o = L.cls("S2Tracked").alloc().init()
    b = L.cls("S2Blocks").alloc().init().makeObjectBlock()
    r = L.call_block("object", b, o)
    return check(r.value() if r is not None else None, 42)

@scenario
def cb5b_receive_rect(L):
    from adapters import rect_values
    b = L.cls("S2Blocks").alloc().init().makeRectBlock()
    return check(rect_values(L.call_block("rect", b, L.rect(1.0, 2.0, 3.0, 4.0))), (1.0, 2.0, 3.0, 4.0))

@scenario
def cb5b_receive_throwing(L):
    b = L.cls("S2Blocks").alloc().init().makeThrowingBlock()
    return expect_exception(lambda: L.call_block("void", b))

def later(L, offer):
    box = {}
    def take(b):
        box["b"] = b
    d = L.delegate({"delegateTakeBlock_": take})
    with Pool():
        offer(L.cls("S2Caller").alloc().init(), d)
    collect()
    if "b" not in box or box["b"] is None:
        return ("wrong value", "delegate did not receive a block")
    return check(L.call_block("int", box["b"], 1), 101)

@scenario
def cb5b_after_return(L):
    return later(L, lambda c, d: c.offerBlockTo_(d))

# Scenario source: PyObjC test_blocks.py, testStackBlocksWithIndirectUse
@scenario
def cb5b_stack_block_after_return(L):
    return later(L, lambda c, d: c.offerStackBlockTo_(d))
