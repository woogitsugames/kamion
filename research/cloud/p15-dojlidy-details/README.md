# M58 — Dojlidy / Krywlany: słupki z łańcuchem, ogrodzenie lotniska, oznakowanie pasa 09R/27L (cloud p15)

Zadanie: `docs/owner/MISTRAL-TASKS-9.md` § M58 (wariant „cloud”: katalog `research/cloud/p15-dojlidy-details/`, id `C58-NNN`, bez ZIP-a — `fetch.py`). Data: 2026-11-14.
Zakres M64 (kadr z oka kierowcy, obiekty lotniska, nawierzchnia) **nie** jest tu wykonywany.

Pliki: `manifest.csv` (80 wierszy), `sources.md`, `audit_20_percent.json`, `fetch.py`, `STATUS.md`. Obrazy i PDF-y nie są w gicie (`files/` w `.gitignore`).

## 0. Najważniejsze wnioski

1. **Słupki z łańcuchem** (Mickiewicza × Kuronia, kadr P11-063): okrągłe, **ok. 1,2 m** wysokości (dwie niezależne metody: 1,17 m i 1,19 m), **rozstaw 2,0 m**, 5 pasów (biały krótki – czerwony – biały – czerwony – biały), **dwa łańcuchy** ogniwowe; w każdym przęśle łańcuch jednobarwny, na przemian czerwony i biały, górny i dolny w przeciwnej fazie. Ten sam typ stoi przy ul. Dywizjonu 303 przed wjazdem na lotnisko (≥ 20 słupków w rzędzie). W OSM nie ma ani jednego `barrier=chain`.
2. **Pas 09R/27L** ma **progi przesunięte**: biały pas poprzeczny + 5 grotów 452 m od końca W i 712 m od końca E; do progów prowadzą w osi białe strzałki (6 od W, 10 od E); między progami tylko linia osiowa (5 kresek); linie krawędziowe na całej długości; oznaczniki „09 R” i „27 L” przy samych końcach nawierzchni. **Nie ma** „zebry” progu, znaków strefy przyziemienia ani punktu celowania. Pomiar zgadza się z AIP (LDA 900 / 640 m).
3. **Werdykt widoczności: NIE.** Oznakowania pasa nie da się odczytać z żadnej z trzech ulic; z ul. Dywizjonu 303 sama nawierzchnia może być co najwyżej cienką szarą kreską w trawie (386–440 m, kąt ≤ 0,45°). Z dróg widać ogrodzenie, trawę, samoloty i hangary przy wjeździe.
4. **Ogrodzenie lotniska**: zielony panel zgrzewany „3D” na zielonych słupkach, 2 rzędy drutu kolczastego na prostych przedłużeniach słupków; panel ok. 1,7 m, wierzch ok. 2,0 m (ESTIMATED przy założonym module 2,5 m).
5. **Luka:** wymiarów U-12b z rozporządzenia nie udało się zacytować — część Dz.U. 2019 poz. 2311 z zał. 4 jest nieosiągalna (szczegóły § 5).

## 1. Słupki biało-czerwone z łańcuchem

### 1.1 Mickiewicza × Kuronia (kadr P11-063 = Commons `20240623_124644_June_2024_in_Białystok.jpg`, CC0)

Kadr obejrzany w 960 px i w dwóch wycinkach z wersji 3840 px. Kamera stoi po zachodniej stronie wschodniej jezdni ul. Mickiewicza (pas dzielący), patrzy na wschód (ok. 100°, ESTIMATED z geometrii). Słupki stoją **po drugiej stronie jezdni**, na chodniku tuż za krawężnikiem, na północ od przejścia dla pieszych; za nimi szafa sterownicza widoczna też na ortofoto — to ona wiąże kadr z miejscem.

