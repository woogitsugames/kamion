# ADR 0144: Węzły r7 — jeden system barier na krawędzi pomostu, zakończenia taśm, rzędy filarów z danych, kruszywo i spód pomostu

Status: w toku (world-builder, gałąź `junctions-r7`, baza main e79c5cc3 + scalony main 70b67fc7 z ADR 0143 / 0139), 2026-11-12.
Wynika z `docs/reports/visual/REVIEW-2026-11-12-s14-0123.md` (P1-1, P1-2, P2-3…5) i `REVIEW-2026-11-12-s14-0128.md` (P1-2)
oraz z „world findings” 4–5 ADR 0143. Powiązane: ADR 0123 (bariery r6), 0128 (nos wysepki), 0117, 0110, 0067 (wiadukt hero),
0060 (`sky_occ`). Dowody: `artifacts/junctions-r7/` (STATUS.md, `logs/`, `ortho/`, `plan_r7c/`, `renders_r7c_low_{clear,overcast}/`,
`pairs_r7c/`, `scripts/`). Build `m1` = main zregenerowany w tym worktree (baza liczb generatora); rendery „przed”: `b7`
(kamery węzła, `artifacts/junctions-r6/renders_b7_*`), `i3` (SBS, `artifacts/biezenstwa-island/renders_i3sbs_*`) i pozy ADR 0143
(`artifacts/sbs-poses-r3/after/renders/`, kadr 4:3).

## Kontekst (zmierzone przed zmianą)
1. **`p0_kerb_merge_eye` (P1-1)** — w wyeksportowanym świecie m1 (`scripts/steel_plot.py`, `dbg_rails.py`):
   - „istniejąca poręcz” to generyczna balustrada pomostu (`roads.meshing.build_bridge_extras`, 0,15 m od krawędzi kapy), a „nowa
     taśma” to bariera pomostu z 0123 (słupki 0,2–0,4 m od tej samej krawędzi). Dwa systemy 0,1–0,3 m od siebie stoją na KAŻDYM
     pomoście generycznym; na 12-metrowym pomoście łącznicy `c:w240542867` linia bariery skacze o 0,5 m między stacjami
     (N 77,51 → 77,02), więc taśma przecinała słupki balustrady na całej długości (~10 m).
   - zachodni koniec tej bariery (E −750,0 N 77,45) nie miał kontynuacji: szyna autorska `dk8-ramp-split-barrier-n` kończyła się
     2,4 m dalej (E −752,3), a `term` na końcach pomostowych był ignorowany — belka kończyła się w powietrzu.
   - szyny autorskie separatora stały na rastrze 1 m (`zsurf`), który miesza wierzch wyspy z jezdnią: stopa 140,15–140,2 przy
     kostce wyspy 140,85 (góra taśmy 0,10 m nad kostką); południowa szyna na ostatnich 3 m schodziła do 139,2 (trawa między końcem
     wyspy E −753 a pomostami E −750…−751; ortofoto 0,08 m: wyspa dochodzi do dylatacji przy E −752).
   - „białe kwadraty” = płytki stóp słupków pomostowych: poziomy ocynkowany quad (metal 0,9) odbija niebo.
