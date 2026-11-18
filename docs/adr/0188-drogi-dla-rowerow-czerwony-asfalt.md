# ADR 0188 — Drogi dla rowerów (DDR): ciepłoszary i czerwonobrązowy asfalt, przejazdy P-11 oraz układ w przekroju
Status: przyjęty (scalony do main 2026-11-15, `5a5ee9166`; status zaktualizowany 2026-11-16); pierwotnie: PROPOSED (gałąź `ddr-0188`, `875719b70`), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0093 (przejście P-10 / przejazd P-11), ADR 0092 (shader asfaltu/nawierzchni), przegląd M65 `docs/reports/REVIEW-2026-11-14-s20-cloud-m65.md` (`research/cloud/p22-red-bike-paths`).

## Kontekst
Wcześniejsza implementacja traktowała wszystkie asfaltowe drogi dla rowerów (DDR) jednolicie jako czerwonawy asfalt i nakładała czerwone pole pod każdy przejazd rowerowy P-11. Dane terenowe zebrane i zweryfikowane w zadaniu M65 (`docs/reports/REVIEW-2026-11-14-s20-cloud-m65.md`, ortofoto GUGiK 5 cm / 8 cm / 25 cm, kadry P11, Mapillary, Panoramax, wytyczne ZDM Białystok) wykazały cztery rozbieżności:
1. **Kolor nawierzchni DDR:** w `bialystok-dojlidy` DDR nie są czerwone — mają ciemny, ciepłoszary asfalt (np. Kuronia P11-001 i skrzyżowanie Mickiewicza/Kuronia P11-063). Czerwonobrązowy (bordowy, matowy) asfalt DDR występuje wyłącznie w `bialystok-industrial-c` w rejonie Ronda Krzysztofa Putry i ul. Gen. W. Andersa.
2. **Czerwone pola przejazdów P-11:** czerwona masa (RAL 3020 wg wytycznych ZDM) nie występuje na każdym przejeździe — m.in. całe skrzyżowanie z P11-063 oraz przejazdy przy Rondzie Putry mają wyłącznie białe kwadraty P-11 bez czerwonego podkładu.
3. **Układ w przekroju (`segregated=yes`):** na części ciągów pieszo-rowerowych (m.in. Kuronia `212811563`, Mickiewicza `180233649`, SW łącznik Ronda Putry `591365139` i ciągi przy Maczka/Elewatorskiej) chodnik leży bliżej jezdni, a DDR dalej od niej (`cycle_side: away`), a zjazdy bramowe (jak przy Kuronia 3, `kuronia3-gate-driveway`) przerywają ciągłość DDR nawierzchnią z kostki bez czerwonego pola.
4. **Szerokości:** wartości domyślne z przepisów minimalnych (2,0 m DDR / 4,0 m ciąg) zaniżały szerokości zmierzone na ortofoto (w Dojlidach 2,45–2,80 m, w C 2,50–3,30 m).

## Decyzja
1. **Rozdzielenie materiałów DDR (`tools/worldgen/streetscape/materials.py`, `tools/worldgen/roads/standards.py`, zestaw `asphalt_tint`):**
   - `cycle_asphalt` `[0.160, 0.151, 0.145]` (WORKING_VALUE, skalibrowane w renderze Low overcast na P11-001): ciepłoszary asfalt dla wszystkich DDR w `bialystok-dojlidy` oraz szarych DDR w `bialystok-industrial-c`.
   - `cycle_asphalt_red` `[0.220, 0.138, 0.130]` (WORKING_VALUE): czerwonobrązowy (bordowy) asfalt wyłącznie dla 11 zweryfikowanych odcinków OSM w `bialystok-industrial-c` (`RED_ASPHALT_WAYS` w `tools/worldgen/streetscape/cycleways.py`: 9 dróg w rejonie Ronda Putry / Andersa + 2 odcinki z `cycleway:both=track`).
   - `cycle_crossing_red` `[0.134, 0.093, 0.093]` (decal `depth_offset_m: 0.003`): czerwona powłoka przejazdów P-11.
2. **Selektywne czerwone pola przejazdów P-11 (`tools/worldgen/streetscape/cycleways.py`, `tools/worldgen/roads/markings.py`):**
   - Czerwone pole (`cycle_crossing_red`) nakładane jest wyłącznie na **25 zweryfikowanych węzłach przejazdów** (`P11_RED_NODES`: 9 w Dojlidach, w tym `5825973689` na P11-056 Dywizjonu 303, oraz 16 w regionie C).
   - Pozostałe przejazdy P-11 (w tym całe skrzyżowanie Mickiewicza/Kuronia P11-063 i przejazdy Ronda Putry) dostają wyłącznie białe kwadraty P-11. Węzły z `P11_NONE_NODES` (4 węzły) nie dostają oznakowania przejazdu.
   - Poprawiono `_drape_crossing` i ścieżkę P-11 w `markings.py`: brak cichego gubienia `cycle_crossing_red` na obrzeżach płyt oraz zakaz degradacji nieudanych P-11 do pasów P-10.
