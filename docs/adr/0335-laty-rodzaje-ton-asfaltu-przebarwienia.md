# ADR 0335 — Łaty asfaltu w czterech rodzajach, tylko na asfalcie; ton asfaltu na km, ślady kół, olej, piasek przy krawędzi

Status: propozycja (gałąź `patches2-s24`, nie scalone). Źródło: krytyk build #5 (`artifacts/critic-s24-build5/CRITIC.md`,
pkt 4: „Łaty wciąż prostokątne … asfalt jednolity na prostych odcinkach”; klatki `t2931`, `t0950`, `t3261`).

## Kontekst

ADR 0322 / 0323 dały łatom zaokrąglone narożniki, szum obrysu i zalewkę, ale nadal jeden wspólny „kształt”: prostokąt
zjedzony szumem (55 %) albo prostokąt z cięciem piłą (45 %). Prawdziwe naprawy różnią się budową i obrysem
(Commons DW671 `cs11749508`, `cs7403215`, CC BY: długie ciemne pasy w śladach kół, które słabną i wracają, jasny piasek przy
krawędzi, ciemne i jasne odcinki jezdni na przemian). Asfalt poza łatami miał jeden ton na kilometry, smuga oleju była
równą linią w osi każdego pasa. Render kontrolny przed zmianami ujawnił dwa błędy generatora:
1. na dwupasmowej jezdni dwukierunkowej łata „na cały pas” (3,25 m) po odsunięciu od korony o 0,4 m wychodziła za
   krawężnik i była odrzucana — pełnopasowych łat praktycznie nie było (test syntetyczny: 4 z 80);
2. łaty asfaltu były kładzione też na kostce granitowej Tykocina i na kostce brukowej podwórek (pas „koleiny” 24 m na
   `road_sett`); wykluczone były tylko `road_asphalt_new`.

## Decyzja

Wszystko, co się da, w masce piksela (`WorldPBR _DECAL_PATCH`), bez nowej geometrii: ta sama siatka (kwadraty 2,5 x 2 m),
ta sama liczba trójkątów na łatę.

1. **Rodzaj łaty w `UV1.y`** (`roads/decals.py`): `kind + 0.02 + 0.96 * ziarno`, dekodowane `floor` / `frac` w shaderze
   (przesunięcie 0,02 chroni przed przeskokiem `floor` przy interpolacji przy cięciu kafla). `UV1.y < 1`, brak i `>= 5`
   = stara maska (łaty podwórzowe `yard_wear`, stare dane). Wiek (UV1.x) trójmodalny: 35 % świeże, 35 % pośrednie, 30 % stare.
   - 1 **frezowanie + nakładka** (połowa łat „na cały pas”, 3–8 m, obrót x0,35): proste cięcia poprzeczne, brzegi
     podłużne poszarpane 3–12 cm, narożniki ścięte nieregularnie (r 4–20 cm modulowany szumem), zalewka tylko wzdłuż cięć
     poprzecznych, z przerwami.
   - 2 **wykop** (druga połowa pełnopasowych, 20 % małych, połowa śladów kół): prostokąt, połowa wycięta piłą (narożnik
     2–6 cm), połowa łyżką (12–40 cm), krawędzie nierówne 2–4 cm na 0,3–1 m, zalewka 2,5–8 cm o zmiennej szerokości z
     przerwami na ok. 50 % obwodu.
   - 3 **na gorąco** (80 % małych 0,6–1,5 m): nieregularny owal (dwie oktawy szumu), poszarpany rzut, bez zalewki.
   - 4 **koleina** (30 % długich 8–25 m + połowa krótkich): pas wzdłuż śladu o szerokości wędrującej 60–115 %,
     zwężone / poszarpane końce, miękkie boki.
2. **Materiał łaty**: ziarno kruszywa (3,5 i 13 cm, ±1,5 %/±7 %, drobne zanika z odległością), jasne drobiny (okrągłe,
   +0,018 albedo, zanikają z odległością), wyblakły brzeg starej łaty (rąbek 6 cm), ciepła czerń świeżej (x1,06/1,0/0,93),
   świeża x0,8 ciemniejsza od starej, ton na łatę 0,82–1,18 x, zalewka matowsza na starych łatach. Współrzędne szumu
   zawijane co 45 m (utrata precyzji `Hash12` na indeksach 1e4–1e5 dawała chmurkowate plamy 0,5–1 m).
