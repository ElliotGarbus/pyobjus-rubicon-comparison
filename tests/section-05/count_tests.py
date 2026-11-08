"""T1: lines of test code in each suite, counted as Section 4 counts examples.

Usage: count_tests.py WORK OUT.json

WORK holds the checkouts named in VERSIONS. Python is every .py file under
tests/, formatted with ruff, then blank lines, comments, docstrings and imports
aren't counted. Native code is the Objective-C the suite compiles into its test
library, not reformatted, without blank lines, comments and imports.
"""
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "section-04"))
from count import RUFF, formatted, native_lines, python_lines  # noqa: E402

NATIVE = {"pyobjus": "objc_classes/test", "rubicon": "testbed/objc"}
VERSIONS = ["pyobjus-1.2.4", "pyobjus-master", "rubicon-0.5.7", "rubicon-main"]


def main():
    work, out = sys.argv[1], sys.argv[2]
    version = subprocess.run(["uvx", RUFF, "--version"], capture_output=True, text=True,
                             check=True).stdout.strip()
    result = {"ruff": version, "versions": {}}
    for name in VERSIONS:
        checkout = os.path.join(work, name)
        tracked = subprocess.run(["git", "ls-files"], cwd=checkout, capture_output=True, text=True,
                                 check=True).stdout.split()
        py = sorted(p for p in tracked if p.startswith("tests/") and p.endswith(".py"))
        native_dir = NATIVE[name.split("-")[0]]
        native = sorted(p for p in tracked if p.startswith(native_dir + "/") and p.endswith((".m", ".h")))
        row = {"commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True,
                                        text=True).stdout.strip(),
               "python_files": len(py),
               "python_lines": sum(python_lines(formatted(os.path.join(checkout, p))) for p in py),
               "native_files": len(native),
               "native_lines": sum(native_lines(os.path.join(checkout, p)) for p in native)}
        result["versions"][name] = row
        print(name, row, flush=True)
    json.dump(result, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
