#!/usr/bin/env python3
"""Builds assets/hero.svg: a rotating 3D dotted globe with your portrait at its core.

Put your photo at  assets/photo.jpg  (or .png / .jpeg / .webp), then run:

    python scripts/build_hero.py

The photo is embedded inside the SVG, so the hero never depends on another server.
With no photo present, a neutral silhouette is drawn instead.
Optional: if Pillow is installed the photo is auto-cropped square and shrunk.
"""
import base64
import io
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import *  # noqa: E402,F401,F403

W, H = 900, 470
CX, CY = 655, 235  # globe centre
R = 166  # globe radius
PR = 90  # portrait radius
TILT = math.radians(20)
K = 36  # keyframes per rotation
SPIN = 70  # seconds per rotation


# --------------------------------------------------------------------------- #
def keyframes(points, total):
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


def starfield(n, seed):
    import random

    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(8, W - 8), rnd.uniform(8, H - 8)
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rnd.choice([.6, .8, 1., 1.3])}" fill="#cfe8ff">'
            f'<animate attributeName="opacity" values=".15;.9;.15" dur="{rnd.uniform(2.5, 6):.1f}s" begin="-{rnd.uniform(0, 6):.1f}s" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


def find_photo():
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = ASSETS / f"photo.{ext}"
        if p.exists():
            return p
    return None


def photo_uri(path):
    raw = path.read_bytes()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[path.suffix[1:].lower()]
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(raw)).convert("RGB")
        s = min(im.size)
        l, t = (im.width - s) // 2, (im.height - s) // 2
        im = im.crop((l, t, l + s, t + s)).resize((440, 440), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88, optimize=True)
        raw, mime = buf.getvalue(), "image/jpeg"
    except Exception:
        if len(raw) > 400_000:
            print("  note: photo is large; install Pillow (pip install pillow) to auto-shrink it")
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


# --------------------------------------------------------------------------- #
def project(lat, lon, phi):
    """Sphere point -> (screen x, screen y, depth). Rotation phi about the vertical axis, then tilt."""
    x = math.cos(lat) * math.sin(lon + phi)
    y = math.sin(lat)
    z = math.cos(lat) * math.cos(lon + phi)
    y2 = y * math.cos(TILT) - z * math.sin(TILT)
    z2 = y * math.sin(TILT) + z * math.cos(TILT)
    return R * x, -R * y2, z2


def smooth(a, lo, hi):
    t = min(max((a - lo) / (hi - lo), 0), 1)
    return t * t * (3 - 2 * t)


