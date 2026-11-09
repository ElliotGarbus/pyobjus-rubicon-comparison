"""E1: apply the exclusions to code_search.py's matches and count repositories.

Usage: summarize.py CODE_SEARCH.json OUT.json [HEADERS.json]

A repository is left out if it's pyobjus or Rubicon, or a fork of pyobjus,
Rubicon, Plyer or Toga. Plyer and Toga count like any other repository that
imports the library, as Kivy does. A match is left out if it's in a copied or
generated folder, or in a copy of one of those four projects inside another
repository.

Copies of other projects that import the library, such as Ren'Py's engine
or Kivy's own modules carried inside an app, are found by path: a file whose
last two path parts (three, when the folder has a common name such as src or
game) also appear in another repository counts only for the repository with
the most stars, and the others are copies. Then a file in a copying
repository counts as part of the copy if it sits under the copy's root and a
repository with more stars has a file at the same relative path. A file with
an uncommon name counts as a copy if a repository with more stars has a
top-level file of that name, such as Ren'Py's launcher, renpy.py.

With HEADERS.json from fetch_headers.py, a file that opens with another
project's license header or module docstring counts as a copy of that
project, outside that project's own GitHub organization. This catches
Ren'Py's launcher, which Ren'Py renames after each game. Every
exclusion is kept with its reason. For each library: distinct repositories
with at least one counted match, how many were pushed to between the start of
the 24 months before the baseline and the search, and the 10 with the most
stars.
"""
import json
import sys

BASELINE = "2026-11-04T14:10:39Z"
WINDOW_START = "2024-11-04T14:10:39Z"
LIBRARIES = {"kivy/pyobjus", "beeware/rubicon-objc"}
PROJECTS = LIBRARIES | {"kivy/plyer", "beeware/toga"}  # forks of these are copies
PROJECT_NAMES = {"pyobjus", "rubicon-objc", "plyer", "toga"}
GENERATED = {"site-packages", "dist-packages", ".buildozer", "venv", ".venv", "virtualenv", "build", "dist",
             "__pycache__", ".tox"}


def excluded_repo(name, details):
    if name in LIBRARIES:
        return "the project itself"
    if details.get("fork") and (details.get("parent") in PROJECTS
                                or name.split("/", 1)[1].lower() in PROJECT_NAMES):
        return "fork of " + (details.get("parent") or name.split("/", 1)[1])
    return None


# Plyer's iOS and macOS implementations, by file name.
PLYER_FILES = {"accelerometer", "barometer", "battery", "call", "camera", "compass", "email", "filechooser",
               "flash", "gps", "gravity", "gyroscope", "keystore", "sms", "spatialorientation", "storagepath", "tts",
               "uniqueid", "vibrator", "audio", "bluetooth", "cpu", "devicename", "notification", "screenshot",
               "wifi"}


def excluded_path(path, repo=""):
    parts = [p.lower() for p in path.split("/")]
    dirs = parts[:-1]
    for d in dirs:
        if d in GENERATED or d.startswith("python3.") or d.startswith("lib-python"):
            return "copied or generated folder: " + d
    for i, d in enumerate(dirs):
        nxt = dirs[i + 1] if i + 1 < len(dirs) else parts[-1]
        if d == "pyobjus" and (nxt in ("consts", "__init__.py", "dylib_manager.py", "objc_py_types.py",
                                       "protocols.py") or i + 1 < len(dirs) and dirs[i + 1] == "pyobjus"):
            return "copy of pyobjus"
        if repo == "kivy/plyer" and d in ("plyer", "platforms"):
            continue  # Plyer's own code
        if repo == "beeware/toga" and d.startswith("toga_"):
            continue  # Toga's own code
        if d == "plyer" and nxt in ("platforms", "facades", "tools", "utils.py", "__init__.py"):
            return "copy of Plyer"
        if d == "platforms" and nxt in ("ios", "macosx") and parts[-1][:-3] in PLYER_FILES:
            return "copy of Plyer"
        if d == "renpy" and nxt in ("audio", "display", "translation", "exports", "bootstrap.py", "main.py") \
                and not repo.startswith("renpy/"):
            return "copy of Ren'Py"
        if d.startswith("rubicon-objc") or d.startswith("rubicon_objc"):
            return "copy of Rubicon"
        if d == "rubicon" and nxt == "objc":
            return "copy of Rubicon"
        if d in TOGA_PACKAGES:
            return "copy of Toga"
        if d == "pyobjus-examples":
            return "copy of pyobjus"
    return None


