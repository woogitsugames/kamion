# STATUS — jackknife-0228 (chmura E / E1, B-077, ADR 0228)

Gałąź `jackknife-0228` od `origin/main` fc450006. ADR: `docs/adr/0228-przegub-kontakt-kabina-naczepa-ladowanie.md`.

## Zrobione
- Kontakt ciągnik–naczepa w rdzeniu (`CouplingContact` + wiersze kontaktu w `FifthWheel.Solve`, `CombinationModel`): pierwszy
  kontakt poziomego zestawu 117,12° (ściana boczna naczepy na narożniku kabiny); stop kątowy 90° tylko awaryjnie.
- Jedno źródło geometrii: `bodyBoxes` w `tractor_4x2_generic.vehicle.json` i `curtainsider_tridem_13_6.trailer.json`
  (flagi ground/coupling); runner czyta kolidery z danych; testy: `test_dims_sync.py` (z dims.json), xUnit (lustro ADR 0158),
  EditMode `BodyBoxGeometryTests` (buildery graybox, NIEuruchomiony — brak Unity).
- Lądowanie: histereza odbojnika przy odciążaniu (h 4 s/m): zrzut 0,5 m 40 t 0,68 → 0,39, bez ponownego lotu.
- Scenariusze: `jackknife_fold_90_reverse_comb`/`_empty`, `jackknife_fold_120_reverse_comb`, `jackknife_fast_fold_impact_comb`,
  `jackknife_reverse_countersteer_comb`, `drop_05m_comb` (generator `tests/physics/generate_jackknife_scenarios.py`);
  `reverse_dock_s_maneuver_comb` (generator stage2) ma nowe kryteria; golden `brake_80_0_dry_abs_comb@laden40` przepisany.

## Zmierzone (runner .NET 8, Linux, chmura)
- `dotnet test tools/physics-runner`: **295/295** (`dotnet-test.log`), main 277/277.
- Runner pełny: **145 scenariuszy / 879 checków ALL PASSED** (`full-runner.log`, `full/summary.md`).
- Przed/po (ten kod z `--no-coupling-contact --elastic-landing`): `before/summary.md` (8 FAIL na nowych kryteriach),
  `after/summary.md` (20/20 PASS). CSV 20 Hz gzip: `csv/{before,after}/`. Wykresy obejrzane: `png/`.
- `--robustness`: BIT-IDENTICAL, NaN 0 (`robustness/robustness.md`). Bench A/B: p50 13,6 vs 13,2 µs/krok (`bench-ab.log`).
- pytest `tests/physics/test_dims_sync.py` 12/12; `test_scenario_strictness.py`: 1 FAIL `kerb_step_27cm_42kmh_comb.json`
  — ten sam FAIL jest na origin/main (generator ≠ commit, nie z tej gałęzi).

## NIEuruchomione
Unity EditMode/PlayMode, build Android, telefon, feel test (brak Unity i telefonów w chmurze).

## Następny krok (lider)
```
pwsh scripts/test.ps1 -Platform EditMode      # BodyBoxGeometryTests + reszta
pwsh scripts/test.ps1 -Platform PlayMode      # CombinationLabTests, KerbStrikeParityTests
pwsh scripts/build-android.ps1 -Install -Run  # potem feel test cofania z kontrą (B-075)
```