3. **Układ w przekroju (`cycle_side: away`) i zjazd Kuronia 3:**
   - Zdefiniowano `AWAY_WAYS` (8 odcinków OSM: `212811563, 180233649, 1534813757` w Dojlidach oraz `344253261, 257367436, 268470393, 591358181, 591365139` w C) oraz odpowiadające im wpisy w `Data/Regions/bialystok-dojlidy/overrides.yaml` i `Data/Regions/bialystok-industrial-c/overrides.yaml`.
   - Dodano zjazd z kostki `kuronia3-gate-driveway` przerywający DDR na Kuronia 3 (P-23 po obu stronach, bez czerwonego pola).
4. **Szerokości per odcinek (`M65_WIDTHS` w `cycleways.py`):**
   - Przypisano zmierzone na ortofoto szerokości DDR `2,45–2,80 m` w Dojlidach (mediana ~2,60 m; szerokość całkowita ciągów `4,45–5,00 m`) oraz `2,50–3,30 m` w regionie C.

## Wyniki
### Statystyki generatora (`build_world.py`, r4)
- **Dojlidy (`artifacts/ddr-0188/bw-doj-r4.log`):** 22 odcinki OSM, zbudowano 19 (`ddr: 6`, `segregated: 13`, pominięto 3 `shared`), łączna długość `6894,3 m`, `planned_m2 = 25 108 m²`, `p23 = 5`, `P-11 cycle crossing = 18` (`in junction = 15`), `P-11 red surfacing = 18`.
- **Region C (`artifacts/ddr-0188/bw-c-r4.log`):** 71 odcinków OSM, zbudowano 41 (`ddr: 22`, `segregated: 19`, pominięto 28 `shared` i 2 `unpaved`), łączna długość `5125,5 m`, `planned_m2 = 15 705 m²`, `p23 = 9`, `P-11 cycle crossing = 24` (`in junction = 18`), `P-11 red surfacing = 23`, powierzchnia `cycle_asphalt_red = 8516 m²`, `cycle_red = 407 m²`, `kerb triangles inside paved gore fills: 0`.

### Wizualnie (r4, `artifacts/ddr-0188/sbs-r4/`)
- `sbs-D-High-photo-P11-001.jpg`, `D-Low-photo-P11-001.jpg`: DDR na Kuronia w ciepłej szarości z P-23, białą linią krawędziową/osią oraz przerwaniem na zjeździe z kostki do bramy Kuronia 3 — zgodne ze zdjęciem.
- `sbs-D-High-photo-P11-056.jpg`: czerwone pole przejazdu P-11 na skrzyżowaniu z ul. Dywizjonu 303 zgodne ze zdjęciem.
- `sbs-D-High-photo-P11-063.jpg`: białe przejazdy P-11 na skrzyżowaniu Mickiewicza/Kuronia bez czerwonego pola.
- `sbs-C-High-g3_c_1173244557941023.jpg`, `sbs-C-High-g3_c_295679109352815.jpg`, `C-Low-putry-above.jpg`: wyraźnie czerwonobrązowy asfalt DDR wokół Ronda Putry obok chodnika z kostki, białe P-11 na rondzie i czerwone na wyznaczonych przejazdach.

### Budżet A/B w Unity (r4: `artifacts/ddr-0188/r4/*/stats.txt`, `import-*-r4.log`)
Estymata klatki (przed SRP batchingiem; `Low` 1440×810 `renderScale=0.75` msaa 2, `High` 1920×1080 `renderScale=1` msaa 2, RTX 5070):

| Region / Tier | Kadr | `drawsEst` | `trisExact` | `instancedTrisExact` | `frame` [ms] |
|---|---|---:|---:|---:|---:|
| **D-Low** | `photo-P11-001` | 346 | 469 944 | 9 272 | 2,22 |
| D-Low | `photo-P11-056` | 127 | 164 469 | 2 073 | 1,91 |
| D-Low | `photo-P11-063` | 334 | 346 302 | 16 418 | 3,07 |
| D-Low | `photo-P11-094` | 208 | 299 071 | 16 973 | 2,35 |
| D-Low | `photo-P11-129` | 175 | 230 837 | 18 934 | 2,63 |
| D-Low | `route-s0152` | 146 | 161 402 | 2 281 | 1,74 |
| D-Low | `route-s1370` | 336 | 274 490 | 11 184 | 2,44 |
| **D-High** | `photo-P11-001` | 461 | 709 564 | 32 498 | 4,65 |
| D-High | `photo-P11-056` | 217 | 302 783 | 9 599 | 3,38 |
| D-High | `photo-P11-063` | 599 | 873 691 | 91 473 | 4,95 |
| D-High | `photo-P11-094` | 527 | 873 195 | 65 017 | 4,90 |
| D-High | `photo-P11-129` | 190 | 301 454 | 62 120 | 6,06 |
| D-High | `route-s0152` | 638 | 637 240 | 52 500 | 4,05 |
| D-High | `route-s1370` | 491 | 629 994 | 43 982 | 4,31 |
| **C-Low** | `dk8-dk19-exit` | 76 | 108 246 | 63 686 | 3,01 |
| C-Low | `fire-station-above` | 280 | 278 507 | 26 240 | 3,68 |
| C-Low | `putry-above` | 311 | 321 845 | 16 593 | 2,92 |
| C-Low | `sbs-g3-b-1528935774382039` | 429 | 373 519 | 49 849 | 3,61 |
| C-Low | `sbs-g3-b-297817221966185` | 431 | 389 910 | 26 416 | 3,52 |
| **C-High** | `dk8-dk19-exit` | 91 | 143 582 | 81 646 | 4,74 |
| C-High | `fire-station-above` | 553 | 687 026 | 93 564 | 7,51 |
| C-High | `putry-above` | 427 | 605 811 | 33 037 | 5,57 |
| C-High | `sbs-g3-b-1528935774382039` | 895 | 1 122 138 | 100 382 | 7,75 |
| C-High | `sbs-g3-b-297817221966185` | 868 | 1 082 714 | 75 286 | 7,10 |

