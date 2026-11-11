# ADR 0097: Zabudowa r5 — dachy wielopołaciowe z koszami, jeden typ balustrady na budynek, zacieki pod parapetami, balkony na obu stronach, paleta domów wg sąsiadów

Status: propozycja (world-builder, gałąź `buildings-r5`, z main `0e73211a`), 2026-11-11. Kontynuacja ADR 0094; odpowiedź
na `docs/reports/visual/REVIEW-2026-11-11-s9-0094.md` („Następna runda (ADR 0097)” pkt 1–7; pkt 8 — zrzut z A16 —
robi lider).

## Kontekst
Recenzja 0094 (PASS warunkowy): bloki z 10–30 m to czyste bryły z naklejonymi oknami (P1-a), konfetti balustrad
(P1-b), skrzydło domu L wyższe niż okap z płaską opaską i ukośną belką (P1-c), gołe długie elewacje bloków (P1-d),
5/5 bliskich domów kremowe (P2-a), drzwi bez stopnia (P2-b), dwie barwy wiatrownicy (P2-c), pranie jak flaga (P2-d),
szczyt w słońcu przy klipie (P2-e), ząbkowana „maska” pod okapem (P2-f), cokół ~2,3 m jako jedna płyta (P2-g).

Rozpoznanie (baza = main `0e73211a` z ADR 0086, `artifacts/buildings-r13/base/`):
- Shader już ma tryb „pod parapetem” warstwy zacieków (ADR 0092: TEXCOORD_1.v ≥ 48 → linia brudu pod obróbką
  i gęstsze zacieki), ale generator zabudowy nigdy go nie używał — tynk bloków/domów miał tylko zacieki spod attyki.
- Konfetti = tabela wierszy `facade_far` „balcony”: każdy balkon brał wariant `balf` z wiersza (8 wariantów
  w jednym rzędzie), LOD0 czytał ten sam wariant.
- Skrzydło domu L: dach był jednym polem wysokości nad prostokątem otaczającym; rzuty „L/T/U” (fill < 0,6) dostawały
  dach płaski albo jedno pole, w którym ściana skrzydła rośnie pod połać.
- **P2-f to nie maska**: tekstura `parapet_runoff` jest gładka (`base/runoff_top.png`); ząbki pod obróbką attyki
  są piłą mapy cieni (High clear wyraźnie, Low overcast prawie wcale — `base/crop_fence2_lc.png`). Do renderingu.

## Decyzja
1. **Zużycie elewacji maskami (P1-a, P2-g)** — `buildings_mesh.wall_with_openings(sills=…)`: kawałek ściany tuż pod
   oknem (kolumna okna, od nadproża okna niżej do parapetu) dostaje TEXCOORD_1 = (u, 65 + głębokość / skala) — tryb
   parapetu shadera ADR 0092; skala długości 0,55–0,9 m na budynek (WORKING_VALUE). Bloki, biura, domy (nie drewniane).
   Filary między oknami bez zmian (zacieki spod attyki jak dotąd). `facade_kit.plinth_drip`: profil startowy
   ocieplenia nad cokołem, 3,5 cm przed licem, front + spód w ciemnej obróbce (spód patrzy w dół → linia cienia),
   przerwany na drzwiach. Cokół 0,20 → 0,24, strefa rozbryzgu 0,5 → 0,8 m (stały mnożnik shadera: jaśniejsza baza
   daje więcej poziomów rozbryzgu). `facade_kit.wall_apron` (opaska z kostki 0,5 m wokół bloków) jest napisana, ale
   **wyłączona** (`BLOCK_APRON = False`): położona na polu wysokości zapadała się pod siatkę terenu i wychodziła jasnymi
   łatami na skarpie (r2 `r10_block_5`).
2. **Jeden typ balustrady na budynek (P1-b)** — `facade_atlas`: grupy wierszy `balcony_1/6/3` (blacha trapezowa
   biała, płyty włóknocementowe, szkło mrożone), po 2 wiersze (row atlas 14 → 16 wierszy); wpis „bal” niesie tylko
   wariant drzwi/okna. Typ budynku: para typów na osiedle (komórka 250 m), budynek bierze pierwszy w 70 %
   (≤ 2 typy na osiedle). LOD0: 12 % balkonów to wyjątki lokatorów (pręty ze skrzynkami, mata, blacha perforowana).
   Wypełnienia mniej nasycone (błękit 140/162/180 → 150/160/166, brąz i zielony stonowane).
