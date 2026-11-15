# ADR 0198 — podpory estakady A (rondo Putry): rzędy z `pier_lines_en` per pomost, kontrola kolizji z jezdnią
Status: Proposed (agent world-builder, s20, gałąź `piers-0198`, sesja w chmurze), 2026-11-15. Do scalenia przez lidera
po weryfikacji w Unity. Powiązane: ADR 0105 (underdeck Putry), 0123 (`pier_lines_en`), 0144 (`BLOCKED_COLS`),
0117 (bariery przy podporach), przegląd `docs/reports/REVIEW-2026-11-14-s20-mistral-m56-fix.md` (§3 P1),
badanie `research/mistral/p13-andersa-viaducts/` (P13).

## Kontekst
- Estakada A (E4) to dwa pomosty: NE (łańcuch `c:w1101181473`, ruch na NW) i SW (`c:w173956078`, ruch na SE).
  Podpory stawia reguła przęseł `hero_bridge.build_spec` (cel 25 m, przesunięcia ±10 m co 2 m, keep-out = maska
  nawierzchni ±2 węzły). Wynik w `generated/landmarks/viaduct_putry_underdeck.spec.json`: SW 5 rzędów i 3 pominięte
  (przęsło **94,8 m**), NE 7 rzędów i 1 pominięty (przęsło **48,8 m**, para **16,4 m**).
- Zdjęcia (P13-030 / P13-031, ESTIMATED): 7–9 rzędów na pomost, rytm regularny, brak długiego przęsła. Stacji rzędów
  zdjęcia nie podają; dokumentacja obiektu nie jest publiczna (P13-032/033 UNVERIFIED).
- Sesja bez Unity, bez `Data/raw`, bez `build_world`. Wycinków c027 / c022 nie ma w repo
  (`research/_incoming/` jest poza gitem) — użyto ich opisów z `manifest.csv` (P13-022, P13-027) i z przeglądu.

## Decyzja
1. **Rzędy autorskie per pomost.** `viaduct_underdeck.json` dostaje `pier_lines_en` jako słownik
   `{"<osm way łańcucha pomostu>": [[E, N], …]}` (punkt każdego rzędu na osi TEGO pomostu). Każdy pomost underdeck
   jest osobnym spec, więc płaska lista z ADR 0123 rzutowałaby każdy punkt na oba pomosty. Odczyt:
   `hero_bridge.underdeck_rows`; dalej działa niezmieniona gałąź ADR 0123 w `build_spec` (rząd stoi tam, gdzie go
   wpisano; kolumna na masce trafia do `BLOCKED_COLS`). Pomost bez klucza zachowuje regułę przęseł.
2. **Stacje (wszystkie WORKING_VALUE, w metrach od końca NW zakresu otwartego `s_open[0]`):**
   - NE, 8 rzędów: 24,39 / 48,78 (z reguły) / 82,5 / 106,0 (dwie krawędzie wyspy, wzór zmierzony na estakadzie B
     w ADR 0123) / 133,5 (za wschodnią jezdnią pierścienia) / 155,0 / 176,5 / 198,0. Przęsła 24,4 / 24,4 / 33,7 /
     23,5 / 27,5 / 4 × 21,5 m. Jedno szersze przęsło nad zachodnią jezdnią pierścienia zgadza się z c023.
   - SW, 6 rzędów aktywnych: 19,5 / 40,0 / 56,5 / 135,5 / 161,5 / 187,5. Przęsła 19,5 / 20,5 / 16,5 / **79,0** /
     26,0 / 26,0 / 25,8 m.
   - Źródła układu: liczba i rytm ze zdjęć; położenie względem jezdni z mapy nawierzchni generatora (skrypt z p. 4)
     i z ortofoto GUGiK WMS HighResolution (obejrzane 2026-11-15, nieprzechowywane poza dwoma podglądami w
     `artifacts/piers-0198/`). Słupy są na ortofoto zasłonięte pomostami — stacji nie da się z niego odczytać.
3. **Konflikt zgłoszony, jezdnia nieruszona (pomost SW, 62–133 m).** W wygenerowanym świecie południowo-zachodnia
   krawędź wyspy ronda leży pod osią pomostu SW: dla każdej stacji z tego zakresu jedna kolumna (±2,0 m od osi)
   stoi na asfalcie pierścienia albo na pierścieniu najazdowym (`apron_sett`). Na ortofoto prawdziwa wyspa sięga
   ok. 1,5–2,5 m poza południową krawędź pomostu SW na odcinku ok. 88–108 m (WORKING_VALUE, odczyt „na oko”,
   ±0,5 m), czyli krawężnik wyspy jest ok. 3–4 m dalej na SW niż krawędź asfaltu z generatora. Dwa rzędy wyspowe
   (86,0 i 111,0 m) zapisano w `pier_lines_en_held` — pole dokumentacyjne, generator go nie czyta. Po korekcie
   geometrii pierścienia / wyspy (osobne zadanie właściciela dróg) należy je przenieść do `pier_lines_en`; test
   `test_sw_deck_conflict_is_explicit` wtedy celowo pada, a skrypt wypisuje `FREE NOW`.
   Skutek dziś: przęsło SW skraca się z 94,8 do 79,0 m, ale **nie znika** — P1 z przeglądu jest zamknięte dla NE,
   dla SW tylko częściowo.
