# Status ADR — audyt i aktualizacja (D24, 2026-11-16, s23)

Baza: `origin/main` @ `e2578ab78`. Gałąź `adr-status-s23`. Zakres: wyłącznie wiersze `Status:` w `docs/adr/*.md`, indeks
`docs/adr/README.md` (generator) i ten raport. Treść decyzji nie zmieniona; nowych ADR brak.

## Metoda
- Spis: `python3 tools/docs/adr_index.py` (istniejący generator indeksu + audyt; `--check` = bez zapisu).
- Data scalenia = data commita na pierwszej linii rodziców `origin/main`, który dodał plik:
  `git log --first-parent origin/main --diff-filter=A --format='%h %cd' --date=short -- <plik>`.
- Zmiana statusu: wartość po `Status:` zastąpiona przez
  `przyjęty (scalony do main <data>, \`<sha>\`; status zaktualizowany 2026-11-16); pierwotnie: <dawny status bez zmian>` (pliki PL)
  albo `Accepted (merged to main <data>, \`<sha>\`; status updated 2026-11-16); originally: <old status>` (pliki EN).
  Język wg treści pliku (liczba typowych słów PL vs EN). Dawny status zostaje w całości po „pierwotnie/originally”.
- Za „proponowany” uznano: Proposed/PROPOSED/proposed, propozycja, proponowany, zaproponowany, kandydat, implemented on branch …
  not merged, zaimplementowane/wdrożone/wykonane na gałęzi, gotowe do recenzji/integracji, do review lidera — wszystkie pliki
  są w `main`, więc „not merged/nie scalone” w starym statusie jest nieaktualne. Wymagania „przed scaleniem” (recenzja
  visual-critic, „do weryfikacji i scalenia przez lidera”) uznano za spełnione scaleniem przez lidera (HANDOVER: int-pc-s23
  i merge 0229/0230 z EditMode; merge-commity 0101–0200 z werdyktami krytyka).

## Spis (stan po zmianie)
- 229 plików `*.md` (numery 0001–0272) + `README.md` + 1 plik nie-md (`0237-build-world-hook.patch`).
- Status przyjęty/Accepted: 69 przed zmianą → **205** po zmianie (136 zmienionych); bez zmian i do decyzji lidera: 24 (16 w B, 8 w C).
- Pełna tabela numer / tytuł / status / data: `docs/adr/README.md` (z generatora).

