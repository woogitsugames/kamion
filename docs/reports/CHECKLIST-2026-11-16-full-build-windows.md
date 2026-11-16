# Lista kontrolna pełnego buildu Windows (d67-full) — build-hygiene-s23, 16.11.2026

Dla lidera, przed buildem dla właściciela. Liczby: zmierzone (źródło w nawiasie) albo `ESTIMATED` / `UNVERIFIED`.

## Skąd lista scen (zadanie 1)

- `game/ProjectSettings/EditorBuildSettings.asset` ma tylko Boot, DrivingLab i WorldC i tak ma zostać
  (`BuildScenes.Apply` przywraca je przy każdym imporcie). Regiony dochodzą wyłącznie przez `-Regions`:
  `RegionBuildList.ComposeScenes` składa listę w pamięci z katalogu
  `game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json` (zestaw `d67-full` pisze
  `scripts/export-region-catalog.py`). Ręcznej listy nie ma i nie trzeba jej robić.
- Na regiony przypadają: scena Low, scena kafla Low `_Tile` (gdy istnieje), High i kafel High (z `-worldHigh`, domyślne).
- **dk65-03 i dk65-04 są w ostatnim pełnym buildzie** (`artifacts/logs/build-win-20261116-035803.log`, e28533ca31):
  44 sceny = Boot, DrivingLab i 21 regionów × (Low + High).
- **Pierścień (ADR 0231, 18 kafli) nie jest w main.** Jest na `origin/world2-s23`: tam katalog ma 39 regionów,
  `d67-full` = 39, a `check-build-scenes.py` na tym katalogu i scenach z worktree world2 daje OK (39/39 Low i High).
  Warunek: scalić world2-s23 przed buildem.
- **D86 (właściciel, docs/11): dk65-03 i dk65-04 wchodzą do buildu dopiero z treścią High.** Powód (#168,
  `StreamingContentChoice.HighCoversLow`): jeden region z kaflem Low bez kafla High przełącza streaming PC (tier
  High/Ultra) na treść Low w całym grafie (zmierzone w int-ui-s23: dk65-04 z samym `_Tile` → `FALLBACK Low`).
  `check-build-scenes.py` ma tę regułę zawsze przy `-worldHigh`: FAIL „D86 Low tile without High tile”. Do
  EditorBuildSettings tych scen nie dodawać (trafiłyby do każdego buildu, też APK) — wchodzą przez `-Regions d67-full`,
  gdy check jest zielony. Import zawsze `-Tiers Low,High` (domyślne `import-region.ps1`).
- **Brakuje kafli `_Tile`:** main 0/21 (stan 17.11 ~00:00), world2 0/39; checkout `win-build-0261` (był 19/21 o
  20:00) już nie istnieje. Żaden dotychczasowy build nie ma sceny `_Tile`. Bez nich `-stream 1` nie otworzy
  szwu (`WorldStreamer`: „not in the build: seam stays closed”), a `Kamion-korytarz.cmd` nie powstanie
  (postbuild wypisze WARNING).
- Narzędzie: `python scripts/check-build-scenes.py` (pytest `tests/dist/test_build_hygiene.py`; test na prawdziwym
  katalogu sprawdza, że `d67-full` obejmuje każdy region katalogu i każdy `Data/Regions/<id>` z `route_start.json`).

## Równoległy import regionów (zadanie 4)

- `import-region.ps1` przyjmuje jeden region. `Invoke-UnityBatch` odmawia startu, gdy `game/` jest otwarte
  (`Temp/UnityLockfile`). **W jednym checkoucie równoległy import jest niemożliwy**: drugi proces kończy się od razu
  błędem, nie czeka.
- Wiele worktree mogłoby działać równolegle, ale:
  - każdy ma własne `Library`: 6,7 GB w main (du) i osobny reimport Win64;
  - wynik (`game/Assets/_Generated/World/<id>` + `.meta`) trzeba skopiować do checkoutu buildu, a tam Unity i tak
    zaimportuje kopię jeszcze raz (Win64);
  - `-Build` pisze `Data/raw/derived/<id>` przez junction do main, więc dwa procesy na tym samym regionie się nadpiszą;
  - `unity-slot.ps1` daje najwyżej 4 sloty `unity` na cały komputer, dzielone z innymi agentami.
- Czasy:
  - Unity w `import-region` trwa 72–211 s na region (Android, 45 logów w `artifacts/logs/import-region-*` 15–16.11,
    czas od utworzenia do ostatniego zapisu logu);
  - starty kolejnych importów w łańcuchu są co ok. 10 min;
  - reimport Win64 ok. 10 min na region (HANDOVER 16.11 10:19: kleeberga 618 s, knyszynska 585 s).
- **Wniosek: nie warto zrównoleglać.** Kopiowanie i ponowny import w checkoucie buildu zjada zysk, a ryzyko kolizji
  derived rośnie. Lepiej sekwencyjnie w checkoucie buildu (Win64), tylko regiony bez `_Tile`/High
  (`check-build-scenes.py` je wypisuje). Gdyby czas był krytyczny, najwięcej dałoby wiele regionów w jednej sesji Unity
  (`RegionImporter.ImportBatch` z listą `-region`): odpada start Unity przy każdym regionie. To zmiana kodu Editor,
  nie robię jej tutaj.

## Kroki (zadanie 5)

Checkout buildu: nowy worktree z main z Library pod Win64 (`win-build-0261` usunięty; pierwszy build w checkoucie z
Library pod Androida = pełny reimport Win64, ADR 0261). Najpierw scal world2-s23 i tę gałąź do main. Każdy krok uruchamiaj z katalogu checkoutu w PowerShell 7.

