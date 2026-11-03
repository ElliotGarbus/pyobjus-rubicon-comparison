# Section 1 snapshot: 2026-11-03 21:53 UTC

- `manifest.json`: snapshot time, collection times and commits used
- `raw/`: data as collected, with email fields and PyPI project descriptions removed, and commit records reduced to the fields used
- `derived/metrics.json`: all calculated metrics

## Recalculate from this snapshot

From the repository root, with `requirements.txt` installed:

```bash
python scripts/section01_analyze.py results/section-01/2026-11-03T215300Z
```

```bash
python scripts/section01_render.py results/section-01/2026-11-03T215300Z
```

`scripts/section01_collect.py` collects a new snapshot. Live data keeps changing, so a new collection won't match these numbers exactly.

Facts labeled **Source** in Section 1 were read directly from the pages and pinned commits linked there on 2026-11-03. Their collection isn't scripted.

## Cross-checks

Each check compares a calculated figure with a separate source. All were run on 2026-11-03.

| Figure | pyobjus | Rubicon ObjC | Independent source | Result |
|---|---|---|---|---|
| Commits on the default branch | 510 | 2,232 | `git rev-list` on a separate clone | Match |
| Non-merge commits by people | 408 | 1,138 | `git log` filtered by author name | Match |
| Non-merge commits by people, last 12 months | 41 | 48 | `git log --since` | Match |
| Merged PRs, including bots | 122 | 684 | GitHub search API | Match |
| Merged PRs by people, last 12 months | 39 | Not checked | GitHub search API | Match |
| Merged PRs by people, last 24 months | 40 | Not checked | GitHub search API | Match |
| Total issues | 72 | 136 | GitHub search API | Match |
| Open issues, including bots | 17 | 18 | GitHub search API | Match |
| Downloads over 180 days | 16,100 | 4,131,347 | pypistats `overall` endpoint | Match |
| Closer of a sampled issue | #15: ElliotGarbus | #137: freakboy3742 | GitHub REST API | Match |

GitHub's rate limit stopped the remaining planned searches, including Rubicon's PR counts by window. Rubicon's all-time figures reconcile: 684 merged PRs, less 438 by bots, gives the 246 by people.

The maintainer flaw in I3 was found during these checks by reading the classified items by hand. See the changes table in the [metric definitions](../../../metrics/01-history-and-maintenance.md).
