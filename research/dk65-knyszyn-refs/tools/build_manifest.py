"""Build manifest.csv (K1) from measured/observed data. Observations (cross-sections, photo descriptions) are entered
by hand after viewing the ortho crops / photos (see README); this script only assembles rows and computes derived numbers."""
import csv, json, math, os, sys, hashlib
from pyproj import Transformer
K1 = '/tmp/claude-0/-workspace-kamion/f4a38e02-1bbc-5042-8a92-a3868938a174/scratchpad/k1/'
OUT = '/workspace/kamion/.claude/worktrees/agent-ab851075007c7ffbb/research/dk65-knyszyn-refs/'
ACC = '2026-11-15'
fw = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True); bw = Transformer.from_crs('EPSG:2180', 'EPSG:4326', always_xy=True)
pts = {f"km{p['km']:05.2f}": p for p in json.load(open(K1 + 'km_points.json'))}
om = json.load(open(K1 + 'orto/meta.json')); oj = json.load(open(K1 + 'orto_j/meta.json'))
oj.update(json.load(open(K1 + 'orto_r/meta.json'))); oj.update(json.load(open(K1 + 'orto_f/meta.json')))
pm = json.load(open(K1 + 'ph/photos_meta.json'))
WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
ORTO_LIC = "GUGiK ortofotomapa — dane udostępniane bez opłat (art. 40a ust. 2 pkt 1 Prawa geodezyjnego i kartograficznego); wycinek jako dowód pomiaru"
cols = ["id", "kafel", "temat", "element", "parametr", "wartość", "jednostka", "lat", "lon", "osm_id", "kierunek_deg", "data_zdjęcia", "sezon", "pora_dnia", "opis_co_widać",
        "url_źródła", "url_pliku", "plik_lokalny", "sha256", "licencja", "autor", "data_dostępu", "status", "uwagi"]
rows = []
def sha(p): return hashlib.sha256(open(OUT + p, 'rb').read()).hexdigest() if p and os.path.exists(OUT + p) else ""
def add(**k):
    r = {c: "" for c in cols}; r.update({c: ("" if v is None else v) for c, v in k.items()}); r["data_dostępu"] = r["data_dostępu"] or ACC
    if r["plik_lokalny"] and not r["sha256"]: r["sha256"] = sha(r["plik_lokalny"])
    rows.append(r)
def dk65km(route_km):  # OSM milestones ref=65: distance 161 at route km 9.05 ... 143 at 27.10 (data/osm_corridor.json)
    return round(170.05 - route_km, 2)

# ---------- (a) cross-sections every ~1 km: values read from orto rot/zoom crops + profile peaks (data/analysis.json)
# (km, L line, centre, R line, asphalt L edge, asphalt R edge, edge-line type, centre-line type, shoulders/side, extras)
X = [
 (8.80, -3.2, 0.0, 3.1, -4.5, 3.4, "ciągłe obie; przerywane na odcinku zjazdu P", "przerywana; w dolnej części kadru obok niej druga linia ciągła (typ UNVERIFIED)", "pobocze żwirowe ~1 m L; utwardzony zjazd do posesji P", "drzewa L 8–12 m od krawędzi"),
 (9.00, -3.3, -0.2, 2.9, -4.5, 3.9, "ciągłe obie", "przerywana", "pobocza żwirowo-trawiaste ~0,6–1 m", "betonowe dojście/zjazd P; linia kolejowa 38 ~111 m na L (OSM)"),
 (10.00, -3.4, -0.2, 3.0, -4.8, 3.6, "L ciągła; P przerywana (krótkie kreski)", "przerywana", "pobocze żwirowe P ~1,2 m, L ~0,8 m", "kolej 38 ~150 m na L"),
 (11.00, -3.3, -0.3, 3.0, -4.6, 3.75, "ciągłe obie", "ciągła pojedyncza", "pobocza trawiaste; zadrzewienie gęste L", "OSM embankment=yes (km 10,94–11,08), za mostem na Supraśli"),
 (11.50, -3.4, -0.3, 2.7, -4.7, 3.1, "przerywane obie (krótkie kreski)", "przerywana", "żwir ~0,8 m L, ~1 m P", "szpaler drzew po L (orto 200 m)"),
 (12.00, -3.4, -0.5, 2.7, -4.9, 4.1, "L: linia nieczytelna na krawędzi asfaltu (AUDYT: poprawka — wartość L z krawędzi, UNVERIFIED); P przerywana", "przerywana", "żwir/trawa", "pojedyncze drzewo P przy krawędzi"),
 (12.50, -3.4, -0.25, 2.8, -4.5, 4.0, "przerywane obie (AUDYT: poprawka L z ciągłej na przerywaną)", "przerywana", "trawa", "wlot drogi bocznej L z utwardzonym poszerzeniem"),
 (13.00, -3.5, -0.5, 2.75, None, 4.4, "L przerywana wzdłuż zatoki; P ciągła", "przerywana", "zatoka autobusowa L z wiatą (orto), poszerzenie ~4 m", "OSM: przystanek Dobrzyniewo Duże km 12,99 L (node 14067837805)"),
 (13.50, -3.1, 0.1, 3.3, -4.0, 3.5, "ciągłe obie", "przerywana", "pobocze żwirowe; zjazd gruntowy P", "las/zadrzewienie L"),
 (14.00, -3.2, 0.0, 3.0, -3.6, 3.4, "ciągłe obie", "ciągła na wysokości wlotu (UNVERIFIED czy pojedyncza)", "trawa", "wlot betonowy L; drzewa obie strony"),
 (14.50, -3.2, -0.3, 3.0, None, None, "L ciągła; P przerywana wzdłuż poszerzenia", "ciągła", "poszerzenie/zatoka P ~3 m", "OSM: przystanek km 14,48 P (node 11243685568)"),
 (15.00, -3.2, -0.2, 3.0, -4.7, 4.4, "ciągłe obie", "ciągła", "pobocza trawiaste", "drzewa P"),
 (15.50, -2.5, 0.6, 3.6, None, None, "L ciągła; P przerywana przy wlocie", "przerywana", "—", "wlot drogi bocznej P"),
 (16.00, -3.0, 0.1, 3.2, -4.1, 3.6, "ciągłe obie", "ciągła", "rów L; równoległe cienkie linie na −5,2 i +5,9 m (bariera lub ogrodzenie — UNVERIFIED)", "Studzienna, przed rondem S19"),
 (17.00, -3.5, -0.1, 2.6, -4.4, None, "ciągłe obie", "UNVERIFIED (cień drzew)", "pas trawy/żwiru L", "las P"),
 (18.00, -2.9, 0.1, 3.1, -4.2, 4.4, "przerywane obie (krótkie kreski)", "przerywana (długie kreski)", "pobocza żwirowe", "las P"),
 (19.00, -3.4, -0.2, 3.0, None, None, "L ciągła; P przerywana wzdłuż zatoki", "ciągła", "zatoka autobusowa P z peronem i żółtą barierką (orto)", "OSM platforma km 19,03 P (node 14067837823)"),
 (20.00, -2.25, 0.5, 3.75, None, None, "przerywane obie", "przerywana", "pobocza trawiaste", "pozycje z obrazu (pik zakłócony przez ciężarówkę); oś OSM przesunięta ~0,75 m"),
 (21.00, -3.25, 0.0, 3.0, -4.0, 3.4, "ciągłe obie", "przerywana (długie kreski)", "bariery stalowe obie strony ~±4,5–4,8 m od osi", "przepust/przejście pod drogą — wloty widoczne po obu stronach"),
 (21.65, -3.5, -0.2, 2.6, -4.8, 3.6, "przerywane obie", "przerywana", "pobocza żwirowe ~1 m", "las P, zarośla L"),
 (22.00, -3.7, -0.6, 2.4, -4.6, 3.4, "przerywane obie", "przerywana", "pobocza żwirowe", "las P"),
 (23.00, -3.2, -0.1, 3.0, -4.0, 3.8, "ciągłe obie", "przerywana, obok odcinkami druga linia (typ UNVERIFIED)", "pobocza trawiaste", "las obie strony"),
 (24.00, -3.2, -0.2, 2.9, -4.1, 3.6, "ciągłe obie", "przerywana", "pas żwiru L; pole P", "—"),
 (24.60, -3.3, -0.2, 2.7, -4.5, 4.4, "ciągłe obie", "przerywana (długie kreski)", "plac/teren piaszczysty P (budowa?)", "—"),
 (25.00, -3.8, -0.8, 2.3, -4.8, 5.3, "L ciągła; P przerywana wzdłuż zatoki", "ciągła", "zatoka autobusowa P", "zgodne z ADR 0212 Otwarte p.1 (762500, 609950)"),
 (26.00, -3.7, -0.3, 3.1, -4.7, 3.4, "ciągłe obie", "przerywana", "pobocza trawiaste, krzewy", "Obozowa; zgodne z ADR 0212 (6,8 m linia–linia)"),
 (27.00, -3.7, -0.3, 3.1, -4.4, 3.5, "ciągłe obie", "przerywana", "bariery stalowe obie strony (słupki ~±5,4 m)", "dojazd do mostu km 26,96–26,98 (OSM way 286990128)"),
]
for (km, L, C, Rr, aL, aR, et, ct, sh, ex) in X:
    pid = f"km{km:05.2f}"; p = pts[pid]; m = om[pid]; sheet = m["sheets"][-1]
    ll = round(Rr - L, 2); ln = f"L {L:+.2f} / C {C:+.2f} / P {Rr:+.2f} m od osi OSM"
    asp = f"asfalt {aL:+.1f}…{aR:+.1f} m → ~{aR - aL:.1f} m" if (aL is not None and aR is not None) else "krawędź asfaltu nieczytelna (zatoka/wlot/cień)"
    lanes = f"pas L {abs(C - L):.1f} m, pas P {abs(Rr - C):.1f} m (oś linii–oś linii)"
    add(id="", kafel=p["tile"], temat="a", element=f"DK65 trasa A km {km:.2f} (DK65 km ~{dk65km(km)})", parametr="rozstaw linii krawędziowych (oś–oś)",
        wartość=f"{ll:.1f}", jednostka="m", lat=p["lat"], lon=p["lon"], osm_id=f"way/{p['way']}", kierunek_deg="",
        opis_co_widać=f"Ortofoto z góry, wycinek 40×40 m obrócony wzdłuż drogi. {ln}; {lanes}; {asp}. Linie krawędziowe: {et}. Oś: {ct}. Pobocza/otoczenie: {sh}. {ex}.",
        url_źródła=m["wms_url"], url_pliku=sheet[3] or "", plik_lokalny=f"files/orto/km/{pid}_rot.jpg", licencja=ORTO_LIC, autor="GUGiK (Geoportal)",
        status=("UNVERIFIED" if km == 12.00 else "ESTIMATED"), data_zdjęcia=sheet[0], sezon="wiosna", pora_dnia="dzień",
        uwagi=f"Metoda: profil jasności poprzecznie do osi (mediana z 30 m wzdłuż), piki = linie, skoki = krawędź asfaltu; arkusz {sheet[2]} {sheet[0]} piksel {sheet[1]} m; dokładność ±0,2 m (linie), ±0,4 m (asfalt). Zoom 2×: files/orto/km/zoom_*.jpg. OSM: {p['highway']} lanes={p['lanes']} maxspeed={p['maxspeed'] or '—'}")

