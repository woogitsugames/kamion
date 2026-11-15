# STATUS region-select-fix-0267 (chmura H5, ADR 0267)

Gałąź `region-select-fix-0267` od origin/main `ae372b19c`. Poprawki po recenzji #104 (REVIEW-2026-11-15-s21-code-104).

- [krok 1] `d67-full` = d67 (17) + bialystok-dojlidy, knyszyn-w, dk65-monki-01, dw671-tykocin-01 = 21 (= wszystkie regiony katalogu).
  Zestaw generowany przez `scripts/export-region-catalog.py` (DERIVED_SETS), `--check` exit 0. #126 dodał tylko D71 w docs, nie katalog.
  NASTĘPNY KROK: `python3 scripts/export-region-catalog.py --check` + C# (RegionBuildList pusta lista, RegionCatalog.Load).
