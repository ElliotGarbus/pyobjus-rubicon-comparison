"""Run one M1 case on the iPhone, as run_one.py does on the Mac. The host
passes its choice in the environment, because each launch is one run."""
import json
import os
import sys
import traceback

lib, case = os.environ["S8_LIB"], os.environ["S8_CASE"]
try:
    if case == "__version__":
        mod = __import__("pyobjus" if lib == "pyobjus" else "rubicon.objc", fromlist=["x"])
        result = {"outcome": "version", "value": getattr(mod, "__version__", "unknown")}
    else:
        module = __import__("cases_ios_" + lib)
        result = {"outcome": "ran", "value": module.CASES[case]()}
except Exception as e:
    result = {"outcome": "raised", "value": type(e).__name__ + ": " + str(e)[:300],
              "traceback": traceback.format_exc()[-1500:]}
os.write(1, ("S8RESULT " + json.dumps(result, default=repr) + "\n").encode())
sys.stdout.flush()
os._exit(0)
