# Section 3 results, 2026-11-07

Library versions are in [the baseline](../../baseline/2026-11-04.md). Rerun steps are in [the tests README](../../../tests/section-03/README.md). Metric IDs refer to the [approved definitions](../../../metrics/03-capabilities.md).

## Status

| Part | Status |
|---|---|
| Mac cases, 5 runs each | Done: `raw/mac.json`. Every case gave the same outcome in all 5 runs, in every environment |
| iPhone cases, 5 runs each | Done: `raw/iphone.json`. Every case gave the same outcome in all 5 runs, in every environment |
| A1, A2: SDK header counts | Done: `raw/headers_mac.json`, `raw/headers_ios.json` |
| A1, A2: matched to the results | Done: `raw/reach_mac.json`, `raw/reach_ios.json` |
| A3: cross-check with BridgeSupport | Done: `raw/crosscheck_mac.json` |
| A4: Swift-only frameworks | Done: listed in `raw/reach_mac.json` and `raw/reach_ios.json` |
| API and docs checks, L1, L2 | Not started |
| Section text | Not started |

## Tools

| Item | Version |
|---|---|
| Mac and Python environments | As in the baseline, reusing Section 2's environments |
| Xcode, SDKs | Xcode 27.0, with the macOS 27.0 and iOS 27.0 SDKs |
| Apple clang | 21.0.0, for the fixture and the header counts |
| Swift | 6.4 |
| KivyForge | `a36c2cccb7bb3dbd3bc33c89ba90587f1d0fa7db`, the baseline commit, run from a separate worktree |
| iOS wheels | Section 2's, built from the baseline commits |
| iPhone | As in the baseline: iOS 27.0.1, Python 3.15.0 |

The SDKs are newer than macOS 26.6.2 on the Mac, so the header counts leave out anything introduced after the tested versions (macOS 26.6.2, iOS 27.0.1).

## Files in `raw/`

- `mac.json`, `iphone.json`: every run, with its outcome, the route (public API, `ctypes` or Objective-C helper), and the end of its error output. iPhone runs also have a summary of the crash report, if there was one
- `trial1_*.json`, `trial2_*.json`: trial runs, one run per case, before the full runs
- `superseded_mac_f1_6_framework.json`: the Mac F1.6 result replaced by the change below
- `headers_mac.json`, `headers_ios.json`: every public declaration in each SDK, with whether the tested system has it, whether it's deprecated, and the kinds of value it needs
- `reach_mac.json`, `reach_ios.json`: those declarations matched to each library's results, per side (to call, to implement), per declaration type and per framework, with the Swift-only framework lists
- `crosscheck_mac.json`: every declaration compared with BridgeSupport, and each disagreement

Local paths in the raw files are replaced with `<work>`, `<repo>` and `~`, and the phone's identifier with `<device>`.

## Test fixes

The rules allow a test to be corrected when the test itself was wrong. These were found in trial runs, before the full runs, unless stated.

| Case | Fix | Found |
|---|---|---|
| `f1_3_array_with_objects` (Rubicon) | Read the count with `len()`. Rubicon's `NSArray` wrapper has Python's `list.count`, which hides the Objective-C `count` | Mac trial 1 |
| `f3_6_timer` (Rubicon) | Return `True` or `False`, not the list of firings | Mac trial 1 |
| `f2_2_union_return` (pyobjus) | Read the first field as `a`. pyobjus names an unknown type's fields `a`, `b` and so on, as its docs describe | Mac trial 1 |
| `f2_7_enum` (pyobjus) | Hold the strings in variables. Inline temporaries give a wrong result, which `f1_1_multipart` records and this case doesn't test | Mac trial 1 |
| `f1_2_*`, `f7_2_property_write` (all) | Read the value back through `valueForKey:` from Objective-C, so an attribute set only in Python can't pass | Mac trial 1 |
| PyObjC control | Added metadata for `sumRect:`, `failWithError:`, `noteAtIndex:error:` and the delegate's array, used `objc.selector` for the class method, and compared Python strings in the comparators | Mac trial 1 |
| `f2_3_fixed_array` (all) | Added. The definition asks for a fixed-size array argument, and the first draft tested only a struct holding one | Mac trial 1 |
| `f1_1_multipart_held`, `f2_4_opaque_pointer` (all) | Added. The first separates pyobjus's inline-argument result from the call itself. The second gives A a measured case for opaque pointers such as `CGColorRef` | Mac trial 2 |
| `cases_pyobjus.py` | Opens `/usr/lib/libobjc.A.dylib` instead of `/usr/lib/libobjc.dylib`, which iOS doesn't have. Both name the same library on the Mac. Changed after the Mac run, and used only by the `__ctypes` workaround cases | iPhone build |
| `f1_6_framework` (all) | Loads the first framework from a fixed list that isn't loaded yet, and reports which. iOS loads CoreLocation and Contacts at launch, so the case couldn't show a library loading a framework. On the Mac it still uses CoreLocation. The Mac case was rerun after the full run, and the earlier result is in `superseded_mac_f1_6_framework.json` | iPhone trial 1 |

## Header count fixes

`headers.py` was corrected while it was being developed, before any count was used. Each version was rerun over both SDKs, and only the last is kept.

- Frameworks with no umbrella header, such as CoreTelephony and IOKit, were skipped. They're now read by importing each of their headers.
- A local variable reused the name of the set of Objective-C type parameters, so every C function's parameters were classified as objects.
- A typedef behind a pointer, such as `NSInteger *`, and an anonymous struct's typedef weren't resolved. Generic parameters such as `ObjectType` weren't treated as objects. `SEL`, which the dump spells `SEL *`, wasn't treated as a selector.
- SIMD vector types were read as function pointers because of their `__attribute__` spelling, and so was a pointer to a function pointer. Both were found by the BridgeSupport cross-check.

## Cross-check

48,509 declarations were in both the macOS headers and BridgeSupport, and 38 disagreed. 36 are in Tk, which clang couldn't parse, so Tk is left out of the counts. The other 2 are `Tcl_CreateThread`, which is in two BridgeSupport files. Its callback argument is typed `^?` there but not marked as a function pointer, and the header declares a function pointer, so the header's reading was kept.

## Left out of the counts

- **macOS:** DriverKit, Kernel and Tk, whose headers clang couldn't parse as an app does. They're listed in `reach_mac.json`.
- **Unclassified:** declarations needing a kind no case tests, such as a pointer to a pointer or a SIMD vector, are counted as unclassified rather than as expressible or not.
