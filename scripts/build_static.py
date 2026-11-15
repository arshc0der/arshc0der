#!/usr/bin/env python3
"""Builds every static SVG used by README.md into ./assets.

Everything is generated from the local ./icons and ./SVG-Badges folders, so the
README never depends on a third-party image server. Standard library only.

    python3 scripts/build_static.py
"""
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import *  # noqa: E402,F401,F403

W = 900


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def write(name, content):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(content, encoding="utf-8")
    print(f"  {name:<28}{len(content) / 1024:8.1f} KB")


def keyframes(points, total):
    """points: [(t_seconds, value)] -> (values, keyTimes) strings, de-duplicated."""
    pts = []
    for t, v in points:
        k = round(min(max(t / total, 0), 1), 5)
        if pts and pts[-1][0] == k and pts[-1][1] == v:
            continue
        pts.append((k, v))
    if pts[0][0] != 0:
        pts.insert(0, (0, pts[0][1]))
    if pts[-1][0] != 1:
        pts.append((1, pts[-1][1]))
    return ";".join(str(v) for _, v in pts), ";".join(str(k) for k, _ in pts)


def frame(w, h, rx=18, extra=""):
    return (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="url(#bg)" '
        f'stroke="{LINE}" {extra}/>'
    )


def bg_defs(w, h):
    return (
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1222"/>'
        f'<stop offset="1" stop-color="{BG0}"/></linearGradient>'
        f'<clipPath id="clipAll"><rect width="{w}" height="{h}" rx="18"/></clipPath>'
    )


def stars(n, w, h, seed, ymin=0):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(8, w - 8), rnd.uniform(ymin + 6, h - 6)
        r = rnd.choice([0.6, 0.8, 1.0, 1.3])
        d = rnd.uniform(2.5, 6)
        b = -rnd.uniform(0, 6)
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#cfe8ff">'
            f'<animate attributeName="opacity" values=".15;.9;.15" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


