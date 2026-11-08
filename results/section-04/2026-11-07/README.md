# Section 4 results, 2026-11-07

Library versions are in [the baseline](../../baseline/2026-11-04.md). The examples are in [`examples/section-04`](../../../examples/section-04), and the runners in [`tests/section-04`](../../../tests/section-04). Metric IDs refer to the [approved definitions](../../../metrics/04-examples.md).

## Status

| Part | Status |
|---|---|
| E1 on the Mac, 5 runs each | Done: `raw/mac.json` |
| E2 to E4 on the iPhone, 5 runs each | Done: `raw/iphone.json` |
| Line counts (X2, X3) | Done: `raw/counts.json` |
| Section text | Draft |

Every example gave the same outcome in all 5 runs, in each of the four environments: pyobjus 1.2.4 and `master`, and Rubicon 0.5.7 and `main`.

| Example | pyobjus `master` | pyobjus 1.2.4 | Rubicon `main` | Rubicon 0.5.7 |
|---|---|---|---|---|
| E1 Clipboard (Mac) | Wrong value, 5 of 5 | Wrong value, 5 of 5 | Correct, 5 of 5 | Correct, 5 of 5 |
| E2 Location | Correct, 5 of 5 | Crash, 5 of 5 | Correct, 5 of 5 | Correct, 5 of 5 |
| E3 Barometer | Correct, 5 of 5 | Correct, 5 of 5 | Correct, 5 of 5 | Correct, 5 of 5 |
| E4 Swift `async` | Correct, 5 of 5 | Correct, 5 of 5 | Correct, 5 of 5 | Correct, 5 of 5 |

**E1:** pyobjus returned `b'Kivy'` for the short ASCII string, where the task expects `'Kivy'`.

**E2, pyobjus 1.2.4:** the app ended with `NSInvalidArgumentException`, `locationManager:didUpdateLocations:: unrecognized selector`, which is pyobjus 1.2.4's response to a second delegate call after an exception it didn't clear. The first exception wasn't printed. Section 3 found that 1.2.4 raises when building a struct type it doesn't know, so the coordinate struct is the likely cause (**Inferred**).

## Tools

| Item | Version |
|---|---|
| Mac and Python environments | As in the baseline, reusing Section 2's environments |
| iPhone apps | Built with KivyForge at the baseline commit, `a36c2cccb7bb3dbd3bc33c89ba90587f1d0fa7db`, with Section 2's iOS wheels |
| E3's bridge | Compiled with manual reference counting, as kivy-ios's template is |
| E4's Swift | Swift 6.4, built by KivyForge as a local package |
| Line counts | `ruff format` from ruff 0.6.9 |

## Files in `raw/`

- `mac.json`, `iphone.json`: every run, with its outcome and which thread delivered the result. iPhone runs also have a summary of the crash report, if there was one
- `counts.json`: lines of Python and native code for each example and library
- `trial*_mac.json`, `trial*_iphone.json`: trial runs, one run per example, before the full runs

Local paths are replaced with `<work>`, `<repo>` and `~`, and the phone's identifier with `<device>`.

**Location and pressure:** E2 reads the phone's real location, and E3 its air pressure, which hints at altitude. Their checks run on the phone, and the results record only whether each value was valid. No coordinates or pressures are stored in any file, and an exception in either example is recorded by its type alone.

## Test fixes

The rules allow a test to be corrected when the test itself was wrong. All of these were found in trial runs, before the full runs.

| Example | Fix |
|---|---|
| E1, pyobjus | Read `types` as an attribute. pyobjus makes declared properties attributes, as its docs say, and calling it raised `TypeError` |
| E1, both | Also read back a short ASCII string, `"Kivy"`, after a check showed pyobjus returning `bytes` for short strings. Recorded as a change after approval |
| E2, Rubicon | Add Toga's `CLLocationCoordinate2D` declaration, from its `libs/core_location.py`, which was left out when Toga's code was trimmed |
| E2 and E3, both | Location and Motion & Fitness permission were granted by hand in Settings, for each app, before the full runs. A trial before Motion & Fitness was granted read no pressure |

## Line counts

Python is formatted with `ruff format`, then blank lines, comments, docstrings, imports, the `run()` test entry point and lines marked `# measure` aren't counted. Native code isn't reformatted, and blank lines, comments and imports aren't counted. [`count.py`](../../../tests/section-04/count.py) does both.

| Example | pyobjus Python | pyobjus native | Rubicon Python | Rubicon native |
|---|---:|---:|---:|---:|
| E1 Clipboard | 16 | 0 | 13 | 0 |
| E2 Location | 16 | 0 | 25 | 0 |
| E3 Barometer | 9 | 31 Objective-C | 20 | 0 |
| E4 Swift `async` | 13 | 15 Swift | 10 | 7 Swift |
