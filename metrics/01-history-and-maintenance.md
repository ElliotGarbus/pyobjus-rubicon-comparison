# Section 1 metric definitions

**Status: approved 2026-11-03, including the changes recorded below.** These definitions were written before the Section 1 data was collected. Changes made after that are recorded at the end of this document with their reasons.

## What was seen before these were written

A feasibility check confirmed that the data sources work. It wasn't an analysis, but it did expose these figures, and they shaped the rules below:

| Observation (2026-11-03) | pyobjus | Rubicon ObjC | Effect on the rules |
|---|---|---|---|
| Merge commits in the last 24 months | 30 of 86 | 7 of 374 | Merged PRs are the primary unit of activity |
| Commits on the default branch with no linked GitHub account | 171 of 510 | 76 of 2,232 | Identity needs a reviewed fallback |
| Commits by GitHub bot accounts | 23 of 510 | 471 of 2,232 | Bots are excluded and reported separately |
| PyPI versions (versions with no files) | 6 (0) | 37 (1) | Only versions with files are counted |

No metric below has been calculated yet.

## Scope and common rules

- **Repositories:** `kivy/pyobjus` (`master`) and `beeware/rubicon-objc` (`main`) only. Work elsewhere in either organization isn't counted.
- **Snapshot:** one UTC time, *T*, set when collection starts and used for both projects. The commit at *T* is recorded for each, and the raw responses are saved under `results/section-01/`, so results can be recalculated from the same data.
- **Time windows:** calendar years from each project's first commit, plus the 12 and 24 months before *T*. A partial year is labeled as partial.
- **Dates:** commits use committer date, pull requests use merge date, and PyPI releases use the earliest file upload time for that version. All are in UTC.
- **Bots:** an account counts as a bot if GitHub marks it as one, or if it appears on the published list in `results/section-01/bots.csv`. That list starts with `renovate[bot]`, `dependabot[bot]`, `github-actions[bot]` and `Brutus (robot)`. Bot activity is reported separately and never counted as human activity.
- **People:** identity is the GitHub login. Commits with no linked account fall back to the author name, and matches are recorded by hand in `results/section-01/aliases.csv`. Names that can't be matched stay separate. No email addresses are published.
- **Co-author trailers:** these aren't counted, so a commit belongs to its author. AI tools named in trailers aren't contributors, and AI assistance isn't measured.
- **Maintainer:** a commenter or reviewer whose GitHub association on that comment or review is `OWNER`, `MEMBER` or `COLLABORATOR`. This is the association GitHub reports at collection, and it can't show who was a maintainer in the past.
- **Small samples:** every percentage and median is shown with its count, *n*. Percentages aren't reported when *n* is below 10; the counts are shown instead.
- **No scoring:** metrics are never combined or weighted, and no thresholds define labels such as "active" or "abandoned".

## H. History

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| H1 | Origin | First commit date, repository creation date and original authors | Git, GitHub API | Measured |
| H2 | Timeline | Dated events such as transfers, renames, major releases and platform support, each with a link. Only documented events are included | Changelogs, release notes, repository history | Source |

## R. Releases

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| R1 | Release count | PyPI versions with at least one file, per calendar year. Stable, pre-release and yanked versions are counted separately | PyPI JSON | Measured |
| R2 | Latest release | Version, date and age at *T* of the latest stable release | PyPI JSON | Measured |
| R3 | Release gaps | Longest and median gap between stable releases, all time and over the last five years, plus the current gap at *T* | PyPI JSON | Measured |
| R4 | Unreleased work | Human PRs merged to the default branch since the latest stable release | GitHub API, PyPI JSON | Measured |
| R5 | Python support lag | For each CPython 3.10 to 3.15 final release, the days until each of: (a) a macOS arm64 install without compiling; (b) the version first appears in the default branch's CI; (c) a PyPI release declares it in classifiers | python.org, PyPI JSON, workflow history | Measured |
| R6 | iOS availability | Date of the first PyPI artifact installable on iOS, for each Python version that has official iOS support | PyPI JSON | Measured |

**Limits of R5 and R6:** a `py3-none-any` wheel installs on any Python version, so install availability alone doesn't show that it works. That's why (b) and (c) are reported beside (a). Wheels hosted outside PyPI, including kivy-mobile-wheels, are listed separately and aren't counted as PyPI availability.

## A. Activity

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| A1 | Merged PRs (primary) | Human-authored PRs merged to the default branch, per window. Bot PRs are shown separately | GitHub API | Measured |
| A2 | Commits (secondary) | Human non-merge commits on the default branch, per window | Git | Measured |
| A3 | Active months | Months with at least one human non-merge commit, per calendar year | Git | Measured |
| A4 | Commit gaps | Longest gap between human commits, all time and over the last five years, plus the current gap at *T* | Git | Measured |