2. **Filary (P1-2)** — źródła sprawdzone:
   - OSM (`podlaskie-261108.osm.pbf`): 0 węzłów `bridge:support` w oknie E 400…700, N −800…−620 (`logs/osm_supports.txt`);
   - BDOT10k 2061: `OT_BUIN_L` ma dwie linie „estakada” po **196,0 m** (E 466,6 N −675,6 → E 638,7 N −769,3 i równoległa) —
     to potwierdza przyczółki modelu (zakres otwarty pomostu prowadzącego 196,25 m, E 466,0 N −676,3 → E 638,2 N −770,4, różnica
     ≤ 1,1 m); podpór BDOT10k nie zawiera (`OT_BUIT`, `OT_BUWT` w oknie: dystrybutor paliwa, słup energetyczny);
   - ortofoto GUGiK 0,08 m (`ortho/via_all.jpg`, `via_nw.jpg`, `via_se.jpg`): pomosty zasłaniają podpory, cień pada pod pomost;
   - zostają klatki Mapillary (richlv, CC BY-SA 4.0, tylko odczyt geometrii): 2818555625124739 i 3970163613102941 pokazują
     **cztery** rzędy filarów między wyspą a ścianą przyczółka (rząd na wyspie + trzy), model miał trzy (przęsła 35,6 / 24,5 /
     24,5 m — luka z recenzji to przęsło 35,6 m). Pierwsze przęsło z 2818 (namiary dwóch kolumn bliższego pomostu w rzędach 1 i
     2, poza `sbs_cameras.json`; kierunek kamery z dopasowania 263,2° wobec 262,1° w pliku): 19,8 m ± 2 m.
   - kształt: na 178689077481862 / 177786140912399 / 3970163613102941 filar jest owalny (zaokrąglone czoła), czerwony pas na
     czole zajmuje ok. połowy widocznej szerokości; stosunek czoło : bok po zdjęciu skrótu perspektywicznego 1 : 2,0–2,4 (dłuższa
     oś WZDŁUŻ mostu); względem wysokości filara w modelu (4,3 m) przekrój ≈ 0,5–0,75 × 1,1–1,6 m. Kolumny jednego pomostu stoją
     3,8 m od siebie (178689, dwa promienie do stóp) / 3,6–5,4 m (2818) — w modelu 2,6 m.
3. **Materiały (P2)**: `island_gravel` 0,30 / 0,285 / 0,26 (liniowo) na zestawie `gravel_compacted` w kaflu 4 m — jeden materiał dla
   nasypu wyspy i nosa wysepki 0128. Spód pomostu: `viaduct_concrete` z domyślnym `sky_occ` [0,5, 0] — ściany skierowane w dół
   dostają dolną półkulę sondy nieba (ciemna, zielonkawa) przyciemnioną o połowę.

## Decyzja
1. **Jeden system na krawędzi pomostu** (`streetscape.furniture.drop_parapets_at_barriers`, `PARAPET_BARRIER_MIN_M` = 1,0 m): trójkąty
   generycznej balustrady (`<chain>:parapet`) bliżej niż 1 m od bariery pomostowej (taśma W + górna belka na 0,98 m = bariero-
   poręcz) są usuwane. Wiadukt hero zachowuje balustradę z assetu (osobna poręcz za barierą jest na zdjęciu 454716650857984).
   Reguła „dwie taśmy W < 1 m” dla biegów z reguł istniała (dedup 1,0 / 2,5 m) — teraz pilnuje jej test na danych regionu.
2. **Wolny koniec bariery pomostowej jest odginany do gruntu** (`_mark_free_deck_ends`, `guardrail(term_tall=…)`): koniec biegu na
   pomoście, przy którym w promieniu 2,5 m (i ±0,8 m wysokości) nie zaczyna się inny bieg, dostaje zakończenie jak koniec
   gruntowy (4 m, `GUARDRAIL_TERMINAL_M`); końce z anulowanym zakończeniem (połączenia, `free_ends`) bez zmian.
3. **Bez płytek stóp** pod słupkami pomostowymi (−2 trójkąty na słupek).
4. **Skok linii słupków w jednym biegu** (> 0,2 m między stacjami) jest wygładzany na 5 m.
5. **Szyny autorskie**: stopa na dokładnym wierzchu siatek (`SurfaceTop`, max z rastrem), krótkie dołki (< 8 m, > 0,25 m) i spadek na
   końcu biegu są mostkowane (`_bridge_dips`). Dane: wyspa `dk8-ramp-split-island` dostaje języczek do E −751,3 (między początkami
   pomostów), `dk8-ramp-split-barrier-n` jest dociągnięta do pierwszego słupka bariery pomostu łącznicy (E −750,1 N 77,35 —
   współrzędne wygenerowanego świata, do ponownego odczytu, gdy generator przesunie pomost).
6. **Rzędy filarów**: `pier_lines_en` = 8 rzędów zamiast 6. Rząd na NW krawędzi wyspy bez zmian (ADR 0123); od niego do
   przyczółka (84,7 m) 4 równe przęsła po 21,2 m; połowa SE przez symetrię konstrukcji (WORKING_VALUE — żadna otwarta klatka nie
   patrzy wzdłuż tej połowy): rząd wyspy przesunięty 1,5 m do środka ronda (w ramach ±2 m z 0123; inaczej zewnętrzna kolumna
   stała na krawężniku wyspy, `scripts/cols_check.py`), przęsło główne 26,4 m, dalej 4 × 21,3 m.
