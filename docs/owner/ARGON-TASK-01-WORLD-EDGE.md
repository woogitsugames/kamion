# Zadanie dla agenta Antigravity (Argon 4) — tło za krawędzią świata (ADR 0085)

Repo: C:\Users\matma\Documents\Claude\kamion (Unity 6000.3.28f1 URP, Białystok 1:1, mobilny symulator ciężarówki).
Jesteś zwykłym agentem projektu, nie liderem: NIE scalasz do main, NIE pushujesz, NIE ruszasz `ProjectSettings/`, `Packages/`, asmdef, wspólnych scen ani worktree innych agentów w `.claude/worktrees/` (pracuje tam równolegle ok. 9 agentów, w tym GPT w `gpt-megascans`).

## Najpierw przeczytaj
CLAUDE.md → docs/owner/AGENT-RULES.md → docs/06_GRAFIKA_ANTI_AI_SLOP.md → docs/PERFORMANCE_BUDGETS.md → docs/WORLD_GENERATION.md → docs/05 (mapa Białystok i dane) → **docs/adr/0082-speed-limiter-world-edge.md** (krawędź regionu: zapory, fartuch terenu pierścienie 0/60/300/2600 m, `WorldEdgeBuilder`) → docs/LICENSES.md.

## Przygotowanie
- `git worktree add .claude/worktrees/argon-edge -b argon-edge main` i pracuj WYŁĄCZNIE tam.
- `Data/raw` w nowym worktree: `derived` i `cc0` jako KOPIA (`robocopy <main>\Data\raw\derived <wt>\Data\raw\derived /E /XJ`), `gugik`, `osm`, `refs`, `mapillary` mogą być junctionami (tylko odczyt — nigdy nie zapisuj do nich; nowe pobrania zapisuj w `<wt>\Data\raw\derived\far-field\` lub nowym katalogu w worktree). Nie kopiuj `Data/raw/fab`. `git lfs checkout`. Możesz skopiować `game/Library` z main (robocopy) zamiast pełnego importu.
- Utwórz `artifacts/edge-far-r1/STATUS.md`; po KAŻDYM kroku: commit WIP + wpis w STATUS.md z następnym krokiem jako gotową komendą.

## Problem
Region `bialystok-industrial-c` to 2048 × 2048 m. Za krawędzią (po ADR 0082) jest goły fartuch terenu do horyzontu — kierowca widzi pustą, gładką równinę. W realu na N za al. Tysiąclecia, na E/W/S widać las, osiedla bloków, hale, kominy, linie wysokiego napięcia. Właściciel nagrał film (artifacts/owner/fold-video-2026-11-10/, ~116 s): „koniec świata = biała pustka”.

## Cel
Tło dalekie (far-field) za bbox regionu, z PRAWDZIWYCH danych, tanie na mobile:
1. Dane: OSM (Overpass, licencja ODbL — wpis w LICENSES/manifest) dla pierścienia ~2–6 km wokół bbox: `landuse=forest/residential/industrial`, `natural=wood`, budynki z `building:levels`/`height` (albo BDOT10k/LoD1 GUGiK, jeśli jest w Data/raw/gugik), linie `power=line`, kominy `man_made=chimney`. Manifest źródła z SHA256 w `Data/SourceManifests/`. Teren za krawędzią: NMT GUGiK, jeśli dostępny dla pierścienia, inaczej zostaje fartuch 0082.
2. Geometria: sylwetki lasu (pas koron z wariacją wysokości, nie płaski mur), bryły bloków/hal jako LoD1 z prostą elewacją (atlas okien w odległości), kominy i słupy WN jako proste siatki; wszystko w 1–3 dużych siatkach na kierunek (mało draw calli), bez cieni, bez kolizji, za mgłą powietrzną. Ma czytać się jak Białystok z 300–2000 m, nie jak gra mobilna.
3. Integracja: generator w `tools/worldgen` (Python, odtwarzalny) → GLB w `_Generated` → `WorldEdgeBuilder`/import-region ładuje to w scenie `WorldC`. Zapory i powrót z 0082 bez zmian.
4. Budżet: Low (Samsung A16, 30 kl./s) — far-field maks. ~4 draw calle, ≤ 30k tris, tekstury ≤ 1 MB; High/Ultra mogą mieć więcej. Zmierz (stats z visual-qa) i zapisz w ADR.

## Twarde zasady
- Zakaz Google Maps/Street View/Earth/3D Tiles. Referencje tylko z otwartych źródeł (Mapillary przez `tools/refs`, Wikimedia, GUGiK ortofoto, OSM). Bez marek/logo.
- Nie zmyślaj liczb: zmierz albo `WORKING_VALUE`/`UNVERIFIED`.
- Bez telefonów/adb. Przed KAŻDYM startem Unity sprawdź `C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN` — jeśli istnieje, czekaj. Po Unity cofnij efekty uboczne (`M_Sky.mat`, `QualitySettings.asset`, preloadedAssets w `ProjectSettings.asset`).
- Pliki `Data/Regions/*/generated/*.json` regeneruj, nie edytuj ręcznie.

## Pętla jakości (obowiązkowa)
Kamery kontrolne patrzące za krawędź (z kabiny na al. Tysiąclecia N 900–1000 m, i po jednej na E/W/S): `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low|High -Lighting clear|overcast -OutputDir artifacts/edge-far-r1/<runda>/<tier>-<light>` → OBEJRZYJ PNG (≤ 960 px), porównaj z „przed” i z ortofoto/zdjęciami → popraw. Samokrytyka wg docs/06 w STATUS.md. Min. 2 rundy.

## Definition of Done
`uv run --project tools/worldgen pytest tests/gis -q` bez nowych porażek (+ nowy test generatora far-field), EditMode `pwsh scripts/test.ps1 -Platform EditMode` bez nowych porażek, PlayMode `-Filter WorldEdgeRecoveryTests` zielone, budżet Low w normie, ADR `docs/adr/0085-far-field-backdrop.md`, wpisy w docs/LICENSES.md, raport `artifacts/edge-far-r1/REPORT.md` (gałąź, sha, liczby, PNG przed/po, otwarte, przewidywane konflikty — prawdopodobnie `WorldEdgeBuilder.cs`, `build_world.py`, `import-region.ps1`). Lider Claude scali gałąź `argon-edge`.

---
## KOLEJKA — kolejne zadania (dopisuje lider; po skończeniu zadania przeczytaj ten plik ponownie i bierz następne niezrobione)
Zasady jak wyżej (własny worktree z AKTUALNEGO main, kopia Data/raw/derived, STATUS po każdym kroku, nie scalasz, REPORT.md na koniec).

### Q1 (ADR 0087) — ciągnik TRAKT: lakier kabiny, szyba czołowa, reflektory w dzień
Z recenzji `docs/reports/visual/REVIEW-2026-11-10-0070-0083.md` (sekcja 0083, P1 5–7, scalone w main `68e5335`): lakier kabiny kredowy bez odbić (realny lakier użytkowy: połysk, odbicie nieba, fresnel), szyba czołowa mleczna, reflektory świecą pełną bielą w dzień. Pliki: `TruckExterior.shader`, shader szkła kabiny, `TruckLights.cs` (przeczytaj ADR 0083, 0059 i D31/D34/D44 w docs/11 — wymagania odbicia szyby). Po zmianach: `Game.Editor.Setup.TruckAssetBuilder.BuildBatch`, `Game.World.Import.WorldTruckInstaller.InstallBatch`, kamery `chase,truck-side,truck-rear34` + kabina, Low/High × clear/overcast/lowsun, EditMode zielone, budżet bez zmian. P2 jeśli czas: płaskie klosze lamp, plamy na szybie bocznej. Gałąź `argon-truck-paint`, STATUS `artifacts/truck-paint-r1/STATUS.md`, ADR `docs/adr/0087-truck-cab-paint-glass-lights.md`.

### Q2 (ADR 0089) — osobówki: czarny lakier na pionach, koła z bliska, brud progów
Z recenzji `docs/reports/visual/REVIEW-2026-11-11-s9.md` (§2 i kolizje pkt 6; 0078 i 0080 scalone na main `2ab23b2`): drzwi czarnego auta 21–24 sRGB w High overcast (opona 49, niebo ~197) — czarna dziura bez odbicia gruntu/horyzontu. Cel: **drzwi ≥ 30 (cel 30–40) w High overcast**, bez rozjaśniania maski (74) i bez utraty czerni w clear. Kod: `WorldPBR.shader` blok `_CARPAINT`, `WorldPbrMaterials.cs`, ewentualnie probe/ambient z `KamionAtmosphere` (ADR 0080) — dolna granica odbicia dla powierzchni pionowych. Dodatkowo P1: koło z bliska (felga szara z ciemniejszym dnem, więcej segmentów obrysu < 8 m, opona neutralna) i brud progów losowany per instancja (3–4 poziomy, w tym czyste). Kamery z `artifacts/cars-r10` (`r10b_black_05`, `r10_wheel_02`, `sheet_far`) High/Low × overcast/clear; budżet Low bez wzrostu; EditMode zielone. Gałąź `argon-car-paint`, worktree `.claude/worktrees/argon-car-paint`, STATUS `artifacts/car-paint-r1/STATUS.md`, ADR `docs/adr/0089-car-paint-vertical-reflections.md`.

### UWAGI LIDERA s9 do ADR 0085 (PRZED scaleniem — zrób najpierw, potem Q1)
Twój stan końcowy zacommitował lider na `argon-edge` (`wip(edge): Argon final state…`; katalogi `art-source/truck/*/export/export/` NIE weszły — usuń je, to zbędne kopie 197 MB). Lider obejrzał `r0-before` vs `r2` Low-overcast:
1. **`edge-south`, prawa strona tuż za ogrodzeniem:** w `r0-before` widać kremowy 3-kondygnacyjny biurowiec z regionu; w `r2` zamiast niego długa hala z czerwonym pasem w stylu `_FAR_FACADE`. Podejrzenie: budynki przecinające granicę 2048 m są w far-field drugi raz (pełny obrys BDOT/LoD1) i zasłaniają/dublują budynek regionu. Sprawdź i wyklucz z far-field każdy budynek, którego obrys przecina region (albo przytnij do zewnątrz), dodaj test (`far_field` ∩ obrysy regionu = ∅). Pokaż ten kadr przed/po.
2. `dk8-dk19-exit`: zmiana ledwo widoczna — OK, ale w REPORT podaj kadr, gdzie las Pietrasze faktycznie zamyka horyzont.
3. Bazę zrób z aktualnego main (`git merge main` — main poszedł daleko: 0076, 0077, 0084, 0091…; konflikty generated → ours + regeneracja), potem pytest gis (main ma 2 znane czerwone z 0077, naprawia je 0093 — nie Twoje), EditMode, PlayMode `WorldEdgeRecoveryTests`.
Po tym dopisz do REPORT.md sekcję „Poprawki po uwagach lidera” — lider scali.

### ZMIANA KOLEJKI (lider s9, 2026-11-11): Argonowi zostało ~8 % limitu
Zrób TYLKO „UWAGI LIDERA s9” do ADR 0085 (budynki przecinające granicę wykluczone z far-field + test + kadr `edge-south` przed/po + `git merge main` + pytest gis + REPORT „Poprawki po uwagach lidera”). Commit WIP po każdym kroku. **Q1 (0087) i Q2 (0089) przeniesione do GPT** (`docs/owner/GPT-TASK-02-S10.md`, strumienie F i G) — nie zaczynaj ich.
