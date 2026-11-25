from pathlib import Path
p = Path("docs/adr/0334-mozaika-upraw-lata-miedze.md"); s = p.read_text(encoding="utf-8")
a = """  (`textures/verge_tufts.png` jest per region), więc nic się nie psuje; `test_world_roads::test_export_is_deterministic`
  (kafel C) wymaga regeneracji C po zmianie generatora. Lista maszynowa: `artifacts/fields2-s24/tile_list.json`."""
b = """  (`textures/verge_tufts.png` jest per region), więc nic się nie psuje. Kafel C przebudowany na tej gałęzi
  (`test_world_roads::test_export_is_deterministic` porównuje z zapisanym manifestem): 26 z 64 chunków zmienionych, karty
  kęp skarp 1 130 → 985, najgorsza kamera budżetu `stretch_04` 1 996 321 ≤ 2 000 000. Pozostałe 9 miejskich — do fali
  przebudowy. Lista maszynowa: `artifacts/fields2-s24/tile_list.json`."""
assert s.count(a) == 1
s = s.replace(a, b)
a2 = "Ocena `visual-critic` — do zlecenia przez lidera (subagent nie tworzy subagentów).\n\n### Skutki dla innych kafli\n- Shader: od razu"
b2 = "Tier Low (`vqa/after/knyszyn-w-clear-LOW`, ścieżka bez `_KAMION_WORLD_DETAIL`): mozaika, margines i bruzdy renderują się\npoprawnie. Kompilacja wariantu Android (GLES / Vulkan) **niesprawdzona** (`UNVERIFIED`; shader używa tylko ALU i `ddx/ddy`).\nOcena `visual-critic` — do zlecenia przez lidera (subagent nie tworzy subagentów).\n\n### Skutki dla innych kafli\n- Shader: od razu"
assert s.count(a2) == 1
s = s.replace(a2, b2)
p.write_text(s, encoding="utf-8", newline="\n")
