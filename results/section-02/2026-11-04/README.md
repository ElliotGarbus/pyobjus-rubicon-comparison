# Section 2 results, 2026-11-04

Versions are in [the baseline](../../baseline/2026-11-04.md). Rerun steps are in [the tests README](../../../tests/section-02/README.md).

## Status

| Part | Status |
|---|---|
| Mac scenarios, 5 runs each | Done: `raw/mac.json`, with `raw/mac_class_usable.json` and `raw/mac_manual_release.json` for the scenarios added later |
| Free-threaded Python (TH5) | Done: `raw/mac_free_threaded.json` and `raw/th5_gil_status.json` |
| T5, finding each sampled method and its signature | Done: `raw/t5.json` |
| T5, calling sampled methods, 5 runs each | Done: `raw/t5_calls.json`. Results are below |
| iPhone scenarios, 5 runs each | Done: `raw/iphone.json`. Results are below. The first trial is in `raw/iphone_trial1_summary.json` |
| Design facts with pinned links (D1 to D3, T1, M1, TH4, CB1) and M6 | Done: [Section 2](../../../sections/02-architecture.md) |

## Files in `raw/`

- `mac.json`, `mac_free_threaded.json`: every run, with its outcome and the end of its error output
- `iphone.json`: every iPhone run, with its outcome, the end of its error output and a summary of its crash report if there was one
- `mac_class_usable.json`, `mac_manual_release.json`: the scenarios added after the Mac run
- `th5_gil_status.json`: whether the GIL stays disabled after import, 5 runs per library
- `t5_sample.json`, `t5.json`: the T5 sample, with seed and totals, and its results
- `t5_calls.json`: T5's calling step
- `trial1_summary.json` to `trial4_summary.json`: results from trial runs before the full run
- `superseded_*.json`: results replaced by a recorded change

Local paths in the raw files are replaced with `<work>`, `<repo>` and `<env>`.

## T5, calling sampled methods

Of 131 sampled entries, 73 were called and 58 were excluded. Each entry ran 5 times, on macOS 26.6.2, and every entry gave the same outcome in all 5 runs. Rubicon 0.5.7 and `main` matched on every entry.

| Library | Correct | Correct, out object not readable | Wrong value | Python exception | Crash | Not expressible |
|---|---:|---:|---:|---:|---:|---:|
| pyobjus `master` | 11 | 13 | 0 | 4 | 0 | 45 |
| pyobjus 1.2.4 | 8 | 12 | 1 | 8 | 0 | 44 |
| Rubicon | 73 | 0 | 0 | 0 | 0 | 0 |
| PyObjC 13.0 (control) | 66 | 0 | 0 | 7 | 0 | 0 |

"Correct, out object not readable" means the return value was right, but the library can't read the object the method writes to an out parameter. pyobjus accepts only nil for an `id *` argument, so 10 more entries that need one are "not expressible". The other not-expressible entries for pyobjus `master` are 23 blocks and 12 function pointers.

By framework and kind, for pyobjus `master` and Rubicon:

| Framework, kind | Sampled | Excluded | Called | pyobjus: correct, partly correct, exception, not expressible | Rubicon: correct |
|---|---:|---:|---:|---|---:|
| Foundation, struct | 8 | 0 | 8 | 4, 0, 4, 0 | 8 |
| Foundation, block | 20 | 5 | 15 | 0, 0, 0, 15 | 15 |
| Foundation, out | 20 | 1 | 19 | 4, 8, 0, 7 | 19 |
| Foundation, function | 10 | 0 | 10 | 0, 0, 0, 10 | 10 |
| AppKit, block | 20 | 17 | 3 | 0, 0, 0, 3 | 3 |
| AppKit, out | 20 | 9 | 11 | 3, 5, 0, 3 | 11 |
| AppKit, function | 2 | 0 | 2 | 0, 0, 0, 2 | 2 |
| CoreLocation, block | 20 | 19 | 1 | 0, 0, 0, 1 | 1 |
| UserNotifications, block | 10 | 6 | 4 | 0, 0, 0, 4 | 4 |
| UserNotifications, out | 1 | 1 | 0 | none called | none called |

The 4 pyobjus exceptions are the `NSDecimal` entries: pyobjus raises `Bit fields aren't supported`. The 7 PyObjC exceptions are function pointer arguments with no metadata in PyObjC, 6 on `NSPointerFunctions` and 1 on `NSInvocation`.

**Limits of this result:**

