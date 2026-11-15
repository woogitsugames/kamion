# ADR 0229 — wybór regionów w buildzie (`-Regions`) i wybór regionu w menu startowym
Status: Proposed (chmura E, agent E2, gałąź `region-select-0229`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
Powiązane: D67 (`HANDOVER.md`, s21: korytarz Białystok → DK65 → Knyszyn w następnym APK), ADR 0011 (import glTFast,
sceny `_Generated`), ADR 0012 (tiery treści, `-worldHigh`), ADR 0025 (udział świata w APK, `-noWorld`), ADR 0150 (graf
nawigacji `*_route.bytes`), ADR 0169 (zamknięcie drogi 60 m przed krawędzią kafla), ADR 0203–0214 (kafle korytarza).

## Kontekst
APK zawiera dziś tylko sceny z `EditorBuildSettings` w gicie: Boot, DrivingLab, WorldC (`BuildScenes.Paths`). Pozostałe
20 regionów (`Data/Regions/*`, sceny `Assets/_Generated/World/<id>/World_<id>.unity` po `scripts/import-region.ps1`) nie
trafia do buildu, a menu startowe zna tylko trasy G3-A/G3-B regionu C. Właściciel (D67) chce korytarz w następnym APK.
`EditorBuildSettings`, sceny wspólne (Boot w YAML) i asmdef są poza zakresem tego zadania.

## Decyzja
1. **Lista scen składana w pamięci.** `BuildCommands.BuildAndroid` dokleja sceny regionów do listy z `EditorBuildSettings`
   tylko dla jednego `BuildPlayerOptions` (`Game.Editor.Build.RegionBuildList`); plik `EditorBuildSettings.asset` się nie
   zmienia. Argumenty Unity: `-regions "<tokeny>"`, `-regionsFile <plik JSON>`, `-regionsAllowMissing`; z `-worldHigh`
   dochodzą sceny `_High` wymienionych regionów, jeśli istnieją (brak = ostrzeżenie). Region wymieniony, a nie
   zaimportowany = **błąd buildu** (exit 4, `BUILD_RESULT: Failed (-regions: …)`), chyba że `-regionsAllowMissing`.
   Bez argumentów lista jest identyczna jak przed zmianą (test `ComposeScenes_NoRegions_KeepsBuildSettingsListExactly`).
   `-noWorld` nadal usuwa wszystkie sceny `_Generated/World`. `scripts/build-android.ps1` przekazuje `-Regions`,
   `-RegionsFile`, `-RegionsAllowMissing`; nazwa APK dostaje sufiks `-regions`.
2. **Tokeny** (wspólne dla `-regions` i pliku): id regionu, alias (`c`), id bez `bialystok-` (`dojlidy`), nazwa zestawu
   (`d67`), `all`, zakres `a..b` (kolejność katalogu, oba końce) i samodzielne `...` między dwiema nazwami (ten sam
   zakres; przykład z zadania `c,dojlidy,dk65-01,...,knyszyn` działa dosłownie). Separatory: przecinek, średnik, spacja
   (PowerShell skleja tablicę `-Regions a,b` spacją). Nieznana nazwa = błąd. Plik `Data/build_regions.json`
   (schema `truck-sim-pl/build-regions/1`, `regions: ["d67"]`) jest czytany **tylko** z `-RegionsFile`.
3. **Jeden katalog regionów** `game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json`
   (`Game.Gameplay.RegionCatalog`): id, polska etykieta (ulice i miejsca, bez nazw firm — reguła 8, BRAND-SWEEP-S20;
   tytuł `region.yaml` regionu C zawiera nazwę parku logistycznego, więc etykieta jest pisana ręcznie), grupa, kolejność
   menu, aliasy, zestaw `d67` (17 regionów: C, Maczka, Kleeberga, Knyszyńska, DK65 01–11, Knyszyn-S, Knyszyn).
   Pola `routeLengthM` i `startS` odświeża `python scripts/export-region-catalog.py` z `Data/Regions/<id>/route_start.json`
   (`--check` = exit 1 przy nieaktualnym katalogu lub regionie bez wpisu). Ten sam plik czyta build i menu, więc nazwy
   się nie rozjadą.
4. **Nazwa sceny** w jednym miejscu: `Game.World.RegionScenes` (`WorldC` dla C, `World_<id>` dla reszty, `_High` dla
   tieru High); `WorldSceneBuilder.SceneNameFor` deleguje do niej.
5. **Menu (kod, bez YAML sceny Boot).** `GameBootstrap` buduje listę `BootRegionChoice` z katalogu, `BootMenu` rysuje pod
   startami wiersz „< region >” (etykieta + „n/N · grupa · trasa X km”) i przycisk „Jedź w wybranym regionie”. Region,
   którego scena nie jest w APK (`Application.CanStreamedLevelBeLoaded`), jest wyszarzony, a przycisk nieaktywny
   („Region niedostępny w tym APK”); strzałki przechodzą też przez wyszarzone, żeby było widać, czego brakuje. Gdy żaden
   region z katalogu nie jest w APK, wiersza nie ma. Ostatni wybór: `PlayerPrefs menu.region`. Launch argument
   `scene=<id|alias>` (adb `-e scene knyszyn`) ładuje scenę regionu dla bieżącego tieru (inne wartości jak dotąd).
6. **Punkt startu.** Start z menu = `StartRequest.SetRegion(id, s)`: ta sama ścieżka co `route_s` (G3), czyli
   `DrivingLabBootstrap.RouteSpawnPose` na `WorldRoute` sceny (trasa z `route_start.json`), bez końca trasy (jazda
   swobodna). `s = RegionStart.ClampStartS(startS, długość)`: domyślnie **12 m**, jak spawn importera
   (`WorldSceneBuilder spawnS`), i co najmniej `MinAheadM = 100 m` trasy przed końcem (zamknięcie 60 m przed krawędzią,
   ADR 0169; WORKING_VALUE). Po spawnie jedna linia logu
   `[START] region=<id> route_s=<s> en=<E,N> road_edge=<e> road='<ulica>' road_dist=<m>`: punkt w układzie regionu
   przyciągnięty (`RouteGraph.Snap`, ≤ 30 m, WORKING_VALUE) do grafu `Resources/CabDisplay/Nav/<id>_route.bytes` — trójka
   region + pozycja + droga, jak w przyszłym zapisie. Uwaga: `<id>_route.bytes` to graf drogowy KRTG (ADR 0150), nie
   polilinia trasy startowej; polilinia jest w scenie (`WorldRoute`) i w `route_start.json`, więc stamtąd bierzemy punkt.
   Wszystko raz na start; pętla jazdy bez zmian (zero alokacji GC).

## Weryfikacja w chmurze (bez Unity)
- `RegionSelectTests` (EditMode, 16 testów) skompilowane i uruchomione pod .NET 8 z minimalnymi zaślepkami UnityEngine
  (Vector2/3/4, Mathf, Resources z plików, JsonUtility przez System.Text.Json) razem z prawdziwymi plikami
  `RegionScenes.cs`, `RegionCatalog.cs`, `RegionStart.cs`, `StartRequest.cs`, `RouteGraph.cs`, `RegionBuildList.cs`,
  `EditorTools.cs`: **16/16 zielone**. To nie zastępuje przebiegu w Unity (JsonUtility zachowuje się inaczej niż STJ).
- Dane: punkt startu (s = 12 m) 11 regionów z grafem nawigacji leży 0,7–1,9 m od osi drogi grafu (C, Maczka, Knyszyńska,
  DK65 02, 03, 06–11). **10 regionów nie ma `*_route.bytes`** (Kleeberga, DK65 01, 04, 05, Knyszyn-S, Knyszyn, Knyszyn-W,
  Mońki, Tykocin, Dojlidy): start działa, log ma `road_edge=-1`, GPS w kabinie nie ma mapy.
- Nieuruchomione: kompilacja Unity/Android, PlayMode (`StartMenuFlowTests.Menu_RegionPicker_…`,
  `HudLayoutTests.StartMenu_WithRegionPicker_FitsSafeArea`), build z `-Regions`, telefon.

## Szacunek rozmiaru APK i pamięci (ESTIMATED — nie zmierzone)
Metoda: `_Generated` nie ma w gicie, więc bazą jest `WORLD_MEMORY` Low z importu każdego regionu (cytowane ADR) i
pomiary APK regionu C. Współczynnik k = MB APK na MB `WORLD_MEMORY` Low:
- k_min ≈ **0,81**: udział świata C w APK 71 MB przy pamięci świata ≈ 88 MB (`docs/PERFORMANCE_BUDGETS.md` §WorldC v3).
- k_max ≈ **1,18**: APK z samym C 224 MB (`HANDOVER.md`, D67) − ostatni APK `-noWorld` 58,07 MB
  (`PERFORMANCE_BUDGETS.md`, 2026-11-10) − wspólne tekstury PBR ≈ 21 MB (ADR 0063) = ≈ 145 MB na 124,2 MB `WORLD_MEMORY`
  C (ARGON-S20-ddr-0188). Zawyżone: `-noWorld` jest stary, a ciężarówka urosła od tamtej pory.
- Przyrost APK na region = k × `WORLD_MEMORY` Low. Źródła `WORLD_MEMORY` Low [MB]: C 124,2 (0188), Dojlidy 99,6 (0188),
  Maczka 153,2 (0203/0208), Kleeberga 156,7 (0206), Knyszyńska 116,0 (0208), DK65 01 68,2 (0205), 02 60,2 (0210),
  03 50,5, 04 76,1, 05 75,5 (0207), 06 59,0, 07 59,1, 08 55,5, 09 51,4, 10 49,0, 11 48,2 (0214), Knyszyn-S 40,8,
  Knyszyn 95,5, Knyszyn-W 54,0, Mońki 46,6, Tykocin 45,7 (0212). Wartości z różnych dni; regeneracje mogły je zmienić.

| APK (Low/Medium, bez `-worldHigh`) | dodatkowy `WORLD_MEMORY` Low | ESTIMATED rozmiar APK |
|---|---|---|
| dziś (Boot, DrivingLab, WorldC) | — | 224 MB (zmierzone, HANDOVER) |
| `-Regions d67` (17 regionów) | +1 214,9 MB | **≈ 1,2–1,7 GB** |
| `-Regions all` (21) | +1 460,8 MB | ≈ 1,4–1,9 GB |
| jeden kafel DK65 06–11 | +48–59 MB | +39–70 MB na kafel |
| Maczka / Kleeberga (najcięższe) | +153–157 MB | +124–185 MB na kafel |

Pamięć: wczytana jest **jedna** scena regionu naraz (`LoadScene` Single), więc RAM nie rośnie z liczbą regionów w APK.
PSS na A16 ≈ PSS C − `WORLD_MEMORY` C + `WORLD_MEMORY` regionu (założenie k = 1, UNVERIFIED): z C 899,8–926,2 MB
(GATE-3, s17) → najcięższa Kleeberga ≈ **930–960 MB**, kafle DK65 ≈ 820–880 MB, przy budżecie PSS ≤ 1000 MB
(WORKING_VALUE, GATE-3). Kleeberga i Maczka są blisko progu — zmierzyć je pierwsze.

Ryzyka (UNVERIFIED, do sprawdzenia przez lidera): APK > 1 GB instaluje się długo przez `adb` i zajmuje miejsce na
A16; zachowanie Unity/Androida przy APK blisko 2 GB nie było sprawdzane w projekcie — jeśli `d67` przekroczy ~1,5 GB, budować
podzbiory (np. `-Regions c..dk65-05` i `-Regions dk65-06..knyszyn`) albo przejść na AAB + Play Asset Delivery
(`PERFORMANCE_BUDGETS.md`, wariant b).

## Konsekwencje i otwarte
- Regiony to osobne sceny: koniec trasy kafla = zamknięcie drogi, przejazd korytarzem w całości wymaga streamingu
  (ADR 0003), poza zakresem.
- 10 regionów bez grafu nawigacji (lista wyżej): GPS w kabinie pusty — do wygenerowania `tools/worldgen/navgraph/` (inny agent).
- Nowy region = wpis w katalogu (id, etykieta) + `python scripts/export-region-catalog.py`; test
  `ShippedCatalog_CoversEveryRegionWithAStartRoute_…` łapie brak wpisu.
- Teksty menu są w kodzie jak reszta `BootMenu` (brak tabel lokalizacji w projekcie) — przenieść razem z resztą UI.
