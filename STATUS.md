# STATUS embankment-cli — s24, zakończone prace generatora
- Ciągły obrys skarpy i interpolacja wysokości w pasie 16 m; usunięto wtórne schodki z filtra tidy, jezdnia V/T bez zmian (test DK65-10). Pylony far-field mają otwartą kratownicę 204 tris zamiast pełnego trzonu 12 tris.
- 91 PASS / 1 SKIP (brak cache surowej ekstrakcji FF); review kodu i podglądu bez blokujących uwag. Raport: docs/reports/embankment-cli-s24.md; ADR 0311; podgląd i log: artifacts/embankment-cli/. Unity/build_world/player nieuruchamiane; bez push i zapisów poza worktree.
- NASTĘPNY KROK (bez przebudowy): `uv run --project tools/worldgen pytest tests/gis/test_embankment_pylons_s24.py -q`; po integracji osobno przebudować/reimportować minimum dk65-10 i dw671-tykocin-09 oraz sąsiadów, docelowo d67-full. Wygląd playera i przełączeń LOD UNVERIFIED.

# STATUS guardrail-zebra-cli — s24, zakończone prace generatora
- 81 regresyjnych + 16 płaskich + 6 NMT + 1 kontrola farby PASS. Kleeberga NMT: 23 odcinki wycięte, 2520 zachowanych; review bez blokujących uwag. Raport: docs/reports/guardrail-zebra-cli-s24.md; ADR 0308.
- Wdrożono bufor bariera–nawierzchnia i przycinanie/deduplikację P-10; artefakt zebry t=2560 NIEODTWORZONY (0 m² overlap przed zmianą, także NMT i szew). Log wskazuje jeszcze knyszyn. Unity/build_world/player nieuruchamiane, bez push.
- NASTĘPNY KROK (po integracji, osobna sesja przebudowy): przebudować/reimportować bialystok-kleeberga, knyszyn, knyszyn-w i sprawdzić przejazd; testy bez przebudowy: `uv run --project tools/worldgen pytest tests/gis/test_drive_s24_surface_safety.py -q -s`.

# STATUS gps-roundabout-cli — s24
- Przyczyna: tracker kończył rondo na wjeździe, mimo poprawnego manewru „2. zjazd” w grafie DK65-06. Dodano punkt końca manewru i zachowanie go przy CopyFrom/Compose.
- Testy: nav-runner 98/98 PASS, 36 golden routes bez różnic, 0 B GC. Dodano regresję EditMode; Unity i buildów gry nie uruchamiano. Raport: docs/reports/gps-roundabout-cli-s24.md; dowody: artifacts/gps-roundabout/.
- NASTĘPNY KROK (kontrola bez Unity): `dotnet test tools/nav-runner/Tests/Tests.csproj`; test obrazu HUD wymaga osobnej sesji z autoryzacją playera. Bez push.
# STATUS edge-barriers-cli — s24
- Naprawa źródłowa: indywidualne szlabany renderer+collider, rzeczywista strona wyjazdu, wysokość z nawierzchni własnego kafla, WorldEdge ukryty do Ready. Walidacja brakujących materiałów/błędów shaderów; build odrzuca stare ClosureGroup_*.
- Raport: `docs/reports/edge-barriers-cli-s24.md`, kod `e6184e7b2`; review niezależnego agenta bez blokujących uwag.
- Testy: `dotnet test tools/spawn-runner/Tests/Tests.csproj` 30/30 PASS; dodano także testy integracyjne EditMode (bez uruchamiania Unity). Magenta t=510: dokładny materiał/wariant nadal UNVERIFIED; brak artefaktów zaimportowanych scen i logu kompilacji w tym worktree.
- NASTĘPNY KROK (osobna sesja z Unity): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`, pełny import `pwsh scripts/import-region.ps1 -Region <id> -Tiers Low,High -BuildTarget Win64` dla wszystkich używanych kafli (także _Tile), sprawdzić materiały Maczka/Kleeberga, następnie powtórzyć przejazd Windows. Bez push.

# STATUS nav-uturn-alt — DK8 / wybór jezdni startowej
- Odtworzono błędny snap 526 zamiast 530 na al. Tysiąclecia; kierunek był sprawdzany dopiero po ustaleniu krawędzi. Poprawka wybiera bliską jezdnię zgodną z kursem przed A*.
- Dwa nowe testy EditMode + odpowiedniki .NET; regresja czerwona przed poprawką, całość nav-runner 96/96 PASS. Raport: `docs/reports/nav-uturn-alt.md`; dowody lokalne: `artifacts/nav-uturn/`.
- Unity i player nieuruchamiane; brak potwierdzenia dokładnej klatki „300 m”. Bez zmian w Pythonie i bez pushowania.
- NASTĘPNY KROK (w osobnej autoryzowanej sesji Unity): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`, następnie przejazd DK8 z logiem `-nav_log 1`.

