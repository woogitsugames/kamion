#!/usr/bin/env python3
"""R7 sky-weather-bialystok — pobranie i przeliczenie danych IMGW-PIB (stacja synoptyczna BIAŁYSTOK,
kod 353230295 / 12295, plikowy skrót 295).

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy.
Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone.

Użycie (z katalogu pakietu):
    python3 -I tools_imgw.py download   # pobiera paczki do files/imgw/, zapisuje imgw_files.csv (url, sha256, bajty)
    python3 -I tools_imgw.py compute    # liczy tabele do out/*.csv
Wyłącznie biblioteka standardowa. Paczki ZIP są danymi niezaufanymi: czytane w pamięci (zipfile), bez rozpakowywania.
"""
from __future__ import annotations

import csv
import hashlib
import io
import statistics
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE / "files" / "imgw"
OUT = HERE / "out"
BASE = "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne"
STATION = "353230295"
ST_SHORT = "295"

# dane miesięczne: 1991–2023 (2024 w katalogu miesięcznym tylko do czerwca — UWAGA!.txt — pominięty)
MONTHLY_DIRS = ["1991_1995", "1996_2000"] + [str(y) for y in range(2001, 2024)]
# dane terminowe (co godzinę): 10 pełnych lat
HOURLY_YEARS = list(range(2014, 2024))

M_D_HEADER = ("NSP,POST,ROK,MC,TMAX,WTMAX,TMXS,WTMXS,TMIN,WTMIN,TMNS,WTMNS,STM,WSTM,TMNG,WTMNG,SUMM,WSUMM,OPMX,WOPMX,"
              "DN1,DN2,SUUS,WSUUS,PKSN,WPKSN,PSDN,WPSDN,DESD,WDESD,SNID,WSNID,DSND,WDSND,GRDD,WGRDD,MGLD,WMGLD,ZAMD,"
              "WZAMD,SADD,WSADD,GOLD,WGOLD,ZAND,WZAND,ZAWD,WZAWD,ZMED,WZMED,W10D,WW10D,W15D,WW15D,BURD,WBURD,ROSD,"
              "WROSD,SZRD,WSZRD").split(",")
M_T_HEADER = ("NSP,POST,ROK,MC,NOS,WNOS,FWS,WFWS,TEMP,WTEMP,CPW,WCPW,WLGS,WWLGS,PPPS,WPPPS,PPPM,WPPPM,WODZ,WWODZ,"
              "WONO,WWONO").split(",")
S_T_HEADER = ("NSP,POST,ROK,MC,DZ,GG,HPOD,WHPOD,HPON,WHPON,HPOW,WHPOW,HTXT,POM1,POM2,WID,WWID,WIDO,WWIDO,WIDA,WWIDA,"
              "NOG,WNOG,KRWR,WKRWR,FWR,WFWR,PORW,WPORW,TEMP,WTEMP,TTZW,WTTZW,WENT,TWLW,CPW,WCPW,WLGW,WWLGW,TPTR,WTPTR,"
              "PPPS,WPPPS,PPPM,WPPPM,TECH,APP,WAPP,WO6G,WWO6G,ROPT,WROPT,POGB,POGU,CLCM,WCLCM,CHCL,WCHCL,CHLT,CHCM,"
              "WCHCM,CHMT,CHCH,WCHCH,CHHT,SGRN,WSGRN,DEFI,WDEFI,USLN,WUSLN").split(",")  # dalsze kolumny nieużywane

