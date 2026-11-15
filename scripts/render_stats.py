#!/usr/bin/env python3
"""Renders the data-driven SVGs (stats, languages, activity, trophies) from data/stats.json.

Fully offline: reads JSON, writes SVG. Works with empty data too (locked trophies,
"awaiting sync" labels), so the README never shows a broken image.

    python3 scripts/render_stats.py [path/to/stats.json] [output_dir]
"""
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import *  # noqa: E402,F401,F403

W = 900


def bg_defs(w, h):
    return (
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1222"/>'
        f'<stop offset="1" stop-color="{BG0}"/></linearGradient>'
        f'<clipPath id="clipAll"><rect width="{w}" height="{h}" rx="18"/></clipPath>'
    )


def frame(w, h, rx=18):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="url(#bg)" stroke="{LINE}"/>'


def val(d, key):
    v = d.get(key)
    return v if isinstance(v, (int, float)) else None


# --------------------------------------------------------------------------- #
# stat tiles + streak
# --------------------------------------------------------------------------- #
ICON = {
    "star": '<polygon points="12,2 15,9 22,9.5 16.5,14 18.5,21 12,17 5.5,21 7.5,14 2,9.5 9,9" fill="none" stroke-linejoin="round"/>',
    "commit": '<circle cx="12" cy="12" r="4"/><path d="M2 12h6M16 12h6"/>',
    "pr": '<circle cx="6" cy="6" r="2.6"/><circle cx="6" cy="18" r="2.6"/><circle cx="18" cy="18" r="2.6"/><path d="M6 8.6v6.8M18 15.4V9a3 3 0 0 0-3-3h-3"/>',
    "issue": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/>',
    "repo": '<path d="M5 3h12a2 2 0 0 1 2 2v16H7a2 2 0 0 1-2-2zM5 17h14" stroke-linejoin="round"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2 20c0-4 3-6 7-6s7 2 7 6"/><circle cx="17.5" cy="9" r="2.5"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "eye": '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>',
}


def synced_label(d):
    if d.get("synced") and d.get("generated_at"):
        return "synced " + str(d["generated_at"])[:10]
    return "awaiting first sync"


