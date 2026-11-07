# 3. Capabilities and limitations

**Status: draft for factual review.** Neither project has reviewed this section. Versions are in [the baseline](../results/baseline/2026-11-04.md). Metric IDs refer to the [approved definitions](../metrics/03-capabilities.md), which also list every change made after approval.

## Summary of findings

The libraries differ most in callbacks. Rubicon can create blocks, call blocks it receives, pass function pointers and subclass Objective-C classes. pyobjus can do none of these, so an API that takes a completion handler needs Objective-C helper code compiled into the app. About 1,500 macOS and 1,900 iOS methods and properties take or return a block. Apple's Matter smart-home framework has another 10,341, almost all methods that take a block, such as a completion or report handler, counted separately because its generated device APIs would otherwise dominate the total.

That gap, with no API for C functions or constants, sets how much of Apple's API each can reach. Matching the SDK headers to these results, pyobjus `master` can express about half of the public API to call that the cases cover, 50% on macOS and 56% on iOS. Rubicon can express all of it, 100% on macOS and 100% on iOS (**Inferred**).

Both call methods and properties, implement protocols, and reach Swift through `@objc` classes. Neither catches Objective-C exceptions or calls APIs that exist only in Swift. Within what it supports, pyobjus gave wrong results for arguments written inline and for integers passed to a variadic method. Rubicon converts booleans in collections to `1` and `0`, though its docs say `bool`.

All figures are **Measured** unless labeled otherwise, using a test fixture, not a real app. This section makes no recommendation. "`master`" and "`main`" mean the default branches. Results are from 84 cases for each library, plus 5 workarounds for pyobjus, each run 5 times on a Mac and an iPhone. Every case gave the same outcome in all 5 runs, and the same outcome on both platforms unless stated.

| Topic | pyobjus `master` | Rubicon |
|---|---|---|
| Calling methods and properties, loading frameworks | Supported, but arguments created inline, such as `objc_str("x")`, can give a wrong result | Supported |
| Methods that take a variable number of arguments, such as `stringWithFormat:` | Objects only. A number arrived as a different number | Supported, through `send_message` |
| C functions (such as `NSStringFromClass`) and global constants (such as `NSLocaleCountryCode`) | No API for either. Its `symbol()` function for constants isn't documented and raised an exception | Supported: functions through `ctypes` and constants through `objc_const`, as its docs show |
| C structs (such as `CGRect`), unions and bit fields | Structs. Not unions passed as arguments, or bit fields | All three, once the union and bit-field types are registered |
| C arrays, and out parameters (values a method writes back, such as an `NSError`) | Fixed-size arrays and numbers written back. Not arrays passed by pointer, or `NSError`s | All |
| Converting Objective-C values to Python, such as an `NSArray` to a `list` | No API for it | Supported, but `YES` and `NO` inside a collection become `1` and `0`, though its docs say they become `bool` |
| Python operations on Foundation collections: `len()`, indexing, iteration | Not supported | Supported |
| Defining Objective-C classes in Python: subclasses, class methods, properties | Not supported. A delegate can supply instance methods | Supported |
| Delegates: Python objects that implement an Objective-C protocol | Supported, but struct and array arguments arrive as `None`, and a union argument crashed | Supported |
| Blocks (such as completion handlers) and C function pointers | Not supported. Workarounds need Objective-C or `ctypes` | Supported |
| Running `asyncio` on the app's event loop | Not supported | Supported |
| Calling Swift code marked `@objc` | Supported, except reading a throwing method's error and calling `async` methods | Supported, except a `Bool` inside a dictionary becomes `1` or `0` instead of `True` or `False` |
| Share of Apple's public API to call that the cases cover, macOS (**Inferred**) | 50% | 100% |
| Share of Apple's public API to call that the cases cover, iOS (**Inferred**) | 56% | 100% |

