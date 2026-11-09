"""Where Rubicon's import memory goes.

Usage: rubicon_import.py STEP

Run with a Rubicon environment's Python, once per step, each in a new
process. Rubicon's __init__.py imports importlib.metadata to read its own
version, and types.py calls platform.processor() when it loads. STEP is:

- metadata: importlib.metadata.version("rubicon-objc") alone
- processor: platform.processor() alone
- both_then_rubicon: both, then rubicon.objc, measured separately
- rubicon: rubicon.objc alone, as M1 measures it

Footprint and Python allocations are measured as in bench.py. Prints one
line, "S6RESULT " and JSON.
"""
import json
import os
import sys
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench  # noqa: E402


def measure(fn):
    bench.collect()
    modules = len(sys.modules)
    tracemalloc.start()
    footprint = bench.footprint()
    fn()
    bench.collect()
    result = {"footprint_bytes": bench.footprint() - footprint, "python_bytes": tracemalloc.get_traced_memory()[0],
              "modules": len(sys.modules) - modules}
    tracemalloc.stop()
    return result


def metadata():
    from importlib.metadata import version
    version("rubicon-objc")


def processor():
    import platform
    platform.processor()


def import_rubicon():
    from rubicon.objc import NSObject  # noqa: F401


def main():
    step = sys.argv[1]
    if step == "metadata":
        out = {"metadata": measure(metadata)}
    elif step == "processor":
        out = {"processor": measure(processor)}
    elif step == "both_then_rubicon":
        out = {"both": measure(lambda: (metadata(), processor())), "rubicon_after": measure(import_rubicon)}
    else:
        out = {"rubicon": measure(import_rubicon)}
    import rubicon.objc
    out.update(step=step, version=rubicon.objc.__version__, python=sys.version.split()[0])
    print("S6RESULT " + json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
