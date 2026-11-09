"""E1: public Python code that imports each library, from GitHub's code search.

Usage: code_search.py OUT.json

Searches each import form with the gh CLI. The API returns at most 1,000
results per query, so each query is split by file size until it reports
fewer than 1,000, then every page is read. Matches are combined by
repository and path. Repository details (stars, last push, fork parent)
come from the GraphQL API in batches. Every response is saved, and
summarize.py applies the exclusions.
"""
import json
import subprocess
import sys
import time

QUERIES = {
    "pyobjus": ['"from pyobjus import"', '"import pyobjus"'],
    "rubicon": ['"from rubicon.objc import"', '"import rubicon.objc"', '"from rubicon import objc"'],
}
MAX_SIZE = 384_000  # GitHub doesn't index larger files
SEARCH_PAUSE = 7  # the code search API allows 10 requests a minute


def gh(args, retries=6):
    for attempt in range(retries):
        p = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)
        if "rate limit" in (p.stdout + p.stderr).lower() or "403" in p.stderr or "429" in p.stderr:
            time.sleep(60 * (attempt + 1))
            continue
        raise RuntimeError(p.stderr[-500:])
    raise RuntimeError("gave up after rate limits")


def search(q, page=1):
    time.sleep(SEARCH_PAUSE)
    return gh(["-X", "GET", "search/code", "-f", "q=" + q, "-f", "per_page=100", "-f", "page=" + str(page)])


def ranges(q, lo, hi, log):
    """Size ranges under q that each report fewer than 1,000 results."""
    first = search("{} language:Python size:{}..{}".format(q, lo, hi))
    log.append({"query": q, "size": [lo, hi], "total_count": first["total_count"],
                "incomplete": first["incomplete_results"]})
    if first["total_count"] < 1000 or hi - lo <= 1:
        return [(lo, hi, first)]
    mid = (lo + hi) // 2
    return ranges(q, lo, mid, log) + ranges(q, mid + 1, hi, log)


def collect(q, log):
    items = {}
    for lo, hi, first in ranges(q, 0, MAX_SIZE, log):
        pages = min(10, (first["total_count"] + 99) // 100)
        responses = [first] + [search("{} language:Python size:{}..{}".format(q, lo, hi), n)
                               for n in range(2, pages + 1)]
        for r in responses:
            for it in r["items"]:
                repo = it["repository"]
                items[(repo["full_name"], it["path"])] = {
                    "repo": repo["full_name"], "path": it["path"], "url": it["html_url"],
                    "repo_fork": repo["fork"], "query": q}
    return list(items.values())


def repo_details(names):
    out = {}
    names = sorted(names)
    for start in range(0, len(names), 50):
        parts = []
        for i, name in enumerate(names[start:start + 50]):
            owner, repo = name.split("/", 1)
            parts.append('r{}: repository(owner: {}, name: {}) {{ nameWithOwner stargazerCount pushedAt isFork '
                         'isArchived parent {{ nameWithOwner }} }}'.format(i, json.dumps(owner), json.dumps(repo)))
        p = subprocess.run(["gh", "api", "graphql", "-f", "query={" + " ".join(parts) + "}"],
                           capture_output=True, text=True)
        data = json.loads(p.stdout).get("data") or {}
        for i, name in enumerate(names[start:start + 50]):
            r = data.get("r{}".format(i))
            out[name] = {"stars": r["stargazerCount"], "pushed_at": r["pushedAt"], "fork": r["isFork"],
                         "archived": r["isArchived"],
                         "parent": (r["parent"] or {}).get("nameWithOwner")} if r else {"missing": True}
    return out


def main():
    out = sys.argv[1]
    result = {"searched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "libraries": {}}
    for lib, queries in QUERIES.items():
        log, matches = [], []
        for q in queries:
            found = collect(q, log)
            matches += found
            print(lib, q, len(found), "matches", flush=True)
        result["libraries"][lib] = {"queries": queries, "size_ranges": log, "matches": matches}
        json.dump(result, open(out, "w"), indent=1)
    names = {m["repo"] for lib in result["libraries"].values() for m in lib["matches"]}
    result["repositories"] = repo_details(names)
    json.dump(result, open(out, "w"), indent=1)
    print(len(names), "repositories", flush=True)


if __name__ == "__main__":
    main()
