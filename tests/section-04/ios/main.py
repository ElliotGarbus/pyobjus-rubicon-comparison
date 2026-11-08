"""Run one Section 4 example in this process, as run_one.py does on the Mac.
The host passes its choice in the environment, because each launch is one run."""
import json
import os
import sys

from harness import run

lib, example = os.environ["S4_LIB"], os.environ["S4_EXAMPLE"]
if example == "__version__":
    mod = __import__("pyobjus" if lib == "pyobjus" else "rubicon.objc", fromlist=["x"])
    result = {"outcome": "version", "detail": getattr(mod, "__version__", "unknown")}
else:
    result = run(example, lib)
os.write(1, ("S4RESULT " + json.dumps(result) + "\n").encode())
sys.stdout.flush()
os._exit(0)
