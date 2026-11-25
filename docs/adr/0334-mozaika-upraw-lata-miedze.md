# ADR 0334 — Mozaika upraw lata: użycia pasów z własnym albedo, wąskie podłużne działki, miedze z krzewami

Status: Proposed, 2026-11-24 (agent fields-s24; zmiana globalna — shader terenu, generator roślinności).
Powiązane: ADR 0295 / 0298 (mozaika pól per piksel, flaga COLOR_0.b), 0327 (budżet trójkątów), D68 (lato wszędzie, światło
~15 sierpnia). Źródło: krytyk build #5 (`artifacts/critic-s24-build5/CRITIC.md`) pkt 3 — „trawa i pola to jedna zielona
płaszczyzna” (klatki `t0950–t0970` = kafel dk65-03, `t3231–t3261` = dw671-tykocin-09); P0 „listopad” odrzucony (D68).

## Kontekst — przyczyny (odczytane z kodu i danych)

1. **Mozaika ADR 0298 była, ale nie było jej widać.** Kafle trasy mają flagę pól (`streetscape_qa.json` → `farmland.encoding`
   = flaga; dk65-03: 3,26 km² pól, 78 % kafla). Shader nakładał na kolor trawy **mnożnik**: ściernisko
   (1,16; 1,08; 0,80) × trawa (liniowo 0,072; 0,114; 0,011) = nadal zielone (0,084; 0,123; 0,009). Każde użycie było
   „jeszcze jednym odcieniem zieleni”, łąki (4 z 4 odmian) różniły się o kilka procent.
2. **Układ pasów:** bloki Woronoja 300 m z losowym kierunkiem pasów 0–180° na blok — z góry „wiatraczek” wielokątów
   (`artifacts/fields-s24/preview/palette_topdown.png`), nie podlaska szachownica wąskich, długich działek.
3. **Hash `KFHash(i, j) == KFHash(-i, -j)`** (nieparzyste mnożniki, XOR): nie szkodził na nieujemnej siatce EPSG:2180,
   ale każda siatka ze znakiem (ramy lokalne) dostaje bliźniacze bloki.
4. **Brak danych o działkach** (EGiB/ULDK nie ma w `Data/raw`); OSM w tych kaflach nie ma `crop=*`. Układ zostaje
   proceduralny (ESTIMATED), rodzaj gruntu z BDOT10k OT_PTTR_A (orne / trawiaste) jak w ADR 0298.

## Decyzja

### 1. Użycie pasa = własne albedo (`Environment/Shaders/KamionFieldMosaic.hlsl`, `WorldPBR.shader`)
- 16 użyć: orne — zboże dojrzałe (złote), zboże jasne (jęczmień/żyto/owies), ściernisko z wałami słomy, ściernisko po
  prasowaniu, ściernisko rzepaku, kukurydza, ziemniaki/buraki, talerzowane, międzyplon, trawy w uprawie, ugór; łąki —
  odrost po pokosie, pastwisko, świeżo skoszona z wałami, siano schnące, nieskoszona (kwitnąca). Udziały i albedo
  `WORKING_VALUE` (tabela w shaderze i `vegetation.FIELD_USES_*`).
- Kolor pola **zastępuje** kolor trawy z wagą pokrycia (0,65–0,95), tekstura trawy zostaje jako detal luminancji
  (±40 %). Zero nowych tekstur, słów kluczowych i draw calli.
- Struktura, która zdradza użycie z kabiny (filtrowana rozmiarem piksela, znika poniżej ~3 px): ścieżki technologiczne
  18 m w zbożu stojącym i międzyplonie, wały słomy co 7,5 m (heder), drobne rzędy ścierniska 0,16 m, rzędy 0,75 m
  (kukurydza, ziemniaki), przejazdy talerzówki 3 m, wały siana co 6 m, płaty chwastów / kęp / kwiatów 5–17 m (ugór,
  pastwisko, łąka nieskoszona), wyleganie zboża, uwrocia 9 m na końcach pasów, miedze 1,0–2,6 m (szerokość per krawędź)
  i 2,4 m na granicy bloku — szorstka trawa z suchymi kępami.
- Tiery: struktura i kolory liczone w każdym tierze z `_GROUNDMASKS` (Low też — to ALU, bez fetchy); detal pikselowy
  i tak wygasa z rozmiarem piksela.

### 2. Układ: okręgi i wydłużone bloki (shader + `vegetation.field_layout`, lustro 1:1)
- Okręg = komórka Woronoja siatki 1 600 m (`KF_DISTRICT_M`): jeden kierunek długiej osi pasów (pola jednej wsi).
- Blok = komórka Woronoja siatki 300 m w ramie okręgu rozciągniętej 3× wzdłuż pasów (`KF_STRETCH`) — blok ~900 × 300 m;
  kierunek pasów bloku ±5,7° od osi okręgu; szerokość pasa 16–40 m (było 22–46). Odległość do granicy bloku liczona
  w metrach (dwusieczna Woronoja afinicznego przeliczona na teren), granica okręgu też jest granicą bloku.
- Wszystkie punkty siatek względem originu regionu / ziarna okręgu (całe metry, dokładne w fp32), więc współrzędna pasa
  ma precyzję cm 700 km od początku układu.
- Hash bloków: indeksy + 4 096 (`KF_BLOCK_HASH_OFS`) — koniec bliźniaczych bloków.

### 3. Rośliny mozaiki (`vegetation.field_plants`, wywołanie w `vegetation.place`)
- Miedze: kandydat co 7 m krawędzi pasa (siatka 4 m rzutowana na najbliższą krawędź — każda komórka znaleziona przy
  dowolnym obrocie), odcinki 50 m: 9 % to ciągi krzewów (85 % kandydatów), poza nimi 0,4 %. Gatunki: krzew 76 %, brzoza
  młoda 12 %, sosna młoda 5 %, brzoza 4 %, olsza 3 % (wierzba, grusza — brak prototypów).
