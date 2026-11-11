# buildings-r13 (ADR 0097, zabudowa r5) — STATUS

Gałąź `buildings-r5`, worktree `.claude/worktrees/buildings-r5`, z main `0e73211a`.

## krok 1 — przygotowanie + kod r1 (część)
- Library skopiowana z main (robocopy), build_all (pełny) + build_world baza na kodzie main, PNG oznaczone jako świeże.
- Baza: `run_round.ps1 -Round base` (import + High/Low overcast + High clear) — w toku.
- Kod r1 (niezrenderowany): jeden typ balustrady na budynek (grupy `balcony_1/6/3` w row atlasie, typ z osiedla 250 m,
  12 % wyjątków na LOD0), balkony na obu długich stronach bloków, zacieki pod parapetami (TEXCOORD_1 +64, tryb sill
  shadera ADR 0092) na ścianach bloków / biur / domów, profil kapinosu nad cokołem, paleta domów przydzielana wg sąsiadów
  (ściana + dach), drzwi domu na cokole + podest/stopnie/próg, pranie stonowane (12 %).
- NASTĘPNY KROK: dach wielopołaciowy (`roofs.py` MultiRoof), potem
  `pwsh artifacts/buildings-r13/chain.ps1 -Round r1 -Only facade_atlas,facade_far`
