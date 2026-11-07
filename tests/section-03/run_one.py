"""Run one case in this process and print one JSON line.
Usage: run_one.py LIB CASE BUILD_DIR, or run_one.py LIB --list BUILD_DIR"""
import ctypes
import importlib
import json
import os
import sys
import traceback

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from cases import CASES, Check, NotApplicable, NotExpressible, base, expected, same

lib, name, build = sys.argv[1:4]
ctypes.CDLL(os.path.join(build, "libs3fixture.dylib"))
ctypes.CDLL(os.path.join(build, "libS3Swift.dylib"))
os.environ["S3_EXTRA"] = os.path.join(build, "libs3extra.dylib")
module = importlib.import_module(f"cases_{lib}")
if name == "--list":
    print(json.dumps(list(module.CASES)), flush=True)
    os._exit(0)

route = {"ctypes": "ctypes", "helper": "objc helper"}.get(name.partition("__")[2], "api")
result = {"route": route}
try:
    value = module.CASES[name]()
    want = expected(base(name))
    if isinstance(value, Check):
        value, want = value.observed, value.expected
    result.update(outcome="correct" if same(value, want) else "wrong value",
                  detail=repr(value)[:300], expected=repr(want)[:300])
except NotExpressible as e:
    result.update(outcome="not expressible", detail=str(e))
except NotApplicable as e:
    result.update(outcome="not applicable", detail=str(e))
except BaseException as e:
    result.update(outcome="python exception", detail=f"{type(e).__name__}: {e}"[:300])
    traceback.print_exc()
print("S3RESULT " + json.dumps(result), flush=True)
os._exit(0)
