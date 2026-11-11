# buildings-r15 (ADR 0114, zabudowa r7 — działki „wąsko i dobrze”) — STATUS

Gałąź `buildings-r7`, worktree `.claude/worktrees/buildings-r7`, z main `dd45e00c`.

## krok 1 — baza + przebudowa działek na geometrię chunków
- Skrypty r14 skopiowane do `artifacts/buildings-r15/` (ścieżki r15), `game/Library` z main (robocopy).
- Baza (`base/`): build_world z kodu main (356 s), import (550 s — przebudowa wszystkich zestawów PBR po świeżej kopii),
  QA Low/High overcast + 15 kamer `extra/`; snapshot `_snap/base`. Region High 4028 submeshy / 14,04 mln tris, Low 3009 / 4,487 mln.
- Nowy kod: `streetscape/plot_kit.py` (jeden atlas alfa 2048² — 7 typów ogrodzeń, cegła, próbki stali/drewna, tuja,
  świerk, karty drzewka/krzewu/bylin), `streetscape/plots.py` przepisane: zero instancji, wszystko w siatce chunka
  (`furniture`, materiał `plot_kit`), trawnik/podjazd/dojście jako powierzchnie `paved` (drape), obniżenie krawężnika
  (`apply_drops` przez `pipeline.build(side_edit=)`), typologia wg klasy wieku domu.
- Sucha próba planu (`plan_dry.py`): 98 działek (old 21 / prl 51 / new 26), 48 bram (9 przesuwnych), 35 zjazdów,
  28 obniżeń krawężnika, 76,9 tys. trójkątów `plot_kit` w regionie, 0 instancji.
- NASTĘPNY KROK: `pwsh artifacts/buildings-r15/chain.ps1 -Round r1 -Configs 'Low:overcast,High:overcast'` →
  `pwsh artifacts/buildings-r15/extra.ps1 -Round r1` → obejrzeć `r1/extra/960`.
