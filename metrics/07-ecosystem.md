# Section 7 metric definitions

**Status: approved 2026-11-08.** These definitions were written before any Section 7 data was collected, apart from the trial searches listed below. Changes made after that are recorded at the end of this document with their reasons.

Section 7 measures the breadth of each library's use: how many public projects write code against it. It doesn't estimate the work of moving code from one library to the other, or measure Kivy's and Plyer's own use of pyobjus, which Section 8 covers.

## What was seen before these were written

| Seen before writing (2026-11-08) | Where | Effect on the rules |
|---|---|---|
| kivy-ios builds pyobjus from a recipe, so apps built with it rarely declare pyobjus as a dependency, and GitHub's dependency graph wouldn't see them | Sections 1 and 5 | E1 counts code that imports each library, not declared dependencies |
| Trial searches with GitHub's code search API: `from pyobjus import` in 3,372 Python files and `import pyobjus` in 262, `from rubicon.objc import` in 1,748 and `import rubicon.objc` in 29. The first page of 100 results came from 31 repositories for `from pyobjus import` and 2 for `from rubicon.objc import` | GitHub, 2026-11-08 | Most matches are repeated copies, so E1 counts distinct repositories and leaves copies out |

## Date

The searches run once, on a stated date, and every response is saved. GitHub's code search covers public repositories' default branches, and its counts are approximate.

## E. Breadth of use

| ID | Metric | Definition | Label |
|---|---|---|---|
| E1 | Public code that imports each library | The number of distinct public repositories with Python code that imports the library directly (`from pyobjus import`, `import pyobjus`, `from rubicon.objc import`, `import rubicon.objc` and `from rubicon import objc`), found with GitHub's code search. Also, how many of those repositories were pushed to in the 24 months before [the baseline](../results/baseline/2026-11-04.md), and the 10 with the most stars, named and linked | Measured |

## Rules

- **Every match collected:** the search API returns at most 1,000 results per query, so queries are split by file size until each returns fewer than 1,000, and the results are combined.
- **Copies left out:** a repository isn't counted if it is the library itself, Plyer or Toga, or a fork of one of these. A match isn't counted if it's in a copied or generated folder: `site-packages`, `dist-packages`, `.buildozer`, a virtual environment, a `build` or `dist` folder, or a copy of pyobjus, Rubicon, Plyer or Toga inside another repository. The excluded repositories and paths are saved with the results.
- **Direct use only:** a project that uses pyobjus only through Plyer, or Rubicon only through Toga, doesn't import the library and isn't counted. Most Toga apps never import Rubicon, so this likely undercounts Rubicon's reach more than pyobjus's, and the section says so.
- **Same search for both:** both libraries are searched the same way, on the same day.
- **Raw data saved:** every search response, the repository list and each exclusion with its reason are saved under `results/section-07/`.

## Deliberately excluded

| Measure | Why |
|---|---|
| Dependencies declared in manifests, such as GitHub's dependency graph | kivy-ios apps rarely declare pyobjus, so this would undercount it heavily |
| PyPI downloads | Section 1 covers them, and builds through kivy-ios don't download pyobjus |
| Private or commercial use | Not publicly observable |
| Kivy's and Plyer's own use of pyobjus, and the work of migrating | Section 8 covers compatibility and migration |
| Quality or activity judgments beyond the 24-month count | Counts and links are given, so readers can judge |

## Claims

None. Claims 17, 18 and 19, about Kivy's and Plyer's use of pyobjus, move to Section 8.

## Changes after approval

| Metric | Change | Reason |
|---|---|---|
