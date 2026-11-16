# ADR 0282 — Budżet trójkątów gęstych kafli miejskich: estymator zgodny z Unity + reguły LOD w odległościach bliskich

Status: Proposed (agent rendering-perf, chmura D r7, zadanie D28, gałąź `dense-lod-0282`), 2026-11-16. Analiza + prototyp
narzędzia; **nic nie jest podpięte do generatora ani do Unity**. Do decyzji lidera (kolejność wdrożenia, który budżet
obowiązuje) i do scalenia przez lidera.
Powiązane: ADR 0278 (plan mapy, PR #150: kafle 5–9 ESTIMATED 2,6–3,75 M tris High), 0221 (budget-fix, stretch_04 C
1,99 M), 0015 (forest HLOD + far facades LOD1), 0085 (far field), 0141 (skyline), 0124 (plot view cull), 0012
(warstwy LOD chunka), 0238 (typologia frontów), 0260/0266 (PC platformą główną, budżety PC), `docs/PERFORMANCE_BUDGETS.md`.

## Kontekst
Plan mapy (ADR 0278) przenosi `mesh_budget.frame_estimate` (build_world) z kafli zbudowanych na kandydatów regresją
po liczbie budynków i dostaje dla gęstych kafli miejskich 2,6–3,75 M trójkątów na kamerę High wobec bezpiecznika 2 M.
Pytanie: jak zejść do budżetu (LOD budynków, HLOD kwartałów, detal frontów, roślinność/propsy, culling).
Budżety: mobilne High **1,5 M** / Ultra 2 M „triangles in view” (`PERFORMANCE_BUDGETS.md`, 🔒 od D73); PC
`tools/pcperf/budgets/pc-budgets.json` (WORKING_VALUE): min/Low 2 M, zalecany/High 6 M, wysoki/Ultra 12 M (tris.p95).
Bezpiecznik 2 M w `frame_estimate` pochodzi z hipotezy docs/06 §6 (era mobilna).

## Ustalenia (dane z gita; wszystko ESTIMATED, liczone na CPU, nie GPU/telefon)
1. **`frame_estimate` to górna granica, nie liczba z Unity.** Model liczy każdy chunk i instancję w promieniu 200 m we
   wszystkich kierunkach (także za kamerą), klin 120° do 1,6 km, teren LOD0 jako pełną siatkę 1 m (Unity: pas 1 m tylko
   przy drogach, `RegionImporter.TerrainBandM` 15 m, udział 0,407 na C), meble bez odcięcia na High (Unity: do końca LOD1
   chunka ≈ 719 m), budynki LOD0 do 700 m (Unity: 449 m od środka chunka), drzewa LOD0 35 m / LOD1 80 m (Unity High:
   `treeCardLodScale` 0,5 → 10 m / 30 m). Prototyp odtwarza model legacy **dokładnie** (624/624 kategorii × kamer,
   6 regionów) i dodaje model **runtime** (tabela `WorldSceneBuilder.k_HighLods`, LODGroup z `suggested_switch_m` + 0,7
   chunka × lodBias, frustum kamery QA 2340×1080, pas terenu, polityka drzew tieru).
2. **Kalibracja na SceneStats w gicie** (visual-QA `stats.txt`, ta sama kamera, High, mesh + instancje):
   kleeberga (14 kamer, `artifacts/bialystok-dk65-t2-0206/vqa-r4`, 1920×1080): Unity/legacy **0,35–0,65 (mediana
   0,47)**, Unity/runtime 0,51–0,79 (0,66); C (3 kamery, `artifacts/dusk-cal-0199/final`): 0,52–0,62 (0,56) / 0,51–0,57
   (0,56). Ten sam wynik na manifeście z commita renderu (`2c2bd1a7b`): Unity/runtime 0,52–0,82. Model runtime nadal
   zawyża (różnica nie rozłożona — m.in. cieńsze meble ADR 0240, pas terenu poza C) → traktować go jako górną granicę.
   Przykład: kleeberga `route_s0159` legacy 2,51 M, runtime 1,74 M, **Unity 1,10 M** (990 drawsEst).