- Ugory: samosiew 30 % węzłów siatki 12 m EPSG:2180 w 25 % płatów 36 m (brzoza młoda, sosna młoda, krzew).
- Tylko w kaflach wiejskich (nie `bialystok-*`: trawiaste BDOT w mieście to trawniki i nieużytki), w wielobokach
  OT_PTTR_A ≥ 2 ha, ≥ 8 m od granicy wieloboku (tam reguła marginesu ADR 0298) i ≥ 8 m od drogi / podwórza. Pozycja,
  gatunek i ziarno rng z hasha układu — ta sama roślina, który kafel by jej nie budował.

## Pomiary (edytor, visual-qa High 1920×1080, `-Pc`, Win64; nie build playera)
Przed = dane i shader z main (chunki z kopii `before-world`), po = ta gałąź po przebudowie kafli (r2). Dowody:
`artifacts/fields-s24/vqa/{before,after,after-r1}/<kafel>-<clear|overcast>/`, zestawienia `sbs_knyszyn-w_clear.jpg`,
`sbs_dk65-07_clear.jpg`, `after_knyszyn-w_overcast.jpg`, podgląd palety z góry `preview/palette_topdown{,2,3}.png`.

| | przed | po | źródło |
|---|---|---|---|
| knyszyn-w: rośliny mozaiki (miedze / ugory) | 0 / 0 | 1 414 / 27 (krzew 1 023, brzoza młoda 199, sosna młoda 99, brzoza 62, olsza 50) | `streetscape_qa.json`, `instances_*.json` |
| dk65-07: rośliny mozaiki | 0 / 0 | 462 / 4 | jw. |
| knyszyn-w, 6 kamer: instancje / draw calle / trójkąty instancji | 106–357 / 35–95 / 4,2–48,4 tys. | +30…+81 / +0…+3 / +0,4…+1,2 tys. (max +11 %, `dk65-fields-nw`) | `stats.txt` |
| dk65-07, 6 kamer | 596–1 672 / 48–162 / 11–145 tys. | +0…+32 / 0 / +0…+0,4 tys. | `stats.txt` |
| trójkąty siatek (teren, drogi) na kamerach | — | bez zmian (shader: tylko ALU, 0 fetchy) | `stats.txt` trisExact |
| pytest (`test_fields_0334` + 7 plików roślinności / determinizmu) | — | 120 passed | lokalnie |

Ocena wzrokowa (własna, porównanie z 4 zdjęciami CC BY ściernisk z sierpnia — `Data/raw/refs/commons-fields-summer` — i
zdjęciami właściciela 10/11 dla układu): knyszyn-w — pola czytają się jako mozaika pasów: złote ścierniska z wałami
słomy, zboże stojące, brunatne talerzowane, ciemna kukurydza, łąki w kilku tonach, z kabiny i z góry, w clear i overcast;
miedza z pojedynczą brzozą przy drodze. dk65-07 — kamery patrzą głównie na łąki przy szpalerze DK65: zmiana tonu łąk
(oliwkowe / siano / świeży odrost), z kabiny mała. r1 → r2: rozsiane równomiernie samotne sadzonki (wrażenie „posypki”)
zastąpione ciągami krzewów na rzadkich odcinkach miedz i płatami samosiewu na ugorach.
Ocena `visual-critic` — do zlecenia przez lidera (subagent nie tworzy subagentów).

## Skutki dla innych kafli
- Shader działa od razu na każdym kaflu z flagą pól (wszystkie kafle trasy są po ADR 0298) — wystarczy build; w kaflach
  `bialystok-*` trawiaste BDOT (poza OSM `landuse=grass` / parki) też dostaje odmiany łąk, jak od ADR 0298.
- Rośliny miedz / ugorów wymagają przebudowy kafli wiejskich (`build_world.py` + import). Przebudowane tu: `knyszyn-w`,
  `dk65-07`. Do przebudowy (51 kafli z polami, szacunek miedze/ugory bez testu drogi: `artifacts/fields-s24/tile_survey.json`):
  dk65-01…11, dk65-monki-01…07, dk8-korycin-01, dk8-s8-jeroniki, dk8-wasilkow-01…03, dw671-jasionowka-01,
  dw671-tykocin-01…09, knyszyn, knyszyn-s, monki, monki-e, s8-01…05, tykocin. Kafle `bialystok-*` (w tym C) — bez
  zmian danych (`test_export_is_deterministic` C nienaruszony).
- `KamionFieldMosaic(...)` ma nową sygnaturę (local, origin, …, out half4) — jedyne wywołanie w `WorldPBR.shader`.

## Otwarte
- Pomiar playera (build Windows, pc-metrics) na kaflu wiejskim z miedzami — lider przy buildzie #7/#8.
- Bele słomy na ściernisku po prasowaniu (krytyk) — brak modelu; osobne zadanie (Blender, LOD, instancje).
- Prawdziwe granice działek (EGiB / ULDK) i kierunek pasów prostopadły do ulicy wsi — brak danych w repo.
- Gatunki miedz: grusza polna, wierzba, dzika róża, tarnina — brak prototypów (dziś krzew / brzoza / olsza).

---

## Dopisek r2 (2026-11-25, agent fields2-s24) — miękkie obrysy pól, uwrocia, bruzdy, kępy pobocza, drzewa w kępach

Status: Proposed. Źródło: krytyk build #8 (`artifacts/critic-s24-build8/CRITIC.md`) P1#6 „pola: ostre prostokątne obrysy bez
miedz i bruzd” (klatki `t2370`, `t2810`) i P1#7 „powtarzalne sprity trawy na poboczu i samotne lizakowe drzewka na polach”
(`t1600`, `t1710`, `t1930`, `t2150`). Zmiana globalna: shader terenu (wszystkie kafle z flagą pól od razu po buildzie),
generator roślinności i flory pobocza (po przebudowie kafli).