4. **Kontrola kolizji bez `Data/raw`:** `tools/worldgen/qa/check_piers_vs_roads.py`. Uruchamia etap dróg generatora
   (`roads.pipeline.build`) na płaskim modelu terenu (geometria w planie nie zależy od wysokości), liczy rzędy
   funkcją generatora `build_spec` i sprawdza każdą kolumnę: (a) keep-out generatora `hero_bridge.keepout` na
   rasteryzowanym śladzie warstwy dróg → `BLOCKED_COLS`, (b) odległość obrysu kolumny od powierzchni jezdnej
   (`road_*` + `apron_sett`, definicja z `furniture.pier_guardrails`) ≥ 0,5 m (WORKING_VALUE), (c) odległość od
   surowych poligonów placów ≥ 3,0 m. Wynik: `BLOCKED_COLS` pusty, najmniejsza odległość kolumny od jezdni 2,53 m.
   Wiarygodność emulacji: z regułą przęseł skrypt odtwarza scommitowany spec (te same rzędy, te same pominięcia,
   przęsła 94,78 / 48,78 / 16,39 m, zakresy otwarte co do 6 mm).
5. **Generator:** `hero_bridge.keepout` (jedna definicja keep-out, używa jej `build_world`), `column_points`,
   `chain_ways`; `hero_bridges.pier_cols_on_carriageway` w `streetscape_qa.json` obejmuje teraz także pomosty
   underdeck (dotąd lista była zapisywana przed ich przetworzeniem).
6. **Opisy sprzeczne z danymi poprawione** (`overrides.yaml`, `scripts/gate3-segment.py` + `gate3_segment.json`,
   `viaduct_underdeck.json`): słupy A — prostokątne fazowane z głowicą (P13-034), nie „round”; słupy B — przekrój
   stadium z czerwoną węższą ścianą (ADR 0144, P13-076/065), nie „cylindrical”; ekran pomostu SW estakady A —
   potwierdzony CC0 20221203_111814 (P13-040), nie „assumed symmetric (UNVERIFIED)”. Geometrii to nie zmienia.

## Konsekwencje
- Po `build_world` zmieni się spec `viaduct_putry_underdeck.spec.json` (14 rzędów zamiast 12, `params.pier_lines_en`),
  kolizje słupów i bariery przy podporach (ADR 0117: słupy SW stoją 2,5–4,2 m od jezdni równoległej, jak dotąd rzędy
  23,7 / 47,4 m). Budżet: +2 rzędy = +4 kolumny z głowicami i kolizją; draws/tris do zmierzenia przez lidera.
- Przęsło 79 m pomostu SW pozostaje widoczne z jezdni pod estakadą do czasu korekty pierścienia.

## Otwarte / niezweryfikowane
- Brak renderów kamer kontrolnych i porównania SBS (bez Unity) — pętla wizualna do wykonania przez lidera.
- Maska keep-out pełnego buildu zawiera też nawierzchnie placów i działek (`pmask`) — w chmurze sprawdzono tylko surowe
  poligony (najbliższy 67,8 m od kolumny). Rozstrzyga `pier_cols_on_carriageway == []` po `build_world`.
- Ścieżki piesze / rowerowe widoczne na ortofoto pod pomostami za wschodnią jezdnią pierścienia (ok. 135–150 m) nie
  istnieją w śladzie generatora; rzędy NE 133,5 i SW 135,5 mogą w rzeczywistości stać inaczej.
- Wyrównanie rzędów obu pomostów w jednej linii poprzecznej: nieznane, nie wymuszane.
- Czy prawdziwe rondo ma pierścień najazdowy przy wyspie pod pomostem SW: na ortofoto pas żwiru / ziemi, UNVERIFIED.

## Runda 2 (2026-11-15, gałąź `putry-ring-0198b`): konflikt pomostu SW rozwiązany w ADR 0216
Decyzja właściciela: poprawić geometrię ronda, potem dołożyć dwa rzędy. [ADR 0216](0216-rondo-putry-wyspa-z-ortofoto-apron-width.md)
koryguje krawężnik wyspy do ortofoto GUGiK i wpisuje rzędy pomostu SW na 89,0 i 109,0 m (rzędy 86,0 / 111,0 m z p. 3
stały poza jezdnią, ale w keep-out generatora). Pomost SW: 8 rzędów, max przęsło 32,5 m (było 79,0). `pier_lines_en_held`
usunięte; test `test_sw_deck_conflict_is_explicit` zastąpiony przez `test_sw_deck_conflict_is_resolved`.
