# Recenzja niezależna — pakiet C rund GPT (furniture r2, edge r4, light r3, cab r3, life r3) — s12

Data: 2026-11-12 · Recenzent: visual-critic (Opus), niezależny od autorów i ich self-review. Tylko odczyt (jedyny zapisany plik: ten).
Pytanie: czy każdą gałąź można **scalić do main** (`8b74c2c5`, po pakietach A i B). Kryteria jak w `REVIEW-2026-11-12-s12-gpt-batch-a.md` / `-batch-b.md`: (a) brak regresji rozpoznawalności trasy wg D51 i obrazu w kadrach trasy/kabiny, (b) Low draws nie rośnie, tris ≤ +2 %, (c) docs/06 — poprawa albo brak pogorszenia, (d) licencje/marki. PARTIAL dopuszczalny bez regresji.
Wszystko to render edytora. Żadna runda nie była na telefonie — koszt GPU A16 i kompilacja shaderów na Androidzie: **UNVERIFIED** dla wszystkich pięciu.

Metoda własna: `git merge-tree --write-tree main <gałąź>` (bez refów) i `git diff main <drzewo>` = zmiana netto; przegląd konfliktów w drzewach scalenia; własne pary przed|po i wycinki obszaru zmiany (furniture: `before/` vs `after/` `route-putry-entry-signs` Low/High clear + Low dusk, powiększenie znaków A-7/C-12 ×2; tekstury A-7, D-6, U-4a z LFS main vs gałąź; light: `edge-r4/before/*-clear` vs `light-r3/clear-final/*` dla 2948/303305 po przycięciu 13:6 → 16:9, wycinek prawego horyzontu; life: `before-preview` vs `after-c-preview` `life3_black_wheel2`); przegląd diffów kodu; rozmiar artefaktów wnoszonych do gita.

## Podsumowanie

| Runda | Werdykt | Jakość | (a) trasa D51 | (b) Low draws / tris | (c) anti-slop | (d) licencje |
|---|---|---|---|---|---|---|
| furniture r2 (zużycie lic, dystanse mocowań Low, odblask) | **SCAL warunkowo** (unia `materials.py`, `LICENSES.md`; generaty `--ours` + regeneracja) | PARTIAL; w dzień ~0, odblask nocą działa | bez regresji; **nie rusza blokera G3-B D-3/D-6 przy rondzie Bieżeństwa** (to geometria węzła, nie znaki) | +0 / max +0,19 % (165 kamer Low) | drobna poprawa krawędzi A-7; odblask bez „świecących tarcz” | OK (URP Companion License wpisana; bez grafiki producentów folii); BOM w LICENSES.md (P2) |
| edge r4 (diagnoza klina) | **SCAL** (ADR 0121 + lekkie dowody 0,3 MB) | NO-OP produkcji, diagnoza trafna | n/d | 0 / 0 | n/d | OK |
| light r3 (klin nieba; mokra droga odrzucona) | **SCAL** | P1 nieba naprawione; mokra droga FAIL (uczciwie) | poprawa: klin zniknął w 2948/303305, Low i High | +0 / +0 (122 obrazy) | usunięty twardy artefakt horyzontu; zostaje miękki szary pas | OK |
| cab r3 (podświetlenie legend) | **SCAL warunkowo** (dedup wpisu Brown Leather; **bez** `photo-night-reference-vs-render-960.jpg`) | PASS techniczny, efekt wizualny znikomy | bez zmian | 0 / 0 (78 + 42 kamery) | brak poprawy, brak pogorszenia | zdjęcie Volvo (prawa autorskie, logo) nie może trafić do gita |
| life r3 (felgi, czerń, tył osobówek) | **SCAL** (generaty `--ours` + regeneracja; unia `LICENSES.md`) | PARTIAL (zgadzam się) | bez regresji | +0 / max +0,068 % trasa (+0,32 % wszystkie) | felgi: mała poprawa; czerń nadal szary metalik; tył czysty | OK (referencje CC BY 2.0 tylko w artefaktach) |