### Przyczyny (odczytane z kodu i renderów „przed”)
1. **Krawędź pasa = linia od linijki.** Współrzędna pasa była liniowa, miedza miała stałą szerokość na całej długości i ostre
   brzegi, a uprawa stały kolor do samej miedzy.
2. **Zielona obwódka każdego wieloboku ornego.** Flaga pól w COLOR_0.b przechodzi na krawędzi wieloboku z 1,00 (orne) do
   ≤ 0,80 (pobocze) przez jedną komórkę siatki (1 m przy drogach, 8 m dalej) i po drodze mija 0,90 — kod łąki. Shader
   rysował tam prosty pas soczystej zieleni „łąki po pokosie”; to on jest bliską krawędzią żółtego prostokąta w `t2370`.
3. **Brak bruzd.** Jedyny drobny wzór (rzędy ścierniska 0,16 m) był filtrowany izotropowym rozmiarem piksela, który z kabiny
   (kąt padania kilka stopni) jest rzędu 0,2–0,5 m już 20 m od drogi; talerzowane było jednolitym brązem bez orki.
4. **Kępy pobocza:** atlas `verge_tufts` miał 8 kęp o jednym charakterze, kępy skarp stały co 1,1–2,6 m bez przerw, a stopa
   karty była przyciemniona do 0,41 (okluzja 0,62 × ściemnienie tekstury 0,66) — ciemny klon na jaśniejszej darni.
5. **Samotne drzewka:** 565 z 708 samotnych roślin na polach `knyszyn-w` (najbliższy sąsiad > 15 m) to samosiew ADR 0298
   (źródło `bdot:<id>:self`: 2 % węzłów siatki 14 m w środku pola i 35 % w pasie 8 m od każdej granicy wieloboku — czyli
   sadzonka co ~40 m), 90 to pojedyncze krzewy miedz.

### Decyzja
**Shader (`KamionFieldMosaic.hlsl`, `WorldPBR.shader`; nadal 0 fetchy, 0 słów kluczowych, 0 draw calli):**
- Krawędź pasa faluje: do współrzędnej w poprzek pasa dodany szum wartości 71 / 17 / 5 m o amplitudzie 1,8 / 0,5 / 0,12 m
  (`KF_WOB_*`, lustro `vegetation.field_wobble`). Pierwsza próba (47 m / 2,6 m + 17 m / 1,0 m) odrzucona po renderze: bruzdy
  oglądane wzdłuż wyginały się jak słoje drewna.
- Miedza tylko między dwoma gospodarstwami (jeden z dwóch pasów ma własne użycie; ~20 % szwów bez miedzy), szerokość
  pulsuje wzdłuż krawędzi (szum 5 m i 1,7 m), brzeg nie ostrzejszy niż 0,3 m, uprawa rzednie ku miedzy na 0,6–2,8 m;
  między dwiema łąkami miedza to tylko szorstsza trawa (siła 0,35). Ton miedzy mniej brunatny (suchość 0,32 zamiast 0,50).
- Granica bloku: pas trawy o połówce szerokości 1,2–1,9 m, na 40 % granic droga polna (dwie piaszczyste koleiny co 1,6 m).
- Granica wieloboku (przyczyna 2): gradient flagi liczony z pochodnych ekranowych; rampa poniżej progu ornego jest
  marginesem szorstkiej trawy, próg wędruje o ~±0,5 m (poszarpany brzeg uprawy), uprawa rzednie 2,5 m przed nim.
- Uwrocie tam, gdzie granica bloku przecina pasy: szerokość 5,9–12,2 m na blok, **wszystkie rzędy / wały / bruzdy użycia
  biegną w nim wzdłuż granicy** (obrót o 90°), a na linii uwrocia co przejazd pętla dwóch śladów kół (70 % pętli, promień
  0,30–0,42 szerokości przejazdu, siła zależna od szumu).
- Kierunkowa struktura wzdłuż pasa: smugi przejazdów (komórki 2,6 × 60 m) i drobne smugi siewnika (0,55 × 18 m, Medium+),
  rzędy / bruzdy z przyciemnieniem dna i **nachyleniem dodanym do normalnej świata**: orka 0,40 m (połowa pasów
  „talerzowanych” jest teraz orką: ciemniejsza gleba 0,105 / 0,079 / 0,054), ściernisko 0,25 m, rzepak 0,33 m, talerzowane
  0,22 m, kukurydza 0,75 m (tylko ślad). Głębokość bruzdy łamana szumem 1,7 / 5 m i faza przesuwana o ułamek okresu (czysta
  sinusoida wyglądała jak sztruks). Wzory rzędowe filtrowane rozmiarem piksela **w poprzek rzędów** (z `ddx/ddy` pozycji),
  więc rzędy oglądane wzdłuż zostają widoczne daleko w głąb pola, a w poprzek gasną przed aliasingiem.
- Sygnatura: `KamionFieldMosaic(local, origin, footprint, enDx, enDy, mbD, driftN, inout m, out field, out slopeEN)` —
  jedyne wywołanie w `WorldPBR.shader`. Wszystkie wartości `WORKING_VALUE`.

**Generator (`vegetation.py`, `verge_flora.py`):**
- `field_layout` zwraca układ z falowaniem (lustro shadera); rośliny miedz stoją na falującej krawędzi (punkt stały, błąd
  < 1 cm) i tylko na szwach z miedzą.
- Ciągi krzewów miedz: zarośla po ~3 komórki (60 % grup, 85 % kandydatów) z rzadkimi odcinkami między nimi (12 %), krzew
  towarzyszący 1,2–2,6 m obok co drugiej rośliny zarośli; pojedyncze rośliny miedz 0,2 % (było 0,4 %).