3. **Dach wielopołaciowy (P1-c, P2-c)** — `roofs.MultiRoof`: rzut prawie prostokątny (krawędzie ±11°) rozkładany na
   prostokąty (siatka ze skupionych współrzędnych ścian, zachłannie największe pole, ≤ 4 części, części węższe niż
   1 m pomijane); każda część to dach dwuspadowy nad swoim prostokątem, skrzydło przy dłuższej ścianie głównej bryły
   ma kalenicę prostopadle i sięga do kalenicy głównej, kalenica skrzydła ≤ kalenica główna − 0,3 m; pole części
   sięga 1,2 m poza jej prostokąt (ściany rzutu odchodzą od siatki). Dach = **górna
   obwiednia** części: max dwóch połaci zagina się w górę, więc kosz powstaje sam, a kalenica skrzydła ginie w połaci
   głównej. Kosze dostają pas obróbki 2 × 0,18 m. Gdy obwiednia nie pokrywa całego okapu (ściany za daleko od siatki)
   — dawny pojedynczy dach. Deska czołowa przy dachówce = materiał podbitki (`soffit_boards`): jeden kolor desek
   na budynek.
4. **Balkony na gołych elewacjach (P1-d)** — balkony na obu długich stronach każdego bloku ≥ 3 kondygnacji (było 25 %);
   powyżej 2. kondygnacji balkon bez bocznych poręczy (20 → 16 trójkątów).
5. **Przydział tonów domów (P2-a)** — `buildings_mesh.house_palette`: te same 4 tony ścian i 3 dachy, przydział po
   kolei (id): dom nie bierze ściany ani dachu dwóch najbliższych sąsiadów (≤ 40 m) i skłania się do innej rodziny
   (ciepłe beż/krem vs neutralne jasny/szary) niż czterech najbliższych; wagi ciepłe 45 % / neutralne 55 %.
6. **Stopień i próg, pranie (P2-b, P2-d)** — drzwi domu na wierzchu cokołu (cokół ciągły pod drzwiami), podest
   1,4 × 1,0 m + stopnie ≤ 0,18 m do terenu + próg; pranie na 12 % balkonów (było 30 %), na suszarce 0,5 m za
   balustradą, sztuki 0,25–0,55 m, stonowane kolory, przekrzywione.
7. **Ekspozycja clear (P2-e)** — w zakresie zabudowy tylko albedo kremu −8 % (alternatywa wskazana w recenzji).
   Ekspozycja presetu clear i pieprz High — otwarte dla renderingu (ADR 0098), nie ruszane.
8. Pliki wspólne: `materials.py` — tylko blok addytywny na końcu (krem, cokół, `splash_h`); `WorldPbrMaterials.cs`,
   shadery — bez zmian. Kontrakt `_Tint` ADR 0086 nietknięty.

WORKING_VALUE: skala zacieków parapetowych, wymiary kapinosu i opaski, 12 % wyjątków, komórka osiedla 250 m,
70/30, wagi palety domów, zasięg części dachu 1,2 m, min. część 1 m, kalenica skrzydła −0,3 m, wymiary podestu.

## Liczby (edytor; nic z telefonu)
Rundy: base (main) → r1 → r2 → r3 (= stan końcowy: r2 bez opaski). Dowody `artifacts/buildings-r13/<runda>/`.

| miara | base | r1 | r2 | r3 |
|---|---|---|---|---|
| balkony w regionie | 2369 | 3413 | 3413 | 3413 |
| domy: MultiRoof / dwuspad. / czterosp. / jednosp. / płaskie | 0 / 200 / 30 / 36 / 4 | 98 / 102 / 30 / 36 / 4 | = | = |
| region High: submeshe / mln tris | (r12 r3b: 4025 / 13,96) | 4025 / 14,04 | 4038 / 14,03 | 4025 / 14,02 |
| region Low: submeshe / mln tris | (r12 r3b: 3004 / 4,490) | 3006 / 4,489 | 3006 / 4,489 | 3006 / 4,489 |
| budżet Low, 57 kamer: draws | 16688 | 16683 (−0,0 %) | 16697 (+0,1 %) | 16683 (−0,0 %) |
| budżet Low: tris (maks. kamera) | 15117 k | +0,6 % (r10_block_2 +3,0 %) | +0,6 % (r10_block_3 +2,8 %) | +0,5 % (r10_block_2 +2,2 %) |
| cokół `r10_block_3` High overcast (sRGB) | 63,9 | 69,4 | — | 69,4 |
| rozbryzg cokołu, góra − dół pasa (luma) | 8,4 | 11,7 | 11,0 | 11,0 |
| szczyt `r10_house_2` High clear, średnio / p99 R | 232/221/193, 255 | 220/211/189, 253 | — | — |

