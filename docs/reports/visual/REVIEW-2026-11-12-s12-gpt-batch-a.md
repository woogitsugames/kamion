# Recenzja niezależna — pakiet A rund GPT (edge r3, landmarks r2, light r2, truck r2) — s12

Data: 2026-11-12 · Recenzent: visual-critic (Opus), niezależny od autorów i ich self-review. Tylko odczyt.
Pytanie: czy każdą gałąź można **scalić do main** (`c882f81c`). Kryteria jak w `REVIEW-2026-11-12-s11-gpt-r1-batch2.md`: (a) brak regresji rozpoznawalności trasy wg D51 i obrazu w kadrach trasy/kabiny, (b) Low draws nie rośnie, tris ≤ +2 %, (c) docs/06 — poprawa albo brak pogorszenia. PARTIAL dopuszczalny bez regresji.
Wszystko to render edytora. Żadna runda nie była na telefonie — koszt GPU A16: **UNVERIFIED** dla wszystkich czterech.

Metoda własna: obejrzane pary przed/po i zdjęcie|render ≤960 px; różnica luminancji (1/4 rozdzielczości, średnie |Δ| w LSB) na pełnych zestawach PNG edge r2 i r3; natywne wycinki (panorama południowa edge r2, filar DK8 landmarks ×4 upscale NEAREST, filary na oryginale Commons 7204); przegląd diffów kodu wobec main przez `git merge-tree --write-tree main <gałąź>` (tylko odczyt).

**Uwaga ogólna, ważna dla warunku z light r1:** edge r3, landmarks r2 i truck r2 mają bazę main `2c3939b2`, **sprzed scalenia light r1 (`a5d7d4c1`)**; light r2 jest na własnej linii z r1, ale renderowała tylko Dusk/Night. Żaden z dostarczonych renderów dziennych nie zawiera chmur CC0 + far-field z main. **Klin far-field na tle chmur w g3-a 2948 / 303305 nie został ani naprawiony, ani zweryfikowany przez żadną z tych rund.** Integracja s11 też go nie sprawdziła: `artifacts/integration-s11/run.log` kończy się `PLAYMODE / VQA Low-clear / VQA Low-overcast / APK EXIT -1073741502` (0xC0000142, błąd inicjalizacji procesu), END 09:45 — vqa nie powstało. Warunek light r1 pozostaje otwarty i przechodzi na lidera (render na main po integracji) oraz edge r4 (`artifacts/edge-r3/next-round-review/PLAN-R4.md` stawia go jako priorytet — dobrze).

## Podsumowanie

| Runda | Werdykt | Jakość | (a) trasa D51 | (b) Low draws / tris | (c) anti-slop |
|---|---|---|---|---|---|
| edge r3 (+ r2: wysokości LoD1 tła) | **SCAL** | PARTIAL; r3 wizualnie ~0, r2 mała zmiana panoramy | bez regresji; r3: 364/368 kadrów Δ<0,01, max 0,033 (edge-nw-ground); r2: max kadr trasy 0,13 | r3: 0 / 0 (368 wierszy); r2: 0 / −1k..0k (364) | neutralnie; r2 uwidacznia płaskie pudła tła (P1) |
| landmarks r2 (podpomoście DK8) | **SCAL warunkowo** (ręczna unia `materials.py`) | PARTIAL | bez regresji; 116/232 PNG identyczne, zmiana tylko pod wiaduktem | 0 / −0,42 %..0 % (116 Low) | usunięte zmyślone schody: poprawa; szare „fazy” filarów niezgodne ze zdjęciem (P1) |
| light r2 (Night, reflektory opt-in) | **SCAL** | PARTIAL; dzień nietknięty (ścieżka tożsamościowa w kodzie) | brak wpływu na dzień/Dusk; nowy preset nie jest domyślny | 0 / 0 % (134) | noc = „day-for-night”, nie noc (P1), ale addytywnie |
| truck r2 (retencja brudu na stopniach) | **SCAL** | PARTIAL, wizualnie ~0 poza zbliżeniem stopnia | bez zmian (cab-driver, chase) | 0 / 0 (96) | stopień: mała poprawa; lakier/szyba nadal FAIL (stan main) |

