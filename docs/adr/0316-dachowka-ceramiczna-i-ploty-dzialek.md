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

Wypełniane po rundach — patrz „Wyniki”.

## Wyniki

Wypełniane po rundach.

## Otwarte

Wypełniane po rundach.