7. **Filary owalne**: `col_shape: stadium`, 0,70 m w poprzek × 1,40 m wzdłuż, kolumny ±1,75 m od osi pomostu (było: fazowane
   0,8 × 1,0 m, ±1,30 m); czerwony pas na czołach z tego samego pasa atlasu (`make_viaduct.py`: łuk 1 : 1 przez 0,30 m po obu
   stronach osi czoła). Wszystkie wymiary WORKING_VALUE ± 0,2 m (kolumny ± 0,4 m). Kolizja = prostopadłościan 0,70 × 1,40 m.
8. **Kruszywo**: `island_gravel` albedo ×1,30 i cieplej (0,41 / 0,37 / 0,318), `set_tile_m` 7 m (ziarno ×1,75; nowy klucz
   manifestu). Żwir nosa wysepki (`roads.gores`, wierzch `island_gravel` wyspy autorskiej) niesie COLOR_0.r = 1 → `vertex_grime`
   0,31 / 0,265 / 0,218 × ton 0,76 ≈ 0,72 × dawne albedo, brązowiej; COLOR_0.g = waga chwastów (1 przy krawędzi żwiru → 0 w
   0,9 m) → `vertex_weed` w Kamion/World PBR (dwie oktawy szumu 0,35 / 0,12 m, bez nowej tekstury i bez nowego draw calla).
   Nasyp wyspy pisze COLOR_0 = 0.
9. **Spód pomostu**: `ground_bounce` [0,42, 0,41, 0,39] na `viaduct_concrete` (+ `sky_occ` [0, 0]): dla normalnych skierowanych
   w dół światło otoczenia = naświetlenie płaszczyzny poziomej × albedo podłoża × współczynnik widoczności, zamiast dolnej
   półkuli sondy. Model roboczy (bez składowej słońca odbitej od jezdni), wartość WORKING_VALUE.

10. **Tablica F-10 przy 482392** (ADR 0143, pkt 4): `gate3_sign` `biezenstwa-f10-north` w E 515,8 N −680,3, czoło do ruchu o
    kursie 299°. Potwierdzenie w źródłach otwartych: dwie klatki jednej sekwencji Mapillary (richlv 482392746429891 i
    320326319617139, 2020-08-15: niebieska tablica „prosto | w prawo” z linią przerywaną, dwa słupki, za barierą); promienie z
    póz ADR 0143 przecinają się przy E 514–519 N −681, a ortofoto 0,08 m ma w pasie trawy obiekt z cieniem w E 515,8 N −680,3
    (`ortho/board482_r7c.jpg`), 6 m na północ od krawędzi pomostu. Szacunek z 0143 (E 495 N −676) był 21 m dalej, pod pomostem.
    Nowa twarz `F-10` w `streetscape.gate3_landmarks` (własny rysunek, 0,90 × 0,55 m, dwa słupki ±0,3 szerokości) — oznaczenie,
    wymiar i dolna krawędź 2,0 m WORKING_VALUE; stan po 2020 r. UNVERIFIED.