### Konflikty `git merge-tree --write-tree main <gałąź>`
- **furniture r2**: 5 konfliktów.
  - `generated/streetscape_qa.json`, `generated/world_manifest.json`, `art-source/world/props/street_props.glb` (LFS) → `--ours` + regeneracja. Auto-merge `props_meta.json` → i tak regeneracja.
  - **`tools/worldgen/streetscape/materials.py` — UNIA ręczna.** Konflikt na końcu pliku (~l. 557): po stronie main blok ADR 0119 (`_underdeck_pier_paint`, `M["pier_yellow"]["color"] = …`, `_underdeck_pier_weather()`, `M["pier_yellow"].update(...)`); po stronie gałęzi `M["plate_back"] = {**M["plate_back"], "furniture_sign_fronts": {"gain": 800.0}}`. Zostawić **oba** bloki (najpierw main, potem furniture). Pozostałe hunki furniture (po `plot_lawn` ~l. 519, po `decal_oil` ~l. 557) łączą się automatycznie. Po scaleniu: `grep -n "_underdeck_pier_paint\|_underdeck_pier_weather\|furniture_sign_fronts\|furniture_plinth_detail\|road_asphalt" tools/worldgen/streetscape/materials.py` — wszystkie muszą być.
  - **`docs/LICENSES.md` — UNIA.** Main: „Kabina — skan skóry CC0 (Poly Haven), GPT cab r2”; gałąź: „ADR 0120 r2 — wariant materiału znaków oparty o URP Lit”. Zachować obie. Usunąć BOM (U+FEFF) dodany przez gałąź w 1. linii.
  - `WorldPbrMaterials.cs` auto-merge (hunki l. 7, 92, 146, 571 — rozłączne z life r3 l. 228).
- **edge r4**: czysto. Netto: `docs/adr/0121-background-horizon.md` (+23) i 49 plików artefaktów.
- **light r3**: czysto. Netto: `Sky.shader` (+5), `LightingPreset.cs`/`WorldAtmosphere.cs` (+4/+4), `LP_Clear.asset` (`clearCloudSourceMinElevationDeg: 0.5`), `ClearCloudsSource.json` (nota + `checked_utc` przepisany na +01:00 — ta sama chwila), narzędzia Editor (`LightQaBatch`, `LightQaLampProbe`, `WetCubeLab.cs/.shader`), ADR 0108 +22, `DuskStreetLampTests` +9.
- **cab r3**: 1 konflikt — `docs/LICENSES.md`. Main ma już wpis `brown_leather` (dopisany po pakiecie B); gałąź dodaje drugi, dłuższy „ADR 0112 — Brown Leather” z tabelą MD5. **Nie dublować**: zostawić wpis main, dołożyć do niego tabelę 4 × MD5 i zdanie o pochodnych `MI_Cab_Leather`/`MI_Cab_Plastic` z gałęzi.
- **life r3**: 5 konfliktów — `generated/fidelity_qa.json`, `generated/streetscape_qa.json`, `generated/world_manifest.json`, `street_props.glb` → `--ours` + regeneracja; `docs/LICENSES.md` → unia (main: Brown Leather; gałąź: „Life r3 — referencje analityczne (nie zasoby gry)”). `WorldPBR.shader`, `WorldPbrMaterials.cs`, `materials.py` (1 linia `flake_lift` w słowniku `M`, l. 175), `life_cars.py` — auto-merge.
- Między gałęziami: furniture i life dotykają `materials.py`, `WorldPbrMaterials.cs`, `LICENSES.md` — hunki rozłączne (materials: life l. 175 vs furniture koniec pliku; WorldPbrMaterials: life l. 228 vs furniture 7/92/146/571), więc druga z nich da konflikt najwyżej w `LICENSES.md` (dopisać sekcję) i w generatach. cab/light/edge nie mają wspólnych plików kodu z innymi.
- **Kod wymagający ręcznej unii: `tools/worldgen/streetscape/materials.py` (furniture r2, koniec pliku) oraz `docs/LICENSES.md` (furniture, cab — dedup, life).** Reszta konfliktów to generaty → `--ours` + regeneracja.

