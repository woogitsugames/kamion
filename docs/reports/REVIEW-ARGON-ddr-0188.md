# REVIEW 2026-11-15 — ADR 0188 DDR: ciepłoszary i czerwonobrązowy asfalt, przejazdy P-11 oraz układ w przekroju (gałąź `ddr-0188` @ `503848f8b`)

Recenzent: `Reviewer` (niezależny agent, tylko odczyt; bez uruchamiania Unity i `build_world`).
Kryteria odniesienia: wymagania M65 (`docs/reports/REVIEW-2026-11-14-s20-cloud-m65.md` §5), ADR 0188 (`.claude/worktrees/ddr-0188/docs/adr/0188-drogi-dla-rowerow-czerwony-asfalt.md`), standard jakości (`docs/06_GRAFIKA_ANTI_AI_SLOP.md`) oraz budżety (`stats.txt`, `import-*-r4.log`).
Materiał obejrzany (`artifacts/ddr-0188/sbs-r4/`):
- Dojlidy: `sbs-D-High-photo-P11-001.jpg`, `sbs-D-Low-photo-P11-001.jpg`, `sbs-D-High-photo-P11-056.jpg`, `sbs-D-Low-photo-P11-056.jpg`, `sbs-D-High-photo-P11-063.jpg`, `sbs-D-Low-photo-P11-063.jpg`, `D-High-route-s0152.jpg`, `D-High-route-s1370.jpg`.
- Region C: `sbs-C-High-g3_c_1173244557941023.jpg`, `sbs-C-Low-g3_c_1173244557941023.jpg`, `sbs-C-High-g3_c_295679109352815.jpg`, `C-Low-putry-above.jpg`, `C-High-putry-above.jpg`.
- Logi i statystyki: `artifacts/ddr-0188/r4/{C,D}-{Low,High}/stats.txt`, `c-before-Low-overcast/stats.txt`, `import-{c,doj}-r4.log`, `import-{c,doj}.log`, `bw-{c,doj}-r4.log`, `qa-{c,doj}-r4-low.log`.

Współrzędne pikseli: SBS `1920×540` (lewa połowa `x: 0–959` = referencja, prawa połowa `x: 960–1919` = render), widoki pojedyncze (`C-*-putry-above.jpg`, `D-High-route-*.jpg`) w skali `960×540` podglądu JPG.
**Brak zrzutu z telefonu** — `docs/06_GRAFIKA_ANTI_AI_SLOP.md` §5 pkt 2 niespełniony (Render z edytora jest, brak screencap z urządzenia; akceptowalne do scalenia gałęzi generatora, wymagane przed bramką na `main`).

## Werdykt: SCAL warunkowo

Wszystkie cztery wymagania merytoryczne z M65 §5 zostały w rundzie 4 wdrożone poprawnie i potwierdzone wizualnie na Low oraz High:
1. **Dojlidy (`P11-001`, `P11-063`, `route-s0152`):** DDR ma stonowany, **ciepłoszary asfalt (`cycle_asphalt`)**, nie jest jaskrawoczerwona. Na `P11-001` układ w przekroju to poprawnie `away` (jezdnia → pas zieleni → chodnik z kostki → DDR → trawnik przy ogrodzeniu), a zjazd bramowy `kuronia3-gate-driveway` (`highway=service`) wyraźnie przerywa DDR jasną kostką bez czerwonego pola, z piktogramami P-23 po obu stronach.
2. **Przejazdy P-11:** Na `P11-056` przejazd przez wlot Dywizjonu 303 ma czerwone pole (`cycle_crossing_red`) z białymi kwadratami P-11 obok zebry. Na `P11-063` oraz na głównych jezdniach pod estakadą Ronda Putry (`C-*-putry-above.jpg`) przejazdy P-11 są wyłącznie białe, bez czerwonego podkładu.
3. **Region C wokół Ronda Putry (`g3_c_1173244557941023`, `g3_c_295679109352815`, `putry-above`):** DDR ma wyraźnie **czerwonobrązowy (bordowy, matowy) asfalt (`cycle_asphalt_red`)**, spójnie odcinający się od jasnoszarej kostki chodnika i szarego asfaltu jezdni, bez przesycenia. Przejazdy P-11, linie i piktogramy P-23 renderują się czysto na Low i High, bez z-fightingu i migotania.
4. **Budżet A/B i `WORLD_MEMORY`:** Brak regresji względem stanu sprzed zmian (`c-before-Low-overcast` / `import-*.log`). Przyrost pamięci wynosi +0,2–0,7 MB, a przyrost `drawsEst` na porównywanych kadrach w C mieści się w +2 draws.

Nie ma żadnych blokerów **P0** ani **P1** w zakresie ADR 0188.

### Warunki scalenia (lider)
1. Po scaleniu do `main` uruchomić `tools/worldgen/fidelity/run.py`, aby odświeżyć `fidelity_qa.json` (eliminuje błąd `test_road_fidelity.py::test_report_not_stale` z pełnego pytestu).
2. Przed bramką wykonać zrzut z telefonu (Samsung A16) dla kadrów `photo_P11-001`, `photo_P11-056` i `putry_above` zgodnie z `docs/06_GRAFIKA_ANTI_AI_SLOP.md` §5 pkt 2.
3. Zachować w backlogu otwarte pozycje P2 z ADR 0188 (weryfikacja odcienia `cycle_asphalt_red` zdjęciem z poziomu ziemi w C, podział odcinka `237088754` w Dojlidach, 6 niepewnych odcinków w C).

