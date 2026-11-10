# Zadanie dla agenta GPT (Codex) — import Megascans do generatorów świata (ADR 0084)

Repo: C:\Users\matma\Documents\Claude\kamion (Unity 6000.3.28f1 URP, Białystok 1:1, mobilny symulator ciężarówki).
Jesteś zwykłym agentem projektu, nie liderem: NIE scalasz do main, NIE pushujesz main, NIE ruszasz ProjectSettings/, Packages/, wspólnych scen ani worktree innych agentów w `.claude/worktrees/`.

## Najpierw przeczytaj
CLAUDE.md → docs/owner/AGENT-RULES.md → docs/06_GRAFIKA_ANTI_AI_SLOP.md → docs/PERFORMANCE_BUDGETS.md → docs/WORLD_GENERATION.md → docs/LICENSES.md (sekcja „Quixel Megascans z Fab”) → Data/SourceManifests/fab-megascans-2026-11-10.json → ADR 0063 (jak wpięto skany CC0: art-source/world/materials/_src/sets_scan.py, cc0_fetch.py).

## Przygotowanie
- `git worktree add .claude/worktrees/gpt-megascans -b gpt-megascans main` i pracuj WYŁĄCZNIE tam.
- `Data/raw` w nowym worktree: KOPIA (`robocopy C:\Users\matma\Documents\Claude\kamion\Data\raw <wt>\Data\raw /E`), nigdy junction do main. `git lfs checkout`.
- Utwórz `artifacts/megascans-r1/STATUS.md`; po KAŻDYM kroku: commit WIP + wpis w STATUS.md z następnym krokiem jako komendą.

## Cel
19 pobranych pozycji (`Data/raw/fab/<id>/*.zip`) wpiąć do generatorów tak, żeby było widać skok realizmu z kamery jazdy:
1. Krawężniki (`street-curbs`, `modular-curb`) → materiał/siatka krawężnika w generatorze dróg (tools/worldgen/roads, streetscape).
2. Studzienki/kratki (`round-manhole-cover`, `metal-manhole-cover`, `round-drain-cover`, `square-rusty-drain`) → dekale na jezdni/chodniku, rozmieszczenie wg reguł (wpusty przy krawężniku co 30–50 m, studzienki w osi pasa; WORKING_VALUE jeśli brak danych).
3. `trash-can`, `trash-bag-pack`, `urban-trash` → propsy przy przystankach, bramach, parkingach.
4. `grass-clumps`, `wild-grass`, `boxwood`, `elderberry` → roślinność pobocza i wysp (zastąpić/uzupełnić obecne).
5. `silver-birch-bark`, `pine-bark`, `birch-tree-trunk`, `linden-branch` → kora i liście NASZYCH generowanych drzew (brzoza, sosna, lipa).
6. `granite-rock`, `small-granite-rock` → kamienie polne na poboczach.
Każda siatka: własne LOD (LOD0/1/2), budżet tris i tekstur wg PERFORMANCE_BUDGETS (Low = Samsung A16), tekstury przeskalowane (zwykle 1k/512 na mobile), atlasy tam, gdzie się da.

## Twarde zasady
- **Licencja Fab Standard: żaden plik z Fab ani pochodna (FBX, PNG, atlas, wypalona mapa, .asset) nie może być śledzona przez git.** Przetworzone wyniki tylko w `game/Assets/_Generated/` lub `art-source/.../_generated` poza gitem (sprawdź .gitignore). W gicie: tylko kod generatorów, manifesty, testy, ADR. `uv run --project tools/worldgen pytest tests/gis/test_fab_not_tracked.py` musi być zielony; dopisz test, że w `git ls-files` nie ma żadnego pliku o hashu/ścieżce z Fab.
- Build musi działać także BEZ plików Fab (czysty klon publicznego repo) — fallback do obecnych materiałów, z ostrzeżeniem w logu.
- Bez marek/logo/napisów producentów (odrzuć, jeśli skan je ma).
- Nie zmyślaj liczb; WORKING_VALUE/UNVERIFIED tam, gdzie brak źródła.
- Bez telefonów/adb. Jeden proces Unity na katalog projektu (Twój worktree).

## Pętla jakości (obowiązkowa)
Po każdej rundzie: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` → `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/megascans-r1/<runda>/Low-overcast` (i High) → OBEJRZYJ PNG, porównaj z „before” i ze zdjęciami (Data/photos/nowe, docs/REFERENCES.md) → popraw. Zapisz samokrytykę wg docs/06 w STATUS.md.

## Definition of Done
pytest tests/gis zielone (poza znanym P0 korytarza s1432–1480, jeśli main go jeszcze ma), EditMode `pwsh scripts/test.ps1 -Platform EditMode` bez nowych porażek, budżet Low nie gorszy (stats z visual-qa), ADR `docs/adr/0084-megascans-import.md`, wpisy w docs/LICENSES.md (co i gdzie użyte), raport końcowy w `artifacts/megascans-r1/REPORT.md` (gałąź, sha, co zrobione, liczby, ścieżki PNG przed/po, otwarte, przewidywane konflikty: materials.py, plantings.py, life_props.py, build_world.py). Lider Claude scali gałąź `gpt-megascans`.
