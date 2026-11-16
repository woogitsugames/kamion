# Decyzje mapy 2026-11-16: DK19 przez Piastowską/Branickiego i kierunek Podlasia (D29, s23)

Research do dwóch otwartych pytań planu mapy (ADR 0278, PR #150, `docs/reports/MAP-PLAN-2026-11-16.md` §6 „Ryzyka”
i §2.5 „Podlasie”). Wejścia: G10 (`research/g10-truck-restrictions/`), `docs/owner/OPEN-DECISIONS.md`,
`docs/reports/map/map_plan_0278*.json` (gałąź `origin/map-plan-0278`). Data dostępu do wszystkich źródeł: **2026-11-16**,
chyba że podano inaczej. Bez Google Maps/Street View/Earth. HTTP z UA `osm-research-client/1.0`. Nazw firm nie podaję.

Dane źródłowe tego dokumentu (`docs/reports/map-decisions/`):
- `dk19_bialystok_osm_2026-11-16.json`: 311 way DK19 i ulic sąsiednich (wersja, data, tagi ciężarowe) i węzły ze znakami. Pobrane przez API 0.6 `ways.json`/`nodes.json`. ODbL 1.0, © OpenStreetMap contributors.
- `podlasie_corridor_targets_2026-11-16.json`: kategorie celów w 35 komórkach siatki ADR 0203 (API 0.6 `map.json`, 1 zapytanie na komórkę, 1,5 s przerwy). Skrypt: `corridor_targets.py` (kategorie jak w `map_plan_0278.py` plus rolnicze). Odtworzenie: `uv run --project tools/worldgen python -I docs/reports/map-decisions/corridor_targets.py <map_plan_0278.json> <katalog_surowych> <wynik.json>`.
- `plan2018_s23_piastowska_branickiego.png`: wycinek rys. 1–7 z uchwały LI/794/18 (s. 23), materiał urzędowy (art. 4 pkt 2 pr. aut.).

---

## (a) DK19 przez ul. Piastowską i Branickiego: czy zestaw 40 t może tędy jechać?

### Przebieg DK19 w mieście (OSM, relacja 122101, wersja 1724 z 2026-11-10)
Od północy: Al. Tysiąclecia (8;19) → rondo Putry → Andersa (19;65) → Sosabowskiego (19;65;676) → rondo Żołnierzy
Wyklętych → **Piastowska** → **pl. Antonowicza** → **Branickiego** (odcinek pl. Antonowicza–rondo Meyera) → **rondo Meyera** (19;678) →
Nowowarszawska → Dojlidy Fabryczne → rondo Hasbacha → Suchowolca → Zabłudowska (na południe).
Źródło: https://api.openstreetmap.org/api/0.6/relation/122101.json i plik `dk19_bialystok_osm_2026-11-16.json`.

