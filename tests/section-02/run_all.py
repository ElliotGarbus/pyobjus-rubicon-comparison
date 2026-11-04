"""Run every scenario in its own process, RUNS times, for each environment.
Usage: run_all.py OUT.json FIXTURE lib=python [lib=python ...]"""
import json
import os
import signal
import subprocess
import sys
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
RUNS = int(os.environ.get("S2_RUNS", "5"))
TIMEOUT = 30


def names():
    import re
    src = open(os.path.join(here, "scenarios.py")).read()
    found = re.findall(r"^@scenario\s*\ndef (\w+)", src, re.M)
    for k in ("delegate", "subclass", "block", "function"):
        found += [f"cb2_{k}_{v}" for v in ("int", "double", "object", "rect")]
        found += [f"cb3_{k}", f"cb4_{k}"]
    found += ["cb2_block_rect_arg", "cb2_function_rect_arg"]
    only = os.environ.get("S2_ONLY")
    return [n for n in found if not only or n.startswith(tuple(only.split(",")))]


def one(py, lib, name, fixture):
    p = subprocess.Popen([py, "-I", os.path.join(here, "run_one.py"), lib, name, fixture],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         start_new_session=True)
    try:
        out, err = p.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        return {"outcome": "hang", "detail": f"killed after {TIMEOUT}s", "stderr": err[-800:]}
    for line in out.splitlines():
        if line.startswith("S2RESULT "):
            r = json.loads(line[9:])
            r["stderr"] = err[-800:]
            return r
    if p.returncode < 0:
        return {"outcome": "crash", "detail": signal.Signals(-p.returncode).name, "stderr": err[-800:]}
    return {"outcome": "exited", "detail": f"exit code {p.returncode}", "stderr": err[-800:]}


def main():
    out, fixture, *envs = sys.argv[1:]
    results = {}
    for env in envs:
        label, lib, py = env.split("=")
        results[label] = {}
        for name in names():
            rs = [one(py, lib, name, fixture) for _ in range(RUNS)]
            c = Counter(r["outcome"] for r in rs)
            results[label][name] = {"summary": dict(c), "runs": rs}
            print(label, name, dict(c), rs[0]["detail"][:110], flush=True)
    json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