### Konflikty `git merge-tree --write-tree main <gałąź>`
- **edge r3**: czysto. Zmienia jednak `generated/far_field_qa.json`, `generated/world_manifest.json`, `Data/SourceManifests/…-far-field.manifest.json` → po scaleniu regeneracja.
- **landmarks r2**: 3 konflikty — `generated/streetscape_qa.json`, `generated/world_manifest.json` (wziąć main + regeneracja) oraz **`tools/worldgen/streetscape/materials.py` (kod źródłowy)**: obie strony dopisują blok na końcu pliku (main: overrides asphalt r1 ADR 0118, `M["road_asphalt"]` … `M["decal_oil"]`; gałąź: `_underdeck_pier_paint`, ADR 0119). Rozwiązanie = **unia obu bloków** (main, potem landmarks), następnie `tests/gis/test_viaduct_underdeck.py` i testy asfaltu. Nie brać ours/theirs na ślepo — zgubi się albo asphalt r1, albo pigment filarów.
- **light r2**: czysto.
- **truck r2**: czysto (`TruckExterior.shader` +4 linie, ADR 0115).
- Między gałęziami: jedyny wspólny plik edge × landmarks = `generated/world_manifest.json` (regeneracja). Sekwencyjnie (main+edge → landmarks): te same 3 konflikty, nic nowego.
- **Agenci Claude:** `junctions-r6` (0123) dotyka `hero_bridge.py` (auto-merge z landmarks) i `materials.py` (ten sam konflikt końca pliku); `buildings-r8` (0124) też `materials.py`. Kto scala później, powtarza unię.
- Brudne pliki w working tree main (`generated/*.json`, `generated/landmarks/viaduct_putry_underdeck.spec.json`, `props`) — zbackupować/cofnąć przed scaleniem landmarks (ten spec gałąź zmienia: −432 linie, usunięte schody).

Sugerowana kolejność: **truck r2 → light r2 → edge r3 → landmarks r2 (unia `materials.py`)** → jedna regeneracja świata + import + `WorldTruckInstaller.InstallBatch` → kamery kontrolne Low/High × clear/overcast na wspólnym stanie, **obowiązkowo g3-a 2948 i 303305 clear (klin)**.

---

## 1. edge r3 (zawiera r2) — SCAL · PARTIAL

r3 (apron/kurtyny) to poprawka liczbowa bez widocznego skutku; r2 (wysokości LoD1 w tle) realnie zmienia obraz. Oceniam obie, bo scalenie r3 = scalenie r2.

1. **r3 — wizualnie zero, liczby uczciwe.** 368 PNG: 364 z Δ<0,01 LSB; jedyne zmiany w `edge-nw-ground` (Δ 0,03 we wszystkich konfiguracjach) i śladowe w `edge-east`. `pairs/Low-overcast-edge-nw-ground.jpg`: przed i po nierozróżnialne. Raport sam nazywa to PARTIAL i nie ogłasza zamknięcia szwu — zgodnie z prawdą. Podstawy kurtyn >+0,05 m: Low 137→1, High 777→7; Python−Unity max +1,43→+0,89 m (rozbieżność zmalała, nie znikła).
2. **Kadr NW (P2, nie tej rundy):** płot panelowy na ciągłym betonowym cokole, pod nim jednolicie szara, gładka powierzchnia bez faktury, krawężnika i trawy — „podłoga sceny”. Z trasy niewidoczne, z kadru kontrolnego krzyczy „koniec mapy”.
3. **r2 — panorama południowa zmieniła się zauważalnie** (Δ 0,57–0,61, `edge-r2/pairs/Low-clear-edge-south.jpg` + natywny wycinek środka High-clear): za halą pojawiła się wysoka bryła z pomiaru LoD1 — **płaskie pudło: brązowa ściana, jaskrawo pomarańczowy pas pod dachem, zielony pas**, zero okien i faktury, ostre krawędzie. Dane są prawdziwsze (measuredHeight), ale im wyższe pudło, tym mocniej czyta się jako bryła z gry mobilnej 2016 (P1, docs/06 §2 — płaskie kolory). Granatowa hala po prawej obniżona — wiarygodniej. Wschód: subtelnie.
4. **Kadry trasy:** max Δ 0,13 (`sbs-g3-a-500263`, pod wiaduktem; obejrzany — bez artefaktu), `g3a-eye-s0262` 0,11. Bez regresji rozpoznawalności. **B9 (bloki na horyzoncie G3-A) nadal otwarty:** `edge-r3/pairs/photo-High-clear-sbs-g3-a-303305168125936.jpg` — na zdjęciu po lewej wieżowce osiedla nad linią drzew, w renderze tylko las. Diagnoza w `next-round-review/` (regionalne bloki 37–56 m w ~574–680 m wewnątrz kafla, nie far-field; okluzja niezweryfikowana) jest rzetelna i ostrożna — autor słusznie nie dubluje budynków.
5. **Testy:** EditMode 297/297, GIS 591 passed / 1 xfail / 0 failed (pełne powtórzenie po restarcie PC). r2 miał 2 failed (fidelity stale, determinism chunków) — w r3 zielono.
6. **Licencje:** LoD1 2024 GUGiK CC BY 4.0 w `docs/LICENSES.md` (`gugik-lod1-2024-2061`; far-field nadal `LEGAL_REVIEW_REQUIRED`). Bez nowych zasobów.

