"""K2: workflow runs triggered by pushes to each default branch.

Usage: ci_history.py OUT.json

Reads the runs GitHub recorded, through the gh CLI, for the 12 months before
the baseline. Nothing is rerun. Saves each run's workflow, commit, dates and
conclusion, then the per-workflow counts.
"""
import collections
import json
import subprocess
import sys

BASELINE = "2026-11-04T14:10:39Z"
START = "2025-11-04T14:10:39Z"
REPOS = {"pyobjus": ("kivy/pyobjus", "master", "0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81"),
         "rubicon": ("beeware/rubicon-objc", "main", "6bf06390f720226da3d51477f38de3ff1e680eaf")}
FIELDS = ("id", "name", "path", "event", "head_branch", "head_sha", "status", "conclusion",
          "created_at", "updated_at", "run_attempt", "html_url")


def runs(repo, branch):
    out = subprocess.run(
        ["gh", "api", "--paginate",
         f"repos/{repo}/actions/runs?branch={branch}&event=push&per_page=100"
         f"&created={START[:10]}..{BASELINE[:10]}",
         "--jq", ".workflow_runs[]"],
        capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        run = json.loads(line)
        if START <= run["created_at"] <= BASELINE:
            yield {k: run[k] for k in FIELDS}


def main():
    result = {"window": [START, BASELINE], "projects": {}}
    for name, (repo, branch, baseline_sha) in REPOS.items():
        all_runs = sorted(runs(repo, branch), key=lambda r: r["created_at"])
        counts = collections.defaultdict(collections.Counter)
        for run in all_runs:
            counts[run["path"]][run["conclusion"] or run["status"]] += 1
        at_baseline = [{k: r[k] for k in ("path", "conclusion", "html_url")}
                       for r in all_runs if r["head_sha"] == baseline_sha]
        result["projects"][name] = {"repo": repo, "branch": branch, "counts": counts,
                                    "baseline_commit_runs": at_baseline, "runs": all_runs}
        print(name, len(all_runs), dict(counts), at_baseline, flush=True)
    json.dump(result, open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
