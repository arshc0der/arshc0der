#!/usr/bin/env python3
"""Fetch your real GitHub numbers, write data/stats.json, and redraw the stat SVGs.

Run it on your own PC (Python 3.8+, nothing to install):

    python scripts/sync_stats.py

It only uses the free public GitHub API and your public contribution calendar.
Change USERNAME below if you ever need a different profile.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_stats import render_all  # noqa: E402
from svgkit import ASSETS, ROOT  # noqa: E402

USERNAME = "arshc0der"
UA = {"User-Agent": "profile-stats"}


def http(url, data=None, headers=None, retries=3):
    h = dict(UA)
    h.update(headers or {})
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and i < retries - 1:
                time.sleep(12)
                continue
            raise
    raise RuntimeError("unreachable")


def rest(path):
    return json.loads(http("https://api.github.com" + path, headers={"Accept": "application/vnd.github+json"}))


# --------------------------------------------------------------------------- #
# shared
# --------------------------------------------------------------------------- #
def streaks(cal):
    longest = run = 0
    prev = None
    for ds in sorted(cal):
        if cal[ds] > 0:
            cur_d = date.fromisoformat(ds)
            run = run + 1 if prev and (cur_d - prev).days == 1 else 1
            longest = max(longest, run)
            prev = cur_d
    cur = 0
    day = date.today()
    if cal.get(day.isoformat(), 0) == 0:
        day -= timedelta(days=1)
    while cal.get(day.isoformat(), 0) > 0:
        cur += 1
        day -= timedelta(days=1)
    return cur, longest


# --------------------------------------------------------------------------- #
# public data (free public API)
# --------------------------------------------------------------------------- #
TD = re.compile(r"<td\b[^>]*>", re.S)
TIP = re.compile(r'<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>\s*([^<]*?)\s*</tool-tip>', re.S)


def parse_contributions(html):
    """Parse github.com/users/<username>/contributions into {date: count}."""
    tips = {}
    for fid, text in TIP.findall(html):
        m = re.match(r"(\d[\d,]*|No)\s+contribution", text)
        if m:
            tips[fid] = 0 if m[1] == "No" else int(m[1].replace(",", ""))
    out = {}
    for tag in TD.findall(html):
        d = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        i = re.search(r'\bid="([^"]+)"', tag)
        if not d:
            continue
        n = tips.get(i[1]) if i else None
        if n is None:  # older markup: count is in the tag itself
            c = re.search(r'data-count="(\d+)"', tag)
            n = int(c[1]) if c else 0
        out[d[1]] = n
    return out


def search_count(q):
    """Search totals; returns None (shown as a dash) if GitHub refuses, instead of crashing."""
    try:
        data = rest("/search/" + q)
        time.sleep(7)  # stay under the 10 requests/minute search limit
        return data.get("total_count", 0)
    except Exception as e:
        print("  skipped one search:", str(e)[:80])
        return None


def collect_public():
    u = rest(f"/users/{USERNAME}")
    repos = []
    for page in (1, 2, 3):
        batch = rest(f"/users/{USERNAME}/repos?per_page=100&type=owner&sort=pushed&page={page}")
        repos += batch
        if len(batch) < 100:
            break
    own = [r for r in repos if not r.get("fork")]
    stars = sum(r["stargazers_count"] for r in own)
    forks = sum(r["forks_count"] for r in own)
    langs = {}
    for r in own[:30]:
        try:
            for name, size in rest(f"/repos/{USERNAME}/{r['name']}/languages").items():
                langs.setdefault(name, {"name": name, "color": None, "size": 0})["size"] += size
        except Exception as e:
            print("  skipped languages for", r["name"], str(e)[:60])
            break
    q = urllib.parse.quote
    commits = search_count(f"commits?q={q('author:' + USERNAME)}&per_page=1")
    prs = search_count(f"issues?q={q('author:' + USERNAME + ' type:pr')}&per_page=1")
    issues = search_count(f"issues?q={q('author:' + USERNAME + ' type:issue')}&per_page=1")
    reviews = search_count(f"issues?q={q('reviewed-by:' + USERNAME + ' type:pr')}&per_page=1")
    created = datetime.fromisoformat(u["created_at"].replace("Z", "+00:00"))
    cal = {}
    for y in range(created.year, date.today().year + 1):
        try:
            html = http(f"https://github.com/users/{USERNAME}/contributions?from={y}-01-01&to={y}-12-31")
            cal.update(parse_contributions(html))
        except Exception as e:
            print("  skipped contributions for", y, str(e)[:60])
    return dict(
        created_at=u["created_at"], followers=u["followers"], organizations=0, public_repos=u["public_repos"],
        stars=stars, forks=forks, commits=commits, prs=prs, issues=issues, reviews=reviews,
        contributions_total=sum(cal.values()), languages=list(langs.values()), cal=cal,
    )


# --------------------------------------------------------------------------- #
def main():
    print(f"profile: {USERNAME} | source: free public GitHub API")
    raw = collect_public()
    cal = raw.pop("cal")
    cur, longest = streaks(cal)
    days = sorted(cal)
    data = {
        "synced": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "username": USERNAME,
        **raw,
        "current_streak": cur,
        "longest_streak": longest,
        "languages": sorted(raw["languages"], key=lambda l: -l["size"]),
        "calendar": [{"date": d, "count": cal[d]} for d in days[-371:]],
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "stats.json").write_text(json.dumps(data, indent=1))
    render_all(data, ASSETS)
    print(f"done: {data['stars']} stars, {data['commits']} commits, {data['contributions_total']} contributions, streak {cur}/{longest}")


if __name__ == "__main__":
    main()
