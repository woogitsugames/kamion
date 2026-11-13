"""ADR 0175: verdicts for the appearance rules of the TRAKT tractor (N3 4x2) + curtainsider semi-trailer (O4).

    python tools/blender/truck/regs_check.py --tractor tractor.json --trailer trailer.json [--md out.md] [--json out.json]

Input = the dumps of tools/blender/truck/regs_audit.py. Requirements = the artist table in
docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p4.md par. 5 + research/gptpro/p4-truck-regulations/manifest.csv (ids
P4-nnn below). Rows marked O / UNVERIFIED in that table are NOT checked here (ADR 0175 lists them). Exit code 1 when a
row fails. Pure Python (no bpy): also imported by tests/physics/test_truck_regs.py.
"""
import argparse
import json
import re
import sys

MM = 1000.0


class Dump:
    def __init__(self, d):
        self.o = d["objects"]
        self.d = d

    def get(self, pattern):
        rx = re.compile(pattern)
        return {n: v["bbox"] for n, v in self.o.items() if rx.fullmatch(n)}

    def side(self, pattern, s):
        return {n: b for n, b in self.get(pattern).items() if (b[0] + b[1]) * s > 0}


def union(bbs):
    bbs = list(bbs)
    if not bbs:
        return None
    return [min(b[0] for b in bbs), max(b[1] for b in bbs), min(b[2] for b in bbs), max(b[3] for b in bbs),
            min(b[4] for b in bbs), max(b[5] for b in bbs)]


def gaps(ys):
    ys = sorted(ys, reverse=True)
    return [round(a - b, 3) for a, b in zip(ys, ys[1:])]


class Report:
    def __init__(self):
        self.rows = []

    def add(self, veh, item, req, measured, ok, src):
        self.rows.append({"vehicle": veh, "item": item, "requirement": req, "measured": measured,
                          "ok": bool(ok), "source": src})

    def rng(self, veh, item, req, src, val, lo=None, hi=None, unit="mm", fmt="{:.0f}"):
        ok = val is not None and (lo is None or val >= lo - 1e-6) and (hi is None or val <= hi + 1e-6)
        self.add(veh, item, req, "brak" if val is None else fmt.format(val) + " " + unit, ok, src)


def lamp_checks(r, veh, half_w, bb, name, src, edge=None, h=(None, None), n=2, sep=None):
    """Symmetric pair: count, distance of the outer edge from the vehicle side, height band (lowest/highest point)."""
    if not bb:
        r.add(veh, name, f"{n} szt.", "brak", False, src)
        return
    u = union(bb.values())
    cnt = len({(b[0] + b[1]) > 0 for b in bb.values()}) if n == 2 else len(bb)
    r.add(veh, f"{name}: liczba", f">= {n}", str(cnt), cnt >= n, src)
    if edge is not None:
        r.rng(veh, f"{name}: od krawędzi bocznej", f"<= {edge} mm", src, (half_w - max(abs(u[0]), abs(u[1]))) * MM,
              hi=edge)
    if h[0] is not None:
        r.rng(veh, f"{name}: dolna krawędź", f">= {h[0]} mm", src, u[4] * MM, lo=h[0])
    if h[1] is not None:
        r.rng(veh, f"{name}: górna krawędź", f"<= {h[1]} mm", src, u[5] * MM, hi=h[1])
    if sep is not None:
        inner = min(min(abs(b[0]), abs(b[1])) for b in bb.values())
        r.rng(veh, f"{name}: odstęp wewnętrzny", f">= {sep} mm", src, 2 * inner * MM, lo=sep)


def spacing_checks(r, veh, name, src, ys, front, rear, first=3.0, step=3.0, last=1.0):
    if not ys:
        r.add(veh, name, "obowiązkowe", "brak", False, src)
        return
    ys = sorted(ys, reverse=True)
    r.rng(veh, f"{name}: pierwszy od przodu", f"<= {first} m", src, front - ys[0], hi=first, unit="m", fmt="{:.2f}")
    g = gaps(ys)
    r.rng(veh, f"{name}: największy odstęp", f"<= {step} m", src, max(g) if g else 0.0, hi=step, unit="m",
          fmt="{:.2f}")
    r.rng(veh, f"{name}: ostatni od tyłu", f"<= {last} m", src, ys[-1] - rear, hi=last, unit="m", fmt="{:.2f}")