- **Kępy śródpolne**: siatka 180 m EPSG:2180, 45 % komórek, 3–8 roślin (brzoza 30 %, krzew 30 %, młoda brzoza 15 %, olsza
  15 %, sosna 10 %) dociągniętych do najbliższej krawędzi pasa, rozrzut 5 m wzdłuż / 1,2 m w poprzek.
- Samosiew ADR 0298 w wielobokach ≥ 2 ha kafli wiejskich: 0 w środku pola, przy granicy wieloboku tylko w płatach 60 m
  (25 % płatów, 90 % kandydatów) zamiast 35 % wszędzie. Kafle `bialystok-*` bez zmian (ten sam strumień losowy).
- `verge_flora` r4: atlas 2048 × 512 (było 1024 × 512), 16 kęp o własnym charakterze (gęstość, udział suchych źdźbeł,
  pochylenie, rozrzut, ton); kępy skarp w grupach (szum 9 m, próg 0,60, krok 0,45–1,2 m, poza grupą 10 % kandydatów),
  wysokość ×0,7–1,4, ton na kartę 0,78–1,04, stopa jaśniejsza (okluzja 0,76, ściemnienie 0,76).

### Pomiary (edytor, visual-qa High 1920×1080 `-Pc`, Win64; nie build playera)
Przed = main `9dddeb05b` (kafle i shader z kopii worktree), po = gałąź `fields2-s24` po przebudowie `knyszyn-w`, `dk65-07`.
Kafle „przed” były zbudowane starszym generatorem niż `9dddeb05b`, więc różnice instancji mogą zawierać też inne zmiany maina.

| | przed | po | źródło |
|---|---|---|---|
| knyszyn-w: samotne rośliny na polach (sąsiad > 15 m), 3,63 km² | 708 (195 / km²) | 263 (72 / km²) | `artifacts/fields2-s24/lone_trees.py` |
| dk65-07: jw., 1,56 km² | 311 (199 / km²) | 131 (84 / km²) | jw. |
| knyszyn-w: miedze / kępy / ugory (`field_plants`) | 1 414 / 0 / 27 | 940 / 231 / 26 | `streetscape_qa.json` |
| knyszyn-w: samosiew `:self` (instancje) | 1 295 | 683 | `instances_*.json` |
| dk65-07: miedze / kępy / ugory; samosiew | 462 / 0 / 4; 785 | 342 / 126 / 4; 449 | jw. |
| knyszyn-w: karty kęp skarp / trójkąty flory pobocza | 2 363 / 23 002 | 1 935 / 22 146 | `world_manifest.json` |
| dk65-07: jw. | 851 / 8 048 | 717 / 7 780 | jw. |
| knyszyn-w, 6 kamer: trójkąty siatek | 286–772 tys. | −321…0 | `vqa/{before,after}/<kafel>-clear/stats.txt` |
| knyszyn-w, 6 kamer: instancje / draw calle instancji / trójkąty instancji | 137–428 / 37–99 / 5,0–50,3 tys. | −62…−22 / −6…0 / −1 880…+448 (+1,4 % `dk65-polna`) | jw. |
| dk65-07, 6 kamer: jw. | 607–1 660 / 47–163 / 11,3–143,8 tys. | −57…−6 / −3…+1 / −998…−72 | jw. |
| najgorsza kamera budżetu klatki (`mesh_budget.frame_estimate`, tris High) | knyszyn-w 1 097 014, dk65-07 1 020 480 | 1 096 751, 1 013 392 | `streetscape_qa.json` |
| pamięć świata High (`WORLD_MEMORY`) | knyszyn-w 137,3 MB, dk65-07 148,6 MB | 137,2 MB, 148,5 MB | logi importu |
| pytest (`test_fields_0334` 10, bele 0346, pobocza 0324, roślinność, budżet 0221, determinizm jednostkowy) | — | 50 passed | `artifacts/fields2-s24/logs/pytest.log` |

Koszt shadera: +2 szumy wartości zawsze, +2 na Medium+ (po 4 hashe), kilka `frac` / `sincos`; bez fetchy. Czas GPU na
playerze **niezmierzony** (`UNVERIFIED`) — do pomiaru `pc-metrics` na kaflu wiejskim przy następnym buildzie.

Dowody: `artifacts/fields2-s24/vqa/{before,after}/<kafel>-<clear|overcast>[-extra]/`, zestawienia przed | po
`artifacts/fields2-s24/sbs/*.jpg` (kamery kontrolne z kabiny oraz kamery polowe z `cams_<kafel>.json` przez `-Gate3`:
`f2_cab_*` z kabiny w bok, `f2_rows_*` wzdłuż rzędów, `f2_cross_*` w poprzek pasów, `f2_obl_*` ukośnie z góry), podgląd logiki
shadera z góry `preview/r2_*.jpg` (`preview_r2.py`, port numpy wersji sprzed dostrojeń), atlas kęp `verge_tufts_preview.jpg`.

Ocena wzrokowa (własna; porównanie z 4 zdjęciami CC BY ściernisk z sierpnia `Data/raw/refs/commons-fields-summer`):
`dk65-fields-nw`, `route-s1278` — zniknęła zielona obwódka i prosta krawędź żółtego pola przy drodze (teraz poszarpany
margines trawy), orka czyta się jako orka (bruzdy z kabiny), pola bez „posypki” sadzonek, przy miedzy kępa trzech drzew;
kępy pobocza jaśniejsze, różne, w grupach z przerwami. Słabiej: bruzdy orki z kabiny pod niskim kątem są nadal dość
regularne; miedza między pasami soczystej trawy w uprawie (widok z góry `f2_obl_headland`) pozostaje wyraźnym ciemniejszym
pasem; dalekie krawędzie pól (> 300 m) są nadal proste — falowanie ±1,2 m ginie poniżej piksela.
Tier Low (`vqa/after/knyszyn-w-clear-LOW`, ścieżka bez `_KAMION_WORLD_DETAIL`): mozaika, margines i bruzdy renderują się
poprawnie. Kompilacja wariantu Android (GLES / Vulkan) **niesprawdzona** (`UNVERIFIED`; shader używa tylko ALU i `ddx/ddy`).
Ocena `visual-critic` — do zlecenia przez lidera (subagent nie tworzy subagentów).

