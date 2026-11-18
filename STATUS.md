# STATUS regen-wave-s24

Cel: przebudowa kafli nieaktualnych po ADR 0289/0293/0295 (bez zajętych: industrial-c, bojary, mickiewicza, wygoda, dk8-s8-jeroniki, porosly).
Łańcuch: artifacts/regen-wave-s24/chain.ps1 (kolejka queue.txt, claims/, chain.status z exit per kafel; build_world --context -> export-route -> fidelity, slot heavy).

- 2026-11-18 22:3x start łańcucha A (39 kafli w kolejce).

NASTĘPNY KROK: sprawdź `Get-Content artifacts/regen-wave-s24/chain.status`; kafle bez claim w claims/ = do zrobienia; restart: `Start-Process pwsh -ArgumentList '-NoProfile','-File','artifacts/regen-wave-s24/chain.ps1','-Chain','A'` (usuń claim kafla przerwanego).

- 2026-11-19 00:2x: zrobione knyszyn-s (136 s), bialystok-knyszynska (1431 s), bialystok-kleeberga (3891 s) — build/route/fidelity exit 0, commity. Łańcuchy A i B pracują (kolejka współdzielona). knyszyn-s import+VQA High OK (obejrzane: pola, droga; ząbkowany cień skarpy jak w knyszyn-w — istniejący). Import wymagał SM_CabInterior_LOD0.fbx skopiowanego z main (poza gitem). W toku: import+VQA kleeberga.
Pozostałe: dk65-02..11, s8-01..05, bialystok-dojlidy, dk65-monki-01..07, monki, monki-e, dw671-tykocin-01..09, tykocin, dw671-jasionowka-01.
