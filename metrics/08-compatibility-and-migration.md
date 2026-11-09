# Section 8 metric definitions

**Status: approved 2026-11-09.** These definitions were written before any Section 8 data was collected. Changes made after that are recorded at the end of this document with their reasons.

Section 8 documents what it takes to move code from pyobjus to Rubicon. It catalogs how the most-starred public projects use pyobjus, gives the Rubicon way to do each thing they do, and lists what Kivy and Plyer would change. It doesn't design or test a compatibility layer that would let pyobjus code run on Rubicon unchanged.

## What was seen before these were written

| Seen before writing (2026-11-09) | Where | Effect on the rules |
|---|---|---|
| Section 7's list of public repositories that import pyobjus, with stars, and one example file each | [Section 7](../sections/07-ecosystem.md), at `section-7-draft-2` | The catalog's sample is chosen from that list by a fixed rule, U0 below, not by hand |
| During Section 7's hand checks, some files of the counted repositories were read to decide whether they were copies | Section 7 | Disclosed here. The catalog reads every file of the sample again at a pinned commit |
| Kivy imports pyobjus in two files, its macOS clipboard and AVPlayer audio, and GitHub's code search returned only one of them | Sections 4 and 7 | The catalog searches each sampled repository's full source, not code search results |
| Plyer imports pyobjus in 27 files of its iOS and macOS implementations, by code search | Section 7 | Plyer is in the sample, and gets a per-file inventory (M2) |
| Sections 3 and 4 show how each library does the common tasks, including delegates, blocks, structs and loading frameworks | [Section 3](../sections/03-capabilities.md), [Section 4](../sections/04-examples.md) | M1 cites them where they already show the Rubicon way, instead of testing again |
| The kivy-ios pyobjus recipe downloads pyobjus's source from GitHub and compiles it | [Section 1](../sections/01-history-and-maintenance.md) | B1 records how each library gets into an app |

## Versions

Each sampled repository is read at its default branch commit on the collection date, and the commits are recorded. pyobjus and Rubicon are at [the baseline](../results/baseline/2026-11-04.md). Tests run on the baseline Mac and iPhone.

## U. Use catalog

| ID | Metric | Definition | Label |
|---|---|---|---|
| U0 | Sample | Every repository Section 7 counted as importing pyobjus with 50 or more stars at its search, except one its hand check listed as a possible copy. By Section 7's list, that's 10: Kivy, Ren'Py, KivyMD, Plyer, kivy-ios, Ren'Py's build system, MF_run_counter, Carvera Controller, Friendly-Fitness-App and kivy-tensorflow-helloworld | Source |
| U1 | Where each repository uses pyobjus | Per repository: the files that import pyobjus or use its objects, found by searching the full checkout, the number of call sites, the Apple frameworks and classes used, and the platforms the code runs on (iOS, macOS or both), as the code shows | Measured |
| U2 | Use patterns | Every distinct way the sample uses pyobjus, grouped by feature. For example, loading a class with `autoclass`, calling methods, converting strings, implementing a delegate with `@protocol`, loading a framework, passing structs or arrays, and handling errors. For each pattern: how many repositories and call sites use it, and a linked example | Measured |

## M. Moving to Rubicon

| ID | Metric | Definition | Label |
|---|---|---|---|
| M1 | The Rubicon way to do each pattern | For each U2 pattern, the Rubicon code that does the same thing, linked to Rubicon's docs or to Sections 3 and 4 where they already show it. A pattern without a direct equivalent says what's needed instead. Each translation is run on the Mac, or on the iPhone when it needs iOS, with both libraries giving the same result | Measured, or Source where a section already shows it |
| M2 | Kivy and Plyer, file by file | For each file in Kivy and Plyer that uses pyobjus: the patterns it uses, its call sites, and which M1 translations apply | Measured |
| M3 | Changes outside the code | Where each sampled repository declares or builds pyobjus: package metadata, requirements files, kivy-ios recipes and build scripts, linked at the pinned commit | Source |

## B. Getting each library into an app

| ID | Metric | Definition | Label |
|---|---|---|---|
| B1 | How each library is installed for iOS and macOS | For pyobjus and Rubicon: whether it needs compiling, the wheels on PyPI for each platform, and the recipes or steps kivy-ios and KivyForge use to include it | Source and Measured |

## Rules

- **The sample is fixed by U0.** Repositories aren't added or removed by hand. A repository that turns out to be a copy is reported, kept in the catalog and marked.
- **Full source, not search results:** each sampled repository is cloned at a pinned commit and searched for every use of pyobjus, including imports inside functions and through another module.
- **Patterns, not judgments:** the catalog records what code does. It doesn't rate code quality or estimate hours of work.
- **Same tests for both:** each M1 translation runs the pyobjus and Rubicon versions against the same Apple API, checking the same result.
- **Raw data saved:** the commits, the file lists, every call site and every test's output are saved under `results/section-08/`.

## Deliberately excluded

| Measure | Why |
|---|---|
| A compatibility layer or shim that runs pyobjus code on Rubicon | Out of scope: this section documents moving code to Rubicon |
| Estimates of time or effort in hours | Depend on the developer. Call sites and patterns are counted instead |
| Android and pyjnius | Neither library runs on Android |
| Rubicon's users, and moving code from Rubicon to pyobjus | The section documents the move to Rubicon |
| Plans for when or whether any project moves | A decision for each project |
| Running both libraries in one process | Not needed to document the move |

## Claims

| Claim ([register](../CLAIMS.md)) | Tested by |
|---|---|
| 13. Both libraries work side by side on Python 3.15 | Not tested: running both in one process is excluded above |
| 17. Kivy doesn't require pyobjus by design | U1, M2 and M3 for Kivy: whether each import is optional, and whether Kivy declares pyobjus as a dependency |
| 18. Kivy already depends on pyobjus alone | U1, M2 and M3 for Kivy: whether Kivy uses any other Objective-C bridge |
| 19. Plyer's last release was 2.1.0 in November 2022, and it has 69 open PRs, most more than five years old | Plyer's PyPI releases and GitHub's open PRs on the collection date, with their opening dates (**Measured**) |