0. Warunki: `world2-s23` (pierścień) i `build-hygiene-s23` scalone; `git status` czysty (inaczej nazwa `-dirty` i
   `package-windows.py` odmówi bez `--allow-dirty`); brak `artifacts/locks/PHONE_RUN`; wolne miejsce na C: ≥ 60 GB
   (dziś 463 GB).
1. Derived pierścienia w main: dla każdego kafla pierścienia zbudowanego w world2
   `robocopy .claude\worktrees\world2-s23\Data\raw\derived\<kafel> Data\raw\derived\<kafel> /E /MT:16`
   (exit < 8 = OK). Pomiń, jeśli world2 ma junction (`(Get-Item Data\raw\derived).LinkType` = `Junction`).
2. Stan scen:
   `python scripts/check-build-scenes.py --regions d67-full --require-tiles --require-high`
   Oczekiwane po scaleniu: 39 regionów, dziś wiele FAIL `tile scene missing`. Każdy FAIL „D86” = import tego regionu
   z `-Tiers Low,High` albo usunięcie go z listy (`-Regions` bez niego); dk65-03/04 szczególnie (D86).
3. Import brakujących (sekwencyjnie, z Win64):
   ```
   pwsh scripts/unity-slot.ps1 -Acquire -Owner lead-build -Priority
   foreach ($r in <regiony z FAIL kroku 2>) { pwsh scripts/import-region.ps1 -Region $r -BuildTarget Win64; if ($LASTEXITCODE) { break } }
   pwsh scripts/unity-slot.ps1 -Release -Owner lead-build
   ```
   Czas: do ok. 10 min na region (Win64). 39 regionów to ok. 6,5 h, **ESTIMATED** (21 zmierzonych × 10 min
   ekstrapolowane na 39). Z samym brakiem `_Tile` krótszy import (Unity ok. 1,5 min) **UNVERIFIED** dla Win64.
4. Ponownie krok 2 → exit 0 (w tym 0 × D86).
5. Build:
   `pwsh scripts/build-windows.ps1 -Slot -Regions d67-full`
   - Czas: 507–628 s dla 21 regionów (`build.json` e28533ca31 / 4ee3e02626).
   - Rozmiar: 4 941 MB dla 21 regionów; knyszyn sam to 753 MB. 39 regionów + kafle to ok. 8,5–9 GB, **ESTIMATED**
     (ok. 210 MB/region; dopłata za kafle nieznana).
   - Wynik: `artifacts/win/kamion-0.1.0-<sha>-regions/`.
6. Weryfikacja buildu:
   - `python scripts/check-build-scenes.py --regions d67-full --log <log z build.json>` → `missing in log 0`.
   - `build.json` → `launchers` zawiera `Kamion-korytarz.cmd`, `Kamion-korytarz-d3d11.cmd`, `Kamion-d3d11.cmd` i
     39 × `Kamion-<region>.cmd`. Brak korytarza oznacza, że nie ma `World_knyszyn-s_Tile` (wróć do kroku 3).
   - `python scripts/postbuild-windows.py <katalog buildu> --check` → `"ok": true`.
7. Dowód z playera:
   - region: `pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn -RunSeconds 90 -ShotSeconds 45`;
   - korytarz: to samo z `-ExtraPlayerArgs '-stream','1' -Autopilot route -Speed 50`. W `Player.log` szukaj `[STREAM]`,
     nie może być „not in the build”.
8. Paczka:
   - `uv run --no-project python scripts/package-windows.py <katalog buildu> --dry-run`: lista `add` musi mieć
     `README.txt`, `Zbierz-logi.cmd`, `collect-logs.ps1`; żaden `Kamion-*.cmd` nie może być w `exclude`.
   - Potem to samo bez `--dry-run` → `artifacts/dist/<nazwa>.zip` + `.sha256` + `.json`.
   - `--release` kończy się kodem 3, dopóki bloker R-P0-2 jest otwarty.
   - Zip: `unzip -l` / `Expand-Archive` i sprawdź `Kamion-korytarz.cmd` i README (sekcja URUCHOMIENIE wymienia
     korytarz i D3D11).
9. Miejsce na dysku, sumarycznie:
   - build ok. 9 GB (ESTIMATED);
   - zip ok. 9 GB (ESTIMATED, kompresja meshy nieznana);
   - `_Generated/World`: 14 GB dla 21 regionów w main (du);
   - Library Win64 rośnie z importem (nie mierzone);
   - razem rezerwuj ≥ 60 GB (rezerwa, nie pomiar).

## Dry-run paczki na istniejących buildach (zadanie 3)

| Build | Wynik `--dry-run` | Korytarz / README gracza |
|---|---|---|
| `artifacts/win/kamion-0.1.0-e28533ca31-regions` (d67-full, 21 regionów, 04:06) | exit 0; 185 plików, 4 941 MB; `build-id.json` brak → generowany; bloker R-P0-2 (paczka tylko dla testerów) | **brak `Kamion-korytarz.cmd`** (build sprzed launchera, w katalogu tylko okno, knyszyn, knyszyn-w; wszystkie trzy idą do zipu). README.txt dodany. Postbuild z tej gałęzi na jego logu: 21 regionów, 0 kafli → korytarza by nie napisał |
| `win-build-0261/.../kamion-0.1.0-13104cf215-regions` (tylko knyszyn) | exit 0; 186 plików, 753 MB; R-P0-2 | brak korytarza (brak knyszyn-s). README dodany |

Nowe launchery w zipie (korytarz, D3D11, README z ich opisem) są pokryte testem
`test_postbuild_launchers_reach_the_zip_with_readme` na syntetycznym buildzie. **Na prawdziwym buildzie nie są
sprawdzone**: to krok 8 powyżej.
