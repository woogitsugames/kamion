"""Schematic SVG mockups of the ADR 0283 monitor HUD and settings screen (D84).

Geometry is a 1:1 port of game/Assets/_Project/Input/Display/DesktopHudLayout.cs (content 2560 x 1440 canvas units,
the same for 16:9, 21:9 and 32:9 - ultrawide monitors get the content centred) and of the strip drawn in
UI/Driving/DrivingHud.Desktop.cs; colours from Input/Display/UiPalette.cs. The road / scene is a flat grey block on
purpose: these are layout drawings, not renders (the real look is checked with visual-qa on the build).

Run:  python tools/ui/hud_mockups_0283.py   ->  docs/design/hud-0283-*.svg   (stdlib only)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "design"

# ---- UiPalette (sRGB 0-255)
INK = "#ECE9E1"
INK_MUTED = "#B8B5AC"
INK_ON_LIGHT = "#16181B"
PANEL = "#16181B"
ROW = "#1E2125"
BUTTON = "#2B2F34"
SEGMENT_ON = INK
ACCENT = "#E8A33A"
HUD_PANEL = "#111315"
HUD_ALPHA = 0.96
MIRROR_BEZEL = "#0B0C0D"
GAUGE_TRACK = "#3A3D42"
GAUGE_FILL = INK_MUTED
TELL_RED = "#B8321F"
TELL_AMBER = "#E2961C"
TELL_GREEN = "#4AA85C"
TELL_OFF = GAUGE_TRACK

# ---- DesktopHudLayout constants
W, H = 2560.0, 1440.0
MARGIN, GAP = 32.0, 16.0
STRIP_W, STRIP_H, EXT_H = 720.0, 112.0, 84.0
TELL_W, TELL_H = 720.0, 52.0
REVERSE_W, REVERSE_H = 560.0, 316.0
DEV_TOGGLE = (150.0, 56.0)
DEVTEXT_W = 760.0
CLEAR_FRACTION = 0.40
ASPECT = 0.55


def solve(strip=True, extended=False, size=0.42, drop=0.0, inset=0.0, dev_toggle=False, width=W):
    cx, top = width / 2, H - MARGIN
    show_strip = strip or extended
    sh = STRIP_H + (EXT_H if extended else 0.0) if show_strip else 0.0
    r = {"strip": (cx - STRIP_W / 2, MARGIN, STRIP_W, sh) if show_strip else None}
    ty = MARGIN + sh + 8 if show_strip else MARGIN
    r["tell"] = (cx - TELL_W / 2, ty, TELL_W, TELL_H)
    r["dev_toggle"] = (width - MARGIN - DEV_TOGGLE[0], MARGIN, *DEV_TOGGLE) if dev_toggle else None
    clear_w = max(CLEAR_FRACTION * width, DEVTEXT_W, TELL_W, REVERSE_W)
    clear_bottom = ty + TELL_H + GAP
    r["clear"] = (cx - clear_w / 2, clear_bottom, clear_w, top - clear_bottom)
    bottom = MARGIN if not dev_toggle else MARGIN + DEV_TOGGLE[1] + GAP
    mh = min(size * H, top - bottom)
    mw = mh * ASPECT
    room = r["clear"][0] - GAP - MARGIN
    if mw > room:
        mw = room
        mh = mw / ASPECT
    xl = MARGIN + inset * max(0.0, room - mw)
    yt = top - drop * max(0.0, top - bottom - mh)
    r["ml"] = (xl, yt - mh, mw, mh)
    r["mr"] = (width - xl - mw, yt - mh, mw, mh)
    r["reverse"] = (cx - REVERSE_W / 2, top - REVERSE_H, REVERSE_W, REVERSE_H)
    return r


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w / 2:.0f}" height="{h / 2:.0f}" '
            f'font-family="Inter, Arial, sans-serif">',
            f"<title>{title}</title>",
        ]

    def rect(self, x, y, w, h, fill, opacity=1.0, stroke=None, sw=0, dash=None):
        """x, y in canvas units with origin bottom-left (as in Unity); flipped here."""
        attrs = f'x="{x:.1f}" y="{self.h - y - h:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
        if opacity < 1:
            attrs += f' fill-opacity="{opacity}"'
        if stroke:
            attrs += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            attrs += f' stroke-dasharray="{dash}"'
        self.parts.append(f"<rect {attrs}/>")

    def text(self, x, y, s, size, fill=INK, anchor="start", weight=400):
        self.parts.append(
            f'<text x="{x:.1f}" y="{self.h - y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{s}</text>')

    def poly(self, pts, fill):
        p = " ".join(f"{x:.1f},{self.h - y:.1f}" for x, y in pts)
        self.parts.append(f'<polygon points="{p}" fill="{fill}"/>')

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / name).write_text("\n".join(self.parts + ["</svg>"]) + "\n", encoding="utf-8")


def scene(svg, x0=0.0, width=W, cab=False):
    """Flat placeholder of the 3D view: sky, road, (cab: dashboard band)."""
    svg.rect(x0, 0, width, H, "#8C949C")
    svg.rect(x0, 0, width, H * 0.42, "#5B5E60")
    svg.poly([(x0 + width * 0.47, H * 0.42), (x0 + width * 0.53, H * 0.42), (x0 + width * 0.80, 0), (x0 + width * 0.20, 0)], "#4A4C4E")
    if cab:
        svg.rect(x0, 0, width, H * 0.22, "#24272A")
        svg.rect(x0 + width * 0.36, H * 0.05, width * 0.28, H * 0.12, "#0B0C0D", stroke="#3A3D42", sw=3)
        svg.text(x0 + width * 0.5, H * 0.10, "zegary w desce (CabScreens)", 30, INK_MUTED, "middle")


def arrow(svg, cx, cy, left, color):
    s = -1 if left else 1
    svg.poly([(cx + s * 18, cy), (cx - s * 2, cy + 15), (cx - s * 2, cy + 6), (cx - s * 18, cy + 6),
              (cx - s * 18, cy - 6), (cx - s * 2, cy - 6), (cx - s * 2, cy - 15)], color)


def hud(svg, r, x0=0.0, extended=False, warnings=(), turn=0):
    if r["strip"]:
        x, y, w, h = r["strip"]
        x += x0
        svg.rect(x, y, w, h, HUD_PANEL, HUD_ALPHA)
        svg.text(x + 196, y + 28, "87", 68, INK, "end", 600)
        svg.text(x + 202, y + 30, "km/h", 22, INK_MUTED)
        svg.rect(x + 276, y + 16, 1, 80, GAUGE_TRACK)
        svg.text(x + 335, y + 34, "D9", 52, INK, "middle", 600)
        svg.rect(x + 394, y + 16, 1, 80, GAUGE_TRACK)
        for i, (yy, val, frac) in enumerate(((62, "8,1", 0.62), (20, "8,0", 0.61))):
            svg.text(x + 421, y + yy + 8, str(i + 1), 20, INK_MUTED, "middle")
            svg.rect(x + 438, y + yy + 12, 140, 6, GAUGE_TRACK)
            svg.rect(x + 438, y + yy + 12, 140 * frac, 6, GAUGE_FILL)
            svg.text(x + 652, y + yy + 7, val, 28, INK, "end", 600)
            svg.text(x + 656, y + yy + 8, "bar", 20, INK_MUTED)
        if extended:
            ey = y + STRIP_H
            svg.rect(x + 12, ey, w - 24, 1, GAUGE_TRACK)
            svg.text(x + 112, ey + 38, "1300", 28, INK, "end", 600)
            svg.text(x + 118, ey + 39, "obr/min", 20, INK_MUTED)
            svg.rect(x + 16, ey + 16, 240, 6, GAUGE_TRACK)
            svg.rect(x + 16, ey + 16, 240 * 0.55, 6, GAUGE_FILL)
            svg.text(x + 290, ey + 56, "Zwalniacz", 20, INK_MUTED)
            svg.text(x + 290, ey + 20, "R2", 28, ACCENT, weight=600)
            svg.text(x + 460, ey + 56, "Tempomat zjazdu", 20, INK_MUTED)
            svg.text(x + 460, ey + 20, "40 km/h", 28, INK, weight=600)
    x, y, w, h = r["tell"]
    x += x0
    always = r["strip"] is not None   # cab view with live screens: arrows only while lit
    if always or turn in (-1, 2):
        svg.rect(x, y, 64, h, HUD_PANEL, HUD_ALPHA)
        arrow(svg, x + 32, y + h / 2, True, TELL_GREEN if turn in (-1, 2) else TELL_OFF)
    if always or turn in (1, 2):
        svg.rect(x + w - 64, y, 64, h, HUD_PANEL, HUD_ALPHA)
        arrow(svg, x + w - 32, y + h / 2, False, TELL_GREEN if turn in (1, 2) else TELL_OFF)
    n = len(warnings)
    x1 = x + w / 2 - (n * 184 + max(0, n - 1) * 8) / 2
    for i, (label, red) in enumerate(warnings):
        tx = x1 + i * 192
        svg.rect(tx, y, 184, h, TELL_RED if red else TELL_AMBER)
        svg.text(tx + 92, y + 19, label, 19, INK if red else INK_ON_LIGHT, "middle", 600)


def mirrors(svg, r, x0=0.0):
    for key in ("ml", "mr"):
        x, y, w, h = r[key]
        x += x0
        svg.rect(x, y, w, h, MIRROR_BEZEL)
        svg.rect(x + 6, y + 6, w - 12, h - 12, "#9AA2A9")
        svg.rect(x + 6, y + 6, w - 12, (h - 12) * 0.45, "#62666A")
        side = 0.12 * (w - 12)
        sx = x + 6 if key == "mr" else x + w - 6 - side   # own trailer side: inner edge
        svg.rect(sx, y + 6, side, (h - 12) * 0.8, "#C9C4B8")


def clear_view(svg, r, x0=0.0):
    x, y, w, h = r["clear"]
    svg.rect(x + x0, y, w, h, "none", stroke=ACCENT, sw=3, dash="18 12")
    svg.text(x + x0 + w / 2, y + h - 40, "wolny widok drogi (ClearView)", 28, ACCENT, "middle")


def mock_minimal():
    r = solve(strip=True)
    s = Svg(W, H, "ADR 0283 - HUD monitora, minimalny (widok zza / kabina bez zegarów)")
    scene(s)
    clear_view(s, r)
    mirrors(s, r)
    hud(s, r, warnings=[("POSTOJOWY", True)], turn=-1)
    s.save("hud-0283-minimal-16x9.svg")


def mock_extended():
    r = solve(strip=True, extended=True, dev_toggle=True)
    s = Svg(W, H, "ADR 0283 - HUD monitora, tryb rozszerzony (klawisz I) z ostrzeżeniami")
    scene(s)
    mirrors(s, r)
    hud(s, r, extended=True, warnings=[("NISKIE CIŚNIENIE", True), ("USTERKA ABS", False)], turn=2)
    x, y, w, h = r["dev_toggle"]
    s.rect(x, y, w, h, BUTTON)
    s.text(x + w / 2, y + 19, "Panel", 24, INK, "middle")
    s.save("hud-0283-extended-16x9.svg")


def mock_cab():
    r = solve(strip=False)
    s = Svg(W, H, "ADR 0283 - widok z kabiny z żywymi zegarami: tylko rząd kontrolek")
    scene(s, cab=True)
    mirrors(s, r)
    hud(s, r, warnings=[("POSTOJOWY", True)], turn=1)
    s.save("hud-0283-cab-16x9.svg")


def mock_ultrawide():
    full = 5120.0
    x0 = (full - W) / 2
    r = solve(strip=True)
    s = Svg(full, H, "ADR 0283 - 32:9: treść HUD 16:9 na środku, widok 3D na całej szerokości")
    scene(s, 0, full)
    s.rect(x0, 0, W, H, "none", stroke=INK_MUTED, sw=3, dash="10 10")
    s.text(x0 + 20, H - 50, "obszar treści HUD 2560 x 1440 j (HudScaleModel)", 30, INK)
    mirrors(s, r, x0)
    hud(s, r, x0, turn=0)
    s.save("hud-0283-ultrawide-32x9.svg")


def mock_settings():
    pw, ph = 1240.0, 1240.0
    s = Svg(pw, ph, "ADR 0283 - ustawienia, zakładka Lusterka")
    s.rect(0, 0, pw, ph, PANEL)
    s.text(40, ph - 64, "USTAWIENIA", 40, INK, weight=600)
    s.text(pw - 40, ph - 64, "Są niezastosowane zmiany.", 24, ACCENT, "end")
    tabs = ["Grafika", "Sterowanie", "Dźwięk", "Rozgrywka", "Lusterka"]
    tw = (pw - 80 - 8 * 4) / 5
    for i, t in enumerate(tabs):
        on = i == 4
        x = 40 + i * (tw + 8)
        s.rect(x, ph - 96 - 64, tw, 64, SEGMENT_ON if on else BUTTON)
        s.text(x + tw / 2, ph - 96 - 40, t, 26, INK_ON_LIGHT if on else INK, "middle", 600 if on else 400)
    s.text(40, ph - 96 - 64 - 28, "Q / E lub LB / RB: zakładki · Enter / A: wybór · Esc / B: wróć", 20, INK_MUTED)
    y = ph - 96 - 64 - 40 - 16

    def header(label):
        nonlocal y
        s.rect(40, y - 36, 6, 26, ACCENT)
        s.text(58, y - 32, label, 24, INK, weight=600)
        y -= 54

    def row(label, value=None, segs=None, sel=0, focus=False):
        nonlocal y
        s.rect(40, y - 60, pw - 80, 60, ROW)
        s.text(60, y - 38, label, 26, INK)
        if segs:
            x0, w = 480, (pw - 80 - 480 - 12 - 6 * (len(segs) - 1)) / len(segs)
            for i, t in enumerate(segs):
                on = i == sel
                s.rect(40 + x0 + i * (w + 6), y - 54, w, 48, SEGMENT_ON if on else BUTTON)
                s.text(40 + x0 + i * (w + 6) + w / 2, y - 37, t, 23, INK_ON_LIGHT if on else INK, "middle", 600 if on else 400)
        else:
            s.rect(40 + 440, y - 54, 76, 48, BUTTON, stroke=ACCENT if focus else None, sw=3)
            s.text(40 + 440 + 38, y - 38, "−", 28, INK, "middle")
            s.text(40 + 440 + 76 + (pw - 80 - 440 - 2 * 76 - 32) / 2, y - 38, value, 26, INK, "middle", 600)
            s.rect(pw - 40 - 76 - 12, y - 54, 76, 48, BUTTON)
            s.text(pw - 40 - 12 - 38, y - 38, "+", 28, INK, "middle")
        y -= 68

    header("OKIENKA LUSTEREK")
    row("Okienka lusterek", segs=["wyłączone", "włączone"], sel=1)
    row("Rozmiar", "48 %", focus=True)
    row("Położenie w pionie", "0 %")
    row("Odsunięcie od krawędzi", "20 %")
    s.text(40, y - 24, "Podgląd układu (monitor 16:9)", 20, INK_MUTED)
    y -= 34
    k = 480 / W
    bx, by = 40 + 420, y - 270
    s.rect(bx, by, 480, 270, ROW)
    r = solve(size=0.48, inset=0.2)
    for key in ("ml", "mr", "strip", "tell"):
        x, yy, w, h = r[key]
        s.rect(bx + x * k, by + yy * k, w * k, h * k, INK_MUTED if key in ("ml", "mr") else GAUGE_TRACK)
    y = by - 30
    header("REGULACJA LUSTEREK")
    row("Na zewnątrz / do środka", "+1,5°")
    row("W dół / w górę", "0,0°")
    for i, (t, on) in enumerate((("Przywróć domyślne", False), ("Anuluj", False), ("Zastosuj", True))):
        x = 40 if i == 0 else (pw - 40 - 2 * 300 - 20 if i == 1 else pw - 40 - 300)
        w = 420 if i == 0 else 300
        s.rect(x, 20, w, 72, SEGMENT_ON if on else BUTTON)
        s.text(x + w / 2, 47, t, 26, INK_ON_LIGHT if on else INK, "middle", 600 if on else 400)
    s.save("hud-0283-settings-mirrors.svg")


def main():
    mock_minimal()
    mock_extended()
    mock_cab()
    mock_ultrawide()
    mock_settings()
    for p in sorted(OUT.glob("hud-0283-*.svg")):
        print(p.relative_to(ROOT))


if __name__ == "__main__":
    main()
