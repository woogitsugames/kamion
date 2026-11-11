# Zadanie dla GPT (sesja z 3 agentami) — pakiet S10: kalibracja materiałów, roślinność, światło/post (+ nawierzchnie, remiza)

Repo: C:\Users\matma\Documents\Claude\kamion (Unity 6000.3.28f1 URP, Białystok 1:1, mobilny symulator ciężarówki). Wymagania jak w `docs/owner/GPT-TASK-01-MEGASCANS.md` (sekcje „Najpierw przeczytaj”, „Twarde zasady”, „Pętla jakości”) — obowiązują w całości. Jesteś koordynatorem tej sesji GPT i możesz prowadzić **do 3 agentów naraz**, każdy w swoim worktree i na swojej gałęzi. **Nie scalasz do main i nie pushujesz main** — scala lider Claude po `REPORT.md`.

## Najpierw przeczytaj (wszyscy agenci)
HANDOVER.md (górna sekcja s9) → CLAUDE.md → docs/owner/AGENT-RULES.md → docs/06_GRAFIKA_ANTI_AI_SLOP.md → docs/PERFORMANCE_BUDGETS.md → recenzje `docs/reports/visual/REVIEW-2026-11-11-s9*.md` (tam są liczby i listy wad, z których wynikają te zadania).

## Przygotowanie każdego worktree (WAŻNE — inaczej wyniki są fałszywe)
- `git worktree add .claude/worktrees/<nazwa> -b <gałąź> main` (z AKTUALNEGO main), `git lfs checkout`.
- KOPIE (robocopy): `Data\raw\derived`, `Data\raw\cc0`, `art-source\world\cc0\_raw`, **`art-source\world\megascans`** (lokalne produkty Fab — bez nich generator po cichu robi fallback; sprawdź w logu build_world, że NIE ma `fallback=True`), `game\Assets\_Generated`. Junctiony tylko do odczytu: `Data\raw\{gugik,osm,refs,mapillary,fab}`.
- `uv run pytest` bywa zepsuty — używaj `uv run --project tools/worldgen python -m pytest tests/gis -q` (main: zielony).
- STATUS.md w `artifacts/<dir>/`: po KAŻDYM kroku commit WIP + wpis z NASTĘPNYM KROKIEM jako komendą (limit może ubić w każdej chwili).
- Unity: jeden proces na worktree; efekty uboczne (`game/Assets/_Project/Rendering/Settings/Lighting`, `game/ProjectSettings`) cofaj `git checkout --`. Bez telefonów/adb.

## NIE ruszać (pracują inni)
- Claude: `tools/worldgen/roads/*` i `overrides.yaml` (ADR 0095 węzły), `tools/worldgen/streetscape/{buildings_mesh,facade_kit,roofs}.py` i zestawy budynków (ADR 0097 zabudowa r5). Argon: `far_field.py`, `WorldEdgeBuilder.cs` (0085), shadery/kod ciężarówki (0087).
- Wspólne pliki (`WorldPbrMaterials.cs`, `WorldPBR.shader`, `WorldSurface.shader`, `materials.py`) — tylko zmiany addytywne, opisane w REPORT jako „przewidywane konflikty”. Zachowaj istniejące reguły: `_Tile` = `set_tile || elementScan || atlas`; zacieki `weather`‖`runoff`; `macro`, `panel_m`, `splash_h`.

## Strumienie (3 naraz; kolejność scalania przez lidera: A → B → C)

### A — ADR 0086: globalna poprawka `_Tint` (gamma) + przekalibrowanie zestawów
Gałąź `gpt-tint-gamma`, STATUS `artifacts/tint-gamma-r1/STATUS.md`. Treść jak Q1 w GPT-TASK-01: `_Tint` w `Kamion/World PBR` jest `Color` i jest linearyzowany drugi raz (kolor^2,2). Budynki mają już flagę `tint_linear` (ADR 0081) — rozszerz poprawną konwersję na WSZYSTKIE zestawy (ekrany, ogrodzenia, wiadukt, rekwizyty, nawierzchnie, hala Kwadrat Park, remiza), każdy przekalibruj do zmierzonego albedo/zdjęć (były strojone pod błąd). Dowód: kamery kontrolne przed/po Low/High × clear/overcast + tabela jasności wycinków (asfalt, kostka, tynk remizy cel 110/126/145 ±10, hala, ekrany) vs zdjęcia. Nic nie może „skoczyć” bez uzasadnienia. ADR `docs/adr/0086-world-pbr-tint-gamma.md`.

