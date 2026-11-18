# SIGNS — oznakowanie pętli S8 ↔ DW671 ↔ Tykocin (dla ciężarówki)

Zakres: 15 kafli pętli (D82) + pierścień ±2 km. Dane: `signs.json` (OSM API 0.6, surowe w `raw/osm/manifest.json`, ODbL 1.0, © OpenStreetMap contributors).
Weryfikacja zdjęciowa: **UNVERIFIED** — Mapillary wymaga tokenu właściciela (jak w G10 / MAP-DECISIONS A11); Panoramax (CC BY 4.0) ma w bbox pętli tylko pojedyncze zdjęcia, bez detekcji znaków. Każdy znak z OSM poniżej ma status OSM-only.

## 1. Co jest w OSM (zmierzone: liczba way/węzłów z tagami)

| Element | OSM (ten research) | Uwagi |
|---|---|---|
| S8 (motorway) | 99 way w bbox (w tym 71 w 15 kaflach): `maxspeed=120` 99/99, `maxspeed:hgv=80` 99/99, `toll:hgv=yes` 95/99 (4 bez tagu = luka OSM), `surface=asphalt`, `lanes` 2 (68) / 3 (31) | oś S8 ~21,2 km (obie jezdnie 43,1 km) |
| Łącznice węzłów (motorway_link) | `maxspeed`: 60×28, 50×21, 40×7, 70×2, 30×2, brak 86; `lanes` 1×86, 2×41 | długości w `junctions.json` (geometria OSM) |
| DW671 (secondary) | `maxspeed`: 90×6, 70×2, 60×1, 50×1, 40×2, brak 31; `lanes` 2×20, 1×6; `width` — brak tagów | odcinki 90 km/h poza zabudową, 50/40 w zabudowie (D-42/D-43) |
| Znaki pionowe jako węzły (`traffic_sign`) | 6 węzłów w 15 kaflach: `PL:A-2` (wjazd na pas awaryjny? — zakaz postoju/wjazdu, przy Jeżewie, węzeł 3054467143, s8-12), `PL:B-18` + `maxweight=10` (przy Żółtkach, s8-02, node 3012179430), 3× `maxspeed` (40/50/60), 1× `overtaking` (zakaz wyprzedzania, Jeżewo) | **rzadkie pokrycie** — większość znaków w terenie nie ma tagów OSM |
| Zakazy tonażowe na drogach lokalnych | 6 way `tertiary` z `maxweight=10` w s8-01/s8-02 (łączniki w stronę Choroszczy: way 297342246, 888490257, 297345991, 888490258, 1293065571, 1293065572; razem 1395 m) — zgodne z B-18 (10 t) w tym rejonie | prawdopodobnie obiekt mostowy — przyczyna do weryfikacji (UNVERIFIED) |
| `maxaxleload` | 11,5 t na 101 way, 10 t na 11 way (w bbox) | limit ogólny dróg krajowych (Dz.U. 2011 nr 222 poz. 1321, jak w ADR 0203) |
| e-TOLL | `toll:hgv=yes` na S8 | patrz §3 |

## 2. Wymagania przepisów (cytaty) vs dane

