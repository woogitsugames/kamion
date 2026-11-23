# STATUS haze-s24 (rendering-perf) — GOTOWE do przeglądu lidera (nie scalone)
Zadanie: krytyk build #5 pkt 2 — biały pas mgły na horyzoncie -> perspektywa powietrzna zależna od odległości. ADR 0332.
## Zrobione
- Sky.shader: chmury fotograficzne (Clear) — perspektywa powietrzna T = exp(-beta*300 m/sin el) z beta terenu zamiast
  rampy 0..10° do płaskiego koloru mgły; krycie gaśnie tylko w ostatnich ~0,7°.
- KamionAtmosphere.hlsl / WorldAtmosphere.cs: _KamionFarFade — teren dociągany do koloru horyzontu w ostatnich 25 % far clip.
- ForestCanopy.shader: KamionFogTau + KamionMixFog zamiast mgły Unity.
- Test EditMode HazeFarFadeTests; EditMode Win64 1396/0 fail (artifacts/haze-s24/editmode-20261124-002629.xml).
- Visual-qa knyszyn-w High/Low x clear/overcast: artifacts/haze-s24/{before,after150,after300,after2}, arkusze sheet-*-before-after.jpg.
## Otwarte (dla lidera)
- URP Lit las HLOD na PC Medium+ nadal z mgłą Unity (bez warstwy przyziemnej i far fade) — propozycja w ADR 0332.
- Pomiar GPU: UNMEASURED; potwierdzić w buildzie (pc-metrics) i obejrzeć przejazd C->Tykocin (t0950-t1020).
## Następny krok
Lider: przegląd + build Windows z regionami i przejazd, potem `pwsh scripts/pc-metrics.ps1 ... -Tier High` vs build #5.
