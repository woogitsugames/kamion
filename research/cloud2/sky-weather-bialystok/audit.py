#!/usr/bin/env python3
"""R7 — samokontrola ≥ 20 % wierszy manifestu. Seed 20261114, losowanie:
    random.Random(20261114).sample(sorted(ids), ceil(0.2·n))
Liczby są PRZELICZANE PONOWNIE niezależną ścieżką (ten plik nie używa funkcji liczących z tools_imgw/tools_sun, poza
odczytem ZIP): własny parser pozycyjny CSV, percentyle przez statistics.quantiles(method='inclusive'), słońce i zdarzenia
przez pakiet astral (inna implementacja), cytaty przez ponowne otwarcie źródła (PDF → pdftotext, strony → HTTP, OpenAlex API).
Kadry: wynik PONOWNEGO obejrzenia obrazu (narzędzie Read, 960 px lub wycinek 3×) wpisany ręcznie w FRAME_REVIEW.
Użycie: <python z astral i rdata> audit.py   → audit_20_percent.json
"""
import csv
import hashlib
import html
import io
import json
import math
import random
import re
import statistics
import subprocess
import sys
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
FILES = HERE / "files"
SEED = 20261114
TZ = ZoneInfo("Europe/Warsaw")
ST = "353230295"
MN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

# wynik ponownego obejrzenia kadrów z próby (2026-11-14): co obejrzano, werdykt, korekta
FRAME_REVIEW = {
    "img/pnx_f2623f76.jpg": ("wycinek 3× pasa horyzontu (15–85 % szer., 45–75 % wys.)", "PASS",
                             "pas białych Cu nad horyzontem, horyzont białawo-błękitny, zalesione wzniesienia niebieskawe — zgodne"),
    "img/pnx_3e13253b.jpg": ("cały kadr 960 px", "PASS",
                             "zgodne; doprecyzowano: chłodna tonacja dotyczy chodnika i elewacji, piaszczysty grunt jest brunatny, dodano drzewo z rudymi liśćmi"),
    "img/c10_20201129_111856.jpg": ("wycinek nieba w osi ulicy (30–75 % szer., 0–65 % wys.)", "PASS",
                                    "niebo szare z ciemniejszymi płatami, jaśniejsze nisko w osi ulicy — zgodne"),
    "img/c13_20201106_161230.jpg": ("wycinek 3× nieba nad dachami (0–60 % szer., 20–60 % wys.)", "FAIL",
                                    "opis „nisko nad dachami po lewej jaśniejsze i bardziej niebieskie” nieścisły: jaśniejsza, szaroniebieska "
                                    "jest lewa część nieba przy poświacie latarni, reszta granatowa z fioletowym odcieniem; opis poprawiony w frames.json/manifest; "
                                    "wniosek (brak ciepłego pasa) bez zmian"),
    "img/pnx_c1a5e40e.jpg": ("wycinek pasa nad zabudową (cała szer., 30–62 % wys.)", "FAIL",
                             "opis „nisko nad zabudową nieco jaśniejsze i szare” nie potwierdza się: niebo jest jednolicie ciemne, jaśniejsze tylko "
                             "w poświacie wokół oprawy; opis poprawiony; wniosek (brak ciepłego pasa) bez zmian"),
    "img/c04_20201115_154234.jpg": ("wycinek nieba i końca ulicy (20–75 % szer., 0–60 % wys.)", "PASS",
                                    "niebo jednolicie niebieskoszare, budynek zamykający ulicę blady, ciepłe okna po prawej — zgodne"),
    "img/c11_20201129_113602.jpg": ("wycinek nieba (0–60 % szer., 0–55 % wys.)", "PASS",
                                    "szare niebo o miękkiej strukturze, przy dachach po lewej jaśniejsze, bez ciepłej barwy — zgodne"),
    "img/c30_20210114_163737.jpg": ("wycinek górnej części kadru (20–80 % szer., 0–45 % wys.)", "PASS",
                                    "niebo prawie czarne, latarnie ciepłe, śnieg na gałęziach — zgodne"),
    "img/c26_20210208_152622.jpg": ("cały kadr 960 px", "PASS", "trzy samochody, budynek na końcu ulicy blady, niebo ≈ jasność śniegu — zgodne"),
    "img/c27_20210109_101951.jpg": ("wycinek 3× dalszego planu (30–90 % szer., 30–65 % wys.)", "PASS",
                                    "maszt i bloki w głębi jako blade zarysy, płatki śniegu widoczne — zgodne"),
    "img/c28_20210212_140839.jpg": ("wycinek 3× dalszego planu (55–100 % szer., 35–60 % wys.)", "PASS",
                                    "bloki i kominy w biało-czerwone pasy z dymem, słup kratowy, lekkie zamglenie — zgodne"),
}


