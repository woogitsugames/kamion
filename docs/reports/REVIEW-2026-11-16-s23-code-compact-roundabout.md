# REVIEW s23 code — rondo kompaktowe + zmiany int-dk65 w `tools/worldgen/roads/*` (D18, temat 1)

- Merge: `5824464bd` „Merge int-dk65-s22” (pierwszy rodzic `db3963c2d`). Diff: `git diff 5824464bd^1 5824464bd -- tools/worldgen/roads`
- Pliki w zakresie: `compact_roundabout.py` (nowy, 411 l.), `network.py` (+98), `markings.py` (+132), `junctions.py` (+28),
  `build_world.py` (+18), `meshing.py` (+6), `pipeline.py` (+3), `consistency.py` (+2), `route_km.py` (nowy),
  `swept_path.py` (nowy, narzędzie tabel ADR 0218, poza potokiem). `streetscape/tree_rows*` (0222) są poza zakresem tego tematu.
- Kontekst: ADR 0218 §5c (rondo kompaktowe), 0220 (K1: `edge_line_spacing`, `edge_line_dashed`), 0222, D75 `apron_paving_light`.
- main w chwili recenzji: `639da4e54`.

## Werdykt: FIX (bez P0; 1 × P1 przed kolejną regeneracją, reszta P2)

Kod działa na danych Knyszyna i na testach syntetycznych. Klucz `compact_roundabout` jest jawnym override'em na jednym
way. Bez klucza ścieżka generyczna jest nietknięta: `junctions.py` woła `CR.specs`, które zwraca `[]`, i pilnuje tego
`test_without_the_key_nothing_changes`. Determinizm jest zachowany: grupy i feedery są sortowane po `id`, węzły przez
`sorted(...)`, wysepki przez `sorted(by_far)`, a operacje shapely są deterministyczne. Brak `set`/`dict` bez
sortowania na ścieżce wyniku. Największa luka: raport ronda (w tym `built: false` i `notes`) nie trafia do
`roads_qa.json`, więc cicha porażka wyspy przy regeneracji nie zostanie zauważona bez renderu.

## Testy
- `uv run --project tools/worldgen python -m pytest tests/gis/test_compact_roundabout_0218.py test_dk65_k1_0220.py
  test_edge_lines_0205.py test_swept_path_0218.py test_truck_apron_0218.py test_treerows_0222.py test_start_clear_0262.py -q`
  → **124 passed** (38 s).
- `pytest tests/gis -k "roundabout or marking or junction or apron or edge or gore or knyszyn or dk65 or kerb"` → **385 passed,
  15 skipped (brak `Data/raw`), 2 xfailed, 1 failed** = znany `test_forest_0187::test_edge_texture_has_wall_and_mantle_rows` (LFS).
- Nieuruchomione: `build_world` (zakaz regeneracji i brak `Data/raw`), import, VQA.

## Poprawność — uwagi (plik:linia)

### P1
1. **`pipeline.py:153` + `build_world.py:~1446`: raport ronda nie trafia do QA.** `stats["compact_roundabouts"]` (lista
   `report_one`: `built`, `notes`, `splitters`, `outline_m2`) nigdzie nie jest zapisywany. W
   `Data/Regions/knyszyn/generated/roads_qa.json` jest tylko `cr:…:splitter:*` z gore planu. Przypadek
   `compact_roundabout.py:303-306` („no patch surface under the island” → `built: False`, wyspa i opaska niezbudowane)
   oraz notatki `:181` (trim awaryjny), `:207` (koniec ramienia > 5 cm od obrysu) i `:265` (brak wysepki) są
   po regeneracji niewidoczne.
   **Poprawka:** w `build_world.py` przy `"sides_on_carriageway_culled"` dopisać
   `"compact_roundabouts": w.stats.get("compact_roundabouts", []),`. Do tego test w `test_compact_roundabout_0218.py`
   (albo asercja QA): każdy wpis ma `built is True` i `notes == []` dla knyszyn. To 2 linie i jeden test, przed
   następnym `build_world` knyszyn.

