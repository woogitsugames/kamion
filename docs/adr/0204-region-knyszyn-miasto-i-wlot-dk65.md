# ADR 0204 — regiony `knyszyn` i `knyszyn-s`: miasto Knyszyn, wlot DK65 i strefa budowy ekspresówki (z grubsza, D63/D64)
Status: Proposed (agent world-builder, s20, gałąź `knyszyn-0204`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D64 (`docs/11`), ADR 0203 (plan trasy i kafli), ADR 0166/0174 (region ≠ C, import), brief
`docs/owner/S20-REGION-RING-BRIEF.md` (aktualizacje 1–3), `docs/owner/OWNER-PHOTOS-KNYSZYN.md`.

## Kontekst
D64: Białystok → DK65 → Knyszyn; DROGI NAJPIERW (wierna sieć dróg, budynki LoD1 bez szlifu). ADR 0203 zarezerwował
dla Knyszyna kafle siatki 2048 m: `knyszyn-s` (−8,7) i `knyszyn` (−8,8), z opcją (−9,8). Potok (`far_field`,
`chunks`, `heightmap_2049`) zakłada kafel 2048 × 2048 m, więc region = jeden kafel.

## Decyzja
1. **Dwa regiony na siatce ADR 0203** (bez przesuwania kafla, żeby szwy zgadzały się z korytarzem 0205):
   - `knyszyn` (−8,8): EPSG:2180 [760587, 611583, 762635, 613631], origin (761611, 612607) — Rynek, DW671
     (Tykocka, Grodzieńska), rondo DK65/DW671, 528 m DK65 (Obozowa).
   - `knyszyn-s` (−8,7): [760587, 609535, 762635, 611583], origin (761611, 610559) — 2,42 km DK65 od szwu
     z `dk65-11` (762635, 609811) do szwu z `knyszyn` (760985,8, 611583), strefa budowy ekspresówki.
   - Powiat 2008 (moniecki) dla obu; narożnik `knyszyn-s` w powiecie 2002 nie ma zabudowy przy trasie (12 budynków
     w całym kaflu z BDOT 2008) — `teryt_powiat` zostaje jednym kodem.
   - **Kafel (−9,8) nie jest zbudowany**: rondo leży 37 m od zachodniej krawędzi `knyszyn`, wylot DK65 na Mońki
     i zachodnia część miasta (siatka ulic, ~35 % zabudowy) są w (−9,8). Do zbudowania jako `knyszyn-w` (otwarte).
2. **Trasa kontrolna** (`route_endpoints.json`, authored): `knyszyn-s` szew wsch. → szew płn. (2420,7 m);
   `knyszyn` szew płd. → DK65 → rondo → Tykocka → Rynek (1159,9 m). Nowe pole `via_epsg2180` (build_world
   i export-route): bez niego najkrótsza ścieżka skręcała z DK65 w Południową.
3. **Zmiany w potoku** (wspólne; region C i Dojlidy bez zmiany wyniku — patrz walidacja):
   - `osm_extract.BBOX_WGS84 = (22.80, 53.05, 23.32, 53.38)` + bbox w kluczu cache — dokładnie zmiana opisana
     w ADR 0203 §„rzeczy wspólne” p. 1 (osobny commit `7ce3fe325`, do wzięcia przez 0205).
   - `graph_filter.authored.json` (per region, authored): `drop_service: [driveway]`. OSM ma w Knyszynie zjazdy
     posesji co ~12 m jako `highway=service`; jako węzły grafu nakładały się i generator skrzyżowań zostawiał
     **~80 m dziury w jezdni DW671 na trasie** (`plan/knyszyn/r1/tykocka_gap.jpg` → `r3/`). Region bez pliku: bez zmian.
   - Brak pliku klasy w archiwum BDOT10k powiatu (2008 nie ma `OT_OIKM_L`) = pusta warstwa (było `StopIteration`).
   - Pusty poligon lasu po buforze −2 m (`vegetation._scatter`) nie wywraca budowy.
   - Przekrój szlakowy (pobocze, bez krawężników) działa też w kaflu bez żadnego chodnika (`assign_sides`
     wymagał drzewa chodników; `knyszyn-s` dostawał krawężniki na DK65 w lesie).
   - Override `set: {lamps: false}` (droga nieoświetlona): reguła latarni stawiała 122 słupy na DK65 w polu.
   - `ingest.py --with orto10`: ortofoto 0,1 m (najnowszy rok) jako referencja QA.
4. **Poprawki z porównania z ortofoto** (authored_overrides):
   - DK65: BDOT 6,0 m → pomiar na ortofoto 0,1 m 2025-05-27 (4 przekroje, `profile10.py`): linia krawędziowa –
     linia krawędziowa 6,8 m, asfalt 7,3–7,6 m → 2 × 3,4 m + 2 × 0,35 m = 7,5 m (±0,3 m).
   - Rynek: plac wschodni jako `paved_area` (BDOT: żwir — stan sprzed przebudowy), płyta fontanny (pozycja
     ESTIMATED ±5 m, rozmiar WORKING_VALUE), park zachodni jako rzadki drzewostan (BDOT „zadrzewienie” dawało
     zwarty las).
   - Drogi polne i DK65 w `knyszyn-s`: bez latarni.
5. **Strefa budowy (WORKING_VALUE)**: platforma z gruntu (`yard_gravel`) 60 m szerokości wzdłuż osi OSM
   `highway=construction` (ways 1511762695/6) + tarcza ronda w budowie (way 1511762690, środek 762490,5; 609930,6)
   + pas łącznika; wycinka w drzewostanie BDOT 87a8e448. DK65 przejezdna w stanie z OSM. Hałdy, maszyny, znaki
   tymczasowe i żółte oznakowanie — niezrobione.

## Źródła i ich daty (rozbieżności → pytania)
| źródło | stan | uwagi |
|---|---|---|
| OSM `podlaskie-261108` | rondo DK65/DW671: way 1426801304, edycja 2026-01-05; budowa: 2026-05-10 / 2026-09-13 | jedyne źródło ronda |
| ortofoto 0,25 m (potok) | `knyszyn` 2022-07-29; `knyszyn-s` 2024-05-27 | `pick_latest` wymaga jednej daty: 2024 ma dla `knyszyn` dwa dni nalotu → brane 2022 (otwarte) |
| ortofoto 0,1 m (QA) | 2025-05-25/27 | **skrzyżowanie DK65/DW671 zwykłe, skanalizowane (pasy do skrętu w lewo, wysepki) — nie rondo**; w strefie budowy tylko wycinka ~30 m, bez robót ziemnych |
| NMT 1 m | 2022 | teren sprzed robót |
| BDOT10k / LoD1 2024 / LoD2 2017 powiat 2008 | pobrane, sha w manifestach | 1903 budynki w `knyszyn`, 12 w `knyszyn-s` |
| zdjęcia właściciela | 2024-07 … 2026-07 (bez GPS) | roboty ziemne przy DK65 (2026-07), fontanna na Rynku |

## Pytania do właściciela
1. **Skrzyżowanie DK65 × DW671 (Obozowa × Tykocka): czy dziś jest tam rondo?** OSM (2026-01) — małe rondo
   (oś Ø ~17,5 m); ortofoto 2025-05 — zwykłe skrzyżowanie z pasami do skrętu. Zbudowane wg OSM (WORKING_ASSUMPTION).
2. Gdzie dokładnie budowa dotyka DK65 pod Knyszynem (po której stronie, jak szeroko, czy jest objazd/wahadło)?
   Kadr 20260728_072233 — w którą stronę patrzy?
3. Fontanna na Rynku: w którym miejscu placu stoi (przyjęto środek kręgu w bruku, 761036; 612397)?
4. Czy DK65 między granicą miasta a rondem ma latarnie? (reguła je stawia, nie zweryfikowane).

## Budżet (edytor, overcast, `stats.txt`; hipotezy `docs/06` §6: Low ≤ 300–400 draws / ≤ 600 tys. tris, High ≤ 1000 / ≤ 2 mln)
| | `knyszyn` Low | `knyszyn` High | `knyszyn-s` Low | `knyszyn-s` High |
|---|---|---|---|---|
| WORLD_MEMORY | 95,5 MB | 216,7 MB | 39,9 MB (r1) | 105,8 MB (r1) |
| draws max (kamery świata) | 429 (`tykocka-into-town`), 412 (`goniadzka-jagiellonska`) | 768 | patrz „Wyniki” | patrz „Wyniki” |
| tris max | 370 tys. | 1,66 mln | | |
Dwie kamery `knyszyn` Low są 3–7 % ponad górną hipotezę draws (ulice z gęstą zabudową jednorodzinną: ogrodzenia
i działki) — do pomiaru na telefonie przez lidera, nie strojone tutaj. Czas `build_world`: `knyszyn` 771–1091 s,
`knyszyn-s` 60–90 s; import 9 min na region.

## Walidacja
- Sieć dróg vs ortofoto: `artifacts/knyszyn-0204/plan/knyszyn/r3/*.jpg` (14 miejsc: rondo, Rynek, Tykocka,
  Grodzieńska × Rynek/Podlaska/Nowa/Piłsudskiego, Goniądzka × Jagiellońska/Rynek, Jagiellońska × Pocztowa/Nowa,
  Obozowa × Południowa), `plan/knyszyn-s/r1/*.jpg`. Układ skrzyżowań, liczba wlotów i pierwszeństwo zgodne
  poza rondem (pytanie 1). Spójność nawierzchni: `knyszyn` 12 × `lane_blind_end` (1 na trasie), `knyszyn-s` 0.
- Rendery: `artifacts/knyszyn-0204/vqa/knyszyn/r3-{Low,High}`, `vqa/knyszyn-s/r2-{Low,High}` (12 + 8 kamer miejsc
  + kamery trasy); zdjęcia właściciela oglądane tylko z `research/_incoming` (nie kopiowane).
- Region C i Dojlidy: `build_region` po zmianie BBOX — `roads.graph.json` i `buildings.geojson` bajt w bajt
  (sha w `build_manifest.json` bez zmian).
- Testy: patrz „Wyniki”.

## Otwarte (backlog szlifu)
1. Kafel (−9,8) `knyszyn-w`: wylot DK65, zachodnia część miasta; dziś 37 m za rondem stoi zapora końca świata.
2. Rondo: geometria z OSM jest mała dla zestawu 16,5 m (wyspa Ø ~13 m, pierścień ~4 m) — po odpowiedzi na pyt. 1
   pomiar albo powrót do skrzyżowania skanalizowanego z ortofoto 2025.
3. Rynek: bruk granitowy w łuki, fontanna (dysze, podświetlenie), trawniki na placu, pomnik w parku, kiosk/wiata.
4. Strefa budowy: hałdy, wykopy, maszyny, C-5 z tabliczką, B-33, żółte oznakowanie tymczasowe; teren wg NMT 2022.
5. `pick_latest` dla ortofoto 0,25 m grupuje po dacie dnia, nie po roku (Knyszyn dostał 2022 zamiast 2024).
6. Oznakowanie poziome DK65: linie krawędziowe i podwójna ciągła przy skrzyżowaniach (ortofoto) — generator daje
   tylko oś przerywaną. Latarnie na DK65 w `knyszyn` niezweryfikowane.
7. Budynki: LoD1 + generator, bez szlifu (m.in. kamienica z czerwonym dachem z kadru 20251031 nierozpoznana).

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/ingest.py --region knyszyn [--with orto10]      # i knyszyn-s
uv run --project tools/worldgen tools/worldgen/build_region.py --region knyszyn
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn --context
uv run --project tools/worldgen python scripts/export-route.py --region knyszyn
pwsh scripts/import-region.ps1 -Region knyszyn
pwsh scripts/visual-qa.ps1 -Scene World_knyszyn -Tier Low -Lighting overcast -OutputDir artifacts/knyszyn-0204/vqa/knyszyn/Low
```
