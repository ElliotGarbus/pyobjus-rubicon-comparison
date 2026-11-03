# 1. History and maintenance

**Status: draft for factual review.** Neither project has reviewed this section. Data is as of 2026-11-03 21:53 UTC. Metric IDs refer to the [approved definitions](../metrics/01-history-and-maintenance.md).

**Author's role:** Elliot Garbus (`ElliotGarbus`) leads this comparison, opened the proposal in [kivy/kivy#9469](https://github.com/kivy/kivy/issues/9469), has stated a view there in favor of Rubicon, and is the most active recent contributor to pyobjus. Elliot's first pyobjus commit is dated 2026-07-22. Results that depend on this work are shown with and without it.

**AI assistance:** data collection, analysis scripts and drafting were done with AI assistance (Claude, by Anthropic). Elliot Garbus directs the work, reviews it and is responsible for its content.

## Summary of findings

All figures are **Measured** unless labeled otherwise. This section makes no recommendation.

1. **Age:** the projects are similar in age. pyobjus's first commit is from August 2012 and Rubicon ObjC's is from October 2014.
2. **Releases:** Rubicon has released more often. It has 33 stable versions on PyPI, four of them in 2026, with a median gap of 107 days. pyobjus has six stable versions on PyPI since 2018, with a median gap of 502 days. Its latest, 1.2.4, is from December 2025, and 34 PRs by people have merged since then.
3. **Activity pattern:** Rubicon's commits have been spread across 11 or 12 months a year since 2023. pyobjus's have fallen in 2 to 4 months a year over that time, and 32 of its 34 merged PRs in 2026 landed in October. Both projects merged a similar number of PRs by people over the last 12 months: 39 for pyobjus and 42 for Rubicon.
4. **Contributors:** in the last 12 months, Rubicon had 9 contributors and pyobjus had 3. ElliotGarbus wrote 32 of pyobjus's 39 merged PRs (82%), and freakboy3742 wrote 18 of Rubicon's 42 (43%). Without those two people, the counts are 7 PRs from 2 contributors for pyobjus and 24 PRs from 8 contributors for Rubicon.
5. **Merging and releasing:** both are concentrated in a few people on each project. Over the last 24 months each had 4 people merging PRs, with AndreMiras merging 31 of 40 in pyobjus and freakboy3742 merging 42 of 60 in Rubicon. freakboy3742 triggered all of Rubicon's last five releases. On pyobjus, the last five releases trace to two people, matham and misl6, and misl6 triggered the latest.
6. **Backlogs:** pyobjus has no open issue older than a year. All 16 of its open issues were opened by ElliotGarbus. Five issues that had been open for 5.6 to 11.8 years closed in October 2026, each closed by ElliotGarbus or linked to one of Elliot's PRs. Rubicon has 18 open issues, 11 of them over five years old, and it closed five such issues over the last 24 months.
7. **Responsiveness:** the samples are too small for a fair comparison. In the window measured, pyobjus had only 2 issues and no PRs from non-maintainers, and neither issue had a maintainer response within 30 days. Rubicon had 6 such issues, all answered within 7 days, and 17 such PRs, 16 of them answered within 7 days and all within 30.
8. **New Python versions:** PyPI wheels for pyobjus arrived 18 to 448 days after each final release from Python 3.10 to 3.14. It had no Python 3.15 wheel on PyPI, and no 3.15 CI, 25 days after that release. Rubicon's single universal wheel was already installable on each release day, and Rubicon added each version from 3.11 to 3.15 to CI before its final release. Being installable doesn't show that a version works, so the CI and classifier dates matter here too.
9. **Project structure (Source):** BeeWare publishes a named team and a governance page, and offers paid memberships, with Anaconda listed as a Gold member. Kivy lists core developers and has an Open Collective with a reported balance of $32,103.51. The funds cover Kivy as a whole, not pyobjus alone. We found no published Kivy governance document. Neither project publicly states who, if anyone, is paid to maintain the library (**Unknown**).
10. **Downloads:** PyPI recorded 16,100 pyobjus downloads and 4,131,347 Rubicon downloads over 180 days. These counts don't measure users or apps. Linux, which neither library targets, accounts for 35% of pyobjus's downloads and 78% of Rubicon's, so many are likely automation or dependency resolution (**Inferred**).

**What these figures don't measure:** code quality, defect rates, stability, or how many apps depend on either library. The thread's disagreement about whether quiet periods indicate stability can't be settled by this data alone. Sections 2, 3 and 5 cover related evidence.

## Claims from the discussion

