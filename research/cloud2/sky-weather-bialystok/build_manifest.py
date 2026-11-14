#!/usr/bin/env python3
"""R7 — składa manifest.csv z: out/*.csv (IMGW, słońce), frames.json (opisy obejrzanych kadrów), commons_meta.json,
imgw_files.csv oraz wierszy literatury i rekomendacji zapisanych niżej. Liczy sha256 plików z files/.
Użycie: python3 -I build_manifest.py   (po: tools_imgw.py download+compute, tools_normy.py, tools_sun.py, tools_twilight.py)"""
import csv
import hashlib
import json
import math
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tools_imgw as ti  # noqa: E402
import tools_sun as ts  # noqa: E402

TODAY = "2026-11-14"
TZ = ZoneInfo("Europe/Warsaw")
COLS = ["id", "kategoria", "przedmiot", "wartość", "jednostka", "status", "metoda", "cytat", "url_źródła", "url_pliku",
        "licencja", "autor", "data_dostępu", "sha256", "lat", "lon", "kierunek_deg", "opis_co_widać", "duplikat_sha256",
        "uwagi", "plik_lokalny", "data_czas_lokalny", "wys_słońca_deg", "az_słońca_deg", "imgw_N_okt", "imgw_wid_m",
        "imgw_ww", "imgw_chmury_niskie", "pas_ciepły_przy_horyzoncie"]
IMGW_LIC = ("Regulamin udostępniania danych IMGW-PIB (§5: nieodpłatnie; obowiązek podania źródła i informacji o przetworzeniu; "
            "dane o wysokiej wartości — w każdym celu)")
IMGW_AUT = "IMGW-PIB"
IMGW_DIR = "https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/"
MN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
rows = []


def add(**kw):
    r = {c: "" for c in COLS}
    r.update(kw)
    r["id"] = f"R7-{len(rows) + 1:03d}"
    r.setdefault("data_dostępu", TODAY)
    if not r["data_dostępu"]:
        r["data_dostępu"] = TODAY
    rows.append(r)
    return r


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd(name):
    return list(csv.DictReader(open(HERE / "out" / name, encoding="utf-8")))


# ---------- A. normy oficjalne IMGW 1991–2020 (SOURCED) ----------
for r in rd("imgw_normy_1991_2020.csv"):
    vals = [r[str(i)] for i in range(1, 13)] + [r["rok"]]
    f = HERE / "files" / "normy" / f"normy_{r['kod']}.html"
    add(kategoria="imgw_norma_1991_2020", przedmiot=f"{r['wskaznik']} — BIAŁYSTOK 12295, I–XII i rok",
        **{"wartość": " | ".join(vals)}, jednostka={"TSR_AVE": "°C", "OPAD_SUMA": "mm", "SNIEG_0": "dni", "USL": "h",
                                                    "ZACHM": "oktanty", "D_POCHMURNE": "dni", "D_POGODNE": "dni"}[r["kod"]],
        status="SOURCED", metoda="odczyt wiersza stacji z tabeli norm (tools_normy.py)",
        cytat="BIAŁYSTOK 12295 " + " ".join(vals), **{"url_źródła": f"https://klimat.imgw.pl/pl/climate-normals/{r['kod']}"},
        url_pliku=f"https://klimat.imgw.pl/pl/climate-normals/{r['kod']}", licencja=IMGW_LIC, autor=IMGW_AUT,
        sha256=sha(f), plik_lokalny=f"normy/{f.name}", lat="53.107", lon="23.162",
        uwagi="Portal Klimat IMGW-PIB, normy klimatyczne 1991–2020; współrzędne stacji przybliżone (UNVERIFIED)")

# ---------- B. przeliczenie własne z CSV IMGW (ESTIMATED = obliczone) ----------
norm = rd("imgw_monthly_normals.csv")
VAR = {"zachmurzenie_okt": ("średnie zachmurzenie ogólne", "oktanty"), "uslonecznienie_h": ("suma usłonecznienia", "h"),
       "uslonecznienie_h_na_dobe": ("usłonecznienie na dobę", "h/dobę"), "dni_mgla": ("liczba dni z mgłą", "dni"),
       "dni_zamglenie": ("liczba dni z zamgleniem", "dni"), "wilgotnosc_pct": ("średnia wilgotność względna", "%"),
       "temp_sr_C": ("średnia temperatura powietrza", "°C"), "opad_mm": ("suma opadu", "mm"),
       "dni_pokrywa_sniezna": ("liczba dni z pokrywą śnieżną", "dni"), "dni_burza": ("liczba dni z burzą", "dni")}
SRC_M = {"zachmurzenie_okt": "s_m_t (NOS)", "wilgotnosc_pct": "s_m_t (WLGS)", "uslonecznienie_h": "s_m_d (SUUS)",
         "uslonecznienie_h_na_dobe": "s_m_d (SUUS)/liczba dni", "dni_mgla": "s_m_d (MGLD)", "dni_zamglenie": "s_m_d (ZAMD)",
         "temp_sr_C": "s_m_d (STM)", "opad_mm": "s_m_d (SUMM)", "dni_pokrywa_sniezna": "s_m_d (PSDN)",
         "dni_burza": "s_m_d (BURD)"}
