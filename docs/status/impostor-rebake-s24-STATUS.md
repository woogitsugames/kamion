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
- [krok 3] VQA `edge1` (knyszyn-w clear, 4 kamery): kolce w koronie klonu route-s0426 znikają (`view/z1.png` przed|po,
  200 %); zmienione piksele (fuzz 6 %) 0,02-0,05 % kadru, gęstość korony bez widocznej zmiany.
- NASTĘPNY KROK: czas quick bake maple_0 (trwa), potem pełny rebake (komenda wyżej).
- [krok 4] Quick bake maple_0: 146 s/drzewo (render GPU ~1 s/przebieg, reszta = pakowanie numpy). Opening r=3 (skalowany)
  ciął brzeg korony w kwadratowe bloki -> r=1 bez skalowania (min_island skalowane powierzchnią). Wynik: 4096×1024 + _n
  2048×512, brzegi liściaste, wyraźnie ostrzejsze (`view/crop3.png`). Pełny rebake 28 drzew wystartował 16:3x (~70 min).
- NASTĘPNY KROK: po `logs/blender-full.status`: skopiować impostor_tree_*.png do `game/Assets/_Generated/World/{knyszyn-w,dk65-07}/Textures`,
  ImpostorTrimBake.RunBatch -region <id>, audit + VQA `after` (`vqa.ps1 -Label after -Audit`).
- [krok 5] ImpostorTrim: początek widoku k = round(k·4096/6) (było k·682 -> 3 px błędu widoku 5), dylatacja jako udział
  widoku (DilateFor, 6 px @256 -> 16 px @682) + test. _components_min z pointer jumping (ten sam wynik, test ekwiwalencji
  na losowych maskach, pine_0 7,5 -> 3,3 min). Pełny rebake restart 16:38 (ETA ~17:55). EditMode Win64 w toku (editmode1).
- NASTĘPNY KROK: po `logs/blender-full.status`: `pwsh artifacts/impostor-rebake-s24/post.ps1`, potem
  `pwsh artifacts/impostor-rebake-s24/vqa.ps1 -Label after -Audit`, `bash artifacts/impostor-rebake-s24/sbs.sh before after sbs`.
- [krok 6] EditMode Win64 (editmode1, kod gałęzi, atlasy w trakcie rebake'u): 1632 / 1513 pass / 1 fail / 118 skip.
  Jedyny fail: StartClearanceTests("dk65-07") — scena dk65-07 skopiowana z worktree win-build jest starsza niż dane
  trasy w tej gałęzi (środowisko, nie zmiana). ImpostorTrimTests (w tym nowy) zielone.
- [krok 7] Pełny rebake OK (4825 s, 28 drzew): 28 × impostor 4096×1024 + _n 2048×512, trees.glb bez zmian (deterministyczny),
  trees_lod2.glb 62 MB (osadzone PNG; LFS), trees_meta bez zmian treści. Commit be0fca977.
- NASTĘPNY KROK: (trwa) post.ps1 (kopie do _Generated + ImpostorTrimBake) + `vqa.ps1 -Label after -Audit`, potem sbs.sh.
