# STATUS hv-wires-s24 (przewody WN, CRITIC s24 fala 11 pkt 1)

- [krok 1] Diagnoza: pylony na dk65-07 owner02-seam-n-cab to pylony FAR FIELD (kamera n=1080 > 1024, poza kaflem; dk65-08 nie wczytany).
  far_field.py dokleja kratownice 27 m co 210 m wzdluz WSZYSTKICH linii z pierscienia (BDOT OT_SULN_L dowolnego napiecia + OSM line/minor_line)
  i nigdy nie rysuje przewodow; BDOT "slup energetyczny" (glownie slupy SN) tez jako kratownica 26 m. dk65-07 far_field_qa: 307 pylonow, 0 przewodow.
  Kolor COL_PYLON_STEEL (0.27, 0.285, 0.30) liniowo = ~2.3x jasniej niz pylon_steel w kaflu -> w sloncu bialy.
- NASTEPNY KROK: audyt wszystkich kafli `uv run --project tools/worldgen python tools/worldgen/qa/hv_wires_audit.py`
- [krok 2] In-tile: power_supports bierze zmapowane wieze na linii (rzut) -> 31/298 -> 0/308 bez przesla; BDOT slup na linii WN = pylon.
- [krok 3] Far field: wieze tylko na liniach WN (BDOT wysokiego / OSM >=60kV), przesla z zawisem jako wstegi submesh 0, szew = podpora kafla,
  ocynk z rozrzutem, maszty bez trawers. dk65-07: 307 -> 31 wiez + 5 masztow, 30 przesel, 0 bez przewodow. ADR 0351, testy tests/gis/test_hv_wires_0351.py.
- NASTEPNY KROK: import Win64 dk65-07 + knyszyn-w (slot unity) i VQA -> artifacts/hv-wires-s24/