# km 16.70 / 28.00 special
p = pts["km16.70"]; m = om["km16.70"]; s = m["sheets"][-1]
add(kafel=p["tile"], temat="a", element="DK65 km 16,70 — rondo S19/DK65 (OSM)", parametr="przekrój", wartość="nie mierzono", lat=p["lat"], lon=p["lon"], osm_id="way/1151531611",
    opis_co_widać="Ortofoto 2025-05-25: DK65 prosta 2×1 bez ronda, po NE roboty ziemne (piasek, ślady maszyn) korytarza S19; w OSM (2026-10-19) rondo — stan po ortofoto.",
    url_źródła=m["wms_url"], url_pliku=s[3], plik_lokalny="files/orto/junctions/J_rondo_km16_66_north.jpg", licencja=ORTO_LIC, autor="GUGiK (Geoportal)", status="ESTIMATED",
    data_zdjęcia=s[0], sezon="wiosna", pora_dnia="dzień", uwagi="patrz temat b, wiersz ronda km 16,66")
p = pts["km28.00"]; m = om["km28.00"]; s = m["sheets"][-1]
add(kafel="knyszyn", temat="a", element="DW671 Tykocka km 28,00 (w mieście, poza DK65)", parametr="szerokość jezdni między krawężnikami", wartość="~10", jednostka="m", lat=p["lat"], lon=p["lon"], osm_id="way/47812348",
    opis_co_widać="Brak linii krawędziowych; oś przerywana; jezdnia od −5,7 do ~+4,3 m od osi OSM; po P latarnia na słupie z wysięgnikiem (cień), chodniki i zabudowa jednorodzinna obie strony.",
    url_źródła=m["wms_url"], url_pliku=s[3], plik_lokalny="files/orto/km/km28.00_rot.jpg", licencja=ORTO_LIC, autor="GUGiK (Geoportal)", status="ESTIMATED", data_zdjęcia=s[0], sezon="wiosna", pora_dnia="dzień",
    uwagi="±0,5 m; może obejmować pas postojowy (UNVERIFIED)")

# OSM tags (no width/shoulder tags on any way)
ow = json.load(open(K1 + 'osm_route_ways.json'))
groups = {}
for w in ow:
    t = w["tags"]; key = (t.get("highway"), t.get("ref", ""), t.get("name", ""), t.get("lanes", ""), t.get("maxspeed", ""))
    groups.setdefault(key, []).append(w)
