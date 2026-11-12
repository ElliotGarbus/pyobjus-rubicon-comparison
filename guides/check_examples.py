"""Run the guide's marked examples and compare their output with the guide.

Usage: check_examples.py GUIDE.md pyobjus=PYTHON rubicon=PYTHON

Each code block preceded by `<!-- run: LIB -->` is run in its own process
with that library's Python, in an empty temporary directory, with `-I`. Its
standard output must equal the block's `# Prints:` comments, in order.
"""
import re
import subprocess
import sys
import tempfile

BLOCK = re.compile(r"<!-- run: (\w+) -->\n```python\n(.*?)```", re.S)


def main():
    guide = open(sys.argv[1], encoding="utf-8").read()
    pythons = dict(arg.split("=", 1) for arg in sys.argv[2:])
    failures = 0
    for n, match in enumerate(BLOCK.finditer(guide), 1):
        lib, code = match.groups()
        line = guide[:match.start()].count("\n") + 1
        expected = [m.strip() for m in re.findall(r"^# Prints: (.*)$", code, re.M)]
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run([pythons[lib], "-I", "-c", code], cwd=tmp, capture_output=True,
                                 text=True, timeout=60)
        got = run.stdout.strip().splitlines()
        ok = run.returncode == 0 and got == expected
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'} block {n} (line {line}, {lib})")
        if not ok:
            print("  expected:", expected)
            print("  got:     ", got, "exit", run.returncode)
            print("  stderr:  ", run.stderr.strip()[-600:])
    print(f"{failures} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
