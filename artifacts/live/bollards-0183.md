# bollards-0183 (ADR 0183: słupki biało-czerwone z łańcuchem) — LIVE
- Worktree `.claude/worktrees/bollards-0183`, gałąź `bollards-0183` od origin/main de4ff22ac. Data/raw: derived+cc0 kopia, reszta junctiony; Library, megascans, art-source (ignorowane) skopiowane z main.
- Krok 1 GOTOWY: moduł `tools/worldgen/streetscape/chain_bollards.py` (prototypy `bollard_rw_chain` 142/31 tris, `bollard_rw` 78/15 tris, 1 materiał `chain_bollard` = atlas alfa 256x512; override `kind: chain_bollards` w overrides.yaml; `walk` = słupki co 2,00 m po cięciwie). Wpięcie: props.build_all, export.textures, stage (po lamp_rows), materials (blok addytywny).
- Testy: `tests/gis/test_chain_bollards_0183.py` 18/18.
- Miejsce z P11-063 (Dojlidy, Mickiewicza, wsch. krawężnik jezdni NW): rząd lokalnie (-31.7, 382.3) -> (-25.44, 369.78), 7 przęseł / 8 słupków; EPSG:2180 (780011.3, 590461.3) -> (780017.56, 590448.78). Override testowy TYLKO lokalnie (nie commitować plików Dojlid).
## NASTĘPNY KROK (komenda)
`cd C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bollards-0183; pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner bollards-0183; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy *> artifacts/logs/bw-dojlidy.log; pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner bollards-0183`

## Stan 2026-11-13 ~21:55 (STOP na polecenie lidera, limit)
- Zrobione: wysokość 0,80 m (U-12c, wiersz M50-043), przęsło 1,60 m; ADR szkic `docs/adr/0183-slupki-bialo-czerwone-z-lancuchem.md` (sekcje Budżet/Dowody = placeholdery WYNIKI_*); pytest nowy 18/18, podzbiór mebli 68/68.
- build_world dojlidy x2 OK (7,5 min), raport: 8 słupków, 7 przęseł, max_step 0,047 m. Import OK (2 min), rendery r1 Low+High obejrzane: `artifacts/bollards-0183/renders/r1-{low,high}/` (5 kamer, stats.txt).
- LOKALNIE, NIE w gicie: `Data/Regions/bialystok-dojlidy/overrides.yaml` (test; kopia `artifacts/bollards-0183/overrides.dojlidy.chain_bollards.yaml`), zmienione `generated/*` Dojlid (nie commitować), `Data/raw/derived/bialystok-dojlidy/textures/chain_bollard.png` podmieniony ręcznie nowszym atlasem.
- WADY z r1 do poprawy: (1) czerwone odcinki łańcucha w Unity są blado-różowe (w Blenderze czerwone) — sprawdzić kompresję/mipy atlasu 32-px kolumn (krwawienie koloru z sąsiedniej białej kolumny; dać odstęp/gutter albo szersze kolumny); (2) rząd stoi w wygenerowanym trawniku (w rzeczywistości bruk) — na High trawa Fab zakrywa dół słupka i dolny łańcuch: do dowodu przesunąć rząd testowy ~3,5 m na wschód na chodnik albo zgłosić 0179; (3) brak: porównanie z P11-063 obok siebie, A/B budżetu (import bez instancji bollard_rw), EditMode, pełny pytest tests/gis, visual-critic, kopia dowodów do MAIN, uzupełnienie ADR.
- Nic nie działa w tle. Sloty zwolnione.
## NASTĘPNY KROK (komenda)
`cd C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bollards-0183; code tools/worldgen/streetscape/chain_bollards.py` (poprawić kolumny atlasu U_LINK/U_STRIP: gutter między czerwoną a białą) → `uv run --project tools/worldgen pytest tests/gis/test_chain_bollards_0183.py -q` → podmienić PNG (jak wyżej) → `pwsh artifacts/bollards-0183/tools/run_unity.ps1 -Steps import,low,high -Tag r2` → obejrzeć `artifacts/bollards-0183/renders/r2-*`.

## s20 (2026-11-13 ~22:40) — r2
- Atlas r2 (048f35308): granice kolorów na wielokrotnościach 24 px (bloki ASTC 4/6/8/12), kolumny ogniw 32 px z 8 px przezroczystym marginesem w kolorze farby, styk czerwone|białe na u=192 (krawędź tekseli mip 0–6), LOD1 taśmy = stały UV w litej łacie 24x48 px (bez mipów). Przyczyna r1: import ASTC 6x6 + trilinear (InstanceImporter.ImportTexture), granica 160 px w środku bloku 6x6. Zużycie ogniw 0,6->0,4. pytest 19/19 (nowy test bleed mip0-4).
- Rząd testowy przesunięty o 3,5 m od jezdni (normalna (0,894; 0,447)) na wygenerowany chodnik: EPSG:2180 (780014.43, 590462.87) -> (780019.44, 590452.85). Ortofoto: rzeczywisty rząd stoi na nawierzchni utwardzonej na starej linii; wygenerowany świat ma tam trawnik (0179).
- W tle: `artifacts/bollards-0183/tools/pipeline_r2.ps1` (build r2 -> import+Low+High r2 -> EditMode -> A/B bez rzędu -> restore). Status: `artifacts/logs/pipeline-r2.status`.
## NASTĘPNY KROK (komenda)
`Get-Content C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bollards-0183\artifacts\logs\pipeline-r2.status` (gdy przerwane: `pwsh artifacts/bollards-0183/tools/pipeline_r2.ps1 -From <build|render|editmode|ab|restore>`)
- 22:47 build r2 OK (8 min): 8 słupków / 7 przęseł, max_step 0,025 m, PNG w derived = atlas r2 (sprawdzone bajtowo). Kamery przeliczone z instancji (`make_cameras.py`). Trwa import + Low + High r2; pytest tests/gis w tle (`artifacts/logs/pytest-gis-r2.log`).
- 23:05 r2 Low+High wyrenderowane (`renders/r2-*`, `compare/`): rząd na bruku, czerwień ogniw czerwono-brązowa zamiast różowej (naprawione). NOWA WADA: łańcuchy znikają od ~10 m (P11-063: liny 2–3 px przy 13 m). r3 w kodzie (b6be80fe8): łańcuch klasy tworzywowej 8 mm / 30 mm, taśma LOD1 22 mm (pomiar ze zdjęcia). EditMode 511/535, 6 FAIL = brak zbudowanej ciężarówki (TruckDoorCrown, MirrorPresentation; fixture), nie dotyczy 0183.
- W tle: pipeline krok A/B (build bez rzędu -> import -> Low/High ab-off) potem restore (build z kodem r3 + import). pytest tests/gis w tle.
## NASTĘPNY KROK (komenda)
po `restore done` w `artifacts/logs/pipeline-r2.status`: `uv run --project tools/worldgen python artifacts/bollards-0183/tools/make_cameras.py bialystok-dojlidy; pwsh artifacts/bollards-0183/tools/run_unity.ps1 -Steps low,high -Tag r3`