Następna runda (edge r4): (1) **klin far-field na chmurach** — merge main z light r1, maski Apron/FarField w 2948/303305 clear, ustalenie właściciela geometrii; (2) pudła LoD1 w tle: albedo z rozkładu elewacji zamiast jaskrawych pasów, pasy okien/kondygnacji w istniejącym UV0, mgła tonująca kontrast; (3) apron z bliska — faktura trawy/żwiru zamiast gładkiej szarości przy płocie NW; (4) B9 dopiero po (1).

## 2. landmarks r2 (podpomoście wiaduktu DK8/Putry) — SCAL warunkowo · PARTIAL

Warunek: ręczna unia `materials.py` (patrz konflikty) + zielony `test_viaduct_underdeck.py` i testy asfaltu po scaleniu.

1. **Usunięcie 69 stopni czterech niepotwierdzonych biegów schodów — dobrze.** Zgodne z „nie zmyślaj”; w `review/after-weather-from-before/Low-overcast-01.jpg` (biezenstwa-above, kabina) bez widocznej straty. Remiza, kabina, trasa identyczne (116/232 PNG pikselowo identycznych; reszta pod wiaduktem i szum).
2. **Filary: krok w bok, częściowo wstecz w kolorze (P1).** Natywne wycinki `review/pier-before|pier-after-weather/*-column.png` (Low-overcast, High-clear): przed — jednolita czysta żółć z czarnymi „pazurami” zacieków u góry (slop); po — ochra brudnobrązowa z szumem i **szerokim szarym pionowym pasem przez środek ściany** („szare fazy”). Na oryginale Commons 7204 (wycinek filarów z 5520×3680) filary są fazowane, ale **fazy są w tej samej musztardowej farbie**, różnią się tylko zacienieniem. Szary pas czyta się jak namalowany pas albo dziura w teksturze. Pigment po zmianie oddala się od musztardowej żółci zdjęcia (ROI 84/79/47 → 85/71/41 — mniej żółci, więcej brązu). Zniknięcie czarnych pazurów — plus.
3. **Ciemny równoległobok na filarze w połowie wysokości** — przed i po, wszystkie 4 konfiguracje; wygląda jak unoszący się decal. P2 do zbadania.
4. **Zdjęcie|render** `review/photo-after-weather/High-overcast-dk8-ref7204.jpg` vs `review/photo-before/…`: przy 960 px nierozróżnialne. Różnice wobec zdjęcia (nie tej rundy): na zdjęciu filary to masywne żółte bryły blisko jezdni i rura odwodnienia pod krawędzią pomostu; w renderze filary w cieniu, za ekranem; ekrany przy jezdni inne (domena Claude — autor to zgłasza). Poza UNVERIFIED.
5. **Budżet:** 116 Low: draws +0, instancje +0, tris −0,42 %…0 %; generator −906 tris. Bez nowych shaderów/przebiegów; dodatkowe próbki istniejących map na filarach (UNVERIFIED A16, mały udział ekranu).
6. **Testy:** 14/14 celowanych, GIS 585 + 1 xfail, EditMode 295/295; physics/gate3 47 + znana porażka `top_speed_flat_comb.json` (wejścia identyczne z bazą, `known-physics-failure-proof.json`) — nie z tej rundy, ale lider powinien ją mieć na liście.
7. **Licencje:** Rakoon 7204 CC0 w `docs/LICENSES.md` (l. 56). Bez nowych zasobów.

