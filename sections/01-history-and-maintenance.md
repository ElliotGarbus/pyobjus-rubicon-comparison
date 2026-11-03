# 1. History and maintenance

**Status: draft for factual review.** Neither project has reviewed this section. Data is as of 2026-11-03 21:53 UTC. Metric IDs refer to the [approved definitions](../metrics/01-history-and-maintenance.md).

**Author's role:** Elliot Garbus (`ElliotGarbus`) leads this comparison, opened the proposal in [kivy/kivy#9469](https://github.com/kivy/kivy/issues/9469), has stated a view there in favor of Rubicon, and is the most active recent contributor to pyobjus. Elliot's first pyobjus commit is dated 2026-07-22. Results that depend on this work are shown with and without it.

**AI assistance:** data collection, analysis scripts and drafting were done with AI assistance (Claude, by Anthropic). Elliot Garbus directs the work, reviews it and is responsible for its content.

## Summary of findings

All figures are **Measured** at the snapshot unless labeled otherwise. This section makes no recommendation.

1. **Releases and activity:** Rubicon's work is steadier. Its median gap between stable releases is 107 days, against 502 for pyobjus, and it has had commits in 11 or 12 months of each year since 2023, against 2 to 4. pyobjus's recent activity came in a burst: 32 of its 34 merged PRs in 2026 landed in October. None of the 34 are in a PyPI release yet, although kivy-ios builds pyobjus from `master`, so its users get them.
2. **People:** in the last 12 months, Rubicon had 9 contributors and pyobjus had 3. Without its top contributor, Rubicon had 24 merged PRs and pyobjus had 7; that contributor is freakboy3742 for Rubicon and this comparison's author, ElliotGarbus, for pyobjus. Merging and releasing are concentrated on both: freakboy3742 merged 42 of Rubicon's last 60 PRs and triggered its last five releases, and AndreMiras merged 31 of pyobjus's last 40.
3. **New Python versions:** on macOS, installing pyobjus from PyPI without compiling needs a new wheel for each Python version. These arrived 18 to 448 days after Python 3.10 to 3.14 were released, and there was none for 3.15 after 25 days. Rubicon's universal wheel needs no new build, and Python 3.11 to 3.15 were each in its CI before their final releases. Installing doesn't by itself show that a version works. On iOS, wheel delays don't apply to pyobjus's documented route, kivy-ios, which compiles it from source on Python 3.11.6. Both libraries have other routes, listed under [iOS routes](#ios-routes).

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Relevant data |
|---|---|
| 1. pyobjus lacks a clear, active maintainer and a sustainable maintenance model | Findings 1 and 2. "Clear" and "sustainable" are judgments that this data informs but doesn't decide. |
| 2. Bursts followed by quiet periods are a sign of a stable project | The burst pattern is confirmed by finding 1. Whether it indicates stability isn't measured here. |
| 3. Rubicon has sustained activity across multiple maintainers | Findings 1 and 2 show sustained activity and more contributors. Finding 2 also shows that merging and releasing are concentrated. |
| 4. Some pyobjus issues closed in 2026 had been open for 5 to 12 years | Confirmed by I5: five issues, open 5.6 to 11.8 years. Whether any were memory-safety bugs is left to Section 2. |
| 5. At least 20 people and companies use these projects in mission-critical work | **Reported**. No users have been named, so this can't be verified. |
| 16. Separate pyobjus wheels per Python and platform (11 for 1.2.4), one wheel for Rubicon | Confirmed for releases: pyobjus 1.2.4 has 11 wheels and an sdist, and Rubicon 0.5.7 has one `py3-none-any` wheel and an sdist. Section 5 covers the build side. |

## Supporting facts

### Snapshot

|  | pyobjus | Rubicon ObjC |
|---|---|---|
| Repository | `kivy/pyobjus` | `beeware/rubicon-objc` |
| Commit at snapshot | [`0c204ada4a`](https://github.com/kivy/pyobjus/commit/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81) | [`6bf06390f7`](https://github.com/beeware/rubicon-objc/commit/6bf06390f720226da3d51477f38de3ff1e680eaf) |
| First commit | 2012-08-14 | 2014-10-17 |
| First merged PR by a person | 2013-07-22 | 2016-03-11 |

Raw data, scripts and cross-checks are in [`results/section-01/2026-11-03T215300Z`](../results/section-01/2026-11-03T215300Z). The scripts are in [`scripts`](../scripts).

### History

**pyobjus (Source, except where noted)**

| Date | Event |
|---|---|
| 2012-08-14 | [First commit](https://github.com/kivy/pyobjus/commit/8fd4293b2693d971e90225917ac89deed212f43d) by Thomas Hansen. Mathieu Virbel's [first commit](https://github.com/kivy/pyobjus/commit/57bacbe84298a4a6b2453c26a4121cce2fe813d1) follows on 2012-08-21. |
| 2013-06-11 | [A merge commit](https://github.com/kivy/pyobjus/commit/7a8eb8eb1915a7fe59dee561a65d24a1d7ace2a6) names a branch called `ivpusic_gsoc`. Ivan Pusic accounts for 138 commits, all between May and September 2013. The branch name suggests Google Summer of Code work (**Inferred**). |
| 2018-11-08 | [Python 3 support merged](https://github.com/kivy/pyobjus/commit/e73f36124ba4a536ee59cf91783c96b748f8cd39). |
| 2018-11-14 | Version 1.1.0, the earliest release on [PyPI](https://pypi.org/project/pyobjus/#history). |
| 2021-09-24 | [Native arm64 Mac build fix](https://github.com/kivy/pyobjus/commit/8eeea05baec7b563cd7d5e1301bfd995a89f2c8c). |
| 2022-03-26 | Version 1.2.1, the first with wheels on PyPI, following the [wheel build work](https://github.com/kivy/pyobjus/commit/586991a2a50e14ab454bfe00b3a48b2a7b9b733f). |
| 2025-12-29 | Version 1.2.4, the first with iOS wheels on PyPI. |
| 2026-07-22 | First commit by Elliot Garbus. |
| 2026-10-24 | First merge by AndreMiras, who made 28 merge commits by the snapshot. |

**Rubicon ObjC (Source, except where noted)**

| Date | Event |
|---|---|
| 2014-10-17 | [First commit](https://github.com/beeware/rubicon-objc/commit/c0edf0299964ce0a872065aad3023e0664362aa4) by Russell Keith-Magee, with version 0.1.0 on [PyPI](https://pypi.org/project/rubicon-objc/#history) the same day. |
| 2014 to 2015 | Russell Keith-Magee is the only author, with 33 non-merge commits. Versions 0.1.1 and 0.1.2 follow in October 2014, and 0.1.3 on 2015-03-14. |
| 2016-03-11 | [First merged PR](https://github.com/beeware/rubicon-objc/pull/6) by someone other than a bot, from glasnt. |
| 2016-05-18 | Version 0.2.0, after the longest gap between stable releases (431 days). |
| 2016-09-05 | The earliest [merge commit](https://github.com/beeware/rubicon-objc/commit/5c819a76f6a24ad768bf0739e2ae09797e78ac67) that names the `pybee` organization. `pybee/rubicon-objc` now redirects to `beeware/rubicon-objc`. The date of the move wasn't established (**Unknown**). |
| 2016-09-26 | [Python 2 compatibility code removed](https://github.com/beeware/rubicon-objc/commit/8919d882f3b710fa8927b3d41e1ee1369769ef19), with further cleanup commits through 2020. |
| 2016 to 2020 | dgelessus contributes 305 commits, the second most of anyone, from 2016-12-08 to 2020-11-07. |
| 2017-05-30 | [iOS library loading fix](https://github.com/beeware/rubicon-objc/commit/c6ec11437bbbeb43dfa89d7439687344888de75a) merged. Earlier iOS work appears in the [release notes](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/about/releases.md). |
| 2026-09-05 | [iOS CI configuration added](https://github.com/beeware/rubicon-objc/commit/880babd7c39c3011057c8335f383daec6661a10b). |
| 2026-09-30 | Version 0.5.7. Its release notes say iOS is now actively tested as part of development. |

### Releases (R1 to R4)

| Measure | pyobjus | Rubicon ObjC |
|---|---|---|
| Stable PyPI versions (R1) | 6 | 33 |
| Latest stable version (R2) | 1.2.4, 2025-12-29 | 0.5.7, 2026-09-30 |
| Age of latest stable version at snapshot (R2, R3) | 309 days | 35 days |
| Median gap between stable versions, all time (R3) | 502 days | 107 days |
| Median gap, last 5 years (R3) | 457 days | 112 days |
| Longest gap, all time (R3) | 801 days (2023-10-20 to 2025-12-29) | 431 days (2015-03-14 to 2016-05-18) |
| Longest gap, last 5 years (R3) | 801 days (2023-10-20 to 2025-12-29) | 386 days (2021-11-13 to 2022-12-04) |
| PRs by people merged since latest stable (R4) | 34 | 3 |

| Year | pyobjus stable | Rubicon stable | Other Rubicon versions |
|---|---|---|---|
| 2014 | 0 | 3 | None |
| 2015 | 0 | 1 | None |
| 2016 | 0 | 4 | None |
| 2017 | 0 | 6 | None |
| 2018 | 1 | 1 | None |
| 2019 | 0 | 1 | None |
| 2020 | 1 | 1 | None |
| 2021 | 0 | 2 | None |
| 2022 | 1 | 1 | None |
| 2023 | 2 | 3 | 1 pre-release, 1 yanked |
| 2024 | 0 | 2 | None |
| 2025 | 1 | 4 | None |
| 2026 | 0 | 4 | 1 pre-release |

PyPI's history for pyobjus starts in 2018, so earlier releases, if any, aren't counted. Of the 34 pyobjus PRs merged since 1.2.4, 32 are by ElliotGarbus and 2 are by AndreMiras. The [kivy-ios recipe](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/pyobjus/__init__.py) builds from `master`, so R4 describes PyPI users rather than kivy-ios users. All 3 merged since Rubicon 0.5.7 are by mgstabrani.

### Python and iOS support (R5, R6)

| Python | Final release | pyobjus install (a) | Rubicon install (a) | pyobjus CI (b) | Rubicon CI (b) | pyobjus classifier (c) | Rubicon classifier (c) |
|---|---|---|---|---|---|---|---|
| 3.10 | 2021-10-04 | 173 days (1.2.1) | Already installable (0.4.1) | 165 days | 39 days | 586 days | 40 days |
| 3.11 | 2022-10-24 | 201 days (1.2.2) | Already installable (0.4.2) | 201 days | 159 days before final | 201 days | 41 days |
| 3.12 | 2023-10-02 | 18 days (1.2.3) | Already installable (0.4.6) | 13 days | 326 days before final | 18 days | 302 days before final |
| 3.13 | 2024-10-07 | 448 days (1.2.4) | Already installable (0.4.9) | 435 days | 371 days before final | 448 days | 187 days before final |
| 3.14 | 2025-10-07 | 83 days (1.2.4) | Already installable (0.5.2) | 70 days | 357 days before final | 83 days | 274 days before final |
| 3.15 | 2026-10-09 | None on PyPI at snapshot | Already installable (0.5.7) | Not in CI at snapshot | 340 days before final | Not declared at snapshot | 310 days before final |

Days are counted from each Python version's final release. The install columns cover macOS on Apple Silicon without compiling; pyobjus can also be compiled from its source distribution. CI dates include pre-release versions of Python. Rubicon's install column reflects its universal wheel, which installs regardless of whether that Python version has been tested.

### iOS routes

Apps can reach iOS in several ways, so no single date describes availability. This table is **Source** unless labeled otherwise. None of these routes has been tested for this comparison yet. Section 3 will test them on a physical iPhone where possible.

| Route | Python | pyobjus | Rubicon ObjC |
|---|---|---|---|
| **kivy-ios** | [3.11.6](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/python3/__init__.py), built by kivy-ios | [Compiled from `master`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/pyobjus/__init__.py) by a recipe dating from [2015-02-18](https://github.com/kivy/kivy-ios/commits/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/pyobjus/__init__.py). This is the route in [pyobjus's iOS docs](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/docs/source/pyobjus_ios.rst). | No recipe. kivy-ios [documents `toolchain pip install`](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/README.md) for packages that need no compiling. **Reported:** [`@Block` crashes on iOS](https://github.com/kivy/kivy-ios/issues/998#issuecomment-5726400770) on this Python. |
| **KivyForge** | [3.15](https://github.com/kivy/kivy-ios/issues/998#issuecomment-5722409000) | Wheels from kivy-mobile-wheels: 1.2.4 and 1.2.5.dev202610250845. KivyForge and these wheels are maintained by this comparison's author. | Universal wheel from PyPI. **Reported:** [works alongside pyobjus](https://github.com/kivy/kivy/issues/9469#issuecomment-6540817502). |
| **Briefcase** | [BeeWare's support packages](https://github.com/beeware/Python-Apple-support), or official CPython packages [from 3.15.0b1](https://github.com/beeware/briefcase/blob/fee777ed204fe867a8486d8947137dacdb7f05f4/src/briefcase/platforms/iOS/xcode.py) | No documented use found. | Rubicon's own iOS test route. Its [CI](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/.github/workflows/ci.yml) lists Python 3.11 to 3.15 and [runs on the simulator](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/tox.ini). Whether those jobs pass is covered in Section 5. Toga's iOS backend also depends on it. |
| **PyPI wheels (R6)**, for a tool that installs them | 3.13 to 3.15 | 3.13: 448 days after Python's release (1.2.4); 3.14: 83 days after Python's release (1.2.4); 3.15: none at snapshot. | 3.13: already installable (0.4.9); 3.14: already installable (0.5.2); 3.15: already installable (0.5.7). The wheel is universal, so this doesn't show that iOS works. |

[PEP 730](https://peps.python.org/pep-0730/) made iOS a supported platform (Tier 3) from Python 3.13. Briefcase's source says official CPython iOS packages are available from 3.15.0b1. kivy-ios's Python 3.11.6 predates both.

### Activity and contributors by year (A1, A3, C1, C3, C5)

| Year | pyobjus PRs | without ElliotGarbus | Active months | without ElliotGarbus | Contributors | New | Rubicon PRs | without freakboy3742 | Active months | without freakboy3742 | Contributors | New |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2012 | 0 | 0 | 1 | 1 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2013 | 4 | 4 | 6 | 6 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2014 | 2 | 2 | 5 | 5 | 4 | 3 | 0 | 0 | 1 | 0 | 1 | 1 |
| 2015 | 1 | 1 | 6 | 6 | 2 | 1 | 0 | 0 | 5 | 0 | 1 | 0 |
| 2016 | 9 | 9 | 6 | 6 | 3 | 2 | 5 | 5 | 8 | 5 | 7 | 6 |
| 2017 | 1 | 1 | 2 | 2 | 2 | 2 | 48 | 37 | 12 | 12 | 6 | 4 |
| 2018 | 5 | 5 | 2 | 2 | 2 | 0 | 20 | 17 | 7 | 7 | 6 | 3 |
| 2019 | 6 | 6 | 3 | 3 | 4 | 2 | 4 | 3 | 4 | 3 | 4 | 2 |
| 2020 | 7 | 7 | 6 | 6 | 5 | 2 | 38 | 30 | 9 | 7 | 2 | 0 |
| 2021 | 2 | 2 | 3 | 3 | 3 | 2 | 11 | 8 | 6 | 5 | 2 | 1 |
| 2022 | 4 | 4 | 3 | 3 | 2 | 0 | 13 | 3 | 8 | 3 | 4 | 2 |
| 2023 | 13 | 13 | 4 | 4 | 3 | 1 | 26 | 9 | 12 | 5 | 5 | 3 |
| 2024 | 5 | 5 | 3 | 3 | 2 | 0 | 22 | 14 | 11 | 7 | 6 | 2 |
| 2025 | 6 | 6 | 2 | 2 | 2 | 0 | 23 | 13 | 11 | 7 | 6 | 5 |
| 2026 | 34 | 2 | 2 | 1 | 2 | 2 | 36 | 20 | 11 | 10 | 9 | 5 |

"Without" columns remove that person's PRs and commits. "New" counts people whose first merged PR or commit falls in that year. Merge commits aren't counted as authorship. PRs weren't in use for a project's earliest period, so PR counts before its first merged PR in the snapshot table are undercounted. 2026 is a partial year.

### Activity over time windows (A1, A2, A4, C1)

| Measure | pyobjus | Rubicon ObjC |
|---|---|---|
| Merged PRs by people (A1), all time | 99 | 246 |
| Merged PRs by people (A1), last 24 months | 40 | 60 |
| Merged PRs by people (A1), last 12 months | 39 | 42 |
| Commits by people (A2), all time | 408 | 1138 |
| Commits by people (A2), last 24 months | 42 | 136 |
| Commits by people (A2), last 12 months | 41 | 48 |
| Contributors (C1), all time | 20 | 34 |
| Contributors (C1), last 24 months | 4 | 14 |
| Contributors (C1), last 12 months | 3 | 9 |
| Bot PRs merged, all time | 23 | 438 |
| Bot PRs merged, last 12 months | 11 | 130 |
| Current gap since a commit by a person (A4) | 3 days | 2 days |
| Longest gap, all time (A4) | 429 days (2017-08-11 to 2018-10-14) | 217 days (2019-05-25 to 2019-12-29) |
| Longest gap, last 5 years (A4) | 250 days (2024-10-04 to 2025-06-10) | 94 days (2021-11-13 to 2022-02-15) |

Compare the commit rows with care. Merge commits were 30 of 86 for pyobjus and 7 of 374 for Rubicon over the last 24 months, so the projects land work differently.

### Concentration (C2)

| Window and unit | pyobjus top 1 / top 2 / people for 50% | pyobjus top three | Rubicon top 1 / top 2 / people for 50% | Rubicon top three |
|---|---|---|---|---|
| All time, merged PRs | 32% / 59% / 2 | ElliotGarbus (32), misl6 (26), kived (5) | 35% / 64% / 2 | freakboy3742 (87), dgelessus (70), kattni (15) |
| All time, commits | 34% / 52% / 2 | ivpusic (138), tito (76), Zen-CODE (63) | 45% / 72% / 2 | freakboy3742 (513), dgelessus (305), samschott (140) |
| Last 24 months, merged PRs | 80% / 92% / 1 | ElliotGarbus (32), misl6 (5), AndreMiras (2) | 43% / 68% / 2 | freakboy3742 (26), kattni (15), mgstabrani (8) |
| Last 24 months, commits | 81% / 93% / 1 | ElliotGarbus (34), misl6 (5), AndreMiras (2) | 48% / 75% / 2 | samschott (65), freakboy3742 (37), kattni (15) |
| Last 12 months, merged PRs | 82% / 95% / 1 | ElliotGarbus (32), misl6 (5), AndreMiras (2) | 43% / 64% / 2 | freakboy3742 (18), kattni (9), mgstabrani (8) |
| Last 12 months, commits | 83% / 95% / 1 | ElliotGarbus (34), misl6 (5), AndreMiras (2) | 50% / 69% / 1 | freakboy3742 (24), kattni (9), mgstabrani (8) |

Each cell lists the share from the top person, the share from the top two, and the fewest people who account for at least half.

### Results without the top contributor (C3)

| Measure | All contributors | Without top contributor |
|---|---|---|
| pyobjus: Merged PRs, last 12 months | 39 | 7 |
| pyobjus: Merged PRs, last 24 months | 40 | 8 |
| pyobjus: Contributors, last 12 months | 3 | 2 |
| pyobjus: Contributors, last 24 months | 4 | 3 |
| pyobjus: Longest commit gap, last 5 years | 250 days (2024-10-04 to 2025-06-10) | 298 days (2025-12-29 to 2026-10-23) |
| pyobjus: Current commit gap | 3 days | 8 days |
| Rubicon: Merged PRs, last 12 months | 42 | 24 |
| Rubicon: Merged PRs, last 24 months | 60 | 34 |
| Rubicon: Contributors, last 12 months | 9 | 8 |
| Rubicon: Contributors, last 24 months | 14 | 13 |
| Rubicon: Longest commit gap, last 5 years | 94 days (2021-11-13 to 2022-02-15) | 272 days (2022-02-16 to 2022-11-15) |
| Rubicon: Current commit gap | 2 days | 2 days |

ElliotGarbus is pyobjus's top contributor over the last 24 months, so the two exclusions in the definition are the same calculation. The Rubicon rows exclude freakboy3742.

### Merging and review (C4)

| Measure | pyobjus | Rubicon ObjC |
|---|---|---|
| Last 24 months: people who merged | AndreMiras (31), misl6 (6), kuzeyron (2), akshayaurora (1) | freakboy3742 (42), mhsmith (14), kattni (3), samschott (1) |
| Last 24 months: merged by someone other than the author | 82% (33 of 40) | 78% (47 of 60) |
| Last 24 months: reviewed by a person other than the author | 85% (34 of 40) | 87% (52 of 60) |
| Last 12 months: people who merged | AndreMiras (31), misl6 (5), kuzeyron (2), akshayaurora (1) | freakboy3742 (32), mhsmith (6), kattni (3), samschott (1) |
| Last 12 months: merged by someone other than the author | 82% (32 of 39) | 71% (30 of 42) |
| Last 12 months: reviewed by a person other than the author | 85% (33 of 39) | 81% (34 of 42) |

### Issues and PRs (I1, I2)

| Open at snapshot | Total | Under 1 year | 1 to 3 years | 3 to 5 years | Over 5 years | Opened by ElliotGarbus |
|---|---|---|---|---|---|---|
| pyobjus issues | 16 | 16 | 0 | 0 | 0 | 16 |
| pyobjus PRs | 4 | 3 | 0 | 1 | 0 | 3 |
| Rubicon issues | 18 | 2 | 3 | 2 | 11 | 0 |
| Rubicon PRs | 2 | 1 | 1 | 0 | 0 | 0 |

| Year | pyobjus issues opened | closed | pyobjus PRs opened | closed | Rubicon issues opened | closed | Rubicon PRs opened | closed |
|---|---|---|---|---|---|---|---|---|
| 2012 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2013 | 1 | 2 | 5 | 5 | 0 | 0 | 0 | 0 |
| 2014 | 6 | 0 | 4 | 2 | 0 | 0 | 0 | 0 |
| 2015 | 2 | 1 | 2 | 1 | 4 | 2 | 1 | 0 |
| 2016 | 8 | 7 | 8 | 9 | 7 | 3 | 7 | 5 |
| 2017 | 2 | 0 | 1 | 1 | 23 | 18 | 52 | 55 |
| 2018 | 2 | 0 | 6 | 5 | 14 | 8 | 23 | 21 |
| 2019 | 3 | 4 | 4 | 7 | 5 | 2 | 5 | 4 |
| 2020 | 10 | 8 | 7 | 7 | 20 | 20 | 39 | 42 |
| 2021 | 9 | 3 | 2 | 2 | 7 | 8 | 11 | 11 |
| 2022 | 2 | 3 | 5 | 4 | 7 | 4 | 13 | 13 |
| 2023 | 3 | 15 | 14 | 13 | 15 | 16 | 28 | 27 |
| 2024 | 0 | 0 | 4 | 5 | 11 | 11 | 26 | 26 |
| 2025 | 1 | 0 | 6 | 6 | 8 | 8 | 24 | 24 |
| 2026 | 21 | 12 | 39 | 36 | 15 | 18 | 41 | 40 |

| All-time closures | pyobjus | Rubicon ObjC |
|---|---|---|
| Issues closed by a person | 54 | 118 |
| Issues closed by automation | 1 | 0 |
| Issues closed as completed | 43 | 117 |
| Issues closed as not planned | 12 | 1 |
| PRs merged | 99 | 246 |
| PRs closed without merging by a person | 4 | 22 |

Automation closed only one pyobjus issue, so its no-response workflow has little effect on these counts. Issue counts exclude bot-authored items.

### Responsiveness (I3, I4)

**Window for I3:** items opened from 2024-11-03 to 2026-10-04.

| Opened by non-maintainers (I3) | pyobjus | Rubicon ObjC |
|---|---|---|
| Issues answered within 7 days | 0 of 2 | 6 of 6 |
| Issues answered within 30 days | 0 of 2 | 6 of 6 |
| PRs answered within 7 days | No items | 94% (16 of 17) |
| PRs answered within 30 days | No items | 100% (17 of 17) |

Here, a maintainer is anyone GitHub reports as `OWNER`, `MEMBER` or `COLLABORATOR`, or anyone who has merged a PR in that project. The second condition was added after collection because association alone misclassified people: `kattni`, on BeeWare's team page with 99 merges, was reported as a `CONTRIBUTOR`. Using association alone gives these results:

| Opened by non-maintainers (I3) | pyobjus | Rubicon ObjC |
|---|---|---|
| Issues answered within 7 days | 0 of 2 | 60% (6 of 10) |
| Issues answered within 30 days | 0 of 2 | 60% (6 of 10) |
| PRs answered within 7 days | No items | 88% (28 of 32) |
| PRs answered within 30 days | No items | 94% (30 of 32) |

Removing ElliotGarbus as a responder doesn't change the pyobjus row. GitHub reports ElliotGarbus as a `MEMBER`, so Elliot's 4 items opened in this window aren't counted as non-maintainer items. All 7 other pyobjus PRs in the window were also opened by people reported as members.

**Window for I4:** items opened from 2024-11-03 to 2026-08-05.

| All items by people (I4) | pyobjus | Rubicon ObjC |
|---|---|---|
| Issues closed within 90 days | 2 of 4 | 86% (19 of 22) |
| PRs closed within 90 days | 8 of 8 | 96% (51 of 53) |
| PRs merged within 90 days | 8 of 8 | 89% (47 of 53) |
| Median time to merge, merged PRs only | 3.1 days (n=8) | 0.2 days (n=47) |

The pyobjus samples are small, and I4 stops 90 days before the snapshot, which excludes the October 2026 activity. Support on Discord and GitHub Discussions isn't included for either project.

### Long-open issues closed (I5)

| Project | Issue | Opened | Closed | Years open | Closed by | Linked to a PR by ElliotGarbus |
|---|---|---|---|---|---|---|
| pyobjus | [#15](https://github.com/kivy/pyobjus/issues/15) bad kCFTaggedObjectID_Integer definition ? | 2014-12-16 | 2026-10-21 | 11.8 | ElliotGarbus | No |
| pyobjus | [#21](https://github.com/kivy/pyobjus/issues/21) IndexError in type_enc.pxi | 2015-12-09 | 2026-10-21 | 10.9 | ElliotGarbus | No |
| pyobjus | [#44](https://github.com/kivy/pyobjus/issues/44) Can't clone pyobjus on Windows, MS-DOS reserved word as a folder | 2018-11-09 | 2026-10-23 | 8.0 | AndreMiras | Yes |
| pyobjus | [#70](https://github.com/kivy/pyobjus/issues/70) KeyError at field_list.append() | 2020-10-14 | 2026-10-21 | 6.0 | ElliotGarbus | No |
| pyobjus | [#76](https://github.com/kivy/pyobjus/issues/76) autoclass('NSString', ... ) => 'TypeError: expected bytes, str found' | 2021-03-19 | 2026-10-25 | 5.6 | AndreMiras | Yes |
| Rubicon ObjC | [#48](https://github.com/beeware/rubicon-objc/issues/48) Improve memory management documentation | 2017-07-08 | 2024-12-05 | 7.4 | mhsmith | No |
| Rubicon ObjC | [#137](https://github.com/beeware/rubicon-objc/issues/137) Async tests sometimes randomly cause errors | 2019-05-25 | 2026-05-29 | 7.0 | freakboy3742 | No |
| Rubicon ObjC | [#183](https://github.com/beeware/rubicon-objc/issues/183) Speed up instantiating new class instances | 2020-08-26 | 2026-05-29 | 5.8 | freakboy3742 | No |
| Rubicon ObjC | [#188](https://github.com/beeware/rubicon-objc/issues/188) Consider using sphinx-autoapi to generate docs without having to import rubicon.objc | 2020-09-19 | 2025-10-31 | 5.1 | freakboy3742 | No |
| Rubicon ObjC | [#223](https://github.com/beeware/rubicon-objc/issues/223) Calling performSelector for a @objc_method created by rubicon from Objective C crashes in Python 3.9 | 2021-07-07 | 2026-09-03 | 5.2 | freakboy3742 | No |

For pyobjus, 5 issues qualify. Removing the 2 linked to Elliot's PRs leaves 3. All 3 were closed by ElliotGarbus directly, so none closed without Elliot's involvement. The check for links relies on GitHub's records, so a manual close that followed a PR may not show a link. No PRs open for five years were closed by either project in this window.

### Sustainability factors (S1 to S6)

| Factor | pyobjus | Rubicon ObjC |
|---|---|---|
| **PyPI access (S1)** | Five owner accounts: Mathieu.Virbel, kivybot, matham, misl6, tshirtman. | Held by the `beeware` organization. Its individual roles aren't listed publicly. |
| **Last five releases (S1)** | 1.2.0 and 1.2.1: matham. 1.2.2 and 1.2.3: misl6 by release author or tag commit. 1.2.4: misl6 triggered the workflow. GitHub's run record for the older releases isn't available. | All five, 0.5.3 to 0.5.7: freakboy3742 triggered the workflow. |
| **Release mechanism (S1)** | [Workflow](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/.github/workflows/deploy.yml) on tag push, using a stored PyPI password. | [Workflows](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/.github/workflows/publish.yml) on tag and release, using trusted publishing. |
| **Governance and maintainers (S2)** | [Kivy's about page](https://kivy.org/about.html) lists core developers for Kivy overall and doesn't mention pyobjus. [`setup.py`](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/setup.py) names no author or maintainer, and the repository has no `CODEOWNERS` file. We found no published decision process. | The [team page](https://beeware.org/about/team/) lists five current members for BeeWare overall and doesn't assign Rubicon to any of them. [`pyproject.toml`](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/pyproject.toml) lists the BeeWare Team as maintainers, and the repository has no `CODEOWNERS` file. The [governance page](https://beeware.org/community/governance/) sets out core team duties and names Russell Keith-Magee as final decision-maker. |
| **Funding (S3)** | [Kivy Open Collective](https://opencollective.com/kivy): balance $32,103.51, yearly budget $2,937, total received $41,280.32. This covers all Kivy projects. Paid maintenance: **Unknown**. | [Memberships](https://beeware.org/membership/) from $200 a month, with Anaconda listed as a Gold member, and [GitHub Sponsors through freakboy3742](https://github.com/beeware/.github/blob/4e0b8b4799273367f7013d273b9f02b201eb5840/FUNDING.yml). Amounts and paid maintenance: **Unknown**. |
| **First-party dependents (S4)** | [Plyer](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/setup.py) declares it for iOS and macOS. [kivy-ios](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/pyobjus/__init__.py) has a recipe. Kivy's `setup.py` and `pyproject.toml` at [`9f31209`](https://github.com/kivy/kivy/tree/9f31209822494bbd3e7eafacad29534661870054) don't declare it, though two core modules use it. | [Toga's Cocoa](https://github.com/beeware/toga/blob/dd833f156e13d15ed26720ef50b8e544046619c5/cocoa/pyproject.toml) and [iOS](https://github.com/beeware/toga/blob/dd833f156e13d15ed26720ef50b8e544046619c5/iOS/pyproject.toml) backends declare `rubicon-objc >= 0.5.1, < 0.6.0`. |
| **Policies (S5)** | No contributing, conduct, security or support file in the repository. [kivy/kivy](https://github.com/kivy/kivy/tree/9f31209822494bbd3e7eafacad29534661870054) has contributing and conduct files. | Contributing and conduct files in the repository. [BeeWare's `.github` repository](https://github.com/beeware/.github/tree/4e0b8b4799273367f7013d273b9f02b201eb5840) adds security, support and AI policies. |
| **License (S6)** | [MIT](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/LICENSE). | [BSD-3-Clause](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/LICENSE), per `pyproject.toml`. |

Web pages were read on 2026-11-03 and may change. "We found no" means the pages listed here were checked, and doesn't prove a document doesn't exist.

### Adoption signals (U1, U2)

Downloads from 2026-05-07 to 2026-11-02, from [pypistats.org](https://pypistats.org), excluding known mirrors:

| Operating system | pyobjus | Rubicon ObjC |
|---|---|---|
| macOS (Darwin) | 9,582 | 809,704 |
| Linux | 5,571 | 3,214,762 |
| Windows | 242 | 83,970 |
| Other | 16 | 8,933 |
| Not recorded | 689 | 13,978 |
| Total | 16,100 | 4,131,347 |

These counts include CI runs and installs pulled in as dependencies, and apps bundled for iOS aren't re-downloaded when users install them. Linux, which neither library targets, accounts for 35% of pyobjus's downloads and 78% of Rubicon's, so many are likely automation or dependency resolution (**Inferred**).

**Named production use (U2):**
- **Reported:** [akshayaurora](https://github.com/kivy/kivy/issues/9469#issuecomment-6517712158) says shipped Kivy iOS and macOS apps use pyobjus for Core Bluetooth, Bonjour, GPS, pickers and notifications, and [says](https://github.com/kivy/kivy/issues/9469#issuecomment-6540219422) at least 20 people and companies use these projects in mission-critical work. No users are named.
- **Reported:** [kengoon](https://github.com/kivy/kivy/issues/9469#issuecomment-6540733322) says they have used both libraries with Kivy. Their [pyobjus-firebase](https://github.com/PySimpleObjC/pyobjus-firebase) and [pyios-firebase](https://github.com/PySimpleObjC/pyios-firebase) repositories are public.
- **Reported:** Rubicon's [success stories page](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/docs/en/about/success.md) lists Travel Tips, an iOS App Store app, as using Rubicon.
- **Source:** Toga depends on Rubicon, as shown in S4. Its downstream users are covered in Section 7.

Corrections or named uses of either library are welcome, with a source.
