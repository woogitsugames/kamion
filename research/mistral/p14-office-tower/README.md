# P14 — biurowiec „Biazet”, ul. gen. Władysława Andersa 38 (Kwadrat Park), Białystok

Zadanie badawcze: referencje dla 11-kondygnacyjnego biurowca przy wjeździe do kompleksu Kwadrat Park,
obok stacji paliw (Białystok, rejon ~53,154 N 23,169 E). Gałąź: `research/mistral-p14-office-tower`.

## Obiekt

| Cecha | Wartość | Źródło |
|---|---|---|
| OSM | **way/219260018** „Biazet / Biazet S.A.”, building=office, building:levels=11, height=41 | [OSM](https://www.openstreetmap.org/way/219260018) (ODbL) |
| Środek (WGS84) | **53.153231, 23.168022** | z geometrii way/219260018 (konwersja EPSG:2180 zweryfikowana na kaflach P12: x=778573,54, y=595663,57) |
| BDOT10k | 2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140, „siedziba firmy lub firm”, dach płaski (1130), 610,5 m² | kafel bialystok-industrial-c (GUGiK, dane otwarte) |
| Wysokość | LoD1 2024 = **41,81 m**; LoD2 2017 = 41,52 m; teren 140,56 m EVRF2007; 11 kondygnacji | GUGiK |
| Obrys | szczyty SW/NE ~16 m (normalne 208°/28°); ściany SE/NW ~37 m (normalne 118°/298°) | geometria OSM, spójna z ADR 0180 |
| Otoczenie | wiaty stacji Circle K na SW ([way/236606116](https://www.openstreetmap.org/way/236606116)) zasłaniają parter szczytu z drogi; giełda Podlaskie Centrum Rolno-Toworowe ([way/219260052](https://www.openstreetmap.org/way/219260052), Andersa 40) leży **NW** od wieży, 282 m | OSM |


> **Poprawka s21 (2026-11-15, gałąź `research/mistral-p14-office-tower-fix-s21`)** wg `docs/owner/MISTRAL-FIXES-12.md` § M57-FIX
> i przeglądu `docs/reports/REVIEW-2026-11-14-s20-mistral-m57.md`. Wszystkie kadry pobrano ponownie (Commons 3840 px, KartaView, WMS),
> każdy OBEJRZANO osobno, opisy przepisano z obrazu. Pliki są w `files/` w gałęzi (≤ 1600 px). Tabela „Obiekt” powyżej (OSM/BDOT/LoD) bez zmian.

## Reguła strony ściany

Normalne ścian z OSM: SW 212°, SE 122°, NW 301°, NE 31°. Kamera na azymucie φ od wieży widzi ścianę, gdy cos(φ − n) > 0.
Szczyt SW (napis, kolumna okien) PO PRAWEJ i długa ściana PO LEWEJ → φ ∈ (212°, 301°) → długa ściana to **NW**.
Szczyt SW PO LEWEJ i długa ściana PO PRAWEJ → φ ∈ (122°, 212°) → **SE**.

| Kadr | Szczyt SW | Długa ściana | φ kamery od wieży | Odległość | Skąd |
|---|---|---|---|---|---|
| 073045 (Commons) | po prawej | po lewej → **NW** | ≈224° (ESTIMATED) | ≈120–130 m (ESTIMATED) | φ ze stosunku rzutów NW:SW ≈ 0,47 → 37·cos(φ−301)/(16·cos(φ−212)); odległość z kąta pionowego wieży przy ekwiwalencie 27 mm (EXIF), hFoV ≈ 64° |
| 105711 (Commons) | wąski pasek po prawej | frontalnie → **NW** | ≈290–300° (ESTIMATED) | ≈440 m (ESTIMATED) | szerokość kątowa ściany 37 m |
| 115626 (Commons) | wąski pasek po prawej | frontalnie → **NW** | ≈290–300° (ESTIMATED) | ≈300 m (290–360, ESTIMATED) | j.w. |
| KV 993062122 (2019) | po lewej | po prawej → **SE** | ≈163° (pozycja z API) | 212 m | API KartaView; heading 301,7° spójny z obrazem |
| KV 1326673613 (2021) | po lewej | po prawej → **SE** | ≈159° (pozycja z API) | 233 m | j.w., heading 302,4° |

EXIF GPS kadrów Commons jest **sprzeczny z obrazem** (073045: punkt ≈ 40 m od wieży — wtedy dach byłby ok. 46° nad horyzontem;
105711/115626: punkt ≈ 1,2 km na NW, ten sam `{{Location}}` dla obu zdjęć). Nie użyto go; pozycje kamer są ESTIMATED z geometrii kadru.

## Tabela ścian

| Ściana | Układ okien | Kolor (opis słowny) | Kadry | Status |
|---|---|---|---|---|
| **SW** (szczyt ~16 m) | **jedna pionowa kolumna okien w osi szczytu: 10 okien nad parterem** + przy podstawie poziomy pas ciemnego szklenia parteru (widoczny w lewej i prawej części, środek za drzewem). Napis firmowy na prawo od kolumny (nie odtwarzamy). Okładzina z wyraźnym pionowym żebrowaniem | okładzina ochrowo-musztardowa; **białe skrzydła okien w ciemnoszarym obramieniu** (to godzi „ciemne” i „białe” ramy z poprzedniej wersji i ADR 0180) | 073045 (P14-001, P14-011); KV 2019/2021 (P14-017/018) z drugiej strony | **SOURCED** |
| **NW** (~37 m) | **6 GRUP pasmowych na kondygnację**, rozdzielonych wąskimi filarami; w grupie **5–6 świateł** (liczone na powiększeniu 115626, ±1). Ułamki długości od końca NE (ESTIMATED ±0,02, pomiar własny na 115626): [0,01–0,15] [0,18–0,31] [0,33–0,47] [0,49–0,64] [0,66–0,80] [0,83–0,98]. Przy dole końca SW 2 kondygnacje z szarobrązową nieotynkowaną okładziną (UNVERIFIED: przybudówka czy okładzina). Klimatyzatory liczne. Rur spustowych nie widać | tynk ochrowy/piaskowy, ramy białe | 073045 (P14-007), 105711 (P14-008), 115626 (P14-009) | **SOURCED** (układ, 3 kadry) / **ESTIMATED** (ułamki, liczba świateł) |
| **SE** (~37 m) | przy narożniku S **krótka grupa ok. 4 świateł, przerwa pełnej ściany, dalej dłuższe pasmo** (KV 2021; KV 2019 zgodny, mniej wyraźny). Czy dłuższe pasmo jest dzielone filarami jak NW — w 1280 px nierozstrzygalne | w KV 2019 i 2021 **ten sam jasnożółty/kremowy odcień co szczyt**; Mapillary 2020 (ADR 0180) i ortofoto WMS pokazują SE prawie białą → **konflikt źródeł, nierozstrzygnięty** | KV 993062122 (P14-017), KV 1326673613 (P14-018), ortofoto (P14-015) | **SOURCED** (układ; referencja BY-SA) / kolor: **konflikt** |
| **NE** (szczyt ~16 m) | brak danych | brak danych | brak kadru. Ortofoto pokazuje tylko wąski szary pas szczytu NE w cieniu — za mało na układ | **UNVERIFIED** (bez zmian) |
| **parter** | SW: pas szklenia przy podstawie (P14-011), wejścia nie widać. NW: **zasłonięty** w 105711 i 115626 (P14-012; poprzednie „witryny + wejście” to parter hali giełdy). SE: przy środku niska bryła ok. 1 kondygnacji (P14-019, ortofoto) | — | 073045, 105711, ortofoto | SW pas: SOURCED; NW: UNVERIFIED; SE bryła: ESTIMATED |

Elementy na ścianach: klimatyzatory szczytu SW wiszą **pod oknami kolumny** (2 pod 4. oknem od góry, 1 pod 5., 2 przy najniższym).
Drabiny ewakuacyjnej **nie ma** (usunięto). Rur spustowych na SW i NW nie widać (na SW tylko krótki przewód przy najniższym oknie).

## Tabela dachu

| Element | Ortofoto 80 m (P14-015) | 105711 / 115626, z NW (P14-008/009/014) | 073045, z SW (P14-013) | KV 2021, z SSE (P14-018) | Wysokość nad dachem | Status |
|---|---|---|---|---|---|---|
| Wysoki maszt kratowy przy narożniku W / końcu SW, z odciągami | podstawa X przy narożniku W (największa, długie odciągi) | maszt z odciągami w ≈0,88–0,9 długości od NE | wysoki maszt z odciągami i ok. 6 talerzami nad lewą częścią szczytu (który to maszt — patrz uwaga) | lewy wysoki maszt | **≈11 m** (115626: 2,9 podziałki = 11,0 m + ≈0,4 m zasłonięcia) | SOURCED (istnienie) / ESTIMATED (wysokość) |
| Wysoki maszt kratowy w środku długości, przy krawędzi SE | podstawa X przy środku krawędzi SE | maszt w ≈0,49–0,54 długości, ciemny pionowy pas pod nim na ścianie NW | z osi ≈224° prawdopodobnie w jednej linii z pierwszym — nierozstrzygnięte | prawy wysoki maszt | **≈11–12 m** (115626: 2,6 podziałki = 9,9 m + zasłonięcie 14 m × 40,4 / 300 ≈ 1,9 m) | SOURCED / ESTIMATED |
| Koniec NE (narożniki N i E) | podstawy X przy N i przy E | 3–4 krótsze maszty z antenami panelowymi | panele i krótki maszt na dalekim (N) końcu | — | **≈4–6 m** (≈1 podziałka + poprawka) | SOURCED / ESTIMATED |
| Narożnik S | kraty i platformy z antenami, bez X | — | stelaż z antenami panelowymi ok. 1 m ponad attyką, panele zwisają po szczycie | białe anteny panelowe wzdłuż krawędzi SE | ≈1 m ponad attykę (073045) | SOURCED (073045) |
| Nadbudówka maszynowni | **brak** (długi prostokąt korytek wzdłuż osi, nie bryła) | brak | brak | brak | — | **brak** (teza poprzedniej wersji usunięta) |
| Wentylatory / drobne | ok. 10–14 drobnych niebieskich elementów (funkcja UNVERIFIED) | drobne pręty i skrzynki | pręty, skrzynki wzdłuż krawędzi | maszt z małym talerzem + maszt z panelami | — | SOURCED (istnienie) |
| Attyka | w rzucie niewidoczna | cienka krawędź | cienka ciemna krawędź, bez balustrady | — | — | UNVERIFIED (wysokość) |
| Instalacje radiowe | — | — | — | — | rejestr nie podaje | **SOURCED** (UKE, P14-016, sprawdzone ponownie 2026-11-15) |

**Metoda wysokości (ESTIMATED).** Podziałka kondygnacji 3,8 m (41,81 m / 11). Wysokość widoczna = (piksele masztu ponad krawędzią dachu) /
(piksele podziałki na ścianie) × 3,8 m. Zasłonięcie podstawy przez krawędź dachu ≈ d × (42 − 1,6) / D, gdzie d = odległość masztu od
bliższej krawędzi (z ortofoto), D = odległość kamery (ESTIMATED, wyżej), 1,6 m = wysokość aparatu. Liczby:
- 115626 (wycinek 1:1 z 3840 px): podziałka 36,5 px; maszt środkowy 95 px → 2,6 × 3,8 = 9,9 m + 14 × 40,4 / 300 = 1,9 m → **≈11,8 m**;
  maszt przy SW 105 px → 2,9 × 3,8 = 11,0 m + 3 × 40,4 / 300 = 0,4 m → **≈11,4 m**; krótkie przy NE ≈35 px → ≈3,6 m + poprawka → **≈4–6 m**. Zmiana D w zakresie 290–360 m zmienia wynik o < 0,4 m.
- 073045 (wycinek 1:1 z 3840 px): podziałka 107 px (10 okien kolumny); wysoki maszt 237 px → 2,2 × 3,8 = 8,4 m + 3 × 40 / 125 ≈ 1 m → **≈9–10 m**.
  Rozbieżność z 115626 (≈11,4 m) wynika najpewniej z innej odległości d albo z tego, że to inny maszt — zakres do gry: **9–12 m**.
- Cienie na ortofoto padają na **NW** (słońce z SE, przedpołudnie), nie na NE.

## Samokontrola s21 (≥ 20 %)

- Manifest: 19 wierszy. Seed **20261115**: `r = random.Random(20261115); r.sample(WIEZA, 5)`, potem `r.sample(RESZTA, 1)` →
  **P14-001, P14-008, P14-011, P14-015, P14-017** (kadry z wieżą) + **P14-004** = 6 wierszy = **31,6 %**, w tym 5 kadrów z wieżą.
- Każdy kadr OBEJRZANY ponownie osobnym wywołaniem na pliku z `files/`. Wynik: **4 PASS, 2 FIX**.
  FIX P14-001: kolumna okien „nieco na lewo od środka” → „w osi” (pomiar ≈0,49). FIX P14-008: widoczne kondygnacje 6 → 5–6, maszty 0,55/0,95 → 0,54/0,9.
  Przy okazji: P14-013 (panele na końcu N), P14-002 (liczba pasów zbiornika).
- Poprzedni audyt M57 (seed 14) **unieważniony**: jego opisy „zaobserwowano” dla P14-004/005/017 nie odpowiadały obrazom. Szczegóły w `audit_20_percent.json`.

## Kadry negatywne (wieży brak)

- **KartaView 14055 (2016-08-24), 5 klatek P14-002…006**: jazda estakadą Andersa **na SE** — tor pozycji 7119872 → 7119876 daje
  azymut **123°**; heading API 357–359° jest sprzeczny z obrazem i torem (odrzucony). Wieża jest **za kamerą**. W kadrach 7119872–7119874
  biały zbiornik z niebieskimi pasami = OSM **way/279896715** (`man_made=gasometer`, `building=industrial`, ok. 22 m w rzucie, 125 m od
  kamery 7119873 na az 154°) — na pewno nie zbiornik stacji paliw; funkcja (akumulator ciepła EC?) UNVERIFIED. W 7119872 przy prawej
  krawędzi czerwono-biały komin (jeden z dwóch kominów OSM way/628899553 lub 628899554, `man_made=chimney`, height=120 — który, nierozstrzygnięte). Każda klatka opisana osobno w manifeście.
- **Commons 20210328 110808** (wnętrze hali giełdy) i **20210328 131224** (targowisko na parkingu, w tle dwa czerwono-białe kominy) —
  obejrzane 2026-11-15, wieży brak; dopisane do `sources.md` jako kontekst (plików nie commitowano).
- Pozostałe kadry kontekstowe Commons z `sources.md` (065632, 072453, 073116, 152417, 152422, 105802, 105959, 110412, 110541, 20191211 ×2):
  **w s21 nie oglądane ponownie**; przegląd s20 potwierdził „wieży brak”. Plików nie commitowano.
- Kadry KV 2769366 i 3686129 **nie są negatywami** (poprzednio błędnie „wieży brak”) — patrz P14-017/018.

## Luki

1. **Ściana NE** — UNVERIFIED (bez zmian). Ortofoto pokazuje wąski szary pas szczytu NE w cieniu; ciemniejsza plamka w osi to tylko
   poszlaka kolumny okien, **nie dane**. Nie zakładać „jak SW”.
2. **Kolor SE** — konflikt źródeł: KV 2019 i 2021 (ten sam odcień co szczyt) vs Mapillary 2020 (ADR 0180) i ortofoto WMS (prawie biała).
   Kompresja KV i balans bieli vs przepalenie jasnych ścian. Decyzja po sesji zdjęciowej właściciela. Układ okien SE przestał być luką.
3. **Parter NW i wejścia** — zasłonięte we wszystkich kadrach.
4. **Przybudówka SE** (P14-019) — wymiary z ortofoto (ok. 5 × 8 m) i BDOT (6,3 × 1,8 m) się różnią; funkcja UNVERIFIED.
5. **Dolne 2 kondygnacje przy końcu SW ściany NW** — szarobrązowa okładzina; przybudówka czy inna okładzina — UNVERIFIED.
6. **Wysokości masztów** — tylko ESTIMATED (9–12 m); UKE nie podaje wysokości. Który maszt widać w 073045 — UNVERIFIED.
7. **Pozycje kamer Commons** — ESTIMATED z geometrii kadru; EXIF GPS sprzeczny z obrazem.
8. **Data nalotu mozaiki WMS** — UNVERIFIED.

## Deduplikacja względem docs/REFERENCES.md i artifacts/refs/kwadrat-park/INDEX.md

`artifacts/refs/kwadrat-park/INDEX.md` jest gitignored (niedostępny w repo); zreplikowano jego
zapytania narzędziem `tools/refs/open_sources.py` (commons_search: 6 plików = „znane” z INDEX:
20200711 065340, 20210425 100840, 20210425 101130, 20220725 124240, 20240219 084626, 7199 May 2021).
Te pliki oraz wszystkie z docs/REFERENCES.md (7197, 7204, 20240626 103137, EC Białystok,
Andersa/Maczka 1/2/3, Krzysztof Putra Roundabout, 20201102 152339, 20210904 101250, 20241222 122132)
**nie są dublowane** w P14. Nowe dla P14: 20200711 073045, 20210328 105711, 20210328 115626
(+ kontekstowe/deduplikacyjne wymienione w sources.md). Para Mapillary richlv (2020-08-15) — już
udokumentowana w ADR 0180, nie dublowana.


## Pliki (w gałęzi, `files/`, 16 JPG, razem ok. 2,9 MB)

Polecenie właściciela s21: zdjęcia commitowane pomniejszone (≤ 1600 px). ZIP z poprzedniej wersji nie jest już potrzebny.

| Plik | Źródło | Licencja | sha256 | Wymiar |
|---|---|---|---|---|
| files/commons/20200711_073045.jpg | Commons, miniatura 3840 px → 1600 px | CC BY 3.0, Rakoon | 6db45930c49ffadf96bc02e0a7890c1362786220e80bb43ec3ee8c4e8df3f81c | 1600×900 |
| files/commons/20200711_073045_crop_tower.jpg | wycinek wieży z 3840 px | CC BY 3.0, Rakoon | a915299ec2195f9952b1721ee12ef6288d0875ab0c555a3127dfd7b4ac966c13 | 922×1598 |
| files/commons/20210328_105711.jpg | Commons → 1600 px | CC0, Rakoon | f06bbb9c1d1e30e17e49d6766302d0bc6f912f59cb1d7b4d8f99cd3d35060ee5 | 1600×900 |
| files/commons/20210328_105711_crop_tower.jpg | wycinek 1:1 z 3840 px | CC0, Rakoon | 2cc7d890e9c98eabb24f9b8f6936e1a5f9a9bce03faec9511f6f59cf2a956466 | 365×324 |
| files/commons/20210328_115626.jpg | Commons → 1600 px | CC0, Rakoon | 0fc5d42ac2742cb677b4c599c56bcab1d151d9d751c8084569d1fbd81b7339da | 1600×900 |
| files/commons/20210328_115626_crop_tower.jpg | wycinek 1:1 z 3840 px | CC0, Rakoon | e8e0dbca0eda8ccf23694675aab61bc57456cddb8af577ece7ba54afcc0b703e | 500×626 |
| files/kartaview/kv_7119872.jpg … kv_7119876.jpg | KartaView lth (oryginalne bajty) | CC BY-SA 4.0, referencja | w sources.md §4 | 1280×960 |
| files/kartaview/kv_993062122.jpg, kv_1326673613.jpg | KartaView lth (oryginalne bajty) | CC BY-SA 4.0, referencja | w sources.md §4 | **1280×720** |
| files/kartaview/kv_993062122_crop_tower_x3.5.jpg | wycinek wieży, powiększenie 3,5× | CC BY-SA 4.0 | 8d1c0c75d3d70f460a9341ec9a244965c596e088b51b04a07be9e24bb30b8982 | 630×504 |
| files/kartaview/kv_1326673613_crop_tower_x3.5.jpg | j.w. | CC BY-SA 4.0 | a5cd037a6a18cc78e8bbc523a70e08bf4b137dcb3f52b167da42aa85385508e8 | 626×654 |
| files/orto/orto_tower_80m.jpg | GUGiK WMS HighResolution GetMap, PNG → JPG q92 (PNG trafiałby do LFS); sha256 PNG z WMS: bed34e22…dce63 | dane otwarte GUGiK | a2ab53c9cdd24b0a62ada40602962e7d33900c46ffa1c106a6ac35c018f182a5 | 800×800 |

Plik 20210328_110412 (poprzednio 1280×2276 w ZIP-ie) nie jest już w pakiecie — był tylko kontekstem.

## Licencje / użycie komercyjne

- Wikimedia Commons: CC0 / CC BY 3.0 — komercyjne OK, z atrybucją autora (Rakoon).
- KartaView: CC BY-SA 4.0 — **referencja, nie tekstura** (share-alike); atrybucja „użytkownik KartaView, sekwencja …”.
- GUGiK: dane otwarte (art. 40a PGiK); atrybucja: „Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)”.
- OSM: ODbL. UKE BIP: źródło urzędowe.
- Google Maps/Street View/Earth/3D Tiles — **nie użyto**. Mapillary — nie pobierano (brak tokenu).