### B — ADR 0088: roślinność r2 (drzewa, korony, trawa, krzewy)
Gałąź `gpt-vegetation-r2`, STATUS `artifacts/vegetation-r2/STATUS.md`. Każda recenzja s9 ma tę samą czerwoną flagę: **drzewa to czarne kleksy/ciemne sylwetki, trawa wszędzie taka sama z beżową obwódką tej samej szerokości przy każdej krawędzi, żywopłot jak zielony graniastosłup**. Cel:
1. Drzewa (sosna, brzoza, lipa + to, co rośnie przy trasie wg BDOT/OSM): kora i liście z Megascans tam, gdzie R1 je dopuścił (brzoza `silver-birch-bark`, `birch-tree-trunk`, lipa `linden-branch`; kora sosny ze skanów CC0 — Fab `pine-bark` odrzucony), pokrój z prześwitami, LOD0/1/2 + billboard; korony **nie w czerni**: pomiar p10/p50 koron w kadrze vs zdjęcia (por. ADR 0080 r11: LeafAmbient, lt16).
2. Trawa: wariacja w skali metrów (wydeptanie, suchsze pasy, kępy), obwódka przy krawężniku tylko tam, gdzie fizycznie jest (piasek/sól), różna szerokość.
3. Krzewy i żywopłoty (`boxwood`, `elderberry`, tuje, berberys) z sylwetką, nie bryłą.
Budżet Low (A16) bez wzrostu draws na kamerach trasy; tris ≤ +3 %. ADR `docs/adr/0088-vegetation-r2.md`.

### C — ADR 0098: światło i post-process r12
Gałąź `gpt-light-r12`, STATUS `artifacts/light-r12/STATUS.md`. Zebrane z recenzji s9:
1. „Pieprz” na High: wariancja < 2 px na płaskich ścianach i niebie (High 1,03 vs Low 0,16 na niebie) — prawdopodobnie dithering + RCAS profilu High; zmierz i usuń bez utraty ostrości.
2. Ekspozycja clear: biała ściana przepalona 251–254 (`r10_house_2` High clear) — dobierz ekspozycję/tonemapping tak, żeby biel ≤ ~240 bez ciemnienia asfaltu (różnica niebo−asfalt ~116–121 jak na zdjęciach, ADR 0080 r11).
3. Cienie przy ślizgowym słońcu: schodkowe krawędzie cieni (plandeka naczepy w `stretch-05-docks`), jasne trójkąty na szybach hali, samozacienianie ścian hal w `clear` — bias/normal bias/rozdzielczość kaskad per tier.
4. Mgiełka dalekich pionów (kominy/słupy > 300 m ostre przy mlecznym niebie), niebo Low bez struktury, brak cienia/AO pod wiaduktem.
Pliki: `KamionAtmosphere`, presety światła, `QualityProfile`/`RenderOverrides`, shadery — nie `ProjectSettings/` (tylko lider). A/B przełączniki `rq_*` dla telefonu. Budżet GPU na Low nie gorszy. ADR `docs/adr/0098-light-post-r12.md`.

