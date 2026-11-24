# STATUS monument2-s24 (ADR 0331 / dopisek 0325) — twarz króla w Knyszynie + kamery kontrolne pomnika

## Krok 0 — rozpoznanie, render „przed”
- Worktree `.claude/worktrees/monument2-s24`, gałąź `monument2-s24` z main fbbe7d237, `-CopyDerived`.
- Referencje: Commons `Data/raw/refs/knyszyn-king-commons` cs20127375 (zbliżenie, H. Borawski, CC BY-SA 3.0), cs7518515, cs128805425.
- Look-dev przed: `artifacts/monument2-s24/lookdev/before-face.jpg` — głowa-pudło, nos-klin, brwi-belki, korona za wysoka (0,185 m vs twarz 0,135 m),
  kreza za nisko (widoczna szyja), fleurony jak odłamki.
- Pomiary ze zbliżeń (px, oczy→broda = E): pas korony 0,38E nad oczami, szczyt korony 1,27E, koniec brody 0,7E pod brodą, szerokość twarzy ~1,35E.
- NASTĘPNY KROK: nowa głowa (siatka θ×z z przemieszczeniami) w `tools/worldgen/streetscape/knyszyn_king_0325.py`, look-dev:
  `uv run --project tools/worldgen python tools/worldgen/qa/king_preview_0325.py artifacts/monument2-s24/lookdev/r1/king.obj` + Blender `--face`.

## Krok 1 — nowa głowa (look-dev Blender r1–r6, commit 64a50aa28)
- Głowa = jedna gładka siatka θ×z (32 kol. × 39 rzędów) z przemieszczeniami: łuk brwiowy, oczodoły + gałki + powieki, nos z grzbietem
  i skrzydełkami, kości policzkowe, usta, wąsy, broda w szpic nachodząca na krezę, włosy-loki za uszami; uszy jako muszle; lekki przechył 1,6°.
- Głowa+kreza+korona rysowane przy E=0,165 m i skalowane ×1,12 wokół szyi (zdjęcie cs7518515: korona–broda 0,18 wys. figury). H_TOP 3,093.
- Kreza podniesiona do żuchwy, płaty zaokrąglone (48 wierzch.), wpuszczona pod brodę i w szyję płaszcza (bez szpar). Korona: niższa, 4 liście
  z kamieniem i kulą + 4 perły na trzonkach, kamienie na opasce; UV głowy w skali twarzy.
- Trójkąty: LOD0 5 478 (było 2 214 figury), LOD1 372 (było 288). Arkusze: `artifacts/monument2-s24/lookdev/r6-face.jpg`, `r5-sheet.jpg`.
- NASTĘPNY KROK: kamera kierowcy z ulicy przy Rynku w `Data/Regions/knyszyn/control_cameras_place.authored.json`, potem build_world knyszyn (tło).
