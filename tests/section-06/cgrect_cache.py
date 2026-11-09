"""Why pyobjus's CGRect calls slow down: its ctypes_struct_cache list.

Usage: cgrect_cache.py FIXTURE

Run with a pyobjus environment's Python. Every struct argument passed by
value appends its address to pyobjus's module-level ctypes_struct_cache, and
every struct return checks membership in it. This makes rounds of 1,000
echoRect: calls, recording the list's length and the time per call, then
clears the list and times another round. A separate pass measures Python's
allocations per call with tracemalloc, which slows calls, so its times
aren't used. Prints one line, "S6RESULT " and JSON.
"""
import ctypes
import json
import os
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROUND = 1000
ROUNDS = 20


def main():
    ctypes.CDLL(sys.argv[1])
    import bench
    import pyobjus
    import pyobjus.pyobjus as core
    ns, _ = bench.setup_pyobjus()
    t, rect = ns["t"], ns["rect"]
    cache = core.ctypes_struct_cache

    def round_us():
        t0 = time.perf_counter_ns()
        for _ in range(ROUND):
            t.echoRect_(rect)
        return (time.perf_counter_ns() - t0) / ROUND / 1000

    rounds = []
    for _ in range(ROUNDS):
        before = len(cache)
        us = round_us()
        rounds.append({"entries_before": before, "entries_after": len(cache), "us_per_call": round(us, 2)})
    entries = len(cache)
    cache.clear()
    after_clear = round_us()
    tracemalloc.start()
    start = tracemalloc.get_traced_memory()[0]
    round_us()
    python_bytes = (tracemalloc.get_traced_memory()[0] - start) / ROUND
    tracemalloc.stop()
    print("S6RESULT " + json.dumps({
        "pyobjus": pyobjus.__version__, "python": sys.version.split()[0], "round": ROUND,
        "rounds": rounds, "entries_before_clear": entries, "us_per_call_after_clear": round(after_clear, 2),
        "python_bytes_per_call": round(python_bytes, 1)}), flush=True)


if __name__ == "__main__":
    main()
