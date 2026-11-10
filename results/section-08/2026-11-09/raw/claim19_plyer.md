# Claim 19: Plyer's releases and open pull requests

**Measured.** Read from PyPI's JSON API and GitHub's pull request API (`gh api`, all pages) by [`plyer_activity.py`](../../../../tests/section-08/plyer_activity.py), into `claim19_plyer.json`. Collection time: 2026-11-10 00:48 UTC, which was still 9 November locally. Ages are counted from that time.

**The claim**, made [on 30 October 2026](https://github.com/kivy/kivy/issues/9469#issuecomment-6530717668): Plyer's last release was 2.1.0 in November 2022, and it has 69 open PRs, most more than five years old.

## Results

| | Measured |
|---|---|
| Latest release on PyPI | 2.1.0, first uploaded 12 November 2022. The release before it was 2.0.0, on 9 November 2020 |
| Open pull requests | 70. None are drafts |
| Opened more than five years ago | 54 of 70 |
| Opened more than ten years ago | 23 of 70 |
| Oldest and newest | Opened 17 March 2014 and 6 November 2026 |
| Since the claim | One PR, #856, was opened on 6 November 2026. No PR was closed between the claim and collection. Not counting #856, there were 69 open PRs on the claim's date, 54 of them more than five years old on that date |

Open PRs by age in whole years:

| Age | <1 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PRs | 5 | 1 | 4 | 2 | 4 | 5 | 3 | 1 | 1 | 21 | 13 | 7 | 3 |

## Status

The claim holds: the release and its date match, the count was 69 on the claim's date, and most of those PRs (54 of 69) were more than five years old.
