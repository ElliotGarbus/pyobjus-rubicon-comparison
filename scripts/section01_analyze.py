#!/usr/bin/env python3
"""Calculate the Section 1 metrics from a saved snapshot.

Usage: section01_analyze.py SNAPSHOT_DIR
  SNAPSHOT_DIR  for example results/section-01/2026-11-03T215300Z

Writes SNAPSHOT_DIR/derived/metrics.json. Metric IDs match
metrics/01-history-and-maintenance.md. Only saved data is read, so the result
is the same each time it is run on the same snapshot.
"""
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

PROJECTS = ["pyobjus", "rubicon-objc"]
AUTHOR_OF_THIS_COMPARISON = "ElliotGarbus"
MAINTAINER = {"OWNER", "MEMBER", "COLLABORATOR"}
# Rubicon's default branch was renamed from master to main, and merged PRs keep
# the name they were merged under.
DEFAULT_BRANCHES = {"pyobjus": {"master"}, "rubicon-objc": {"main", "master"}}
OFFICIAL_IOS_MINORS = [13, 14, 15]
SUPPORT_MINORS = range(10, 16)


def parse(value):
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    date = datetime.fromisoformat(value)
    return date if date.tzinfo else date.replace(tzinfo=timezone.utc)


def years_before(date, years):
    return date.replace(year=date.year - years)


def days(delta):
    return round(delta.total_seconds() / 86400, 1)


def load_json(path):
    return json.loads(path.read_text())


def percent(part, whole):
    """A count and share, leaving out the share when the sample is below 10."""
    result = {"count": part, "n": whole}
    if whole >= 10:
        result["percent"] = round(100 * part / whole, 1)
    return result


class Project:
    def __init__(self, name, raw, snapshot):
        self.name, self.T = name, snapshot
        folder = raw / name
        self.bots = {row["identity"] for row in csv.DictReader(open(raw.parent.parent / "bots.csv"))}
        self.aliases = {row["name_or_login"]: row["login"]
                        for row in csv.DictReader(open(raw.parent.parent / "aliases.csv"))
                        if row["project"] == name}
        self.commits = load_json(folder / "commits.json")
        self.pulls = [p for p in load_json(folder / "pulls.json") if parse(p["createdAt"]) <= snapshot]
        self.issues = [i for i in load_json(folder / "issues.json") if parse(i["createdAt"]) <= snapshot]
        self.pypi = load_json(folder / "pypi.json")
        self.classifiers = {p.stem: load_json(p).get("classifiers") or []
                            for p in (folder / "pypi_versions").glob("*.json")}
        self.ci_history = load_json(folder / "ci_history.json")
        self.stats = load_json(folder / "pypistats_system.json")
        self.w12, self.w24 = years_before(snapshot, 1), years_before(snapshot, 2)

    def is_bot(self, person):
        person = person or {}
        return person.get("__typename") == "Bot" or person.get("login") in self.bots

    def login(self, person):
        login = (person or {}).get("login") or "ghost"
        return self.aliases.get(login, login)

    def commit_person(self, commit):
        identity = commit["author_login"] or commit["author_name"]
        return self.aliases.get(identity, identity)

    def commit_is_bot(self, commit):
        return commit["author_type"] == "Bot" or commit["author_login"] in self.bots \
            or commit["author_name"] in self.bots

    def human_commits(self, without=()):
        return [c for c in self.commits
                if len(c["parents"]) < 2 and not self.commit_is_bot(c)
                and self.commit_person(c) not in without]

    def merged_pulls(self):
        return [p for p in self.pulls
                if p["merged"] and p["baseRefName"] in DEFAULT_BRANCHES[self.name]
                and parse(p["mergedAt"]) <= self.T]

    def human_merged(self, without=()):
        return [p for p in self.merged_pulls()
                if not self.is_bot(p["author"]) and self.login(p["author"]) not in without]

    def human_items(self, items):
        return [i for i in items if not self.is_bot(i["author"])]


def by_year(dates):
    return dict(sorted(Counter(d.year for d in dates).items()))


def in_windows(p, dates):
    return {"all_time": len(dates),
            "last_24_months": sum(d > p.w24 for d in dates),
            "last_12_months": sum(d > p.w12 for d in dates)}


