# Section 4 metric definitions

**Status: approved 2026-11-07.** These definitions were written before any Section 4 example was written or run. Changes made after that are recorded at the end of this document with their reasons.

Section 4 shows the same tasks written with each library, so readers can see what the differences found in Sections 2 and 3 mean in an app. It uses a few examples, each chosen to show one key capability or difference. It doesn't add new capability tests.

## What was seen before these were written

| Seen before writing (2026-11-07) | Where | Effect on the rules |
|---|---|---|
| All of Section 3's results, including that pyobjus can't create blocks and that both libraries implement delegates | [Section 3](../sections/03-capabilities.md) | The examples are chosen to show those results in real tasks, not to find new ones |
| Kivy itself uses pyobjus in two places: the macOS clipboard and AVPlayer audio | [kivy](https://github.com/kivy/kivy/tree/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core) at `0f23a55` | Example E1 is Kivy's clipboard |
| plyer's iOS and macOS GPS facades use a pyobjus delegate, and Toga's iOS location uses a Rubicon delegate for the same API | [plyer](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/platforms/ios/gps.py) at `4853b3a`, [Toga](https://github.com/beeware/toga/blob/c7d1d4e75505d69554dd6f68da4fa12ed58eb80e/iOS/src/toga_iOS/hardware/location.py) at `c7d1d4e` | Example E2 starts from both, so each library's version comes from a real project |
| plyer's six iOS motion facades call an Objective-C class named `bridge`, which wraps Core Motion's block APIs and stores readings for Python to poll. The only copy found in kivy-ios is a test fixture | [plyer](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/plyer/platforms/ios/accelerometer.py), [kivy-ios](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/tests/tools/fixtures/legacy_mrc/bridge.m) at `fd363d4` | Example E3 uses this as the pyobjus version, through plyer's barometer facade |
| The author's KivyForge guide calls a Swift `async` method through a polled job in pyobjus and a completion handler in Rubicon | [Call Swift from Python](https://github.com/ElliotGarbus/kivyforge/blob/edaa3aa8c4eb2f1a4f9f1b42a7c7b7350ae55012/docs/guides/guides/ios/swift.md), written by the author | Example E4 starts from it, and both versions are rechecked against each library's docs |

## Examples

Each example is one task, done the same way in each library, with the same observable result.

| ID | Task | Shows | Platform | Starting point |
|---|---|---|---|---|
| E1 | Copy text to the clipboard and read it back | Everyday calls, strings and arrays. Both libraries can do this | Mac | Kivy's [`clipboard_nspaste.py`](https://github.com/kivy/kivy/blob/0f23a55ccc59a55d2e726d079fedcca03c5ca068/kivy/core/clipboard/clipboard_nspaste.py) for pyobjus. Rubicon written from its docs |
| E2 | Receive location updates and report latitude and longitude | Delegates, which both libraries support, and reading a struct from a delegate's argument | iPhone | plyer's iOS GPS facade for pyobjus, and Toga's iOS location for Rubicon, each trimmed to the task |
| E3 | Read the barometer | A block-only API: Core Motion's altimeter delivers readings only to a handler. Rubicon passes a Python function, and pyobjus needs Objective-C helper code compiled into the app | iPhone | plyer's barometer facade and the bridge's altimeter code for pyobjus. Rubicon written from its docs |
| E4 | Call a Swift `async` method and get its result | Calling Swift, and the cost of no blocks when Swift exports a completion handler | iPhone | The author's KivyForge example |

## Measures

| ID | Measure | Definition | Label |
|---|---|---|---|
| X1 | Works | The example runs and gives the expected result in 5 runs, each in a new process, on its platform | Measured |
| X2 | Python code | Lines of Python, after formatting both versions with `ruff format` at its defaults, not counting blank lines, comments, docstrings or imports | Measured |
| X3 | Native code | Lines of Objective-C or Swift the app must compile for the example, counted the same way, plus any build steps it adds | Measured |
| X4 | What else it needs | Anything beyond the library's public API: `ctypes`, encodings registered at runtime, types declared by hand, or a helper class. Each is listed, with a link to where the library's docs describe it, if they do | Source |
| X5 | Where results arrive | Which thread delivers the result to Python, and what the example does to hand it to the app's main thread | Measured |

**Code shown in full:** both versions of every example are shown side by side in the section, so readers can judge readability themselves. The section doesn't score readability.

## Rules

- **Versions and platforms:** as in Section 3: [the 2026-11-04 baseline](../results/baseline/2026-11-04.md), each library's default branch on the Mac (Python 3.14) and the iPhone (Python 3.15), built with KivyForge at the baseline commit. The release versions run too, and are reported only where they differ.
- **Public API, as documented:** each version uses its library's public API the way its docs show. Where a version needs something else, X4 lists it.
- **Real code first:** where Kivy, plyer or Toga already does the task, that code is the starting point, trimmed to the task. Every change from the original is listed, with the reason. Otherwise the version is written from the library's docs.
- **Same task:** both versions start and stop the same way and produce the same output. Error handling is the same in both, or left out of both.
- **No Kivy:** the examples run in the test app without Kivy, so Kivy doesn't affect the result. X5 says what a Kivy app would add.
- **Permissions:** E2 needs location permission and E3 Motion & Fitness permission, each granted once by hand on the phone before the runs. This is recorded.
- **Improvements welcome:** anyone can propose a shorter or more idiomatic version for either library. A proposed version that works replaces the current one, and the change is recorded.
- **No scoring:** line counts are reported for each example and not added up or weighted.

## Deliberately excluded

| Measure | Why |
|---|---|
| Whether a feature exists | Section 3 covers this |
| Speed and memory | Section 6 covers these |
| Changes needed to move existing code from one library to the other | Section 8 covers this |
| "Cleaner", "simpler" or "more Pythonic" | These are judgments. The code is shown so readers can judge |

## Claims this section reports on

| Claim ([register](../CLAIMS.md)) | Evidence |
|---|---|
| 9. pyobjus can't create blocks, so APIs with completion handlers need Objective-C helper code | E3 and E4: the helper code pyobjus needs, its size and its build steps |

## Changes after approval

| Metric | Change | Reason |
|---|---|---|
| What was seen | kivy-ios's project template ships `bridge.h` and `bridge.m`, 173 lines, in every app it generates. The test fixture is a snapshot of that template | The approved text said the only copy was a test fixture. Found while writing E3, before any example ran on the iPhone |
| E1 | Also reads back a short ASCII string, `"Kivy"`, as well as `"héllo, Kivy"` | A Mac trial showed pyobjus returning `bytes` for short strings, which Kivy's clipboard code would hit. Both versions read back both strings. Found in a trial run |
