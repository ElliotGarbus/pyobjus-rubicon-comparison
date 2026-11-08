# 5. Testing and CI

**Status: draft for factual review.** Neither project has reviewed this section. Versions are in [the baseline](../results/baseline/2026-11-04.md). Metric IDs refer to the [approved definitions](../metrics/05-testing-and-ci.md), which also list every change made after approval.

## Summary of findings

The key differences are iOS testing and what reaches PyPI. Rubicon runs its full test suite on the iOS simulator in CI. pyobjus has no iOS tests: its CI builds iOS wheels without testing them. Rubicon tests the exact wheel it publishes, on macOS and iOS. pyobjus runs its suite on macOS only, against a build from source rather than its wheels. Its release workflow, run separately, checks the macOS wheels it publishes only by importing the package. Rubicon publishes through trusted publishing, after a maintainer publishes a draft GitHub release, and PyPI holds provenance for its files. pyobjus uploads on a tag push with an API token, without provenance. pyobjus also needs a compiled wheel for each Python version and platform, and libffi built from source for iOS. Rubicon ships one pure-Python wheel.

**pyobjus:** CI runs the suite on Apple Silicon and Intel Macs, Python 3.10 to 3.14, on every push and pull request. The release, 1.2.4, has the same 82 test functions as every release since 2022, no memory tests and no coverage measure. `master` has 200, measures coverage at 76.8% of Cython and Python lines, and adds leak, heap-overrun and object-lifecycle tests. Neither version tests introspection, though pyobjus supports it. 120 of those 200 tests, including all the memory tests, were added in October 2026 by this comparison's author, and no release includes them yet. Six of the lifecycle tests are expected failures, recording that objects created through `alloc`, `new` or `copy` aren't freed. In the 12 months before the baseline, pushes to `master` came in three months, and 6 test runs failed around the 1.2.4 release, for reasons GitHub's expired logs no longer show.

**Rubicon:** CI runs the suite on Apple Silicon and Intel Macs and on the iOS simulator, Python 3.11 to 3.15, on every push and pull request. The release, 0.5.7, and `main` have 335 and 364 test functions, and measure coverage at 89.7% and 92.4% of Python lines and branches. Its memory tests check object lifecycles and retain counts, with no heap-level tests. It doesn't test implementing an Apple protocol, selector targets or Grand Central Dispatch, and tests out parameters and function pointers only in part, though Rubicon supports all of them. In the 12 months before the baseline, pushes to `main` came in every month, and no unit-test job failed. Toga's CI also runs the latest Rubicon release through Toga's own tests on the iOS simulator.

Neither suite tests Swift or runs on a device. All figures are **Measured** on the baseline Mac with Python 3.14 unless labeled otherwise. This section makes no recommendation. "`master`" and "`main`" mean the default branches.

