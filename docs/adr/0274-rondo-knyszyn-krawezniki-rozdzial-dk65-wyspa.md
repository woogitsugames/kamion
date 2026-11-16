# ADR 0274 — rondo Knyszyn: projektowane pasy i promienie krawężnika, rozdział DK65 przed rondem, wyspa, P-13 / P-10 przy pierścieniu
Status: Proposed (chmura D runda 5, zadanie D14, gałąź `roundabout2-0274`), 2026-11-16. Do weryfikacji i scalenia przez lidera.
Powiązane: ADR 0218 §5c (rondo kompaktowe; punkty otwarte a–d), ADR 0272 (pomiar na ortofoto), recenzja D18
(`docs/reports/REVIEW-2026-11-16-s23-code-compact-roundabout.md`, gałąź `reviews-code-s23`), D65, D75.

## Kontekst
ADR 0218 §5c zostawił cztery punkty: (a) szerokie, lejkowate płaty asfaltu między ramionami, (b) krótka wysepka S,
(c) wachlarz trójkątów i brak nasadzeń na wyspie, (d) P-13 i przejścia przy węźle rozdziału zamiast przy pierścieniu.

**Pomiar.** Zadanie zakładało pomiar promieni krawężnika i długości wysepek na ortofoto. Narzędzie
`tools/worldgen/qa/roundabout_ortho.py` (wynik: `docs/reports/roundabout-0274/`) pokazuje, że **ronda nie ma na
ortofoto GUGiK**: arkusz N-34-106-B-b-1-4 ma datę 2025-05-27 (skorowidz 2026 pusty), środek „pierścienia” to w 100 %
asfalt zwykłego skrzyżowania. OSM daje tylko osie ze śladów GPS (changeset 176857414, `source=Yanosik`). Zdjęć
właściciela 9–11 nie ma w gicie. Wszystkie wymiary ronda pozostają więc **WORKING_VALUE / ESTIMATED** — w kodzie jest
mechanizm i jedna miara dla zdjęcia i dla generatora, liczby wpisze lider po przeskalowaniu zdjęcia 9.

## Decyzja
1. **Tryb krawężnikowy** (`compact_roundabout.py`; włącza go `entry_r_m` / `exit_r_m` w kluczu `compact_roundabout`,
   bez nich działa obrys ADR 0218). Przyczyna (a): jezdnie jednokierunkowe z OSM biegną prawie stycznie do pierścienia
   (wlot E i wylot N spotykają pierścień 2,3 m od siebie), a obrys szedł po ich zewnętrznych krawędziach.
   `lay_lanes` (wołane z `network.load`) układa te pasy na nowo: równolegle do osi ramienia, najwyżej
   `splitter_w_m / 2 + lane_w_m / 2` od niej, z łukiem do osi pierścienia o promieniu „promień krawężnika + pół pasa”
   (krawężnik po zewnętrznej stronie skrętu ma dokładnie `entry_r_m` / `exit_r_m`), dalej po osi pierścienia do węzła
   z OSM (albo łukiem prosto w węzeł, gdy leży on przed punktem styczności). Obrys = koło pierścienia + te pasy +
   końce ramion; styk dwóch wyokrągleń przed krawężnikiem pierścienia dostaje nosek R 4 m (`NOSE_R_M`).
   Odrzucone: per-narożnikowe domknięcie morfologiczne wokół śladów OSM z korytarzem `lane_clear_m` — płaty między
   ramionami −40 %, ale wloty zostawały 12,4 m (korytarz wokół stycznych śladów) i łączna powierzchnia się nie zmieniała.
2. **Rozdział DK65** — nowy override na poziomie grafu `kind: carriageway_split` (`roads/carriageway_split.py`):
   węzeł rozdziału przesuwa się `length_m` dalej po drodze dwukierunkowej, oba pasy odchodzą od starej osi
   smoothstepem na `taper_m` do `lane_offset_m` i łączą się z geometrią OSM. Zmieniana jest kopia grafu w
   `network.load`; `roads.graph.json` zostaje jak z ingestu. `pipeline.effective_graph` daje ten sam graf trasie
   startowej (`scripts/export-route.py`, `build_world.route_polyline`); w `route_start.json` węzeł `…s` jest zapisany
   pod id węzła, który zastąpił (czytniki szukają węzłów trasy w grafie z ingestu).
