# K1 — DK65 Białystok → Knyszyn: przekroje, skrzyżowania, rondo DW671, S19/S16, Rynek

Zakres: trasa wariantu A (D65 p.1: stara droga przez Fasty i Dobrzyniewo Duże) w kaflach `dk65-01 … dk65-11`, `knyszyn-s`,
`knyszyn`, `knyszyn-w` (bbox z `tools/worldgen/regions.py` i planu ADR 0203). Kilometraż „km trasy” = od startu wariantu A
w `docs/reports/map/dk65_route_plan.json`; kilometraż DK65 ze słupków OSM: **DK65 km ≈ 170,05 − km trasy** (słupek 161 przy
km 9,05 … 143 przy km 27,10; 19 węzłów `highway=milestone ref=65`).

Pliki: `manifest.csv` (136 wierszy, utf-8, kolumny wg zadania), `sources.md`, `audit_20_percent.json`, `STATUS.md`,
`files/photos/` (42 JPG ≤ 1600 px z Commons), `files/orto/` (wycinki ortofoto GUGiK 0,1 m: 30 przekrojów + 13 skrzyżowań/Rynek/szpalery),
`files/docs/` (odpowiedź MI 10.12.2024), `data/` (punkty, tagi OSM, profile, log zapytań), `tools/` (skrypty odtwarzające).

Statusy w manifeście: **SOURCED 89, ESTIMATED 44, UNVERIFIED 3**. Obejrzane kadry zdjęciowe: **42** (w tym 28 z Knyszyna — 27 bez ryciny historycznej P21 —
z czego 24 temat f: Rynek, pierzeje, pomnik, kościół, ulice); plus 43 wycinki ortofoto obejrzane (wszystkie przekroje także w zoomie 2×).

## Metoda pomiaru przekroju (ESTIMATED)
Ortofoto GUGiK WMS HighResolution, najnowszy arkusz wg skorowidza: **2025-05-25** (korytarz) / **2025-05-27** (Knyszyn),
piksel 0,1 m. Wycinek 80×80 m pobrany w EPSG:2180, obrócony o azymut osi OSM (droga pionowo), środek = oś OSM. Profil jasności
poprzecznie do osi (mediana z 30 m wzdłuż), piki = linie (krawędziowe, środkowa), skoki gradientu = krawędź asfaltu; typ linii
(ciągła/przerywana) odczytany z zoomu 2× (`files/orto/km/zoom_*.jpg`). Dokładność: linie ±0,2 m, krawędź asfaltu ±0,4 m.
OSM na całej trasie **nie ma** tagów `width`, `shoulder`, `lit`, `lane_markings` — tylko `lanes=2`, `surface=asphalt`, `maxspeed`.

