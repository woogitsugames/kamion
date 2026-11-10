"""Generator listy ujec zdjeciowych trasy startowej (D41) -> docs/owner/PHOTO-LIST.md + mapka PNG.

Odtworzenie (z katalogu repo):
    uv run --project tools/worldgen python tools/worldgen/photolist/build_photo_list.py

Zrodla: Data/Regions/bialystok-industrial-c/{gate3_cameras.json, generated/control_cameras.json,
route_start.json, roads.graph.json, buildings.geojson, generated/osm_context.json}.
Tylko dane wlasne repo (OSM + GUGiK BDOT10k). Zadnych kafli ani serwerow zewnetrznych, zadnego Google.
Wspolrzedne kamer: lokalne E,N = EPSG:2180 minus origin regionu (region.yaml) -> WGS84 (pyproj).
Punkty "authored" to WORKING_VALUE (+-10 m): precyzyjne miejsce ustala wlasciciel na miejscu.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon as MplPoly  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.affinity import translate  # noqa: E402
from shapely.geometry import LineString, Point, shape  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
REG = REPO / "Data/Regions/bialystok-industrial-c"
OX, OY = 777995.0, 596223.0  # region.yaml origin (EPSG:2180)
TO_WGS = Transformer.from_crs(2180, 4326, always_xy=True)

# ---------------------------------------------------------------- dane
route = json.load(open(REG / "route_start.json", encoding="utf-8"))
RPTS = [tuple(p) for p in route["points_en"]]
RLINE = LineString(RPTS)
STEP = route["step_m"]


def route_at(s):
    s = max(0.0, min(RLINE.length, s))
    p = RLINE.interpolate(s)
    p1 = RLINE.interpolate(max(0, s - 6))
    p2 = RLINE.interpolate(min(RLINE.length, s + 6))
    hdg = math.degrees(math.atan2(p2.x - p1.x, p2.y - p1.y)) % 360
    return (p.x, p.y), hdg


def offset(pt, hdg, lateral):
    """lateral > 0 = na lewo od kierunku jazdy"""
    a = math.radians(hdg)
    return (pt[0] - math.cos(a) * lateral, pt[1] + math.sin(a) * lateral)


def bearing(a, b):
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


def wgs(pt):
    lon, lat = TO_WGS.transform(pt[0] + OX, pt[1] + OY)
    return lat, lon


def compass(az):
    names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return names[int((az + 22.5) // 45) % 8]


cams = {}
for fn in ("generated/control_cameras.json", "gate3_cameras.json"):
    for c in json.load(open(REG / fn, encoding="utf-8"))["cameras"]:
        cams[c["id"]] = c


def cam_pose(cid):
    c = cams[cid]
    pos = (c["pos"][0], c["pos"][1])
    la = (c["look_at"][0], c["look_at"][1])
    return pos, bearing(pos, la), c


RING_BIE = (554.676, -716.554)
RING_PUT = (-554.253, 21.455)
VIADUCT_AZ = 120.0  # os wiaduktu Andersa (OSM bridge=viaduct, azymut 119/299 i 122/302)

# ---------------------------------------------------------------- ujecia
# kind: K kamera gate3/photo_match, F fasada, N nawierzchnia, Z zielen, L latarnia/znak, P auta, D detal
# time: S = pochmurno w dzien, Z = zmierzch, N = niskie slonce (tez OK)
# access: pub = publicznie z chodnika, priv = teren prywatny (zgoda/z zewnatrz), road = trasa szybkiego ruchu (tylko z auta/pasazer lub bezpieczna zatoka)
SHOTS = []


def add(**kw):
    kw.setdefault("h", "1,5 m")
    kw.setdefault("time", "S")
    kw.setdefault("pri", 1)
    kw.setdefault("access", "pub")
    kw.setdefault("cams", [])
    SHOTS.append(kw)


# ---- Kwadrat Park (teren prywatny) ----
add(key="yard_start", kind="K", mode=("cam", "g3a_eye_s0012"), cams=["g3a_eye_s0012", "stretch_01"], access="priv",
    place="Kwadrat Park, plac przy rampach, start trasy (s = 30 m)",
    toward="wzdłuż placu w głąb bazy; rampy z prawej, hala z lewej",
    h="1,5 m (opcj. 2,5 m z kabiny)",
    goal="Dopasowanie kadru gate3 (g3a_eye_s0012 = stretch_01). Całość: rampy, nawierzchnia placu, oznakowanie poziome, oświetlenie.")
add(key="docks", kind="K", mode=("cam", "stretch_05_docks"), cams=["stretch_05_docks"], access="priv",
    place="Kwadrat Park, rampy załadunkowe (11 bram), widok z placu",
    toward="na rampy — bramy segmentowe, odbojniki, doszczelnienia",
    goal="Dopasowanie kadru stretch_05_docks. Potem 3 zbliżenia: brama, odbojnik, doszczelnienie (bez logo firm).")
add(key="hall_dock_wall", kind="F", mode=("standoff", (708, -491), 22), access="priv",
    place="Hala z rampami (magazyn ok. 2400 m², wys. ok. 5,7 m wg LoD1) — ściana od strony placu",
    toward="prostopadle na środek ściany",
    goal="TEKSTURA FASADY prostopadle: cała ściana + 2 zbliżenia (blacha/płyta warstwowa, cokół, rynna). Karta szarości/biała kartka w kadrze.")
add(key="hall_big", kind="F", mode=("route_target", 62, 0, (568, -422)), access="priv",
    place="Największa hala Kwadrat Parku (ok. 21 000 m², wys. ok. 10 m) — widok z dystansu ok. 130 m",
    toward="na elewację hali (kąt skośny 20-30° dopuszczalny, bryła + dach)",
    goal="Bryła i proporcje hali, rytm bram i okien, kolory. Dodatkowo jedno ujęcie prostopadłe, jeśli da się podejść.", pri=2)
add(key="hall_tall", kind="F", mode=("route_target", 33, 0, (606, -350)), access="priv",
    place="Hala wysoka (ok. 4400 m², wys. ok. 14 m) po zachodniej stronie startu",
    toward="na ścianę szczytową/boczną",
    goal="Tekstura fasady wysokiej hali (blacha trapezowa / płyta). Prostopadle.", pri=2)
add(key="yard_asphalt", kind="N", mode=("route", 80, 0, "down"), access="priv",
    place="Plac bazy — asfalt przy rampach", toward="PIONOWO W DÓŁ (obiektyw równolegle do ziemi)",
    h="ok. 1,3 m nad ziemią", goal="NAWIERZCHNIA z góry: asfalt placu (ziarno, spękania, plamy oleju). Kartka A4 jako skala. 2 ujęcia: czysty fragment + z linią/oznakowaniem.")
add(key="yard_series", kind="K", mode=("cam", "g3a_eye_s0062"),
    cams=["g3a_eye_s0062", "g3a_eye_s0112", "g3a_eye_s0162", "g3a_eye_s0212"], access="priv",
    place="Droga dojazdowa bazy: seria co 50 m (s = 62, 112, 162, 212 m) — dopasowanie kadrów gate3",
    toward="wzdłuż drogi dojazdowej w stronę bramy",
    goal="Seria 4 kadrów wg załącznika A (współrzędne dla każdego). Alternatywa: wideo z auta (patrz niżej).")
add(key="hall_magazyn", kind="F", mode=("route_target", 212, 0, (680, -595)), access="priv",
    place="Magazyn przy bramie bazy (ok. 1600 m², wys. ok. 5,6 m)", toward="na ścianę od strony drogi dojazdowej",
    goal="Tekstura fasady prostopadle + detal bramy i drzwi.", pri=2)
add(key="fence_gate", kind="D", mode=("route", 232, 0, "fwd"), access="priv",
    place="Brama bazy: szlaban/portiernia, ogrodzenie", toward="na wjazd (od środka) — szlaban, słupki, słup oświetleniowy",
    goal="DETAL: ogrodzenie (typ siatki/paneli, słupki), szlaban, portiernia. Z bliska sam materiał, bez logo i tablic.")
add(key="gate_out", kind="K", mode=("cam", "g3a_eye_s0262"), cams=["g3a_eye_s0262", "stretch_03"], access="priv",
    place="Brama bazy od środka — wyjazd na drogę publiczną", toward="na wyjazd i dalej drogą w stronę ronda",
    h="1,5 m (opcj. 2,5 m z kabiny)", goal="Dopasowanie kadru gate3 (g3a_eye_s0262 = stretch_03).")
add(key="gate_in", kind="K", mode=("cam", "kwadrat_park_gate"), cams=["kwadrat_park_gate"],
    place="Z drogi publicznej wstecz na wjazd do Kwadrat Parku", toward="na wjazd/bramę bazy (wstecz trasy)",
    goal="Dopasowanie kadru kwadrat_park_gate: układ wjazdu, krawężniki, studzienki, oznakowanie przed bramą.")
add(key="fuel_canopy", kind="F", mode=("standoff", (572, -632), 18), pri=2,
    place="Stacja paliw przy drodze dojazdowej (wiata)", toward="na wiatę i dystrybutory z boku",
    goal="Konstrukcja wiaty, wysokość, posadzka. BEZ zbliżeń logo i cen; fikcyjne marki w grze.")
add(key="gate_series_to_rondo", kind="K", mode=("cam", "g3a_eye_s0312"),
    cams=["g3a_eye_s0312", "stretch_04"], place="Dojazd do Ronda Bieżeństwa spod wiaduktu (s = 312 m i 360 m)",
    toward="na wlot ronda i wiadukt Andersa",
    goal="Dopasowanie kadrów g3a_eye_s0312 i stretch_04 (podobne pozy).")
# ---- Rondo Bieżeństwa ----
add(key="bie_ground", kind="K", mode=("cam", "photo_biezenstwa_ground"), cams=["photo_biezenstwa_ground"],
    place="Rondo Pamięci Bieżeństwa 1915 r. — widok z nasypu/chodnika (photo match z CC0 20201102_152339)",
    toward="na wiadukt Andersa nad rondem",
    goal="DOPASOWANIE KADRU (photo_match): ten sam punkt widzenia co referencja CC0. Rób z chodnika.")
add(key="bie_approach", kind="K", mode=("cam", "g3a_rondo_bie_approach"), cams=["g3a_rondo_bie_approach", "g3a_eye_s0362", "g3a_eye_s0412"],
    place="30 m przed wlotem na Rondo Bieżeństwa", toward="na środek ronda (wyspa, wiadukt)",
    goal="Dopasowanie kadru g3a_rondo_bie_approach (FOV 65°; użyj 1× i ew. 0,5×).")
add(key="bie_above", kind="K", mode=("cam", "g3a_rondo_bie_above"), cams=["g3a_rondo_bie_above", "biezenstwa_above"],
    h="ok. 12-45 m: tylko jeśli jest dostęp (kładka/nasyp)", pri=3,
    place="Rondo Bieżeństwa — widok z góry ukośnie (gra: 45 m nad ziemią)", toward="na rondo z góry",
    goal="OPCJONALNIE: z nasypu, kładki lub z chodnika wiaduktu (tylko jeśli legalne i bezpieczne). Dron: NIE (przepisy i zasady projektu).")
add(key="bie_viaduct_side", kind="F", mode=("ring_side", RING_BIE, 45, 40), pri=1,
    place="Wiadukt Andersa nad Rondem Bieżeństwa — widok z boku", toward="prostopadle na bok konstrukcji wiaduktu",
    goal="TEKSTURA/KSZTAŁT: dźwigary, balustrada/ekran, przyczółki (beton), skarpa pod wiaduktem.")
add(key="bie_viaduct_under", kind="F", mode=("ring_along", RING_BIE, 300, 18), pri=1,
    place="Spód wiaduktu Andersa nad Rondem Bieżeństwa", toward="w górę i wzdłuż osi wiaduktu pod pomostem",
    h="1,5 m, lekko w górę", goal="Spód pomostu, podpory, przyczółki, oświetlenie pod wiaduktem. Zdjęcie pionowo w górę jako drugie.")
add(key="bie_island", kind="Z", mode=("ring_side", RING_BIE, 200, 28), pri=1,
    place="Wyspa środkowa Ronda Bieżeństwa — zieleń", toward="na wyspę (trawa, krzewy, drzewa)",
    goal="ZIELEŃ: gatunki, wysokość krzewów, obrzeże/krawężnik wyspy. Zbliżenie: liść/kora.")
add(key="bie_kerb", kind="D", mode=("abs", (567.0, -684.0), "ring"), pri=1,
    place="Przejście przy wlocie Ronda Bieżeństwa (przejścia oznaczone w OSM)", toward="PIONOWO W DÓŁ na krawężnik i pasy; potem z boku",
    h="1,3 m w dół + 1,5 m z boku", goal="DETAL: krawężnik obniżony i wysoki, studzienka, linia zatrzymania, pasy zebry. Skala: linijka/A4.")
add(key="bie_ext", kind="K", mode=("cam", "g3a_ext34_s0338"), cams=["g3a_ext34_s0338", "g3a_ext34_s0214", "g3a_ext34_s0040"],
    place="Ujęcia 3/4 „z boku auta” (tła pod widok zewnętrzny): przy rondzie, bramie, placu", toward="wg załącznika A",
    goal="Dopasowanie kadrów ext34 (gra: 3 m nad ziemią obok kabiny). Pieszo 1,5 m z tego samego miejsca. Tylko, jeśli czas pozwala.", pri=3)
add(key="bie_cars", kind="P", mode=("abs", (689.0, -690.0), "parking"), pri=2,
    place="Parking przy sklepie na wschód od Ronda Bieżeństwa", toward="rząd zaparkowanych aut z boku i 3/4",
    goal="TYPOWE AUTA zaparkowane (osobówki, dostawczaki, kombi): z boku prostopadle, z przodu i tyłu 3/4. BEZ tablic (zasłoń/odwróć kadr), bez ludzi i bez logo sklepu w kadrze.")
# ---- rampa i Andersa ----
add(key="onramp", kind="K", mode=("cam", "route_onramp_andersa"), cams=["route_onramp_andersa", "route_onramp_andersa_above"], access="road",
    place="Wjazd na Andersa (łącznica obok rampy zachodniej)", toward="wzdłuż łącznicy na zachód",
    goal="Dopasowanie kadru route_onramp_andersa (r4 blocker): nasyp, bariery, linie. Tylko z auta/pasażera lub z bezpiecznego pobocza.")
add(key="busstop_a1", kind="D", mode=("abs", (137.0, -471.0), "road_ref"), pri=2, access="road",
    place="Przystanek na Andersa (zatoka autobusowa, ok. s = 837 m)", toward="na wiatę, ławkę, słupek przystankowy (bez rozkładu z czytelnym tekstem)",
    goal="DETAL: wiata, słupek, krawężnik zatoki, asfalt zatoki z góry. Tylko z chodnika/zatoki, nigdy z jezdni.")
add(key="andersa_asphalt", kind="N", mode=("abs", (74.0, -437.0), "down"), pri=1, access="road",
    place="Przejście/zatoka przy Andersa (s ok. 900 m) — asfalt jezdni zużyty", toward="PIONOWO W DÓŁ",
    h="ok. 1,3 m", goal="NAWIERZCHNIA: asfalt zużyty droga główna (ziarno, łaty, linia krawędziowa). Skala: A4. Tylko z chodnika/zatoki.")
add(key="andersa_lamp", kind="L", mode=("abs", (14.0, -466.0), "lamp"), time="Z", pri=1, access="road",
    place="Andersa przy przystanku (s ok. 947 m) — latarnie", toward="na słup i oprawę (cała latarnia + zbliżenie oprawy)",
    goal="LATARNIA: cały słup (stopa, wysokość, wysięgnik), oprawa. ZMIERZCH (żarzy się, niebo jeszcze niebieskie) + wersja dzienna.")
add(key="andersa_series", kind="K", mode=("cam", "g3b_eye_s1232"), access="road",
    cams=["g3b_eye_s1232", "g3b_eye_s1282", "g3b_eye_s1332", "g3b_eye_s1382", "g3b_eye_s1432", "g3b_eye_s1482", "g3b_eye_s1532", "g3b_eye_s1582", "g3b_eye_s1632", "g3b_eye_s1682"],
    place="Andersa (3 pasy, trasa szybkiego ruchu): seria G3-B co 50 m (s = 1232…1682 m)",
    toward="wzdłuż Andersa w stronę Ronda Putry",
    h="2,5 m z kabiny / ok. 1,4 m z fotela pasażera", time="S",
    goal="NIE ZATRZYMUJ SIĘ NA JEZDNI. Najlepiej: WIDEO z fotela pasażera przez przednią szybę (czysta szyba, bez wycieraczek) od Ronda Bieżeństwa do Putry; kadry wyciągamy z wideo do współrzędnych z załącznika A.")
add(key="andersa_green", kind="Z", mode=("route", 1290, -22, "left"), pri=2, access="road",
    place="Pas zieleni między Andersa a blokami (s ok. 1290 m)", toward="na pas zieleni: trawa, krzewy, drzewa",
    goal="ZIELEŃ: trawa (zbliżenie z góry), krzewy, drzewa (pień + kora z bliska, korona całości). Z chodnika od strony bloków.")
add(key="blocks", kind="F", mode=("standoff", (-278, -272), 34), pri=1,
    place="Blok mieszkalny przy Andersa (ok. 660 m², 14 m wg LoD1), od strony ulicy bocznej", toward="prostopadle na elewację",
    goal="TEKSTURA FASADY: tynk/płytka, okna, balkony, kolory pasów. Całość + zbliżenia. Stań na chodniku/parkingu (nie przy Andersa). Bez ludzi, bez tablic.")
add(key="blocks2", kind="F", mode=("standoff", (-396, -359), 40), pri=2,
    place="Bloki wielorodzinne na północ od Andersa (ok. 20 m wys.)", toward="prostopadle na elewację (3-4 piętra)",
    goal="TEKSTURA FASADY: wielka płyta/tynk, klatki schodowe, loggie; kolory (zapisz opisowo, jeśli zdjęcie ma dominantę).")
add(key="fire_station", kind="F", mode=("standoff", (-236, -146), 30), pri=1,
    place="Straż pożarna przy Andersa (ok. 1300 m², 6,5 m wg LoD1)", toward="prostopadle na front z bramami garażowymi",
    goal="TEKSTURA FASADY: elewacja, bramy garażowe, wieża/suszarnia (jeśli jest). Bez logo/herbu w zbliżeniu, bez pojazdów z numerami.")
add(key="fire_signal", kind="L", mode=("abs", (-278.0, -197.0), "signal"), pri=2, access="road",
    place="Sygnalizator awaryjny straży na Andersa (s ok. 1337 m)", toward="na sygnalizator i słup/wysięgnik",
    goal="LATARNIA/ZNAK: sygnalizator „emergency” — słup, głowice, tablica tła. Z chodnika/zatoki, nie z jezdni.")
add(key="andersa_ext", kind="K", mode=("cam", "g3b_ext34_s1272"), cams=["g3b_ext34_s1272", "g3b_ext34_s1482", "g3b_ext34_s1658"], access="road", pri=3,
    place="Ujęcia 3/4 przy Andersa i na łącznicy (współrzędne w załączniku A)", toward="wg załącznika A",
    goal="Tylko jeśli bezpieczne miejsce (zatoka/chodnik). Dopasowanie kadrów g3b_ext34_*.")
add(key="ramp_tys", kind="K", mode=("cam", "g3b_eye_s1482"), cams=["g3b_eye_s1482"], access="road", pri=3,
    place="Zjazd z Andersa na łącznicę do Al. Tysiąclecia (s ok. 1427-1569 m)", toward="wzdłuż łącznicy",
    goal="Opcja: kadr z wideo przez szybę (patrz seria G3-B).")
add(key="busstop_link", kind="D", mode=("abs", (-438.0, -36.0), "road_ref"), pri=2, access="road",
    place="Przystanek przy łączniku Andersa → Putry (s ok. 1567 m)", toward="na wiatę/słupek",
    goal="DETAL: wiata, słupek, krawężnik. Z chodnika.")
# ---- Rondo Putry ----
add(key="putry_approach", kind="K", mode=("cam", "route_putry_approach"), cams=["route_putry_approach", "driver_andersa_to_putry"], access="road",
    place="Podejście Andersa do Ronda Putry (s ok. 1540 m)", toward="na rondo i portal z tablicami (wg E-1)",
    goal="Dopasowanie kadru route_putry_approach i driver_andersa_to_putry. Pasażer przez szybę lub z bezpiecznego chodnika.")
add(key="putry_photomatch", kind="K", mode=("cam", "g3b_rondo_putry_approach"), cams=["g3b_rondo_putry_approach"],
    place="Z pobocza w stronę Ronda Putry — photo match (CC0 7204_May_2021)", toward="w górę drogi na portal i wiadukt",
    goal="DOPASOWANIE KADRU (photo_match). Wysokość 1,6 m z pobocza wg komentarza w pliku kamer. Właściciel może przesunąć miejsce.")
add(key="putry_entry_signs", kind="L", mode=("cam", "route_putry_entry_signs"), cams=["route_putry_entry_signs"], access="road",
    place="12 m przed wlotem na Rondo Putry — znaki A-7 + C-12 (+ C-9)", toward="na tablice przed wlotem",
    goal="ZNAKI: cały zestaw na słupku, tył słupka i mocowanie, wysokość tablicy; potem każda tablica z bliska (stan, odblask).")
add(key="putry_ring_approach", kind="K", mode=("cam", "g3b_rondo_put_approach"), cams=["g3b_rondo_put_approach", "g3b_eye_s1632"],
    place="30 m przed wlotem na Rondo Putry", toward="na środek ronda",
    goal="Dopasowanie kadru g3b_rondo_put_approach (FOV 65°).")
add(key="putry_above", kind="K", mode=("cam", "putry_above"), cams=["putry_above", "g3b_rondo_put_above"], access="road", pri=3, h="ok. 12-45 m: tylko jeśli jest dostęp",
    place="Rondo Putry z góry (dwupoziomowe: Andersa nad pierścieniem)", toward="na rondo z góry",
    goal="OPCJONALNIE z kładki/wiaduktu (chodnik) lub zaplecza budynku — tylko legalnie. Dron NIE.")
add(key="putry_viaduct", kind="F", mode=("ring_side", RING_PUT, 32, 40), pri=1,
    place="Wiadukt Andersa/Maczka nad Rondem Putry — widok z boku", toward="prostopadle na bok wiaduktu",
    goal="Dźwigary, balustrada/ekran, przyczółki, skarpa. Kolory betonu i stali.")
add(key="putry_under", kind="F", mode=("ring_along", RING_PUT, 302, 18), pri=1,
    place="Spód wiaduktu nad Rondem Putry", toward="w górę wzdłuż osi pod pomostem",
    h="1,5 m, lekko w górę", goal="Spód pomostu, podpory, oświetlenie, plamy/zacieki.")
add(key="putry_island", kind="Z", mode=("ring_side", RING_PUT, 212, 30), pri=1,
    place="Wyspa środkowa i pasy zieleni Ronda Putry", toward="na wyspę",
    goal="ZIELEŃ: berberys i żywopłoty (przycięta forma, kolor liści listopad/jesień), trawa, drzewa: pień + kora z bliska, korona całości. Zbliżenie liści na tle białej kartki (opcj.).")
add(key="putry_zebra", kind="N", mode=("abs", (-543.0, 65.0), "down"), pri=1, access="road",
    place="Zebra / przejście sygnalizowane przy Rondzie Putry (Al. Tysiąclecia, s ok. 1715 m)", toward="PIONOWO W DÓŁ na pasy; potem z boku wzdłuż pasów",
    h="1,3 m w dół + 1,5 m z boku", goal="NAWIERZCHNIA: zebra (szerokość i odstęp pasów, wytarcie farby), linia zatrzymania, strzałki. Skala: linijka. Tylko, gdy ruch stoi lub z chodnika.")
add(key="putry_signal", kind="L", mode=("abs", (-543.0, 65.0), "signal"), pri=2, access="road",
    place="Sygnalizator przy zebrze Rondo Putry", toward="na słup sygnalizatora i głowice",
    goal="ZNAK/LATARNIA: słup, głowice, osłony, przycisk dla pieszych (bez ludzi). Z chodnika.")
add(key="putry_lamp", kind="L", mode=("abs", (-525.0, 38.0), "lamp"), time="Z", pri=1, access="road",
    place="Rondo Putry — latarnie nad rondem", toward="na latarnię (cały słup) i na oświetlone rondo",
    goal="LATARNIA ZMIERZCH: kolor światła (żółte sodowe / białe LED), rozstaw, wysokość. Statyw lub oprzyj telefon; 2-3 ekspozycje.")
add(key="putry_kerb", kind="D", mode=("abs", (-527.0, 39.0), "kerb"), pri=1, access="road",
    place="Krawężnik wyspy dzielącej / wlot Ronda Putry", toward="na krawężnik z boku i z góry",
    goal="DETAL: krawężnik (kamień/beton, wysokość), studzienka/wpust, szczelina, ubytki, nawierzchnia przy krawężniku.")
# ---- Al. Tysiaclecia ----
add(key="tys_start", kind="K", mode=("route", 1760, 0, "fwd"), pri=2, access="road",
    place="Al. Tysiąclecia Państwa Polskiego tuż za Rondem Putry (s ok. 1760 m)", toward="na północ wzdłuż al. Tysiąclecia",
    goal="Pasy, pobocze/chodnik, latarnie, pierwszy znak/tablica DK8/DK19. Z fotela pasażera lub chodnika.")
add(key="tys_sign", kind="L", mode=("route", 1860, -9, "right"), pri=1, access="road",
    place="Al. Tysiąclecia: tablica kierunkowa DK8/DK19 (jeśli stoi w pierwszych 500 m)", toward="na tablicę kierunkową",
    goal="ZNAK: tablica kierunkowa z nazwami miast — czytelność, kolor tła, krój pisma; tył słupa; wysokość. BEZ aut w kadrze z tablicami.")
add(key="tys_trees", kind="Z", mode=("route", 1960, -12, "right"), pri=2, access="road",
    place="Pas zieleni przy Al. Tysiąclecia", toward="na szpaler drzew",
    goal="ZIELEŃ: drzewa — pień z bliska (kora) + cała korona + liść; trawnik (z góry), rów/pobocze.")
add(key="tys_asphalt", kind="N", mode=("route", 2000, -6, "down"), pri=1, access="road",
    place="Al. Tysiąclecia: asfalt przy zatoczce/poboczu", toward="PIONOWO W DÓŁ",
    h="ok. 1,3 m", goal="NAWIERZCHNIA: asfalt droga krajowa (nowszy), linia krawędziowa ciągła i przerywana. Skala: A4.")
add(key="dk_exit", kind="K", mode=("cam", "dk8_dk19_exit"), cams=["dk8_dk19_exit"], access="road",
    place="Al. Tysiąclecia na północ — wylot z miasta (DK8/DK19, s ok. 2250 m)", toward="na północ, wzdłuż trasy",
    goal="Dopasowanie kadru dk8_dk19_exit. Z fotela pasażera przez szybę lub z bezpiecznego miejsca.")
# ---- ogolne (niezalezne od lokalizacji, ale z punktem sugerowanym) ----
add(key="pavers", kind="N", mode=("abs", (583.0, -655.0), "down"), pri=1,
    place="Chodnik (kostka/płyty) — dowolne miejsce przy ul. dojazdowej/rondzie, najlepiej koło przejścia", toward="PIONOWO W DÓŁ",
    h="ok. 1,3 m", goal="NAWIERZCHNIA: kostka brukowa i płyty chodnikowe — 3 ujęcia z góry (czysty fragment, spoina/fuga, zużycie), skala A4/linijka. Zapisz, czy kostka (np. szara/czerwona) — opis w nazwie.")
add(key="manhole", kind="D", mode=("abs", (557.0, -693.0), "down"), pri=2,
    place="Studzienka kanalizacyjna i wpust uliczny (dowolna, w chodniku/poboczu)", toward="PIONOWO W DÓŁ + 1 z ukosa",
    h="ok. 1,3 m", goal="DETAL: studzienka (pokrywa, wzór, ramka), wpust uliczny (kratka). Skala: moneta/linijka.")
add(key="pole_sign", kind="D", mode=("abs", (576.0, -689.0), "sign"), pri=2,
    place="Słupek prowadzący/blokujący i znak pionowy przy rondzie (stan i mocowanie)", toward="na słupek i na znak (przód + tył)",
    goal="DETAL: słupek (kolor, odblask, wysokość), tył znaku i obejma, wysokość montażu. Nie zbliżaj logo/tablic rej.")

# ---------------------------------------------------------------- pozycje


def resolve(sh):
    m = sh["mode"]
    t = m[0]
    az = None
    if t == "cam":
        pos, az, c = cam_pose(m[1])
        sh["fov"] = c["fov_deg"]
    elif t == "route":
        _, s, lat, d = m
        p, hdg = route_at(s)
        pos = offset(p, hdg, lat)
        az = {"fwd": hdg, "left": (hdg - 90) % 360, "right": (hdg + 90) % 360, "down": None}[d] if d != "down" else None
        if d == "down":
            sh["down"] = True
            az = hdg
    elif t == "route_target":
        _, s, lat, tgt = m
        p, hdg = route_at(s)
        pos = offset(p, hdg, lat)
        az = bearing(pos, tgt)
    elif t == "standoff":
        tgt, dist = m[1], m[2]
        q = RLINE.interpolate(RLINE.project(Point(tgt)))
        v = (q.x - tgt[0], q.y - tgt[1])
        n = math.hypot(*v)
        dist = min(dist, max(n, 8))
        pos = (tgt[0] + v[0] / n * dist, tgt[1] + v[1] / n * dist)
        az = bearing(pos, tgt)
    elif t == "ring_side":
        cen, ang, dist = m[1], m[2], m[3]
        a = math.radians(ang)
        pos = (cen[0] + math.sin(a) * dist, cen[1] + math.cos(a) * dist)
        az = bearing(pos, cen)
    elif t == "ring_along":
        cen, dir_az, dist = m[1], m[2], m[3]
        a = math.radians(dir_az)
        pos = (cen[0] - math.sin(a) * dist, cen[1] - math.cos(a) * dist)
        az = dir_az % 360
    elif t == "abs":
        pos = m[1]
        hint = m[2]
        q = RLINE.interpolate(RLINE.project(Point(pos)))
        az = bearing(pos, (q.x, q.y))
        if hint == "down":
            sh["down"] = True
        # dla pozostalych: patrz w strone osi trasy (WORKING_VALUE), wlasciciel dobiera kadr
        if hint in ("ring", "parking", "road_ref", "lamp", "signal", "sign", "kerb"):
            az = (az + 180) % 360 if hint in ("lamp", "kerb") else az
    sh["pos"], sh["az"] = pos, az
    sh["s"] = RLINE.project(Point(pos))
    sh["lat"], sh["lon"] = wgs(pos)
    sh["dist_route"] = RLINE.distance(Point(pos))


for sh in SHOTS:
    resolve(sh)
SHOTS.sort(key=lambda x: x["s"])
for i, sh in enumerate(SHOTS, 1):
    sh["nr"] = i

SECTIONS = [
    ("A", "Kwadrat Park i droga dojazdowa (s 0-290 m) — teren prywatny", -1, 295),
    ("B", "Rondo Pamięci Bieżeństwa i wiadukt (s 295-480 m)", 295, 480),
    ("C", "Łącznica i Andersa (s 480-1540 m) — trasa szybkiego ruchu", 480, 1540),
    ("D", "Rondo Putry (s 1540-1755 m)", 1540, 1755),
    ("E", "Al. Tysiąclecia → DK8/DK19 (s 1755-2400 m)", 1755, 1e9),
]


def osm_link(lat, lon, z=19):
    return f"https://www.openstreetmap.org/?mlat={lat:.6f}&mlon={lon:.6f}#map={z}/{lat:.6f}/{lon:.6f}"


def mly_link(lat, lon):
    return f"https://www.mapillary.com/app/?lat={lat:.6f}&lng={lon:.6f}&z=17"


KIND_PL = {"K": "kadr gate3", "F": "fasada", "N": "nawierzchnia", "Z": "zieleń", "L": "latarnia/znak", "P": "auta", "D": "detal"}
ACCESS_PL = {"pub": "", "priv": " **[PRYWATNE]**", "road": " **[RUCH]**"}
TIME_PL = {"S": "S", "Z": "Z+S", "N": "S"}


def row(sh):
    az = sh["az"]
    down = sh.get("down")
    dirtxt = sh["toward"] + (f" (azymut {az:.0f}° {compass(az)}, pod stopami: kierunek trasy)" if down else f" (azymut {az:.0f}° {compass(az)})")
    cams_txt = (" Kamery: `" + "`, `".join(sh["cams"]) + "`.") if sh["cams"] else ""
    return (f"| {sh['nr']} | {KIND_PL[sh['kind']]}{ACCESS_PL[sh['access']]} | {sh['place']}<br>`{sh['lat']:.6f}, {sh['lon']:.6f}` "
            f"(s={sh['s']:.0f} m) | {dirtxt} | {sh['h']} | {TIME_PL[sh['time']]} | {sh['goal']}{cams_txt} | "
            f"{mly_cell(sh)} | [OSM]({osm_link(sh['lat'], sh['lon'])}) · [mapa Mapillary]({mly_link(sh['lat'], sh['lon'])}) | P{sh['pri']} |")


COV_FILE = REG / "generated/photo_coverage.json"
COV = {int(k): v for k, v in json.load(open(COV_FILE, encoding="utf-8")).items()} if COV_FILE.exists() else {}
STATUS_PL = {"DOBRE": "DOBRE", "SLABE": "SŁABE", "BRAK": "BRAK"}


def cov_of(sh):
    """Ocena pokrycia Mapillary (reczna, z miniatur). Ujecia bez punktu (pod stopami) = BRAK."""
    return COV.get(sh["nr"]) or {"status": "BRAK", "note": "ujęcie z góry/pod stopami: Mapillary nie pokrywa"}


def mly_cell(sh):
    c = cov_of(sh)
    st = STATUS_PL[c["status"]]
    if c.get("best"):
        return f"**{st}** [{c['dist']:.0f} m, {c['dev']:.0f}°, {c['date'][:4]}]({c['page']})"
    return f"**{st}**"


def gaps_section():
    rows = []
    for sh in SHOTS:
        c = cov_of(sh)
        if c["status"] == "DOBRE":
            continue
        az = sh["az"]
        why = c.get("note", "")
        if c.get("best"):
            why = f"najlepsze {c['dist']:.0f} m / {c['dev']:.0f}° / {c['date'][:4]}" + (f"; {why}" if why else "")
        need = {"F": "fasada prostopadle (tekstura)", "N": "nawierzchnia z góry", "Z": "zmierzch/latarnie", "K": "kadr gate3",
                "L": "latarnia/znak", "D": "detal", "P": "auta"}[sh["kind"]]
        rows.append(f"| {sh['nr']} | {need}{ACCESS_PL[sh['access']]} | {sh['place']} | `{sh['lat']:.5f}, {sh['lon']:.5f}` | {az:.0f}° | "
                    f"{STATUS_PL[c['status']]} | {why} |")
    n = {k: sum(1 for s in SHOTS if cov_of(s)["status"] == k) for k in ("DOBRE", "SLABE", "BRAK")}
    head = (f"## Luki w referencjach (D43)\n\n"
            f"Właściciel **nie robi własnych zdjęć** (D43). Pokrycie Mapillary sprawdzono API (zdjęcia 2048 px, bez panoram; "
            f"promień 30 m, azymut ±40°, a dla braków 70 m / ±60°) i oceniono z miniatur: **DOBRE {n['DOBRE']}**, **SŁABE {n['SLABE']}**, **BRAK {n['BRAK']}** z {len(SHOTS)}. "
            f"Kryterium DOBRE: ≤ 15 m, azymut ±30°, ostre, ≥ 2019, bez prześwietlenia. Poniższe ujęcia trzeba uzupełnić z innych otwartych źródeł "
            f"(KartaView, Panoramax, Wikimedia Commons, Openverse, GUGiK) lub zostają jako proceduralne z OSM/BDOT10k. "
            f"Mapillary (kamery samochodowe) **nie zastąpi** tekstur fasad z bliska, nawierzchni z góry ani zmierzchu: te ujęcia i tak są w tabeli. "
            f"Dane maszynowe: `artifacts/refs/coverage.json`, `Data/Regions/bialystok-industrial-c/generated/photo_coverage.json`. "
            f"Zdjęcia Mapillary = tylko referencje (nie wchodzą do builda, ADR 0065).\n\n"
            f"| Nr | Czego brakuje | Miejsce | WGS84 | Azymut | Mapillary | Uwagi |\n|---|---|---|---|---|---|---|")
    return head + "\n" + "\n".join(rows) + "\n"


def write_coverage_json(path):
    out = []
    for sh in SHOTS:
        c = cov_of(sh)
        out.append({"id": f"p{sh['nr']:02d}", "nr": sh["nr"], "key": sh["key"], "lat": round(sh["lat"], 7), "lon": round(sh["lon"], 7),
                    "azimuth": round(sh["az"], 1), "kind": sh["kind"], "mapillary_status": c["status"],
                    "best_image_id": c.get("best"), "best_dist_m": c.get("dist"), "best_dev_deg": c.get("dev"),
                    "best_date": c.get("date"), "other_image_ids": c.get("others", []), "note": c.get("note", "")})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"shots": out}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def appendix_rows():
    out = []
    order = []
    for cid, c in cams.items():
        if c.get("type") == "ortho":
            continue
        pos, az, _ = cam_pose(cid)
        order.append((RLINE.project(Point(pos)), cid, c, pos, az))
    order.sort()
    for s, cid, c, pos, az in order:
        lat, lon = wgs(pos)
        nr = [str(sh["nr"]) for sh in SHOTS if cid in sh["cams"] or sh["mode"] == ("cam", cid)]
        eye = c["pos"][2]
        out.append(f"| `{cid}` | {', '.join(nr) or '—'} | `{lat:.6f}, {lon:.6f}` | {az:.0f}° {compass(az)} | {c['fov_deg']:.0f}° | "
                   f"{s:.0f} | [OSM]({osm_link(lat, lon)}) · [Mapillary]({mly_link(lat, lon)}) |")
    return out


# ---------------------------------------------------------------- mapka


def draw_map(path):
    g = json.load(open(REG / "roads.graph.json", encoding="utf-8"))
    b = json.load(open(REG / "buildings.geojson", encoding="utf-8"))
    colors = {"trunk": "#c0392b", "trunk_link": "#d98880", "tertiary": "#7f8c8d", "tertiary_link": "#95a5a6",
              "secondary": "#7f8c8d", "service": "#b2bec3", "residential": "#b2bec3", "unclassified": "#b2bec3"}
    widths = {"trunk": 2.6, "trunk_link": 1.8, "tertiary": 1.6, "tertiary_link": 1.3}
    kcol = {"K": "#1f77b4", "F": "#e67e22", "N": "#555555", "Z": "#2e8b57", "L": "#8e44ad", "P": "#16a085", "D": "#b8860b"}

    fig = plt.figure(figsize=(20, 12), dpi=110)
    gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1, 1], hspace=0.12, wspace=0.08)
    axo = fig.add_subplot(gs[:, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[1, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1, 2])
    polys = []
    for f in b["features"]:
        gm = translate(shape(f["geometry"]), -OX, -OY)
        for pg in (gm.geoms if gm.geom_type == "MultiPolygon" else [gm]):
            polys.append(list(pg.exterior.coords))
    for ax in (axo, ax1, ax2, ax3, ax4):
        ax.set_aspect("equal")
        ax.set_facecolor("#fbfaf6")
        for pl in polys:
            ax.add_patch(MplPoly(pl, closed=True, fc="#d9d4c7", ec="#b9b3a3", lw=0.3, zorder=1))
        for e in g["edges"]:
            gm = e["geometry"]
            pts = gm["coordinates"] if isinstance(gm, dict) else gm
            hw = e["attrs"]["highway"]["v"]
            xs = [p[0] - OX for p in pts]
            ys = [p[1] - OY for p in pts]
            ax.plot(xs, ys, color=colors.get(hw, "#b2bec3"), lw=widths.get(hw, 0.9), solid_capstyle="round", zorder=2)
        ax.plot([p[0] for p in RPTS], [p[1] for p in RPTS], color="#111", lw=1.0, ls=(0, (4, 2)), zorder=3)
        ax.set_xticks([])
        ax.set_yticks([])
    # ujecia
    for ax, big in ((axo, False), (ax1, True), (ax2, True), (ax3, True), (ax4, True)):
        for sh in SHOTS:
            x, y = sh["pos"]
            ax.scatter([x], [y], s=(150 if big else 95), c=kcol[sh["kind"]], ec="white", lw=1, zorder=6)
            ax.annotate(str(sh["nr"]), (x, y), ha="center", va="center", fontsize=(7.5 if big else 6), color="white", weight="bold", zorder=7)
            if big and sh["az"] is not None and not sh.get("down"):
                a = math.radians(sh["az"])
                ax.annotate("", xy=(x + math.sin(a) * 22, y + math.cos(a) * 22), xytext=(x, y),
                            arrowprops=dict(arrowstyle="-|>", color=kcol[sh["kind"]], lw=1.4), zorder=5)
    # kadrowanie
    axo.set_xlim(-900, 960)
    axo.set_ylim(-1000, 800)
    axo.set_title("Trasa startowa: Kwadrat Park -> Andersa -> Rondo Putry -> DK8/DK19 (siatka: lokalne E,N; N u góry)", fontsize=11)
    INS = [(ax1, (560, 790, -640, -330), "1. Kwadrat Park: plac, rampy, brama"),
           (ax2, (470, 660, -790, -620), "2. Rondo Bieżeństwa i wiadukt"),
           (ax3, (-480, -150, -430, -90), "3. Andersa: blok, straż pożarna, łącznica"),
           (ax4, (-650, -420, -40, 130), "4. Rondo Putry i początek Al. Tysiąclecia")]
    for ax, (xa, xb, ya, yb), ttl in INS:
        ax.set_xlim(xa, xb)
        ax.set_ylim(ya, yb)
        ax.set_title(ttl + " (strzałka = kierunek patrzenia)", fontsize=9)
        axo.plot([xa, xb, xb, xa, xa], [ya, ya, yb, yb, ya], color="#444", lw=1.0)
        axo.annotate(ttl[0], (xa, yb), fontsize=11, weight="bold", color="#444", xytext=(-10, 4), textcoords="offset points")
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="", color=kcol[k], label=v, markersize=9) for k, v in KIND_PL.items()]
    handles.append(Line2D([], [], color="#111", ls=(0, (4, 2)), label="trasa startowa (2,4 km)"))
    handles.append(Line2D([], [], color="#c0392b", lw=2.6, label="droga krajowa (trunk)"))
    axo.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.95)
    fig.text(0.01, 0.005, "Dane: © OpenStreetMap contributors (ODbL); budynki: GUGiK BDOT10k / OSM (geoportal.gov.pl). Bez kafli zewnętrznych, bez Google. Numery = tabela w PHOTO-LIST.md.",
             fontsize=8, color="#444")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- markdown

TEMPLATE_HEAD = (Path(__file__).parent / "photo_list_head.md").read_text(encoding="utf-8")
TEMPLATE_TAIL = (Path(__file__).parent / "photo_list_tail.md").read_text(encoding="utf-8")


def build():
    first, rest = TEMPLATE_HEAD.replace("{{N}}", str(len(SHOTS))).split("\n", 1)
    banner = ("\n> **D43: właściciel nie robi własnych zdjęć.** Sekcje 1, 2, 4, 5 i Załącznik B poniżej opisują pierwotny plan i są **nieaktualne** "
              "(zostają jako opis standardu ujęć dla innych źródeł). Aktualne zadanie: sekcja „Luki w referencjach”.\n")
    out = [first, banner, gaps_section(), rest]
    hdr = "| Nr | Typ | Miejsce i współrzędne WGS84 | Kierunek patrzenia | Wys. | Pora | Cel / co ma być na zdjęciu | Mapillary | Mapy | Pri |\n|---|---|---|---|---|---|---|---|---|---|"
    for code, title, lo, hi in SECTIONS:
        sec = [s for s in SHOTS if lo <= s["s"] < hi] if lo >= 0 else [s for s in SHOTS if s["s"] < hi]
        if not sec:
            continue
        out.append(f"\n### Etap {code}. {title}\n")
        out.append(hdr)
        out.extend(row(s) for s in sec)
    out.append("\n## Załącznik A. Wszystkie pozy kamer gate3 / photo_match / kontrolnych (te same pozy co w grze)\n")
    out.append("Wysokość kamery w grze: 2,5 m (oko kierowcy), kamery `*_above` ok. 12-45 m, `ext34` ok. 3 m. Pieszo robisz 1,5 m; różnicę wysokości policzymy przy dopasowaniu. Wartości FOV pionowe wg Unity.\n")
    out.append("| Id kamery | Nr ujęcia | WGS84 | Azymut | FOV | s [m] | Mapy |\n|---|---|---|---|---|---|---|")
    out.extend(appendix_rows())
    out.append(TEMPLATE_TAIL)
    return "\n".join(out)


def export_points(path):
    """Punkty WGS84 + azymut dla tools/refs/mapillary_fetch.py --points (ujecia 'z gory' pomijane)."""
    pts = [{"id": f"p{sh['nr']:02d}", "nr": sh["nr"], "kind": sh["kind"], "lat": round(sh["lat"], 7),
            "lon": round(sh["lon"], 7), "azimuth": round(sh["az"], 1)}
           for sh in SHOTS if sh["az"] is not None and not sh.get("down")]
    path.write_text(json.dumps({"points": pts}, indent=1) + "\n", encoding="utf-8")
    return pts


if __name__ == "__main__":
    export_points(REG / "generated/photo_points.json")
    write_coverage_json(REPO / "artifacts/refs/coverage.json")
    draw_map(REPO / "docs/owner/img/photo-list-map.png")
    (REPO / "docs/owner/PHOTO-LIST.md").write_text(build(), encoding="utf-8")
    print(len(SHOTS), "ujec")
    kinds = {}
    for s in SHOTS:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    print(kinds)
    for s in SHOTS:
        print(s["nr"], s["key"], round(s["s"]), round(s["dist_route"]), f"{s['lat']:.5f},{s['lon']:.5f}", None if s["az"] is None else round(s["az"]))
