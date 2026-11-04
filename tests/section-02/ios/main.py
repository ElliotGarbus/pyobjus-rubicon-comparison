"""Run one Section 2 scenario in this process, as run_one.py does on the Mac.
The host passes its choice in the environment, because each launch is one run."""
import ctypes
import json
import os
import traceback


def report(outcome, detail):
    line = "S2RESULT " + json.dumps({"outcome": outcome, "detail": detail}) + "\n"
    os.write(1, line.encode())


here = os.path.dirname(os.path.abspath(__file__))
ctypes.CDLL(os.path.join(here, "..", "Frameworks", "S2Fixture.framework", "S2Fixture"))
try:
    from adapters import NotExpressible, load
    L = load(os.environ["S2_LIB"])
    if os.environ["S2_NAME"] == "__version__":
        report("version", L.version)
    else:
        L.cls("S2Caller").delegateProtocol()
        from scenarios import SCENARIOS
        try:
            outcome, detail = SCENARIOS[os.environ["S2_NAME"]](L)
        except NotExpressible as e:
            outcome, detail = "not expressible", str(e)
        report(outcome, detail)
except BaseException as e:
    traceback.print_exc()
    report("python exception", f"{type(e).__name__}: {e}"[:300])
os._exit(0)
