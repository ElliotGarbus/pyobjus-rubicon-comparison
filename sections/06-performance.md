# 6. Performance

**Status: draft for factual review.** Neither project has reviewed this section. Versions are in [the baseline](../results/baseline/2026-11-04.md). Metric IDs refer to the [approved definitions](../metrics/06-performance.md), which also list every change made after approval.

## Summary of findings

Rubicon is faster than pyobjus for every call measured, and the gap is largest when Objective-C calls into Python. A delegate call takes about 100 times as long with pyobjus: 73 µs against 0.7 µs on the Mac, and 128 µs against 0.9 µs on the iPhone. Calls that return an object or pass a string take 10 to 20 times as long with pyobjus, and calls that pass and return numbers 1.3 to 1.8 times as long. pyobjus starts faster: on the iPhone it imports in 5 ms against Rubicon's 44 ms, and wraps a class for the first time in 0.3 ms against 1.6 to 1.7 ms. In memory, pyobjus doesn't free objects from `alloc`, `new` or `copy`, keeps about 10 KB per delegate it has been given, and keeps 6 to 16 bytes per call that returns an object, so its memory grows with use. Rubicon's doesn't, but it uses about 12 MB more after importing on the iPhone, and 3 times as much per live wrapped object.

**pyobjus:** calls with numbers take 2.0 to 3.9 µs on the Mac and 2.4 to 4.7 µs on the iPhone. Returning an object takes 30 µs on the Mac and 55 µs on the iPhone, and a 10-character string 181 µs and 466 µs. Calls that pass a struct, such as a `CGRect`, get slower the more of them a process makes, because pyobjus adds each struct argument's address to a list it never clears and searches the whole list on every struct return. Each call adds about 4 ns to every later one, so after 10,000 such calls each takes about 40 µs longer than the first, and each keeps about 48 bytes. pyobjus 1.2.4 crashed in 3 of 5 processes on those calls, and returned the wrong value from a delegate. pyobjus imports in 5 to 7 ms and adds 0.8 MB of memory on the iPhone, and 1.1 MB to the app. Its default branch imports `traceback`, added by this comparison's author, which accounts for most of its extra import time and memory on the Mac over 1.2.4.

**Rubicon:** calls with numbers take 1.6 to 2.2 µs on the Mac and 1.8 to 2.6 µs on the iPhone, and looking the method up once beforehand cuts the empty call to 0.7 µs. Returning an object takes 2.5 µs and 2.9 µs, a 10-character string 19 µs and 24 µs, and a delegate call 0.7 µs and 0.9 µs. It freed every object, and its memory stayed flat over a million calls on the Mac. Importing it takes 21 ms on the Mac and 44 ms on the iPhone, and adds 12 to 13 MB of memory. A live wrapper takes 730 to 760 bytes, and Rubicon adds 0.24 MB to the app. 0.5.7 and `main` gave the same results.

At 60 frames a second, a frame lasts 16.7 ms. On the iPhone that's time for about 130 pyobjus delegate calls, or about 18,000 Rubicon ones, before anything else in the frame (**Inferred**, from CB1).

All figures are **Measured** on a shared fixture, not a real app, unless labeled otherwise. This section makes no recommendation. "`master`" and "`main`" mean the default branches. The Mac ran both versions of each library, and the iPhone the default branches. Times are medians of 150 rounds over 5 processes.

