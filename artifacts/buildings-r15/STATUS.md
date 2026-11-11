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

## krok 2 — r1 zrenderowane (Low), P1-f od nowa, testy r7
- r1 = działki jako geometria chunka (`plot_kit` + `plot_lawn` + podjazd `paved`), 98 działek, 48 bram (9 przesuwnych),
  28 obniżeń krawężnika, 8 nakładek przez pobocze, 76,9 tys. tris `plot_kit`, 0 instancji. Region Low 3009 → 3072 submeshy,
  4,487 → 4,632 mln tris.
- Budżet Low, 67 kamer, r1 względem bazy (= main z działkami r6 jako instancje), `budget2.py`:
  MeshRenderer draws 18243 → 18459 (+216, maks. g3b-rondo-putry-approach +19, r10_shed_2 +16);
  instancjonowane 19314 → 19187 (−127); suma +89; r10_house_2 −33, r10_shed_2 −19; cienie MR +44 (maks. +6).
  UWAGA: względem świata BEZ działek najgorsza kamera MR to ok. +19 — ponad cel +15. Pomiar odniesienia `noplots` w toku.
- P1-f: paski ściany 12 cm obok końców parapetu (`sill_strip_uv1`, |u| ≥ 2) + nowy blok shadera (wąs na osi końca parapetu,
  siła ≥ 0,5). Jeszcze NIE zrenderowane ani zmierzone (`sill_contrast.py` — para Runoff on/off).
- Testy: `tests/gis/test_buildings_r7.py` 12 passed, r5/r6 dostosowane (30 passed łącznie w tych plikach). Pełny pytest i EditMode jeszcze nie.
- Obejrzane r1 `r10_house_2` Low: płot kuty na podmurówce ceglanej, brama, rabata, ciągły podjazd — OK; świerki za jasne
  (miętowe) → przyciemnić wiersz `spruce`; trawnik za mało różny od łąki.
- Do zrobienia: (A) bez żwirowych podjazdów i bez obrzeża `curb_concrete` na podjazdach działek (−2 submeshe / chunk),
  ew. (B) trawnik/podjazd tylko w LOD0/1; świerk ciemniej; kamery `cams_r15.py` (po buildzie z `plots.list`); ADR 0114.
- W tle: `noplots` (KAMION_NO_PLOTS=1) — build + import + QA Low/High.
- NASTĘPNY KROK: `python artifacts/buildings-r15/budget2.py artifacts/buildings-r15/noplots/Low-overcast artifacts/buildings-r15/base/Low-overcast artifacts/buildings-r15/r1/Low-overcast`
  → poprawki (A) → `pwsh artifacts/buildings-r15/chain.ps1 -Round r2 -Configs 'Low:overcast,High:overcast'` →
  `uv run --project tools/worldgen python artifacts/buildings-r15/cams_r15.py` → `pwsh artifacts/buildings-r15/extra.ps1 -Round r2`