| Wymaganie | Przepis (wydanie) | Co wynika dla pętli | Status w OSM |
|---|---|---|---|
| Limit 120 km/h na S8, 80 km/h dla >3,5 t | PoRD, t.j. **Dz.U. 2024 poz. 1251**, art. 20 ust. 3 pkt 2 lit. a (80 km/h ekspresowa poza obszarem zabudowanym dla pojazdu >3,5 t) i ust. 2 pkt 1 lit. a (120); w obszarze zabudowanym 50 (ust. 1) | B-33 120 na S8; dla ciężarówki efektywnie 80 (przepis, nie tylko znak); na DW671 poza zabudową 90→dla >3,5 t 70 (art. 20 ust. 3 pkt 2 lit. b), w zabudowie 50 | OSM zgodne (120/80, 90/70/50) |
| Znaki zakazu: definicje, wymiary, wysokość | rozp. ws. znaków i sygnałów drogowych, t.j. **Dz.U. 2019 poz. 2310**; rozp. ws. szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń BRD i warunków ich umieszczania na drogach, t.j. **Dz.U. 2019 poz. 2311** (zm. m.in. Dz.U. 2021 poz. 2066); PDF 525 str.: `api.sejm.gov.pl/eli/acts/DU/2019/2311/text.pdf` | B-5 (zakaz wjazdu >X t), B-18/B-19/B-20 (ograniczenia), B-33 (prędkość), D-42/D-43 (obszar zabudowany / koniec), A-7 (ustąp pierwszeństwa na węzłach), znaki kierunku E-* | tylko 6 węzłów traffic_sign w pętli — reszta UNVERIFIED |
| Powtórzenie B-33 po skrzyżowaniu | Dz.U. 2019 poz. 2310 § 27 ust. 1 | na każdym wlocie łącznicy/wyjściu z węzła | nie w OSM — do postawienia w świecie wg D63 (układ dróg) |
| Węzły S8 = typ WA (brak przecięć w poziomie na jezdniach głównych) | rozp. MI z 24.06.2022 r. ws. przepisów techniczno-budowlanych dotyczących dróg publicznych, **Dz.U. 2022 poz. 1518** (tekst: `eli.gov.pl/api/acts/DU/2022/1518/text.html`, pobrany w tej sesji), dział III rozdział „Węzły drogowe”: z drogą klasy A/S projektuje się węzeł typu WA; § 63–64: pasy wyłączania/włączania równoległe, długość wg opóźnienia 1,5 m/s² (klasa A/S) | 5 węzłów na pętli (Białystok Zachód, Choroszcz, Tykocin, Rzędziany, Jeżewo) — wszystkie jako WA/trąbka (ESTIMATED z topologii OSM, `junctions.json`) | topologia OSM zgodna |
| Przekrój S8: 2/2, 2/3, 2/4; pas 3,50 m; pas awaryjny 2,50 m; pas dzielący z barierą | jw. Dz.U. 2022 poz. 1518: § 15 (przekrój klasy S), § 17 ust. 1 pkt 2 (pas ruchu 3,50 m), § 23 + przepis o części pobocza o nawierzchni twardej (klasa S: standardowo 2,50 m), § 16 ust. 2 (pas dzielący na drodze >50 km/h ze strefą bez przeszkód lub barierą ochronną) | pomiar z ortofoto (`xsec/`): jezdnia 2-pasowa ~7,0–7,5 m + pobocze utwardzone ~2,5 m, pas dzielący ~4–4,8 m (oś–oś 12,27 m) ze stalową barierą — **zgodne z przepisem** | pomierzone |
| MOP | ustawa o drogach publicznych + Dz.U. 2022 poz. 1518 (miejsce obsługi podróżnych projektuje się standardowo) | 2 MOP na pętli (Radule, Złotoria) — `mop.json` | OSM |
| e-TOLL na S8 | ustawa z 21.03.1985 r. o drogach publicznych (przepisy o opłacie elektronicznej za przejazd drogami krajowymi); wykaz odcinków: rozp. Rady Ministrów z 8.01.2026 r. (zmiany od 1.02.2026, gov.pl/KAS — S8 na liście dróg ekspresowych objętych e-TOLL); stawki 2026: obwieszczenie MI z 3.12.2025; lista: etoll.gov.pl | opłata za cały odcinek pętli S8 (element ekonomii gry) | `toll:hgv=yes` 95/99 way |

## 3. Lista UNVERIFIED do potwierdzenia (lider / właściciel)

1. Wszystkie znaki pionowe poza 6 węzłami OSM (B-33 wartości na łącznicach, D-42/D-43 na wjazdach do wsi: Żółtki, Babino, Rzędziany, Broniszewo, Tykocin-Kolonia, Zimna Woda, Jeżewo Stare/Nowe, Pajewo; A-7 na wlotach łącznic; E-* kierunkowe na węzłach; tablice e-TOLL) — brak zdjęć (Mapillary bez tokena).
2. Przyczyna `maxweight=10` na 6 way tertiary przy Choroszczy (s8-01/s8-02) — prawdopodobnie obiekt mostowy; do sprawdzenia na ortofoto przy budowie kafla.
3. 4 way S8 bez `toll:hgv` — luka tagowania OSM, przepisowo S8 jest płatna (e-TOLL) na całości.
4. B-18 (10 t) przy Żółtkach — zgodny z tagami way, ale fizyczny znak: UNVERIFIED.
5. Dokładne długości pasów włączania/wyłączania per węzeł wg Dz.U. 2022 poz. 1518 § 63–64 (zależą od prędkości projektowej 120 km/h i geometrii) — w danych są długości łącznic z OSM (`junctions.json`), rozbicie na pas zwalniania/klina/przyspieszania: ESTIMATED.

## 4. Źródła (wszystkie publiczne, bez Google)

- OSM API 0.6 — ODbL 1.0, © OpenStreetMap contributors (`raw/osm/manifest.json`: URL-e, UTC, SHA256 per komórka).
- Dz.U. 2019 poz. 2310 / 2311 (znaki; ELI/Sejm API), Dz.U. 2022 poz. 1518 (warunki techniczne dróg; ELI), Dz.U. 2024 poz. 1251 (PoRD t.j.; api.sejm.gov.pl), gov.pl/KAS + etoll.gov.pl (e-TOLL, rozp. RM 8.01.2026, stawki 2026).
- Panoramax API (CC BY 4.0) — tylko sprawdzenie pokrycia bbox pętli.
- Brak Mapillary (token) — patrz §3.