def gaps(dates, T, five_years_ago):
    """Longest gap overall and ending in the last five years, plus the current gap."""
    dates = sorted(dates)
    pairs = list(zip(dates, dates[1:]))
    def longest(items):
        if not items:
            return None
        start, end = max(items, key=lambda pair: pair[1] - pair[0])
        return {"days": days(end - start), "from": start.date().isoformat(), "to": end.date().isoformat()}
    recent = [pair for pair in pairs if pair[1] > five_years_ago]
    return {
        "longest_all_time": longest(pairs),
        "longest_ending_in_last_5_years": longest(recent),
        "median_all_time_days": days(statistics.median(b - a for a, b in pairs)) if pairs else None,
        "median_ending_in_last_5_years_days":
            days(statistics.median(b - a for a, b in recent)) if recent else None,
        "current_gap_days": days(T - dates[-1]) if dates else None,
    }


def release_table(p):
    releases = []
    for version, files in p.pypi["releases"].items():
        if not files:
            continue
        releases.append({
            "version": version,
            "date": parse(min(f["upload_time_iso_8601"] for f in files)),
            "prerelease": Version(version).is_prerelease,
            "yanked": all(f["yanked"] for f in files),
            "files": files,
        })
    return sorted(releases, key=lambda r: r["date"])


def wheel_installs(filename, minor, ios=False):
    """Whether a wheel installs on CPython 3.<minor> on Apple Silicon macOS or iOS, by its tags."""
    if not filename.endswith(".whl"):
        return False
    python_tag, abi_tag, platform_tag = filename[:-4].split("-")[-3:]
    if platform_tag == "any":
        return any(tag in ("py3", f"py3{minor}", f"cp3{minor}") for tag in python_tag.split("."))
    if python_tag != f"cp3{minor}":
        return False
    if ios:
        return platform_tag.startswith("ios_") and platform_tag.endswith("arm64_iphoneos")
    return platform_tag.startswith("macosx_") and ("arm64" in platform_tag or "universal2" in platform_tag)


def installable(releases, minor, ios=False):
    """Stable releases with a wheel that installs on this Python, oldest first."""
    found = []
    for release in releases:
        if release["prerelease"] or release["yanked"]:
            continue
        for file in release["files"]:
            spec = file.get("requires_python")
            if spec and f"3.{minor}.0" not in SpecifierSet(spec):
                continue
            if wheel_installs(file["filename"], minor, ios):
                found.append((release["version"], release["date"], file["filename"]))
                break
    return found


def install_lag(releases, minor, final, ios=False):
    """The first install date after a Python's final release, or the release that already worked."""
    found = installable(releases, minor, ios)
    if not found:
        return None
    before = [item for item in found if item[1] <= final]
    if before:
        return {"already_installable_at_final": True, "version": before[-1][0],
                "date": before[-1][1].date().isoformat(), "file": before[-1][2], "days_after_final": 0}
    return {"already_installable_at_final": False, "version": found[0][0],
            "date": found[0][1].date().isoformat(), "file": found[0][2],
            "days_after_final": days(found[0][1] - final)}


def first_ci(p, minor):
    """First uncommented CI configuration line that selects this Python version."""
    pattern = re.compile(rf"""["'\s:-]3\.{minor}(?:[.\-"'\s,\]]|$)""")
    for hit in p.ci_history:
        code = hit["line"].split("#", 1)[0]
        if hit["minor"] == minor and pattern.search(" " + code):
            return hit
    return None


def support_lag(p, releases, python_dates):
    rows = {}
    for minor in SUPPORT_MINORS:
        final = parse(python_dates[f"3.{minor}.0"])
        row = {"python_final": final.date().isoformat()}
        row["a_install"] = install_lag(releases, minor, final)
        hit = first_ci(p, minor)
        row["b_ci"] = {"date": hit["date"][:10], "sha": hit["sha"], "line": hit["line"],
                       "days_after_final": days(parse(hit["date"]) - final)} if hit else None
        row["c_classifier"] = None
        label = f"Programming Language :: Python :: 3.{minor}"
        for release in releases:
            if not release["prerelease"] and label in p.classifiers.get(release["version"], []):
                row["c_classifier"] = {"version": release["version"],
                                       "date": release["date"].date().isoformat(),
                                       "days_after_final": days(release["date"] - final)}
                break
        rows[f"3.{minor}"] = row
    return rows


