# ADR 0316 — Dachówka ceramiczna (esówka, karpiówka, zakładkowa) i rzędy płotów działek (roof-tiles-s24)

Status: Proposed, 2026-11-20 (agent roof-tiles-s24; numer wg HANDOVER „Ostatni przydzielony ADR” + gałęzie 0314 / 0315).
Powiązane: D93 pkt 2 (wygląd świata), ADR 0091 (dachy spadziste, zestaw `roof_tiles`), 0094 / 0097 (kalenica, paleta domów),
0305 (Dom Klattów, `roof_tiles_old`), 0114 / 0124 (atlas `plot_kit`), 0287 (dachy z ortofoto).
Referencje: zdjęcia kolegi właściciela `Data/raw/refs/owner-knyszyn-klattow-2026-11-19/klattow-01…05` (zgoda 19.11.2026:
tylko oglądanie i pomiar; **żaden piksel nie trafia do gry ani do gita**).

## Kontekst

1. **Dachy czytały się jako równa krata.** Zestaw `roof_tiles` z ADR 0091 to kafel 1,4 × 1,4 m: 7 × 4 identycznych dachówek
   z losowym tonem na idealnej siatce, wałki prawie niewidoczne (−6 % albedo, 12 mm), linia rzędu prosta i ciągła. Ten sam
   zestaw służył blachodachówce. Na połaci 8 × 20 m powtarzał się 6 × 14 razy; z ulicy widać szachownicę płaskich
   prostokątów (render rundy 2 ADR 0305 obok zdjęcia klattow-01: na zdjęciu dominuje profil — jasne grzbiety, ciemne
   koryta, ciemne „oczka” pod dolną krawędzią każdej dachówki — a ton zmienia się plamami po kilkanaście dachówek).
2. **Atlas płotów `plot_kit`.** Rząd `picket` (sztachety rdzawoczerwone) miał 16 % sztachet „bez farby” w neutralnej
   szarości 112 / 102 / 92; brązowy tint działki Klattów (G × 1,4, ADR 0305 r3) robił z nich oliwkowe. Brakowało sztachet
   z naturalnego / bejcowanego drewna, malowanych farbą olejną i siatki ocynkowanej — a to połowa płotów podlaskiej wsi.
   Atlas 2048² jest pełny (68 px wolnego paska), a regiony zbudowane wcześniej mają UV rzędów zapisane w siatkach.

## Decyzja

### 1. Zestawy PBR dachówek (`art-source/world/materials/_src/sets_roof.py`, proceduralne, bez pobrań)
Mapy modulacji jak pozostałe zestawy fasad (średnia liniowa 0,5 × 2 × kolor materiału), UV = metry połaci (u wzdłuż okapu,
v w górę). Wspólny mechanizm: rzędy rozwiązywane jako **zachodzące na siebie** (`_courses`: dolna krawędź każdej dachówki
ma własne przesunięcie, punkt należy do najwyższego rzędu, którego krawędź leży pod nim), powolne falowanie linii rzędów
i kolumn (`_warp`), ton w skupiskach (szum 0,5–2,8 m) + mniejszy ton własny dachówki, pojedyncze ciemne (nasiąknięte)
i jasne (wymienione) dachówki, własne pochylenie każdej dachówki w mapie normalnych, porosty (plamy dwuskalowe), zacieki
wzdłuż spadku, cień pod krawędzią rzędu wyżej.

| zestaw | kafel | wymiary (WORKING_VALUE w zakresie wyrobów) | cechy |
|---|---|---|---|
| `roof_tiles` (przepisany) | 4,2 m, 21 × 12 | esówka: krycie 0,20 m, rozstaw łat 0,35 m, wałek 28 mm | ciemne koryta, jasne grzbiety, **ciemny łuk pod wylotem każdego wałka** zamiast ciągłej kreski, zakład boczny |
| `roof_tiles_old` (przepisany) | 4,2 m, 21 × 12 (było 2,8 m) | jak wyżej | stara, kładziona ręcznie: krawędzie ±13 mm, ton ±13 % + skupiska, 14 % ciemnych, mech w korytach i na zakładach, skorupy porostów |
| `roof_karpiowka` (nowy) | 4,2 m, 23 × 28 | karpiówka 18 × 38 cm w łuskę, rozstaw 0,15 m, rzędy przesunięte o pół | łukowa dolna krawędź (strzałka 34 mm), styk 3 mm, ciemny klin między narożami |
| `roof_zakladkowa` (nowy) | 4,2 m, 18 × 12 | zakładkowa płaska (cementowa / angobowana): krycie 0,233 m, rozstaw 0,35 m, rzędy przesunięte o pół | dwa płaskie pola, żeberko, wałek zamka, nosek; równy ton fabryczny, pył przy żeberkach, jasne porosty |
| `roof_metal_tile` (= dawny `roof_tiles`) | 1,4 m, 7 × 4 | blachodachówka, moduł 350 mm | bez zmian: tłoczona blacha **jest** idealną kratą |

