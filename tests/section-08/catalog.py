"""U1: where each sampled repository uses pyobjus, from its full checkout.

Usage: catalog.py CLONES_DIR SAMPLE.json OUT.json

SAMPLE.json lists each repository with the commit it was cloned at. Each clone
is in CLONES_DIR, named owner__repo. Every text file outside .git that names
pyobjus is listed. A code file (.py, .pyx, .rpy, .rpym) that imports pyobjus
is a "using" file, and its uses are counted from the source text, with
comments removed:

- pyobjus API calls: each call of a name imported from pyobjus or its
  submodules (autoclass, objc_str, load_framework and so on), each
  pyobjus.NAME(...) call, and each @protocol(...) decorator. When a file
  imports the same name from pyobjus and from another module, such as
  pyjnius's autoclass for Android, each call is credited to the import of
  that name that comes before it in the file. A name kept on the instance,
  as in self.objc_str = objc_str, is counted where self.objc_str(...) is
  called.
- Objective-C method calls in selector form: each call of an attribute whose
  name ends in one underscore, such as initWithString_(...). pyobjus spells a
  method with arguments this way. Calls of methods without arguments, such
  as .init(), and property reads and writes look like ordinary Python and
  aren't counted.
- The classes named in autoclass("..."), the frameworks named in
  load_framework(...), and the protocols named in @protocol("...").

Symbolic links are skipped. Files that name pyobjus without importing it (docs, recipes, build scripts,
Objective-C sources) are listed as mentions, for M3.
"""
import json
import os
import re
import sys

CODE = (".py", ".pyx", ".rpy", ".rpym")
IMPORT_ANY = re.compile(r"^\s*from\s+([\w.]+)\s+import\s+(\([^)]*\)|[^\n]+)", re.M)
IMPORT_MOD = re.compile(r"^\s*import\s+pyobjus\b", re.M)
STRING = r"""['"]([^'"]+)['"]"""


def strip_comments(text):
    out = []
    for line in text.split("\n"):
        # A '#' inside a string is rare in this code; strings with one are kept whole.
        code, quote = [], None
        for ch in line:
            if quote:
                code.append(ch)
                if ch == quote:
                    quote = None
            elif ch in "'\"":
                quote = ch
                code.append(ch)
            elif ch == "#":
                break
            else:
                code.append(ch)
        out.append("".join(code))
    return "\n".join(out)


def framework_name(arg):
    arg = arg.strip()
    m = re.match(r"INCLUDE\.(\w+)", arg)
    if m:
        return m.group(1)
    m = re.search(r"(\w+)\.framework", arg)
    if m:
        return m.group(1)
    return "(a path computed at run time)"


