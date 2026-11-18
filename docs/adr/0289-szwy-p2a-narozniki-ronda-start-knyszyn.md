# ADR 0289 — P-2a przez szew kafli, wysokości narożników ronda kompaktowego, start autopilota w knyszyn (seams-fix-s23)

Status: Accepted (lider s24, 2026-11-17; numer 0289 — 0288 = pętla S8).
Powiązane: ADR 0275 (przejścia na szwach, `seam_taper.py` — wzorzec reguły symetrycznej), 0285 (trasy łączące), 0227 D41 (e)
(narożnik mieszany ronda kompaktowego, uskok DK65 płd.), 0110 (trawa za krawężnikiem), 0218 5c / 0274 (rondo kompaktowe),
HANDOVER 17.11 01:4x / 07:0x (uskok zach. 0,506 m otwarty), 07:4x (zlecenie seams-fix-s23).

## Kontekst — pięć usterek po scaleniach s23
1. **Uskok DK65 od południa, strona zachodnia** (`qa/knyszyn_s_kerb_step.py`): 0,506 m (próg 0,15). Narożniki ronda Knyszyna
   S→W i W→N dostawały **zero trawy** — bezpiecznik `build_corner_strips` (linia krawężnika > 0,15 m/m ⇒ bez trawy w całym
   narożniku). Zrzut wysokości obrysu płyty (`PatchHeight.boundary_z`) pokazał, że to nie są dwa poziomy płyt, tylko
   **1–3 pojedyncze punkty łuku** 0,13–0,17 m pod sąsiadami (waga `on_arm` innego ramienia w IDW) i jeden schodek 0,16 m na
   0,54 m przy końcu narożnika S→W. Ten sam karb był w stopie krawężnika.
2. **Szew knyszyn-s | knyszyn, asfalt 9,48 | 7,64 m** (ADR 0285 „Znaleziska”): po scaleniu world3 + ADR 0275 jest **7,66 | 7,66 m**
   (`link_seams.py` na main 5a1c2c37b) — bez zmian w kodzie, potwierdzone po przebudowie.
3. **DW671 na szwie knyszyn | knyszyn-w**: w knyszyn linie ±1,75 m ciągłe (P-2a 20 m przed rondem, Dz.U. 2019 poz. 2311
   zał. 2 pkt 2.2.1.6), ale kafel kończy się 11,65 m za rondem; knyszyn-w nie wie o rondzie i malował P-1 od szwu z przerwą
   2 m — „linia urywa się”.
4. **C | Maczka, linia 2,91 m tylko po stronie Maczki**: linia między pasami DK8 (`w257367422`) w C leży pod wstęgą łącznicy
   `w606396469` (ułożonej obok DK8 przez `abreast_forks` z `shift_max_m = 0,0`, zakładka ~4,25 m) i jest usuwana przez
   `markings.drop_overlapping`; w Maczce wychodzi spod łącznicy 0,7 m za szwem. To spójna decyzja obu kafli, nie rozjazd reguł.
5. **Autopilot z `-scene knyszyn` staje na Rynku**: ścieżką startową jest trasa kontrolna (ADR 0204) kończąca się na Rynku;
   linki ADR 0285 tylko ZASTĘPUJĄ trasę doklejaną przy wjeździe z knyszyn-s.

## Decyzja
1. **`meshing.despike_arcs`** (tylko rondo kompaktowe — `j.compact`; inne skrzyżowania bajt w bajt): wysokości punktów `arc`
   obrysu płyty odbiegające > `ARC_SPIKE_M = 0,05 m` od mediany okna 7 punktów (zamknięty obrys) — liniowo między najbliższymi
   dobrymi punktami; schodek między dwoma punktami łuku > `ARC_GRADE_MAX = 0,15 m/m` (próg bezpiecznika trawy) — prosta rampa
   na 2·3+1 odcinkach, gdy wszystkie są `arc`. Punkty `end` / `gutter` (wyloty ramion) bez zmian — przekrój ramienia zostaje
   dokładny. Zmienia `zb`, więc płyta, krawężnik i trawa narożnika dostają te same wysokości (brak szczeliny płyta|krawężnik).
   Bezpiecznik 0,15 m/m zostaje bez zmian (chroni j:n2591872092).
