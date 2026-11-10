"""M2: Kivy and Plyer, file by file. What each file that uses pyobjus would change
to use Rubicon, from the M1 results.

Usage: inventory.py CLONES_DIR CATALOG.json M1_MAC.json M1_IPHONE.json OUT.json OUT.md [WINDOW.json]

WINDOW.json, from window/run_window.py, adds keyWindow and rootViewController,
which need an app with a window, read the same way as M1's names.

For every file catalog.py found using pyobjus in kivy/kivy and kivy/plyer,
each change below is found with a regular expression on the comment-stripped
source, and its line numbers at the pinned commit are kept. A zero-argument
call is classed by its name:

- "property in Rubicon": M1 found the name is a property in Rubicon and a
  method in pyobjus, on the Mac or the iPhone (zero_arg, zero_arg_ios), so
  the () goes. UTF8String() and count() have their own rows.
- "property in both": M1 found it's a property in pyobjus too, so its () would
  raise in either library.
- "method in both": M1 or m2_names found it's a method in both libraries.
- Python: called on self or super(), or one of PYTHON_NAMES, read by hand.
- Plyer's helper classes: declared as methods in kivy-ios's bridge.h or in
  Plyer's Voip.h (Source).
- Anything else is listed as not checked.
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog import strip_comments  # noqa: E402

REPOS = ("kivy/kivy", "kivy/plyer")

# Read by hand: Python methods, not Objective-C ones.
PYTHON_NAMES = {
    "strip": "str.strip", "keys": "dict.keys", "start": "threading.Thread.start",
    "run": "MacFileChooser.run, a Python class", "get_music_dir": "OSXStoragePath, a Python class",
}
# Declared as methods in the helper classes' headers (Source).
HELPER_METHODS = {
    "bridge": ["startAccelerometer", "stopAccelerometer", "startGyroscope", "stopGyroscope", "startMagnetometer",
               "stopMagnetometer", "startDeviceMotion", "startDeviceMotionWithReferenceFrame", "stopDeviceMotion",
               "startRelativeAltitude", "stopRelativeAltitude"],
    "Voip": ["requestMicrophonePermission", "receiveAudioData", "connected", "disconnect"],
}

# Read by hand: what the regular expressions can't see. (files, note)
HAND = [
    (["plyer/platforms/ios/accelerometer.py", "plyer/platforms/ios/barometer.py", "plyer/platforms/ios/compass.py",
      "plyer/platforms/ios/gravity.py", "plyer/platforms/ios/gyroscope.py", "plyer/platforms/ios/spatialorientation.py"],
     "Poll kivy-ios's template `bridge` class, which runs CoreMotion's block-based updates in Objective-C. Rubicon "
     "calls the `bridge` unchanged (M1 `app_class`), or can pass Python functions to CoreMotion directly, as Section 4 "
     "E3 does for the barometer. Its `ac_x` and similar values are properties in `bridge.h`."),
    (["plyer/platforms/ios/filechooser.py"],
     "Calls kivy-ios's `NativeImagePicker` for `UIImagePNGRepresentation`, a C function. Rubicon calls the class "
     "unchanged, or the function through `ctypes` (Section 3 F1.5). Plyer 2.1.0's `open_file()` raised "
     "`TypeError` on the iPhone, with pyobjus 1.2.4 and `master`, at `keyWindow.rootViewController()` (line 59): "
     "`rootViewController` is a property in both libraries, so the `()` raises in either, and the picker never "
     "opens (window test). Read without `()`, the picker opened in both libraries, with a Rubicon delegate in "
     "Rubicon. `load_framework` takes Photos' folder path, which Rubicon's `load_library` rejects with "
     "`ValueError`; `load_library(\"Photos\")` works."),
    (["plyer/platforms/ios/voip.py", "plyer/platforms/ios/frameworks/utils.py"],
     "Loads Plyer's bundled `Voip.framework` by its folder path. Rubicon's `load_library` rejects a framework "
     "folder path with `ValueError`, and loads the binary inside it, as the window test found for Photos; the "
     "bundled `Voip.framework` itself isn't tested. `self.error`, an `NSError` object, is passed to "
     "`setCategory_mode_options_error_` and `setActive_error_`, the form that crashed pyobjus when an error was "
     "written (M1 `nserror_out`)."),
    (["plyer/platforms/macosx/audio.py"],
     "Passes `NSError.alloc()` to `initWithURL_format_error_` and `initWithContentsOfURL_error_`, the form that "
     "crashed pyobjus when an error was written (M1 `nserror_out`)."),
    (["plyer/platforms/ios/flash.py"],
     "Writes `AVMediaTypeVideo` as `\"vide\"`. Rubicon can read the constant with `objc_const` (M1 `constant`)."),
    (["plyer/platforms/ios/gps.py", "plyer/platforms/macosx/gps.py"],
     "Parses latitude, longitude and accuracy out of `location.description` instead of reading the `coordinate` "
     "struct. Reading that struct in Rubicon isn't tested here; M1 read `frame` and `bounds` structs in both."),
    (["plyer/platforms/ios/uniqueid.py"],
     "Calls `identifierForVendor.UUIDString()`. M1 found `UUIDString` is a property in pyobjus 1.2.4, `master` and "
     "Rubicon, on an `NSUUID` from `NSUUID.UUID()` on the Mac and the iPhone, so the `()` would raise in either. "
     "`identifierForVendor` itself wasn't run."),
    (["kivy/core/audio_output/audio_avplayer.py"],
     "The `Sound` subclass is its own delegate. M1's `delegate` case is this code: in Rubicon the delegate becomes "
     "an `NSObject` subclass that the `Sound` keeps a reference to."),
    (["kivy/core/clipboard/clipboard_nspaste.py"],
     "Raises `SystemError` with a `pip install --user pyobjus` hint when the import fails, which names the library."),
]

# (id, what to change, regex, M1 case or source)
CHANGES = [
    ("autoclass", "autoclass(...) becomes ObjCClass(...)", r"\bautoclass\s*\(", "strings"),
    ("load_framework", "load_framework(...) becomes load_library(...)", r"\bload_framework\s*\(", "delegate"),
    ("utf8string", ".UTF8String() becomes str(...); in Rubicon UTF8String is a property giving bytes",
     r"\.UTF8String\s*\(\s*\)", "strings"),
    ("bytes_check", "a bytes check after UTF8String() is no longer needed with str(...)",
     r"isinstance\s*\(\s*[\w.]+\s*,\s*bytes\s*\)", "strings"),
    ("count", ".count() on an NSArray becomes len(...)", r"\.count\s*\(\s*\)", "property_call"),
    ("objc_str", "objc_str(x) becomes x", r"\bobjc_str\s*\(", "defaults"),
    ("objc_arr", "objc_arr(...) becomes a list", r"\bobjc_arr\s*\(", "collections"),
    ("init_utf8", "initWithUTF8String_(s) takes bytes, or pass the str directly",
     r"initWithUTF8String_\s*\(", "strings"),
    ("protocol", "a @protocol(...) method moves to an NSObject subclass with @objc_method",
     r"@\s*protocol\s*\(", "delegate"),
    ("delegate_self", "a Python object set as delegate becomes an instance of that subclass, kept alive by Python",
     r"\.delegate\s*=\s*self\b|\.setDelegate_\s*\(\s*self\s*\)", "delegate"),
    ("bool_return", "return ObjcBOOL(...) becomes a -> bool annotation", r"\bObjcBOOL\s*\(", "Section 3 F3.7"),
    ("error_alloc", "an NSError object passed for an NSError ** argument becomes byref(objc_id())",
     r"NSError['\"]?\)?\s*\.alloc\s*\(\s*\)", "nserror_out"),
    ("completion_nil", "None for a completion block still works; a Python function can now be passed",
     r"[cC]ompletion(?:Handler)?_\s*\(", "block"),
    ("property_or_method", "a try/except or callable() check for property versus method can go",
     r"\bcallable\s*\(|try:\s*\n[^\n]*\.(\w+)\(\)[^\n]*\n\s*except[^\n]*\n[^\n]*\.\1\b(?!\()", "search_path"),
    ("nsarray_index", "objectAtIndex_(i) loops can become indexing or iteration", r"\.objectAtIndex_\s*\(",
     "languages"),
]


def lines_of(code, pattern):
    return [code.count("\n", 0, m.start()) + 1 for m in re.finditer(pattern, code)]


def rubicon_properties(mac, iphone):
    """Names M1 found to be a property in Rubicon and a method in pyobjus, a method in both,
    or a property in both."""
    props, methods, both = set(), set(), set()
    for data, case in ((mac, "zero_arg"), (mac, "m2_names"), (iphone, "zero_arg_ios")):
        p = next(r["value"] for r in data["pyobjus-master"][case]["runs"] if r["outcome"] == "ran")
        q = next(r["value"] for r in data["rubicon-main"][case]["runs"] if r["outcome"] == "ran")
        for key, kind in q.items():
            name = key.split(".")[-1]
            if kind == "property" and p.get(key) == "method":
                props.add(name)
            elif kind == "method" and p.get(key) == "method":
                methods.add(name)
            elif kind == "property" and p.get(key) == "property":
                both.add(name)
    props.add("userInfo")  # the observer cases read it as a property in Rubicon
    return props, methods, both


def window_names(window, props, methods, both):
    """keyWindow and rootViewController from the window test, at the main versions."""
    p = next(r["value"] for r in window["main"]["pyobjus"]["runs"] if r["outcome"] == "ran")
    q = next(r["value"] for r in window["main"]["rubicon"]["runs"] if r["outcome"] == "ran")
    for name in ("keyWindow", "rootViewController"):
        kinds = (p.get(name), q.get(name))
        if kinds == ("property", "property"):
            both.add(name)
        elif kinds == ("method", "property"):
            props.add(name)
        elif kinds == ("method", "method"):
            methods.add(name)


def main():
    clones, catalog, mac, iphone, out_json, out_md = sys.argv[1:7]
    catalog, mac, iphone = json.load(open(catalog)), json.load(open(mac)), json.load(open(iphone))
    props, methods, both = rubicon_properties(mac, iphone)
    if len(sys.argv) > 7:
        window_names(json.load(open(sys.argv[7])), props, methods, both)
    methods |= {"alloc", "init", "new"}
    props.discard("UTF8String")
    helper = {n: cls for cls, names in HELPER_METHODS.items() for n in names}
    result = {"collected_at": catalog["collected_at"], "rubicon_properties": sorted(props), "files": []}
    for repo in catalog["repositories"]:
        if repo["repo"] not in REPOS:
            continue
        root = os.path.join(clones, repo["repo"].replace("/", "__"))
        for f in repo["files"]:
            code = strip_comments(open(os.path.join(root, f["path"]), encoding="utf-8").read())
            changes = {}
            for cid, _, pattern, _ in CHANGES:
                found = lines_of(code, pattern)
                if found:
                    changes[cid] = found
            zero = {"property in Rubicon": {}, "property in both": {}, "method in both": Counter(), "Python": Counter(),
                    "helper class method": Counter(), "not checked": {}}
            for m in re.finditer(r"([\w)\]]+)\.([A-Za-z]\w*)\(\s*\)", code):
                receiver, name = m.group(1), m.group(2)
                line = code.count("\n", 0, m.start()) + 1
                if name in ("UTF8String", "count"):
                    continue
                if name in props:
                    zero["property in Rubicon"].setdefault(name, []).append(line)
                elif name in both:
                    zero["property in both"].setdefault(name, []).append(line)
                elif receiver == "self" or receiver.endswith(")") and code[:m.start()].rstrip().endswith("super(") \
                        or re.search(r"super\([^)]*\)$", code[max(0, m.start() - 60):m.start() + len(receiver)]) \
                        or name in PYTHON_NAMES:
                    zero["Python"][name] += 1
                elif name in methods:
                    zero["method in both"][name] += 1
                elif name in helper:
                    zero["helper class method"][name] += 1
                else:
                    zero["not checked"].setdefault(name, []).append(line)
            platform = "macOS" if "/macosx/" in f["path"] or "clipboard_nspaste" in f["path"] else \
                "iOS and macOS" if "audio_avplayer" in f["path"] else "iOS"
            result["files"].append({
                "repo": repo["repo"], "path": f["path"], "commit": repo["commit"], "platform": platform,
                "pyobjus_calls": f["api_calls"], "selector_calls": f["selector_call_count"],
                "classes": f["classes"], "protocols": f["protocols"], "changes": changes,
                "zero_argument": {k: (dict(v) if isinstance(v, Counter) else v) for k, v in zero.items()},
                "helper_classes": [c for c in f["classes"] if c in ("bridge", "NativeImagePicker", "Voip")]})
    json.dump(result, open(out_json, "w"), indent=1)
    write_md(result, out_md)


def write_md(result, out_md):
    labels = {c[0]: c[1] for c in CHANGES}
    cases = {c[0]: c[3] for c in CHANGES}
    lines = ["# M2: Kivy and Plyer, file by file", "",
             "Generated by `tests/section-08/inventory.py` from `catalog.json`, `m1_mac.json` and `m1_iphone.json`."
             " Line numbers are at the pinned commits in `sample.json`, counted in the file with comments removed,"
             " so they match the file's own numbering. Method calls with arguments in pyobjus's flat form, such as"
             " `setObject_forKey_(...)`, need no change, as M1 found, and are only counted.", "",
             "## Changes, and the M1 case that shows each", "", "| ID | Change | M1 |", "|---|---|---|"]
    lines += [f"| `{c[0]}` | {c[1]} | `{c[3]}` |" for c in CHANGES]
    lines += ["| `property_parens` | a zero-argument call of a name Rubicon reads as a property loses its `()` |"
              " `zero_arg`, `zero_arg_ios` |",
              "| `property_both` | a zero-argument call of a name that's a property in pyobjus too, so its `()` would"
              " raise in either library | `zero_arg`, `zero_arg_ios` |", ""]
    for repo in REPOS:
        files = [f for f in result["files"] if f["repo"] == repo]
        lines += [f"## {repo}", "", "| File | Platform | pyobjus calls | Flat-form calls, unchanged | Changes |"
                  " Not checked |", "|---|---|---:|---:|---|---|"]
        for f in files:
            url = f"https://github.com/{repo}/blob/{f['commit']}/{f['path']}"
            parts = [f"`{cid}` {len(ln)} (line {', '.join(map(str, ln))})" for cid, ln in f["changes"].items()]
            pp = f["zero_argument"]["property in Rubicon"]
            if pp:
                parts.append("`property_parens` " + str(sum(len(v) for v in pp.values())) + " (" +
                             "; ".join(f"`{n}` line {', '.join(map(str, v))}" for n, v in pp.items()) + ")")
            if f["helper_classes"]:
                parts.append("helper class " + ", ".join(f"`{c}`" for c in f["helper_classes"]))
            pb = f["zero_argument"]["property in both"]
            if pb:
                parts.append("`property_both` " + "; ".join(f"`{n}()` line {', '.join(map(str, v))}" for n, v in pb.items()))
            nc = "; ".join(f"`{n}()` line {', '.join(map(str, v))}" for n, v in f["zero_argument"]["not checked"].items())
            lines.append(f"| [`{f['path']}`]({url}) | {f['platform']} | {sum(f['pyobjus_calls'].values())} |"
                         f" {f['selector_calls']} | {'<br>'.join(parts) or 'none'} | {nc or '-'} |")
        totals = Counter()
        for f in files:
            for cid, ln in f["changes"].items():
                totals[cid] += len(ln)
            totals["property_parens"] += sum(len(v) for v in f["zero_argument"]["property in Rubicon"].values())
        lines += ["", f"**Totals for {repo}:** {len(files)} files, "
                  f"{sum(sum(f['pyobjus_calls'].values()) for f in files)} pyobjus calls, "
                  f"{sum(f['selector_calls'] for f in files)} flat-form calls. Changes: " +
                  ", ".join(f"`{k}` {v}" for k, v in totals.most_common()) + ".", ""]
    lines += ["## Read by hand", ""]
    for paths, note in HAND:
        lines.append("- " + ", ".join(f"`{p}`" for p in paths) + ": " + note)
    open(out_md, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
