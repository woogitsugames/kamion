# ADR 0305 — Dom Klattów ze zdjęć właściciela: dom z bali bielony, stara dachówka, ganek, płot (klattow-s24)

Status: Proposed, 2026-11-19 (agent klattow-s24; numer wskazany przez lidera).
Powiązane: ADR 0287 (nadpisania punktów orientacyjnych Knyszyna, deski `wood_siding`), 0295 (dom drewniany z reguły),
0298 (kolory desek), 0227 (autorskie budynki Knyszyna: kościół, urząd), D51 (rozpoznawalność).
Referencje: zdjęcia kolegi właściciela `Data/raw/refs/owner-knyszyn-klattow-2026-11-19/klattow-01…05` (zgoda właściciela
19.11.2026: tylko oglądanie i pomiar; **żaden piksel nie trafia do gry ani do gita**).

## Kontekst

Dom Klattów (ul. Kościelna, BDOT `2002917F-2F22…`, OSM way 294345657 `material=wood`) był od ADR 0287 domem drewnianym
z reguły: surowe brązowe deski poziome, dach z czerwonej dachówki z losowania, 3–4 okna z zestawu fasad, ganek jako
występ bryły. Wpis nadpisania sam mówił „ESTIMATED: plank colour (dark brown)” i prosił o zdjęcie. Zdjęcia właściciela
pokazują co innego: dom z bali **bielony wapnem**, szczyty z pionowych białych desek, stara dachówka esówka, ganek
z kratką, ciemnobrązowe okna ze szprosami, płot sztachetowy przy chodniku. Reguła `dom_drewniany` tego nie odda —
potrzebny autorski obiekt, tak jak kościół i urząd (ADR 0227).

## Decyzja

### 1. Autorski generator budynku (`tools/worldgen/streetscape/knyszyn_dom_klattow_0305.py`)
Ten sam mechanizm co `knyszyn_townhall_0227`: `hero_targets()` wyłącza fasadę z reguły (zostaje pryzma kolizyjna obrysu
i maski terenu), `build()` dokłada siatkę do warstw `buildings` (LOD0, treść High / PC) i `buildings_low` (LOD1).
Obiekt powstaje wyłącznie z danych i stałych w kodzie — przeżywa każdy reimport; gdy obrys w danych przestanie być
„długim domem z jednym gankiem”, generator się wyłącza i wraca dom z reguły (nadpisanie `look-dom-klattow-wooden`,
teraz białe deski `wood_planks_white` zamiast brązowych).

| Element | Źródło | Wartość |
|---|---|---|
| Bryła, ganek | BDOT10k (SOURCED) | korpus 21,10 × 7,84 m; ganek 2,7 × 2,0 m, środek 10,35 m od zachodniego narożnika ściany od ulicy |
| Okap, kalenica | GUGiK LoD2 2017 (SOURCED) | okap 2,22 m → górny bal 2,25 m; kalenica 6,06 m → 6,05 m; spadek 39,7° |
| Okna od ulicy (6) | zdjęcie 01, skala 0,0213 m/px z długości ściany, względem ganku (ESTIMATED ±0,3 m) | −8,65 / −4,98 / −3,19 / +2,34 / +4,45 / +8,12 m; 0,95 × 0,97 m, nadproże pod okapem |
| Ściana od podwórza: 3 okna, drzwi, 3 okna | zdjęcie 05 (dopasowanie rzutowe), zdjęcie 03 potwierdza kolejność (ESTIMATED ±0,4 m) | od wschodniego narożnika 3,26 / 6,87 / 9,18, drzwi 12,06, 14,69 / 16,30 / 18,85 m |
| Szczyt wschodni | zdjęcia 03–05 | 2 okna parteru ±1,98 m od osi, okno strychu z daszkiem, daszek okapowy 0,55 m z blachy, pionowe białe deski, białe wiatrownice |
| Szczyt zachodni | brak zdjęcia | lustrzane odbicie wschodniego (ESTIMATED) |
| Kominy (2) | zdjęcie 01 + ortofoto 2025 (ESTIMATED ±0,5 m) | −2,35 / +0,55 m od osi ganku, na kalenicy |
| Ganek | zdjęcia 01, 04 | słupki 10 cm, dół z desek, kratka ukośna (158 listew jako geometria), dach dwuspadowy z dachówki, białe wiatrownice, drzwi czerwonobrązowe |
| Płot | zdjęcie 01 | sztachety 9 cm co 14 cm, 1,05 m, dwie łaty, słupki co ≤ 2,4 m, na linii czoła ganku; 2,6 m za narożnik zachodni, 4,5 m za wschodni |
| Podmurówka | zdjęcie 05 | kamień polny 0,30 m |

Wymiary elementów (deski, listwy, przekroje) to `WORKING_VALUE` odczytane ze zdjęć. Bez tabliczek, numerów, napisów.
Płot stoi tylko tam, gdzie cały pas między ścianą a sztachetami jest wolny od obrysu jezdni / chodnika (0,15 m zapasu);
inaczej linia cofa się co 0,1 m, a poniżej 0,8 m płotu nie ma (raport `streetscape_qa.json`).