- Paleta domów (270, `palette_stats.py`): ciepłe (krem + beż) 63 % → 48 %; najbliższy sąsiad z tą samą ścianą
  24 % → 0 %, z tym samym dachem 39 % → 1 %.
- Row atlas `facade_far`: 40,2 → 45,8 m wysokości, GPU (ASTC + mipy) High 4,95 → 5,64 MB, Medium 1,59 → 1,82 MB,
  Low 0,59 → 0,67 MB (+14 %).
- Tynk, cegła, niebo bez zmian (`measure.py`: szary tynk 128,0 / 131,9, cegła R/B 1,66).
- Testy: `pytest tests/gis` (r2) 380 passed, 1 xfailed; `test_buildings_r5.py` 10 testów. EditMode: 226: 223 passed, 3 failed — `TruckDoorGlassTests` × 3 (materiał ciężarówki, te same co w ADR 0091/0094; C# w tym zadaniu bez zmian).

## Samokrytyka (docs/06)
- **Bez `visual-critic` i bez telefonu** (zakaz subagentów; A16 robi lider). Oceny wyłącznie moje.
- **Zacieki pod parapetami są subtelne** (siła z shadera × 0,6 dla tynków — nie zmieniałem shadera ani importera);
  z 10–30 m czytelne pod oknami bloków, przy pełnym słońcu słabsze. Narożników nie dotknąłem.
- **P2-g tylko częściowo**: kapinos i rozbryzg tak; cokół 2 m na skarpie to dalej jedna płaszczyzna, opaska wyłączona.
- **MultiRoof** obejmuje 98 domów; rzuty bez prostokątnej siatki (± 11°) albo z dziurą w pokryciu zostają przy
  jednym polu (dawne zachowanie). Kosze oglądane tylko z kamer `r13_house2_*` i z wykresu `roof_plot.png`;
  część rzutów rozkłada się na 3–4 części z małymi daszkami nad uskokami ≥ 1 m — mogą wyglądać „rozdrobnione”.
- **Wyjątki balustrad 12 %** to reguła, nie dane; typy na osiedle z siatki 250 m, nie z granic osiedli.
- **P2-e**: krem −8 % zbił średnią szczytu o 12 poziomów R, ale p99 dalej 253 — reszta to ekspozycja clear (0098).
- **P2-f** zdiagnozowane jako aliasing mapy cieni od obróbki attyki, nie maska — nienaprawione (rendering).
- Opaska kosztowała +13 submeshy High (osobna siatka `buildings|sidewalk_paving`) i nie działała wizualnie — wyłączona.

## Otwarte / do decyzji lidera
- visual-critic + zrzut z A16 (pkt 8).
- Rendering (ADR 0098): ekspozycja clear, pieprz High, piła cienia pod obróbką attyki (P2-f, `base/crop_fence2_lc.png`).
- Opaska wokół bloków: wymaga wysokości siatki terenu (albo wycięcia terenu) — `BLOCK_APRON`.
- Cokół na skarpie: pas cokołu + ściana piwnicy (P2-g) — niezrobione.
- Po scaleniu: `build_all.py --only facade_atlas,facade_far` → `build_world` → `import-region`.

## Przewidywane konflikty
- `tools/worldgen/streetscape/materials.py`: tylko blok dopisany na końcu (krem, `plinth_dark` kolor i `splash_h`);
  konflikt tylko, gdy 0086/0098 też dopisują na końcu pliku albo zmienią `plinth_dark` / `plaster_cream` (moje
  przypisania w miejscu nadpiszą ich wartości — do uzgodnienia przy scaleniu).
- `tests/gis/test_world_v31.py` (`test_r3_materials` — `splash_h` cokołu 0,8; `test_far_plan…` — `is_bal`),
  `tests/gis/test_buildings_r4.py` (MULTI wyłączone w teście okapu, cokół 0,24, balkon 16 tris).
- `art-source/world/materials/materials_spec.json` (rozmiary facade_atlas / facade_far) — regenerowany plik.
- `WorldPbrMaterials.cs`, `WorldPBR.shader`, `WorldSurface.shader` — bez zmian.
