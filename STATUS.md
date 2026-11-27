# STATUS agy-clouds-s24 (chmury: warianty, miękkie krawędzie i usunięcie „kropki” na niebie; dopisek ADR 0332)

- Worktree `agy-clouds-s24`, gałąź `agy-clouds-s24`. Nie scalać / nie pushować (lider).
- [krok 0] Baseline visual-qa przed zmianami: `World_knyszyn-w_High`, `-Pc -Tier High -BuildTarget Win64`, 1920×1080, clear + overcast (`artifacts/agy-clouds-s24/before/{clear,overcast}/`).
- [krok 1-2] Usunięcie ciemnego punktu x~1170, y~142 u źródła: potwierdzony w obu trybach (clear drop +51,3 sRGB, overcast drop +75,7 sRGB) jako plama owada `B=214` w `T_Windscreen_Grime.png` (`obj=(-0.314, 1.702)`). Naprawa w `tools/rendering/windscreen_grime.py` (pominięcie nieprzezroczystych owadów poza polami wycieraczek w górnej środkowej strefie nieba `y > 1.45, |x| < 0.85`), pokrycie brudu zachowane (3,81 % w paśmie 3–6 %). Commit `a837aff1f`.
- [krok 3-4] 3 miękkie warianty map chmur CC0 z Poly Haven 4K PureSky (`tools/rendering/fetch_sky_hdris.py`, `tools/rendering/build_cloud_variants.py`):
  - Var 0 `T_ClearClouds.png` (`kloofendal_48d_partly_cloudy_puresky`, słońce 47,9°): gradient krawędzi p90/p99 `0,162/0,459 → 0,059/0,172` (2,7× miękcej), bez dziury/aureoli/ducha flary.
  - Var 1 `T_ClearClouds_02.png` (`sunflowers_puresky`, słońce 43,0°): szerokie cumulusy + pasma cirrusów (`p90/p99 0,065/0,198`).
  - Var 2 `T_ClearClouds_03.png` (`kloofendal_38d_partly_cloudy_puresky`, słońce 37,8°): delikatne altocumulus/wisp (`p90/p99 0,066/0,153`).
  - `WorldAtmosphere.cs` + `RenderOverrides.cs`: deterministyczny wybór wariantu + lustrzane odbicie względem południka słońca (6 układów o spójnym oświetleniu słońca; leniwe ładowanie 1 tekstury, 0 dodatkowego VRAM) + `rq_cloudvar` / `rq_cloudmirror` / `rq_cloudseed`.
  - `Sky.shader`: miękka krzywa krycia i lekki chłodny/ciepły ton cienia/oświetlenia chmur (D100 saturacja nieba ×2 nietknięta, Overcast nietknięty, +0 odczytów tekstur, ~6 ALU).
- [krok 5] Visual-qa AFTER (`clear`, `overcast`, `var0`, `var1`, `var2`, `var1_mirror`) obejrzane i porównane: kropka `(1170,142)` zniknęła (clear drop `+51,3 → +7,7`, overcast `+75,7 → +1,0`), Overcast bez szyby `diff mean=0,00000 max=0,0`, D100 błękit `B−R 94,9 → 93,2`. EditMode Sky/Cloud/Windscreen: `39 passed, 0 failed, 0 inconclusive, 1 skipped` (XML `artifacts/tests/editmode-20261127-102754.xml`).
- NASTĘPNY KROK: uruchomić testy budżetowe GIS (`test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py`), dopisać ADR 0332 i `docs/LICENSES.md`, skopiować dowody do `C:\Users\matma\Documents\Claude\kamion\artifacts\agy-clouds-s24\`.
