"""Section 5: whether starting a kivy-ios app imports and calls pyobjus.

The app imports this module first. It watches imports without changing them,
and write(stage) saves what it saw to Documents/ci-smoke/s5check-<stage>.json.
It reads Python state only and makes no Objective-C calls of its own.
"""
import json
import os
import sys
import traceback
from pathlib import Path

WATCH = ("ios", "pyobjus")
first_import = {}


def _short(filename):
    parts = filename.replace("\\", "/").split("/")
    for marker in ("site-packages", "YourApp"):
        if marker in parts:
            return "/".join(parts[parts.index(marker) + 1:])
    return "/".join(parts[-2:])


class _Watcher:
    """Records the Python frames that first import each watched module."""

    def find_spec(self, name, path=None, target=None):
        if name in WATCH and name not in first_import:
            frames = [f for f in traceback.extract_stack()[:-1]
                      if "importlib" not in f.filename and not f.filename.endswith("s5check.py")]
            first_import[name] = ["{}:{} {}".format(_short(f.filename), f.lineno, f.name)
                                  for f in frames[-6:]]
        return None


sys.meta_path.insert(0, _Watcher())


def write(stage):
    ios = sys.modules.get("ios")
    keyboard = getattr(ios, "iOSKeyboard", None) if ios else None
    core = sys.modules.get("pyobjus.pyobjus")
    delegates = getattr(core, "delegate_register", {}) if core else {}
    try:
        from kivy.base import EventLoop
        status = EventLoop.status
    except Exception as error:
        status = "unknown: {!r}".format(error)
    result = {
        "stage": stage,
        "event_loop_status": status,
        "imported": {name: name in sys.modules for name in WATCH},
        "pyobjus_modules": sorted(m for m in sys.modules if m == "pyobjus" or m.startswith("pyobjus.")),
        "ios_keyboard": type(keyboard).__name__ if keyboard is not None else None,
        # A Python object passed to Objective-C through pyobjus gets an entry here.
        "pyobjus_delegates": sorted(type(obj).__name__ for obj in delegates),
        "first_import": first_import,
    }
    directory = Path.home() / "Documents" / "ci-smoke"
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / "s5check-{}.json.tmp".format(stage)
    temporary.write_text(json.dumps(result), encoding="utf-8")
    os.replace(str(temporary), str(directory / "s5check-{}.json".format(stage)))
    print("S5CHECK " + json.dumps(result), flush=True)