for (hw, ref, name, lanes, ms), ws in groups.items():
    if ws[0]["km_end"] < 8.7: continue
    kmin = min(w["km_start"] for w in ws); kmax = max(w["km_end"] for w in ws)
    add(kafel="", temat="a", element=f"OSM {hw} {('ref='+ref) if ref else ''} {name}".strip(), parametr="lanes / maxspeed / surface (width, shoulder: brak tagów)",
        wartość=f"lanes={lanes or '—'}; maxspeed={ms or '—'}; surface={ws[0]['tags'].get('surface','—')}", osm_id=";".join(f"way/{w['way_id']}" for w in ws),
        opis_co_widać=f"Tagi OSM odcinków trasy km {kmin:.2f}–{kmax:.2f}; ostatnie edycje {', '.join(sorted({w.get('osm_timestamp','')[:10] for w in ws}))}. Brak tagów width/shoulder/lit/lane_markings.",
        url_źródła="https://api.openstreetmap.org/api/0.6/ways?ways=" + ",".join(str(w["way_id"]) for w in ws[:20]), licencja="ODbL (© OpenStreetMap contributors)", autor="OpenStreetMap", status="SOURCED",
        uwagi="data/osm_route_ways.json")

# ---------- per tile photo coverage gaps (Panoramax + Commons)
ql = json.load(open(OUT + 'data/query_log.json'))
for t in ["dk65-01", "dk65-02", "dk65-03", "dk65-04", "dk65-05", "dk65-06", "dk65-07", "dk65-08", "dk65-09", "dk65-10", "dk65-11", "knyszyn-s", "knyszyn", "knyszyn-w"]:
    pn = ql["panoramax"]["tiles"][t]; cg = ql["commons_geosearch_tiles"]["tiles"][t]
    npx = pn["api.panoramax.xyz"]["n"]
    add(kafel=t, temat="a", element="pokrycie zdjęciami ulicznymi kafla", parametr="Panoramax (api.panoramax.xyz) / Commons geosearch r=1450 m", wartość=f"{npx} / {cg['n']}", jednostka="szt.",
        opis_co_widać=("Panoramax: 9 zdjęć z 2019 przy płd. krawędzi kafla (lat 53,154) — ~1,7 km od trasy, nie na DK65. " if t == "dk65-01" and npx else "Panoramax: brak zdjęć w bbox kafla. ") +
        "Commons: kadry na trasie wymienione w wierszach zdjęć (temat a/f/g); pozostałe trafienia = bociany, maszt RTCN, kapliczki, cmentarze — nie pokazują DK65.",
        url_źródła=pn["api.panoramax.xyz"]["url"], licencja="", autor="", status="SOURCED", uwagi="luka pokrycia; zapytania w data/query_log.json (osm.fr, ign.fr też 0)")

