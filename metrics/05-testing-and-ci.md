# Section 5 metric definitions

**Status: approved 2026-11-08.** These definitions were written before any Section 5 data was collected. Changes made after that are recorded at the end of this document with their reasons.

Section 5 describes how each project checks its own code: its test suite, what its CI runs and how reliably, and how a release is built and tested before it's published. It doesn't test the libraries' behavior again, which Sections 2 to 4 cover.

## What was seen before these were written

| Seen before writing (2026-11-08) | Where | Effect on the rules |
|---|---|---|
| The file lists, CI workflows, `tox.ini`, `Makefile` and coverage settings of both projects at the baseline commits, and pyobjus's CI workflow at `v1.2.4` | [pyobjus](https://github.com/kivy/pyobjus/tree/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81) at `0c204ad`, [Rubicon](https://github.com/beeware/rubicon-objc/tree/6bf06390f720226da3d51477f38de3ff1e680eaf) at `6bf0639` | The metrics below name what each project actually has. No test was run and no CI history was read |
| pyobjus has 14 test files at each release from 1.2.1 to 1.2.4, and 29 at the baseline commit. Every non-merge commit to `tests/` since 1.2.4, 28 in all, is the author's, from October 2026, and the other 12 merge the author's PRs. The author also added the memory tests and the CI job that runs the examples. A pyobjus maintainer, AndreMiras, added Cython coverage to CI | `git log` of pyobjus | pyobjus's release and default branch are reported separately throughout, T6 shows when tests were added and by whom, and the section calls out the author's share wherever it affects a figure |
| The author has no commits in Rubicon | `git log` of Rubicon | None |
| Rubicon's CI at the baseline commit lists Python 3.11 to 3.15. Claim 14 says 3.11 to 3.16 | Rubicon `ci.yml` | K1 reports what the workflow at each pinned commit lists, and K2 when each version first appeared |
| Rubicon runs its suite on the iOS simulator through Briefcase. pyobjus builds iOS wheels in CI and doesn't run tests on them | Both projects' workflows | T4 runs each project's own iOS route, where it has one |

## Versions

Each project is read and run at two points, as in earlier sections: its latest release (pyobjus `v1.2.4`, Rubicon `v0.5.7`) and its default branch at [the baseline](../results/baseline/2026-11-04.md) commit. Runs use the baseline Mac, with Python 3.14.

## T. Test suites

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| T1 | Size | Tests that `pytest --collect-only` collects, and lines of test code counted as in Section 4. A parameterized test counts once per case, and that is reported beside the count | Each suite | Measured |
| T2 | Features tested | For each row of Section 3's feature matrix, whether the project's own suite has at least one test that exercises it, with a link to one such test. A row is marked tested only if the test calls that feature, not if it merely imports it | Each suite, read against Section 3 | Source |
| T3 | Line coverage | Coverage from each project's own coverage setup, run on the Mac: Cython and Python lines for pyobjus, as its CI measures them, and Python lines and branches for Rubicon. Reported with the method beside each figure, and not compared as one number, since they measure different code in different ways | Each project's coverage config | Measured |
| T4 | Suite results | Passed, failed, skipped and errored tests, from 3 runs of each suite on the Mac, each in a new environment, following the project's own instructions. Where the project has its own iOS test route, it is run the same way. Failures are listed with their messages | Each suite | Measured |
| T5 | Memory testing | Tests that check for leaks, use after free or heap errors, such as tests that measure allocated memory, run under Guard Malloc, or check that objects are freed. Each is listed by file with what it checks, and whether CI runs it | Each suite | Source |
| T6 | Test history | T1's collected test count at each stable release since 2022, and at the default branch. The share of the default branch's test functions added in the 12 months before the baseline, and the share added by the author, from `git blame` of each test function's first line | Git | Measured |

## K. Continuous integration

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| K1 | What CI runs, and where | Each job in the workflows that run on pushes and pull requests: what it does (unit tests, coverage, examples, linters, docs, packaging) and its matrix of operating systems, architectures, Python versions and iOS targets. Read at the release tag and the default branch | Workflow files, pinned | Source |
| K2 | CI results | For workflow runs triggered by pushes to the default branch in the 12 months before the baseline: runs per workflow, and the share that succeeded, failed or were cancelled. Also the result for the baseline commit itself, and the date each Python version first appeared in the test matrix, where Section 1 doesn't already give it | GitHub Actions API | Measured |
| K3 | Release artifacts tested | Whether the files published to PyPI are the files the test suite ran against, for each platform. For example, a wheel that is built, then tested with the full suite, then published counts; a wheel tested only by importing the package is reported as that | Release workflows, pinned | Source |

## B. Build and release

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| B1 | Build inputs | What building a release needs: compilers, Cython, libffi for iOS, the build tool, and the files produced for each platform and Python version. Section 1 has the file counts. This covers what produces them | Build config and release workflows, pinned | Source |
| B2 | Release process | What starts a release (a tag, a manual step), which steps are automated, how files reach PyPI (a token, or trusted publishing) and whether provenance attestations are published | Release workflows, PyPI | Source |

## Rules

- **The project's own setup:** suites run the way each project's CI or contributor docs say, with their declared dependencies. If a suite can't run that way, the fix is recorded, and the smallest change that works is used.
- **Same checks for both:** a metric that reads a file in one project reads the equivalent file in the other. Where one project has no equivalent, the section says so.
- **No pass marks:** coverage and pass rates are reported as they are, with no threshold for good or bad.
- **CI history is read, not rerun:** K2 uses the results GitHub recorded. Workflow runs aren't retriggered.
- **Raw data saved:** collected test lists, coverage reports, test logs and API responses are saved under `results/section-05/`, with local paths replaced as in earlier sections.

## Deliberately excluded

| Measure | Why |
|---|---|
| Whether the libraries behave correctly | Sections 2 to 4 test this directly |
| Running either suite on the physical iPhone | Neither project's suite runs on a device. Section 3 tested behavior on the phone |
| Test quality, such as "thorough" or "well written" | A judgment. T2 and T5 show what is tested, so readers can judge |
| Release counts and dates, and how fast new Python versions got wheels | Section 1 covers these |
| Code review and merge practice | Section 1 covers these |
| Downstream projects' tests, such as Kivy's or Toga's | Section 7 covers dependents |

## Claims this section reports on

| Claim ([register](../CLAIMS.md)) | Evidence |
|---|---|
| 14. Rubicon CI runs on Python 3.11 to 3.16, including iOS | K1, K2 and T4 |
| 15. pyobjus has no iOS tests in CI and no systematic leak testing | K1, T4 and T5, at the release and the default branch |
| 16. Each pyobjus release needs separate wheels per Python version and platform, while Rubicon ships one `py3-none-any` wheel | B1 and K3, for the build side. Section 1 confirmed the file counts |

## Changes after approval

None yet.
