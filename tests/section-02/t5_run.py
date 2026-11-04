"""Run t5_one.py for each sampled entry, RUNS times, in parallel processes.
Usage: t5_run.py SAMPLE.json OUT.json lib=python [lib=python ...]"""
import json
import os
import signal
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

here = os.path.dirname(os.path.abspath(__file__))
RUNS = int(os.environ.get("S2_RUNS", "5"))


def one(py, lib, e):
    args = [py, "-I", os.path.join(here, "t5_one.py"), lib, e["framework"], e["class"], e["selector"],
            "1" if e["class_method"] else "0", e["type"] if e["kind"] in ("struct", "block", "function") else ""]
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return "hang"
    for line in p.stdout.splitlines():
        if line.startswith("S2RESULT "):
            return json.loads(line[9:])["outcome"]
    return "crash " + signal.Signals(-p.returncode).name if p.returncode < 0 else f"exit {p.returncode}"


def main():
    sample_path, out, *envs = sys.argv[1:]
    sample = json.load(open(sample_path))["sample"]
    results = {}
    with ThreadPoolExecutor(6) as pool:
        for env in envs:
            label, lib, py = env.split("=")
            rows = []
            futures = [[pool.submit(one, py, lib, e) for _ in range(RUNS)] for e in sample]
            for e, fs in zip(sample, futures):
                rows.append({**e, "summary": dict(Counter(f.result() for f in fs))})
            results[label] = rows
            print(label, Counter(next(iter(r["summary"])) for r in rows), flush=True)
    json.dump(results, open(out, "w"), indent=1)


main()