- The excluded entries include all but one of CoreLocation and most of UserNotifications, so T5 says little about either. Each entry's reason is in `EXCLUDED` in [`t5_calls.py`](../../../tests/section-02/t5_calls.py).
- Some correct results are shallow. Four blocks are accepted but never run (`NSTableViewDiffableDataSource`, `CLMonitorConfiguration`, an empty `NSTableView` and an unstarted `NSMetadataQuery`). Five blocks are only checked for running and receiving a value (`getFileProviderServices` and the four notification getters). Six `NSPointerFunctions` entries set a function and read it back without it being called. Some out entries test only the error path of a missing file.
- Expected values for the less obvious entries come from [`t5_truth.m`](../../../tests/section-02/t5_truth.m), which makes the same calls in Objective-C. The rest come from each method's documented behavior.
- `typeForContentsOfURL:error:` is excluded because its result depended on the host process. It returned nil in Python on all three libraries, and `public.plain-text` in the Objective-C program.
- The tests were written by the AI assistant and corrected during trial runs, against Rubicon and PyObjC as well as pyobjus. A test written around one library's working form can favor it, so the tests need review by people who know each library.

## Test fixes during trial runs

Each was a fault in the test, not in a library.

| Scenario | Fault | Fix |
|---|---|---|
| M4 | A new class per object kept the Python state alive through the class | One class, with state on each instance |
| M2 cycle | The test deleted the variable its own closure used, which broke the cycle | State held on an object |
| M5 weak | Rubicon treated the fixture's `setWeakObject:` and `weakObject` as a property | Renamed to `storeWeak:` and `loadWeak` |
| Rubicon object callbacks and received blocks | The adapter returned raw pointers or used the wrong type annotation | Uses `ObjCInstance` annotations, `objc_block` and integer addresses for ctypes returns |
| T2 pointer, class and selector | The check didn't read each library's return form | Reads each form, and reports when there's no public way to read it |
| T3 insets and nested | The check assumed field names | Flattens the returned struct |
| PyObjC adapter | Class creation and required protocol methods | Uses `types.new_class`, and the fixture protocol methods are now `@optional` |
| CB4 function, PyObjC | The stored function needed PyObjC's documented `callbackFor` | Uses `callbackFor` |
| pyobjus adapter | `NSEdgeInsets` isn't exported | Defined in the adapter, as pyobjus's own tests do |
| T2 class, pyobjus adapter | The test passed the `autoclass` wrapper, and pyobjus casts a class argument without checking its type | Uses `.oclass()`, as pyobjus's tests do. The outcome is unchanged |
| T3 insets, Rubicon on iOS | The adapter used `NSEdgeInsets`, while the fixture uses `UIEdgeInsets` on iOS | Uses each platform's own type |
| iPhone runner | `devicectl` reported exit code 0 for an abort, and the iOS launch watchdog killed hung apps with `SIGKILL` | The phone's crash report decides the outcome. A watchdog kill is recorded as a hang |
| iPhone runner | iOS stopped writing crash reports after enough crashes, so 26 runs with a signal from `devicectl` were filed as "exited" | Those runs were relabelled as crashes from the saved signal, and each is marked `relabelled` in `iphone.json`. The runner now falls back to that signal. Where both existed, the report and the signal never disagreed |
| iPhone runner | A crash report that couldn't be copied stopped the run 3 scenarios short on Rubicon 0.5.7 | The runner now carries on without the report. Those 3 scenarios were then run |
| T5 calling, all libraries | Class properties called as methods, Rubicon's `count` is Python's `list.count`, PyObjC needs real `NS` objects and returns out values differently | Shared helpers for each form |
| T5 `NSMatrix` | `NSCell` has no `setTag:`, so the setup raised an Objective-C exception on all three | Uses `NSActionCell` |
| T5 `getResourceValue:forKey:error:`, pyobjus | The test passed nil where the method requires somewhere to write, which crashed | Recorded as not expressible, without calling it |
| T5 linguistic tagger and XSLT | The expected values were assumptions | Replaced with the values from `t5_truth.m` |

## Added after the run: a class passed as an argument

While setting up the `NSMatrix` entry, pyobjus crashed inside AppKit when passed a class. `autoclass("NSObject").oclass()` returns the metaclass, not the class, because pyobjus's conversion of a returned class calls [`object_getClass`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L247-L250) on it. A metaclass has the same name as its class, so a check by name still passes.

The new scenario, `t2_class_usable`, passes `NSObject` to `[NSArray isSubclassOfClass:]`. It returned NO on pyobjus `master` and 1.2.4 in 5 of 5 runs, and YES on Rubicon and PyObjC. This is `raw/mac_class_usable.json`.

## Added after the run: a manual release

