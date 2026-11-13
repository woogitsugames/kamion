# STATUS bldg2-0171 (ADR 0171)
- 16:45 nowy agent przejął; rozpoznanie w ADR §1; baza vqa Low-clear jest (`artifacts/bldg2-0171/base/Low-clear`, exit 0).
- NASTĘPNY KROK: materiały (pawilon, plaster_blue, ramy LOD1, wieżowiec) → `pwsh artifacts/bldg2-0171/tools/full.ps1 -Tag r1`
- 17:10 kod+dane r1: `plaster_blue` 0.12/0.26/0.46, nowy `plaster_slate_blue` (pawilon), frontage `frame` (białe ramy LOD0/LOD1) + glazing `window_m` (okna punktowe), override `ribbon: false, bands: false` wieżowca (rzędy ribbon LOD1 niosły szare spandrele — stąd szary wieżowiec). Testy 0167/0171/g3b: 29 zielone. Baza LOD1 GLB w `artifacts/bldg2-0171/base/world`.
- NASTĘPNY KROK: `pwsh artifacts/bldg2-0171/tools/full.ps1 -Tag r1` (build_world → import → vqa Low → SBS; Unity czeka na PHONE_RUN)
- 17:07 r1 build_world exit 0 (478 s). LOD1 budynków vs baza: prymitywy netto 0 (6_6: +plaster_slate_blue, −plaster_beige__far_ribbon; 6_7 bez zmian), tris 94 604 → 94 938 (+0,35 %). `generated/` zmienione, NIE commitowane (lider przebudowuje po scaleniu).
- W toku: `round.ps1 -Tag r1` (import + vqa Low + SBS) — czeka na slot Unity / PHONE_RUN. Jeśli przerwane: `pwsh artifacts/bldg2-0171/tools/round.ps1 -Tag r1`
