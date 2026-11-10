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
