"""T4: run Rubicon's own iOS test route on the iOS simulator.

Usage: run_ios_sim.py WORK OUT [RUNS]

WORK holds checkouts named rubicon-0.5.7-ios and rubicon-main-ios. Each run
starts from a clean checkout and a new environment, installs Rubicon's tox-uv
group and runs `tox -e py314-iOS`, which builds the wheel and runs the suite in
Briefcase's testbed app on the simulator. CI runs the same environment with
`-ci`, which takes the wheel from its package job instead of building it.

pyobjus has no iOS test route, so there is nothing to run for it.

Results are read from pytest's verbose output, which the testbed prints.
"""
import json
import os
import re
import subprocess
import sys
import time

PYTHON = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
VERSIONS = ["rubicon-0.5.7-ios", "rubicon-main-ios"]
OUTCOMES = ("PASSED", "FAILED", "SKIPPED", "ERROR", "XFAIL", "XPASS")
SUMMARY = re.compile(r"^=+ (.*(?:passed|failed|error).*) in [\d.]+s", re.M)


def sh(cmd, cwd, log):
    with open(log, "a") as f:
        f.write(f"\n$ {cmd}\n")
        f.flush()
        p = subprocess.run(cmd, shell=True, cwd=cwd, stdout=f, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL)
        f.write(f"[exit {p.returncode}]\n")
    return p.returncode


def outcomes(text):
    """(test, outcome) pairs. The simulator log usually puts a test's outcome
    on a later line than its name, sometimes after the test's own output."""
    current = None
    for line in text.splitlines():
        same_line = re.match(r"^(tests/.+::.+?) +(%s)\b" % "|".join(OUTCOMES), line)
        if same_line:
            yield same_line.group(1), same_line.group(2)
            current = None
        elif re.match(r"^tests/.+::", line):
            current = line.strip()
        elif current and line.startswith(OUTCOMES):
            yield current, line.split()[0]
            current = None


def run(checkout, logdir, n):
    subprocess.run(["git", "clean", "-xfdq"], cwd=checkout, check=True)
    log = os.path.join(logdir, f"run{n}.log")
    venv = os.path.join(checkout, "toolvenv")
    for step in [f"{PYTHON} -m venv toolvenv",
                 f"{venv}/bin/python -m pip install -q -U pip",
                 f"{venv}/bin/python -m pip install -q --group tox-uv"]:
        if sh(step, checkout, log):
            return {"setup_failed": step}
    status = sh(f"{venv}/bin/tox -r -e py314-iOS", checkout, log)
    text = open(log).read()
    counts = {}
    not_passed = []
    for test, outcome in outcomes(text):
        counts[outcome] = counts.get(outcome, 0) + 1
        if outcome not in ("PASSED", "SKIPPED"):
            not_passed.append({"test": test, "outcome": outcome})
    summary = SUMMARY.findall(text)
    direct_url = [os.path.join(root, "direct_url.json")
                  for root, _, files in os.walk(os.path.join(checkout, ".tox", "py314-iOS"))
                  if os.path.basename(root).startswith("briefcase-") and "direct_url.json" in files]
    briefcase = json.load(open(direct_url[0]))["vcs_info"]["commit_id"] if direct_url else None
    return {"exit": status, "counts": counts, "collected": sum(counts.values()),
            "pytest_summary": summary[-1] if summary else None, "not_passed": not_passed,
            "briefcase_commit": briefcase}


def main():
    work, out = sys.argv[1], sys.argv[2]
    runs = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    results = json.load(open(out)) if os.path.exists(out) else {}
    for version in VERSIONS:
        checkout = os.path.join(work, version)
        logdir = os.path.join(os.path.dirname(out), "logs", version)
        os.makedirs(logdir, exist_ok=True)
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True,
                                text=True).stdout.strip()
        entry = {"commit": commit, "runs": []}
        for n in range(1, runs + 1):
            start = time.monotonic()
            r = run(checkout, logdir, n)
            r["seconds"] = round(time.monotonic() - start)
            entry["runs"].append(r)
            print(version, n, {k: v for k, v in r.items() if k != "not_passed"}, flush=True)
        results[version] = entry
        json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
