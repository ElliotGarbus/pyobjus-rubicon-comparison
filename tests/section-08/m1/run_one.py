"""Run one M1 case in this process and print its result as one JSON line.
Usage: run_one.py LIB CASE"""
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

lib, case = sys.argv[1:3]
try:
    module = __import__("cases_" + lib)
    result = {"outcome": "ran", "value": module.CASES[case]()}
except Exception as e:
    result = {"outcome": "raised", "value": type(e).__name__ + ": " + str(e)[:300],
              "traceback": traceback.format_exc()[-1500:]}
print("S8RESULT " + json.dumps(result, default=repr), flush=True)