3. **Łaty tylko na `road_asphalt`** (`SEAL_SURFACES`): nie na kostce, betonie, żwirze ani świeżym asfalcie. Łata pełnopasowa
   mieści się w pasie (`fits_lane`). Łaty jednego łańcucha nie nakładają się (odstęp 0,4 m wzdłuż, 0,25 m w poprzek).
4. **Odległość do krawędzi w masce** (`RoundedInset`): stary wzór `min(b, rc - |max(rc - b, 0)|)` ogranicza wnętrze do
   `rc`; przy narożniku 2 cm wnętrze łaty było dziurawe. Nowe rodzaje używają poprawnej odległości do zaokrąglonego
   prostokąta; maska dla rodzaju 0 bez zmian.
5. **Ton asfaltu** (`_ROADWEAR`): trzy oktawy szumu w przestrzeni obiektu (90 m, 23 m, 7 m): `1 + 1,4 (tv − 0,5) + 0,3 mid`
   i +-2,5 % ciepło/zimno; ta sama funkcja na wstęgach, płytach i łatach skrzyżowań (brak szwów); świeży asfalt bez zmian.
6. **Ślady kół** x1,35 (było x1,0), kontrast słabnie do 35–100 % na odcinkach 20–60 m (szum 38 m).
7. **Ślad oleju** wędruje +-8 % pasa, występuje na ok. 65 % drogi (17 m), kropkowany, plamy 0,3–0,8 m (x1,9 / x1,8).
8. **Piasek / osad przy krawędzi** (tylko wstęgi, `w.y < 15`): pas 0,1–0,9 m z językami (szum 1,3 m), w odcinkach
   3–14 m ciemny osad (do −17 %) albo na ok. 45 % długości beżowy piasek (warstwa koloru, albedo 0,17/0,145/0,11, do 60 %).

Wszystkie progi: WORKING_VALUE, oceniane wzrokowo wobec Commons DW671; brak danych SOSN/DSN.

## Wyniki

- Testy: `tests/gis/test_patch_kinds_0335.py` (6: kodowanie rodzaju, dekodowalność, geometria rodzajów, wiek, determinizm i
  liczba trójkątów na komórkę, brak łat na kostce/betonie/żwirze/nowym asfalcie, brak nakładania) + 0322/0323/0327/budżet:
  122 passed (wybrany podzbiór, przed ostatnimi zmianami shadera; pełny przebieg `tests/gis` — patrz STATUS.md).
- Budżet (`streetscape_qa.json`, `stretch_04` kafla C): **1 996 244 (main) -> 1 995 509**, zapas do 2 000 000: 4 491
  (było 3 756). Łat w C: 817 -> 573 kawałków chunków (571 łat); `dw671-tykocin-01`: 273 -> 135. Trójkąty na łatę bez zmian
  (2 na komórkę 2,5 x 2 m), spadek z odrzucenia łat na kostce i nakładających się.
- Render kontrolny (edytor, High 1920x1080, clear; `artifacts/patches2-s24/sheets`, `.../frames`): kamery `p_*` / `q_*`
  przy łatach każdego rodzaju, z 4,2 m (blisko) i 26 m (kabina, 2,5 m), po dwie z kontrastowym wiekiem na rodzaj, oraz
  kadry wzdłuż prostej. `visual-critic`: runda 1 FAIL (ziarno pikselowe, komiksowa zalewka, zagnieżdżone łaty), runda 2
  FAIL (zalewka bez przerw, piasek niewidoczny, ślady kół słabe), runda 3 4x PASS / 2x FAIL (ślady kół x3 za mocne),
  runda 4 (po korekcie) **PASS z trzema uwagami P2**.
- Otwarte (P2 z rundy 4): (a) zalewka na jednej krawędzi miejscami 2–3 x szersza niż na przeciwnej — ograniczyć zmienność
  do 0,6–1,0 szerokości bazowej; (b) znakowanie poziome (strzałka) przechodzi przez świeżą łatę wykopu bez zmiany —
  zamaskować lub odświeżyć farbę nad łatą; (c) koleiny w oddali ciemniejsze niż przy kamerze — mnożnik
  `1 − 0,4 saturate((d − 60)/120)`; (d) piasek wchodzi na jezdnię mniej niż na `cs11749508` (pobocze szutrowe poza zasięgiem
  tej warstwy).