| parametr | przepis (Dz.U. 2019 poz. 2311 zał. 4, U-12b) | odczyt | metoda | status |
|---|---|---|---|---|
| wysokość słupka | UNVERIFIED (zał. 4 niedostępny; G5 podaje 1,10 m bez cytatu z aktu) | **1,17 m** | model otworkowy na 3 słupkach + rozstaw z ortofoto | ESTIMATED |
| wysokość słupka (kontrola) | — | **1,19 m** (1,15–1,24) | cień na ortofoto 0,05 m × tan(wys. Słońca 43,7°, 2025-04-18) | ESTIMATED |
| przekrój | UNVERIFIED | okrągły, Ø ok. 0,07 m (0,06–0,075) | szerokość w pikselach przy odległości 19 m | ESTIMATED |
| pasy | UNVERIFIED | 5: biały ~0,12 m (góra), potem czerwony/biały/czerwony/biały po ~0,24–0,29 m | odczyt z wycinka | SOURCED (układ) / ESTIMATED (wymiary) |
| rozstaw | UNVERIFIED (G5: 1,5/1,8 m bez cytatu) | **2,0 m** (2,04; 1,91; 1,96) | ortofoto 0,05 m/px, wierzchy słupków | ESTIMATED |
| łańcuchy | UNVERIFIED | 2: zaczep ok. 1,10 m i ok. 0,56 m | wycinek | ESTIMATED |
| zwis | UNVERIFIED | 0,17–0,25 m (0,21 m w P11-063) | piksele względem wysokości słupka | ESTIMATED |
| kolor łańcucha | UNVERIFIED | przęsła na przemian czerwone i białe; górny i dolny w przeciwnej fazie | wycinki P11-063 i P11-076 | SOURCED |
| przebieg | — | wzdłuż krawężnika, nie wokół trawnika | ortofoto + kadr | SOURCED |
| końce odcinka | — | N: 53.105827, 23.184959; S: 53.105707, 23.185021 (±2 m) | ortofoto | ESTIMATED |
| długość | — | ok. 14 m, ≥ 8 słupków | 7 przęseł × 2,0 m | ESTIMATED |
| OSM | — | brak `barrier=chain` w całym bbox | API 0.6 | SOURCED |

Uwagi do odtworzenia: kilka słupków jest wyraźnie krzywych (do ~5° od pionu); łańcuch wygląda na tworzywo (matowy, bez rdzy) — materiał UNVERIFIED. Kadr P11-077 (2020) pokazuje takie same łańcuchy także po zachodniej stronie jezdni i przed gmachem sądu.

### 1.2 Dywizjonu 303 przy rondzie kpt. K. Wünschego (wjazd na lotnisko)

Kadry P11-076 (2020), P11-079 i P11-078 (2023). Budowa identyczna jak w 1.1 — w P11-076 na pierwszym planie widać pojedyncze ogniwa i zaczepy. Rząd po stronie lotniska: ≥ 20 słupków (≥ 38 m). Na ortofoto 2025 trzy słupki po stronie SW rozpoznane po cieniach, przęsło 2,03 m (53.105683, 23.167169). Końce odcinków i stan strony NE w 2025 r. — UNVERIFIED.

### 1.3 Zjazd do bramy E lotniska (ul. Mickiewicza, kadr P11-022)

Dwa inne warianty: po lewej 4 pojedyncze słupki biało-czerwone z czarnym kapturkiem **bez łańcucha**; po prawej 3 słupki z **jednym ciemnym łańcuchem** od wierzchu.

## 2. Pas startowy 09R/27L

### 2.1 AIP (fakty z karty, bez kopiowania mapy)

eAIP VFR Polska, obowiązujące wydanie **AIRAC AMDT VFR 11/26 (29 OCT 2026)**; karta **VFR AD 4 EPBK 2-1**, data 11 JUN 2026, stopka „AIRAC AMDT VFR 06/26”:
RWY 09R/27L — TRUE 092°/272°, MAG 087°/267°, **1350 × 30 m, CONC/ASPH**, 24/F/A/X/U, **TORA 1350/1350 m, LDA 900 m (09R) i 640 m (27L)**. RWY 09L/27R — 840 × 160 m, GRASS (SUP 02/26: zwężenie do 80 m). Część tekstowa AD 4.1–4.13 nie opisuje oznakowania ani świateł.

### 2.2 Ortofoto GUGiK

WMS `PZGIK/ORTO/WMS/HighResolution`, arkusz **N-34-107-C-b-3-4, aktualność 2025-04-18, piksel 0,05 m** (skorowidz). Metoda px→m: żądanie GetMap w EPSG:2180 z zadanym BBOX i rozmiarem, więc skala wynika z żądania (0,4 / 0,1 / 0,05 m/px). Pomiary w układzie (s wzdłuż osi, c w poprzek) dopasowanym do linii krawędziowych; s = 0 w węźle OSM 8866086772, koniec W nawierzchni s = −11,4 m, koniec E s = 1342,4 m. Zastrzeżenie: WMS nie podaje, który arkusz renderuje (istnieje też 2024-03-30, 0,05 m) — za 2025 przemawia fenologia i długość cienia pieszego.