# ---------- photos (descriptions written after viewing files/photos/*.jpg; direction from content only)
PH = {
 "K1-P01": ("knyszyn", "f", "Rynek — park", "Aleja parkowa o nawierzchni gruntowo-żwirowej, po bokach trawniki z niskimi obrzeżami betonowymi i wysokie drzewa liściaste (gatunek UNVERIFIED); w głębi ławki i niska zabudowa. Pełne lato, słońce.", "lato", "dzień", ""),
 "K1-P02": ("knyszyn", "f", "pierzeja Rynku (Rynek 1 wg tytułu)", "Dom 2-kondygnacyjny z poddaszem: parter i piętro w tynku szaro-brązowym, obok część kremowa; dach dwuspadowy szary; napis firmowy kwiaciarni (nie odtwarzamy); przed nim przejście dla pieszych i chodnik z płyt.", "lato", "dzień", "lokalizacja z tytułu pliku, brak współrzędnych"),
 "K1-P03": ("knyszyn", "f", "tabliczka adresowa Rynek 4", "Tabliczka: górna część czerwona z białą cyfrą 4, dolny pas żółto-biały z napisem RYNEK i herbem; na szarych deskach elewacji drewnianej.", "lato", "dzień", "detal do tekstur/oznaczeń"),
 "K1-P04": ("knyszyn", "f", "róg Grodzieńska/Rynek — tabliczki ulic", "Białe tabliczki z czarnym napisem i herbem (ul. Grodzieńska, Rynek) na szarym słupku; w tle dach z czerwonej blachodachówki, balkon z kwiatami; reklama piwa (marka — nie odtwarzamy).", "lato", "dzień", ""),
 "K1-P05": ("knyszyn", "f", "ul. Grodzieńska — stara tabliczka", "Niebieska emaliowana tabliczka z białym napisem UL. GRODZIEŃSKA na białym tynku.", "lato", "dzień", ""),
 "K1-P06": ("knyszyn", "f", "ul. Grodzieńska (DW671) — widok wzdłuż", "Jezdnia asfaltowa bez linii, chodnik P z czerwono-brązowej kostki, parterowe domy drewniane i murowane, słupy betonowe z linią napowietrzną i oprawami na wysięgnikach; drzewa liściaste.", "lato", "dzień", "typ opraw UNVERIFIED (2012)"),
 "K1-P07": ("knyszyn", "f", "Urząd Miasta przy Rynku", "Budynek 2-kondygnacyjny z poddaszem i rzędem lukarn, dach czerwony; elewacja kremowo-biała, żółte obramienia okien, portyk z żółtymi kolumnami; asfaltowy plac/parking przed wejściem, chodnik z kostki.", "lato", "dzień", "zgodny z dużym budynkiem o czerwonym dachu na N od Rynku (orto J_rynek_W)"),
 "K1-P08": ("knyszyn", "f", "Rynek — pomnik Zygmunta Augusta i zegar słoneczny", "Brązowa figura stojąca na granitowym cokole, przed nią granitowy blok z tablicą (zegar słoneczny); posadzka z szarej kostki z czerwonym wzorem; drzewa liściaste, ławki w tle.", "lato", "dzień", ""),
 "K1-P09": ("knyszyn", "f", "tablica na cokole zegara słonecznego", "Brązowa tablica z napisem o ustawie króla z 1568 r. na granitowym bloku.", "lato", "dzień", "detal"),
 "K1-P10": ("knyszyn", "f", "Rynek — pomnik (2019)", "Brązowa figura na granitowym cokole na placu z szarej kostki z wzorem; w tle trawniki, drzewa liściaste, alejki, budynki z czerwonymi dachami.", "lato", "dzień", ""),
 "K1-P11": ("knyszyn", "f", "dom z XVIII w. (2019)", "Długi parterowy dom, ściany białe, dach dwuspadowy z czerwonej dachówki, drewniany płot brązowy, słup betonowy z liniami; jezdnia asfaltowa i chodnik z płyt.", "lato", "dzień", "dokładny adres UNVERIFIED"),
 "K1-P12": ("knyszyn", "f", "pomnik — detal popiersia", "Zbliżenie brązowej figury w koronie i z łańcuchem; tło drzewa.", "lato", "dzień", "detal, nie widok ogólny"),
 "K1-P13": ("knyszyn", "f", "kościół św. Jana — bok", "Biały tynk z czerwonymi detalami i obramieniami okien, dach czerwony, wieża; słup przed kościołem, mur ogrodzenia biały.", "lato", "dzień", "rok zdjęcia UNVERIFIED (panoramio)"),
 "K1-P14": ("knyszyn", "f", "kościół św. Jana — fasada", "Biała fasada z czerwonym hełmem wieży i czerwonymi detalami, figura przed wejściem, stylizowane czarne latarnie z dwoma kloszami, niski mur; plac przed kościołem.", "lato", "dzień", ""),
 "K1-P15": ("knyszyn", "f", "kościół św. Jana — fasada (2024)", "Jak P14; plac przed kościołem z kostki granitowej (bruk), czarna stylizowana latarnia z dwoma kloszami, niski murowany mur.", "lato", "dzień", "najnowszy stan (2024-07-21)"),
 "K1-P16": ("knyszyn", "f", "kościół św. Jana — elewacja boczna (2024)", "Ściany białe, dach czerwony, czerwone obramienia okien; chodnik z czerwonej kostki, trawnik, głazy.", "lato", "dzień", ""),
 "K1-P17": ("knyszyn", "f", "kościół św. Jana — fasada (2009)", "Fasada kremowo-żółtawa (stan 2009, przed obecnym białym tynkiem), rusztowanie przy wieży, piaszczysty plac.", "lato", "dzień", "historyczny stan elewacji — porównaj P15"),
 "K1-P18": ("knyszyn", "f", "ul. Kościelna — widok wzdłuż", "Jezdnia asfaltowa bez linii, chodnik szary L, słup betonowy z oprawą na wysięgniku, domy parterowe z dachami dwuspadowymi, płoty.", "lato", "dzień", ""),
 "K1-P19": ("knyszyn", "f", "pierzeja Rynku — budynek handlowy", "Budynek 2-kondygnacyjny z poddaszem, elewacja z ciemnoczerwonej cegły klinkierowej i szarego tynku, napis firmowy (nie odtwarzamy), chodnik z kostki; obok budynek tynkowany szaro-beżowy.", "lato", "dzień", ""),
 "K1-P20": ("knyszyn", "f", "ul. Tykocka — pawilon handlowy", "Parterowy pawilon, elewacja żółto-niebieska z napisem firmowym (nie odtwarzamy), schody i rampa, parking asfaltowy.", "lato", "dzień", ""),
 "K1-P21": ("knyszyn", "f", "grafika historyczna", "Rycina XIX w. (ruiny i drzewa) — nie przedstawia stanu obecnego.", "", "", "nie liczona jako kadr celu"),
 "K1-P22": ("knyszyn", "b", "DK65 przy dawnym skrzyżowaniu z DW671 (2009)", "Widok na DK65 w stronę Białegostoku: pojazdy nadjeżdżają łukiem, czerwone barierki dla pieszych, przejście dla pieszych, wysepka z niskimi krzewami, zielony drogowskaz, pola i las w tle.", "lato", "dzień", "stan sprzed przebudowy na rondo; kierunek ~SE ESTIMATED z treści"),
 "K1-P23": ("knyszyn", "e", "ul. Tykocka (DW671) — latarnia (2009)", "Słup betonowy z liniami napowietrznymi i oprawą na wysięgniku po stronie chodnika; chodnik z szarej kostki z czerwonymi pasami; tuje, płot murowany.", "lato", "dzień", "typ oprawy z 2009 — nie dowodzi stanu LED"),
 "K1-P24": ("knyszyn", "b", "krzyż przy skrzyżowaniu DK65/DW671", "Wysoki stalowy krzyż na trawniku, ławki, chodnik; drzewa.", "lato", "dzień", "pl. Jana Pawła II (OSM way 1017406446) przy rondzie"),
 "K1-P25": ("dk65-02", "g", "Supraśl z mostu DK65 — widok W", "Rzeka między łąkami; w tle kratownicowy most kolejowy linii 38.", "wiosna", "dzień", "zrobione z mostu km 10,89; drogi nie widać"),
 "K1-P26": ("dk65-02", "g", "ujście Białej do Supraśli z mostu DK65", "Rzeka, łąki, w tle wieś; drogi nie widać.", "wiosna", "dzień", "km 10,89"),
 "K1-P27": ("dk65-04", "a", "Dobrzyniewo Duże — opis pliku 'DK65'", "Pole i łąka, wieś w oddali; drogi DK65 nie widać.", "lato", "dzień", "kadr przypisany do kafla, ale nie pokazuje drogi"),
 "K1-P28": ("(-3,0)", "a", "Fasty — skrzyżowanie drogi bocznej (2009)", "Jezdnia asfaltowa, znak ustąp pierwszeństwa, słup betonowy z oprawą na wysięgniku, domy z czerwonymi dachami, tuje.", "lato", "dzień", "155 m od trasy, kafel (-3,0) przed dk65-01"),
 "K1-P29": ("(-3,0)", "a", "Szosa Knyszyńska w Fastach km 8,12 (2020)", "Jezdnia 2×1: oś podwójna ciągła przechodząca dalej w przerywaną; chodnik L z kostki, ciąg pieszo-rowerowy P (niebieski znak), słupy betonowe z oprawami na wysięgnikach po L; pochmurno, jesień.", "jesień", "dzień", "11 m od trasy; 640 m przed kaflem dk65-01 — ten sam typ drogi"),
 "K1-P30": ("(-3,0)", "", "cerkiew w Fastach — kopuła", "Biała wieża cerkwi z kopułą, czarne ogrodzenie z krzyżem.", "lato", "dzień", "kontekst, nie cel"),
 "K1-P31": ("dk65-02", "g", "przystanek kolejowy Fasty (linia 38)", "Peron, budynek z wysokim dachem, wysoka latarnia peronowa z dwiema oprawami, tory i sieć trakcyjna.", "wiosna", "dzień", "~160 m na L od trasy (km 10,76)"),
 "K1-P32": ("(poza kaflami)", "g", "stacja Knyszyn (Krypno) — perony", "Peron, latarnie peronowe, sieć trakcyjna, elektryczny zespół trakcyjny.", "jesień", "świt", "~3 km od trasy — linia 38 nie biegnie wzdłuż DK65 w Knyszynie"),
 "K1-P33": ("(poza kaflami)", "g", "stacja Knyszyn — budynek", "Budynek 2-kondygnacyjny, tynk żółty, tablica z nazwą stacji.", "jesień", "świt", "jw."),
 "K1-P34": ("(poza kaflami)", "g", "stacja Knyszyn — peron NW", "Peron z płyt, sieć trakcyjna, tor.", "wiosna", "dzień", "jw."),
 "K1-P35": ("dk65-07", "", "Kozińce — droga wiejska", "Droga brukowana z kamienia polnego, chodnik z płyt, płoty, domy.", "lato", "dzień", "388 m od trasy — nie DK65"),
 "K1-P36": ("dk65-08", "", "Zalesie — droga wiejska", "Wąska asfaltowa droga, słup betonowy z oprawą na wysięgniku, zieleń.", "lato", "dzień", "641 m od trasy — nie DK65"),
 "K1-P37": ("dk65-06", "", "Obrubniki — droga", "Asfalt z piaszczystym poboczem, słupy, las.", "lato", "dzień", "911 m od trasy — nie DK65"),
 "K1-P38": ("dk65-04", "", "Dobrzyniewo Duże — wlot drogi przy szkole", "Wlot drogi bocznej, znak STOP, w tle szkoła z czerwonym dachem.", "lato", "dzień", "287 m od trasy"),
 "K1-P39": ("knyszyn", "f", "ul. Kościelna 4 — dom", "Parterowy dom z poddaszem, dach brązowy, elewacja jasna, ogrodzenie z czerwonej cegły z metalowymi przęsłami.", "lato", "dzień", ""),
 "K1-P40": ("knyszyn", "f", "plebania", "Dom 2-kondygnacyjny z dachem z czerwonej blachodachówki, elewacja szaro-beżowa, ogród z iglakami, alejka z kostki.", "lato", "dzień", ""),
 "K1-P41": ("knyszyn", "f", "tablica pamiątkowa na ścianie kościoła", "Granitowa tablica ze złotymi literami (1930).", "lato", "dzień", "detal"),
 "K1-P44": ("knyszyn", "e", "ul. Kościelna — latarnie, wieża kościoła", "Jezdnia asfaltowa z krawężnikami, słupy betonowe z oprawami na wysięgnikach po obu stronach, w tle wieża kościoła z czerwonym hełmem.", "lato", "dzień", "typ opraw z 2012 — LED UNVERIFIED"),
}
for pid, meta in sorted(pm.items()):
    tile, topic, el, desc, sez, pora, note = PH[pid]
    c = meta["coords"][0] if meta["coords"] else {}
    add(kafel=tile, temat=topic, element=el, parametr="zdjęcie (obejrzane)", lat=c.get("lat", ""), lon=c.get("lon", ""), kierunek_deg="UNVERIFIED",
        data_zdjęcia=(meta["date"] or "")[:19], sezon=sez, pora_dnia=pora, opis_co_widać=desc, url_źródła=meta["page"], url_pliku=meta["file_url"],
        plik_lokalny=f"files/photos/{pid}.jpg", licencja=meta["license"], autor=meta["artist"], status="SOURCED",
        uwagi=f"kadr {pid}; " + (note + "; " if note else "") + ("współrzędne kamery z Commons" if c else "brak współrzędnych w Commons") + "; kierunek: brak azymutu w metadanych")

