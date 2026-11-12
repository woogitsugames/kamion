# tyre-scrub (ADR 0145) STATUS
- Krok 1 (pomiar): runner, okręgi z naczepą R9/R12/R20/R30/R50 przy 5–50 km/h, `artifacts/tyre-scrub/slip_scan_before.md`.
  Pisk w ciasnym skręcie pochodzi z tridemu naczepy (oś 1 i 3: kąt znoszenia 8–10° przy R12, 18–22° przy R9), ciągnik ≤ 2°.
  Przed: SquealGain = 0,51 przy 10 km/h R12, 1,00 przy 15 km/h R12 (pełny „gwizd” 930 Hz).
- Krok 2: REGEN-03 (16 WAV) dostarczone; analiza wariantów + warstwy scrub/squeal.
NASTĘPNY KROK: `cd tools/audio; uv run python el_regen03.py` (wybór wariantów)
