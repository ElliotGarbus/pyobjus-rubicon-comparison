"""K1 and claim 15: does a kivy-ios app import and call pyobjus once Kivy's
event loop runs?

Usage: kivy_ios_startup.py KIVY_IOS TOUCHTRACER WORK OUT.json [RUNS]

KIVY_IOS is a kivy-ios checkout where `toolchain build python3 kivy` has
already run, with `toolchain` on PATH. TOUCHTRACER is Kivy's example folder.
Two apps are measured:

- startupsmoke: kivy-ios's own `tests/test_startup`, the app its CI launches
  on the simulator. The result is also checked the way its CI checks it.
- touchtracer: Kivy's example, which kivy-ios's CI builds but doesn't launch.

Each app gets s5check.py, imported first, and Clock callbacks that call
s5check.write() once the event loop runs. The startup app writes once, at its
first event-loop frame, then stops as kivy-ios's smoke test expects.
Touchtracer writes at its first frame and again after 3 seconds, after Kivy's
first keyboard-height update, which is timed for 0.5 seconds. Each app is
built for the simulator in Release, as kivy-ios's smoke test builds, then
installed and launched RUNS times. A booted iPhone simulator is used if there
is one. Otherwise one is chosen as kivy-ios's smoke test chooses it, an iPhone
on the newest iOS runtime the app supports, and booted.

Set XCODE_XCCONFIG_FILE as for the toolchain build, if one was needed.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE / "kivy_ios_app" / "s5check.py"


def run(cmd, cwd=None, log=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if log:
        with open(log, "a") as f:
            f.write("$ {}\n{}{}[exit {}]\n".format(" ".join(map(str, cmd)), p.stdout[-20000:],
                                                   p.stderr[-20000:], p.returncode))
    if check and p.returncode:
        raise RuntimeError("{} failed ({}); see {}".format(cmd[0], p.returncode, log))
    return p.stdout


def insert_after(text, anchor, line):
    assert text.count(anchor) == 1, anchor
    return text.replace(anchor, anchor + line)


def prepare(kivy_ios, touchtracer, work):
    apps = work / "apps"
    shutil.rmtree(apps, ignore_errors=True)
    smoke = apps / "startupsmoke"
    shutil.copytree(kivy_ios / "tests" / "test_startup", smoke)
    main = (smoke / "main.py").read_text()
    main = insert_after(main, "original_argv = list(sys.argv)\n",
                        "import s5check  # noqa: E402  Section 5 measurement\n")
    main = insert_after(main, '                payload["stage"] = "kivy-event-loop"\n',
                        '                s5check.write("kivy-event-loop")  # Section 5 measurement\n')
    (smoke / "main.py").write_text(main)
    tracer = apps / "touchtracer"
    shutil.copytree(touchtracer, tracer)
    main = (tracer / "main.py").read_text()
    main = insert_after(main, "__version__ = '1.0'\n", "\nimport s5check  # Section 5 measurement\n")
    main = insert_after(main, "    def on_pause(self):\n        return True\n",
                        "\n    def on_start(self):  # Section 5 measurement\n"
                        "        from kivy.clock import Clock\n"
                        "        Clock.schedule_once(lambda dt: s5check.write('kivy-event-loop'), 0)\n"
                        "        Clock.schedule_once(lambda dt: s5check.write('after-3s'), 3)\n")
    (tracer / "main.py").write_text(main)
    for app in (smoke, tracer):
        shutil.copy(CHECK, app / "s5check.py")
    return {"startupsmoke": ("StartupSmoke", smoke), "touchtracer": ("Touchtracer", tracer)}


def version(text):
    return tuple(int(p) for p in text.split("."))


def select_device(minimum, log):
    """A booted iPhone, or else the first iPhone on the newest iOS runtime at or
    above minimum, booted here, as kivy-ios's test_simulator_startup.py selects."""
    devices = json.loads(run(["xcrun", "simctl", "list", "devices", "--json"]))["devices"]
    for runtime, entries in devices.items():
        for d in entries:
            if d["state"] == "Booted" and "iPhone" in d["name"]:
                return {"udid": d["udid"], "name": d["name"], "runtime": runtime.rsplit(".", 1)[-1],
                        "booted_here": False}
    runtimes = json.loads(run(["xcrun", "simctl", "list", "runtimes", "--json"]))["runtimes"]
    ios = [r for r in runtimes if r.get("isAvailable") and r["identifier"].startswith(
        "com.apple.CoreSimulator.SimRuntime.iOS-") and version(r["version"]) >= version(minimum)]
    for r in sorted(ios, key=lambda r: version(r["version"]), reverse=True):
        for d in devices.get(r["identifier"], []):
            if d.get("isAvailable") and ".iPhone-" in d.get("deviceTypeIdentifier", ""):
                run(["xcrun", "simctl", "boot", d["udid"]], log=log)
                run(["xcrun", "simctl", "bootstatus", d["udid"], "-b"], log=log)
                return {"udid": d["udid"], "name": d["name"], "runtime": r["version"], "booted_here": True}
    raise RuntimeError("no available iPhone simulator at or above iOS {}".format(minimum))


