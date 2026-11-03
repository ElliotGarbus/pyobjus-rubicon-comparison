#!/usr/bin/env python3
"""Collect the raw data for Section 1 into results/section-01/<snapshot>/raw.

Usage: section01_collect.py SNAPSHOT_UTC WORK_DIR
  SNAPSHOT_UTC  snapshot time T, for example 2026-11-03T18:00:00Z
  WORK_DIR      directory for temporary bare clones, outside this repository

Requires an authenticated `gh` CLI and `git`. Email addresses are removed
before anything is saved, and only the commit fields used by the analysis are
kept. Everything else is saved as returned by the source.
"""
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPOS = {"pyobjus": "kivy/pyobjus", "rubicon-objc": "beeware/rubicon-objc"}
PYTHON_RELEASES = ["3.10.0", "3.11.0", "3.12.0", "3.13.0", "3.14.0", "3.15.0"]
ROOT = Path(__file__).resolve().parent.parent

PERSON = "author { __typename login }"
COMMENTS = "comments(first: 100) { totalCount nodes { createdAt authorAssociation %s } }" % PERSON

PR_QUERY = """
query($owner: String!, $name: String!, $after: String, $size: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: $size, after: $after, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title createdAt closedAt mergedAt merged state baseRefName isDraft
        authorAssociation %s
        mergedBy { __typename login }
        mergeCommit { oid }
        %s
        reviews(first: 100) {
          totalCount
          nodes { submittedAt state authorAssociation %s }
        }
        timelineItems(itemTypes: [CLOSED_EVENT], last: 1) {
          nodes { ... on ClosedEvent { createdAt stateReason actor { __typename login } } }
        }
      }
    }
  }
}
""" % (PERSON, COMMENTS, PERSON)

ISSUE_QUERY = """
query($owner: String!, $name: String!, $after: String, $size: Int!) {
  repository(owner: $owner, name: $name) {
    issues(first: $size, after: $after, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title createdAt closedAt state stateReason
        authorAssociation %s
        %s
        timelineItems(itemTypes: [CLOSED_EVENT], last: 1) {
          nodes {
            ... on ClosedEvent {
              createdAt stateReason actor { __typename login }
              closer {
                __typename
                ... on PullRequest { number author { login } }
                ... on Commit { oid author { user { login } } }
              }
            }
          }
        }
        closedByPullRequestsReferences(first: 10, includeClosedPrs: true) {
          nodes { number merged author { login } }
        }
      }
    }
  }
}
""" % (PERSON, COMMENTS)


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def gh_json(*args):
    return json.loads(run("gh", "api", *args))