3. **Budynki to mały udział klatki.** Najgorsza kamera runtime: teren 0,69–0,88 M (41–53 %), drogi 0,17–0,62 M, meble
   (z działkami) 0,08–0,28 M, **budynki 0,16–0,29 M (9–16 %)**, far field 29–56 k, drzewa/propsy < 50 k. Agresywniejsze LOD
   budynków daje dziesiątki tysięcy trójkątów, nie miliony; legacy 3,29 M Maczki to w 1,09 M drzewa LOD0/LOD1 policzone
   za gęsto (model, nie treść).
4. **Pomiar generatora budynków** (`building_probe`: `streetscape.buildings_mesh` na `buildings.geojson` kafla, płaski
   teren; LOD0 sondy = manifest −3,3…+0,5 %): detal otworów (ościeża `reveal_*`, parapety, ramy) 24–30 % LOD0, rury/rynny
   (`downpipe`) 14–18 % → **LOD0b (bez nich) = 0,56–0,60 LOD0**; blok wielka płyta LOD0 ≈ 11 300 tris vs LOD1 300;
   **HLOD kwartału** (reguła `block_hlod_tris`: scalenie śladów w klasach wysokości co 3 m, płaski dach) = 0,11–0,14 LOD1;
   LOD1 ma 14–20 materiałów na chunk (mediana; max 38) → HLOD w jednym materiale far field oszczędza ~13–19 draw na chunk (drawsEst przed SRP batching; −260…−665 na najgorszej kamerze przy progu ≈ 900 m od środka, górna granica).
5. **Granulacja chunka 256 m jest twardym limitem.** LODGroup przełącza cały chunk po odległości do środka, więc żadna
   reguła nie może zejść poniżej odległości bliskiej = środek − 0,7 chunka (179 m). Dziś LOD0 budynków kończy się na
   bliskiej ≈ 270 m — reguła „LOD1 od 250 m” liczona od środka (pierwsza wersja prototypu) pokazałaby prymityw LOD1 70 m
   od kamery. Wszystkie propozycje są więc w **odległościach bliskich** (jak `suggested_switch_m`); bliżej da się zejść
   tylko mniejszymi komórkami LOD (P2c: budynki w komórkach 64 m, margines 45 m).
6. **Istniejące mechanizmy**: forest HLOD komórek (0015, High od 120 m), fasady dalekie LOD1 (UV1 siatka okien, 0015),
   far field (0085, pierścień 1–4,5 km skrócony perspektywicznie, materiał `far_field_buildings` z trybem okien w alfie
   wierzchołka), skyline (0141), pas terenu (RegionImporter), `PlotViewCull` (0124, tylko lusterka). HLOD kwartałów
   powinien użyć języka far field (jeden materiał, kolor w wierzchołkach, okna UV1), żeby szew LOD1↔HLOD↔far field był
   spójny. Occlusion culling: przy jednym rendererze warstwy na 256 m prawie nic nie jest w całości zasłonięte — bez
   podziału rendererów zysk ≈ 0 (UNVERIFIED), z podziałem rośnie liczba draw; nie zalecane teraz.