DAYS = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def file_list() -> list[tuple[str, str]]:
    """(nazwa lokalna, url)"""
    out = []
    for d in MONTHLY_DIRS:
        out.append((f"{d}_m_s.zip", f"{BASE}/miesieczne/synop/{d}/{d}_m_s.zip"))
    for y in HOURLY_YEARS:
        out.append((f"t_{y}_{ST_SHORT}_s.zip", f"{BASE}/terminowe/synop/{y}/{y}_{ST_SHORT}_s.zip"))
    for n, u in [
        ("Opis.txt", f"{BASE}/Opis.txt"),
        ("s_m_d_format.txt", f"{BASE}/miesieczne/synop/s_m_d_format.txt"),
        ("s_m_t_format.txt", f"{BASE}/miesieczne/synop/s_m_t_format.txt"),
        ("s_t_format.txt", f"{BASE}/terminowe/synop/s_t_format.txt"),
        ("wykaz_stacji.csv", f"{BASE}/wykaz_stacji.csv"),
    ]:
        out.append((n, u))
    return out


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def download() -> None:
    FILES.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, url in file_list():
        p = FILES / name
        if not p.exists() or p.stat().st_size == 0:
            for attempt in range(4):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "research-fetch/1.0"})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        p.write_bytes(r.read())
                    break
                except Exception as e:  # noqa: BLE001
                    print("retry", name, e, file=sys.stderr)
                    time.sleep(2 ** (attempt + 1))
            else:
                raise SystemExit(f"nie pobrano {url}")
        rows.append({"plik": f"imgw/{name}", "url": url, "sha256": sha256(p), "bajty": p.stat().st_size})
        print(name, p.stat().st_size)
    with open(HERE / "imgw_files.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["plik", "url", "sha256", "bajty"])
        w.writeheader()
        w.writerows(rows)
    print("razem bajtów:", sum(r["bajty"] for r in rows))


def read_zip_csv(zp: Path, prefix: str):
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if Path(n).name.lower().startswith(prefix):
                txt = z.read(n).decode("cp1250")
                yield from csv.reader(io.StringIO(txt))


def val(row: dict, key: str, status_key: str):
    """Wartość liczbową zwraca tylko dla statusu 'pomiar' (spacja/pusty). Status 8 = brak pomiaru -> None.
    Status 9 = brak zjawiska -> 0 dla sum (opad, usłonecznienie, pokrywa), ALE dla agregacji "Liczba dni z"
    status 9 = "brak pomiaru zjawisk na stacji" (s_m_d_format.txt) -> None (Białystok: zjawiska IV 2022–XII 2023)."""
    st = (row.get(status_key) or "").strip()
    v = (row.get(key) or "").strip()
    if st == "8":
        return None
    if st == "9":
        return None if key.endswith("D") and key not in ("STD",) else 0.0
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load_monthly():
    """-> dict[(rok, mies)] = {zmienna: wartość}"""
    data: dict[tuple[int, int], dict] = defaultdict(dict)
    for d in MONTHLY_DIRS:
        zp = FILES / f"{d}_m_s.zip"
        for r in read_zip_csv(zp, "s_m_d"):
            if r and r[0] == STATION:
                row = dict(zip(M_D_HEADER, r))
                k = (int(row["ROK"]), int(row["MC"]))
                data[k].update({
                    "temp_sr_C": val(row, "STM", "WSTM"),
                    "tmax_sr_C": val(row, "TMXS", "WTMXS"),
                    "tmin_sr_C": val(row, "TMNS", "WTMNS"),
                    "opad_mm": val(row, "SUMM", "WSUMM"),
                    "uslonecznienie_h": val(row, "SUUS", "WSUUS"),
                    "dni_pokrywa_sniezna": val(row, "PSDN", "WPSDN"),
                    "pokrywa_max_cm": val(row, "PKSN", "WPKSN"),
                    "dni_deszcz": val(row, "DESD", "WDESD"),
                    "dni_snieg": val(row, "SNID", "WSNID"),
                    "dni_mgla": val(row, "MGLD", "WMGLD"),
                    "dni_zamglenie": val(row, "ZAMD", "WZAMD"),
                    "dni_burza": val(row, "BURD", "WBURD"),
                })
        for r in read_zip_csv(zp, "s_m_t"):
            if r and r[0] == STATION:
                row = dict(zip(M_T_HEADER, r))
                k = (int(row["ROK"]), int(row["MC"]))
                data[k].update({
                    "zachmurzenie_okt": val(row, "NOS", "WNOS"),
                    "wilgotnosc_pct": val(row, "WLGS", "WWLGS"),
                    "wiatr_ms": val(row, "FWS", "WFWS"),
                })
    return data


MVARS = ["zachmurzenie_okt", "uslonecznienie_h", "dni_mgla", "dni_zamglenie", "wilgotnosc_pct", "temp_sr_C",
         "tmax_sr_C", "tmin_sr_C", "opad_mm", "dni_pokrywa_sniezna", "pokrywa_max_cm", "dni_deszcz", "dni_snieg",
         "dni_burza", "wiatr_ms"]


def pctl(sorted_vals, q):
    if not sorted_vals:
        return None
    i = q * (len(sorted_vals) - 1)
    lo = int(i)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (i - lo)


def compute_monthly():
    data = load_monthly()
    OUT.mkdir(exist_ok=True)
    with open(OUT / "imgw_monthly_raw.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rok", "miesiac"] + MVARS)
        for k in sorted(data):
            w.writerow([k[0], k[1]] + ["" if data[k].get(v) is None else data[k][v] for v in MVARS])
    periods = {"1991-2020": (1991, 2020), "2014-2023": (2014, 2023)}
    with open(OUT / "imgw_monthly_normals.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["okres", "miesiac", "zmienna", "srednia", "min", "max", "n_lat"])
        for pname, (a, b) in periods.items():
            for v in MVARS:
                annual = []
                for m in range(1, 13):
                    xs = [data[(y, m)][v] for y in range(a, b + 1) if (y, m) in data and data[(y, m)].get(v) is not None]
                    if xs:
                        w.writerow([pname, m, v, round(statistics.fmean(xs), 2), min(xs), max(xs), len(xs)])
                        annual.append(statistics.fmean(xs))
                    else:
                        w.writerow([pname, m, v, "", "", "", 0])
                if len(annual) == 12:
                    if v in ("zachmurzenie_okt", "wilgotnosc_pct", "temp_sr_C", "tmax_sr_C", "tmin_sr_C", "wiatr_ms"):
                        agg = sum(x * d for x, d in zip(annual, DAYS)) / sum(DAYS)
                    elif v == "pokrywa_max_cm":
                        agg = max(annual)
                    else:
                        agg = sum(annual)
                    w.writerow([pname, "rok", v, round(agg, 2), "", "", ""])
            # usłonecznienie na dobę
            for m in range(1, 13):
                xs = [data[(y, m)]["uslonecznienie_h"] for y in range(a, b + 1)
                      if (y, m) in data and data[(y, m)].get("uslonecznienie_h") is not None]
                if xs:
                    w.writerow([pname, m, "uslonecznienie_h_na_dobe", round(statistics.fmean(xs) / DAYS[m - 1], 2), "", "", len(xs)])
    print("miesięczne: lat-miesięcy", len(data))


def fnum(s):
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def compute_hourly():
    """Dane terminowe 2014–2023: widzialność [m], zachmurzenie ogólne [oktanty], kod pogody bieżącej, chmury CL.
    Godziny GG są w UTC (terminy synoptyczne). 'Dzień' = terminy 06–15 UTC (07–16 CET / 08–17 CEST): w grudniu
    obejmuje też zmierzch (zachód ok. 14:10 UTC), co jest zamierzone — jazda w grze = pora dzienna."""
    per_month = defaultdict(lambda: defaultdict(list))
    cnt = defaultdict(lambda: defaultdict(int))
    cl_over = defaultdict(lambda: defaultdict(int))
    base_over = defaultdict(list)
    src_kind = defaultdict(int)
    nrows = 0
    daily = defaultdict(lambda: {"fog_vis": False, "fog_ww": False})  # (rok, mies, dzień)
    nog_all = defaultdict(list)
    for y in HOURLY_YEARS:
        zp = FILES / f"t_{y}_{ST_SHORT}_s.zip"
        for r in read_zip_csv(zp, "s_t"):
            if not r or r[0] != STATION:
                continue
            row = dict(zip(S_T_HEADER, r))
            nrows += 1
            m = int(row["MC"])
            gg = int(row["GG"])
            day = 6 <= gg <= 15
            # widzialność: operator (WIDO), w razie braku automat (WIDA); status 8 = brak
            vis = None
            if (row["WWIDO"] or "").strip() != "8":
                vis = fnum(row["WIDO"])
                if vis is not None:
                    src_kind["WIDO"] += 1
            if vis is None and (row["WWIDA"] or "").strip() != "8":
                vis = fnum(row["WIDA"])
                if vis is not None:
                    src_kind["WIDA"] += 1
            nog = fnum(row["NOG"]) if (row["WNOG"] or "").strip() != "8" else None
            ww = fnum(row["POGB"])
            dk = (y, m, int(row["DZ"]))
            if vis is not None and vis < 1000:
                daily[dk]["fog_vis"] = True
            if ww is not None and 40 <= ww <= 49:
                daily[dk]["fog_ww"] = True
            else:
                daily[dk]  # rejestruje dobę
            if nog is not None and nog <= 8:
                nog_all[m].append(nog)
            if vis is not None:
                per_month[m]["vis_all"].append(vis)
                if day:
                    per_month[m]["vis_day"].append(vis)
                    if nog is not None and nog >= 7:
                        per_month[m]["vis_day_overcast"].append(vis)
                    if nog is not None and nog <= 2:
                        per_month[m]["vis_day_clear"].append(vis)
            if nog is not None and day:
                cnt[m]["n_day_nog"] += 1
                if nog == 8:
                    cnt[m]["nog8"] += 1
                if nog >= 7:
                    cnt[m]["nog78"] += 1
                if nog <= 2:
                    cnt[m]["nog02"] += 1
                if nog == 9:
                    cnt[m]["nog9"] += 1
                if 3 <= nog <= 6:
                    cnt[m]["nog36"] += 1
                if nog == 8:
                    cl = (row["CHCL"] or "").strip()
                    cl_over[m][cl] += 1
                    hb = fnum(row["HPON"]) if (row["WHPON"] or "").strip() != "8" else None
                    if hb is not None and hb > 0:
                        base_over[m].append(hb)
            if ww is not None and day:
                cnt[m]["n_day_ww"] += 1
                if 40 <= ww <= 49:
                    cnt[m]["ww_mgla"] += 1
                if ww == 10:
                    cnt[m]["ww_zamglenie"] += 1
                if 50 <= ww <= 99:
                    cnt[m]["ww_opad"] += 1
    with open(OUT / "imgw_hourly_visibility_cloud.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        cols = ["miesiac", "n_obs_dzien", "wid_dzien_p05_m", "wid_dzien_p10_m", "wid_dzien_p25_m", "wid_dzien_mediana_m",
                "wid_dzien_p75_m", "udzial_wid_lt1km_dzien_pct", "udzial_wid_lt4km_dzien_pct", "udzial_wid_lt10km_dzien_pct",
                "udzial_wid_ge20km_dzien_pct", "wid_mediana_przy_N>=7_m", "wid_mediana_przy_N<=2_m", "wid_mediana_doba_m",
                "udzial_wid_lt1km_doba_pct", "udzial_N=8_dzien_pct", "udzial_N>=7_dzien_pct", "udzial_N3-6_dzien_pct",
                "udzial_N<=2_dzien_pct", "udzial_N=9_niebo_niewidoczne_pct", "udzial_ww_mgla_40-49_dzien_pct",
                "udzial_ww_zamglenie_10_dzien_pct", "udzial_ww_opad_50-99_dzien_pct", "podstawa_chmur_mediana_przy_N=8_m",
                "CL_przy_N=8_top3", "dni_z_wid_lt1km_na_miesiac", "dni_z_ww_mgla_40-49_na_miesiac",
                "zachmurzenie_srednie_doba_okt"]
        w.writerow(cols)

        def emit(label, months):
            vd = sorted(x for m in months for x in per_month[m]["vis_day"])
            va = sorted(x for m in months for x in per_month[m]["vis_all"])
            vo = sorted(x for m in months for x in per_month[m]["vis_day_overcast"])
            vc = sorted(x for m in months for x in per_month[m]["vis_day_clear"])
            c = defaultdict(int)
            clc = defaultdict(int)
            for m in months:
                for k, v in cnt[m].items():
                    c[k] += v
                for k, v in cl_over[m].items():
                    clc[k] += v
            bo = sorted(x for m in months for x in base_over[m])

            def share(xs, lo=None, hi=None):
                if not xs:
                    return ""
                n = sum(1 for x in xs if (lo is None or x >= lo) and (hi is None or x < hi))
                return round(100 * n / len(xs), 1)

            def pc(k, n):
                return round(100 * c[k] / c[n], 1) if c[n] else ""

            tot = sum(clc.values()) or 1
            top = "; ".join(f"CL={k or '∅'}:{round(100 * v / tot)}%" for k, v in sorted(clc.items(), key=lambda t: -t[1])[:3])
            w.writerow([label, len(vd), round(pctl(vd, .05)), round(pctl(vd, .10)), round(pctl(vd, .25)), round(pctl(vd, .5)),
                        round(pctl(vd, .75)), share(vd, hi=1000), share(vd, hi=4000), share(vd, hi=10000), share(vd, lo=20000),
                        round(pctl(vo, .5)) if vo else "", round(pctl(vc, .5)) if vc else "", round(pctl(va, .5)),
                        share(va, hi=1000), pc("nog8", "n_day_nog"), pc("nog78", "n_day_nog"), pc("nog36", "n_day_nog"),
                        pc("nog02", "n_day_nog"), pc("nog9", "n_day_nog"), pc("ww_mgla", "n_day_ww"),
                        pc("ww_zamglenie", "n_day_ww"), pc("ww_opad", "n_day_ww"), round(pctl(bo, .5)) if bo else "", top,
                        round(sum(1 for k, d in daily.items() if k[1] in months and d["fog_vis"]) / len(HOURLY_YEARS), 1),
                        round(sum(1 for k, d in daily.items() if k[1] in months and d["fog_ww"]) / len(HOURLY_YEARS), 1),
                        round(statistics.fmean([x for m in months for x in nog_all[m]]), 2)])

        for m in range(1, 13):
            emit(m, [m])
        emit("rok", list(range(1, 13)))
        emit("XI-II", [11, 12, 1, 2])
        emit("V-VIII", [5, 6, 7, 8])
    print("terminowe: wierszy", nrows, dict(src_kind))


_OBS_CACHE: dict = {}


def obs_at(y: int, mo: int, d: int, hour_utc: int):
    """Obserwacja terminowa stacji BIAŁYSTOK dla podanej godziny UTC (lata HOURLY_YEARS). Zwraca dict lub None.
    N = zachmurzenie ogólne [oktanty], wid = widzialność [m], ww = kod pogody bieżącej, CL = kod chmur niskich,
    podstawa = wysokość podstawy niższej [m], T [°C], RH [%]."""
    if y not in HOURLY_YEARS:
        return None
    if y not in _OBS_CACHE:
        tab = {}
        for r in read_zip_csv(FILES / f"t_{y}_{ST_SHORT}_s.zip", "s_t"):
            if r and r[0] == STATION:
                row = dict(zip(S_T_HEADER, r))
                tab[(int(row["MC"]), int(row["DZ"]), int(row["GG"]))] = row
        _OBS_CACHE[y] = tab
    row = _OBS_CACHE[y].get((mo, d, hour_utc))
    if row is None:
        return None
    return {"N_okt": row["NOG"], "wid_m": row["WIDO"] if (row["WWIDO"] or "").strip() != "8" else row["WIDA"],
            "ww": row["POGB"], "CL": row["CHCL"], "CL_txt": row["CHLT"], "podstawa_m": row["HPON"],
            "T_C": row["TEMP"], "RH_pct": row["WLGW"]}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "download":
        download()
    elif cmd == "obs":  # python3 -I tools_imgw.py obs 2019 8 15 15
        print(obs_at(*[int(x) for x in sys.argv[2:6]]))
    elif cmd == "compute":
        compute_monthly()
        compute_hourly()
    else:
        raise SystemExit(__doc__)
