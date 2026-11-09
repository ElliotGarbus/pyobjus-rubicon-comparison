"""S2 on the iPhone: what each library adds to the built test app.

Usage: app_size.py APP OUT.json

Counts every file the library puts in the app bundle: its Python package
under pip-deps, and for pyobjus the framework that holds its compiled
extension. Package metadata (.dist-info) isn't counted.
"""
import json
import os
import sys

PARTS = {"pyobjus": ["pip-deps/pyobjus", "Frameworks/pyobjus.pyobjus.framework"],
         "rubicon": ["pip-deps/rubicon"]}


def size(path):
    files = [os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs]
    return sum(os.path.getsize(f) for f in files), len(files)


def main():
    app, out = sys.argv[1:3]
    result = {"app_bytes": size(app)[0]}
    for lib, parts in PARTS.items():
        total, count = 0, 0
        for part in parts:
            b, n = size(os.path.join(app, part))
            total += b
            count += n
        result[lib] = {"bytes": total, "files": count, "parts": parts}
    json.dump(result, open(out, "w"), indent=1)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
