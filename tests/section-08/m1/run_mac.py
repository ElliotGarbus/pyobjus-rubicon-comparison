"""Run every M1 case in its own process, RUNS times, for each environment.
Usage: run_mac.py OUT.json BUILD label=lib=python [label=lib=python ...]

BUILD holds libs8helper.dylib (see s8helper.m). A crash, hang or exception
is recorded and doesn't stop the run. Set S8_RUNS to change the number of
runs, and S8_ONLY to comma-separated case names to run only those."""
import json
import os
import signal
import subprocess
import sys
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
RUNS = int(os.environ.get("S8_RUNS", "5"))
TIMEOUT = 30


def one(py, lib, case, env):
    p = subprocess.Popen([py, "-I", os.path.join(here, "run_one.py"), lib, case], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, start_new_session=True, env=env, cwd=here)
    try:
        out, err = p.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        return {"outcome": "hang", "value": f"killed after {TIMEOUT}s", "stderr": err[-800:]}
    for line in out.splitlines():
        if line.startswith("S8RESULT "):
            r = json.loads(line[9:])
            r["stderr"] = err[-800:]
            return r
    if p.returncode < 0:
        return {"outcome": "crash", "value": signal.Signals(-p.returncode).name, "stderr": err[-800:]}
    return {"outcome": "exited", "value": f"exit code {p.returncode}", "stderr": err[-800:]}


def main():
    out, build, *envs = sys.argv[1:]
    env = dict(os.environ, S8_HELPER=os.path.join(os.path.abspath(build), "libs8helper.dylib"))
    # The case names, read from the source so this runner needs neither library.
    src = open(os.path.join(here, "cases_rubicon.py")).read()
    cases = src.split("CASES = {f.__name__: f for f in (")[1].split(")}")[0].replace("\n", " ")
    cases = [c.strip() for c in cases.split(",") if c.strip()]
    only = os.environ.get("S8_ONLY")
    if only:
        cases = [c for c in cases if c in only.split(",")]
    results = json.load(open(out)) if os.path.exists(out) else {}
    for spec in envs:
        label, lib, py = spec.split("=", 2)
        for case in cases:
            runs = [one(py, lib, case, env) for _ in range(RUNS)]
            keys = Counter(json.dumps([r["outcome"], r["value"]], sort_keys=True) for r in runs)
            results.setdefault(label, {})[case] = {"lib": lib, "runs": runs,
                                                   "distinct": [json.loads(k) + [n] for k, n in keys.items()]}
            print(label, case, dict(keys), flush=True)
            json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