2. **`roads/seam_p2a.py`** (reguła symetryczna jak ADR 0275): kafel czyta z gita dane sąsiada (`region.yaml`, `roads.graph.json`,
   `overrides.yaml` oraz `generated/osm_context.json` — wejście etapu skrzyżowań z `build_region`, nie wynik `build_world`),
   buduje jego sieć „plain” + skrzyżowania i pyta **tę samą regułę** (`markings.approach_ends`, wydzieloną z pętli oznakowania),
   które końce łańcuchów są dojazdami z P-2a. Dla drogi przeciętej szwem (pary końców `seam_taper.match`) z dojazdem
   sąsiada bliżej niż `P2A_MIN_LEN` od szwu kafel maluje resztę ciągłą od szwu: `20 m − odległość szwu od końca dojazdu`.
   `net.seam_p2a` → `markings` dokłada przedział do `cont` (linie pasa i środkowa); `roads_qa` bez nowego klucza (inne kafle
   bez zmian). Mapa dla wszystkich 39 kafli w `Data/Regions`: **tylko knyszyn-w** (`w1478765548`, 8,354 m; w knyszyn
   11,65 m ⇒ razem 20,0 m).
3. **Linki `after_route: knyszyn`** w `Data/Streaming/route_links.yaml`: `knyszyn-rynek-to-dw671-w` (tykocin, 744 m) i
   `knyszyn-rynek-to-dk65-w` (monki, 765 m): Rynek → Grodzieńska → Tykocka → rondo → ramię celu, koniec w tym samym punkcie
   co link korytarza (dalsze linki / trasa knyszyn-w dołączają bez zmian). `route_links.py`: link `after_route` **nie wraca**
   krawędzią, którą trasa przyjechała (zestaw nie zawraca w miejscu; najkrótsza droga prowadziła z powrotem), a narożnik
   startu jest liczony z tą krawędzią na początku (`lane_route` zaokrągla go jak każdy węzeł trasy), link zaczyna się
   w punkcie zaokrąglonego pasa najbliższym końcowi trasy i głowa jest dociągnięta do niego (`_blend`, 1,6–1,7 m).
   Link C → Maczka bez zmian (bajt w bajt w JSON).
4. **C | Maczka — bez zmiany** (pkt 4 kontekstu): przyczyną jest ułożenie łącznicy na pasie DK8 (`abreast_forks`
   `shift_max_m = 0`), a poprawka `drop_overlapping` dotknęłaby każdego rozwidlenia (ratchety fidelity C) w trakcie pracy
   c-p2-s23 nad C. Otwarte niżej.

## Wynik (przebudowa po merge main e0a0ccc21; sondy w `artifacts/seams-fix-s23/`)
- Narożniki ronda: max spadek linii krawężnika 0,514 / 0,102 / 0,125 / 0,462 → 0,116 / 0,102 / 0,125 / 0,132 m/m, trawa na
  4/4 narożnikach (było 2/4). `knyszyn_s_kerb_step.py`: zachód max 0,506 → 0,218 m (mediana 0,152), wschód 0,191 m —
  **poprawa do poziomu strony wschodniej, nie zamknięcie progu 0,15** (reszta = teren za pasem trawy 1 m).
- DW671 knyszyn | knyszyn-w: linie ±1,75 m ciągłe przez szew, w knyszyn-w 0–8,35 m, potem P-1 (`dw671_seam_lines_after.txt`).
- knyszyn-s | knyszyn: asfalt 7,66 | 7,66 m, linie ±3,55 | ±3,55 (`link_seams_after.json`).
- `qa.seams`: FAIL 19 (ADR 0275) → 16 (pozostałe: referencje rozstawu linii K1, pobocza DK8 kleeberga | knyszynska), PRZEJŚCIE 11.
- Start w knyszyn: model kinematyczny `swept_path` po ścieżce „60 m ogona trasy + cały link” (`qa/link_swept_check.py`):
  0 punktów krawędzi opon poza twardą nawierzchnią; poza jezdnią tylko naczepa na rondzie (s 689–697 m, fartuch/krawężnik
  wyspy). Link `knyszyn-rynek-to-dk65-w` (Mońki): 15 punktów opon naczepy poza twardą nawierzchnią i 77 poza jezdnią
  na rondzie (s 689–702 m, skręt z Tykockiej W w DK65 W) — do sprawdzenia przy rondzie (ADR 0274), złącze na Rynku czyste.
  Prędkość/poślizg poza modelem.

