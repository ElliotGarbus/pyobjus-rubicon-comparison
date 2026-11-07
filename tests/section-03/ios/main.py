"""Run one Section 3 case in this process, as run_one.py does on the Mac.
The host passes its choice in the environment, because each launch is one run.
S3_NAME can also be "__version__" or "__list__"."""
import ctypes
import json
import os
import sys
import traceback


def report(result):
    os.write(1, ("S3RESULT " + json.dumps(result) + "\n").encode())


here = os.path.dirname(os.path.abspath(__file__))
frameworks = os.path.join(here, "..", "Frameworks")
ctypes.CDLL(os.path.join(frameworks, "S3Fixture.framework", "S3Fixture"))
os.environ["S3_EXTRA"] = os.path.join(frameworks, "S3Extra.framework", "S3Extra")
lib, name = os.environ["S3_LIB"], os.environ["S3_NAME"]
try:
    import importlib
    module = importlib.import_module(f"cases_{lib}")
    if name == "__version__":
        mod = __import__("pyobjus" if lib == "pyobjus" else "rubicon.objc", fromlist=["x"])
        report({"outcome": "version", "detail": getattr(mod, "__version__", "unknown")})
    elif name == "__list__":
        report({"outcome": "list", "detail": json.dumps(list(module.CASES))})
    else:
        from cases import Check, NotApplicable, NotExpressible, base, expected, same
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
            traceback.print_exc()
            result.update(outcome="python exception", detail=f"{type(e).__name__}: {e}"[:300])
        report(result)
except BaseException as e:
    traceback.print_exc()
    report({"outcome": "python exception", "detail": f"{type(e).__name__}: {e}"[:300]})
sys.stdout.flush()
os._exit(0)