# --------------------------------------------------------------------------- #
# 1. HERO
# --------------------------------------------------------------------------- #
def hero():
    w, h = W, 360
    roles = [
        "Full-Stack Developer",
        "Tech Enthusiast",
        "Lifelong Learner",
        "Building AI, Cloud & Security projects",
    ]
    fs = 22
    cw = fs * 0.6
    slot = 4.4
    total = slot * len(roles)

    css = (
        ".l{animation:fin .6s ease-out both}"
        "@keyframes fin{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
        ".h{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}"
        ".blink{animation:blink 1.05s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
    )

    defs = bg_defs(w, h)
    defs += (
        f'<linearGradient id="gHead" gradientUnits="userSpaceOnUse" x1="300" y1="0" x2="560" y2="0" spreadMethod="reflect">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/>'
        f'<animate attributeName="x1" values="300;560;300" dur="9s" repeatCount="indefinite"/>'
        f'<animate attributeName="x2" values="560;820;560" dur="9s" repeatCount="indefinite"/></linearGradient>'
        f'<linearGradient id="gBar" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{LIME}"/></linearGradient>'
        f'<linearGradient id="gRing" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>'
        '<filter id="glow" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="9"/></filter>'
        '<radialGradient id="a1"><stop offset="0" stop-color="#22d3ee" stop-opacity=".30"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="a2"><stop offset="0" stop-color="#a78bfa" stop-opacity=".34"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="a3"><stop offset="0" stop-color="#f472b6" stop-opacity=".26"/><stop offset="1" stop-color="#f472b6" stop-opacity="0"/></radialGradient>'
        '<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#fff" stroke-opacity=".045"/></pattern>'
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" fill-opacity=".035"/></pattern>'
        '<radialGradient id="gridFade" cx=".5" cy=".55" r=".7"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
        f'<mask id="gridMask"><rect width="{w}" height="{h}" fill="url(#gridFade)"/></mask>'
        '<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22d3ee" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#22d3ee" stop-opacity=".10"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></linearGradient>'
    )
    # typing clip paths
    tx = 70
    ty = 292
    for i, r in enumerate(roles):
        tw = len(r) * cw
        s = i * slot
        pts = [(0, 0), (s, 0), (s + slot * 0.45, tw), (s + slot * 0.88, tw), (s + slot, 0), (total, 0)]
        v, k = keyframes(pts, total)
        defs += (
            f'<clipPath id="rc{i}"><rect x="{tx}" y="{ty - 4}" width="0" height="34">'
            f'<animate attributeName="width" values="{v}" keyTimes="{k}" dur="{total}s" repeatCount="indefinite"/></rect></clipPath>'
        )

    b = [f'<g clip-path="url(#clipAll)">', frame(w, h)]
    b.append(f'<rect width="{w}" height="{h}" fill="url(#grid)" mask="url(#gridMask)"/>')
    # aurora blobs
    b.append(
        '<circle cx="180" cy="70" r="230" fill="url(#a1)"><animate attributeName="cx" values="180;260;180" dur="14s" repeatCount="indefinite"/>'
        '<animate attributeName="cy" values="70;120;70" dur="11s" repeatCount="indefinite"/></circle>'
        '<circle cx="640" cy="330" r="260" fill="url(#a2)"><animate attributeName="cx" values="640;560;640" dur="16s" repeatCount="indefinite"/>'
        '<animate attributeName="cy" values="330;280;330" dur="12s" repeatCount="indefinite"/></circle>'
        '<circle cx="800" cy="60" r="200" fill="url(#a3)"><animate attributeName="cx" values="800;730;800" dur="13s" repeatCount="indefinite"/></circle>'
    )
    b.append(stars(46, w, h, 7, 40))
    # window chrome
    b.append(f'<rect x="0" y="0" width="{w}" height="40" fill="#fff" fill-opacity=".035"/>')
    b.append(f'<path d="M0 40.5H{w}" stroke="{LINE}"/>')
    b.append(
        '<circle cx="24" cy="20" r="6" fill="#ff5f57"/><circle cx="46" cy="20" r="6" fill="#febc2e"/><circle cx="68" cy="20" r="6" fill="#28c840"/>'
    )
    b.append(
        f'<text x="{w / 2}" y="25" text-anchor="middle" class="m" font-size="12.5" fill="{MUTED}">arsh@dev: ~/boot — zsh</text>'
    )
    b.append(
        f'<circle cx="{w - 88}" cy="20" r="4" fill="{EMERALD}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>'
        f'<text x="{w - 76}" y="24.5" class="m" font-size="12" fill="{EMERALD}">online</text>'
    )
    # boot log
    log = [
        ("Reached target", "full-stack.target"),
        ("Started", "cloud.service"),
        ("Started", "security.service"),
        ("Mounted", "/skills  (74 modules)"),
        ("Listening on", "arshdev.in"),
    ]
    for i, (verb, what) in enumerate(log):
        y = 72 + i * 20
        d = 0.25 + i * 0.32
        b.append(
            f'<g class="l m" style="animation-delay:{d:.2f}s" font-size="13">'
            f'<text x="44" y="{y}" fill="{MUTED}">[</text>'
            f'<text x="66" y="{y}" fill="{EMERALD}" font-weight="700">OK</text>'
            f'<text x="88" y="{y}" fill="{MUTED}">]</text>'
            f'<text x="108" y="{y}" fill="{TXT}" fill-opacity=".85">{esc(verb)}</text>'
            f'<text x="244" y="{y}" fill="{CYAN}">{esc(what)}</text></g>'
        )
    # headline
    b.append(
        '<g class="h" style="animation-delay:1.5s">'
        f'<text x="44" y="236" class="s" font-size="68" font-weight="800" fill="url(#gHead)" opacity=".55" filter="url(#glow)">Hi, I\'m Arsh</text>'
        f'<text x="44" y="236" class="s" font-size="68" font-weight="800" fill="{TXT}">Hi, I\'m <tspan fill="url(#gHead)">Arsh</tspan></text>'
        f'<text x="46" y="264" class="m" font-size="14" fill="{MUTED}">@arshc0der  ·  github.com/arshc0der  ·  arshdev.in</text></g>'
    )
    # role typing line
    b.append(f'<text x="44" y="{ty + 17}" class="m" font-size="{fs}" font-weight="700" fill="{LIME}">$</text>')
    for i, r in enumerate(roles):
        b.append(
            f'<g clip-path="url(#rc{i})"><text x="{tx}" y="{ty + 17}" class="m" font-size="{fs}" fill="{TXT}" '
            f'textLength="{len(r) * cw:.1f}" lengthAdjust="spacing">{esc(r)}</text></g>'
        )
        s = i * slot
        tw = len(r) * cw
        pts_x = [(0, tx), (s, tx), (s + slot * 0.45, tx + tw), (s + slot * 0.88, tx + tw), (s + slot, tx), (total, tx)]
        vx, kx = keyframes(pts_x, total)
        pts_o = [(0, 0), (max(s - 0.01, 0), 0), (s, 1), (s + slot - 0.01, 1), (s + slot, 0), (total, 0)]
        vo, ko = keyframes(pts_o, total)
        b.append(
            f'<g opacity="0"><animate attributeName="opacity" values="{vo}" keyTimes="{ko}" dur="{total}s" repeatCount="indefinite"/>'
            f'<rect class="blink" x="{tx}" y="{ty}" width="11" height="24" fill="{LIME}">'
            f'<animate attributeName="x" values="{vx}" keyTimes="{kx}" dur="{total}s" repeatCount="indefinite"/></rect></g>'
        )
    # loading bar
    b.append(
        f'<text x="44" y="342" class="m" font-size="11" fill="{MUTED}">loading /skills</text>'
        f'<rect x="150" y="334" width="706" height="6" rx="3" fill="#fff" fill-opacity=".07"/>'
        f'<rect x="150" y="334" width="0" height="6" rx="3" fill="url(#gBar)">'
        f'<animate attributeName="width" from="0" to="706" dur="3.4s" begin="0.4s" fill="freeze" calcMode="spline" keySplines=".3 .6 .2 1" keyTimes="0;1"/></rect>'
    )
    # emblem
    cx, cy = 780, 190
    b.append(
        f'<g transform="translate({cx} {cy})">'
        f'<circle r="86" fill="none" stroke="{CYAN}" stroke-opacity=".35" stroke-dasharray="3 9">'
        f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="40s" repeatCount="indefinite"/></circle>'
        f'<g><circle r="68" fill="none" stroke="url(#gRing)" stroke-width="2" stroke-dasharray="120 60 40 90" stroke-linecap="round"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="22s" repeatCount="indefinite"/></g>'
        f'<circle r="50" fill="{BG1}" stroke="{LINE}"/>'
        f'<circle r="50" fill="none" stroke="{VIOLET}" stroke-opacity=".5"><animate attributeName="r" values="50;74;50" dur="3.2s" repeatCount="indefinite"/>'
        f'<animate attributeName="stroke-opacity" values=".5;0;.5" dur="3.2s" repeatCount="indefinite"/></circle>'
        f'<text y="19" text-anchor="middle" class="m" font-size="58" font-weight="800" fill="url(#gHead)">A</text>'
        f'<g><circle cx="86" cy="0" r="4.5" fill="{CYAN}"/><circle cx="-86" cy="0" r="3" fill="{PINK}"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="40s" repeatCount="indefinite"/></g>'
        f'</g>'
    )
    # scan beam
    b.append(
        f'<rect x="0" y="-80" width="{w}" height="80" fill="url(#beam)"><animate attributeName="y" values="-80;{h}" dur="7s" repeatCount="indefinite"/></rect>'
        f'<rect width="{w}" height="{h}" fill="url(#scan)"/>'
    )
    b.append("</g>")
    write(
        "hero.svg",
        wrap(w, h, "Arsh — boot sequence banner", "Animated terminal banner: Hi, I'm Arsh. Full-Stack Developer, Tech Enthusiast, Lifelong Learner.", "".join(b), css, defs),
    )