1. **Calling Objective-C:** both libraries call methods and properties and load frameworks and dylibs. pyobjus returned `"+"` instead of `"a+b"` when `stringByReplacingOccurrencesOfString:withString:` was called with `objc_str(...)` written inline, as its docs do, and the right value when the arguments were held in variables first. An integer passed to `stringWithFormat:` arrived as a different number in pyobjus. pyobjus has no API for C functions, and its `symbol()` function for constants, which isn't in its docs, raised `TypeError` inside pyobjus. Rubicon calls C functions and reads constants through `ctypes`, as its C functions guide shows.
2. **Types:** pyobjus passed structs, fixed-size arrays and scalar out parameters. It raised an exception for unions passed in, bit fields, pointers to arrays and structs holding arrays, and can pass only nil for an `NSError **`. On the iPhone, a struct that Objective-C fills through a pointer came back as zeros in pyobjus, in both versions. Rubicon passed every type case once the union and bit-field types were registered with `register_encoding`.
3. **Python behavior:** pyobjus raised `TypeError` for `len()`, indexing, iteration and `in` on Foundation collections, and has no conversion from Objective-C to Python. Rubicon supports these, but converts `@YES` in a collection to `1`, though its docs say a boolean becomes `bool`, and indexing an `NSDictionary` returned an `NSNumber`.
4. **Defining Objective-C in Python:** pyobjus has no API for subclassing, so it can't override an Apple class's method or call `super`, define a class method, or declare a property Objective-C can read. A delegate can supply instance methods if their encodings are registered at runtime, which its docs don't describe. Both implement Apple's protocols and the app's own. pyobjus delegates receive struct and array arguments as `None`, as its docs say, and a union argument crashed. Rubicon handled every case.
5. **Blocks and function pointers:** pyobjus can't create a block, call a block it receives, or pass a function pointer. A completion handler worked through an Objective-C helper that calls a delegate, and a function pointer through calling `objc_msgSend` with `ctypes`. Rubicon handled each case, including Grand Central Dispatch.
6. **Swift:** both found Swift classes by their `@objc` names and by Swift's generated names, passed Swift values, and implemented Swift protocols, including on a thread Swift created. pyobjus can't read the `NSError` from a throwing method or call an `async` method. Rubicon handled each case, apart from a `Bool` in a dictionary, which becomes `1` or `0` instead of `True` or `False`.
7. **Reach into Apple's API (Inferred):** of the 71,874 public declarations to call on macOS that the cases cover, pyobjus `master` can express 36,167 to 36,369 (50.3% to 50.6%) and Rubicon all of them. On iOS it's 33,988 to 34,108 of 60,385 (56.3% to 56.5%), and all 60,385. Left out for both are inline functions (494 on macOS, 397 on iOS) and declarations needing a kind no case tested (1,562 and 673). Matter, a smart-home framework, makes up about a fifth of macOS's declarations and a quarter of iOS's, and most of its methods take blocks.
8. **Versions:** pyobjus 1.2.4 doesn't return delegate methods' values to Objective-C, swaps a `dict` argument's keys and values, and crashed when a Swift delegate raised. `master` fixes all three, through changes by this comparison's author. Rubicon 0.5.7 and `main` matched in every case.

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Relevant data |
|---|---|
| 8. Each library can do things the other can't | pyobjus: `dir()` lists an object's methods (F1.7), it ships two enums (F2.7), and `make_dylib` compiles a dylib from Python (**Source**, not tested). Rubicon: every row in the summary table where pyobjus is "not supported". No outside rows had been proposed when this was written. |
| 9. pyobjus can't create blocks, so APIs with completion handlers need Objective-C helper code | Confirmed (F4.1). An Objective-C helper worked as the workaround. Of the macOS methods and properties to call, 11,824 take or return a block, 10,341 of them in Matter. On iOS it's 12,193, again 10,341 in Matter. Delegates also can't call a block they receive (F4.2), which 381 macOS and 692 iOS protocol methods pass. |
| 10. pyobjus can't subclass Objective-C classes from Python | Confirmed: no subclass API, no class methods and no overriding with `super` (F3.1, F3.2). A delegate can supply instance methods to Objective-C, using encodings registered at runtime. |
| 11. pyobjus delegates can register protocols at runtime, but can't pass struct, union or array values | Confirmed. A protocol registered at runtime worked (F3.5). Struct arguments arrive as `None` (Section 2), an array arrived as `None` and Objective-C read `0`, and a union argument crashed (F3.7). pyobjus's [docs](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L718) say so. |

## Supporting facts