## A. Zmienione na „przyjęty / Accepted” (136)
| ADR | Język wpisu | Data scalenia | Commit na main |
|---|---|---|---|
| [0020-cab-screens-command-buffer-canvas](../adr/0020-cab-screens-command-buffer-canvas.md) | EN | 2026-11-09 | `753dbcce1` |
| [0044-cab-interior-phone-legibility-shader](../adr/0044-cab-interior-phone-legibility-shader.md) | EN | 2026-11-10 | `4b012bff2` |
| [0046-high-tier-gate3-60fps-headroom](../adr/0046-high-tier-gate3-60fps-headroom.md) | EN | 2026-11-10 | `7612b1b0f` |
| [0062-high-scale-floor-fsr-pacing-dusk-lamps](../adr/0062-high-scale-floor-fsr-pacing-dusk-lamps.md) | EN | 2026-11-10 | `c0a03d08d` |
| [0063-cc0-scan-materials](../adr/0063-cc0-scan-materials.md) | EN | 2026-11-10 | `6382fc104` |
| [0064-baked-ground-sky-visibility-far-shadows](../adr/0064-baked-ground-sky-visibility-far-shadows.md) | EN | 2026-11-10 | `0e45111f3` |
| [0068-mirror-capture-shadow-pass-cost](../adr/0068-mirror-capture-shadow-pass-cost.md) | EN | 2026-11-10 | `1ff9fb59a` |
| [0073-cars-r9-silhouettes](../adr/0073-cars-r9-silhouettes.md) | PL | 2026-11-10 | `fd0e25388` |
| [0078-cars-r10-lamps-paint-lod2](../adr/0078-cars-r10-lamps-paint-lod2.md) | PL | 2026-11-11 | `2ab23b251` |
| [0079-adaptive-hud-layout](../adr/0079-adaptive-hud-layout.md) | EN | 2026-11-10 | `ba74b1e47` |
| [0081-buildings-r10-facade-atlases](../adr/0081-buildings-r10-facade-atlases.md) | PL | 2026-11-11 | `24964e954` |
| [0083-truck-exterior-r10](../adr/0083-truck-exterior-r10.md) | EN | 2026-11-10 | `68e53354f` |
| [0086-world-pbr-tint-gamma](../adr/0086-world-pbr-tint-gamma.md) | EN | 2026-11-11 | `0e73211ad` |
| [0088-vegetation-r2](../adr/0088-vegetation-r2.md) | PL | 2026-11-11 | `6b8f9123c` |
| [0091-buildings-r3-roofs-balconies](../adr/0091-buildings-r3-roofs-balconies.md) | PL | 2026-11-11 | `9f9a34c50` |
| [0092-kwadrat-park-r12](../adr/0092-kwadrat-park-r12.md) | PL | 2026-11-11 | `8cbc92640` |
| [0094-buildings-r4](../adr/0094-buildings-r4.md) | PL | 2026-11-11 | `aac557492` |
| [0097-buildings-r5](../adr/0097-buildings-r5.md) | PL | 2026-11-11 | `7c094c3f6` |
| [0098-light-post-r12](../adr/0098-light-post-r12.md) | PL | 2026-11-11 | `bfdde95f5` |
| [0101-tint-calibration-r2](../adr/0101-tint-calibration-r2.md) | PL | 2026-11-11 | `4c63f4c4c` |
| [0102-street-furniture-r1](../adr/0102-street-furniture-r1.md) | PL | 2026-11-11 | `85e19ebf8` |
| [0104-cab-interior-mirrors-r1](../adr/0104-cab-interior-mirrors-r1.md) | EN | 2026-11-11 | `1c894f25d` |
| [0105-dk8-putry-underdeck](../adr/0105-dk8-putry-underdeck.md) | PL | 2026-11-11 | `68ca9fd86` |
| [0106-perf-low-a16-r1](../adr/0106-perf-low-a16-r1.md) | PL | 2026-11-11 | `1791a0ed8` |
| [0107-buildings-r6-plots](../adr/0107-buildings-r6-plots.md) | PL | 2026-11-11 | `615d7e6e7` |
| [0113-perf-low-a16-r2](../adr/0113-perf-low-a16-r2.md) | PL | 2026-11-11 | `33e800737` |
| [0114-buildings-r7-plots](../adr/0114-buildings-r7-plots.md) | PL | 2026-11-11 | `3540bbdf7` |
| [0125-gate3-signs-gantries](../adr/0125-gate3-signs-gantries.md) | EN | 2026-11-12 | `efe75dc9d` |
| [0126-g3b-frontage](../adr/0126-g3b-frontage.md) | EN | 2026-11-12 | `543f9be3d` |
| [0127-g3b-low-readability](../adr/0127-g3b-low-readability.md) | EN | 2026-11-12 | `a6cfe38ab` |
| [0128-biezenstwa-island](../adr/0128-biezenstwa-island.md) | EN | 2026-11-12 | `e79c5cc32` |
| [0129-frontage-r2](../adr/0129-frontage-r2.md) | EN | 2026-11-12 | `b596efe9a` |
| [0130-sbs-poses-g3b](../adr/0130-sbs-poses-g3b.md) | EN | 2026-11-12 | `abf15f9ef` |
| [0131-render-p1](../adr/0131-render-p1.md) | EN | 2026-11-12 | `2fbab3657` |
| [0132-buildings-r9](../adr/0132-buildings-r9.md) | PL | 2026-11-12 | `4e76cb328` |
| [0133-putry-deck-lamps](../adr/0133-putry-deck-lamps.md) | EN | 2026-11-12 | `09d0e355a` |
| [0134-truck-feel](../adr/0134-truck-feel.md) | EN | 2026-11-12 | `d38c2e847` |
| [0135-steer-fold](../adr/0135-steer-fold.md) | PL | 2026-11-12 | `5636fe043` |
| [0136-a16-gpu-regression-impostor-trim](../adr/0136-a16-gpu-regression-impostor-trim.md) | PL | 2026-11-12 | `b596efe9a` |
| [0137-elevenlabs-engine-audio](../adr/0137-elevenlabs-engine-audio.md) | PL | 2026-11-12 | `e37569842` |
| [0138-audio-regen01](../adr/0138-audio-regen01.md) | PL | 2026-11-12 | `b142dd8f5` |
| [0139-g3b-r2-review-fixes](../adr/0139-g3b-r2-review-fixes.md) | EN | 2026-11-12 | `97996ef6b` |
| [0141-edge-skyline-closures](../adr/0141-edge-skyline-closures.md) | EN | 2026-11-12 | `ca0bc16e0` |
| [0142-audio-fx](../adr/0142-audio-fx.md) | PL | 2026-11-12 | `b596efe9a` |
| [0143-sbs-poses-r3](../adr/0143-sbs-poses-r3.md) | EN | 2026-11-12 | `70b67fc7b` |
| [0144-junctions-r7](../adr/0144-junctions-r7.md) | PL | 2026-11-12 | `48905cb7d` |
| [0145-tyre-scrub-squeal](../adr/0145-tyre-scrub-squeal.md) | PL | 2026-11-12 | `f39332740` |
| [0146-putry-andersa-world](../adr/0146-putry-andersa-world.md) | EN | 2026-11-12 | `430f7e93b` |
| [0147-orientation-phones-fold](../adr/0147-orientation-phones-fold.md) | PL | 2026-11-12 | `fee0d9405` |
| [0148-audio-idle-fold](../adr/0148-audio-idle-fold.md) | PL | 2026-11-12 | `63bf93dc6` |
| [0149-steering-feel-fold-r2](../adr/0149-steering-feel-fold-r2.md) | PL | 2026-11-12 | `34940850f` |
| [0150-map-minimap-gps](../adr/0150-map-minimap-gps.md) | PL | 2026-11-12 | `bbf601d7d` |
| [0151-fifth-wheel-creep-hud-steer-r3](../adr/0151-fifth-wheel-creep-hud-steer-r3.md) | PL | 2026-11-12 | `e364975f1` |
| [0152-fold-flicker-shadows-fps](../adr/0152-fold-flicker-shadows-fps.md) | PL | 2026-11-12 | `fbb610dd3` |
| [0153-vehicle-lod-atlas](../adr/0153-vehicle-lod-atlas.md) | PL | 2026-11-13 | `87ffeb301` |
| [0155-putry-island-sun-spots](../adr/0155-putry-island-sun-spots.md) | PL | 2026-11-13 | `2051104f5` |
| [0156-elevenlabs-regen04-cab-noload](../adr/0156-elevenlabs-regen04-cab-noload.md) | PL | 2026-11-12 | `81ab77881` |
| [0158-physics-airborne-energy](../adr/0158-physics-airborne-energy.md) | PL | 2026-11-13 | `ff5c62a6a` |
| [0159-barriers-screens-putry-andersa](../adr/0159-barriers-screens-putry-andersa.md) | EN | 2026-11-13 | `230fa0f14` |
| [0160-g3a-p0-poses-foreground-anchors](../adr/0160-g3a-p0-poses-foreground-anchors.md) | PL | 2026-11-13 | `227c2b6f7` |
| [0161-p1-kadrow-bramki-3](../adr/0161-p1-kadrow-bramki-3.md) | PL | 2026-11-13 | `9ce107f1f` |
| [0162-street-furniture-signs-g5-g3](../adr/0162-street-furniture-signs-g5-g3.md) | PL | 2026-11-13 | `68d2b5dd6` |
| [0163-house-street-greenery-g7](../adr/0163-house-street-greenery-g7.md) | PL | 2026-11-13 | `0fa8d7362` |
| [0164-tagi-limitow-ciezarowki-w-grafie-drog](../adr/0164-tagi-limitow-ciezarowki-w-grafie-drog.md) | PL | 2026-11-13 | `4ea7a6c11` |
| [0165-physics-compliant-body-contact](../adr/0165-physics-compliant-body-contact.md) | PL | 2026-11-13 | `4c71a1dc7` |
| [0166-region-dojlidy-krywlany](../adr/0166-region-dojlidy-krywlany.md) | PL | 2026-11-13 | `78bb6d563` |
| [0167-budynki-p1-kadry-bramki-3](../adr/0167-budynki-p1-kadry-bramki-3.md) | PL | 2026-11-13 | `63ddfae4f` |
| [0168-nav-exit-policy-voice-tiers-eta-no-return](../adr/0168-nav-exit-policy-voice-tiers-eta-no-return.md) | EN | 2026-11-13 | `668b027b7` |
| [0169-world-edge-one-closure-source](../adr/0169-world-edge-one-closure-source.md) | EN | 2026-11-13 | `8c73d2a8f` |
| [0170-horizon-forest-stand-near-crowns](../adr/0170-horizon-forest-stand-near-crowns.md) | PL | 2026-11-13 | `a4d2a1782` |
| [0171-budynki-follow-up-kolory-cm109-ec-wiezowiec](../adr/0171-budynki-follow-up-kolory-cm109-ec-wiezowiec.md) | PL | 2026-11-13 | `6230a9a6d` |
| [0173-world-determinism-between-builds](../adr/0173-world-determinism-between-builds.md) | EN | 2026-11-13 | `b880fc6a1` |
| [0174-import-dojlidy-biblioteka-per-region](../adr/0174-import-dojlidy-biblioteka-per-region.md) | PL | 2026-11-13 | `110c756fe` |
| [0175-truck-appearance-regulations](../adr/0175-truck-appearance-regulations.md) | PL | 2026-11-13 | `e0aee8560` |
| [0176-synteza-retarder-hamulec-silnikowy-amt-osuszacz](../adr/0176-synteza-retarder-hamulec-silnikowy-amt-osuszacz.md) | PL | 2026-11-13 | `27f4127f8` |
| [0177-perf-p99-pso-refresh](../adr/0177-perf-p99-pso-refresh.md) | PL | 2026-11-13 | `3e62962c5` |
| [0178-lamp-hue](../adr/0178-lamp-hue.md) | PL | 2026-11-13 | `280e5cff1` |
| [0179-dojlidy-poprawki-wizualne](../adr/0179-dojlidy-poprawki-wizualne.md) | PL | 2026-11-13 | `b546b4df2` |
| [0181-lamp-lens-structure](../adr/0181-lamp-lens-structure.md) | PL | 2026-11-13 | `b823e3c49` |
| [0182-dusk-civil-twilight-end-rear-soiling](../adr/0182-dusk-civil-twilight-end-rear-soiling.md) | PL | 2026-11-13 | `1be00a4f0` |
| [0183-slupki-bialo-czerwone-z-lancuchem](../adr/0183-slupki-bialo-czerwone-z-lancuchem.md) | PL | 2026-11-14 | `1e5f38f47` |
| [0185-dojlidy-budynki-p1](../adr/0185-dojlidy-budynki-p1.md) | PL | 2026-11-14 | `a1f1615ee` |
| [0186-dojlidy-zielen-kadru-063](../adr/0186-dojlidy-zielen-kadru-063.md) | PL | 2026-11-15 | `dd4bdd42d` |
| [0187-sciana-lasu-swierk-mlodnik-plaszcz-horyzont](../adr/0187-sciana-lasu-swierk-mlodnik-plaszcz-horyzont.md) | PL | 2026-11-15 | `33ee4f985` |
| [0188-drogi-dla-rowerow-czerwony-asfalt](../adr/0188-drogi-dla-rowerow-czerwony-asfalt.md) | PL | 2026-11-15 | `5a5ee9166` |
| [0189-brama-szpitala-masonry-gate](../adr/0189-brama-szpitala-masonry-gate.md) | PL | 2026-11-15 | `35aecd6f1` |
| [0190-wiezowiec-jasne-pasma-nadproze-rama-szczytu-maszty](../adr/0190-wiezowiec-jasne-pasma-nadproze-rama-szczytu-maszty.md) | PL | 2026-11-14 | `baae5f0e0` |
| [0191-lamp-pools-road-luminaire-footprint](../adr/0191-lamp-pools-road-luminaire-footprint.md) | PL | 2026-11-14 | `1d72f829c` |
| [0192-night-windows-twilight-magenta-lamp-glare](../adr/0192-night-windows-twilight-magenta-lamp-glare.md) | PL | 2026-11-14 | `1d72f829c` |
| [0193-sygnalizator-tarcza-i-kamera-d6](../adr/0193-sygnalizator-tarcza-i-kamera-d6.md) | PL | 2026-11-15 | `fa857b11b` |
| [0194-plamy-i-brud-asfaltu](../adr/0194-plamy-i-brud-asfaltu.md) | PL | 2026-11-15 | `5d64bcd92` |
| [0195-autopilot-prosta-0-80-0](../adr/0195-autopilot-prosta-0-80-0.md) | PL | 2026-11-13 | `ea6fdf840` |
| [0196-dojlidy-zaklad-bramy-zacieki-pas](../adr/0196-dojlidy-zaklad-bramy-zacieki-pas.md) | PL | 2026-11-14 | `5eb18d59e` |
| [0199-kalibracja-zmierzchu-i-nocy](../adr/0199-kalibracja-zmierzchu-i-nocy.md) | PL | 2026-11-14 | `f1dfef0af` |
| [0200-wiezowiec-nw-pasma-maszt-srodkowy-przybudowka](../adr/0200-wiezowiec-nw-pasma-maszt-srodkowy-przybudowka.md) | PL | 2026-11-14 | `6031883c7` |
| [0201-truckdata-r3-promien-toczny-naciski-marki](../adr/0201-truckdata-r3-promien-toczny-naciski-marki.md) | PL | 2026-11-15 | `a31939ef5` |
| [0201b-naciski-osi-73-27-strojenie-zawieszenia-amt](../adr/0201b-naciski-osi-73-27-strojenie-zawieszenia-amt.md) | PL | 2026-11-15 | `f9781a32b` |
| [0202-dojlidy-u12b-pas-27l-ogrodzenie](../adr/0202-dojlidy-u12b-pas-27l-ogrodzenie.md) | PL | 2026-11-14 | `e4bd4f95c` |
| [0203-trasa-bialystok-knyszyn-plan-kafli-i-kafel-maczka](../adr/0203-trasa-bialystok-knyszyn-plan-kafli-i-kafel-maczka.md) | PL | 2026-11-15 | `67eea261c` |
| [0204-region-knyszyn-miasto-i-wlot-dk65](../adr/0204-region-knyszyn-miasto-i-wlot-dk65.md) | PL | 2026-11-15 | `c8afe5a7a` |
| [0205-korytarz-dk65-kafel-dk65-01](../adr/0205-korytarz-dk65-kafel-dk65-01.md) | PL | 2026-11-15 | `f6ba266e4` |
| [0206-kafel-bialystok-kleeberga](../adr/0206-kafel-bialystok-kleeberga.md) | PL | 2026-11-15 | `4320d3b6a` |
| [0207-korytarz-dk65-kafle-02-05](../adr/0207-korytarz-dk65-kafle-02-05.md) | PL | 2026-11-15 | `8205aa15d` |
| [0208-kafel-bialystok-knyszynska-i-mur-na-pomoscie](../adr/0208-kafel-bialystok-knyszynska-i-mur-na-pomoscie.md) | PL | 2026-11-15 | `134298d01` |
| [0209-region-knyszyn-w-wylot-dk65-na-monki](../adr/0209-region-knyszyn-w-wylot-dk65-na-monki.md) | PL | 2026-11-15 | `d4914ba6e` |
| [0210-etap-wody-rzeki-stawy](../adr/0210-etap-wody-rzeki-stawy.md) | PL | 2026-11-15 | `e243e3e86` |
| [0211-tunel-plyta-nad-wykopem-dk8](../adr/0211-tunel-plyta-nad-wykopem-dk8.md) | PL | 2026-11-15 | `1990afc8d` |
| [0212-linie-krawedziowe-dk65-knyszyn-i-kafle-monki-tykocin](../adr/0212-linie-krawedziowe-dk65-knyszyn-i-kafle-monki-tykocin.md) | PL | 2026-11-15 | `8fbe0b972` |
| [0213-woda-dk65-03-kolor-brzegi](../adr/0213-woda-dk65-03-kolor-brzegi.md) | PL | 2026-11-15 | `2ff133e21` |
| [0214-korytarz-dk65-kafle-06-11-place-budowy](../adr/0214-korytarz-dk65-kafle-06-11-place-budowy.md) | PL | 2026-11-15 | `8a99d4302` |
| [0215-d65-elcka-6p9-i-jezdnia-w-budowie-dk65-05](../adr/0215-d65-elcka-6p9-i-jezdnia-w-budowie-dk65-05.md) | PL | 2026-11-15 | `f64364ba4` |
| [0216-lato-i-biale-led-dk65-knyszyn](../adr/0216-lato-i-biale-led-dk65-knyszyn.md) | PL | 2026-11-15 | `5432820e3` |
| [0217-torowisko-i-przejazdy-kolejowe](../adr/0217-torowisko-i-przejazdy-kolejowe.md) | PL | 2026-11-15 | `f92d0ab6a` |
| [0218-rondo-knyszyn-opaska-dla-naczepy](../adr/0218-rondo-knyszyn-opaska-dla-naczepy.md) | PL | 2026-11-16 | `5824464bd` |
| [0220-dk65-k1-przekroj-linie-krawedziowe-zatoki](../adr/0220-dk65-k1-przekroj-linie-krawedziowe-zatoki.md) | PL | 2026-11-16 | `5824464bd` |
| [0221-budzet-drog-p23-obrzeza](../adr/0221-budzet-drog-p23-obrzeza.md) | PL | 2026-11-15 | `dedefc104` |
| [0222-szpalery-dk65](../adr/0222-szpalery-dk65.md) | PL | 2026-11-16 | `5824464bd` |
| [0229-wybor-regionu-w-buildzie-i-menu](../adr/0229-wybor-regionu-w-buildzie-i-menu.md) | PL | 2026-11-15 | `90426fdd2` |
| [0230-legalnosc-atrybucje-dane-miasta](../adr/0230-legalnosc-atrybucje-dane-miasta.md) | PL | 2026-11-15 | `db3678f60` |
| [0232-dzwiek-silnika-sterowany-fizyka-ab](../adr/0232-dzwiek-silnika-sterowany-fizyka-ab.md) | PL | 2026-11-15 | `63baf7776` |
| [0233-dk65-szew-knyszyn-s-przekroj-k1-lanes-follow-width](../adr/0233-dk65-szew-knyszyn-s-przekroj-k1-lanes-follow-width.md) | PL | 2026-11-15 | `fb9cd8318` |
| [0236-drogowskazy-trasy-c-wg-normy-i-r2](../adr/0236-drogowskazy-trasy-c-wg-normy-i-r2.md) | PL | 2026-11-16 | `e4fad6868` |
| [0237-chodniki-krawezniki-typy-nawierzchni](../adr/0237-chodniki-krawezniki-typy-nawierzchni.md) | PL | 2026-11-16 | `e4fad6868` |
| [0239-plot-panelowy-pokrycie-z-dystansem](../adr/0239-plot-panelowy-pokrycie-z-dystansem.md) | PL | 2026-11-16 | `e4fad6868` |
| [0240-cienie-cienkich-obiektow-low](../adr/0240-cienie-cienkich-obiektow-low.md) | PL | 2026-11-16 | `e4fad6868` |
| [0241-gpu-ab-a16-low](../adr/0241-gpu-ab-a16-low.md) | PL | 2026-11-16 | `e4fad6868` |
| [0242-dojlidy-rozpoznawalnosc-wysokosci-z-nmpt](../adr/0242-dojlidy-rozpoznawalnosc-wysokosci-z-nmpt.md) | PL | 2026-11-16 | `e4fad6868` |
| [0261-build-windows](../adr/0261-build-windows.md) | PL | 2026-11-15 | `6182b3966` |
| [0263-kierownica-pedaly-ffb](../adr/0263-kierownica-pedaly-ffb.md) | PL | 2026-11-16 | `3e9ef52fc` |
| [0264-pad-klawiatura-rebinding](../adr/0264-pad-klawiatura-rebinding.md) | PL | 2026-11-16 | `3e9ef52fc` |
| [0265-hud-ui-pc](../adr/0265-hud-ui-pc.md) | PL | 2026-11-16 | `3e9ef52fc` |
| [0267-poprawki-wyboru-regionow](../adr/0267-poprawki-wyboru-regionow.md) | PL | 2026-11-16 | `3e9ef52fc` |
| [0268-oznakowanie-dojazdu-do-przejazdow-kolejowych](../adr/0268-oznakowanie-dojazdu-do-przejazdow-kolejowych.md) | PL | 2026-11-16 | `feb542757` |
| [0269-tiery-grafiki-pc](../adr/0269-tiery-grafiki-pc.md) | PL | 2026-11-16 | `3e9ef52fc` |
| [0270-menu-ustawien-pc](../adr/0270-menu-ustawien-pc.md) | PL | 2026-11-16 | `3e9ef52fc` |
| [0271-dystrybucja-pc](../adr/0271-dystrybucja-pc.md) | PL | 2026-11-16 | `3e9ef52fc` |