| Topic | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` |
|---|---|---|---|---|
| [iOS tests](#t4-on-the-ios-simulator) | None | None | Full suite on the simulator, in CI | The same as Rubicon 0.5.7 |
| [Published files tested with the suite](#k3-b1-and-b2-releases) | None. macOS wheels are import-tested, iOS wheels untested | The same as pyobjus 1.2.4 | The wheel, on macOS and the iOS simulator | The same as Rubicon 0.5.7 |
| [Publishing](#k3-b1-and-b2-releases) | API token, on a tag push. No provenance | The same as pyobjus 1.2.4 | Trusted publishing, after a maintainer publishes a draft release. Provenance on PyPI | The same as Rubicon 0.5.7 |
| [Memory tests](#t5-memory-testing) | None | Leak, heap-overrun and lifecycle tests | Lifecycle and retain tests | The same as Rubicon 0.5.7 |
| [Coverage](#t3-coverage), each project's own measure | None | 76.8% of Cython and Python lines | 89.7% of Python lines and branches | 92.4% |
| [Section 3 features supported and tested](#t2-features-tested) | 10 of 20 | 14 of 20 | 17 of 31 | The same as Rubicon 0.5.7 |
| [Pushes to the default branch, 12 months](#k2-ci-results) | — | 50, in 3 months | — | 179, in every month |

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Relevant data |
|---|---|
| 14. Rubicon CI runs on Python 3.11 to 3.16, including iOS | Confirmed for 3.11 to 3.15, on macOS and the iOS simulator, at 0.5.7 and `main`. No version of Rubicon's CI workflow has listed 3.16, up to its latest commit on 2026-11-06. Rubicon's code and tests have conditions for 3.16. |
| 15. pyobjus has no iOS tests in CI and no systematic leak testing | iOS: confirmed at both versions. CI builds iOS wheels and doesn't test them, and the suite has no iOS route. Leak testing: 1.2.4 has no memory tests. `master` has leak, heap-overrun and lifecycle tests that CI runs, added in October 2026 by this comparison's author, who also made the claim. Whether they're systematic is left to the reader. Outside pyobjus's own CI, kivy-ios's CI compiles pyobjus `master` for iOS and launches a minimal Kivy app on the simulator, though whether that app loads pyobjus hasn't been measured, while Toga's CI runs released Rubicon through its test suite on the simulator ([K1](#k1-what-ci-runs)). |
| 16. Each pyobjus release needs separate wheels per Python version and platform (11 for 1.2.4), while Rubicon ships one `py3-none-any` wheel | Build side confirmed. Each pyobjus wheel is compiled with Cython for one Python version, and iOS wheels for one architecture each, against libffi 3.5.2 built in CI. Rubicon's single wheel needs no compiler. Section 1 confirmed the file counts. |

## Supporting facts

Raw results, tools, redactions and the fixes made during collection are in [`results/section-05/2026-11-08`](../results/section-05/2026-11-08/README.md). The scripts are in [`tests/section-05`](../tests/section-05). pyobjus is read at [`v1.2.4`](https://github.com/kivy/pyobjus/tree/v1.2.4) and [`0c204ad`](https://github.com/kivy/pyobjus/tree/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81), and Rubicon at [`v0.5.7`](https://github.com/beeware/rubicon-objc/tree/v0.5.7) and [`6bf0639`](https://github.com/beeware/rubicon-objc/tree/6bf06390f720226da3d51477f38de3ff1e680eaf).

### T1 and T4. Size and results

Each suite ran 3 times, each time from a clean checkout and a new environment, with the project's own CI steps. For pyobjus that's `pip install -e .`, `make test_lib` and `pytest tests -v`. For Rubicon it's `tox -e py314-cov`, which builds the wheel and installs it.

| | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` |
|---|---:|---:|---:|---:|
| Collected | 84 | 202 | 595 | 624 |
| From parameterized tests | 4 cases, from 2 tests | 4, from 2 | 315, from 53 | 315, from 53 |
| Passed | 78 | 194 | 587 | 609 |
| Skipped | 6 | 2 | 8 | 15 |
| Expected failures | 0 | 6 | 0 | 0 |
| Failed or errored | 0 | 0 | 0 | 0 |
| Lines of Python test code | 714 | 2,211 | 3,055 | 3,294 |
| Lines of Objective-C in the test library | 1,118 | 1,180 | 582 | 582 |

Lines are counted as in Section 4, after `ruff format`, without blank lines, comments, docstrings and imports.