### Skutki dla innych kafli
- Shader: od razu na każdym kaflu z flagą pól (także `bialystok-*`), bez przebudowy.
- Rośliny pól (kępy, zarośla, samosiew w płatach) + nowe kępy pobocza: przebudowa 44 kafli wiejskich — przebudowane tu:
  `knyszyn-w`, `dk65-07`; pozostałe 42: dk65-01…06, dk65-08…11, dk65-monki-01…07, dk8-korycin-01, dk8-s8-jeroniki,
  dk8-wasilkow-01…03, dw671-jasionowka-01, dw671-tykocin-01…09, knyszyn, knyszyn-s, monki, monki-e, s8-01…05, tykocin.
- Tylko kępy pobocza (odcinki bez krawężnika): 10 kafli miejskich — bialystok-bojary, -dojlidy, -industrial-c, -kleeberga,
  -knyszynska, -krywlany, -maczka, -mickiewicza, -porosly, -wygoda. Do przebudowy kafel zachowuje własny stary atlas
  (`textures/verge_tufts.png` jest per region), więc nic się nie psuje. Kafel C przebudowany na tej gałęzi
  (`test_world_roads::test_export_is_deterministic` porównuje z zapisanym manifestem): 26 z 64 chunków zmienionych, karty
  kęp skarp 1 130 → 985, najgorsza kamera budżetu `stretch_04` 1 996 321 ≤ 2 000 000. Pozostałe 9 miejskich — do fali
  przebudowy. Lista maszynowa: `artifacts/fields2-s24/tile_list.json`.
- Bele (ADR 0346) czytają `field_layout` — po falowaniu krawędzi stoją nadal ≥ 3,5 m od miedzy (test 0346 zielony).

### Otwarte (r2)
- Pomiar playera (czas GPU shadera terenu na kaflu wiejskim, High i Low).
- Prawdziwe granice działek (EGiB / ULDK) — nadal brak danych; krawędź wieloboku BDOT pozostaje prostą w skali > 10 m.
- Wysokość łanu (zboże stojące vs ściernisko jako geometria / paralaksa) i maszyny na polach — poza zakresem.

---

## Dopisek r3 (2026-11-25, agent fields3-s24) — flaga łąki, kukurydza i miedze jako geometria, kępy pobocza bez rytmu, koleiny

Status: Proposed. Źródło: krytyk `artifacts/critic-s24-wave10-pre/CRITIC.md` §1 (pola r2 = FAIL: P0 „idealnie prostokątna
zielona łatka” w `sbs/dk65-07_clear_f2_obl_maize`, kukurydzy w rzędach nie widać, #7 „ten sam sprite równo rozstawiony”,
pola bez miedz z kabiny, pasy „jak boisko golfowe”, ślady kół „jak namalowane”, kafelek trawy). Zmiana globalna: shader
terenu (od razu na każdym kaflu), generator (po przebudowie kafli), jedna linia importu obrzeża (`WorldEdgeBuilder.cs`).

### Przyczyny (zmierzone: `artifacts/fields3-s24/probe_glb.py`, `plot_b.py`, `project.py`, rendery `vqa/before*`)
1. **P0 nie był łatką danych, tylko regułą marginesu r2.** Kamery `-Gate3` są re-seatowane 2,5 m nad grunt
   (`Gate3Cameras.HeightAboveRoad`, każdy `kind` poza `photo_match`), więc „ukośna 38 m” patrzy z wysokości kabiny;
   prostokąt leży ~14 m od kamery, E 58 N 526: granica łąki (siano, flaga 0,90) i pola ornego (1,00). Flaga łąki 0,90 leży
   NA rampie siatki między 1,00 a każdą inną wartością, a `margin` r2 (gradient flagi z `ddx/ddy`, stały na trójkąt)
   malował komórki terenu na tej rampie jako szorstką trawę — twardy prostokąt kilku metrów przy schodkowej granicy
   rastra 1 m (w dalszych LOD terenu: wielkości komórki 2–8 m). Wierzchołki: `COLOR_0.b` 0,906 … 0,941 w pasie N 523–526.
2. **Kamery „maize” r2 nie patrzyły na kukurydzę** (`find_spots.py` liczył użycie przed ostatnim strojeniem układu):
   `dk65-07 f2_obl_maize` = łąka z sianem, `knyszyn-w f2_*_maize` = kukurydza, ale tylko jako płaski ciemnozielony kolor
   z rzędami 0,75 m — zero geometrii, 0 m wysokości.
3. **Kępy pobocza:** 16 kęp atlasu r4 miało JEDNĄ formę wzrostu (symetryczny wachlarz źdźbeł na prostej stopie), a karty
   stały krokiem 0,40–0,85 m wzdłuż dwóch linii (krawędź kruszywa, skarpa) z restartem co stację siatki.
4. **Miedze:** pas 1–2,6 m oglądany w poprzek z 2,5 m to włos, a filtr izotropowym rozmiarem piksela gasił go ~40 m od kamery
   także wtedy, gdy biegł wzdłuż widoku. Nic nie stało na miedzy poza rzadkimi krzewami (`field_plants`).
5. **„Boisko golfowe”:** nie pokosy, tylko smugi przejazdów — szum wartości na JEDNEJ siatce 2,6 m w poprzek rzędów jest
   quasi-okresową przemianą jasny / ciemny (sprawdzone kolorem diagnostycznym: pokosy łąk nie brały w tym udziału);
   do tego naprzemienne pasy kosiarki 2,8 m na trawach w uprawie i odroście.
