# Section 6 results, 2026-11-08

Library versions are in [the baseline](../../baseline/2026-11-04.md). The scripts are in [`tests/section-06`](../../../tests/section-06), and each one's docstring gives its usage. Metric IDs refer to the [approved definitions](../../../metrics/06-performance.md), which also list the changes made after approval.

## Status

| Part | Status |
|---|---|
| C1 to C4, CB1 timing, Mac, 5 processes per operation and version | Done: `raw/mac.json`. Every operation gave correct values, except where noted |
| C1 to C4, CB1 timing, iPhone, default branches | Done: `raw/iphone.json` |
| C5 first use, S1 import time | Done, both platforms |
| M1 to M4 memory | Done, both platforms |
| S2 installed size | Done: `raw/mac.json` and `raw/iphone_size.json` |
| Figures | `raw/summary.json`, from [`summarize.py`](../../../tests/section-06/summarize.py) |
| Cause of pyobjus's `CGRect` slowdown | Done: `raw/cgrect_cache.json`. Added after the full runs |
| Rubicon's footprint after `alloc` then `init` | Done: `raw/rubicon_alloc_init.json`. Added after the full runs |
| Section text | Draft |

## Conditions

| | Mac | iPhone |
|---|---|---|
| Device | Apple M5 Pro, macOS 26.6.2 | iPhone 18 Pro Max, iOS 27.0.1 |
| Python | 3.14.7 (python.org) | 3.15.0, in a KivyForge test app without Kivy |
| Versions | pyobjus 1.2.4 and `master`, Rubicon 0.5.7 and `main`, PyObjC 13.0 as a reference | pyobjus `master` and Rubicon `main` (see the definitions' changes) |
| Power | On AC power. Low Power Mode off in every process | Low Power Mode off in every launch |
| Thermal state | Nominal in every process | Nominal or fair. 3 launches reached serious and were rerun after 2 minutes, as the definitions require. They're kept in `raw/iphone.json` under `discarded` |

## Timing

Median time per call in µs, over all 30 timed rounds of 5 processes. Each library's rounds were sized to take at least 20 ms (N is in `summary.json`). The 25th to 75th percentile range is within 8% of the median for every pyobjus and Rubicon operation except pyobjus's `CGRect` calls (see below), and within 12% for PyObjC, whose rounds are shorter. An empty Python function call took 0.009 µs on the Mac and 0.011 µs on the iPhone.

### Mac

| Operation | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` | PyObjC 13.0 |
|---|---:|---:|---:|---:|---:|
| C1 Empty call | 1.8 | 2.0 | 1.6 | 1.6 | 0.10 |
| C2 `NSInteger` | 3.1 | 3.1 | 2.2 | 2.2 | 0.12 |
| C2 `double` | 3.9 | 3.9 | 2.2 | 2.2 | 0.13 |
| C2 `BOOL` | 3.2 | 3.1 | 2.2 | 2.2 | 0.12 |
| C2 Object | 30.1 | 30.1 | 2.5 | 2.5 | 0.15 |
| C2 `CGRect` | Crash in 3 of 5 processes | See below | 2.3 | 2.3 | 1.1 |
| C2 String, 10 characters | 182 | 181 | 19.2 | 19.0 | 0.16 |
| C2 String, 10,000 characters | 256 | 219 | 21.7 | 21.5 | 0.15 |
| C3 Class method | 1.9 | 2.0 | 1.8 | 1.8 | 0.15 |
| C3 Property read | 2.1 | 2.2 | 1.1 | 1.1 | 0.11 |
| C3 Property write | 3.6 | 3.6 | 1.4 | 1.4 | 0.12 |
| C4 Empty call, method looked up first | 1.8 | 1.9 | 0.68 | 0.68 | 0.05 |
| C4 `NSInteger` | 3.1 | 3.0 | 1.5 | 1.5 | 0.06 |
| C4 `double` | 3.8 | 3.8 | 1.5 | 1.5 | 0.06 |
| C4 `BOOL` | 3.1 | 3.1 | 1.5 | 1.5 | 0.06 |
| C4 Object | 30.2 | 30.1 | 1.8 | 1.8 | 0.08 |
| C4 `CGRect` | Crash in 3 of 5 processes | See below | 1.6 | 1.6 | 1.0 |
| C4 String, 10 characters | 183 | 180 | 18.1 | 18.1 | 0.08 |
| C4 String, 10,000 characters | 254 | 221 | 20.5 | 20.4 | 0.09 |
| CB1 Delegate, no arguments | 67.4 | 73.1 | 0.71 | 0.70 | 0.06 |
| CB1 Delegate, `NSInteger` argument and return | 77.2, wrong value | 91.1 | 0.78 | 0.78 | 0.07 |
| CB1 Delegate, object argument | 104 | 111 | 1.00 | 0.98 | 0.08 |

**Wrong value:** pyobjus 1.2.4's delegate returned 0 to Objective-C instead of its value, as Section 2 found.

**Crash:** pyobjus 1.2.4 ended with `SIGTRAP` in 3 of 5 processes for each `CGRect` operation, and in its calibration process. macOS kept two crash reports from these runs, and in both the allocator stopped the process (`EXC_BREAKPOINT` in `malloc`): once inside pyobjus's `type_encoding_to_ffitype` and once in the Objective-C runtime's method cache. An allocator stopping in different places is what heap corruption looks like (**Inferred**), and it fits the heap overrun with a struct argument that pyobjus `master`'s Guard Malloc test checks for (Section 5).

### iPhone

| Operation | pyobjus `master` | Rubicon `main` | pyobjus ÷ Rubicon |
|---|---:|---:|---:|
| C1 Empty call | 2.4 | 1.8 | 1.3 |
| C2 `NSInteger` | 3.9 | 2.5 | 1.5 |
| C2 `double` | 4.7 | 2.6 | 1.8 |
| C2 `BOOL` | 3.9 | 2.5 | 1.5 |
| C2 Object | 55.0 | 2.9 | 18.7 |
| C2 `CGRect` | See below | 2.7 | |
| C2 String, 10 characters | 466 | 23.6 | 19.8 |
| C2 String, 10,000 characters | 508 | 25.3 | 20.1 |
| C3 Class method | 2.4 | 2.1 | 1.2 |
| C3 Property read | 2.7 | 1.3 | 2.1 |
| C3 Property write | 4.5 | 1.7 | 2.7 |
| C4 Empty call, method looked up first | 2.3 | 0.84 | 2.7 |
| C4 `NSInteger` | 3.8 | 1.8 | 2.1 |
| C4 `double` | 4.6 | 1.8 | 2.5 |
| C4 `BOOL` | 3.8 | 1.8 | 2.1 |
| C4 Object | 55.9 | 2.2 | 25.5 |
| C4 `CGRect` | See below | 1.9 | |
| C4 String, 10 characters | 466 | 22.7 | 20.5 |
| C4 String, 10,000 characters | 506 | 24.4 | 20.7 |
| CB1 Delegate, no arguments | 128 | 0.90 | 143 |
| CB1 Delegate, `NSInteger` argument and return | 150 | 0.99 | 152 |
| CB1 Delegate, object argument | 193 | 1.2 | 155 |

### pyobjus `CGRect` calls slow down with use

In every pyobjus process, each round of `CGRect` calls took longer than the last. Time per call rises in a straight line with the number of `CGRect` calls the process has already made (r² of 0.999 or more in every process). No other operation, and no other library, shows this: their slopes are 0.00 ns per call.

| | Added to each later call, per call made | Extrapolated to the first call | First round | Last round |
|---|---:|---:|---:|---:|
| Mac, pyobjus `master`, N = 2,000 | 3.7 ns | 6.6 µs | 32 µs | 249 µs |
| Mac, pyobjus 1.2.4, 2 processes that didn't crash | 3.7 ns | 15.5 µs | 40 µs | 258 µs |
| iPhone, pyobjus `master`, N = 1,000 | 4.1 ns | 7.3 µs | 24 µs | 141 µs |

So after 10,000 `CGRect` calls, each further call takes about 37 µs longer than the first did. Because the time depends on how many calls came before, the median for these operations depends on N and isn't reported as a figure. The same slope appears whether the method is looked up each time or beforehand.

**Cause:** pyobjus appends the address of every struct argument passed by value to a module-level list, `ctypes_struct_cache` (`pyobjus_conversions.pxi`, lines 2 and 691 at `0c204ad`), and never removes entries. Every struct return checks membership in that list (line 263), which compares against each entry. [`cgrect_cache.py`](../../../tests/section-06/cgrect_cache.py) times rounds of 1,000 `echoRect:` calls while the list grows, then clears it. Added after the full runs, once the slope was found. In `raw/cgrect_cache.json`:

| pyobjus `master`, Mac, 3 processes | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| First 1,000 calls, list empty | 7.09 µs | 7.08 µs | 6.97 µs |
| 1,000 calls with 19,000 to 20,000 entries | 75.98 µs | 75.94 µs | 75.51 µs |
| 1,000 calls after clearing the list | 6.94 µs | 7.09 µs | 6.98 µs |
| Python memory kept per call (`tracemalloc`) | 48.2 B | 48.2 B | 48.2 B |

The list grew by exactly one entry per call. pyobjus 1.2.4 crashed in all 3 processes before finishing, as it did in the timing runs.

### C5 First use

In a new process, with the library already imported and `NSObject` already wrapped: the time to name a fixture class not used before and call a class method on it. Median of 5 processes, in ms.

| | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` | PyObjC 13.0 |
|---|---:|---:|---:|---:|---:|
| Mac, class with 5 methods | 0.16 | 0.15 | 0.70 | 0.70 | 0.018 |
| Mac, class with 100 methods | 0.15 | 0.15 | 0.71 | 0.70 | 0.017 |
| iPhone, class with 5 methods | | 0.33 | | 1.7 | |
| iPhone, class with 100 methods | | 0.33 | | 1.6 | |

### S1 Import time

Median of 5 processes, in ms: the time from just before the import to after `NSObject.alloc().init()` or its equivalent, inside the process. On the Mac, the wall-clock time of the same process less that of an empty Python process is also given.

| | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` | PyObjC 13.0 |
|---|---:|---:|---:|---:|---:|
| Mac, inside the process | 1.8 | 7.3 | 21.3 | 21.3 | 22.9 |
| Mac, wall clock less empty Python | 6.2 | 13.1 | 30.1 | 30.1 | 30.9 |
| iPhone, inside the process | | 5.1 | | 43.6 | |

pyobjus `master` imports `traceback`, which 1.2.4 doesn't, and on Python 3.14 that loads `inspect`, `dataclasses` and others: about 6.6 ms of `master`'s import in `python -X importtime`, and most of its difference from 1.2.4. Both measurements start after the harness has imported its own modules (`ctypes`, `json`, `statistics` and others), so those aren't counted for either library. On the iPhone, the app's entry point also imports `traceback` first, so iPhone figures leave out `traceback` and what it loads, such as `inspect`, for both libraries.

## Memory

Footprint is `phys_footprint`, which grows in 16 KB pages, so differences below about 2 bytes per object (for 10,000 objects) or 16 bytes per delegate (for 1,000) are within a page. Python is `tracemalloc`'s count. Median of 5 processes.

### Mac

| | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` |
|---|---:|---:|---:|---:|
| M1 Import, footprint | 0.57 MB | 4.1 MB | 11.8 MB | 11.8 MB |
| M1 Import, Python | 0.29 MB | 2.2 MB | 6.1 MB | 6.1 MB |
| M2 Per live wrapper, footprint | 249 B | 226 B | 765 B | 764 B |
| M2 Per live wrapper, Python | 113 B | 113 B | 398 B | 398 B |
| M3 Kept per `alloc` then `init` object | 69 B, 0 of 10,000 freed | 56 B, 0 freed | 64 B, all freed | 62 B, all freed |
| M3 Kept per `new` object | 36 B, 0 freed | 38 B, 0 freed | 3 B, all freed | 3 B, all freed |
| M3 Kept per `copy` object | 38 B, 0 freed | 38 B, 0 freed | 3 B, all freed | 3 B, all freed |
| M3 Kept per object from an ordinary method | 21 B, 9,999 freed | 21 B, 9,999 freed | 3 B, all freed | 7 B, all freed |
| M3 Kept per delegate, footprint | 10.5 KB | 10.4 KB | 573 B | 573 B |
| M3 Kept per delegate, Python | 4.6 KB | 4.6 KB | 6 B | 7 B |
| M4 Growth per call over 900,000 calls | 16 B | 16 B | 0 | 0 |

### iPhone

| | pyobjus `master` | Rubicon `main` |
|---|---:|---:|
| M1 Import, footprint | 0.82 MB | 12.8 MB |
| M1 Import, Python | 0.35 MB | 5.7 MB |
| M2 Per live wrapper, footprint | 233 B | 726 B |
| M2 Per live wrapper, Python | 113 B | 398 B |
| M3 Kept per `alloc` then `init` object | 52 B, 0 of 10,000 freed | 51 B, all freed |
| M3 Kept per `new` object | 36 B, 0 freed | 7 B, all freed |
| M3 Kept per `copy` object | 38 B, 0 freed | 7 B, all freed |
| M3 Kept per object from an ordinary method | 21 B, 9,999 freed | 7 B, all freed |
| M3 Kept per delegate, footprint | 9.9 KB | 426 B |
| M3 Kept per delegate, Python | 4.5 KB | 6 B |
| M4 Growth per call over 270,000 calls | 6.5 B | 0 |

- **M3 objects freed** are counted by the fixture's own `dealloc`, as in Section 2.
- **Rubicon:** its footprint figures in M3 are memory freed and held by the allocator, not memory in use: every object was freed. After `alloc` then `init` they're higher, because the first method call on a new wrapper makes a `ctypes.cast` that, in CPython, leaves a reference cycle for the cycle collector. [`rubicon_alloc_init.py`](../../../tests/section-06/rubicon_alloc_init.py) shows the cycle, reproduces it in plain `ctypes`, and shows the footprint doesn't grow over 4 batches (`raw/rubicon_alloc_init.json`). The section doesn't report these figures for Rubicon.
- **pyobjus ordinary methods and M4:** the objects are freed, yet footprint grows by about 16 bytes per call on the Mac and 6.5 on the iPhone, outside Python's allocations. On the iPhone the samples dip once before rising, so the figure is less steady there.
- **M1 on the Mac** includes `traceback` for pyobjus `master`, as under S1. On the iPhone it doesn't.

## S2 Installed size

| | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` | PyObjC 13.0 |
|---|---:|---:|---:|---:|---:|
| Mac, installed package | 1.60 MB | 1.98 MB | 0.24 MB | 0.24 MB | 10.9 MB (`objc` package only) |
| Added to the iPhone app | | 1.13 MB | | 0.24 MB | |

On the Mac, both pyobjus builds are universal (arm64 and x86_64), so the figure includes both. pyobjus 1.2.4 is PyPI's wheel and `master` was built from source, as in Section 2. On the iPhone, pyobjus's figure includes the framework that holds its compiled extension (0.96 MB), and both exclude package metadata. The whole Debug test app is 260 MB, most of it Python.

## Tools

| Item | Version |
|---|---|
| Mac environments | Section 2's, as in the baseline |
| Fixture | `s6fixture.m`, built with `-O2 -fno-objc-arc`, for macOS arm64 and as an iOS xcframework |
| iPhone app | KivyForge at the baseline commit, `a36c2cccb7bb3dbd3bc33c89ba90587f1d0fa7db`, Debug build, with Section 2's iOS wheels for the default branches |

## Files in `raw/`

- `mac.json`, `iphone.json`: every process or launch, with its result, value check, thermal state and Low Power Mode, and the calibration and N used. `mac.json` also has `superseded`, the pyobjus 1.2.4 `CGRect` runs made with the wrong fallback N (see below). `iphone.json` has `discarded`, the 3 launches that reached a serious thermal state, and `superseded_timing_before_autolock`
- `superseded_mac_same_n.json`: the first Mac timing pass, with one N for every library, stopped and replaced
- `summary.json`: the figures in this README
- `iphone_size.json`: S2 on the iPhone
- `cgrect_cache.json`: the `ctypes_struct_cache` measurement
- `rubicon_alloc_init.json`: the Rubicon `alloc` then `init` investigation
- `mac_run.log`, `iphone_run.log`: the runners' output

Local paths are replaced with `<work>`, `<envs>` and `~`, and the phone's identifier with `<device>`.

## Fixes during collection

These were changes to this comparison's scripts or runs. The ones that change a definition are recorded there.

| Change | Why |
|---|---|
| Added a value check to every timed operation | The definitions record a wrong value in place of a time. Added before any timing run |
| Ran each operation in its own processes | pyobjus 1.2.4's `CGRect` crash would otherwise end every measurement in the process. Recorded in the definitions |
| Replaced one N for every library with an N per library | Recorded in the definitions. The first Mac timing pass, about 80 measurements, is in `superseded_mac_same_n.json` |
| Fallback N for a crashed calibration | pyobjus 1.2.4's `CGRect` calibration crashed, and the runner first gave it the largest N of any version, PyObjC's 20,000. Because pyobjus's `CGRect` calls slow down with use, each process then took 14 minutes. It now takes the other pyobjus version's N, 2,000, and the 2 completed runs at 20,000 are kept under `superseded` |
| M4 on the iPhone: 300,000 calls | 1,000,000 ran past iOS's 20-second limit for a launch. Recorded in the definitions |
| Reran 37 iPhone timing launches | The run started before the phone's Auto-Lock was set to Never, so the phone may have been in use. Those launches are kept under `superseded_timing_before_autolock` |