# STATUS cabin-polish-s23 (D84: wnętrze kabiny PC — polish po recenzji REVIEW-2026-11-17-s23-cabin-pc)
- Worktree z origin/main 14925a7cc. Skrypty odłączone: `artifacts/cabin-polish-s23/{run,chain,assets-win64,bl,a6}.ps1` (status `*.status`, `exit=`).
- Plastik (P1-2): `plastic_grain.py` + `cab_material_scans.json` — ziarno 2–5 mm (waga 0,7) + plamy połysku 2,5–10 cm; normalne mediana 10,3°, p95 20,7° (było 6,9°/14,1°). Z fotela 1 px ≈ 0,9 mm (wyliczone).
- Zmierzch (P1-3): `CabInteriorLighting` `nightViewEv` 0,45, `panelGlow` 0,07, wygaszanie +3°…−5°. Pomiar sRGB cab-dash dusk: piasta 20,21,28 → 12,12,13; droga 10,12,20; niebo 41,59,94.
- Geometria (`build_interior.py`, eksport a6): uszczelki + zaślepki słupka A, żebra tacek 22 mm, daszek zegarów fade 50 mm, roleta kierowcy 0,20 m, przeszycie ×3,2, wytarcie wieńca niesymetryczne. LOD0 105 121 / LOD1 43 984 / LOD2 21 551 tris; `check_export.py` PASS.
- Końcowy przebieg (`final.ps1`): eksport LOD0 105 163 / LOD1 44 003 / LOD2 21 557, `check_export.py` PASS, BuildBatch + InstallBatch `TRUCK_RESULT: OK`, EditMode Win64 1249/22/37 (20× `StartClearanceTests.ImportedScene_*` + 2× `CarPaintMaterialTests.DepositionChannel` — jak na main; nowy `CabTwilightTests` 2/2).
- Rendery High -Pc 1920×1080 DrivingLab: `artifacts/cabin-polish-s23/{base,f}-{clear,dusk}`, `f-lowsun`, `f-night`, tier mobilny `f-mob-{clear,dusk}`, WorldC `f-world-clear` (cab-apillar, cab-driver-ab10); przed/po `view/ab-*.jpg`. Kopia w main `artifacts/cabin-polish-s23/`.
- Pomiary cab-dash (sRGB): dusk piasta 20,21,28 → 10,10,11 przy drodze 10,12,20; lowsun 89 % pikseli dolnej deski > 3 % luma; szczyt legend dusk 112 → 113 (podniesienie `cab_backlight.json` 8→12 cd/m², cap 0,09 bez mierzalnego efektu — do sprawdzenia).
- Roleta wróciła do autorskiego 0,10 m. ADR: `docs/adr/DRAFT-d84-kabina-polish-zmierzch-i-ziarno.md`.
- Otwarte: lusterka/daszek poza kadrem 62° (decyzja pitch/FOV — A/B `cab-driver-ab10`), ciepła poświata niemierzalna na piaście, brak zdjęć referencyjnych (docs/06 §5 pkt 3), kurz bez zmian, pojedyncze jaśniejsze odcinki żeber tacek (atlas AO), kamery QA nie w scenie DrivingLab (`pwsh scripts/build-lab.ps1 -SkipAudio`).
- NASTĘPNY KROK (lider): visual-critic na `view/ab-*.jpg`, `f-*`; po scaleniu w main: `-executeMethod Game.Editor.Setup.TruckAssetBuilder.BuildBatch`, potem `Game.World.Import.WorldTruckInstaller.InstallBatch`.

# STATUS guardrail-zebra-cli — s24 (WIP)
- Dodano kontrolę odcinków barier po wygładzaniu/łączeniu oraz przycinanie P-10 przy wysepkach i między łańcuchami; review drugiego agenta uwzględnione.
- Testy jednostkowe: 9/9 PASS; istniejące testy barier/oznakowania: 29/29 PASS. Testy rzeczywistych kafli w toku, bez Unity/build_world.
- NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_drive_s24_surface_safety.py -q -s` (pomiar regresji na Data/Regions); dokończyć raport i commit. Bez push.

# STATUS guardrail-zebra-cli — s24 (walidacja kafli)
- 81/81 testów bez pełnej generacji kafli PASS; NMT Knyszyn/Knyszyn-w 4/4 PASS (SHA wejść zgodne), dodatkowy test chowania zebry pod nawierzchnią 1/1 PASS.
- Płaski Kleeberga: zachowane 2610 odcinków, wycięte 38; porównanie PNG obejrzane. Nie odtworzono overlap zebr ani ich schowania pod drogą — konkretny artefakt t=2560 UNVERIFIED, log wskazuje jeszcze knyszyn.
- NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_drive_s24_surface_safety.py -q -s` — zakończyć bieżący przebieg płaski i NMT Kleeberga, uzupełnić docs/reports/guardrail-zebra-cli-s24.md, commit bez push.