6. **Koleiny dróg polnych:** dwa pasy `|d − 0,8| < 0,26` o stałej szerokości i jednej barwie, bez normalnej.
7. **Kafelek trawy w polach:** detal luminancji pola brany był z PIERWSZEJ próbki tekstury trawy (kafel 3 m), a nie z wyniku
   de-tilingu (druga, obrócona próbka).

### Decyzja
**Kontrakt flagi (`vegetation.FIELD_FLAG_B`, shader `KF_MEADOW_B0/B1`, `WorldEdgeBuilder`):** łąka = `COLOR_0.b` 0,00
(było 0,90), orne = 1,00, każdy inny grunt 0,07–0,80 (`GROUND_B_MIN`). Każda rampa poniżej kodu ornego opuszcza teraz
pole: między polem a łąką zostaje pas otwartej, szorstkiej trawy (rampa po wygładzeniu sigma 1,5 m). Shader czyta oba
kody — kafle jeszcze nieprzebudowane (łąka 0,90) zachowują zachowanie r2, z artefaktem P0 do czasu przebudowy. Obrzeże
kafla przenosi w pas zewnętrzny także kod 0,00 (`bc.b <= 8`).

**Generator pól (`vegetation.ground_masks`):**
- Poszarpany margines: uprawa kończy się 1 … 6 m przed linią wieloboku / pobocza (1 + 3,5·n64^1,5 + 1,5·n19 m, szum
  EPSG:2180 — zgodny na szwie kafli), każdy rodzaj BDOT osobno (między polem a łąką falisty pas szorstkiej trawy).
- Ścinki pasów: spójny kawałek jednego pasa mniejszy niż 600 m², odcięty obrysem (nie krawędzią kafla), staje się
  nieużytkiem. Pierwsze wartości (6 + 2 m, 2 500 m²) zabrały 41 % pól `dk65-07` i znikły pola przy drodze w
  `dk65-fields-nw` — odrzucone po renderze.
- Lustro warpu układu: `field_warp` / `field_unwarp`, `on_edge` (punkt stały falowania i warpu, 12 rund).

**Shader (`KamionFieldMosaic.hlsl`, `WorldPBR.shader`; nadal 0 fetchy, 0 słów kluczowych):**
- **Warp układu:** okręgi, bloki i szwy pasów szukane są w pozycji przesuniętej dwiema oktawami szumu 2D (230 m / ±5 m,
  53 m / ±1,5 m na oś); rzędy, wały i ścieżki liczone z pozycji nieprzesuniętej (r2: wyginane rzędy = „słoje”), więc
  przy wygiętej krawędzi rzędy wybiegają ukosem. Krawędź pola 300 m dalej przestaje być linią od linijki.
- Miedza filtrowana rozmiarem piksela W POPRZEK miedzy (jak rzędy od r2): oglądana wzdłuż zostaje ostrą linią do
  horyzontu. Szumy 1,7 m i 5 m gasną do średniej, gdy komórka spada poniżej ~2 px (mniej migotania dalekich pól).
- Smugi przejazdów: szeroka oktawa 7,3 m niesie większość tonu, smugi 2,6 m pojawiają się płatami (szum 17 / 71 m);
  amplituda na łąkach 0,05–0,07 (było 0,10–0,14). Pasy kosiarki 2,8 m usunięte.
- Pokosy (łąka skoszona / siano): każdy wał przesunięty do ±1,1 m, własna szerokość 0,35–1,25 m, 40 % wałów brak, przerwy
  wzdłuż wału; filtr pudełkowy zachowuje energię (wał 0,8 m pod pikselem 3 m to słaby ton, nie pas 3 m).
- Ruń (trawy w uprawie, łąki, pastwisko): płaty bujniejsze / suchsze 1–17 m ze zmianą BARWY (mapa makro A + szum 5 / 17 m);
  detal luminancji pola z trawy PO de-tilingu (`grassLum`).
- Koleiny drogi polnej: środek wędruje ±0,25 m, połówka szerokości 0,05–0,30 m, zarastają odcinkami (szum 17 / 9 m),
  miękki postrzępiony brzeg, wilgotne ciemniejsze dno i jasny suchy rant, garb z wyższą trawą między koleinami, profil
  koleiny pochyla normalną (wygasa poniżej ~1 px).
- Sygnatura: `KamionFieldMosaic(local, origin, footprint, enDx, enDy, mbD, driftN, mott, inout m, out field, out slopeEN)`.

**Atlas i kępy pobocza (`verge_atlas.py` NOWY, `verge_flora.py` r5):**
- Atlas `verge_tufts` 2048 × 1024 (było 2048 × 512): 16 roślin o RÓŻNYCH formach wzrostu, każda malowana na własnym
  płótnie — kępa trawy, kępa sucha, źdźbła z wiechami, szczaw z rdzawymi kwiatostanami, wrotycz, krwawnik / marchew,
  bylica, cykoria; nisko: kępka, kępka sucha, rozeta babki, koniczyna, trawa położona, pojedyncze źdźbła, brodawnik,
  niski krwawnik — oraz górna połowa: rząd kukurydzy (4 komórki 1,6 × 2,4 m, dwie warstwy głębi).
- Jedna roślina na kartę; wybór formy z tabeli strefy (krawędź / skarpa / dno / miedza) z KOLONIAMI: bylina dominuje na
  odcinku ~23 m (waga ×10), poza nim jest rzadka (×0,2).
- Rozrzut: przerzedzony proces Poissona na globalnym kilometrażu (sloty 0,15 m, gęstość = iloczyn dwóch szumów 14 / 47 m,
  spadająca do zera na metry) — skupiska i luki, bez kroku i bez restartu na stacjach siatki; rośliny krawędzi w paśmie
  (do 0,42 m na kruszywie i do 0,9 m za nim, wysokość z terenu), skala 0,6–1,4 na kartę, obrót ±63° lub dowolny.

