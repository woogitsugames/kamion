# STATUS haze-s24 (rendering-perf)
Zadanie: krytyk build #5 pkt 2 — biały pas mgły na horyzoncie -> perspektywa powietrzna zależna od odległości.
## Kroki
- [x] worktree utworzony (2026-11-23)
- [x] diagnoza: Sky.shader tryb fotograficznych chmur (Clear) — chmury w dolnych ~10° (smoothstep(0,0.18,d.y)) gaszone do płaskiego
      _SkyFogColor (szary ~132 sRGB), chmury nad nim na poziomie display-cap (~196-250) => bezstrukturalny pas, odwrócony gradient.
      Teren: KamionFogTau (Koschmieder z visibilityKm 20, Clear bez warstwy przyziemnej) — sam w sobie spójny.
- [x] region knyszyn-w skopiowany z win-build do _Generated/World (poza gitem)
- [ ] baseline visual-qa (w tle): artifacts/haze-s24/run-qa.ps1 -Tag before -> artifacts/haze-s24/before/
- [ ] zmiana Sky.shader (perspektywa powietrzna chmur z tego samego beta co teren), po, EditMode, ADR 0332
## Następny krok
Po zakończeniu baseline: obejrzeć artifacts/haze-s24/before/High-clear/*.png (pomniejszone), potem edycja Sky.shader i
`pwsh C:\Users\matma\Documents\Claude\kamion\artifacts\haze-s24\run-qa.ps1 -Tag after`.