def ios_availability(releases, python_dates):
    rows = {}
    for minor in OFFICIAL_IOS_MINORS:
        final = parse(python_dates[f"3.{minor}.0"])
        rows[f"3.{minor}"] = install_lag(releases, minor, final, ios=True)
    return rows


def activity(p, without=()):
    prs = [parse(x["mergedAt"]) for x in p.human_merged(without)]
    commits = [parse(c["committer_date"]) for c in p.human_commits(without)]
    active = defaultdict(set)
    for date in commits:
        active[date.year].add(date.month)
    five = years_before(p.T, 5)
    return {
        "A1_merged_prs": {"windows": in_windows(p, prs), "by_year": by_year(prs)},
        "A2_commits": {"windows": in_windows(p, commits), "by_year": by_year(commits)},
        "A3_active_months": {year: len(active[year]) for year in sorted(active)},
        "A4_commit_gaps": gaps(commits, p.T, five),
        "C1_contributors": contributors(p, without),
    }


def contributors(p, without=()):
    events = [(parse(x["mergedAt"]), p.login(x["author"])) for x in p.human_merged(without)]
    events += [(parse(c["committer_date"]), p.commit_person(c)) for c in p.human_commits(without)]
    per_year = defaultdict(set)
    for date, person in events:
        per_year[date.year].add(person)
    return {
        "all_time": len({person for _, person in events}),
        "last_24_months": len({person for date, person in events if date > p.w24}),
        "last_12_months": len({person for date, person in events if date > p.w12}),
        "by_year": {year: len(per_year[year]) for year in sorted(per_year)},
    }


def concentration(names):
    counts = Counter(names).most_common()
    total = sum(n for _, n in counts)
    if not total:
        return {"n": 0}
    running, fewest = 0, 0
    for _, n in counts:
        running += n
        fewest += 1
        if running * 2 >= total:
            break
    return {"n": total, "people": len(counts), "top": counts[:5],
            "top1_percent": round(100 * counts[0][1] / total, 1),
            "top2_percent": round(100 * sum(n for _, n in counts[:2]) / total, 1),
            "fewest_for_50_percent": fewest}


def concentration_tables(p):
    prs = [(parse(x["mergedAt"]), p.login(x["author"])) for x in p.human_merged()]
    commits = [(parse(c["committer_date"]), p.commit_person(c)) for c in p.human_commits()]
    table = {}
    for label, since in [("all_time", None), ("last_24_months", p.w24), ("last_12_months", p.w12)]:
        keep = lambda rows: [person for date, person in rows if since is None or date > since]
        table[label] = {"merged_prs": concentration(keep(prs)), "commits": concentration(keep(commits))}
    return table


def engagement(p):
    """C3. The five people most active in the last 24 months, by commits written and PRs merged."""
    activity_dates = defaultdict(list)
    for commit in p.human_commits():
        activity_dates[p.commit_person(commit)].append(parse(commit["committer_date"]))
    merged_by = Counter()
    for pull in p.merged_pulls():
        if not p.is_bot(pull["mergedBy"]):
            who = p.login(pull["mergedBy"])
            merged_by[who] += 1
            activity_dates[who].append(parse(pull["mergedAt"]))
    authored = Counter(p.login(x["author"]) for x in p.human_merged())
    rows = []
    for who, dates in activity_dates.items():
        recent = {d.strftime("%Y-%m") for d in dates if d > p.w24}
        if recent:
            rows.append({"person": who, "first_activity": min(dates).date().isoformat(),
                         "latest_activity": max(dates).date().isoformat(),
                         "years_active": len({d.year for d in dates}),
                         "months_active_last_24_months": len(recent),
                         "prs_authored": authored[who], "prs_merged": merged_by[who]})
    rows.sort(key=lambda r: (r["months_active_last_24_months"], r["latest_activity"]), reverse=True)
    window_months = (p.T.year - p.w24.year) * 12 + p.T.month - p.w24.month + 1
    return {"people_active_last_24_months": len(rows), "calendar_months_in_window": window_months,
            "top_five": rows[:5]}