## Tabela per kafel
| kafel | km trasy | droga (OSM) | rozstaw linii krawędziowych [m] (km) | linie krawędziowe | oś | pobocza / otoczenie | inne | zdjęcia na trasie |
|---|---|---|---|---|---|---|---|---|
| dk65-01 | 8,76–9,39 | Szosa Knyszyńska, secondary bez ref, 70 km/h | 6,3 (8,8) · 6,2 (9,0) | ciągłe, przerywane na zjazdach | przerywana | żwir 0,6–1 m, asfalt ~7,9–8,4 m | kolej 38: 111–115 m na L | brak (Panoramax 9 zdjęć 1,7 km od trasy; P29 — 640 m przed kaflem) |
| dk65-02 | 9,39–11,80 | Szosa Knyszyńska → Ełcka, most 10,85–10,94 | 6,4 (10,0) · 6,3 (11,0) · 6,1 (11,5) | mieszane: ciągłe / P przerywana / obie przerywane (11,5) | przerywana; ciągła (11,0) | żwir 0,8–1,2 m; nasyp za mostem | wiadukt S19 (orto 2025: w budowie, objazd); kolej 38 150–330 m | P25, P26 (z mostu — rzeka, droga niewidoczna), P31 (przystanek) |
| dk65-03 | 11,80–12,28 | Ełcka, 90 km/h | 6,1 (12,0, **UNVERIFIED** L) | L nieczytelna, P przerywana | przerywana | żwir/trawa | kolej ≥ 487 m | brak |
| dk65-04 | 12,28–14,36 | Ełcka | 6,2 (12,5) · 6,25 (13,0) · 6,4 (13,5) · 6,2 (14,0) | przerywane (12,5), ciągłe (13,5–14,0) | przerywana; ciągła przy wlotach | zatoka autobusowa L z wiatą (13,0) | skrzyżowanie Białostocka/Kościelna km 13,13 | P27 (droga niewidoczna), P38 (287 m) |
| dk65-05 | 14,36–16,56 | Ełcka → Studzienna (od 15,39) | 6,2 (14,5) · 6,2 (15,0) · 6,1 (15,5) · 6,2 (16,0) | ciągłe; przerywane przy wlotach/zatoce | ciągła (14,5–16,0) | zatoka P (14,5); rów L (16,0) | szpaler drzew L ~15 m rozstawu | brak |
| dk65-06 | 16,56–18,26 | rondo S19/DK65 (OSM), DK65 primary 90 | 6,1 (17,0) · 6,0 (18,0) | ciągłe (17) / przerywane (18) | przerywana | pas żwiru | rondo OSM Ø osi ~44 m — na orto 2025 jeszcze nie ma | brak (P37 911 m) |
| dk65-07 | 18,27–19,13 | DK65 | 6,4 (19,0) | L ciągła, P przerywana (zatoka) | ciągła | zatoka autobusowa P z peronem i żółtą barierką | skrzyżowanie 1392B km 18,77 | brak (P35 388 m) |
| dk65-08 | 19,13–21,49 | DK65 | 6,0 (20,0) · 6,25 (21,0) | przerywane (20) / ciągłe (21) | przerywana | bariery stalowe obie strony przy przepuście (21,0) | grupa drzew przy zatoce ~20,5 | brak (P36 641 m) |
| dk65-09 | 21,49–21,84 | DK65 | 6,1 (21,65) | przerywane obie | przerywana | żwir ~1 m | — | brak |
| dk65-10 | 21,84–24,45 | DK65 | 6,1 (22,0) · 6,2 (23,0) · 6,1 (24,0) | przerywane (22) / ciągłe (23–24) | przerywana | trawa, las | skrzyżowanie 1397B km 22,65 | brak |
| dk65-11 | 24,45–24,83 | DK65 | 6,0 (24,6) | ciągłe | przerywana | teren piaszczysty P | — | brak |
| knyszyn-s | 24,83–27,25 | DK65 → Obozowa | 6,1 (25,0) · 6,8 (26,0) · 6,8 (27,0) | ciągłe; P przerywana przy zatoce (25,0) | ciągła (25) / przerywana | zatoka P (25,0); bariery przy moście (27,0) | rondo S16 w budowie (OSM, Ø osi ~41 m) | brak (Commons/Panoramax 0) |
| knyszyn | 27,25–28,44 | Obozowa → rondo → Tykocka DW671 → Rynek | DW671 w mieście: ~10 m między krawężnikami, bez linii krawędziowych | — | przerywana | chodniki, latarnie na słupach z wysięgnikiem | rondo DK65×DW671 (OSM Ø osi 17,6 m) | 28 kadrów (P01–P24, P39–P41, P44; P21 to rycina historyczna) |
| knyszyn-w | (poza trasą A) | DK65 na Mońki, DW671 na Tykocin | nie mierzono — ADR 0212: 6,8 m linia–linia | ADR 0212 | — | — | — | 0 (Commons geosearch 81 trafień = cmentarz żydowski/inne) |

Podsumowanie (a): **rozstaw linii krawędziowych na całym korytarzu 6,0–6,4 m** (mediana 6,2 m, n = 25, km 8,8–25,0), w Knyszynie (Obozowa)
**6,8 m**; asfalt łącznie z opaskami za liniami 7,0–9,0 m; 2 pasy, pas ruchu (oś–oś linii) 2,9–3,4 m. Linie krawędziowe
**przerywane** (krótkie kreski) na km 11,5; 12,5; 18; 20; 21,65; 22 — reszta ciągłe; ich symbol (P-7b / P-7c/d) z samego obrazu
**UNVERIFIED**. Rowy: widoczne lokalnie (km 16,0), ogólnie UNVERIFIED z ortofoto. Bariery: km 21,0 (przepust), km 27,0 (most).
Zatoki autobusowe: km 13,0 L, 14,5 P, 19,0 P, 25,0 P (+ przystanki OSM co 0,2–2 km).

## (b) Skrzyżowania i rondo DK65×DW671
- **Rondo w Knyszynie** (OSM way 1426801304, edycja 2026-01-05): pierścień r osi 8,4–9,1 m → **średnica osi ~17,6 m** (SOURCED z
  geometrii OSM); 4 wloty jednokierunkowe 1-pasowe przy wysepkach (Obozowa N/S, Tykocka E/W; `destination` Ełk, Białystok,
  Tykocin, Korycin). Średnica zewnętrzna, szerokość jezdni ronda, wyspa środkowa i jej zawartość — **UNVERIFIED** (OSM nie ma
  obiektu wyspy; ortofoto 2025-05-27 jest sprzed budowy).
