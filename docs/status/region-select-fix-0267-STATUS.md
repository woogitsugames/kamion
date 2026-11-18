# STATUS region-select-fix-0267 (chmura H5, ADR 0267)

Gałąź `region-select-fix-0267` od origin/main `ae372b19c`. Poprawki po recenzji #104 (REVIEW-2026-11-15-s21-code-104).

- [krok 1] `d67-full` = d67 (17) + bialystok-dojlidy, knyszyn-w, dk65-monki-01, dw671-tykocin-01 = 21 (= wszystkie regiony katalogu).
  Zestaw generowany przez `scripts/export-region-catalog.py` (DERIVED_SETS), `--check` exit 0. #126 dodał tylko D71 w docs, nie katalog.
  NASTĘPNY KROK: `python3 scripts/export-region-catalog.py --check` + C# (RegionBuildList pusta lista, RegionCatalog.Load).
- [krok 2] C#: `RegionBuildList.ResolveRegions` (pusta lista po rozwiązaniu = błąd, także plik `regions: []`), `RegionsArgFrom`
  (wartości `-regions` rozbite spacjami przez Start-Process są sklejane), `ParseFile` łapie Exception; `RegionCatalog.ParseOrNull`
  (Load łapie każdy Exception, log `[REGIONS] … unreadable`, null = brak wiersza); separator także NBSP. 4 nowe testy EditMode w
  RegionSelectTests. build-android.ps1: normalizacja `-Regions` (`[\s;]+` → `,`), pusta po normalizacji = throw; `-RegionsFile`
  względem bieżącego katalogu (fallback korzeń repo) + Test-Path + ścieżka absolutna do Unity. Unity/pwsh NIEuruchomione (chmura).
  NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode` (RegionSelectTests 20/20).
- [krok 3] pytest `tests/gis/test_region_catalog_0267.py` 3/3, `--check` exit 0. ADR 0267 + odsyłacz w ADR 0229 §3 (odstępstwo d67 vs D67, d67-full).
  NASTĘPNY KROK: PR do main; lider: `pwsh scripts/test.ps1 -Platform EditMode`, `pwsh scripts/build-android.ps1 -Regions d67-full`.
- [krok 4, H6] merge origin/main @c45cf8d60 (win-build-0261, rail-fix-s21) bez konfliktów → 86d571773. `build-windows.ps1` (0261) ma
  `-Regions` / `-RegionsFile` / `-RegionsAllowMissing`, ale bez normalizacji spacji — nie zmieniany: `RegionBuildList.RegionsArgFrom`
  (C#) skleja rozbite wartości dla każdego targetu, `RegionCatalog.Resolve` dzieli po spacjach, więc `-Regions 'a b'` działa też
  na Windows. Propozycja dla lidera: ta sama normalizacja i rozwiązywanie `-RegionsFile` w build-windows.ps1 (ADR 0267 Otwarte).
  NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode`, `pwsh scripts/build-windows.ps1 -Slot -Regions 'd67,knyszyn-w'`.