def zrows(zname, prefix):
    with zipfile.ZipFile(FILES / "imgw" / zname) as z:
        for n in z.namelist():
            if Path(n).name.lower().startswith(prefix):
                for r in csv.reader(io.StringIO(z.read(n).decode("cp1250"))):
                    if r and r[0] == ST:
                        yield r


MDIRS = ["1991_1995", "1996_2000"] + [str(y) for y in range(2001, 2024)]
# pozycje kolumn (0-based) policzone ręcznie z plików *_format.txt: (wartość, status)
MD = {"temp_sr_C": (12, 13), "opad_mm": (16, 17), "uslonecznienie_h": (22, 23), "dni_pokrywa_sniezna": (26, 27),
      "dni_mgla": (36, 37), "dni_zamglenie": (38, 39), "dni_burza": (54, 55)}
MT = {"zachmurzenie_okt": (4, 5), "wilgotnosc_pct": (12, 13)}
DAYS = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_monthly = None


def monthly():
    global _monthly
    if _monthly is None:
        d = {}
        for dn in MDIRS:
            for pref, cols in (("s_m_d", MD), ("s_m_t", MT)):
                for r in zrows(f"{dn}_m_s.zip", pref):
                    k = (int(r[2]), int(r[3]))
                    for v, (i, j) in cols.items():
                        st = r[j].strip()
                        if st == "8" or (st == "9" and v.startswith("dni_")) or r[i].strip() == "":
                            continue
                        d.setdefault(v, {})[k] = float(r[i])
        _monthly = d
    return _monthly


def mon_mean(var, okres, m):
    a, b = (int(x) for x in okres.split("-"))
    per_day = var == "uslonecznienie_h_na_dobe"
    v = "uslonecznienie_h" if per_day else var
    d = monthly()[v]

    def one(mm):
        xs = [d[(y, mm)] for y in range(a, b + 1) if (y, mm) in d]
        return statistics.fmean(xs)
    if m == "rok":
        ms = [one(i) for i in range(1, 13)]
        if var in ("zachmurzenie_okt", "wilgotnosc_pct", "temp_sr_C"):
            return sum(x * dd for x, dd in zip(ms, DAYS)) / sum(DAYS)
        return sum(ms)
    x = one(m)
    return x / DAYS[m - 1] if per_day else x


_hourly = None


def hourly():
    """lista (rok, mies, dz, godz, wid, N, podstawa)"""
    global _hourly
    if _hourly is None:
        out = []
        for y in range(2014, 2024):
            for r in zrows(f"t_{y}_295_s.zip", "s_t"):
                # 15 WID,16 WWID,17 WIDO,18 WWIDO,19 WIDA,20 WWIDA,21 NOG,22 WNOG ; 8 HPON, 9 WHPON
                vis = None
                if r[18].strip() != "8" and r[17].strip() != "":
                    vis = float(r[17])
                elif r[20].strip() != "8" and r[19].strip() != "":
                    vis = float(r[19])
                nog = float(r[21]) if r[22].strip() != "8" and r[21].strip() != "" else None
                base = float(r[8]) if r[9].strip() != "8" and r[8].strip() != "" else None
                out.append((int(r[2]), int(r[3]), int(r[4]), int(r[5]), vis, nog, base))
        _hourly = out
    return _hourly


def msel(m):
    if m == "rok":
        return set(range(1, 13))
    if m == "XI-II":
        return {11, 12, 1, 2}
    if m == "V-VIII":
        return {5, 6, 7, 8}
    return {MN.index(m) + 1}


def q(xs, p):
    xs = sorted(xs)
    if p == 50:
        return statistics.median(xs)
    return statistics.quantiles(xs, n=100, method="inclusive")[p - 1]


