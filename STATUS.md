# STATUS — D42 physics-determinism-s23

- Przyczyna flake'a: `TouchSteeringTests.Residual_PlateFrictionSweep_Diagnostic` zmieniał wspólny `ScenarioRunner.Defs` (fifthWheel.plateFrictionCreepRateDegS), a xUnit równolegle uruchamiał kombinacje laden40. Naprawa: każdy przebieg ma prywatny DefinitionSet, Defs jako Lazy, 2 testy regresji.
- Naczepa: `park_brake_hold_no_interlock` 55,2 mm to przeciek relaksacji (4 mm/s bez końca), nie 7,63 m. Poprawka w TrailerModel: 14,4 mm (ustala się).
- NASTĘPNY KROK: pętle po poprawce `bash /tmp/claude-0/-workspace-kamion/eaf1f027-ac6a-5b30-aebf-5dca5fb09234/scratchpad/loops/loop.sh after_provoke 200 "FullyQualifiedName~RobustnessTests|FullyQualifiedName~TouchSteeringTests.Residual_PlateFrictionSweep"`, potem PR.
