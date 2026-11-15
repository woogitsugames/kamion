# STATUS — K63 (M63 hala A i zakład B)

- 2026-11-15 ~12:10 UTC — gotowe: manifest 89 wierszy (16 segment, 12 ściana, 10 brama, 3 ogrodzenie, 2 latarnia, 1 znak, 45 kadr), README z sekcją „Co przejęto z P20…”, sources, audyt 18/18 PASS (seed 20261116), files/ (16 kadrów + 3 ortofoto + 2 mapy nDSM), tools/.
- Następny krok: PR do main „research: M63 zakład i bramy segmentowe (K63)”; po recenzji ewentualnie nowe kadry ściany W części A3 (doki) i hali S.
- Odtworzenie wysokości: `python3 -I tools/py_heights.py <scratch> A 780520 780840 590180 590500 1.5` (wymaga mozaiki NMPT z `tools/asc_crop.py` i NMT z `tools/nmt_fetch.py`); bramy: `python3 -I tools/gates_calib.py`.