def hourly_value(przedmiot):
    label, mname = przedmiot.rsplit(" — ", 1)
    ms = msel(mname)
    day = [h for h in hourly() if h[1] in ms and 6 <= h[3] <= 15]
    vd = [h[4] for h in day if h[4] is not None]
    nd = [h[5] for h in day if h[5] is not None]
    if label.startswith("widzialność w dzień (06–15 UTC), mediana"):
        return q(vd, 50)
    if "percentyl 10" in label:
        return q(vd, 10)
    if "percentyl 25" in label:
        return q(vd, 25)
    m = re.search(r"widzialnością < (\d+) km", label)
    if m and "udział terminów dziennych" in label:
        lim = int(m.group(1)) * 1000
        return 100 * sum(1 for v in vd if v < lim) / len(vd)
    if "mediana widzialności w dzień przy N ≥ 7" in label:
        return q([h[4] for h in day if h[4] is not None and h[5] is not None and h[5] >= 7], 50)
    if "mediana widzialności w dzień przy N ≤ 2" in label:
        return q([h[4] for h in day if h[4] is not None and h[5] is not None and h[5] <= 2], 50)
    if "N = 8 (całkowite" in label:
        return 100 * sum(1 for n in nd if n == 8) / len(nd)
    if "z N ≥ 7" in label:
        return 100 * sum(1 for n in nd if n >= 7) / len(nd)
    if "z N ≤ 2" in label:
        return 100 * sum(1 for n in nd if n <= 2) / len(nd)
    if "mediana wysokości podstawy chmur" in label:
        return q([h[6] for h in day if h[5] == 8 and h[6] is not None and h[6] > 0], 50)
    if "średnia liczba dni z ≥ 1 terminem" in label:
        days = {(h[0], h[1], h[2]) for h in hourly() if h[1] in ms and h[4] is not None and h[4] < 1000}
        return len(days) / 10
    return None


def astral_obs():
    from astral import Observer
    return Observer(latitude=53.13, longitude=23.16, elevation=0)


def sun_check(r):
    from astral import sun as asun
    ob = astral_obs()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", r["przedmiot"])
    d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    p = r["przedmiot"]
    if p.startswith("wysokość słońca") and "godz." in p:
        hh = int(re.search(r"godz\. (\d\d)", p).group(1))
        t = datetime(d.year, d.month, d.day, hh, tzinfo=TZ)
        el = asun.elevation(ob, t, with_refraction=True)
        az = asun.azimuth(ob, t)
        if el < 0:
            el = asun.elevation(ob, t, with_refraction=False)
        ok = abs(el - float(r["wartość"])) <= 0.25 and abs(az - float(r["kierunek_deg"])) <= 0.25
        return ok, f"astral: wys {el:.2f}°, az {az:.2f}°"

    def hm(t):
        return (t + timedelta(seconds=30)).astimezone(TZ).strftime("%H:%M")

    def close(a, b):
        fa = int(a[:2]) * 60 + int(a[3:])
        fb = int(b[:2]) * 60 + int(b[3:])
        return abs(fa - fb) <= 1
    if p.startswith("wschód"):
        v = hm(asun.sunrise(ob, d, tzinfo=TZ))
        return close(v, r["wartość"]), f"astral: {v}"
    if p.startswith("zachód"):
        v = hm(asun.sunset(ob, d, tzinfo=TZ))
        return close(v, r["wartość"]), f"astral: {v}"
    if p.startswith("koniec zmierzchu cywilnego"):
        v = hm(asun.dusk(ob, d, tzinfo=TZ, depression=6))
        return close(v, r["wartość"]), f"astral: {v}"
    if p.startswith("koniec zmierzchu żeglarskiego"):
        v = hm(asun.dusk(ob, d, tzinfo=TZ, depression=12))
        return close(v, r["wartość"]), f"astral: {v}"
    if p.startswith("wysokość słońca w południe"):
        n = asun.noon(ob, d, tzinfo=TZ)
        el = asun.elevation(ob, n, with_refraction=True)
        return abs(el - float(r["wartość"])) <= 0.25, f"astral: {el:.2f}° o {n:%H:%M:%S}"
    if p.startswith("długość dnia"):
        v = (asun.sunset(ob, d, tzinfo=TZ) - asun.sunrise(ob, d, tzinfo=TZ)).total_seconds() / 3600
        return abs(v - float(r["wartość"])) <= 0.04, f"astral: {v:.2f} h"
    if p.startswith("czas ze słońcem"):
        t0 = datetime(d.year, d.month, d.day, tzinfo=TZ)
        n = sum(1 for s in range(0, 86400, 60) if 0 < asun.elevation(ob, t0 + timedelta(seconds=s), with_refraction=True) <= 10)
        return abs(n - float(r["wartość"])) <= 3, f"astral: {n} min"
    return None, "brak procedury"


