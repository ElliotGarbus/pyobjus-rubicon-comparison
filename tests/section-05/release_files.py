"""B2 and K3: each release's files on PyPI, and whether PyPI has provenance for them.

Usage: release_files.py OUT.json

PyPI's integrity API returns a provenance record for a file uploaded through
trusted publishing with attestations, and 404 for one that wasn't.
"""
import json
import sys
import urllib.error
import urllib.request

RELEASES = {"pyobjus": "1.2.4", "rubicon-objc": "0.5.7"}


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.pypi.integrity.v1+json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None


def main():
    out = {}
    for project, version in RELEASES.items():
        status, meta = get(f"https://pypi.org/pypi/{project}/{version}/json")
        files = []
        for f in meta["urls"]:
            code, prov = get(f"https://pypi.org/integrity/{project}/{version}/{f['filename']}/provenance")
            publisher = None
            if prov:
                publisher = [b["publisher"] for b in prov.get("attestation_bundles", [])]
            files.append({"filename": f["filename"], "uploaded": f["upload_time_iso_8601"],
                          "provenance_status": code, "publisher": publisher})
            print(project, f["filename"], code, publisher, flush=True)
        out[project] = {"version": version, "files": files}
    json.dump(out, open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