def wait_for(path, timeout, done=lambda data: True):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists():
            try:
                data = json.loads(path.read_text())
                if done(data):
                    return data
            except ValueError:
                pass
        time.sleep(0.5)
    return None


def measure(name, title, source, kivy_ios, work, runs, logdir, result):
    log = logdir / "{}.log".format(name)
    project = kivy_ios / "{}-ios".format(title.lower())
    shutil.rmtree(project, ignore_errors=True)
    run(["toolchain", "create", title, str(source)], cwd=kivy_ios, log=log)
    derived = work / "DerivedData-{}".format(name)
    shutil.rmtree(derived, ignore_errors=True)
    run(["xcodebuild", "-project", str(project / "{}.xcodeproj".format(title.lower())),
         "-scheme", title.lower(), "-configuration", "Release",
         "-destination", "generic/platform=iOS Simulator", "-derivedDataPath", str(derived),
         "build", "CODE_SIGNING_ALLOWED=NO", "ARCHS=arm64"], log=log)
    product = derived / "Build/Products/Release-iphonesimulator/{}.app".format(title.lower())
    plist = str(product / "Info.plist")
    bundle = run(["/usr/libexec/PlistBuddy", "-c", "Print :CFBundleIdentifier", plist]).strip()
    minimum = run(["/usr/libexec/PlistBuddy", "-c", "Print :MinimumOSVersion", plist]).strip()
    if "device" not in result:
        result["device"] = select_device(minimum, log)
    udid = result["device"]["udid"]
    stages = ["kivy-event-loop"] + (["after-3s"] if name == "touchtracer" else [])
    run(["xcrun", "simctl", "install", udid, str(product)], log=log)
    data = Path(run(["xcrun", "simctl", "get_app_container", udid, bundle, "data"]).strip())
    results_dir = data / "Documents" / "ci-smoke"
    results = []
    try:
        for n in range(1, runs + 1):
            run(["xcrun", "simctl", "terminate", udid, bundle], log=log, check=False)
            results_dir.mkdir(parents=True, exist_ok=True)
            for f in results_dir.glob("*.json"):
                f.unlink()
            request = None
            if name == "startupsmoke":
                request = {"launch_id": uuid.uuid4().hex, "case": "ordinary"}
                (results_dir / "request.json").write_text(json.dumps(request))
            stdout = logdir / "{}-run{}.stdout.log".format(name, n)
            run(["xcrun", "simctl", "launch", "--stdout={}".format(stdout),
                 "--stderr={}".format(logdir / "{}-run{}.stderr.log".format(name, n)), udid, bundle], log=log)
            entry = {"run": n, "s5check": {stage: wait_for(results_dir / "s5check-{}.json".format(stage), 90)
                                           for stage in stages}}
            if request:
                smoke = wait_for(results_dir / "result.json", 30,
                                 lambda d: d.get("status") in ("passed", "failed"))
                entry["smoke_result"] = {k: smoke.get(k) for k in ("stage", "status", "error")} if smoke else None
            results.append(entry)
            print(name, n, json.dumps(entry), flush=True)
    finally:
        run(["xcrun", "simctl", "terminate", udid, bundle], log=log, check=False)
        run(["xcrun", "simctl", "uninstall", udid, bundle], log=log, check=False)
    return {"bundle": bundle, "minimum_ios": minimum, "runs": results}


def main():
    kivy_ios, touchtracer, work = (Path(a).resolve() for a in sys.argv[1:4])
    out = Path(sys.argv[4]).resolve()
    runs = int(sys.argv[5]) if len(sys.argv) > 5 else 3
    logdir = out.parent / "kivy_ios_logs"
    shutil.rmtree(logdir, ignore_errors=True)
    logdir.mkdir(parents=True)
    work.mkdir(parents=True, exist_ok=True)
    result = {"kivy_ios_commit": run(["git", "rev-parse", "HEAD"], cwd=kivy_ios).strip(),
              "touchtracer_source": str(touchtracer),
              "xcode": run(["xcodebuild", "-version"]).split("\n")[0],
              "xcconfig": Path(os.environ["XCODE_XCCONFIG_FILE"]).read_text()
              if os.environ.get("XCODE_XCCONFIG_FILE") else None,
              "apps": {}}
    try:
        for name, (title, source) in prepare(kivy_ios, touchtracer, work).items():
            result["apps"][name] = measure(name, title, source, kivy_ios, work, runs, logdir, result)
            json.dump(result, open(out, "w"), indent=1)
    finally:
        device = result.get("device")
        if device and device.get("booted_here"):
            run(["xcrun", "simctl", "shutdown", device["udid"]], check=False)
        json.dump(result, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
