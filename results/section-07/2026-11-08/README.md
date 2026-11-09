# Section 7 results, 2026-11-08

The scripts are in [`tests/section-07`](../../../tests/section-07), and each one's docstring gives its usage. Metric IDs refer to the [approved definitions](../../../metrics/07-ecosystem.md), which also list the changes made after approval.

## Status

| Part | Status |
|---|---|
| E1 code search, both libraries | Done: `raw/code_search.json`, with every match, the size ranges searched and each repository's details |
| Opening text of each counted file | Done: `raw/header_markers.json`. Added after approval, as the definitions record. Only the marker each file carried is saved, not its text |
| Figures | `raw/summary.json`, from [`summarize.py`](../../../tests/section-07/summarize.py), with every exclusion and its reason |
| Hand check of the counted repositories | Done. Results below |
| Section text | Draft |

## Conditions

| | |
|---|---|
| Searched | 2026-11-09 02:57 UTC (the evening of 2026-11-08 in US time zones), by [`code_search.py`](../../../tests/section-07/code_search.py) |
| Search | GitHub's REST code search (`search/code`) through the `gh` CLI 2.101.0, with `language:Python`. It covers the default branches of public repositories, and files up to 384,000 bytes |
| Queries | `"from pyobjus import"`, `"import pyobjus"`, `"from rubicon.objc import"`, `"import rubicon.objc"` and `"from rubicon import objc"` |
| Splitting | Each query was split by file size until every range reported fewer than 1,000 results, then every page was read: 12 ranges for pyobjus and 10 for Rubicon. No response was marked incomplete |
| Repository details | Stars, last push, fork and parent, from GitHub's GraphQL API in the same run |
| Opening text | The first 2,000 characters of each of the 1,098 files the path rules counted at the time, read through the GraphQL API by [`fetch_headers.py`](../../../tests/section-07/fetch_headers.py) the same day. All 1,098 were read. Plyer's and Toga's files, and the three Toga widget packages, were counted later and weren't read. The markers are Ren'Py's and Kivy's, and the rule doesn't apply inside Kivy's own organization |
| Activity window | Pushed to since 2024-11-04 14:10 UTC, the start of the 24 months before [the baseline](../../baseline/2026-11-04.md), up to the search |

## Results

| | pyobjus | Rubicon |
|---|---:|---:|
| Files found by the search | 3,842 | 2,006 |
| Repositories those files are in | 702 | 479 |
| Files counted, after exclusions | 160 | 796 |
| **Repositories counted** | **84** | **78** |
| Pushed to since 2024-11-04 | 56 | 63 |
| Of those, last pushed after the baseline | 5 | 16 |
| With 100 or more stars | 7 | 9 |
| With 100 or more stars, outside its own organization (`kivy`, `beeware`) | 4 | 8 |
| With 10 or more stars | 20 | 21 |
| With no stars | 33 | 25 |
| Importing the library in one file only | 62 | 37 |