| element | co widać | wymiar (ESTIMATED z ortofoto) |
|---|---|---|
| nawierzchnia | szara, w trawie; poszerzenie do zawracania na końcu E; droga kołowania od końca W na NW | 1353,6 × 30,0 m |
| linie krawędziowe | białe ciągłe na całej długości | szer. 0,80–0,87 m, rozstaw osi 29,1 m |
| oznaczniki | „09” + „R” przy końcu W, „27” + „L” przy końcu E — przy samych końcach, przed strzałkami | znak 9,1–9,3 × ok. 3,0 m |
| strzałki w osi | 6 od W (s 74,5–402), 10 od E (s 698,5–1257), grotem do środka | dł. 40 m (trzon 30 × ~0,35 + grot 10 × 3,1), co 57,5 m |
| próg przesunięty 09R | pas poprzeczny + 5 grotów po stronie W | pas 1,25 m; 452 m od końca W; 53.100961, 23.169899 |
| próg przesunięty 27L | pas poprzeczny + 5 grotów po stronie E | pas 1,25 m; 712 m od końca E; 53.100907, 23.172716 |
| groty przed progiem | po 5 szt. | 10,0 × 3,1 m, co ~5,5 m w poprzek, 2,1 m od pasa |
| linia osiowa | tylko między progami: 5 kresek | 30–30,5 m / przerwa 27–27,5 m, szer. ~0,35 m |
| brak | „zebra” progu, strefa przyziemienia, punkt celowania | — (ślad usuniętej „zebry” przy końcu E, wytarty „X” przy końcu W) |
| linie żółte | kołowanie: łuk z TWY na oś (W), pętla na płycie (E) | UNVERIFIED szerokość |
| oprawy | 6 jasnych elementów za krawędzią E co ~6 m | typ UNVERIFIED |

Kontrola krzyżowa: 1342,4 − 441,2 = **901 m** (AIP LDA 09R 900) i 630,0 + 11,4 = **641 m** (AIP LDA 27L 640); azymut osi 91,8° (AIP 092°).

### 2.3 Czy oznakowanie widać z drogi — **NIE**

| ulica | odległość do pasa | geometria (oko 2,5 m) | kadr | wynik |
|---|---|---|---|---|
| Dywizjonu 303 | min. 386 m (way 443103344), naprzeciw progu 09R | depresja 0,25–0,45°; cała 30-m nawierzchnia = 0,014–0,035° w pionie; linia 0,85 m ≈ 0,001° | P11-099, P11-076: ogrodzenie, trawa, samoloty, las — pasa nie da się wskazać | znaki NIE; nawierzchnia co najwyżej cienka kreska |
| Mickiewicza | 306 m od końca E (way 206333509) | depresja ~1,0°; wg NMT teren przecina linię widzenia (−1,4 m); las po obu stronach ulicy | P11-022 (przez bramę E): łąka i las; P11-023/024: sam las | NIE |
| Kuronia | 551 m | ogrody działkowe, zabudowa, drzewa | brak kadrów | NIE |

Wzory: depresja = atan(Δz / d); rozpiętość pionowa pasa = atan(Δz/(d−15)) − atan(Δz/(d+15)); Δz = wysokość oka + rzędna jezdni − rzędna pasa (NMT 1 m). Dla oka 1,7 m wartości ok. 30 % mniejsze.
Uwaga o NMT: arkusze z 2018 r. (budowa pasa) zawierają podłużne nasypy 2–3 m po obu stronach pasa; ortofoto 2025 ich nie pokazuje → **nie odtwarzać wałów**.

## 3. Ogrodzenie lotniska i brama E

- Typ (P11-080, P11-079, P11-099, P11-076): zielony panel zgrzewany z poziomymi przetłoczeniami, zielone słupki z profilu prostokątnego, **2 rzędy drutu kolczastego** na pionowych przedłużeniach słupków; czerwone tabliczki „LOTNISKO”; przy wjeździe banery (napisy firmowe, nie odtwarzamy).
- Wysokość: panel ok. **1,7 m**, wierzch słupka ok. **2,0 m** — ESTIMATED przy założeniu modułu słupków 2,5 m (WORKING_VALUE).
- OSM: way 483199984 (N, wzdłuż Dywizjonu 303, 2354 m), 483199985 (W), 542255310 (S/E). Od osi jezdni S ul. Dywizjonu 303 ok. 18 m.
- Brama E (53.100518, 23.188044): stalowa ramowa, ciemnozielona, 4 pola z zastrzałami, bez wypełnienia; długość ok. 9–10 m (ortofoto); wysokość UNVERIFIED.
- Kadry P11-021 i P11-055 pokazują ogrodzenia **ogrodów działkowych**, nie lotniska.

## 4. Inne wygrodzenia przy drogach ciężarówek

