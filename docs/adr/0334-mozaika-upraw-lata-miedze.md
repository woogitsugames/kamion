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
