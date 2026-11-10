"""Run the window test on a phone, one app launch per run, with M1's launcher.
Usage: run_window.py OUT.json DEVICE label=bundle_id [label=bundle_id ...]

Each label runs plyer, pyobjus and rubicon S8_RUNS times (default 5). Only the
result line is saved, and devicectl's output only when a run doesn't finish."""
import datetime
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "m1", "ios"))
import run_device  # noqa: E402

RUNS = int(os.environ.get("S8_RUNS", "5"))


def main():
    out, device, *apps = sys.argv[1:]
    results = {"collected_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
    for app in apps:
        run_device.SEEN.update(run_device.crash_reports(device, app.split("=")[1].rsplit(".", 1)[-1]))
    for app in apps:
        label, bundle = app.split("=")
        for lib in ("plyer", "pyobjus", "rubicon"):
            runs = []
            for _ in range(RUNS):
                r = run_device.launch(device, bundle, {"S8_LIB": lib})
                if r.get("outcome") in ("ran", "raised"):
                    r.pop("stderr", None)
                runs.append(r)
            keys = Counter(json.dumps([r["outcome"], r.get("value", r.get("detail"))], sort_keys=True) for r in runs)
            results.setdefault(label, {})[lib] = {"runs": runs, "distinct": [json.loads(k) + [n] for k, n in keys.items()]}
            print(label, lib, dict(keys), flush=True)
            json.dump(results, open(out, "w"), indent=1)


main()
