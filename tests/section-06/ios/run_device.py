"""Run every Section 6 measurement on a phone, one app launch per process.

Usage: run_device.py OUT.json DEVICE label=lib=bundle_id [...]

Launching, crash reports and hangs are handled as in Section 2's runner. lib
is pyobjus, rubicon or none (the empty-call reference). Steps, in order:

- version, then calibrate: one launch per operation and version
- N for each version: rounded up so its rounds on the phone take at least
  20 ms, to the next 1, 2 or 5 times a power of ten, as on the Mac. A version
  whose calibration crashed uses the N of the same library's other version
- timing: 5 launches per operation and version, interleaved
- first_use, import, memory: 5 launches each

A launch whose thermal state reached "serious" is kept in the record as
discarded, and rerun after the phone has had 2 minutes to cool. A rerun
resumes from OUT.json.
"""
import json
import math
import os
import re
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bench  # noqa: E402

PROCESSES = 5
TIMEOUT = 30
TARGET_NS = 20_000_000
SERIOUS = 2
# M4 makes 300,000 calls here, not 1,000,000, so a launch ends within 20 seconds.
MEMORY = ["M1", "M2", "alloc_init", "new", "copy", "method", "delegate", "M4:300000"]
FRESH = ["S6Fresh5", "S6Fresh100"]
SEEN = set()


def launch(device, bundle, env):
    cmd = ["xcrun", "devicectl", "device", "process", "launch", "--device", device, "--terminate-existing",
           "--console", "--environment-variables", json.dumps(env), bundle]
    failures = 0
    while True:
        start = time.time()
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired as e:
            err = (e.stderr or b"").decode(errors="replace")[-800:]
            return {"outcome": "hang", "detail": "no exit after {}s".format(TIMEOUT), "stderr": err}
        out, err = p.stdout, p.stderr
        for line in out.splitlines():
            if line.startswith("S6RESULT "):
                r = json.loads(line[len("S6RESULT "):])
                r["outcome"] = "python exception" if "error" in r and "result" not in r else "ok"
                r["seconds"] = round(time.time() - start, 1)
                return r
        for line in out.splitlines():
            if line.startswith(("App terminated due to signal", "The app terminated with the exit code")):
                return ended(device, bundle, line, err, round(time.time() - start, 1))
        # The phone is locked, busy or reconnecting. It isn't a test result, so wait.
        failures += 1
        if failures > 120 or "-10814" in err + out:  # 30 minutes, or the app isn't installed.
            sys.exit("giving up on launching: " + (err or out)[:500])
        print("launch failed, retrying in 15s:", (err or out)[:200].replace("\n", " "), flush=True)
        time.sleep(15)


def crash_reports(device, app):
    p = subprocess.run(["xcrun", "devicectl", "device", "info", "files", "--device", device,
                        "--domain-type", "systemCrashLogs"], capture_output=True, text=True)
    return sorted(set(re.findall(r"{}-[^ ]*\.ips".format(re.escape(app)), p.stdout)))


def read_report(device, name):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "report.ips")
        subprocess.run(["xcrun", "devicectl", "device", "copy", "from", "--device", device, "--domain-type",
                        "systemCrashLogs", "--source", name, "--destination", path], capture_output=True)
        if not os.path.exists(path):
            return None
        report = json.loads(open(path).read().split("\n", 1)[1])
    term, exc = report.get("termination", {}), report.get("exception", {})
    images = report["usedImages"]
    thread = next((t for t in report["threads"] if t.get("triggered")), {"frames": []})
    frames = ["{}!{}".format(images[f["imageIndex"]].get("name"), f.get("symbol")) for f in thread["frames"][:6]]
    indicator = term.get("indicator") or " ".join(term.get("reasons", []))[:200]
    return {"type": exc.get("type"), "signal": exc.get("signal"), "subtype": exc.get("subtype"),
            "namespace": term.get("namespace"), "code": term.get("code"), "indicator": indicator, "frames": frames}