**Limits:** A1 undercounts the years before a project used PRs, so that period is marked wherever it can be identified. A2 depends on how each project merges work, so it shouldn't be compared directly between projects without A1 beside it.

## C. Contributors

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| C1 | Active contributors | Distinct human authors of merged PRs or non-merge commits, per window | GitHub API, Git | Measured |
| C2 | Concentration | Share of merged human PRs and of human commits from the top one and top two people, and the fewest people who account for at least 50%, for all time and the 12 and 24 months before *T* | GitHub API, Git | Measured |
| C3 | Engagement | Each project's five most active people over the last 24 months, ranked by months active, with first and latest activity, years active, PRs authored and PRs merged. Activity means writing a non-merge commit or merging a PR | GitHub API, Git | Measured |
| C4 | Merge and review | Distinct people who merged PRs, and the share of merged human PRs merged by someone other than the author and with a non-author human review, over the last 12 and 24 months | GitHub API | Measured |
| C5 | New contributors | People whose first merged PR or commit falls in each calendar year | GitHub API, Git | Measured |

Contributors are named by GitHub handle. The author's own contribution to pyobjus is called out wherever it affects a figure.

## I. Issues and pull requests

Issues and PRs are always reported separately, and bot-authored items are excluded.

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| I1 | Open backlog | Open items at *T*, by age: under 1 year, 1 to 3, 3 to 5, and over 5 years | GitHub API | Measured |
| I2 | Opened and closed | Items opened and closed per calendar year. Closures are split by whether a human or automation closed them, and by close reason where GitHub records one | GitHub API | Measured |
| I3 | First maintainer response | For items opened by non-maintainers from 24 months before *T* until 30 days before *T*: the share with a comment or review from a maintainer other than the author within 7 and 30 days | GitHub API | Measured |
| I4 | Resolution | For items opened from 24 months before *T* until 90 days before *T*: the share closed within 90 days, and for PRs the share merged within 90 days. Median time to merge is shown for merged PRs only, and labeled as such | GitHub API | Measured |
| I5 | Long-open items closed | Items closed in the last 24 months that had been open for at least 5 years, shown with and without closures linked to the author's PRs | GitHub API | Measured |

**Limits:**
- These metrics show responsiveness on GitHub Issues and PRs only. Support on Discord, and on GitHub Discussions (enabled for Rubicon, not pyobjus), isn't counted.
- pyobjus runs a workflow that auto-closes issues labeled `awaiting-reply` after 42 days, which is why I2 separates automated closures.
- Fast closure doesn't mean a problem was fixed, and an open item doesn't mean a problem is still present.

## S. Sustainability factors

**Removed from Section 1 on 2026-11-03, except the last five releases in S1.** S4 moves to Section 7. See the changes table at the end of this document. The original definitions are kept here for reference.

These are descriptive facts with links, and they aren't scored.

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| S1 | Release access | Accounts listed as owners or maintainers on PyPI, and the distinct people or automation behind the last five releases | PyPI JSON, Git tags, release workflows | Measured; Unknown where not public |
| S2 | Governance | Publicly documented maintainers, roles and decision process, at repository or organization level | Project docs | Source |
| S3 | Funding | Publicly documented funding routes, sponsors and paid roles | `FUNDING.yml`, Open Collective, project sites | Source |
| S4 | First-party dependents | Projects in the same organization that declare the library as a dependency | Their packaging metadata, pinned | Source |
| S5 | Project policies | Whether contributing, conduct, security and support documents exist at repository or organization level. Existence only, not quality | Repositories, project sites | Source |
| S6 | License | License of each project at *T* | License file, pinned | Source |

GitHub's license field returns `NOASSERTION` for Rubicon ObjC, so S6 reads the license file directly.

## U. Adoption signals

These are context only, and they don't measure how many apps use either library.

| ID | Metric | Definition | Source | Label |
|---|---|---|---|---|
| U1 | PyPI downloads | Downloads over the 180 days before *T*, excluding mirrors and split by operating system | pypistats.org | Measured |
| U2 | Production use | Named uses, each with a link. Unnamed statements are recorded as such | Public statements | Reported |

**Limits of U1:** counts include CI runs and installs pulled in as dependencies, and an app bundled for iOS isn't re-downloaded when users install it. Builds through kivy-ios don't download pyobjus from PyPI, so they aren't counted. pypistats keeps about 180 days of data, so a long-term trend isn't available from this source. U1 shouldn't be read as a count of users or apps. Downstream dependents are covered in Section 7.

## Deliberately excluded

