# STATUS haze-s24 (rendering-perf)
Zadanie: krytyk build #5 pkt 2 — biały pas mgły na horyzoncie -> perspektywa powietrzna zależna od odległości.
## Kroki
- [x] worktree utworzony (2026-11-23)
- [x] diagnoza: Sky.shader tryb fotograficznych chmur (Clear) — chmury w dolnych ~10° (smoothstep(0,0.18,d.y)) gaszone do płaskiego
      _SkyFogColor (szary ~132 sRGB), chmury nad nim na poziomie display-cap (~196-250) => bezstrukturalny pas, odwrócony gradient.
      Teren: KamionFogTau (Koschmieder z visibilityKm 20, Clear bez warstwy przyziemnej) — sam w sobie spójny.
- [x] region knyszyn-w skopiowany z win-build do _Generated/World (poza gitem)
- [x] baseline visual-qa: artifacts/haze-s24/before/ (High/Low x clear/overcast)
- [x] Sky.shader: perspektywa powietrzna chmur (beta terenu, welon 150 m); ForestCanopy: KamionFogTau
- [ ] visual-qa po, EditMode Win64, ADR 0332, raport
## Następny krok
Puścić `pwsh C:SERSMATMADOCUMENTSCLAUDEKAMIONRTIFACTSHAZE-S24UN-QA.PS1 -TAG AFTER` I PORóWNAć SHEET.PY/CROP.PY.
`pwsh C:\Users\matma\Documents\Claude\kamion\artifacts\haze-s24\run-qa.ps1 -Tag after`.