for okres in ("1991-2020", "2014-2023"):
    for v, (label, unit) in VAR.items():
        if okres == "2014-2023" and v not in ("zachmurzenie_okt", "uslonecznienie_h", "dni_mgla", "dni_pokrywa_sniezna",
                                              "temp_sr_C"):
            continue
        for r in norm:
            if r["okres"] != okres or r["zmienna"] != v or r["srednia"] == "":
                continue
            m = r["miesiac"]
            mname = "rok" if m == "rok" else MN[int(m) - 1]
            add(kategoria=f"imgw_obliczone_{okres}", przedmiot=f"{label} — {mname} ({okres})", **{"wartość": r["srednia"]},
                jednostka=unit, status="ESTIMATED",
                metoda=f"średnia z wartości miesięcznych stacji 353230295, plik {SRC_M[v]}; tools_imgw.py compute; "
                       f"n lat = {r['n_lat'] or 'agregat roczny z 12 średnich'}",
                **{"url_źródła": IMGW_DIR + "miesieczne/synop/"}, licencja=IMGW_LIC, autor=IMGW_AUT,
                uwagi=("min–max miesięczne w okresie: " + r["min"] + "–" + r["max"]) if r["min"] != "" else "",
                lat="53.107", lon="23.162")

# ---------- C. dane terminowe 2014–2023: widzialność i zachmurzenie w dzień ----------
hv = rd("imgw_hourly_visibility_cloud.csv")
HC = [("wid_dzien_mediana_m", "widzialność w dzień (06–15 UTC), mediana", "m"),
      ("wid_dzien_p10_m", "widzialność w dzień, percentyl 10", "m"),
      ("wid_dzien_p25_m", "widzialność w dzień, percentyl 25", "m"),
      ("udzial_wid_lt1km_dzien_pct", "udział terminów dziennych z widzialnością < 1 km", "%"),
      ("udzial_wid_lt4km_dzien_pct", "udział terminów dziennych z widzialnością < 4 km", "%"),
      ("udzial_wid_lt10km_dzien_pct", "udział terminów dziennych z widzialnością < 10 km", "%"),
      ("wid_mediana_przy_N>=7_m", "mediana widzialności w dzień przy N ≥ 7", "m"),
      ("wid_mediana_przy_N<=2_m", "mediana widzialności w dzień przy N ≤ 2", "m"),
      ("udzial_N=8_dzien_pct", "udział terminów dziennych z N = 8 (całkowite zachmurzenie)", "%"),
      ("udzial_N>=7_dzien_pct", "udział terminów dziennych z N ≥ 7", "%"),
      ("udzial_N<=2_dzien_pct", "udział terminów dziennych z N ≤ 2", "%"),
      ("podstawa_chmur_mediana_przy_N=8_m", "mediana wysokości podstawy chmur przy N = 8 w dzień", "m"),
      ("dni_z_wid_lt1km_na_miesiac", "średnia liczba dni z ≥ 1 terminem o widzialności < 1 km (cała doba)", "dni")]
for col, label, unit in HC:
    for r in hv:
        m = r["miesiac"]
        mname = MN[int(m) - 1] if m.isdigit() else m
        if col in ("wid_dzien_p25_m", "udzial_wid_lt10km_dzien_pct", "podstawa_chmur_mediana_przy_N=8_m") and m.isdigit():
            continue  # tylko agregaty (rok, XI-II, V-VIII) — pełne dane w out/
        add(kategoria="imgw_terminowe_2014_2023", przedmiot=f"{label} — {mname}", **{"wartość": r[col]}, jednostka=unit,
            status="ESTIMATED",
            metoda="dane terminowe (co 1 h) stacji 353230295 z lat 2014–2023, pola WIDO/WIDA, NOG, HPON; terminy 06–15 UTC; "
                   f"n obserwacji dziennych = {r['n_obs_dzien']}; tools_imgw.py compute",
            **{"url_źródła": IMGW_DIR + "terminowe/synop/"}, licencja=IMGW_LIC, autor=IMGW_AUT, lat="53.107", lon="23.162")
for r in hv:
    if r["miesiac"] in ("rok", "XI-II", "V-VIII"):
        add(kategoria="imgw_terminowe_2014_2023", przedmiot=f"rodzaj chmur niskich (kod CL) przy N = 8 w dzień, 3 najczęstsze — {r['miesiac']}",
            **{"wartość": r["CL_przy_N=8_top3"]}, jednostka="% terminów", status="ESTIMATED",
            metoda="dane terminowe 2014–2023, pole CHCL przy NOG = 8, terminy 06–15 UTC; opisy tekstowe z pola CHLT: CL=5 „Sc …”, "
                   "CL=6 „St neb”, CL=7 „St fra”/„Sc op” z St fra, CL=9 „Cb cap”",
            **{"url_źródła": IMGW_DIR + "terminowe/synop/"}, licencja=IMGW_LIC, autor=IMGW_AUT,
            uwagi="znaczenie cyfr kodu CL wg klucza SYNOP przyjęte na podstawie pola tekstowego CHLT w tych samych danych")
