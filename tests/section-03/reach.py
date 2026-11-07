"""A1 and A2: how much of an SDK's API each library can express.

Usage: reach.py HEADERS.json S3_RESULTS.json S2_RESULTS.json OUT.json

Each kind of value a declaration needs is matched to measured cases from
Section 3 and, for kinds Section 2 already tested, Section 2. A kind is
supported for a library only if every case mapped to it was correct in all
runs. A declaration is expressible only if all its kinds are supported. A kind
with no measured case leaves the declaration unclassified.

Two kinds are ambiguous in a header. A pointer to a scalar can be one value or
an array, and a variadic method can take objects or numbers. Each has a lenient
case (one value, objects) and a strict one (an array, a number), so the result
is a range.
"""
import json
import sys

# kind: (strict cases, lenient cases). "s2:" marks a Section 2 scenario.
CALL = {
    "object": (["f1_1_class_method"],) * 2,
    "scalar": (["s2:t2_int", "s2:t2_float", "s2:t2_bool"],) * 2,
    "selector": (["f3_6_notification"],) * 2,
    "cstring": (["s2:t2_bytes"],) * 2,
    "void_pointer": (["s2:t2_pointer"],) * 2,
    "opaque_pointer": (["f2_4_opaque_pointer"],) * 2,
    "scalar_pointer": (["f2_4_scalar_out", "f2_3_pass_array", "f2_3_fill_array"], ["f2_4_scalar_out"]),
    "struct_pointer": (["f2_1_struct_pointer_in", "f2_1_struct_pointer_out"],) * 2,
    "object_pointer": (["f2_4_error_out"],) * 2,
    "struct": (["s2:t3_rect", "s2:t3_range", "s2:t3_insets", "s2:t3_nested", "f2_1_user_struct"],) * 2,
    "union": (["f2_2_union_arg", "f2_2_union_return"],) * 2,
    "c_array": (["f2_3_fixed_array"],) * 2,
    "block": (["f4_1_completion"],) * 2,
    "block_return": (["s2:cb5b_receive_int", "s2:cb5b_receive_object"],) * 2,
    "function_pointer": (["f4_4_sort_function"],) * 2,
    "variadic": (["f1_3_format", "f1_3_array_with_objects"], ["f1_3_array_with_objects"]),
    "c_function": (["f1_5_function"],) * 2,
    "object_constant": (["f1_4_object_constant"],) * 2,
    "scalar_constant": (["f1_4_scalar_constant"],) * 2,
    "inline": ([None],) * 2,  # no symbol to call
}
IMPLEMENT = {
    "object": (["f3_4_apple_protocol", "f3_7_object_return"],) * 2,
    "scalar": (["f3_5_app_protocol", "f3_7_bool_return"],) * 2,
    "struct": (["s2:cb2_delegate_rect"],) * 2,
    "union": (["f3_7_union_arg"],) * 2,
    "scalar_pointer": (["f3_7_array_arg"],) * 2,
    "c_array": (["f3_7_array_arg"],) * 2,
    "block": (["f4_2_delegate_completion"],) * 2,
}
FRAMEWORKS = {
    "macos": ["Foundation", "AppKit", "AVFoundation", "CoreBluetooth", "CoreLocation", "StoreKit", "UserNotifications"],
    "ios": ["UIKit", "Foundation", "AVFoundation", "CoreBluetooth", "CoreLocation", "Photos", "StoreKit",
            "UserNotifications"],
}


def passed(label, case, s3, s2):
    if case is None:
        return False
    if case.startswith("s2:"):
        r = s2.get(label, {}).get(case[3:])
        return bool(r) and r["summary"] == {"ok": sum(r["summary"].values())}
    r = s3.get(label, {}).get(case)
    return bool(r) and list(r["summary"]) == ["correct"]


def kinds(decl):
    ks = list(decl["kinds"])
    if decl["decl"] == "function":
        ks.append("inline" if decl["inline"] else "c_function")
    elif decl["decl"] == "constant":
        # A CF constant, such as a CFStringRef, is read the same way as an
        # object constant. A struct constant is read like a scalar one.
        main = {("object",): "object", ("opaque_pointer",): "object", ("scalar",): "scalar",
                ("struct",): "scalar"}.get(tuple(ks))
        ks = [f"{main}_constant"] if main else ks + ["unclassified_constant"]
    return ks


def verdict(decl, label, s3, s2, which):
    table = IMPLEMENT if decl["side"] == "implement" else CALL
    blocked = []
    for k in kinds(decl):
        if k not in table:
            return "unclassified", k
        if not all(passed(label, c, s3, s2) for c in table[k][which]):
            blocked.append(k)
    return ("expressible", None) if not blocked else ("not expressible", sorted(blocked)[0])


def tally(decls, label, s3, s2):
    out = {}
    for side in ("call", "implement"):
        ds = [d for d in decls if d["side"] == side and d["available"]]
        row = {"available": len(ds), "deprecated": sum(d["deprecated"] for d in ds), "by_decl": {}}
        for decl in ("method", "property", "function", "constant"):
            sub = [d for d in ds if d["decl"] == decl]
            if not sub:
                continue
            c = {}
            for d in sub:
                for which, name in ((0, "strict"), (1, "lenient")):
                    v = verdict(d, label, s3, s2, which)[0]
                    c.setdefault(name, {})
                    c[name][v] = c[name].get(v, 0) + 1
            row["by_decl"][decl] = {"available": len(sub), **c}
        for which, name in ((0, "strict"), (1, "lenient")):
            counts, first = {}, {}
            for d in ds:
                v, k = verdict(d, label, s3, s2, which)
                counts[v] = counts.get(v, 0) + 1
                if k:
                    first.setdefault(v, {})
                    first[v][k] = first[v].get(k, 0) + 1
            row[name] = {"counts": counts, "by_kind": first}
        out[side] = row
    return out


def main():
    headers, s3_path, s2_path, out = sys.argv[1:]
    h = json.load(open(headers))
    s3, s2 = json.load(open(s3_path)), json.load(open(s2_path))
    labels = [l for l in s3 if l in s2 or l.startswith("pyobjc")]
    # A framework clang couldn't parse is left out of the totals and listed.
    failed = sorted(n for n, e in h["frameworks"].items() if e.get("clang_exit"))
    every = [d for n, e in h["frameworks"].items() if n not in failed for d in e.get("declarations", [])]
    result = {"sdk": h["sdk"], "sdk_version": h["sdk_version"], "tested": h["tested"], "clang": h["clang"],
              "left_out_parse_failed": failed, "labels": {}}
    for label in labels:
        per = {"total": tally(every, label, s3, s2), "frameworks": {}}
        for fw in FRAMEWORKS[h["platform"]]:
            per["frameworks"][fw] = tally(h["frameworks"][fw].get("declarations", []), label, s3, s2)
        result["labels"][label] = per
    fws = h["frameworks"]
    result["swift_only_frameworks"] = sorted(n for n, e in fws.items() if e["has_swift_interface"] and not e["has_headers"])
    result["swift_and_objc_frameworks"] = sorted(n for n, e in fws.items() if e["has_swift_interface"] and e["has_headers"])
    result["objc_only_frameworks"] = sorted(n for n, e in fws.items() if e["has_headers"] and not e["has_swift_interface"])
    json.dump(result, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