**Kolejność:** **edge r4 → light r3 → cab r3** (dedup LICENSES, bez zdjęcia Volvo) → **life r3** (`--ours` generaty, unia LICENSES) → **furniture r2** (unia `materials.py` + LICENSES, `--ours` generaty) → jedna regeneracja (materials → build_world → fidelity → import) + `WorldTruckInstaller.InstallBatch` → kamery kontrolne Low/High × clear/overcast + `sbs-g3-a-2948…`/`303305…` clear (potwierdzić brak klina na main) + `route-putry-entry-signs` dusk → **APK** (nowy `FurnitureSign.shader` = kopia URP Lit z pełnym zestawem `multi_compile`: czas kompilacji wariantów, rozmiar APK, SRP Batcher na Vulkan) → `device-metrics.ps1` na A16.

Wnoszone artefakty: furniture 30,2 MB (m.in. 3 × 0,8 MB `protected-geometry-*.json` — kopie pochodnych, wystarczą SHA; kopie `furniture-r1/24h/references-lamps/*.jpg` do 0,9 MB), life 7,2 MB (4 × 0,9 MB `*-all-camera-budget.json` dla A/B/C/D — wystarczy C), cab 3,5 MB, light 0,7 MB, edge 0,3 MB.

---

## 1. furniture r2 — SCAL warunkowo · PARTIAL

1. **Co faktycznie widać.** Moje powiększenie `route-putry-entry-signs` (przed|po: Low-clear, High-clear, Low-dusk): A-7 i C-12 przy wjeździe na rondo Putry w kadrze gry nierozróżnialne; średnie |Δ| 0,005–0,02 LSB, tylko na licach. W teksturze źródłowej (`A-7.png`, 256 px) zmiana jest realna: przed — rozmyta, ciemna obwódka czerwieni (wyglądała jak poświata), po — ostra krawędź z delikatnym, lokalnym zmatowieniem. D-6 i U-4a praktycznie bez zmian. To kosmetyka, nie zmiana czytelności na Low.
2. **Odblask** (`night-preview/after3-low-25.jpg`): B-33 „70” z 25 m czytelny tylko dzięki odpowiedzi na światła mijania, reszta kadru ciemna — tak to wygląda w realu. Bez halo i bez „stale świecących tarcz” w dusk (moje Low-dusk: lica przyciemnione, bez emisji). Zgodne z docs/06. EV100 5, gain 800, odcięcie — WORKING_VALUE, uczciwie opisane.
3. **Tył znaku** (`baseline-detail/after3-Low-overcast-furniture-sign-back.jpg`): szara tarcza z naklejką, dwie obejmy. P2: tarcza płaska, za jasna i jednolita — prawdziwy tył to ocynk z wywiniętym rantem i profilem usztywniającym (ciemniejszy pierścień przy krawędzi). Obejmy zlewają się ze słupkiem.
4. **G3-B (rondo Bieżeństwa D-3/D-6) — runda tego nie rusza.** D-3/D-6 są zablokowane brakiem wysepki z przejściem w geometrii węzła (`REVIEW-2026-11-12-s11-0125.md` §2). Furniture r2 nie przybliża G3-B — nie zaliczać w HANDOVER jako postępu tego blokera. Para zdjęcie|render `reference-sign-Low-after3.jpg` (297817): poza B niezgodna (w renderze bramownica blisko, na zdjęciu jej nie ma, inna oś jezdni) — nic nie dowodzi, autor to przyznaje.
5. **Budżet:** CPU DrawEst mesh/instancje/cienie +0 na 330 wariantach; Low tris max +0,19 %; geometria chroniona 6833→6833; import Low 120,7→120,8 MB.
6. **Ryzyka techniczne (P1 przy integracji, nie blokują scalenia):**
   - `FurnitureSign.shader` to kopia URP Lit z pełnym zestawem `multi_compile` (cienie, additional lights, probe blending/box/atlas, SSAO, dbuffer, light cookies, SH). Nowa rodzina wariantów w APK i osobny shader dla wszystkich lic znaków. „Draws +0” to estymata widoczności CPU, nie liczba partii SRP Batchera. Lider: log buildu (liczba wariantów), Frame Debugger, A16. Rozważyć stripping do zestawu z tierów.
   - `FurnitureRetroSource.BeginCamera`: gdy w scenie nie ma `TruckLights` albo brakuje któregoś z 4 socketów, co 1 s wywołuje `FindAnyObjectByType` + `GetComponentsInChildren<Transform>` (alokacja), a przez 2 s po zmianie sceny — przy każdym renderze kamery. Ciężarówka ma `LIGHT_HighBeam_*` w manifeście, więc w jeździe zero GC; P2: sceny bez ciężarówki (menu, WorldC bez instalatora) alokują co sekundę. `[InitializeOnLoadMethod]` wpina hook globalnie w edytorze.