**`WORLD_MEMORY` (`import-doj-r4.log` / `import-c-r4.log`):**
- **Dojlidy Low:** `render_meshes=65.8 MB`, `instances=18.2 MB`, `collision_src=15.6 MB`, **`total=99.6 MB`** (`markings 2.3`, `paved 2.9`).
- **Dojlidy High:** `render_meshes=181.2 MB`, `instances=18.2 MB`, `collision_src=15.6 MB`, **`total=214.9 MB`** (`markings 2.3`, `paved 2.9`).
- **Region C Low:** `render_meshes=84.4 MB`, `instances=22.6 MB`, `collision_src=17.2 MB`, **`total=124.2 MB`** (`markings 3.6`, `paved 3.5`).
- **Region C High:** `render_meshes=227.3 MB`, `instances=22.6 MB`, `collision_src=17.2 MB`, **`total=267.0 MB`** (`markings 3.6`, `paved 3.5`).

### Walidacja (testy)
- **Unity EditMode** (`pwsh scripts/test.ps1 -Platform EditMode` → `artifacts/tests/editmode-20261115-112422.xml`): **581 total, 580 passed, 0 failed, 1 skipped** (`Skipped:Ignored`).
- **Pytest celowany** (`uv run --project tools/worldgen python -m pytest tests/gis/test_cycleways_0188.py tests/gis/test_markings_pl_standards.py -q`): **36 passed** in `0.49s`.
- **Pytest pełny GIS** (`uv run --project tools/worldgen python -m pytest tests/gis -q`): **1157 passed, 5 failed, 2 xfailed** in `1680.33s` (`0:28:00`). Żaden z 5 błędów nie wynika z logiki 0188 (znane upstream / odświeżenie artefaktów po zmianie `overrides.yaml` i generatora):
  1. `tests/gis/test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage` — niezgodność w `InstanceImporter.cs` na scalonej gałęzi.
  2. `tests/gis/test_hero_bridge.py::test_asset_matches_spec` — nieaktualny `spec_sha256` dla `viaduct_biezenstwa` (wymaga przebudowy w Blenderze).
  3. `tests/gis/test_hero_bridge.py::test_asset_lods_and_budget` — `stretch_04` `tris_high = 2 024 890 > 2 000 000`.
  4. `tests/gis/test_road_fidelity.py::test_report_not_stale` — `fidelity_qa.json` nieaktualne dla zmienionych `overrides.yaml`, `build_world.py`, `markings.py`, `pipeline.py`, `standards.py` (do odświeżenia przez `tools/worldgen/fidelity/run.py` przy integracji).
  5. `tests/gis/test_world_v31.py::test_frame_budget_with_forest_hlod` — przekroczenie `2 000 000` na kamerze `stretch_04` w regionie C (`2 024 890`).

## Otwarte
- **Korekta `cycle_asphalt_red`:** kolor bordowej DDR w C jest skalibrowany jako `WORKING_VALUE` z ortofoto (bez bezpośredniego zdjęcia z poziomu ziemi w C dla barwy masy).
- **Wątek `fidelity_qa.json`:** przed scaleniem do `main` / po scaleniu lider powinien uruchomić `tools/worldgen/fidelity/run.py`, aby odświeżyć `fidelity_qa.json`.
- **Odcinki niepewne i dzielone (M65 §5 A/C):**
  - `237088754` (Dojlidy) ma zmienną stronę DDR na długości (25 % `away`, 75 % przy jezdni) — wymaga ewentualnego podziału odcinka w przyszłości.
  - 6 niepewnych odcinków w C (m.in. `257367436`, `268470393`, `741639504`) pozostawiono jako ciepłoszare (`WORKING_VALUE`).
  - 10 drobnych przejazdów na uliczkach osiedlowych w C pozostawiono bez czerwonego pola (`WORKING_VALUE`).
- **Zrzut z telefonu (Bramka 1/2):** do wykonania przy integracji na `main`.

## Odtworzenie
```powershell
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
pwsh scripts/import-region.ps1 -Region bialystok-dojlidy
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
```