---

## Weryfikacja szczegółowa (checklista M65 §5 + ADR 0188)

| Obszar | Kadry dowodowe (`sbs-r4/`) | Wynik | Obserwacja |
|---|---|---|---|
| Dojlidy: ciepłoszary asfalt `cycle_asphalt` | `sbs-D-{High,Low}-photo-P11-001.jpg`, `D-High-route-s0152.jpg` | **PASS** | `P11-001` (`x≈1220–1600, y≈260–540`) i `route-s0152` (`x≈580–960, y≈300–540`): ciepłoszary, matowy asfalt bliski barwie na zdjęciu CC0 (`x≈0–340`). Brak jaskrawej czerwieni. |
| Dojlidy: układ `away` i zjazd Kuronia 3 | `sbs-D-{High,Low}-photo-P11-001.jpg`, `D-High-route-s1370.jpg` | **PASS** | Od prawej: jezdnia → zieleń → chodnik z kostki → DDR → trawnik. Zjazd `kuronia3-gate-driveway` (`x≈960–1860, y≈320–390`) z jasnej kostki przerywa DDR bez czerwonego pola; P-23 przed zjazdem (`x≈1290–1370, y≈445–485`) i za nim. |
| Przejazd P-11 czerwony (`P11-056`) | `sbs-D-{High,Low}-photo-P11-056.jpg` | **PASS** | Przejazd przez wlot Dywizjonu 303 (`x≈1260–1450, y≈365–395`) ma stonowane czerwone pole `cycle_crossing_red` z białymi kwadratami P-11 obok zebry, zgodnie ze zdjęciem (`x≈240–340`). |
| Przejazdy P-11 wyłącznie białe (`P11-063`, Putry) | `sbs-D-{High,Low}-photo-P11-063.jpg`, `C-{Low,High}-putry-above.jpg` | **PASS** | `P11-063` (`x≈1420–1500, y≈495–525`): tylko białe kwadraty P-11. Rondo Putry (`x≈380–460, y≈440–490` oraz `x≈580–650, y≈450–510` na obrazie `960×540`): na jezdniach wyłącznie białe P-11 bez czerwonego podkładu. |
| Region C: czerwonobrązowy asfalt `cycle_asphalt_red` | `sbs-C-{High,Low}-g3_c_1173244557941023.jpg`, `sbs-C-High-g3_c_295679109352815.jpg`, `C-{Low,High}-putry-above.jpg` | **PASS** | Wyraźnie bordowa/czerwonobrązowa DDR (`g3_c_1173...` `x≈1530–1919, y≈260–400`; `g3_c_2956...` `x≈1710–1919, y≈345–400`; `putry-above` `x≈270–360, y≈360–430`) obok kostki chodnika. |
| Jakość renderu Low/High (z-fighting, migotanie) | Wszystkie powyższe pary Low i High | **PASS** | Brak z-fightingu na decalach P-23, liniach segregacyjnych i polach P-11; krawędzie pasów na Low (MSAA 2×, `renderScale=0.75`) czytelne i bez artefaktów. |

---

## Oceny (1–10)

| Kategoria | Ocena | Uzasadnienie (w zakresie ADR 0188 i kontekście kadrów r4) |
|---|---:|---|
| Zgodność z referencją (M65) | 9 | Wszystkie 4 tezy M65 (ciepłoszara DDR Dojlid, bordowa DDR Putry, selektywne czerwone P-11, układ `away` + przerwanie Kuronia 3) odtworzone zgodnie z ortofoto i zdjęciami. |
| Materiały DDR i P-11 | 8 | `cycle_asphalt`, `cycle_asphalt_red` i `cycle_crossing_red` mają naturalne, przygaszone albedo bez plastikowego połysku ani przesycenia (`docs/06` §2). Kalibracja `cycle_asphalt_red` pozostaje `WORKING_VALUE` z ortofoto. |
| Czytelność i detale (Low/High) | 8 | P-23, linie przerywane/krawędziowe i kwadraty P-11 ostre, dobrze osadzone na nawierzchni, spójne między Low i High. |
| Budżet i wydajność | 9 | Brak regresji: `WORLD_MEMORY` +0,2–0,7 MB, `drawsEst` w C +2–3 draws wobec baseline, czasy klatek w edytorze 1,74–3,68 ms (Low) i 3,38–7,75 ms (High). |

---

## Budżet A/B (`drawsEst`, `trisExact`, `WORLD_MEMORY`)

Porównanie z `artifacts/ddr-0188/r4/*/stats.txt`, `c-before-Low-overcast/stats.txt`, `import-*-r4.log` oraz bazowych `import-{c,doj}.log`:

