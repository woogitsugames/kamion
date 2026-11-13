# bollards-0183 (ADR 0183: słupki biało-czerwone z łańcuchem) — LIVE
- Worktree `.claude/worktrees/bollards-0183`, gałąź `bollards-0183` od origin/main de4ff22ac. Data/raw: derived+cc0 kopia, reszta junctiony; Library, megascans, art-source (ignorowane) skopiowane z main.
- Krok 1 GOTOWY: moduł `tools/worldgen/streetscape/chain_bollards.py` (prototypy `bollard_rw_chain` 142/31 tris, `bollard_rw` 78/15 tris, 1 materiał `chain_bollard` = atlas alfa 256x512; override `kind: chain_bollards` w overrides.yaml; `walk` = słupki co 2,00 m po cięciwie). Wpięcie: props.build_all, export.textures, stage (po lamp_rows), materials (blok addytywny).
- Testy: `tests/gis/test_chain_bollards_0183.py` 18/18.
- Miejsce z P11-063 (Dojlidy, Mickiewicza, wsch. krawężnik jezdni NW): rząd lokalnie (-31.7, 382.3) -> (-25.44, 369.78), 7 przęseł / 8 słupków; EPSG:2180 (780011.3, 590461.3) -> (780017.56, 590448.78). Override testowy TYLKO lokalnie (nie commitować plików Dojlid).
## NASTĘPNY KROK (komenda)
`cd C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bollards-0183; pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner bollards-0183; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy *> artifacts/logs/bw-dojlidy.log; pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner bollards-0183`
