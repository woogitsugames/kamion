# controls-0243 (G1, chmura G, s21) — ADR 0243

- 2026-11-15: ustawienia schemat 5 (okienka lusterek, preset 270/900), Low z okienkami = harmonogram due II co 3 / wypukłe co 16 (0,67–0,92 render/klatkę zamiast 1,00), `MirrorInsetLayout` + `MirrorInsetBudget` jako czyste klasy, EditMode `Controls0243Tests` (12), .NET runner 13/13 zielony.
- NASTĘPNY KROK (lider, Unity + A16): `pwsh scripts/test.ps1 -Platform EditMode`, potem `pwsh scripts/test.ps1 -Platform PlayMode`, potem `pwsh scripts/build-android.ps1 -Install -Run -Serial RFGL34SJYDZ -Tier Low`, potem A/B z ADR 0243 §5 (`rq_ab=mirrorrate`).