- **pyobjus skips:** 1.2.4 skips `test_carray_struct` ("issue with signature that looks invalid, therefore it crash"), 2 `test_nsvalue` tests ("Segfault since a long time") and 3 `test_unknown_types` tests ("Segfault, TBF"). `master` runs the `test_carray_struct` and `test_unknown_types` tests, and they pass.
- **pyobjus expected failures:** [`test_object_lifecycle.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_object_lifecycle.py#L56) checks with a weak reference that an object is deallocated once its wrapper is gone. Objects returned by an ordinary method pass. Six cases are marked `expectedFailure`: `alloc`, `alloc` then `init`, `new`, `copy`, `mutableCopy`, and an `init` that returns a different object. Section 2 measured the same leak.
- **Rubicon skips:** all name a Python version. 0.5.7 skips 8 tests of `ctypes` internals that changed in Python 3.13. `main` skips 9 of those, 5 `asyncio` tests for APIs Python 3.14 removed, and 1 whose reason names 3.16.

### T4 on the iOS simulator

Rubicon's [`tox.ini`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tox.ini#L67) has an iOS environment that builds the test library for the simulator and runs the suite inside Briefcase's testbed app, with `briefcase run iOS --test`. It ran 3 times for each version on an iPhone 17e simulator with iOS 27.0, using Python 3.14 from Briefcase's support package.

| | Rubicon 0.5.7 | Rubicon `main` |
|---|---:|---:|
| Passed | 584 | 606 |
| Skipped | 11 | 18 |
| Failed or errored | 0 | 0 |

The same tests were collected as on the Mac, and 3 more were skipped at each version. Rubicon's `briefcase` dependency group installs Briefcase from its GitHub default branch without a pin, so the iOS route depends on Briefcase's state when it runs.

pyobjus has no iOS test route. Its release workflow builds iOS wheels with `cibuildwheel` and has the test step [commented out](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/.github/workflows/deploy.yml#L43), noting that the tests would need to be in the package. Section 3 ran its own cases on an iPhone for both libraries.

### T3. Coverage

| Version | Method | Result |
|---|---|---|
| pyobjus 1.2.4 | None | — |
| pyobjus `master` | Its CI's coverage job: Cython line tracing (`PYOBJUS_COVERAGE=1`) and `pytest --cov`, counting Cython and Python lines | 76.8%, 1,526 of 1,988 lines |
| Rubicon 0.5.7 | `tox -e coverage314`: Python lines and branches, without lines marked for other Python versions or for iOS | 89.7%. 181 of 2,266 statements missed, 86 of 690 branches partly covered |
| Rubicon `main` | The same | 92.4%. 131 missed, 71 of 682 branches partly covered |

AndreMiras, a pyobjus maintainer, [added](https://github.com/kivy/pyobjus/commit/e8524ab) the coverage job in October 2026, and it uploads to Coveralls. Rubicon's CI also combines its macOS runs into a project coverage report.

### T2. Features tested

For each Section 3 row, whether the project's own suite has a test that calls the feature. F6.1, declared platforms, isn't a behavior, and K1 and T4 cover where each suite runs. Each status links to one such test in [`features_tested.json`](../results/section-05/2026-11-08/raw/features_tested.json).

| Status | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 and `main` |
|---|---:|---:|---:|
| Tested | 10 | 14 | 17 |
| Partly tested | 2 | 1 | 5 |
| Used only to set up other tests | 1 | 0 | 1 |
| Not tested | 7 | 5 | 8 |
| Not supported (Section 3) | 16 | 16 | 5 |

| Row | pyobjus 1.2.4 | pyobjus `master` | Rubicon |
|---|---|---|---|
| F1.1 to F1.3 Classes, properties, variadic methods | Tested | Tested | Tested |
| F1.4 Global constants | Not supported | Not supported | [Tested](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tests/test_const.py#L8) |
| F1.5 C functions | Not supported | Not supported | Partly. Runtime functions through Rubicon's own bindings, no framework function |
| F1.6 Loading code | Setup only | [Tested](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_load_framework.py#L37) | Setup only |
| F1.7 Introspection | Not tested | Not tested | Not supported |
| F2.1 Structs | Tested | Tested | Tested |
| F2.2 Unions and bit fields | [Tested](https://github.com/kivy/pyobjus/blob/v1.2.4/tests/test_union.py#L24), returned unions | Tested, and a clear error for bit fields | Partly. Type-encoding conversion, no union passed to a method |
| F2.3 C arrays | [Tested](https://github.com/kivy/pyobjus/blob/v1.2.4/tests/test_carray.py#L40) | Tested | Partly. Conversion, no array passed to a method |
| F2.4 Out parameters | Tested, a count written back | Tested | [Partly](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tests/test_partial_method.py#L33). Pointers are passed and the bytes written to a buffer are checked, not the scalar values. No `NSError **` |
| F2.5 Collections | Tested, explicit conversion | Tested | Tested |
| F2.6 Python behavior on Objective-C objects | Not supported | Not supported | Tested |
| F2.7 Enums and constants | Not tested | [Tested](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_downstream_call_shapes.py#L47) | Tested |
| F3.1 to F3.3 New classes, subclasses, instance state | Not supported | Not supported | Tested |
| F3.4 Apple protocol | [Tested](https://github.com/kivy/pyobjus/blob/v1.2.4/tests/test_delegate.py#L90), `NSURLConnectionDelegate` | Tested | Not tested. Apple's protocols are checked with `isinstance` and `issubclass`, but none is implemented |
| F3.5 Protocol not known in advance | Tested, no delegate call received | Tested, the same | Tested |
| F3.6 Selector targets | Partly. Observers registered, no notification posted | Partly, the same | Not tested |
| F3.7 Delegate values | Partly, object arguments only | [Tested](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_delegate_returns.py#L248) | Tested |
| F3.8 Removing a delegate | Not supported | Not supported | Not supported, automatic |
| F4.1, F4.2 Blocks | Not supported | Not supported | [Tested](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tests/test_blocks.py#L130) |
| F4.3 GCD | Not supported | Not supported | Not tested |
| F4.4 Function pointers | Not supported | Not supported | [Partly](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tests/test_ctypes_patch.py#L11). Python functions become C function pointers and are called, but none is passed to a C or Objective-C function |
| F5.1 Memory management | Not tested | Tested (T5) | Tested (T5) |
| F5.2 Exceptions, F5.4 Main thread | Not supported | Not supported | Not supported |
| F5.3 Event loops | Not supported | Not supported | [Tested](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tests/test_async.py#L41) |
| F7.1 to F7.5 Swift | Not tested. `async` not supported | Not tested, the same | Not tested |
| F7.6 Swift-only APIs | Not supported | Not supported | Not supported |

Rows are grouped where every version has the same status. Rubicon 0.5.7 and `main` match in every row.

### T5. Memory testing

| Version | Tests | What they check |
|---|---|---|
| pyobjus 1.2.4 | None | — |
| pyobjus `master` | 3 in [`test_call_memory.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_call_memory.py#L30), and `test_carray_char_ptr_args_do_not_leak` in [`test_carray.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_carray.py#L134) | Heap bytes in use, from `malloc_zone_statistics`, don't grow across repeated calls that raise, return their receiver, or pass arguments by reference or as `char *` |
| | `test_nested_lists_stay_in_bounds` in [`test_reentrant_call.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_reentrant_call.py#L62), `test_rect_arg_does_not_overrun_heap` in [`test_struct_arg_by_value.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_struct_arg_by_value.py#L122) | A script runs under Guard Malloc (`/usr/lib/libgmalloc.dylib`), which crashes on a heap overrun. Skipped if Guard Malloc isn't installed |
| | 7 in [`test_object_lifecycle.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_object_lifecycle.py#L53) | An object is deallocated once its wrapper is gone. 1 passes and 6 are expected failures (T4) |
| | `test_weak_reference_to_a_wrapper` in [`test_objc_instance_identity.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_objc_instance_identity.py#L79), 2 in [`test_delegate_returns.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_delegate_returns.py#L274) | A wrapper is freed when unreferenced, and objects returned from delegate methods have the expected retain counts |
| Rubicon 0.5.7 and `main` | 11 in [`test_ObjCInstance.py`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tests/test_ObjCInstance.py#L127) | Objects from ordinary methods, `alloc`, `alloc` then `init`, `new`, `copy`, `mutableCopy`, a copy of an immutable object and an `init` that returns a different object are retained and released correctly, `dealloc` runs, and Python attributes stay alive with their object and are freed with it |
| | 4 in [`test_ObjCClass.py`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tests/test_ObjCClass.py#L343) | Strong and weak properties retain and release their values |

CI runs all of them. In the baseline commit's pyobjus CI run, both Guard Malloc tests passed on Apple Silicon and Intel with Python 3.14 (logs in [`ci_logs`](../results/section-05/2026-11-08/raw/ci_logs)).

### T6. Test history

Test functions are counted from each release's source. pyobjus 1.2.1 to 1.2.3 don't build on Python 3.14, and Rubicon 0.5.1 and earlier have one test module that doesn't import on 3.14, so collected counts for those releases are partial or missing. The full table is in the [results](../results/section-05/2026-11-08/README.md#t6-test-history).

| pyobjus | Test functions | | Rubicon | Test functions |
|---|---:|---|---|---:|
| 1.2.1 (2022-03) | 82 | | 0.4.3 (2022-12) | 246 |
| 1.2.2 (2023-05) | 82 | | 0.4.7 (2023-10) | 267 |
| 1.2.3 (2023-10) | 82 | | 0.5.0 (2025-01) | 284 |
| 1.2.4 (2025-12) | 82 | | 0.5.3 (2025-12) | 284 |
| | | | 0.5.4 (2026-05) | 287 |
| | | | 0.5.7 (2026-09) | 335 |
| `master` (2026-10) | 200 | | `main` (2026-11) | 364 |

Each default-branch test function is attributed to the first commit that added a test of its name. `git blame`, the approved method, credited all 364 of Rubicon's tests to its March 2026 migration to pytest, so it was replaced, as recorded in the definitions.

| | pyobjus `master` | Rubicon `main` |
|---|---|---|
| Added in the 12 months before the baseline | 120 of 200 | 208 of 364 |
| Added by this comparison's author | 120, all in October 2026 | 0 |
| Net change over the 12 months | +118, from 82 at 1.2.4 | +80, from 284 at 0.5.3 |

A renamed test counts as new. 128 of Rubicon's 208 come from two March 2026 refactoring PRs that renamed tests, the pytest migration ([#722](https://github.com/beeware/rubicon-objc/pull/722)) and a `test_core.py` refactor ([#730](https://github.com/beeware/rubicon-objc/pull/730)), so the net change is the better measure of growth there. Most of the rest came from [#820](https://github.com/beeware/rubicon-objc/pull/820) and [#836](https://github.com/beeware/rubicon-objc/pull/836), which added tests for type encodings and the event loop.

### K1. What CI runs

| Job | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 and `main` |
|---|---|---|---|
| Unit tests, macOS | `macos-latest` (Apple Silicon) and `macos-15-intel`, Python 3.10 to 3.14, on an editable source build | The same | `macos-26` (Apple Silicon) and `macos-26-intel`, Python 3.11 to 3.15, plus `macos-15` with 3.11, on the built wheel |
| Unit tests, iOS | None | None | iOS simulator on `macos-26`, Python 3.11 to 3.15, on the built wheel |
| Coverage | None | Cython and Python lines, on the `macos-latest` 3.14 job, uploaded to Coveralls | Per run, and combined across macOS runs |
| Other checks | None | The headless examples on `macos-latest`, and an Ubuntu job checking that installing fails with a clear error | Pre-commit hooks, a towncrier change note, docs spelling |
| Packaging | All wheels and the sdist built on every push and pull request | The same | Wheel and sdist built once per run |

Both run on pushes and pull requests. The examples and unsupported-platform jobs were added by this comparison's author ([`d1f7624`](https://github.com/kivy/pyobjus/commit/d1f7624), [`50df29c`](https://github.com/kivy/pyobjus/commit/50df29c)). Rubicon 0.5.7's [`ci.yml`](https://github.com/beeware/rubicon-objc/blob/v0.5.7/.github/workflows/ci.yml) differs from `main`'s only in pinned action versions. Section 1 gives when each Python version first entered each project's CI.

Workflows: pyobjus [`python-package.yml`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/.github/workflows/python-package.yml) and [`deploy.yml`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/.github/workflows/deploy.yml); Rubicon [`ci.yml`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/.github/workflows/ci.yml), [`release.yml`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/.github/workflows/release.yml) and [`publish.yml`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/.github/workflows/publish.yml).

**Downstream CI.** Each library is also built for iOS in the CI of a project that depends on it. This covers only that, and Section 7 covers dependents in full. Data is in [`downstream_ci.json`](../results/section-05/2026-11-08/raw/downstream_ci.json).

| | pyobjus, in kivy-ios | Rubicon, in Toga |
|---|---|---|
| Dependency | kivy-ios's [Kivy recipe](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/kivy/__init__.py#L21), the route pyobjus's iOS docs describe | Toga's [iOS backend](https://github.com/beeware/toga/blob/dd833f156e13d15ed26720ef50b8e544046619c5/iOS/pyproject.toml#L117), `rubicon-objc >= 0.5.1, < 0.6.0` |
| Version used | `master`, downloaded when the job runs | The newest matching release on PyPI, 0.5.7 at the baseline |
| What runs | [`kivy_ios.yml`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/.github/workflows/kivy_ios.yml) compiles pyobjus for iOS devices and the simulator, and builds Kivy's Touchtracer example without running it. On Apple Silicon, [`test_simulator_startup.py`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/.ci/test_simulator_startup.py) launches kivy-ios's own [startup app](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/tests/test_startup/main.py), a bare Kivy widget, on the simulator, where it must reach Kivy's event loop and then stops. Whether it loads pyobjus hasn't been measured. kivy-ios's [`ios` module](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/ios/src/ios.pyx#L221) imports pyobjus and calls it when loaded, and Kivy loads that module on iOS for screen density and keyboard height. The startup app needs neither, and Kivy's first keyboard-height update is timed for 0.5 seconds after the window opens, after the app has stopped (**Inferred**, from the source) | [`ci.yml`](https://github.com/beeware/toga/blob/dd833f156e13d15ed26720ef50b8e544046619c5/.github/workflows/ci.yml) runs Toga's testbed app and its test suite on the iOS simulator. Toga's iOS widgets call iOS through Rubicon |
| At the last commit before the baseline | `fd363d4` (2026-10-20): [succeeded](https://github.com/kivy/kivy-ios/actions/runs/39490576806), and the startup app reached the event loop on an iPhone 17 Pro simulator | `dd833f1` (2026-11-03): [succeeded](https://github.com/beeware/toga/actions/runs/41652092131), with 472 passed, 130 skipped and 65 expected failures on an iPhone 17e simulator with iOS 26.5 |
| Push runs in the 12 months before the baseline | 20, from April to October 2026 | 707 |
| Started by changes to the library | No | No |

### K2. CI results

Runs triggered by pushes to each default branch from 2025-11-04 to the baseline, as GitHub recorded them.

| | pyobjus | Rubicon |
|---|---|---|
| Pushes | 50: 11 in December 2025, 2 in July 2026, 37 in October 2026 | 179, in every month |
| Runs | 100: one test and one deploy run per push | 179 |
| Succeeded | 94 | 99 |
| Failed | 6, all test runs | 5 |
| Cancelled | 0 | 75, 74 of them superseded by a newer push |
| Baseline commit | Both [succeeded](https://github.com/kivy/pyobjus/actions/runs/41220927715) | [Succeeded](https://github.com/beeware/rubicon-objc/actions/runs/41398512326) |

- **pyobjus failures:** one on 2025-12-16 and five on 2025-12-29, the day 1.2.4 was released. Each was a single unit-test job on `macos-latest`, with Python 3.12, 3.14, 3.11, 3.11, 3.10 and 3.13. The deploy workflow succeeded for the same pushes. GitHub no longer has the logs, so the cause isn't known.
- **Rubicon failures:** packaging (2026-02-22), docs linting (3 runs, March to July 2026) and the project coverage job (2026-09-09). No unit-test job failed.
- **Cancellations:** Rubicon's `ci.yml` cancels a running workflow when a newer one starts for the same branch, so a quick series of merges leaves only the last run complete.

### K3, B1 and B2. Releases

| | pyobjus | Rubicon |
|---|---|---|
| Build tools | Cython (`cython>3`), setuptools and a C compiler. iOS wheels link libffi 3.5.2, which [`build_ios_dependencies.sh`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/.ci/build_ios_dependencies.sh) downloads and builds. macOS wheels link the system's libffi | setuptools and setuptools_scm, at pinned versions (84.0.0 and 10.2.3 for 0.5.7). No compiler |
| Files built | 5 macOS `universal2` wheels (cp310 to cp314) and 6 iOS wheels (cp313 and cp314, for the device and two simulator architectures) with `cibuildwheel` (3.3.0 for 1.2.4, 3.4.1 at `master`), and an sdist | One `py3-none-any` wheel and an sdist, built by BeeWare's shared [`python-package-create.yml`](https://github.com/beeware/.github/blob/4e0b8b4/.github/workflows/python-package-create.yml) with `hynek/build-and-inspect-python-package` |
| Tests on the release files | macOS wheels: an import of `autoclass` and `objc_str`. iOS wheels: none. sdist: installed and imported, after the upload to PyPI | The wheel: the full suite on macOS and the iOS simulator. The sdist isn't tested |
| What starts a release | Pushing a tag. The deploy workflow uploads to a GitHub release and to PyPI in one run | Pushing a `v*` tag runs CI on the wheel, checks the docs build and the version number, creates a draft GitHub release and publishes to TestPyPI. Publishing the draft release runs `publish.yml`, which uploads the same files to PyPI |
| Upload to PyPI | `twine` with an API token stored as a secret | Trusted publishing, through `pypa/gh-action-pypi-publish` |
| Provenance on PyPI | None for any of 1.2.4's 12 files | Both of 0.5.7's files, with `beeware/rubicon-objc`'s `publish.yml` as publisher |

pyobjus's suite never runs against a wheel. Its unit tests use an editable build from source, and its release workflow builds the wheels separately, so the macOS wheels users install from PyPI are checked only by the import, and the iOS wheels not at all. Rubicon's shared packaging workflow is referenced at `@main`, so a change to it affects Rubicon's next build. It was at commit `4e0b8b4` on 2026-11-02.

## Limits of this section

- **Each project measures coverage its own way.** pyobjus's figure includes Cython, and Rubicon's leaves out code for other Python versions and for iOS. They aren't one comparable number.
- **Feature coverage is judged by reading the suites.** T2 counts a row as tested if one test calls it, so it doesn't measure how thoroughly. The cited tests are linked so readers can check.
- **Test counts depend on style.** Rubicon parameterizes more, which raises its collected count. pyobjus `master` has 56 subtests, which pytest doesn't count as collected tests.
- **The iOS runs were on the simulator.** Neither project runs its suite on a device. Sections 3 and 4 ran their own cases on an iPhone.
- **pyobjus's CI logs from December 2025 have expired,** so its 6 failures can't be diagnosed.
- **This comparison's author wrote most of pyobjus `master`'s tests, its memory tests and two of its CI jobs.** Those parts of the results describe the author's work, and a maintainer's review of them is welcome.