## Budżet
Rondo: trawa na 2 dodatkowych narożnikach (pas `_emit_verge`) — ESTIMATED ≤ ~1,5 tys. tris. `roads_qa.verge_strips` knyszyn
7 101 → 28 083 tris po przebudowie, ale razem ze zmianami batter z main (c-p1/c-p2; knyszyn-w bez rond też +5,9 tys.) — podział UNVERIFIED. P-2a: 8,4 m linii ciągłej zamiast 2 kresek — +0 draw calls (ta sama
siatka `markings`). Linki tras: dane, 0 kosztu renderu.

## Otwarte
1. **C | Maczka NIE naprawione**: łącznica `w606396469` leży ~4,25 m na pasie DK8 przez 27 m (`fork_abreast` shift 0), więc
   `drop_overlapping` usuwa linię między pasami DK8 na ostatnich ~7,5 m w C. Ortofoto GUGiK 2025 (`ortho_c_maczka.jpg`,
   `ortho_maczka_c.jpg`) pokazuje linię przerywaną ciągłą przez szew i łącznicę obok DK8 oddzieloną szrafem — błąd jest
   w ułożeniu łącznicy (abreast), do właściciela kafla C.
2. Start w knyszyn: złącze trasa → link ma załamanie 70–73° i promień ~3,9 m (narożnik Rynku, trasa kończy się w węźle);
   na Rynku dalej R 4,9 m (trasa C ma 5,9 m). Przejazd ciężarówką autopilotem NIESPRAWDZONY (zakaz uruchamiania exe w tym
   zadaniu) — do sprawdzenia: `Kamion.exe -scene knyszyn -stream 1 -autopilot route -speed 30`.
3. `ARC_SPIKE_M`, `ARC_SPIKE_HALF` — WORKING_VALUE.

## Odtworzenie
```
uv run --project tools/worldgen python -m pytest tests/gis/test_seams_fix_s23.py tests/gis/test_route_links_s23.py -q
uv run --project tools/worldgen python tools/worldgen/qa/knyszyn_s_kerb_step.py
uv run --project tools/worldgen python tools/worldgen/qa/seam_marking_strip.py knyszyn knyszyn-w 760587.0 611964.502 -0.7577 -0.6526 30
uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py --check
```

## Recenzja s24 (Codex, `artifacts/codex-review-0289-s24/out2.txt`; poprawki knyszyn-r24, 2026-11-17)
Każde znalezisko sprawdzone w kodzie przed poprawką.

1. **P1 — link `knyszyn-rynek-to-dk65-w` (Mońki): POTWIERDZONE.** Skręt w prawo Tykocka → DK65 W na rondzie
   kompaktowym prowadził środkiem prawego pasa przez narożnik R ≈ 7 m; naczepa ścinała narożnik krawężnika między
   ramionami (opony prawej strony naczepy w (−982…−985, −596…−598) lokalnie). **Poprawka:** nowy klucz linku `swing`
   w `route_links.yaml` (`route_links._swing`: przesunięcie toru w lewo z wagą podniesionego kosinusa, potem
   `_resample` do 2 m); dla Mońki 3,0 m w lewo w szczycie ronda, ±30 m. Przeszukane 680–692 m × 1,0–3,0 m × 15–35 m
   (2,5 m / 35 m zostawia 7 punktów na krawężniku / fartuchu) — WORKING_VALUE. Zmierzone (`qa/link_swept_check.py`,
   model kinematyczny, 1 punkt / m / oś): punkty opon poza twardą nawierzchnią **15 → 0** (16 po wyłączeniu wyspy
   `island_sand` z „twardej”), poza jezdnią **77 → 0**; po przebudowie knyszyn bez zmian.
   **Twardy próg:** `test_links_keep_tyres_on_hard_surface` — każdy link zbudowanego kafla: 0 punktów poza twardą
   nawierzchnią (8/8 linków: c-dk8-to-maczka, knyszyn ×4, knyszyn-w-dw671, dk65-01-s8-corner, s8-03-to-s8-04), oraz
   kontrola negatywna `test_swept_gate_catches_the_monki_corner_without_swing` (bez `swing` > 0). Narzędzie: wyspa
   ronda nie jest twarda, pokład mostu (`bridge`) jest, linki bez ogona trasy liczone od 15,7 m (długość zestawu —
   wcześniej poza modelem), punkty poza kaflem pomijane (należą do sąsiada), wyszukiwanie trójkątów w komórkach 25 m
   (`--all` 14 s zamiast > 3 min).
