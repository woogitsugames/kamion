# DRAFT — D84: wnętrze kabiny na PC, polish po recenzji (ziarno plastiku, zmierzch, detale kadru)

Status: DRAFT (agent cabin-polish-s23, 2026-11-17; numer nadaje lider). Kontekst: `docs/reports/REVIEW-2026-11-17-s23-cabin-pc.md` (wnętrze 4/10), D84.

## Decyzje
1. **Ziarno plastiku czytelne z fotela.** Z punktu oczu 1 px przy 1080p i pionowym FOV 62° pokrywa ok. 0,9 mm deski (odległość 0,8 m; wyliczone, nie zmierzone w buildzie). Stippling 0,25–0,6 mm był podpikselowy i znikał w mipmapach. `plastic_grain.py` dostaje drugą warstwę: ziarno 2–5 mm (waga 0,7; 1,2–3 mm nadal nie czytało się w cieniu) oraz plamy połysku 2,5–10 cm w kanale roughness. Nachylenie normalnych: mediana 10,3°, p95 20,7° (było 6,9° / 14,1°). Wszystkie wzmocnienia `WORKING_VALUE` w `cab_material_scans.json`. Dotyczy też tekstur Medium/Low (tier mobilny).
2. **Zmierzch.** `CabInteriorLighting`: dzienne podbicie widoku z kabiny (`cabViewEv` + pomiar do `cabMeterMaxEv`, razem do 2,5 EV) wygasa między wysokością słońca +3° a −5° do `nightViewEv` = 0,45 EV (`NightFactor`, `CabViewStops`; test `CabTwilightTests`). Presety dzienne (Clear 42°, Overcast 41°, LowSun 9°) mają czynnik 0 — bez zmian; Dusk (−6°) i Night = 1. Pomiar cab-dash dusk High -Pc: piasta kierownicy sRGB 20,21,28 → 12,12,13 przy drodze 10,12,20. Dodany `panelGlow` (0,07, barwa ciepła): poświata podświetlonych legend/zegarów liczona jak fill (× albedo × AO); w pomiarze piasty pozostaje neutralna — efekt słaby. Legendy: `cab_backlight.json` 8 → 12 cd/m², cap 0,06 → 0,09. Bez nowych świateł, przebiegów i wariantów shadera. `WORKING_VALUE`, brak fotometrii.
3. **Geometria (generator `build_interior.py`, tylko LOD0 przez `LOD1_DROP`)**: uszczelki słupka A po stronie szyby i drzwi + zaślepki śrub; żebra mat w tackach deski jako geometria (11 mm, podziałka 22 mm; były tylko mapą normalnych); krótsze przejście policzków daszka zegarów (107 → 50 mm); przeszycie kierownicy ×3,2 zamiast ×6,0 koloru wykończenia; wytarcie wieńca niesymetryczne (lewa dłoń mocniej). LOD0 ≤ 120k, LOD1 ≤ 45k, LOD2 ≤ 22k zachowane.

## Odrzucone / otwarte
- Roleta kierowcy opuszczona 0,30 m: czarna płyta na 10 % kadru; 0,20 m: poza kadrem. Zostaje autorskie 0,10 m.
- Zmiana `DriverHead.RestPitchDownDeg` i FOV kamery kierowcy: bez zdjęcia referencyjnego z fotela (docs/07 §4) to decyzja kierunku — kamera QA `cab-driver-ab10` do A/B z właścicielem. Lusterka leżą ok. 40–60° od osi wzroku, poza poziomym FOV 94°.
- Schodkowe cienie Win64 (P1-1) — poza zakresem (agent full-build-s23).
- Kurz w zagłębieniach: bez zmian (istniejące strefy `tint_add` na desce).
- Bramka docs/06 §5 pkt 3 (side-by-side z referencją) nadal otwarta: brak legalnych zdjęć kabiny w repo.