### 2. Materiały i reguła pokrycia (`streetscape/materials.py`, `buildings_mesh.py`)
- `roof_tiles_red` → `roof_tiles` (esówka), `roof_tiles_brown` → `roof_zakladkowa`, `roof_metal_graphite` → `roof_metal_tile`.
- Nowe: `roof_karp_red` (karpiówka; **kolor = `roof_tiles_red`**, więc LOD1 rysuje ją materiałem `roof_tiles_red` —
  `ROOF_LOD1`, zero dodatkowych drawów LOD1 i brak skoku tonu przy zmianie LOD), `roof_cement_grey` (szara dachówka
  cementowa; tylko z nadpisania `roof_material`).
- Paleta domów (`house_palette`: czerwona / brązowa dachówka / blacha, reguła sąsiadów) **bez zmian**. Po niej
  `roof_variant(klucz, materiał, drewniany)`: czerwona dachówka domu drewnianego → w 70 % `roof_tiles_old`; pozostałych
  domów → w 22 % `roof_karp_red`. Także na kolor odczytany z ortofoto (ortofoto mówi „czerwona dachówka”, nie „która”).
  Udziały WORKING_VALUE (brak inwentaryzacji).
- `roof_karp_red` i `roof_cement_grey` dopuszczone w nadpisaniu `roof_material`.

### 3. Kalenica / gąsiory (`streetscape/roofs.py`)
Geometria gąsiora z ADR 0094 bez zmian (6 trójkątów na odcinek kalenicy / naroża). Zmienia się UV: pasek 0,22 m był
obróconym wycinkiem zestawu w poprzek profilu. Teraz `RIDGE_UV[materiał]` wybiera pasek, który profilu nie przecina:
esówka — dokładnie jeden wałek (grzbiet w osi gąsiora, „oczka” zestawu kończą każdy gąsior co 0,35 m); karpiówka — pasek
6 cm ćwierć dachówki od osi (nigdy na styku), v × 0,43 (gąsior 0,35 m); zakładkowa — pasek płaskiego pola.

### 4. Atlas `plot_kit` (`streetscape/plot_kit.py`, `plots.py`)
- **Żaden istniejący rząd nie zmienia miejsca** (test `_OLD_ROWS`): regiony sprzed ADR zachowują poprawne UV.
- Ostatni wolny pasek (58 px, 1,3 m → 45 px/m w pionie; sztachety są pionowe, traci się tylko ostrość końcówek):
  `picket_wood` (sztachety bejcowane / naturalne, proste końce, wg klattow-01) i `picket_paint` (sztachety malowane,
  **neutralne** — kolor farby to tint przęsła `PICKET_PAINTS`: zielona, niebieska, ugier, kremowa, czerwonobrązowa,
  szaroniebieska; jedna farba na działkę; w rzędzie nie ma gołego drewna, więc nic nie oliwieje).
- `chainlink` przemalowany na neutralny cynk 104 / 108 / 106; zielona siatka powlekana z ADR 0114 = ten sam rząd pod
  tintem `CHAINLINK_GREEN` (styl `chainlink`), ocynkowana = styl `chainlink_galv` bez tintu. Region sprzed ADR pokazuje
  siatkę ocynkowaną na zielonych słupkach do czasu przebudowy.
- `picket`: sztacheta bez farby = ciepłe, zwietrzałe drewno 124 / 100 / 82, o połowę rzadziej.
- Udziały stylów (Podlasie, WORKING_VALUE): działki `old` — sztachety naturalne 16 %, malowane 12 %, rdzawe 14 %,
  siatka zielona 12 % / ocynk 10 %; boki: siatka pół na pół.
- Działka Domu Klattów: `plot_fence: {front: picket_wood, side: picket_wood}` bez tintu.

## Budżet (przed → po)

Runda r1 (build_world knyszyn + tykocin, import High, edytor, High clear 1920 × 1080; `artifacts/roof-tiles-s24/budget-r1.json`).
„Przed” = świat sprzed scalenia road-widen (D94), więc trójkąty warstw dróg / działek zawierają też tamtą zmianę; drawy od niej
nie zależą (te same materiały).

