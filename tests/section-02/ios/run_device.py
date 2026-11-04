"""Run every scenario on a phone, one app launch per run. A crash or hang is
recorded and doesn't stop the run. Results are saved after every scenario.
Usage: run_device.py OUT.json DEVICE label=lib=bundle_id [label=lib=bundle_id ...]"""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from run_all import names

RUNS = int(os.environ.get("S2_RUNS", "5"))
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
            if line.startswith("S2RESULT "):
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
    for env in envs:
        label, lib, bundle = env.split("=")
        table = results.setdefault(label, {})
        version = launch(device, bundle, {"S2_LIB": lib, "S2_NAME": "__version__"})
        table["__version__"] = version["detail"]
        print(label, "version", version["detail"], flush=True)
        for name in names():
            if name in table:
                continue
            rs = [launch(device, bundle, {"S2_LIB": lib, "S2_NAME": name}) for _ in range(RUNS)]
            table[name] = {"summary": dict(Counter(r["outcome"] for r in rs)), "runs": rs}
            print(label, name, table[name]["summary"], rs[0]["detail"][:110], flush=True)
            json.dump(results, open(out, "w"), indent=1)


main()
