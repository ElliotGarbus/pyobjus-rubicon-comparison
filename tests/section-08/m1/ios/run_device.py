"""Run every M1 iPhone case on a phone, one app launch per run. A crash or hang is
recorded and doesn't stop the run. Results are saved after every case.
Usage: run_device.py OUT.json DEVICE label=lib=bundle_id [label=lib=bundle_id ...]

Set S8_ONLY to comma-separated case names to run only those, and S8_RUNS
to change the number of runs. Adapted from Section 4's runner."""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter

import ast

M1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def case_names():
    """The case names, read from cases_ios_pyobjus.py so the host needs neither library."""
    tree = ast.parse(open(os.path.join(M1, "cases_ios_pyobjus.py")).read())
    names = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "PORTABLE":
            names += [e.value for e in node.value.elts]
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and \
                getattr(node.value.func, "attr", None) == "update":
            names += [e.id for e in node.value.args[0].generators[0].iter.elts]
    return names


RUNS = int(os.environ.get("S8_RUNS", "5"))
TIMEOUT = 30
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
            return {"outcome": "hang", "detail": f"no exit after {TIMEOUT}s", "stderr": err}
        out, err = p.stdout, p.stderr
        for line in out.splitlines():
            if line.startswith("S8RESULT "):
                r = json.loads(line[9:])
                r["stderr"] = err[-800:]
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
    return sorted(set(re.findall(rf"{re.escape(app)}-[^ ]*\.ips", p.stdout)))


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
    frames = [f"{images[f['imageIndex']].get('name')}!{f.get('symbol')}" for f in thread["frames"][:6]]
    indicator = term.get("indicator") or " ".join(term.get("reasons", []))[:200]
    return {"type": exc.get("type"), "signal": exc.get("signal"), "subtype": exc.get("subtype"),
            "namespace": term.get("namespace"), "code": term.get("code"), "indicator": indicator, "frames": frames}


def ended(device, bundle, line, err, seconds):
    """The app ended with no result. devicectl's line can be wrong: it has reported
    exit code 0 for an abort. So the phone's crash report decides, if there is one.
    iOS stops writing reports after enough crashes, so devicectl's signal is the fallback."""
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


def main():
    out, device, *envs = sys.argv[1:]
    for env in envs:
        SEEN.update(crash_reports(device, env.split("=")[2].rsplit(".", 1)[-1]))
    results = json.load(open(out)) if os.path.exists(out) else {}
    only = os.environ.get("S8_ONLY")
    for env in envs:
        label, lib, bundle = env.split("=")
        table = results.setdefault(label, {})
        version = launch(device, bundle, {"S8_LIB": lib, "S8_CASE": "__version__"})
        table["__version__"] = version.get("value")
        print(label, "version", version.get("value"), flush=True)
        for name in case_names():
            if (only and name not in only.split(",")) or (name in table and not only):
                continue
            rs = [launch(device, bundle, {"S8_LIB": lib, "S8_CASE": name}) for _ in range(RUNS)]
            keys = Counter(json.dumps([r["outcome"], r.get("value", r.get("detail"))], sort_keys=True) for r in rs)
            table[name] = {"lib": lib, "runs": rs, "distinct": [json.loads(k) + [n] for k, n in keys.items()]}
            print(label, name, dict(keys), flush=True)
            json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
