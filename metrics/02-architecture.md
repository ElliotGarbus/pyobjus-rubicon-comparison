# Section 2 metric definitions

**Status: approved 2026-11-04.** These definitions were written before the Section 2 data was collected. Changes made after that are recorded at the end of this document with their reasons.

Section 2 explains how each library works and how that design behaves. It answers what happens, not which design is better. Speed and memory amounts belong to Section 6, and the list of features belongs to Section 3.

## What was seen before these were written

| Seen before writing (2026-11-04) | Where | Effect on the rules |
|---|---|---|
| The author wrote pyobjus fixes, including memory fixes, and has said publicly that pyobjus has significant memory management issues | [kivy/kivy#9469](https://github.com/kivy/kivy/issues/9469), Section 1 | pyobjus is tested at its release and its default branch, so those fixes are credited, and scenarios are fixed before any results |
| `ctypes` is said to make some memory-safe behavior impossible, and `delegate_register` is said to leak | Claims 6 and 7 | Both are tested directly |
| Automatic retain and release were added to Rubicon, but the documentation lagged | [rubicon-objc#48](https://github.com/beeware/rubicon-objc/issues/48) | Tests cover documented use and use with no manual memory calls |
| Objective-C exceptions are described as hard to handle using only `ctypes` | [rubicon-objc#73](https://github.com/beeware/rubicon-objc/issues/73) | Objective-C exceptions are a scenario for both libraries |
| Python exceptions in `ctypes` callbacks are printed rather than propagated | [rubicon-objc#137](https://github.com/beeware/rubicon-objc/issues/137) | Exceptions in callbacks are a scenario for both libraries |
| A struct return raised `KeyError` in pyobjus, and a method called from Objective-C crashed in Rubicon on Python 3.9 | [pyobjus#70](https://github.com/kivy/pyobjus/issues/70), [rubicon-objc#223](https://github.com/beeware/rubicon-objc/issues/223) | Struct handling and calls from Objective-C are scenarios for both libraries |
| A search of both repositories found no code that reads BridgeSupport files. The only mention is a commented-out path in pyobjus's quickstart docs | Section 1's pinned commits | T5 uses this metadata as a reference that neither library depends on |
| macOS has BridgeSupport files for 249 frameworks and none for UIKit. A trial generated UIKit metadata from the iOS 27.0 SDK headers, and the generator logged merged signatures | This Mac, 2026-11-04. No library was run | T5 uses the macOS files Apple ships, and doesn't use generated metadata |

The AI assistant read build files for Section 1 but hasn't read either library's architecture code for this section. The author has worked in pyobjus's source.

## Scope and common rules

- **Versions:** the latest PyPI release and the default branch of each library, each at a pinned commit. One baseline, set when collection starts, covers Sections 2 to 6. A result is shown once if both points match, and separately if they differ.
- **Evidence:** design facts are **Source**, linked to pinned lines of code or docs. Behavior is **Measured**, using a published test.
- **Platforms:** Apple Silicon Mac on Python 3.14, using each library's PyPI wheel at the release point and a source build at the default branch. iPhone on Python 3.15, using the build route in [METHODOLOGY.md](../METHODOLOGY.md). Compiler, Cython and OS versions are recorded.
- **Same test for both:** each scenario runs against both libraries, using a shared Objective-C test fixture that counts object deallocations and can call back from other threads. Tests live in `tests/section-02/`.
- **PyObjC control:** on the Mac, each scenario also runs against PyObjC 13.0, using its PyPI wheels. Control results are reported separately and PyObjC isn't compared or scored. They help separate a library's limit from a faulty test: if a scenario fails on all three, the test or its expected result is reviewed first. A control result isn't proof about the design of either library. PyObjC isn't tested on iPhone, because it has no iOS support to test.
- **Scenario sources:** scenarios may draw on the test suites of [PyObjC](https://github.com/ronaldoussoren/pyobjc/tree/main/pyobjc-core/PyObjCTest) and [Apple's objc4](https://github.com/apple-oss-distributions/objc4/tree/main/test). Each scenario taken from them links to its source at a pinned commit. Their test code isn't copied or run as a score.
- **Documented use:** tests use public APIs as each library documents them. Memory scenarios also run with no manual memory calls, and the two results are labeled separately.
- **Results:** each scenario runs 5 times, each in its own process, so a crash is recorded and doesn't stop the run. Each result is the outcome and its count, such as "crash, 2 of 5", with the raw output saved.
- **Can't be expressed:** if a library has no public way to write a scenario, the result is "not expressible", with a link to its Section 3 entry. This isn't counted as a failure here.
- **Test fixes:** a test can be corrected after a run if the test itself was wrong. The change and the earlier result are recorded.
- **Outside scenarios:** anyone can propose a scenario with code, and it runs against both libraries. Results are published even if they favor neither or contradict the author's view.
- **No scoring:** metrics are never combined or weighted, and no design is labeled safer or better.

## D. Design

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| D1 | Binding mechanism | How a Python call reaches the Objective-C runtime, traced for one instance method call, and how the method is found and invoked | Code at pin | Source |
| D2 | Compiled parts and native dependencies | What each library compiles, what it needs at build time and at runtime, and what ships in each artifact | Code, build files, wheels | Source |
| D3 | Reliance on Python internals | Whether a library depends on the CPython C API or ABI, or needs a build per Python version, and which interpreter features it declares support for | Code, build files | Source |

## T. Type handling

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| T1 | Source of type information | Where argument and return types come from: runtime encodings, declarations in Python, or built-in tables | Code at pin | Source |
| T2 | Conversions | Round trip through the fixture for `int`, `float`, `bool`, `str`, `bytes`, `None`, `list`, `dict`, a class, a selector and a pointer: the Python value returned, and any error | Tests | Measured |
| T3 | Structs | How struct layouts are found, and a round trip of `CGRect`, `NSRange`, `UIEdgeInsets` and a nested struct, passed and returned | Code, tests | Source, Measured |
| T4 | Wrong use | The result of an unknown selector, wrong argument type, wrong argument count and an Objective-C exception: Python exception, wrong value, or process crash | Tests | Measured |
| T5 | Apple API sample | Handling of a sample of Apple's API taken from BridgeSupport metadata, on macOS. Rules below | BridgeSupport, tests | Measured |

**T5 metadata:** BridgeSupport is Apple's XML description of framework APIs, documented in the `BridgeSupport(5)` man page. T5 uses the files shipped with macOS for Foundation, AppKit, CoreBluetooth, CoreLocation and UserNotifications. The files used and the macOS version are published.

**T5 sample:** a script with a fixed, published seed selects 20 entries per framework for each of four kinds: structs by value, blocks, out parameters and function pointers. A framework with fewer gives all it has. The sample is published before any test runs.

**T5 results:** each entry is checked for whether the library sees the correct signature. It's then called where that's possible without hardware, permissions or a particular UI state. Results are counted per framework and kind as correct, wrong value, Python exception, crash, not expressible, or excluded, and each exclusion gives its reason.

**Limits of T5:** the sample shows how each library handles these kinds of API, not how often apps use them. Metadata can't confirm how a method behaves, only its declared shape. T5 runs on macOS only, so its results aren't assumed for iOS.

## M. Memory management

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| M1 | Ownership model | When each library retains and releases, what the caller must do, and what its docs say | Code, docs | Source |
| M2 | Object lifetime | Scenarios below, reporting objects created and deallocated after Python references are dropped, garbage collection runs and the pool drains | Tests | Measured |
| M3 | Autorelease pools | Who creates and drains pools on the main thread and on background threads, and whether temporary objects are freed in a long loop with no pool from the caller | Code, tests | Source, Measured |
| M4 | Delegates and Python-defined objects | Whether each object and its Python state are freed after use, including through `delegate_register` in pyobjus and `@objc_method` classes in Rubicon | Tests | Measured |
| M5 | Stale references | The result of using an object after its last owner has released it, and after a weak reference to it has been cleared: nil, Python exception or crash | Tests | Measured |
| M6 | Long-open issues | Whether any of the 10 issues in Section 1's I5 table concern memory safety, read from each issue and its fix | GitHub | Source |

**M2 scenarios:** 1,000 objects, each obtained through `alloc` and `init`, `new`, `copy`, and a convenience constructor that returns an autoreleased object. Two further scenarios cover an object retained and later released by an Objective-C container, and a retain cycle through a Python-defined object. Expected counts are stated in each test before it runs. Too few deallocations are reported as a possible leak, and a crash or too many releases as a possible over-release.

**Limits of M:** these tests show whether objects are released, not how much memory is used, which Section 6 measures. A cycle or leak in the fixture's own scenario doesn't show that a real app is affected.

## TH. Threading

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| TH1 | GIL during calls | Whether the GIL is released during an Objective-C call, shown by whether another Python thread makes progress during a blocking call | Code, tests | Source, Measured |
| TH2 | Calls from background threads | Creating and using objects from a Python thread, including objects moved between threads, with the results of M2 repeated there | Tests | Measured |
| TH3 | Callbacks on foreign threads | A Python callback run from a thread Python didn't create: a GCD queue and a raw `pthread` | Tests | Measured |
| TH4 | Main thread and event loops | What each library provides for running work on the main thread and for integrating with a run loop or `asyncio` | Code, docs | Source |
| TH5 | Free-threaded Python | On a free-threaded Python 3.14 build on Mac: whether it builds and imports, whether the GIL stays disabled, and the results of TH2 and TH3 | Tests | Measured |

## CB. Callbacks

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| CB1 | Implementation | How each callback type a library supports reaches Python: delegates, Python-defined methods, blocks and function pointers | Code at pin | Source |
| CB2 | Signatures | How callback types are declared or discovered, and a round trip of objects, scalars and structs as callback arguments and return values | Code, tests | Source, Measured |
| CB3 | Exceptions in callbacks | What happens when Python code raises inside a callback: propagated, printed, swallowed or crash, and the value Objective-C receives | Tests | Measured |
| CB4 | Callback lifetime | Whether a callback still works, or crashes, when Objective-C calls it after Python has dropped its own reference | Tests | Measured |
| CB5 | Blocks | Two scenarios, reported separately: (a) creating a block in Python and passing it to Objective-C; (b) receiving a block from Objective-C and calling it from Python, including after the call that passed it has returned | Code, tests | Source, Measured |

**Callback types:** CB2, CB3 and CB4 each run for every callback type: delegates, Python-defined methods, blocks created in Python and function pointers. A type a library has no public way to write is reported as "not expressible" for that row. CB2 and CB3 also run for blocks received from Objective-C, covering the arguments and return values passed when Python calls the block, and what happens when the block raises an Objective-C exception. Each row states which callback type it covers, so a result for one type isn't read as a result for all.

## Deliberately excluded

| Measure | Why |
|---|---|
| Call speed and memory amounts | Section 6 measures these |
| Whether a feature exists | Section 3 covers this. Section 2 covers how the feature works |
| Lines of code | They vary with formatting and generated files |
| "Safer", "cleaner" or "more modern" | These are judgments, so the section reports the behavior behind them |

## Claims this section reports on

Claims 6 and 7 in [CLAIMS.md](../CLAIMS.md), and the question Section 1 left open under claim 4: whether any long-open issue was a memory-safety bug (M6). The claim 6 examples [requested in the thread](https://github.com/kivy/kivy/issues/9469#issuecomment-6543683260) are tested if they're provided by the time results are written. If none are, the claim stays **Reported**, and the section says the examples weren't provided. Section 6 also uses claim 7. CB5 and T5 provide evidence for claim 9, which Section 3 reports on.

Section 3's definitions are expected to use the same metadata to count how much of Apple's API each library can reach on macOS. That count isn't part of Section 2.

## Changes after approval

| Metric | Change | Reason |
|---|---|---|
| All tests | **Approved 2026-11-04.** PyObjC 13.0 added as a control on the Mac, reported separately. The test suites of PyObjC and objc4 added as scenario sources. | A control helps separate a library's limit from a faulty test. The author approved this after the baseline was set and before any test was written or run. |
| M2, M3, TH2 | One object left after a run is reported as its own result, "most recent object held", rather than a leak. | pyobjus's tests note that a class's methods hold the most recently wrapped instance until the next one. Changed after a trial run, which is kept in the raw results. |
| TH1 | Progress during a blocking call is compared with progress during `time.sleep`, and the result is "released" above 50%. | A fixed count of 1,000 iterations misread pyobjus as releasing the GIL, because the other thread could run briefly before the call started. Changed after a trial run. |
| CB2 to CB4 | The result for function pointers in pyobjus is "not expressible". Struct arguments use a separate case, `rect_arg`, as well as the struct round trip. | pyobjus has no public way to pass one. The crashes came from forms the test tried, so they aren't library results. They're kept in `superseded_pyobjus_function_pointer_results.json`. `rect_arg` was added because ctypes callbacks can't return structs, which hid whether they could receive them. |
| T5 | Struct entries compare the layout, not the struct name. Calling each entry is reported separately from finding it. | The runtime reports many structs as anonymous, so 8 entries differed by name alone for both Rubicon and the PyObjC control. The earlier result is kept in `superseded_t5_struct_name_mismatches.json`. |
| T2 | A scenario was added, `t2_class_usable`, which checks that a class passed as an argument works as that class. | The runtime can't tell a class from its metaclass by name, so the existing check couldn't catch it. It was found when pyobjus crashed during T5's setup. |
| M2 | A scenario was added, `m2_alloc_init_manual_release`, on pyobjus only. | The rules ask for documented use and no manual calls to be labeled separately. Rubicon and PyObjC document that the library manages this, and pyobjus's docs don't mention it, so a manual `release` was the only way to learn whether its result can be avoided. |
| T5 | A result was added for calls: "correct, out object not readable". | pyobjus can pass only nil for an object out parameter. Some methods still return the right value, which differs from a method that can't be called at all. |
| T5 | `typeForContentsOfURL:error:` is excluded. | Its result depended on the host process, not the library. All three libraries returned nil in Python, and Objective-C outside Python returned a type. |
| M2 to M5, TH, CB on iPhone | A hang is recorded when the phone's crash report shows the iOS launch watchdog's kill, at 20 seconds rather than 30. A crash is taken from the crash report, or from `devicectl`'s signal when iOS wrote no report. | `devicectl` reported exit code 0 for an abort, a test app with no UI never finishes launching, and iOS stops writing reports after enough crashes. |
| Test bugs | Several scenarios were corrected during trial runs before the full run. Trial summaries are in `results/section-02/2026-11-04/raw/`, and the fixes are listed in that folder's README. | The tests themselves were wrong. |
