# STATUS regen-wave-2-s24

Cel: przebudowa 43 kafli korytarza po ADR 0298/0300/0303 (bez zajętych: industrial-c, bojary, mickiewicza, wygoda, knyszyn, knyszyn-w).
Łańcuch: artifacts/regen-wave-2-s24/chain.ps1 (kolejka queue.txt w kolejności importów buildu #2, bramka: kafel musi mieć 'import <kafel> exit=' w win-build/artifacts/full-build-2-s24/chain.status; claims/, chain.status; build_world --context -> export-route -> fidelity, slot heavy). Autocommit co 15 min (commit.ps1).

- 2026-11-19 07:54 start łańcuchów A i B.

NASTĘPNY KROK: `Get-Content artifacts/regen-wave-2-s24/chain.status`; restart: `Start-Process pwsh -ArgumentList '-NoProfile','-File','artifacts/regen-wave-2-s24/chain.ps1','-Chain','A'` (usuń claim kafla przerwanego).
