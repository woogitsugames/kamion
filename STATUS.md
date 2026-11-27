# STATUS neon-avenue-s24 (szpalery drzew przy drodze — koniec „klonów bliźniaków”, dopisek ADR 0352)

- Worktree `neon-avenue-s24`, gałąź `neon-avenue-s24`. Nie scalane ani nie pushowane.
- Środowisko: prywatne kopie `Data/raw/derived/{knyszyn-w,dk65-07}` (pozostałe kafle junction do main, bez zapisu do main), Win64 `game/Library` lokalnie.
- [krok 1] Import bazowy Win64 (`knyszyn-w`, `dk65-07`) + rendery PRZED (`before`, High PC 1920×1080, `clear` + `overcast`, 10 kamer `knyszyn-w` + 6 kamer `dk65-07` = 32 PNG) w `artifacts/neon-avenue-s24/before/`.
- [krok 2] Implementacja w `tools/worldgen/streetscape/tree_rows.py` i `tools/worldgen/streetscape/vegetation.py` (commit `fb6c4e06e`):
  - Zmienność wieku/skali `0.70–1.15 × href_m`, brak powtarzania wariantu modelu (`v0/v1/v2`) na sąsiednich drzewach tego samego gatunku, separacja obrotu `yaw >= 1.05 rad` (~60°), pochylenie `0.005–0.065 rad`.
  - Przesunięcia wzdłuż (`10–16 m` BDOT / `12–18 m` `tree_rows`) i w poprzek (`σ = 1.0–1.05 m`, clamp `±2.5 m`), przerwy (`missing_share` 0.16–0.18), pojedyncze młode nasadzenia/samosiejki w ~35% luk (`birchyoung`/`linden`/`maple`/`shrub` 2–8,2 m), domieszka gatunków z dębem (`linden`/`maple`/`oak`/`birch`/`alder`). Zero nowych prototypów.
- [krok 3] Przebudowa `knyszyn-w` i `dk65-07` w prywatnej kopii `Data/raw/derived/`, import Win64, rendery PO (`after`, High PC 1920×1080, `clear` + `overcast`, 32 PNG) oraz porównania SBS ≤ 960 px (`artifacts/neon-avenue-s24/sbs/`), skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\neon-avenue-s24\`.
  - `knyszyn-w`: `treerow` 85 → 88 (16 luk, 4 `replants`, 26 dębów, h `11.2–18.9` → `2.4–19.5 m`), `total_trees` 11 360 → 11 327 (−33), `violations_after: 0`; visual-QA High: `scene_draws` −1..+0, `scene_tris` −25 954..−5 216, `inst_draws` −1..+7 (dąb ADR 0352 względem derived main z 17.11), `inst_tris` −104..+2 986.
  - `dk65-07`: `treerow` 18 → 17 (4 luki, 2 `replants`, 11 dębów, h `11.2–18.8` → `3.7–17.8 m`), `total_trees` 166 578 → 166 534 (−44), `violations_after: 0`; visual-QA High: `scene_draws` −1..+0, `scene_tris` −13 876..−10 860, `inst_draws` +0..+2, `inst_tris` −84..+728.
- [krok 4] Testy:
  - `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py`: **62 passed**.
  - `test_treerows_0222.py`, `test_trees_0308.py`, `test_trees_0352.py`, `test_trees_0347.py`: **73 passed, 1 failed** (`test_profile_table_matches_the_glb` — pre-existing różnica CRLF vs LF w hashu `trees_meta.json`, 29/29 prototypów identycznych; wszystkie 28 kafli korytarza ADR 0347 przeszły).
- [krok 5] Dopisek do `docs/adr/0352-drzewa-gatunki-tint-per-drzewo-dab.md`, cofnięty efekt uboczny Unity (`game/Assets/Resources.meta`), commit końcowy na `neon-avenue-s24`.
- GOTOWE DO SCALENIA PRZEZ LIDERA.
- NASTĘPNY KROK (lider): przejrzeć diff na `neon-avenue-s24` i dowody w `artifacts/neon-avenue-s24/sbs/`, scalić gałąź, a następnie w kolejnej fali regeneracji przebudować kafle z szpalerami (`knyszyn-w`, `dk65-01..11`, `dw671-tykocin-*`, `dk65-monki-*`):
  `git merge --no-ff neon-avenue-s24`

## codex-audio-wipers-s24 — rozpoznanie
Przeczytano reguły, ADR 0142 i 0341. Stan bazowy: zaparkowane pióra, brak osobnego zdarzenia serwisowego pisku.
Następny krok: pwsh scripts/visual-qa.ps1 -Scene DrivingLab -BuildTarget Win64 -Pc -Tier High -Lighting clear

Synteza gotowa: 8 własnych WAV (48 kHz mono), w tym suche i mokre pióra, park i hamulce w dwóch perspektywach. Render bazowy Win64 importuje zasoby.
Następny krok: pwsh scripts/build-lab.ps1 -SkipAudio -BuildTarget Win64 (jeśli bazowa scena wymaga odbudowy).

Sterowanie, HUD i zegar piór spięte z audio. GIS Win64/Python: 62/62. DrivingLab odbudowany lokalnie, zrzuty bazowe High clear i overcast z TRAKT-em.
Następny krok: pwsh scripts/test.ps1 -BuildTarget Win64

Zaimportowano 8 klipów w Unity Win64, wpisano referencje do biblioteki i dodano testy logiki oraz przejazdu w DrivingLab.
Następny krok: pwsh scripts/test.ps1 -Platform All -BuildTarget Win64

ADR 0355, docs/08 i rejestr licencji opisują procedurę, strojenie i źródła ośmiu klipów.
Następny krok: pwsh scripts/visual-qa.ps1 -Scene DrivingLab -BuildTarget Win64 -Pc -Tier High -Lighting overcast -WiperPhase 0.5

Próby hamulca w PlayMode zaczynają na początku prostej, aby obie perspektywy zmieściły się na placu. Telemetria zapisze ciśnienie i GC w aktualizacjach pisku.
Następny krok: pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64

Pierwsze EditMode: 1529 przeszło, 122 pominięto, 1 błąd limitu długości etykiety. Skrócono etykietę do Tryb wycieraczek. Nowe testy EditMode przeszły 11/11.
Następny krok: pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64

DrivingLab: 5 startów i 4 powroty piór przed końcem próby, pisk 17/64 w kabinie i 20/64 na zewnątrz, ciśnienie 0,460. Zmierzono 0 B GC w 8620 aktualizacjach.
Następny krok: pwsh scripts/visual-qa.ps1 -Scene DrivingLab -BuildTarget Win64 -Pc -Tier High -Lighting clear -WiperPhase 0.5
