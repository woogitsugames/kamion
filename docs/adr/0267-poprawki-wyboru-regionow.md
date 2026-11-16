# ADR 0267 — poprawki wyboru regionów po recenzji #104 (`d67-full`, pusta lista, spacje, odporny katalog)
Status: przyjęty (scalony do main 2026-11-16, `3e9ef52fc`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (chmura H, zadanie H5, gałąź `region-select-fix-0267`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
Powiązane: ADR 0229 (wybór regionów), D67, D71 (zestaw `d67-full`), D72 (limit APK 10 GB), D73 (Windows główną platformą),
`docs/reports/REVIEW-2026-11-15-s21-code-104.md` (lista FIX 1–7), ADR 0261 (build Windows).

## Kontekst
Recenzja #104 zostawiła 1× P1 i 6× P2. Właściciel w D71 rozstrzygnął P1: dodać `d67-full`, a `d67` zostawić jako lżejszy
wariant. Pozostałe poprawki to odporność narzędzi buildu i menu.

## Decyzja
1. **`d67-full`** = `d67` (17) + `bialystok-dojlidy`, `knyszyn-w`, `dk65-monki-01`, `dw671-tykocin-01` = **21 regionów**
   (wszystkie z katalogu, kolejność: trasa główna, potem odgałęzienia). Zestaw jest **pochodny**: definicja w
   `scripts/export-region-catalog.py` (`DERIVED_SETS`), skrypt rozwija go w `region_catalog.json` (resolver C# nie
   zagnieżdża zestawów), a `--check` zgłasza brak lub nieaktualność. Rozmiar APK: **ESTIMATED 1407–1948 MB** (recenzja #104,
   jak `all`). HANDOVER s22 podaje build lidera `-Regions d67-full` = 1 821 MB. To nie mój pomiar, a build był z drzewa
   `-dirty`. Według D72 limit wynosi 10 GB.
2. **Pusta lista po rozwiązaniu jest błędem buildu.** `RegionBuildList.ResolveRegions`: gdy podano `-regions` lub
   `-regionsFile`, a wynik jest pusty (`-Regions ','`, plik z `"regions": []`), build kończy się błędem z komunikatem
   „resolves to no region”. Bez argumentów lista scen zostaje bez zmian.
3. **Spacje i średniki jako separatory, w dwóch warstwach.** `build-android.ps1` normalizuje `-Regions`
   (`[\s;]+` → `,`, sklejanie przecinków, pusty wynik = `throw`). Po stronie C# `RegionBuildList.RegionsArgFrom` skleja
   wszystkie argumenty po `-regions` aż do następnego `-…`, więc wartość rozbita przez `Start-Process` dociera w całości.
   `RegionCatalog.Resolve` dzieli tokeny po `,`, `;`, białych znakach i NBSP.
4. **`RegionCatalog.Load` nie rzuca.** Nowa funkcja `ParseOrNull` łapie każdy `Exception`, w tym `ArgumentException`
   z `JsonUtility` przy uszkodzonym JSON. Błąd trafia do logu `[REGIONS] region catalog unreadable…`, a wynik `null`
   oznacza menu bez wiersza regionów. `ParseFile` (plik `-regionsFile`) też łapie `Exception`.
5. **`-RegionsFile` (FIX 5).** Ścieżka jest liczona względem bieżącego katalogu, z zapasowym korzeniem repo dla
   udokumentowanego `Data/build_regions.json`. `Test-Path` działa przed startem Unity, a do Unity trafia ścieżka absolutna.

## Otwarte
- FIX 6 (`scene=<id>` regionu spoza APK → zostać w menu z logiem, `GameBootstrap.cs`) i FIX 7 (podwójne
  `RouteGraph.Load`, `DrivingLabBootstrap.cs`) nie są zrobione. Te pliki należą do logiki startu (spawn-fix-0262).
- `scripts/build-windows.ps1` (ADR 0261) powinien przejąć tę samą normalizację `-Regions` i obsługę `-RegionsFile`.
  `BuildCommands.cs` nie był zmieniany. `RegionBuildList.AppendFromCommandLine` działa tak samo dla każdego targetu.
- Wczesna walidacja tokenów w PowerShell (`export-region-catalog.py --resolve`) nie jest zrobiona.
- Ścieżki ze spacjami w innych argumentach `Invoke-UnityBatch` (`Start-Process -ArgumentList`) mają ten sam problem
  quotingu. Zachowanie w PS7 jest UNVERIFIED.

## Weryfikacja
- Python: `python3 scripts/export-region-catalog.py --check` daje exit 0. `pytest tests/gis/test_region_catalog_0267.py`
  przechodzi 3/3.
- Unity EditMode `RegionSelectTests` (20 testów, w tym 4 nowe) i `pwsh` nie zostały uruchomione, bo chmura nie ma Unity,
  dotnet ani pwsh. Lider uruchamia `pwsh scripts/test.ps1 -Platform EditMode`.