def merge_and_review(p):
    table = {}
    for label, since in [("last_24_months", p.w24), ("last_12_months", p.w12)]:
        prs = [x for x in p.human_merged() if parse(x["mergedAt"]) > since]
        mergers = Counter(p.login(x["mergedBy"]) for x in prs)
        by_other = sum(p.login(x["mergedBy"]) != p.login(x["author"]) for x in prs)
        def reviewed(pull, states=None):
            return any(r["submittedAt"] and not p.is_bot(r["author"])
                       and p.login(r["author"]) != p.login(pull["author"])
                       and (states is None or r["state"] in states)
                       for r in pull["reviews"]["nodes"])
        table[label] = {
            "distinct_mergers": len(mergers), "mergers": mergers.most_common(),
            "merged_by_non_author": percent(by_other, len(prs)),
            "with_non_author_human_review": percent(sum(reviewed(x) for x in prs), len(prs)),
        }
    return table


def new_contributors(p):
    first = {}
    events = [(parse(x["mergedAt"]), p.login(x["author"])) for x in p.human_merged()]
    events += [(parse(c["committer_date"]), p.commit_person(c)) for c in p.human_commits()]
    for date, person in sorted(events):
        first.setdefault(person, date)
    return by_year(list(first.values()))


def backlog(p, items):
    buckets, by_author = Counter(), 0
    for item in p.human_items(items):
        if item["closedAt"] and parse(item["closedAt"]) <= p.T:
            continue
        age = p.T - parse(item["createdAt"])
        years = age.days / 365.25
        buckets["under_1" if years < 1 else "1_to_3" if years < 3 else "3_to_5" if years < 5 else "over_5"] += 1
        by_author += p.login(item["author"]) == AUTHOR_OF_THIS_COMPARISON
    return {"open": sum(buckets.values()), "opened_by_ElliotGarbus": by_author,
            **{k: buckets[k] for k in ("under_1", "1_to_3", "3_to_5", "over_5")}}


def opened_closed(p, items, is_pull):
    opened, closed = Counter(), defaultdict(Counter)
    for item in p.human_items(items):
        opened[parse(item["createdAt"]).year] += 1
        if not item["closedAt"] or parse(item["closedAt"]) > p.T:
            continue
        year = parse(item["closedAt"]).year
        closed[year]["total"] += 1
        if is_pull and item["merged"]:
            closed[year]["merged"] += 1
            continue
        events = item["timelineItems"]["nodes"]
        actor = events[-1]["actor"] if events else None
        kind = "unknown_closer" if actor is None else "automation" if p.is_bot(actor) else "human"
        closed[year][kind] += 1
        reason = (item.get("stateReason") if not is_pull else None)
        if reason:
            closed[year][f"reason_{reason.lower()}"] += 1
    return {"opened": dict(sorted(opened.items())),
            "closed": {year: dict(closed[year]) for year in sorted(closed)}}


def first_response(p, items, is_pull, excluded_responders=(), include_mergers=True):
    """I3. People who have merged a PR count as maintainers unless include_mergers is False.

    GitHub can report a private organization member as a CONTRIBUTOR, depending on
    who is asking, so association alone doesn't treat the two projects alike.
    """
    mergers = {p.login(x["mergedBy"]) for x in p.merged_pulls() if not p.is_bot(x["mergedBy"])} \
        if include_mergers else set()

    def is_maintainer(entry):
        return entry["authorAssociation"] in MAINTAINER or p.login(entry["author"]) in mergers

    start, end = p.w24, p.T - timedelta(days=30)
    population = [i for i in p.human_items(items)
                  if start < parse(i["createdAt"]) <= end and not is_maintainer(i)]
    within7 = within30 = 0
    for item in population:
        created, author = parse(item["createdAt"]), p.login(item["author"])
        times = [parse(c["createdAt"]) for c in item["comments"]["nodes"]
                 if is_maintainer(c) and not p.is_bot(c["author"])
                 and p.login(c["author"]) != author and p.login(c["author"]) not in excluded_responders]
        if is_pull:
            times += [parse(r["submittedAt"]) for r in item["reviews"]["nodes"]
                      if r["submittedAt"] and is_maintainer(r)
                      and not p.is_bot(r["author"]) and p.login(r["author"]) != author
                      and p.login(r["author"]) not in excluded_responders]
        if times:
            wait = min(times) - created
            within7 += wait <= timedelta(days=7)
            within30 += wait <= timedelta(days=30)
    return {"within_7_days": percent(within7, len(population)),
            "within_30_days": percent(within30, len(population))}


