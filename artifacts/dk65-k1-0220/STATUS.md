# STATUS dk65-k1-0220 (chmura C, C4; ADR 0220)

- [krok 1] `tools/worldgen/roads/route_km.py` (km trasy -> x/z regionu + strona L/P), generator: `edge_line_spacing`
  (network/markings), `kind: edge_line_dashed` (markings). Pikietaż = plan 0203 polyline od węzła 3341716402.
- [krok 2] Paski ortofoto WMS 0,1 m km 8,76–16,57 (`tools/strip.py`, cache w scratchpad), odczyt `lines.py`/`meter.py`/`view.py`;
  dowody `evidence/`. Tabela `docs/reports/map/dk65_k1_elements.json` -> `tools/worldgen/qa/dk65_k1_elements.py` -> bloki
  ADR 0220 w overrides.yaml 01–05: rozstaw 6,2 m, 11 odcinków przerywanych, 2 zatoki (paved_area).
- [krok 3] ADR 0220, testy 18/18, pełny tests/gis 1280 pass (1 fail = fidelity C stale przez hash kodu -> lider).
  NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dk65-0N --context`
  (N=1..5), potem fidelity/import/visual-qa wg opisu PR.