def graphql(query, **variables):
    args = ["graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is None:
            continue
        args += ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
    for attempt in range(5):
        try:
            return gh_json(*args)
        except subprocess.CalledProcessError as error:
            if attempt == 4:
                raise
            print(f"  retrying after: {error.stderr.strip()[:200]}", flush=True)
            time.sleep(10 * (attempt + 1))


def collect_connection(query, key, owner, name):
    nodes, after, size = [], None, 50
    while True:
        try:
            data = graphql(query, owner=owner, name=name, after=after, size=size)
        except subprocess.CalledProcessError:
            if size == 10:
                raise
            size = 10
            continue
        page = data["data"]["repository"][key]
        nodes += page["nodes"]
        print(f"  {key}: {len(nodes)}", flush=True)
        if not page["pageInfo"]["hasNextPage"]:
            return nodes
        after = page["pageInfo"]["endCursor"]


def fetch_url(url):
    request = urllib.request.Request(url, headers={"User-Agent": "pyobjus-rubicon-comparison"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode()


def fetch_json(url):
    return json.loads(fetch_url(url))


def remove_emails(value):
    """Return a copy of decoded JSON without email fields or free-text descriptions."""
    if isinstance(value, dict):
        return {k: remove_emails(v) for k, v in value.items()
                if "email" not in k.lower() and k != "description"}
    if isinstance(value, list):
        return [remove_emails(v) for v in value]
    return value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n")


def collect_commits(repo, sha):
    pages = run("gh", "api", "--paginate", "--slurp", f"repos/{repo}/commits?sha={sha}&per_page=100")
    commits = []
    for page in json.loads(pages):
        for item in page:
            author = item.get("author") or {}
            commit = item["commit"]
            commits.append({
                "sha": item["sha"],
                "parents": [p["sha"] for p in item["parents"]],
                "author_login": author.get("login"),
                "author_type": author.get("type"),
                "author_name": commit["author"]["name"],
                "author_date": commit["author"]["date"],
                "committer_date": commit["committer"]["date"],
                "subject": commit["message"].split("\n", 1)[0],
            })
    return commits


def collect_ci_history(clone, branch):
    """Record every added CI configuration line that names a Python 3.10+ version."""
    log = run(
        "git", "log", "--reverse", "--format=commit %H %cI", "-p", "--unified=0",
        "--no-renames", branch, "--", ".github/workflows", ".travis.yml", "appveyor.yml",
        ".circleci", "azure-pipelines.yml", cwd=clone,
    )
    hits, sha, date, path = [], None, None, None
    for line in log.splitlines():
        if line.startswith("commit "):
            _, sha, date = line.split()
        elif line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and not line.startswith("+++"):
            for minor in range(10, 17):
                if f"3.{minor}" in line:
                    hits.append({"sha": sha, "date": date, "path": path, "minor": minor,
                                 "line": line[1:].strip()})
    return hits


def main():
    snapshot, work_dir = sys.argv[1], Path(sys.argv[2])
    raw = ROOT / "results" / "section-01" / snapshot.replace(":", "") / "raw"
    manifest = {
        "snapshot_T": snapshot,
        "collection_started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repositories": {},
    }
    for key, repo in REPOS.items():
        print(repo, flush=True)
        meta = gh_json(f"repos/{repo}")
        branch = meta["default_branch"]
        head = gh_json(f"repos/{repo}/commits?sha={branch}&until={snapshot}&per_page=1")[0]["sha"]
        save(raw / key / "repo.json", meta)
        clone = work_dir / f"{key}.git"
        if clone.exists():
            run("git", "fetch", "-q", "origin", "+refs/*:refs/*", cwd=clone)
        else:
            run("git", "clone", "-q", "--bare", "--filter=blob:none",
                f"https://github.com/{repo}.git", str(clone))
        commits = collect_commits(repo, head)
        git_count = int(run("git", "rev-list", "--count", head, cwd=clone))
        save(raw / key / "commits.json", commits)
        save(raw / key / "ci_history.json", collect_ci_history(clone, head))
        save(raw / key / "pulls.json", collect_connection(PR_QUERY, "pullRequests", *repo.split("/")))
        save(raw / key / "issues.json", collect_connection(ISSUE_QUERY, "issues", *repo.split("/")))
        tags = run("git", "for-each-ref", "refs/tags",
                   "--format=%(refname:short)\t%(objecttype)\t%(taggername)\t%(creatordate:iso-strict)",
                   cwd=clone)
        save(raw / key / "tags.json", [line.split("\t") for line in tags.splitlines()])
        save(raw / key / "github_releases.json", json.loads(
            run("gh", "api", "--paginate", "--slurp", f"repos/{repo}/releases")))

        pypi = fetch_json(f"https://pypi.org/pypi/{key}/json")
        save(raw / key / "pypi.json", remove_emails(pypi))
        for version in pypi["releases"]:
            quoted = urllib.parse.quote(version)
            detail = fetch_json(f"https://pypi.org/pypi/{key}/{quoted}/json")
            save(raw / key / "pypi_versions" / f"{version}.json", remove_emails(detail["info"]))
        save(raw / key / "pypistats_system.json",
             fetch_json(f"https://pypistats.org/api/packages/{key}/system?mirrors=false"))
        manifest["repositories"][key] = {
            "repository": repo, "default_branch": branch, "commit_at_T": head,
            "commits_from_api": len(commits), "commits_from_git": git_count,
        }

    releases = fetch_json("https://www.python.org/api/v2/downloads/release/?is_published=true")
    wanted = {f"Python {v}": v for v in PYTHON_RELEASES}
    save(raw / "python_releases.json",
         {wanted[r["name"]]: r["release_date"] for r in releases if r["name"] in wanted})
    save(raw / "kivy_mobile_wheels_pyobjus.html.json", {
        "url": "https://elliotgarbus.github.io/kivy-mobile-wheels/simple/pyobjus/",
        "html": fetch_url("https://elliotgarbus.github.io/kivy-mobile-wheels/simple/pyobjus/"),
    })
    manifest["collection_finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save(raw.parent / "manifest.json", manifest)
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
