"""K1 and claim 15: the CI of the main downstream project that builds each
library for iOS. Section 7 covers dependents in full.

Usage: downstream_ci.py OUT.json

kivy-ios is pyobjus's documented iOS route, and its Kivy recipe depends on
pyobjus. Toga's iOS backend depends on Rubicon. For each, at its last
default-branch commit before the baseline, this saves the workflow's CI run,
the result and steps of the job that builds for iOS, the job log's lines that
name the library or report the simulator check, and the push runs of that
workflow in the 12 months before the baseline.
"""
import json
import re
import subprocess
import sys

BASELINE = "2026-11-04T14:10:39Z"
START = "2025-11-04T14:10:39Z"
PROJECTS = {
    "kivy-ios": {"repo": "kivy/kivy-ios", "branch": "master", "workflow": "kivy_ios.yml",
                 "job": "build_python3_kivy (macos-latest)", "library": "pyobjus",
                 "log_pattern": r"\[INFO.*pyobjus|passed on|Startup smoke"},
    "toga": {"repo": "beeware/toga", "branch": "main", "workflow": "ci.yml",
             "job": "Testbed (iOS)", "library": "rubicon",
             "log_pattern": r"rubicon_objc-|=+ .*(passed|failed).* in |simulator"},
}


def gh(*args):
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=True).stdout


def main():
    result = {"window": [START, BASELINE], "projects": {}}
    for name, cfg in PROJECTS.items():
        repo = cfg["repo"]
        commit = json.loads(gh(f"repos/{repo}/commits?sha={cfg['branch']}&until={BASELINE}&per_page=1"))[0]
        sha = commit["sha"]
        runs = json.loads(gh(f"repos/{repo}/actions/workflows/{cfg['workflow']}/runs?head_sha={sha}"))
        run = [r for r in runs["workflow_runs"] if r["event"] == "push"][0]
        jobs = json.loads(gh(f"repos/{repo}/actions/runs/{run['id']}/jobs?per_page=100"))["jobs"]
        job = [j for j in jobs if j["name"].startswith(cfg["job"])][0]
        log = subprocess.run(["gh", "api", "--allow-escape-sequences", f"repos/{repo}/actions/jobs/{job['id']}/logs"],
                             capture_output=True, text=True).stdout
        log = re.sub(r"\x1b\[[0-9;]*m", "", log)
        lines = [line[29:].strip() for line in log.splitlines()
                 if re.search(cfg["log_pattern"], line, re.I)][:200]
        history = gh("--paginate", f"repos/{repo}/actions/workflows/{cfg['workflow']}/runs?branch={cfg['branch']}"
                     f"&event=push&per_page=100&created={START[:10]}..{BASELINE[:10]}",
                     "--jq", ".workflow_runs[] | [.created_at, .conclusion] | @tsv").splitlines()
        history = [h.split("\t") for h in history if START <= h.split("\t")[0] <= BASELINE]
        conclusions = {}
        for _, c in history:
            conclusions[c] = conclusions.get(c, 0) + 1
        result["projects"][name] = {
            "repo": repo, "commit": sha, "commit_date": commit["commit"]["committer"]["date"],
            "run": run["html_url"], "run_conclusion": run["conclusion"],
            "job": job["name"], "job_conclusion": job["conclusion"],
            "steps": [(s["name"], s["conclusion"]) for s in job["steps"]],
            "log_lines": lines,
            "push_runs_in_window": len(history), "push_run_conclusions": conclusions,
            "first_push_run_in_window": min((h[0] for h in history), default=None),
        }
        print(name, json.dumps({k: v for k, v in result["projects"][name].items() if k != "log_lines"}), flush=True)
    json.dump(result, open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