ss = rd("imgw_sunset_cloud.csv")
for r in ss:
    mname = MN[int(r["miesiac"]) - 1] if r["miesiac"].isdigit() else r["miesiac"]
    pora = "zachodu słońca" if r["pora"] == "zachod" else "końca zmierzchu cywilnego"
    for col, label in (("udzial_N<=2_pct", "N ≤ 2"), ("udzial_N>=7_pct", "N ≥ 7")):
        add(kategoria="imgw_zmierzch_2014_2023", przedmiot=f"udział dni z {label} w terminie najbliższym {pora} — {mname}",
            **{"wartość": r[col]}, jednostka="%", status="ESTIMATED",
            metoda=f"dla każdej doby 2014–2023: godzina zdarzenia z tools_sun (NOAA) → najbliższy termin UTC → pole NOG; "
                   f"n dni = {r['n_dni']}; tools_twilight.py",
            **{"url_źródła": IMGW_DIR + "terminowe/synop/"}, licencja=IMGW_LIC, autor=IMGW_AUT)

# ---------- D. słońce (ESTIMATED, NOAA) ----------
sun = rd("sun_table.csv")
NOAA = "https://gml.noaa.gov/grad/solcalc/calcdetails.html"
for r in sun:
    d = r["data"]
    tzn = r["strefa"]
    for hh in ("08", "12", "16", "20"):
        add(kategoria="słońce", przedmiot=f"wysokość słońca {d} godz. {hh}:00 {tzn} (azymut w kolumnie kierunek_deg)",
            **{"wartość": r[f"wys_{hh}_deg"]}, jednostka="°", status="ESTIMATED",
            metoda="algorytm NOAA Solar Calculator (Meeus), własna implementacja tools_sun.py; wysokość pozorna z refrakcją NOAA "
                   "nad horyzontem, geometryczna pod horyzontem; kontrola: astral 3.2",
            **{"url_źródła": NOAA}, lat="53.130000", lon="23.160000", kierunek_deg=r[f"az_{hh}_deg"],
            data_czas_lokalny=f"{d} {hh}:00 {tzn}", **{"wys_słońca_deg": r[f"wys_{hh}_deg"], "az_słońca_deg": r[f"az_{hh}_deg"]})
    for col, label, unit in (("wschod", "wschód słońca", "gg:mm"), ("zachod", "zachód słońca", "gg:mm"),
                             ("koniec_zm_cywilnego", "koniec zmierzchu cywilnego (−6°)", "gg:mm"),
                             ("koniec_zm_zeglarskiego", "koniec zmierzchu żeglarskiego (−12°)", "gg:mm"),
                             ("wys_poludnie_deg", "wysokość słońca w południe słoneczne", "°"),
                             ("dlugosc_dnia_h", "długość dnia", "h"),
                             ("minuty_slonce_0_10deg", "czas ze słońcem na wysokości 0–10°", "min/dobę")):
        az = {"wschod": r["az_wschodu_deg"], "zachod": r["az_zachodu_deg"],
              "koniec_zm_cywilnego": r["az_konca_zm_cywilnego_deg"]}.get(col, "")
        add(kategoria="słońce", przedmiot=f"{label} {d} ({tzn})" + (" — azymut słońca w kolumnie kierunek_deg" if az else ""),
            **{"wartość": r[col]}, jednostka=unit, status="ESTIMATED",
            metoda="algorytm NOAA (tools_sun.py); zdarzenia = przejście wysokości geometrycznej środka tarczy przez −0,833° / −6° / −12° "
                   "(bisekcja do 1 s); kontrola: astral 3.2 (różnice ≤ 1 min)",
            **{"url_źródła": NOAA}, lat="53.130000", lon="23.160000", kierunek_deg=az,
            uwagi=("południe słoneczne " + r["poludnie_sloneczne"]) if col == "wys_poludnie_deg" else "")