# Toga's own packages. Other toga_ folders, such as toga_console, are separate projects.
TOGA_PACKAGES = {"toga_cocoa", "toga_ios", "toga_core", "toga_dummy", "toga_gtk", "toga_winforms", "toga_android",
                 "toga_web", "toga_textual", "toga_qt"}


GENERIC_DIRS = {"src", "app", "game", "base", "lib", "code", "scripts", "source", "main", "tests", "test",
                "python", "ios", "macos", "osx", "mac", "platforms", "examples", "example", "demo", "demos", "utils", "core"}


GENERIC_FILES = {"main.py", "__init__.py", "__main__.py", "app.py", "setup.py", "test.py", "tests.py", "utils.py",
                 "run.py", "start.py", "util.py", "helpers.py", "config.py", "settings.py", "ios.py", "macos.py"}


def suffix(path):
    """The path's last two parts, or three when the folder has a common name."""
    parts = path.split("/")
    if len(parts) >= 2 and parts[-2].lower() not in GENERIC_DIRS:
        return "/".join(parts[-2:])
    if len(parts) >= 3:
        return "/".join(parts[-3:])
    return None


def find_copies(matches, repos):
    """(repo, path) -> original repository, for files carried from another repository."""
    stars = lambda name: repos.get(name, {}).get("stars") or 0
    by_suffix = {}
    for m in matches:
        key = suffix(m["path"])
        if key:
            by_suffix.setdefault(key, set()).add(m["repo"])
    copies, roots = {}, {}
    for m in matches:
        key = suffix(m["path"])
        if not key or len(by_suffix[key]) < 2:
            continue
        # pyobjus, Rubicon, Plyer and Toga are the origins of their own files.
        origin = max(by_suffix[key], key=lambda r: (r in PROJECTS, stars(r), r))
        if origin != m["repo"]:
            copies[(m["repo"], m["path"])] = origin
            roots.setdefault((m["repo"], origin), set()).add(m["path"][:len(m["path"]) - len(key)])
    for m in matches:
        if (m["repo"], m["path"]) in copies:
            continue
        for (repo, origin), prefixes in roots.items():
            if repo != m["repo"]:
                continue
            for prefix in prefixes:
                rest = m["path"][len(prefix):] if m["path"].startswith(prefix) else None
                if not rest:
                    continue
                source = next((o["repo"] for o in matches if o["repo"] != repo and stars(o["repo"]) > stars(repo)
                               and (o["path"] == rest or o["path"].endswith("/" + rest))), None)
                if source:
                    copies[(m["repo"], m["path"])] = source
    top_level = {}
    for m in matches:
        if "/" not in m["path"] and m["path"].lower() not in GENERIC_FILES:
            top_level.setdefault(m["path"], set()).add(m["repo"])
    for m in matches:
        if (m["repo"], m["path"]) in copies or m["repo"] in PROJECTS:
            continue
        name = m["path"].split("/")[-1]
        sources = [r for r in top_level.get(name, ()) if r != m["repo"] and stars(r) > stars(m["repo"])]
        if sources:
            copies[(m["repo"], m["path"])] = max(sources, key=lambda r: (stars(r), r))
    return copies


# Opening text that marks a file as part of another project.
HEADERS = [("This file is part of Ren'Py", "renpy/renpy", "renpy/"),
           ("Tom Rothamel", "renpy/renpy", "renpy/"),
           ("Clipboard OsX: implementation of clipboard using Appkit", "kivy/kivy", "kivy/"),
           ("AudioAvplayer: implementation of Sound using pyobjus", "kivy/kivy", "kivy/")]