## Propozycje — zysk na najgorszej kamerze (4 gęste kafle; ESTIMATED; `docs/reports/map/dense_lod_0282.json`)
| # | element (odległość bliska) | legacy Δ | runtime Δ | koszt: draw / pamięć / wygląd | ryzyko |
|---|---|---|---|---|---|
| P0 | estymator: drzewa wg polityki tieru (+ docelowo frustum, pas terenu) | 0–731 k (Maczka 3,29→2,56 M) | — | 0 / 0 / 0 — zmiana bramki, nie treści | niskie; zmienia `test_world_v31` (lider/D26) |
| P1 | LOD1 budynków od 200 m (dziś ~270 m) | 63–159 k | 2–42 k | 0 / 0 / prymityw LOD1 z oknami UV1 od 200 m (6 px/okno) | średnie (pop, fadeMode None) |
| P2 | LOD0b od 100 m: otwory płaskie, bez ościeży/parapetów/rur | 32–76 k | 11–26 k | 0 / +0,6 LOD0 w pamięci (Maczka ≈ +1,6 M tris ≈ +50 MB ESTIMATED) / rura Ø0,1 m < 1 px od 100 m — mniej migotania | niskie wizualnie, wysokie pamięciowo |
| P2c | komórki LOD budynków 64 m: LOD0 ≤ 60 m, LOD0b ≤ 250 m, LOD1 dalej | 78–179 k | 41–82 k | +draw (16 rendererów zamiast 1 na chunk blisko, ~+200–500 drawsEst ESTIMATED) / jak P2 | średnie |
| P3 | HLOD kwartałów od 700 m (0,30 LOD1, dachy spadziste zachowane) | 33–70 k | 30–71 k | **−260…−665 drawsEst** (górna granica) / +2–6 MB / 0,75 m/px, schodki wysokości zostają | średnie (szew kolorów LOD1↔HLOD) |
| P4 | zestaw działek (płoty, bramy, żywopłoty) do 200 m; nawierzchnie działek bez zmian | 75–296 k | 0–74 k | −draw / 0 / płot 1,5 m = 7 px przy 200 m | średnie (ulice podmiejskie) |
| P5 | meble drogowe i oznakowanie poziome do 300 m | 74–176 k | 3–37 k | −draw / 0 / linia 0,15 m = 0,5 px (migotanie znika) | średnie (długie proste, bariery) |
| P6 | propsy −15 %, drzewa −10 % w dalekich pierścieniach | 17–115 k | 1–5 k | 0 / 0 / rzadsze | **nie zalecane** (zysk tylko w modelu legacy) |
| P7 | pas terenu 1 m do 150 m (dziś ~270 m), dalej siatka 2 m | 0 | 77–122 k | 0 / 0 / szew teren↔krawędź jezdni 150–270 m | średnie-wysokie (skarpy, krawężniki) |
| Σ | P1–P7 (P2c zamiast P1/P2) | 397–761 k | 152–347 k | | |

Najgorsza kamera po Σ (P2c): runtime C 1,58 M, kleeberga 1,54 M, knyszyńska 1,10 M, Maczka 1,74 M (mediany 0,78–1,47 M);
po kalibracji (×0,51–0,82) **Unity ≈ 0,56–1,43 M**. Kafle planu 0278 (legacy 2,6–3,75 M, ekstrapolacja współczynnikami
Maczki 0,636 / 0,531 i kalibracji ×0,655, przedział ×0,51–0,82): dziś Unity ≈ 1,08–1,56 M (0,84–1,96 M), po Σ
≈ 0,90–1,30 M (0,70–1,63 M). Na PC (High 6 M, Low 2 M) gęste kafle mieszczą się już dziś; budżet mobilny High 1,5 M —
najgorszy kafel planu na granicy, po Σ zwykle poniżej.

## Decyzja (propozycja)
1. **Najpierw zmierzyć, potem ciąć** (żelazna zasada 2): visual-QA High na Maczce i Knyszyńskiej (brak `stats.txt` High
   w gicie) + `--stats` prototypu → współczynnik Unity/legacy dla najgęstszych kafli. Bramka budżetu gęstych kafli =
   SceneStats z Unity (`trisExact` + instancje) ≤ budżet tieru, nie `frame_estimate`.
2. **P0** w `build_world.mesh_budget` (lider; plik wspólny z D26): drzewa i propsy wg polityki tieru, frustum zamiast koła
   200 m, pas terenu — `frame_estimate` przestaje karać kafle za treść, której Unity nie rysuje. Bezpiecznik 2 M zostaje
   na model legacy do czasu decyzji, który budżet (mobilny 1,5 M czy PC) obowiązuje kafle miejskie.
3. Kolejność treści, jeśli pomiar Unity przekroczy budżet: **P3** (głównie draw), **P4**, **P5**, **P2c** (LOD0b w
   komórkach — dopiero z pomiarem pamięci), **P7** ostatnie (ryzyko szwu). P6 nie wdrażać. P1 bez P2c daje mało (2–42 k).
4. Każdy element = przełącznik w profilu jakości (`QualityProfile` + A/B przez `-Rq`) przed włączeniem domyślnym; lusterka
   bez zmian (ADR 0042/0124).