7. GIS 644 / 1 fail (stare hashe fidelity — zniknie po regeneracji) / 1 xfail; EditMode 340/340; FurnitureSignTests 16/16; physics/gate3 48/48.

Oceny (1–10): skala/proporcje 7 · światło 6 · materiały 6 · zużycie/osadzenie 5 · powtarzalność 6 · polskie realia 8 (A-7 żółte z czerwonym obrzeżem, C-12, B-33 zgodne z rozporządzeniem) · czytelność Low 6 (bez zmian) · artefakty 7.

## 2. edge r4 — SCAL · NO-OP produkcji (sprawdzone)

1. Zmiana netto = ADR 0121 (+23) i artefakty. Diagnoza klina poprawna i niezależnie potwierdzona przez light r3 (twarda granica dolnej półsfery fotografii chmur po obrocie; maski far-field/apron go nie obejmują). Słusznie nie ukrywano artefaktu kolorem/wysokością edge.
2. **Wysoka bryła LoD1 bez okien** (`south-baseline-review.jpg`, środek-lewo nad lasem: brązowo-pomarańczowa płaska hala) — **nadal jest**. Plan r5 trafny: reguła `h ≥ 22 → elektrociepłownia` w `far_field.py` barwi każdą wysoką halę jak EC, a losowy akcent zajmuje 16 % wysokości. Kolor z reguły zamiast ze źródła = typowy slop generatora — P1 r5.
3. **Apron NW / styk kurtyn** — nie ruszony, backlog r5 (Low 1 / High 7 wierzchołków > +0,05 m). P2 wobec hali.
4. Errata r3 (render 13:6 vs zdjęcia 16:9/4:3) — dobra praktyka; pary r3 traktować jako poglądowe.

Oceny (stan main w kadrze edge-south): skala 6 · światło 5 · materiały 4 · powtarzalność 5 · polskie realia 5 · czytelność 6 · artefakty 5 (hala).

## 3. light r3 — SCAL · P1 nieba naprawione, mokra droga FAIL