- **Ortofoto 2025-05-27**: w tym miejscu skrzyżowanie czterowlotowe skanalizowane (malowane wyspy, wysepka z krzewami NW, przejścia
  na 4 wlotach) — zgodne z ADR 0204. Rondo wynika z dokumentu MI 10.12.2024 (przebudowa „na skrzyżowanie z ruchem okrężnym”,
  chodniki, oświetlenie przejść; ZRID złożony VII 2024) i potwierdzenia właściciela D65 p.2. Data oddania ronda — UNVERIFIED.
- Krzyż stalowy na trawniku przy skrzyżowaniu (pl. Jana Pawła II, K1-P24); widok 2009 na DK65 z czerwonymi barierkami (K1-P22) —
  stan sprzed przebudowy.
- Rondo S19/DK65 km 16,66 (OSM, Ø osi ~44 m) — na ortofoto 2025-05-25 brak; rondo S16 w budowie ~3 km na S od Knyszyna (OSM
  construction, Ø osi ~41 m; Auto Świat 14.05.2026). Skrzyżowania zwykłe: Białostocka/Kościelna km 13,13 (4 wloty),
  1392B km 18,77 (T z szrafami). Pełna lista węzłów trasy w `docs/reports/map/dk65_route_plan.json` (`junctions`).

## (c) S19 / S16 — stan budowy (każdy fakt z datą dokumentu)
- S19 Krynice–Dobrzyniewo–Białystok Zachód (10,2 km) **oddany do ruchu 20.10.2026** (wartowiedziec.pl, 21.10.2026; zapowiedź
  GDDKiA w Auto Świat 13.10.2026). Komunikatu GDDKiA na gov.pl nie udało się pobrać (503/reset).
- Wiadukt w Fastach: ortofoto 2025-05-25 — płyta wiaduktu na przyczółkach nad wykopem S19, ruch objazdem łukiem z czerwono-białym
  wygrodzeniem; GDDKiA 14.10.2025 — likwidacja objazdu od 15.10.2025 9:00 (**UNVERIFIED** — cytat tylko z indeksu wyszukiwarki).
  Stan „na dziś” = deklaracja właściciela D65 p.3 (otwarty).
- Stara DK65 przez Fasty/Dobrzyniewo traci status drogi krajowej po otwarciu S19 (MI 10.12.2024, s.2) — zgodne z OSM
  (secondary, bez ref, `old_ref`). Nowa kategoria — UNVERIFIED.
- S16 Knyszyn–Krynice: 8,4 km, start rondem na DK65 ~3 km na S od Knyszyna, oddanie 2028, na DK65 ograniczenia do 50 km/h,
  zakazy wyprzedzania, zwężenia (Auto Świat 14.05.2026). Zwężenia/objazdy na DK65 obowiązujące dziś — **UNVERIFIED** (brak
  dokumentu; kadry właściciela 2026-07-28 pokazują żółte oznakowanie tymczasowe).
- OSM: `highway=construction` motorway 16,6 km przy km 16,7–25,0 (edycja 2026-09-28). Sprzeczność: OSM (2026-11-08) ma nową
  jezdnię DK65 przy rondzie km 16,66 jako `primary`, a właściciel (D65 p.6) — nieotwarta.

## (d) ul. Ełcka (+ Studzienna), km 10,94–16,6
Kafle dk65-02 (km 10,94–11,80), dk65-03 (11,80–12,28), dk65-04 (12,28–14,36), dk65-05 (14,36–16,56; Studzienna od km 15,39).
Rozstaw linii krawędziowych **6,1–6,4 m (mediana 6,2 m)** z 8 przekrojów; asfalt z opaskami **7,0–9,0 m**. Wartość właściciela
~6,9 m leży pomiędzy (bliżej „linia–linia + opaski 0,3–0,4 m”). Obecny override ADR 0207 (7,6 m) jest szerszy od rozstawu linii o
~1,4 m. OSM: brak `width`.

## (e) Latarnie
- OSM: **0** węzłów `highway=street_lamp` w pasie ±300 m wzdłuż całej trasy; `lit=interval` tylko na ul. Rynek.
- Ortofoto: na DK65 km 17–25 brak cieni słupów (poza zatoką km 19); słup z wysięgnikiem przy zatoce km 13,0; w Knyszynie (Tykocka km 28,0)
  słup z wysięgnikiem po jednej stronie.
- Zdjęcia 2009–2012 (P06, P18, P23, P44): słupy betonowe z linią napowietrzną i oprawą na wysięgniku, po jednej stronie; przy
  kościele stylizowane czarne latarnie z dwoma kloszami (P14, P15). Typ LED, barwa, wysokość, rozstaw — **UNVERIFIED** (D65 p.8: białe LED —
  deklaracja właściciela). MI 10.12.2024: w zakresie ronda „oświetlenie dedykowane na przejściach dla pieszych”. Przetargu gminy Knyszyn
  na LED nie znaleziono (wyszukiwanie 2026-11-15).

