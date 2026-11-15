"""Shared helpers for the profile SVG generators. Standard library only."""
import base64
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICONS = ROOT / "icons"
BADGES = ROOT / "SVG-Badges"

MONO = "ui-monospace,SFMono-Regular,'SF Mono','JetBrains Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace"
SANS = "'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"

# palette
BG0 = "#070b14"
BG1 = "#0d1424"
BG2 = "#111a2e"
LINE = "rgba(148,163,184,.18)"
TXT = "#e6edf7"
MUTED = "#8b9ab3"
CYAN = "#22d3ee"
VIOLET = "#a78bfa"
PINK = "#f472b6"
LIME = "#a3e635"
AMBER = "#fbbf24"
SKY = "#38bdf8"
ROSE = "#fb7185"
EMERALD = "#34d399"

BASE_CSS = (
    ".m{font-family:" + MONO + "}"
    ".s{font-family:" + SANS + "}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


def esc(s):
    return html.escape(str(s), quote=True)


def data_uri(path):
    raw = Path(path).read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode()


def wrap(w, h, title, desc, body, css="", defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
        f"<title id=\"t\">{esc(title)}</title><desc id=\"d\">{esc(desc)}</desc>"
        f"<style>{BASE_CSS}{css}</style><defs>{defs}</defs>{body}</svg>\n"
    )


def aurora_grad(gid, x1=0, x2=900, y1=0, y2=0, units="userSpaceOnUse"):
    return (
        f'<linearGradient id="{gid}" gradientUnits="{units}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/>'
        f'<stop offset="1" stop-color="{PINK}"/></linearGradient>'
    )


def fmt_num(n):
    if n is None:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1000:.1f}k"
    return f"{n:,}"