3. **Wyspa** — `island_fill_mesh`: pierścienie koncentryczne z malejącą liczbą segmentów (każdy ≥ połowa
   zewnętrznego, przy środku 8), wysokość = płaszczyzna linii krawężnika + 2 pierwsze harmoniczne jej odchyłki × (r/r0)²;
   pełna odchyłka gaśnie w pasie 0,25 m. Dawna siatka niosła odchyłkę każdej próbki po promieniu (szprychy = promieniste
   cieniowanie) i zamykała środek wachlarzem 65 drzazg; przy całkowitym r0 dublowała pierścień (D18 P2-2).
   Rośliny i kamienie: `kind: plantings` dostaje listy `clumps` / `stones` (punkty EPSG:2180, promień, wysokość) —
   kamień = spłaszczona kopuła 49 trójkątów, materiał `bed_stones`; krzew = istniejące `hedge_mass`.
4. **Oznakowanie** — P-13 na pasie wlotowym wzdłuż krawędzi jezdni pierścienia, 0,15 m za nią (WORKING_VALUE).
   Podstawa: Dz.U. 2019 poz. 2311, zał. 2 pkt 4.2.4 („Zasady i sposób umieszczania znaku P-13 … są analogiczne jak
   znaku P-12”), pkt 4.2.3 („Przebieg linii … wyznacza się wzdłuż krawędzi jezdni z pierwszeństwem”), pkt 8.4 (wloty
   ronda z C-12 + A-7 znakuje się jak wloty podporządkowane, pkt 7.6.2.2); tekst czytany z
   `api.sejm.gov.pl/eli/acts/DU/2019/2311/text/I/D20192311-c2.pdf`, str. 571–572 i 678. P-10 (pkt 4.2.1: szerokość
   4,0 m, pasy 0,5 / 0,5 m — `standards.py`) w poprzek pasa wlotowego i wylotowego ramion z listy `crossings`,
   bliższa krawędź `crossing_offset_m` za krawędzią jezdni pierścienia; wysepka jest w tym miejscu przecięta (azyl w
   poziomie jezdni). **Odsunięcie 5,0 m = WORKING_VALUE** (długość samochodu osobowego; zał. 2 nie podaje tej
   odległości, WR-D-31-3 nie czytane w oryginale — UNVERIFIED). Ogólne reguły (`markings.py`) pomijają ramiona i
   węzły przejść takiego ronda.
5. **Poprawki recenzji D18** (temat rondo): P1 raport `compact_roundabouts` w `roads_qa.json`; P2-2 zdublowany
   pierścień; P2-3 za mały pierścień → stale; P2-4 narożnik z jednym punktem (`_corner_points`); P2-5 < 3 ramiona →
   notatka + stale; P2-6 walidacja wartości `compact_roundabout`, `edge_line_spacing`, `edge_line_dashed`; P2-7
   `truck_apron` beton / asfalt tylko bez progu (z `height_m > 0` → stale); P2-8 asercja kodów `WALK_MATS`; P2-11
   `reason` wpisu ronda. Nie ruszone: P2-9 (koszt `edge_dashed_spans`), P2-10 (rytm kresek na granicy sekcji).

## Knyszyn (`Data/Regions/knyszyn/overrides.yaml`, tylko wpisy ronda)
`knyszyn-roundabout-compact`: `entry_r_m 6,0`, `exit_r_m 8,0`, `splitter_w_m 2,4`, `lane_w_m 4,0`,
`crossing_offset_m 5,0`, przejścia na 4 ramionach (węzły przejść OSM N / E / W; S wg opisu zdjęcia 9) — wszystko
WORKING_VALUE. `knyszyn-roundabout-dk65-split-s` 27 m i `-n` 17 m (taper 14 m, pasy ±3,0 m) → wysepki 29,2 m (S,
ESTIMATED: „kilkadziesiąt metrów”) i 20,2 m (N, WORKING_VALUE) od krawędzi pierścienia. `knyszyn-roundabout-island-
plantings`: 3 krzewy 0,35–0,45 m i 5 kamieni 0,15–0,30 m, ≥ 0,5 m + promień od lica krawężnika wyspy (ESTIMATED z
opisu w `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`).

