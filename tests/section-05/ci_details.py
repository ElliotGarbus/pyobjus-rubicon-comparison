"""K2: which jobs failed in each failed run, and which cancelled runs were
superseded.

Usage: ci_details.py CI_HISTORY.json OUT.json

Reads the runs ci_history.py saved. For each failed run, the failed jobs come
from the GitHub API. A cancelled run counts as superseded if another push to
the branch started a run before the cancelled run ended.
"""
import json
import subprocess
import sys


def failed_jobs(repo, run_id):
    out = subprocess.run(
        ["gh", "api", "--paginate", f"repos/{repo}/actions/runs/{run_id}/jobs?filter=all&per_page=100",
         "--jq", '.jobs[] | select(.conclusion == "failure") | .name'],
        capture_output=True, text=True, check=True).stdout
    return out.splitlines()


def main():
    history = json.load(open(sys.argv[1]))
    result = {}
    for name, project in history["projects"].items():
        runs = project["runs"]
        failures = [{"created_at": r["created_at"], "head_sha": r["head_sha"], "html_url": r["html_url"],
                     "failed_jobs": failed_jobs(project["repo"], r["id"])}
                    for r in runs if r["conclusion"] == "failure"]
        cancelled = [r for r in runs if r["conclusion"] == "cancelled"]
        not_superseded = [r["html_url"] for r in cancelled
                          if not any(r["created_at"] < o["created_at"] <= r["updated_at"] for o in runs)]
        result[name] = {"failures": failures, "cancelled": len(cancelled),
                        "superseded": len(cancelled) - len(not_superseded),
                        "cancelled_not_superseded": not_superseded}
        print(name, json.dumps(result[name], indent=1), flush=True)
    json.dump(result, open(sys.argv[2], "w"), indent=1)


if __name__ == "__main__":
    main()
