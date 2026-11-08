"""X2 and X3: count each example's lines of Python and native code.

Usage: count.py OUT.json

Python is formatted with ruff first, then blank lines, comments, docstrings,
imports, the run() function and lines ending in "# measure" aren't counted.
run() is the test's entry point, and "# measure" marks a line that exists only
to record a result for the test, such as which thread a callback ran on.
Objective-C and Swift aren't reformatted. Blank lines, comments and import
lines aren't counted.
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import tokenize

RUFF = "ruff@0.6.9"
here = os.path.dirname(os.path.abspath(__file__))
examples = os.path.join(here, "..", "..", "examples", "section-04")
NATIVE = {"e3": {"pyobjus": ["e3_bridge.h", "e3_bridge.m"], "rubicon": []},
          "e4": {"pyobjus": ["e4_job.swift"], "rubicon": ["e4_async.swift"]}}


def formatted(path):
    src = open(path).read()
    return subprocess.run(["uvx", RUFF, "format", "-"], input=src, capture_output=True, text=True,
                          check=True).stdout


def python_lines(src):
    tree = ast.parse(src)
    skip = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            skip.update(range(node.lineno, node.end_lineno + 1))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            skip.update(range(node.lineno, node.end_lineno + 1))
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                skip.update(range(body[0].lineno, body[0].end_lineno + 1))
    code_lines = set()
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type not in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                            tokenize.DEDENT, tokenize.ENDMARKER):
            code_lines.update(range(tok.start[0], tok.end[0] + 1))
    lines = src.splitlines()
    counted = [n for n in sorted(code_lines - skip) if not lines[n - 1].rstrip().endswith("# measure")]
    return len(counted)


def native_lines(path):
    src = re.sub(r"/\*.*?\*/", "", open(path).read(), flags=re.S)
    n = 0
    for line in src.splitlines():
        s = line.strip()
        if not s or s.startswith("//") or s.startswith(("#import", "import ")):
            continue
        n += 1
    return n


def main():
    out = sys.argv[1]
    version = subprocess.run(["uvx", RUFF, "--version"], capture_output=True, text=True, check=True).stdout.strip()
    result = {"ruff": version, "examples": {}}
    for example in ("e1", "e2", "e3", "e4"):
        row = {}
        for lib in ("pyobjus", "rubicon"):
            path = os.path.join(examples, f"{example}_{lib}.py")
            native = NATIVE.get(example, {}).get(lib, [])
            row[lib] = {"python": python_lines(formatted(path)),
                        "native": {f: native_lines(os.path.join(examples, f)) for f in native}}
        result["examples"][example] = row
        print(example, row, flush=True)
    json.dump(result, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