Następna runda (przed kominami): fazy filarów w tej samej musztardowej farbie (ciemniejsze tylko przez normalną/AO), pigment bliżej żółci zdjęcia, rura odwodnienia pod krawędzią pomostu, zbadać ciemny równoległobok.

## 3. light r2 (Night, odbicia nocne, reflektory opt-in) — SCAL · PARTIAL

1. **Dzień i Dusk nietknięte — sprawdzone w kodzie.** `WorldAtmosphere.DisplaySkyFog` zwraca wejście, gdy gain==1 i desaturacja==0; stare assety z polem 0 → gain 1; gałąź w `Sky.shader` za uniformem `_KamionSkyDisplay.z` (0 poza Night); `KamionHeadlampCone` za `_KamionHeadlampOn` (domyślnie off we wszystkich presetach). Klin far-field: **ani naprawiony, ani pogorszony** — runda nie renderowała dnia (uwaga ogólna).
2. **Noc wygląda jak dzień z ekspozycją −3 EV, nie jak noc (P1, docs/06 §2 — światło).** `final-route-v2/Low-night/{g3b-rondo-putry-approach, route-putry-approach, stretch-05-docks, truck-34}.png` i `reference-pairs/night-appearance-1.jpg`: trawa nadal nasycona zielona (brak desaturacji skotopowej), asfalt równomiernie szary na całej szerokości — **na trasie Putry nie widać plam światła pod latarniami**, głowice latarni prawie nie świecą, brak poświaty, okna budynków ciemne, niebo czarne bez łuny miasta; dok praktycznie czarny. Na zdjęciu (inne miejsce): pomarańczowe głowice z halo, wyraźne plamy, kontrast cień/światło, oświetlone witryny. Raport tego nie ukrywa.
3. **Usunięcie pomarańczowego zachodu odbitego w ekranie Putry i szkle przy czarnym niebie** — konkretna poprawka spójności (`ReflectionCubemap(skyPresentation)`).
4. **Ablacja −2…−5 EV** (`night-Low-driver-andersa-to-putry.jpg`): wybór −3 sensowny; −4/−5 gubi czytelność Low.
5. **Budżet:** 134 wpisy draws +0, tris +0 %. Koszt: gałąź uniformu w `KamionLampPools.hlsl` (wszystkie shadery świata z pulami) i w `Sky.shader`; reflektory po włączeniu 2× stożek ALU/piksel, bez okluzji. UNVERIFIED A16.
6. **Testy:** EditMode 276/276 (stara baza), GIS 523 + 1 xfail. Brak nowych zasobów; zdjęcia Rakoon CC0 tylko do porównań.

Następna runda (przed mokrą nawierzchnią): (1) **render dzienny clear na aktualnym main w 2948/303305**, jeśli lider go nie zrobi — klin to wspólny problem edge × light; (2) noc: desaturacja terenu, widoczne plamy pod latarniami na trasie Putry, emisja głowic + halo na Low bez nowego przebiegu, oświetlone wybrane okna (nieregularnie), łuna nad miastem; (3) reflektory: przybliżona okluzja, zanim staną się domyślne.

## 4. truck r2 (brud na stopniach) — SCAL · PARTIAL, wizualnie ~0

