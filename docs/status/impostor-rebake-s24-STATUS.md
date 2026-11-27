# STATUS impostor-rebake-s24 (rebake atlasu impostorów drzew + „kolce” koron route-s0426)

- Worktree `agent-af9193d9e837e4652`, gałąź `worktree-agent-af9193d9e837e4652`. Nie scalane, nie pushowane.
- Zadanie: dopiski ADR 0308/0352/0023 — (1) atlas impostorów: komórka 256×384 za mała po crown-lod (karty do 90 m),
  rebake w Blenderze z wyższą rozdzielczością, MB przed/po; (2) krytyk day27 pkt 7: cienkie „kolce” w route-s0426.
- [krok 0] Generator: `tools/blender/world/make_trees.py` (`IMP_RES`, `bake_impostor`, `pack`), import:
  `InstanceImporter.ImportTexture` (npotScale ToNearest, max 2048 PC). Środowisko: Library Win64 + `_Generated`
  knyszyn-w (z a492e5af) + dk65-07 (z win-build) kopiowane robocopy.
- NASTĘPNY KROK: zmierzyć rozmiar/format zaimportowanych atlasów (batch editor) + VQA before.
