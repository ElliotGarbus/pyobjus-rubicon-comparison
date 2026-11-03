#!/usr/bin/env python3
"""Build sections/01-history-and-maintenance.md from the template and metrics.

Usage: section01_render.py SNAPSHOT_DIR

Every {{token}} in scripts/section01_template.md is replaced by a table
generated from SNAPSHOT_DIR/derived/metrics.json, so the tables can't drift
from the calculated values.
"""
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY, RB = "pyobjus", "rubicon-objc"


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def whole(value):
    return "n/a" if value is None else f"{round(value):,}"


def share(item):
    if item["n"] == 0:
        return "No items"
    if "percent" in item:
        return f"{item['percent']:.0f}% ({item['count']} of {item['n']})"
    return f"{item['count']} of {item['n']}"


def gap(item):
    return f"{whole(item['days'])} days ({item['from']} to {item['to']})" if item else "n/a"


def year_range(*maps):
    years = sorted({int(year) for mapping in maps for year in mapping})
    return range(years[0], years[-1] + 1)


def lookup(mapping, year):
    return mapping.get(str(year), 0)


def build(m):
    p, r = m[PY], m[RB]
    tokens = {}

    tokens["snapshot"] = table(
        ["", "pyobjus", "Rubicon ObjC"],
        [["Repository", "`kivy/pyobjus`", "`beeware/rubicon-objc`"],
         ["Commit at snapshot",
          f"[`{m['repositories'][PY]['commit_at_T'][:10]}`](https://github.com/kivy/pyobjus/commit/{m['repositories'][PY]['commit_at_T']})",
          f"[`{m['repositories'][RB]['commit_at_T'][:10]}`](https://github.com/beeware/rubicon-objc/commit/{m['repositories'][RB]['commit_at_T']})"],
         ["First commit", p["H1"]["first_commit"][:10], r["H1"]["first_commit"][:10]],
         ["First merged PR by a person", p["H1"]["first_merged_human_pr"], r["H1"]["first_merged_human_pr"]]])

    tokens["releases"] = table(
        ["Measure", "pyobjus", "Rubicon ObjC"],
        [["Stable PyPI versions (R1)", p["R3_stable_count"], r["R3_stable_count"]],
         ["Latest stable version (R2)", f"{p['R2']['version']}, {p['R2']['date']}", f"{r['R2']['version']}, {r['R2']['date']}"],
         ["Age of latest stable version at snapshot (R2, R3)", f"{whole(p['R2']['age_days'])} days", f"{whole(r['R2']['age_days'])} days"],
         ["Median gap between stable versions, all time (R3)", f"{whole(p['R3']['median_all_time_days'])} days", f"{whole(r['R3']['median_all_time_days'])} days"],
         ["Median gap, last 5 years (R3)", f"{whole(p['R3']['median_ending_in_last_5_years_days'])} days", f"{whole(r['R3']['median_ending_in_last_5_years_days'])} days"],
         ["Longest gap, all time (R3)", gap(p["R3"]["longest_all_time"]), gap(r["R3"]["longest_all_time"])],
         ["Longest gap, last 5 years (R3)", gap(p["R3"]["longest_ending_in_last_5_years"]), gap(r["R3"]["longest_ending_in_last_5_years"])],
         ["PRs by people merged since latest stable (R4)", p["R4"]["human_prs_merged_since"], r["R4"]["human_prs_merged_since"]]])

    rows = []
    for year in year_range(p["R1"], r["R1"]):
        pr, rr = p["R1"].get(str(year), {}), r["R1"].get(str(year), {})
        other = []
        if rr.get("prerelease"):
            other.append(f"{rr['prerelease']} pre-release")
        if rr.get("yanked"):
            other.append(f"{rr['yanked']} yanked")
        rows.append([year, pr.get("stable", 0), rr.get("stable", 0), ", ".join(other) or "None"])
    tokens["releases_by_year"] = table(["Year", "pyobjus stable", "Rubicon stable", "Other Rubicon versions"], rows)

    def install(cell):
        if not cell:
            return "None on PyPI at snapshot"
        if cell["already_installable_at_final"]:
            return f"Already installable ({cell['version']})"
        return f"{whole(cell['days_after_final'])} days ({cell['version']})"

    def after(cell, none):
        if not cell:
            return none
        lag = cell["days_after_final"]
        return f"{whole(lag)} days" if lag >= 0 else f"{whole(-lag)} days before final"

    rows = []
    for version in p["R5"]:
        a, b = p["R5"][version], r["R5"][version]
        rows.append([version, a["python_final"], install(a["a_install"]), install(b["a_install"]),
                     after(a["b_ci"], "Not in CI at snapshot"), after(b["b_ci"], "Not in CI at snapshot"),
                     after(a["c_classifier"], "Not declared at snapshot"), after(b["c_classifier"], "Not declared at snapshot")])
    tokens["python_support"] = table(
        ["Python", "Final release", "pyobjus install (a)", "Rubicon install (a)", "pyobjus CI (b)",
         "Rubicon CI (b)", "pyobjus classifier (c)", "Rubicon classifier (c)"], rows)

    def wheel_row(project, none):
        cells = []
        for version, cell in project["R6"].items():
            if not cell:
                cells.append(f"{version}: {none}")
            elif cell["already_installable_at_final"]:
                cells.append(f"{version}: already installable ({cell['version']})")
            else:
                cells.append(f"{version}: {whole(cell['days_after_final'])} days after Python's release ({cell['version']})")
        return "; ".join(cells)
    tokens["ios_pypi_row"] = ("| **PyPI wheels (R6)**, for a tool that installs them | 3.13 to 3.15 | "
                              f"{wheel_row(p, 'none at snapshot')}. | "
                              f"{wheel_row(r, 'none at snapshot')}. The wheel is universal, so this doesn't show that iOS works. |")

    rows = []
    for year in year_range(p["A3_active_months"], r["A3_active_months"]):
        rows.append([year,
                     lookup(p["A1_merged_prs"]["by_year"], year), lookup(p["A3_active_months"], year),
                     lookup(p["C1_contributors"]["by_year"], year), lookup(p["C5"], year),
                     lookup(r["A1_merged_prs"]["by_year"], year), lookup(r["A3_active_months"], year),
                     lookup(r["C1_contributors"]["by_year"], year), lookup(r["C5"], year)])
    tokens["activity_by_year"] = table(
        ["Year", "pyobjus PRs", "Active months", "Contributors", "New",
         "Rubicon PRs", "Active months", "Contributors", "New"], rows)

    def windows(name, key, sub=None):
        a = p[key][sub] if sub else p[key]
        b = r[key][sub] if sub else r[key]
        return [[f"{name}, {label}", a[field], b[field]] for label, field in
                [("all time", "all_time"), ("last 24 months", "last_24_months"), ("last 12 months", "last_12_months")]]

    tokens["activity_windows"] = table(
        ["Measure", "pyobjus", "Rubicon ObjC"],
        windows("Merged PRs by people (A1)", "A1_merged_prs", "windows")
        + windows("Commits by people (A2)", "A2_commits", "windows")
        + windows("Contributors (C1)", "C1_contributors")
        + [[f"Bot PRs merged, {label}", p["bot_activity"]["merged_prs"][f], r["bot_activity"]["merged_prs"][f]]
           for label, f in [("all time", "all_time"), ("last 12 months", "last_12_months")]]
        + [["Current gap since a commit by a person (A4)", f"{whole(p['A4_commit_gaps']['current_gap_days'])} days", f"{whole(r['A4_commit_gaps']['current_gap_days'])} days"],
           ["Longest gap, all time (A4)", gap(p["A4_commit_gaps"]["longest_all_time"]), gap(r["A4_commit_gaps"]["longest_all_time"])],
           ["Longest gap, last 5 years (A4)", gap(p["A4_commit_gaps"]["longest_ending_in_last_5_years"]), gap(r["A4_commit_gaps"]["longest_ending_in_last_5_years"])]])

    def top(item):
        return ", ".join(f"{who} ({n})" for who, n in item["top"][:3])

    rows = []
    for label, key in [("All time", "all_time"), ("Last 24 months", "last_24_months"), ("Last 12 months", "last_12_months")]:
        for measure, field in [("merged PRs", "merged_prs"), ("commits", "commits")]:
            a, b = p["C2"][key][field], r["C2"][key][field]
            rows.append([f"{label}, {measure}",
                         f"{a['top1_percent']:.0f}% / {a['top2_percent']:.0f}% / {a['fewest_for_50_percent']}", top(a),
                         f"{b['top1_percent']:.0f}% / {b['top2_percent']:.0f}% / {b['fewest_for_50_percent']}", top(b)])
    tokens["concentration"] = table(
        ["Window and unit", "pyobjus top 1 / top 2 / people for 50%", "pyobjus top three",
         "Rubicon top 1 / top 2 / people for 50%", "Rubicon top three"], rows)

    rows = []
    for name, project in [("pyobjus", p), ("Rubicon ObjC", r)]:
        for row in project["C3"]["top_five"]:
            months = row["months_active_last_24_months"]
            rows.append([name, row["person"], row["first_activity"], row["latest_activity"], row["years_active"],
                         "Every month" if months == project["C3"]["calendar_months_in_window"] else months,
                         row["prs_authored"], row["prs_merged"]])
    tokens["rubicon_active"] = str(r["C3"]["people_active_last_24_months"])
    tokens["engagement"] = table(
        ["Project", "Contributor", "First activity", "Latest activity", "Years active",
         "Months active, last 24 months", "PRs authored", "PRs merged"], rows)

    rows = []
    for label, key in [("Last 24 months", "last_24_months"), ("Last 12 months", "last_12_months")]:
        a, b = p["C4"][key], r["C4"][key]
        names = lambda item: ", ".join(f"{who} ({n})" for who, n in item["mergers"])
        rows += [[f"{label}: people who merged", names(a), names(b)],
                 [f"{label}: merged by someone other than the author", share(a["merged_by_non_author"]), share(b["merged_by_non_author"])],
                 [f"{label}: reviewed by a person other than the author", share(a["with_non_author_human_review"]), share(b["with_non_author_human_review"])]]
    tokens["merge_review"] = table(["Measure", "pyobjus", "Rubicon ObjC"], rows)

    def backlog(item):
        return [item["open"], item["under_1"], item["1_to_3"], item["3_to_5"], item["over_5"], item["opened_by_ElliotGarbus"]]
    tokens["backlog"] = table(
        ["Open at snapshot", "Total", "Under 1 year", "1 to 3 years", "3 to 5 years", "Over 5 years", "Opened by ElliotGarbus"],
        [["pyobjus issues"] + backlog(p["I1"]["issues"]), ["pyobjus PRs"] + backlog(p["I1"]["prs"]),
         ["Rubicon issues"] + backlog(r["I1"]["issues"]), ["Rubicon PRs"] + backlog(r["I1"]["prs"])])

    def flow(project):
        issues, prs = project["I2"]["issues"], project["I2"]["prs"]
        return issues, prs
    pi, pp = flow(p)
    ri, rp = flow(r)
    rows = []
    for year in year_range(pi["opened"], pi["closed"], pp["opened"], ri["opened"], ri["closed"], rp["opened"]):
        def closed(group):
            return group["closed"].get(str(year), {}).get("total", 0)
        rows.append([year, lookup(pi["opened"], year), closed(pi), lookup(pp["opened"], year), closed(pp),
                     lookup(ri["opened"], year), closed(ri), lookup(rp["opened"], year), closed(rp)])
    tokens["flow"] = table(
        ["Year", "pyobjus issues opened", "closed", "pyobjus PRs opened", "closed",
         "Rubicon issues opened", "closed", "Rubicon PRs opened", "closed"], rows)

    def closures(group, is_pull):
        totals = {}
        for year in group["closed"].values():
            for key, value in year.items():
                totals[key] = totals.get(key, 0) + value
        return totals
    a, b = closures(pi, False), closures(ri, False)
    c, d = closures(pp, True), closures(rp, True)
    tokens["closure_types"] = table(
        ["All-time closures", "pyobjus", "Rubicon ObjC"],
        [["Issues closed by a person", a.get("human", 0), b.get("human", 0)],
         ["Issues closed by automation", a.get("automation", 0), b.get("automation", 0)],
         ["Issues closed as completed", a.get("reason_completed", 0), b.get("reason_completed", 0)],
         ["Issues closed as not planned", a.get("reason_not_planned", 0), b.get("reason_not_planned", 0)],
         ["PRs merged", c.get("merged", 0), d.get("merged", 0)],
         ["PRs closed without merging by a person", c.get("human", 0), d.get("human", 0)]])

    def response_table(key):
        return table(
            ["Opened by non-maintainers (I3)", "pyobjus", "Rubicon ObjC"],
            [[f"{label} answered within {window} days",
              share(p[key][kind][f"within_{window}_days"]), share(r[key][kind][f"within_{window}_days"])]
             for label, kind in [("Issues", "issues"), ("PRs", "prs")] for window in (7, 30)])
    tokens["response"] = response_table("I3")
    tokens["response_association_only"] = response_table("I3_association_only")

    tokens["resolution"] = table(
        ["All items by people (I4)", "pyobjus", "Rubicon ObjC"],
        [["Issues closed within 90 days", share(p["I4"]["issues"]["closed_within_90_days"]), share(r["I4"]["issues"]["closed_within_90_days"])],
         ["PRs closed within 90 days", share(p["I4"]["prs"]["closed_within_90_days"]), share(r["I4"]["prs"]["closed_within_90_days"])],
         ["PRs merged within 90 days", share(p["I4"]["prs"]["merged_within_90_days"]), share(r["I4"]["prs"]["merged_within_90_days"])],
         ["Median time to merge, merged PRs only",
          f"{p['I4']['prs']['median_days_to_merge_merged_prs_only']['days']} days (n={p['I4']['prs']['median_days_to_merge_merged_prs_only']['n']})",
          f"{r['I4']['prs']['median_days_to_merge_merged_prs_only']['days']} days (n={r['I4']['prs']['median_days_to_merge_merged_prs_only']['n']})"]])

    with open(ROOT / "results" / "section-01" / "long_open_resolutions.csv", newline="") as source:
        resolutions = {(row["project"], int(row["issue"])): row["resolution"] for row in csv.DictReader(source)}
    rows = []
    for name, key, repo, project in [("pyobjus", PY, "kivy/pyobjus", p), ("Rubicon ObjC", RB, "beeware/rubicon-objc", r)]:
        for item in project["I5"]["issues"]["items"]:
            rows.append([name, f"[#{item['number']}](https://github.com/{repo}/issues/{item['number']}) {item['title']}",
                         item["opened"], item["closed"], item["years_open"], item["closed_by"],
                         resolutions[(key, item["number"])]])
    tokens["long_open"] = table(["Project", "Issue", "Opened", "Closed", "Years open", "Closed by", "Resolution"], rows)

    def os_row(label, key):
        return [label, f"{p['U1']['by_os'].get(key, 0):,}", f"{r['U1']['by_os'].get(key, 0):,}"]
    tokens["downloads"] = table(
        ["Operating system", "pyobjus", "Rubicon ObjC"],
        [os_row("macOS (Darwin)", "Darwin"), os_row("Linux", "Linux"), os_row("Windows", "Windows"),
         os_row("Other", "other"), os_row("Not recorded", "null"),
         ["Total", f"{p['U1']['total']:,}", f"{r['U1']['total']:,}"]])
    return tokens


def main():
    folder = Path(sys.argv[1]).resolve()
    metrics = json.loads((folder / "derived" / "metrics.json").read_text())
    tokens = build(metrics)
    template = (ROOT / "scripts" / "section01_template.md").read_text()
    used = set(re.findall(r"\{\{(\w+)\}\}", template))
    missing, unused = used - set(tokens), set(tokens) - used
    if missing or unused:
        sys.exit(f"Template mismatch. Missing: {sorted(missing)}. Unused: {sorted(unused)}.")
    output = re.sub(r"\{\{(\w+)\}\}", lambda match: tokens[match.group(1)], template)
    (ROOT / "sections" / "01-history-and-maintenance.md").write_text(output)
    print(f"Rendered {len(used)} tables at {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