| kamera | draws | cień draws | tris |
|---|---|---|---|
| knyszyn look-dom-klattow-street | 556 → 562 (+6) | 231 → 237 | 1 495 926 → 1 494 635 |
| knyszyn look-roofs-above | 542 → 548 (+6) | 225 → 231 | 1 618 590 → 1 616 863 |
| knyszyn gardens-tykocka-eye | 725 → 730 (+5) | 141 → 144 | 1 538 467 → 1 535 523 |
| knyszyn tykocka-into-town | 746 → 750 (+4) | 162 → 165 | 1 410 513 → 1 407 918 |
| knyszyn look-wooden-house-brown | 491 → 497 (+6) | 180 → 189 | 1 506 486 → 1 504 748 |
| tykocin look-tykocin-roofs-above | 309 → 311 (+2) | 336 → 348 | 914 027 → 912 990 |
| tykocin look-tykocin-rynek-s | 418 → 423 (+5) | 318 → 324 | 1 193 695 → 1 191 880 |
| tykocin look-tykocin-zlota | 332 → 335 (+3) | 204 → 210 | 1 035 051 → 1 034 207 |

- Drawy: +0 … +7 na 13 kamerach (≤ +1,7 %), cień +3 … +12 — to `roof_karp_red` (LOD0) i `roof_tiles_old` w kaflach.
  Wszystkie kamery ≤ 750 draws i ≤ 1,62 mln tris (hipoteza docs/06 §6 High: 700–1000 / 1,5–2 mln).
- Kafel knyszyn: budynki LOD0 673 066 → 672 948, LOD1 110 065 → 110 051 (bez nowej geometrii; różnica = road-widen);
  materiały w kaflach (suma po 64) 1 513 → 1 533, maks. 73 → 74; `roof_karp_red` w 19 kaflach, `roof_tiles_old` 1 → 3.
  Tykocin: 1 360 → 1 379, maks. 67 → 68; `roof_karp_red` w 16 kaflach, `roof_tiles_old` w 1.
- Płoty: 0 drawów, 0 trójkątów, ten sam atlas 2048² (kafle z `plot_kit`: 32 → 32, 27 → 27).
- Pamięć tekstur (szacunek ASTC z mipami wg `materials_spec.json`, tier High): zestawy dachów 3,11 MB → 10,58 MB
  (+7,47 MB: `roof_tiles` 0,62 → 2,49 MB, nowe `roof_karpiowka` i `roof_zakladkowa` po 2,49 MB, `roof_metal_tile` 0,62 MB);
  raport importu knyszyn `pbr_textures_gpu_bytes_astc` 232,97 MB → 240,44 MB. Medium +1,46 MB, Low +0,26 MB.

## Wyniki

- Baseline: `artifacts/roof-tiles-s24/before/`; rundy tekstur t1–t4 (świat baseline) i runda r1 (pełna przebudowa):
  `artifacts/roof-tiles-s24/sbs/` — `klattow-street-vs-photo01-r1.jpg`, `crop-klattow-roof-t1/-t2/-r1.jpg`, `crop-above-k-r1.jpg`,
  `crop-above-t-r1.jpg`, `crop-wooden-r1.jpg`, `crop-gardens-r1.jpg`, `crop-zlota-r1.jpg`, `sheet-karp-t4.jpg`, `sheet-knyszyn-t3.jpg`.
- Dachy: szachownica płaskich prostokątów znikła; widać wałki, ciemne łuki pod krawędziami, ton w plamach; z 30–150 m bez mory.
  Dom Klattów obok zdjęcia 01: plamista stara esówka; zdjęcie ma nadal mocniejszy rysunek wałków (słońce z boku) i więcej
  drobnych ciemnych punktów.
- Płoty: działka Klattów — brązowe sztachety `picket_wood` bez oliwkowych; w kadrach r1 widać `picket_wood` przy domu
  drewnianym, siatkę ocynkowaną i zieloną. `picket_paint` (malowane) nie trafił w żaden kadr kontrolny — sprawdzony tylko
  testem i w podglądzie atlasu.
- Testy: patrz STATUS (pytest dotkniętych plików, EditMode Win64 1485 / 1383 passed / 1 failed poza gałęzią).

## Otwarte

- `visual-critic` na `sbs/*` (subagent nie uruchamia subagentów — po stronie lidera).
- Udziały pokryć i stylów płotów to WORKING_VALUE; brak zdjęć referencyjnych karpiówki / zakładkowej z Knyszyna i Tykocina
  (wzór: wyroby, nie konkretne dachy). `roof_cement_grey` czeka na nadpisania z ortofoto / zdjęć.
- Rzędy `picket_wood` / `picket_paint` mają 45 px/m w pionie (pasek 58 px); gdyby końcówki sztachet były za miękkie z 3–5 m,
  potrzebny drugi atlas albo 2048 × 4096 (zmiana importera — lider).
- Regiony niezbudowane ponownie: siatka `chainlink` wygląda jak ocynkowana (zielone słupki zostają) do czasu przebudowy.
- Krawędzie połaci (wiatrownica, okap) bez zmian geometrii; dachówki skrajne / rynny pod falą dachówki — osobne zadanie.