def resolution(p, items, is_pull):
    start, end = p.w24, p.T - timedelta(days=90)
    population = [i for i in p.human_items(items) if start < parse(i["createdAt"]) <= end]
    closed = merged = 0
    for item in population:
        created = parse(item["createdAt"])
        if item["closedAt"] and parse(item["closedAt"]) - created <= timedelta(days=90):
            closed += 1
        if is_pull and item["merged"] and parse(item["mergedAt"]) - created <= timedelta(days=90):
            merged += 1
    result = {"closed_within_90_days": percent(closed, len(population))}
    if is_pull:
        result["merged_within_90_days"] = percent(merged, len(population))
        waits = [parse(i["mergedAt"]) - parse(i["createdAt"]) for i in population if i["merged"]]
        result["median_days_to_merge_merged_prs_only"] = {
            "days": days(statistics.median(waits)) if waits else None, "n": len(waits)}
    return result


def linked_to_author(item):
    events = item.get("timelineItems", {}).get("nodes", [])
    closer = (events[-1].get("closer") or {}) if events else {}
    logins = {(closer.get("author") or {}).get("login")}
    if closer.get("__typename") == "Commit":
        logins = {((closer.get("author") or {}).get("user") or {}).get("login")}
    for pull in item.get("closedByPullRequestsReferences", {}).get("nodes", []):
        logins.add((pull.get("author") or {}).get("login"))
    return AUTHOR_OF_THIS_COMPARISON in logins


def long_open_closed(p, items):
    rows = []
    for item in p.human_items(items):
        if not item["closedAt"] or not p.w24 < parse(item["closedAt"]) <= p.T:
            continue
        created, closed = parse(item["createdAt"]), parse(item["closedAt"])
        if created <= years_before(closed, 5):
            events = item["timelineItems"]["nodes"]
            rows.append({
                "number": item["number"], "title": item["title"],
                "opened": created.date().isoformat(), "closed": closed.date().isoformat(),
                "years_open": round((closed - created).days / 365.25, 1),
                "closed_by": p.login(events[-1]["actor"]) if events else None,
                "linked_to_ElliotGarbus": linked_to_author(item),
            })
    return {"total": len(rows),
            "not_linked_to_ElliotGarbus": sum(not r["linked_to_ElliotGarbus"] for r in rows),
            "neither_linked_to_nor_closed_by_ElliotGarbus":
                sum(not r["linked_to_ElliotGarbus"] and r["closed_by"] != AUTHOR_OF_THIS_COMPARISON for r in rows),
            "items": rows}