def header_copy(repo, path, texts):
    text = texts.get("{}:{}".format(repo, path)) or ""
    for marker, origin, org in HEADERS:
        if marker in text and not repo.startswith(org):
            return origin
    return None


def main():
    data = json.load(open(sys.argv[1]))
    texts = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    if "markers" in texts:  # header_markers.json, as saved in the results
        texts = {k: v or "" for k, v in texts["markers"].items()}
    repos = data["repositories"]
    result = {"searched_at": data["searched_at"], "libraries": {}}
    for lib, info in data["libraries"].items():
        # A file with two import forms is found by two queries; count it once.
        unique = {}
        for m in info["matches"]:
            unique.setdefault((m["repo"], m["path"]), m)
        info = dict(info, matches=list(unique.values()))
        counted, excluded = {}, []
        # Projects excluded by name still count as originals of copies.
        candidates = [m for m in info["matches"]
                      if not (excluded_path(m["path"], m["repo"]) or "").startswith("copied or generated")]
        copies = find_copies(candidates, repos)
        for m in info["matches"]:
            details = repos.get(m["repo"], {})
            reason = excluded_repo(m["repo"], details) or excluded_path(m["path"], m["repo"])
            if not reason and (m["repo"], m["path"]) in copies:
                reason = "copy of another repository: " + copies[(m["repo"], m["path"])]
            if not reason and header_copy(m["repo"], m["path"], texts):
                reason = "copy of another project, by its header: " + header_copy(m["repo"], m["path"], texts)
            if reason:
                excluded.append({"repo": m["repo"], "path": m["path"], "reason": reason})
            else:
                counted.setdefault(m["repo"], []).append(m["path"])
        rows = [{"repo": name, "files": len(paths), "stars": repos.get(name, {}).get("stars"),
                 "pushed_at": repos.get(name, {}).get("pushed_at"), "example": sorted(paths)[0]}
                for name, paths in counted.items()]
        # GitHub reports only the last push, so a repository last pushed after the
        # baseline counts too: it was pushed between the window's start and the search.
        recent = [r for r in rows if r["pushed_at"] and r["pushed_at"] >= WINDOW_START]
        by_reason = {}
        for e in excluded:
            key = e["reason"].split(":")[0]
            by_reason[key] = by_reason.get(key, 0) + 1
        result["libraries"][lib] = {
            "matches": len(info["matches"]), "matches_counted": sum(r["files"] for r in rows),
            "repositories": len(rows), "pushed_in_24_months": len(recent),
            "pushed_after_baseline": sum(1 for r in rows if r["pushed_at"] and r["pushed_at"] > BASELINE),
            "top_by_stars": sorted(rows, key=lambda r: -(r["stars"] or 0))[:10],
            "excluded_by_reason": by_reason, "excluded_repositories": sorted({e["repo"] for e in excluded
                                                                              if e["reason"] == "the project itself"
                                                                              or e["reason"].startswith("fork")}),
            "size_ranges_over_limit": [r for r in info["size_ranges"] if r["total_count"] >= 1000],
            "incomplete_results": any(r["incomplete"] for r in info["size_ranges"]),
            "repositories_list": sorted(rows, key=lambda r: r["repo"]), "excluded": excluded}
    both = set(r["repo"] for r in result["libraries"]["pyobjus"]["repositories_list"]) & \
        set(r["repo"] for r in result["libraries"]["rubicon"]["repositories_list"])
    result["repositories_using_both"] = sorted(both)
    json.dump(result, open(sys.argv[2], "w"), indent=1)
    for lib, r in result["libraries"].items():
        print(lib, {k: r[k] for k in ("matches", "matches_counted", "repositories", "pushed_in_24_months",
                                      "excluded_by_reason", "incomplete_results")})
    print("both:", len(both))


if __name__ == "__main__":
    main()