### Ustalenia (każde ze źródłem)
| # | Stwierdzenie | Źródło | Status |
|---|---|---|---|
| A1 | Plan ograniczeń ruchu ciężarowego UM: Piastowska i Branickiego (pl. Antonowicza–rondo Meyera) są czerwone, czyli „40 t dla wszystkich”. Branickiego na NW od pl. Antonowicza jest zielona (12 t). Strefa 3,5 t (żółta) obejmuje tylko ścisłe centrum (Lipowa/Rynek), ok. 1,5 km na W od Piastowskiej | Uchwała LI/794/18 RM Białystok z 2018-06-18, załącznik, rys. 1–7, s. 23: https://www.bip.bialystok.pl/resource/file/download-file/id.45342 (kopia w G10). Wycinek: `docs/reports/map-decisions/plan2018_s23_piastowska_branickiego.png`, obejrzany | SOURCED (stan 2018) |
| A2 | Ten sam dokument (s. 23): budowa ul. Ciołkowskiego „powinna spowodować redukcję natężenia ruchu na ul. Baranowickiej czy ul. Piastowskiej”. Jest to cel programu, a nie zakaz | jw., tekst s. 23 | SOURCED |
| A3 | OSM, stan 2026-11-08 (ostatnia edycja tych way): 40 way Piastowskiej, 4 way pl. Antonowicza i 13 way Branickiego z `ref=19` nie mają `maxweight`, `hgv`, `maxweight:hgv` ani `maxgvweightrating:hgv`. Jedyny tag tonażowy to `maxaxleload=11.5` ze `source:maxaxleload` = ustawa (Dz.U. 2011 nr 222 poz. 1321), czyli limit ogólny dróg krajowych | `dk19_bialystok_osm_2026-11-16.json` | SOURCED (OSM) |
| A4 | Na 32 way Piastowskiej OSM ma `maxspeed:hgv:conditional=40 @ (20:00-06:00)` i `source:maxspeed:hgv=sign`: w nocy ciężarówki jadą do 40 km/h. Brak zdjęcia znaku | jw. | OSM-only, UNVERIFIED |
| A5 | Branickiego na NW od pl. Antonowicza (poza DK19): 12 way `maxweight=8` i znak B-5 z tabliczką 8 t (węzeł 6634908300: `traffic_sign=PL:B-5`, `maxgvweightrating:hgv=8`, wyjątek dostaw). Ciężarówka wjeżdżająca z pl. Antonowicza w lewo/prosto na Branickiego NW trafia na zakaz | jw.; G10-007 (plan 2018: 12 t; rozbieżność 8/12 t UNVERIFIED) | OSM-only |
| A6 | Za rondem Meyera DK19 (Nowowarszawska → Dojlidy Fabryczne → Suchowolca) ma od 12.2025 zakaz > 3,5 t dla tranzytu. Tranzyt idzie przez Kuronia–Dywizjonu 303–Ciołkowskiego. Mickiewicza (Kuronia–Ciołkowskiego): > 8 t | UM Białystok 2025-11-19: https://www.bialystok.pl/pl/wiadomosci/aktualnosci/zmiany-w-ruchu-wokol-ulicy-suchowolca.html („przekierowania ruchu tranzytowego powyżej 3,5 t na ulice Kuronia, Dywizjonu 303 i Ciołkowskiego”); Radio JARD 2025-11-24: https://radio.jard.pl/zmiany-w-organizacji-ruchu-w-bialymstoku-ciezarowki-pojada-nowa-trasa/ | SOURCED |
| A7 | OSM: B-5 z wyjątkiem „Nie dotyczy zaopatrzenia, mieszkańców oraz służb komunalnych” na wlocie z ronda Meyera w Nowowarszawską (węzeł 13429238121, utworzony 2026-01-03). Ten sam węzeł oraz 5 way Nowowarszawskiej, 10 way Dojlidy Fabryczne i 5 way Suchowolca mają `maxweight=3.5` + `hgv=no` | `dk19_bialystok_osm_2026-11-16.json` | OSM, zgodne z A6 |
| A8 | Komunikaty UM i prasy o zmianach z 2025 roku **nie wymieniają** Piastowskiej ani Branickiego: nie ma tam nowego zakazu | jw. A6 (oba teksty przeczytane pod tym kątem) | SOURCED (brak wzmianki) |
| A9 | W 2026 roku społeczność OSM obniżyła klasę starej DK19 do `secondary`, a ciąg tranzytowy (Kuronia) podniosła do `trunk`. Historia way: Piastowska 23800159 v51 2025-09-09 `secondary`; Kuronia 80184955 v30 2026-07-19 `trunk`. Klasa OSM opisuje funkcję drogi, a nie dopuszczalność ruchu | https://community.openstreetmap.org/t/kategorie-drog-dk19-bialystok/144827 (posty 2026-06-23 do 2026-07-19); `…/api/0.6/way/23800159/history.json` | SOURCED |
| A10 | Obwodnica dla tranzytu: S19 Krynice–Dobrzyniewo–Białystok Zachód (połączenie S8 z S19 na północy) miała być oddana „jesienią” 2026, przy ok. 80 % zaawansowania (artykuł bez daty, wiosna 2026). Odcinki południowe (Białystok Zachód–Księżyno–Białystok Południe) są w odwołaniach od decyzji środowiskowej, więc nie zostały zbudowane. Dziś nie ma ekspresowego objazdu miasta dla DK19 północ–południe | Interia: https://motoryzacja.interia.pl/polskie-drogi/news-na-poludniu-zerwana-umowa-na-polnocy-4-nowe-odcinki-s19-w-20,nId,23479159; strona GDDKiA (status „uzyskano nową decyzję środowiskową, ponownie wniesiono odwołania”), znana tylko z wyników wyszukiwarki, bo gov.pl zwracał HTTP 503: https://www.gov.pl/web/gddkia-bialystok/przygotowanie-inwestycji-drogowych-w-wojewodztwie-podlaskim2 | Otwarcie północnego odcinka w XI 2026: UNVERIFIED |
| A11 | Zdjęcia znaków: Panoramax `api/search` dla bbox 23.180–23.202 E / 53.120–53.142 N zwraca 0 zdjęć. Mapillary wymaga tokenu właściciela (jak w G10), a KartaView nie był sprawdzany | https://api.panoramax.xyz/api/search?bbox=23.180,53.120,23.202,53.142 | brak zdjęć |
| A12 | Projektów stałej organizacji ruchu ani zarządzeń dla Piastowskiej/Branickiego nie znaleziono: wyszukiwanie w BIP nic nie zwróciło (tak samo jak w G10) | wyszukiwanie 2026-11-16 | UNVERIFIED |

