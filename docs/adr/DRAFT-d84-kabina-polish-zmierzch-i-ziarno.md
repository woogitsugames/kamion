# DRAFT — D84: wnętrze kabiny na PC, polish po recenzji (ziarno plastiku, zmierzch, detale kadru)

Status: DRAFT (agent cabin-polish-s23, 2026-11-17; numer nadaje lider). Kontekst: `docs/reports/REVIEW-2026-11-17-s23-cabin-pc.md` (wnętrze 4/10), D84.

## Decyzje
1. **Ziarno plastiku czytelne z fotela.** Z punktu oczu 1 px przy 1080p i pionowym FOV 62° pokrywa ok. 0,9 mm deski (odległość 0,8 m; wyliczone, nie zmierzone w buildzie). Stippling 0,25–0,6 mm był podpikselowy i znikał w mipmapach. `plastic_grain.py` dostaje drugą warstwę: ziarno 1,2–3 mm (waga 0,7) oraz plamy połysku 2,5–10 cm w kanale roughness. Nachylenie normalnych: mediana 8,9°, p95 18,2° (było 6,9° / 14,1°). Wszystkie wzmocnienia `WORKING_VALUE` w `cab_material_scans.json`.
2. **Zmierzch.** `CabInteriorLighting`: dzienne podbicie widoku z kabiny (`cabViewEv` + pomiar do `cabMeterMaxEv`, razem do 2,5 EV) wygasa między wysokością słońca +3° a −5° do `nightViewEv` = 0,25 EV — kierownica nie jest jaśniejsza od świata. Dodany `panelGlow` (0,035, barwa ciepła): poświata podświetlonych legend/zegarów na okładzinach, liczona jak fill (× albedo × AO), niezależna od ekspozycji. Bez nowych świateł, przebiegów i wariantów shadera. `WORKING_VALUE`, brak fotometrii.
3. **Geometria (generator `build_interior.py`)**: uszczelki słupka A po stronie szyby i drzwi + zaślepki śrub; żebra mat w tackach deski jako geometria (były tylko mapą normalnych); krótsze przejście policzków daszka zegarów (107 → 50 mm); roleta kierowcy opuszczona 0,30 m (ok. 23° nad linią wzroku, nad polem widzenia w przód); przeszycie kierownicy ×3,2 zamiast ×6,0 koloru wykończenia; wytarcie wieńca niesymetryczne (lewa dłoń mocniej).

## Odrzucone / otwarte
- Zmiana `DriverHead.RestPitchDownDeg` i FOV kamery kierowcy: bez zdjęcia referencyjnego z fotela (docs/07 §4) to decyzja kierunku — do A/B z właścicielem.
- Schodkowe cienie Win64 (P1-1) — poza zakresem (agent full-build-s23).
- Bramka docs/06 §5 pkt 3 (side-by-side z referencją) nadal otwarta: brak legalnych zdjęć kabiny w repo.
