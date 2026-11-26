# tree-species-s24 — STATUS (ADR 0352)

Gałąź `worktree-agent-a492e5af856a32ed3`, worktree `.claude/worktrees/agent-a492e5af856a32ed3`.
`Data/raw/derived` = PRYWATNA kopia tylko `knyszyn-w`, `dw671-tykocin-03`, `cache` (nie junction; main nietknięty).

## Diagnoza (krytyk fala 11 pkt 10)
- Biblioteka drzew (`make_trees.py`, ADR 0308) MA już osobne atlasy gałązek per gatunek (`leaves_{linden,maple,birch,alder,poplar,pine,spruce}.png`).
- „Jeden atlas liści na wszystkich” = drzewa ogrodowe zestawu działek (`plot_kit._crown_card`): `crown_ovoid/round/birch` rysowane jednym
  soczewkowym stemplem `_leaf_stamps`; ciemny płaski wielokąt `fill` prześwitywał jako ciemne plamy o prostych krawędziach.
- „Sztywny gradient” = `Vegetation.shader` `_CrownShade`: `smoothstep(-0.6, 0.75, normal.y)` — jedna pozioma rampa na każdej koronie;
  brak wariacji koloru per drzewo (każda lipa ten sam odcień).

## Kroki
1. [x] worktree: kopie + prywatny derived 2 kafli; `artifacts/tree-species-s24/vqa.ps1` (import Win64 + High clear/overcast).
2. [~] render „przed” (w tle): `pwsh artifacts/tree-species-s24/vqa.ps1 -Label before`.
3. [x] `plot_kit.py`: stemple blaszek per gatunek (`_blade_stamps`: lipa / klon / brzoza z `leaf_sprays.blade`), ciemne liście w głębi
   zamiast płaskiego wielokąta. Podgląd: scratchpad `kit_cmp.png`.
4. [ ] `Vegetation.shader` `_TreeVar` (tint per drzewo z macierzy instancji, kępy światła/cienia) — łatka gotowa w
   `artifacts/tree-species-s24/wip/shader.patch`, nałożyć PO zakończeniu renderu „przed” (Unity czyta shader przy każdym starcie).
5. [ ] dąb (`leaves_oak`, korona), wierzba; sylwety w dali; testy; ADR 0352; render „po”.

NASTĘPNY KROK: `git apply artifacts/tree-species-s24/wip/shader.patch` (po `before/vqa.status` = DONE), potem
`uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn-w`.
