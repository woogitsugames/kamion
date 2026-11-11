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

## krok 3 — odniesienie `noplots`, r2, pomiar zacieków (po resecie limitu)
- `noplots` (świat bez działek) = prawdziwe odniesienie budżetu. Low, 67 kamer, MeshRenderer + instancjonowane:
  r6 (main): suma +152, maks. +45 (r10_house_2); r1: suma +241, maks. +20; r2 (bez żwiru i obrzeża): suma +192, maks. +15
  (r10_shed_2), MR maks. +15, cienie MR +44 (maks. +6). Pliki `budget_low_r1.txt`, `budget_low_r2.txt`.
- r3 w budowie: warstwa `plot_ground` (trawnik/podjazd tylko LOD0/1 chunka, bez cieni) — ma zbić sumę w dalekich kadrach.
- P1-f zmierzone na r2 (para Runoff on/off, `sill_r2.txt`): 20 m — wąsy średnio 10,0 poziomu sRGB (p10 8,1), rdzeń 14,8;
  5 m — p50 9,0 / p90 27,6 poziomu na pikselach śladu.
- Znalezione: krawężnik przy `r15_front_brick_bars` NIE wygląda na obniżony i podjazd kończy się ~0,5 m przed nim
  (pas trawy) → `drop_check.py` (w toku) sprawdza wysokość krawężnika w siatce przed/po `apply_drops`.
- Tuje: graniaste „kryształy” z plamiastą teksturą → do poprawy (więcej boków/pierścieni, gęstsza tekstura).
- NASTĘPNY KROK: `cat <wynik drop_check>` → poprawka zjazdu → `pwsh artifacts/buildings-r15/run_round.ps1 -Round r3 -Configs 'Low:overcast,High:overcast'`
  (świat r3 już zbudowany, jeśli `r3/round.log` ma `build_world exit 0`) → `python artifacts/buildings-r15/budget2.py artifacts/buildings-r15/noplots/Low-overcast artifacts/buildings-r15/r3/Low-overcast`

## krok 4 — r3/r4/r5, testy
- r3: warstwa chunka `plot_ground` (trawnik + podjazd tylko LOD0/1, bez cieni) → Low razem +118 / maks. +11.
- r4: pas kostki domykający lukę przed krawężnikiem (`drop_check.py`: 26 z 35 zjazdów < 6 cm), tuje bardziej obłe.
- `pytest` wykrył przekroczenie budżetu `stretch_04` High (2,011 mln > 2,000) → r5: tuje 6 boków i ≤ 12 w rzędzie,
  lżejsze ramy bram, przęsła co 5,12 m: `plot_kit` 76,9 k → 57,0 k tris, `stretch_04` 1,992 mln.
- Skrypty rund biorą slot Unity (`scripts/unity-slot.ps1`, owner `claude-buildings-r7`).

## RAPORT KOŃCOWY (docs/09 §4)
ZADANIE: ADR 0114 — zabudowa r7, działki „wąsko i dobrze”. Gałąź `buildings-r7` (z main `dd45e00c`), ostatni sha: patrz `git log -1`.
ZROBIONE:
1. Budżet — działki bez instancji: jedna siatka na chunk w materiale `plot_kit` (atlas 2048²) + warstwa `plot_ground`.
   Low overcast, 67 kamer, względem świata BEZ działek (`noplots`), `budget_low_r5.txt`:
   | | r6 (main) | r7 (r5) |
   |---|---|---|
   | draws MeshRendererów suma / maks. | +0 / +0 | +97 / +10 |
   | draws instancjonowane suma / maks. | +152 / +45 (`r10_house_2`) | +21 / +5 (instancji działek: 0) |
   | razem suma / maks. | +152 / +45 | +118 / +11 (`r10_house_1`) |
   | draws cieni MR suma / maks. | 0 (cienie instancji nieliczone) | +44 / +6 |
   | trójkąty siatek, k (same działki) suma / maks. | 0 | +169 / +19 |
   High overcast (`budget_high_r5.txt`): razem +282 / +51 → +359 / +29 (suma gorsza niż r6), cienie +189 / +27,
   trójkąty +994 k (+2,5 %), maks. +97 k (`r10_fence_1`, +15 %). Zasięg: LOD0/LOD1 chunka (~300 m), było 60 m na Low.