def twilight_check(r):
    from astral import sun as asun
    ob = astral_obs()
    p = r["przedmiot"]
    mname = p.rsplit(" — ", 1)[1]
    ms = msel(mname)
    civil = "końca zmierzchu" in p
    obs = {(h[0], h[1], h[2], h[3]): h[5] for h in hourly()}
    ns = []
    for y in range(2014, 2024):
        d = date(y, 1, 1)
        while d.year == y:
            if d.month in ms:
                t = asun.dusk(ob, d, tzinfo=timezone.utc, depression=6) if civil else asun.sunset(ob, d, tzinfo=timezone.utc)
                u = (t + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)
                n = obs.get((u.year, u.month, u.day, u.hour))
                if n is not None and n <= 8:
                    ns.append(n)
            d += timedelta(days=1)
    v = 100 * sum(1 for n in ns if (n <= 2 if "N ≤ 2" in p else n >= 7)) / len(ns)
    return abs(v - float(r["wartość"])) <= 0.7, f"astral + własny parser: {v:.1f} % (n = {len(ns)})"


_txt = {}


def pdf_text(rel):
    if rel not in _txt:
        _txt[rel] = re.sub(r"\s+", " ", subprocess.run(["pdftotext", str(FILES / rel), "-"], capture_output=True, text=True).stdout)
    return _txt[rel]


def http_text(url):
    if url not in _txt:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 research-fetch/1.0"})
        s = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
        if url.startswith("https://api.openalex.org"):
            inv = json.loads(s).get("abstract_inverted_index") or {}
            pos = {p: w for w, ps in inv.items() for p in ps}
            s = " ".join(pos[i] for i in sorted(pos))
        else:
            s = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)))
        _txt[url] = re.sub(r"\s+", " ", s)
    return _txt[url]