# --------------------------------------------------------------------------- #
# 2. SECTION HEADERS
# --------------------------------------------------------------------------- #
def section(slug, num, title, sub, color):
    w, h = W, 64
    gid = f"gl{slug}"
    defs = (
        f'<linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="{color}"/><stop offset=".6" stop-color="{color}" stop-opacity=".25"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
        '<filter id="gl2"><feGaussianBlur stdDeviation="3"/></filter>'
    )
    css = (
        ".t{animation:slide .8s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes slide{from{opacity:0;transform:translateX(-14px)}to{opacity:1;transform:none}}"
    )
    body = (
        f'<rect x="1" y="6" width="52" height="40" rx="10" fill="{color}" fill-opacity=".12" stroke="{color}" stroke-opacity=".55"/>'
        f'<text x="27" y="33" text-anchor="middle" class="m" font-size="17" font-weight="800" fill="{color}">{num}</text>'
        f'<g class="t"><text x="72" y="36" class="s" font-size="25" font-weight="800" letter-spacing="3" fill="{TXT}">{esc(title)}</text></g>'
        f'<text x="{w}" y="33" text-anchor="end" class="m" font-size="12.5" fill="{MUTED}">{esc(sub)}</text>'
        f'<rect x="72" y="52" width="{w - 72}" height="2" rx="1" fill="url(#{gid})"/>'
        f'<circle cy="53" r="4" fill="{color}" filter="url(#gl2)"><animate attributeName="cx" values="72;{w};72" dur="6s" repeatCount="indefinite"/></circle>'
        f'<circle cy="53" r="2" fill="#fff"><animate attributeName="cx" values="72;{w};72" dur="6s" repeatCount="indefinite"/></circle>'
    )
    write(f"section-{slug}.svg", wrap(w, h, title, sub, body, css, defs))


