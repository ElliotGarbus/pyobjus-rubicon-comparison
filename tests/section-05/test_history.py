"""T6: each suite's size at each stable release since 2022, and who added the
default branch's tests.

Usage: test_history.py CLONES WORK OUT.json

CLONES holds full clones named pyobjus and rubicon-objc. For each release tag,
the package is installed into a new Python 3.14 environment, the test library
is built as that version's own setup builds it, and `pytest --collect-only`
counts the tests. Where that fails, the failure is recorded. Test functions are
also counted from the source at every tag, so every tag has a count made the
same way.

For the default branch, each test function is attributed to the first commit
that added a `def` line with its name anywhere under `tests/`, giving when it
was added and by whom. `git blame` was the approved method, but it credits a
test to whoever last rewrote its `def` line, such as a migration to pytest.
"""
import ast
import collections
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

PYTHON = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
BASELINE = "2026-11-04T14:10:39Z"
YEAR_BEFORE = "2025-11-04T14:10:39Z"
AUTHOR = "Elliot Garbus"
PROJECTS = {
    "pyobjus": {"tags": ["v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"],
                "default": "0c204ada4a5aa4f065ac65fc678c6cb35e4dcb81"},
    "rubicon-objc": {"tags": ["v0.4.3", "v0.4.4", "v0.4.5", "v0.4.6", "v0.4.7", "v0.4.8",
                              "v0.4.9", "v0.5.0", "v0.5.1", "v0.5.2", "v0.5.3", "v0.5.4",
                              "v0.5.5", "v0.5.6", "v0.5.7"],
                     "default": "6bf06390f720226da3d51477f38de3ff1e680eaf"},
}


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          check=True).stdout


def test_functions(repo, ref):
    """(path, line, name) for every function named test* in tests/test_*.py at ref."""
    found = []
    for path in git(repo, "ls-tree", "-r", "--name-only", ref, "tests").split():
        if not re.search(r"(^|/)test_[^/]*\.py$", path):
            continue
        tree = ast.parse(git(repo, "show", f"{ref}:{path}"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                found.append((path, node.lineno, node.name))
    return found


def collect(repo, ref, work, log):
    """Install the package at ref and count what pytest collects."""
    checkout = os.path.join(work, ref)
    if os.path.exists(checkout):
        subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", checkout])
    git(repo, "worktree", "add", "-q", "--detach", checkout, ref)
    py = os.path.join(checkout, "venv", "bin", "python")
    makefile = open(os.path.join(checkout, "Makefile")).read() if os.path.exists(
        os.path.join(checkout, "Makefile")) else ""
    if "test_lib" in makefile:
        build = "make test_lib"
    elif os.path.exists(os.path.join(checkout, "tests", "objc", "Makefile")):
        build = "make -C tests/objc"
    else:
        build = "make darwin"
    # Editable, as pyobjus's CI installs it, so the tests import the built
    # extension rather than the source package beside them.
    install = "-e ." if "test_lib" in makefile else "."
    steps = [f"{PYTHON} -m venv venv", f"{py} -m pip install -q pytest", f"{py} -m pip install -q {install}",
             build, f"{py} -m pytest --collect-only -q tests"]
    with open(log, "a") as f:
        for step in steps:
            f.write(f"\n$ [{ref}] {step}\n")
            f.flush()
            p = subprocess.run(step, shell=True, cwd=checkout, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
            f.write(p.stdout[-20000:])
            partial = re.search(r"(\d+) tests? collected, (\d+) errors?", p.stdout)
            if p.returncode and partial:
                shutil.rmtree(checkout, ignore_errors=True)
                subprocess.run(["git", "-C", repo, "worktree", "prune"])
                return {"collected_with_errors": int(partial.group(1)),
                        "collection_errors": int(partial.group(2)), "build": build}
            if p.returncode:
                shutil.rmtree(checkout, ignore_errors=True)
                subprocess.run(["git", "-C", repo, "worktree", "prune"])
                return {"failed_step": step, "exit": p.returncode}
    m = re.search(r"(\d+) tests? collected", p.stdout)
    shutil.rmtree(checkout, ignore_errors=True)
    subprocess.run(["git", "-C", repo, "worktree", "prune"])
    return {"collected": int(m.group(1)) if m else None, "build": build}


def first_added(repo, ref, functions):
    """The first commit that added a def line for each test function's name."""
    first = {}
    commit = None
    log = git(repo, "log", "--reverse", "--format=COMMIT %H%x09%an%x09%at", "-p", "-U0", ref, "--", "tests")
    for raw in log.splitlines():
        if raw.startswith("COMMIT "):
            sha, author, when = raw[7:].split("\t")
            commit = {"commit": sha, "author": author, "author_time": int(when)}
            continue
        m = re.match(r"^\+\s*(?:async\s+)?def (test\w*)\(", raw)
        if m and m.group(1) not in first:
            first[m.group(1)] = commit
    return [{"path": path, "test": name, **first[name]} for path, line, name in functions]


def main():
    clones, work, out = sys.argv[1:4]
    os.makedirs(work, exist_ok=True)
    log = os.path.splitext(out)[0] + ".log"
    open(log, "w").close()
    start = datetime.datetime.fromisoformat(YEAR_BEFORE).timestamp()
    end = datetime.datetime.fromisoformat(BASELINE).timestamp()
    result = {}
    for project, cfg in PROJECTS.items():
        repo = os.path.join(clones, project)
        tags = []
        for tag in cfg["tags"] + [cfg["default"]]:
            row = {"ref": tag, "date": git(repo, "log", "-1", "--format=%cs", tag).strip(),
                   "test_functions": len(test_functions(repo, tag))}
            row.update(collect(repo, tag, work, log))
            tags.append(row)
            print(project, row, flush=True)
        rows = first_added(repo, cfg["default"], test_functions(repo, cfg["default"]))
        recent = [r for r in rows if start <= r["author_time"] <= end]
        by_author = collections.Counter(r["author"] for r in rows)
        result[project] = {
            "releases": tags,
            "default_branch_test_functions": len(rows),
            "added_in_year_before_baseline": len(recent),
            "added_by_author": sum(1 for r in rows if r["author"] == AUTHOR),
            "added_by_author_in_year": sum(1 for r in recent if r["author"] == AUTHOR),
            "by_author": by_author.most_common(),
            "functions": rows,
        }
        print(project, {k: v for k, v in result[project].items() if k not in ("functions", "releases")},
              flush=True)
    json.dump(result, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