def analyze(p, python_dates):
    releases = release_table(p)
    stable = [r for r in releases if not r["prerelease"] and not r["yanked"]]
    per_year = defaultdict(Counter)
    for release in releases:
        kind = "yanked" if release["yanked"] else "prerelease" if release["prerelease"] else "stable"
        per_year[release["date"].year][kind] += 1
    latest = stable[-1]
    human_prs = p.human_merged()
    since = [x for x in human_prs if parse(x["mergedAt"]) > latest["date"]]
    bot_merged = [parse(x["mergedAt"]) for x in p.merged_pulls() if p.is_bot(x["author"])]
    bot_commits = [parse(c["committer_date"]) for c in p.commits if len(c["parents"]) < 2 and p.commit_is_bot(c)]
    first_commit = min(p.commits, key=lambda c: parse(c["committer_date"]))
    first_pr = min((parse(x["mergedAt"]) for x in human_prs), default=None)

    last24 = [p.login(x["author"]) for x in human_prs if parse(x["mergedAt"]) > p.w24]
    commits24 = [p.commit_person(c) for c in p.human_commits() if parse(c["committer_date"]) > p.w24]
    pr_counts, commit_counts = Counter(last24), Counter(commits24)
    top = max(pr_counts or commit_counts, key=lambda who: (pr_counts[who], commit_counts[who]))
    sensitivity = {f"without_top_contributor:{top}": activity(p, without={top})}
    if p.name == "pyobjus" and top != AUTHOR_OF_THIS_COMPARISON:
        sensitivity[f"without:{AUTHOR_OF_THIS_COMPARISON}"] = activity(p, without={AUTHOR_OF_THIS_COMPARISON})

    downloads = defaultdict(int)
    window_start = (p.T - timedelta(days=180)).date().isoformat()
    dates = []
    for row in p.stats["data"]:
        if row["date"] >= window_start and row["date"] <= p.T.date().isoformat():
            downloads[row["category"]] += row["downloads"]
            dates.append(row["date"])

    tagged = [r["version"] for r in stable[-5:]]
    return {
        "H1": {"first_commit": first_commit["committer_date"],
               "first_commit_author": p.commit_person(first_commit),
               "first_commit_subject": first_commit["subject"],
               "first_merged_human_pr": first_pr.date().isoformat() if first_pr else None},
        "R1": {year: dict(per_year[year]) for year in sorted(per_year)},
        "R2": {"version": latest["version"], "date": latest["date"].date().isoformat(),
               "age_days": days(p.T - latest["date"])},
        "R3": gaps([r["date"] for r in stable], p.T, years_before(p.T, 5)),
        "R3_stable_count": len(stable),
        "R4": {"since_version": latest["version"], "human_prs_merged_since": len(since),
               "by_author": Counter(p.login(x["author"]) for x in since).most_common()},
        "R5": support_lag(p, releases, python_dates),
        "R6": ios_availability(releases, python_dates),
        **activity(p),
        "bot_activity": {"merged_prs": in_windows(p, bot_merged), "commits": in_windows(p, bot_commits)},
        "C2": concentration_tables(p),
        "C3": engagement(p),
        "C3_without_top_contributor_superseded": sensitivity,
        "C4": merge_and_review(p),
        "C5": new_contributors(p),
        "I1": {"issues": backlog(p, p.issues), "prs": backlog(p, p.pulls)},
        "I2": {"issues": opened_closed(p, p.issues, False), "prs": opened_closed(p, p.pulls, True)},
        "I3": {"issues": first_response(p, p.issues, False), "prs": first_response(p, p.pulls, True)},
        "I3_association_only": {
            "issues": first_response(p, p.issues, False, include_mergers=False),
            "prs": first_response(p, p.pulls, True, include_mergers=False)},
        "I3_without_ElliotGarbus_as_responder": {
            "issues": first_response(p, p.issues, False, {AUTHOR_OF_THIS_COMPARISON}),
            "prs": first_response(p, p.pulls, True, {AUTHOR_OF_THIS_COMPARISON})},
        "I4": {"issues": resolution(p, p.issues, False), "prs": resolution(p, p.pulls, True)},
        "I5": {"issues": long_open_closed(p, p.issues), "prs": long_open_closed(p, p.pulls)},
        "S1": {"pypi_ownership": p.pypi["ownership"], "last_five_stable": tagged},
        "U1": {"window_start": window_start, "first_date_in_data": min(dates), "last_date_in_data": max(dates),
               "by_os": dict(sorted(downloads.items())), "total": sum(downloads.values())},
    }


def main():
    folder = Path(sys.argv[1]).resolve()
    manifest = load_json(folder / "manifest.json")
    snapshot = parse(manifest["snapshot_T"])
    python_dates = load_json(folder / "raw" / "python_releases.json")
    results = {"snapshot_T": manifest["snapshot_T"], "repositories": manifest["repositories"]}
    for name in PROJECTS:
        results[name] = analyze(Project(name, folder / "raw", snapshot), python_dates)
    out = folder / "derived" / "metrics.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=1, default=str) + "\n")
    print(out)


if __name__ == "__main__":
    main()