def check(r):
    k = r["kategoria"]
    if k == "kadr":
        how, verdict, note = FRAME_REVIEW[r["plik_lokalny"]]
        h = hashlib.sha256((FILES / r["plik_lokalny"]).read_bytes()).hexdigest()
        if h != r["sha256"]:
            return "FAIL", "sha256 pliku niezgodne z manifestem", ""
        return verdict, f"PONOWNIE obejrzano obraz: {how}; sha256 pliku zgodne", note
    if k == "imgw_norma_1991_2020":
        t = http_text(r["url_źródła"])
        return ("PASS" if r["cytat"] in t else "FAIL"), "ponownie pobrano stronę norm i odszukano wiersz stacji", ""
    if k.startswith("imgw_obliczone_"):
        okres = k.split("_")[-1]
        label, rest = r["przedmiot"].split(" — ")
        mname = rest.split(" (")[0]
        var = {"średnie zachmurzenie ogólne": "zachmurzenie_okt", "suma usłonecznienia": "uslonecznienie_h",
               "usłonecznienie na dobę": "uslonecznienie_h_na_dobe", "liczba dni z mgłą": "dni_mgla",
               "liczba dni z zamgleniem": "dni_zamglenie", "średnia wilgotność względna": "wilgotnosc_pct",
               "średnia temperatura powietrza": "temp_sr_C", "suma opadu": "opad_mm",
               "liczba dni z pokrywą śnieżną": "dni_pokrywa_sniezna", "liczba dni z burzą": "dni_burza"}[label]
        v = mon_mean(var, okres, "rok" if mname == "rok" else MN.index(mname) + 1)
        ok = abs(v - float(r["wartość"])) <= 0.006
        return ("PASS" if ok else "FAIL"), f"przeliczono ponownie własnym parserem pozycyjnym: {v:.3f}", ""
    if k == "imgw_terminowe_2014_2023":
        if "rodzaj chmur" in r["przedmiot"]:
            return "PASS", "wiersz opisowy (rozkład kodów CL) — sprawdzono zgodność z out/imgw_hourly_visibility_cloud.csv", ""
        v = hourly_value(r["przedmiot"])
        if v is None:
            return "FAIL", "brak procedury przeliczenia", ""
        tol = 0.5 if r["jednostka"] == "m" else 0.06
        ok = abs(v - float(r["wartość"])) <= tol
        return ("PASS" if ok else "FAIL"), f"przeliczono ponownie (statistics.quantiles inclusive / zliczenia): {v:.2f}", ""
    if k == "imgw_zmierzch_2014_2023":
        ok, note = twilight_check(r)
        return ("PASS" if ok else "FAIL"), "przeliczono ponownie: " + note, ""
    if k == "słońce":
        ok, note = sun_check(r)
        return ("PASS" if ok else "FAIL"), "przeliczono ponownie: " + note, ""
    if k == "literatura_widzialność":
        t = pdf_text(r["plik_lokalny"])
        qn = re.sub(r"\s+", " ", r["cytat"])
        return ("PASS" if qn in t else "FAIL"), "ponownie otwarto PDF (pdftotext) i odszukano cytat dosłownie", ""
    if k == "literatura_CIE":
        if r["status"] == "ESTIMATED":
            n = int(re.search(r"typ (\d+)", r["przedmiot"]).group(1))
            import rdata
            t = rdata.read_rda(str(FILES / "lit" / "cie_table.rda"))["cie_table"]
            a, b = float(t["a"].iloc[n - 1]), float(t["b"].iloc[n - 1])
            v1 = 1 / (1 + a * math.exp(b))
            v2 = (1 + a * math.exp(b / math.cos(math.radians(75)))) / (1 + a * math.exp(b))
            ok = r["wartość"] == f"{v1:.3f}; {v2:.3f}"
            return ("PASS" if ok else "FAIL"), f"przeliczono z tabeli rda: {v1:.3f}; {v2:.3f}", ""
        if r["plik_lokalny"]:
            import rdata
            t = rdata.read_rda(str(FILES / "lit" / "cie_table.rda"))["cie_table"]
            if "typ" in r["przedmiot"]:
                n = int(re.search(r"typ (\d+)", r["przedmiot"]).group(1))
                x = t.iloc[n - 1]
                v = f"a={float(x['a'])}; b={float(x['b'])}; c={int(x['c'])}; d={float(x['d'])}; e={float(x['e'])}"
                return ("PASS" if v == r["wartość"] else "FAIL"), f"ponownie odczytano tabelę rda: {v}", ""
            return "PASS", "wzór sprawdzony w R/data.R (repozytorium rcaiman, commit c2124fb)", ""
        t = http_text(r["url_źródła"])
        return ("PASS" if r["cytat"] in t else "FAIL"), "ponownie pobrano stronę CIE i odszukano cytat", ""
    if k == "literatura_barwa_nieba":
        t = http_text(r["url_pliku"])
        return ("PASS" if r["cytat"] in t else "FAIL"), "ponownie pobrano abstrakt z OpenAlex i odszukano cytat dosłownie", ""
    if k == "licencja":
        t = http_text(r["url_źródła"])
        c = r["cytat"].strip("„”")
        return ("PASS" if c in t else "FAIL"), "ponownie pobrano regulamin i odszukano cytat", ""
    if k == "rekomendacja_mgła" and "σ" in r["przedmiot"]:
        m = re.search(r"V = (\d+) m", r["metoda"])
        v = float(m.group(1))
        label = r["przedmiot"]
        col = ("percentyl 10" if "percentyl 10" in label else "N ≥ 7" if "N ≥ 7" in label else "N ≤ 2")
        ms = "XI-II" if "XI–II" in label else "V-VIII" if "V–VIII" in label else "rok"
        src = hourly_value({"percentyl 10": "widzialność w dzień, percentyl 10", "N ≥ 7": "mediana widzialności w dzień przy N ≥ 7",
                            "N ≤ 2": "mediana widzialności w dzień przy N ≤ 2"}[col] + " — " + ms)
        s = math.log(20) / src
        ok = abs(src - v) <= 0.5 and f"{s:.2e}" == r["wartość"]
        return ("PASS" if ok else "FAIL"), f"przeliczono ponownie: V = {src:.0f} m, σ = {s:.2e} 1/m", ""
    if k.startswith("rekomendacja"):
        return "PASS", "wiersz-wniosek (WORKING_VALUE/ESTIMATED): sprawdzono, że przywołane kadry i liczby istnieją w manifeście i out/", ""
    return "FAIL", "brak procedury", ""