## Konsekwencje

- Reimport shadera i przebudowa **wszystkich** regionów z łatami (UV1.y łat, `world_manifest` sha): w tej gałęzi
  przebudowane i skomitowane tylko `bialystok-industrial-c` i `dw671-tykocin-01`; pozostałe (dw671-tykocin-02..09, knyszyn,
  tykocin, dzielnice Białegostoku) po scaleniu przez lidera: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id> --context`.
- Region zbudowany starym kodem + nowy shader: łaty z `UV1.y < 1` dostają starą maskę (poprawnie), ale tracą dziury /
  zalewkę nowego rodzaju; efekt tonu / śladów kół / piasku działa na każdym regionie od razu.
- Ślady kół x1,35 i ton +65 % zmieniają wygląd wszystkich dróg asfaltowych (nieoglądane poza DW671, Tykocin i kafel C).

## Dopisek P2 (runda 4 krytyka, gałąź `neon-patches-p2-s24`)

Rozwiązanie czterech uwag P2 z rundy 4 bez dodawania trójkątów (budżet `stretch_04` ≤ 2 000 000, ADR 0327):

1. **Stała szerokość zalewki bitumicznej w metrach** (`WorldPBR.shader`, `_DECAL_PATCH`):
   - Odległość prostopadła do krawędzi liczona z pełnego Jakobianu powierzchni (`sinTheta = length(cross(Eu0/lenEu, Ev0/lenEv))`,
     `sizeM = float2(lenEu, lenEv) * (invAbs * max(sinTheta, 0.25))`), odpornego na ścinanie UV przy przycięciu do
     krawężnika, łuki i obrót łaty oraz na przepełnienie fp32.
   - Szerokość zalewki ograniczona do stałego pasma fizycznego `baseSw = _PatchSeam.x * (0.70 + 0.30 * n2)` (4,2–6,0 cm
     przy `_PatchSeam.x = 0,06 m`, stosunek ≤ 1,43× zamiast 3–5×); przerwy wzdłuż obwodu sterują wyłącznie kryciem
     (`sealMask`), nie zwężają szerokości.
   - Usunięto mnożnik `endD * 0.5` w rodzaju 4 (`rut`), który podwajał szerokość zalewki na końcach pasa.
2. **Znakowanie poziome na łatach (0 dodatkowych trójkątów)**:
   - **Wykop (`PATCH_TRENCH`, 2) i na gorąco (`PATCH_HOT`, 3)** (`roads/decals.py`): podniesienie siatki na
     `LIFT_PATCH_OVER_PAINT = 0.009 m` (+3 mm ponad `MARKING_LIFT = 0.006 m`), przy zachowaniu `LIFT_PATCH = 0.002 m`
     dla `milled` (1), `rut` (4) i starych łat (0) oraz niezmienionego porządku kolejek (`marking_white` Geometry+10,
     `ZWrite On` → `decal_patch` Geometry+12, alpha-blend, `ZWrite Off`). Dzięki temu łata wykopu / na gorąco przerywa
     znakowanie (strzałki P-8, linie) dokładnie wzdłuż maski pikselowej i zalewki, bez nowych trójkątów.
   - **Frezowanie + nakładka (`PATCH_MILLED`, 1)** (`streetscape/yard_wear.py: mark_milled_patch_paint`, `WorldPBR.shader`
     `_DECAL_PAINT`): znakowanie nad łatą frezowaną dostaje pasmo odnowionej farby `UV1.y += 8` (`[8,9)` podłużne,
     `[10,11)` poprzeczne; zgodne z kwantyzacją FP16 i wstecznie kompatybilne z nieprzebudowanymi kaflami oraz sentinelem
     `(-1, 5)`). Krótkie znaki (strzałki, pasy poprzeczne, kreski ≤ 5,5 m) odnawiane w całości; długie linie ciągłe dzielą
     istniejące trójkąty siatki 2 m na część odnowioną i zwykłą (dokładnie +0 trójkątów). W shaderze `paintRenewed`:
     zużycie ×0,12, brud ×0,15, albedo farby ×1,22 (WORKING_VALUE, świeża biała farba EN 1436), gładkość +0,08.
3. **Koleiny i smuga oleju w dali** (`WorldPBR.shader`, `_ROADWEAR`):
   - Prefiltrowanie analitycznego paska koleiny śladem piksela (`wpMip = saturate(0.11 / max(rwFwx, 0.11))`, pochodne
     wyciągnięte przed niejednorodny warunek `w.x > -0.5`), wygaszanie szumów wysokoczęstotliwościowych poniżej śladu piksela
     (`brk` 1,3 m, `drops` 0,9 m, `blot` 0,55 m) oraz łagodne tłumienie z odległością
     `rwDistAtten = 1.0 - 0.50 * smoothstep(25.0, 130.0, rwDist)` (WORKING_VALUE; na `dw671-tykocin-01 q_far` przed
     zmianą kontrast `med − p15` wynosił 11,3 sRGB blisko vs 22,4 sRGB w dali).
4. **Poszerzony pas piasku przy krawędzi** (`WorldPBR.shader`, `_ROADWEAR`, WORKING_VALUE):
   - Rozdzielono ciemny osad (`eband`, 0,2–0,9 m bez zmian) od języka piasku (`sandTongue = 0.35 + 1.05 * (0.65 * n1.5m + 0.35 * n4.3m)`
     = 0,35–1,40 m, `sandy` ~55 % długości, krycie 0,62, zmatowienie `smooth *= 1 - 0.35 * sandW`) dla zbliżenia do
     referencji `cs11749508.jpg`.

### Weryfikacja P2
- Testy jednostkowe Python: `test_patch_kinds_0335.py` (9/9, w tym 3 nowe testy dla P2), `test_road_surface_0323.py` (10/10),
  `test_asphalt_patch_uv.py` (4/4), `test_asphalt_paint_surface.py` (6/6), `test_budget_0221.py` (8/8),
  `test_typology_0238.py` + `test_world_v31.py` + `test_hero_bridge.py` (55/55), `test_streetscape.py` +
  `test_fab_details.py` + `test_stains_0194.py` + `test_world_pbr_tint_contract.py` (102/102).
- Unity EditMode (`AsphaltScopeTests|RoadPaintLaneFieldTests|RoadWearUvContractTests|WorldPbrTintTests`, Android):
  32/32 PASS, 0 błędów i 0 ostrzeżeń kompilacji `WorldPBR.shader`.
- Pytest po przebudowie (24.11): `test_budget_0221` + `test_typology_0238` + `test_world_v31` + `test_hero_bridge` + `test_patch_kinds_0335` + `test_road_surface_0323` = **82/82 PASS** (limit 2 M trójkątów High na najcięższej kamerze nie przekroczony; zmiany P2 = 0 nowych trójkątów).
- Przebudowa: `dw671-tykocin-01` 455 s, `bialystok-industrial-c` 1133 s (exit 0, pod slotem `heavy`); PBR Medium aktualne (233 pliki, 0 braków).
- Visual-QA przed|po (High 1920x1080, arkusze `artifacts/neon-patches-p2-s24/sheets/*.jpg`): ocena lidera-agenta, NIE visual-critic:
  1. Zalewka: szerokość wyrównana i bez przerw tylko nieznacznie widoczna w skali arkusza (zoom `zoom_C_trench0_seam.jpg`: krawędź jednolitej grubości, brak rozjazdu na skos) — poprawa subtelna.
  2. Znakowanie vs łata: potwierdzone — na `C q_trench0_close` strzałka P-8 jest teraz przerwana przez łatę wykopu (przed: namalowana na łacie); na `C q_milled0_close` linia nad łatą frezowaną jaśniejsza (odnowiona farba).
  3. Koleiny w dali: pomiar `med − p15` (`make_sheets.py`, `tykocin q_far`, clear): przed blisko 11,3 / dal 22,4 sRGB, po blisko 11,2 / dal 22,6 — w clear BEZ zmiany mierzalnej; w overcast po: blisko 10,6 / dal 18,0 (przed niemierzalne, patrz niżej). Poprawka UNVERIFIED jako skuteczna w clear — do oceny visual-critic/lidera.
  4. Piasek przy krawędzi: pas szerszy, miękki (`tykocin p_trench1_close`), nie odtwarza jeszcze pełnej szerokości `cs11749508.jpg` — do oceny visual-critic.
- Ograniczenie: render „przed” w overcast (shader z `71336ba56` podstawiony tymczasowo) wyszedł magenta (błąd kompilacji/niezgodność z nowym UV1) — porównanie przed|po tylko w clear (przed = runda 4 `after8`); overcast tylko „po”.
- Nieweryfikowane: ocena `visual-critic` (nie uruchomiona w tym przebiegu), build gracza Windows.

## Dopisek P2b: koleiny w dali (gałąź `rut-far-s24`, 24.11)

Uwaga P2 nr 3 („koleiny w dali ciemniejsze niż przy kamerze”) — diagnoza i poprawka.

1. **Poprzedni pomiar był nieważny.** `med − p15` z `make_sheets.py` liczył pole „far” (wiersze 56–66 % wysokości, kolumny 43–57 %) na `q_far`. Pole obejmuje ciemną łatę wykopu i podstawę barierki zamknięcia drogi, więc liczba 22,4–22,6 sRGB nie opisywała kolein. „11,2 vs 22,6” nie jest dowodem ani na problem, ani na brak poprawki.
2. **Nowy pomiar (sonda).** `WorldPBR.shader`: `#if defined(KAMION_RUT_PROBE_OFF)` zeruje `wp` (pasy polerowania). Kontrast koleiny w gotowych pikselach = `1 − lum(on) / lum(off)` w obrębie jezdni (`artifacts/rut-far-s24/rutmeasure.py`, `rutdist.py`, `rutratio.py`). Kamery `rg_S`: ten sam odcinek jezdni oglądany z S = 0…100 m dalej (kamera cofnięta wzdłuż osi, za barierką zamknięcia nie wolno), wysokość kamery dopasowana z korelacji profili wzdłuż drogi (h ≈ 2,0 m, UNVERIFIED), High 1920x1080, Win64, clear i overcast.
3. **Wynik „przed”:** na tym samym gruncie średnie ściemnienie koleiny jest płaskie z odległością (15–25 m od bazy: 2,35 % z 15–25 m, 1,3–2,1 % z 35–125 m; szczyt p95 8,7 → 6–9,6 %). Czyli nie ma mnożnika w shaderze, który ciemni koleiny dalej; stary `wpMip` nie działał poniżej ~300 m (pochodna `fwidth(w.x)` jest tam małą liczbą). Skok widoczny na `q_far2` (peak 15–18 % przy 8–12 m → 22 % przy 21 m) to szum położenia (`trackFade`, `brk`), nie odległość. Percepcja „ciemniejsze w dali” = tekstura asfaltu przy kamerze zasłania pasy, w dali mipy ją wygładzają i koleiny zostają jedynymi ciemnymi liniami do horyzontu.
4. **Poprawka (WORKING_VALUE):** `rwDistAtten = 1 − 0,60·smoothstep(20, 120, d)` (było `1 − 0,50·smoothstep(25, 130, d)`; 1,0 do 20 m → 0,40 od 120 m) oraz prefiltr paska z zachowaniem pola: szerokość `max(0,11; 1,2·fwidth)`, amplituda `0,11/szerokość` (zbiega do średniego ściemnienia zamiast aliasować; stare `* saturate(0,11/fwx)` zmniejszało pole).
5. **Wynik „po”** (to samo podłoże, `rutratio.py`, średnie ściemnienie, stosunek po/przed): ≤ 25 m 0,97–1,01 (bez zmiany przy kamerze); 35–65 m 0,86–0,98; 85–140 m 0,71–0,79 (clear), 0,73–0,76 (overcast). Szczyt p95 z 8,2 → 6,0 % (115–125 m). Zasięg ≤ 25 m nietknięty — kontrast przy kamerze bez zmiany, w dali spada łagodnie do ok. 0,6–0,75 (perspektywa powietrzna).
6. **Ograniczenia:** pomiar w dali opiera się na 3–6 wierszach pikseli (szum ±30 %); odległości z geometrii wiersza przy h = 2,0 m (dopasowane, nie zmierzone); render „po” ocenił agent, NIE visual-critic (zmiana subtelna, arkusze `artifacts/rut-far-s24/sheets/`); nie sprawdzano Białegostoku C ani telefonu. Po rebase na main import `dw671-tykocin-01` wymagał osobnej poprawki `WorldPbrMaterials.FurnitureSignFronts` (materiały `sign_post*` brane za tablice, ADR 0337).
7. **Testy:** EditMode Win64 (`AsphaltScopeTests|RoadPaintLaneFieldTests|RoadWearUvContractTests|WorldPbrTintTests`) 32/32 PASS.

## Dopisek render-artifacts-s24 (2026-11-26): pionowe ciemne smugi zbiegające się do horyzontu (krytyk fala 11, P1 #6)
**Przyczyna (dowód renderem, knyszyn-w High clear).** Ablacja: `_ROADWEAR` wyłączony (`KAMION_QA_DIAG=kwoff:_ROADWEAR`) →
smugi znikają; cienie wyłączone (`rq_shadow=0`) + przewody wyłączone (`-Wires off`) → smugi bez zmian (to nie cień przewodów
ani kaskad); maska `decal_tyre` → 0 rendererów w kadrze. Smugi = pasy kół (`wp`, 0,26 / 0,74 pasa) i pas kapania (0,5) z
`_ROADWEAR`: route-s1846 trzy jednakowo ciemne, ciągłe pasy na pas ruchu, kontrast pasa (najciemniejszy − p10 względem
renderu bez `_ROADWEAR`) 9–16 pkt %, widoczne do horyzontu, gdzie perspektywa zbiega je w „szyny”.

**Poprawka (WorldPBR, WORKING_VALUE).** `rwDistAtten = 1 − 0,85·smoothstep(15, 90, d)` (było 0,60 / 20–120 m); profil pasa
koła smoothstep zamiast trójkąta (bez ciemnej linii w środku), szerokość ≥ 0,13 pasa; boczne błądzenie pasów ±5 % szerokości
pasa z tego samego szumu 38 m co `trackFade` (bez nowego wywołania szumu); mnożnik ściemnienia 1,35 → 0,75; pas kapania
1,9 → 1,2. Wynik: kontrast pasów 3,5–5 pkt % (wiersze 640–1000 route-s1846), smugi do horyzontu znikają
(`artifacts/render-artifacts-s24/sbs/crop-road-s1846-before-after.jpg`, `route-s0426-before-vs-after.jpg`).
Koszt: te same odczyty tekstur, +~4 ALU na piksel jezdni (smoothstep, przesunięcie); draw calle bez zmian; GPU **UNMEASURED**
(edytor nie jest dowodem — pomiar `pc-metrics` w buildzie).
## Dopisek P3: łaty widziane z kabiny, szew osi (gałąź `worktree-agent-a4b13d4540b9ae795` / road-patches-s24, 26.11)

Źródło: krytyk fali 11 (`artifacts/critic-s24-wave11/CRITIC.md` pkt 2 P0 i pkt 4 P1, trzeci raz z rzędu „prostokątne łaty”).

### Diagnoza (render „przed” w worktree = obraz krytyka)
1. **Szew osi + czarny falisty pas** (`knyszyn-w dk65-goniadzka` x~985–1040): to nie łata, koleina ani szew kafla, tylko
   `decals.seal_cracks` — „centre construction joint”: pasmo `decal_seal` 12–20 cm, `strength 2,6` (pełne, bez rozbicia
   makroszumem), meander ±5 cm na falach 5–9 m (ten sam co pęknięcie termiczne). Obok prostych kresek P-1 ciemne pasmo,
   które co kilka metrów przechodzi z lewej strony kreski na prawą, czyta się jako przeskakująca linia środkowa.
2. **Jasny twardy prostokąt** (`dw671-tykocin-03 cab-view-b`): jezdnia ma ton `_ROADWEAR` 0,44–1,56 x (szum 90/23/7 m),
   łata go nie miała — stara łata na ciemnym odcinku wychodziła jasna, świeża na wyblakłym czarna. Przez łatę biegło
   pęknięcie `decal_seal` (kolejka +20 nad łatą +12).
3. **Obrys prostokątny z kabiny**: szum obrysu ADR 0335 (2–12 cm) miał długości fal 0,07–0,9 m — z 10–40 m (1,5–6 cm na
   piksel) każda krawędź to linijka. Zalewka 4–6 cm leżała na rampie alfa krawędzi (0..`fth`+aa) i z odległością znikała.

### Decyzja (0 nowych draw calli, 0 nowych trójkątów łat; WORKING_VALUE)
1. **Szew osi** (`roads/decals.py`): prosty (meander ±1 cm, `CENTRE_JOINT_AMP_M`), pasmo 6–9 cm (rdzeń 3,5–5,5 cm),
   `strength 1,7` (< 2,5 → przetarty makroszumem, nie pełny pas). Pęknięcia termiczne / krawędziowe bez zmian.
2. **Pęknięcia nie przechodzą przez łaty**: polilinia pęknięcia dzielona na odcinki poza obrysem łat łańcucha
   (`_runs_outside`, margines 15 cm, obrót łaty uwzględniony). Trójkąty pęknięć: knyszyn-w 5 716 → 4 990,
   dw671-tykocin-03 8 190 → 7 326 (r1).
3. **Łata dziedziczy ton odcinka** (`WorldPBR`: wspólna funkcja `KamionRoadTone`, ta sama na wstędze i łacie): stara łata
   w pełni, świeża w 60 % (wyblaknięcie 90 m przyszło później). Kontrast łaty względem jezdni nie zależy już od miejsca.
4. **Obrys z kabiny**: wędrówka 5–15 cm na falach 0,55 i 1,6 m (amplituda na łatę), wyszczerbienia do 12 cm (szum 0,35 m);
   frezowanie: każdy koniec z własnym skosem ±3°, 40 % z końcem schodkowym 0,1–0,4 m na połowie szerokości (dwa przejazdy
   bębna), brzegi podłużne wędrujące; wykop: boki wędrujące, 45 % w kształcie L (narożnik 25–45 % x 30–55 % niewykopany).
5. **Zalewka 2–4 cm okrakiem na cięciu** (`asphalt_patch_seam.width_m` 0,06 → 0,032, `darkening` 0,75 → 0,80): obrys
   cofnięty o pół szerokości, zalewka składana z własnym kryciem (0,94) i filtrowana pudełkowo (pod pikselem zachowuje
   ~pole zamiast znikać); wypełnia fakturę (normalna spłaszczona); gładkość — pkt 7.
6. **Szorstkość / faktura wg wieku**: świeża łata — ziarno x0,55 i normalna spłaszczona o 35 % (lepiszcze zamyka
   powierzchnię), stara — ziarno x1,15; ton partii 0,88–1,14 (było 0,82–1,18). Trzy pokolenia (wiek trójmodalny) bez zmian.
7. **Gładkość łaty i zalewki jak jezdni (r3; główna przyczyna „jasnego prostokąta”)**: zestaw `asphalt_patch` (skan
   clean_asphalt) ma średnią gładkość 0,34 wobec 0,10 `asphalt_worn` (alfa MaskMap High); pod kątem patrzenia z kabiny
   łata odbijała niebo i była jasna niezależnie od albedo (sondy `artifacts/road-patches-s24/probe2|probe3`: wiek/rodzaj
   zakodowane w kolorze potwierdziły ścieżkę `_DECAL_PATCH`; gładkość 0 na 1/3 łaty sprowadziła ją do tonu jezdni).
   Ograniczenie `smooth <= 0,17 (świeża) .. 0,11 (stara)`, zalewka 0,22 .. 0,14 (ADR 0131: błyszcząca czarna zalewka pod
   kątem wychodzi biała). Stara łata x0,82 na końcu „aged”, plamistość ±(3–12) % rosnąca z wiekiem, jasny rąbek 0,30 → 0,12.

### Wyniki (edytor, High PC 1920x1080; `artifacts/road-patches-s24/{before,after,after-r1,after-r2}`, arkusze `sheets/`)
- `dw671-tykocin-03 cab-view-b` (jasność sRGB: łata / jezdnia obok, te same pola): przed **1,17 x** (clear 125,6/107,3),
  **1,21 x** (overcast 75,9/62,5); r1 i r2 bez zmiany (dominowało odbicie nieba); po r3 **0,92 x** (99,2/107,7) i
  **0,85 x** (53,8/63,0). Pęknięcie przez łatę zniknęło; stara łata na lewym pasie czyta się słabo, jak powinna.
- `knyszyn-w dk65-goniadzka`: czarny falisty pas w osi → krótki, prosty, wąski, przetarty odcinek szwu; łata frezowana ma
  schodkowy koniec z zalewką na cięciu; łata przy krawędzi ma kształt L z cienką ciemną zalewką.
- Testy: `tests/gis -k "patch or 0335 or shader or seal or 0323 or budget or pbr"` **87 passed, 1 skipped** (nowe:
  `test_centre_joint_is_straight_and_worn`, `test_seal_cracks_split_at_patches`, `test_crack_seals_do_not_cross_repairs`).
- Ocena: agent, NIE visual-critic. Otwarte: frez z bliska ma nadal proste cięcia poprzeczne (zgodne z rzeczywistością);
  zalewka wykopu to ciągła cienka linia — ew. więcej przerw; `route-s0144` (dk65-07) nie przebudowany ani nie renderowany;
  brak buildu playera Windows i testów EditMode Unity w tej gałęzi.

### Konsekwencje
- Zalewka 3,2 cm i nowe parametry trafiają do regionu dopiero po przebudowie (`world_manifest`); przebudowane tu tylko
  `knyszyn-w` i `dw671-tykocin-03` (prywatna kopia derived worktree). Shader działa od razu na każdym regionie
  (ton, obrys, kształty), ale stare regiony mają zalewkę 6 cm (teraz okrakiem, więc wyraźniejszą).
- Pozostałe regiony z łatami/pęknięciami po scaleniu: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>`.

## Dopisek axis-driveway-s24 (27.11): szew osi po P3 nadal „pionowy ciemny odcinek” + falisty pas (krytyk build #10 pkt 4)

**Diagnoza** (`KAMION_QA_DIAG=colorby:material`, `artifacts/axis-driveway-s24/diag-before-material/dk65-goniadzka*`):
oba elementy to `M_decal_seal` — pionowy odcinek = szew osi z P3 leżący DOKŁADNIE w osi (przedłużał kreskę P-1 między
kreskami, startował/kończył się na krótkim wygaszeniu 0,65/0,9 m), poziomy = dwa połówkowe pęknięcia termiczne
(pełna czarna zalewka `strength 2,6`, meander ±16 cm) stykające się z nim w „T”. Nie łata, szew kafla ani dylatacja.

**Decyzja** (`roads/decals.py`, 0 nowych draw calli; WORKING_VALUE):
- szew osi 14–26 cm OBOK linii (strona i odsunięcie per odcinek, `CENTRE_JOINT_OFFSET_M`) — linię maluje się po
  sznurze po ułożeniu, nie na szwie; krawędź pasma ≥ 2 cm od krawędzi kreski 12 cm; długie wygaszenie końców
  (dodatnia długość w UV1.x → 2,5/4 m w shaderze, bez zmiany shadera); `CENTRE_JOINT_STRENGTH` 1,7 → 1,25 (stara,
  przetarta zalewka);
- pęknięcia poprzeczne: meander 0,16 → 0,09 m (`TRANSVERSE_MEANDER_M`); tylko ~35 % zalewek świeżych (2,6), reszta
  1,5–2,1 (przetarte makroszumem, szarsze) — nigdy jednolita czarna wstęga.
- Wynik (`artifacts/axis-driveway-s24/sbs/dk65-goniadzka-before-after.jpg`): szew obok kreski, słaby, z wygaszeniem;
  pęknięcie cieńsze i szare. drawsEst/trisK kamery bez zmian (170→171, 812k→812k).
- Testy: `tests/gis/test_road_surface_0323.py` 14/14 (nowy `test_transverse_seals_not_all_solid_black`, zmieniony
  `test_centre_joint_is_straight_and_worn`). Pozostałe regiony po scaleniu: przebudowa `build_world.py --region <id>`.
