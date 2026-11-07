"""A1, A2 and A4: count the public Objective-C API in an SDK's headers.

Usage: headers.py SDK TARGET PLATFORM VERSION OUT.json [FRAMEWORK ...]

SDK is "macosx" or "iphoneos". TARGET is the clang target triple. PLATFORM is
the availability platform ("macos" or "ios") and VERSION the tested OS version,
such as 26.6.2. With no FRAMEWORK names, every framework in the SDK is read.

Each framework's umbrella header is parsed by Xcode's clang, which dumps its
syntax tree as text. The text dump is used because the JSON dump leaves out
availability details. Only declarations in that framework's own headers are
kept, so a framework included by another isn't counted twice.

For each declaration, the output lists the kinds of value its signature needs.
Mapping those kinds to what each library supports is a separate step.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

QUALIFIERS = re.compile(r"\b(_Nullable_result|_Nullable|_Nonnull|_Null_unspecified|__nullable|__nonnull|__strong|"
                        r"__weak|__autoreleasing|__unsafe_unretained|__kindof|const|volatile|restrict|__restrict)\b")
SCALARS = {"char", "signed char", "unsigned char", "short", "unsigned short", "int", "unsigned int", "long",
           "unsigned long", "long long", "unsigned long long", "float", "double", "long double", "bool", "_Bool",
           "__int128", "unsigned __int128", "_Float16", "__fp16", "wchar_t", "char16_t", "char32_t"}
OBJECT_WORDS = {"id", "Class", "instancetype"}
NODE = re.compile(r"^([| `-]*)(\w+) (0x[0-9a-f]+)?(.*)$")
PATH = re.compile(r"(/[^\s:,<>']+?\.(?:h|hpp|m|mm|inc|def)):\d+:\d+")
QUOTED = re.compile(r"'([^']*)'(?::'([^']*)')?")
AVAIL = re.compile(r"\b(macos|ios|maccatalyst|tvos|watchos|visionos|driverkit)\s+(\S+)\s+(\S+)\s+(\S+)\s*(Unavailable)?")


def framework_of(path):
    """The innermost framework whose headers hold this file."""
    m = re.findall(r"/([^/]+)\.framework/", path)
    return m[-1] if m else None


def version(v):
    return tuple(int(x) for x in v.split(".") if x.isdigit()) if v and v != "0" else ()


def clean(t):
    t = QUALIFIERS.sub("", t)
    return re.sub(r"\s+", " ", t).replace(" *", "*").replace("* ", "*").strip()


def resolve(t, typedefs):
    """Replace typedef names with what they stand for, keeping any pointer stars."""
    t = clean(t)
    for _ in range(12):
        base, stars = t.rstrip("*"), t[len(t.rstrip("*")):]
        head = re.sub(r"<.*>$", "", base).strip()
        if head in typedefs and head not in OBJECT_WORDS and head != "SEL":
            t = clean(typedefs[head]) + stars
        else:
            break
    return t


def classify(t, interfaces, complete, typedefs=None, params=()):
    """The kind of value a type needs, from its spelling with typedefs resolved."""
    t = resolve(t, typedefs or {})
    if "ext_vector_type" in t or "vector_size" in t:
        return "vector"  # a SIMD vector, such as simd_float3
    t = clean(re.sub(r"__attribute__\(\(.*?\)\)", "", t))
    if t in ("void", ""):
        return None
    if "(^" in t:
        return "block"
    if "(*" in t:
        # "R (*)(A)*" and "R (**)(A)" are pointers to a function pointer, such as
        # an out parameter.
        return "other_pointer" if re.search(r"\)\*+$", t) or "(**" in t else "function_pointer"
    if re.search(r"\)\*$", t):
        return "function_pointer"  # a function typedef, then one pointer
    if re.search(r"\)\*\*+$", t):
        return "other_pointer"
    if t.endswith("]"):
        return "c_array"
    if t == "SEL":
        return "selector"
    base, stars = t.rstrip("*"), len(t) - len(t.rstrip("*"))
    head = re.sub(r"<.*>$", "", base).strip()
    if head in params:
        head = "id"
    if head == "SEL":
        return "selector" if stars <= 1 else "other_pointer"  # SEL desugars to "SEL *"
    is_object = head in OBJECT_WORDS or head in interfaces
    if is_object:
        return {0: "object" if head in OBJECT_WORDS else "other", 1: "object", 2: "object_pointer"}.get(stars, "other_pointer")
    if base.startswith("struct "):
        name = base[7:]
        if stars == 0:
            return "struct"
        if stars == 1:
            return "struct_pointer" if name in complete else "opaque_pointer"
        return "other_pointer"
    if base.startswith("union "):
        return "union" if stars == 0 else "other_pointer"
    if base.startswith("enum ") or base in SCALARS:
        if stars == 0:
            return "scalar"
        if stars == 1:
            return "cstring" if base in ("char",) else "scalar_pointer"
        return "other_pointer"
    if base == "void":
        return "void_pointer" if stars == 1 else "other_pointer"
    return "other"


def type_of(rest):
    """The desugared type from the quoted part of a dump line."""
    m = QUOTED.search(rest)
    if not m:
        return ""
    return m.group(2) or m.group(1)


def parse(lines, keep, platform, tested):
    """Walk the text dump. Returns declarations, interfaces and complete structs."""
    current = None
    stack = []  # (depth, record)
    decls, interfaces, complete = [], set(), set()
    typedefs, params = {}, set()
    for line in lines:
        m = NODE.match(line)
        if not m:
            continue
        prefix, kind, addr, rest = m.groups()
        depth = len(prefix) // 2
        paths = PATH.findall(rest.split("'")[0])
        if paths:
            current = paths[-1]
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent = stack[-1][1] if stack else None
        rec = None
        here = current and framework_of(current) == keep
        if kind == "ObjCTypeParamDecl":
            params.add(rest.split("'")[0].split()[-1])
        if depth == 1 and kind == "TypedefDecl":
            name = rest.split("'")[0].split()[-1]
            m2 = QUOTED.search(rest)
            if m2:
                # An anonymous struct's typedef desugars to its own name, so the
                # sugared spelling ("struct NSDecimal") says what it is.
                value = m2.group(2) if m2.group(2) and m2.group(2) != name else m2.group(1)
                typedefs[name] = value
                if value in (f"struct {name}", f"union {name}") and m2.group(2) == name:
                    complete.add(name)
        if depth == 1:
            if kind == "ObjCInterfaceDecl":
                name = rest.split()[-1]
                interfaces.add(name)
                rec = {"container": "class", "owner": name, "here": here}
            elif kind == "ObjCCategoryDecl":
                rec = {"container": "category", "owner": None, "here": here}
            elif kind == "ObjCProtocolDecl":
                rec = {"container": "protocol", "owner": rest.split()[-1], "here": here}
            elif kind == "RecordDecl" and " definition" in rest:
                words = rest.replace(" definition", "").split()
                if len(words) >= 2 and words[-2] in ("struct", "union"):
                    complete.add(words[-1])
            elif kind == "FunctionDecl" and here and "implicit" not in rest.split("'")[0]:
                name = rest.split("'")[0].split()[-1]
                ftype = type_of(rest)
                rec = {"decl": "function", "owner": None, "name": name, "side": "call",
                       "inline": " inline" in rest.split("'")[-1], "variadic": "..." in ftype,
                       "ftype": ftype, "params": [], "avail": [], "unavailable": False, "deprecated": False}
                decls.append(rec)
            elif kind == "VarDecl" and here and " extern" in rest:
                name = rest.split("'")[0].split()[-1]
                rec = {"decl": "constant", "owner": None, "name": name, "side": "call", "types": [type_of(rest)], "params": [],
                       "avail": [], "unavailable": False, "deprecated": False}
                decls.append(rec)
        elif parent is not None and "container" in parent:
            if kind == "ObjCInterface" and parent["container"] == "category":
                parent["owner"] = QUOTED.search(rest).group(1)
            elif kind in ("ObjCMethodDecl", "ObjCPropertyDecl") and parent["here"] and parent["owner"]:
                head = rest.split("'")[0]
                if kind == "ObjCMethodDecl" and " implicit " in f" {head} ":
                    rec = {"skip": True}
                else:
                    words = head.split()
                    if kind == "ObjCMethodDecl":
                        name = words[-2] + words[-1]
                    else:
                        name = words[-1]
                    rec = {"decl": "method" if kind == "ObjCMethodDecl" else "property",
                           "owner": parent["owner"], "name": name,
                           "side": "implement" if parent["container"] == "protocol" else "call",
                           "variadic": " variadic" in rest, "types": [type_of(rest)], "params": [],
                           "avail": list(parent.get("avail", [])), "unavailable": parent.get("unavailable", False),
                           "deprecated": parent.get("deprecated", False), "own_avail": False}
                    decls.append(rec)
            elif kind == "AvailabilityAttr":
                parent.setdefault("avail", []).append(rest)
            elif kind == "UnavailableAttr":
                parent["unavailable"] = True
            elif kind == "DeprecatedAttr":
                parent["deprecated"] = True
        elif parent is not None and "decl" in parent:
            if kind == "ParmVarDecl":
                parent["params"].append(type_of(rest))
            elif kind == "AvailabilityAttr":
                if not parent.get("own_avail"):
                    parent["avail"] = []
                    parent["own_avail"] = True
                parent["avail"].append(rest)
            elif kind == "UnavailableAttr":
                parent["unavailable"] = True
            elif kind == "DeprecatedAttr":
                parent["deprecated"] = True
        if rec is not None:
            stack.append((depth, rec))
    return decls, interfaces, complete, typedefs, params


def available(rec, platform, tested):
    """Whether the tested system has this declaration, and whether it's deprecated."""
    if rec["unavailable"]:
        return False, rec["deprecated"]
    deprecated = rec["deprecated"]
    for a in rec["avail"]:
        m = AVAIL.search(a)
        if not m or m.group(1) != platform:
            continue
        introduced, dep, obsoleted, unavailable = m.group(2), m.group(3), m.group(4), m.group(5)
        if unavailable:
            return False, deprecated
        if version(introduced) > tested:
            return False, deprecated
        if version(obsoleted) and version(obsoleted) <= tested:
            return False, deprecated
        if version(dep) and version(dep) <= tested:
            deprecated = True
    return True, deprecated