# ---------- (b) junctions/roundabouts
J = [
 ("knyszyn", "rondo DK65×DW671 Knyszyn (OSM)", "średnica osi jezdni ronda (OSM, 2×r śr.)", "17,6", "m", 760623.5, 611996.5, "way/1426801304",
  "Pierścień OSM (21 węzłów, edycja 2026-01-05): r osi 8,4–9,1 m (śr. 8,8). Wloty jednokierunkowe 1-pasowe przy wysepkach: Obozowa N/S (ways 1464342634/-635/-638/-640), Tykocka E/W (1464342636/-637/-639, 1426600413); destination: Ełk, Białystok, Tykocin, Korycin. Wyspa środkowa: brak obiektu w OSM.",
  "https://www.openstreetmap.org/way/1426801304", "ODbL", "SOURCED", "Średnica zewnętrzna UNVERIFIED: przy szer. jezdni ronda 5–6 m (nieznana) wyszłoby ~23–24 m — WORKING_VALUE, nie pomiar. Ortofoto 2025-05-27 sprzed budowy."),
 ("knyszyn", "skrzyżowanie DK65×DW671 — stan na ortofoto", "typ skrzyżowania 2025-05-27", "4-wlotowe skanalizowane", "", 760623.5, 611996.5, "",
  "Ortofoto: skrzyżowanie czterowlotowe bez ronda, malowane wyspy kanalizujące (szrafy) i wysepka z krzewami na wlocie NW, przejścia dla pieszych na wszystkich 4 wlotach, pasy do lewoskrętu; chodniki z kostki.",
  "", ORTO_LIC, "ESTIMATED", "Rozbieżność z OSM i D65 (rondo) — rondo powstało po 2025-05-27 (OSM 2026-01-05); planowane wg MI 10.12.2024. Plik: files/orto/junctions/J_rondo_knyszyn_north.jpg"),
 ("knyszyn", "przebudowa skrzyżowania DK65×DW671 na rondo — dokument", "zakres i harmonogram", "rondo + chodniki + oświetlenie przejść", "", 760623.5, 611996.5, "",
  "MI, znak DDP-6.054.39.2024, 10.12.2024, s.1: „przebudowa skrzyżowania DK 65 z DW 671 na skrzyżowanie z ruchem okrężnym, przebudowa chodników … budowa oświetlenia dedykowanego na przejściach dla pieszych”; „złożyła wniosek o ZRiD … w VII 2024 r.”",
  "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDBUJN7/i05277-o1.pdf", "dokument urzędowy (art. 4 pr. aut.)", "SOURCED", "data zakończenia budowy UNVERIFIED (brak dokumentu)"),
 ("dk65-06", "rondo S19/DK65 przy Krynicach (km 16,66)", "średnica osi pierścienia (OSM)", "44", "m", 767646.4, 603505.1, "way/1151531611;way/1560819266",
  "Pierścień z 2 odcinków (r osi 19–26 m, śr. 22 m), jednokierunkowy 1-pasowy; wloty: DK65 stara (secondary bez ref, 1448265994/-995), DK65 nowa jezdnia dwukierunkowa jako 2 jednokierunkowe 2-pasowe (1151531608/1151531613, edycja 2026-11-08), droga gospodarcza. Węzeł proponowany 'Dobrzyniewo Północ' (node 13816249645).",
  "https://www.openstreetmap.org/way/1151531611", "ODbL", "SOURCED", "Ortofoto 2025-05-25 ronda nie ma (roboty ziemne). D65 p.6: nowa jezdnia DK65 nieotwarta — sprzeczne z tagowaniem OSM highway=primary (2026-11-08); UNVERIFIED stan na dziś."),
 ("knyszyn-s", "rondo S16 na DK65 ~3 km na S od Knyszyna (w budowie)", "średnica osi pierścienia (OSM construction)", "41", "m", 762490.7, 609929.7, "way/1511762690",
  "OSM highway=construction, construction=primary, junction=roundabout (2026-05-10), r osi 19,8–21,7 m. Ortofoto 2025-05-25: las i DK65 bez robót w tym miejscu.",
  "https://www.openstreetmap.org/way/1511762690", "ODbL", "SOURCED", "Auto Świat 14.05.2026: „Nowy odcinek S16 rozpocznie się rondem na drodze krajowej nr 65, około 3 km na południe od Knyszyna”."),
 ("dk65-04", "skrzyżowanie Ełcka × Białostocka/Kościelna (Fasty/Dobrzyniewo, km 13,13)", "typ", "4-wlotowe zwykłe", "", 768548.1, 600126.5, "node/839431354",
  "Ortofoto 2025-05-25: skrzyżowanie czterowlotowe bez sygnalizacji, przejście dla pieszych na wlocie N drogi głównej, duży parking NE, zabudowa usługowa.",
  "", ORTO_LIC, "ESTIMATED", "files/orto/junctions/J_fasty_bialostocka_km13_1_north.jpg"),
 ("dk65-07", "skrzyżowanie DK65 × droga 1392B (km 18,77)", "typ", "3-wlotowe (T) z poszerzeniem", "", 766440.6, 605132.6, "node/897574830",
  "Ortofoto: wlot drogi powiatowej od E z wyokrągleniami, malowane szrafy na wlocie, DK65 z linią ciągłą przy skrzyżowaniu.",
  "", ORTO_LIC, "ESTIMATED", "files/orto/junctions/J_1392B_km18_77_north.jpg"),
 ("dk65-10", "skrzyżowanie DK65 × droga 1397B (km 22,65)", "typ", "wlot boczny (OSM)", "", 764073.6, 608177.3, "node/13495192875",
  "Wycinek ortofoto pobrany (files/orto/junctions/J_1397B_km22_65_north.jpg) — nieopisany szczegółowo.", "", ORTO_LIC, "UNVERIFIED", "do obejrzenia przy szlifie"),
]
for (tile, el, par, val, unit, x, y, osm, desc, url, lic, st, note) in J:
    lon, lat = bw.transform(x, y)
    pf = {"rondo DK65×DW671 Knyszyn (OSM)": "", "skrzyżowanie DK65×DW671 — stan na ortofoto": "files/orto/junctions/J_rondo_knyszyn_north.jpg",
          "przebudowa skrzyżowania DK65×DW671 na rondo — dokument": "files/docs/MI-odp-interpelacja-5277-2024-12-10.pdf"}.get(el, "")
    if not pf and "files/orto" in note: pf = note.split()[-1] if note.startswith("files/") else ""
    add(kafel=tile, temat="b", element=el, parametr=par, wartość=val, jednostka=unit, lat=round(lat, 6), lon=round(lon, 6), osm_id=osm, opis_co_widać=desc, url_źródła=url or WMS,
        plik_lokalny=pf, licencja=lic, autor="Ministerstwo Infrastruktury" if "MI," in desc else ("OpenStreetMap" if lic == "ODbL" else "GUGiK (Geoportal)"), status=st, uwagi=note,
        data_zdjęcia="2025-05-27" if tile == "knyszyn" and lic == ORTO_LIC else ("2025-05-25" if lic == ORTO_LIC else ""))