## B. Pozostawione bez zmian — wątpliwe (16)
| ADR | Powód (z tekstu statusu / historii) |
|---|---|
| 0084 | „**not cleared for merge**: full visual realism and strict per-view Low cost gates…” (scalone 2026-11-11 `98e54e477`) |
| 0087 | „PARTIAL OWNER QUALITY: appearance thresholds remain FAIL” |
| 0089 | „dust realism PARTIAL; historical R3 visual acceptance is withdrawn” |
| 0103 | status nie jest propozycją: „tooling … delivered; **gate 3 NOT accepted**” |
| 0109 | „ograniczona korekta … PASS; ogólny realizm pozostaje FAIL” |
| 0112 | „r1 zakończona w zakresie K1–K3, bez przejścia bramki wizualnej; K4–K6 do r2” |
| 0115 | „cel wyglądu lakieru i szyby pozostaje otwarty” |
| 0118 | „Stan r1: ocena wizualna warunkowa, bez pełnego PASS” |
| 0120 | „praca w toku, bez zgody na integrację” (plik trafił do main 2026-11-12 `1f95455eb` z gpt-furniture-r2) |
| 0122 | „life r4 A2 wybrany, PARTIAL” |
| 0124 | „propozycja, runda r1 — przerwana limitem sesji” (scalona r2 „SCAL warunkowo”) — lider: przyjąć częściowo? |
| 0140 | tytuł/sekcja „PARTIAL diagnosis” (dane SBS r2) |
| 0154 | „kandydat B …; Fotograficzne D51 i Gate 3 pozostają PARTIAL” |
| 0219 | PR #95 `qa-tools-0219` **zamknięty bez scalenia**; plik wszedł przez `c-regen-s22` (`1ab7e9b63`, „z #95 far_field (0219)”) |
| 0223 | PR #102 `rail-dk65-0223` **zamknięty bez scalenia**; plik wszedł przez `rail-dk65-s22` (`feb542757`, „#102 linia 38”) |
| 0272 | PR #138 `rural-xsec-0272` **zamknięty bez scalenia**; plik wszedł przez `rail-dk65-s22` (`feb542757`) |

