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
   daje więcej poziomów rozbryzgu). `facade_kit.wall_apron`: opaska z kostki 0,5 m wokół bloków, położona na terenie.
2. **Jeden typ balustrady na budynek (P1-b)** — `facade_atlas`: grupy wierszy `balcony_1/6/3` (blacha trapezowa
   biała, płyty włóknocementowe, szkło mrożone), po 2 wiersze (row atlas 14 → 16 wierszy); wpis „bal” niesie tylko
   wariant drzwi/okna. Typ budynku: para typów na osiedle (komórka 250 m), budynek bierze pierwszy w 70 %
   (≤ 2 typy na osiedle). LOD0: 12 % balkonów to wyjątki lokatorów (pręty ze skrzynkami, mata, blacha perforowana).
   Wypełnienia mniej nasycone (błękit 140/162/180 → 150/160/166, brąz i zielony stonowane).
3. **Dach wielopołaciowy (P1-c, P2-c)** — `roofs.MultiRoof`: rzut prawie prostokątny (krawędzie ±11°) rozkładany na
   prostokąty (siatka ze skupionych współrzędnych ścian, zachłannie największe pole, ≤ 4 części, części węższe niż
   1 m pomijane); każda część to dach dwuspadowy nad swoim prostokątem, skrzydło przy dłuższej ścianie głównej bryły
   ma kalenicę prostopadle i sięga do kalenicy głównej, kalenica skrzydła ≤ kalenica główna − 0,3 m. Dach = **górna
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
