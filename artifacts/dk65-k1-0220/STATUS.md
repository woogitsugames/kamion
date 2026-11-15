# STATUS dk65-k1-0220 (chmura C, C4; ADR 0220)

- [krok 1] `tools/worldgen/roads/route_km.py` (km trasy -> x/z regionu + strona L/P), generator: `edge_line_spacing`
  (network/markings), `kind: edge_line_dashed` (markings), test `tests/gis/test_dk65_k1_0220.py` 16/16 (z 0205).
  Pikietaż: plan 0203 `variants.A_old_road.polyline`, km 0 = węzeł 3341716402 (Andersa), rośnie do Knyszyna;
  zgodność z K1 `km_points.json` < 0,05 m. Paski ortofoto WMS 0,1 m w toku (`artifacts/dk65-k1-0220/tools/strip.py`).
  NASTĘPNY KROK: `uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/strip.py 8.76 16.57 <out>` → odczyt
  zasięgów linii przerywanych i zatok → overrides dk65-01…05.
