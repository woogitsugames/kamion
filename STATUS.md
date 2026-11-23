# STATUS monument2-s24 (ADR 0331 / dopisek 0325) — twarz króla w Knyszynie + kamery kontrolne pomnika

## Krok 0 — rozpoznanie, render „przed”
- Worktree `.claude/worktrees/monument2-s24`, gałąź `monument2-s24` z main fbbe7d237, `-CopyDerived`.
- Referencje: Commons `Data/raw/refs/knyszyn-king-commons` cs20127375 (zbliżenie, H. Borawski, CC BY-SA 3.0), cs7518515, cs128805425.
- Look-dev przed: `artifacts/monument2-s24/lookdev/before-face.jpg` — głowa-pudło, nos-klin, brwi-belki, korona za wysoka (0,185 m vs twarz 0,135 m),
  kreza za nisko (widoczna szyja), fleurony jak odłamki.
- Pomiary ze zbliżeń (px, oczy→broda = E): pas korony 0,38E nad oczami, szczyt korony 1,27E, koniec brody 0,7E pod brodą, szerokość twarzy ~1,35E.
- NASTĘPNY KROK: nowa głowa (siatka θ×z z przemieszczeniami) w `tools/worldgen/streetscape/knyszyn_king_0325.py`, look-dev:
  `uv run --project tools/worldgen python tools/worldgen/qa/king_preview_0325.py artifacts/monument2-s24/lookdev/r1/king.obj` + Blender `--face`.