- **Dojlidy (`r4/D-Low`, `r4/D-High`):**
  - `D-Low`: `drawsEst` `127–346` (hipoteza `docs/06` §6: ≤ 300–400), `trisExact` `161 402–469 944` (≤ 400–600 tys.), frame time `1,74–3,07 ms`.
  - `D-High`: `drawsEst` `190–638` (≤ 700–1000), `trisExact` `301 454–873 691` (≤ 1,5–2 mln), frame time `3,38–6,06 ms`.
  - `WORLD_MEMORY`: Low `99,6 MB` (przed zmianą `99,3 MB`, +0,3 MB; `markings` `2,0 → 2,3 MB`, `paved` `3,5 → 2,9 MB`), High `214,9 MB` (przed zmianą `214,7 MB`, +0,2 MB).
- **Region C (`r4/C-Low`, `r4/C-High`):**
  - `C-Low` vs `c-before-Low-overcast`:
    - `dk8-dk19-exit`: `76` draws / `108 246` tris (przed: `73` / `107 059`)
    - `fire-station-above`: `280` draws / `278 507` tris (przed: `280` / `276 183`)
    - `sbs-g3-b-1528935774382039`: `429` draws / `373 519` tris (przed: `427` / `367 668`)
    - `sbs-g3-b-297817221966185`: `431` draws / `389 910` tris (przed: `429` / `383 027`)
  - `C-High`: `drawsEst` `91–895` (≤ 700–1000), `trisExact` `143 582–1 122 138` (≤ 1,5–2 mln), frame time `4,74–7,75 ms`.
  - `WORLD_MEMORY`: Low `124,2 MB` (przed zmianą `123,5 MB`, +0,7 MB; `markings` `3,1 → 3,6 MB`), High `267,0 MB` (przed zmianą `266,5 MB`, +0,5 MB).

---

## Problemy (lista P0 / P1 / P2)

### W zakresie ADR 0188 (`ddr-0188`)
Brak P0 i P1. Zidentyfikowano wyłącznie drobne pozycje **P2**:
- **P2 — `cycle_asphalt_red` skalibrowane jako `WORKING_VALUE` z ortofoto** (`sbs-C-High-g3_c_1173244557941023.jpg` `x≈1530–1919, y≈260–400`, `C-High-putry-above.jpg` `x≈270–360, y≈360–430`): w materiale C brakuje bezpośredniego zdjęcia z poziomu ziemi obejmującego samą nawierzchnię DDR pod estakadą, więc odcień bordowy pozostaje do potwierdzenia przy okazji wizji lokalnej lub nowych zdjęć CC0.
- **P2 — otwarte odcinki niepewne i dzielone z M65 §5** (świadomie udokumentowane w ADR 0188): odcinek `237088754` w Dojlidach (25 % `away` / 75 % przy jezdni) do ewentualnego podziału, 6 niepewnych odcinków w C pozostawionych jako ciepłoszare oraz 10 drobnych przecięć osiedlowych w C bez czerwieni.
- **P2 — niespójność nazwy materiału w starszym logu `bw-doj-r4.log`** (`artifacts/ddr-0188/bw-doj-r4.log` z 14.11 19:31, linia 12): w podsumowaniu `paved 306 areas` widnieje jeszcze klucz `cycle_asphalt_red: 14828`, choć w aktualnym `tools/worldgen/streetscape/cycleways.py` (`875719b70`) Dojlidy używają `MAT_GREY = "cycle_asphalt"` i renderują się w r4 jako ciepłoszare. Drobiazg porządkowy przy najbliższym przebudowaniu regionu na `main`.

### Poza zakresem ADR 0188 (zaobserwowane na kadrach r4, nie blokują scalenia `ddr-0188`)
- **P1 (0185 / ogrodzenia) — mora na zielonym/białym ogrodzeniu panelowym**: `sbs-D-Low-photo-P11-001.jpg` (`x≈960–1280, y≈270–340`) i `sbs-D-High-photo-P11-063.jpg` (`x≈1680–1919, y≈405–440`).
- **P1 (0186 / kamera i sygnalizator) — przesunięty kadr i biała tarcza sygnalizatora na `P11-063`**: `sbs-D-High-photo-P11-063.jpg` (`x≈1410–1590, y≈20–360`) ma maszt w środku kadru i nienaturalnie białe plecy sygnalizatora oraz kępki krzewów z przerwami (`x≈960–1370, y≈360–440`).
- **P1 (far-field / roślinność) — brak linii lasu na horyzoncie `P11-056` i ciemne plamy na koronach HLOD lasu w `C-High-putry-above.jpg`**: `sbs-D-High-photo-P11-056.jpg` (`x≈960–1400, y≈270–330`) oraz `C-High-putry-above.jpg` (`x≈140–380` i `780–930, y≈75–155`).
- **P2 (skrypt `sbs.py`) — czarny pas u dołu prawej połowy w kadrach pionowych/kwadratowych C**: `sbs-C-{High,Low}-g3_c_1173244557941023.jpg` (`x≈960–1919, y≈400–540`) oraz `sbs-C-High-g3_c_295679109352815.jpg` (`x≈960–1919, y≈400–540`) — wynik różnicy proporcji zdjęcia referencyjnego i rendera `16:9`.
