"""T1, T3 and T4: run each project's own test suite on the Mac.

Usage: run_mac.py WORK OUT [RUNS]

WORK holds one checkout per version, named pyobjus-1.2.4, pyobjus-master,
rubicon-0.5.7 and rubicon-main. Each run starts from a clean checkout and a new
environment, and uses the test command of the project's own CI:

- pyobjus: install .ci/cicd-requirements.txt and the project, `make test_lib`,
  then `python -m pytest tests -v`, as its unit-test matrix does.
- Rubicon: install its tox-uv group, then `tox -e py314-cov`, as its macOS
  matrix does. tox builds the wheel itself, where CI passes the wheel from its
  package job.

The only addition is `--junitxml`, so results can be counted. After the runs,
coverage is measured once with each project's own setup: pyobjus's coverage
job, where the version has one, and Rubicon's `coverage314` report of the
last run's data.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PYTHON = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
VERSIONS = ["pyobjus-1.2.4", "pyobjus-master", "rubicon-0.5.7", "rubicon-main"]


def sh(cmd, cwd, log, env=None):
    """Run a shell command, appending its output to log. Returns the exit status."""
    with open(log, "a") as f:
        f.write(f"\n$ {cmd}\n")
        f.flush()
        p = subprocess.run(cmd, shell=True, cwd=cwd, stdout=f, stderr=subprocess.STDOUT,
                           env=dict(os.environ, **(env or {})))
        f.write(f"[exit {p.returncode}]\n")
    return p.returncode


def junit(path):
    """Counts and the non-passing tests from a JUnit XML file."""
    if not os.path.exists(path):
        return None
    root = ET.parse(path).getroot()
    counts = {"passed": 0, "failed": 0, "errored": 0, "skipped": 0, "xfailed": 0}
    problems = []
    for case in root.iter("testcase"):
        name = f"{case.get('classname')}::{case.get('name')}"
        kinds = {c.tag: c for c in case}
        if "failure" in kinds:
            counts["failed"] += 1
        elif "error" in kinds:
            counts["errored"] += 1
        elif "skipped" in kinds and kinds["skipped"].get("type") == "pytest.xfail":
            counts["xfailed"] += 1
        elif "skipped" in kinds:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
            continue
        child = case[0]
        problems.append({"test": name, "kind": child.tag,
                         "message": (child.get("message") or "")[:300]})
    counts["collected"] = sum(counts.values())
    return {"counts": counts, "not_passed": problems}


def clean(checkout):
    subprocess.run(["git", "clean", "-xfdq"], cwd=checkout, check=True)


def run_pyobjus(checkout, logdir, n):
    clean(checkout)
    log = os.path.join(logdir, f"run{n}.log")
    xml = os.path.join(logdir, f"run{n}.xml")
    venv = os.path.join(checkout, "venv")
    pip = f"{venv}/bin/python -m pip"
    steps = [f"{PYTHON} -m venv venv",
             f"{pip} install -q -r .ci/cicd-requirements.txt",
             f"{pip} install -q -e .",
             "make test_lib"]
    for step in steps:
        if sh(step, checkout, log):
            return {"setup_failed": step}
    status = sh(f"{venv}/bin/python -m pytest tests -v --junitxml={xml}", checkout, log)
    return {"exit": status, **(junit(xml) or {"no_results": True})}


def run_rubicon(checkout, logdir, n):
    clean(checkout)
    log = os.path.join(logdir, f"run{n}.log")
    xml = os.path.join(logdir, f"run{n}.xml")
    venv = os.path.join(checkout, "toolvenv")
    for step in [f"{PYTHON} -m venv toolvenv",
                 f"{venv}/bin/python -m pip install -q -U pip",
                 f"{venv}/bin/python -m pip install -q --group tox-uv"]:
        if sh(step, checkout, log):
            return {"setup_failed": step}
    status = sh(f"{venv}/bin/tox -r -e py314-cov -- -vv --junitxml={xml}", checkout, log)
    return {"exit": status, **(junit(xml) or {"no_results": True})}


def coverage_pyobjus(checkout, logdir):
    if "PYOBJUS_COVERAGE" not in open(os.path.join(checkout, "setup.py")).read():
        return {"setup": "none"}
    clean(checkout)
    log = os.path.join(logdir, "coverage.log")
    venv = os.path.join(checkout, "venv")
    py = f"{venv}/bin/python"
    env = {"PYOBJUS_COVERAGE": "1"}
    for step in [f"{PYTHON} -m venv venv",
                 f"{py} -m pip install -q -r .ci/cicd-requirements.txt",
                 f'{py} -m pip install -q "Cython>3" "setuptools>=77" wheel',
                 f"{py} -m pip install -q --no-build-isolation -e .",
                 f"{py} setup.py build_ext --inplace --force",
                 "make test_lib"]:
        if sh(step, checkout, log, env):
            return {"setup_failed": step}
    sh(f"{py} -m pytest tests -v --cov --cov-report=xml:coverage.xml", checkout, log, env)
    shutil.copy(os.path.join(checkout, "coverage.xml"), os.path.join(logdir, "coverage.xml"))
    root = ET.parse(os.path.join(checkout, "coverage.xml")).getroot()
    sh(f"{py} -m coverage report", checkout, log, env)
    return {"setup": "coverage job in python-package.yml", "line_rate": float(root.get("line-rate")),
            "lines_valid": int(root.get("lines-valid")), "lines_covered": int(root.get("lines-covered"))}


def coverage_rubicon(checkout, logdir):
    """Report the coverage data the last run left in the checkout."""
    log = os.path.join(logdir, "coverage.log")
    venv = os.path.join(checkout, "toolvenv")
    report = os.path.join(logdir, "coverage-report.txt")
    sh(f"{venv}/bin/tox -e coverage314 > {report} 2>&1", checkout, log)
    text = open(report).read()
    total = re.search(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)%", text, re.M)
    if not total:
        return {"setup": "tox coverage314", "report_unparsed": True}
    stmts, miss, branches, partial, pct = total.groups()
    return {"setup": "tox coverage314 (lines and branches, excluding code for other Python versions)",
            "statements": int(stmts), "missed": int(miss), "branches": int(branches),
            "partial": int(partial), "percent": float(pct)}


def main():
    work, out = sys.argv[1], sys.argv[2]
    runs = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else VERSIONS
    results = json.load(open(out)) if os.path.exists(out) else {}
    for version in only:
        checkout = os.path.join(work, version)
        logdir = os.path.join(os.path.dirname(out), "logs", version)
        shutil.rmtree(logdir, ignore_errors=True)
        os.makedirs(logdir)
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True,
                                text=True).stdout.strip()
        entry = {"commit": commit, "python": PYTHON, "runs": []}
        runner = run_pyobjus if version.startswith("pyobjus") else run_rubicon
        for n in range(1, runs + 1):
            start = time.monotonic()
            r = runner(checkout, logdir, n)
            r["seconds"] = round(time.monotonic() - start)
            entry["runs"].append(r)
            print(version, n, {k: v for k, v in r.items() if k != "not_passed"}, flush=True)
        cov = coverage_pyobjus if version.startswith("pyobjus") else coverage_rubicon
        entry["coverage"] = cov(checkout, logdir)
        print(version, "coverage", entry["coverage"], flush=True)
        results[version] = entry
        json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