### P2
2. **`compact_roundabout.py:317` — zdublowany pierścień przy całkowitym `r0`.** `rings = [r0] + arange(floor(r0), 0.5, -1)`:
   dla `r0 = 5.0` daje `[5.0, 5.0, 4.0, …]`, czyli pas o zerowej szerokości i 2·n zdegenerowanych trójkątów (render
   i kolizja). Dla `r0 = 5.05` powstaje pas 5 cm z trójkątami-drzazgami. Knyszyn ma `r0 ≈ 2,8 m` (wyspa 2,95 m minus
   krawężnik), więc dziś tego nie widać. **Poprawka:** `rings = [r0] + [r for r in np.arange(math.ceil(r0) - 1.0, 0.5, -1.0) if r < r0 - 0.3]`.
3. **`compact_roundabout.py:136` — brak dolnej granicy szerokości opaski.** `min(ap[2], r - w/2 - 1.0)` przy małym rondzie
   (`r_in < 1 m`) daje ujemną szerokość, a w `build` `ri`/`r0` ≤ 0 (pętle `np.arange`, `1/ri` w `kap`).
   **Poprawka:** jeśli `r - w/2 - 1.0 < 0.5`, pominąć spec z notatką „ring too small for compact mode” i
   `overrides_stale += [id]`.
4. **`compact_roundabout.py:213-226` — narożnik z jednym punktem.** Gdy `idxL[i] == idxR[i1]` (dwa ramiona stykają się
   na obrysie po `closing_r_m`), `seq = [k0]`, `pts` ma 1 punkt, a `np.gradient` (`:226`) rzuca `ValueError`
   i przerywa cały `build_world`. **Poprawka:** przy `len(pts) < 2` dać `pts = [gutter_i, gutter_i1]` i dopisać notatkę.
5. **`junctions.py:316-333` — wchłanianie pierścienia przed sprawdzeniem liczby ramion.** `sp` decyduje, że wszystkie
   łańcuchy wewnątrz klastra są wchłonięte (`:321`). Mimo to `j.compact = None`, gdy `len(arms) < 3` (`:333`). Wtedy
   `compute_corners` działa generycznie na klastrze bez łańcuchów pierścienia, więc powstaje płyta bez ronda i bez
   ostrzeżenia. **Poprawka:** przy `len(arms) < 3` z `sp` dopisać `j.notes`/`overrides_stale` (klucz nieskuteczny)
   albo nie scalać węzłów `sp` w `parent` (`:304-307`), gdy spec ma < 3 ramiona.
6. **`network.py:400-420` — opcje `compact_roundabout` walidowane tylko po kluczach.** Wartości nie są sprawdzane:
   `closing_r_m: "6"` albo `-1` wywali `float()`/`buffer(-rc)` w `corners`. To samo dotyczy
   `edge_line_spacing` (`network.py:392`: `float(...)` bez zakresu, NaN/ujemne przechodzą) oraz `edge_dashed_spans`
   (`markings.py:256`: `S.DASH[o.get("line")]` → `KeyError` dla nieznanego znaku, `dash_m` o złej długości →
   `ValueError`, brak `o["id"]` → `KeyError`). **Poprawka:** jak `_truck_apron`: walidacja typu i zakresu,
   błędny wpis → `overrides_stale`, bez wyjątku.
7. **`network.py:46-48` i `meshing.py:1416` — `truck_apron` z `material: beton|asfalt` (kody 6/7).** Override jest
   akceptowany z `height_m`, ale `road_concrete`/`road_asphalt` należą do `CULL_CARRIAGEWAY`. Opaska staje się więc
   „jezdnią”, a próg i krawężnik wyspy obok niej podlegają `cull_sides_on_carriageway` (to samo uzasadnienie podaje
   komentarz przy kodzie 8). Dziś żaden region tego nie używa. **Poprawka:** dla kodów 6/7 wymuszać `h = 0`
   (flush, jak `apron: asphalt`) albo odrzucać `height_m > 0` → `overrides_stale`. Plus test.
