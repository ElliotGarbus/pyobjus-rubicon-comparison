"""Run one example in this process and print one JSON line.
Usage: run_one.py EXAMPLE LIB"""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
sys.path.insert(0, os.path.join(here, "..", "..", "examples", "section-04"))
from harness import run

result = run(sys.argv[1], sys.argv[2])
print("S4RESULT " + json.dumps(result), flush=True)
os._exit(0)