The approved rules ask for memory scenarios to cover documented manual calls as well as none. Rubicon's and PyObjC's docs say the library manages this, and pyobjus's docs don't mention it. So `m2_alloc_init_manual_release` calls `release` after `alloc` and `init`, on pyobjus only. It freed 999 of 1,000 objects on 1.2.4 and `master`, on Mac and iPhone, in 5 of 5 runs. Other method families weren't tested.

## iPhone setup

- **Apps:** one app per version point, with no Kivy, built by KivyForge at `a36c2cc` on Python 3.15.0. Each launch runs one scenario, so a crash or hang is recorded and doesn't stop the run. Steps are in [the tests README](../../../tests/section-02/README.md).
- **Not a supported app mode:** with no Kivy, KivyForge's app runs Python on the main thread with no `UIApplicationMain` and no run loop, as Python does on the Mac. Its source calls this a smoke-test scaffold. It's used here so the two platforms match, and a Kivy app's behavior isn't assumed from it.
- **Hangs:** iOS's launch watchdog kills an app at 20 seconds, because this app never finishes launching. A hang is recorded when the crash report shows that kill.
- **pyobjus wheels:** built from source for this comparison at the baseline commits, because KivyForge's index has no wheel at `0c204ad` and the `kivy-mobile-wheels` recipe needs the Python 3.15 Mac framework installed. The script uses the same Cython, libffi 3.5.2 and compiler flags, with a 16.0 deployment target for libffi because Xcode 27 refuses the project's 8.0.
- **Rubicon `main` wheel:** built at the baseline commit, versioned `0.5.8.dev21` without a local segment, because KivyForge's install step rejected the `+` in the default version.
- **PyObjC:** not run on the iPhone, as the definitions state.

## iPhone results

All 82 scenarios ran 5 times on each of the 4 builds, on iOS 27.0.1, for 1,640 runs. Only 5 scenarios gave a different outcome from the Mac at the same version. No other scenario changed, so the Mac results also describe the iPhone for this fixture.

| Scenario | Build | iPhone | Mac |
|---|---|---|---|
| `cb3_delegate`, `cb3_subclass` | Rubicon 0.5.7 and `main` | Python exception swallowed, and Objective-C got a different large value each run | Swallowed, and Objective-C got zero |
| `cb5b_stack_block_after_return` | Rubicon 0.5.7 and `main` | Crash, `SIGKILL` | Crash, `SIGSEGV` |
| `t3_rect` | pyobjus 1.2.4 | Crash, 1 of 5 | Crash, 3 of 5 |
| `cb2_delegate_rect` | pyobjus 1.2.4 | Python exception, 5 of 5 | Crash, 5 of 5 |

- **Rubicon's swallowed exceptions:** on the iPhone the delegate and subclass values differ between runs, which suggests the return value is never set (**Inferred**). The zero on the Mac may therefore be chance. Blocks and function pointers returned 2 every run on the iPhone, and a large value on the Mac.
- **The stack block:** a crash report from the trial shows the `SIGKILL` as an invalid page at a stack address, under code signing. iOS reports this differently from macOS, but it's the same call of a block that has gone out of scope.
- **pyobjus 1.2.4 against `master`:** the same 9 scenarios differ as on the Mac. Rubicon 0.5.7 and `main` matched everywhere.
- **Still the same on both platforms:** the leaks and delegate retention on pyobjus, the GIL held during calls and the resulting hang, and the crash on an Objective-C exception for both libraries. pyobjus's GIL progress was 0.1% to 0.2% of its progress during `time.sleep` on the iPhone, against 90% to 119% for Rubicon.
- **Mixed builds:** 68 pyobjus `master` scenarios ran before the phone's connection dropped and the app was rebuilt with the class scenario. Only the class argument code changed between those builds.


## Scenario sources

- `t4_objc_exception`: PyObjC [`test_exceptions.py`](https://github.com/ronaldoussoren/pyobjc/blob/3e53fecb4512b9771e11c123a16b19a9baf09301/pyobjc-core/PyObjCTest/test_exceptions.py), `testSimple`
- `cb5a_block_collected`: PyObjC [`test_blocks.py`](https://github.com/ronaldoussoren/pyobjc/blob/3e53fecb4512b9771e11c123a16b19a9baf09301/pyobjc-core/PyObjCTest/test_blocks.py), `test_block_is_collected`
- `cb5b_stack_block_after_return`: the same file, `testStackBlocksWithIndirectUse`
- `m3_with_pool_loop`: objc4 [`rr-autorelease2.m`](https://github.com/apple-oss-distributions/objc4/blob/fb265098298302243cd7eeaa1f63f0ba7786dd9a/test/rr-autorelease2.m)
