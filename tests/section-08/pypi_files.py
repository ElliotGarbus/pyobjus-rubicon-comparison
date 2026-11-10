"""B1: the files each library's latest release has on PyPI, and the wheels the
kivy-mobile-wheels index has for pyobjus.

Usage: pypi_files.py OUT.json

Reads PyPI's JSON API and the index's simple page. For each wheel: its
Python, ABI and platform tags, from the file name.
"""
import datetime
import json
import re
import sys
import urllib.request

INDEX = "https://elliotgarbus.github.io/kivy-mobile-wheels/simple/pyobjus/"


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()


def tags(filename):
    if not filename.endswith(".whl"):
        return None
    name, version, *rest = filename[:-4].split("-")
    python, abi, platform = rest[-3:]
    return {"python": python, "abi": abi, "platform": platform}


def main():
    out = {"collected_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "pypi": {}}
    for project in ("pyobjus", "rubicon-objc"):
        d = json.loads(get(f"https://pypi.org/pypi/{project}/json"))
        out["pypi"][project] = {
            "version": d["info"]["version"], "requires_python": d["info"]["requires_python"],
            "files": [{"filename": f["filename"], "type": f["packagetype"], "uploaded": f["upload_time_iso_8601"],
                       "size": f["size"], "sha256": f["digests"]["sha256"], "tags": tags(f["filename"])}
                      for f in d["urls"]]}
    names = sorted(set(re.findall(r"(pyobjus-[^\"#<>/]+\.whl)", get(INDEX))))
    out["kivy_mobile_wheels"] = {"url": INDEX, "files": [{"filename": n, "tags": tags(n)} for n in names]}
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    for project, d in out["pypi"].items():
        print(project, d["version"], len(d["files"]), "files")
    print("kivy-mobile-wheels pyobjus:", len(names), "wheels")


if __name__ == "__main__":
    main()