def render_stats(d):
    h = 286
    tiles = [
        ("STARS EARNED", val(d, "stars"), "star", AMBER),
        ("COMMITS", val(d, "commits"), "commit", CYAN),
        ("PULL REQUESTS", val(d, "prs"), "pr", VIOLET),
        ("ISSUES", val(d, "issues"), "issue", ROSE),
        ("REPOSITORIES", val(d, "public_repos"), "repo", SKY),
        ("FOLLOWERS", val(d, "followers"), "users", PINK),
        ("CONTRIBUTIONS", val(d, "contributions_total"), "grid", EMERALD),
        ("CODE REVIEWS", val(d, "reviews"), "eye", LIME),
    ]
    css = (
        ".t{animation:up .6s cubic-bezier(.2,.8,.2,1) both}@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
        ".f{animation:fl 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:50% 100%}@keyframes fl{50%{transform:scale(1.08,.94)}}"
    )
    defs = bg_defs(W, h) + aurora_grad("ag", 0, 300) + (
        f'<linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{AMBER}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>'
    )
    b = [frame(W, h)]
    b.append(f'<text x="28" y="38" class="m" font-size="12" letter-spacing="2.5" fill="{MUTED}">GITHUB TELEMETRY</text>')
    b.append(f'<text x="196" y="38" class="m" font-size="12" font-weight="700" fill="{CYAN}">@{esc(d.get("login", "arshc0der"))}</text>')
    b.append(f'<text x="{W - 28}" y="38" text-anchor="end" class="m" font-size="11.5" fill="{MUTED}">{esc(synced_label(d))}</text>')
    tw, th, gx, gy = 158, 100, 12, 12
    for i, (label, v, ico, col) in enumerate(tiles):
        x = 28 + (i % 4) * (tw + gx)
        y = 56 + (i // 4) * (th + gy)
        b.append(
            f'<g class="t" style="animation-delay:{i * .07:.2f}s"><rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="14" fill="{col}" fill-opacity=".06" stroke="{col}" stroke-opacity=".32"/>'
            f'<g transform="translate({x + 16} {y + 16}) scale(.85)" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" color="{col}">{ICON[ico]}</g>'
            f'<text x="{x + tw - 14}" y="{y + 31}" text-anchor="end" class="m" font-size="9.5" letter-spacing="1.4" fill="{MUTED}">{label}</text>'
            f'<text x="{x + 16}" y="{y + 78}" class="s" font-size="34" font-weight="800" fill="{TXT if v is not None else MUTED}">{fmt_num(v)}</text>'
            f'<rect x="{x + 16}" y="{y + 88}" width="{tw - 32}" height="2" rx="1" fill="{col}" fill-opacity=".25"/>'
            f'<rect x="{x + 16}" y="{y + 88}" width="0" height="2" rx="1" fill="{col}"><animate attributeName="width" from="0" to="{(tw - 32) * (0.35 if v else 0)}" dur="1.2s" begin="{i * .07 + .3:.2f}s" fill="freeze"/></rect></g>'
        )
    # streak panel
    px = 28 + 4 * (tw + gx)
    pw = W - 28 - px
    cur, lng = val(d, "current_streak"), val(d, "longest_streak")
    b.append(f'<rect x="{px}" y="56" width="{pw}" height="212" rx="14" fill="{AMBER}" fill-opacity=".05" stroke="{AMBER}" stroke-opacity=".3"/>')
    rcx, rcy, rr = px + pw / 2, 138, 50
    circ = 2 * math.pi * rr
    frac = min((cur or 0) / max(lng or 1, 1), 1) if cur else 0
    b.append(
        f'<circle cx="{rcx}" cy="{rcy}" r="{rr}" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="8"/>'
        f'<circle cx="{rcx}" cy="{rcy}" r="{rr}" fill="none" stroke="url(#ring)" stroke-width="8" stroke-linecap="round" stroke-dasharray="0 {circ:.1f}" transform="rotate(-90 {rcx} {rcy})">'
        f'<animate attributeName="stroke-dasharray" from="0 {circ:.1f}" to="{circ * frac:.1f} {circ:.1f}" dur="1.6s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/></circle>'
        f'<g transform="translate({rcx - 8} {rcy - 38}) scale(.7)" fill="{AMBER}"><g class="f"><path d="M12 2c1 4 5 6 5 11a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-4-1-6 1-10z"/></g></g>'
        f'<text x="{rcx}" y="{rcy + 14}" text-anchor="middle" class="s" font-size="34" font-weight="800" fill="{TXT if cur is not None else MUTED}">{fmt_num(cur)}</text>'
        f'<text x="{rcx}" y="{rcy + 30}" text-anchor="middle" class="m" font-size="9.5" letter-spacing="1.4" fill="{MUTED}">DAY STREAK</text>'
        f'<text x="{rcx}" y="{rcy + 82}" text-anchor="middle" class="m" font-size="11.5" fill="{MUTED}">longest <tspan fill="{AMBER}" font-weight="700">{fmt_num(lng)}</tspan> days</text>'
    )
    return wrap(W, h, "GitHub telemetry", "GitHub statistics tiles: stars, commits, pull requests, issues, repositories, followers, contributions, reviews and streak.", "".join(b), css, defs)


# --------------------------------------------------------------------------- #
# languages
# --------------------------------------------------------------------------- #
def render_languages(d):
    langs = [l for l in d.get("languages", []) if l.get("size", 0) > 0][:8]
    total = sum(l["size"] for l in langs) or 1
    h = 40 + 70 + (math.ceil(max(len(langs), 1) / 4)) * 28 + 20
    defs = bg_defs(W, h) + f'<clipPath id="barc"><rect x="28" y="62" width="{W - 56}" height="16" rx="8"/></clipPath>'
    b = [frame(W, h)]
    b.append(f'<text x="28" y="38" class="m" font-size="12" letter-spacing="2.5" fill="{MUTED}">LANGUAGE DNA</text>')
    b.append(f'<text x="{W - 28}" y="38" text-anchor="end" class="m" font-size="11.5" fill="{MUTED}">{esc(synced_label(d))}</text>')
    b.append(f'<rect x="28" y="62" width="{W - 56}" height="16" rx="8" fill="#fff" fill-opacity=".06"/>')
    if langs:
        bw = W - 56
        b.append('<g clip-path="url(#barc)">')
        x = 28.0
        for i, l in enumerate(langs):
            seg = bw * l["size"] / total
            col = l.get("color") or [CYAN, VIOLET, PINK, LIME, AMBER, SKY, ROSE, EMERALD][i % 8]
            b.append(
                f'<rect x="{x:.1f}" y="62" width="0" height="16" fill="{col}"><animate attributeName="width" from="0" to="{seg + .5:.1f}" dur="1s" begin="{i * .12:.2f}s" fill="freeze"/></rect>'
            )
            x += seg
        b.append("</g>")
        for i, l in enumerate(langs):
            col = l.get("color") or [CYAN, VIOLET, PINK, LIME, AMBER, SKY, ROSE, EMERALD][i % 8]
            lx = 28 + (i % 4) * 215
            ly = 108 + (i // 4) * 28
            b.append(
                f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{col}"/><text x="{lx + 18}" y="{ly}" class="s" font-size="13.5" font-weight="600" fill="{TXT}">{esc(l["name"])}</text>'
                f'<text x="{lx + 196}" y="{ly}" text-anchor="end" class="m" font-size="12" fill="{MUTED}">{100 * l["size"] / total:.1f}%</text>'
            )
    else:
        b.append(f'<text x="28" y="112" class="m" font-size="13" fill="{MUTED}">language data appears after the first workflow run</text>')
    return wrap(W, h, "Language DNA", "Most used languages across repositories.", "".join(b), "", defs)


# --------------------------------------------------------------------------- #
# activity heatmap
# --------------------------------------------------------------------------- #
def render_activity(d):
    cell, gap = 12, 3
    cols = 53
    h = 56 + 7 * (cell + gap) + 54
    ramp = ["#131c31", "#134e6b", "#0891b2", CYAN, VIOLET]
    days = {}
    for c in d.get("calendar", []):
        try:
            days[date.fromisoformat(c["date"])] = int(c["count"])
        except Exception:
            pass
    css = ".c{animation:pop .5s ease-out both}@keyframes pop{from{opacity:0}to{opacity:1}}"
    defs = bg_defs(W, h)
    b = [frame(W, h)]
    b.append(f'<text x="28" y="38" class="m" font-size="12" letter-spacing="2.5" fill="{MUTED}">CONTRIBUTION HEATMAP</text>')
    total = sum(days.values())
    b.append(f'<text x="{W - 28}" y="38" text-anchor="end" class="m" font-size="11.5" fill="{MUTED}">{f"{total:,} in the last year" if days else esc(synced_label(d))}</text>')
    end = max(days) if days else date.today()
    start_idx = (end.weekday() + 1) % 7  # Sunday = 0
    first = end.toordinal() - (cols - 1) * 7 - start_idx
    mx = max(days.values()) if days else 0
    x0, y0 = 28 + 0, 56
    gridw = cols * (cell + gap) - gap
    ox = (W - gridw) / 2
    last_month = None
    for col in range(cols):
        for row in range(7):
            dt = date.fromordinal(first + col * 7 + row)
            if dt > end:
                continue
            n = days.get(dt, 0)
            lvl = 0 if n == 0 or mx == 0 else min(4, max(1, math.ceil(4 * n / mx)))
            x, y = ox + col * (cell + gap), y0 + row * (cell + gap)
            b.append(f'<rect class="c" style="animation-delay:{col * .02:.2f}s" x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{ramp[lvl]}"><title>{dt.isoformat()}: {n}</title></rect>')
            if row == 0 and dt.month != last_month:
                last_month = dt.month
                b.append(f'<text x="{x:.1f}" y="{y0 - 8}" class="m" font-size="9.5" fill="{MUTED}">{dt.strftime("%b")}</text>')
    ly = y0 + 7 * (cell + gap) + 18
    b.append(f'<text x="{W - 28 - 5 * 17 - 40}" y="{ly + 9}" text-anchor="end" class="m" font-size="10" fill="{MUTED}">less</text>')
    for i, c in enumerate(ramp):
        b.append(f'<rect x="{W - 28 - 5 * 17 - 32 + i * 17}" y="{ly}" width="12" height="12" rx="3" fill="{c}"/>')
    b.append(f'<text x="{W - 28 - 24}" y="{ly + 9}" class="m" font-size="10" fill="{MUTED}">more</text>')
    return wrap(W, h, "Contribution heatmap", "Daily GitHub contributions over the last year.", "".join(b), css, defs)


# --------------------------------------------------------------------------- #
# trophies
# --------------------------------------------------------------------------- #
RANKS = ["C", "B", "A", "AA", "AAA", "S", "SS", "SSS"]
RANK_COL = {
    "SSS": ("#fde047", "#f472b6"), "SS": ("#fde68a", "#f59e0b"), "S": ("#fecaca", "#fb7185"),
    "AAA": ("#a7f3d0", "#10b981"), "AA": ("#a5f3fc", "#06b6d4"), "A": ("#bfdbfe", "#3b82f6"),
    "B": ("#e2e8f0", "#94a3b8"), "C": ("#fdba74", "#b45309"), "-": ("#334155", "#1e293b"),
}
# value thresholds for C, B, A, AA, AAA, S, SS, SSS
TROPHIES = [
    ("Stars", "stars", [1, 5, 15, 40, 100, 250, 600, 1500]),
    ("Commits", "commits", [10, 100, 300, 800, 1500, 3000, 6000, 12000]),
    ("Followers", "followers", [1, 5, 15, 40, 100, 300, 800, 2000]),
    ("Pull Requests", "prs", [1, 5, 20, 60, 150, 400, 900, 2000]),
    ("Issues", "issues", [1, 5, 15, 40, 100, 250, 600, 1500]),
    ("Repositories", "public_repos", [1, 5, 10, 20, 40, 70, 120, 200]),
    ("Reviews", "reviews", [1, 5, 15, 40, 100, 250, 600, 1500]),
    ("Experience", "years", [1, 2, 3, 5, 7, 10, 14, 18]),
    ("Streak", "longest_streak", [3, 7, 14, 30, 60, 100, 200, 365]),
    ("Contributions", "contributions_total", [50, 250, 750, 2000, 4000, 8000, 15000, 30000]),
    ("Forks", "forks", [1, 3, 10, 25, 60, 150, 400, 1000]),
    ("Languages", "language_count", [1, 3, 5, 8, 12, 16, 22, 30]),
]


def rank_for(v, th):
    if not v:
        return "-"
    r = "-"
    for name, t in zip(RANKS, th):
        if v >= t:
            r = name
    return r


def derive(d):
    d = dict(d)
    if d.get("created_at") and "years" not in d:
        try:
            created = datetime.fromisoformat(d["created_at"].replace("Z", "+00:00")).date()
            d["years"] = max(0, (date.today() - created).days // 365)
        except Exception:
            pass
    if "language_count" not in d and d.get("languages"):
        d["language_count"] = len(d["languages"])
    return d


def trophy_glyph(i, c1, c2, locked):
    """cup drawn around (0,0), ~64px tall."""
    gid = f"tg{i}"
    defs = f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'
    cup = (
        f'<path d="M-20-30H20V-8A20 20 0 0 1-20-8Z" fill="url(#{gid})"/>'
        f'<path d="M-20-24H-30V-18A12 12 0 0 0-19-6M20-24H30V-18A12 12 0 0 1 19-6" fill="none" stroke="url(#{gid})" stroke-width="5" stroke-linecap="round"/>'
        f'<rect x="-5" y="12" width="10" height="14" fill="url(#{gid})"/><path d="M-18 34Q-18 26-8 26H8Q18 26 18 34Z" fill="url(#{gid})"/>'
    )
    if not locked:
        cup += (
            '<polygon points="0,-24 3.2,-16.5 11,-16 5,-10.5 7,-2.5 0,-7 -7,-2.5 -5,-10.5 -11,-16 -3.2,-16.5" fill="#fff" fill-opacity=".85"/>'
            f'<clipPath id="cl{i}"><path d="M-20-30H20V-8A20 20 0 0 1-20-8Z"/></clipPath>'
            f'<g clip-path="url(#cl{i})"><rect x="-40" y="-40" width="14" height="80" fill="#fff" fill-opacity=".45" transform="skewX(-20)">'
            f'<animate attributeName="x" values="-60;60" dur="3.4s" begin="{i * .35:.2f}s" repeatCount="indefinite"/></rect></g>'
        )
    else:
        cup += '<text y="-8" text-anchor="middle" class="m" font-size="20" font-weight="800" fill="#64748b">?</text>'
    return defs, cup


def render_trophies(d):
    d = derive(d)
    cols, tw, th, gap = 6, 140, 156, 12
    rows = math.ceil(len(TROPHIES) / cols)
    h = rows * th + (rows - 1) * gap
    css = (
        ".k{animation:up .6s cubic-bezier(.2,.8,.2,1) both}@keyframes up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
        ".fl{animation:bob 3.6s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-3px)}}"
    )
    defs = ""
    b = []
    for i, (label, key, th_) in enumerate(TROPHIES):
        v = val(d, key)
        r = rank_for(v, th_)
        locked = r == "-"
        c1, c2 = RANK_COL[r]
        x = (i % cols) * (tw + gap)
        y = (i // cols) * (th + gap)
        gdefs, cup = trophy_glyph(i, c1, c2, locked)
        defs += gdefs
        edge = c2 if not locked else "#334155"
        nxt = ""
        if not locked and r != "SSS":
            t = th_[RANKS.index(r) + 1]
            nxt = f"next {fmt_num(t)}"
        elif locked:
            nxt = f"unlock at {fmt_num(th_[0])}"
        else:
            nxt = "max rank"
        b.append(
            f'<g transform="translate({x} {y})"><g class="k" style="animation-delay:{i * .06:.2f}s">'
            f'<rect x=".5" y=".5" width="{tw - 1}" height="{th - 1}" rx="16" fill="#0c1324" stroke="{edge}" stroke-opacity="{.25 if locked else .6}"/>'
            f'<rect x=".5" y=".5" width="{tw - 1}" height="{th - 1}" rx="16" fill="{c2}" fill-opacity="{.02 if locked else .08}"/>'
            f'<rect x="{tw / 2 - 20}" y="0" width="40" height="3" rx="1.5" fill="{c2}" fill-opacity="{.3 if locked else .9}"/>'
            f'<text x="{tw - 12}" y="24" text-anchor="end" class="m" font-size="12" font-weight="800" fill="{c2 if not locked else "#64748b"}">{"" if locked else r}</text>'
            f'<g transform="translate({tw / 2} 62)" opacity="{.55 if locked else 1}"><g class="fl" style="animation-delay:{i * .25:.2f}s">{cup}</g></g>'
            f'<text x="{tw / 2}" y="116" text-anchor="middle" class="s" font-size="12.5" font-weight="800" letter-spacing="1" fill="{TXT if not locked else MUTED}">{esc(label.upper())}</text>'
            f'<text x="{tw / 2}" y="134" text-anchor="middle" class="m" font-size="13" font-weight="700" fill="{c2 if not locked else "#64748b"}">{fmt_num(v) if not locked else "locked"}</text>'
            f'<text x="{tw / 2}" y="148" text-anchor="middle" class="m" font-size="9" fill="{MUTED}">{esc(nxt)}</text></g></g>'
        )
    return wrap(W, h, "Trophy room", "Local GitHub trophies ranked C to SSS from your stats.", "".join(b), css, defs)


def render_all(d, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in (("stats.svg", render_stats), ("languages.svg", render_languages), ("activity.svg", render_activity), ("trophies.svg", render_trophies)):
        (out / name).write_text(fn(d), encoding="utf-8")
        print("  wrote", out / name)


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "stats.json"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ASSETS
    data = json.loads(src.read_text()) if src.exists() else {}
    render_all(data, dst)
