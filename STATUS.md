# STATUS — F3 signs-c-0236 (ADR 0236)

- krok 1 (WIP): `streetscape/sign_norms.py` (tabele Dz.U. 2019 poz. 2311 zał. 1: 1.8/1.9/1.10/9.5.1–9.5.6, pkt 6.3.x), `signs.py`
  tablice E-1/E-2/E-2b wg normy (d = 210 mm, wiersz 0,35 m zamiast 0,62 m; tablice regułowe d = 132 mm zamiast 66–74 mm),
  `gate3_landmarks.py` lica E-15/E-16 (h = 300 mm). Testy jeszcze nie dostosowane.
- NASTĘPNY KROK: LOD bramownic/tablic, overrides C (R2-079, R2-081, R2-017, R2-077), testy:
  `uv run --project tools/worldgen python -m pytest tests/gis -k "sign" -q`