| Claim ([register](../CLAIMS.md)) | Relevant data |
|---|---|
| 1. pyobjus lacks a clear, active maintainer and a sustainable maintenance model | Findings 3 to 5. "Clear" and "sustainable" are judgments that this data informs but doesn't decide. |
| 2. Bursts followed by quiet periods are a sign of a stable project | The burst pattern is confirmed by finding 3. Whether it indicates stability isn't measured here. |
| 3. Rubicon has sustained activity across multiple maintainers | Findings 3 and 4 show sustained activity and more contributors. Finding 5 shows that merging and releasing are still concentrated. |
| 4. Some pyobjus issues closed in 2026 had been open for 5 to 12 years | Confirmed by I5: five issues, open 5.6 to 11.8 years. Whether any were memory-safety bugs is left to Section 2. |
| 5. At least 20 people and companies use these projects in mission-critical work | **Reported**. No users have been named, so this can't be verified. |
| 16. Separate pyobjus wheels per Python and platform (11 for 1.2.4), one wheel for Rubicon | Confirmed for releases: pyobjus 1.2.4 has 11 wheels and an sdist, and Rubicon 0.5.7 has one `py3-none-any` wheel and an sdist. Section 5 covers the build side. |

## Supporting facts

### Snapshot

{{snapshot}}

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

{{releases}}

{{releases_by_year}}

PyPI's history for pyobjus starts in 2018, so earlier releases, if any, aren't counted. Of the 34 pyobjus PRs merged since 1.2.4, 32 are by ElliotGarbus and 2 are by AndreMiras. All 3 merged since Rubicon 0.5.7 are by mgstabrani.

### Python and iOS support (R5, R6)

{{python_support}}

Days are counted from each Python version's final release. CI dates include pre-release versions of Python. Rubicon's install column reflects its universal wheel, which installs regardless of whether that Python version has been tested.

