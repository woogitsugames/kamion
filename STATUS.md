# STATUS hv-wires-s24 (przewody WN, CRITIC s24 fala 11 pkt 1)

- [krok 1] Diagnoza: pylony na dk65-07 owner02-seam-n-cab to pylony FAR FIELD (kamera n=1080 > 1024, poza kaflem; dk65-08 nie wczytany).
  far_field.py dokleja kratownice 27 m co 210 m wzdluz WSZYSTKICH linii z pierscienia (BDOT OT_SULN_L dowolnego napiecia + OSM line/minor_line)
  i nigdy nie rysuje przewodow; BDOT "slup energetyczny" (glownie slupy SN) tez jako kratownica 26 m. dk65-07 far_field_qa: 307 pylonow, 0 przewodow.
  Kolor COL_PYLON_STEEL (0.27, 0.285, 0.30) liniowo = ~2.3x jasniej niz pylon_steel w kaflu -> w sloncu bialy.
- NASTEPNY KROK: audyt wszystkich kafli `uv run --project tools/worldgen python tools/worldgen/qa/hv_wires_audit.py`