8. **`network.py:47` — `WALK_MATS` rozszerzany przez doklejenie.** Kody 5–8 działają tylko dlatego, że bazowa lista ma
   dokładnie 5 pozycji. **Poprawka:** `assert all(WALK_MATS[k] == v for k, v in TRUCK_APRON_MATS.items())` zaraz pod definicją.
9. **`markings.py:268-280` — koszt `edge_dashed_spans`.** Każda próbka co 2 m × każdy łańcuch regionu × `c.line.project`.
   Przy 2 overrides × ~100 próbek × ~1–2 tys. łańcuchów to rząd 10⁵ rzutów na kafel dk65 (czas generatora,
   nie budżet gry; ESTIMATED, niemierzone). **Poprawka:** prefiltr po bbox łańcucha (`STRtree` na `LineString` łańcuchów, zapytanie `dwithin`).
10. **`markings.py:624-629` — rytm kresek przerywa się na granicach sekcji.** `_solid_with_dashes` dostaje `sa..sb` jednej
    sekcji, a `dashed()` zaczyna rytm od nowa w każdej. Jeśli przęsło K1 obejmuje dwie sekcje łańcucha, na styku
    pojawi się niepełna kreska. Do sprawdzenia na renderze dk65-03/04/05. Ewentualnie liczyć fazę od `span[0]`.
11. **`Data/Regions/knyszyn/overrides.yaml:30-36` — `reason` niezgodny z `set`.** Tekst mówi o łukach 8 m i wyspie
    „gravel”, a `set` ma `closing_r_m: 6.0`, `splitter_w_m: 3.6` (reason: 2–3 m) i domyślne `island_sand`.
    **Poprawka:** zaktualizować `reason` (wpis ronda, dozwolony obszar w tym pliku).

## Przypadki brzegowe sprawdzone i OK
- `_sink_under_island` (`:351-401`) obniża wyłącznie patch tego skrzyżowania (`p.src == j.id`, materiały `road_*`
  i `collision_asphalt`). Wierzchołki na linii cięcia zostają (`< r - 0.02`), więc nad progiem opaski nie ma szczeliny.
- `cull_sides_on_carriageway` pomija `src` zaczynające się od `island:` (`meshing.py:1464`), więc krawężnik wyspy
  na obniżonym patchu nie jest usuwany. `apron_paving_light` nie należy do `CULL_*`.
- `_outward` (`meshing.py:1252`): jawne normalne narożnika są indeksowane przez `round(tag[2]·(len-1))`, w zakresie.
- Kolizja: opaska `collision_paving` (`meshing.py:382`), wypełnienie `collision_paving`/`collision_grass`.

## Budżet
Wyspa Knyszyna: `n = max(48, ⌈2π·6,15/0,6⌉) = 65` punktów na pierścień, `r0 ≈ 2,8 m` → pierścienie [2,8; 2; 1].
Wypełnienie to 2·2·65 + 65 = **325 tris** render (+325 kolizji), a opaska to `_emit_strip` jak dawny pierścień
z 8 klinów (ESTIMATED z kodu, niemierzone; kafel knyszyn, nie region C). Poza knyszyn bajtowo bez zmian (test).
Gra: brak kodu runtime, brak wpływu na GC/fizykę.

## Zgodność z CLAUDE.md
Bez zmian `ProjectSettings/`, `Packages/` i asmdef (sprawdzone na liście plików merge). Liczby z oznaczeniami
WORKING_VALUE/ESTIMATED. Override'y jawne z `reason`/`confidence`/`verify`. Nie znalazłem odwołań do zakazanych źródeł.
