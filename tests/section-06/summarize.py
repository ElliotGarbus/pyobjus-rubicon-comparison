"""Summarize the raw Section 6 results into one JSON file of figures.

Usage: summarize.py MAC.json IPHONE.json OUT.json

Timing: per operation and version, the median time per call over all timed
rounds of all processes, the 25th and 75th percentiles, each process's
median, the first and last round's time per call (to show drift within a
process), the slope of time per call against calls already made (to show
whether each call slows later ones), and how many processes crashed. The empty Python call is the
reference. Memory: the median of the processes, per object where the
measurement creates objects.
"""
import json
import statistics
import sys


def quantiles(values):
    q = statistics.quantiles(values, n=4)
    return q[0], q[2]


def slope(values, n, warmup=3):
    """Least-squares slope of time per call against calls made before each
    round's midpoint, counting the warm-up rounds, and its r squared."""
    x = [(warmup + i) * n + n / 2 for i in range(len(values))]
    mx, my = statistics.mean(x), statistics.mean(values)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, values))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in values)
    return sxy / sxx, (sxy * sxy / (sxx * syy) if syy else 0.0), my - sxy / sxx * mx


def timing(runs, op):
    per_call, process_medians, first, last, crashes, checks = [], [], [], [], 0, set()
    fits = []
    for r in runs:
        res = r.get("result", {}).get(op) if r.get("outcome") == "ok" else None
        if not res or "round_ns" not in res:
            crashes += 1
            continue
        n = ns_n = res["n"]
        values = [t / n for t in res["round_ns"]]
        per_call += values
        process_medians.append(statistics.median(values))
        fits.append(slope(values, n))
        first.append(values[0])
        last.append(values[-1])
        checks.add(res["check"]["ok"])
    if not per_call:
        return {"processes": len(runs), "crashed": crashes}
    p25, p75 = quantiles(per_call)
    return {"processes": len(runs), "crashed": crashes, "n": ns_n,
            "median_ns": statistics.median(per_call), "p25_ns": p25, "p75_ns": p75,
            "process_medians_ns": process_medians, "first_round_ns": statistics.median(first),
            "last_round_ns": statistics.median(last), "value_correct": sorted(checks),
            "slope_ns_per_call": statistics.median(f[0] for f in fits),
            "slope_r2": statistics.median(f[1] for f in fits),
            "at_zero_calls_ns": statistics.median(f[2] for f in fits)}


def memory(runs, kind):
    ok = [r["result"] for r in runs if r.get("outcome") == "ok"]
    out = {"processes": len(runs), "ok": len(ok)}
    if not ok:
        return out
    if kind.startswith("M4"):
        growth = [s["footprint_samples"][-1] - s["footprint_samples"][1] for s in ok]
        calls = ok[0]["calls_per_sample"] * 9
        out.update({"calls_measured": calls, "growth_bytes": statistics.median(growth),
                    "growth_per_call_bytes": statistics.median(growth) / calls,
                    "samples_first_process": ok[0]["footprint_samples"]})
        return out
    out["footprint_bytes"] = statistics.median(r["footprint_bytes"] for r in ok)
    out["python_bytes"] = statistics.median(r["python_bytes"] for r in ok)
    if "count" in ok[0]:
        count = ok[0]["count"]
        out.update({"count": count, "footprint_per_object": out["footprint_bytes"] / count,
                    "python_per_object": out["python_bytes"] / count})
    if "items_deallocated" in ok[0]:
        out["items_freed"] = [r["items_deallocated"] for r in ok]
        out["items_created"] = ok[0]["items_created"]
    return out


def platform(data, memory_kinds):
    out = {"timing": {}, "first_use": {}, "import": {}, "memory": {}}
    for env, ops in data.get("timing", {}).items():
        out["timing"][env] = {op: timing(runs, op) for op, runs in ops.items()}
    for env, items in data.get("first_use", {}).items():
        out["first_use"][env] = {cls: {"median_ns": statistics.median(r["result"]["ns"] for r in runs
                                                                       if r.get("outcome") == "ok")}
                                 for cls, runs in items.items()}
    for env, items in data.get("import", {}).items():
        ok = [r["result"]["ns"] for r in items["None"] if r.get("outcome") == "ok"]
        out["import"][env] = {"median_ns": statistics.median(ok), "processes": len(items["None"])}
    for env, items in data.get("memory", {}).items():
        out["memory"][env] = {kind: memory(runs, kind) for kind, runs in items.items()}
    return out


def main():
    mac, iphone, dest = sys.argv[1:4]
    mac = json.load(open(mac))
    result = {"mac": platform(mac, None)}
    result["mac"]["import_wall"] = {
        env: {"median_ns": statistics.median(r["import"] - r["empty"] for r in runs)}
        for env, runs in mac.get("import_wall", {}).items()}
    result["mac"]["size"] = {env: {k: v for k, v in s.items() if k != "root"} for env, s in mac.get("size", {}).items()}
    result["mac"]["n"] = mac["calibration"]["n"]
    try:
        ios = json.load(open(iphone))
    except FileNotFoundError:
        ios = None
    if ios:
        result["iphone"] = platform(ios, None)
        result["iphone"]["n"] = ios.get("n")
        result["iphone"]["discarded"] = len(ios.get("discarded", []))
    json.dump(result, open(dest, "w"), indent=1)


if __name__ == "__main__":
    main()
