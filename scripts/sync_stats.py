#!/usr/bin/env python3
"""Fetch your real GitHub numbers, write data/stats.json, and redraw the stat SVGs.

Run it on your own PC (Python 3.8+, nothing to install):

    python scripts/sync_stats.py

It only uses the free public GitHub API and your public contribution calendar.
Change USERNAME below if you ever need a different profile.

GitHub allows 60 free API requests per hour per internet connection. This script
uses about 10 per run. If the limit is hit, it keeps whatever it already has
(heatmap, streaks, your last saved numbers), tells you when to run it again, and
never crashes.
"""
import json
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
DATA_FILE = ROOT / "data" / "stats.json"

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5", "C": "#555555", "C++": "#f34b7d",
    "Java": "#b07219", "HTML": "#e34c26", "CSS": "#563d7c", "SCSS": "#c6538c", "PHP": "#4F5D95",
    "Shell": "#89e051", "Assembly": "#6E4C13", "Vue": "#41b883", "Dart": "#00B4AB", "Kotlin": "#A97BFF",
    "Go": "#00ADD8", "Rust": "#dea584", "C#": "#178600", "Ruby": "#701516", "Swift": "#F05138",
    "Jupyter Notebook": "#DA5B0B", "Makefile": "#427819", "Dockerfile": "#384d54", "Batchfile": "#C1F12E",
}


class RateLimited(Exception):
    def __init__(self, reset_epoch=None):
        self.reset_epoch = reset_epoch


RATE_LIMITED = {"hit": False, "reset": None}


def http(url, headers=None):
    h = dict(UA)
    h.update(headers or {})
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            reset = e.headers.get("X-RateLimit-Reset")
            raise RateLimited(int(reset) if reset and reset.isdigit() else None)
        raise


def rest(path):
    """One API call. After the first rate-limit hit, no further API calls are attempted."""
    if RATE_LIMITED["hit"]:
        raise RateLimited(RATE_LIMITED["reset"])
    try:
        return json.loads(http("https://api.github.com" + path, headers={"Accept": "application/vnd.github+json"}))
    except RateLimited as e:
        RATE_LIMITED.update(hit=True, reset=e.reset_epoch)
        raise


def attempt(label, fn):
    """Run fn(); on any failure print a short note and return None."""
    try:
        return fn()
    except RateLimited:
        print(f"  - {label}: GitHub rate limit, skipped")
    except Exception as e:  # network hiccup, unexpected shape, ...
        print(f"  - {label}: skipped ({str(e)[:70]})")
    return None


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
    """Search totals. Search has its own 10/minute limit, so pause between calls."""
    n = rest("/search/" + q).get("total_count", 0)
    time.sleep(7)
    return n


# --------------------------------------------------------------------------- #
def collect(old):
    got = {}

    # 1) profile + repos (2-4 API calls). Languages come from the repo list: no extra calls.
    u = attempt("profile", lambda: rest(f"/users/{USERNAME}"))
    if u:
        got.update(created_at=u["created_at"], followers=u["followers"], public_repos=u["public_repos"])

    def repos():
        out = []
        for page in (1, 2, 3):
            batch = rest(f"/users/{USERNAME}/repos?per_page=100&type=owner&sort=pushed&page={page}")
            out += batch
            if len(batch) < 100:
                break
        return out

    rp = attempt("repositories", repos)
    if rp is not None:
        own = [r for r in rp if not r.get("fork")]
        got["stars"] = sum(r["stargazers_count"] for r in own)
        got["forks"] = sum(r["forks_count"] for r in own)
        langs = {}
        for r in own:
            name = r.get("language")
            if name:
                langs.setdefault(name, {"name": name, "color": LANG_COLORS.get(name), "size": 0})["size"] += max(r.get("size", 0), 1)
        got["languages"] = list(langs.values())

    # 2) totals via search (4 calls, 7 s apart)
    q = urllib.parse.quote
    for key, query in (
        ("commits", f"commits?q={q('author:' + USERNAME)}&per_page=1"),
        ("prs", f"issues?q={q('author:' + USERNAME + ' type:pr')}&per_page=1"),
        ("issues", f"issues?q={q('author:' + USERNAME + ' type:issue')}&per_page=1"),
        ("reviews", f"issues?q={q('reviewed-by:' + USERNAME + ' type:pr')}&per_page=1"),
    ):
        v = attempt(key, lambda query=query: search_count(query))
        if v is not None:
            got[key] = v

    # 3) contribution calendar: plain public web pages, not the API, so no API limit
    created = got.get("created_at") or old.get("created_at")
    start_year = int(created[:4]) if created else date.today().year - 3
    cal = {}
    for y in range(start_year, date.today().year + 1):
        html = attempt(f"contributions {y}", lambda y=y: http(f"https://github.com/users/{USERNAME}/contributions?from={y}-01-01&to={y}-12-31"))
        if html:
            cal.update(parse_contributions(html))
    return got, cal


def main():
    print(f"profile: {USERNAME} | source: free public GitHub API")
    old = {}
    try:
        old = json.loads(DATA_FILE.read_text())
    except Exception:
        pass
    got, cal = collect(old)

    data = {k: v for k, v in old.items() if k not in ("synced",)}  # keep last known numbers
    data.update(got)
    if cal:
        cur, longest = streaks(cal)
        days = sorted(cal)
        data.update(
            contributions_total=sum(cal.values()), current_streak=cur, longest_streak=longest,
            calendar=[{"date": d, "count": cal[d]} for d in days[-371:]],
        )
    data["languages"] = sorted(data.get("languages", []), key=lambda l: -l["size"])
    data["username"] = USERNAME
    data["synced"] = bool(got or cal)
    data["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=1))
    render_all(data, ASSETS)

    if RATE_LIMITED["hit"]:
        when = ""
        if RATE_LIMITED["reset"]:
            when = " after " + datetime.fromtimestamp(RATE_LIMITED["reset"]).strftime("%H:%M")
        print(f"\nGitHub's free limit (60 requests/hour) was reached. Run this again{when} to fill in the missing numbers;")
        print("everything it already had was kept and the SVGs were still redrawn.")
    print(f"done: stars={data.get('stars')} commits={data.get('commits')} contributions={data.get('contributions_total')} "
          f"streak={data.get('current_streak')}/{data.get('longest_streak')}")


if __name__ == "__main__":
    main()