1. **Klin usunięty — sprawdziłem sam.** Wycinek prawego horyzontu `sbs-g3-a-2948595898752384` Low-clear: przed — twardy, ukośny, ciemnoszary pas nieba od środka kadru w prawo, rosnący nad halami (jak doklejona zła tekstura); po — ciągłe niebo nad halami. To samo High i 303305. Mechanizm: clamp elewacji próbkowania mapy chmur do +0,5° po obrocie, opt-in tylko w `LP_Clear.asset`; inne presety 0 = stara ścieżka. Mała, czysta zmiana bez nowej tekstury i przebiegu.
2. **Pozostaje (P1 light r4):** `native-review/sky-v2-Low-p0.jpg` — miękki, ciemnoszary pas tuż nad horyzontem (yaw 0–135, 270–315) i ciepły beżowy pas (yaw 180–225); czyta się jak smog przemysłowy. Na zdjęciach trasy (picturehoover 2948, zsolt 297817) dół nieba jest jasny, bladoniebieski. Na Low prawa dolna część nieba w 2948 nadal szara. D51 tego nie blokuje, ale to najbardziej widoczna różnica render|zdjęcie w kadrach G3-A.
3. Zweryfikowane dla słońca 42°. Obrót mapy zależy od pozycji słońca — inne kąty **UNVERIFIED**; po scaleniu sprawdzić 2948 przy ≥ 2 innych kątach.
4. **Mokra droga — odrzucenie słuszne.** Warianty dały „ciemny owal 8–12 m” albo globalne jasne wygładzenie zamiast odbić — obie czerwone flagi docs/06 (lustro/plastik z generatora). P2: `WetCubeLab.cs/.shader` zostają w `Rendering/Editor/` (poza buildem), a raport mówi „usunięto cały mechanizm” — doprecyzować w ADR 0108, że lab zostaje jako narzędzie.
5. Budżet +0/+0 (122 obrazy); EditMode 310/310; GIS 576 / 1 xfail, exit 0.

Oceny (kadry 2948/303305 clear): skala 7 · światło 6 (z 4) · artefakty 7 (z 4) · czytelność 7.

## 4. cab r3 — SCAL warunkowo · PASS techniczny, efekt ≈ 0

**Warunki:** (1) dedup wpisu Brown Leather w `LICENSES.md` (patrz konflikty); (2) **nie wnosić do gita `artifacts/cab-r3/photo-night-reference-vs-render-960.jpg`** — to zdjęcie Volvo Trucks z prawami autorskimi i widocznym logo na kierownicy. Autor sam pisze „nie jest CC0”; CLAUDE.md §8. Zostawić link w `artifacts/cab-r2/NIGHT-REFERENCE.md`, plik trzymać lokalnie poza gitem.

1. **Wizualnie prawie nic.** `backlight-details-Low-960.jpg` (Low dusk, kierownica i panel centralny): przed|po nierozróżnialne; pomiar autora 27,0→27,3 kodu luminancji w ROI. Dusk = słońce −5°, kabina w świetle dnia; podświetlenie ma sens w nocy, której model nieba nie pokazuje (kończy się na −8°). Para Volvo (pełna noc, świecące legendy i zegary) vs render High dusk (dzień z pomarańczowym niebem) nie porównuje tego samego stanu.
2. Implementacja poprawna i tania: lokalny keyword tylko na paśmie ikon (UV v < 0,5), szwy/korpusy bez emisji (test GPU: ikona 0,0588, szwy 0), wyłączenie zeruje. 0/0/0/0 na całej macierzy; EditMode 301/301; GIS 576 / 1 xfail, exit 0 (w tym `test_export_is_deterministic` — porażka z cab r2 się nie powtórzyła; lider niech potwierdzi na czystym main po integracji).
3. **Prawdziwy problem tych kadrów: ikony na Low to rozmyte białe kleksy** (kierownica i panel). To nie podświetlenie, tylko mipy/rozdzielczość pasma Decal na Low — P1 cab r4 (mip bias albo atlas ikon 2× tylko dla tego materiału).
4. Otwarte z pakietu B bez zmian (zgodnie z raportem): tworzywo = tłoczenie skóry (pomięty skaj), brak wytarcia kontaktowego, pasmo AO deski.
5. Napis „TRAKT” na piaście — fikcyjny znak projektu, OK.

Oceny: skala 7 · światło 5 · materiały 5 · zużycie 3 · czytelność Low 4 (ikony) · artefakty 6.

## 5. life r3 — SCAL · PARTIAL (zgadzam się z autorem)