## (f) Rynek w Knyszynie
Ortofoto 2025-05-27: plac zieleni ok. 120×110 m (OSM park 7441 m²), alejki z jasnej kostki zbiegające promieniście do okrągłego
placu (Ø ~25 m ESTIMATED), **fontanna posadzkowa ~6×6 m** (OSM `fountain=splash_pad`, `lit=yes`, 32 m²), pomnik (brązowa figura
na granitowym cokole, P08/P10/P12) i zegar słoneczny z tablicą (P09), kilkadziesiąt dużych drzew liściastych (gatunki UNVERIFIED),
trawniki, ławki. Na N: budynek UM/biblioteki/ośrodka kultury — 2 kondygnacje + lukarny, dach czerwony, elewacja kremowo-biała,
żółte obramienia, portyk (P07). Pierzeje: 1–2 kondygnacje z poddaszem, dachy czerwone/brązowe/grafitowe, elewacje kremowe, białe,
szaro-beżowe, cegła ciemnoczerwona (P02, P19, P39, P40); tabliczki adresowe czerwono-żółte z herbem (P03), tabliczki ulic białe
(P04). Kościół św. Jana: biały, dach i hełm czerwone (2024, P15/P16; w 2009 elewacja kremowa, P17), plac z bruku granitowego.

## (g) Kolej i drzewa
- **Linia kolejowa nr 38** (OSM ref=38, zelektryfikowana 3 kV) biegnie po L (SW/W) od drogi: 111 m (km 9,0), 150 m (10,0), 203 m
  (11,0), 328 m (11,5), ≥ 487 m od km 12; przystanek Fasty ~160 m od trasy; most kolejowy nad Supraślą ~200 m od mostu drogowego
  (P25). **Brak przejazdów na trasie**; przejazdy 038 010 194 / 038 010 956 / 038 012 443 na drogach bocznych (64–177 m). Stacja
  „Knyszyn” leży ~3 km od trasy (P32–P34).
- Szpalery: Ełcka km ~11,7 — jednostronny L, ~20–25 m rozstawu, 8–12 m od krawędzi; km ~14,6 — L, ~15 m rozstawu, 5–10 m od krawędzi;
  DK65 km ~20,5 — grupa ~8 drzew przy zatoce; w polu/lesie dalej las sosnowy. Gatunki **UNVERIFIED** (brak źródła; OSM tylko
  `tree_row` 74 m przy Obozowej km 27,4).

## Luki i UNVERIFIED (najważniejsze)
1. Zdjęcia uliczne korytarza: Panoramax 0 na trasie (9 zdjęć 1,7 km od trasy w dk65-01), Commons — brak kadrów pokazujących jezdnię
   w kaflach dk65-01, 03, 05–11, knyszyn-s; Openverse bez dodatkowych wyników; KartaView błąd TLS; Mapillary bez tokenu. Cel „≥ 1 kadr
   na każdy kafel DK65” **nie do spełnienia** z dozwolonych źródeł — dowód w `data/query_log.json`.
2. Rondo DK65×DW671: średnica zewnętrzna, szerokość jezdni ronda, zawartość wyspy, data otwarcia.
3. Stan objazdów/zwężeń na DK65 „na dziś” (S16), komunikat GDDKiA 14.10.2025 (strona niedostępna).
4. Latarnie: typ LED, wysokość, wysięgnik, rozstaw.
5. Gatunki drzew; rowy (głębokość, ciągłość).
6. Symbol prawny przerywanych linii krawędziowych (P-7b vs P-7c/d).
7. km 12,00 — lewa linia krawędziowa nieczytelna.

## Audyt 20 %
`random.seed(20261115)`, 28 z 136 wierszy; ponowne obejrzenie zoomów ortofoto / JPG 960 px, ponowny sha256 i ponowne pobranie
URL. Wynik: **24 PASS, 4 FIX** — km 12,00 (L linia nieczytelna → UNVERIFIED), km 12,50 (L linia przerywana, nie ciągła), wiadukt
S19 (doprecyzowany opis: płyta nad wykopem S19), URL zapytania OSM bez bbox (400 → poprawiony). Wszystkie sha256 zgodne.

## Odtworzenie
Skrypty w `tools/` (uruchamiane z venv z pyproj/pillow/numpy/requests; ścieżki scratchpad w nagłówkach): `sample.py` (punkty co 1 km),
`orto.py` + `sheets_fix.py` (wycinki i daty arkuszy), `analyze.py`, `zoom.py`, `osmways.py`, `osm_corridor.py`, `raildist.py`,
`rondo.py`, `pano_search.py`, `commons_*.py`, `csearch.py`, `dl_photos.py`, `build_manifest.py`, `audit_pick.py`, `audit_write.py`.