def kinds_of(rec, interfaces, complete, typedefs, params):
    if rec["decl"] == "function":
        m = re.match(r"^(.*?)\s*\((.*)\)$", rec["ftype"])
        ret = m.group(1) if m else rec["ftype"]
        types = [ret] + rec["params"]
    else:
        types = rec["types"] + rec["params"]
    found = set()
    for i, t in enumerate(types):
        k = classify(t, interfaces, complete, typedefs, params)
        if k is None:
            continue
        if k == "block" and i == 0 and rec["decl"] != "constant":
            k = "block_return"
        found.add(k)
    if rec.get("variadic"):
        found.add("variadic")
    return sorted(found)


def frameworks(sdk_path):
    root = os.path.join(sdk_path, "System/Library/Frameworks")
    out = []
    for name in sorted(os.listdir(root)):
        if not name.endswith(".framework"):
            continue
        fw = name[:-10]
        headers = os.path.join(root, name, "Headers")
        has_headers = os.path.isdir(headers) and any(f.endswith(".h") for f in os.listdir(headers))
        modules = os.path.join(root, name, "Modules")
        has_swift = os.path.isdir(modules) and any(f.endswith(".swiftmodule") for f in os.listdir(modules))
        umbrella = os.path.join(headers, fw + ".h")
        out.append({"name": fw, "headers": has_headers, "swift": has_swift,
                    "umbrella": os.path.exists(umbrella)})
    return out


