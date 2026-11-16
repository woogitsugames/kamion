# STATUS — pc-visual-s23 (tiery PC High/Ultra: wygląd > telefon; ADR 0269)
- Krok 1: visual-qa `-Pc` (z main, night-pc-s23) + nowe `-Aniso 0|1|2` (A/B).
- Krok 2: przed: WorldC_High i knyszyn-w (mob High / PC High / PC Ultra). Kabina PC = gruba faktura „tkaniny” + przyciemnienie = SSAO (ablacja rq_ssao=0 czyści, aniso bez wpływu; mob Ultra ma to samo). D84.
- Krok 3: `t.ssao` nie był czytany (rq_ssao=0 = no-op) → `QualityProfileApplier` wybiera renderer 1; test EditMode.
- Krok 4: tabela High: SSAO off, soft High, karty 1.0, capture co klatkę; Ultra: SSAO off, scale 1.5, karty 1.5; assety z generatora. Po: kabina czysta, drzewa pełniejsze.
- Krok 5: player przed (exe e28533ca31, knyszyn-w autopilot 50, 1080p okno, -Fps 1000): High 395 fps p50 2,52 ms, Ultra 258 fps p50 3,82 ms (inny Unity równolegle — orientacyjne).
- Krok 6: exe d6e60131d6 (knyszyn-w): `[PC_TIER] High … ssao=False`, Ultra scale=1,5; kabina w playerze czysta. Orientacyjnie (1080p okno, -Fps 1000, autopilot 50, cicha maszyna, różne buildy): High 437→450 fps (p50 2,22→2,19 ms, p99 3,09→2,91), Ultra 269→274 fps (p50 3,69→3,60, p99 4,52→4,65; 1 klatka 39 ms). EditMode PcGraphicsTier* 15/15.
- NASTĘPNY KROK (lider): przegląd + scalenie; komendy w ADR 0269 „Rewizja pc-visual-s23”; mobilny Ultra ma ten sam artefakt SSAO w kabinie (decyzja dla telefonu).

# STATUS — D42 physics-determinism-s23

- Przyczyna flake'a: `TouchSteeringTests.Residual_PlateFrictionSweep_Diagnostic` zmieniał wspólny `ScenarioRunner.Defs` (fifthWheel.plateFrictionCreepRateDegS), a xUnit równolegle uruchamiał kombinacje laden40. Naprawa: każdy przebieg ma prywatny DefinitionSet, Defs jako Lazy, 2 testy regresji.
- Naczepa: `park_brake_hold_no_interlock` 55,2 mm to przeciek relaksacji (4 mm/s bez końca), nie 7,63 m. Poprawka w TrailerModel: 14,4 mm (ustala się).
- Pętle: provoke 198/200 → 0/200; Robustness 0/200 → 0/200; pełny zestaw 0/30 → 0/30 (289/289).
- NASTĘPNY KROK: lider: `pwsh scripts/test.ps1 -Platform EditMode` (TrailerModel.cs współdzielony z Unity), potem scalenie PR.