def dist3(a, b):
    """Shortest distance between two axis-aligned boxes."""
    d = [max(a[2 * i] - b[2 * i + 1], b[2 * i] - a[2 * i + 1], 0.0) for i in range(3)]
    return (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5


def plate_size(r, v, nm, b):
    src = "Dz.U. 2024 poz. 1709 zał. 12 rys. 1 (review [zm. M44-FIX], P)"
    r.rng(v, f"płyta tablicy {nm}: szerokość", "520 ± 1 mm", src, (b[1] - b[0]) * MM, lo=519, hi=521)
    r.rng(v, f"płyta tablicy {nm}: wysokość", "114 ± 1 mm", src, (b[5] - b[4]) * MM, lo=113, hi=115)


def check_tractor(r, T):
    v = "ciągnik"
    half = max(abs(x) for b in T.get(r"mudflap_-?1").values() for x in b[:2])     # widest body point (mirrors excluded)
    ov = T.d["overall"]
    front = max(b[3] for b in T.get(r"plate|lamp_lens_-?1").values()) + 0.02      # bumper face ~ plate + holder
    front = max(front, 1.443)                                                     # sun-visor nose (dims.json)
    rear = ov[2]
    r.rng(v, "szerokość nadwozia (bez lusterek)", "<= 2,55 m", "96/53 zał. I 1.2", 2 * half, hi=2.55, unit="m",
          fmt="{:.3f}")
    r.rng(v, "wysokość", "<= 4,00 m", "96/53 zał. I 1.3", ov[5], hi=4.0, unit="m", fmt="{:.3f}")
    lamp_checks(r, v, half, T.get(r"indicator_-?1"), "kierunkowskazy przód", "R48 6.5 (P4-018..)", edge=400,
                h=(350, 1500), sep=600)
    amber = {n: b for n, b in T.get(r"rear_lens_-?1_\d").items() if "lens_amber" in T.o[n]["mat"]}
    red = {n: b for n, b in T.get(r"rear_lens_-?1_\d").items() if "lens_red" in T.o[n]["mat"]}
    clear = {n: b for n, b in T.get(r"rear_lens_-?1_\d").items() if "lens_clear" in T.o[n]["mat"]}
    lamp_checks(r, v, half, amber, "kierunkowskazy tył", "R48 6.5", edge=400, h=(350, 1500), sep=600)
    lamp_checks(r, v, half, T.get(r"side_repeater_-?1"), "kierunkowskazy boczne", "R48 6.5 kat. 5/6", h=(500, 1500))
    # the tractor's tail / stop chamber; the old red reflector strip was also a rear_lens (innermost)
    refl = T.get(r"rear_reflex_-?1")
    if not refl:      # baseline layout: reflector strip = the narrow innermost red chamber
        refl = {n: b for n, b in red.items() if b[1] - b[0] < 0.06}
    stop = {n: b for n, b in red.items() if n not in refl}
    lamp_checks(r, v, half, stop, "stop + pozycyjne tył", "R48 6.7 / 6.10", edge=400, h=(350, 1500), sep=600)
    lamp_checks(r, v, half, T.get(r"marker_front_[01]"), "obrysowe górne przód (białe)", "R48 6.13", edge=400,
                h=(3120, None))
    lamp_checks(r, v, half, T.get(r"marker_rear_-?1"), "obrysowe górne tył (czerwone)", "R48 6.13", edge=400)
    lamp_checks(r, v, half, refl, "odblaski tylne nietrójkątne", "R48 6.14 (P4-044/045)", edge=400, h=(250, 900))
    r.add(v, "odblaski tylne: kształt", "nietrójkątne; trójkątne zakazane", "trójkąt" if T.get(r"tri_reflector.*")
          else "prostokątne", not T.get(r"tri_reflector.*"), "R48 6.14 / 6.15")
    lamp_checks(r, v, half, clear, "światła cofania", "R48 6.4 (P4-032/033)", h=(250, 1200))
    fog = T.get(r"rear_fog_lens.*")
    r.add(v, "przeciwmgłowe tylne: liczba", "1-2 (pojedyncze po lewej)", str(len(fog)),
          1 <= len(fog) <= 2 and (len(fog) == 2 or all(b[1] < 0 for b in fog.values())), "R48 6.11 (P4-035/037)")
    if fog:
        u = union(fog.values())
        r.rng(v, "przeciwmgłowe tylne: górna krawędź", "<= 1000 mm", "R48 6.11.4.2 (P4-036)", u[5] * MM, hi=1000)
        r.rng(v, "przeciwmgłowe tylne: dolna krawędź", ">= 250 mm", "R48 6.11.4.2 (P4-036)", u[4] * MM, lo=250)
        r.rng(v, "przeciwmgłowe tylne: odległość od stop", "> 100 mm", "R48 6.11.9 (P4-031)",
              min(dist3(a, b) for a in fog.values() for b in stop.values()) * MM, lo=100.001)
    sr = T.get(r"side_reflex_.*")
    for s, nm in ((-1, "L"), (1, "P")):
        ys = [(b[2] + b[3]) / 2 for b in sr.values() if (b[0] + b[1]) * s > 0]
        spacing_checks(r, v, f"odblaski boczne {nm}", "R48 6.17.4 (P4-047), WT §12.1.11 (P4-138)", ys, front, rear)
    if sr:
        u = union(sr.values())
        r.rng(v, "odblaski boczne: dolna krawędź", ">= 250 mm", "R48 6.17.4 (P4-047)", u[4] * MM, lo=250)
        r.rng(v, "odblaski boczne: górna krawędź", "<= 900 mm", "R48 6.17.4 (P4-047)", u[5] * MM, hi=900)
    for pat, nm, src in ((r"contour.*", "oznakowanie konturowe R104", "R48 6.21.1.2.1 a) (P4-073)"),
                         (r"r70.*", "tablice wyróżniające", "WT §42, R70 1.2"),
                         (r"rup.*", "osłona tylna R58", "R58 1.2"), (r"sideguard.*", "osłony boczne R73", "R73 2.1.4")):
        r.add(v, nm, "BRAK (ciągnik siodłowy wyłączony)", "jest" if T.get(pat) else "brak", not T.get(pat), src)
    for pat, nm in ((r"mirror_main_glass_-1", "lusterko kl. II kierowca"), (r"mirror_main_glass_1", "kl. II pasażer"),
                    (r"mirror_wide_glass_-1", "kl. IV kierowca"), (r"mirror_wide_glass_1", "kl. IV pasażer"),
                    (r"mirror_kerb_glass", "kl. V pasażer"), (r"front_mirror_glass", "kl. VI przód")):
        r.add(v, nm, "obowiązkowe", "jest" if T.get(pat) else "brak", bool(T.get(pat)), "R46 04 15.2.1.1.1 (tab. N3)")
    k = T.get(r"mirror_kerb_glass")
    if k:
        b = union(k.values())
        r.add(v, "kl. V: strona", "pasażera (x > 0)", "pasażer" if b[0] > 0 else "kierowca", b[0] > 0, "R46 04")
    for pat, nm in ((r"mirror_kerb", "kl. V: dolna krawędź obudowy"), (r"front_mirror", "kl. VI: dolna krawędź"),
                    (r"mirror_main_house_-?1", "kl. II/IV: dolna krawędź (wystawanie > 250 mm)")):
        b = union(T.get(pat).values())
        if b:
            r.rng(v, nm, ">= 2000 mm", "R46 04 15.2.4", b[4] * MM, lo=2000)
    pf, pr = union(T.get(r"plate").values()), union(T.get(r"rear_plate").values())
    r.add(v, "tablica rejestracyjna przód", "jest", "jest" if pf else "brak", bool(pf), "rozp. rej. §33")
    for nm, b_ in (("przód", pf), ("tył", pr)):
        if b_:
            plate_size(r, v, nm, b_)
    if pr:
        r.rng(v, "tablica tył: dolna krawędź", ">= 300 mm", "WT zał. 5 §2.2 (P4-149)", pr[4] * MM, lo=300)
        r.rng(v, "tablica tył: górna krawędź", "<= 1200 mm", "WT zał. 5 §2.2 (P4-149)", pr[5] * MM, hi=1200)
        r.rng(v, "miejsce na tablicę tył: szerokość", ">= 520 mm", "WT zał. 5 §2.1 (P4-147)", (pr[1] - pr[0]) * MM,
              lo=519.9)
    else:
        r.add(v, "tablica rejestracyjna tył", "jest", "brak", False, "rozp. rej. §33")


def check_trailer(r, T):
    v = "naczepa"
    dm = T.d["dims"]
    half, front, rear, roof = dm["half_width"], dm["y_front"], dm["y_rear"], dm["roof"]
    ov = T.d["overall"]
    r.rng(v, "wysokość", "<= 4,00 m", "96/53 zał. I 1.3", ov[5], hi=4.0, unit="m", fmt="{:.3f}")
    r.rng(v, "szerokość nadwozia", "<= 2,55 m", "96/53 zał. I 1.2", 2 * half, hi=2.55, unit="m", fmt="{:.3f}")
    r.rng(v, "sworzeń - tył", "<= 12,00 m", "96/53 zał. I 1.6", -rear, hi=12.0, unit="m", fmt="{:.2f}")
    lens = lambda nm: T.get(rf"rear_lens_{nm}_[LR]")     # noqa: E731
    lamp_checks(r, v, half, lens("ind"), "kierunkowskazy tył", "R48 6.5", edge=400, h=(350, 1500), sep=600)
    lamp_checks(r, v, half, lens("stop"), "stop", "R48 6.7", h=(350, 1500), sep=600)
    lamp_checks(r, v, half, lens("tail"), "pozycyjne tył", "R48 6.10", edge=400, h=(350, 1500))
    lamp_checks(r, v, half, lens("rev"), "światła cofania", "R48 6.4.2.2 (P4-060)", h=(250, 1200))
    fog = lens("fog")
    r.add(v, "przeciwmgłowe tylne: liczba", "1-2 (pojedyncze po lewej)", str(len(fog)),
          1 <= len(fog) <= 2 and (len(fog) == 2 or all(b[1] < 0 for b in fog.values())), "R48 6.11")
    if fog:
        u = union(fog.values())
        r.rng(v, "przeciwmgłowe tylne: górna krawędź", "<= 1000 mm", "R48 6.11.4.2 (P4-036)", u[5] * MM, hi=1000)
        r.rng(v, "przeciwmgłowe tylne: odległość od stop", "> 100 mm", "R48 6.11.9 (P4-031)",
              min(dist3(a, b) for a in fog.values() for b in lens("stop").values()) * MM, lo=100.001)
    pos = {n: b for n, b in T.get(r"front_lamp_lens.*").items() if b[5] <= 1.5 + 1e-6}
    lamp_checks(r, v, half, pos, "pozycyjne przód (białe, <= 1500 mm)", "R48 6.9 (P4-053..055)", edge=150,
                h=(250, 1500))
    out_f = {n: b for n, b in T.get(r"front_lamp_lens.*|stalk_lens_w.*").items() if b[5] > 2.1}
    lamp_checks(r, v, half, out_f, "obrysowe górne przód (białe)", "R48 6.13", h=(roof * MM - 400, None))
    lamp_checks(r, v, half, T.get(r"rear_marker_lens.*"), "obrysowe górne tył (czerwone)", "R48 6.13", edge=400,
                h=(roof * MM - 400, None))
    lamp_checks(r, v, half, T.get(r"front_reflex_.*"), "odblaski przednie białe", "R48 6.16 (P4-063..065)", edge=150,
                h=(250, 1500))
    tri = T.get(r"tri_reflector_[LR]")
    lamp_checks(r, v, half, tri, "odblaski tylne trójkątne", "R48 6.15 (P4-066..068)", edge=400, h=(250, 900), sep=600)
    for s, nm in ((-1, "L"), (1, "P")):
        ys = [(b[2] + b[3]) / 2 for b in T.side(r"side_marker_lens.*", s).values()]
        spacing_checks(r, v, f"obrysowe boczne {nm}", "R48 6.18.4 (P4-049)", ys, front, rear)
        ys = [(b[2] + b[3]) / 2 for b in T.side(r"side_marker_reflex.*|side_reflector.*", s).values()]
        spacing_checks(r, v, f"odblaski boczne {nm}", "R48 6.17.4 (P4-047/069)", ys, front, rear)
    sm = union(T.get(r"side_marker_lens.*").values())
    if sm:
        r.rng(v, "obrysowe boczne: wysokość", "250-1500 mm", "R48 6.18.4 (P4-049)", sm[5] * MM, lo=250, hi=1500)
    # R104 rear: full contour
    hor_top, sill = T.get(r"contour_rear_header"), T.get(r"contour_rear_sill_\d+")
    posts = T.get(r"contour_rear_post_-?1")
    r.add(v, "kontur tył: pełny (góra + dół + 2 pionowe)", "pełny kontur", f"góra {len(hor_top)}, dół {len(sill)}, "
          f"pion {len(posts)}", bool(hor_top) and bool(sill) and len(posts) == 2, "R48 6.21.1.1 (P4-071)")
    if sill and hor_top:
        cum = sum(b[1] - b[0] for b in sill.values())
        r.rng(v, "kontur tył: łączna długość dolnej linii", ">= 70 % szerokości", "R48 6.21.4.1.2 (P4-074)",
              100 * cum / (2 * half), lo=70, unit="%")
        u = union(sill.values())
        r.rng(v, "kontur tył: dolna krawędź", "250-1500 mm", "R48 6.21.4 (P4-075)", u[4] * MM, lo=250, hi=1500)
        r.rng(v, "kontur tył: góra od górnej krawędzi pojazdu", "<= 400 mm", "R48 6.21.4",
              (roof - union(hor_top.values())[5]) * MM, hi=400)
        allr = list(sill.values()) + list(hor_top.values()) + list(posts.values())
        r.rng(v, "kontur tył: odległość od stop", "> 200 mm", "R48 6.21.7.3 (P4-077)",
              min(dist3(a, b) for a in allr for b in lens("stop").values()) * MM, lo=200.001)
        w = min(min(b[5] - b[4] for b in sill.values()), min(b[1] - b[0] for b in posts.values()))
        r.rng(v, "kontur tył: szerokość taśmy", ">= 60 mm (R104: 50 +10/-0)", "R48 6.21.7.5 (P4-079)", w * MM, lo=59.9,
              hi=60.1)
    # R104 side: partial contour = line + upper corners
    for s, nm in ((-1, "L"), (1, "P")):
        line = T.side(r"contour_side_-?1_\d+", s)
        cum = sum(b[3] - b[2] for b in line.values())
        r.rng(v, f"kontur bok {nm}: łączna długość linii", ">= 70 % długości", "R48 6.21.4.1.2 (P4-074)",
              100 * cum / (front - rear), lo=70, unit="%")
        if line:
            u = union(line.values())
            r.rng(v, f"kontur bok {nm}: początek od przodu", "<= 600 mm", "R48 6.21.4.1.3", (front - u[3]) * MM, hi=600)
            r.rng(v, f"kontur bok {nm}: koniec od tyłu", "<= 600 mm", "R48 6.21.4.1.3", (u[2] - rear) * MM, hi=600)
            r.rng(v, f"kontur bok {nm}: szerokość taśmy", ">= 60 mm", "R48 6.21.7.5 (P4-079)", (u[5] - u[4]) * MM,
                  lo=59.9, hi=60.1)
        cor = T.side(r"contour_corner_.*", s)
        nf = len([b for b in cor.values() if b[3] > 0])
        nr = len([b for b in cor.values() if b[3] < -6])
        r.add(v, f"kontur bok {nm}: górne narożniki (częściowy kontur)", "przód + tył, 2 ramiona >= 250 mm",
              f"przód {nf} el., tył {nr} el.", nf >= 2 and nr >= 2, "R48 6.21.1.2 (P4-072)")
        if cor:
            r.rng(v, f"kontur bok {nm}: narożniki od górnej krawędzi", "<= 400 mm", "R48 6.21.4",
                  (roof - union(cor.values())[5]) * MM, hi=400)
    # R70 / WT annex 10 rear marking plates
    pl = T.get(r"r70_plate_-?1")
    r.add(v, "tablice wyróżniające: liczba", "1, 2 lub 4", str(len(pl)), len(pl) in (1, 2, 4), "WT §42 (P4-140)")
    if pl:
        u = union(pl.values())
        r.rng(v, "tablice wyróżniające: dolna krawędź", ">= 250 mm", "WT zał. 10 §4 (P4-143)", u[4] * MM, lo=250)
        r.rng(v, "tablice wyróżniające: górna krawędź", "<= 2100 mm", "WT zał. 10 §4 (P4-143)", u[5] * MM, hi=2100)
        r.rng(v, "tablice wyróżniające: od obrysu", "<= 400 mm", "WT zał. 10 §5 (P4-144)",
              (half - max(abs(u[0]), abs(u[1]))) * MM, hi=400)
        r.rng(v, "tablice wyróżniające: wysokość tablicy", "195-230 mm", "R70 zał. 12 (review s17 r8 p4, S)",
              (u[5] - u[4]) * MM, lo=195, hi=230)
        r.rng(v, "tablice wyróżniające: łączna długość", "1130-2300 mm", "R70 zał. 12 (review s17 r8 p4, S)",
              sum(b[1] - b[0] for b in pl.values()) * MM, lo=1129.9, hi=2300)
    # R58 rear underrun
    rup = union(T.get(r"rup_bar").values())
    if rup:
        r.rng(v, "osłona tylna R58: wysokość belki", ">= 120 mm", "R58 03", (rup[5] - rup[4]) * MM, lo=120)
        r.rng(v, "osłona tylna R58: prześwit", "<= 450 mm (pneumatyczne)", "R58 03 16.2/25.1", rup[4] * MM, hi=450)
        r.rng(v, "osłona tylna R58: od tyłu pojazdu", "<= 200 mm", "R58 03 (P4-093)", (rup[2] - rear) * MM, hi=200)
    else:
        r.add(v, "osłona tylna R58", "obowiązkowa", "brak", False, "R58 03")
    # R73 side guards
    sg = T.get(r"sideguard_-?1_0\.\d+")
    caps = T.get(r"sideguard_cap_.*")
    if sg:
        u = union(list(sg.values()) + list(caps.values()))
        zs = sorted({(round(b[4], 3), round(b[5], 3)) for b in sg.values()})
        r.rng(v, "osłony boczne R73: dolna krawędź", "<= 550 mm", "R73 01", u[4] * MM, hi=550)
        leg_rear = min(b[2] for b in T.get(r"leg_inner_[LR]").values())
        r.rng(v, "osłony boczne R73: przód za nogami podporowymi", "<= 250 mm", "R73 01", (leg_rear - u[3]) * MM,
              hi=250)
        tyre_front = max(b[3] for b in T.get(r"wheel_1L_tyre").values())
        r.rng(v, "osłony boczne R73: tył przed oponą", "<= 300 mm", "R73 01", (u[2] - tyre_front) * MM, hi=300)
        r.rng(v, "osłony boczne R73: odstęp listew", "<= 300 mm", "R73 01",
              max((b[0] - a[1]) for a, b in zip(zs, zs[1:])) * MM if len(zs) > 1 else 0.0, hi=300)
        r.rng(v, "osłony boczne R73: wysokość listwy", ">= 100 mm", "R73 01", min(b - a for a, b in zs) * MM, lo=99.9)
        r.rng(v, "osłony boczne R73: w głąb od obrysu", "<= 150 mm", "R73 01", (half - max(abs(u[0]), abs(u[1]))) * MM,
              hi=150)
    else:
        r.add(v, "osłony boczne R73", "obowiązkowe", "brak", False, "R73 01")
    pr = union(T.get(r"plate_rear").values())
    if pr:
        plate_size(r, v, "tył", pr)
        r.rng(v, "tablica rejestracyjna tył: dolna krawędź", ">= 300 mm", "WT zał. 5 §2.2 (P4-149)", pr[4] * MM, lo=300)
        r.rng(v, "tablica rejestracyjna tył: górna krawędź", "<= 1200 mm", "WT zał. 5 §2.2 (P4-149)", pr[5] * MM,
              hi=1200)
    else:
        r.add(v, "tablica rejestracyjna tył", "jest (tylko z tyłu)", "brak", False, "rozp. rej. §33")
    r.add(v, "oświetlenie tablicy", "obowiązkowe", "jest" if T.get(r"plate_lamp_lens") else "brak",
          bool(T.get(r"plate_lamp_lens")), "R48 6.8 (P4-061)")


def run(tractor=None, trailer=None):
    r = Report()
    if tractor:
        check_tractor(r, Dump(tractor))
    if trailer:
        check_trailer(r, Dump(trailer))
    return r.rows


def to_md(rows):
    out = ["| pojazd | element | wymaganie | stan | wynik | źródło |", "|---|---|---|---|---|---|"]
    for x in rows:
        out.append(f"| {x['vehicle']} | {x['item']} | {x['requirement']} | {x['measured']} | "
                   f"{'OK' if x['ok'] else '**RÓŻNICA**'} | {x['source']} |")
    return "\n".join(out) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tractor")
    p.add_argument("--trailer")
    p.add_argument("--md")
    p.add_argument("--json")
    a = p.parse_args()
    tr = json.load(open(a.tractor, encoding="utf-8"))["tractor"] if a.tractor else None
    tl = json.load(open(a.trailer, encoding="utf-8"))["trailer"] if a.trailer else None
    rows = run(tr, tl)
    bad = [x for x in rows if not x["ok"]]
    if a.md:
        open(a.md, "w", encoding="utf-8", newline="\n").write(to_md(rows))
    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for x in bad:
        print(f"FAIL {x['vehicle']}: {x['item']} | {x['requirement']} | {x['measured']} | {x['source']}")
    print(f"{len(rows) - len(bad)}/{len(rows)} OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
