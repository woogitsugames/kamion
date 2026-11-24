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