# ---------- (c) S19/S16 construction
C = [
 ("dk65-01/02", "S19 Krynice–Dobrzyniewo–Białystok Zachód", "data oddania do ruchu", "2026-10-20", "",
  "wartowiedziec.pl 21.10.2026: „Trasa o długości 10,2 km została oddana do ruchu 20 października 2026 roku”; obiekty „nad drogą krajową nr 65”.",
  "https://wartowiedziec.pl/komunikacja-i-transport/82331-nowy-odcinek-s19-otwarty", "SOURCED", "źródło prasowe; komunikat GDDKiA (gov.pl) niedostępny 2026-11-15 (503/reset) — potwierdzić"),
 ("dk65-01/02", "S19 Krynice–Dobrzyniewo–Białystok Zachód", "zapowiedź otwarcia", "tydzień 13.10.2026", "",
  "Auto Świat 13.10.2026: lista GDDKiA „Oddanie do ruchu S19 Krynice — Dobrzyniewo — Białystok Zachód”; odcinek 10,18 km „od istniejącej DK65”.",
  "https://www.auto-swiat.pl/wiadomosci/aktualnosci/jakie-nowe-drogi-beda-gotowe-w-pazdzierniku-2026-r-gddkia-podaje-nowe-odcinki/e3ld8mg", "SOURCED", ""),
 ("dk65-02", "wiadukt S19 nad Szosą Knyszyńską w Fastach — objazd", "likwidacja objazdu tymczasowego", "2025-10-15 9:00", "",
  "GDDKiA O/Białystok 14.10.2025 (fragment w indeksie wyszukiwarki): „Zamykamy tymczasowy objazd wiaduktu, który powstaje w ciągu drogi ekspresowej S19 Krynice - Białystok Zachód. Ruch wraca na stały przebieg DK65.”",
  "https://www.gov.pl/web/gddkia-bialystok/zmiana-organizacji-ruchu-na-drodze-krajowej-nr-65", "UNVERIFIED", "strona gov.pl zwracała 503/reset 2026-11-15 — cytat tylko z wyników wyszukiwania; ortofoto 2025-05-25 pokazuje objazd łukiem z czerwono-białymi pachołkami i budowany wiadukt (files/orto/junctions/J_s19_wiadukt_km10_3_north.jpg)"),
 ("dk65-02", "wiadukt S19 w Fastach — stan na ortofoto", "stan 2025-05-25", "w budowie (pomost obok objazdu)", "",
  "Ortofoto: konstrukcja wiaduktu (przyczółki, płyta) nad wykopem korytarza S19 (biegnącego N–S), obok drogi; droga prowadzona łukiem objazdu z czerwono-białym wygrodzeniem, plac budowy z materiałami.",
  WMS, "ESTIMATED", "D65 p.3: wiadukt stoi, otwarty (właściciel)"),
 ("dk65-01…05", "status starej DK65 przez Fasty/Dobrzyniewo", "kategoria po otwarciu S19", "utrata statusu drogi krajowej", "",
  "MI 10.12.2024 s.2: „w III kwartale 2026 r. po wybudowaniu i oddaniu do użytkowania … S19 … DK 65 na przedmiotowym odcinku drogi … utraci status drogi krajowej”.",
  "https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDBUJN7/i05277-o1.pdf", "SOURCED", "zgodne z OSM: secondary bez ref, old_ref (data/osm_route_ways.json); nowa kategoria (wojewódzka/powiatowa) UNVERIFIED"),
 ("dk65-06…11, knyszyn-s", "S16 Knyszyn–Krynice", "długość / termin / ograniczenia na DK65", "8,4 km / 2028 / 50 km/h, zakazy wyprzedzania, zwężenia", "",
  "Auto Świat 14.05.2026: „Nowy odcinek S16 będzie miał 8,4 km długości”; „nowa trasa ma zostać oddana do użytku w 2028 r.”; „Na drodze krajowej nr 65, biegnącej równolegle do inwestycji, pojawią się ograniczenia prędkości do 50 km na godz.”",
  "https://www.auto-swiat.pl/wiadomosci/aktualnosci/s16-knyszynkrynice-w-budowie-kluczowy-odcinek-wchodzi-w-faze-realizacji/vtwl63z", "SOURCED", "wykonawca wg artykułu: firma budowlana (nazwy nie odtwarzamy w grze); obecne oznakowanie tymczasowe na DK65 — UNVERIFIED (kadry właściciela 2026-07-28 pokazują żółte oznakowanie)"),
 ("dk65-06…11", "OSM — budowa wzdłuż DK65", "długość highway=construction motorway w pasie 600 m", "16,6", "km",
  "ADR 0203 / data plan: construction motorway 16 573 m przy km 16,7–25,0 (ostatnia edycja 2026-09-28); proposed motorway 33,6 km.",
  "https://www.openstreetmap.org/way/1511762695", "SOURCED", "OSM ODbL; w ortofoto 2025-05-25 roboty widoczne przy km 16,7 (NE), brak przy rondzie S16"),
]
for (tile, el, par, val, unit, desc, url, st, note) in C:
    pf = "files/docs/MI-odp-interpelacja-5277-2024-12-10.pdf" if "sejm" in url else ("files/orto/junctions/J_s19_wiadukt_km10_3_north.jpg" if "ortofoto" in desc.lower() else "")
    add(kafel=tile, temat="c", element=el, parametr=par, wartość=val, jednostka=unit, opis_co_widać=desc, url_źródła=url, plik_lokalny=pf,
        licencja=("dokument urzędowy" if ("sejm" in url or "gov.pl" in url) else (ORTO_LIC if url == WMS else ("ODbL" if "openstreetmap" in url else "cytat prasowy (prawo cytatu), tylko referencja"))),
        autor="", status=st, uwagi=note)