11. **„Pas zjazdu idzie zygzakiem”** (zgłoszenie właściciela, film z Folda 2026-11-12, t 17–19 s; `artifacts/owner-feedback/
    2026-11-12-fold-video/ramp_zigzag_19…22.jpg`): to łącznica do Ronda Putry tuż za rozwidleniem z Andersa (E −345 N −133,
    łańcuch `c:w173956083:2840742310-1852129066`, stacje 161–178; wysięgnik p37 w kadrze). Przyczyna: węzły profilu autorskiego
    `putry-link-fork-placement` (ADR 0095/0100) przy t 0,15–0,37 — odczyt „6,0 m z pasem P-21” i środki pasa przy N −138 / −135 —
    przesuwały OBIE krawędzie o 0,9–1,4 m na NE na odcinku 12 m i z powrotem: krawężnik NE wychodził 0,6 m na trawnik (stacje
    161–171) i cofał się 1,4 m w pas (172–178), krawężnik nosa wyspy miał garb 0,9 m (`scripts/zz_edges.py`, `zz_net.py`).
    Na ortofoto 0,08 m granica asfalt / ściek betonowy po stronie NE jest jedną gładką linią (przekroje jasności co 6 m,
    `scripts/zz_ortho_edge.py`; ±0,15 m). Węzły t 0,154–0,704 dopasowane na nowo (`scripts/zz_fit.py`): krawędź NE po tej
    granicy, krawędź SW po linii, którą miała poza garbem; odchyłka od celu ≤ 0,08 m, nachylenie krawędzi względem osi ≤ 0,14
    (było: skok 1,4 m na 6 m). Szerokość jezdni łącznicy na tym odcinku 4,3–5,3 m (było 4,4–5,4 m z garbem). To poprawka danych
    (override), nie reguły: generator odtwarzał profil wiernie; `smooth_1d` 2,5 m nie maskuje błędnych węzłów i tak ma zostać.
    Kamera kontrolna `r7_exit_zigzag_eye` (`junctions_cameras.json`).
12. **Księgowanie poręczy wiaduktu hero**: trójkąty balustrady zdjęte przy barierach (pkt 1) są liczone do
    `generic_tris_removed.parapet` wiaduktu hero (`buf.parapet_dropped`), bo budżet assetu („nie więcej trójkątów niż dekoracja,
    którą zastępuje”, `test_hero_bridge`) porównuje z całą zastąpioną dekoracją. Pkt 1 w praktyce zdejmuje balustradę także z
    łańcuchów hero (bariera pomostowa biegnie tam < 1 m od niej) — geometria końcowa ta sama, bo asset niesie własną poręcz.

## Pliki wspólne (addytywnie)
- `game/`: `Environment/Shaders/WorldPBR.shader` (`_VertexWeed`, `_GroundBounce`), `World/Import/RegionImporter.cs` (klucze manifestu
  `vertex_weed`, `ground_bounce`, `set_tile_m`).
- `tools/worldgen/streetscape/`: `furniture.py`, `hero_bridge.py` (QA `pier_cols_on_carriageway`), `materials.py`, `plantings.py`,
  `stage.py` (log); `tools/worldgen/roads/`: `gores.py`, `build_world.py` (log); `tools/blender/world/landmarks/make_viaduct.py`.
- `overrides.yaml`: `hero_bridge.set` (`pier_lines_en`, `col_*`), `dk8-ramp-split-island`, `dk8-ramp-split-barrier-n`.
- `tests/gis/test_guardrail_overlap.py` (5 jednostkowych + 3 na `furniture.guardrail_runs` w `streetscape_qa.json`).
- asset `art-source/world/landmarks/viaduct_biezenstwa/` przebudowany przez Blender z nowej specyfikacji.

## Wynik
@@RESULT@@

## Otwarte / niezrobione (uczciwie)
1. **Telefon** — brak pomiaru (agent nie używa adb); koszt tylko z edytora.
2. **Połowa SE wiaduktu** — rytm rzędów przez symetrię, bez zdjęcia. Rzędy są pomiarem ze zdjęć o pozach klasy B, nie z projektu.
3. **Luki barier na pomostach przy wlotach** — 34 końce biegów pomostowych nie mają kontynuacji w 2,5 m (m.in. wiadukt Putry
   E −740…−690); dostają teraz odgięcie zamiast końca w powietrzu, ale w rzeczywistości bariera biegnie tam ciągle.
4. **Tablica F-10** dodana (pkt 10), ale położenie ±2 m, wymiar i stan po 2020 r. niezweryfikowane w terenie. „Bariera wzdłuż
   łącznicy zaczyna się później niż na zdjęciu” (0143) — nie ruszone.
5. Generyczne spody pomostów (`bridge_soffit`, DK8 / Putry) zostają na `sky_occ` — poza zakresem (0105).
6. Mur oporowy, profil W z bliska, latarnie, C-9 (P2-6…11 recenzji 0123), chodnik SSW i płyta dotykowa (0128 P2-4…6) — nie ruszone.