def analyse(text):
    code = strip_comments(text)
    # Every "from M import names", so that a name such as autoclass imported
    # from both pyobjus and pyjnius is credited to the import that precedes
    # each call.
    bindings = []
    for m in IMPORT_ANY.finditer(code):
        module, imported = m.group(1), m.group(2)
        for part in imported.strip("()").replace("\n", " ").replace("\\", " ").split(","):
            part = part.strip()
            if part:
                bindings.append((m.start(), part.split(" as ")[-1].strip(), module, part.split(" as ")[0].strip()))
    imports_module = bool(IMPORT_MOD.search(code))
    ours = [b for b in bindings if b[2] == "pyobjus" or b[2].startswith("pyobjus.")]
    if not ours and not imports_module:
        return None

    def owner(name, pos):
        before = [b for b in bindings if b[1] == name and b[0] < pos]
        return before[-1] if before else None

    api, classes, frameworks, protocols = {}, set(), set(), set()
    for name in sorted(set(b[1] for b in ours)):
        if name in ("INCLUDE", "protocols"):
            continue  # constants, counted with the calls that use them
        pattern = r"@\s*protocol\s*\(\s*(?:" + STRING + r")?" if name == "protocol" else \
            r"(?<![\w.])" + re.escape(name) + r"\s*\(\s*(?:" + STRING + r"|([^)]*))?"
        for m in re.finditer(pattern, code):
            b = owner(name, m.start())
            if not b or not (b[2] == "pyobjus" or b[2].startswith("pyobjus.")):
                continue
            full = b[2] + "." + b[3]
            api[full] = api.get(full, 0) + 1
            if name == "autoclass" and m.group(1):
                classes.add(m.group(1))
            elif name == "load_framework":
                frameworks.add(framework_name(m.group(1) or m.group(2) or ""))
            elif name == "protocol" and m.group(1):
                protocols.add(m.group(1))
        # A name kept on the instance, as in self.objc_str = objc_str, and called from there.
        if re.search(r"\bself\.%s\s*=\s*%s\b" % (re.escape(name), re.escape(name)), code):
            n = len(re.findall(r"\bself\.%s\s*\(" % re.escape(name), code))
            if n:
                b = [b for b in ours if b[1] == name][0]
                api[b[2] + "." + b[3]] = api.get(b[2] + "." + b[3], 0) + n
    for m in re.finditer(r"\bpyobjus\.(\w+)\s*\(\s*(?:" + STRING + r")?", code):
        api["pyobjus." + m.group(1)] = api.get("pyobjus." + m.group(1), 0) + 1
        if m.group(1) == "autoclass" and m.group(2):
            classes.add(m.group(2))
    selectors = {}
    for sel in re.findall(r"\.([A-Za-z]\w*[A-Za-z0-9]_)\s*\(", code):
        selectors[sel] = selectors.get(sel, 0) + 1
    registered = sorted(set(re.findall(r"protocols\s*\[\s*" + STRING + r"\s*\]\s*=", code)))
    return {"imports": sorted(set(b[2] + "." + b[3] for b in ours)) + (["pyobjus"] if imports_module else []),
            "api_calls": api, "api_call_count": sum(api.values()),
            "selector_calls": selectors, "selector_call_count": sum(selectors.values()),
            "alloc_calls": len(re.findall(r"\.alloc\s*\(\s*\)", code)),
            "classes": sorted(classes), "frameworks": sorted(frameworks), "protocols": sorted(protocols),
            "protocols_registered": registered}


def main():
    clones, sample, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
    result = {"collected_at": sample["collected_at"], "repositories": []}
    for repo in sample["repositories"]:
        root = os.path.join(clones, repo["repo"].replace("/", "__"))
        using, mentions = [], []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d != ".git")
            for f in sorted(filenames):
                path = os.path.join(dirpath, f)
                if os.path.islink(path):
                    continue  # counted where it points
                rel = os.path.relpath(path, root)
                try:
                    text = open(path, encoding="utf-8").read()
                except (UnicodeDecodeError, OSError):
                    continue
                if "pyobjus" not in text.lower():
                    continue
                info = analyse(text) if f.endswith(CODE) else None
                if info:
                    using.append(dict(path=rel, **info))
                else:
                    mentions.append(rel)
        result["repositories"].append({
            "repo": repo["repo"], "commit": repo["commit"], "stars": repo["stars"],
            "using_files": len(using), "api_calls": sum(u["api_call_count"] for u in using),
            "selector_calls": sum(u["selector_call_count"] for u in using),
            "classes": sorted(set(c for u in using for c in u["classes"])),
            "frameworks": sorted(set(c for u in using for c in u["frameworks"])),
            "protocols": sorted(set(c for u in using for c in u["protocols"])),
            "files": using, "mentions": mentions})
    json.dump(result, open(out, "w"), indent=1)
    for r in result["repositories"]:
        print("{repo}: {using_files} files, {api_calls} API calls, {selector_calls} selector calls, "
              "{n} classes, {m} mentions".format(n=len(r["classes"]), m=len(r["mentions"]), **r))


if __name__ == "__main__":
    main()