**Uprawy i miedze jako geometria (`field_crops.py` NOWY; materiał i atlas `verge_tufts`, warstwa `banks` = High, LOD0 / LOD1
kafla, bez cienia; tylko kafle wiejskie):**
- Kukurydza: co trzeci rząd (2,25 m) pasa kukurydzy to ciąg kart 3,2 m o wysokości 2,05–2,40 m (`WORKING_VALUE`:
  kukurydza pastewna w połowie sierpnia), dokładnie na rzędach shadera, z przesunięciem między rzędami, plus karty
  poprzeczne (34 %) zamykające korytarze. Tylko do 300 m od drogi; ≥ 1,6 m od szwu pasa, ≥ 2,8 m od granicy bloku.
- Ruń miedz: wysokie trawy / wiechy / bylica / wrotycz 0,3–1,3 m na szwach z miedzą (lustro `hasBaulk`) i na zewnętrznej
  części pasa granicy bloku (1,4–2,2 m, poza koleinami), w skupiskach (szum 13 / 41 m), do 110 m od drogi.

### Pomiary (edytor, visual-qa High 1920×1080 `-Pc`, Win64; nie build playera)
Przed = main `253e9c8b4` (kafle i shader z kopii worktree), po = ta gałąź po przebudowie `knyszyn-w`, `dk65-07` (build r3c).

| | przed | po | źródło |
|---|---|---|---|
| P0: prostokąt w `dk65-07 f2_obl_maize` | jest | brak | `sbs/dk65-07_clear_f2_obl_maize.jpg` |
| knyszyn-w: pola (komórki z flagą) / ścinki | 3 693 958 m² / — | 3 479 916 m² (−5,8 %) / 267 | `streetscape_qa.json` |
| dk65-07: jw. | 1 670 816 m² / — | 1 436 425 m² (−14,0 %) / 498 | jw. |
| knyszyn-w: karty flory pobocza / trójkąty | 11 501 / 23 002 | 13 237 / 26 474 | `world_manifest.json` |
| dk65-07: jw. | 4 024 / 8 048 | 4 699 / 9 398 | jw. |
| knyszyn-w: kukurydza (pasy / karty rzędów / poprzeczne), ruń miedz (rośliny / karty poprzeczne), trójkąty | 0 | 54 / 31 494 / 9 896, 11 200 / 3 312, 111 804 | `logs/build_r3c_*.log` |
| dk65-07: jw. | 0 | 84 / 23 454 / 7 283, 5 511 / 1 647, 75 790 | jw. |
| kafle (chunki) z węzłem `banks` | knyszyn-w 12, dk65-07 4 | 45, 34 | `world_manifest.json` |
| draw calle, kamery kontrolne (siatki + instancje) | — | dk65-07: +0…+2; knyszyn-w: +1…+3 (`route-s0710` +5 − 2) | `stats_before_after3.txt` |
| draw calle, kamery polowe `f2_*` / `f3_*` | — | +0…+10 (`dk65-07 f2_cross_ploughed` +8 + 2) | jw. |
| trójkąty siatek na kamerach | 190–812 tys. | −1 tys. … +39,5 tys. (`knyszyn-w route-s0710`, +5,1 %) | jw. |
| najgorsza kamera budżetu klatki (`mesh_budget.frame_estimate`, tris High) | knyszyn-w 1 097 660, dk65-07 1 014 973 | 1 107 535, 1 015 112 | `streetscape_qa.json` |
| pamięć świata High (`WORLD_MEMORY`) | knyszyn-w 137,2 MB, dk65-07 148,5 MB | 143,2 MB, 152,5 MB | logi importu |
| atlas `verge_tufts` | 2048 × 512 | 2048 × 1024 (pamięć GPU: niezmierzona, `UNVERIFIED`) | `verge_atlas.py` |

**Budżet draw calli „+≤2 na kamerę” NIE jest spełniony wszędzie:** kamery kontrolne `dk65-07` tak (+0…+2), `knyszyn-w`
do +3, kamery stojące w polu do +10 — każdy chunk z kartami upraw / miedz dostaje własny prymityw `banks` (ten sam
materiał co pobocze, więc bez nowego SetPass). Do decyzji lidera: zawęzić zasięgi (kukurydza 300 m, miedze 110 m od
drogi) albo przyjąć. Czas GPU shadera (+5 szumów wartości) na playerze niezmierzony (`UNVERIFIED`).

Dowody: `artifacts/fields3-s24/sbs/*.jpg` (156 zestawień przed | po, te same kamery co r2 + nowe `f3_*`; `only_*` =
kamery lotnicze `f3_air_*` z `seat: file`, tylko „po”), `vqa/{before,after3}/`, diagnostyka P0 `view/`, atlas
`verge_tufts_r5_preview.jpg`.

Ocena wzrokowa (własna; brak zdjęć referencyjnych właściciela dla pól — jak w r2): prostokąt P0 zniknął; z kabiny
kukurydza jest ścianą liści z wiechami (`f3_maize_chase`, `route-s1278`), pobocze ma rozróżnialne rośliny w skupiskach
z lukami, krawędzie ścierniska są wygięte, koleiny wędrują i zarastają. **Słabiej / nie zrobione:**
- z 14 m nad ziemią (`only_knyszyn-w_clear_f3_air_maize_low`) widać, że karty kukurydzy pokrywają tylko CZĘŚĆ pasa
  rysowanego przez shader jako kukurydza i czytają się jak labirynt żywopłotów — przyczyna luk nieustalona (maska orna
  w tym miejscu jest pełna, `view/b_flags_maize.png`); z kabiny niewidoczne;
- ruń miedz: 11 200 roślin w `knyszyn-w`, ale na miedzy z kamer `f3_baulk_*` w kadrze ich prawie nie ma — „miedze
  widoczne z kabiny” są zrobione tylko częściowo (linia miedzy ostra wzdłuż widoku, geometria nierówno);