### 2. Materiały (bez pobrań — zestawy proceduralne, licencja: własne, kod w repo)
- **`log_whitewash`** (nowy zestaw modulacyjny, `sets_facade.log_whitewash`, kafel 4,0 × 2,2 m = cała wysokość ściany):
  dziesięć wieńców bali 0,20–0,24 m, falujące fugi z pakułami, pęknięcia wzdłuż włókien, chmury pędzla, zabrudzony
  i łuszczący się dół. Materiał `log_wall_white` (liniowo 0,66 / 0,65 / 0,61).
- **`fieldstone`** (nowy, kafel 2,4 × 0,6 m): otoczaki 0,15–0,30 m w zaprawie, wilgotny dół. Materiał `fieldstone_plinth`.
- **`wood_planks_white`**, **`wood_planks_stain`** — istniejący skan CC0 `wood_siding` (Poly Haven `raw_plank_wall`, wpis
  w `docs/LICENSES.md` od ADR 0287) pod białą farbą (szczyty, wiatrownice, deski czołowe) i czerwonobrązową bejcą (ganek, płot).
- **`roof_tiles_old`** — istniejący zestaw `roof_tiles` (esówka: fala 0,20 m, rząd 0,35 m), kolor pomarańczowo-brązowy,
  silny dryf tonu w małej skali (`macro` 3,5 m / 0,34) = łaty starej dachówki. Zielonego mchu dryf jasności nie da (otwarte).
- **`wood_trim_brown`** — płaski ciemny brąz stolarki (elementy 2–9 cm).
- `log_wall_` i `fieldstone_` dopisane do `_TINT_LINEAR` (kolor liniowy, jak tynki i dachy).
Poly Haven / ambientCG nie mają skanu bielonej ściany z bali; zestaw proceduralny daje kontrolę nad wysokością wieńców
i zabrudzeniem dołu. Wszystkie kolory `WORKING_VALUE` do oceny właściciela.

### 3. Reguła ogólna „dom z bali bielony” — NIE wprowadzona (brak danych)
Sprawdzone na danych Knyszyna: w OSM (`podlaskie-261108.osm.pbf`) znacznik `material` / `building:material` ma **jeden**
budynek miasta — Dom Klattów; BDOT10k nie niesie materiału ścian; `buildings.geojson` nie przenosi znaczników materiału
z OSM (otwarte w ADR 0295). Masowa zmiana bez danych byłaby zgadywaniem. Zamiast tego:
- `wood_planks_white` jest dozwoloną ścianą nadpisania (`HOUSE_WALL_OVERRIDES`) — każdy dom drewniany, który właściciel
  lub zdjęcie z otwartej licencji pokaże jako biały, dostaje wpis w `overrides.yaml` (deski, nie bale);
- `log_wall_white` zostaje materiałem obiektów autorskich (kafel = wysokość ściany parterowej; reguła `wood_wall`
  zakłada kafel desek 6,0 × 2,6 m);
- droga do reguły: przeniesienie `building:material` / `building:colour` z OSM do `buildings.geojson` + uzupełnienie
  znaczników w OSM dla Knyszyna i Tykocina (praca terenowa właściciela lub Mapillary) — osobne zadanie geo-worldgen.

### 4. Lamus przy plebanii (zdjęcie 02) — tylko nadpisanie danych
Budynek zidentyfikowany na ortofoto (BDOT `40f8044a…6fe1`, „budynek gospodarczy”, 6,7 × 12,1 m, jedyny ciemnoszary dach
czterospadowy między frontem kościoła a Kościelną). W OSM nie ma go jako osobnego obiektu ze znacznikami. Wpis
`look-lamus-plebanski`: dom drewniany z brązowych desek, dach czterospadowy, wysokość 6,4 m (ESTIMATED ze zdjęcia).
Gont i podcień na słupach z mieczami wymagają osobnego obiektu autorskiego i zestawu gontu — otwarte.

### 5. Kamery kontrolne
`look_dom_klattow_street` (z drugiej strony Kościelnej, 18,4 m od ściany, 1,6 m, kadr zdjęcia 01) obok istniejącej
`look_dom_klattow`; `look_lamus_plebanski` (kadr zdjęcia 02, pozycja ESTIMATED).

## Budżet i walidacja
(uzupełniane pomiarem — patrz sekcja „Pomiary”)

## Otwarte
- Ocena właściciela i `visual-critic` (kolory bielenia, dachówki, bejcy; rozmieszczenie okien).
- Mech i porosty na dachu (kolor), krzew i pnącze przy ganku, tabliczka z numerem, słup energetyczny przy narożniku.
- Zachodni szczyt (brak zdjęcia), wnętrze ganku.
- Płot w LOD1 (treść Low / Medium) — pominięty; atlas `plot_kit` ma sztachety, ale w innym kolorze.
- Lamus: gont, podcień, surowe bale.
- Reguła ogólna dla bielonych domów — po danych (pkt 3).
