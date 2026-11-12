# tyre-scrub (ADR 0145) STATUS
- Krok 1 (pomiar): pisk w ciasnym skręcie = tridem naczepy (osie 1/3: 8–10° przy R12, 18–22° przy R9), ciągnik ≤ 2°.
  Przed: SquealGain 0,51 przy 10 km/h R12, 1,00 przy 15 km/h R12. `slip_scan_before.md`.
- Krok 2: LayerMath ScrubGain (α naczepy 1→5°, v 0,3–1,2 m/s on, 6–11 m/s off) + SquealGain v2 (1,3→2,0, v 5→9 m/s).
- Krok 3: REGEN-03 wybór auto (el_regen03.py): scrub (2), scrub_cab (3), squeal (2), squeal_cab (3); el_fx 47 klipów 0 FAIL.
- Krok 4: A/B `artifacts/tyre-scrub/ab/tyre_ab_{ext,cab}.ogg` + spektrogram (obejrzany).
- W toku: Unity import + testy (czeka na PHONE_RUN, skrypt w tle, log artifacts/tyre-scrub/unity_run.log).
NASTĘPNY KROK: `pwsh <scratchpad>/unity_run.ps1` (slot → ImportBatch → test.ps1 EditMode Audio, PlayMode Audio|TyreScrub|DrivingLabScene)