Raw results, test fixes and rerun steps are in [`results/section-03/2026-11-07`](../results/section-03/2026-11-07/README.md) and [`tests/section-03`](../tests/section-03/README.md). The Mac is on Python 3.14 and macOS 26.6.2. The iPhone is on Python 3.15 and iOS 27.0.1. Rubicon 0.5.7 and `main` gave the same result in every case, so "Rubicon" means both. Where pyobjus 1.2.4 differs from `master`, the table says so. PyObjC 13.0 ran as a control on the Mac, and is [reported separately](#pyobjc-control).

Each cell gives the result and whether the library's docs describe the feature, at the pinned commits. The case IDs are in [`tests/section-03/cases.py`](../tests/section-03/cases.py). "Undocumented" means it worked but the docs don't describe it.

### F1. Calling Objective-C and C

| Row | pyobjus `master` | Rubicon |
|---|---|---|
| F1.1 Classes and methods | Supported, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/pyobjus_internal.rst#L82). Temporary `objc_str(...)` arguments gave `"+"` for `"a+b"`, and the same call with the arguments in variables was correct | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/type-mapping.md#L57) |
| F1.2 Properties | Supported, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/pyobjus_internal.rst#L172) | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/type-mapping.md#L57) |
| F1.3 Variadic methods | Object arguments only, as [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L765). `%ld` with `7` gave a different number | Supported through [`send_message`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/runtime.py#L866) with `varargs`, documented in its reference |
| F1.4 Global constants | [`symbol()`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus.pyx#L1276), undocumented, raised `TypeError: 'NSString' object is not callable` inside pyobjus. Scalars: workaround with `ctypes` | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/c-functions.md#L144): `objc_const` for objects, `ctypes` for scalars |
| F1.5 C functions | Workaround with `ctypes`. No API. Objects can go in through `get_address()`, which is undocumented, but a returned object can't be turned back into a pyobjus object, so the workaround makes its Objective-C calls through `ctypes` too | Supported through `ctypes`, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/c-functions.md#L11), with types declared by hand. Inline functions must be [rewritten in Python](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/c-functions.md#L100) |
| F1.6 Loading code | Supported, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/api.rst#L327), including `make_dylib` to compile one (not tested) | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-runtime.md#L11) |
| F1.7 Introspection | Supported, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/pyobjus_internal.rst#L118) | `dir()` didn't list `host`, and the docs describe no other way |

The F1.6 case loads the first of five frameworks not already loaded. That was CoreLocation on the Mac and EventKit on the iPhone, which loads CoreLocation and Contacts at launch.

### F2. Types

| Row | pyobjus `master` | Rubicon |
|---|---|---|
| F2.1 Structs | Supported, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L221), including a struct the user defines and [pointers](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L280). On the iPhone, a struct filled through a pointer came back as zeros. 1.2.4 raised for the user's struct | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-types.md#L93), with the user's struct registered by `register_encoding` |
| F2.2 Unions and bit fields | Not supported for unions passed in or bit fields, as [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/remarks.rst#L6). A returned union worked at `master` | Undocumented: worked with the `ctypes` types registered by `register_encoding` |
| F2.3 C arrays | Fixed-size array arguments only, as [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L784). An `int *` with a count, an array to fill and a struct holding an array raised | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-types.md#L186) |
| F2.4 Out parameters | Scalar and opaque pointers, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L280). Only nil for `NSError **` | Undocumented: worked with `byref`. [rubicon-objc#3](https://github.com/beeware/rubicon-objc/issues/3) asks for docs |
| F2.5 Collections | Python `list` and `dict` arguments convert, and [`objc_arr`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/api.rst#L128) builds one. No conversion from Objective-C. 1.2.4 swapped a `dict`'s keys and values | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/type-mapping.md#L299). `py_from_ns` gave `[1, 0, 1]` for `@[@YES, @NO, @1]`, though [its docs](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/src/rubicon/objc/api.py#L1785) say a boolean becomes `bool`. It checks for the type code `B`, and Apple's boolean numbers report `c` (**Source**) |
| F2.6 Python behavior | Not supported: `len()`, indexing, iteration, `in` and `upper()` raised | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/type-mapping.md#L107). `mapping["two"]` returned an `NSNumber`, not `2` |
| F2.7 Enums | Two enums ship, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L728). Adding one means rebuilding pyobjus | None ship. Python constants are used instead |

The pyobjus F2.1 difference on the iPhone was the same in all 5 runs and in both versions. pyobjus's docs say the pointer it passes points to the value given, so Objective-C's write would be expected to show, as it did on the Mac.

### F3. Defining Objective-C behavior in Python

| Row | pyobjus `master` | Rubicon |
|---|---|---|
| F3.1 New class | No API. A delegate supplied an instance method once its encoding was registered at runtime, which is undocumented. No class methods. 1.2.4 didn't return the value | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-api.md#L70) |
| F3.2 Subclass an Apple class | Not supported | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-api.md#L70), with [`send_super`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-runtime.md#L59) |
| F3.3 Instance state | Python attributes. No properties Objective-C can read | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-api.md#L146) |
| F3.4 Apple protocol | Supported, [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L680) | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/protocols.md#L24) |
| F3.5 Protocol not known in advance | Supported: found by name at runtime, and through encodings registered at runtime. The docs describe a [table rebuilt with pyobjus](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L695), not runtime registration | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/protocols.md#L72) |
| F3.6 Selector targets | Supported, through encodings registered at runtime | Supported |
| F3.7 Delegate values | Objects, integers and `BOOL` returns. An array arrived as `None`, and a union argument crashed, as [documented](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L710). 1.2.4 returned nothing to Objective-C | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-api.md#L134) |
| F3.8 Removing a delegate | No API. Section 2 found no delegate freed | Automatic. Section 2 found all freed |

### F4. Blocks and function pointers

| Row | pyobjus `master` | Rubicon |
|---|---|---|
| F4.1 Completion handlers | Workaround with an Objective-C helper. The docs [say so](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/pyobjus_ios.rst#L168) | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-api.md#L164) |
| F4.2 Received blocks | Not supported: the block arrived as an `__NSStackBlock__` with no way to call it | Supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-api.md#L212) |
| F4.3 GCD | Not supported | Supported, following its [C functions guide](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/c-functions.md#L206) |
| F4.4 Function pointers | Workaround with `ctypes`, calling `objc_msgSend` directly | Undocumented: worked with a `ctypes` function type. The docs mention function pointers only as an [unknown pointer type](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-types.md#L158) |

### F5 and F6. Runtime services and platforms

| Row | pyobjus `master` | Rubicon |
|---|---|---|
| F5.1 Memory management | Not automatic for `alloc`, `new` or `copy`, and the docs don't describe it (Section 2) | Automatic, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/memory-management.md#L7) (Section 2) |
| F5.2 Objective-C exceptions | Crash (Section 2), though an [`ObjcException`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/api.rst#L256) class is documented | Crash (Section 2). [rubicon-objc#73](https://github.com/beeware/rubicon-objc/issues/73) is open |
| F5.3 Event loops | Not supported | Core Foundation run loop supported, [documented](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/async.md#L7). `NSApplication` and `UIApplication` documented, not tested |
| F5.4 Main thread | No API. Reached through a timer added to the main run loop | No API. Reached through `performSelectorOnMainThread:` |
| F6.1 Platforms (**Source**) | Classifiers name macOS and iOS. 1.2.4 has wheels for macOS on Python 3.10 to 3.14, and for iOS on 3.13 and 3.14 | No operating system classifier. One `py3-none-any` wheel, and docs for AppKit and UIKit apps |

pyobjus's F5.4 route differs because pyobjus gives no handle on the Objective-C object behind a delegate, so `performSelectorOnMainThread:` can't be sent to it.

### F7. Swift

Both libraries call Swift through `@objc` classes. Neither library's docs mention Swift.

| Row | pyobjus `master` | Rubicon |
|---|---|---|
| F7.1 Finding Swift classes | Supported, by `@objc` name and generated name | Supported |
| F7.2 Swift values | Supported, read with the test's own converter, since pyobjus has none. 1.2.4 swapped a `dict`'s keys and values | Supported, except a `Bool` in a dictionary, which `py_from_ns` converts to `1` or `0` instead of `True` or `False`, for the same reason as in F2.5. The test's `false` came back as `0` |
| F7.3 Throwing methods | The value, and `None` on failure. The `NSError` can't be read | Supported |
| F7.4 `async` methods | Not supported | Supported, including the two-argument handler |
| F7.5 Swift protocols in Python | Supported, including returns and a background thread. 1.2.4 returned nothing to Swift and crashed when the method raised | Supported |
| F7.6 Swift-only APIs (**Source**) | No route | No route. [rubicon-objc#563](https://github.com/beeware/rubicon-objc/issues/563) asks for one |

### A. Reach into Apple's API (Inferred)

Every public Objective-C declaration in the macOS 27.0 and iOS 27.0 SDK headers was classified by the kinds of value it needs, leaving out anything the tested systems (macOS 26.6.2, iOS 27.0.1) don't have. Each kind was then matched to the cases above, and to Section 2's for scalars, C strings and built-in structs. A declaration counts as expressible only if every kind it needs passed in all runs. The [script](../tests/section-03/reach.py) lists which cases decide each kind. Where a range is given, a header's pointer to a scalar could be one value or an array, or a variadic method could take objects or numbers.

Shares are of the declarations the cases cover. Two groups are counted separately, and are the same for both libraries:

- **Inline functions,** such as `NSMakeRange`, have no symbol to call, so a library or the app has to rewrite them in Python. Rubicon ships Python versions of 8, such as `CGRectMake`.
- **Untested kinds:** declarations that need a kind of value no case tested, mostly pointers to pointers and SIMD vectors, aren't counted as expressible or not.

| Declarations to call | macOS | iOS |
|---|---:|---:|
| Public declarations | 73,930 | 61,455 |
| Inline functions, counted separately | 494 | 397 |
| Untested kinds, counted separately | 1,562 | 673 |
| **Covered by the cases** | **71,874** | **60,385** |

**To call, of the declarations covered:**

| Declarations | macOS covered | macOS: pyobjus `master` | macOS: Rubicon | iOS covered | iOS: pyobjus `master` | iOS: Rubicon |
|---|---:|---|---|---:|---|---|
| Methods | 29,526 | 16,575 to 16,769 (56.1% to 56.8%) | 29,526 (100%) | 26,727 | 13,745 to 13,861 (51.4% to 51.9%) | 26,727 (100%) |
| Properties | 19,814 | 19,592 to 19,600 (98.9%) | 19,814 (100%) | 20,561 | 20,243 to 20,247 (98.5%) | 20,561 (100%) |
| C functions | 10,150 | 0 | 10,150 (100%) | 3,691 | 0 | 3,691 (100%) |
| Constants | 12,384 | 0 | 12,384 (100%) | 9,406 | 0 | 9,406 (100%) |
| All | 71,874 | 36,167 to 36,369 (50.3% to 50.6%) | 71,874 (100%) | 60,385 | 33,988 to 34,108 (56.3% to 56.5%) | 60,385 (100%) |

**To implement**, meaning protocol methods the app writes: the cases cover 4,169 of 4,439 on macOS and 4,678 of 4,907 on iOS. Of those, pyobjus `master` can express 3,423 (82.1%) on macOS and 3,651 (78.0%) on iOS, and Rubicon all of them. pyobjus 1.2.4 can express 86 (2.1%) and 101 (2.2%), because it returns nothing to Objective-C.

**By framework, to call, of the declarations covered:**

| Framework | Covered | pyobjus `master` | Rubicon |
|---|---:|---|---|
| macOS Foundation | 5,058 | 3,691 to 3,765 (73.0% to 74.4%) | 5,058 |
| macOS AppKit | 7,987 | 6,183 to 6,251 (77.4% to 78.3%) | 7,987 |
| macOS AVFoundation | 3,116 | 1,925 to 1,929 (61.8% to 61.9%) | 3,116 |
| macOS CoreBluetooth | 121 | 86 (71.1%) | 121 |
| macOS CoreLocation | 182 | 165 (90.7%) | 182 |
| macOS StoreKit | 123 | 95 (77.2%) | 123 |
| macOS UserNotifications | 118 | 101 (85.6%) | 118 |
| iOS UIKit | 6,005 | 4,965 to 4,982 (82.7% to 83.0%) | 6,005 |
| iOS Foundation | 4,042 | 2,931 to 3,001 (72.5% to 74.2%) | 4,042 |
| iOS AVFoundation | 3,511 | 2,247 to 2,249 (64.0% to 64.1%) | 3,511 |
| iOS CoreBluetooth | 134 | 94 (70.1%) | 134 |
| iOS CoreLocation | 208 | 186 (89.4%) | 208 |
| iOS Photos | 329 | 278 (84.5%) | 329 |
| iOS StoreKit | 198 | 139 (70.2%) | 198 |
| iOS UserNotifications | 125 | 108 (86.4%) | 125 |

- **Matter:** this smart-home framework has 15,804 macOS and 15,806 iOS declarations to call, a fifth and a quarter of the totals, and 10,341 of its methods take a block.
- **Left out:** DriverKit, Kernel and Tk on macOS, whose headers clang couldn't parse as an app does.
- **Cross-check (A3, Source):** of 48,509 declarations in both the macOS headers and BridgeSupport, 38 disagreed: 36 in Tk, which is left out, and 2 in a Tcl function whose callback BridgeSupport types but doesn't mark.
- **Swift-only frameworks (A4, Source):** 46 on macOS and 54 on iOS have a Swift interface and no Objective-C headers, not counting 47 and 53 underscore-prefixed overlay modules. 99 macOS and 124 iOS frameworks have both.

**Limits of A:** these counts show what can be written, not what apps use. Each kind rests on one to five cases, so one failing case moves thousands of declarations: all of pyobjus's constants are counted as not expressible because of F1.4. Rubicon's 100% means every kind it needs passed its cases, not that every declaration works. The counts read declared types and don't call anything.

### L. Stated limits and open gaps

**L1, documented limits (Source):**

| pyobjus | Rubicon |
|---|---|
| [Bit fields and unions by value](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/remarks.rst#L6) aren't supported, a libffi restriction | [C functions](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/c-functions.md#L45) need their types declared by hand |
| Delegates return [only some types](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L710), and receive struct, union and array arguments as `None` | [Inline functions](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/c-functions.md#L100) must be rewritten in Python |
| Protocols missing from its table need [a rebuild](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L695), and so do [new enums](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/core_tutorials.rst#L762) | [`NSString`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/topics/type-mapping.md#L166) can't be a `dict` key, and handles characters above `U+FFFF` differently from `str` |
| Handlers can't be [written in pyobjus](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/pyobjus_ios.rst#L168), so the example uses an Objective-C bridge class | Method types come from [annotations](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/reference/rubicon-objc-api.md#L134), and default to objects |

**L2, open capability issues (Reported):** at Section 1's snapshot, pyobjus had 17 open issues and Rubicon 18. Issues that report a missing or faulty feature are matched to rows below. The rest are a dependency dashboard, documentation, design proposals and test coverage. 16 of pyobjus's 17 open issues were filed by this comparison's author.

| Row | pyobjus | Rubicon |
|---|---|---|
| F1.1 | [#198](https://github.com/kivy/pyobjus/issues/198), [#206](https://github.com/kivy/pyobjus/issues/206), [#213](https://github.com/kivy/pyobjus/issues/213) | [#221](https://github.com/beeware/rubicon-objc/issues/221), [#333](https://github.com/beeware/rubicon-objc/issues/333) |
| F1.2 | [#191](https://github.com/kivy/pyobjus/issues/191) | [#96](https://github.com/beeware/rubicon-objc/issues/96) |
| F1.3 | [#195](https://github.com/kivy/pyobjus/issues/195) | |
| F2.1 to F2.3 | [#200](https://github.com/kivy/pyobjus/issues/200), [#201](https://github.com/kivy/pyobjus/issues/201) | |
| F2.5, F2.6 | [#192](https://github.com/kivy/pyobjus/issues/192), [#207](https://github.com/kivy/pyobjus/issues/207), [#212](https://github.com/kivy/pyobjus/issues/212) | [#71](https://github.com/beeware/rubicon-objc/issues/71) |
| F3.4, F3.5 | [#203](https://github.com/kivy/pyobjus/issues/203) | [#69](https://github.com/beeware/rubicon-objc/issues/69), [#94](https://github.com/beeware/rubicon-objc/issues/94) |
| F3.7 | [#202](https://github.com/kivy/pyobjus/issues/202) | |
| F5.1 | [#176](https://github.com/kivy/pyobjus/issues/176), [#194](https://github.com/kivy/pyobjus/issues/194) | |
| F5.2 | [#196](https://github.com/kivy/pyobjus/issues/196) | [#73](https://github.com/beeware/rubicon-objc/issues/73) |
| F5.3 | | [#206](https://github.com/beeware/rubicon-objc/issues/206), [#445](https://github.com/beeware/rubicon-objc/issues/445), [#846](https://github.com/beeware/rubicon-objc/issues/846) |
| F6.1 | | [#176](https://github.com/beeware/rubicon-objc/issues/176) (GNUstep), [#406](https://github.com/beeware/rubicon-objc/issues/406) (PyPy) |
| F7.6 | | [#563](https://github.com/beeware/rubicon-objc/issues/563) |

Rubicon's #221 is a user's report that hasn't been confirmed. No open pyobjus issue reports the wrong result with temporary arguments. #195 reports the variadic integers.

### PyObjC control

PyObjC 13.0 got 74 of 84 cases right on the Mac. It raised for unions and bit fields, as pyobjus did, and for a delegate receiving a union or an array without metadata. When a Swift delegate method raised, PyObjC passed the exception back through Swift, which stopped the loop after the first tick. 3 cases weren't applicable. A control result isn't evidence about either library's design.

### Limits of this section

- The cases use a fixture, not a real app, and one or a few cases per row.
- A result shows that the case worked, not that every use of the feature works.
- Docs were checked at the pinned commits. A feature described elsewhere, such as in an issue, counts as undocumented.
- Swift was tested only through `@objc` classes, which is the only route either library has.