# --------------------------------------------------------------------------- #
# 3. ABOUT TERMINAL
# --------------------------------------------------------------------------- #
def about():
    w, h = W, 272
    css = (
        ".l{animation:fin .55s ease-out both}"
        "@keyframes fin{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".blink{animation:blink 1.05s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        ".p{animation:pulse 3.4s ease-in-out infinite}@keyframes pulse{50%{opacity:.35}}"
    )
    defs = bg_defs(w, h) + aurora_grad("ag", 0, 220)
    b = [frame(w, h)]
    b.append(f'<rect x="1" y="1" width="{w - 2}" height="38" rx="17" fill="#fff" fill-opacity=".035"/>')
    b.append('<circle cx="24" cy="20" r="6" fill="#ff5f57"/><circle cx="46" cy="20" r="6" fill="#febc2e"/><circle cx="68" cy="20" r="6" fill="#28c840"/>')
    b.append(f'<text x="92" y="25" class="m" font-size="12.5" fill="{MUTED}">~/about.sh</text>')
    lines = [
        (70, 0.2, "cmd", "whoami"),
        (92, 0.7, "out", "arsh  —  full-stack developer, tech enthusiast, lifelong learner"),
        (124, 1.4, "cmd", "cat now.txt"),
        (146, 1.9, "kv", ("currently building", "AI, Cloud & Security projects")),
        (168, 2.2, "kv", ("also hacking on", "MyOS — a hobby x86 operating system")),
        (200, 2.9, "cmd", "ls ~/projects"),
        (222, 3.4, "kv", ("everything lives at", "arshdev.in")),
    ]
    for y, d, kind, val in lines:
        if kind == "cmd":
            b.append(
                f'<g class="l m" style="animation-delay:{d}s" font-size="14.5"><text x="26" y="{y}" fill="{LIME}" font-weight="700">arsh@dev</text>'
                f'<text x="98" y="{y}" fill="{MUTED}">:</text><text x="108" y="{y}" fill="{SKY}">~</text>'
                f'<text x="124" y="{y}" fill="{MUTED}">$</text><text x="144" y="{y}" fill="{TXT}">{esc(val)}</text></g>'
            )
        elif kind == "out":
            b.append(f'<g class="l m" style="animation-delay:{d}s"><text x="26" y="{y}" font-size="14.5" fill="{TXT}" fill-opacity=".85">{esc(val)}</text></g>')
        else:
            k, v = val
            b.append(
                f'<g class="l m" style="animation-delay:{d}s" font-size="14.5"><text x="26" y="{y}" fill="{VIOLET}">→</text>'
                f'<text x="48" y="{y}" fill="{MUTED}">{esc(k)}</text><text x="226" y="{y}" fill="{CYAN}" font-weight="700">{esc(v)}</text></g>'
            )
    b.append(
        f'<g class="l m" style="animation-delay:3.9s" font-size="14.5"><text x="26" y="252" fill="{LIME}" font-weight="700">arsh@dev</text>'
        f'<text x="98" y="252" fill="{MUTED}">:</text><text x="108" y="252" fill="{SKY}">~</text><text x="124" y="252" fill="{MUTED}">$</text>'
        f'<rect class="blink" x="144" y="238" width="9" height="16" fill="{LIME}"/></g>'
    )
    # right: focus tiles
    fx = 640
    b.append(f'<path d="M{fx - 18} 56V250" stroke="{LINE}"/>')
    b.append(f'<text x="{fx}" y="70" class="m" font-size="11" letter-spacing="2" fill="{MUTED}">CURRENT FOCUS</text>')
    tiles = [
        ("AI", "models · agents · data", CYAN, "ai"),
        ("CLOUD", "deploy · scale · observe", VIOLET, "cloud"),
        ("SECURITY", "harden · audit · defend", PINK, "sec"),
    ]
    for i, (name, sub, col, kind) in enumerate(tiles):
        y = 86 + i * 54
        b.append(f'<rect x="{fx}" y="{y}" width="244" height="46" rx="12" fill="{col}" fill-opacity=".07" stroke="{col}" stroke-opacity=".35"/>')
        gx, gy = fx + 26, y + 23
        if kind == "ai":
            nodes = [(-9, -8), (-9, 0), (-9, 8), (0, -5), (0, 5), (9, -8), (9, 0), (9, 8)]
            edges = [(0, 3), (1, 3), (1, 4), (2, 4), (3, 5), (3, 6), (4, 6), (4, 7)]
            g = "".join(
                f'<path d="M{nodes[a][0]} {nodes[a][1]}L{nodes[c][0]} {nodes[c][1]}" stroke="{col}" stroke-opacity=".6"/>' for a, c in edges
            )
            g += "".join(
                f'<circle cx="{x}" cy="{y2}" r="2.4" fill="{col}"><animate attributeName="opacity" values="1;.3;1" dur="{2 + (n % 3) * .6:.1f}s" begin="-{n * .4:.1f}s" repeatCount="indefinite"/></circle>'
                for n, (x, y2) in enumerate(nodes)
            )
        elif kind == "cloud":
            g = (
                f'<path d="M-11 6a6 6 0 0 1 1-12 8 8 0 0 1 15-2 6.5 6.5 0 0 1 5 14z" fill="none" stroke="{col}" stroke-width="1.8" stroke-linejoin="round"/>'
                f'<path d="M0 8V-1M-3 2l3-3 3 3" stroke="{col}" stroke-width="1.6" fill="none" stroke-linecap="round" class="p"/>'
            )
        else:
            g = (
                f'<path d="M0-12 11-8V1c0 6-5 10-11 13C-6 11-11 7-11 1V-8z" fill="none" stroke="{col}" stroke-width="1.8" stroke-linejoin="round"/>'
                f'<path d="M-4 1l3 3 6-7" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="p"/>'
            )
        b.append(f'<g transform="translate({gx} {gy})">{g}</g>')
        b.append(f'<text x="{fx + 52}" y="{y + 20}" class="s" font-size="14" font-weight="800" letter-spacing="1.5" fill="{TXT}">{name}</text>')
        b.append(f'<text x="{fx + 52}" y="{y + 36}" class="m" font-size="11" fill="{MUTED}">{esc(sub)}</text>')
    write("about.svg", wrap(w, h, "About Arsh", "Terminal-style about card: building AI, Cloud and Security projects; projects at arshdev.in.", "".join(b), css, defs))


# --------------------------------------------------------------------------- #
# 4. ORBIT
# --------------------------------------------------------------------------- #
SOCIAL_ICONS = {"linked-in", "youtube", "hackerrank", "leet-code"}
INNER = ["python-original", "javascript-original", "typescript-original", "react-original-wordmark", "node-js", "docker-original"]
MID = [
    "java-original", "c", "cplusplus", "html", "css", "next-js", "express-original-wordmark",
    "mongodb-original-wordmark", "mysql-original-wordmark", "postgresql-original-wordmark", "git", "linux-original",
]


def orbit():
    w, h = W, 440
    cx, cy, tilt = 450, 220, -8
    all_icons = sorted(p.stem for p in ICONS.glob("*.svg"))
    orbit_icons = [i for i in all_icons if i not in SOCIAL_ICONS]
    outer = [i for i in orbit_icons if i not in INNER and i not in MID]
    rings = [
        (INNER, 168, 60, 26, 30, 1, CYAN),
        (MID, 294, 106, 24, 46, -1, VIOLET),
        (outer, 418, 150, 21, 78, 1, PINK),
    ]
    K = 48
    defs = bg_defs(w, h) + (
        '<radialGradient id="hub"><stop offset="0" stop-color="#a78bfa" stop-opacity=".55"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="core" cx=".35" cy=".3"><stop offset="0" stop-color="#1e2b4d"/><stop offset="1" stop-color="#0a1020"/></radialGradient>'
        + aurora_grad("ag", 0, 120)
    )
    css = ".d{animation:dash 40s linear infinite}@keyframes dash{to{stroke-dashoffset:-400}}"
    b = [f'<g clip-path="url(#clipAll)">', frame(w, h, 20), stars(60, w, h, 3), f'<circle cx="{cx}" cy="{cy}" r="150" fill="url(#hub)"/>']
    b.append(f'<g transform="translate({cx} {cy}) rotate({tilt})">')
    for (_, rx, ry, _r, _dur, _dir, col) in rings:
        b.append(f'<ellipse rx="{rx}" ry="{ry}" fill="none" stroke="{col}" stroke-opacity=".28" stroke-dasharray="2 8" class="d"/>')
    b.append("</g>")
    # hub
    b.append(
        f'<circle cx="{cx}" cy="{cy}" r="46" fill="none" stroke="{CYAN}" stroke-opacity=".5"><animate attributeName="r" values="46;78;46" dur="4s" repeatCount="indefinite"/>'
        f'<animate attributeName="stroke-opacity" values=".5;0;.5" dur="4s" repeatCount="indefinite"/></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="46" fill="url(#core)" stroke="{VIOLET}" stroke-opacity=".6"/>'
        f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" class="m" font-size="21" font-weight="800" fill="url(#ag)" letter-spacing="2">STACK</text>'
        f'<text x="{cx}" y="{cy + 22}" text-anchor="middle" class="m" font-size="10" fill="{MUTED}" letter-spacing="2">40 TOOLS</text>'
    )
    b.append(f'<g transform="translate({cx} {cy}) rotate({tilt})">')
    for (names, rx, ry, rad, dur, direction, col) in rings:
        n = len(names)
        for i, name in enumerate(names):
            phase = i / n
            pos, scl, opa = [], [], []
            for k in range(K + 1):
                th = direction * 2 * math.pi * k / K
                x, y = rx * math.cos(th), ry * math.sin(th)
                d = (math.sin(th) + 1) / 2
                pos.append(f"{x:.1f},{y:.1f}")
                scl.append(f"{0.74 + 0.26 * d:.3f}")
                opa.append(f"{0.5 + 0.5 * d:.3f}")
            begin = f"-{phase * dur:.2f}s"
            anim = lambda kind, vals: (
                f'<animateTransform attributeName="transform" type="{kind}" values="{";".join(vals)}" dur="{dur}s" begin="{begin}" repeatCount="indefinite"/>'
            )
            ico = rad * 1.22
            b.append(
                f'<g>{anim("translate", pos)}<g transform="rotate({-tilt})"><g>{anim("scale", scl)}'
                f'<animate attributeName="opacity" values="{";".join(opa)}" dur="{dur}s" begin="{begin}" repeatCount="indefinite"/>'
                f'<circle r="{rad}" fill="#eef3fb" stroke="{col}" stroke-opacity=".8" stroke-width="2"/>'
                f'<image x="{-ico / 2:.1f}" y="{-ico / 2:.1f}" width="{ico:.1f}" height="{ico:.1f}" preserveAspectRatio="xMidYMid meet" href="{data_uri(ICONS / (name + ".svg"))}"/>'
                f"</g></g></g>"
            )
    b.append("</g></g>")
    write("orbit.svg", wrap(w, h, "Tech constellation", "Animated orbit of 40 technology icons around a central STACK hub.", "".join(b), css, defs))


# --------------------------------------------------------------------------- #
# 5. STACK CARDS (all 74 local badges)
# --------------------------------------------------------------------------- #
GROUPS = [
    # slug, [(title, accent, [badge numbers])]
    ("languages", [("Languages & Markup", CYAN, [1, 2, 6, 3, 8, 13, 11, 7, 10, 12, 4, 5, 9])]),
    ("frontend", [("Frontend & UI", VIOLET, [31, 38, 40, 39, 34, 24, 36, 37, 35, 23, 25])]),
    ("backend", [("Backend & Servers", LIME, [30, 26, 32, 27, 28, 29, 33, 22, 42, 41, 43])]),
    ("data-cloud", [("Databases", AMBER, [46, 47, 45, 50, 51, 48, 49, 44]), ("Cloud & Hosting", SKY, [16, 14, 18, 17, 19, 20, 15])]),
    ("devops", [("DevOps, Testing & Workflow", ROSE, [69, 71, 62, 64, 63, 73, 70, 66, 65, 68])]),
    (
        "misc",
        [("Data Science", EMERALD, [21, 60, 59, 57, 58, 61]), ("Design", PINK, [54, 52, 53, 55, 56]), ("Hardware & Graphics", CYAN, [67, 72, 74])],
    ),
]


def load_badge(n):
    path = next(BADGES.glob(f"{n:02d}-*.svg"))
    s = path.read_text(encoding="utf-8")
    m = re.search(r'<svg[^>]*?width="([\d.]+)"[^>]*?height="([\d.]+)"[^>]*>(.*)</svg>', s, re.S)
    return float(m[1]), float(m[2]), m[3], path.stem


def stack_row(slug, cards):
    gap, pad, outer = 14, 22, 10
    cw = (W - gap * (len(cards) - 1)) / len(cards)
    laid = []
    for title, col, nums in cards:
        x = pad
        y = 0
        rows = [[]]
        for n in nums:
            bw, bh, inner, stem = load_badge(n)
            if x + bw > cw - pad and rows[-1]:
                rows.append([])
                x = pad
            rows[-1].append((x, bw, bh, inner, stem, n))
            x += bw + 10
        laid.append((title, col, rows))
    inner_h = max(len(r) for _, _, r in laid) * 38 - 10
    ch = 22 + 34 + inner_h + 22
    h = ch + outer
    defs = (
        '<linearGradient id="cardbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#111b33"/><stop offset="1" stop-color="#0a1020"/></linearGradient>'
        '<linearGradient id="sheen" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    )
    css = ".b{animation:up .55s cubic-bezier(.2,.8,.2,1) both}@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
    body = []
    idx = 0
    for ci, (title, col, rows) in enumerate(laid):
        x0 = ci * (cw + gap)
        cid = f"cc{ci}"
        defs += f'<clipPath id="{cid}"><rect width="{cw:.1f}" height="{ch}" rx="16"/></clipPath>'
        count = sum(len(r) for r in rows)
        g = [f'<g transform="translate({x0:.1f} 0)">']
        g.append(f'<rect x=".5" y=".5" width="{cw - 1:.1f}" height="{ch - 1}" rx="16" fill="url(#cardbg)" stroke="{LINE}"/>')
        g.append(f'<g clip-path="url(#{cid})"><rect x="0" y="0" width="{cw:.1f}" height="3" fill="{col}" fill-opacity=".9"/>')
        g.append(
            f'<rect x="-120" y="0" width="120" height="{ch}" fill="url(#sheen)" transform="skewX(-18)"><animate attributeName="x" values="-160;{cw + 80:.0f}" dur="7s" begin="{ci * 1.3:.1f}s" repeatCount="indefinite"/></rect></g>'
        )
        g.append(f'<circle cx="{pad + 4}" cy="38" r="4.5" fill="{col}"><animate attributeName="opacity" values="1;.35;1" dur="2.6s" repeatCount="indefinite"/></circle>')
        g.append(f'<text x="{pad + 18}" y="43" class="m" font-size="13" font-weight="800" letter-spacing="1.6" fill="{TXT}">{esc(title.upper())}</text>')
        g.append(f'<rect x="{cw - pad - 38:.1f}" y="26" width="38" height="22" rx="11" fill="{col}" fill-opacity=".14" stroke="{col}" stroke-opacity=".5"/>')
        g.append(f'<text x="{cw - pad - 19:.1f}" y="41" text-anchor="middle" class="m" font-size="12" font-weight="800" fill="{col}">{count}</text>')
        for ri, row in enumerate(rows):
            for (bx, bw, bh, inner, stem, n) in row:
                by = 62 + ri * 38
                idx += 1
                g.append(
                    f'<g class="b" style="animation-delay:{0.04 * idx:.2f}s"><clipPath id="bc{n}"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="7"/></clipPath>'
                    f'<g clip-path="url(#bc{n})"><svg x="{bx}" y="{by}" width="{bw}" height="{bh}" viewBox="0 0 {bw} {bh}">{inner}</svg></g>'
                    f'<rect x="{bx + .5}" y="{by + .5}" width="{bw - 1}" height="{bh - 1}" rx="6.5" fill="none" stroke="#fff" stroke-opacity=".16"/></g>'
                )
        g.append("</g>")
        body.append("".join(g))
    names = " / ".join(t for t, _, _ in cards)
    write(f"stack-{slug}.svg", wrap(W, h, names, f"Technology badges: {names}", "".join(body), css, defs))


# --------------------------------------------------------------------------- #
# 6. SOCIAL PILLS, COFFEE
# --------------------------------------------------------------------------- #
def pill(slug, label, sub, color, icon_xml, w=168):
    h = 52
    defs = (
        f'<linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="{color}" stop-opacity=".22"/><stop offset="1" stop-color="{color}" stop-opacity=".04"/></linearGradient>'
        '<linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="pc"><rect width="{w}" height="{h}" rx="14"/></clipPath>'
    )
    body = (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="#0c1324"/><rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="url(#pg)" stroke="{color}" stroke-opacity=".55"/>'
        f'<g clip-path="url(#pc)"><rect x="-60" width="50" height="{h}" fill="url(#sh)" transform="skewX(-20)"><animate attributeName="x" values="-80;{w + 40}" dur="4.5s" repeatCount="indefinite"/></rect></g>'
        f'<g transform="translate(16 15)">{icon_xml}</g>'
        f'<text x="52" y="23" class="s" font-size="14.5" font-weight="800" fill="{TXT}">{esc(label)}</text>'
        f'<text x="52" y="38" class="m" font-size="10.5" fill="{MUTED}">{esc(sub)}</text>'
    )
    write(f"social-{slug}.svg", wrap(w, h, label, f"{label} link button", body, "", defs))


def img_icon(name, size=22):
    return f'<image width="{size}" height="{size}" preserveAspectRatio="xMidYMid meet" href="{data_uri(ICONS / (name + ".svg"))}"/>'


def socials():
    pill("linkedin", "LinkedIn", "in/arshmd", "#3b82f6", img_icon("linked-in"))
    pill("youtube", "YouTube", "@Code.ByArsh", "#ff3b3b", img_icon("youtube"))
    pill("hackerrank", "HackerRank", "arshc0der", "#2ec866", img_icon("hackerrank"))
    pill("leetcode", "LeetCode", "arshc0der", "#ffa116", img_icon("leet-code"))
    globe = (
        f'<g fill="none" stroke="{CYAN}" stroke-width="1.6" transform="translate(11 11)"><circle r="10"/><ellipse rx="4.6" ry="10"/>'
        f'<path d="M-10 0h20M-8.6-5h17.2M-8.6 5h17.2"/></g>'
    )
    pill("portfolio", "Portfolio", "arshdev.in", CYAN, globe)
    cup = (
        f'<g fill="none" stroke="{AMBER}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"><path d="M3 7h14v6a6 6 0 0 1-6 6H9a6 6 0 0 1-6-6z"/>'
        f'<path d="M17 9h2a2.5 2.5 0 0 1 0 5h-2"/><path d="M7 2v2M11 2v2M15 2v2" class="s"/></g>'
    )
    pill("coffee", "Buy me a coffee", "support the work", AMBER, cup.replace('translate', 'translate'), w=190)


# --------------------------------------------------------------------------- #
# 7. MYOS FEATURE CARD
# --------------------------------------------------------------------------- #
def myos():
    w, h = W, 250
    css = (
        ".l{animation:fin .5s ease-out both}@keyframes fin{from{opacity:0}to{opacity:1}}"
        ".blink{animation:blink 1.05s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    )
    defs = bg_defs(w, h) + aurora_grad("ag", 360, 700) + (
        '<linearGradient id="scr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#050a14"/><stop offset="1" stop-color="#02050b"/></linearGradient>'
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" fill-opacity=".04"/></pattern>'
        '<clipPath id="scrc"><rect x="26" y="52" width="300" height="172" rx="6"/></clipPath>'
    )
    b = ['<g clip-path="url(#clipAll)">', frame(w, h)]
    b.append('<circle cx="760" cy="40" r="220" fill="#a78bfa" fill-opacity=".08"/><circle cx="100" cy="240" r="180" fill="#22d3ee" fill-opacity=".07"/>')
    # qemu window
    b.append(f'<rect x="18" y="20" width="316" height="208" rx="10" fill="#0a1020" stroke="{LINE}"/>')
    b.append(f'<rect x="19" y="21" width="314" height="26" rx="9" fill="#fff" fill-opacity=".05"/>')
    b.append('<circle cx="34" cy="34" r="4.5" fill="#ff5f57"/><circle cx="50" cy="34" r="4.5" fill="#febc2e"/><circle cx="66" cy="34" r="4.5" fill="#28c840"/>')
    b.append(f'<text x="176" y="38" text-anchor="middle" class="m" font-size="11" fill="{MUTED}">QEMU — MyOS</text>')
    b.append('<rect x="26" y="52" width="300" height="172" rx="6" fill="url(#scr)"/>')
    lines = [
        (74, 0.3, MUTED, "GNU GRUB  Multiboot loader"),
        (94, 0.9, TXT, "Loading MyOS kernel ..."),
        (114, 1.5, EMERALD, "[ ok ] 32-bit protected mode"),
        (134, 2.1, EMERALD, "[ ok ] kernel entry reached"),
        (154, 2.7, EMERALD, "[ ok ] console ready"),
    ]
    for y, d, col, t in lines:
        b.append(f'<text class="l m" style="animation-delay:{d}s" x="38" y="{y}" font-size="12" fill="{col}">{esc(t)}</text>')
    b.append(f'<g class="l m" style="animation-delay:3.4s"><text x="38" y="186" font-size="14" font-weight="700" fill="{CYAN}">Welcome to MyOS</text>')
    b.append(f'<text x="38" y="208" font-size="12" fill="{LIME}">myos&gt;</text><rect class="blink" x="82" y="197" width="8" height="13" fill="{LIME}"/></g>')
    b.append('<rect x="26" y="52" width="300" height="172" rx="6" fill="url(#scan)"/>')
    # text side
    x = 372
    b.append(f'<text x="{x}" y="52" class="m" font-size="11" letter-spacing="2.5" fill="{MUTED}">FEATURED PROJECT</text>')
    b.append(f'<text x="{x}" y="104" class="s" font-size="52" font-weight="800" fill="url(#ag)">MyOS</text>')
    b.append(f'<text x="{x}" y="132" class="s" font-size="16" fill="{TXT}" fill-opacity=".9">A 32-bit x86 hobby operating system, built from scratch.</text>')
    chips = ["C", "Assembly", "GRUB / Multiboot", "QEMU", "MIT"]
    cx_ = x
    for c in chips:
        cwid = 16 + len(c) * 7.4
        b.append(
            f'<rect x="{cx_:.1f}" y="150" width="{cwid:.1f}" height="26" rx="13" fill="#fff" fill-opacity=".05" stroke="{VIOLET}" stroke-opacity=".5"/>'
            f'<text x="{cx_ + cwid / 2:.1f}" y="167.5" text-anchor="middle" class="m" font-size="12" fill="{TXT}">{esc(c)}</text>'
        )
        cx_ += cwid + 8
    b.append(f'<text x="{x}" y="200" class="m" font-size="12.5" fill="{MUTED}">Bootable ISO and full source published as GitHub releases.</text>')
    b.append(
        f'<rect x="{x}" y="212" width="236" height="26" rx="13" fill="{CYAN}" fill-opacity=".12" stroke="{CYAN}" stroke-opacity=".6"/>'
        f'<text x="{x + 118}" y="229.5" text-anchor="middle" class="m" font-size="12" font-weight="700" fill="{CYAN}">github.com/arshc0der/myOS  →</text>'
    )
    b.append("</g>")
    write("myos.svg", wrap(w, h, "MyOS", "Featured project: MyOS, a 32-bit x86 hobby operating system written in C and assembly.", "".join(b), css, defs))


# --------------------------------------------------------------------------- #
# 8. QUOTES + FOOTER
# --------------------------------------------------------------------------- #
def quotes():
    w, h = W, 92
    qs = [
        "Read the source. Then read it again.",
        "Every bug is a lesson in disguise.",
        "Build it small, break it early, ship it often.",
        "Curiosity compiles faster than ambition.",
        "Today's side project is tomorrow's skill set.",
    ]
    slot = 4.5
    total = slot * len(qs)
    defs = bg_defs(w, h) + aurora_grad("ag", 0, 900)
    b = [frame(w, h, 16)]
    b.append(f'<text x="36" y="62" class="m" font-size="46" font-weight="800" fill="url(#ag)">{{</text>')
    b.append(f'<text x="{w - 36}" y="62" text-anchor="end" class="m" font-size="46" font-weight="800" fill="url(#ag)">}}</text>')
    for i, q in enumerate(qs):
        s = i * slot
        pts = [(0, 0), (max(s - .01, 0), 0), (s + .5, 1), (s + slot - .5, 1), (s + slot, 0), (total, 0)]
        v, k = keyframes(pts, total)
        b.append(
            f'<text x="{w / 2}" y="54" text-anchor="middle" class="m" font-size="19" fill="{TXT}" opacity="0">{esc(q)}'
            f'<animate attributeName="opacity" values="{v}" keyTimes="{k}" dur="{total}s" repeatCount="indefinite"/></text>'
        )
    b.append(f'<text x="{w / 2}" y="80" text-anchor="middle" class="m" font-size="10.5" letter-spacing="3" fill="{MUTED}">DEV NOTES</text>')
    write("quotes.svg", wrap(w, h, "Dev notes", "Rotating one-line developer notes.", "".join(b), "", defs))


def footer():
    w, h = W, 150
    defs = bg_defs(w, h) + aurora_grad("ag", 0, 900) + (
        '<linearGradient id="wv1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22d3ee" stop-opacity=".35"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="wv2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a78bfa" stop-opacity=".35"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="wv3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f472b6" stop-opacity=".3"/><stop offset="1" stop-color="#f472b6" stop-opacity="0"/></linearGradient>'
    )

    def wave(amp, period, y0, gid, dur, rev=False):
        pts = []
        n = int((w + 2 * period) / 10)
        for i in range(n + 1):
            x = i * 10
            pts.append(f"{x},{y0 + amp * math.sin(2 * math.pi * x / period):.1f}")
        d = "M" + " L".join(pts) + f" L{n * 10},{h} L0,{h} Z"
        a, b_ = (0, -period) if not rev else (-period, 0)
        return (
            f'<path d="{d}" fill="url(#{gid})"><animateTransform attributeName="transform" type="translate" from="{a} 0" to="{b_} 0" dur="{dur}s" repeatCount="indefinite"/></path>'
        )

    b = ['<g clip-path="url(#clipAll)">', frame(w, h)]
    b.append(stars(30, w, h, 11))
    b.append(wave(8, 300, 92, "wv1", 14) + wave(10, 450, 100, "wv2", 20, True) + wave(6, 220, 108, "wv3", 11))
    b.append(f'<text x="{w / 2}" y="52" text-anchor="middle" class="s" font-size="22" font-weight="800" fill="url(#ag)">Thanks for stopping by.</text>')
    b.append(f'<text x="{w / 2}" y="76" text-anchor="middle" class="m" font-size="12" fill="{MUTED}">every badge, icon, trophy and chart on this page is served from this repository.</text>')
    b.append("</g>")
    write("footer.svg", wrap(w, h, "Footer", "Animated wave footer.", "".join(b), "", defs))


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("building static assets ->", ASSETS)
    import build_hero  # 3D globe hero (embeds assets/photo.* when present)

    build_hero.hero()
    section("about", "01", "ABOUT", "whoami --verbose", CYAN)
    section("orbit", "02", "TECH CONSTELLATION", "40 tools · always in motion", VIOLET)
    section("arsenal", "03", "ARSENAL", "74 badges · all local", LIME)
    section("featured", "04", "FEATURED BUILD", "from the lab", AMBER)
    section("telemetry", "05", "TELEMETRY", "live from the GitHub API", SKY)
    section("trophies", "06", "TROPHY ROOM", "earned, not given", PINK)
    section("connect", "07", "CONNECT", "find me around the web", ROSE)
    about()
    orbit()
    for slug, cards in GROUPS:
        stack_row(slug, cards)
    socials()
    myos()
    quotes()
    footer()
    print("done")
