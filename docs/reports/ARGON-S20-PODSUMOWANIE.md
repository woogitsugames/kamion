# ARGON-S20 — Podsumowanie (checkpoint 2026-11-15 11:44)

| # | ADR | Gałąź | SHA | Gotowe do scalenia | Najważniejsze liczby / stan | Otwarte / co zostało |
|---|---|---|---|---|---|---|
| 1 | 0194 | `stains-0194` | `5b87ea429` | **TAK** | `after4` (D+C): ciemne plamy oleju, łaty z 25 mm szwem wg klasy/wlotów, `_GrimeTraffic`, naprawione UV1 poboczy/płyt; `EditMode 583/584`, `pytest-gis 1157/1159` (upstream); `REVIEW-ARGON-stains-0194.md`: **SCAL** | P2 (`wheel_darkening` na nowych drogach, pomiar ALU na A16) |
| 2 | 0188 | `ddr-0188` | `503848f8b` | **TAK** | M65 `r4`: ciepłoszary DDR w D (`6894 m`, `away`, przerwy na `service`), czerwono-brunatny w C (`8516 m²` Rondo Putry), 25 czerwonych P-11; `EditMode 580/581`, `pytest-gis 1157/1162` (5 upstream); `REVIEW-ARGON-ddr-0188.md`: **SCAL warunkowo** (0 P0/P1) | Po scaleniu: odświeżyć `fidelity_qa.json` + zrzut A16 przed bramką |
| 3 | 0193 | `sigplate-0193` | `5b77931d4` | **TAK** | M66 rundy 3 (`after-C3`/`after-D3`): tarcza `0,85×1,40 m` R70 z obwódką `40 mm` tylko na wysięgnikach (`-1144` tris C / `-592` tris D), D-6 na `P11-094` OK; `EditMode 580/581`, `pytest-gis 1168/1169` (`0185` niezwiązany); `REVIEW-ARGON-sigplate-0193.md`: **SCAL** | P2 nieblokujące (piktogramy `ped`/`bike`, obejma wysięgnika); zrzut z telefonu przed bramką |
| 4 | 0187 | `forest-0187` | `aa76c671e` | W TOKU | Scalono `origin/main`, zacommitowano M68 §6 (BDL/NMPT 2023: `forest_stand`, `UNDERSTOREY` `pineyoung=0`, częściowy płaszcz krzewów/HLOD, `tree_stand`, `docs/LICENSES.md`) | Trwa: `build_world` D+C, render `after2` (Low/High), `EditMode` + `pytest`, ADR `0187`, `Reviewer`, `robocopy`, `ARGON-S20-forest-0187.md` |
| 5 | 0186 | `dojgreen-0186` | `da3640105` | **TAK** | Runda `B-r4`: naprawiono P1-1/P1-2/P1-3 z recenzji + scalono `e668a9588` (płoty Low); `P11-063` Low `279 draws / 339k tris / 98.8 MB`, High `461 draws / 754k tris / 214.1 MB`; `test_dojgreen_0186+0179` `13/13`; `REVIEW-ARGON-dojgreen-0186.md`: **SCAL** | Drobne P2 (`thicket` High cętki, odcień `berberis_red`); po scaleniu pełny `EditMode` + `pytest` + zrzut z telefonu |
| 6 | 0189 | `hospgate-0189` | `fa709e40c` | W TOKU | Scalono `origin/main` (`M62-FIX`); trwa wdrażanie poprawek `r4` (`masonry_gate.py`, `overrides.yaml`, `plantings.py`, `stage.py`, `test_masonry_gate_0189.py`) | Trwa: dokończenie `r4`, `build_world` D, render `r4` (Low/High), `EditMode` + `pytest`, ADR `0189`, `Reviewer`, `robocopy`, `ARGON-S20-hospgate-0189.md` |

## Pliki już zapisane w głównym repozytorium
- `docs/reports/REVIEW-ARGON-sigplate-0193.md` (**SCAL**), `docs/reports/ARGON-S20-sigplate-0193.md`, `artifacts/sigplate-0193/`
- `docs/reports/REVIEW-ARGON-dojgreen-0186.md` (**SCAL**), `docs/reports/ARGON-S20-dojgreen-0186.md`, `artifacts/dojgreen-0186/`
- `artifacts/live/{stains-0194,ddr-0188,sigplate-0193,forest-0187,dojgreen-0186,hospgate-0189}.md` (zsynchronizowane z worktree)
