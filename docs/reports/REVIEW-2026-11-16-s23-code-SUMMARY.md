# Recenzje kodu s23 (chmura D, runda 5, D18): podsumowanie dla lidera

Data: 2026-11-16. Przedmiot recenzji to nocne scalenia bez zewnętrznej recenzji kodu. Diff liczony względem
pierwszego rodzica merge. main w chwili recenzji: `639da4e54`. Chmura niczego nie scala ani nie zatwierdza.
Kodu nie zmieniałem, ta gałąź zawiera tylko raporty.

| # | temat | merge / commit | raport | werdykt | najważniejsze |
|---|---|---|---|---|---|
| 1 | `compact_roundabout.py` + int-dk65 w `tools/worldgen/roads/*` (ADR 0218 §5c, 0220, 0222, D75) | `5824464bd` | `REVIEW-2026-11-16-s23-code-compact-roundabout.md` | **FIX** | P1: raport ronda (`built`, `notes`) nie trafia do `roads_qa.json`; P2 ×10: zdublowany pierścień przy całkowitym `r0`, opaska bez dolnej granicy, `ValueError` dla narożnika z 1 punktem, wchłanianie pierścienia przy < 3 ramionach, brak walidacji wartości opcji `compact_roundabout` / `edge_line_spacing` / `edge_line_dashed`, `truck_apron` beton/asfalt + cull, kruche `WALK_MATS`, koszt `edge_dashed_spans`, faza kresek na granicy sekcji, `reason` w overrides knyszyn |
| 2 | `FenceMeshForward.hlsl` (c-regen2, ADR 0239) | `e4fad6868` (`a2a5dfa64`) | `REVIEW-2026-11-16-s23-code-fence-mesh-forward.md` | **FIX** (sama poprawka OK) | Poprawka zgodna z URP 17.3 (`IsAlphaToMaskAvailable` tylko pod `_ALPHATEST_ON`, `_AlphaToMaskAvailable` globalny, ustawiany w `DrawObjectsPass` przy MSAA). P1: importer sprawdza tylko `Shader.Find != null`, więc shader z błędem kompilacji = magenta + mipy box (obiecana w ADR ścieżka awaryjna nie działa). P2: test `ShaderHasError` nie złapał błędu |
| 3 | `EnvironmentLighting.OnDisable` (lamp-test) | `dbfe8c60e` | `REVIEW-2026-11-16-s23-code-environment-lighting.md` | **OK** | P2: przy dwóch aktywnych środowiskach wyłączenie nowszego przywraca kolor domyślny zamiast koloru starszego (ważne przy streamingu); P2: `SetSunElevation` / `NightWindows` nadal przeciekają między scenami i testami |
| 4 | `SpawnSafety` r2 (ADR 0262) | `8778bbe5a` | `REVIEW-2026-11-16-s23-code-spawn-safety.md` | **OK** | P2: przy kolizji tuż przed wyjazdem `limit` blokuje szukanie, więc start w kolizji (nasila znane P2-2), proponowane szukanie wstecz; P2: wyjazd w strefie wjazd + 25 m jest ignorowany, więc start za wyjazdem na bardzo krótkiej trasie |

Żaden P0. Żaden z czterech tematów nie zmienia `ProjectSettings/`, `Packages/` ani asmdef (sprawdzone na liście plików
merge). Brak nowych alokacji w pętli jazdy, fizyka nadal w stałym kroku (temat 4: tylko zapytanie `OverlapBoxNonAlloc`
przy spawnie). Generator jest deterministyczny (sortowanie po id, brak iteracji po nieuporządkowanych zbiorach na
ścieżce wyniku).

## Testy
- Uruchomione (chmura): `uv run --project tools/worldgen python -m pytest tests/gis/test_compact_roundabout_0218.py
  tests/gis/test_dk65_k1_0220.py tests/gis/test_edge_lines_0205.py tests/gis/test_swept_path_0218.py
  tests/gis/test_truck_apron_0218.py tests/gis/test_treerows_0222.py tests/gis/test_start_clear_0262.py -q` → **124 passed**.
- `pytest tests/gis -k "roundabout or marking or junction or apron or edge or gore or knyszyn or dk65 or kerb"` → 385 passed,
  15 skipped (brak `Data/raw`), 2 xfailed, 1 failed = znany `test_forest_0187` (LFS).
- Nieuruchomione: EditMode/PlayMode (brak Unity), kompilacja C#/HLSL (oceniona czytając, HLSL zweryfikowany w źródłach
  URP `6000.3/staging`), `build_world`, VQA.

## Co naprawić przed kolejną regeneracją (kolejność)
1. **Temat 1, P1** (`build_world.py` ~l. 1450): dopisać `"compact_roundabouts": w.stats.get("compact_roundabouts", [])` do
   `roads_qa.json` i test „knyszyn: `built` True, `notes` puste”. Bez tego cicha porażka wyspy (`no patch surface under the island`)
   wyjdzie dopiero na renderze.
2. **Temat 2, P1** (Editor): `RegionImporter.cs:464` i `InstanceImporter.cs:679-680` mają traktować shader z
   `ShaderUtil.ShaderHasError` jak brak shadera, z ostrzeżeniem. Inaczej każdy przyszły błąd kompilacji płotu znowu
   da magentę na całym regionie, zamiast łagodnej mory z s20.
3. **Temat 1, P2-4/P2-6** (tanie, chronią generator przed wyjątkiem z danych): narożnik z 1 punktem oraz walidacja wartości
   `compact_roundabout` / `edge_line_spacing` / `edge_line_dashed` (błędny override → `overrides_stale`, bez wyjątku).
4. Reszta P2 według uznania. Temat 4 P2-1 (szukanie wstecz) warto zrobić razem z otwartym P2-2 ADR 0262.

## Komendy dla lidera (weryfikacja po poprawkach)
- pytest: `uv run --project tools/worldgen python -m pytest tests/gis -k "0218 or 0220 or 0262 or roundabout or apron" -q`
- EditMode: `pwsh scripts/test.ps1 -Platform EditMode` (FenceMeshCoverageTests, RegionLightingProfileTests, StreetLampOpticsTests,
  StartClearanceTests). PlayMode: `pwsh scripts/test.ps1 -Platform PlayMode` (RouteSpawnTests).
- Płot po poprawce importera: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Cameras 'kwadrat-park-gate,truck-at-gate' -OutputDir artifacts/reviews-code-s23/C-Low`.

Gotowe do scalenia (raporty, bez kodu) po weryfikacji lidera: TAK.