## Jak to wdrożyć (szkic dla lidera; nic z tego nie jest w tym PR)
- Unity (`WorldSceneBuilder`, lider): `merged_lod_table()` daje tabelę jednego LODGroup na chunk z dodatkowymi poziomami
  (Σ chunkowe: 8 poziomów, przełączenia 279/329/379/479/719/879/1319 m od środka przy fov 60, lodBias 1,5; switch =
  koniec − 0,7 chunka). P2c wymaga osobnych LODGroup na komórki budynków (warstwa `buildings` dzielona przy imporcie).
- Generator (`buildings_mesh.py`, world3): warstwa `buildings_mid` (LOD0b) = `wall_with_openings` z otworami jak w LOD1
  (atlas UV1, bez ościeży), bez `FK.downpipe`, parapetów i ram; warstwa `buildings_hlod` = `block_hlod_tris` z dachem
  spadzistym tam, gdzie LOD1 ma gable, w materiale `far_field_buildings` (`far_field._add_building`).
  Zmieni manifest wszystkich kafli (nowe węzły) — przebudowa world3, nie teraz.
- Testy: `tests/gis/test_dense_lod_0282.py` (narzędzie); po wdrożeniu EditMode na tabelę LOD i kontrakt warstw.

## Pomiar (komendy dla lidera, Windows)
```
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-maczka -Tier High -Lighting overcast -OutputDir artifacts/dense-lod-0282/maczka-High
pwsh scripts/visual-qa.ps1 -Scene World_bialystok-knyszynska -Tier High -Lighting overcast -OutputDir artifacts/dense-lod-0282/knyszynska-High
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -OutputDir artifacts/dense-lod-0282/C-High
uv run --project tools/worldgen python tools/worldgen/qa/dense_lod_estimate.py --buildings `
  --stats bialystok-maczka=artifacts/dense-lod-0282/maczka-High/stats.txt@2340x1080 `
  --stats bialystok-knyszynska=artifacts/dense-lod-0282/knyszynska-High/stats.txt@2340x1080 `
  --stats bialystok-industrial-c=artifacts/dense-lod-0282/C-High/stats.txt@2340x1080 --json artifacts/dense-lod-0282/calib.json
pwsh scripts/build-windows.ps1 -Regions 'bialystok-maczka,bialystok-knyszynska'
pwsh scripts/pc-metrics.ps1 -Exe artifacts/win/<build>/Kamion.exe -Scene bialystok-maczka -Tier High -Fps 60 -Class zalecany
```
`stats.txt`: `trisExact` (renderery) + `trianglesExact` z linii `instanced` = trójkąty kamery; `drawsEst`,
`shadowDrawsEst` = draw przed SRP batching. `frame_estimate`: `Data/Regions/<id>/generated/streetscape_qa.json` →
`mesh_budget.frame_estimate[].tris_high`. Telefon (🔒 D73): `pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch
-DurationSeconds 90` dopiero po odblokowaniu ścieżki mobilnej.

## Odtworzenie
`uv run --project tools/worldgen python tools/worldgen/qa/dense_lod_estimate.py --buildings --json docs/reports/map/dense_lod_0282.json`
(≈ 2,5 min; bez `--buildings` 10 s) · `uv run --project tools/worldgen python -m pytest tests/gis/test_dense_lod_0282.py -q`.
Wejścia tylko z gita: `Data/Regions/<4 kafle>/generated/{world_manifest,control_cameras,streetscape_qa}.json` (odczyt),
`buildings.geojson`, `overrides.yaml`, `region.yaml`, `art-source/world/vegetation/trees_meta.json`, dwa `stats.txt`.

## Konsekwencje
- Nic w `generated/*`, `game/**`, zablokowanych kaflach. Wpływ na kafle przy world3: zero (prototyp niepodpięty).
- Ryzyko: model runtime zawyża 1,2–2× (kalibracja na 17 kamerach dwóch kafli, jeden starszy build); rozkład drzew/propsów
  przybliżony (pliki instancji w `Data/raw`); współczynniki LOD0b/HLOD z generatora na płaskim terenie.
- Otwarte: brak `stats.txt` High dla Maczki/Knyszyńskiej; który budżet (mobilny/PC) obowiązuje kafle miejskie; sąsiednie
  kafle w widoku po streamingu (dziś far field) nie są w żadnym modelu.
