# Section 5 results, 2026-11-08

Library versions are in [the baseline](../../baseline/2026-11-04.md). The scripts are in [`tests/section-05`](../../../tests/section-05), and each one's docstring gives its usage. Metric IDs refer to the [approved definitions](../../../metrics/05-testing-and-ci.md), which also list the changes made after approval.

## Status

| Part | Status |
|---|---|
| T1 size: collected tests and lines of test code | Done: `raw/mac.json`, `raw/test_lines.json` |
| T2 features tested | Done: `raw/features_tested.json` |
| T3 coverage | Done: `raw/mac.json`, with the reports in `raw/mac_logs` |
| T4 on the Mac, 3 runs each | Done: `raw/mac.json`. Every suite gave the same result in all 3 runs |
| T4 on the iOS simulator, 3 runs each | Done for Rubicon: `raw/ios_sim.json`. Same result in all 3 runs. pyobjus has no iOS test route |
| T5 memory testing | Done, from reading each suite. Listed in the section |
| T6 test history | Done: `raw/test_history.json` |
| K1 CI jobs, K3 release testing, B1 build inputs | Done, from the pinned workflow files. Listed in the section |
| K2 CI results | Done: `raw/ci_history.json`, `raw/ci_details.json` |
| K1 downstream CI, kivy-ios and Toga | Done: `raw/downstream_ci.json`. Added after approval, as the definitions record |
| B2 release process | Done: `raw/release_files.json` and the pinned workflow files |
| Section text | Draft |

## Results

### T1 and T4 on the Mac

Python 3.14.7 on the baseline Mac. Each run started from a clean checkout and a new environment, using the project's own CI steps (see [`run_mac.py`](../../../tests/section-05/run_mac.py)).

| | pyobjus 1.2.4 | pyobjus `master` | Rubicon 0.5.7 | Rubicon `main` |
|---|---:|---:|---:|---:|
| Collected | 84 | 202 | 595 | 624 |
| Passed | 78 | 194 | 587 | 609 |
| Skipped | 6 | 2 | 8 | 15 |
| Expected failures | 0 | 6 | 0 | 0 |
| Failed or errored | 0 | 0 | 0 | 0 |
| Collected cases from parameterized tests | 4, from 2 tests | 4, from 2 tests | 315, from 53 tests | 315, from 53 tests |
| Lines of Python test code | 714 in 14 files | 2,211 in 32 files | 3,055 in 21 files | 3,294 in 22 files |
| Lines of Objective-C in the test library | 1,118 in 3 files | 1,180 in 3 files | 582 in 16 files | 582 in 16 files |

**Skips:**
- **pyobjus 1.2.4:** 6 tests are skipped by the suite itself, with reasons such as "Segfault since a long time" (`test_nsvalue`: `test_objCType`, `test_valueWithRect`), "Segfault, TBF" (3 tests in `test_unknown_types`) and a crash on an invalid signature (`test_carray_struct`).
- **pyobjus `master`:** the 2 `test_nsvalue` skips remain. The other 4 now run and pass.
- **Rubicon:** every skip is for a Python version. 0.5.7 skips 8 tests of `ctypes` internals that changed in Python 3.13. `main` skips 9 of those, 5 `asyncio` tests for APIs removed in Python 3.14, and 1 whose reason says the API is removed in 3.16.

