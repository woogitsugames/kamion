# STATUS — pc-visual-s23 (tiery PC High/Ultra: wygląd > telefon; ADR 0269)
- Krok 1: visual-qa `-Pc` (w main już z night-pc-s23; scalone, zostawiony wariant main) + `-Aniso 0|1|2` (A/B).
- Krok 2: zrzuty „przed” WorldC_High: mob High / PC High / PC Ultra (`artifacts/pc-visual-s23/before`). Znalezisko: wnętrze kabiny na PC i na mob Ultra ma grubą fakturę „tkaniny” (D84); mob High gładkie. Ablacje SSAO/aniso w `ablate/`.
- Krok 3: `t.ssao` nie był nigdzie czytany (rq_ssao=0 = no-op) → `QualityProfileApplier` przełącza renderer 1 gdy ssao off.
- NASTĘPNY KROK: obejrzeć `artifacts/pc-visual-s23/ablate/{pcHigh-aniso1,pcHigh-nossao2,pcHigh-both}/cab-driver.png` vs before.

# STATUS — D42 physics-determinism-s23

- Przyczyna flake'a: `TouchSteeringTests.Residual_PlateFrictionSweep_Diagnostic` zmieniał wspólny `ScenarioRunner.Defs` (fifthWheel.plateFrictionCreepRateDegS), a xUnit równolegle uruchamiał kombinacje laden40. Naprawa: każdy przebieg ma prywatny DefinitionSet, Defs jako Lazy, 2 testy regresji.
- Naczepa: `park_brake_hold_no_interlock` 55,2 mm to przeciek relaksacji (4 mm/s bez końca), nie 7,63 m. Poprawka w TrailerModel: 14,4 mm (ustala się).
- Pętle: provoke 198/200 → 0/200; Robustness 0/200 → 0/200; pełny zestaw 0/30 → 0/30 (289/289).
- NASTĘPNY KROK: lider: `pwsh scripts/test.ps1 -Platform EditMode` (TrailerModel.cs współdzielony z Unity), potem scalenie PR.
