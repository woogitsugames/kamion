# furn-0162 STATUS (ADR 0162 meble uliczne + tablice G5/G3)

- 08:25 worktree z origin/main ff9777e2d, przygotowanie (Data/raw copies, junctions, Library).
- Krok 1 (kod): wiata BKM 5/7/9 m czerwona + czarna 7 m (atlas 1 materiał, szkło przezroczyste, dach PC dymiony, stelaż D-15 na dachu),
  latarnie GP 12 -> 11 m + drzwiczki 0.60x0.13 + szara podstawa 0.3 m (atlas galv), słup energetyczny 12 m jedno źródło (GROUND_PROP_H),
  U-12a / U-12 / U-5a prototypy (w danych regionu brak -> 0 sztuk), tablice: panele ze strzałkami, Centrum w białym polu, owale PL/BY,
  p40 wg 2024 (Centrum osobno ←) + kolumny z ortofoto, 3 nowe konstrukcje na al. Tysiąclecia (E-1 P009, VMS P010, portal P005-8).
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q -k "furniture or props or signs or landmarks"` potem build_world.
