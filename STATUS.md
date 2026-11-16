# STATUS — D42 physics-determinism-s23

- Przyczyna flake'a: `TouchSteeringTests.Residual_PlateFrictionSweep_Diagnostic` zmieniał wspólny `ScenarioRunner.Defs` (fifthWheel.plateFrictionCreepRateDegS), a xUnit równolegle uruchamiał kombinacje laden40. Naprawa: każdy przebieg ma prywatny DefinitionSet, Defs jako Lazy, 2 testy regresji.
- Naczepa: `park_brake_hold_no_interlock` 55,2 mm to przeciek relaksacji (4 mm/s bez końca), nie 7,63 m. Poprawka w TrailerModel: 14,4 mm (ustala się).
- Pętle: provoke 198/200 → 0/200; Robustness 0/200 → 0/200; pełny zestaw 0/30 → 0/30 (289/289).
- NASTĘPNY KROK: lider: `pwsh scripts/test.ps1 -Platform EditMode` (TrailerModel.cs współdzielony z Unity), potem scalenie PR.
