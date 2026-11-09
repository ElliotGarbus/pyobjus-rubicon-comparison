"""Run every Section 6 measurement on the Mac, each in its own process.

Usage: run_mac.py FIXTURE OUT.json ENV=LIB=PYTHON [...] [--only STEP,...]

ENV names a version point, such as rubicon-main. LIB is pyobjus, rubicon,
pyobjc or none (Python only, for the empty-call reference). Steps, in order:

- calibrate: one process per operation and version, to choose N for that
  version: rounded up so its rounds take at least 20 ms, to the next 1, 2 or
  5 times a power of ten. A version whose calibration crashed uses the N of
  the same library's other version, or else the largest N of the others
- timing: 5 processes per operation and version, interleaved so that drift
  over the run affects every version alike
- first_use, import, memory: 5 processes each
- size: installed package size

A process that crashes, hangs or prints no result is recorded with its exit
status and the end of its output. Calibration results are saved, and an
existing calibration in OUT.json is reused.
"""
import json
import math
import os
import platform
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, "bench.py")
PROCESSES = 5
TARGET_NS = 20_000_000
COMPARED = ("pyobjus", "rubicon")  # memory is measured for these only
MEMORY = ["M1", "M2", "alloc_init", "new", "copy", "method", "delegate", "M4"]
FRESH = ["S6Fresh5", "S6Fresh100"]
sys.path.insert(0, HERE)


def run(python, lib, fixture, mode, arg=None, timeout=1800):
    cmd = [python, "-X", "faulthandler", BENCH, lib, fixture, mode] + ([str(arg)] if arg is not None else [])
    start = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return {"outcome": "hang", "seconds": round(time.time() - start, 1),
                "output_tail": ((e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes)
                                else (e.stdout or ""))[-1500:]}
    for line in p.stdout.splitlines():
        if line.startswith("S6RESULT "):
            out = json.loads(line[len("S6RESULT "):])
            out["outcome"] = "ok"
            out["seconds"] = round(time.time() - start, 1)
            return out
    tail = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if not l.strip().startswith("Binary file"))
    return {"outcome": "crash" if p.returncode < 0 or p.returncode > 128 else "no result",
            "exit": p.returncode, "seconds": round(time.time() - start, 1), "output_tail": tail[-1500:]}


def round_up(x):
    exp = 10 ** math.floor(math.log10(x))
    for m in (1, 2, 5, 10):
        if m * exp >= x:
            return int(m * exp)


def per_version_n(cal, ops, envs):
    """N for each version and operation, so each version's rounds take at least 20 ms."""
    n = {}
    for op in ops:
        runs = cal["runs"][op]
        ok = {name: round_up(TARGET_NS / r["result"][op]["per_call_ns"]) for name, r in runs.items()
              if r["outcome"] == "ok"}
        for name in runs:
            same = [other for other in ok if envs[other][0] == envs[name][0]]
            n.setdefault(name, {})[op] = ok.get(name, ok[same[0]] if same else max(ok.values()))
    for name, r in cal["empty"].items():
        n.setdefault(name, {})["python_empty_call"] = (
            round_up(TARGET_NS / r["result"]["python_empty_call"]["per_call_ns"]) if r["outcome"] == "ok"
            else 10_000_000)
    return n


def mac_info():
    def sh(*cmd):
        return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    return {"macos": sh("sw_vers", "-productVersion"), "build": sh("sw_vers", "-buildVersion"),
            "cpu": sh("sysctl", "-n", "machdep.cpu.brand_string"), "machine": platform.machine(),
            "power": sh("pmset", "-g", "batt").splitlines()[0] if sh("pmset", "-g", "batt") else "",
            "low_power_mode": [l.strip() for l in sh("pmset", "-g").splitlines() if "lowpowermode" in l]}


def package_size(python, lib):
    code = ("import importlib.util, os, sys\n"
            "name = {'pyobjus': 'pyobjus', 'rubicon': 'rubicon.objc', 'pyobjc': 'objc'}[sys.argv[1]]\n"
            "spec = importlib.util.find_spec(name)\n"
            "root = os.path.dirname(spec.origin)\n"
            "files = [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs if '__pycache__' not in d]\n"
            "print(root, sum(os.path.getsize(f) for f in files), len(files))\n")
    out = subprocess.run([python, "-c", code, lib], capture_output=True, text=True).stdout.split()
    return {"root": out[0].replace(os.path.expanduser("~"), "~"), "bytes": int(out[1]), "files": int(out[2])}