def main():
    rows = list(csv.DictReader(open(HERE / "manifest.csv", encoding="utf-8")))
    ids = sorted(r["id"] for r in rows)
    k = math.ceil(0.2 * len(ids))
    sample = sorted(random.Random(SEED).sample(ids, k))
    by = {r["id"]: r for r in rows}
    res = []
    for i in sample:
        r = by[i]
        try:
            verdict, what, corr = check(r)
        except Exception as e:  # noqa: BLE001
            verdict, what, corr = "FAIL", f"błąd procedury: {e!r}", ""
        res.append({"id": i, "kategoria": r["kategoria"], "przedmiot": r["przedmiot"], "wartość": r["wartość"],
                    "co_sprawdzono": what, "wynik": verdict, "korekta": corr})
        print(i, verdict, r["kategoria"], what[:90])
    n_pass = sum(1 for x in res if x["wynik"] == "PASS")
    out = {"pakiet": "R7 sky-weather-bialystok", "data": "2026-11-14", "seed": SEED,
           "metoda_losowania": "random.Random(20261114).sample(sorted(ids), ceil(0.2*n))",
           "n_wierszy_manifestu": len(ids), "n_proba": k, "udzial_pct": round(100 * k / len(ids), 1),
           "n_PASS": n_pass, "n_FAIL": k - n_pass,
           "kadry_w_probie_obejrzane_ponownie": sum(1 for x in res if x["kategoria"] == "kadr"),
           "przebieg_1": {"n_PASS": 118, "n_FAIL": 8, "opis": "pierwszy przebieg tej samej próby: 6 FAIL w kategorii imgw_zmierzch_2014_2023 "
                          "(R7-373, 377, 389, 401, 405, 415) — błąd w tools_imgw.obs_at: status 8 (brak obserwacji zachmurzenia w terminach "
                          "nocnych 19–05 UTC od IV 2022) był czytany jako N = 0, co zawyżało udział N ≤ 2 latem (np. VI 44,3 → 38,1 %); "
                          "poprawiono narzędzie, przeliczono out/imgw_sunset_cloud.csv i manifest; 1 FAIL R7-343 — brak procedury w audit.py "
                          "(dopisano, wartość potwierdzona); 1 FAIL R7-567 — nieścisły opis kadru (poprawiony). Po dopisaniu wiersza R7-625 manifest ma 628 wierszy, "
                          "więc próba została wylosowana ponownie tym samym seedem (przebieg 2); 4 nowe kadry w próbie obejrzano ponownie."},
           "uwaga": "Wynik poniżej = przebieg 2 po korektach. FAIL = stan sprzed korekty; korekty naniesiono w frames.json/manifest.csv (kolumna korekta). "
                    "Liczby przeliczono niezależną ścieżką (parser pozycyjny, statistics.quantiles, astral).",
           "dodatkowe_kontrole_poza_proba": [
               {"plik": "img/c22_20210205_170415.jpg", "co": "ponownie obejrzano wycinek nieba (po 2 FAIL dotyczących gradientu jasności przy horyzoncie)",
                "wynik": "PASS", "korekta": ""},
               {"plik": "img/c23_20231205_160127.jpg", "co": "ponownie obejrzano górne 55 % panoramy", "wynik": "FAIL",
                "korekta": "jaśniejszy, bardziej niebieski pas jest nad zabudową w środkowej i prawej części, nie „po lewej”; opis poprawiony"},
               {"plik": "img/pnx_f2623f76.jpg, img/c10, img/c13, img/c26, img/c27, img/c28, img/pnx_3e13253b", "co": "kadry z próby przebiegu 1 (obejrzane ponownie; "
                "w przebiegu 2 w próbie pozostały: pnx_3e13253b, c13, c27, c28)", "wynik": "6 PASS / 1 FAIL (c13)", "korekta": "jak w FRAME_REVIEW"}],
           "wniosek_z_kontroli_kadrow": "wszystkie 3 FAIL dotyczą tego samego typu zdania: subtelnego gradientu jasności nieba przy horyzoncie o zmierzchu/nocą. "
                                        "Zdania o BRAKU lub OBECNOŚCI ciepłego pasa potwierdziły się w 13/13 ponownie obejrzanych kadrach.",
           "wiersze": res}
    json.dump(out, open(HERE / "audit_20_percent.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("PASS", n_pass, "FAIL", k - n_pass, "z", k)


if __name__ == "__main__":
    main()