**iOS.** [PEP 730](https://peps.python.org/pep-0730/) made iOS a supported platform (Tier 3) from Python 3.13, so R6 starts there.

{{ios}}

Rubicon's iOS column has the same limit: its wheel doesn't declare iOS separately. Rubicon's iOS CI dates from September 2026, as shown in the timeline above.

pyobjus iOS wheels for Python 3.15 exist outside PyPI on [kivy-mobile-wheels](https://elliotgarbus.github.io/kivy-mobile-wheels/simple/pyobjus/), which Elliot maintains: versions 1.2.4 and 1.2.5.dev202610250845. They aren't counted above.

### Activity and contributors by year (A1, A3, C1, C3, C5)

{{activity_by_year}}

"Without" columns remove that person's PRs and commits. "New" counts people whose first merged PR or commit falls in that year. Merge commits aren't counted as authorship. PRs weren't in use for a project's earliest period, so PR counts before its first merged PR in the snapshot table are undercounted. 2026 is a partial year.

### Activity over time windows (A1, A2, A4, C1)

{{activity_windows}}

Compare the commit rows with care. Merge commits were 30 of 86 for pyobjus and 7 of 374 for Rubicon over the last 24 months, so the projects land work differently.

### Concentration (C2)

{{concentration}}

Each cell lists the share from the top person, the share from the top two, and the fewest people who account for at least half.

### Results without the top contributor (C3)

{{sensitivity}}

ElliotGarbus is pyobjus's top contributor over the last 24 months, so the two exclusions in the definition are the same calculation. The Rubicon rows exclude freakboy3742.

### Merging and review (C4)

{{merge_review}}

### Issues and PRs (I1, I2)

{{backlog}}

{{flow}}

{{closure_types}}

Automation closed only one pyobjus issue, so its no-response workflow has little effect on these counts. Issue counts exclude bot-authored items.

### Responsiveness (I3, I4)

**Window for I3:** items opened from 2024-11-03 to 2026-10-04.

{{response}}

Here, a maintainer is anyone GitHub reports as `OWNER`, `MEMBER` or `COLLABORATOR`, or anyone who has merged a PR in that project. The second condition was added after collection because association alone misclassified people: `kattni`, on BeeWare's team page with 99 merges, was reported as a `CONTRIBUTOR`. Using association alone gives these results:

{{response_association_only}}

Removing ElliotGarbus as a responder doesn't change the pyobjus row. GitHub reports ElliotGarbus as a `MEMBER`, so Elliot's 4 items opened in this window aren't counted as non-maintainer items. All 7 other pyobjus PRs in the window were also opened by people reported as members.

**Window for I4:** items opened from 2024-11-03 to 2026-08-05.

{{resolution}}

The pyobjus samples are small, and I4 stops 90 days before the snapshot, which excludes the October 2026 activity. Support on Discord and GitHub Discussions isn't included for either project.

### Long-open issues closed (I5)

{{long_open}}

For pyobjus, 5 issues qualify. Removing the 2 linked to Elliot's PRs leaves 3. All 3 were closed by ElliotGarbus directly, so none closed without Elliot's involvement. The check for links relies on GitHub's records, so a manual close that followed a PR may not show a link. No PRs open for five years were closed by either project in this window.

### Sustainability factors (S1 to S6)

| Factor | pyobjus | Rubicon ObjC |
|---|---|---|
| **PyPI access (S1)** | Five owner accounts: Mathieu.Virbel, kivybot, matham, misl6, tshirtman. | Held by the `beeware` organization. Its individual roles aren't listed publicly. |
| **Last five releases (S1)** | 1.2.0 and 1.2.1: matham. 1.2.2 and 1.2.3: misl6 by release author or tag commit. 1.2.4: misl6 triggered the workflow. GitHub's run record for the older releases isn't available. | All five, 0.5.3 to 0.5.7: freakboy3742 triggered the workflow. |
| **Release mechanism (S1)** | [Workflow](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/.github/workflows/deploy.yml) on tag push, using a stored PyPI password. | [Workflows](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/.github/workflows/publish.yml) on tag and release, using trusted publishing. |
| **Governance (S2)** | [Kivy's about page](https://kivy.org/about.html) lists core developers. We found no published decision process. | [Team page](https://beeware.org/about/team/) lists five current members. The [governance page](https://beeware.org/community/governance/) names Russell Keith-Magee as final decision-maker. |
| **Funding (S3)** | [Kivy Open Collective](https://opencollective.com/kivy): balance $32,103.51, yearly budget $2,937, total received $41,280.32. This covers all Kivy projects. Paid maintenance: **Unknown**. | [Memberships](https://beeware.org/membership/) from $200 a month, with Anaconda listed as a Gold member, and [GitHub Sponsors through freakboy3742](https://github.com/beeware/.github/blob/4e0b8b4799273367f7013d273b9f02b201eb5840/FUNDING.yml). Amounts and paid maintenance: **Unknown**. |
| **First-party dependents (S4)** | [Plyer](https://github.com/kivy/plyer/blob/4853b3a92a786237af966b86d07fa8242eee9aec/setup.py) declares it for iOS and macOS. [kivy-ios](https://github.com/kivy/kivy-ios/blob/fd363d49eddb5ac06766348738bd89c7d46007f8/kivy_ios/recipes/pyobjus/__init__.py) has a recipe. Kivy's `setup.py` and `pyproject.toml` at [`9f31209`](https://github.com/kivy/kivy/tree/9f31209822494bbd3e7eafacad29534661870054) don't declare it, though two core modules use it. | [Toga's Cocoa](https://github.com/beeware/toga/blob/dd833f156e13d15ed26720ef50b8e544046619c5/cocoa/pyproject.toml) and [iOS](https://github.com/beeware/toga/blob/dd833f156e13d15ed26720ef50b8e544046619c5/iOS/pyproject.toml) backends declare `rubicon-objc >= 0.5.1, < 0.6.0`. |
| **Policies (S5)** | No contributing, conduct, security or support file in the repository. [kivy/kivy](https://github.com/kivy/kivy/tree/9f31209822494bbd3e7eafacad29534661870054) has contributing and conduct files. | Contributing and conduct files in the repository. [BeeWare's `.github` repository](https://github.com/beeware/.github/tree/4e0b8b4799273367f7013d273b9f02b201eb5840) adds security, support and AI policies. |
| **License (S6)** | [MIT](https://github.com/kivy/pyobjus/blob/0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81/LICENSE). | [BSD-3-Clause](https://github.com/beeware/rubicon-objc/blob/6bf06390f720226da3d51477f38de3ff1e680eaf/LICENSE), per `pyproject.toml`. |

Web pages were read on 2026-11-03 and may change. "We found no" means the pages listed here were checked, and doesn't prove a document doesn't exist.

### Adoption signals (U1, U2)

Downloads from 2026-05-07 to 2026-11-02, from [pypistats.org](https://pypistats.org), excluding known mirrors:

{{downloads}}

These counts include CI runs and installs pulled in as dependencies, and apps bundled for iOS aren't re-downloaded when users install them.

**Named production use (U2):**
- **Reported:** [akshayaurora](https://github.com/kivy/kivy/issues/9469#issuecomment-6517712158) says shipped Kivy iOS and macOS apps use pyobjus for Core Bluetooth, Bonjour, GPS, pickers and notifications, and [says](https://github.com/kivy/kivy/issues/9469#issuecomment-6540219422) at least 20 people and companies use these projects in mission-critical work. No users are named.
- **Reported:** [kengoon](https://github.com/kivy/kivy/issues/9469#issuecomment-6540733322) says they have used both libraries with Kivy. Their [pyobjus-firebase](https://github.com/PySimpleObjC/pyobjus-firebase) and [pyios-firebase](https://github.com/PySimpleObjC/pyios-firebase) repositories are public.
- **Source:** Toga depends on Rubicon, as shown in S4. Its downstream users are covered in Section 7.

Corrections or named uses of either library are welcome, with a source.