def ended(device, bundle, line, err, seconds):
    """The app ended with no result. The phone's crash report decides, if there
    is one, and devicectl's signal is the fallback, as in Section 2."""
    app = bundle.rsplit(".", 1)[-1]
    report = None
    for _ in range(8):
        new = [n for n in crash_reports(device, app) if n not in SEEN]
        if new:
            SEEN.update(new)
            report = read_report(device, new[-1])
            break
        time.sleep(1)
    r = {"seconds": seconds, "devicectl": line, "stderr": err[-800:], "report": report}
    if report is None:
        match = re.search(r"signal (\d+)", line)
        if not match:
            r.update(outcome="exited", detail=line)
        elif int(match.group(1)) == signal.SIGKILL and seconds >= 19:
            r.update(outcome="hang", detail="killed at the iOS launch watchdog's 20s, with no crash report")
        else:
            r.update(outcome="crash", detail=signal.Signals(int(match.group(1))).name)
    elif report["namespace"] == "FRONTBOARD" and report["code"] == 0x8BADF00D:
        r.update(outcome="hang", detail="main thread blocked until the iOS launch watchdog killed the app at 20s")
    else:
        r.update(outcome="crash", detail=report["signal"] or line)
    return r


def measure(device, bundle, lib, mode, arg, discarded):
    """One launch, rerun after cooling if the phone reached a serious thermal state."""
    while True:
        env = {"S6_LIB": lib, "S6_MODE": mode}
        if arg is not None:
            env["S6_ARG"] = str(arg)
        r = launch(device, bundle, env)
        hot = max(r.get("thermal_start", 0), r.get("thermal_end", 0)) >= SERIOUS
        if not hot:
            return r
        discarded.append({"lib": lib, "mode": mode, "arg": arg, "run": r})
        print("thermal state serious, cooling for 2 minutes", flush=True)
        time.sleep(120)


def round_up(x):
    exp = 10 ** math.floor(math.log10(x))
    for m in (1, 2, 5, 10):
        if m * exp >= x:
            return int(m * exp)


def main():
    out, device, *specs = sys.argv[1:]
    envs = {}
    for spec in specs:
        label, lib, bundle = spec.split("=")
        envs[label] = (lib, bundle)
        SEEN.update(crash_reports(device, bundle.rsplit(".", 1)[-1]))
    result = json.load(open(out)) if os.path.exists(out) else {}
    discarded = result.setdefault("discarded", [])

    def save():
        json.dump(result, open(out, "w"), indent=1)

    versions = result.setdefault("versions", {})
    for label, (lib, bundle) in envs.items():
        if label not in versions:
            r = measure(device, bundle, lib, "version", None, discarded)
            versions[label] = {k: r.get(k) for k in ("result", "python", "platform", "low_power_mode")}
            print(label, versions[label], flush=True)
            save()

    ops = bench.operation_names("pyobjus")
    cal = result.setdefault("calibration", {})
    for op in ops + ["python_empty_call"]:
        for label, (lib, bundle) in envs.items():
            if (lib == "none") != (op == "python_empty_call") or label in cal.get(op, {}):
                continue
            r = measure(device, bundle, lib, "calibrate", op, discarded)
            cal.setdefault(op, {})[label] = r
            print("calibrate", op, label, r.get("result", {}).get(op, {}).get("per_call_ns", r["outcome"]), flush=True)
            save()
    n = {}
    for op, runs in cal.items():
        ok = {label: round_up(TARGET_NS / r["result"][op]["per_call_ns"]) for label, r in runs.items()
              if r["outcome"] == "ok"}
        for label in runs:
            same = [other for other in ok if envs[other][0] == envs[label][0]]
            n.setdefault(label, {})[op] = ok.get(label, ok[same[0]] if same else max(ok.values()) if ok else 1000)
    result["n"] = n
    save()

    timing = result.setdefault("timing", {})
    for p in range(1, PROCESSES + 1):
        for op in ops + ["python_empty_call"]:
            for label, (lib, bundle) in envs.items():
                if (lib == "none") != (op == "python_empty_call"):
                    continue
                runs = timing.setdefault(label, {}).setdefault(op, [])
                if len(runs) >= p:
                    continue
                r = measure(device, bundle, lib, "timing", "{}:{}".format(op, n[label][op]), discarded)
                runs.append(r)
                median = r.get("result", {}).get(op, {}).get("per_call_ns_median")
                print("timing", p, op, label, round(median) if median else r["outcome"], flush=True)
                save()

    for step, items in (("first_use", FRESH), ("import", [None]), ("memory", MEMORY)):
        store = result.setdefault(step, {})
        for p in range(1, PROCESSES + 1):
            for item in items:
                for label, (lib, bundle) in envs.items():
                    if lib == "none":
                        continue
                    runs = store.setdefault(label, {}).setdefault(str(item), [])
                    if len(runs) >= p:
                        continue
                    r = measure(device, bundle, lib, step, item, discarded)
                    runs.append(r)
                    print(step, p, item, label, r["outcome"], json.dumps(r.get("result"))[:150], flush=True)
                    save()


if __name__ == "__main__":
    main()
