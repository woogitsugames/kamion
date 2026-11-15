# ADR 0223 — linia kolejowa nr 38 w kaflach korytarza DK65: włączenie torowiska (rail-0217) i wyposażenie przejazdów
Status: Proposed (chmura D, s21, gałąź `rail-dk65-0223`, stacked na `rail-0217` / PR #96), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0217 (generator torowiska, opt-in `Region.rail`, PR #96), ADR 0212 (przejazd DW671), K1
`research/dk65-knyszyn-refs/README.md` §(g), ADR 0210 (wzorzec opt-in), docs/06 §6 (budżety).

## Kontekst
ADR 0217 dał generator torowiska, ale nie włączył żadnego regionu. Linia nr 38 biegnie wzdłuż DK65; trzeba ustalić
z danych, które kafle przecina, gdzie są przejazdy i jak są zabezpieczone, i przygotować włączenie bez Data/raw
(chmura). Przy okazji: ADR 0217 cytuje Dz.U. 2015 poz. 1744 „§ 5” dla G-3/G-4 — w tym akcie § 5 to podział na
kategorie, a G-3/G-4 to § 82 ust. 1; co ważniejsze akt **uznano za uchylony 27.08.2025** (ELI `DU/2015/1744`,
status „uznany za uchylony”, uchylenie z `DU/2025/1105`). Obowiązuje **Dz.U. 2025 poz. 1105** — rozporządzenie MI
z 9.07.2025 w sprawie warunków technicznych, jakim powinny odpowiadać skrzyżowania linii kolejowych oraz bocznic
kolejowych z drogami i ich usytuowanie, oraz warunków technicznych ich użytkowania (tekst: `https://api.sejm.gov.pl/eli/acts/DU/2025/1105/text.pdf`,
SHA256 `c3caeb07…dd924`; dla porównania 2015: `…/DU/2015/1744/text.pdf`, `e488501a…2527c385`).

## Dane (OSM API 0.6, 2026-11-15, ODbL)
Pobrane małymi zapytaniami (UA generyczny): 17 wycinków `/map?bbox=` (kafel + 200 m), `/way/<id>/full` czterech dróg
linii i `/relation/2316318`. Manifest: `Data/SourceManifests/osm-api-0.6-rail-l38.json` (URL, czas, SHA256, CRS,
licencja, zakres, dokładność); surowe XML poza gitem (`Data/raw/osm_api/`). Linia: **relacja 2316318** `route=railway`
`ref=38` „Linia kolejowa nr 38 Białystok - Głomno” (operator PKP PLK); drogi 41533341, 166369632, 173466803,
406675496 są jej członkami. Tagi wszystkich odcinków w kaflach: `usage=main`, `electrified=contact_line`,
`voltage=3000`, `maxspeed=100`, `gauge=1435`; **`tracks` nieotagowane** → generator: 1 tor (`tracks_src: default`;
`railway:track_ref=1` na 173466803 to potwierdza pośrednio).

| kafel | tor w bbox (m, policzony) | drogi OSM | przejazdy (węzeł, droga, tagi → wyposażenie / kat.) |
|---|---|---|---|
| dk65-01 | **770,4** | 173466803 | 2559254736, ul. Św. Franciszka z Asyżu (residential), brak tagów → `nieznane` / – (default) |
| dk65-02 | **1614,1** | 173466803 (+ peron 339410499, przystanek – pominięte) | 2335160489, Dzikowska (tertiary), brak tagów → `nieznane` / – ; S8 (way 1151531620/21, `bridge`, layer 1) nad torem – bezkolizyjnie |
| dk65-03 | **1688,9** (w tym most 41533341 57,5 m, `bridge=yes`) | 41533341, 173466803, 406675496 | brak |
| dk65-04 | **1278,7** | 406675496 (+ peron 339411137) | 1778182442, droga bez nazwy (residential), `crossing:light=no`, `crossing:bell=no` → `brak` / **D** (derived); 2335162693, Białostocka (unclassified), te same tagi → `brak` / **D** (derived) — **0,47 m od zachodniej krawędzi kafla** |
| dw671-tykocin-01 | **1096,9** | 166369632 | 1778182481, DW671 (secondary), brak tagów → `nieznane` / – |
| bialystok-knyszynska | 2251,9 (+ bocznica 7,6, spur 2,1; abandoned 1292,9, disused 499,8) | 173466803 … | 2070722551, Łyskowska, brak tagów — **kafel zakazany (0216), nie włączony** |
| dk65-05…11, knyszyn, knyszyn-s, knyszyn-w, dk65-monki-01 | **0** | – | – |

Długości: przecięcie geometrii OSM (EPSG:2180, pyproj) z bbox kafla — te same liczby daje `Plan` generatora
(test `test_line38_tracks_per_tile`, ±1 m). `railway=crossing` (przejścia piesze) w kaflach: brak. Żaden przejazd nie
ma `crossing:barrier`, `crossing:saltire` ani `supervision`.

## Decyzja
1. **Włączenie** (`regions.py` `rail=True`): `dk65-01`, `dk65-02`, `dk65-03`, `dk65-04`, `dw671-tykocin-01`.
   `region.yaml` dostaje klucz `rail` dokładnie w postaci z `build_region.py` (dopisany na końcu, ten sam dump;
   hash w `build_manifest.json` zaktualizowany — test). Zakazane bez zmian: knyszyn*, bialystok-knyszynska,
   dk65-05…11 (+ dk65-monki-01, bez toru).
2. **Źródła kafli**: `generated/rail_sources.json` w schemacie 0217 (`truck-sim-pl/rail-sources/1`), blok `osm`
   z nowego `rail.extract_osm_xml` (te same reguły co `extract_osm`: kafel + 100 m, `simplify(0.1)`, wspólna lista
   `KEEP_TAGS` — dodane `maxspeed`, `voltage`, `railway:track_ref`), plus `provenance` (`osm-api-0.6`, pliki + SHA256).
   Odtworzenie: `tools/worldgen/rail_sources_api.py --region <id> [--fetch]`. `build_region.py` nadal ekstrahuje z pbf
   (kanoniczny snapshot, spójny z `roads.graph.json`); `extract()` zapisuje teraz `provenance: osm-pbf`.
3. **Wyposażenie przejazdu z tagów OSM** (`rail.crossing_equipment`, pole `equipment` + `category` +
   `equipment_src` source/derived/default/authored_override + `equipment_confidence` + `category_basis`), kategorie wg
   Dz.U. 2025 poz. 1105 **§ 6 ust. 1**:
   | `crossing:barrier` / `crossing:light` | wyposażenie | kat. | podstawa |
   |---|---|---|---|
   | `full`, `gate` | `rogatki_pelne` | A | § 6 ust. 1 pkt 1 lit. b (rogatki na całą szerokość + sygnalizatory) |
   | `half` | `polrogatki` | B | § 6 ust. 1 pkt 2 lit. a (wjazd) |
   | `double_half` | `polrogatki_wjazd_wyjazd` | B | § 6 ust. 1 pkt 2 lit. b |
   | `yes` / `chain` | `rogatki_typ_nieznany` | A\|B / A\|F | pkt 1–2 / § 12 ust. 3 pkt 1 |
   | `no` + `light=yes` | `sygnalizacja_swietlna` | C | § 6 ust. 1 pkt 3 |
   | `no` + `light=no` | `brak` | D | § 6 ust. 1 pkt 4 |
   | brak + `light=no` | `brak` (derived) | D | A z rogatkami, B i C zawsze mają sygnalizatory drogowe (pkt 1 lit. b, 2, 3) |
   | brak + `light=yes` | `sygnalizacja_swietlna_rogatki_nieznane` (derived) | A\|B\|C | – |
   | brak + brak | `nieznane` (default, low) | – | renderowane jak D (same znaki) — **brak raportowany, nie zgadywany** |
   Kategorii F (droga wewnętrzna, § 12) i E (przejścia, § 11) nie wnioskujemy z tagów. Renderowanie markerów
   (rogatki / światła / znaki) dalej idzie z `barrier` / `light` jak w 0217 — kategoria jest opisowa (QA, przyszły spawner).
4. **Authored overrides** (`overrides.yaml`, przeżywają reimport): `{id, kind: rail_crossing, target: {osm_node},
   set: {barrier, light, bell, saltire}, reason, confidence, source}` → `equipment_src: authored_override`; cel
   nieobecny w źródłach → `overrides_stale`; nieznany klucz / typ rogatki → błąd. Wpisy z `kind` road-pipeline pomija
   (`network.apply_edge_overrides`). **Żadnego wpisu nie dodano** — brak źródła o rzeczywistym wyposażeniu (OSM bez
   tagów, Street View zakazany, rejestr przejazdów PLK na dane.gov.pl niedostępny przez proxy). Do uzupełnienia po
   zdjęciu właściciela (lista węzłów w tabeli wyżej).
5. **G-2 „sieć pod napięciem”** na linii zelektryfikowanej (§ 81 ust. 1): marker `sign` `code: G-2` na każdym wlocie —
   `mount: below_cross` (kat. D, na słupku G-3/G-4, pkt 2) albo `signal_mast` (przejazd ze światłami, pkt 1).
   G-3/G-4: § 80 ust. 1 (A bez rogatek, C, D) — poprawiony cytat w `sign_code`.
6. **Markery poza kaflem**: przejazd Białostocka w `dk65-04` leży 0,47 m od krawędzi — znak/G-2 zewnętrznego wlotu
   wypadłyby w dalekim planie sąsiada (bez jezdni, wysokość z obciętej siatki). Takie markery idą do
   `markers_outside_tile` + ostrzeżenie; nie są stawiane.

## Styk z #96 (ADR 0217)
- Zakłada: `Region.rail`, hooki w `build_world` / `build_region` / `stage`, schemat `rail_sources.json`, LAYERS/NODES
  `rail_*`, `LOW_EXCLUDE`, wzory trójkątów — bez zmian.
- Zmienia: `rail.py` (dodatki: `KEEP_TAGS`, `extract_osm_xml`, `crossing_equipment`, `apply_crossing_overrides`,
  `tracks_src`/`maxspeed_kmh`, G-2, `markers_outside_tile`, `provenance` w `extract`), `build_world.py` (jedna linia:
  `Plan(..., overrides=pipeline.load_overrides(region_id))`), `test_rail_0217.py::test_stage_is_opt_in_and_off_everywhere`
  (lista włączeń = 5 kafli zamiast pustej). Strażniki `RL.enabled` / `w.rail is not None` nietknięte (test 0217 zielony).
- Nie zmienia: importera `rail_*` w Unity ani sha256 w qa-tools (FIX #95/#96 lidera).

## Budżet (ESTIMATED z geometrii generatora, test `test_tile_meshes_and_budget`, płaski teren)
| kafel | km | LoD0 | LoD1 | LoD2 | płyty | markery (G-3 + G-2) |
|---|---|---|---|---|---|---|
| dk65-01 | 0,770 | 10 494 | 1 458 | 80 | 18 | 4 |
| dk65-02 | 1,614 | 21 936 | 2 976 | 164 | 24 | 4 |
| dk65-03 | 1,689 | 22 992 | 3 060 | 172 | 0 | 0 |
| dk65-04 | 1,279 | 17 364 | 2 388 | 130 | 36 | 6 (+2 poza kaflem) |
| dw671-tykocin-01 | 1,097 | 14 904 | 2 052 | 112 | 30 | 4 |
| razem | 6,449 | 87 690 | 11 934 | 658 | 108 | 18 instancji |
Zgodne ze wzorem 0217 (1 tor: 13 600 / 1 800 / 100 tris/km). Kadr (LoD per chunk 256 m jak w 0217): ≈ 8 tys. tris
wzdłuż toru (≤ 2 % dolnej granicy 400 tys.), w GLB Low LoD0 nie ma. Draws ≤ 4 na chunk z torem i przejazdem.
Instancje: 18 markerów (9 krzyży G-3 + 9 tablic G-2 na tych samych słupkach) — prefabów jeszcze nie ma (0217 p. 3).
Telefon: nie mierzono.

## Walidacja
`tests/gis/test_rail_dk65_0223.py` (37 przypadków, bez Data/raw): włączenie tylko 5 kafli (+ zakazane wyłączone,
`region.yaml` jak dump `build_region`, hash w `build_manifest`), schemat i provenance (SHA256 = manifest), długości/
drogi/tagi per kafel, przejazdy + wyposażenie per kafel, **tor nie nachodzi na jezdnię poza przejazdem** (podsypka ±
korona vs jezdnie grafu dróg; mosty drogowe pominięte; strefa 15 m od węzła przejazdu), **ciągłość na szwach**
01|02, 02|03, 03|04 (końce ≤ 0,1 m; zmierzone 0,00 m), lista otwartych końców, budżet = wzór, markery w kaflu,
mapowanie A–F (10 kombinacji), overrides (zastosowany / stale / błędy), G-2, ekstrakcja XML.
`uv run --project tools/worldgen python -m pytest tests/gis -k rail -q` → 83 passed.
Nie sprawdzone: pełny `build_world` (Data/raw), wysokość toru na szwach (zależy od terenu kafli), Unity/render.

## Kolejność scalania
1. PR #96 (`rail-0217`) → main. 2. FIX #95/#96 lidera (importer `rail_*`, sha256 qa-tools). 3. Ta gałąź: lider
przestawia bazę PR na `main` (`gh api -X PATCH repos/woogitsugames/kamion/pulls/<nr> -f base=main`), rebase jeśli trzeba.

## Odtworzenie (lider, PowerShell 7, po krokach 1–2)
Źródła są w gicie — `build_region` nie jest potrzebny. Dla każdego `<id>` z: `dk65-01 dk65-02 dk65-03 dk65-04 dw671-tykocin-01`:
```
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>
uv run --project tools/worldgen python scripts/export-route.py --region <id>
pwsh scripts/import-region.ps1 -Region <id> -Build
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low  -Lighting clear -OutputDir artifacts/rail-dk65-0223/vqa/<id>/Low
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir artifacts/rail-dk65-0223/vqa/<id>/High
```
Potem: `git diff --stat Data/Regions/<id>/generated` (nowe `rail.json`, klucz `rail` w `world_manifest.json`),
`uv run --project tools/worldgen python -m pytest tests/gis -k rail -q`, przegląd `rail.json` → `warnings`
(oczekiwane: dk65-04 „crossing on the tile edge”). Opcjonalna kontrola pbf vs API:
`uv run --project tools/worldgen tools/worldgen/build_region.py --region <id>` i `git diff Data/Regions/<id>/generated/rail_sources.json`
— blok `osm` powinien być identyczny (różnice = edycje OSM między 2026-11-08 a 2026-11-15; wtedy zostaw pbf i popraw
`EXPECTED` w teście albo `git checkout` pliku). Kamery kontrolne nie celują dziś w przejazdy; pozycje do dopisania
(lokalne E/N): dk65-01 (540,5; 906,9), dk65-02 (−830,8; −671,9), dk65-04 (−157,9; −874,5) i (−1023,5; −446,6),
dw671-tykocin-01 (−732,2; −533,4); most kolejowy dk65-03 ≈ (988; −314).

## Otwarte
1. **Szew dk65-01 | bialystok-knyszynska** (x = 770827, y ≈ 596885): tor kończy się na krawędzi, bo sąsiad jest
   zakazany (latarnie/niebo 0216). Włączyć tam rail po zamknięciu 0216 (2,25 km linii + przejazd Łyskowska,
   bocznica/spur 9,7 m; odcinki abandoned/disused pomijane). Pozostałe końce (dk65-04 W, dw671 W i S) wychodzą do
   kafli spoza regionów — daleki plan bez toru.
2. Wyposażenie 4 przejazdów `nieznane` (DW671, Dzikowska, Św. Franciszka) — zdjęcie właściciela albo rejestr PLK →
   override `kind: rail_crossing`. Przejazd DW671 (droga wojewódzka, 100 km/h) z dużym prawdopodobieństwem nie jest D,
   ale nie zgadujemy.
3. Przejazd Białostocka w dk65-04 na krawędzi kafla: połowa płyt i zewnętrzny wlot poza światem; szerokość jezdni
   w strefie przycięta do minimum 3,0 m. Przy dokładaniu kafla (-6,2) — wspólny przejazd na szwie.
4. Most kolejowy 41533341 (dk65-03): profil liniowy bez podpór (0217 p. Otwarte 4).
5. ADR 0217 nadal cytuje „Dz.U. 2015 poz. 1744 § 5” w tekście ADR — do poprawienia przy scaleniu #96 (kod już ma
   § 80 ust. 1 Dz.U. 2025 poz. 1105).
