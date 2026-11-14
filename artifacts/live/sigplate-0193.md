# sigplate-0193
- c5950cb47+ADR: głowica S-1 przebudowana, kamera P11-094 przesunięta o 10 m, testy 43/43, before-C wyrenderowane (artifacts/sigplate-0193/before-C-sheet.jpg).
- b4ed01d93 + 5ba20690b + a77a1f96f + ff4909ba7: runda 2 (`after-C2` / `after-D2`) — naprawione sortowanie głębi w `sheet.py`, pełny pytest i EditMode.
- Runda 3 (M66 §5, po scaleniu `origin/main` `b0d9769fc`):
  1. Tarcza kontrastowa TYLKO na wysięgnikach (`signal_head_{green,yellow,red,off}`); dodano warianty boczne bez tarczy `signal_head_side_{green,yellow,red,off}` (`plate=False`) użyte na słupach bocznych w `furniture.py:868/874` i `gate3_landmarks.py:492`; `signal_ped_*` z `plate=False`.
  2. Wymiary tarczy wg Dz.U. rys. 10.28a: `0.85 × 1.40 m` (`ph=0.425, pz=0.70`), czarna z narożami `R70`, biała obwódka `40 mm` (`signal_border` = kolor `marking_white` `[0.55, 0.55, 0.54]`) odsunięta o `20 mm` czarnego marginesu od krawędzi tarczy.
  3. Tarcza kontrastowa umieszczona na tylnej płaszczyźnie komory (ZA obudową `280 mm`, `y = -0.085..-0.075` vs obudowa `-0.080..+0.200`), tył tarczy i obudowy czarny.
  4. Daszki wydłużone do `L = 0.22 m` (≥ 0.20 m), głowice wysięgnikowe pochylone o `7°` w dół ku nadjeżdżającym.
- `after-C3` / `after-D3` (Low + High) + `sbs3/*.jpg` wyrenderowane i zweryfikowane wizualnie (`after-heads.jpg`, `after-C-sheet-{Low,High}.jpg`, `gate3-signal-{Low,High}.jpg`, `sbs-P11-{063,094}-{Low,High}.jpg`).
- Testy po przebudowie świata: `pytest tests/gis/test_signal_head_0193.py tests/gis/test_p1_0161.py tests/gis/test_p1b_0172.py tests/gis/test_photo_cameras_0174.py tests/gis/test_dojlidy_0179.py tests/gis/test_road_fidelity.py` = **62 passed, 1 xfailed** (`test_signal_head_0193.py` = 26 passed).
- ADR `docs/adr/0193-sygnalizator-tarcza-i-kamera-d6.md` zaktualizowany, scommitowany i wypchnięty na `origin/sigplate-0193`.
- NASTĘPNY KROK: KONIEC — gotowe do finałowej recenzji i scalenia przez lidera.