1. **Stopień: czytelna kratka zamiast szarej plamy.** `final-pairs/Low-overcast-truck-step-detail.jpg`: przed — dolny stopień jednolicie zabrudzony; po — perforowana kratka, wnęki dalej ciemne, bez halo. σ luminancji ROI 2,1→8,4 (Low-overcast). Opisane jako WORKING_VALUE.
2. **Cały kadr bez zmian** (`final-pairs/High-clear-truck-34.jpg`): kredowy, płaski biały lakier bez odbić, mleczna szyba, czysty dach i plandeka. Nadal „ciężarówka z gry mobilnej 2016” — stan main (FAIL z batch2), nie regresja.
3. **Zdjęcie|render** `photo-render-tractor-rear-working.jpg`: zdjęcie — blacha ryflowana z kurzem i rysami; render — idealnie regularne okrągłe otwory, czyste brzegi.
4. **Odrzucone próby** (zacieki plandeki, suchy plastik, krótszy rozbryzg) wycofane z obrazami i uzasadnieniem — dobra dyscyplina.
5. **Budżet:** 96 wierszy identyczne; build Android OK (0 błędów, 12 ostrzeżeń jak w r1). Koszt `normalize` + smoothstep na piksel nielakierowanych materiałów — pomijalny (UNVERIFIED A16).
6. **Testy:** EditMode 300/300; GIS 575 / 1 failed (`test_export_is_deterministic`, chunk 0_0 — jak w r1, nie z tej rundy) / 1 xfail.
7. **Licencje/marki (P2):** zdjęcia porównawcze CC BY 2.0 / CC BY-SA 4.0 z atrybucją w `references/CREDITS.md`, nie trafiają do gry — OK. Wycinek w `photo-render-tractor-rear-working.jpg` pokazuje jednak fragment litery logo producenta na chlapaczu — w dowodach przycinać bez marek.

Następna runda (opony/felgi wg autora): równolegle lakier (D44 0,49/0,53 → ≥0,7: odbicie nieba, clearcoat), szyba z odbiciem zamiast mleka, brud progów/błotników z pionowymi smugami (otwarte od r1), zużycie krawędzi kratki stopnia.

---

## Oceny 1–10 (stan po rundzie; w nawiasie zmiana vs main)

| Kategoria | edge r3+r2 | landmarks r2 | light r2 (Night) | truck r2 |
|---|---|---|---|---|
| Skala i proporcje | 6 (+0,5, wysokości LoD1) | 6 (0) | — | 6 (0) |
| Światło i ekspozycja | 6 (0) | 6 (0) | 3 noc (nowe; dzień 0) | 5 (0) |
| Materiały | 4 (0; pudła tła bardziej widoczne) | 5 (0: −pazury, +szary pas) | — | 4 (0) |
| Zużycie i osadzenie | 4 (0, apron NW) | 5 (+0,5 brud stopy) | — | 3,5 (+0,5 stopień) |
| Powtarzalność | 5 (0) | 5 (0) | 4 (jednolity asfalt nocą) | — |
| Realia PL | 5 (0, B9 otwarty) | 6 (+0,5, bez zmyślonych schodów) | 3 (brak plam latarni) | 5 (0) |
| Czytelność | 6 (0) | 6 (0) | 4 noc | 6 (0) |
| Artefakty | 5 (0; klin niezweryfikowany) | 5 (równoległobok) | 6 (+, odbicia zachodu usunięte) | 7 (0) |
| Budżet Low | 9 | 8 (próbki na filarach) | 8 (gałęzie uniformu) | 9 |

Wniosek: wszystkie cztery do scalenia; landmarks z warunkiem ręcznej unii `materials.py`. Żadna runda nie zmienia mierzalnie tego, co kierowca widzi na trasie G3 za dnia (max Δ trasy 0,13 LSB) — **pakiet nie przybliża bramki 3**. Bramkę nadal blokują: klin far-field na chmurach (niezweryfikowany od light r1; integracja s11 padła z 0xC0000142 przed vqa), B9 bloki na horyzoncie, pozy SBS i blokery geometrii G3-B. Po scaleniu: regeneracja + import + Truck InstallBatch + kamery Low/High clear/overcast z obowiązkowym kadrem g3-a 2948/303305 clear, pełny GIS, pomiar A16 Low.

Obrazy pomocnicze recenzenta (scratchpad sesji, poza repo): `e2_south_before|after.png` (panorama edge r2), `lm_pier.png` (filar ×4), `p7204_piers.png` (filary na zdjęciu), `night_low.png` (montaż nocy Low), skrypt `diff.py`.
