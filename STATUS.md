# STATUS — F3 signs-c-0236 (ADR 0236)

- Gotowe: `sign_norms.py` (Dz.U. 2019 poz. 2311 zał. 1), lica E-1/E-2/E-2b/E-15/E-16 wg normy, `row_m` 0,62 → 0,35 m,
  overrides C z R2 (bramownica E-1 R2-079, p37 jako E-1 R2-081, 4 × E-15), usunięcie regułowej E-1 przy portalu p40,
  LOD bramownic/tablic/tarcz (bramownica 1008/480 → 792/208), testy `tests/gis/test_direction_signs_0236.py`, ADR 0236.
- Budżet (szacunek): stretch_04 −224 High; jedyna dodatnia kamera High: fire_station_abeam +448.
- Nieuruchomione w chmurze: build_world C, import, visual-qa (lider).
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`