Wynik na danych z gita (wysokości płaskie; liczby w `docs/reports/roundabout-0274/README.md`): wloty 2 m za
krawężnikiem pierścienia 13,1 / 11,8 / 12,9 / 13,4 m → 10,9 / 11,0 / 11,5 / 11,4 m i równoległe zamiast lejka; asfalt w
pasie 3 m za krawężnikiem pierścienia 165,5 → 141,3 m²; P-13 4 × (3,3–3,6 m), P-10 4 × (6–8 pasów na dwóch
pasach ruchu, azyl 2,3–2,4 m); 7 wysepek (4 noski + ogony W / S / N). Trasa startowa wyeksportowana ponownie:
1159,80 m (było 1159,85), przesunięcie do 3,0 m (na projektowany pas DK65 S), ≥ 1,5 m od wysepek.

## Budżet (kafel knyszyn, nie region C — kamery C bez zmian)
Zmierzone `pipeline.build` + `markings` na danych z gita z syntetycznym polem wysokości (NMT jest w `Data/raw`),
trójkąty warstw `road` + `markings` w promieniu 60 m od środka ronda, main `08c2e21f8` → ta gałąź: **7 937 → 8 999
(+1 062)**: asfalt 2 417 → 2 315, krawężniki 3 813 → 4 805 (dłuższe wysepki i narożniki), oznakowanie 277 → 768
(P-13 / P-10 jako drapowane decale: 672), wyspa 325 → 329. Do tego nasadzenia wyspy **+945 tris, 4 materiały**
(`hedge_privet` ×3, `bed_stones`; najwyżej +4 draw calle, jeśli chunk ich nie ma). Razem ok. **+2,0 tys. tris** w
kadrach ronda; do potwierdzenia w `streetscape_qa.json` po przebudowie. Płyta ronda w trybie krawężnikowym jest
gwiaździsta względem środka — bez poprawki w `meshing.build_patch` (Delaunay zamiast siatki biegunowej dla ronda
kompaktowego > 15 m) miałaby 25 194 trójkąty zamiast 1 840; pilnuje tego test. Poza knyszyn bajtowo bez zmian.

## Testy
`tests/gis/test_roundabout_0274.py` (62): syntetyczne — obrys prosty, pasy w obrysie, szerokość wlotu ≤ pas +
wysepka + pas, płaty między ramionami w zasięgu łuku, odczyt wygenerowanego ronda narzędziem ortofoto, rozdział jezdni
(długość wysepki, graf niezmieniony, 8 przypadków stale), siatka wyspy (brak wachlarza, kąty, normalne ≤ 0,5°), P-13 /
P-10 względem pierścienia, walidacje D18; Knyszyn z gita — `built`, `notes == []`, długości wysepek, obrys ciaśniejszy
niż ADR 0218, trasa ≥ 1,5 m od wysepek, nasadzenia w budżecie. `test_truck_apron_0218.py` zaktualizowany (P2-7).

## Otwarte
- Wymiary ze zdjęć 9–11 (lider): promienie, szerokość pasa i wysepek, długości wysepek N / S, odsunięcie przejść,
  liczba i układ krzewów / kamieni; potem ponowny `swept_path.py` (ADR 0218 §3) i przejazd zestawem (PlayMode).
- `navgraph/build_route_graph.py`, `streetscape` i narzędzia QA czytające `roads.graph.json` wprost widzą graf bez
  rozdziału DK65 (do ±3 m na 2 × ok. 45 m) — przepiąć na `pipeline.effective_graph`, jeśli wyjdzie w grze.
- Wysepka E za przejściem ma < 3 m² i zostaje asfaltem; kamienie bez kolizji.
- Render kamer ronda i porównanie ze zdjęciem 9 (`visual-critic`) — nie wykonane w chmurze.
