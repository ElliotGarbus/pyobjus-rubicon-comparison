"""Pack a pyobjus source tree and one compiled extension into an iOS wheel.
Usage: pack_wheel.py SRC VERSION SDK OUT"""
import base64
import hashlib
import os
import sys
import zipfile

src, version, sdk, out = sys.argv[1:]
tag = f"cp315-cp315-ios_13_0_arm64_{sdk}"
info = f"pyobjus-{version}.dist-info"
files = {}
for root, dirs, names in os.walk(os.path.join(src, "pyobjus")):
    for n in names:
        if n.endswith(".py") or n.endswith(f"-{sdk}.so"):
            path = os.path.join(root, n)
            files[os.path.relpath(path, src)] = open(path, "rb").read()
files[f"{info}/METADATA"] = f"Metadata-Version: 2.1\nName: pyobjus\nVersion: {version}\n".encode()
files[f"{info}/WHEEL"] = (f"Wheel-Version: 1.0\nGenerator: pack_wheel\nRoot-Is-Purelib: false\nTag: {tag}\n").encode()
files[f"{info}/licenses/LICENSE"] = open(os.path.join(src, "LICENSE"), "rb").read()


def record(data):
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    return f"sha256={digest},{len(data)}"


lines = [f"{name},{record(data)}" for name, data in files.items()] + [f"{info}/RECORD,,"]
files[f"{info}/RECORD"] = ("\n".join(lines) + "\n").encode()
with zipfile.ZipFile(os.path.join(out, f"pyobjus-{version}-{tag}.whl"), "w", zipfile.ZIP_DEFLATED) as z:
    for name in sorted(files):
        z.writestr(name, files[name])
