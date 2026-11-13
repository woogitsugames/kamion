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
| Otoczenie | wiaty stacji Circle K na SW (OSM [way/236606116](https://www.openstreetmap.org/way/236606116)) zasłaniają parter szczytu z drogi; giełda Podlaskie Centrum Rolno-Towarowe ([way/219260052](https://www.openstreetmap.org/way/219260052), Andersa 40) leży **NW** od wieży, 282 m | OSM |

## Tabela ścian

| Ściana | Układ okien | Kolor (opis słowny) | Źródło | Status |
|---|---|---|---|---|
| **SW** (szczyt, ~16 m) | gładka, **jedna pionowa kolumna dwudzielnych okien** w osi; bez pasm | tynk **bladożółty/piaskowy**; ramy okien: ADR 0180 → „białe”, obserwacja kadru 073045 → „ciemne (contre-jour)” — **rozbieżność, nie ujednolicona** | Commons [20200711 073045](https://commons.wikimedia.org/wiki/File:20200711_073045_Genera%C5%82a_W%C5%82adys%C5%82awa_Andersa_38,_Bia%C5%82ystok.jpg) (P14-001, kadr obejrzany) + ADR 0180 (krzyżowo) | **SOURCED** (układ, kolor tynku); kolor ram: rozbieżność |
| **SE** (~37 m) | **poziome pasma okien na bieli** (krótki odcinek 0,03–0,20 + długi od 0,30 dł. 37 m — wg ADR 0180) | tynk bladożółty; pasma na bieli | ADR 0180 (krzyżowo — kadry ADR nie są tu dublowane); fragment w kadrze 073045 (P14-007: klimatyzatory, pionowe rury — obserwowany) | **SOURCED** (układ z ADR 0180) |
| **NW** (~37 m) | **regularna siatka okien punktowych**, ~11 rzędów (ortofoto ADR 0180) / „kolumny–siatka” (obserwacja 105711) | tynk bladożółty | Commons [20210328 105711](https://commons.wikimedia.org/wiki/File:20210328_105711_March_2021_in_Bia%C5%82ystok_Podlaskie_Centrum_Rolno%E2%80%93Toworowe_(ul._Andersa).jpg) (P14-008), [20210328 115626](https://commons.wikimedia.org/wiki/File:20210328_115626_March_2021_in_Bia%C5%82ystok_Podlaskie_Centrum_Rolno%E2%80%93Toworowe_(Andersa_Street).jpg) (P14-009) + ADR 0180 | **SOURCED** |
| **NE** (szczyt, ~16 m) | **brak danych** | brak danych | brak legalnego kadru (KartaView/Panoramax nie nagrywają od NE — teren giełdy/parkingu; Panoramax: 0 klatek w 800 m) | **UNVERIFIED** |
| **parter** | portal wejściowy od strony drogi (szczyt SW, P14-011); witryny na parterze NW (P14-012) | tynk bladożółty | 073045, 105711 (kadry obejrzane) | **SOURCED** (fragmenty); cokół i detale portalu: UNVERIFIED |

Elementy na ścianach (obserwacja 073045, P14-001): klimatyzatory na różnych wysokościach i pionowe
rury przy narożniku SW–SE, drabina ewakuacyjna; napis firmowy pod szczyciem (napis firmowy — nie odtwarzamy).

## Tabela dachu

| Element | Liczba | Wysokość nad dachem | Położenie | Źródło | Status |
|---|---|---|---|---|---|
| maszt/antena wysoki | 1 | **ESTIMATED 7–11 m** (2–3 kondygnacje × 3,7 m) | przy prawej krawędzi budynku (strona narożnika SW–SE) | kadr 073045 (P14-013, obejrzany) | SOURCED (istnienie) / ESTIMATED (wysokość) |
| maszty mniejsze | 2 | ESTIMATED 3,7–5,5 m (1–1,5 kondygnacji) | obok masztu wysokiego | kadr 073045 (P14-013) | j.w. |
| maszt mały | 1 | ESTIMATED ≤ 1 kondygnacja (≤3,7 m) | przy lewej krawędzi | kadr 073045 (P14-013) | j.w. |
| nadbudówka (maszynownia) | 1 | ESTIMATED ~3,7–4 m (~1 kondygnacja) | ~1/3 szerokości budynku | kadry 073045 + 105711 (P14-013, P14-008) | SOURCED (istnienie) / ESTIMATED (wymiary) |
| attyka/balustrada | ciągła | ESTIMATED 0,5–1 m | obwodowo | kadry 073045 + 105711 | SOURCED (istnienie) / ESTIMATED (wysokość) |
| instalacje radiowe (stacje bazowe) | **2**: P4/Play (MNET/4/2043/13/25, IdStacji BIA1035, ważne 2033-12-31) i T-Mobile (MNET/11/96018/15/26, IdStacji 24026, ważne 2032-03-31) | rejestr **nie podaje** wysokości | dach, lokalizacja rejestru 53°09′12″N 23°10′05″E | [UKE BIP — wykaz pozwoleń radiowych](https://bip.uke.gov.pl/pozwolenia-radiowe/wykaz-pozwolen-radiowych-tresci/stacje-gsm-umts-lte-5gnr-oraz-cdma,12,90.html), stan 2026-02-25 (P14-016) | **SOURCED** (urzędowe potwierdzenie istnienia instalacji) |

**Metoda wysokości ESTIMATED**: proporcja do kondygnacji 3,7 m (zgodnie z konwencją zadania;
kontrolnie 41,81 m / 11 kondygnacji = 3,80 m — różnica <3%). Wysokości odczytane z kadru 073045
(sylwetki konstrukcji względem rzędów okien), stąd przedziały, nie punkty.

## Samokontrola ≥20 % (audyt)

- Manifest: 18 wierszy → próba **4 wiersze** (22,2 %); seed **14**: `random.Random(14).sample(range(1,19), 4)` → **P14-004, P14-005, P14-008, P14-017**.
- Status wykonania: **BLOCKED** — narzędzie analizy obrazów ma limit 20 wywołań na odpowiedź; limit wyczerpany
  po obejrzeniu kadrów kluczowych (073045, 105711, 115626 + kadry rozstrzygnięć adresowych/kontekstowe).
  Ponowna obserwacja wylosowanych kadrów niemożliwa w tej sesji — szczegóły w `audit_20_percent.json`.
- Kadry do audytu są w ZIP-ie (przekazywanym liderowi poza gitem); audyt do dokończenia przy pierwszym
  dostępie do analizy obrazów.

## Luki (UNVERIFIED — celowo nie dopisywano domysłów)

1. **Ściana NE** — brak jakiegokolwiek legalnego kadru; nie zakładano „jak SW”.
2. **Parter NE/NW** — detale portalu, cokół, stolarka witryn.
3. **Wysokości masztów** — tylko ESTIMATED (metoda proporcji); rejestr UKE nie podaje wysokości.
4. **Rzut dachu z ortofoto** (P14-015) — kafel pobrany do ZIP-a, w sesji nie obejrzany (limit analizy obrazów).
5. **Pozycje kamer Commons** — brak GPS w EXIF; w manifeście szacunki oznaczone UNVERIFIED.
6. **7 klatek KartaView** (2016/2019/2021) — pobrane do ZIP-a, w sesji nie obejrzane (limit); geometria
   (pozycja/kierunek/odległość/azymut wieży) podana z API — do obejrzenia przez lidera.

## Ograniczenia sesji (analiza obrazów)

Analiza kadrów wykonywana narzędziem wizyjnym z twardym limitem **20 wywołań na odpowiedź**. W sesji
obejrzano: 073045 (szczyt SW + fragment SE + dach + parter), 105711 (ściana NW + parter + dach),
115626 (ściana NW z dala + maszty), kadry rozstrzygnięcia adresowego 38A (20201102 152417/152422 —
38A to NISKI budynek, nie wieża), kadry kontekstowe (20200711 065632/072453/073116, 20191211 Wojewoda 001/003,
20210328 105802/105959/110412/110541/110808/131224 — wieży brak lub marginalnie). Po wyczerpaniu limitu
pobrane klatki KartaView i ortofoto oznaczono UNVERIFIED zamiast opisywać nieobejrzane — zgodnie z zasadą
„nie zmyślaj”.

## Deduplikacja względem docs/REFERENCES.md i artifacts/refs/kwadrat-park/INDEX.md

`artifacts/refs/kwadrat-park/INDEX.md` jest gitignored (niedostępny w repo); zreplikowano jego zapytania
narzędziem `tools/refs/open_sources.py` (commons_search: 6 plików = „znane” z INDEX: 20200711 065340,
20210425 100840, 20210425 101130, 20220725 124240, 20240219 084626, 7199 May 2021). Te pliki oraz
wszystkie z docs/REFERENCES.md (7197, 7204, 20240626 103137, EC Białystok, Andersa/Maczka 1/2/3,
Krzysztof Putra Roundabout, 20201102 152339, 20210904 101250, 20241222 122132) **nie są dublowane** w P14.
Nowe dla P14: 20200711 073045, 20210328 105711, 20210328 115626 (+ kontekstowe/deduplikacyjne wymienione
w sources.md). Para Mapillary richlv (2020-08-15) — już udokumentowana w ADR 0180, nie dublowana.

## Pliki

- `manifest.csv` — 18 wpisów P14-001…P14-018 (kolumny wg specyfikacji zadania).
- `sources.md` — pełne źródła z URL-ami, licencjami, wynikami negative (Panoramax 0 klatek w 800 m,
  Openverse 0, NMPT/NMPP GUGiK HTTP 401, BIP miasta 404).
- `audit_20_percent.json` — próba audytu (seed 14) i status.
- `files/` — **poza gitem** (.gitignore), przekazywane w **mistral-p14-office-tower-files.zip**
  (26 plików: 16 Commons 1280 px ≤1600, 7 KartaView lth 1280×960, 3 ortofoto GUGiK PNG 800×800):
  rozmiar **8 341 903 B**, sha256 **111c6c33233880d25890fe981a0a368fae2a88e1bc1c8a570e2b5dc1256aa12c**.
  ZIP właściciel przekazuje liderowi poza gitem (nie wchodzi do PR).

## Licencje / użycie komercyjne

- Wikimedia Commons: CC0 / CC BY 3.0 (PL) — komercyjne OK, z atrybucją autora (Rakoon / PUW Białystok).
- KartaView: CC BY-SA 4.0 — **referencja, nie tekstura** (share-alike); z atrybucją „nieznany użytkownik
  KartaView (sekwencja …)”. Kadry KV służą tu tylko jako opis/referencja.
- GUGiK: dane otwarte (art. 40a PGiK) — komercyjne OK; atrybucja: „Źródło danych: Główny Urząd Geodezji
  i Kartografii (www.geoportal.gov.pl)”.
- OSM: ODbL. UKE BIP: źródło urzędowe (przedruk informacji rejestrowej).
- ZAKAZ Google Maps/Street View/Earth/3D Tiles — **naruszony gdziekolwiek: nie**; nie użyto.
