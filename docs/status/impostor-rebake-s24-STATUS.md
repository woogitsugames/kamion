# STATUS impostor-rebake-s24 (rebake atlasu impostorów drzew + „kolce” koron route-s0426)

- Worktree `agent-af9193d9e837e4652`, gałąź `worktree-agent-af9193d9e837e4652`. Nie scalane, nie pushowane.
- Zadanie: dopiski ADR 0308/0352/0023 — (1) atlas impostorów: komórka 256×384 za mała po crown-lod (karty do 90 m),
  rebake w Blenderze z wyższą rozdzielczością, MB przed/po; (2) krytyk day27 pkt 7: cienkie „kolce” w route-s0426.
- [krok 0] Generator: `tools/blender/world/make_trees.py` (`IMP_RES`, `bake_impostor`, `pack`), import:
  `InstanceImporter.ImportTexture` (npotScale ToNearest, max 2048 PC). Środowisko: Library Win64 + `_Generated`
  knyszyn-w (z a492e5af) + dk65-07 (z win-build) kopiowane robocopy.
- NASTĘPNY KROK: zmierzyć rozmiar/format zaimportowanych atlasów (batch editor) + VQA before.
- [krok 1] Pomiar przed (ImpostorAtlasAudit, `artifacts/impostor-rebake-s24/before/atlas-audit.tsv`): źródło 1536×384
  (6×256×384), importer npotScale ToNearest ROZCIĄGA je do 2048×512 DXT5 (+ _n 768×192 -> 1024×256 DXT1) — impostor
  to bilinearny upscale miękkiego bake'u. GPU (wyliczone): 1,40 MB + 0,17 MB na drzewo; knyszyn-w 25 drzew = 39,3 MB.
  VQA before High clear+overcast knyszyn-w (8 kamer) + dk65-07 (59 kamer) OK, 342 s.
- [krok 2] Kod: make_trees.py bake 683×1024/widok -> pas 4096×1024 (pow2, bez resamplingu importera; open_r/min_island
  skalowane do metrów). „Kolce” route-s0426 = karty liści widziane krawędzią (cała tekstura na pasku): VegCardEdge
  w Vegetation.shader (anizotropia UV z pochodnych -> cutoff > 1 przy cos < 0,12..0,3; global _KamionCardEdge,
  WorldInstances.CardEdgeFade, A/B rq_cardedge=0). Zero nowych draw calli.
- NASTĘPNY KROK: VQA `edge1` (trwa) + quick bake maple_0 (czas), potem pełny bake:
  `blender -b --factory-startup -P tools/blender/world/make_trees.py -- --reuse-bakes --rebake pine,birch,alder,maple,linden,shrub,spruce,pineyoung,birchyoung,poplar,oak`
