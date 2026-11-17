"""Mine benign PR/issue/comment text from active public GitHub repos.

Uses the authenticated `gh` CLI (no token handling, stdlib only). Output is JSONL, one
row per text, label "benign". Email-bearing rows are flagged (`has_email`) so the
downstream sampler can balance email rate against the injection class.

    python3 training/scripts/mine_negatives.py --out training/data/raw/github_negatives/negatives.jsonl
"""
import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
MIN_LEN, MAX_LEN = 20, 4000


def gh(path, **params):
    args = ["gh", "api", "-X", "GET", path]
    for k, v in params.items():
        args += ["-f", f"{k}={v}"]
    out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def discover_repos(n, rng, active_days):
    since = (date.today() - timedelta(days=active_days)).isoformat()
    # Mid-popularity repos: active enough to have fresh text, not just mega-projects.
    q = f"stars:200..20000 pushed:>{since} archived:false"
    pool = []
    for page in (1, 2, 3):
        items = gh("search/repositories", q=q, sort="updated", per_page=100, page=page)["items"]
        pool += [i["full_name"] for i in items]
    rng.shuffle(pool)
    return pool[:n]


def keep(user, text):
    if not text or not (MIN_LEN <= len(text.strip()) <= MAX_LEN):
        return False
    return user and user.get("type") != "Bot" and not user["login"].endswith("[bot]")


def rows_for_repo(repo):
    issues = gh(f"repos/{repo}/issues", state="all", sort="updated", per_page=100)
    comments = gh(f"repos/{repo}/issues/comments", sort="updated", direction="desc", per_page=100)
    for it in issues:
        kind = "pr" if "pull_request" in it else "issue"
        for part, text in (("title", it["title"]), ("body", it["body"])):
            if keep(it["user"], text):
                yield kind + "_" + part, text, it["html_url"], it["created_at"]
    for c in comments:
        if keep(c["user"], c["body"]):
            yield "comment", c["body"], c["html_url"], c["created_at"]


EMAIL_QUERIES = ['"gmail.com" in:body', '"contact me at" in:body', '"send it to" email in:body',
                 '"co-authored-by" in:body', '"email" "@" in:body']


def email_search_rows(n, active_days):
    """Search-driven pass: real text that mentions emails, incl. hard 'send X to Y' cases."""
    since = (date.today() - timedelta(days=active_days)).isoformat()
    for q in EMAIL_QUERIES:
        items = gh("search/issues", q=f"{q} is:public updated:>{since}", sort="updated",
                   per_page=min(n, 100))["items"]
        for it in items:
            if keep(it["user"], it["body"]) and EMAIL.search(it["body"]):
                kind = "pr_body" if "pull_request" in it else "issue_body"
                repo = it["repository_url"].split("repos/")[1]
                yield repo, kind, it["body"], it["html_url"], it["created_at"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--repos", nargs="*", help="owner/name list; default: discover via search")
    ap.add_argument("--max-repos", type=int, default=100)
    ap.add_argument("--per-repo", type=int, default=40, help="max rows kept per repo")
    ap.add_argument("--email-search", type=int, default=50,
                    help="results per email query (0 disables the targeted pass)")
    ap.add_argument("--active-days", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    repos = a.repos or discover_repos(a.max_repos, rng, a.active_days)
    seen, rows = set(), []
    for repo in repos:
        try:
            got = list(rows_for_repo(repo))
        except subprocess.CalledProcessError as e:
            print(f"skip {repo}: {e.stderr.strip()[:100]}", file=sys.stderr)
            continue
        rng.shuffle(got)
        n = 0
        for kind, text, url, created in got:
            h = hashlib.sha1(text.strip().encode()).hexdigest()
            if h in seen or n >= a.per_repo:
                continue
            seen.add(h)
            n += 1
            rows.append({"text": text, "label": "benign", "source": "github_api", "repo": repo,
                         "kind": kind, "via": "repo_sample", "has_email": bool(EMAIL.search(text)), "url": url,
                         "created_at": created})

    if a.email_search:
        for repo, kind, text, url, created in email_search_rows(a.email_search, a.active_days):
            h = hashlib.sha1(text.strip().encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                rows.append({"text": text, "label": "benign", "source": "github_api", "repo": repo,
                             "kind": kind, "via": "email_search", "has_email": True, "url": url,
                             "created_at": created})

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    emails = sum(r["has_email"] for r in rows)
    print(f"{len(rows)} rows from {len(repos)} repos, {emails} with email "
          f"({emails / max(len(rows), 1):.1%}) -> {out}")


if __name__ == "__main__":
    main()