### Wniosek (a)
**Prawdopodobnie TAK. Zestaw 40 t może jechać DK19 Piastowską, pl. Antonowicza i Branickiego do ronda Meyera, ale w rondzie
Meyera musi skręcić w Ciołkowskiego.** Za tym przemawiają urzędowy plan UM (A1, „40 t dla wszystkich”), brak jakiegokolwiek tagu tonażowego w aktualnym OSM
(A3) i to, że w zmianach z 2025 roku miasto zakazało tylko odcinka za rondem Meyera (A6–A8). Pewności nie ma, bo plan
pochodzi z 2018 roku, nie ma zdjęcia znaku ani projektu organizacji ruchu (A11–A12), a wyrok WSA II SA/Bk 438/13 (G10) pokazuje, że w Białymstoku
znaki tonażowe bywają zmieniane. Strefa 3,5 t centrum (A1) **nie** obejmuje tej trasy.

**Co to znaczy dla gry**
- Trasa kontrolna ADR 0278 (Andersa → Sosabowskiego → Piastowska/Branickiego → rondo Meyera → Ciołkowskiego → Dywizjonu 303,
  8,3 km) jest zgodna ze wszystkimi źródłami. Kafle 5–7 (`bialystok-mickiewicza`, `-bojary`, `-wygoda`) mają uzasadnienie.
- Planer tras musi przy rondzie Meyera zablokować prosto w Nowowarszawską (3,5 t, A7). OSM już to daje, jeśli graf czyta `hgv=no`
  (G10: czyta). Wyjątek „zaopatrzenie” (`none @ delivery`) potok ignoruje, co jest poprawne dla tranzytu, ale blokuje też dostawy do Dojlid.
- Pl. Antonowicza: skręt w Branickiego NW (8 t, A5) zabroniony. Nocne 40 km/h na Piastowskiej (A4) jako `WORKING_VALUE` do HUD/AI.
- Dopóki S19 nie obejdzie miasta (A10), DK19 przez Białystok jest realną trasą tranzytu. Objazd centrum nie jest wymagany,
  a „objazd” w grze oznacza tylko ciąg Kuronia–Dywizjonu 303–Ciołkowskiego wokół Dojlid (A6).

### Pytanie (a) do AskUserQuestion
**Pytanie:** Czy trasa ciężarówki C ↔ Dojlidy ma iść DK19 przez Piastowską i Branickiego (40 t wg planu UM 2018 i OSM, bez zdjęcia znaków)?
- **Piastowska–Branickiego, skręt Ciołkowskiego (Rekomendowane):** budujemy kafle 5–7 wg ADR 0278. Za rondem Meyera zakaz 3,5 t, nocne 40 km/h jako WORKING_VALUE.
- **Objazd Sulika–Ciołkowskiego:** trasa C ↔ Dojlidy przez kafle 8–9 zamiast 5–7. Dłuższa droga i inne gęste kafle, ale nie zależy od Piastowskiej.
- **Najpierw zdjęcia znaków:** właściciel robi zdjęcia (Piastowska, pl. Antonowicza, rondo Meyera) albo daje token Mapillary. Kafle 5–7 czekają.

---

## (b) Kierunek Podlasia: Mońki → Grajewo (DK65) czy pętla S8 ↔ DW671 ↔ Tykocin

### Poprawka do planu: pętla ma 15 kafli, nie 17
`map_plan_0278.json` liczy 12 kafli S8 i 5 kafli DW671 osobno, ale komórki (−13,−2) i (−14,−2) mają **obie** drogi
(węzeł S8/DW671 przy Jeżewie). Unikalnych kafli jest **15**: (−5…−9, 0), (−9…−12, −1), (−12…−14, −2), (−13, −1…1).
Szacunek GLB z planu (4295 + 1790 = 6085 MB) liczy te dwa kafle podwójnie.

