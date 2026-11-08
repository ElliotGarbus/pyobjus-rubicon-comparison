# Section 6 metric definitions

**Status: approved 2026-11-08.** These definitions were written before any Section 6 data was collected. Changes made after that are recorded at the end of this document with their reasons.

Section 6 measures how fast each library makes calls in both directions, and how much memory it uses and keeps. It doesn't test whether calls are correct, which Sections 2 to 4 cover.

## What was seen before these were written

| Seen before writing (2026-11-08) | Where | Effect on the rules |
|---|---|---|
| The thread's scope for this section: "reproducible benchmarks of call overhead, callbacks, and memory consumption" | [kivy/kivy#9469](https://github.com/kivy/kivy/issues/9469#issuecomment-6591775602) | The three groups below. Startup and size are added, because both matter on a phone |
| No one in the thread claims either library is faster or slower | Search of the thread | No speed claim to test |
| Section 2 counted objects freed: pyobjus freed 0 of 1,000 `alloc` and `init` objects and 0 of 100 delegates, and Rubicon freed all of them. It didn't measure how much memory that is | [Section 2](../sections/02-architecture.md) | M3 measures the amounts, for claim 7 |
| pyobjus `master` has malloc-growth and lifecycle tests, written by this comparison's author | [Section 5](../sections/05-testing-and-ci.md) | M3 uses its own workload and measure, not those tests |
| Section 2's fixture, adapters and iPhone harness | [`tests/section-02`](../tests/section-02) | Reused where they fit, so builds and call styles match earlier sections |

No timing or memory measurement was run for this comparison before these were written.

## Versions and platforms

Each library at two points, as in earlier sections: its latest release (pyobjus `v1.2.4`, Rubicon `v0.5.7`) and its default branch at [the baseline](../results/baseline/2026-11-04.md) commit.

| Platform | Python | Builds |
|---|---|---|
| The baseline Mac (Apple Silicon) | 3.14.7 | As in Section 2: pyobjus 1.2.4 from PyPI and `master` built from source, Rubicon from PyPI and from source |
| The baseline iPhone | 3.15.0 | Section 2's iOS wheels, in a KivyForge test app without Kivy |

PyObjC 13.0 runs on the Mac as a reference point, as it did in Section 2. It isn't one of the libraries being compared.

## C. Calls from Python to Objective-C

| ID | Metric | Definition | Label |
|---|---|---|---|
| C1 | Empty call | Time per call of a fixture instance method that takes and returns nothing, written the library's usual way (`obj.noop()`), on an object created beforehand | Measured |
| C2 | Argument and return conversion | The same, for methods that take and return one value each of: `NSInteger`, `double`, `BOOL`, an object, a struct (`CGRect`), and a string passed as a Python `str` and returned as Python text by each library's documented route, at 10 and 10,000 characters. Shown beside C1, so the cost of conversion is visible | Measured |
| C3 | Class methods and properties | A class method call, a property read and a property write | Measured |
| C4 | Bound method | C1 and C2 with the method looked up once beforehand (`f = obj.noop`, then `f()`), separating the lookup from the call | Measured |
| C5 | First use | In a new process, the time from naming a fixture class not used before to the first call on it returning, which includes building the wrapper and looking up the method | Measured |

## CB. Calls from Objective-C to Python

| ID | Metric | Definition | Label |
|---|---|---|---|
| CB1 | Delegate call | Time per call when the fixture calls a Python delegate's method in a loop in Objective-C: with no arguments, with an `NSInteger` argument and return value, and with an object argument | Measured |

## M. Memory

Memory is measured as the process's physical footprint (`phys_footprint` from `task_info`), the figure iOS uses when it ends apps for using too much memory, and as Python's own allocations (`tracemalloc`).

| ID | Metric | Definition | Label |
|---|---|---|---|
| M1 | Import footprint | Footprint and Python allocations added by importing the library and wrapping `NSObject`, in a new process | Measured |
| M2 | Memory per object | Growth per live wrapper while holding 10,000 fixture objects returned by a class method | Measured |
| M3 | Memory kept after use (claim 7) | Growth that remains after creating and dropping 10,000 objects through each of `alloc` then `init`, `new`, `copy` and an ordinary method, and 1,000 delegates, once Python's garbage is collected and the autorelease pool is drained. Reported per object, beside Section 2's counts of objects freed | Measured |
| M4 | Steady state | Footprint sampled every 100,000 calls over 1,000,000 calls that return an object, to show whether ordinary calls accumulate memory | Measured |

## S. Startup and size

| ID | Metric | Definition | Label |
|---|---|---|---|
| S1 | Import time | In a new process, the time to import the library and make a first call (`NSObject.alloc().init()` or its equivalent), with Python's own startup measured separately and subtracted | Measured |
| S2 | Installed size | The installed package's size on disk for macOS and for an iPhone build, and what it adds to the test app's bundle | Measured |

## Method

- **Timing:** each timed operation runs in rounds of N calls, timed with `time.perf_counter_ns`. N is set once per operation on the Mac so a round takes at least 20 ms, and the same N is used for every library and platform. Each process runs 3 warm-up rounds and then 30 timed rounds, and each measurement uses 5 processes. The result is the median time per call over all timed rounds, with the 25th to 75th percentile range, and the medians of the 5 processes are shown so variation between processes is visible.
- **References:** each timing run also times an empty Python function call, and on the Mac the same operation through PyObjC, so the figures have a scale.
- **Garbage collection and pools:** garbage collection stays on, with a collection before each round. Loops that return objects run inside an autorelease pool that the harness drains each round, the same way for every library, since neither library creates one for the caller (Section 2).
- **Conditions:** the Mac on power, Low Power Mode off and no other user apps open. The iPhone with the test app in the foreground and Low Power Mode off. The device's thermal state is recorded at the start and end of each run, and a run that reaches "serious" is discarded and rerun, with the discard recorded.
- **Memory:** each memory measurement runs in a new process, 5 times, after a garbage collection and a pool drain at each sample point. The result is the median of the 5.

## Rules

- **Usual public API:** each library is called the way its docs show, as in Section 4. Where a library can't express an operation, the result is "not supported" rather than a workaround.
- **Same workload:** every library calls the same compiled fixture with the same arguments and N. The fixture is compiled without ARC, as in Section 2.
- **Failures are results:** a crash, hang or wrong value is recorded in place of a time, with the error.
- **No scores:** results are reported as times, sizes and ratios to the references, with no threshold for good or bad and no combined score.
- **Raw data saved:** every round's timing, every memory sample, the device conditions and the build details are saved under `results/section-06/`, with local paths replaced as in earlier sections.

## Deliberately excluded

| Measure | Why |
|---|---|
| Frame rates or timings in a real Kivy app | They depend on the app. Section 4's tasks spend most of their time in Apple's code |
| Timings on the iOS simulator | The methodology excludes them as a measure of device performance |
| Intel Macs | Out of scope for the comparison |
| Free-threaded Python and GIL contention | Section 2 measured GIL behavior |
| Build time | Section 5 covers what a build needs |
| PyObjC as a candidate | A reference point only |
| Block and function-pointer calls | pyobjus can't create either (Section 3), so there's nothing to compare. Section 4 shows the code each library needs for a block-only API |

## Claims this section reports on

| Claim ([register](../CLAIMS.md)) | Evidence |
|---|---|
| 7. pyobjus leaks memory, for example through `delegate_register` | M3 gives the amounts. Section 2 confirmed the leak on its fixture |

## Changes after approval

| Metric | Change | Reason |
|---|---|---|