One repository imports both, [MASSIVEMAGNETICS/Victor_Synthetic_Super_Intelligence](https://github.com/MASSIVEMAGNETICS/Victor_Synthetic_Super_Intelligence). `"from rubicon import objc"` found no files. 435 of Rubicon's 796 counted files are in one repository, Pyto.

The search's totals are approximate. `"from pyobjus import"` reported 3,372 files over its full size range, while reading every split range returned 3,558. A file with two import forms is found by two queries and counted once: 16 such files for pyobjus and 4 for Rubicon.

### Most stars, pyobjus

Stars and last push as GitHub reported them at the search. The example is the first counted file, by path.

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

### Most stars, Rubicon

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

The hand check below found that RemusDBD/ctftools-all-in-one's 3 files have the same paths as files in Pyto, so it is likely a copy that the rules miss.

The full lists are in `raw/summary.json` under `repositories_list`.

## Exclusions

Files left out, by the first rule that matched. Each exclusion is in `raw/summary.json` with its reason, and for copies the repository it was copied from.

| Reason | pyobjus | Rubicon |
|---|---:|---:|
| The library itself: kivy/pyobjus or beeware/rubicon-objc | 44 | 20 |
| Copied or generated folder, such as `site-packages`, `venv` or `.buildozer` | 2,250 | 482 |
| Copy of the library itself | 60 | 10 |
| Copy of Plyer | 338 | 0 |
| Copy of Toga, by its package folders | 0 | 201 |
| Copy of Ren'Py, by its folder layout | 609 | 0 |
| Copy of another repository, by path | 144 | 497 |
| Copy of another project, by its opening text | 237 | 0 |
| **Total** | **3,682** | **1,210** |

- **Ren'Py:** 893 of pyobjus's excluded files are copies of Ren'Py, across all three copy rules, in 259 repositories that weren't counted. Most are games made with Ren'Py, which carry its engine and its launcher. Ren'Py names the launcher after each game, so the opening-text rule was needed to find them: 230 files carried Ren'Py's license header.
- **Pyto:** 415 of Rubicon's excluded files are copies of Pyto's files, all in [ColdGrub1384/Apple-Frameworks-Python](https://github.com/ColdGrub1384/Apple-Frameworks-Python), another repository by Pyto's author.
- **Toga:** 223 of Rubicon's excluded files are copies of Toga's code, in 5 repositories, including 22 found by path.
- **Other copies, pyobjus:** the largest after Ren'Py were of BillBillBillBill/Tickeys-linux (26 files), rgsouthall/vi-suite06 (16), Kivy's own modules (11, 7 of them by their docstring), and kivy/kivy-ios (11).
- **Other copies, Rubicon:** the largest after Pyto were of markblundeberg/openswap (36 files), beeware/toga (22), and asweigart/mouseinfo (8).
- **Forks:** no fork of pyobjus, Rubicon, Plyer or Toga had a match, and no counted repository is a fork.

## Hand check

The copy rules were built by hand-checking random samples of the counted repositories and reading the files, then adding a rule for each kind of copy found, applied to both libraries. Each step, as the definitions record:

1. The approved rules left out the projects, their forks, generated folders and copies of the four named projects.
2. Samples showed copies of other projects, mostly Ren'Py games for pyobjus and copies of Toga's test backends and of other apps' iOS code for Rubicon. The path, root and top-level rules were added, and folder names such as `src` or `game` were made to need a third path part, because two parts alone matched unrelated files.
3. Ren'Py's renamed launchers were still counted, so the opening text of each counted file was read and the Ren'Py and Kivy markers added.
4. An early version also stopped renpy/renpy from counting as the origin of its own files, which raised pyobjus's count from 86 to 92. Origins now exclude only generated folders.
5. Plyer and Toga were then counted like any other repository that imports the library, as Kivy is, instead of being left out as part of each library's project. That showed two more problems, both fixed. The approved rule treated any `toga_` folder as a copy of Toga, which left out three separate Toga widget packages: `toga_console`, `toga_code_editor` and `toga_bitmap_view`. It now matches only Toga's own packages, such as `toga_cocoa` and `toga_iOS`, and `platforms` joined the common folder names, because two of those packages share the path `platforms/cocoa.py`. And 4 of Plyer's own files were treated as copies of markqvist/Sideband, which carries a copy of Plyer and has more stars, so pyobjus, Rubicon, Plyer and Toga are now always the origin of their own files. This raised pyobjus from 83 to 84 and Rubicon from 74 to 78.

After the last change, both full lists were checked by hand. Possible copies the rules miss:

| Library | Repository | Why it may be a copy |
|---|---|---|
| pyobjus | [gistable/gistable](https://github.com/gistable/gistable) | An archive of other people's gists |
| Rubicon | [RemusDBD/ctftools-all-in-one](https://github.com/RemusDBD/ctftools-all-in-one) | Its 3 files have the same paths as files in Pyto |
| Rubicon | [HaroonZm/Cassiopee](https://github.com/HaroonZm/Cassiopee) | A dataset folder of Pyto files, under other paths |
| Rubicon | [johndpope/face](https://github.com/johndpope/face) | A copy of an old version of Python-Apple-support's test app |
| Rubicon | [iamprivacy/Waves](https://github.com/iamprivacy/Waves) | One of its 2 files may be adapted from desktop-notifier's tests |

Removing all of them would give pyobjus 83 and Rubicon 74.

## Limits

- **The search doesn't return every file.** [kivy/kivy](https://github.com/kivy/kivy) imports pyobjus in at least two files, `kivy/core/clipboard/clipboard_nspaste.py` and `kivy/core/audio_output/audio_avplayer.py`, but the search returned only the second. A repository is missed only if the search misses all its files.
- **Direct use only.** Plyer and Toga are counted, but projects that use pyobjus only through Plyer, or Rubicon only through Toga, aren't, nor are Ren'Py games.
- **Public code on GitHub only.** Private repositories and code hosted elsewhere aren't seen.
- **This comparison's author** owns [ElliotGarbus/kivyforge](https://github.com/ElliotGarbus/kivyforge), one of Rubicon's 78, through 6 files in its iOS examples. None of the author's repositories is among pyobjus's.

## Files

| File | Contents |
|---|---|
| `raw/code_search.json` | Every match from every query and size range, the reported totals, and each repository's details |
| `raw/header_markers.json` | For each file the path rules counted, which marker its opening text carried, if any |
| `raw/summary.json` | The figures above, the full repository lists, and every exclusion with its reason |

To rerun the summary from the saved data:

```bash
python tests/section-07/summarize.py results/section-07/2026-11-08/raw/code_search.json summary.json results/section-07/2026-11-08/raw/header_markers.json
```

A new search would give different results, because GitHub's index and the repositories change.