def dump(sdk, target, fw, headers=None):
    """Parse the umbrella header, or every top-level header if there's none."""
    with tempfile.NamedTemporaryFile("w", suffix=".m", delete=False) as f:
        if headers is None:
            f.write(f"#import <{fw}/{fw}.h>\n")
        else:
            f.write("".join(f"#import <{fw}/{h}>\n" for h in headers))
        src = f.name
    cmd = ["xcrun", "--sdk", sdk, "clang", "-target", target, "-fsyntax-only", "-fobjc-arc", "-fno-color-diagnostics",
           "-Wno-everything", "-Xclang", "-ast-dump", src]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    return p, src


def main():
    sdk, target, platform, tested, out, *only = sys.argv[1:]
    tested = version(tested)
    sdk_path = subprocess.run(["xcrun", "--sdk", sdk, "--show-sdk-path"], capture_output=True, text=True,
                              check=True).stdout.strip()
    sdk_version = subprocess.run(["xcrun", "--sdk", sdk, "--show-sdk-version"], capture_output=True, text=True,
                                 check=True).stdout.strip()
    clang = subprocess.run(["xcrun", "--sdk", sdk, "clang", "--version"], capture_output=True, text=True,
                           check=True).stdout.splitlines()[0]
    result = {"sdk": sdk, "sdk_version": sdk_version, "target": target, "platform": platform,
              "tested": ".".join(map(str, tested)), "clang": clang, "frameworks": {}}
    if os.path.exists(out):
        result["frameworks"] = json.load(open(out))["frameworks"]
    for fw in frameworks(sdk_path):
        name = fw["name"]
        if only and name not in only:
            continue
        if name in result["frameworks"]:
            continue
        entry = {"has_headers": fw["headers"], "has_swift_interface": fw["swift"], "umbrella": fw["umbrella"]}
        if fw["headers"]:
            listed = None
            if not fw["umbrella"]:
                hdir = os.path.join(sdk_path, "System/Library/Frameworks", name + ".framework", "Headers")
                listed = sorted(h for h in os.listdir(hdir) if h.endswith(".h"))
            p, src = dump(sdk, target, name, listed)
            decls, interfaces, complete, typedefs, params = parse(p.stdout, name, platform, tested)
            err = p.stderr.read()
            p.wait()
            os.unlink(src)
            entry["clang_exit"] = p.returncode
            if p.returncode:
                entry["clang_error"] = err[-500:]
            seen, records = set(), []
            for d in decls:
                key = (d["decl"], d["owner"], d["name"], d["side"])
                if key in seen:
                    continue
                seen.add(key)
                ok, deprecated = available(d, platform, tested)
                records.append({"decl": d["decl"], "owner": d["owner"], "name": d["name"], "side": d["side"],
                                "available": ok, "deprecated": deprecated, "inline": d.get("inline", False),
                                "kinds": kinds_of(d, interfaces, complete, typedefs, params)})
            entry["declarations"] = records
        result["frameworks"][name] = entry
        n = len(entry.get("declarations", []))
        print(f"{name}: {n} declarations", flush=True)
        json.dump(result, open(out, "w"))


if __name__ == "__main__":
    main()