## C. ADR bez wiersza statusu (8) — bez zmian
0099 (tekst: „appearance remains PARTIAL”), 0108, 0111 („częściowa … UNVERIFIED”), 0116, 0119 („Runda r2 — w toku”),
0121 — format dziennika rund GPT bez statusu; **0260** (D73, decyzja właściciela) i **0266** (bramki PC, scalone z int-pc-s23
`3e9ef52fc`) — jasne decyzje bez wiersza `Status:`; propozycja dla lidera: dopisać `Status: przyjęty (…)`.

## D. Numery bez pliku w main (51)
Źródła: HANDOVER „Ostatni przydzielony ADR: 0279” + zakresy (0222–0226 D r1, 0227 Codex, 0228–0232 E, 0234–0242 D r2,
0243–0246 G, 0247–0259 D r3, 0269–0271 H r2, 0272–0273 D r4, 0274–0275 D r5, 0276–0277 H r3, 0278–0279 D r6);
docs/11 wymienia z tego zakresu tylko 0234. Sprawdzone `git ls-tree origin/<gałąź> docs/adr` dla 18 otwartych PR i wszystkich gałęzi `origin/*`.

| Numer | Plik poza main | Gdzie |
|---|---|---|
| 0197 | `0197-lamp-r148-stop-tail-amber-plate.md` | PR #79 `lights-0197` (otwarty) |
| 0198 | `0198-podpory-estakady-a-putry-pier-lines-en.md` | PR #93 `putry-ring-0198b` (otwarty); wcześniejszy #82 `piers-0198` zamknięty |
| 0224 | `0224-qa-szwow-przekroju-drogi-dk65.md` | PR #106 `seams-0224` i PR #143 `seam-taper-0275` (oba otwarte; #143 zastępuje #106) |
| 0225 | — | brak na żadnej gałęzi (zakres D r1) |
| 0226 | `0226-rondo-putry-wyspa-z-ortofoto-apron-width.md` | PR #93 `putry-ring-0198b` |
| 0227 | `0227-knyszyn-rynek.md` | PR #139 `knyszyn-rynek-0227` |
| 0228 | `0228-przegub-kontakt-kabina-naczepa-ladowanie.md` | PR #113 `jackknife-0228` |
| 0231 | `0231-pierscien-monki-tykocin-jasionowka-definicja-z-grubsza.md` | PR #115 `ring-0231` |
| 0234 | `0234-osobne-paczki-regionow-assetbundles.md` | PR #112 `regionpacks-0234` |
| 0235 | `0235-streaming-kafli-addytywny.md` | tylko gałąź `streaming-0235` (PR #114 zamknięty bez scalenia) |
| 0238 | `0238-typologia-zabudowy-bialegostoku.md` | PR #123 `typology-0238` |
| 0243 | `0243-kierownica-270-900-lusterka-okienka.md` | PR #117 `controls-0243` |
| 0244 | `0244-audyt-petli-jazdy-zero-gc-koszt-cpu.md` | PR #118 `perf-loop-0244` |
| 0245 | `0245-higiena-testow-bez-data-raw.md` | PR #119 `tests-hygiene-0245` |
| 0246 | `0246-zrzuty-a16-poz-par-zdjeciowych-g3.md` | PR #116 `g3-poses-0246` |
| 0247–0254, 0256–0259 | — | zarezerwowane dla chmury D r3, brak plików na żadnej gałęzi |
| 0255 | `0255-oznakowanie-dojazdu-do-przejazdow.md` | tylko gałąź `claude/awesome-fermi-3s2wdi` (bez otwartego PR; temat jak ADR 0268 w main) |
| 0273 | `0273-swiat-streaming-kafli-paczki-jako-dystrybucja.md` | PR #112 `regionpacks-0234` |
| 0274 | `0274-rondo-knyszyn-krawezniki-rozdzial-dk65-wyspa.md` | PR #144 `roundabout2-0274` |
| 0275 | `0275-przejscia-szerokosci-na-szwach-kafli.md` | PR #143 `seam-taper-0275` |
| 0276 | `0276-pc-polish.md` | PR #142 `pc-polish-0276` |
| 0277 | `0277-bezpiecznik-startu.md` | PR #141 `spawn-safety-0277` |
| 0278, 0279 | — | zarezerwowane w rundzie 6 (D19, D21), w toku |
| 0026–0028, 0030–0032, 0034–0037, 0040, 0053–0055, 0057, 0090 | — | historyczne luki (przenumerowania s1–s10), brak na gałęziach; martwe odwołania „ADR 0032” (`tests/physics/test_scenario_strictness.py`, raport mistral) i „ADR 0090” (GPT-TASK-02-S10, recenzja s10) — audyt generatora |

## E. Duplikaty numerów i nazwy niezgodne ze wzorcem `NNNN-slug.md`
- Duplikaty w main: **brak**. Na otwartych gałęziach: **0224** w PR #106 i #143 (ten sam plik — scalić tylko jeden);
  **0198** w otwartym #93 i zamkniętym #82; temat „oznakowanie dojazdu do przejazdów” jako 0255 (gałąź bez PR) i 0268 (main).
- `0201b-naciski-osi-73-27-strojenie-zawieszenia-amt.md` — numer z literą; generator pokazuje go jako `????` z tytułem „b — Naciski…”
  (regex `^(\d{4})-`). Propozycja dla lidera: zostawić nazwę (odwołania „ADR 0201b”) i poprawić regex generatora na `^(\d{4}[a-z]?)-`.
- `0237-build-world-hook.patch` — plik nie-`.md` w `docs/adr/` (łatka do ADR 0237); generator go pomija. Propozycja: przenieść do `tools/` albo `docs/adr/assets/`.

## Uwaga dla lidera — konflikty indeksu
Inne PR (np. #106, #112, #113, #115–#119, #123, #139, #141–#144) też dodają ADR i ruszają `docs/adr/README.md`. Przy konflikcie
w `README.md` weź dowolną stronę i **po każdym scaleniu zregeneruj indeks**:
```
python3 tools/docs/adr_index.py          # z katalogu głównego repo; zapisuje docs/adr/README.md + drukuje audyt
python3 tools/docs/adr_index.py --check  # sam audyt
```
Nowe ADR scalane później ze statusem „Proposed” warto od razu przestawiać przy scaleniu tym samym wzorcem co w sekcji A.
