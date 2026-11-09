"""Run one Section 6 measurement in this launch, as bench.py's main() does on
the Mac. The host passes the library, mode and argument in the environment,
because each launch is one process."""
import ctypes
import json
import os
import traceback


def report(out):
    os.write(1, ("S6RESULT " + json.dumps(out) + "\n").encode())


here = os.path.dirname(os.path.abspath(__file__))
ctypes.CDLL(os.path.join(here, "..", "Frameworks", "S6Fixture.framework", "S6Fixture"))
try:
    import bench
    report(bench.run(os.environ["S6_LIB"], os.environ["S6_MODE"], os.environ.get("S6_ARG") or None))
except BaseException as e:
    traceback.print_exc()
    report({"error": "{}: {}".format(type(e).__name__, e)[:300]})
os._exit(0)
