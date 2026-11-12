# tyre-scrub (ADR 0145) STATUS — GOTOWE
- Pomiar (runner + Unity): pisk w ciasnym skręcie = tridem naczepy ciągnięty bokiem (R12 10 km/h: 9,4–9,7°, poślizg 1,64–1,69); stary SquealGain 0,51 (10 km/h) / 1,00 (15 km/h).
- Nowe: ScrubGain (α naczepy 1→5°, v 0,3→1,2 m/s, wygasa 6→11 m/s), SquealGain v2 (1,3→2,0, v 5→9 m/s), squealVolume 0,60, scrubVolume 0,25.
- REGEN-03 (532 kredyty): scrub (2), scrub_cab (3), squeal (2), squeal_cab (3); oba zestawy. Synteza pisk v2 + szuranie = zapas.
- Testy: PlayMode 27/27 (TyreScrubTests 4/4, 0 B GC), EditMode Audio 1/1. A/B: artifacts/tyre-scrub/ab/.
NASTĘPNY KROK (lider): `git merge tyre-scrub` + odsłuch właściciela `artifacts/tyre-scrub/ab/tyre_ab_ext.ogg`, `tyre_ab_cab.ogg`