# STATUS embankment-cli — s24 (WIP)
- Usunięto metrykę schodkowego obrysu w konformowaniu skarpy: obrys wektorowy + interpolacja wysokości w pasie 16 m. Pylony far-field: otwarta kratownica, 420 tris/słup, bez nowego materiału.
- Nowe testy syntetyczne 18/18 PASS; review w toku. Unity i build_world nieuruchamiane, zmiany tylko w tym worktree, bez push.
- NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_embankment_pylons_s24.py tests/gis/test_unit_meshing_chunks.py tests/gis/test_terrain_walls.py -q`; uzupełnić walidację końcowej skarpy i podgląd offline.

## STATUS rondo-fix-cli — D95, 2026-11-20
- WIP commit `31e534e35`, bez push. Raport: `docs/reports/visual/2026-11-20-knyszyn-d95-cli.md`.
- Szerokości/promienie D94 zachowane; dwa pasy W przy 11,75 m asfaltu po D94; wydłużone soczewki E/W; świeży asfalt i materiał płyty z pierścienia; opaska, znaki, lampy. Zapora/szew nadal otwarte, brak wizualnego PASS.
- W tle uruchomiono wyłącznie build_world knyszyn, przez slot heavy rondo-fix-cli; potem automatycznie pytest i combo. Runner: `artifacts/logs/d95-run.ps1`, logi `d95-build.log`, `d95-tests-final.log`, `d95-combo-after.log`, kody w `*.exit`.
- NASTĘPNY KROK: `Get-Content artifacts/logs/d95-build.log -Tail 30; Get-Content artifacts/logs/d95-tests-final.log -Tail 30; Get-Content artifacts/logs/d95-combo-after.log -Tail 30`; sprawdzić bramkę D95, poprawić błędy, uzupełnić raport i commit. Nie uruchamiać Unity ani build_world innego kafla.

### D95 15:08 — walidacja w kolejce
- Pierwszy build knyszyn exit0 (1164,7 s), road_consistency 3/5 i zero na trasie. Pytest 142 pass / 2 skip / 2 fail; oba błędy poprawione, retest w kolejce.
- Combo r1: DK65→DW671 W 0/17/0, swing0/0/0; DK65→DK65 W0/0/0. Zapisano korektę authored toru 0,75 m w prawo (optymalizator daje0/0/0); finalny pomiar gotowego linku w kolejce. Rynek nadal nie przechodzi globalnie.
- Dalsze runnery w tle: d95-signs-run.ps1, d95-retest-run.ps1, d95-final-combo-run.ps1 w artifacts/logs, wszystkie przez heavy. Pula zajęta regen-wave A/B/C. Nie uruchamiać ponownie tych samych zadań; sprawdzać *.exit i logi. Drugi build pozostawi nowe wygenerowane pliki do przeglądu/commitu. Szew i zapora nadal wymagają poprawki, Unity nie uruchomiono.

### D95 kontynuacja — szew statycznego QA
- Stare runnery zakończyły procesy przed przydziałem slotu, bez wyników. Wznowiono w tle `d95-resume-run.ps1`: build knyszyn → combo → pytest, jeden slot heavy, bez Unity.
- QA Knyszyna wymaga rzeczywistej sceny knyszyn-w w tym samym tierze; wspólna logika streamera usuwa obie zapory oraz stuby dopiero po załadowaniu i cook kolizji. Brak sceny = jawny błąd. Dodana regresja EditMode, bez wykonania Unity.
- NASTĘPNY KROK: `Get-Content artifacts/logs/d95-resume-slot.log -Tail 3; Get-Content artifacts/logs/d95-resume.status -ErrorAction SilentlyContinue; Get-Content artifacts/logs/d95-build-signs.log -Tail 15 -ErrorAction SilentlyContinue`. W playerze wymagane `-stream 1`; samodzielny kafel zachowuje koniec mapy.
- Wydzielono `WorldNeighbourQa.cs`; kompilacja Roslyn lokalnego Game.World + nowego helpera QA + zmodyfikowanego testu EditMode PASS (bez Unity, referencje z istniejącego cache main, logi `artifacts/d95-compile/`). Runner .NET reguł krawędzi: 35/35 PASS. To nie wykonanie testu EditMode ani pełny build gry.
