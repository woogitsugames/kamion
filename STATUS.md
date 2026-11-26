# STATUS — road-patches-s24 (krytyk fala 11 pkt 2 i 4: łaty prostokątne, szew osi dk65-goniadzka)

Gałąź: `worktree-agent-a4b13d4540b9ae795` (nie scalać — lider). Dowody: `artifacts/road-patches-s24/`.
Prywatna kopia derived: `Data/raw/derived/{knyszyn-w,dw671-tykocin-03}` (reszta = junctiony do main; `artifacts/road-patches-s24/setup.ps1`).

## Kroki
1. Diagnoza (26.11 09:55): czarny falisty pas w osi dk65-goniadzka = `decals.seal_cracks` „centre construction joint”
   (pasmo `decal_seal` 12–20 cm, solid strength 2.6, meander ±5 cm na falach 5–9 m jak pęknięcie termiczne) — obok
   prostych kresek P-1 wygląda jak przeskakująca linia. Jasny prostokąt dw671 cab-view-b: łata nie dziedziczy tonu
   jezdni (`_ROADWEAR` ton 0,44–1,56 x na 90/23 m), więc na ciemnym odcinku stara łata jest jaśniejsza od drogi;
   pęknięcie `decal_seal` biegnie przez łatę (kolejka +20 nad łatą +12).
2. Generator (`roads/decals.py`): szew osi prosty (±1 cm), 7–11 cm, strength 1,9 (przetarty); pęknięcia dzielone na
   łatach (`_runs_outside`, margines 15 cm). WIP.

## Następny krok
`pwsh -NoProfile -File artifacts/road-patches-s24/vqa.ps1 -Phase before` (w toku) → shader → przebudowa 2 kafli →
`pwsh -NoProfile -File artifacts/road-patches-s24/vqa.ps1 -Phase after`
3. (11:00) Shader r1 (ton jezdni `KamionRoadTone`, obrys 5–15 cm, skos/schodek frezu, L-wykop, zalewka 3,2 cm okrakiem);
   oba kafle przebudowane (szew osi r2 6–9 cm, strength 1,7; pęknięcia: knyszyn-w 5716→4990, dw671-03 8190→7326 tri).
   Testy `tests/gis -k "patch or 0335 or shader or seal or 0323 or budget"` 83 passed. ADR 0335 dopisek P3.
4. (12:00) dw671 cab-view-b: jasna łata nie reaguje na ton/wiek/gładkość — sondy (`probe*`) w toku: rozdział albedo vs odbicie.
   Sonda w shaderze oznaczona `DEBUG PROBE` — USUNĄĆ przed commitem (kopia czysta: scratchpad WorldPBR.keep).