# ---------- (d) Ełcka width summary
ek = [r for r in X if 10.94 <= r[0] <= 16.6 and r[0] not in (13.0, 14.5, 15.5)]
lls = [round(r[3] - r[1], 2) for r in ek]; asp = [r[5] - r[4] for r in ek if r[4] is not None and r[5] is not None]
add(kafel="dk65-02…05", temat="d", element="ul. Ełcka/Studzienna (stara DK65, km 10,94–16,6)", parametr="rozstaw linii krawędziowych (oś–oś), min–mediana–max",
    wartość=f"{min(lls):.1f}–{sorted(lls)[len(lls)//2]:.1f}–{max(lls):.1f}", jednostka="m", osm_id="way/716806121;way/1024956365;way/41533343;way/1243220441;way/1024956364;way/1399803717",
    opis_co_widać=f"{len(lls)} przekrojów z ortofoto 0,1 m (2025-05-25). Asfalt łącznie z opaskami za liniami: {min(asp):.1f}–{max(asp):.1f} m (n={len(asp)}). Pas ruchu (oś linii środkowej–oś linii krawędziowej) 2,9–3,3 m.",
    url_źródła=WMS, licencja=ORTO_LIC, autor="GUGiK", status="ESTIMATED",
    uwagi="Wartość właściciela ~6,9 m (D65 p.5) mieści się między rozstawem linii (~6,2 m) a szerokością asfaltu (~7,5–9 m). OSM: brak tagu width. Przebieg: kafle dk65-02 (km 10,94–11,80), dk65-03 (11,80–12,28), dk65-04 (12,28–14,36), dk65-05 (14,36–16,56); nazwa Studzienna od km 15,39.")

# ---------- (e) lamps
add(kafel="dk65-01…11, knyszyn*", temat="e", element="latarnie w OSM", parametr="liczba węzłów highway=street_lamp w pasie ±300 m od trasy", wartość="0", jednostka="szt.",
    opis_co_widać="API 0.6 /map co 500 m (data/osm_corridor.json): brak latarni zmapowanych jako węzły; lit=interval tylko na ul. Rynek (ways 98071185, 173422687).",
    url_źródła="https://api.openstreetmap.org/api/0.6/map?bbox=22.9300,53.2950,22.9330,53.2970", licencja="ODbL", autor="OpenStreetMap", status="SOURCED", uwagi="Overpass niedostępny przez proxy 2026-11-15")
add(kafel="knyszyn", temat="e", element="oświetlenie przejść przy rondzie DK65×DW671", parametr="zakres projektu", wartość="oświetlenie dedykowane przejść dla pieszych",
    opis_co_widać="MI 10.12.2024: „budowa oświetlenia dedykowanego na przejściach dla pieszych” (w zakresie przebudowy skrzyżowania).", url_źródła="https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDBUJN7/i05277-o1.pdf",
    plik_lokalny="files/docs/MI-odp-interpelacja-5277-2024-12-10.pdf", licencja="dokument urzędowy", autor="Ministerstwo Infrastruktury", status="SOURCED", uwagi="typ opraw, wysokość, rozstaw — UNVERIFIED")
add(kafel="knyszyn", temat="e", element="latarnie uliczne w mieście (Tykocka, Grodzieńska, Kościelna)", parametr="typ słupa / wysięgnik / strona", wartość="słup betonowy z linią napowietrzną, oprawa na wysięgniku, jedna strona",
    opis_co_widać="Zdjęcia 2009–2012 (K1-P06, P18, P23, P44) i orto km 28,00 (cień słupa z wysięgnikiem po P). Kościół: stylizowane czarne latarnie z 2 kloszami (P14, P15).",
    licencja="", status="ESTIMATED", uwagi="LED/barwa światła: UNVERIFIED w źródłach (D65 p.8: białe LED — deklaracja właściciela); wysokość słupa i rozstaw UNVERIFIED; przetarg gminy Knyszyn na LED — nie znaleziono (wyszukiwanie 2026-11-15)")
add(kafel="dk65-04", temat="e", element="latarnia przy zatoce autobusowej km 13,0", parametr="obecność", wartość="słup z wysięgnikiem (cień na orto)", lat=pts["km13.00"]["lat"], lon=pts["km13.00"]["lon"],
    opis_co_widać="Na zoomie km 13,00 cień słupa z wysięgnikiem przy zatoce L.", url_źródła=om["km13.00"]["wms_url"], plik_lokalny="files/orto/km/zoom_km12.50_km13.00_km13.50_km14.00.jpg", licencja=ORTO_LIC, autor="GUGiK", status="ESTIMATED", uwagi="typ oprawy UNVERIFIED")
add(kafel="dk65-06…11", temat="e", element="oświetlenie DK65 poza terenem zabudowanym", parametr="obecność na ortofoto (przekroje km 17–25)", wartość="nie stwierdzono",
    opis_co_widać="W 10 wycinkach km 17–25 brak cieni słupów oświetleniowych przy jezdni (poza zatoką km 19).", url_źródła=WMS, licencja=ORTO_LIC, autor="GUGiK", status="ESTIMATED", uwagi="zgodne z ADR 0204 (DK65 w polu nieoświetlona)")