def globe_dots(n=170):
    golden = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        lat = math.asin(1 - 2 * (i + .5) / n)
        lon = golden * i
        xs, ys, os_, rs = [], [], [], []
        far = 0
        for k in range(K + 1):
            sx, sy, z = project(lat, lon, 2 * math.pi * k / K)
            xs.append(f"{sx:.1f}")
            ys.append(f"{sy:.1f}")
            d = (z + 1) / 2
            os_.append(f"{.1 + .9 * smooth(z, -.25, .9):.2f}")
            far = max(far, math.hypot(sx, sy))
        if far < PR + 2:  # never leaves the portrait: skip
            continue
        dur = SPIN
        out.append(
            f'<circle r="1.7" fill="#9fe9ff"><animate attributeName="cx" values="{";".join(xs)}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{";".join(ys)}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{";".join(os_)}" dur="{dur}s" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


def pin(lat_deg, lon_deg):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    pos, op = [], []
    for k in range(K + 1):
        sx, sy, z = project(lat, lon, 2 * math.pi * k / K)
        pos.append(f"{sx:.1f},{sy:.1f}")
        op.append(f"{smooth(z, .05, .35) * smooth(math.hypot(sx, sy), PR + 2, PR + 16):.2f}")
    return (
        f'<g><animateTransform attributeName="transform" type="translate" values="{";".join(pos)}" dur="{SPIN}s" repeatCount="indefinite"/>'
        f'<g><animate attributeName="opacity" values="{";".join(op)}" dur="{SPIN}s" repeatCount="indefinite"/>'
        f'<circle r="4" fill="none" stroke="{LIME}" stroke-width="1.5"><animate attributeName="r" values="4;16;4" dur="2.4s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;0;1" dur="2.4s" repeatCount="indefinite"/></circle>'
        f'<circle r="4.2" fill="{LIME}"/><circle r="1.6" fill="#fff"/></g></g>'
    )


def satellites(rings):
    """rings: (icons, rx, ry, rot_deg, tile_r, dur, dir, color).
    Returns (defs, back, front). Each icon is drawn twice via <use>: once behind the portrait
    (only while on the far half of its orbit) and once in front of it (near half)."""
    defs, back, front = [], [], []
    for ri, (icons, rx, ry, rot, rad, dur, direction, col) in enumerate(rings):
        back.append(f'<g transform="rotate({rot})"><ellipse rx="{rx}" ry="{ry}" fill="none" stroke="{col}" stroke-opacity=".30" stroke-dasharray="2 7"/>')
        front.append(f'<g transform="rotate({rot})">')
        n = len(icons)
        for i, name in enumerate(icons):
            nid = f"sat{ri}_{i}"
            ico = rad * 1.25
            defs.append(
                f'<g id="{nid}"><circle r="{rad}" fill="#eef3fb" stroke="{col}" stroke-opacity=".85" stroke-width="2"/>'
                f'<image x="{-ico / 2:.1f}" y="{-ico / 2:.1f}" width="{ico:.1f}" height="{ico:.1f}" preserveAspectRatio="xMidYMid meet" href="{data_uri(ICONS / (name + ".svg"))}"/></g>'
            )
            pos, scl, ob, of = [], [], [], []
            for k in range(49):
                th = direction * 2 * math.pi * k / 48
                sn = math.sin(th)
                d = (sn + 1) / 2
                pos.append(f"{rx * math.cos(th):.1f},{ry * sn:.1f}")
                scl.append(f"{.72 + .28 * d:.3f}")
                base = .55 + .45 * d
                ob.append(f"{base * smooth(-sn, -.1, .1):.3f}")
                of.append(f"{base * smooth(sn, -.1, .1):.3f}")
            begin = f"-{i / n * dur:.2f}s"
            tr = lambda kind, v: f'<animateTransform attributeName="transform" type="{kind}" values="{";".join(v)}" dur="{dur}s" begin="{begin}" repeatCount="indefinite"/>'
            op = lambda v: f'<animate attributeName="opacity" values="{";".join(v)}" dur="{dur}s" begin="{begin}" repeatCount="indefinite"/>'
            for bucket, ov in ((back, ob), (front, of)):
                bucket.append(f'<g>{tr("translate", pos)}<g transform="rotate({-rot})"><g>{tr("scale", scl)}{op(ov)}<use href="#{nid}"/></g></g></g>')
        back.append("</g>")
        front.append("</g>")
    return "".join(defs), "".join(back), "".join(front)


# --------------------------------------------------------------------------- #
def hero():
    roles = ["Full-Stack Developer", "AI Engineer (Intern)", "Tech Enthusiast", "Lifelong Learner"]
    fs = 22
    cw = fs * 0.6
    slot = 4.4
    total = slot * len(roles)
    tx, ty = 74, 316

    css = (
        ".h{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}"
        ".blink{animation:blink 1.05s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        ".fl{animation:bob 6s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-5px)}}"
    )
    defs = (
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1222"/>' f'<stop offset="1" stop-color="{BG0}"/></linearGradient>'
        f'<clipPath id="clipAll"><rect width="{W}" height="{H}" rx="18"/></clipPath>'
        f'<clipPath id="pc"><circle r="{PR}"/></clipPath>'
        f'<linearGradient id="gHead" gradientUnits="userSpaceOnUse" x1="48" y1="0" x2="300" y2="0" spreadMethod="reflect">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/>'
        '<animate attributeName="x1" values="48;300;48" dur="9s" repeatCount="indefinite"/><animate attributeName="x2" values="300;552;300" dur="9s" repeatCount="indefinite"/></linearGradient>'
        f'<linearGradient id="gBar" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{LIME}"/></linearGradient>'
        f'<linearGradient id="gRing" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>'
        '<filter id="glow" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="10"/></filter>'
        '<radialGradient id="a1"><stop offset="0" stop-color="#22d3ee" stop-opacity=".28"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="a2"><stop offset="0" stop-color="#a78bfa" stop-opacity=".34"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="a3"><stop offset="0" stop-color="#f472b6" stop-opacity=".22"/><stop offset="1" stop-color="#f472b6" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="atmo"><stop offset=".78" stop-color="#22d3ee" stop-opacity="0"/><stop offset=".93" stop-color="#22d3ee" stop-opacity=".22"/><stop offset="1" stop-color="#a78bfa" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="sphere" cx=".38" cy=".32" r=".8"><stop offset="0" stop-color="#1b2a55" stop-opacity=".55"/><stop offset="1" stop-color="#050912" stop-opacity=".1"/></radialGradient>'
        '<radialGradient id="vig"><stop offset=".62" stop-color="#050912" stop-opacity="0"/><stop offset="1" stop-color="#050912" stop-opacity=".5"/></radialGradient>'
        '<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#fff" stroke-opacity=".04"/></pattern>'
        '<radialGradient id="gridFade" cx=".7" cy=".5" r=".8"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
        f'<mask id="gridMask"><rect width="{W}" height="{H}" fill="url(#gridFade)"/></mask>'
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" fill-opacity=".03"/></pattern>'
    )
    for i, r in enumerate(roles):
        tw = len(r) * cw
        s = i * slot
        v, k = keyframes([(0, 0), (s, 0), (s + slot * .45, tw), (s + slot * .88, tw), (s + slot, 0), (total, 0)], total)
        defs += f'<clipPath id="rc{i}"><rect x="{tx}" y="{ty - 4}" width="0" height="34"><animate attributeName="width" values="{v}" keyTimes="{k}" dur="{total}s" repeatCount="indefinite"/></rect></clipPath>'

    b = ['<g clip-path="url(#clipAll)">', f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="url(#bg)" stroke="{LINE}"/>']
    b.append(f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gridMask)"/>')
    b.append(
        '<circle cx="140" cy="80" r="240" fill="url(#a1)"><animate attributeName="cx" values="140;230;140" dur="14s" repeatCount="indefinite"/></circle>'
        '<circle cx="700" cy="380" r="270" fill="url(#a2)"><animate attributeName="cy" values="380;320;380" dur="12s" repeatCount="indefinite"/></circle>'
        '<circle cx="860" cy="50" r="200" fill="url(#a3)"><animate attributeName="cx" values="860;780;860" dur="13s" repeatCount="indefinite"/></circle>'
    )
    b.append(starfield(50, 21))

    # ---------------- left column ---------------- #
    b.append(
        f'<circle cx="52" cy="46" r="4" fill="{EMERALD}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>'
        f'<text x="66" y="50" class="m" font-size="12.5" letter-spacing="4.5" font-weight="700" fill="{CYAN}">COMPUTER SCIENCE</text>'
        f'<rect x="48" y="62" width="150" height="2" rx="1" fill="url(#gRing)"/>'
    )
    b.append(
        '<g class="h" style="animation-delay:.3s">'
        f'<text x="48" y="140" class="s" font-size="34" font-weight="600" fill="{TXT}" fill-opacity=".9">Hi, I\'m</text>'
        f'<text x="44" y="236" class="s" font-size="112" font-weight="900" fill="url(#gHead)" opacity=".5" filter="url(#glow)">Arsh</text>'
        f'<text x="44" y="236" class="s" font-size="112" font-weight="900" fill="url(#gHead)">Arsh</text>'
        f'<text x="50" y="270" class="m" font-size="14" fill="{MUTED}">@arshc0der  ·  arshdev.in</text></g>'
    )
    b.append(f'<text x="48" y="{ty + 17}" class="m" font-size="{fs}" font-weight="700" fill="{LIME}">$</text>')
    for i, r in enumerate(roles):
        tw = len(r) * cw
        s = i * slot
        b.append(
            f'<g clip-path="url(#rc{i})"><text x="{tx}" y="{ty + 17}" class="m" font-size="{fs}" fill="{TXT}" textLength="{tw:.1f}" lengthAdjust="spacing">{esc(r)}</text></g>'
        )
        vx, kx = keyframes([(0, tx), (s, tx), (s + slot * .45, tx + tw), (s + slot * .88, tx + tw), (s + slot, tx), (total, tx)], total)
        vo, ko = keyframes([(0, 0), (max(s - .01, 0), 0), (s, 1), (s + slot - .01, 1), (s + slot, 0), (total, 0)], total)
        b.append(
            f'<g opacity="0"><animate attributeName="opacity" values="{vo}" keyTimes="{ko}" dur="{total}s" repeatCount="indefinite"/>'
            f'<rect class="blink" x="{tx}" y="{ty}" width="11" height="24" fill="{LIME}"><animate attributeName="x" values="{vx}" keyTimes="{kx}" dur="{total}s" repeatCount="indefinite"/></rect></g>'
        )
    # tagline + chips
    b.append(f'<text x="48" y="376" class="s" font-size="19" font-style="italic" fill="{TXT}" fill-opacity=".85">Let\'s Contribute.</text>')
    cx_ = 48
    for label, col in (("AI", CYAN), ("CLOUD", VIOLET), ("SECURITY", PINK), ("FULL-STACK", LIME)):
        cwid = 26 + len(label) * 8.2
        b.append(
            f'<rect x="{cx_}" y="394" width="{cwid:.1f}" height="26" rx="13" fill="{col}" fill-opacity=".1" stroke="{col}" stroke-opacity=".55"/>'
            f'<text x="{cx_ + cwid / 2:.1f}" y="411" text-anchor="middle" class="m" font-size="11" font-weight="700" letter-spacing="1.5" fill="{col}">{label}</text>'
        )
        cx_ += cwid + 8
    b.append(
        f'<text x="48" y="448" class="m" font-size="10.5" fill="{MUTED}">loading /skills</text>'
        f'<rect x="150" y="441" width="286" height="5" rx="2.5" fill="#fff" fill-opacity=".07"/>'
        f'<rect x="150" y="441" width="0" height="5" rx="2.5" fill="url(#gBar)"><animate attributeName="width" from="0" to="286" dur="3.2s" begin=".4s" fill="freeze"/></rect>'
        f'<text x="446" y="448" class="m" font-size="10.5" fill="{EMERALD}">74/74</text>'
    )

    # ---------------- the globe ---------------- #
    g = [f'<g transform="translate({CX} {CY})">']
    g.append(f'<circle r="{R * 1.5}" fill="url(#a2)" opacity=".55"/>')
    g.append(f'<circle r="{R}" fill="url(#sphere)"/><circle r="{R + 10}" fill="url(#atmo)"/>')
    # latitude lines (static: rotation about the vertical axis leaves them unchanged)
    for lat in (-60, -30, 0, 30, 60):
        la = math.radians(lat)
        rx = R * math.cos(la)
        ry = rx * math.sin(TILT)
        cy_ = -R * math.sin(la) * math.cos(TILT)
        g.append(f'<ellipse cx="0" cy="{cy_:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="none" stroke="{CYAN}" stroke-opacity=".16"/>')
    g.append(f'<circle r="{R}" fill="none" stroke="{CYAN}" stroke-opacity=".35"/>')
    g.append(globe_dots())
    g.append(pin(28.6, 77.2))
    sat_defs, sat_back, sat_front = satellites(
        [
            (["python-original", "javascript-original", "typescript-original", "react-original-wordmark", "node-js", "docker-original", "git", "linux-original"], 226, 54, -22, 19, 46, 1, CYAN),
            (["next-js", "mongodb-original-wordmark", "postgresql-original-wordmark", "java-original", "c", "cplusplus"], 206, 46, 24, 17, 38, -1, PINK),
        ]
    )
    defs += sat_defs
    g.append(sat_back)
    # portrait
    photo = find_photo()
    g.append('<g class="fl">')
    g.append(f'<circle r="{PR + 14}" fill="{VIOLET}" opacity=".35" filter="url(#glow)"/>')
    g.append(f'<circle r="{PR + 5}" fill="{BG0}"/>')
    if photo:
        g.append(
            f'<g clip-path="url(#pc)"><image x="{-PR}" y="{-PR}" width="{2 * PR}" height="{2 * PR}" preserveAspectRatio="xMidYMid slice" href="{photo_uri(photo)}"/>'
            f'<circle r="{PR}" fill="url(#vig)"/></g>'
        )
    else:
        g.append(
            f'<g clip-path="url(#pc)"><rect x="{-PR}" y="{-PR}" width="{2 * PR}" height="{2 * PR}" fill="#16213a"/>'
            f'<circle cy="-18" r="30" fill="#2c3d66"/><path d="M-62 {PR}C-62 34 -34 20 0 20S62 34 62 {PR}Z" fill="#2c3d66"/></g>'
        )
    g.append(
        f'<circle r="{PR + 5}" fill="none" stroke="url(#gRing)" stroke-width="3.5" stroke-dasharray="200 80 90 120" stroke-linecap="round">'
        f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="14s" repeatCount="indefinite"/></circle>'
        f'<circle r="{PR + 16}" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-dasharray="2 8">'
        f'<animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="30s" repeatCount="indefinite"/></circle>'
        f'<circle r="{PR + 5}" fill="none" stroke="{VIOLET}" stroke-opacity=".6"><animate attributeName="r" values="{PR + 5};{PR + 34};{PR + 5}" dur="4s" repeatCount="indefinite"/>'
        f'<animate attributeName="stroke-opacity" values=".6;0;.6" dur="4s" repeatCount="indefinite"/></circle>'
    )
    g.append("</g>")
    g.append(sat_front)
    g.append("</g>")
    b.append("".join(g))
    b.append(f'<rect width="{W}" height="{H}" fill="url(#scan)"/></g>')
    out = wrap(W, H, "Arsh - 3D globe hero", "Rotating 3D globe with Arsh's portrait at the centre. Computer Science. Hi, I'm Arsh. Let's Contribute.", "".join(b), css, defs)
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "hero.svg").write_text(out, encoding="utf-8")
    print(f"  hero.svg  {len(out) / 1024:.0f} KB  (photo: {photo.name if photo else 'none - using silhouette'})")


if __name__ == "__main__":
    hero()
