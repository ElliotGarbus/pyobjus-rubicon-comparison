"""Run one scenario in this process and print one JSON line."""
import ctypes
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
lib, name, fixture = sys.argv[1:4]
ctypes.CDLL(fixture)
from adapters import NotExpressible, load
L = load(lib)
L.cls("S2Caller").delegateProtocol()
from scenarios import SCENARIOS
try:
    outcome, detail = SCENARIOS[name](L)
except NotExpressible as e:
    outcome, detail = "not expressible", str(e)
except BaseException as e:
    outcome, detail = "python exception", f"{type(e).__name__}: {e}"[:300]
    traceback.print_exc()
print("S2RESULT " + json.dumps({"outcome": outcome, "detail": detail}), flush=True)
os._exit(0)