2. Płoty wg typologii z referencji i klasy wieku domu (98 działek: old 21 / prl 51 / new 26); 11 stylów, matowe.
3. Front: furtka + brama (48, w tym 9 przesuwnych), ciągły podjazd (48), dojście, obniżony krawężnik (28; zmierzone
   3,0–4,6 cm na 26 z 35 zjazdów), pas trawy 1,5 m, skrzynki, śmietniki, kolizja płotów.
4. Ogród: trawnik `plot_lawn`, 1100 kart bylin, 435 tuj (nieregularne), 22 świerki, 54 jabłonie, 253 krzewy.
5. P1-f: wąsy od końców parapetu — 5 m: rdzeń 19,3 poziomu sRGB; 14 m: 22,0; 20 m: mediana 10,2 (p10 5,2, p90 18,4), 32 ślady
   (`sill_r5.txt`, `sill_marks.py`, para Runoff on/off).
PLIKI: `tools/worldgen/streetscape/{plots.py, plot_kit.py, buildings_mesh.py, stage.py, paved.py, materials.py, export.py, props.py}`,
  `tools/worldgen/roads/{build_world.py, pipeline.py, standards.py}`, `game/Assets/_Project/World/Import/{RegionImporter, WorldSceneBuilder, WorldSkyBake, WorldPbrMaterials, InstanceImporter}.cs`,
  `game/Assets/_Project/Editor/VisualQA/Gate3Audit.cs`, `game/Assets/_Project/Environment/Shaders/WorldPBR.shader`,
  `tests/gis/test_buildings_r{5,6,7}.py`, `docs/adr/0114-buildings-r7-plots.md`, `docs/LICENSES.md`, dane wygenerowane regionu.
TESTY: `pytest tests/gis` 481 passed / 1 xfailed / 1 failed (`test_road_fidelity::test_report_not_stale` — raport sprzed
  zmian w `roads/*.py`); po `fidelity/run.py` plik przechodzi (46 passed w plikach fidelity + hero_bridge + buildings r5–r7).
  EditMode 261 / 261 (`r5/editmode.log`). Bez telefonu, bez visual-critic.
DOWODY (PNG ≤ 960 px): `pairs/ref_*.jpg` (render | klatka referencji: picket_C04, boards_P09, chainlink_P10,
  brick_picket_C01, brick_bars_P24, bars_P06, wall_P14, lamella_P13, concrete_P10, cab0_P08), `pairs/base_*.jpg`
  (main | r5: r14_plot2_eye_az250, r14_plots_aerial_low, r13_houses_aerial, r13_block3_close …), `pairs/base_low_*.jpg`
  (Low: r10_house_1/2, r10_shed_2, r10_fence_2, r10_block_3); pełne zestawy `r5/{Low-overcast,High-overcast,High-clear}/960`,
  `r5/extra/960` (33 kamery), `r5/extra_low/960`, `r5/sill_off/*_diff.png`.
OTWARTE: High droższy w sumie niż r6; zapas `stretch_04` High 7,6 k tris; brak ditheru przy znikaniu (tylko zasięg);
  7 zjazdów bez obniżenia (łaty skrzyżowań), 13 bram bez dojazdu do jezdni; tuje / świerki low-poly z bliska, bez wiatru;
  mur i beton skosem po terenie; dojście do ściany, nie do drzwi; żwirowe podjazdy usunięte dla budżetu; najsłabsze 10 %
  zacieków ~5 poziomów z 20 m; kamery `r14_plot2_eye_az160` (w ścianie) i `r15_dist_250` (pod wiaduktem) do przestawienia;
  działki nadal z reguły, nie z EGiB.
KONFLIKTY: `stage.py`, `props.py`, `export.py`, koniec `materials.py`, `build_world.py` (LAYERS/NODES, wstawka między
  przebiegami), `pipeline.build` (sygnatura), `WorldSceneBuilder.cs` (tabele LOD), `RegionImporter.cs`, blok sill w
  `WorldPBR.shader` — szczegóły w ADR.
NASTĘPNY KROK (lider): visual-critic na `artifacts/buildings-r15/pairs/` + `r5/extra/960/`; po scaleniu
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` →
  `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`; A16 Low na `r10_house_1`, `r10_house_2`, `r10_shed_2`.