def wall_import(python, lib):
    """S1 cross-check: wall time of a process that imports and makes the first
    call, less the wall time of an empty Python process."""
    stmt = {"pyobjus": "from pyobjus import autoclass; autoclass('NSObject').alloc().init()",
            "rubicon": "from rubicon.objc import NSObject; NSObject.alloc().init()",
            "pyobjc": "import objc; objc.lookUpClass('NSObject').alloc().init()"}[lib]
    times = {}
    for name, code in (("empty", "pass"), ("import", stmt)):
        t0 = time.perf_counter_ns()
        subprocess.run([python, "-c", code], check=True)
        times[name] = time.perf_counter_ns() - t0
    return times


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--only")]
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only"):
            only = a.split("=", 1)[1].split(",")
    fixture, out = args[0], args[1]
    envs = {}
    for spec in args[2:]:
        name, lib, python = spec.split("=", 2)
        envs[name] = (lib, python)
    import bench
    result = json.load(open(out)) if os.path.exists(out) else {}
    result["mac"] = mac_info()
    result["envs"] = {k: {"lib": v[0]} for k, v in envs.items()}

    def save():
        json.dump(result, open(out, "w"), indent=1)

    def want(step):
        return only is None or step in only

    ops = bench.operation_names("pyobjus")
    if want("calibrate") and "calibration" not in result:
        cal = {}
        for op in ops:
            cal[op] = {name: run(python, lib, fixture, "calibrate", op)
                       for name, (lib, python) in envs.items() if lib != "none"}
            print("calibrate", op, {k: v.get("result", {}).get(op, {}).get("per_call_ns", v["outcome"])
                                    for k, v in cal[op].items()}, flush=True)
        empty = {name: run(python, "none", fixture, "calibrate", "python_empty_call")
                 for name, (lib, python) in envs.items() if lib == "none"}
        result["calibration"] = {"runs": cal, "empty": empty}
        save()
    if "calibration" in result:
        result["calibration"]["n"] = per_version_n(result["calibration"], ops, envs)
        save()
    n = result.get("calibration", {}).get("n", {})

    if want("timing"):
        timing = result.setdefault("timing", {})
        for p in range(1, PROCESSES + 1):
            for op in ops + ["python_empty_call"]:
                for name, (lib, python) in envs.items():
                    if (lib == "none") != (op == "python_empty_call"):
                        continue
                    runs = timing.setdefault(name, {}).setdefault(op, [])
                    if len(runs) >= p:
                        continue
                    r = run(python, lib, fixture, "timing", "{}:{}".format(op, n[name][op]))
                    runs.append(r)
                    median = r.get("result", {}).get(op, {}).get("per_call_ns_median")
                    print("timing", p, op, name, round(median) if median else r["outcome"], flush=True)
                    save()

    for step, mode, items in (("first_use", "first_use", FRESH), ("import", "import", [None]),
                              ("memory", "memory", MEMORY)):
        if not want(step):
            continue
        store = result.setdefault(step, {})
        for p in range(1, PROCESSES + 1):
            for item in items:
                for name, (lib, python) in envs.items():
                    if lib == "none" or (step == "memory" and lib not in COMPARED):
                        continue
                    runs = store.setdefault(name, {}).setdefault(str(item), [])
                    if len(runs) >= p:
                        continue
                    r = run(python, lib, fixture, mode, item)
                    runs.append(r)
                    print(step, p, item, name, r["outcome"], json.dumps(r.get("result"))[:160], flush=True)
                    save()

    if want("import_wall"):
        walls = result.setdefault("import_wall", {})
        for p in range(1, PROCESSES + 1):
            for name, (lib, python) in envs.items():
                if lib == "none":
                    continue
                runs = walls.setdefault(name, [])
                if len(runs) < p:
                    runs.append(wall_import(python, lib))
                    save()

    if want("size"):
        result["size"] = {name: package_size(python, lib) for name, (lib, python) in envs.items()
                          if lib != "none"}
        save()


if __name__ == "__main__":
    main()
