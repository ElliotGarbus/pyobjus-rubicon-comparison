# 7. Ecosystem considerations

**Status: draft for factual review.** Neither project has reviewed this section. Metric IDs refer to the [approved definitions](../metrics/07-ecosystem.md), which also list every change made after approval. Kivy's and Plyer's own use of pyobjus, and the work of migrating, are in Section 8.

## Summary of findings

The two libraries have a similar breadth of direct use in public code. 84 public GitHub repositories import pyobjus in their own Python code and 78 import Rubicon, after leaving out copies of other projects. 56 and 63 of them were pushed to in the last two years, and only one imports both. Each library's most-starred user is the GUI toolkit from its own organization: Kivy, with 19,025 stars, for pyobjus, and Toga, with 5,431, for Rubicon. Beyond those, they differ in who the users are. pyobjus's next most-starred users are Ren'Py, KivyMD, Plyer, kivy-ios and Ren'Py's build system, and after those, none has more than 102 stars. Rubicon's are mostly outside BeeWare, led by Pyto, a Python IDE for iOS. Outside each library's own GitHub organization, 8 of Rubicon's users have 100 stars or more, against 4 of pyobjus's. Neither count includes indirect use: 259 repositories that carry Ren'Py, mostly games, apps that use pyobjus only through Kivy or Plyer, and apps that use Rubicon only through Toga.

**pyobjus:** 84 repositories, 56 of them pushed to since November 2024. Kivy imports it in its audio and clipboard modules, Plyer in 27 files of its iOS and macOS implementations, kivy-ios in its tests, KivyMD in its iOS behaviors, and Ren'Py in its launcher, engine and iOS build support. The rest are mostly small projects: 33 of the 84 have no stars, and 62 import pyobjus in a single file. Most of the 3,842 files the search found were copies, 2,250 of them in generated folders such as Buildozer's, 893 copies of Ren'Py and 398 copies of pyobjus or Plyer.

**Rubicon:** 78 repositories, 63 of them pushed to since November 2024. Five belong to BeeWare, which maintains Rubicon: Toga, whose macOS and iOS backends are written against it in 90 files, two Toga widget packages, a test app for BeeWare's Python support packages, and yorkshire4. Pyto holds 435 of the 796 files counted. Others include desktop-notifier, a cross-platform notification library, and apps such as F95Checker and picframe. 25 of the 78 have no stars, and 37 import Rubicon in a single file. Up to 4 may still be copies, including the fourth most-starred, whose files have the same paths as Pyto's. One of the 78 is KivyForge, by this comparison's author.

All figures are **Measured** from GitHub's code search on 2026-11-08 (02:57 UTC on 2026-11-09), unless labeled otherwise. This section makes no recommendation.