# ---------- E. kadry ----------
meta = json.load(open(HERE / "commons_meta.json", encoding="utf-8"))
frames = json.load(open(HERE / "frames.json", encoding="utf-8"))
seen_sha = {}
for f in frames:
    p = HERE / "files" / "img" / (f["k"] + ".jpg")
    h = sha(p)
    if f["src"] == "commons":
        m = meta[f["title"]]
        t = datetime.strptime(m["dto"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)
        url_file = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(f["title"].replace(" ", "_")) + "?width=1280"
        url_src, lic, aut = m["page"], m["lic"], m["artist"]
        lat, lon, az = m["lat"], m["lon"], "UNVERIFIED"
        note = ("czas z EXIF/nazwy pliku przyjęty jako czas lokalny Europe/Warsaw (założenie); miniatura 1280 px; "
                + ("CC BY-SA = referencja, nie tekstura; " if "SA" in lic else ""))
        if not lat:
            note += "brak współrzędnych w metadanych Commons; "
    else:
        t = datetime.fromisoformat(f["dt"])
        pid = f["pid"]
        url_file = f"https://panoramax.openstreetmap.fr/derivates/{pid[0:2]}/{pid[2:4]}/{pid[4:6]}/{pid[6:8]}/{pid[9:]}/sd.jpg"
        url_src = f"https://api.panoramax.xyz/api/collections/{f['coll']}/items/{pid}"
        lic, aut = "CC BY-SA 4.0", f["autor"] + " (Panoramax)"
        lat, lon, az = f"{f['lat']:.6f}", f"{f['lon']:.6f}", f["az"]
        note = "czas i azymut z API Panoramax (datetimetz, view:azimuth); pochodna SD 2048 px; CC BY-SA = referencja, nie tekstura; "
    hg, ha, saz, _, _ = ts.sun(t)
    u = (t.astimezone(timezone.utc) + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)
    o = ti.obs_at(u.year, u.month, u.day, u.hour) if u.year in ti.HOURLY_YEARS else None
    if o is None:
        note += "brak danych terminowych IMGW dla tej daty w pobranym zakresie (2014–2023); "
    else:
        note += f"obserwacja IMGW z terminu {u:%Y-%m-%d %H} UTC (stacja lotniskowa Białystok, nie miejsce zdjęcia); "
    add(kategoria="kadr", przedmiot=f"niebo/horyzont — {f['warunki']}", **{"wartość": ""}, jednostka="",
        status="SOURCED", metoda="pobrano, zmniejszono do 960 px, obejrzano narzędziem Read; wysokość słońca: tools_sun (NOAA) dla 53.13N 23.16E",
        cytat=(f["title"] if f["src"] == "commons" else f"Panoramax item {f['pid']}"),
        **{"url_źródła": url_src}, url_pliku=url_file, licencja=lic, autor=aut, sha256=h, lat=lat, lon=lon, kierunek_deg=az,
        opis_co_widać=f["opis"], duplikat_sha256=seen_sha.get(h, ""), uwagi=note.strip(), plik_lokalny=f"img/{f['k']}.jpg",
        data_czas_lokalny=t.strftime("%Y-%m-%d %H:%M:%S %Z"),
        **{"wys_słońca_deg": f"{(ha if hg > -0.833 else hg):.1f}", "az_słońca_deg": f"{saz:.0f}",
           "imgw_N_okt": o["N_okt"] if o else "", "imgw_wid_m": o["wid_m"] if o else "", "imgw_ww": o["ww"] if o else "",
           "imgw_chmury_niskie": o["CL_txt"] if o else "", "pas_ciepły_przy_horyzoncie": f["pas"]})
    seen_sha.setdefault(h, rows[-1]["id"])

# ---------- F. literatura ----------
WMO_URL = "https://old.wmo.int/extranet/pages/prog/www/IMOP/publications/CIMO-Guide/Prelim_2018_ed/8_I_9_en_MR_tc.pdf"
WMO_SHA = sha(HERE / "files" / "lit" / "wmo_cimo_8_I_9_prelim2018.pdf")
WMO_KW = dict(**{"url_źródła": WMO_URL}, url_pliku=WMO_URL, sha256=WMO_SHA, plik_lokalny="lit/wmo_cimo_8_I_9_prelim2018.pdf",
              licencja="dokument publiczny WMO (wersja wstępna 2018 rozdz. 9 WMO-No. 8, z naniesionymi zmianami)", autor="WMO",
              kategoria="literatura_widzialność")
add(przedmiot="definicja MOR (meteorological optical range): próg transmisji", **{"wartość": "0.05"}, jednostka="-",
    status="SOURCED", metoda="odczyt z PDF (s. 1 pliku)",
    cytat="The meteorological optical range is the length of path in the atmosphere required to reduce the luminous flux in a collimated beam "
          "from an incandescent lamp, at a colour temperature of 2 700 K, to 5 %", **WMO_KW)
add(przedmiot="próg kontrastu Koschmiedera", **{"wartość": "0.02"}, jednostka="-", status="SOURCED", metoda="odczyt z PDF (s. 3 pliku)",
    cytat="In 1924, Koschmieder, followed by Helmholtz, proposed a value of 0.02 for ε.", **WMO_KW)
add(przedmiot="zależność MOR od współczynnika ekstynkcji: P = (1/σ)·ln(1/0,05) ≈ 3/σ", **{"wartość": "2.996"}, jednostka="-",
    status="SOURCED", metoda="odczyt z PDF (s. 5 pliku, równ. 9.6 i zdanie przy równ. 9.13); 2,996 = ln 20 (obliczone)",
    cytat="Noting that P = (1/σ) · ln (1/0.05) in equation 9.6", **WMO_KW,
    uwagi="dla progu 0,02 (Koschmieder): V = ln(50)/σ = 3,912/σ — tak liczy gra (ADR 0010)")
add(przedmiot="czarny obiekt na tle horyzontu o kontraście pozornym 0,05 jest w odległości MOR", **{"wartość": "0.05"}, jednostka="-",
    status="SOURCED", metoda="odczyt z PDF (s. 6 pliku)",
    cytat="when the magnitude of the apparent contrast of a black object, seen against the horizon, is 0.05, that object is at MOR (P)", **WMO_KW)
add(przedmiot="zgodność wizualnej oceny widzialności w dzień z MOR", **{"wartość": "0.05"}, jednostka="-", status="SOURCED",
    metoda="odczyt z PDF (s. 10 pliku)",
    cytat="Visibility and MOR should be equal if the observer’s contrast threshold is 0.05 (using the criterion of recognition)", **WMO_KW,
    uwagi="podstawa przyjęcia σ = 2,996/V dla widzialności IMGW (pole WIDO)")
CIE_URL = "https://cie.co.at/node/4086"
CIE_KW = dict(kategoria="literatura_CIE", **{"url_źródła": CIE_URL}, licencja="strona wydawcy (opis normy); sama norma płatna — nie pobrano",
              autor="CIE")
add(przedmiot="ISO 15469:2004(E) / CIE S 011/E:2003 — zakres normy (zestaw rozkładów luminancji nieba)", **{"wartość": ""},
    status="SOURCED", metoda="odczyt strony CIE",
    cytat="This standard lists a set of luminance distributions, which model the sky under a wide range of conditions, from the heavily "
          "overcast sky to cloudless weather.", **CIE_KW)
add(przedmiot="CIE general sky: luminancja względna jako funkcja luminancji zenitu", **{"wartość": ""}, status="SOURCED",
    metoda="odczyt strony CIE",
    cytat="This Standard defines relative luminance distributions: the luminance of the sky at any point is given as a function of the "
          "zenith luminance.", **CIE_KW)
add(przedmiot="CIE Standard Overcast Sky zachowane jako osobny wzór", **{"wartość": ""}, status="SOURCED", metoda="odczyt strony CIE",
    cytat="The Overcast Sky is retained as a separate formula because there are many calculation procedures that embody the mathematical "
          "formulation of this particular distribution.", **CIE_KW,
    uwagi="wzór Moona–Spencer L(γ) = Lz·(1 + 2 sin γ)/3 jest już w repo (ADR 0010, „CIE standard overcast sky L(θ) = Lz (1 + 2 cos θ)/3”); "
          "samej pracy Moon & Spencer 1942 (Illum. Eng. 37, 707) nie otwarto — brak DOI, UNVERIFIED")
RC_URL = "https://github.com/GastonMauroDiaz/rcaiman/blob/c2124fbd47698c00f9f45936a5facf002dd8a5f8/R/data.R"
RC_FILE = "https://raw.githubusercontent.com/GastonMauroDiaz/rcaiman/c2124fbd47698c00f9f45936a5facf002dd8a5f8/data/cie_table.rda"
RC_SHA = sha(HERE / "files" / "lit" / "cie_table.rda")
RC_KW = dict(kategoria="literatura_CIE", **{"url_źródła": RC_URL}, url_pliku=RC_FILE, sha256=RC_SHA, plik_lokalny="lit/cie_table.rda",
             licencja="GPL-3 (pakiet R rcaiman; tabela wg ISO 15469:2004/CIE S 011:2003, źródło pakietu: Li i in. 2016, doi:10.1016/j.energy.2016.02.054)",
             autor="G. M. Díaz (rcaiman)")
add(przedmiot="CIE general sky — funkcja gradacji φ(Z) i indykatrysa f(χ)", **{"wartość": "φ(Z) = 1 + a·exp(b/cos Z); f(χ) = 1 + c·[exp(dχ) − exp(dπ/2)] + e·cos²χ"},
    status="SOURCED", metoda="odczyt dokumentacji pakietu (R/data.R)",
    cytat="\\Phi(\\theta) = 1 + a \\cdot \\exp\\left(\\frac{b}{\\cos\\theta}\\right)", **RC_KW,
    uwagi="źródło wtórne (otwarte); norma ISO/CIE płatna")
CIE15 = [(1, 4.0, -0.7, 0, -1.0, 0.0, "Overcast", "Steep gradation, azimuthal uniformity"),
         (2, 4.0, -0.7, 2, -1.5, 0.15, "Overcast", "Steep gradation, slight brighten around sun"),
         (3, 1.1, -0.8, 0, -1.0, 0.0, "Overcast", "Gentle gradation, azimuthal uniformity"),
         (4, 1.1, -0.8, 2, -1.5, 0.15, "Overcast", "Gentle gradation, slight brighten around sun"),
         (5, 0.0, -1.0, 0, -1.0, 0.0, "Overcast", "Uniform")]
for n, a, b, c, d, e, g, desc in CIE15:
    add(przedmiot=f"CIE general sky typ {n}: parametry a, b, c, d, e", **{"wartość": f"a={a}; b={b}; c={c}; d={d}; e={e}"}, jednostka="-",
        status="SOURCED", metoda="odczyt tabeli cie_table.rda (pakiet rdata w Pythonie)",
        cytat=f"{n},{a},{b},{c},{d},{e},{g},\"{desc}\"" if "," in desc else f"{n},{a},{b},{c},{d},{e},{g},{desc}", **RC_KW,
        uwagi="typy 1–5 = grupa „Overcast” (zachmurzenie całkowite); cytat = wiersz tabeli w zapisie CSV (kolumna indicatrix_group pominięta)")
    ratio = 1.0 / (1.0 + a * math.exp(b))
    g15 = (1.0 + a * math.exp(b / math.sin(math.radians(15)))) / (1.0 + a * math.exp(b))
    add(kategoria="literatura_CIE", przedmiot=f"CIE typ {n}: stosunek luminancji horyzont/zenit i (wys. 15°)/zenit — sama gradacja",
        **{"wartość": f"{ratio:.3f}; {g15:.3f}"}, jednostka="-", status="ESTIMATED",
        metoda="obliczone: φ(90°)/φ(0°) = 1/(1 + a·e^b) oraz φ(Z=75°)/φ(0°), z parametrów a, b poprzedniego wiersza (build_manifest.py)",
        **{"url_źródła": RC_URL},
        uwagi="typ 1: 0,335 ≈ 1/3 — zgodne z niebem pochmurnym CIE/Moona–Spencer (zenit 3× jaśniejszy od horyzontu)" if n == 1 else "")
OA = "https://api.openalex.org/works/https://doi.org/"
LIT = [
 ("10.1364/AO.44.005712", "Lee, Hernández-Andrés 2005, Colors of the daytime overcast sky, Appl. Opt. 44, 5712",
  "barwa światła pod zachmurzeniem całkowitym: niebieszczenie, nie ocieplenie",
  "Colorimetric analyses show that overcasts make daylight bluer and that the amount of bluing increases with cloud optical depth."),
 ("10.1364/AO.44.005712", "Lee, Hernández-Andrés 2005 (jw.)", "gama barw nieba pochmurnego: pastelowa",
  "Time-series measurements of daylight (skylight plus direct sunlight) spectra beneath overcast skies reveal an unexpectedly wide gamut of pastel colors."),
 ("10.1364/AO.47.00H106", "Lee 2008, Measuring overcast colors with all-sky imaging, Appl. Opt. 47, H106",
  "rozkład kątowy barw nieba pochmurnego — wzorce regularne, wymagają modelu z absorpcją i rozpraszaniem w chmurze i pod nią",
  "Histograms and azimuthally averaged curves of the resulting chromaticities show consistent, but unexpected, patterns in time-averaged overcast colors."),
 ("10.1364/JOSA.43.000113", "Hulburt 1953, Explanation of the Brightness and Color of the Sky, Particularly the Twilight Sky, JOSA 43, 113",
  "zenit o zmierzchu jest niebieski dzięki absorpcji ozonu (pasmo Chappuisa)",
  "with ozone the zenith sky is blue at sunset and throughout twilight (as is observed)"),
 ("10.1364/AO.56.00G179", "Lee, Mollner 2017, Tropospheric haze and colors of the clear twilight sky, Appl. Opt. 56, G179",
  "najżywsze barwy zmierzchu po stronie słońca wymagają aerozolu; dotyczy nieba BEZCHMURNEGO",
  "the most vivid solar-sky colors require at least some turbidity"),
 ("10.1364/AO.56.00G179", "Lee, Mollner 2017 (jw.)", "barwy zmierzchu cywilnego zależą od rozpraszania molekularnego, aerozolu i ozonu",
  "clear-sky colors during civil twilights depend on the combined spectral effects of molecular scattering, extinction by tropospheric aerosols, and absorption by ozone"),
 ("10.1364/AO.42.000445", "Lee, Hernández-Andrés 2003, Measuring and modeling twilight’s purple light, Appl. Opt. 42, 445",
  "pastelowe purpury po stronie słońca przy pogodnym zmierzchu („purple light”)",
  "During many clear twilights, much of the solar sky is dominated by pastel purples."),
 ("10.1364/AO.33.004629", "Lee 1994, Twilight and daytime colors of the clear sky, Appl. Opt. 33, 4629",
  "barwy pogodnego nieba dziennego leżą blisko krzywej ciała doskonale czarnego",
  "the observed colors of the clear daytime sky do lie near the blackbody locus"),
]
for doi, ref, what, quote in LIT:
    add(kategoria="literatura_barwa_nieba", przedmiot=what, **{"wartość": ""}, status="SOURCED",
        metoda="abstrakt publikacji pobrany z API OpenAlex (pełnego tekstu nie otwarto — za paywallem)", cytat=quote,
        **{"url_źródła": "https://doi.org/" + doi}, url_pliku=OA + doi, licencja="abstrakt (metadane OpenAlex CC0); artykuł — prawa wydawcy, nie pobrano",
        autor=ref)
add(kategoria="licencja", przedmiot="warunki wykorzystania danych IMGW-PIB — obowiązek wskazania źródła", **{"wartość": ""}, status="SOURCED",
    metoda="odczyt regulaminu (§5 ust. 3)",
    cytat="„Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy”",
    **{"url_źródła": "https://danepubliczne.imgw.pl/regulations"}, licencja=IMGW_LIC, autor=IMGW_AUT)
add(kategoria="licencja", przedmiot="warunki wykorzystania danych IMGW-PIB — informacja o przetworzeniu", **{"wartość": ""}, status="SOURCED",
    metoda="odczyt regulaminu (§5 ust. 4)",
    cytat="„Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone”",
    **{"url_źródła": "https://danepubliczne.imgw.pl/regulations"}, licencja=IMGW_LIC, autor=IMGW_AUT)
add(kategoria="licencja", przedmiot="warunki wykorzystania danych IMGW-PIB — cel użycia", **{"wartość": ""}, status="SOURCED",
    metoda="odczyt regulaminu (§5 ust. 1)",
    cytat="Korzystający może używać nieodpłatnie udostępnionych danych do celów prywatnych, a w przypadku danych o wysokiej wartości w każdym celu.",
    **{"url_źródła": "https://danepubliczne.imgw.pl/regulations"}, licencja=IMGW_LIC, autor=IMGW_AUT,
    uwagi="czy archiwalne dane synoptyczne są „danymi o wysokiej wartości” (rozp. wyk. KE 2023/138, kategoria meteorologiczna) — UNVERIFIED, "
          "do potwierdzenia przez właściciela przed użyciem liczb w produkcie komercyjnym; w grze trafiają tylko parametry pochodne")

# ---------- G. rekomendacje dla gry (WORKING_VALUE / ESTIMATED) ----------
def hvrow(m):
    return next(r for r in hv if r["miesiac"] == m)


def sigma(v):
    return math.log(20) / float(v)


for label, m, col in (("pogodny dzień letni (V–VIII, N ≤ 2)", "V-VIII", "wid_mediana_przy_N<=2_m"),
                      ("pochmurny dzień letni (V–VIII, N ≥ 7)", "V-VIII", "wid_mediana_przy_N>=7_m"),
                      ("pogodny dzień zimowy (XI–II, N ≤ 2)", "XI-II", "wid_mediana_przy_N<=2_m"),
                      ("pochmurny dzień zimowy (XI–II, N ≥ 7)", "XI-II", "wid_mediana_przy_N>=7_m"),
                      ("zamglony dzień zimowy (XI–II, percentyl 10 widzialności)", "XI-II", "wid_dzien_p10_m"),
                      ("pochmurny dzień — cały rok (N ≥ 7)", "rok", "wid_mediana_przy_N>=7_m")):
    v = float(hvrow(m)[col])
    s = sigma(v)
    add(kategoria="rekomendacja_mgła", przedmiot=f"gęstość mgły wykładniczej σ — {label}", **{"wartość": f"{s:.2e}"}, jednostka="1/m",
        status="ESTIMATED",
        metoda=f"σ = ln(1/0,05)/V = 2,996/V (WMO, MOR), V = {v:.0f} m z out/imgw_hourly_visibility_cloud.csv ({col}, {m})",
        **{"url_źródła": IMGW_DIR + "terminowe/synop/"}, licencja=IMGW_LIC, autor=IMGW_AUT,
        uwagi=f"parametr „visibility” gry przy wzorze 3,912/V (ADR 0010) dający tę samą σ: {v * math.log(50) / math.log(20):.0f} m; "
              f"udział barwy horyzontu 1−exp(−σd): 100 m {100 * (1 - math.exp(-s * 100)):.1f} %, 500 m {100 * (1 - math.exp(-s * 500)):.1f} %, "
              f"1000 m {100 * (1 - math.exp(-s * 1000)):.1f} %")
REK = [
 ("rekomendacja_niebo", "niebo pochmurne (LP_Overcast): barwa przy horyzoncie", "neutralna szarość do lekko niebieskawej; bez ciepłego pasa na żadnej wysokości słońca ≥ 0°", "",
  "WORKING_VALUE", "wniosek z 15 obejrzanych kadrów z N = 8 wg stacji (0 z ciepłym pasem; w tym 4 ze słońcem 1–4° nad horyzontem: c07, c08, c09, c25) i 2 kadrów Panoramax z XI 2026 (zachmurzenie całkowite, bez danych stacji); przy N = 7 i słońcu 1–4° (c17, c31) tylko ledwo widoczny kremowy odcień; literatura: Lee & Hernández-Andrés 2005"),
 ("rekomendacja_niebo", "niebo pochmurne: rozkład luminancji dla St neb / mgły", "CIE typ 5 (jednolite) do typu 3 (horyzont/zenit 0,67)", "",
  "WORKING_VALUE", "kadry St neb i mgły pokazują jednolitą płaszczyznę bez gradientu w zakresie kadru; typ 1 (1:3) zostawić dla grubej warstwy Ns/Sc bez mgły — do sprawdzenia na zdjęciu typu rybie oko (luka)"),
 ("rekomendacja_niebo", "zmierzch przy zachmurzeniu całkowitym: barwa nieba", "jednolity niebieskoszary → granat; bez pasa pomarańczowego/koralowego", "",
  "WORKING_VALUE", "kadry c04, c13, c14, c30, pnx_c1a5e40e (N = 8 lub brak danych, słońce −2…−10°): żaden nie ma ciepłego pasa"),
 ("rekomendacja_niebo", "zmierzch pogodny: ciepły pas tylko w sektorze słońca", "pastelowy brzoskwiniowy/łososiowy, nad szarofioletową warstwą przy samym horyzoncie; poza sektorem słońca błękit lub różowo-liliowy pas przeciwsłoneczny", "",
  "WORKING_VALUE", "kadry c32 (lato, w stronę słońca), c16 (zachód, N=6), c21 (pastelowy róż), c22/c23 (N=0, słońce −7°: brak ciepłego pasa w kadrze); kierunki kadrów Commons UNVERIFIED"),
 ("rekomendacja_niebo", "udział wieczorów bez barwnego zmierzchu (N ≥ 7 przy końcu zmierzchu cywilnego) XI–I", "79–82", "%",
  "ESTIMATED", "out/imgw_sunset_cloud.csv (koniec_zm_cyw, miesiące 11, 12, 1)"),
 ("rekomendacja_niebo", "udział wieczorów pogodnych (N ≤ 2 przy końcu zmierzchu cywilnego) VI–VIII", "29–38", "%",
  "ESTIMATED", "out/imgw_sunset_cloud.csv (koniec_zm_cyw, miesiące 6, 7, 8)"),
 ("rekomendacja_niebo", "hipoteza przyczyny „koralowego pasa”: barwa mgły = średnia radiancji nieba z 32 azymutów na wys. ok. 2,9° (SkyModel.HorizonColorExposed), więc o zmierzchu ciepły sektor słońca barwi mgłę we WSZYSTKICH kierunkach", "barwę mgły o zmierzchu liczyć bez sektora słońca (np. ±60° azymutu) albo kierunkowo; warstwa zamglenia przy horyzoncie ma być szarofioletowa/niebieskoszara", "",
  "WORKING_VALUE", "kod: game/Assets/_Project/Rendering/Runtime/Sky/SkyModel.cs:251–261 i EnvironmentLighting.cs:136 (przeczytane, nie zmieniane, nie uruchamiane); zdjęcia: c32 (szarofioletowa warstwa przy horyzoncie pod łososiowym pasem), c13/c14/c04 (brak ciepłej barwy przy N = 8); do potwierdzenia renderem — nie sprawdzono w Unity"),
 ("rekomendacja_słońce", "azymut słońca przy końcu zmierzchu cywilnego: LP_Dusk ma 300° — odpowiada dacie", "21 IV / 21 VIII (299°)", "",
  "ESTIMATED", "out/sun_table.csv: az_konca_zm_cywilnego 299,3° (21 IV) i 299,1° (21 VIII); XI–I: 238–245°; VI: 324°"),
 ("rekomendacja_słońce", "LP_Clear (słońce 42°, az. 200°) odpowiada dacie i godzinie", "6–7 IV oraz 4–6 IX, ok. 13:24–13:30 CEST", "",
  "ESTIMATED", "przeszukanie tools_sun.sun() co 2 min dla roku 2026: |wys. − 42°| < 0,4° i |az. − 200°| < 0,8° (tools_checks.py → out/checks.csv)"),
 ("rekomendacja_mgła", "mgiełka przy gruncie z ADR 0080 (odpowiednik widzialności ok. 2,4 km): udział terminów dziennych z widzialnością < 2400 m — XI–II / V–VIII / rok", "11.6 / 0.2 / 4.4", "%",
  "ESTIMATED", "dane terminowe 2014–2023, terminy 06–15 UTC, pole WIDO (tools_checks.py → out/checks.csv)"),
]
for kat, what, val, unit, st, met in REK:
    add(kategoria=kat, przedmiot=what, **{"wartość": val}, jednostka=unit, status=st, metoda=met)

with open(HERE / "manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r["kategoria"] for r in rows), Counter(r["status"] for r in rows))
