"""Claim 19: Plyer's PyPI releases, and its open pull requests with their opening dates.

Usage: plyer_activity.py OUT.json

Reads PyPI's JSON API for every release and its first upload time, and
GitHub's open pull requests for kivy/plyer through `gh api` (all pages).
Counts open PRs by age in whole years on the collection date.
"""
import datetime
import json
import subprocess
import sys
import urllib.request


def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    with urllib.request.urlopen("https://pypi.org/pypi/plyer/json", timeout=30) as r:
        d = json.load(r)
    releases = []
    for version, files in d["releases"].items():
        if files:
            releases.append({"version": version, "first_upload": min(f["upload_time_iso_8601"] for f in files),
                             "yanked": all(f.get("yanked") for f in files)})
    releases.sort(key=lambda r: r["first_upload"])
    pages = subprocess.run(["gh", "api", "--paginate", "--slurp", "repos/kivy/plyer/pulls?state=open&per_page=100"],
                           check=True, capture_output=True, text=True).stdout
    prs = [{"number": p["number"], "created_at": p["created_at"], "draft": p["draft"]}
           for page in json.loads(pages) for p in page]
    prs.sort(key=lambda p: p["created_at"])
    by_years = {}
    for p in prs:
        created = datetime.datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
        years = (now - created).days / 365.25
        p["age_years"] = round(years, 2)
        key = f"{int(years)}+" if years >= 1 else "<1"
        by_years[key] = by_years.get(key, 0) + 1
    older_than_5 = sum(1 for p in prs if p["age_years"] > 5)
    out = {"collected_at": now.strftime("%Y-%m-%dT%H:%MZ"),
           "pypi": {"latest": d["info"]["version"], "releases": releases},
           "open_prs": {"count": len(prs), "older_than_5_years": older_than_5,
                        "by_whole_years": dict(sorted(by_years.items())), "prs": prs}}
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    print("latest:", d["info"]["version"], releases[-1]["first_upload"])
    print("open PRs:", len(prs), "older than 5 years:", older_than_5)
    print("by whole years:", out["open_prs"]["by_whole_years"])
    print("oldest:", prs[0]["created_at"], "newest:", prs[-1]["created_at"])


if __name__ == "__main__":
    main()
