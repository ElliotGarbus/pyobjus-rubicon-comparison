# 2. Architecture

**Status: draft for factual review.** Neither project has reviewed this section. Versions are in [the baseline](../results/baseline/2026-11-04.md). Metric IDs refer to the [approved definitions](../metrics/02-architecture.md), which also list every change made after approval.

## Summary of findings

pyobjus is compiled Cython that calls `objc_msgSend` through libffi. It passed the basic type and struct scenarios at its default branch, but it doesn't free objects from `alloc`, `new` or `copy` by itself, never frees delegates, and holds the GIL during calls. It has no public way to write blocks, function pointers or Python subclasses. In a sample of Apple methods chosen for those harder kinds of call, it couldn't express 45 of the 73 called.

Rubicon is pure Python that calls `objc_msgSend` through `ctypes`. It passed the same scenarios, frees those objects, releases the GIL and can write those callback types. It got all 73 sampled Apple methods right. It relies on CPython internals for one feature, returns an unpredictable value when a callback raises, and crashes in some misuse and exception scenarios.

All figures are **Measured** unless labeled otherwise, on a shared fixture, not a real app. This section makes no recommendation. "`master`" and "`main`" mean the default branches. Results are from 82 scenarios run 5 times each, and are the same on Mac and iPhone unless stated.

| Topic | pyobjus `master` | Rubicon |
|---|---|---|
| How it calls Objective-C (**Source**) | Compiled Cython, through libffi | Pure Python, through `ctypes` |
| Builds and Python internals (**Source**) | One build per Python version and platform | One wheel, but relies on private CPython structures for struct returns from methods |
| Basic types and structs | Pass, except short `dict` keys, an ignored extra argument and classes passed as arguments | Pass |
| Apple API sample, 73 calls (Mac only) | 11 correct, 13 partly correct, 4 exceptions, 45 not expressible | 73 correct |
| 1,000 `alloc` and `init` objects freed | 0, or 999 with a manual `release` | 1,000 |
| 100 delegates freed | 0 | 100 |
| Reference cycle between Python and Objective-C | Not freed | Not freed |
| GIL during a call | Held | Released |
| Call waiting on a callback from another thread | Hangs | Passes |
| Free-threaded Python, on import (Mac only) | GIL re-enabled | GIL stays disabled |
| Blocks, function pointers, Python subclasses | No public way to write them | Supported, but blocks and function pointers can't return structs |
| Structs in a delegate | Not supported | Supported |
| Python exception in a callback | Objective-C gets zero | Value varies by callback type and platform |
| Objective-C exception | Crash | Crash |

