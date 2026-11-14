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

## Tabela ścian

| Ściana | Układ okien | Kolor (opis słowny) | Źródło | Status |
|---|---|---|---|---|
| **SW** (szczyt, ~16 m) | gładka, **jedna pionowa kolumna dwudzielnych okien** w osi, **11 rzędów** (audyt) | tynk **beżowy/bladożółty/piaskowy**; ramy okien **ciemne** (2× obserwacja; ADR 0180 podaje „białe” — **rozbieżność światła/dystansu, nie ujednolicona**) | Commons [20200711 073045](https://commons.wikimedia.org/wiki/File:20200711_073045_Genera%C5%82a_W%C5%82adys%C5%82awa_Andersa_38,_Bia%C5%82ystok.jpg) (P14-001, obserwowany + audytowany) + ADR 0180 (krzyżowo) | **SOURCED** |
| **SE** (~37 m) | **poziome pasma okien na bieli** (ADR 0180: krótki odcinek 0,03–0,20 + długi od 0,30 dł. 37 m) — **potwierdzone niezależnie przechyłem ortofoto** (P14-015: ciemne poziome pasy na długiej ścianie wschodniej) | tynk bladożółty; pasma na bieli | ADR 0180 (krzyżowo) + ortofoto GUGiK (P14-015, obserwowany) + fragment w kadrze 073045 (P14-007: klimatyzatory) | **SOURCED** |
| **NW** (~37 m) | **regularna siatka osobnych okien, ~11 rzędów, ~6 kolumn** (ortofoto P14-015 + ADR 0180); odczyt z kadru 105711 na granicy rozdzielczości: raz „siatka/kolumny”, raz „pasma + 6 kolumn” — **udokumentowana niejednoznaczność odczytu** | tynk piaskowy/beżowy; ramy ciemne | Commons [20210328 105711](https://commons.wikimedia.org/wiki/File:20210328_105711_March_2021_in_Bia%C5%82ystok_Podlaskie_Centrum_Rolno%E2%80%93Toworowe_(ul._Andersa).jpg) (P14-008, obserwowany + audytowany), [20210328 115626](https://commons.wikimedia.org/wiki/File:20210328_115626_March_2021_in_Bia%C5%82ystok_Podlaskie_Centrum_Rolno%E2%80%93Toworowe_(Andersa_Street).jpg) (P14-009) + ortofoto | **SOURCED** (przypisanie NW z 3 przesłanek: giełda NW, światło na szczytowym narożniku, ortofoto) |
| **NE** (szczyt, ~16 m) | **brak danych** | brak danych | brak legalnego kadru (KartaView/Panoramax nie nagrywają od NE — teren giełdy/parkingu; Panoramax: 0 klatek w 800 m). Próba pośrednia z narożnika w kadrach giełdowych: odczyty sprzeczne, szczyt w nich przypisywany raczej do SW — **nie uznano za dane o NE** | **UNVERIFIED** |
| **parter** | SW: zasłonięty wiatami Circle K z jezdni; portal **nierozstrzygnięty** (odczyty sprzeczne — P14-011). NW: **witryny + wejście** potwierdzone audytem (P14-012) | tynk piaskowy/beżowy | 073045, 105711 (kadry obserwowane) | SW parter: **UNVERIFIED**; NW parter: **SOURCED** |

Elementy na ścianach (073045, audytowany): klimatyzatory przy prawym narożniku (2× potwierdzone);
pionowe rury — odczyt niepewny (obserwacja 1: widoczne; audyt: niewidoczne); drabina ewakuacyjna
(obserwacja 1); napis firmowy pod szczyciem (napis firmowy — nie odtwarzamy).

## Tabela dachu

| Element | Liczba | Wysokość nad dachem | Położenie | Źródło | Status |
|---|---|---|---|---|---|
| maszty/anteny | **4–5** (ortofoto: 4 — 2 bliżej krawędzi zachodniej, 2 bliżej wschodniej; audyt 073045: 5; kadr 115626: 4 po prawej stronie) | najwyższy **ESTIMATED 7–11 m** (2–3 kondygnacje × 3,7 m); pozostałe **ESTIMATED 3,7–7,4 m** (1–2 kondygnacje) | rozłożone w parach przy obu krótkich krańcach dachu; najwyższy środek/prawo (odczyty rozbieżne) | 073045 (P14-013, obserwowany + audytowany), ortofoto (P14-015, obserwowany), 115626 (P14-014) | SOURCED (liczba 4–5, rozmieszczenie) / ESTIMATED (wysokości) |
| nadbudówka (maszynownia) | 1 | ESTIMATED ~3,7–4 m (~1 kondygnacja) | **centralna** część dachu, ok. 1/4 powierzchni (orto) / 1/4–1/3 szerokości (kadry) | ortofoto (P14-015) + kadry 073045, 105711 | SOURCED (istnienie, pozycja) / ESTIMATED (wymiary) |
| attyka/balustrada | ? | jeśli występuje: ESTIMATED 0,5–1 m | obwodowo | odczyty **rozbieżne**: twierdzące (073045 v1, 105711 v1), negatywne (audyt 073045, ortofoto 0,10 m/px) | **UNVERIFIED** |
| instalacje radiowe (stacje bazowe) | **2**: P4/Play (MNET/4/2043/13/25, IdStacji BIA1035, ważne 2033-12-31) i T-Mobile (MNET/11/96018/15/26, IdStacji 24026, ważne 2032-03-31) | rejestr **nie podaje** wysokości | dach, lokalizacja rejestru 53°09′12″N 23°10′05″E | [UKE BIP — wykaz pozwoleń radiowych](https://bip.uke.gov.pl/pozwolenia-radiowe/wykaz-pozwolen-radiowych-tresci/stacje-gsm-umts-lte-5gnr-oraz-cdma,12,90.html), stan 2026-02-25 (P14-016) | **SOURCED** (urzędowe potwierdzenie istnienia instalacji) |

**Metoda wysokości ESTIMATED**: proporcja do kondygnacji 3,7 m (konwencja zadania; kontrolnie
41,81 m / 11 kondygnacji = 3,80 m — różnica <3%). Wysokości odczytane z sylwetek konstrukcji
względem rzędów okien, stąd przedziały, nie punkty. Rzut ortofoto: cienie masztów ku NE → nalot
poranny; przechył ujawnia siatkę okien na NW i pasma na SE.

## Samokontrola ≥20 % (audyt) — WYKONANA

- Manifest: 18 wierszy → próba **4 wiersze** (22,2 %); seed **14**: `random.Random(14).sample(range(1,19), 4)` → **P14-004, P14-005, P14-008, P14-017**.
- Wynik ponownej obserwacji (szczegóły w `audit_20_percent.json`):
  - **P14-004, P14-005, P14-017** (KartaView): wieża **brak w kadrze** — geometryczne przewidywanie
    widoczności szczytu SW z sekwencji 1405 **nie potwierdziło się** (zasłona: drzewa, słupy/linie,
    zbiornik stacji paliw); dla P14-017 (2019) przewidywane „ryzyko wykadrowania” **potwierdzone**.
    Manifest zaktualizowany do obserwowanych negatywów (wcześniej: „nie obejrzany”).
  - **P14-008** (105711): **POTWIERDZONE** — wieża po prawej, długa ściana, 11 kondygnacji, witryny +
    wejście, klimatyzatory, tynk piaskowy, nadbudówka, maszty. **Rozbieżności odczytu** (udokumentowane):
    układ okien „siatka/kolumny” vs „pasma + 6 kolumn” (przypisanie do NW utrzymane na podstawie ortofoto
    i lokalizacji giełdy), dach 2 maszty w tym kadrze vs 4 w ortofoto.
- Dodatkowa ponowna obserwacja **P14-001** (073045, poza próbą): **POTWIERDZONE** — jedna kolumna,
  **11 rzędów** (poprzednio model naliczał ~13 — zawyżenie skorygowane), okna dwudzielne, ramy ciemne,
  klimatyzatory. Skorygowano: pionowe rury (odczyt niepewny), portal wejściowy (nierozstrzygnięty —
  P14-011 downgraded do UNVERIFIED), attyka (rozbieżna — tabela dachu), liczba masztów 3–4 → 4–5.

## Kadry negatywne (szukałem, wieży brak — wartość coverage)

Wszystkie 7 klatek KartaView z pobrania **obserwowane**: sekwencja 14055 (2016-08-24, 5 klatek
164–259 m od wieży) — wieża niewidoczna (zasłona drzew/słupów/stacji paliw); sekwencje 2769366
(2019) i 3686129 (2021) — kamera na NW, wieża poza kadrem, zgodnie z geometrią (41,6°/36,3° od osi
przy hFoV ~70°). Kontekstowe kadry Commons z serii 2021-03-28 (105802, 105959, 110412, 110541) —
zbliżenia straganów/wnętrza hali, wieży brak. Panoramax: 0 klatek w 800 m. Openverse: 0 wyników.

## Luki (UNVERIFIED — celowo nie dopisywano domysłów)

1. **Ściana NE** — brak legalnego kadru; nie zakładano „jak SW”.
2. **Parter od SW** — portal/cokół nierozstrzygnięte (odczyty sprzeczne + zasłona wiat Circle K).
3. **Wysokości masztów** — tylko ESTIMATED (proporcja 3,7 m/kondygnację); UKE nie podaje wysokości.
4. **Attyka/balustrada** — odczyty rozbieżne między obserwacjami i ortofoto.
5. **Pozycje kamer Commons** — brak GPS w EXIF; szacunki oznaczone UNVERIFIED.
6. **Układ okien w kadrach giełdowych** — na granicy rozdzielczości; rozstrzygnięto ortofoto (NW = siatka).

## Deduplikacja względem docs/REFERENCES.md i artifacts/refs/kwadrat-park/INDEX.md

`artifacts/refs/kwadrat-park/INDEX.md` jest gitignored (niedostępny w repo); zreplikowano jego
zapytania narzędziem `tools/refs/open_sources.py` (commons_search: 6 plików = „znane” z INDEX:
20200711 065340, 20210425 100840, 20210425 101130, 20220725 124240, 20240219 084626, 7199 May 2021).
Te pliki oraz wszystkie z docs/REFERENCES.md (7197, 7204, 20240626 103137, EC Białystok,
Andersa/Maczka 1/2/3, Krzysztof Putra Roundabout, 20201102 152339, 20210904 101250, 20241222 122132)
**nie są dublowane** w P14. Nowe dla P14: 20200711 073045, 20210328 105711, 20210328 115626
(+ kontekstowe/deduplikacyjne wymienione w sources.md). Para Mapillary richlv (2020-08-15) — już
udokumentowana w ADR 0180, nie dublowana.

## Pliki

- `manifest.csv` — 18 wpisów P14-001…P14-018 (kolumny wg specyfikacji zadania).
- `sources.md` — pełne źródła z URL-ami, licencjami, wynikami negative (Panoramax 0 klatek w 800 m,
  Openverse 0, NMPT/NMPP GUGiK HTTP 401, BIP miasta 404).
- `audit_20_percent.json` — próba audytu (seed 14) i pełne wyniki ponownej obserwacji.
- `files/` — **poza gitem** (.gitignore), przekazywane w **mistral-p14-office-tower-files.zip**
  (26 plików: 16 Commons 1280 px ≤1600, 7 KartaView lth 1280×960, 3 ortofoto GUGiK PNG 800×800):
  rozmiar **8 341 903 B**, sha256 **a4e05d205d70590566e9562819e1df873125378929b31ea3c31233c26eaddd4e**.
  ZIP właściciel przekazuje liderowi poza gitem (nie wchodzi do PR).

## Licencje / użycie komercyjne

- Wikimedia Commons: CC0 / CC BY 3.0 (PL) — komercyjne OK, z atrybucją autora (Rakoon / PUW Białystok).
- KartaView: CC BY-SA 4.0 — **referencja, nie tekstura** (share-alike); z atrybucją „nieznany użytkownik
  KartaView (sekwencja …)”. Kadry KV służą tu tylko jako opis/referencja (i tu: udokumentowane negatywy).
- GUGiK: dane otwarte (art. 40a PGiK) — komercyjne OK; atrybucja: „Źródło danych: Główny Urząd Geodezji
  i Kartografii (www.geoportal.gov.pl)”.
- OSM: ODbL. UKE BIP: źródło urzędowe (przedruk informacji rejestrowej).
- ZAKAZ Google Maps/Street View/Earth/3D Tiles — **naruszony gdziekolwiek: nie**; nie użyto.
