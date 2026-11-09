"""U2: use patterns across the sample, from catalog.py's list of using files.

Usage: patterns.py CLONES_DIR CATALOG.json REGIONS.json OUT.json IOS_SDK MACOS_SDK

Each pattern is a regular expression applied to the comment-stripped source
of every file catalog.py found using pyobjus. In a file that mixes pyobjus
code with code for other platforms, only the line ranges REGIONS.json gives
are searched, so that pyjnius calls and unrelated code aren't counted. For each pattern: the
repositories and files that use it, the number of matches (call sites), and
the first match as an example, with its line at the pinned commit.

Each class loaded with autoclass is looked up in the iOS and macOS SDK
headers. A class with no "@interface NAME" in either SDK isn't Apple's: the
app, a library it bundles, or the toolchain has to supply it.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from catalog import strip_comments  # noqa: E402

# (id, feature, pattern, what it matches)
PATTERNS = [
    ("load-class", "Classes", r"\bautoclass\s*\(", "autoclass(...) loads an Objective-C class"),
    ("load-framework", "Classes", r"\bload_framework\s*\(", "load_framework(...) loads a framework before its classes"),
    ("alloc-init", "Objects", r"\.alloc\s*\(\s*\)", ".alloc() then an init method creates an object"),
    ("selector-call", "Methods", r"\.[A-Za-z]\w*[A-Za-z0-9]_\s*\(",
     "a method with arguments, named in selector form with underscores, such as setObject_forKey_(...)"),
    ("property-or-method", "Methods",
     r"\bcallable\s*\(|try:\s*\n[^\n]*\.(\w+)\(\)[^\n]*\n\s*except[^\n]*\n[^\n]*\.\1\b(?!\()",
     "code that tries a name both as a property and as a method, because which one pyobjus returns varies"),
    ("objc-str", "Strings", r"\bobjc_str\s*\(", "objc_str(...) turns a Python str into an NSString"),
    ("utf8string", "Strings", r"\.UTF8String\s*\(\s*\)", ".UTF8String() turns an NSString into Python"),
    ("bytes-check", "Strings", r"isinstance\s*\(\s*[\w.]+\s*,\s*bytes\s*\)",
     "a check for bytes after converting a string, because UTF8String() can return either"),
    ("nsarray-index", "Collections", r"\.objectAtIndex_\s*\(", "objectAtIndex_(i) reads an NSArray element by element"),
    ("objc-arr", "Collections", r"\bobjc_arr\s*\(", "objc_arr(...) builds an NSArray"),
    ("python-container-arg", "Collections", r"_\s*\([^()]*(?:\{\}|\[\])[^()]*\)",
     "a Python {} or [] passed straight to a method"),
    ("delegate-self", "Delegates", r"\.delegate\s*=\s*self\b|\.setDelegate_\s*\(\s*self\s*\)",
     "a Python object set as an Objective-C object's delegate"),
    ("observer-self", "Delegates", r"addObserver_selector_name_object_\s*\(\s*self\b",
     "a Python object registered with NSNotificationCenter"),
    ("protocol-method", "Delegates", r"@\s*protocol\s*\(", "@protocol(...) marks a method that Objective-C calls back"),
    ("protocol-register", "Delegates", r"\bprotocols\s*\[[^\]]+\]\s*=",
     "a protocol's method signatures written out by hand, for a protocol pyobjus doesn't know"),
    ("selector", "Delegates", r"\bselector\s*\(", "selector(...) names a method for a target-action API"),
    ("bool-return", "Delegates", r"\bObjcBOOL\s*\(", "ObjcBOOL(...) returns a BOOL from a callback"),
    ("completion-nil", "Blocks", r"[cC]ompletion(?:Handler)?_\s*\(",
     "a method that takes a completion block, called with None because pyobjus can't create blocks"),
    ("error-arg", "Errors", r"[eE]rror_\s*\(", "a method with an NSError ** argument"),
    ("struct-field", "Structs", r"\.(?:origin|size)\s*\.\s*(?:x|y|width|height)\b|CGRectValue\s*\(",
     "a field of a returned struct, such as frame.size.width"),
    ("enum", "Constants", r"\benum\s*\(", "pyobjus's enum(...) declares enum values by hand"),
    ("retain-release", "Memory", r"\.(?:retain|release|retainCount|autorelease)\s*\(\s*\)",
     "reference counts managed by hand"),
    ("raw-pointer", "Memory", r"\.arg_ref\b|\bcast\s*\([^)]*POINTER", "a raw pointer read or passed through ctypes"),
]


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def sdk_classes(sdk):
    found = {}
    for header in glob.glob(os.path.join(sdk, "System/Library/Frameworks/*.framework/Headers/*.h")):
        framework = header.split("/")[-3][:-len(".framework")]
        try:
            text = open(header, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for name in re.findall(r"@interface\s+(\w+)\s*[:(<\n{]", text):
            found.setdefault(name, framework)
    return found


def main():
    clones, catalog, regions, out, ios_sdk, mac_sdk = sys.argv[1:7]
    catalog = json.load(open(catalog))
    regions = json.load(open(regions))["regions"]
    rows = {p[0]: {"id": p[0], "feature": p[1], "description": p[3], "repositories": {}, "matches": 0,
                   "example": None} for p in PATTERNS}
    for repo in catalog["repositories"]:
        root = os.path.join(clones, repo["repo"].replace("/", "__"))
        for f in repo["files"]:
            code = strip_comments(open(os.path.join(root, f["path"]), encoding="utf-8").read())
            ranges = regions.get(repo["repo"], {}).get(f["path"])
            if ranges:
                # Blank the lines outside the ranges, keeping line numbers.
                lines = code.split("\n")
                keep = set(n for a, b, _ in ranges for n in range(a, b + 1))
                code = "\n".join(l if i + 1 in keep else "" for i, l in enumerate(lines))
            # The API patterns must agree with catalog.py, which credits each call to its import.
            for pid, name in (("load-class", "pyobjus.autoclass"), ("objc-str", "pyobjus.objc_str"),
                              ("protocol-method", "pyobjus.protocol")):
                pattern = [p[2] for p in PATTERNS if p[0] == pid][0]
                assert len(re.findall(pattern, code)) == f["api_calls"].get(name, 0), (f["path"], pid)
            for pid, _, pattern, _ in PATTERNS:
                found = list(re.finditer(pattern, code))
                if not found:
                    continue
                row = rows[pid]
                row["repositories"].setdefault(repo["repo"], []).append({"path": f["path"], "matches": len(found)})
                row["matches"] += len(found)
                if row["example"] is None:
                    row["example"] = {"repo": repo["repo"], "commit": repo["commit"], "path": f["path"],
                                      "line": line_of(code, found[0].start())}
    ios, mac = sdk_classes(ios_sdk), sdk_classes(mac_sdk)
    classes = {}
    for repo in catalog["repositories"]:
        for f in repo["files"]:
            for c in f["classes"]:
                entry = classes.setdefault(c, {"class": c, "ios_sdk": ios.get(c), "macos_sdk": mac.get(c),
                                               "repositories": {}})
                entry["repositories"].setdefault(repo["repo"], []).append(f["path"])
    result = {"collected_at": catalog["collected_at"],
              "sdks": {"ios": os.path.basename(ios_sdk), "macos": os.path.basename(mac_sdk)},
              "patterns": [dict(r, repository_count=len(r["repositories"]),
                                file_count=sum(len(v) for v in r["repositories"].values())) for r in rows.values()],
              "classes": sorted(classes.values(), key=lambda c: c["class"].lower())}
    json.dump(result, open(out, "w"), indent=1)
    for r in result["patterns"]:
        print("{id:22} {repository_count:2} repos {file_count:3} files {matches:4} matches".format(**r))
    for c in result["classes"]:
        if not c["ios_sdk"] and not c["macos_sdk"]:
            print("not in either SDK:", c["class"], sorted(c["repositories"]))


if __name__ == "__main__":
    main()