- szczaw i wrotycz nadal wyraźnie odcinają się kolorem od runi (`dk65-fields-nw`);
- liście kukurydzy z bliska (< 5 m) są płaskie, malowane.
Ocena `visual-critic` — do zlecenia przez lidera (subagent nie tworzy subagentów).

### Skutki dla innych kafli
- Shader: od razu wszędzie; kafle nieprzebudowane zachowują kod łąki 0,90 i artefakt P0 na granicach pole / łąka.
- Przebudowa (flaga łąki, margines, ścinki, kępy pobocza, kukurydza, miedze): te same 42 kafle wiejskie co w r2
  (dk65-01…06, dk65-08…11, dk65-monki-01…07, dk8-korycin-01, dk8-s8-jeroniki, dk8-wasilkow-01…03, dw671-jasionowka-01,
  dw671-tykocin-01…09, knyszyn, knyszyn-s, monki, monki-e, s8-01…05, tykocin) + 10 miejskich `bialystok-*` (flaga łąki,
  margines i kępy pobocza; bez kukurydzy i miedz). Przebudowane tu: `knyszyn-w`, `dk65-07`. Lista: `tile_list_r2.json`.
- Kamery `-Gate3`: każdy `kind` poza `photo_match` jest sadzany 2,5 m nad gruntem — kamery „ukośne z góry” r2 były
  widokami z wysokości kabiny; prawdziwy widok z góry wymaga `"seat": "file"`.

### Otwarte (r3)
- Luki kart kukurydzy i nierówna ruń miedz (wyżej); pokrywa łanu z góry (dziś tylko rzędy kart).
- Pomiar playera (czas GPU terenu, pamięć atlasu), wariant Low / Android (`UNVERIFIED`).
- Lasy i zagajniki znikają w kamerach patrzących stromo w dół (instancje / HLOD: 233 instancje w `f2_obl_maize`) — poza
  zakresem, do sprawdzenia przez rendering.

### Testy i kafel C (r3)
- pytest (`artifacts/fields3-s24/logs/pytest-r3.log`: budżet 0221, typologia 0238, world_v31, hero_bridge, pola 0334 + r3,
  bele 0346, pobocza 0324, roślinność, determinizm jednostkowy, far_field i in., 21 plików): 349 passed, 25 skipped,
  2 failed przed przebudową C; po przebudowie C `test_far_field` zielony, zostaje
  `test_trees_0347::test_corridor_to_tykocin_no_tree_enters_the_clearance_box[bialystok-industrial-c]` (2 drzewa w skrajni:
  klon E −682 N −1014, lipa E −477 N −650) — pada tak samo na kopii derived z main sprzed tej zmiany, generator drzew
  kafli miejskich nie był ruszany; przyczyna niezbadana. Długie testy (`test_world_roads`, `test_streetscape`) nie były
  (`logs/pytest-r3c-long.log`).
- `bialystok-industrial-c` przebudowany (1 139 s): najgorsza kamera budżetu `stretch_04` 1 996 321 → 1 996 877
  (limit 2 000 000 — zapas 3 123 trójkąty), flora pobocza 12 308 → 19 468 trójkątów, pola 683 288 → 508 997 m²
  (−25,5 %, 632 ścinki — w kaflu miejskim reguła ścinek zabiera dużo; do oceny na renderze C, którego tu nie zrobiono).

### r3b — budżet draw calli (uwaga lidera po r3: trasa / kabina ≤ +2, kamery polowe ≤ +4)
- Wszystkie karty chunka (kępy pobocza, kukurydza, miedze) były już JEDNYM prymitywem (`assemble`: chunk × warstwa ×
  materiał); koszt to 1 draw call na chunk, który wcześniej nie miał `banks`. Reguła (`field_crops.prune_sparse_chunks`,
  liczona per trójkąt jak podział eksportera, usuwa całe karty): chunk dostaje prymityw, gdy jego pobocze ma ≥ 60
  trójkątów albo wszystkie karty razem ≥ 4 000 (`CHUNK_MIN_TRIS`; 2 500 dawało +6 na jednej kamerze). Karta na granicy
  chunka zostawiała wcześniej 1–8 trójkątów u sąsiada = osobny draw call. Zasięgi: kukurydza 300 → 220 m, miedze 110 → 90 m.
- Wynik (`artifacts/fields3-s24/draw_table.py`, `stats_before_after4.txt`; draw calle siatek + instancji, przed → po):
  kamery trasy / kabiny (30): maks. +5 (r3) → **+1**; kamery polowe (60): maks. +10 → **+5** na jednej
  (`dk65-07 f2_cross_ploughed`: siatki +3, instancje +2 — instancje to inny rozkład roślin pól przy poszarpanym
  marginesie, nie karty), pozostałe ≤ +4. Chunki z `banks`: knyszyn-w 12 → 17 (r3: 45), dk65-07 4 → 8 (r3: 34).
- Koszt: karty upraw knyszyn-w 111 804 → 53 040 trójkątów (kukurydza 31 494 → 24 612 kart rzędów, ruń miedz 11 200 →
  9 553 roślin przed regułą chunków; reguła zdejmuje 36 298 trójkątów w 23 chunkach), dk65-07 75 790 → 31 084
  (zdjęte 29 434 w 24 chunkach) — kukurydza i miedze stoją tylko tam, gdzie jest ich dużo albo jest pobocze.
- Budżet klatki High: knyszyn-w 1 102 754, dk65-07 1 013 995 (przed r3: 1 097 660 / 1 014 973). Low: karty są tylko w
  warstwie `banks`, wariant Low kafla bierze `banks_low`, której te moduły nie zapisują — 340 237 / 233 577
  (przed: 340 114 / 252 951), zasięgu na Low nie trzeba zmniejszać. Pamięć świata High: 140,2 / 150,2 MB.
