"""Run t5_calls.py for each sampled entry, RUNS times, in parallel processes.
A crash or hang is recorded against that entry and doesn't stop the run.
Usage: t5_call_run.py SAMPLE.json OUT.json lib=python [lib=python ...]"""
import json
import os
import signal
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

here = os.path.dirname(os.path.abspath(__file__))
RUNS = int(os.environ.get("S2_RUNS", "5"))
ONLY = os.environ.get("S2_ONLY")
TIMEOUT = 30


def one(py, lib, index):
    args = [py, "-I", os.path.join(here, "t5_calls.py"), lib, str(index)]
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"outcome": "hang", "detail": f"killed after {TIMEOUT}s"}
    for line in p.stdout.splitlines():
        if line.startswith("S2RESULT "):
            return json.loads(line[9:])
    if p.returncode < 0:
        return {"outcome": "crash", "detail": signal.Signals(-p.returncode).name, "stderr": p.stderr[-400:]}
    return {"outcome": "exited", "detail": f"exit code {p.returncode}", "stderr": p.stderr[-400:]}


def main():
    sample_path, out, *envs = sys.argv[1:]
    sample = json.load(open(sample_path))["sample"]
    indexes = [int(i) for i in ONLY.split(",")] if ONLY else range(len(sample))
    results = {}
    with ThreadPoolExecutor(6) as pool:
        for env in envs:
            label, lib, py = env.split("=")
            futures = {i: [pool.submit(one, py, lib, i) for _ in range(RUNS)] for i in indexes}
            rows = []
            for i, fs in futures.items():
                runs = [f.result() for f in fs]
                rows.append({**sample[i], "index": i, "summary": dict(Counter(r["outcome"] for r in runs)),
                             "detail": runs[0]["detail"], "stderr": runs[0].get("stderr", "")})
            results[label] = rows
            print(label, dict(Counter(next(iter(r["summary"])) for r in rows)), flush=True)
    json.dump(results, open(out, "w"), indent=1)


main()