| Measure | Why |
|---|---|
| Stars, forks and watchers | They reflect visibility and project age more than maintenance |
| Lines of code changed | They vary with formatting, generated files and vendored code |
| Composite health scores | The weighting would be a judgment presented as a measurement |
| "Active" or "abandoned" labels | The thread disputes what these mean, so the section reports the data behind them instead |

## Claims this section reports on

Claims 1 to 5 and the release half of claim 16 in [CLAIMS.md](../CLAIMS.md). Section 1 reports the data relevant to each, and leaves conclusions about them to readers and to the later recommendation.

## Changes after approval

Approved 2026-11-03. These changes were made during collection and analysis.

| Metric | Change | Reason |
|---|---|---|
| S1 to S6 | **Approved 2026-11-03.** Removed from Section 1, except the last five releases from S1, which moved to the merging section as evidence for finding 2. First-party dependents (S4) move to Section 7. PyPI owners, release mechanism, governance, funding, policies and license are no longer reported. | The author's judgment that these facts don't help the decision. This was changed after seeing the results. |
| I3 | **Approved 2026-11-03.** A maintainer is now also anyone who has merged a PR in that project. Results using association alone are shown beside the new results. | Association alone misclassified people. `kattni`, on BeeWare's team page with 99 merges, was reported as a `CONTRIBUTOR`, likely because of private organization membership (**Inferred**). The collecting account belongs to the Kivy organization but not BeeWare, which could treat the two projects differently. |
| C3 | **Approved 2026-11-03.** Replaced the results without each project's top contributor with the engagement table above, for both projects. The original results stay in `derived/metrics.json` as `C3_without_top_contributor_superseded`. | The original metric treated a founder with 12 years of steady work the same as someone who started in July 2026, so it could mislead about engagement. This was changed after seeing the results, at the author's request, and the new table also favors Rubicon. Reliance on individuals remains visible in C2 and C4. |
| I3 | Added a check with ElliotGarbus removed as a responder. | The author's role. The result didn't change. |
| I5 | **Approved 2026-11-03.** The table no longer has a column for links to ElliotGarbus's PRs, or the counts with and without them. It now has a Resolution column for both projects, read by hand from each issue's closing comments and linked PRs and recorded in `long_open_resolutions.csv`. | "Closed by" alone made closing an issue look like fixing it. Two of the five pyobjus issues were fixed by earlier work from others, and one of Elliot's fixes was merged by kuzeyron rather than AndreMiras. |
| I5 | Added whether ElliotGarbus closed the issue directly. | Three of the five pyobjus issues were closed by Elliot with no linked PR recorded, so the approved split alone would understate Elliot's involvement. |
| Raw data | Commit records keep only the fields used by the analysis. Email fields and free-text project descriptions are removed from PyPI records. | The approved rule that no email addresses are published. |
| Bots | Added `brutusthebee`, its commit names `Brutus the Bee` and `Brutus (robot)`, and GitHub's short bot names. | Hand review. The account's profile says it performs bot activities for BeeWare. |
| Default branch | Rubicon PRs merged to `master` count as default-branch merges. | The branch was later renamed to `main`, and 127 merged PRs keep the old name. |
| R5, R6 | When a compatible wheel already existed at a Python final release, the result is "already installable", with the version available at that time. | Rubicon's universal wheels date from 2014, so day counts from the first compatible wheel wouldn't mean anything. |
| R6 | Official iOS support starts at Python 3.13, based on PEP 730. | The definition didn't name a starting version. |
| R6 | **Approved 2026-11-03.** R6 is now one row in a table of routes to iOS: kivy-ios, KivyForge, Briefcase and PyPI wheels. The other rows are Source or Reported, not Measured. | PyPI wheels aren't how pyobjus has mainly reached iOS. kivy-ios compiles it from source on Python 3.11.6, so PyPI wheel dates alone made pyobjus look unavailable when it wasn't. Pointed out by the author during review. |
| R4, R5 | **Approved 2026-11-03.** No calculation changed. The text now says that R4 describes PyPI users and that R5(a) covers macOS only. | Same reason: kivy-ios builds from `master`, and the R5(a) figures don't apply to iOS. |
| R3, A4 | "Last five years" means gaps that end in those five years. | The definition didn't specify how to treat a gap crossing the boundary. |
| S1 | Release actors come from GitHub release authors, tag commits and workflow runs. | Tags are lightweight, with no tagger, and GitHub no longer has workflow records for older pyobjus releases. |
| U1 | No calculation changed. The limits now say that pyobjus builds through kivy-ios aren't counted. | The kivy-ios recipe downloads pyobjus from GitHub, so PyPI counts miss this route. The author pointed this out after seeing the results. |