### Gdy zwolni się miejsce (po A, B lub C)
- **D — ADR 0099: zużycie nawierzchni** (gałąź `gpt-surface-wear`, STATUS `artifacts/surface-wear-r1/STATUS.md`). START dopiero gdy na main jest scalone ADR 0095 (sprawdź `git log main --oneline | grep 0095`). Asfalt „sterylny” w każdej recenzji: łaty, koleiny na pasach ciężarówek, spękania podłużne/siatkowe, plamy oleju na skrzyżowaniach i przystankach, przetarcia farby oznakowania (przejścia, linie zatrzymania, strzałki — mocniej w śladach kół), ślady opon na wjazdach do bram. Tylko materiały/dekale/maski (WorldSurface/WorldPBR, warstwy wear) — bez zmian geometrii dróg. Kalibracja do zdjęć z `Data/photos` i Mapillary (tylko referencja). ADR `docs/adr/0099-road-surface-wear.md`.
- **E — ADR 0090: remiza JRG2 r7** (gałąź `gpt-firestation-r7`, STATUS `artifacts/firestation-r10/STATUS.md`). Lista z `docs/reports/visual/REVIEW-2026-11-11-s9.md` §1: świerki piętrowe z prześwitami przesunięte 3–5 m w prawo (oba łuki okien widoczne jak na zdjęciu 7197), tuje 3 kształty z rozrzutem odstępu ±25 % i ten sam kolor na Low i High, szkło okien łukowych cel 60–75 sRGB z gradientem nieba, zacieki pod obróbką i strefa rozbryzgu, skrzydło z wieżą nie ciemniejsze od szczytu, filary klinkier brąz, kratki/flaga. Pliki: `sets_fire_station.py`, `make_fire_station.py`, `art-source/world/landmarks/fire_station_jrg2/`. Referencja: `artifacts/firestation-r9/refs/lead_7197_960.jpg`. ADR: dopisz „r7” do `docs/adr/0070-hero-fire-station.md`.

- **F — ADR 0087: ciągnik TRAKT — lakier kabiny, szyba czołowa, reflektory w dzień** (przeniesione od Argona; gałąź `gpt-truck-paint`, STATUS `artifacts/truck-paint-r1/STATUS.md`). Treść = „Q1 (ADR 0087)” w `docs/owner/ARGON-TASK-01-WORLD-EDGE.md` (lakier kredowy bez odbić → połysk/fresnel/odbicie nieba; szyba mleczna; reflektory pełną bielą w dzień; `TruckExterior.shader`, szkło kabiny, `TruckLights.cs`; po zmianach `Game.Editor.Setup.TruckAssetBuilder.BuildBatch` + `Game.World.Import.WorldTruckInstaller.InstallBatch`; kamery `chase,truck-side,truck-rear34` + kabina, Low/High × clear/overcast/lowsun). Uwaga: integracja s9 zgłosiła pikselowe odbicie w szybie czołowej w `truck-at-gate`. ADR `docs/adr/0087-truck-cab-paint-glass-lights.md`.
- **G — ADR 0089: osobówki — czarny lakier na pionach, koła z bliska, brud progów** (przeniesione od Argona; gałąź `gpt-car-paint`, STATUS `artifacts/car-paint-r1/STATUS.md`). Treść = „Q2 (ADR 0089)” w ARGON-TASK-01: drzwi czarnego auta 21–24 sRGB w High overcast → cel 30–40 bez rozjaśniania maski; felga szara z ciemniejszym dnem, więcej segmentów < 8 m, opona neutralna; brud progów 3–4 poziomy per instancja. Może iść równolegle z C (inne pliki: `_CARPAINT` w `WorldPBR.shader` — uzgodnij z C, jeśli C rusza ten shader). ADR `docs/adr/0089-car-paint-vertical-reflections.md`.
- Kolejność dla wolnych miejsc: F, G, E, D (D dopiero po scaleniu 0095).

## Definition of Done (każdy strumień)
pytest tests/gis zielone · EditMode bez nowych porażek · budżet Low nie gorszy (stats z visual-qa) · obejrzane PNG przed/po (Low/High × overcast/clear) z samokrytyką wg docs/06 · liczby zmierzone, nie zmyślone (WORKING_VALUE/UNVERIFIED) · ADR · `artifacts/<dir>/REPORT.md` (gałąź, sha, co zrobione, liczby przed/po, ścieżki PNG, otwarte, przewidywane konflikty z innymi strumieniami i z Claude) · kopia `artifacts/<dir>` do main `artifacts/<dir>` (robocopy, bez commitowania do main).

Numery ADR zarezerwowane dla tej sesji: 0086, 0088, 0098, 0099, 0087, 0089 (+ 0090 r7). Ostatni przydzielony w projekcie: **0099**.