1. **Felgi** (`life3_black_wheel2` przed|po, High-clear): ramiona dostały fazy, odlew czyta się nieco lepiej; nadal płaskie, jasne, szerokie ramiona bez głębi, bez środka/śrub, dół opony kanciasty. Poprawa mała, prawdziwa.
2. **Czerń — nadal FAIL.** `refs/sbs-black-c.jpg` i `rear-detail/compare-black.jpg`: „czarne” auto w clear to średnioszary/grafitowy metalik (zdjęcie Mapillary: granat-czerń z ostrymi, kontrastowymi odbiciami nieba). Na High-clear gruboziarnisty szum płatków na całym boku — czyta się jak **papier ścierny**, nie lakier (docs/06: szum zamiast materiału). ROI 0,97→0,92 to kosmetyka. P1 r4: brakuje ciemnego odbicia otoczenia (ADR 0089, pionowe odbicia), a nie niższego albedo.
3. **Tył** (`refs/sbs-tail-c.jpg`, biały kombi High-overcast): czysty jak z salonu; referencja z brudem po trasie nieosiągnięta (autor to przyznaje). Tablice `BMN 655YR`, `BI 19136` z polem UE — polski format, wiarygodne.
4. **Artefakt (P1, stan sprzed r3, widoczny w dowodach):** pod autem (`sbs-black-c.jpg`, `life3_black_wheel2`) ostry, ciemny prostokąt między kołami — płyta cienia/podwozia o twardych krawędziach; na zdjęciu cień jest miękki i zgodny ze słońcem. Wygląda jak blob shadow z 2012.
5. **Uwagi pakietu B dla naczep placowych** (felgi/opony LOD0 naczep, barierki, zderzak, plandeka) **nie zrealizowane** — r3 zajęła się osobówkami; NEXT-R4 zapowiada koła placowe. Nie oznaczać tamtych uwag jako zamkniętych.
6. Budżet: draws +0/+0; trasa Low max +0,068 %, High +0,155 %; wszystkie kamery Low +0,32 %; biblioteka +960 tris. EditMode 323/323; GIS 640 / 1 xfail, exit 0. Shader: `deposition` przeniesione przed gałąź, tylko ALU, bez nowego próbkowania.
7. Licencje: referencje Schechter / Stojkovic CC BY 2.0 z atrybucją, tylko w artefaktach; logo producenta na zdjęciu referencyjnym nie trafia do gry.

Oceny: skala/proporcje 6 · światło 5 · materiały 3 (czerń, szum płatków) · zużycie 3 · powtarzalność 4 (flota) · polskie realia 7 (tablice) · czytelność 6 · artefakty 4 (prostokątny cień).

---

## Uwagi do następnych rund GPT

- **furniture r3:** przystanki/wiaty/kosze/słupki — zgoda; dodatkowo tył tarczy z rantem i profilem, obejmy kontrastowe wobec słupka; stripping wariantów `FurnitureSign`; D-3/D-6 ronda Bieżeństwa należą do węzła — przygotować tylko lica/słupki na moment, gdy wysepka powstanie.
- **edge r5:** hala LoD1 na panoramie południowej — kolor z funkcji/źródła, nie z `h ≥ 22`; podział fasady; potem kontakt kurtyn.
- **light r4:** dolny pas nieba (szary/beżowy „smog”) vs bladoniebieski dół na zdjęciach G3-A; clamp przy innych kątach słońca; spójność Low/High po merge.
- **cab r4:** czytelność ikon na Low (mip/atlas), skan tworzywa zamiast tłoczenia skóry, wytarcie kontaktowe, pasmo AO; prawdziwy test nocny przed kolejnym ruszaniem podświetlenia; zdjęcia z logo poza gitem.
- **life r4:** czerń przez odbicie otoczenia, nie albedo; szum płatków na clear; miękki cień kontaktowy zamiast prostokąta; zaległe naczepy placowe z pakietu B.
- Wszystkie: GPU A16 i kompilacja shaderów na Androidzie UNVERIFIED — po integracji pakietu C: APK (warianty `FurnitureSign`) + `device-metrics.ps1` na A16 (telefon odblokowany).
