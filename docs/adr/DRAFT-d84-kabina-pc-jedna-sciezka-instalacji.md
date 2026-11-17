# ADR DRAFT (numer nada lider) — D84: pełny model kabiny w każdej scenie jazdy na PC, plastik deski bez skanu skóry

Status: propozycja (gałąź `cabin-pc-s23`), 2026-11-16. Rendery ocenia `visual-critic` — nie autor.

## Kontekst
Właściciel na PC: „brzydkie wnętrze ciężarówki, na telefonie było ładne”. Stan zastany (zmierzony w kodzie i na zrzutach):
- `DrivingLab.unity` (git) instancjonował `Tractor4x2_Graybox`; sceny regionów brały TRAKT przez `WorldSceneBuilder`, ale z **cichym** fallbackiem na graybox, gdy prefab `_Generated/Truck/Tractor4x2_TRAKT.prefab` nie istniał (katalog poza gitem).
- Run PC `artifacts/win/runs/20261116-041031-keys` (`World_knyszyn_High`) miał już TRAKT — sama podmiana prefabu nie tłumaczy całości uwagi. Na High 1080p widać to, czego ekran telefonu (Low, mały kąt na piksel) nie pokazywał: plastik deski = emboss ze skanu Brown Leather (ADR 0112, backlog „cab r4”), z fałdami skóry na każdej wyprasce.
- DrivingLab nie miał `EnvironmentLighting` — kabina TRAKT liczy wypełnienie z modelu nieba (`CabInteriorLighting`), więc po samej podmianie prefabu wnętrze było prawie czarne (`artifacts/cabin-pc-s23/lab1/`).

## Decyzja
1. **Jedna ścieżka instalacji**: `Game.Editor.Setup.DrivingVehiclePrefabs` (`Tractor`, `Trailer`, `EnsureBuilt`, `Resolve`). Używają jej `DrivingLabSceneBuilder`, `WorldSceneBuilder` (sceny regionów i hosty streamingu; sceny `_Tile` nie mają pojazdu, ADR 0235) oraz `WorldTruckInstaller`. Brak prefabu art → próba zbudowania (`TruckAssetBuilder.Build` / `TrailerAssetBuilder.Build`), a dopiero potem graybox z ostrzeżeniem `[VEHICLE] FALLBACK ...`.
2. **Przypięte GUID-y** prefabów art (`TractorGuid`, `TrailerGuid` = dotychczasowe wartości z tej maszyny; `PinGuid` pisze `.meta` tylko gdy go nie ma). Powód: scena w gicie odwołuje się do prefabu spoza gita; bez tego świeży checkout wygenerowałby inny GUID i scena straciłaby pojazd.
3. **DrivingLab dostaje rig nieba scen regionów** (`EnvironmentLighting` z 5 presetami, `WorldVolume`, `QualityProfileApplier` na kamerze) i kamery kontrolne TRAKT (`cab-*`, `truck-*`). Skutek uboczny: `-Lighting clear|dusk|night` działa też na placu.
4. **Plastik kabiny = syntezowany stippling wtryskowy** (`tools/blender/truck/interior/plastic_grain.py`, wywoływany z `cc0_leather.apply_runtime_maps`, tryb `plastic.mode = procedural_stipple` w `cab_material_scans.json`): pasmo 0,25–0,6 mm na kaflu 0,10 m, bez fałd i porów; nachylenie normalnych mediana 6,9°, p95 14,1° (zmierzone przez skrypt). Wszystkie wzmocnienia `WORKING_VALUE`. To nie jest skan tworzywa — świadomie (przegląd `artifacts/cab-r4/PLASTIC-SOURCE-CHECK.md`: sprawdzone zasoby CC0 „Plastic” też nie są skanami).
5. Ekran nawigacji bez mapy (DrivingLab): ciemne tło i czytelny komunikat zamiast jasnoszarej płyty.

## Odrzucone
- Zmiana asmdef (`Game.Editor` → `Game.Rendering.Editor`) dla `LookDevAssets`: poza uprawnieniami agenta; ścieżki presetów powtórzone w `DrivingLabSceneBuilder` z komentarzem.
- Otwieranie każdej sceny świata w teście EditMode: minuty; test czyta GUID-y `m_SourcePrefab` z tekstu scen.

## Dowody
`artifacts/cabin-pc-s23/`: `lab1/` (TRAKT bez rigu nieba — czarna kabina), `lab2-*` (rig, stary plastik), `p2-*`/`p3-*` (nowy plastik, DrivingLab High dzień/zmierzch), `w1-*` (WorldC High dzień/zmierzch), `ab-grain-crop.jpg` (przed/po 1:1). Referencja telefonu: `artifacts/gate3/20261110-120931/RFGL34SJYDZ/cam/cab-dash_*.png`; PC przed: `artifacts/cab-r4/baseline/High-*`.
Test: `Game.Tests.DrivingScenesFullTruckTests` (5).

## Otwarte
- Świeży checkout bez `art-source/truck/interior/export/SM_CabInterior_LOD0.fbx` (poza gitem, eksport Blendera) nie zbuduje TRAKT → graybox z ostrzeżeniem. Do decyzji lidera: LOD0 do LFS/gita albo krok Blendera w pipeline buildu.
- Pasmo AO deski przy konsoli środkowej, legendy przycisków (czytelne na High; Low — backlog cab r4), brązowa wstawka „skóra” na desce pasażera, szyby/zegary — bez zmian w tej rundzie.
- Budżet: tekstury plastiku w tych samych rozmiarach (1024/512/256), geometria bez zmian; DrivingLab renderuje teraz TRAKT + naczepę art zamiast grayboxu — pomiar playera na placu nie wykonany.
