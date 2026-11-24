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

## Krok 2 — kamery, testy, ADR (commity b1b1e832a .. )
- Kamery `king_street_driver_0331` / `king_street_tele_0331` (DW671 Grodzieńska, pas południowy, 36 m od pomnika, oko 2,5 m) w
  `Data/Regions/knyszyn/control_cameras_place.authored.json`; do renderu „przed” wstrzyknięte tymczasowo do generated/control_cameras.json (nie commitowane).
- `tests/gis/test_knyszyn_park_props_0227.py`: 9 passed (nowe asercje nosa/brody, LOD0 ≤ 6000, LOD1 ≤ 480).
- ADR szkic `docs/adr/0331-twarz-krola-knyszyn-kamery-pomnika.md`.
- W toku (tło): `pwsh artifacts/monument2-s24/before.ps1` → `artifacts/monument2-s24/vqa-before/` (import knyszyn-w + knyszyn, VQA High).
- NASTĘPNY KROK: po „przed”: slot heavy + `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn`, potem
  `pwsh artifacts/monument2-s24/run-unity.ps1 -Region knyszyn -Out artifacts/monument2-s24/vqa-after -Cameras <jak w before.ps1>` i `make-sbs.sh`.

## Krok 3 — Unity przed | po (runda 1), runda 2 w toku
- Przed: `artifacts/monument2-s24/vqa-before/` (import knyszyn-w + knyszyn z kopii derived main; wymagało skopiowania `art-source/truck/interior/export` z main).
- build_world knyszyn exit 0 (1047 s). Po r1: `vqa-after/`, arkusze `sbs/after-ref-vs-game.jpg`, `sbs/head-crop-ref-before-after.jpg`, `sbs/before-ref-vs-game.jpg`.
- r1 w Unity: twarz czyta się (nos, broda w szpic na krezie, uszy, korona z liśćmi); wada: usta+wąsy jak grymas, żuchwa szeroka → r2 (commit „runda 2”).
- Kamera `king_head_0325` trisExact 429 862 → 431 797. pytest celowany 32 passed (`logs/pytest-targeted.log`).
- Uwaga: commit „runda 2” zawiera też przegenerowane `generated/{roads_qa,streetscape_qa,world_manifest}.json` (build_world na kodzie main + ADR 0331).
- W toku: `after.ps1 -Out artifacts/monument2-s24/vqa-after2`. NASTĘPNY KROK: `artifacts/monument2-s24/make-sbs.sh vqa-after2 after2`, ADR wyniki, kopia dowodów do main/artifacts.