# ---------- (f) Rynek
RY = [
 ("układ placu", "park z promienistymi alejkami, plac okrągły w centrum", "", "Ortofoto 2025-05-27: plac zieleni ok. 120×110 m, alejki z jasnej kostki promieniście do centralnego okrągłego placyku (Ø ~25 m ESTIMATED), trawniki, kilkadziesiąt drzew liściastych, ławki; na N budynek UM z czerwonym dachem i lukarnami, parking.", "files/orto/junctions/J_rynek_W_north.jpg", "ESTIMATED", "OSM leisure=park way 300660468 (7441 m²)"),
 ("fontanna", "fontanna posadzkowa ~6×6 m, podświetlana", "m", "Ortofoto: kwadrat jaśniejszej posadzki ~6,3×5,8 m z kratką odpływową w środku, na okrągłym placu. OSM: amenity=fountain, fountain=splash_pad, lit=yes, pow. 32 m² (way 1484732058, 2026-03-02).", "files/orto/junctions/J_fontanna_north.jpg", "ESTIMATED", "zgodne z opisem kadrów właściciela (fontanna nocą z podświetleniem fiolet/róż, OWNER-PHOTOS-KNYSZYN.md)"),
 ("pomnik", "figura brązowa na granitowym cokole", "", "Pomnik Zygmunta Augusta na kwadratowym cokole NW od fontanny (orto: obiekt z cieniem ~7 m od placu centralnego); zdjęcia K1-P08, P10, P12.", "files/photos/K1-P10.jpg", "SOURCED", ""),
 ("nawierzchnia", "jasnoszara kostka betonowa (alejki); posadzka z wzorem czerwonym przy pomniku", "", "Orto + K1-P08/P10 (szara kostka z czerwonym wzorem). Kadry właściciela: kostka granitowa w łuki (OWNER-PHOTOS) — przy fontannie.", "files/photos/K1-P08.jpg", "ESTIMATED", "materiał (beton/granit) UNVERIFIED na całym placu"),
 ("pierzeje", "1–2 kondygnacje + poddasze; dachy dwuspadowe i wielospadowe", "", "Pierzeje (orto + K1-P02, P07, P19, P39): domy parterowe i 2-kondygnacyjne; dachy czerwone, brązowe, grafitowe; elewacje kremowe, białe, szaro-beżowe, cegła klinkierowa ciemnoczerwona; UM 2 kondygnacje + lukarny.", "files/photos/K1-P07.jpg", "ESTIMATED", "kolory słownie z obrazów"),
 ("kościół", "kościół św. Jana Apostoła i Ewangelisty — biały z czerwonymi detalami", "", "K1-P15/P16 (2024): tynk biały, dach i hełm wieży czerwone, czerwone obramienia okien, plac z bruku granitowego, stylizowane latarnie; w 2009 elewacja kremowo-żółtawa (P17).", "files/photos/K1-P15.jpg", "SOURCED", "~100–150 m od Rynku"),
 ("zieleń", "drzewa liściaste w alejach i na obrzeżach", "", "Orto: kilkadziesiąt dużych koron; K1-P01: wysokie drzewa liściaste wzdłuż alejki. Gatunki UNVERIFIED.", "files/photos/K1-P01.jpg", "ESTIMATED", ""),
]
for (par, val, unit, desc, pf, st, note) in RY:
    add(kafel="knyszyn", temat="f", element="Rynek w Knyszynie", parametr=par, wartość=val, jednostka=unit, lat=53.3121, lon=22.9188, osm_id="way/300660468" if par == "układ placu" else ("way/1484732058" if par == "fontanna" else ""),
        opis_co_widać=desc, url_źródła=WMS if "orto" in pf else "", plik_lokalny=pf, licencja=ORTO_LIC if "orto" in pf else "CC BY-SA (patrz wiersz zdjęcia)", autor="GUGiK" if "orto" in pf else "", status=st, uwagi=note,
        data_zdjęcia="2025-05-27" if "orto" in pf else "")

# ---------- (g) rail + trees
add(kafel="dk65-01, dk65-02", temat="g", element="linia kolejowa nr 38 wzdłuż trasy", parametr="odległość od osi drogi", wartość="111 (km 9,0) / 150 (km 10,0) / 203 (km 11,0) / 328 (km 11,5) / ≥487 (km ≥12)", jednostka="m",
    osm_id="way/173466803;way/41533341;way/406675496", opis_co_widać="Tor po L (SW/W) od drogi, zelektryfikowany 3 kV (OSM electrified=contact_line, voltage=3000), ref=38; most kolejowy nad Supraślą ~200 m od mostu drogowego (widoczny na K1-P25); przystanek Fasty ~160 m (K1-P31).",
    url_źródła="https://www.openstreetmap.org/way/173466803", licencja="ODbL", autor="OpenStreetMap", status="SOURCED", uwagi="odległości: tools/raildist.py; od km ~12 linia odchodzi na W (stacja Knyszyn w Krypnie ~3 km od miasta)")
add(kafel="dk65-01…knyszyn", temat="g", element="przejazdy kolejowe na trasie", parametr="liczba przejazdów na trasie wariantu A km 8,6–28,4", wartość="0", jednostka="szt.",
    opis_co_widać="Przejazdy z OSM w pobliżu są na drogach bocznych: 038 010 194 (131 m od trasy), 038 010 956 (64 m, droga gruntowa), 038 012 443 (177 m, przy przystanku Fasty).",
    url_źródła="https://www.openstreetmap.org/node/2559254736", licencja="ODbL", autor="OpenStreetMap", status="SOURCED", uwagi="data/osm_corridor.json; przejazd na DW671 w dw671-tykocin-01 (ADR 0212) poza zakresem")
TR = [("T_km11_7", "dk65-02/03", "szpaler drzew Ełcka km ~11,6–11,8", "jednostronny po L (W), ~8 drzew / 200 m → rozstaw ~20–25 m; 8–12 m od krawędzi asfaltu; po P zadrzewienie grupowe"),
      ("T_km14_6", "dk65-04/05", "szpaler drzew Ełcka km ~14,5–14,7", "gęstszy po L (W): ~13 drzew / 200 m → rozstaw ~15 m, 5–10 m od krawędzi; po P pojedyncze drzewa"),
      ("T_km20_5", "dk65-08", "grupa drzew przy DK65 km ~20,5", "~8 drzew na ~60 m po NE przy zatoce autobusowej; dalej las sosnowy (ciemne korony) po SW")]
for (fid, tile, el, val) in TR:
    m = json.load(open(K1 + 'orto_t/meta.json'))[fid]; lon, lat = bw.transform(m["x"], m["y"])
    add(kafel=tile, temat="g", element=el, parametr="liczba/rozstaw/odległość (ortofoto 200×200 m)", wartość=val, lat=round(lat, 6), lon=round(lon, 6), url_źródła=m["wms_url"],
        plik_lokalny=f"files/orto/junctions/{fid}_north.jpg", licencja=ORTO_LIC, autor="GUGiK", status="ESTIMATED", data_zdjęcia="2025-05-25", sezon="wiosna", pora_dnia="dzień",
        opis_co_widać="Ortofoto z góry; korony i cienie drzew liczone ręcznie.", uwagi="gatunki UNVERIFIED (brak źródła; OSM brak natural=tree/tree_row na odcinku poza km 27,4); skala 2,25 px/m w podglądzie — ±3 m")
add(kafel="knyszyn", temat="g", element="szpaler drzew przy Obozowej km 27,4", parametr="OSM natural=tree_row", wartość="74", jednostka="m", osm_id="way/300804461",
    opis_co_widać="Tree row po P, 12–62 m od trasy (edycja 2014).", url_źródła="https://www.openstreetmap.org/way/300804461", licencja="ODbL", autor="OpenStreetMap", status="SOURCED", uwagi="gatunek brak")

# ---------- milestones (kilometraż)
add(kafel="dk65-01…knyszyn-s", temat="a", element="słupki kilometrowe DK65 (OSM)", parametr="kilometraż DK65 na trasie", wartość="161 (trasa km 9,05) … 143 (trasa km 27,10)", jednostka="km",
    osm_id="node/3314359595…node/3314359613", opis_co_widać="19 węzłów highway=milestone ref=65 co ~1 km po L stronie (3–6 m od osi): kilometraż DK65 maleje w stronę Knyszyna; DK65 km ≈ 170,05 − km trasy A.",
    url_źródła="https://www.openstreetmap.org/node/3314359611", licencja="ODbL", autor="OpenStreetMap", status="SOURCED", uwagi="km DK65 w kolumnie element wierszy przekroju liczone tym wzorem (ESTIMATED ±0,1 km)")

# ---------- assign ids, write
n = 0
for r in rows:
    if not r["id"]:
        n += 1; r["id"] = f"K1-{n:03d}"
with open(OUT + "manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print("rows", len(rows), "photos", sum(1 for r in rows if r["parametr"].startswith("zdjęcie")))
json.dump([{k: r[k] for k in ("id", "kafel", "temat", "parametr", "wartość", "status")} for r in rows], open(K1 + "rows_summary.json", "w"), ensure_ascii=False, indent=0)
