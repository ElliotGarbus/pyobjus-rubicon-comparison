"""M3: where each sampled repository declares, builds, links or documents pyobjus,
outside its code.

Usage: build_refs.py CLONES_DIR CATALOG.json OUT.json

For each repository: every line naming pyobjus in a file catalog.py listed
as a mention (not a using code file), and whether each package-metadata or
build file the repository has names pyobjus. Kinds are given by FILE_KINDS,
from the file's name and place, read by hand. Lines link to the pinned commit.
"""
import fnmatch
import json
import os
import sys

# Package metadata and build files: (glob on the path, kind).
METADATA = [("setup.py", "package metadata"), ("setup.cfg", "package metadata"),
            ("pyproject.toml", "package metadata"), ("requirements*.txt", "requirements"),
            ("*buildozer.spec", "buildozer spec"), ("Podfile", "CocoaPods"), ("*.github/workflows/*", "CI"),
            ("scripts/build_ios.sh", "build script")]

FILE_KINDS = [("*/recipes/*/__init__.py", "kivy-ios recipe"), ("tasks/*", "build script"),
              ("patches/*", "build patch"), ("ci/*", "CI"), ("*.pbxproj", "Xcode project"),
              ("*.m", "Objective-C source"), ("*tools/biglink", "build tool"), ("setup.py", "package metadata"),
              ("*.md", "docs"), ("*.rst", "docs")]


def kind_of(path):
    for pattern, kind in FILE_KINDS:
        if fnmatch.fnmatch(path, pattern):
            return kind
    return "other"


def main():
    clones, catalog, out = sys.argv[1:4]
    catalog = json.load(open(catalog))
    result = {"collected_at": catalog["collected_at"], "repositories": []}
    for repo in catalog["repositories"]:
        root = os.path.join(clones, repo["repo"].replace("/", "__"))
        mentions = []
        for rel in repo["mentions"]:
            lines = [i for i, line in enumerate(open(os.path.join(root, rel), encoding="utf-8", errors="replace"), 1)
                     if "pyobjus" in line.lower()]
            mentions.append({"path": rel, "kind": kind_of(rel), "lines": lines,
                             "url": f"https://github.com/{repo['repo']}/blob/{repo['commit']}/{rel}#L{lines[0]}"})
        metadata = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d != ".git")
            for f in sorted(filenames):
                rel = os.path.relpath(os.path.join(dirpath, f), root)
                for pattern, kind in METADATA:
                    if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f, pattern):
                        text = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
                        metadata.append({"path": rel, "kind": kind, "names_pyobjus": "pyobjus" in text.lower()})
                        break
        result["repositories"].append({"repo": repo["repo"], "commit": repo["commit"], "mentions": mentions,
                                       "metadata": metadata})
    json.dump(result, open(out, "w"), indent=1)
    for r in result["repositories"]:
        named = [m["path"] for m in r["metadata"] if m["names_pyobjus"]]
        print(f"{r['repo']}: {len(r['mentions'])} mentions, {len(r['metadata'])} metadata files, naming it: {named}")


if __name__ == "__main__":
    main()
