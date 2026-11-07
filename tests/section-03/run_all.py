"""Run every case in its own process, RUNS times, for each environment.
Usage: run_all.py OUT.json BUILD_DIR label=lib=python [label=lib=python ...]

Set S3_ONLY to comma-separated case prefixes to run only those, and S3_RUNS
to change the number of runs. A rerun keeps the cases already in OUT.json."""
import json
import os
import signal
import subprocess
import sys
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from cases import CASES

RUNS = int(os.environ.get("S3_RUNS", "5"))
TIMEOUT = 30


def names(py, lib, build):
    out = subprocess.run([py, "-I", os.path.join(here, "run_one.py"), lib, "--list", build],
                         capture_output=True, text=True, check=True).stdout
    found = json.loads(out)
    missing = [c for c in CASES if "__" not in c and c not in found]
    if missing:
        sys.exit(f"cases_{lib}.py doesn't define: {', '.join(missing)}")
    only = os.environ.get("S3_ONLY")
    return [n for n in found if not only or n.startswith(tuple(only.split(",")))]


def one(py, lib, name, build):
    p = subprocess.Popen([py, "-I", os.path.join(here, "run_one.py"), lib, name, build],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         start_new_session=True)
    try:
        out, err = p.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        return {"outcome": "hang", "detail": f"killed after {TIMEOUT}s", "stderr": err[-800:]}
    for line in out.splitlines():
        if line.startswith("S3RESULT "):
            r = json.loads(line[9:])
            r["stderr"] = err[-800:]
            return r
    if p.returncode < 0:
        return {"outcome": "crash", "detail": signal.Signals(-p.returncode).name, "stderr": err[-800:]}
    return {"outcome": "exited", "detail": f"exit code {p.returncode}", "stderr": err[-800:]}


def main():
    out, build, *envs = sys.argv[1:]
    results = json.load(open(out)) if os.path.exists(out) else {}
    for env in envs:
        label, lib, py = env.split("=")
        results.setdefault(label, {})
        for name in names(py, lib, build):
            if name in results[label] and not os.environ.get("S3_ONLY"):
                continue
            rs = [one(py, lib, name, build) for _ in range(RUNS)]
            c = Counter(r["outcome"] for r in rs)
            results[label][name] = {"summary": dict(c), "runs": rs}
            print(label, name, dict(c), rs[0]["detail"][:110], flush=True)
            json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