| Measure | pyobjus `master`, Mac | Rubicon `main`, Mac | pyobjus `master`, iPhone | Rubicon `main`, iPhone |
|---|---:|---:|---:|---:|
| [Empty method call](#c-calls-from-python-to-objective-c) | 2.0 µs | 1.6 µs | 2.4 µs | 1.8 µs |
| [Returning an object](#c-calls-from-python-to-objective-c) | 30 µs | 2.5 µs | 55 µs | 2.9 µs |
| [A 10-character string, there and back](#c-calls-from-python-to-objective-c) | 181 µs | 19 µs | 466 µs | 24 µs |
| [A delegate called from Objective-C](#cb1-calls-from-objective-c-to-python) | 73 µs | 0.7 µs | 128 µs | 0.9 µs |
| [`CGRect` calls slow down with use](#cgrect-calls-in-pyobjus) | 3.7 ns per call | No | 4.1 ns per call | No |
| [Memory kept per `alloc` then `init` object](#m-memory) | 56 B, never freed | Freed | 52 B, never freed | Freed |
| [Memory kept per delegate](#m-memory) | 10.4 KB | 0.6 KB | 9.9 KB | 0.4 KB |
| [Memory kept per call returning an object](#m-memory) | 16 B | 0 | 6.5 B | 0 |
| [Memory added by importing](#m-memory) | 4.1 MB | 11.8 MB | 0.8 MB | 12.8 MB |
| [Memory per live wrapper](#m-memory) | 226 B | 764 B | 233 B | 726 B |
| [Import and first call](#s-startup-and-size) | 7.3 ms | 21 ms | 5.1 ms | 44 ms |
| [Size added](#s-startup-and-size) | 2.0 MB (universal) | 0.24 MB | 1.1 MB | 0.24 MB |

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Relevant data |
|---|---|
| 7. pyobjus leaks memory, for example through `delegate_register` | Confirmed, with amounts. Each delegate given to Objective-C keeps about 10 KB after it's dropped, 4.5 to 4.6 KB of it Python's, on both platforms and versions. Objects from `alloc` then `init`, `new` or `copy` are never freed, keeping 36 to 69 bytes each. Ordinary calls that return an object free the object but keep 6.5 to 16 bytes per call, and calls that pass a struct keep about 48 bytes each in a list pyobjus never clears ([below](#cgrect-calls-in-pyobjus)). Rubicon freed all of these. Its delegates kept 0.4 to 0.6 KB each. |

## Supporting facts

Raw results, conditions, tools and the fixes made during collection are in [`results/section-06/2026-11-08`](../results/section-06/2026-11-08/README.md). The scripts are in [`tests/section-06`](../tests/section-06).

**How it was measured:** every library calls the same compiled fixture, [`s6fixture.m`](../tests/section-06/s6fixture.m), the way its docs show. Each operation runs in its own processes, 5 per version, each with 3 warm-up and 30 timed rounds of N calls, where N is set for each library so its rounds take at least 20 ms. Garbage collection stays on, and the harness drains an autorelease pool after each round, the same way for every library. Every operation's result was checked once in each process. The Mac is an Apple M5 Pro on AC power, and the phone an iPhone 18 Pro Max. Low Power Mode was off throughout, and 3 iPhone launches that reached a serious thermal state were rerun. An empty Python function call took 0.009 µs on the Mac and 0.011 µs on the iPhone.

### C. Calls from Python to Objective-C

Median time per call, in µs. pyobjus 1.2.4 and Rubicon 0.5.7 are within 10% of their default branches in every row, except as noted, and are in the [results](../results/section-06/2026-11-08/README.md#mac).

| Operation | pyobjus `master`, Mac | Rubicon `main`, Mac | pyobjus `master`, iPhone | Rubicon `main`, iPhone |
|---|---:|---:|---:|---:|
| C1 Empty call | 2.0 | 1.6 | 2.4 | 1.8 |
| C2 `NSInteger` | 3.1 | 2.2 | 3.9 | 2.5 |
| C2 `double` | 3.9 | 2.2 | 4.7 | 2.6 |
| C2 `BOOL` | 3.1 | 2.2 | 3.9 | 2.5 |
| C2 Object | 30.1 | 2.5 | 55.0 | 2.9 |
| C2 String, 10 characters | 181 | 19.0 | 466 | 23.6 |
| C2 String, 10,000 characters | 219 | 21.5 | 508 | 25.3 |
| C3 Class method | 2.0 | 1.8 | 2.4 | 2.1 |
| C3 Property read | 2.2 | 1.1 | 2.7 | 1.3 |
| C3 Property write | 3.6 | 1.4 | 4.5 | 1.7 |
| C4 Empty call, method looked up first | 1.9 | 0.68 | 2.3 | 0.84 |
| C4 Object, method looked up first | 30.1 | 1.8 | 55.9 | 2.2 |

- **Strings:** each library converts the Python `str` to an `NSString` and back to Python text, by its documented route: `.UTF8String()` for pyobjus, `str()` for Rubicon. The time barely depends on length in either, so most of it is per call, not per character. pyobjus 1.2.4 took 256 µs for 10,000 characters, against 219 µs for `master`.
- **Looking the method up first (C4)** saves about 0.9 µs per call in Rubicon and about 0.1 µs in pyobjus.
- **`CGRect`:** see [below](#cgrect-calls-in-pyobjus). Rubicon took 2.3 µs on the Mac and 2.7 µs on the iPhone.
- **C5 First use:** naming a fixture class for the first time and calling it took 0.15 ms with pyobjus and 0.70 ms with Rubicon on the Mac, and 0.33 ms and 1.6 to 1.7 ms on the iPhone. A class with 100 methods took no longer than one with 5, in either library.

### CB1. Calls from Objective-C to Python

The fixture calls a Python delegate's method in a loop in Objective-C. Median time per call, in µs.

| Delegate method | pyobjus 1.2.4, Mac | pyobjus `master`, Mac | Rubicon `main`, Mac | pyobjus `master`, iPhone | Rubicon `main`, iPhone |
|---|---:|---:|---:|---:|---:|
| No arguments | 67.4 | 73.1 | 0.70 | 128 | 0.90 |
| `NSInteger` argument and return | 77.2, wrong value | 91.1 | 0.78 | 150 | 0.99 |
| Object argument | 104 | 111 | 0.98 | 193 | 1.2 |

pyobjus 1.2.4 returned 0 to Objective-C instead of the delegate's value, as Section 2 found. `master` returns it, through a change by this comparison's author, and is 8 to 18% slower here than 1.2.4.

### `CGRect` calls in pyobjus

In every pyobjus process, each round of calls passing and returning a `CGRect` took longer than the last. Time per call rose in a straight line with the number of `CGRect` calls already made (r² of 0.999 or more in every process). No other pyobjus operation, and no Rubicon operation, changed over a process.

| | Added to each later call, per call made | Extrapolated first call | First timed round | Last timed round |
|---|---:|---:|---:|---:|
| pyobjus `master`, Mac | 3.7 ns | 6.6 µs | 32 µs | 249 µs |
| pyobjus 1.2.4, Mac, 2 processes that didn't crash | 3.7 ns | 15.5 µs | 40 µs | 258 µs |
| pyobjus `master`, iPhone | 4.1 ns | 7.3 µs | 24 µs | 141 µs |

Because each call's time depends on how many came before, no single figure is given for these calls.

**The cause (Source and Measured):** pyobjus keeps a module-level list, [`ctypes_struct_cache`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L2). Every struct argument passed by value appends its address to it ([line 691](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L691)), and nothing removes entries. Every struct return then checks whether its first 8 bytes are in that list ([line 263](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/pyobjus/pyobjus_conversions.pxi#L263)), which compares against each entry in turn. The code dates from 2013 and is the same in 1.2.4. [`cgrect_cache.py`](../tests/section-06/cgrect_cache.py) confirms it on the Mac with pyobjus `master`, in 3 processes that agreed within 3%:

| | Time per `echoRect:` call |
|---|---:|
| First 1,000 calls, list empty | 7.0 µs |
| 1,000 calls with 19,000 to 20,000 entries | 76 µs |
| 1,000 calls after clearing the list | 7.0 µs |

The list grew by one entry per call, and each call kept about 48 bytes of Python memory, an integer and its place in the list. That memory is in addition to what M3 and M4 measured, since neither passes a struct. The check also compares the returned struct's first 8 bytes, for a `CGRect` the bits of `origin.x`, with stored addresses, so a value that happened to match one would be read as a pointer (**Inferred**, from the code). pyobjus 1.2.4 crashed in all 3 processes before finishing.

pyobjus 1.2.4 also crashed in 3 of 5 processes for each `CGRect` operation: in the two crash reports macOS kept, the allocator stopped the process, once inside pyobjus and once in the Objective-C runtime. That fits heap corruption from the struct argument overrun that pyobjus `master`'s Guard Malloc test checks for (Section 5, **Inferred**).

### M. Memory

Footprint is the process's physical footprint, the figure iOS uses when it ends apps for memory. It grows in 16 KB pages, so a few bytes per object is within one page. Median of 5 processes.

| | pyobjus `master`, Mac | Rubicon `main`, Mac | pyobjus `master`, iPhone | Rubicon `main`, iPhone |
|---|---:|---:|---:|---:|
| M1 Import, footprint | 4.1 MB | 11.8 MB | 0.82 MB | 12.8 MB |
| M1 Import, Python's share | 2.2 MB | 6.1 MB | 0.35 MB | 5.7 MB |
| M2 Per live wrapper | 226 B | 764 B | 233 B | 726 B |
| M3 Kept per `alloc` then `init` object | 56 B, 0 of 10,000 freed | All freed | 52 B, 0 freed | All freed |
| M3 Kept per `new` object | 38 B, 0 freed | All freed | 36 B, 0 freed | All freed |
| M3 Kept per `copy` object | 38 B, 0 freed | All freed | 38 B, 0 freed | All freed |
| M3 Kept per object from an ordinary method | 21 B, 9,999 freed | All freed | 21 B, 9,999 freed | All freed |
| M3 Kept per delegate | 10.4 KB, 4.6 KB of it Python's | 573 B | 9.9 KB, 4.5 KB Python's | 426 B |
| M4 Kept per call returning an object | 16 B | 0 | 6.5 B | 0 |

- **pyobjus 1.2.4** was within 25 bytes of `master` per object in M2 to M4, and Rubicon 0.5.7 matched `main`. pyobjus 1.2.4 added 0.57 MB on import, against `master`'s 4.1 MB.
- **Import memory (M1):** on the Mac, most of pyobjus `master`'s extra over 1.2.4 is `traceback` and the modules it loads, such as `inspect` (**Inferred**, from `python -X importtime` and the modules each version loads). `master` imports it to print exceptions raised in delegate methods, a change by this comparison's author. The iPhone app's entry point imports `traceback` before measuring, so the iPhone figures leave it out for both libraries.
- **pyobjus M4:** the returned objects were freed, as in Rubicon (pyobjus 999,999 and Rubicon 1,000,000 of 1,001,000 at the last sample), yet pyobjus's footprint kept growing, outside Python's allocations. The iPhone made 300,000 calls instead of 1,000,000 to stay within iOS's 20-second limit for a launch, and its samples dipped once before rising, so its figure is less steady.

### S. Startup and size

| | pyobjus 1.2.4, Mac | pyobjus `master`, Mac | Rubicon, Mac | pyobjus `master`, iPhone | Rubicon `main`, iPhone |
|---|---:|---:|---:|---:|---:|
| S1 Import and first call, inside the process | 1.8 ms | 7.3 ms | 21 ms | 5.1 ms | 44 ms |
| S1 Wall clock, less an empty Python process | 6.2 ms | 13 ms | 30 ms | | |
| S2 Installed size | 1.6 MB | 2.0 MB | 0.24 MB | 1.1 MB added to the app | 0.24 MB added |

On the Mac, both pyobjus builds are universal, holding arm64 and x86_64 code. On the iPhone, pyobjus's figure includes the framework holding its compiled extension, 0.96 MB. Both S1 measurements start after the harness has imported its own modules, such as `ctypes`, so those aren't counted for either library.

## Limits of this section

- **These are calls to a test fixture, not app workloads.** A real API call also spends time in Apple's code, which is the same for both libraries, so the share of an app's time spent in the bridge depends on the app.
- **Each library is used the way its docs show.** Other styles may be faster, as looking a method up first shows for Rubicon.
- **The iPhone measured the default branches only,** at the author's decision. The Mac measured both versions, and they matched closely apart from the differences noted.
- **Memory is measured in pages.** Figures of a few bytes per object are within one 16 KB page and shouldn't be read as differences.
- **The harness imports some modules before measuring,** including `ctypes`, and on the iPhone `traceback`. Import figures count only what each library adds beyond those.
- **The cause of one result wasn't investigated:** pyobjus's memory growth on calls whose objects are freed.
- **This comparison's author wrote changes in pyobjus `master` that affect these results:** the `traceback` import and the delegate return values.
