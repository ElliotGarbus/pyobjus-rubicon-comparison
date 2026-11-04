"""Select the T5 sample from the BridgeSupport files shipped with macOS.
Usage: t5_select.py OUT.json"""
import json
import random
import sys
import xml.etree.ElementTree as ET

SEED = 20261104
FRAMEWORKS = ["Foundation", "AppKit", "CoreBluetooth", "CoreLocation", "UserNotifications"]
KINDS = ["struct", "block", "out", "function"]
PER_KIND = 20


def kind_of(arg):
    ty = arg.get("type64") or arg.get("type") or ""
    if ty.startswith("{"):
        return "struct"
    if ty.lstrip("rnNoORV").startswith("@?"):
        return "block"
    if arg.get("function_pointer") == "true" or ty.startswith("^?"):
        return "function"
    if arg.get("type_modifier") in ("o", "N"):
        return "out"
    return None


rng = random.Random(SEED)
sample = []
totals = {}
for fw in FRAMEWORKS:
    path = f"/System/Library/Frameworks/{fw}.framework/Resources/BridgeSupport/{fw}.bridgesupport"
    root = ET.parse(path).getroot()
    found = {k: [] for k in KINDS}
    for cl in root.findall("class"):
        for m in cl.findall("method"):
            seen = set()
            for a in m.findall("arg") + m.findall("retval"):
                k = kind_of(a)
                if k and k not in seen:
                    seen.add(k)
                    found[k].append({"framework": fw, "kind": k, "class": cl.get("name"),
                                     "selector": m.get("selector"),
                                     "class_method": m.get("class_method") == "true",
                                     "type": a.get("type64") or a.get("type") or "",
                                     "is_return": a.tag == "retval",
                                     "index": a.get("index")})
    totals[fw] = {k: len(v) for k, v in found.items()}
    for k in KINDS:
        rows = sorted(found[k], key=lambda e: (e["class"], e["selector"]))
        sample += rng.sample(rows, min(PER_KIND, len(rows)))
json.dump({"seed": SEED, "per_kind": PER_KIND, "totals": totals, "sample": sample}, open(sys.argv[1], "w"), indent=1)
print(totals, len(sample))