1. **Design (Source):** pyobjus needs a build per Python version and platform, because it compiles against the CPython C API. Rubicon compiles nothing, so one wheel covers all, but its `ctypes_patch` module relies on the layout of private CPython and `ctypes` structures, and warns on untested Python versions.
2. **Types:** at the default branches, all struct scenarios passed on both. pyobjus returned short dictionary keys as `bytes`, ignored an extra argument, and passed a metaclass where a class was asked for. In a sample of Apple's API, 73 methods were called. Rubicon got 73 correct. pyobjus `master` got 11 correct and 13 with a correct return value but an unreadable out object, raised 4 exceptions, and couldn't express 45.
3. **Memory:** pyobjus freed 0 of 1,000 objects from `alloc` and `init`, and 999 of 1,000 when the test added a manual `release`. It freed 0 of 100 delegates, and their Python state stayed alive. Rubicon freed all of these. Neither library creates a pool for the caller, and neither frees a reference cycle between Python and Objective-C.
4. **Threads:** during a blocking call, another Python thread made 0.1% to 1.3% of the progress it made during `time.sleep` on pyobjus, and 90% to 119% on Rubicon. A pyobjus call that waits on a callback from another thread hangs. Importing pyobjus re-enables the GIL on free-threaded Python, and importing Rubicon doesn't.
5. **Callbacks:** pyobjus can write delegates only, and delegates receive structs as `None` by design. Rubicon can write all four types, but blocks and function pointers can't return structs. When a Python callback raises, pyobjus gives Objective-C zero. Rubicon's value depends on the callback type and platform, and changed between runs on the iPhone.
6. **Crashes:** on Rubicon, four scenarios crash beyond the test that deliberately over-releases: an Objective-C exception, one thrown by a received block, a function pointer whose Python reference was dropped, and a stack block called after it went out of scope. On pyobjus `master`, only the Objective-C exception crashes. Many of the same scenarios can't be written on pyobjus, so this isn't a like-for-like count.
7. **Versions:** 9 scenarios improved from pyobjus 1.2.4 to `master`, including a struct crash and wrong delegate return values. Rubicon 0.5.7 and `main` matched everywhere.
8. **Long-open issues (Inferred, from reading each issue):** none of pyobjus's five concerns memory safety. One of Rubicon's five reports a memory-access crash whose cause was never identified, and another concerns memory-management docs.

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Relevant data |
|---|---|
| 4. Some pyobjus issues closed in 2026 had been open for 5 to 12 years | Section 1 left open whether any were memory-safety bugs. None were (M6). pyobjus's known lifetime failures are recorded in its tests, not in these issues. |
| 6. `ctypes` makes some memory-safe behavior impossible in Rubicon | Stays **Reported**. The [examples requested](https://github.com/kivy/kivy/issues/9469#issuecomment-6543683260) hadn't been provided by the time this was written. These tests found `ctypes` limits, and [rubicon-objc#73](https://github.com/beeware/rubicon-objc/issues/73) says Objective-C exceptions can't be handled with `ctypes` alone. Rubicon freed every object in M2 and M4 apart from the cycle. See [Reading claim 6](#reading-claim-6). |
| 7. pyobjus leaks memory, for example through `delegate_register` | Confirmed on this fixture for delegates and for objects from `alloc`, `new` and `copy` (M2, M4). A manual `release` frees `alloc` objects, and there's no public way to remove a delegate. Section 6 measures the amounts. |
| 9. pyobjus can't create blocks | Confirmed: no public API (CB5). Section 3 reports on the effect. |
| 10. pyobjus can't subclass Objective-C classes from Python | No public API found, so results are "not expressible". Section 3 reports on this. |
| 11. pyobjus delegates can register protocols at runtime, but can't pass struct, union or array values | Struct arguments confirmed: [the source](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L959) passes `None`, and a delegate received none of the rect's values (CB2). Union and array values weren't tested. |
| 12. Rubicon `@Block` crashes on iOS with kivy-ios Python 3.11 and works on 3.15 | Blocks worked on the iPhone on Python 3.15 (CB5). Python 3.11 and kivy-ios weren't tested. |

## Supporting facts

Raw results, the test-fix log and rerun steps are in [`results/section-02/2026-11-04`](../results/section-02/2026-11-04/README.md) and [`tests/section-02`](../tests/section-02/README.md). The Mac is on Python 3.14 and macOS 26.6.2. The iPhone is on Python 3.15 and iOS 27.0.1, using a no-Kivy test app. Rubicon 0.5.7 and `main` gave the same result in every scenario, so "Rubicon" means both. Where pyobjus 1.2.4 differs from `master`, the table says so. PyObjC 13.0 ran as a control on the Mac, and is [reported separately](#pyobjc-control).

### D. Design (Source)

**D1, how a call reaches Objective-C:**

| Step | pyobjus | Rubicon |
|---|---|---|
| Find the method | [`autoclass`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L706) builds a Python class, copying the method list with [`class_copyMethodList`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L562) | [`ObjCClass`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L1202) looks up a method [on first use](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L1477) and can [load the full list](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L1685) |
| Convert arguments | [`ObjcMethod.__call__`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L358) in Cython | [`ObjCMethod.__call__`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L198) in Python |
| Call | [`ffi_call` on `objc_msgSend`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L463) | [`send_message`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/runtime.py#L866), which calls `objc_msgSend` through `ctypes` |

**D2, compiled parts and dependencies:**

|  | pyobjus | Rubicon |
|---|---|---|
| Compiled code | One Cython extension, [`pyobjus.pyx`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L77) | None |
| Build needs | Cython, a C compiler, and [libffi](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/setup.py#L48) | Packaging tools only |
| Runtime libffi | Mac wheel links the system's `/usr/lib/libffi.dylib`, and iOS links a static copy | Python's own `_ctypes` module |
| Release artifacts | 11 wheels for 1.2.4 (Section 1) | One `py3-none-any` wheel |

**D3, reliance on Python internals:** pyobjus uses the CPython C API through Cython, so each Python version needs its own build. Rubicon needs no build per version. [`ctypes_patch`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/ctypes_patch.py#L21) patches private CPython and `ctypes` structures so that methods can return structs, has [separate code for Python before 3.13](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/ctypes_patch.py#L94), and warns on Python [3.16 or later](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/ctypes_patch.py#L30). Neither library's metadata declares free-threading support.

### T. Type handling

**T1, source of types (Source):**

|  | pyobjus | Rubicon |
|---|---|---|
| Methods | Runtime, through [`method_copyArgumentType`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L553) | Runtime, through [`method_getTypeEncoding`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L187) |
| Struct layouts | [Parsed from the encoding](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/type_enc.pxi#L12), with [named types in a registry](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/objc_py_types.py#L27) and [generated ones for the rest](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/objc_py_types.py#L78) | [Parsed from the encoding](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/types.py#L342), and users can [register names](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/types.py#L423) |
| Bit fields | [Raises an exception](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L280) | Supported |
| Python-defined callbacks | [Protocol from the runtime](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L1098), then a [built-in table](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L1091) | [Python annotations](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L144) |

**T2 to T4, scenarios through the fixture:**

| Scenario | pyobjus `master` | Rubicon |
|---|---|---|
| `int`, `float`, `bool`, `str`, `bytes`, `None`, `list`, pointer | Pass | Pass |
| `dict` | Wrong value: key `'a'` returned as `b'a'`. 1.2.4 also swapped keys and values | Pass |
| Class returned | Returned, with no public way to read it | Pass |
| Selector returned | Returned, with no public way to read it | Pass |
| Class passed as an argument | Wrong value: [`oclass()`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L249) gives the metaclass, so `NSArray` isn't a subclass of `NSObject` | Pass |
| `CGRect`, `NSRange`, edge insets, nested struct | Pass. On 1.2.4, `CGRect` crashes 3 of 5 runs on Mac and 1 of 5 on iPhone, and insets and nested structs raise exceptions | Pass |
| Unknown selector, wrong type, too few arguments | Python exception | Python exception |
| Too many arguments | No exception, and returns 1 | Python exception |
| Objective-C exception | Crash, `SIGABRT` | Crash, `SIGABRT` |

**T5, Apple API sample (macOS only):** a [seeded sample](../results/section-02/2026-11-04/raw/t5_sample.json) of 131 entries from Apple's BridgeSupport files, of which 12 are informal protocol entries that aren't methods on a class. pyobjus found the other 119 but has no public way to read a signature. Rubicon found them, and each signature matched. 73 entries were then called, 5 times each, and each gave the same result in all 5 runs. 58 were excluded, each [with a reason](../tests/section-02/t5_calls.py), for example because they need a permission, the network or a window.

| Library | Correct | Correct, out object unreadable | Wrong value | Python exception | Not expressible |
|---|---:|---:|---:|---:|---:|
| pyobjus `master` | 11 | 13 | 0 | 4 | 45 |
| pyobjus 1.2.4 | 8 | 12 | 1 | 8 | 44 |
| Rubicon | 73 | 0 | 0 | 0 | 0 |

- **pyobjus not expressible on `master`:** 23 blocks, 12 function pointers, and 10 methods that need an object out parameter. For `id *`, pyobjus [treats any value but nil as a delegate to create](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L456).
- **pyobjus exceptions on `master`:** 4 `NSDecimal` entries, because of bit fields.
- **Limits:** coverage is thin for CoreLocation (1 of 20 called) and UserNotifications (4 of 11). Some correct results are shallow: 4 blocks are accepted but never run, and 6 function pointers are set and read back without being called. The sample shows how each library handles these kinds of API, not how often apps use them. Full results are in [the results README](../results/section-02/2026-11-04/README.md).

### M. Memory management

**M1, ownership (Source):**

|  | pyobjus | Rubicon |
|---|---|---|
| On receiving an object | [Always retains](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_types.pxi#L727), whichever method it came from | [Retains unless](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L968) the [method family](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L96) already gave ownership |
| When Python no longer references the object | [Gives up one reference immediately, with `release`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_types.pxi#L721) | [Gives up one reference when the autorelease pool drains, with `autorelease`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L1007) |
| Result for `alloc`, `new`, `copy` | One reference is left, and pyobjus's [own tests mark this as an expected failure](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_object_lifecycle.py#L56) | Balanced |
| Python-held class reference | A class's method [holds the most recent instance](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L355) until the next one | None |
| Delegates | [Stored in `delegate_register`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L1272), and nothing removes them | Ordinary objects |
| Docs | [Don't cover ownership](https://github.com/kivy/pyobjus/tree/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source) | [A topic page](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/memory-management.md#L1) covers this, plus weak references and cycles |

Rubicon's docs say the caller must keep a Python reference to an object stored in a weak property, which is common for delegates. pyobjus's `delegate_register` removes that need (**Inferred**), because the delegate is never freed. No scenario here tests a weak delegate property.

**M2 to M5, objects deallocated:**

| Scenario | pyobjus | Rubicon |
|---|---|---|
| `alloc` and `init`, 1,000 objects | 0 | 1,000 |
| The same, with a manual `release` | 999 | Not run: its docs say the library manages this |
| `new`, 1,000 objects | 0 | 1,000 |
| `copy`, 2,000 originals and copies | 0 | 2,000 |
| Convenience constructor, 1,000 objects | 999 | 1,000 |
| Held and released by a container, 1,000 objects | 0 | 1,000 |
| Reference cycle between Python and Objective-C, 1 object | 0, as expected | 0, as expected |
| Main thread, no pool from the caller, 1,000 objects | 0, as expected | 0, as expected |
| Main thread, a pool around every 100 objects, 1,000 objects | 999 | 1,000 |
| Background thread, no pool, after it ends, 1,000 objects | 999 | 1,000 |
| Delegates, 100 objects | 0, with Python state alive for 100 | 100, with no state alive |
| Python subclass, 100 objects | Not expressible | 100, with no state alive |
| Use after the owner's release, while Python holds a reference | Correct value | Correct value |
| Weak reference after dropping the object | Not cleared, because the object is never freed (**Inferred**) | Nil |
| Deliberate extra `release` by the test | No crash, because of the extra reference (**Inferred**) | Crash, `SIGSEGV` |

The manual `release` was tested only for `alloc` and `init`. The 1 object left in the 999 results is the "most recent instance" in the table above. pyobjus's 0 for the reference cycle doesn't isolate the cycle, because its objects from `alloc` and `init` and its delegates aren't freed without one.

**M3, pools (Source):** neither library creates a pool around calls. pyobjus [has pool helpers](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/_runtime.h#L13) that nothing calls, and no public pool API. Rubicon provides [`autoreleasepool()`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/runtime.py#L1247). The scenarios run with no run loop. An app's event loop normally drains a pool on each cycle, so the main-thread result applies to long loops outside one.

**M6, long-open issues (Inferred, from reading each issue):**

| Issue | Kind | Memory safety? |
|---|---|---|
| [pyobjus#15](https://github.com/kivy/pyobjus/issues/15) | Questioned a tagged-pointer constant, in code later removed. No failure reported | No |
| [pyobjus#21](https://github.com/kivy/pyobjus/issues/21) | `IndexError` parsing a type encoding | No |
| [pyobjus#44](https://github.com/kivy/pyobjus/issues/44) | Clone fails on Windows | No |
| [pyobjus#70](https://github.com/kivy/pyobjus/issues/70) | `KeyError` returning `UIEdgeInsets` | No |
| [pyobjus#76](https://github.com/kivy/pyobjus/issues/76) | `TypeError` from a `str` argument to `autoclass` | No |
| [rubicon-objc#48](https://github.com/beeware/rubicon-objc/issues/48) | Asked for memory-management docs. Automatic retain and release were added along the way | Concerns memory management. No crash or leak reported |
| [rubicon-objc#137](https://github.com/beeware/rubicon-objc/issues/137) | Intermittent async test errors | No |
| [rubicon-objc#183](https://github.com/beeware/rubicon-objc/issues/183) | Slow instance creation | No |
| [rubicon-objc#188](https://github.com/beeware/rubicon-objc/issues/188) | Docs build | No |
| [rubicon-objc#223](https://github.com/beeware/rubicon-objc/issues/223) | `EXC_BAD_ACCESS` calling a Python-defined method from Objective-C on Python 3.9. It didn't reproduce on Python 3.12, and the cause wasn't identified | Possibly |

### TH. Threading

| Metric | pyobjus | Rubicon |
|---|---|---|
| TH1, GIL during a call | Held, because [`ffi_call`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L463) has no `nogil` (**Source**). Another thread made 0.3% to 1.3% of its progress during `time.sleep` on Mac, and 0.1% to 0.2% on iPhone | Released, because Rubicon uses [`CDLL`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/runtime.py#L96), which Python documents as releasing it (**Source**). 98% to 101% on Mac, and 90% to 119% on iPhone |
| TH2, calls from background threads | Pass, including 40,000 concurrent calls, with M2 results unchanged | Pass, with M2 results unchanged |
| TH3, delegate on a GCD queue or `pthread` | Pass | Pass |
| TH3, call waiting on a callback from another thread | Hang, because the waiting call holds the GIL the callback needs. On iPhone, iOS kills the app at 20 seconds | Pass |
| TH4, main thread and event loops (**Source**) | Nothing in the code or docs | [`RubiconEventLoop`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/eventloop.py#L821) runs `asyncio` on the run loop, with [Cocoa](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/eventloop.py#L840) and [iOS](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/eventloop.py#L870) lifecycles. Other threads reach it through `asyncio`'s [`call_soon_threadsafe`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/eventloop.py#L587) |
| TH5, free-threaded Python 3.14 on Mac | Builds and imports, and [the import re-enables the GIL](../results/section-02/2026-11-04/raw/th5_gil_status.json) with a warning. TH2 and TH3 match the normal build, including the hang | GIL stays disabled. TH2 and TH3 pass |

TH5 passing doesn't show that Rubicon is safe without the GIL. These are a few scenarios, and it doesn't declare support.

### CB. Callbacks

**CB1, implementation (Source):**

| Type | pyobjus | Rubicon |
|---|---|---|
| Delegate | A class made at runtime, using [`forwardInvocation:`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L895) to reach Python | A Python class with [`objc_method`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L389) and protocols |
| Python subclass | No public API | [The same, added to the class](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/runtime.py#L1115) as a `ctypes` callback |
| Block created in Python | No public API | [`Block`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L2346) builds a block literal in `ctypes`, and [keeps it alive](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L2357) until Objective-C disposes of it |
| Block received | [Raises an assertion error](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L297) when a method returns one. A delegate gets an object with no public way to call it | [`ObjCBlock`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L2214) reads [the block's signature](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L2255) and calls it |
| Function pointer | No public way to pass one | A plain `ctypes` `CFUNCTYPE`, which Rubicon doesn't manage |

**CB2, round trips through a callback:**

| Value | pyobjus delegate | Rubicon delegate and subclass | Rubicon block | Rubicon function pointer |
|---|---|---|---|---|
| Integer, double, object | Pass. Wrong value on 1.2.4 | Pass | Pass | Pass |
| Struct as an argument | [Passed as `None`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L959) | Pass | Pass | Pass |
| Struct returned | [Zeros, because struct returns are unsupported](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L940). On 1.2.4, a crash on Mac and an exception on iPhone | Pass | `TypeError` | `TypeError` |

Python-defined methods can return structs because [`add_method` applies `ctypes_patch`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/runtime.py#L1145). [`Block`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L2426) doesn't. A manual trial of that helper on a block and a function pointer worked, but it's undocumented and isn't a published test.

**CB3, when Python code raises in a callback:** nothing reaches the Objective-C caller as an exception. On the Mac the traceback is printed in every case. On the iPhone Python's error output isn't captured, so this wasn't checked.

| Type | pyobjus | Rubicon on Mac | Rubicon on iPhone |
|---|---|---|---|
| Delegate | [Zero, by design](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L999). On 1.2.4, the next call raises `SystemError` | Zero | A different large value each run |
| Python subclass | Not expressible | Zero | A different large value each run |
| Block | Not expressible | A large value, the same every run for a build | 2, every run |
| Function pointer | Not expressible | A large value, the same every run for a build | 2, every run |

The values on Rubicon suggest that the return value is never set (**Inferred**), so the Mac's zero may be chance.

**CB4, after Python drops its reference:** delegates, subclasses and blocks kept working on both libraries where they can be written. A Rubicon function pointer crashes (`SIGSEGV`), which follows the rule in [Python's `ctypes` docs](https://docs.python.org/3/library/ctypes.html#callback-functions) that a caller must keep a reference for as long as C uses it.

**CB5, blocks:**

| Scenario | pyobjus | Rubicon |
|---|---|---|
| (a) Create, pass and call | Not expressible | Pass |
| (a) Python function freed after Objective-C drops the block | Not expressible | Pass |
| (b) Receive and call: integer, double, object, struct | `AssertionError` | Pass |
| (b) Call later, a heap block | Not expressible | Pass |
| (b) Call later, a stack block | Not expressible | Crash: `SIGSEGV` on Mac, `SIGKILL` on iPhone, at a stack address |
| (b) The received block throws an Objective-C exception | `AssertionError`, before it can be called | Crash, `SIGABRT` |

In Objective-C, a callee that keeps a stack block has to copy it first, so this scenario may be rare in practice.

### Reading claim 6

The examples behind this claim weren't provided, so this section can't test it directly. These results bear on it:

- **Limits of `ctypes` seen here:** a callback can't return a struct without Rubicon's patch, a Python exception can't cross a callback, and [rubicon-objc#73](https://github.com/beeware/rubicon-objc/issues/73), still open, says Objective-C exceptions need a small C helper.
- **An Objective-C exception isn't specific to `ctypes`:** pyobjus, which is compiled, also crashes, because it doesn't catch them. PyObjC, also compiled, raises a Python exception.
- **Lifetime crashes in Rubicon:** a dropped function pointer is the `ctypes` rule above. Whether the stack block crash comes from `ctypes` isn't shown, since `_Block_copy` is an ordinary C function (**Inferred**).
- **Lifetime results in Rubicon:** it freed every object in M2 and M4 apart from the cycle, with no over-release.

### PyObjC control

PyObjC 13.0 is a control, not a third option, and a result here isn't proof about the other two. On the Mac, it passed every scenario except these, which also failed on both libraries: the cycle and the main-thread loop with no pool weren't freed, and the deliberate extra `release` crashed (`SIGABRT`). Objective-C exceptions became Python exceptions, and Python exceptions in callbacks reached the caller. So the failures unique to one library aren't caused by the fixture. In T5, it got 66 correct, and raised 7 exceptions on function pointers it has no metadata for.

### iPhone and Mac differences

82 scenarios ran 5 times on 4 builds on the iPhone, for 1,640 runs, and only these gave a different outcome from the Mac at the same version:

| Scenario | Build | iPhone | Mac |
|---|---|---|---|
| Exception in a delegate or subclass | Rubicon | A different large value each run | Zero |
| Stack block after it goes out of scope | Rubicon | Crash, `SIGKILL` | Crash, `SIGSEGV` |
| `CGRect` round trip | pyobjus 1.2.4 | Crash, 1 of 5 | Crash, 3 of 5 |
| Struct passed to a delegate | pyobjus 1.2.4 | Python exception | Crash |

### Limits

- **The fixture isn't an app.** It shows how each library behaves in a scenario, not how often that scenario arises. Objects not being freed doesn't show that a real app is affected, or by how much.
- **The test app isn't a Kivy app.** On the iPhone, Python runs on the main thread with no run loop, as it does on the Mac, using KivyForge's [smoke-test path](https://github.com/ElliotGarbus/kivyforge/blob/a36c2cccb7bb3dbd3bc33c89ba90587f1d0fa7db/kivyforge/platforms/ios/templates/kivyforge_bootstrap.m). pyobjus's Python 3.15 iOS wheels were built for this comparison at the tested commits, so they aren't published artifacts.
- **The tests come from one source and haven't been reviewed by either project.** They were corrected during trial runs, and each fix is [logged](../results/section-02/2026-11-04/README.md#test-fixes-during-trial-runs). A test written around one library's working form can favor it. Anyone can propose a scenario, and it will run against both.
- **"Not expressible" means no public way was found.** Section 3 will cover those gaps. A maintainer who knows of a way can correct the result.
