"""A3: compare the kinds headers.py assigns with BridgeSupport's annotations.

Usage: crosscheck.py HEADERS_MAC.json OUT.json

For every method and function that both the macOS headers and Apple's
BridgeSupport files describe, four annotations are checked: a block argument or
return value, a function pointer, an out parameter and a variadic signature.
Each disagreement is listed for review.
"""
import glob
import json
import sys
import xml.etree.ElementTree as ET

CHECKS = ("block", "function_pointer", "out_parameter", "variadic")
POINTERS = {"object_pointer", "scalar_pointer", "struct_pointer", "opaque_pointer", "void_pointer", "cstring",
            "other_pointer", "c_array"}


def bridgesupport_kinds(node):
    """The kinds BridgeSupport's annotations say a method or function needs."""
    found = set()
    if node.get("variadic") == "true":
        found.add("variadic")
    for arg in node.findall("arg") + node.findall("retval"):
        t = arg.get("type64") or arg.get("type") or ""
        if arg.get("function_pointer") == "true" or arg.find("arg") is not None:
            found.add("block" if t == "@?" else "function_pointer")
        elif t == "@?":
            found.add("block")
        elif arg.get("type_modifier") == "o" and arg.tag == "arg":
            found.add("out_parameter")
    return found


def main():
    headers, out = sys.argv[1:]
    h = json.load(open(headers))
    ours = {}
    for fw, e in h["frameworks"].items():
        for d in e.get("declarations", []):
            if d["decl"] in ("method", "function"):
                name = d["name"].lstrip("+-") if d["decl"] == "method" else d["name"]
                ours[(fw, d["owner"], name)] = set(d["kinds"])
    compared, disagree = 0, []
    for path in sorted(glob.glob("/System/Library/Frameworks/*.framework/Resources/BridgeSupport/*.bridgesupport")):
        fw = path.split("/")[4][:-10]
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        entries = [(c.get("name"), m.get("selector"), m) for c in root.iter("class") for m in c.findall("method")]
        entries += [(None, f.get("name"), f) for f in root.iter("function")]
        for owner, name, node in entries:
            key = (fw, owner, name)
            if key not in ours:
                continue
            theirs = bridgesupport_kinds(node)
            # BridgeSupport marks only some out parameters and often leaves out
            # their type, so an out parameter is compared one way: marked there
            # means some pointer kind here.
            mine = set(ours[key])
            if mine & POINTERS:
                mine.add("out_parameter")
            compared += 1
            for k in CHECKS:
                if k == "out_parameter":
                    if k in theirs and k not in mine:
                        disagree.append({"framework": fw, "owner": owner, "name": name, "kind": k,
                                         "bridgesupport": True, "headers": False})
                elif (k in theirs) != (k in mine):
                    disagree.append({"framework": fw, "owner": owner, "name": name, "kind": k,
                                     "bridgesupport": k in theirs, "headers": k in mine})
    by_kind = {}
    for d in disagree:
        by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
    json.dump({"compared": compared, "disagreements": len(disagree), "by_kind": by_kind, "list": disagree},
              open(out, "w"), indent=1)
    print(compared, "compared,", len(disagree), "disagreements", by_kind)


if __name__ == "__main__":
    main()