| Measure | pyobjus | Rubicon |
|---|---:|---:|
| [Repositories that import it directly](#e1-public-code-that-imports-each-library) | 84 | 78 |
| [Pushed to since 2024-11-04](#e1-public-code-that-imports-each-library) | 56 | 63 |
| [Most-starred user](#most-stars) | Kivy, 19,025 | Toga, 5,431 |
| [Most-starred user outside its own organization](#most-stars) | Ren'Py, 6,998 | Pyto, 1,028 |
| [With 100 or more stars, outside its own organization](#e1-public-code-that-imports-each-library) | 4 | 8 |
| [With 10 or more stars](#e1-public-code-that-imports-each-library) | 20 | 21 |
| [Possible copies the rules miss](#copies) | Up to 1 | Up to 4 |
| [Files the search found](#copies) | 3,842 | 2,006 |
| [Files counted](#copies) | 160 | 796 |

## Claims from the discussion

None of the claims in the [register](../CLAIMS.md) is tested here. Claims 17, 18 and 19, about Kivy's and Plyer's use of pyobjus, are in Section 8.

## Supporting facts

Raw results, conditions, the full repository lists and every exclusion with its reason are in [`results/section-07/2026-11-08`](../results/section-07/2026-11-08/README.md). The scripts are in [`tests/section-07`](../tests/section-07).

**How it was measured:** [`code_search.py`](../tests/section-07/code_search.py) searched GitHub's code search for Python files containing `from pyobjus import`, `import pyobjus`, `from rubicon.objc import`, `import rubicon.objc` or `from rubicon import objc`, the last of which found nothing. The search covers public repositories' default branches. It returns at most 1,000 results per query, so each query was split by file size until every part returned fewer, and every page was read. Repository details came from GitHub's GraphQL API in the same run. [`summarize.py`](../tests/section-07/summarize.py) then left out copies, the same way for both libraries, and counted the repositories left.

### E1. Public code that imports each library

| | pyobjus | Rubicon |
|---|---:|---:|
| Files found by the search | 3,842 | 2,006 |
| Repositories those files are in | 702 | 479 |
| Files counted, after leaving out copies | 160 | 796 |
| **Repositories counted** | **84** | **78** |
| Pushed to since 2024-11-04 | 56 | 63 |
| With 100 or more stars | 7 | 9 |
| With 100 or more stars, outside its own organization | 4 | 8 |
| With 10 or more stars | 20 | 21 |
| With no stars | 33 | 25 |
| Importing the library in one file only | 62 | 37 |

The activity window is the 24 months before [the baseline](../results/baseline/2026-11-04.md), extended to the search. GitHub reports only a repository's last push, so a repository last pushed after the baseline, as Kivy, Ren'Py and Toga were, can't be checked against the window's end. 5 of pyobjus's 56 and 16 of Rubicon's 63 were last pushed between the baseline and the search.

A library's own organization is `kivy` for pyobjus and `beeware` for Rubicon. Kivy, Plyer and kivy-ios are pyobjus's three users with 100 or more stars inside it, and Toga is Rubicon's only one.

One repository imports both, [MASSIVEMAGNETICS/Victor_Synthetic_Super_Intelligence](https://github.com/MASSIVEMAGNETICS/Victor_Synthetic_Super_Intelligence).

### Most stars

Stars and last push as GitHub reported them at the search. The example is the first counted file, by path.

**pyobjus**

| Repository | Stars | Files counted | Last push | Example file |
|---|---:|---:|---|---|
| [kivy/kivy](https://github.com/kivy/kivy) | 19,025 | 1 | 2026-11-08 | `kivy/core/audio_output/audio_avplayer.py` |
| [renpy/renpy](https://github.com/renpy/renpy) | 6,998 | 6 | 2026-11-09 | `renpy.py` |
| [kivymd/KivyMD](https://github.com/kivymd/KivyMD) | 2,468 | 1 | 2026-10-26 | `kivymd/uix/behaviors/ios/native_behavior.py` |
| [kivy/plyer](https://github.com/kivy/plyer) | 1,805 | 27 | 2026-10-04 | `plyer/platforms/ios/accelerometer.py` |
| [kivy/kivy-ios](https://github.com/kivy/kivy-ios) | 856 | 1 | 2026-10-26 | `tests/test_python3/main.py` |
| [renpy/renpy-build](https://github.com/renpy/renpy-build) | 123 | 2 | 2026-11-01 | `runtime/iossupport.py` |
| [oskros/MF_run_counter](https://github.com/oskros/MF_run_counter) | 102 | 1 | 2026-02-10 | `libs/screeninfo/enumerators/osx.py` |
| [Carvera-Community/Carvera_Controller](https://github.com/Carvera-Community/Carvera_Controller) | 94 | 1 | 2026-11-06 | `carveracontroller/ios_helpers.py` |
| [gistable/gistable](https://github.com/gistable/gistable) | 75 | 1 | 2023-02-11 | `all-gists/8831412/snippet.py` |
| [Dirk-Sandberg/Friendly-Fitness-App](https://github.com/Dirk-Sandberg/Friendly-Fitness-App) | 70 | 1 | 2020-05-13 | `main.py` |

**Rubicon**

| Repository | Stars | Files counted | Last push | Example file |
|---|---:|---:|---|---|
| [beeware/toga](https://github.com/beeware/toga) | 5,431 | 90 | 2026-11-09 | `cocoa/src/toga_cocoa/app.py` |
| [ColdGrub1384/Pyto](https://github.com/ColdGrub1384/Pyto) | 1,028 | 435 | 2025-09-14 | `Lib/UIKit.py` |
| [aitobox/ATBClone](https://github.com/aitobox/ATBClone) | 461 | 6 | 2026-10-26 | `src/atbclone/gui/patch_cocoa.py` |
| [RemusDBD/ctftools-all-in-one](https://github.com/RemusDBD/ctftools-all-in-one) | 413 | 3 | 2026-09-19 | `Lib/bookmarks.py` |
| [WillyJL/F95Checker](https://github.com/WillyJL/F95Checker) | 248 | 1 | 2026-11-01 | `modules/notification_proc.py` |
| [iamprivacy/Waves](https://github.com/iamprivacy/Waves) | 209 | 2 | 2026-11-08 | `tests/test_desktop_notify.py` |
| [helgeerbe/picframe](https://github.com/helgeerbe/picframe) | 168 | 1 | 2026-09-17 | `src/picframe/video_player.py` |
| [samschott/desktop-notifier](https://github.com/samschott/desktop-notifier) | 158 | 2 | 2026-09-16 | `src/desktop_notifier/backends/macos.py` |
| [PlantCraft/PlantCraft](https://github.com/PlantCraft/PlantCraft) | 157 | 1 | 2026-11-06 | `notebooks/python/plantcraft_notebook/kit.py` |
| [beeware/yorkshire4](https://github.com/beeware/yorkshire4) | 43 | 1 | 2026-09-16 | `yorkshire4/widgets/cocoa/bitmap_view.py` |

RemusDBD/ctftools-all-in-one is likely a copy of Pyto's files ([below](#copies)).

### Copies

Most files the search found weren't written against the library by the repository holding them. They were installed packages, build output, or other projects' code carried inside an app.

| Left out | pyobjus | Rubicon |
|---|---:|---:|
| The library itself: pyobjus or Rubicon | 44 | 20 |
| Copied or generated folder, such as `site-packages`, `venv` or `.buildozer` | 2,250 | 482 |
| Copy of the library, Plyer or Toga inside another repository | 398 | 211 |
| Copy of another project | 990 | 497 |
| **Total** | **3,682** | **1,210** |

- **The approved rules** left out the libraries, Plyer, Toga and their forks, generated folders, and copies of those four projects. Hand checks of random samples then showed many copies of other projects, so rules were added that find a copy by its path, by its folder layout, or by the license header or docstring it opens with. Plyer and Toga were then counted like any other repository, as Kivy is, and only copies of Toga's own packages, such as `toga_cocoa`, count as copies of Toga. The rules apply to both libraries, and the definitions record each change after approval.
- **Ren'Py:** 893 of pyobjus's files left out are copies of Ren'Py, in 259 repositories, mostly games made with it. Ren'Py names its launcher after each game, so 230 of them were found only by its license header.
- **Pyto:** 415 of Rubicon's are copies of Pyto's files, all in another repository by Pyto's author.
- **Toga:** 223 of Rubicon's are copies of Toga's code, in 5 repositories.

After the last rule was added, both full lists were checked by hand. These may still be copies:

| Library | Repository | Why |
|---|---|---|
| pyobjus | [gistable/gistable](https://github.com/gistable/gistable) | An archive of other people's gists |
| Rubicon | [RemusDBD/ctftools-all-in-one](https://github.com/RemusDBD/ctftools-all-in-one) | Its 3 files have the same paths as files in Pyto |
| Rubicon | [HaroonZm/Cassiopee](https://github.com/HaroonZm/Cassiopee) | A dataset folder of Pyto files, under other paths |
| Rubicon | [johndpope/face](https://github.com/johndpope/face) | A copy of an old version of Python-Apple-support's test app |
| Rubicon | [iamprivacy/Waves](https://github.com/iamprivacy/Waves) | One of its 2 files may be adapted from desktop-notifier's tests |

Leaving all of them out would give pyobjus 83 and Rubicon 74 (**Inferred**, from the hand check).

## Limits of this section

- **This counts direct use only.** Kivy, Plyer and Toga are counted, but projects that use pyobjus only through Kivy or Plyer, or Rubicon only through Toga, don't import the library and aren't, nor are the Ren'Py games.
- **It counts public code on GitHub only.** Private and commercial apps, and code hosted elsewhere, aren't seen.
- **The search doesn't return every file.** Kivy imports pyobjus in at least two files, `kivy/core/clipboard/clipboard_nspaste.py` and `kivy/core/audio_output/audio_avplayer.py`, but the search returned only the second. A repository is missed only if the search misses all of its files. GitHub's totals are approximate.
- **Repositories are counted, not apps or users.** A repository with one import counts the same as Pyto, with 435 files. Stars and the last push are shown so readers can judge each one.
- **A new search would give different results,** because GitHub's index and the repositories change. Every response is saved.
- **This comparison's author** owns [ElliotGarbus/kivyforge](https://github.com/ElliotGarbus/kivyforge), one of Rubicon's 78, through 6 files in its iOS examples.