**Expected failures, pyobjus `master`:** the 6 tests in [`test_object_lifecycle.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/tests/test_object_lifecycle.py) marked `expectedFailure` (`test_alloc`, `test_alloc_init`, `test_new`, `test_copy`, `test_mutable_copy`, `test_init_returning_another_object`). Each checks that an object is freed once its Python wrapper is gone, which pyobjus [#194](https://github.com/kivy/pyobjus/issues/194) reports it isn't.

**Line counts** use Section 4's method: Python is formatted with `ruff format` (ruff 0.6.9), then blank lines, comments, docstrings and imports aren't counted. Python is every `.py` file under `tests/`. Objective-C is the test library each suite compiles (`objc_classes/test` in pyobjus, `testbed/objc` in Rubicon), not reformatted, without blank lines, comments and imports. [`count_tests.py`](../../../tests/section-05/count_tests.py) does both.

### T4 on the iOS simulator

Rubicon's own route, `tox -e py314-iOS`, which builds the wheel and runs the suite in Briefcase's testbed app (see [`run_ios_sim.py`](../../../tests/section-05/run_ios_sim.py)). CI runs the same environment with `-ci`, which uses the wheel from its package job.

| | Rubicon 0.5.7 | Rubicon `main` |
|---|---:|---:|
| Passed | 584 | 606 |
| Skipped | 11 | 18 |
| Failed or errored | 0 | 0 |

The simulator was an iPhone 17e on iOS 27.0, with Python 3.14.10 from Briefcase's support package (`Python-3.14-iOS-support.b14`) and Briefcase at commit `d94b1eb06d55d1cf01559f8818b1df0625a3ea3d`. Rubicon's `briefcase` dependency group installs Briefcase from its GitHub default branch without a pin, so this is the commit that was current on 2026-11-08. The same number of tests is collected as on the Mac, and 3 more are skipped at each version. The counts come from the testbed's verbose output, and match pytest's own summary line in every run.

### T3 coverage

Each project's own setup, so the figures measure different things and aren't one comparable number.

| Version | Method | Result |
|---|---|---|
| pyobjus 1.2.4 | None. No coverage setup at this version | — |
| pyobjus `master` | The coverage job in `python-package.yml`: Cython line tracing (`PYOBJUS_COVERAGE=1`), Cython and Python lines | 76.8%: 1,526 of 1,988 lines |
| Rubicon 0.5.7 | `tox -e coverage314` on the last run's data: Python lines and branches, without lines marked as specific to other Python versions or to iOS | 89.7%: 181 of 2,266 statements missed, 86 of 690 branches partial |
| Rubicon `main` | The same | 92.4%: 131 of 2,266 statements missed, 71 of 682 branches partial |

### T6 test history

Test functions are counted from each tag's source with Python's `ast`. Collected counts are from `pytest --collect-only` with Python 3.14, after installing that version (see [`test_history.py`](../../../tests/section-05/test_history.py)).

| pyobjus | Date | Test functions | Collected |
|---|---|---:|---|
| 1.2.1 | 2022-03-26 | 82 | Doesn't build on Python 3.14 (Cython errors) |
| 1.2.2 | 2023-05-13 | 82 | Doesn't build on Python 3.14 |
| 1.2.3 | 2023-10-20 | 82 | Doesn't build on Python 3.14 |
| 1.2.4 | 2025-12-29 | 82 | 84 |
| `master` | 2026-10-31 | 200 | 202 |

| Rubicon | Date | Test functions | Collected |
|---|---|---:|---|
| 0.4.3 | 2022-12-05 | 246 | 259, with 1 collection error |
| 0.4.4 | 2023-01-23 | 252 | 265, with 1 error |
| 0.4.5 | 2023-02-03 | 253 | 266, with 1 error |
| 0.4.6 | 2023-04-14 | 254 | 267, with 1 error |
| 0.4.7 | 2023-10-21 | 267 | 280, with 1 error |
| 0.4.8 | 2024-04-03 | 276 | 287, with 1 error |
| 0.4.9 | 2024-05-03 | 279 | 290, with 1 error |
| 0.5.0 | 2025-01-07 | 284 | 295, with 1 error |
| 0.5.1 | 2025-06-03 | 284 | 295, with 1 error |
| 0.5.2 | 2025-08-07 | 284 | 302 |
| 0.5.3 | 2025-12-03 | 284 | 302 |
| 0.5.4 | 2026-05-06 | 287 | 428 |
| 0.5.5 | 2026-07-02 | 287 | 428 |
| 0.5.6 | 2026-07-02 | 287 | 428 |
| 0.5.7 | 2026-09-30 | 335 | 595 |
| `main` | 2026-11-02 | 364 | 624 |

The collection error at Rubicon 0.5.1 and earlier is the test module that imports `asyncio.events.AbstractEventLoopPolicy`, which Python 3.14 doesn't have, so that module's tests aren't counted.

**Who added the default branch's tests**, attributing each test function to the first commit that added a `def` line with its name under `tests/`:

| | pyobjus `master` | Rubicon `main` |
|---|---|---|
| Test functions | 200 | 364 |
| Added in the 12 months before the baseline | 120 | 208 |
| Added by this comparison's author | 120, all in October 2026 | 0 |
| Others, all time | ivpusic 61, Mathieu Virbel 14, 3 others 5 | Kattni 128, Russell Keith-Magee 89, Mgs. Tabrani 77, dgelessus 38, 5 others 32 |
| Largest additions in the 12 months | 27 in [`bfdccbe`](https://github.com/kivy/pyobjus/commit/bfdccbe), then 10, 9 and 8 in other commits | 83 in [#730](https://github.com/beeware/rubicon-objc/pull/730) and 45 in [#722](https://github.com/beeware/rubicon-objc/pull/722), then 34 in [#820](https://github.com/beeware/rubicon-objc/pull/820) and 27 in [#836](https://github.com/beeware/rubicon-objc/pull/836) |

A renamed test counts as new. #722 migrated Rubicon's suite to pytest and #730 refactored `test_core.py`, both in March 2026, and both renamed tests. Rubicon's count went from 284 test functions at 0.5.3, the last release before the 12 months began, to 364, a net gain of 80. pyobjus went from 82 to 200, a net gain of 118.

### K2 CI results

Workflow runs triggered by pushes to the default branch from 2025-11-04T14:10:39Z to the baseline, as GitHub recorded them (see [`ci_history.py`](../../../tests/section-05/ci_history.py) and [`ci_details.py`](../../../tests/section-05/ci_details.py)).

| | pyobjus | Rubicon |
|---|---|---|
| Pushes with runs | 50, in December 2025 (11), July 2026 (2) and October 2026 (37) | 179, in every month |
| Workflow runs | 100: 50 `Python package`, 50 `Deploy sdist/wheels` | 179 `CI` |
| Succeeded | 94 | 99 |
| Failed | 6, all `Python package` | 5 |
| Cancelled | 0 | 75, of which 74 were superseded by a newer push before they ended |
| The baseline commit | Both workflows succeeded ([run](https://github.com/kivy/pyobjus/actions/runs/41220927715), [run](https://github.com/kivy/pyobjus/actions/runs/41220927728)) | Succeeded ([run](https://github.com/beeware/rubicon-objc/actions/runs/41398512326)) |

**Failed runs, pyobjus:** each failed in one unit-test job on `macos-latest`, with Python 3.12 on 2025-12-16, and with 3.14, 3.11, 3.11, 3.10 and 3.13 in five pushes on 2025-12-29, the day 1.2.4 was released. GitHub no longer has the logs (HTTP 410) or the failed step, so the cause isn't known.

**Failed runs, Rubicon:** packaging on 2026-02-22, documentation linting on 2026-03-29, 2026-04-13 and 2026-07-02, and the project coverage job on 2026-09-09. No unit-test job failed. The coverage job's log is no longer available.

**Cancelled runs, Rubicon:** `ci.yml` cancels a run when another starts for the same branch. The one cancelled run with no newer push while it ran is [19881511372](https://github.com/beeware/rubicon-objc/actions/runs/19881511372), which ended 71 seconds after it started.

### K1 downstream CI

The CI of the main project that builds each library for iOS, at its last default-branch commit before the baseline (see [`downstream_ci.py`](../../../tests/section-05/downstream_ci.py)). Section 7 covers dependents in full.

| | kivy-ios, for pyobjus | Toga, for Rubicon |
|---|---|---|
| Commit | `fd363d49eddb5ac06766348738bd89c7d46007f8` (2026-10-20) | `dd833f156e13d15ed26720ef50b8e544046619c5` (2026-11-03) |
| Job | `build_python3_kivy (macos-latest)` in `kivy_ios.yml` | `Testbed (iOS)` in `ci.yml` |
| Library version | pyobjus `master`, from `archive/master.zip` when the job ran | rubicon-objc 0.5.7 from PyPI, as the log shows |
| Result | [Succeeded](https://github.com/kivy/kivy-ios/actions/runs/39490576806). pyobjus built for `iphoneos-arm64` and `iphonesimulator-arm64`, Touchtracer was built for the device and the simulator, and kivy-ios's startup app (`tests/test_startup`) reached the event loop on an iPhone 17 Pro simulator | [Succeeded](https://github.com/beeware/toga/actions/runs/41652092131). 472 passed, 130 skipped and 65 expected failures on an iPhone 17e simulator with iOS 26.5 |
| Push runs of the workflow, 12 months | 20, from 2026-04-18: 18 succeeded, 2 failed | 707: 206 succeeded, 112 failed, 389 cancelled |

The push-run conclusions cover each workflow as a whole, which builds and tests far more than the library, so they aren't a measure of either library and aren't reported in the section.

**Attempt to measure whether the startup app loads pyobjus.** [`kivy_ios_startup.py`](../../../tests/section-05/kivy_ios_startup.py) would build kivy-ios's startup app and Touchtracer, each with [`s5check.py`](../../../tests/section-05/kivy_ios_app/s5check.py) recording which of `ios` and `pyobjus` are imported once Kivy's event loop runs, and launch them on the simulator. It didn't get to run. `toolchain build python3 kivy` at kivy-ios `fd363d4`, with Python 3.14.7 and Cython 0.29.36 as its CI uses, failed twice on this Mac (macOS 26.6.2, Xcode 27.0):

1. libffi's Xcode project targets iOS 8.0, which Xcode 27 rejects (it accepts 15.0 and later). Setting `IPHONEOS_DEPLOYMENT_TARGET = 15.0` through `XCODE_XCCONFIG_FILE`, without changing kivy-ios, got libffi, OpenSSL, libpng and SDL2 built.
2. The host Python 3.11.6 that kivy-ios compiles to run its build crashed with segmentation faults while installing itself (`make install`), in its library install step and in `ensurepip`.

kivy-ios's CI ran on GitHub's `macos-latest` runner, macOS 15 at the time, with an older Xcode. Getting past the second failure would mean changing the Python kivy-ios builds, so the run was stopped there. Running it on GitHub's macOS 15 runner, as kivy-ios's CI did, was prepared but not pursued. Homebrew's `pkg-config`, `autoconf` and `automake`, which kivy-ios's CI installs, weren't present. kivy-ios only warns about them, and no recipe in this build uses them. pyobjus `master` was still at the baseline commit, so the build would have used the same pyobjus as the rest of this section. The first lines of each failure are in `raw/kivy_ios_build_failures.txt`.

### B2 and K3 release files

From PyPI's JSON and integrity APIs (see [`release_files.py`](../../../tests/section-05/release_files.py)).

| | pyobjus 1.2.4 | Rubicon 0.5.7 |
|---|---|---|
| Files | 12: an sdist, 5 macOS `universal2` wheels (cp310 to cp314) and 6 iOS wheels (cp313 and cp314, for the device and two simulator architectures) | 2: an sdist and a `py3-none-any` wheel |
| Provenance on PyPI | None (404 for all 12) | Both files, published by `beeware/rubicon-objc`'s `publish.yml` |

## Tools

| Item | Version |
|---|---|
| Mac and Python | As in the baseline: macOS 26.6.2, Xcode 27.0, Python 3.14.7 from python.org |
| Test dependencies | Each project's own, as its CI installs them on 2026-11-08: pyobjus's `.ci/cicd-requirements.txt`, Rubicon's `tox-uv` dependency group |
| iOS simulator | iPhone 17e, iOS 27.0, from Xcode 27.0 |
| Briefcase | `d94b1eb06d55d1cf01559f8818b1df0625a3ea3d`, its default branch on 2026-11-08, installed unpinned by Rubicon's tox environment |
| Line counts | ruff 0.6.9 |
| GitHub data | `gh` CLI, read on 2026-11-08 |

## Files in `raw/`

- `mac.json`: every Mac run, with counts, each non-passing test and its message, and the coverage result
- `mac_logs/`: each run's log and JUnit XML, and the coverage reports
- `ios_sim.json`, `ios_sim_logs/`: every simulator run, with counts and the log
- `trial_mac.json`, `trial_ios_sim.json`: one trial run of each, before the full runs. The trial results match the full runs, except that the Mac trial counted expected failures as skips (see below)
- `test_lines.json`: T1's line counts
- `features_tested.json`: T2's status for each Section 3 row and version, with the cited test and its line
- `test_history.json`, `test_history.log`: T6's counts per tag, and every default-branch test function with the commit that first added it
- `ci_history.json`: every workflow run in the 12 months, with its commit, dates and conclusion
- `ci_details.json`: the failed jobs in each failed run, and which cancelled runs were superseded
- `ci_logs/`: the logs of pyobjus's unit-test jobs for the baseline commit on `macos-latest` and Intel with Python 3.14, which show the Guard Malloc tests running
- `release_files.json`: each release's files on PyPI, with the provenance status
- `kivy_ios_build_failures.txt`: the failing commands and errors from the two kivy-ios build attempts, with local paths replaced
- `downstream_ci.json`: kivy-ios's and Toga's CI at their last commits before the baseline, with the job's steps, the log lines naming the library or reporting the simulator result, and the workflow's push runs in the 12 months

Local paths are replaced with `<work>`, `<results>`, `<tmp>` and `~` (escaped as `&lt;work&gt;` and so on in the XML files). pytest writes the Mac's host name into its JUnit XML files, and it's replaced with `REDACTED`.

## Fixes during collection

No project's tests were changed. These fixes were to this comparison's scripts, before any figure was reported.

| Script | Fix |
|---|---|
| `run_mac.py` | JUnit XML records an expected failure as a skip of type `pytest.xfail`. These are now counted separately. The Mac trial counted pyobjus `master`'s 6 expected failures as skips |
| `run_ios_sim.py` | The simulator log often puts a test's outcome on a later line than its name, and some test IDs contain spaces. The parser was rewritten, and its counts now match pytest's summary line in every run |
| `test_history.py` | A non-editable install let pyobjus's source directory shadow the built package, so collection failed. It now installs pyobjus as its CI does, with `pip install -e .` |
| `test_history.py` | `git blame` was replaced by the first commit that added each test's name, as recorded in the definitions' changes after approval |
| `features_tested.py` | Two cited tests didn't exist at every ref, which the script's check caught. They were replaced with tests that exist |
| Raw XML | The first redaction left `<work>` and `<host>` unescaped, so the JUnit files weren't valid XML. Escaped, and checked by parsing every file |