2. **P2 — `meshing.despike_arcs` interpolacja po indeksach: POTWIERDZONE.** Oflagowane wysokości są teraz
   interpolowane po odległości wzdłuż zamkniętego obrysu (bez geometrii — po indeksach jak dotąd). Test
   `test_despike_arcs_interpolates_by_distance_on_uneven_outline` (stary kod FAIL, nowy PASS). Druga część uwagi
   (okno z `end`/`gutter` pomija rampę) — zamierzone: wyloty ramion zachowują przekrój ramienia; po poprawce
   interpolacji spadek przy wylocie nie rośnie do 1 m/m.
3. **P2 — `route_links.py:76` start `after_route` tylko przy krawędzi powrotnej: POTWIERDZONE** i dotyczyło realnego
   linku: `c-dk8-to-maczka` (DK8 dwujezdniowa = dojazd jednokierunkowy) nie miał zaokrąglonego startu („bajt w bajt”
   z ADR wyżej wynikało z tego błędu). Nowa funkcja `arrival_edge` zwraca krawędź przyjazdu niezależnie od krawędzi
   powrotnej; głowa C → Maczka dociągnięta o 0,31 m (było 0,0). Test `test_after_route_start_rounded_on_one_way_arrival`.
4. **P2 — `seam_p2a.py:52` P-2a tylko przez jeden szew: POTWIERDZONE** (w danych dziś nieistotne). Krótki łańcuch
   sąsiada (< 20 m) od szwu do szwu przekazuje dalej resztę, którą sam dostaje (`plan(depth−1)`, `CARRY_DEPTH = 3`).
   Test 3 kafli `test_p2a_rest_carried_through_two_seams`; mapa dla wszystkich kafli `Data/Regions` bez zmian
   (tylko knyszyn-w, 8,354 m).
5. **Przy okazji:** `fidelity/gen.py` padał (`strip_cross(..., kind="P-12")` z main, atrapa bez `kind`) — atrapa
   przyjmuje `kind`, P-12 liczona jako linia zatrzymania w `overlays.STOP_KINDS` / `run.py`.

### Deski `wood_siding` (render `look_dom_klattow`, High clear, edytor Win64)
Ocena z wysokości oczu (18 m): ściana szczytowa Domu Klattów czytała się jako **podłoga / ściana z palet** — wąskie
(0,093 m) krótkie deski 0,3–1,2 m ze stykami na przemian, ciasny wzór jak cegła; w słońcu jak jasna cegła.
Poprawka: `set_tile_m [6,0, 2,6]` dla `wood_planks*` (wzdłuż ściany ×3,2 — styki 3,2 × rzadziej, deski ~1–4 m;
w poprzek ×1,39 — rozstaw 0,129 m). WORKING_VALUE: w repo brak zmierzonej szerokości desek domów knyszyńskich i
zdjęcia właściciela Domu Klattów. Test `test_wood_planks_long_boards_not_floor`.
Po przebudowie i imporcie (render 18.11, `artifacts/knyszyn-r24/small/klattow_before_after.jpg`): ściana czyta się jako
długie poziome deski (styki rzadkie, przesunięte), nie jak podłoga / cegła. Zostaje: deski wyglądają na surowe,
spłowiałe (plamy tonu między deskami widoczne w cieniu), a domy podlaskie są zwykle malowane jednolicie i mają opaski
okienne / deski narożne, których generator nie robi — do oceny `visual-critic` / właściciela (brak zdjęcia Domu Klattów).
