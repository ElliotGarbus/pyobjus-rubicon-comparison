"""E1: read the start of every match that the path rules count, to find copies
of other projects that path rules miss.

Usage: fetch_headers.py CODE_SEARCH.json SUMMARY.json OUT.json

Ren'Py names its launcher after each game, so a game repository can carry a
copy of Ren'Py's launcher, which imports pyobjus, under any name. This reads
the first 2,000 characters of each counted file through the GraphQL API, in
batches of 50, and saves them. summarize.py treats a file carrying another
project's license header as a copy of that project.
"""
import json
import subprocess
import sys

HEAD = 2000


def main():
    search, summary, out = sys.argv[1:4]
    search = json.load(open(search))
    summary = json.load(open(summary))
    wanted = []
    for lib, info in summary["libraries"].items():
        excluded = {(e["repo"], e["path"]) for e in info["excluded"]}
        wanted += [(m["repo"], m["path"]) for m in search["libraries"][lib]["matches"]
                   if (m["repo"], m["path"]) not in excluded]
    wanted = sorted(set(wanted))
    texts = {}
    for start in range(0, len(wanted), 50):
        parts = []
        batch = wanted[start:start + 50]
        for i, (repo, path) in enumerate(batch):
            owner, name = repo.split("/", 1)
            parts.append('f{}: repository(owner: {}, name: {}) {{ object(expression: {}) {{ ... on Blob {{ text }} }} }}'
                         .format(i, json.dumps(owner), json.dumps(name), json.dumps("HEAD:" + path)))
        p = subprocess.run(["gh", "api", "graphql", "-f", "query={" + " ".join(parts) + "}"],
                           capture_output=True, text=True)
        data = (json.loads(p.stdout or "{}").get("data") or {})
        for i, (repo, path) in enumerate(batch):
            obj = ((data.get("f{}".format(i)) or {}).get("object") or {})
            texts["{}:{}".format(repo, path)] = (obj.get("text") or "")[:HEAD] if obj else None
        print(start + len(batch), "of", len(wanted), flush=True)
    json.dump(texts, open(out, "w"), indent=0)


if __name__ == "__main__":
    main()