| co | gdzie | kadr | uwagi |
|---|---|---|---|
| żółte przęsła siatkowe z czerwonymi słupkami | pas dzielący: Kuronia (53.105600, 23.185605), Mickiewicza, Dywizjonu 303 | P11-005, P11-063, P11-077, P11-076 | proporcje zgodne z G5 (1,10 m / 2,0 m); bez nowego pomiaru bezwzględnego |
| szlaban + brama przesuwna zakładu | Mickiewicza (53.104304, 23.186054) | P11-019 | ramię białe z czerwonymi pasami, podniesione |
| szlaban z pomarańczową szafką | Mickiewicza 49 (53.109722, 23.205833) | P11-143 (2015, CC BY-SA) | ramię z ukośnymi pasami, żółta tabliczka; czarne słupki z łańcuchem |
| szlaban wjazdu szpitala | Żurawia (53.109464, 23.190654) | P11-129 | ramię okrągłe, dłuższe pasy, niebieska tablica na ramieniu |
| tablice prowadzące na wyspie ronda | rondo Wünschego | nowy kadr 2020 | biało-czerwona „jodełka”; kod znaku UNVERIFIED |
| płot z blachy trapezowej | N strona Dywizjonu 303 | nowy kadr 2023 | tymczasowy, w 2025 r. już go nie ma |
| OSM `lift_gate` | 17 węzłów w bbox | — | lista w C58-079 |
| U-5a | — | — | **nie znaleziono** w obejrzanych kadrach (UNVERIFIED) |

## 5. Luki

1. **Dz.U. 2019 poz. 2311 zał. 4 (U-12b, U-12a, U-12c, U-3, U-5a) — brak cytatu.** API Sejmu wymienia `D20192311-c1.pdf` i `-c2.pdf`, ale pod oboma adresami oddaje ten sam plik (525 stron, tylko zał. 1); ISAP zwraca stronę antybotową; dziennikustaw.gov.pl i gov.pl niedostępne przez proxy. Zacytowano tylko odesłanie ze s. 79. Kolumna „przepis” w tabeli 1.1 jest więc UNVERIFIED, a kody U-12c/U-3 w opisach to robocze nazwy.
2. **Oryginały Commons bez sha256.** `upload.wikimedia.org` zwracał HTTP 429 (Retry-After 600) przez całą sesję; kadry obejrzano przez `commons.wikimedia.org/w/thumb.php` (960 i 3840 px). W manifeście jest URL oryginału i `sha1_commons` z API; `fetch.py` sprawdza sha1 tam, gdzie brak sha256. Skutek uboczny: brak EXIF, więc ogniskowa w metodzie A to WORKING_VALUE (wpływ < 0,02 m).
3. **Kierunki kadrów**: Commons nie daje azymutu; 3 kadry mają kierunek ESTIMATED z geometrii, reszta UNVERIFIED.
4. Panoramax i KartaView: 0 zdjęć w bbox regionu; Mapillary nieużywane. Stąd brak kadrów z ul. Kuronia w stronę lotniska i brak przykładów U-5a.
5. Końce odcinków łańcucha przy Dywizjonu 303, wysokość bramy E, typ opraw przy końcu E pasa, materiał łańcucha — UNVERIFIED.
6. NMPT (WCS) niedostępny (404/401) — wysokość zieleni tylko z kadrów.

## 6. Samokontrola

Seed `random.Random(20261114).sample(ids, 16)` → 16 z 80 wierszy (20 %). Ponownie obejrzano 11 obrazów, sprawdzono cytat i stronę Dz.U., tabelę AIP, przeliczono kąty i policzono węzły OSM. **10 PASS, 6 poprawek** (zwis łańcucha — dodany zakres; liczba przetłoczeń panelu 3 → „pewne 2”; rozdzielenie źródeł tabliczka/banery; proporcja przęsła 1,7 → 1,5–1,9; rozpiętość kątowa 0,03° → 0,014–0,035°; dwie współrzędne OSM). Szczegóły: `audit_20_percent.json`.

## 7. fetch.py

`python3 -I fetch.py [--out katalog] [--skip-large]` — pobiera 33 pliki (ok. 114 MB, w tym 39,7 MB PDF Dz.U.; `--skip-large` go pomija) i weryfikuje sumy; exit ≠ 0 przy braku pliku lub niezgodności. Test w czystym katalogu (2026-11-14): 16 plików GUGiK/PAŻP/Dz.U. OK (sha256 zgodne, WMS deterministyczny), 17 plików Commons — HTTP 429 z adresu sesji.

## Errata lidera (s20, 2026-11-14)
Patrz `docs/reports/REVIEW-2026-11-14-s20-cloud-m58.md` — errata obowiązuje przed użyciem danych.