### Fakty (OSM API 0.6, 2026-11-16; ODbL; kompletność tagów nieznana)
| | Mońki → Grajewo (DK65) | Pętla S8 ↔ DW671 ↔ Tykocin |
|---|---|---|
| Nowe kafle | 20 (19 pozamiejskich + miasto Grajewo) | **15** (12 pozamiejskich + 3 podmiejskie przy Białymstoku) |
| Długość nowej drogi | 35,9 km DK65 (plan) | 21,2 km S8 (oś) + 8,6 km DW671 = 29,8 km (plan) |
| Czas przejazdu nowej części, ESTIMATED | ok. 31 min przy 70 km/h, ok. 33–38 min z terenem zabudowanym (50 km/h). W jedną stronę, powrót tą samą drogą | ok. 16 min S8 przy 80 km/h + ok. 7 min DW671 przy 70 km/h, razem ok. 23–25 min. Powrót przez istniejące kafle Tykocin–Knyszyn–DK65 |
| Limity prędkości > 3,5 t | 70 km/h poza obszarem zabudowanym, 50 w obszarze zabudowanym: PoRD art. 20 ust. 3 pkt 2 lit. b i ust. 1 (t.j. Dz.U. 2024 poz. 1251, https://api.sejm.gov.pl/eli/acts/DU/2024/1251/text.html) | S8: 80 km/h (art. 20 ust. 3 pkt 2 lit. a). OSM: `toll:hgv=yes` na S8 (G10-021), czyli opłata e-TOLL jako element ekonomii |
| Klasy dróg | primary (DK65) 35,8 km, secondary 5,3 km, tertiary 19,5 km w kaflach | motorway (S8 + łącznice, obie jezdnie) 52,9 km, secondary (DW671) 8,5 km, tertiary 30,2 km, primary (DK64 przy Jeżewie) 2,6 km |
| Miejscowości w kaflach (OSM `place`) | miasto Grajewo i 14 wsi (m.in. Osowiec-Twierdza, przeprawa przez Biebrzę) | 8 wsi (Jeżewo, Żółtki, Pajewo, Rzędziany…). Tykocin jest już w pierścieniu |
| Hale ≥ 1000 m² / magazyny / zakłady (`man_made=works`) | 6 / 13 / 1 (z tego miasto Grajewo 2 / 5 / 1) | **15 / 12 / 5** (9 / 8 / 5 w jednym kaflu (−5,0) obok dk65-01) |
| Teren przemysłowy (`landuse=industrial`) | 39,8 ha (29,4 ha w Grajewie) | **80,0 ha** (47,0 ha w kaflu (−5,0)) |
| Silosy / elewatory (`man_made=silo`) | **7** (wszystkie w Grajewie) | 1 |
| Mleczarnie / parking TIR / paliwo HGV (tagi) | 0 / 0 / 0, luka OSM (UNVERIFIED w terenie) | 0 / 0 / 0, luka OSM |
| Stacje paliw / MOP (`highway=services\|rest_area`) | 8 / 1 | 4 / **2** |
| Sklepy wielkopowierzchniowe (cele dostaw) | **11** | 2 |
| Podwórza gospodarstw (`landuse=farmyard`) / żwirownie | 19,1 ha / 0 | 67,1 ha / 1 (9,4 ha) |
| Ciągłość | 1. kafel (−14,13) styka się z `monki` (pierścień 0231, PR #115). Koniec w Grajewie to ślepy zaułek, bo DK61 jest poza planem | 1. kafel (−5,0) styka się z `dk65-01` (zbudowany), ostatni (−13,1) z `tykocin` (pierścień 0231). **Pętla zamknięta** przez istniejące kafle |
| Koszt danych BDOT/LoD | powiat 2004 do pobrania: 26,2 + 6,3 + 11,0 = 43,5 MB (plan, HEAD 2026-11-16), 2008 na dysku | 0 MB: powiat 2002 na dysku (przypisanie PRG poza AOI UNVERIFIED, ADR 0278 Otwarte 7) |
| NMT / ORTO, ESTIMATED (proporcja planu: 34 arkusze i 1783 MB na 14 kafli) | ok. 49 arkuszy ≈ 1,8 GB / ≈ 2,5 GB | ok. 36 arkuszy ≈ 1,4 GB / ≈ 1,9 GB (część może być na dysku, bo kafle sąsiadują z dk65-01) |
| GLB, ESTIMATED (mediany i regresja z `map_plan_0278.json`) | 18 × 357,9 + 1 × 440,9 + Grajewo 909 = **≈ 7,8 GB** | 12 × 357,9 + 3 × 440,9 = **≈ 5,6 GB** |
| Klatka High max, ESTIMATED | Grajewo (3210 budynków): 1,60 M + 498 × 3210 ≈ **3,19 M** (ekstrapolacja poza zakres 406–1903), **powyżej bezpiecznika 2 M**. Reszta ≤ 1,56 M | ≤ 1,56 M (pozamiejskie), 1,19 M (podmiejskie): w budżecie |
| Zgodność z decyzjami | Zgodny z D64 („zwykłą drogą, nie ekspresówką”) | S8 to ekspresówka: wymaga świadomego rozszerzenia D64 (D64 dotyczył dojazdu do Knyszyna) |

### Tabela kryteriów (wagi jawne, oceny 1–5)
| Kryterium | Waga | Grajewo | Pętla | Uzasadnienie |
|---|---|---|---|---|
| Cele dla ciężarówki (OSM) | 20 | 3 | 4 | pętla: 2× ha przemysłu, 2,5× hal, 5 zakładów. Grajewo: silosy i sklepy, za to mniej przemysłu |
| Nowe miejsce docelowe | 10 | 5 | 2 | Grajewo to nowe miasto i cel kursu „z Białegostoku do…”. W pętli same wsie, Tykocin już jest |
| Różnorodność dróg | 15 | 3 | 5 | pętla: ekspresówka, węzły, łącznice, MOP, wojewódzka. Grajewo: jedna krajówka i miasto |
| Ciągłość i kształt trasy | 15 | 3 | 5 | pętla zamyka obieg bez zawracania. Grajewo kończy się ślepym zaułkiem |
| Długość i czas kursu | 10 | 4 | 4 | oba w przedziale 20–40 min nowej jazdy (ESTIMATED) |
| Koszt danych | 10 | 3 | 5 | 20 vs 15 kafli, nowy powiat 2004 vs 0 MB BDOT |
| Budżet wydajności | 15 | 2 | 5 | Grajewo ≈ 3,19 M High > 2 M. Pętla ≤ 1,56 M |
| Zgodność z decyzjami właściciela | 5 | 5 | 2 | D64: na razie bez ekspresówek |
| **Wynik ważony (max 500)** | 100 | **325 (65 %)** | **425 (85 %)** | Σ waga × ocena |

Wagi są WORKING_VALUE (propozycja D29). Wynik jest wrażliwy na „Nowe miejsce docelowe”: przy wadze 30 zamiast 10
(kosztem budżetu 15 → 5 i danych 10 → 0) wychodzi 375 vs 365 i wygrywa Grajewo. To więc decyzja o kierunku gry, a nie czysto techniczna.

### Wniosek (b)
**Rekomendacja: najpierw pętla S8 ↔ DW671 ↔ Tykocin (15 kafli), Grajewo później.** Pętla jest tańsza (15 kafli, 0 MB BDOT,
≈ 5,6 GB GLB), mieści się w budżecie klatki, zamyka obieg przez zbudowane kafle, dodaje brakującą klasę drogi (ekspresówka,
węzły, MOP, e-TOLL) i największą strefę przemysłową poza miastem (47 ha przy dk65-01). Grajewo daje nowe miasto docelowe
i elewatory, ale kafel miasta (≈ 3,19 M High, ESTIMATED) wymaga najpierw tej samej decyzji budżetowej co gęste kafle
Białegostoku (ADR 0278 Otwarte 1). Warunki: (1) właściciel zgadza się na S8 mimo D64, (2) oba kierunki zależą od scalenia
pierścienia 0231 (#115: `monki`, `tykocin`), (3) kolejność ADR 0278 („Podlasie po Białymstoku”) zostaje.

### Pytanie (b) do AskUserQuestion
**Pytanie:** Który kierunek Podlasia budujemy jako pierwszy po kaflach Białegostoku z planu ADR 0278?
- **Pętla S8–Tykocin (Rekomendowane):** 15 kafli, ekspresówka S8 z węzłami i powrót przez Tykocin–Knyszyn. Wymaga zgody na S8 mimo D64.
- **Mońki → Grajewo (DK65):** 20 kafli zwykłą krajówką do nowego miasta z elewatorami. Kafel Grajewa przekracza budżet 2 M High i wymaga redukcji.
- **Odłożyć Podlasie:** najpierw 14 kafli Białegostoku i gęste kafle (decyzja budżetowa). Kierunek Podlasia wybieramy po ich pomiarze.

---

## Ograniczenia tego researchu
- Kategorie celów pochodzą tylko z OSM. Mleczarnie, parkingi TIR i paliwo HGV mają 0 wpisów, bo OSM ich nie taguje, a nie dlatego, że obiektów nie ma (jak w ADR 0278 §3).
- Budżety i koszty NMT/ORTO są ekstrapolacjami (ESTIMATED). Prawdziwe liczby da dopiero `ingest.py`/`build_world.py` u lidera.
- Brak zdjęć znaków na DK19 w mieście (A11) i brak aktów organizacji ruchu (A12). Status (a) zamknie dopiero zdjęcie albo projekt organizacji ruchu.
- Strony GDDKiA na gov.pl zwracały HTTP 503, więc status S19 w XI 2026 jest UNVERIFIED.
