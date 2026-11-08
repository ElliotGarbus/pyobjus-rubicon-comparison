"""Run the Mac examples in their own processes, RUNS times, for each environment.
Usage: run_mac.py OUT.json label=lib=python [label=lib=python ...]"""
import json
import os
import signal
import subprocess
import sys
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
RUNS = int(os.environ.get("S4_RUNS", "5"))
TIMEOUT = 30


def one(py, example, lib):
    p = subprocess.Popen([py, "-I", os.path.join(here, "run_one.py"), example, lib],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = p.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        return {"outcome": "hang", "detail": f"killed after {TIMEOUT}s", "stderr": err[-800:]}
    for line in out.splitlines():
        if line.startswith("S4RESULT "):
            r = json.loads(line[9:])
            r["stderr"] = err[-800:]
            return r
    if p.returncode < 0:
        return {"outcome": "crash", "detail": signal.Signals(-p.returncode).name, "stderr": err[-800:]}
    return {"outcome": "exited", "detail": f"exit code {p.returncode}", "stderr": err[-800:]}


def main():
    out, *envs = sys.argv[1:]
    from harness import EXAMPLES
    results = {}
    for env in envs:
        label, lib, py = env.split("=")
        results[label] = {}
        for example, platform in EXAMPLES.items():
            if platform != "Mac":
                continue
            rs = [one(py, example, lib) for _ in range(RUNS)]
            results[label][example] = {"summary": dict(Counter(r["outcome"] for r in rs)), "runs": rs}
            print(label, example, results[label][example]["summary"], rs[0]["detail"][:110], flush=True)
    json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
