# Przegląd RESEARCH-PACK-02 (ChatGPT Pro) + P1 — s17, 2026-11-13

## NASTĘPNY KROK (dla sesji przejmującej)

**Przegląd ZAKOŃCZONY** (s17, 2026-11-13): P6, P9, P10, P4, P7, P1, P8, P2, P3, P5 — werdykty §2. Przyjęte paczki skopiowane 1:1 z ZIP do `research/gptpro/p*/` (P4 i P8 z podkatalogu `gptpro-*`); `research/_incoming/` zostaje. Bloki Mistrala M49–M55 + korekty M44/M45: `docs/owner/RESEARCH-PACK-03-MISTRAL.md`. Dla lidera: (1) dopisać `.gitignore` z §6 i `git add` listy z §6 (nic nie scommitowano); (2) przekazać §5 agentom — **pilne dla 0162: NIE dzielić bramownicy A na dwie tablice** (teza P7 fałszywa); (3) gałęzie GPT: `research/p8-*` można scalić (identyczna z ZIP), `p2/p6/p10` — nie scalać (ZIP pełniejszy/poprawny), `p7-s8-signs-2` — usunąć (test, uszkodzony JPG); (4) przekazać Mistralowi korektę M45 pkt 2. → kopiowanie przyjętych do `research/gptpro/` → `docs/owner/RESEARCH-PACK-03-MISTRAL.md`. Procedura na paczkę: §1. Skrypty pomocnicze (poza repo, `python -I`): `inv.py` (inwentarz manifestów), `show.py <manifest> <kolumny> <seed> <procent>` (losowanie próby) — w katalogu scratch sesji s17; łatwo odtworzyć (csv.DictReader, utf-8-sig, separator `,` lub `;`, `random.Random(seed).sample`).

## 1. Metoda (bez zmian względem pierwotnego planu)

Na paczkę: README/manifest (`utf-8-sig`; P3 i P8 mają separator `;`)/sources/audit → zgodność plików z manifestem → licencje (odrzucone: NC/ND/Google/brak licencji; Panoramax i Commons CC BY-SA, Mapillary CC BY-SA = tylko referencja) → **własna próba ≥ 20 %** (`random.Random(seed).sample(wiersze, ceil(0,2·n))`, seed podany) sprawdzana na żywo (API OSM `api.openstreetmap.org/api/0.6`, WebFetch źródeł, obejrzenie JPG) → porównanie z `research/g5-*`, `g7-*`, `g10-*`, `research/gptpro/*`. Nic z ZIP nie uruchamiano. Zakaz Google zachowany (nie otwierano żadnych linków Google).

## 2. Werdykty

| Paczka | Wiersze manifestu | Pliki | Werdykt | Próba (seed) |
|---|---|---|---|---|
| P6 regiony 2 | 48 | 29 (14 JPG ortofoto bram, 9 JPG RS16, 2 PDF urzędowe, 4 TXT/JSON OSM) | **PRZYJĘTA** | 10/48 (seed 6113): 10/10 zgodne + 2 dodatkowe (GDDKiA) zgodne |
| P9 meble 2 | 100 | 14 (6 PDF + 1 DOCX urzędowe/proxy, 6 JPG Commons CC0, 1 CSV) | **PRZYJĘTA z zastrzeżeniami** (11 wierszy Mapillary odrzucone — brak danych) | 20/100 (seed 9113): 15/15 sprawdzalnych zgodne; 2 UNVERIFIED zgodnie z deklaracją; 2 Mapillary puste; 1 (AKWA) nie sprawdzono |
| P10 zieleń 2 | 82 | 13 JPG Commons CC0 | **PRZYJĘTA z zastrzeżeniami** (liczby odcinków = WORKING_VALUE, niereprodukowalne) | 17/82 (seed 10113): 4/4 źródłowe zgodne, 1 częściowo, 12 ESTIMATED — rząd wielkości zgodny z ortofoto (3 wycinki) |
| P4 przepisy (nowa) | 161 | 10 (6 PDF + 4 HTML, urzędowe) | **PRZYJĘTA z zastrzeżeniami** (R48 Rev.12 / R46 Rev.5 nieaktualne — M44) | 33/161 (seed 4113): 20 potwierdzone, 6 nieznalezione dosłownie, 2 UNVERIFIED wg deklaracji, 4 pliki OK, 1 trywialne; 0 sprzeczności, 3 błędy opisu |
| P7 tablice 2 (nowa) | 7 (+25 recheck) | 7 JPG (6 Mapillary CC BY-SA, 1 Commons CC0) | **PRZYJĘTA CZĘŚCIOWO** — teza „675 Centrum osobna tablica na bramownicy A” **odrzucona** (fałsz na P7-001 i G3-P013); metoda tokenu Mapillary niedopuszczalna | 7/7 + G3-P005/P013: 5 zgodne, 1 fałszywa teza, 1 częściowa; recheck 25/25 zgodny z G3 |
| P1 zdjęcia trasy | 144 | 141 JPG (84 CC0, 54 CC BY-SA, 3 CC BY) | **PRZYJĘTA jako referencja** (CC BY-SA tylko referencja; kadry kierowcy z 2019) | 29/144 (seed 1113): 17/17 sprawdzone API zgodne, 11 niesprawdzone (HTTP 429 Commons), 1 UNVERIFIED wg deklaracji; 2/4 obejrzanych z luźnym przypisaniem |
| P8 ograniczenia 2 | 41 | 6 PDF urzędowe | **PRZYJĘTA** | 9/41 (seed 8113): 8/8 OSM zgodne, § 80 / e-TOLL / POŚPH potwierdzone w PDF, 3 UNVERIFIED wg deklaracji |
| P2 nawierzchnie | 94 | 37 (33 JPG, 4 PDF urzędowe) | **PRZYJĘTA z poprawkami** (P-11 źle opisany; pas rowerowy nie zawsze czerwony; Rynek = granit) | 19/94 (seed 2113): 15 zgodne (7 Commons/Panoramax API, 8 w PDF/rozporządzeniu), 1 błąd (P2-041), 1 przypisanie nietrafne (P2-024), 2 UNVERIFIED wg deklaracji |
| P3 zabudowa | 62 | 62 JPG + 1 PDF (skan) | **PRZYJĘTA CZĘŚCIOWO** — galeria zdjęć i parametry systemów WP; dane LoD1/kondygnacje/typ per adres **odrzucone** | 13/62 (seed 3113): metadane Commons 6/6 zgodne; treść: 5 błędów na 9 wierszy z liczbami (zły budynek LoD1, zły typ); Biazet = Andersa 44, nie 38 |
| P5 audio 2 | 83 | 51 (43 MP3, 7 OGG/Opus, 1 WAV) | **PRZYJĘTA** (referencje; NC/BBC tylko linki) | 17/83 (seed 5113): 8/8 licencji Freesound na żywo, 9/9 długości ffprobe zgodne, 2 UNVERIFIED wg deklaracji; 0 duplikatów z G9 |

## 3. Paczki

### P6 — regiony 2 (uzupełnienie G2) — PRZYJĘTA

**Formalnie:** README, manifest (48 wierszy: 6 kafli K, 12 celów C, 6 domknięć U, 10 tras R, 14 bram G), sources, audit (ich seed 20261113, 10/48, po poprawkach 10/10). Pliki bez wiersza manifestu to pomocnicze `P6-*00-*.txt/json` i 9 wycinków RS16 `P6-U01-a…h` (opisane w README). PDF-y 0,7 i 0,2 MB (urzędowe: PFU BIP Białystok, TED).

**Próba (seed 6113, 10 wierszy):** P6-C01, C11, G06, G13, G14, K01, R05, R08, U02, U03. API OSM: way 392226308 v9 „Enea Ciepło Oddział Elektrociepłownia Białystok” power=plant; way 229040230 v4 aeroway=hangar „Aeroklub Białostocki”; node 6085185775 v2 barrier=gate access=private (53.10726, 23.20303 = współrzędne manifestu); node 10875232003 v2 gate; node 6539179208 v1 gate; way 221209538 „Biaform”; way 687816195 v4 warehouse „DPD” (operator Panattoni Europe); way 1525765624 v1 „Panattoni Park Białystok III”; way 236603303 v5 „Biazet S.A.”. Wersje i nazwy zgodne 10/10. Dodatkowo WebFetch GDDKiA: komunikat z 20.10.2026 — „Kierowcy mogą już korzystać z drogi ekspresowej S19 Krynice - Dobrzyniewo - Białystok Zachód” (zgodne); komunikat z 29.10.2026 — MOP Haćki Wschód/Zachód po 26 ukośnych stanowisk dla ciężarówek (zgodne). Panattoni (U02): u nas **nadal HTTP 403** — twierdzenie paczki „403 nie odtwarza się” nie potwierdzone; fakt (32 000 m², Choroszcz) zostaje tylko referencją. Obraz P6-G06 obejrzany: ortofoto zakładu z rzędem tanków na dachu, placem z oznakowaniem poziomym i bramą przy drodze dojazdowej — zgodne z „Browar Dojlidy, brama”.

**Nowe względem G2:** kafle E/SE (G2 je pominęło — było to zastrzeżenie przeglądu G2, teraz domknięte i zgodne z D60), 5 domknięć UNVERIFIED z G2, trasy od S8 z wersjami ways, 14 bram z node OSM. **Sprzeczności/uwagi:** szerokości bram tylko 2/14 (ESTIMATED z przerwy w ogrodzeniu OSM), promienie łuków wszystkie UNVERIFIED; trasy to własny Dijkstra autora na wycinku Geofabrik — korytarze badawcze, nie organizacja ruchu; PZZ w OSM leży przy ul. Zbożowej (adres G2 „Elewatorska 14” niepotwierdzony); RS16 WIM Zabłudowska tylko ESTIMATED ±150 m.

### P9 — meble uliczne 2 (uzupełnienie G5) — PRZYJĘTA z zastrzeżeniami

**Formalnie:** README, manifest (100 wierszy: 26 wymiarowych P9-001…026, 52 przystanki P9-101…152, 6 zdjęć Commons P9-301…306, 11 pustych Mapillary P9-32x, reszta), sources, audit (ich seed 20261113, 20/100, 20/20 PASS). Statusy: SOURCED 74, UNVERIFIED 22, ESTIMATED 4. Pliki zgodne z manifestem; PDF-y ≤ 2,2 MB. `P9-005.pdf` to skan (pdftotext = 0 znaków) — wartość „ścianka ≥ 4 mm, uchwyt ø60–72” (STO ZDM Warszawa) niesprawdzalna tekstowo.

**Próba (seed 9113, 20 wierszy):** P9-006, 009, 010, 017, 026, 101, 107, 125, 126, 127, 133, 138, 143, 144, 147, 152, 304, 306, 324, 329.
- 11 przystanków — API OSM `nodes.json`: 11/11 współrzędne co do 1e-6°, `highway=bus_stop`, nazwy zgodne. Uwaga: w OSM dziś „Elektrociepłownia/Pętla” (poprawnie) — literówka „Elektociepłownia” jest po stronie GTFS, nie OSM (P9-133/147 można podnieść do SOURCED).
- P9-009 (U-12b: słupki 1,10 m, rozstaw 1,50/1,80, strzałka 0,10) i P9-010 (przęsło U-12 2,50×0,83, RAL 1012) — potwierdzone w `P9-002.pdf` (pdftotext, pkt 7–8); plik bajtowo zgodny z BIP (HTTP 200, 2 166 848 B). Dodatkowo `P9-001.pdf` = BIP bajt w bajt; ławka 1900 mm, deski ≥ 40 mm, PALISANDER — potwierdzone.
- P9-017 Oldisvet SS3: karta pobrana na żywo (HTTP 200) — H 5,8 m, 63/265 mm zgodne.
- Wrocław `P9-004.pdf` (kopia Wayback 20260707155954): treść spójna — maszt HY wysoki do 4,3 m, niski 1,5 m (pkt a/b), sygnalizatory od dołu 2,50 m na masztach HY, 5,50 m skrajnia podwyższona. Kopia z Wayback uznana za wiarygodną (spójny 189 kB tekstu, numeracja punktów), ale to **proxy spoza Białegostoku**.
- P9-304, P9-306 obejrzane: Andersa/Elektrociepłownia (komin, wiadukt, latarnie z talerzowymi oprawami, stacja paliw), grudzień i kwiecień — pasują do kafla. Commons API: obie CC0, autor Rakoon — zgodne.
- P9-006 (OPZ ZMK skan) — UNVERIFIED zgodnie z deklaracją; P9-026 AKWA — nie sprawdzono (karta ma zepsute fonty, wartość ESTIMATED 0,65 m nad gruntem pozostaje ESTIMATED).
- P9-324/329 Mapillary — puste wiersze (brak tokenu) → **odrzucone**, nie są danymi.

**Nowe względem G5:** G5 miał `signal_pole` 4,0 / `signal_mast` 6,8 jako WORKING_VALUE bez źródła i niespójność `power_pole` 10 vs 12 m. P9 daje: maszt HY 4,3 m (proxy Wrocław, potwierdzone), słupek SS3 5,8 m (producent białostocki, potwierdzone), głowica nad jezdnią ≥ 5,50 m (proxy); żerdzie ZPUE 9,0/10,5/12,0 m (brak „E-10”) — karta nie pobrana, nie sprawdzono w próbie → traktować jako SOURCED-referencja. Bariery ZDM Białystok 2018 (U-5a, „olsztyński”, U-12, U-12b, słupek podznakowy ø60,3) — **dokument białostocki, najcenniejsza część paczki**. **Uwagi:** wymiary koszy/stojaków/ławek „PSMPT Piotrków” to proxy; Glasdon bez modelu; latarnie 4–6/8–10 m = proxy Rapio (ESTIMATED); bbox README (≤ 23,185 E) nie obejmuje P9-126 (23,1927 E) — drobna niespójność opisu, dane OK.

### P10 — zieleń przyuliczna 2 (uzupełnienie G7) — PRZYJĘTA z zastrzeżeniami (dane liczbowe = ESTIMATED)

**Formalnie:** README (z gotowym, **niewysłanym** wnioskiem o informację publiczną do ZDM — wysłanie wymaga decyzji właściciela), manifest 82 wiersze (001–009 rejestr/nasadzenia, 101–114 zdjęcia Commons, 201–237 odcinki żywopłotów, 301–313 młode drzewa, 401–410 wymiary gatunków), sources, audit (seed 20261113, 17/82, 17/17). Statusy: ESTIMATED 50, SOURCED 31, UNVERIFIED 1. 13 JPG zgodnych z manifestem.

**Próba (seed 10113, 17 wierszy):** P10-005, 008, 201, 203, 208, 210, 212, 214, 215, 217, 222, 301, 303, 304, 305, 401, 410.
- P10-008: WebFetch rynekinfrastruktury.pl (HTTP 200) — „posadzono 74 drzewa oraz 109 krzewów” — zgodne.
- P10-401/410: karty Ebben (HTTP 200) — lipa drobnolistna 20–25 / 10–15 m, świerk 30–55 / 8–10 m — zgodne.
- P10-005: strona BIP (HTTP 200) istnieje; liczba „11 szt.” jest w załączniku (nie sprawdzono).
- Odcinki żywopłotów i młode drzewa (12 wierszy, ESTIMATED): **niereprodukowalne** — paczka nie zawiera pliku detekcji koron (3500 obiektów) ani skryptu. Kontrola jakościowa na ortofoto GUGiK WMS HighResolution (pobrane 3 wycinki ~130×130 m): P10-203 Buska 76 % — szeregowce z przedogródkami i żywopłotami, wiarygodne; P10-217 Motoszko odc. 4 „100 % / 33 korony” — luźna zabudowa z ogrodami i zadrzewieniem po W stronie, pokrycie wysokie, ale metryka liczy zieleń ogółem, nie żywopłot; P10-304 Al. Tysiąclecia odc. 7 „5 szt./100 m” — na ortofoto widać pojedyncze młode drzewa przy chodniku wschodnim, rząd wielkości zgodny. Werdykt: **rząd wielkości wiarygodny, liczby WORKING_VALUE**.
- Dodatkowo (poza próbą) Commons API dla P10-101/106/110: współrzędne, daty EXIF i CC0 zgodne co do cyfry. Obejrzane P10-101 (XII 2020, Al. Tysiąclecia przy Łańcuckiej w przebudowie — **zwarty żywopłot iglasty ~1,5–2 m przed domami**, stare topole/klony za ogrodzeniem budowy) i P10-110 (XII 2022, Andersa — młode nasadzenia z palikami, resztki śniegu).

**Nowe względem G7:** brak publicznego rejestru drzew (potwierdzone przeglądem ArcGIS miasta), Łaska 2015 (transekt Andersa 178 osobników, dominują Acer negundo/platanoides, Crataegus), 74 drzewa + 109 krzewów przy Al. Tysiąclecia (2021/22), 10 gatunków z wymiarami maksymalnymi (sufit, nie średnia). **Braki:** Skidelska i Świsłocka — 0 zdjęć; 6 ulic osiedla tylko kwiecień 2024; brak lata dla ulic jednorodzinnych; gatunki żywopłotów UNVERIFIED; detekcja tylko dla lon ≤ ~23,156 (Andersa poza zasięgiem).

### P4 — przepisy dla ciągnika N3 4×2 + naczepy O4 (nowa) — PRZYJĘTA z zastrzeżeniami (wersje R48/R46 nieaktualne → M44)

**Formalnie:** README, manifest 161 wierszy (separator `;`; 10 plików źródłowych + 151 pozycji normatywnych), sources, audit (seed 20261113, 33/161, 33/33). Statusy: SOURCED 157, UNVERIFIED 4 (P4-153 wymiar tablicy 520×114 z rysunku, P4-156 miejsce tachografu, P4-158 znak 80/90, P4-160 oznaczenia „promilowe”). Licencje: 158 × dokument urzędowy (art. 4), 3 × „—”. Pliki: 6 PDF (0,2–2,3 MB) + 4 HTML ELI/EUR-Lex (0,6–2,5 MB) — wszystkie urzędowe, ≤ 5 MB. HTML czytane wyłącznie jako tekst (strip tagów, bez wykonywania).

**Tożsamość i aktualność plików:**
- P4-001 = `E/ECE/324/Rev.1/Add.47/Rev.12`, 16.10.2014, **R48 seria 06**; P4-002 = `…Add.45/Rev.5`, 19.08.2013, **R46 seria 04** (manifest błędnie: „seria 03”). Obie kopie z Wayback (`…id_/http://www.unece.org/fileadmin/DAM/…`) — **wiarygodne** (oryginalna sygnatura dokumentu, spójne nagłówki, 349 / 183 tys. znaków tekstu, numeracja punktów ciągła), ale **NIEAKTUALNE**: wg wyszukiwania istnieje R48 **Rev.13** (seria 07; Amend.1 w mocy 30.09.2021) i propozycje do **serii 08** (WP.29 III 2025); R46 ma serie **05 (2022), 06, 07** (GRSG 2026: suplementy do serii 07). Na wygląd pojazdu (liczba/rozmieszczenie świateł, klasy lusterek) zmiany są prawdopodobnie małe, ale **nie wolno tego zakładać** — do potwierdzenia w M44.
- P4-003 R58 seria 03 (OJ L 49, 20.02.2019), P4-004 R73 seria 01 (OJ L 122, 2012), P4-005 R104 (OJ L 75, 2014) — teksty EN z EUR-Lex (URL wskazuje PL, plik EN — bez znaczenia). P4-006 96/53/WE konsolidat 14.08.2019 (PL). P4-007 WT t.j. Dz.U. 2024 poz. 502; P4-009 UTD t.j. Dz.U. 2024 poz. 1539. **P4-008**: manifest opisuje „rozporządzenie MI z 31.08.2022 (t.j.)”, a plik to **rozporządzenie MI z 8.11.2024** w sprawie rejestracji i oznaczania pojazdów (Dz.U. 2024 poz. 1709) — niespójny opis, treść (barwy, podział tablic) zgodna.
- README: „dyrektywa 96/53/WE zostanie zastąpiona rozporządzeniem (UE) 2024/5450” — numer aktu **niezweryfikowany, podejrzany**; traktować jako UNVERIFIED.

**Tezy kluczowe — zweryfikowane w pełnych tekstach (grep):**
- **Ciągnik siodłowy bez konturu R104:** R48 6.21.1.2.1(a) i 6.21.1.2.2.1(a) — „N3 (with the exception of chassis-cabs, incomplete vehicles and tractors for semi-trailers)”; WT §12 ust. 1 pkt 17 a/b — „nie dotyczy podwozia samochodu ciężarowego z kabiną i ciągnika siodłowego”. **POTWIERDZONE.**
- **Bez tablic wyróżniających:** WT §42 ust. 1 — „…przekracza 7,5 tony, z wyłączeniem ciągnika siodłowego, oraz przyczepy, w tym naczepy…”. **POTWIERDZONE** (naczepa O4 > 8 m — obowiązkowe, zał. 10).
- **Bez R58:** R58 seria 03, pkt **1.2.2** (nie 1.2.1, jak w manifeście P4-095) — „Tractive units for articulated vehicles”. **POTWIERDZONE** (pkt 1.2.1 w PDF pusty po ekstrakcji).
- Odblaski boczne na ciągniku: WT §12 ust. 1 pkt 11 „odblaskowe boczne — pojazd samochodowy o długości przekraczającej 6,0 m, ciągnik siodłowy i przyczepa”. **POTWIERDZONE.**
- **96/53/WE (P4-006):** 16,50 m, 2,55 m, 4,00 m, 12,00 m (sworzeń–tył), 2,04 m (sworzeń–przód naczepy), 11,5 t oś napędowa, 40 t, 44 t — wszystkie znalezione. Uwaga: **44 t dotyczy 3-osiowego pojazdu silnikowego** w transporcie intermodalnym (zał. I 2.2.2 c) — nasz ciągnik 4×2 → 40 t (w PL WT: 2-osiowy ciągnik + 3-osiowa naczepa intermodalnie 42 t przy kontenerze 45 stóp).

**Próba (seed 4113, 33 wiersze; automatyczny grep cytatów w oknach 6 słów + ręczny grep):** P4-001, 004, 008, 009 (pliki — obecne, tożsamość jw.); **potwierdzone 20:** 021 (2 przednie kierunkowskazy 1/1a/1b), 023 (boczne kat. 5 lub 6), 035 (tylne przeciwmgłowe obowiązkowe 1–2), 039 (obrysowe 2+2), 044 (tylne RA klasa IA/IB), 060 (cofania obowiązkowe na O2–O4), 064 (≤150 mm od krawędzi), 093 (R58: 200 mm przed próbą / 300 mm minus odkształcenie dla O3/O4), 095 (jw., zły numer punktu), 097 (listwy ≤ 300 mm, ≥ 100 mm dla N3/O4), 098 (≤ 250 mm za podporami), 100 (dolna krawędź ≤ 550 mm), 107 (16,50 m), 121 (4,00 m w WT), 136 (kontur PL, wyjątek ciągnika), 144 (≤ 400 mm od obrysu), 151 (podział tablic), 152 (czarne na białym/zielonym), 157 (tachograf w WT tylko autobusy/nauka jazdy), 161 (ADR — trywialne); **nieznalezione dosłownie (układ kolumn PDF, cytat skrócony „…”) — 6:** 043 (kąty 80°/5°/20°), 076 (przerwy konturu ≤ 50 %), 078/106 (R70 jako część konturu), 080 (klasa I opcjonalna na N3 — tabela), 155 (rozp. 2016/799 — pliku celowo brak); **UNVERIFIED zgodnie z deklaracją — 2** (158, 160). **Sprzeczności: 0**; błędy opisowe: 3 (seria R46, punkt R58, opis P4-008).

**Wartość dla gry:** pierwsza w projekcie kompletna normatywna lista elementów zewnętrznych ciągnika i naczepy z wysokościami/odległościami — bezpośrednio do modelu ciężarówki (docs/07). Wszystkie wartości R48/R46 oznaczyć `SOURCED (R48 06 / R46 04 — do aktualizacji M44)`.

### P7 — tablice 2 (uzupełnienie G3) — PRZYJĘTA CZĘŚCIOWO; **główna teza o bramownicy A ODRZUCONA**

**Formalnie:** README, manifest 7 wierszy (45 kolumn, schemat G3), `asset_manifest.csv` (sha256 7/7 zgodne z plikami — sprawdzone), `mapillary_recheck.csv` (25 pozycji G3), `LICENSE-DATA.md`, sources, audit (seed tekstowy, 2/7). Pliki: 6 JPG Mapillary `thumb_1024` (CC BY-SA 4.0 → **tylko referencja**), 1 JPG Commons CC0 (P7-006, Rakoon). Próba własna: **7/7** (całość — paczka mała) + 2 kadry G3 do porównania.

**Bramownica A (Andersa przed estakadą) — „675 Centrum na OSOBNEJ małej tablicy pod główną”: NIEPRAWDA.**
- P7-001 (2020-08-15, richlv) — powiększenie ×6 prawej tablicy: **jedna** zielona tablica z ramką obejmującą trzy wiersze: „8 | E 67 Augustów”, „19 Kuźnica PL BY ↗”, „675 Centrum” — wiersz 675 jest wewnątrz tej samej ramki.
- G3-P013 (2024-07-26, kino) — ten sam układ: jedna tablica, trzy wiersze, kartusz 675 rozmyty automatycznie.
- Źródło pomyłki GPT: G3-P005 (2024-08-15) pokazuje **inny obiekt — portal C przed rondem Putry**, gdzie rzeczywiście jest osobny mały panel „↑ 675 Centrum” między lewą tablicą (675 Centrum / 65 Bobrowniki PL BY / 19 Lublin) a prawą (8 E 67 Warszawa / 65 Ełk). GPT przypisał ten panel bramownicy A.
- **Dla 0162: NIE zmieniać geometrii `andersa-putry-approach-gantry` na dwie tablice.** Obecny model (jedna tablica, 675 Centrum jako wiersz) jest zgodny z 2020 i 2024. Ewentualna poprawka dotyczy portalu C (sprawdzić, czy w grze jest środkowy mały panel „↑ 675 Centrum”, G3-P005).

**Pozostałe ustalenia (obejrzane):**
- Wysięgnik B (łącznica Maczka–Putry): P7-003 (2020) — wysięgnik kratowy z tablicą-schematem (Warszawa/Ełk, Augustów/Kuźnica, 675 Centrum) — **potwierdzone**; P7-004 (2024-07-26, ~60 m dalej w tym samym kierunku) — nad jezdnią brak wysięgnika, widać tylko daleki portal — **zgodne z tezą o demontażu 2020–2024** (ESTIMATED, data nieznana).
- Portal C: P7-006 (Commons 2021-05-03, CC0) — portal z dwiema tablicami, w lewej dolny wiersz „675 Centrum” wyraźnie ciemniejszy (zaklejony) — **zgodne**; P7-005 (2020) — brak portalu — przyjęte (nie oglądano szczegółowo).
- P7-007 (E-1 Wasilków, 2024-09-01) — odczyt częściowy, tylko potwierdzenie istnienia.
- `mapillary_recheck.csv`: 25/25 wierszy zgodnych z manifestem G3 (klucz, data, współrzędne) — sprawdzone skryptem. Zgodności z API **nie dało się sprawdzić bez tokenu**.
- **DK19 SE / DK65 E / DK8 N / S19:** zrobione tylko jako **wynik negatywny bez dowodów** — „16 kadrów przy 10 węzłach, brak E-1…E-4”, ale klucze tych kadrów nie są w manifeście → niesprawdzalne, traktować jako UNVERIFIED. S19 (otwarta 20.10.2026): zero kadrów; tylko dokumenty — WebFetch `s19-krynice-ksiezyno.pl` (15.10.2026): „w dniu 20.10.2026 r. o godzinie 08.30”, „klauzulą nr 1249/2024” — **zgodne**.

**Metoda Mapillary („publiczny token odczytu”):** wg sources.md (MLY-API) token **wyjęty z kodu strony embed mapillary.com** — to nie jest token wydany projektowi; regulamin API Mapillary przewiduje własny token klienta z rejestracji aplikacji. Oceniam jako **niezgodne z warunkami serwisu (szara strefa, nie stosować w projekcie)**. Same odczyty treści tablic to fakty; kadry CC BY-SA i tak tylko jako referencja. Na przyszłość: Mistral/agent — własny token (konto właściciela, decyzja) albo brak Mapillary.

**Gałąź `origin/research/p7-s8-signs-2`:** 3 commity testowe GPT („to be reverted”), pliki `.tmp-test/test256.*` + `files/P7-001.jpg` **inny niż w ZIP** (124 259 B vs 83 680 B; push_files uszkadza binaria) → **nie scalać, usunąć gałąź**.

### P1 — zdjęcia trasy z poziomu kierowcy (kafel 53,152 N 23,168 E) — PRZYJĘTA jako referencja (bez tekstur z CC BY-SA)

**Formalnie:** README (tabela pokrycia 34 obiektów), manifest 144 wiersze (141 kadrów + 3 UNVERIFIED: Batorego, Brzeska, Buska — 0 zdjęć), sources, audit. 141 JPG (50 MB), ≤ 1600 px. Licencje: CC0 84 (Commons, głównie Rakoon), Panoramax CC BY-SA 4.0 50, CC BY-SA 3.0/4.0 Commons 4, CC BY 3.0 (pl) 3, puste 3 (wiersze UNVERIFIED). Mapillary — nie użyto (zgodnie z zasadą A). Drobna niespójność: Olsztyńska ma 0 ujęć w tabeli, a nie ma jej w lukach.

**Próba (seed 1113, 29 wierszy):** P1-004, 005, 008, 013, 016, 017, 018, 022, 023, 024, 026, 029, 030, 034, 035, 041, 042, 043, 045, 053, 082, 095, 105, 108, 130, 133, 135, 140, 143.
- **Panoramax API** (`api.panoramax.xyz/api/search?ids=`) — 7/7: data co do sekundy, położenie Δ 0,0 m, azymut `view:azimuth` = `kierunek_deg` (129, 169, 254, 128, 105, 264, 258), licencja CC-BY-SA-4.0 — **zgodne**.
- **Commons API** — 10/10 sprawdzonych: DateTimeOriginal co do sekundy, współrzędne Δ 0,0 m, CC0 — **zgodne**; 11 kolejnych (P1-026…082) — **HTTP 429 (limit API Commons), niesprawdzone na żywo** (pliki obecne, ten sam autor/seria co sprawdzone).
- P1-143 (Brzeska) — UNVERIFIED zgodnie z deklaracją.
- **Obejrzane 4:** P1-108 (Maczka, przejazd pod wiaduktem między ścianami oporowymi, 2019, poziom kierowcy — dobre), P1-022 (Skidelska — prosta ulica z latarniami, słup WN, ciężarówka; poziom pieszego), P1-041 („Andersa środek”) — w rzeczywistości **parking Podlaskiego Centrum Rolno-Towarowego**, nie widok jezdni; P1-095 („wiadukt Al. Tysiąclecia nad torowiskiem”) — droga w lesie sosnowym z barierą, wiaduktu nie widać → **przypisanie do obiektu luźne** (bufor 25 m od osi; kadr najazdu, nie obiektu).

**Wartość:** metadane rzetelne (17/17 sprawdzonych na żywo). Kadry kierowcy (Panoramax) **wszystkie z 15.08 i 01.09.2019** — sprzed portalu C przy rondzie Putry (2021) i przed przebudową Al. Tysiąclecia (2021/22) → do geometrii wiaduktów/łącznic Maczka i DK8 dobre, do oznakowania i zieleni Al. Tysiąclecia **nieaktualne**. Kadry Commons to głównie poziom pieszego; kierunek UNVERIFIED. Duża część kadrów Commons pokrywa się z P9/P10 (seria Rakoon).

### P8 — ograniczenia ciężarówek 2 (uzupełnienie G10) — PRZYJĘTA

**Formalnie:** README, manifest 41 wierszy (`;`), sources, audit. SOURCED 21, UNVERIFIED 20 (uczciwie: skrajnie pod wiaduktami bez znaku, podstawy zakazów bez zarządzeń, 2 pozycje zdjęciowe Mapillary puste). 6 PDF urzędowych (0,2–4,9 MB, wszystkie ≤ 5 MB): Dz.U. 2022 poz. 1518 (WT dróg), Dz.U. 2026 poz. 33 (e-TOLL), 3 listy MF e-TOLL, POŚPH (uchwała LI/794/18). Pliki P8-015/017 są tekstowe (pdftotext OK) — „własny dekoder CMap” niepotrzebny po naszej stronie.

**Próba (seed 8113, 9 wierszy):** P8-001, 002, 003, 014, 016, 022, 023, 030, 033.
- API OSM `ways.json` (8 ways): Maczka 23844386 v40 i Andersa 25447143 v30 (`bridge=viaduct`, `maxaxleload=11.5`, brak `maxheight`), Al. Tysiąclecia 197904073 v19 (`ref=8;19`, 11.5), S8 183639790 v24 `toll:hgv=yes`, S8 183639794 v31 bez toll, Bitwy Białostockiej 178208423 `hgv=no`+`goods=delivery`, Branickiego 572651591 `maxweight=8`, Warszawska 842154286 `maxweight=12 t`+`hgv=no`+`goods=delivery` — **8/8 zgodne** z manifestem (w tym sprzeczność Warszawskiej).
- P8-012 (Dz.U. 2022 poz. 1518) — § 80 ust. 1: „5,00 m — … klasy A lub S; 4,50 m — … klasy GP, G, Z, L lub D” — **potwierdzone** (korekta założenia „4,0 m” z G10 słuszna).
- P8-015 (lista MF od 1.02.2026) — sekcje „Węzeł Tykocin — Węzeł Choroszcz” 3490 m i „Węzeł Choroszcz — Choroszcz (skrzyżowanie…)” 960 m na S8 — **potwierdzone**; obwodnica S8 bezpłatna — zgodne z OSM.
- P8-025 POŚPH — „zakaz ruchu pojazdów ciężarowych o dopuszczalnej masie całkowitej > 12 t” jako planowane działanie — **potwierdzone**; „klasy tonażowe 3,5/12/40 t” z G10 — w tekście brak (7 trafień słów kluczowych, żadne nie jest klasyfikacją) → **G10 do korekty**.
- P8-014/016 — pliki obecne, tożsame z opisem (nagłówki), treści nie grepowano. Wiadukty P8-001…003: skrajnia UNVERIFIED zgodnie z deklaracją.

**Nowe względem G10:** skrajnia ustawowa 4,50/5,00 m (nie 4,0), e-TOLL po 1.02.2026 (S8 płatna tylko do węzła Choroszcz; DK8 przy Białymstoku, DK19, DK65, nowa S19 — bezpłatne), uchwała LI/794/18 = program ochrony przed hałasem (archiwalny), nie plan tonażowy; B-20 to STOP (G10 błędnie), ograniczenia masy = B-18/B-19; komunikaty ZDM XI 2025 (Suchowolca 3,5 t, Mickiewicza 8 t — zgodne z OSM). Reguła rozstrzygania: urzędowe > OSM (z `check_date`) > wartości ustawowe; przy sprzeczności OSM — restrykcyjniej.

### P2 — nawierzchnie i elementy jezdni (nowa) — PRZYJĘTA z poprawkami

**Formalnie:** README (z tabelą szerokości linii P-1…P-25), manifest 94 wiersze, sources, audit (seed 20261113, 19/94 — **lista odtwarza się z seeda** i zgadza z README ZIP; README w gałęzi `origin/research/p2-surfaces` ma błędną listę → gałęzi nie scalać). 33 JPG + 4 PDF urzędowe (0,25–1,05 MB): ZDiT Białystok wytyczne (zał. 5, BIP 99308), WT-2 2016 cz. II GDDKiA, SST pl. Niepodległości, SST D.05.03.05 ścieżka rowerowa. Statusy: SOURCED 78, UNVERIFIED 9, ESTIMATED 7. Licencje: urzędowe 44, CC0 12 (README mówi 17 — niespójność), CC BY-SA 3.0/4.0 22, tioman.pl copyright 7 (tylko referencja), „—” 9.

**Próba (seed 2113, 19 wierszy):** P2-001, 002, 011, 015, 017, 022, 024, 033, 034, 040, 041, 048, 055, 069, 070, 071, 082, 089, 094.
- Commons API (7 zdjęć, jedno zapytanie): licencje, autorzy i daty zgodne (Rakoon CC0 ×2; CC BY-SA 3.0/4.0 ×5). Panoramax P2-033: położenie i licencja zgodne (2019-08-15).
- Dokumenty w paczce (pdftotext): krawężniki 15×22×100 i 12×25×100 B30 (P2-069) ✓; obrzeża 6×20 na podsypce 5 cm (P2-070) ✓; kostka 6 cm (P2-071) ✓; „wyraźnie inny kolor” przejazdu rowerowego (P2-055) ✓; ZDiT krawężnik przystankowy 16 cm ✓; AC 8 S 50/70 czerwony 3 cm ✓.
- **Rozporządzenie Dz.U. 2019 poz. 2311 zał. 2** — pobrałem sam (ELI, część c2, 28 MB, tylko do scratch): P-7a/b 0,24 m „na autostradach i drogach ekspresowych, na drogach posiadających twarde pobocze lub opaskę” ✓; przejście dla pieszych 4,0 m ✓; cienkowarstwowe 0,3–0,8 mm / grubowarstwowe 0,9–3,5 mm / punktowe do 25 mm ✓; β 0,32/0,30 ✓. **BŁĄD P2-041:** P-11 to **przejazd dla rowerzystów**, a 1,8 m / 3,0 m to minimalna szerokość przejazdu **jednokierunkowego / dwukierunkowego** — nie „przebieg przejścia/azyl, max 3,0 przy dużym ruchu rowerów”.
- P2-082 (P-21 z tioman.pl) — ESTIMATED, źródło chronione → tylko referencja (zgodnie z deklaracją). P2-089/094 — UNVERIFIED zgodnie z deklaracją.
- **Obejrzane 4:** P2-001 — pas rowerowy wymalowany na **szarym** asfalcie (linia przerywana + symbol roweru), **nie czerwony** → teza README „czerwony asfalt potwierdzony zdjęciami P2-001…008” **częściowo fałszywa**: w Białymstoku są oba warianty (pas malowany na jezdni szary; wydzielona droga rowerowa czerwona wg SST); P2-015 (S8 Złotoria, zima 2013, poziom wiaduktu) ✓; P2-024 (Rynek Kościuszki) — **kostka granitowa** (nieregularna, szaro-beżowa) z pasami płyt, nie betonowa 6 cm — „analogia SST” nietrafna; P2-033 (pod wiaduktem przy Putry, z auta) ✓.

**Wartość:** standardy białostockie (ZDiT) + SST + rozporządzenie — rzetelne. Kolory sRGB = ESTIMATED (mediana wycinka) — tylko orientacyjnie. Brak zdjęć kafla startowego (Jaroszówka), azyli, płytek dotykowych, ścieków.

### P3 — typologia zabudowy (nowa) — PRZYJĘTA CZĘŚCIOWO (zdjęcia + parametry systemów); **dane per adres (LoD1/kondygnacje/typ) ODRZUCONE**

**Formalnie:** README, manifest 62 wiersze (`;`; 8 typów), sources, audit (13/62, 13/13 — sprawdzali tylko HTTP 200, licencję i JPG, **nie treść**), 62 JPG (16 MB), `docs/mpzp_bialostoczek_uchwala.pdf` (0,97 MB — **skan bez warstwy tekstowej**; tezy o kolorach elewacji/dachach z MPZP pochodzą z „projektu tekstu planu” spoza paczki → niesprawdzalne). Licencje: CC0 39 (Rakoon), CC BY 3.0 4, CC BY-SA 2.0/3.0/4.0 19 (Borawski, Adam63 — tylko referencja).

**Próba (seed 3113, 13 wierszy):** P3-003, 015, 016, 017, 023, 028, 030, 031, 042, 044, 050, 052, 058.
- Commons API (6 z próby): licencje, autorzy, daty, współrzędne — **zgodne** (Rakoon CC0, Borawski CC BY-SA 3.0/4.0).
- **Treść vs dane — 5 błędów na 9 wierszy z liczbami:**
  - P3-003 „blok wielkopłytowy, Białostoczek 4/1”: zdjęcie = 5-kondygnacyjny blok ✓, ale w manifeście **2 kondygnacje i LoD1 4,94 m** (dopasowany inny budynek);
  - P3-015/016 „dom jednorodzinny, Wysoki Stoczek 21/23”: LoD1 **19,31 / 18,46 m** (dopasowany kościół w tle; na zdjęciu mały budynek z latarnią na dachu przy kościele — typ wątpliwy);
  - P3-030 „pawilon handlowy, Sitarska 7”: LoD1 **16,44 m**; zdjęcie: parter usługowy budynku 2-kondygnacyjnego;
  - P3-044 „garaże blaszane, Zwierzyniecka 21”: na zdjęciu **garaże murowane** (cegła, żółte bramy), LoD1 **16,15 m** (blok obok);
  - P3-050 „stacja paliw, Andersa 38”: to ten sam plik co P9-306 (`20250412_090304`) — na zdjęciu **pusty plac, latarnie i żółty wieżowiec, żadnej stacji**; LoD1 10,16 m.
- **README: „Andersa 38 = biurowiec Biazet S.A.” — błąd.** API OSM: way 236603303 v5 „Biazet S.A.” = **Andersa 44**, `building=industrial`, `building:levels=2` (zgodne z P6). Opisana „rozbieżność 41 m vs 10,16 m” dotyczy więc innego obiektu.
- Przyczyna: dopasowanie „najmniejszy obrys LoD1 zawierający **punkt kamery**” / „najbliższy ≤ 30 m” — kamera stoi na ulicy, fotografowany budynek jest dalej → systematycznie zły budynek.

**Co przyjąć:** zdjęcia jako galeria typów (CC0 do dowolnego użytku, CC BY-SA tylko referencja); parametry systemów wielkiej płyty (OWT-67 kondygnacja 2,70 m, siatka 5,4×4,8 m; W-70 2,80 m, moduł 0,60 m, rozstawy 2,4–6,0 m; Szczecin 4,80 m) — fakty z Wikipedii/POIIB, nie przypisane do osiedli (UNVERIFIED per adres); dowody termomodernizacji (BZP 2024/BZP 00352328: Kołłątaja 67/69/71 + Pileckiego 4 — nie sprawdzałem na żywo); obserwacja, że **LoD1 2024 ma wszędzie roofType=1000** (płaskie) — do potwierdzenia na danych z naszego pipeline. **Nie przyjmować:** kolumn `kondygnacje`, `lod1_measuredHeight_m`, `adres` przy ESTIMATED, typu dla P3-044/050.

### P5 — referencje audio 2 (uzupełnienie G9) — PRZYJĘTA (jako referencje; luki kategorii 1, 2, 4, 5 potwierdzone)

**Formalnie:** README, manifest 83 wiersze, `download_list.csv` (59 oryginałów Freesound do pobrania przez właściciela — tylko licencje CC0/BY), sources, audit (17/83). 51 plików (74 MB): 43 podglądy MP3 Freesound, 7 OGG/Opus Commons, 1 WAV 96 kHz/24 bit (fragment OGA). Licencje: CC0 35, CC BY 3.0/4.0 29, CC BY-SA 3.0/4.0 3, **NC 4 + BBC RemArc 12 — tylko linki, nie pobrane** (sprawdzone skryptem: 0 plików NC/RemArc w `files/`, 0 plików bez wiersza). **0 ID wspólnych z G9** (72 ID G9 vs 63 P5 — sprawdzone).

**Próba (seed 5113, 17 wierszy):** P5-002, 010, 013, 014, 022, 026, 031, 047, 056, 057, 059, 061, 062, 065, 071, 074, 079.
- Freesound na żywo (8 stron): 87316 CC BY 4.0 „Bus Step Lowering”, 488679 CC BY 3.0 „Air dryer1.wav”, 833747 CC BY 4.0 „2007 New Flyer D40LFR (Voith transmission)”, 420925 CC BY 3.0 „modern truck driving exterior”, 166501 **BY-NC 3.0** (manifest: NC, nie pobrano ✓), 135208 CC0 „Mercedes Benz 709D … Icy Road”, 62513 **BY-NC 4.0** (manifest: NC ✓), 90348 CC BY 4.0 — **8/8 licencji i tytułów zgodnych**.
- ffprobe (9 plików lokalnych): długości zgodne z manifestem co do ±0,15 s (np. P5-002 20,000 s 96 kHz; P5-022 228,8; P5-031 126,4 vs 126,5 deklarowane, 16 kHz MPEG-2 — ich poprawka błędu z G9 działa).
- P5-013 „osuszacz” — tytuł na Freesound „Air dryer1.wav”; UNVERIFIED (czy pojazdowy) zgodnie z deklaracją. P5-079 BBC — UNVERIFIED/niekomercyjne ✓. P5-071/074/062/061 — niepobrane, licencje nie sprawdzane na żywo.
- Uwaga merytoryczna: Mercedes 709D to minibus z silnikiem pod/za kabiną (półwagonowy), nie klasyczny cab-over — jako referencja „kabina nad silnikiem” tylko przybliżona.

**Wartość:** uczciwe wyniki negatywne (brak wolnych nagrań retardera, AMT z przerwą momentu, R6 12–13 l z nazwanym modelem; najbliżej MAN D2566MUM 11,4 l — Commons/Work With Sounds CC BY 4.0). Do pracy audio: kategorie 3 (pneumatyka) i 7 (foley kabiny, 33 pozycje) są użyteczne; retarder i hamulec silnikowy dalej przez ElevenLabs / własne nagrania (zgodnie z wcześniejszą decyzją o ElevenLabs).

### Gałęzie GPT na origin (`origin/research/*`) vs ZIP — porównanie SHA (po normalizacji CRLF/BOM)
- `research/p6-next-regions-2`: README, manifest, sources, audit, 4 TXT identyczne; **`P6-R00-trasy.json` w gałęzi jest uboższy** (brak pól `detail` w 10 trasach) + dodatkowy `files/BINARIES.md`. → **nie scalać**; kopiować z ZIP (pełniejszy).
- `research/p8-truck-restrictions-2`: README, manifest, sources, audit identyczne + `files/FILES_NOTKA.md`. → można scalić gałąź (i dołożyć PDF-y z ZIP), jeśli P8 przyjęta.
- `research/p10-street-greenery-2`: manifest identyczny; README/sources/audit różnią się tylko formatowaniem (brak backticków w gałęzi; audit w jednej linii) + `files/BINARIA.md`. → kopiować z ZIP (ładniejszy markdown); gałąź można zamknąć bez scalania.
- `research/p2-surfaces`: manifest, sources, audit identyczne; **README różni się listą ID próby** (gałąź: P2-040, 041, 048…; ZIP: P2-039, 040, 047…) — rozstrzygnięte: ZIP zgodny z `audit_20_percent.json` i z seedem 20261113 (odtworzone), gałąź błędna → **nie scalać**, kopiować z ZIP.
- `research/p7-s8-signs-2`: test GPT — nie przyjmować (patrz P7).

## 4. Licencje (zbiorczo)

| Paczka | Licencje w manifeście | Co do repo | Co odrzucone / tylko referencja |
|---|---|---|---|
| P6 | ODbL (28), otwarte dane PZGIK/GUGiK (14), urzędowe art. 4 (4), brak licencji – tylko referencja (2) | README, manifest, sources, audit, `P6-*00-*.txt/json`, PDF U01 i U04 | JPG ortofoto lokalnie (`files/`, poza gitem); Panattoni i Biazet — tylko fakty |
| P4 | dokument urzędowy art. 4 (158), „—” (3) | README, manifest, sources, audit, wszystkie 10 plików (PDF/HTML urzędowe ≤ 2,5 MB) | nic; rozp. 2016/799 (19,5 MB) — tylko link |
| P5 | CC0 (35), CC BY 3.0/4.0 (29), CC BY-SA (3), NC (4, tylko link), BBC RemArc (12, tylko link) | README, manifest, download_list.csv, sources, audit | 51 plików audio lokalnie (`files/`, 74 MB); NC/BBC — nie pobrane, odrzucone do użytku |
| P3 | CC0 (39), CC BY 3.0 (4), CC BY-SA 2.0/3.0/4.0 (19); MPZP — urzędowy | README, manifest (z adnotacją przeglądu), sources, audit, `docs/mpzp_bialostoczek_uchwala.pdf` (0,97 MB) | 62 JPG lokalnie; CC BY-SA — tylko referencja |
| P2 | urzędowe (44), CC0 (12), CC BY-SA 3.0/4.0 (22), tioman.pl copyright (7), „—” (9) | README (z ZIP, nie z gałęzi), manifest, sources, audit, 4 PDF | 33 JPG lokalnie; CC BY-SA — tylko referencja; tioman — tylko referencja (nie pobrano) |
| P8 | ODbL (19), urzędowe art. 4 (19), Mapillary puste (2), „-” (1) | README, manifest, sources, audit, 6 PDF (≤ 4,9 MB) — **lub scalić gałąź `research/p8-truck-restrictions-2` (identyczna) i dołożyć PDF** | nic |
| P1 | CC0 (84), Panoramax CC BY-SA 4.0 (50), Commons CC BY-SA 3.0/4.0 (4), CC BY 3.0 (3), puste (3) | README, manifest, sources, audit | 141 JPG lokalnie (`files/`); CC BY-SA (54) — tylko referencja, nie tekstury; CC BY 3.0 — wolno z atrybucją |
| P7 | CC BY-SA 4.0 Mapillary (6), CC0 Commons (1); recheck — fakty | README, manifest, asset_manifest, mapillary_recheck, LICENSE-DATA, sources, audit | 6 JPG Mapillary — tylko referencja, lokalnie; P7-006 CC0 lokalnie; gałąź testowa — odrzucić |
| P10 | CC BY 4.0 GUGiK ortofoto (+ODbL osie) (50), CC0 Commons (13), katalog Ebben — fakty (10), artykuły — fakty (5), urzędowe (2), pusta (1) | README, manifest, sources, audit | 13 JPG CC0 lokalnie (`files/`); Panoramax CC BY-SA — tylko referencja (nie pobrano); karty Ebben — tylko fakty |
| P9 | ODbL (52), urzędowe art. 4 (17), producenci — fakty (12), CC0 (4), CC BY 3.0 (2), Mapillary brak dostępu (11), GTFS bez licencji (1) | README, manifest, sources, audit, PDF P9-001…006 (urzędowe/wytyczne, ≤ 2,2 MB), DOCX P9-007 | JPG Commons lokalnie (CC0/CC BY 3.0 — wolno, ale binaria poza gitem); `P9-401.csv` lokalnie (zawiera kody GTFS bez jawnej licencji — tylko referencja); Mapillary — odrzucone; karty producentów — tylko fakty |

## 5. Przekaż agentom

### 0166 — region Dojlidy/Krywlany (z P6, zweryfikowane próbą)
- Kafle 2×2 km, rogi EPSG:2180 (SW→NE), kolejność wg P6: **K01** 777019,593199→779019,595199 (przylega od S do bboxu `bialystok-industrial-c`; 11,53 km dróg ≥ secondary; cele TAK: Elektrociepłownia Andersa 15 way 392226308, Forte way 219260044, ALBA way 264234891) → **K04** 779019,589199→781019,591199 (4,44 km; Rosti, KAN, Odlewnia way 315456645, Bravilor way 513010463, PSS Społem DC way 1317072247) → **K05** 781019,589199→783019,591199 (4,37 km; browar Dojlidy, Bieldruk way 913986997, Polfood way 1280704126) → **K03** 777019,589199→779019,591199 (lotnisko Krywlany, hangary Aeroklubu way 229040230 — punkt orientacyjny, nie cel) → **K02** 777019,591199→779019,593199 (czysty korytarz Branickiego/Legionowa). Ciągłość: K1–K2 Branickiego, Legionowa; K2–K3 Wiejska; K3–K4 Dywizjonu 303, Ciołkowskiego; K4–K5 Kuronia. Źródło: `research/gptpro/p6-next-regions-2/README.md` §3.1, `files/P6-K00-kafle.txt`.
- Uwaga: K01 zaczyna się na x=777019, region na x=776971 (przesunięcie 48 m, konwencja G2 — 2048 m regionu vs 2000 m kafli). Sprawdzić przy siatce chunków.
- Bramy (node OSM, do ustawienia wjazdów): browar Fabryczne 28 node 6085185775 (private), Bieldruk node 10875232003, Bravilor node 6539179208, Rosti node 6596800253, KAN node 4656499172 (lift_gate), Masterpress node 2999986083, BIAFORM node 2814000970; Elektrociepłownia — brama nie zmapowana. Szerokości i promienie UNVERIFIED (zmierzyć na `files/P6-G*.jpg`, 10 cm/px, bbox w manifeście).
- Konflikty z G10: dojazd do KAN wg routera wchodzi 247 m w Adama Mickiewicza (maxweight=8); BIAFORM — rondo Meyera (hgv=no) i Dojlidy Fabryczne (3,5 t od XII 2025). Browar: wjazd od Kuronia. Nie projektować zleceń przez te odcinki bez decyzji.
- S19 Krynice–Dobrzyniewo–Białystok Zachód otwarta 20.10.2026; MOP Haćki 2×26 stanowisk TIR od 29.10.2026 (GDDKiA, zweryfikowane).

### 0161 — kadry kontrolne Putry/Maczka (z P1, metadane zweryfikowane API)
- Kadry z poziomu kierowcy ze znanym azymutem (Panoramax, CC BY-SA → tylko referencja do porównania, nie do tekstur): **rondo Putry** — P1-114 (wlot Al. Tysiąclecia, az. 56°), P1-120 (wlot Maczka, az. 113°); **Maczka** — P1-108/118/137 (początek, az. 254°, przejazd pod wiaduktem), P1-099/135/140 (początek, 258–264°), P1-096/103/131/139 (środek, 96–104°), P1-098/132 (skrzyżowanie z Orlicz-Dreszera, 103°/271°); **wiadukt Maczka nad torami** — P1-094/117/123 (269°), P1-133/134/136 (93–117°); **most Maczka nad Białą** — P1-092/115 (100°), P1-141 (274°); **łącznica DK8 węzeł Andersa/Maczka** — P1-097/122/124/128/138 (268–275°), P1-111/125/127/129 (98–113°); **kładka Maczka** — P1-109 (108°), P1-113 (272°). Pliki: `research/gptpro/p1-route-photos/files/P1-NNN.jpg` (lokalnie), azymut w `manifest.csv` `kierunek_deg`.
- **Uwaga epoki:** wszystkie kadry kierowcy z 15.08.2019 / 01.09.2019 — przed portalem C (2021) i przebudową Al. Tysiąclecia (2021/22). Do kamer kontrolnych: geometria wiaduktów/ścian oporowych/bariery — tak; oznakowanie i zieleń — porównywać z G3 2024 i P10.
- Kamera Panoramax za szybą samochodu osobowego (widoczna maska i wycieraczka; wysokość ESTIMATED ~1,3–1,5 m, niezmierzona) — dla kamery ciężarówki (oko ~2,5 m) skorygować wysokość.

### 0162 — tablice (z P7, zweryfikowane na zdjęciach)
- **Bramownica A `andersa-putry-approach-gantry`: NIE dzielić na dwie tablice.** Prawa tablica to jedna tablica 3-wierszowa (8 E 67 Augustów / 19 Kuźnica PL BY ↗ / 675 Centrum) — `research/_incoming/p7-s8-signs-2/files/P7-001.jpg` (2020) i `research/gptpro/3-s8-signs/files/G3-P013.jpg` (2024). Lewa: 8 E 67 Warszawa / 65 Ełk ↑.
- **Portal C (przed rondem Putry, od 2021):** lewa tablica (↑675 Centrum / ←65 Bobrowniki PL BY / 19 Lublin) + **osobny mały panel „↑ 675 Centrum”** + prawa (8 E 67 Warszawa / 65 Ełk →) — G3-P005. Sprawdzić, czy gra ma ten środkowy panel.
- Oś czasu: wysięgnik B na łącznicy Maczka–Putry istniał 2018–2020, w 2024 brak (epoka gry 2024+ → bez wysięgnika B); portal C powstał 08.2020–05.2021.
- S19 Krynice–Dobrzyniewo–Białystok Zachód: docelowa organizacja ruchu od 20.10.2026 8:30 (klauzula 1249/2024) — treści tablic nieznane (0 zdjęć) → nie modelować tablic S19 bez dokumentu/zdjęcia.

### 0162 — meble i tablice (z P9, zweryfikowane próbą)
- **Bariery białostockie (ZDM 2018, `research/gptpro/p9-street-furniture-2/files/P9-002.pdf` pkt 6–9):** U-5a pylon PE 0,90 m, ø0,20, podstawa 0,30, RAL 1012; panel „olsztyński” słupki ø60,3 (ścianka 2–3,2 mm), przęsło ø48,3, RAL 1012; U-12b słupki 1,10 m co 1,50/1,80 m, łańcuch strzałka 0,10; U-12 przęsło 2,50×0,83, 5 płaskowników 15×6, pręty pionowe ≥ 5 mm co 5 cm, słupki 60×40×1,5 RAL 3020; słupek podznakowy ø60,3 × ≥ 2,9 mm.
- **Ławka miejska Białystok (P9-001):** min. 1,90×0,45×0,45 m, beton + drewno PALISANDER, deski ≥ 40 mm, podstawa grafit/jasnoszara.
- **Sygnalizacja:** zamienić `signal_pole` 4,0 → **4,3 m** (maszt HY, proxy Wrocław) lub 5,8 m (SS3 Oldisvet); `signal_mast` 6,8 → wysięgnik z głowicą **≥ 5,50 m** nad jezdnią (dolna krawędź), oznaczyć WORKING_VALUE (proxy). Soczewki S-1 ø200, S-2 ø300 (zał. 4 rozporządzenia — wtórne źródło). Sygnalizator na maszcie od dołu 2,50 m.
- **Żerdź energetyczna:** `power_pole` → 12,0 m (ZPUE E-12, ø0,398→0,218) — SOURCED-referencja (karta niepobrana; nie w próbie).
- **Hydrant nadziemny:** AKWA H to długość całkowita; część nadziemna ≈ H − Rd = 0,65 m (ESTIMATED, nie w próbie), kolumna ø0,1016, RAL 3000. Szafka gazowa 0,60×0,60×0,25 RAL 7035 (proxy ANCO); szafka telekom 27U 1,52×0,87×0,66 (proxy KZA). Osłona drzewa ø1,20/1,50/2,00, gr. 0,04 (proxy Zano).
- **Przystanki:** 52 węzły OSM w kaflu Andersa ↔ kody GTFS (`files/P9-401.csv`, lokalnie) — do nazw i numerów słupków przystankowych; 50 pewnych + 2 (Elektrociepłownia/Pętla) też pewne wg OSM dziś.
- Wszystkie „PSMPT Piotrków”, „ZDiUM Wrocław”, „Kraków 162/2025”, producenci = **proxy**, nie Białystok; nie wpisywać jako SOURCED-Białystok.

### Graf dróg / ograniczenia (geo-worldgen, ADR 0164) — z P8
- Skrajnia domyślna: **5,00 m** drogi A/S, **4,50 m** pozostałe (§ 80 ust. 1 Dz.U. 2022 poz. 1518); redukcja do 4,20 m tylko za zgodą — w grze nie zakładać < 4,50 m bez znaku B-16. `maxheight=default` ignorować.
- e-TOLL (od 1.02.2026): S8 płatna na zachód do węzła Choroszcz włącznie (`toll:hgv=yes` w OSM zgodne), obwodnica S8, DK8 przy Białymstoku, DK19, DK65 i nowa S19 — bezpłatne.
- Reguła sprzeczności: dokument urzędowy > OSM (z `check_date`) > wartość ustawowa; przy sprzeczności wewnątrz OSM (Warszawska `maxweight=12 t` + `hgv=no`) — wariant restrykcyjny z flagą. `hgv=no`+`goods=delivery` = zakaz z wyjątkiem dostaw (dojazd do celu dozwolony).
- Znaki: B-5 zakaz ciężarowych > 3,5 t; B-18 rzeczywista masa; B-19 nacisk osi; **B-20 to STOP** (G10 do korekty). „Klasy tonażowe 3,5/12/40 t” z uchwały LI/794/18 — **nie istnieją** (to program ochrony przed hałasem, archiwalny).

### 0163 — zieleń (z P10 i P1)
- Al. Tysiąclecia (przebudowa Strabag, koniec 01.2022): 74 drzewa + 109 krzewów na całym odcinku; młode korony (r 0,7–2,0 m) 0–18 szt./100 m w buforze 20 m, średnio ~5/100 m, maksima przy lat 53,1575 (18), 53,1558 (12), 53,1524 (10) — `manifest.csv` P10-301…313, WORKING_VALUE. Drzewa z palikami (3 paliki) widoczne na kadrach zimowych Andersa (P10-110).
- Ulice jednorodzinne (Buska, Grodzieńska, Lidzka, Łańcucka, Motoszko, Olsztyńska, Kowieńska, Racławicka, Wołkowyska…): pokrycie zielenią przydomową w buforze 8 m od osi — P10-201…237 (37 odcinków po 100 m); wysokie (≥ 75 %) na większości, niskie: Buska środek (0–59 %), Grodzieńska-2 26 %, Olsztyńska-1 22 %. Żywopłot dominujący na kadrze P10-101: iglasty (tuja/żywotnik) ~1,5–2 m — gatunek UNVERIFIED.
- Andersa (transekt Łaska 2015, 2011 r.): 178 osobników, 15 gatunków; Acer negundo 35, A. platanoides 30, Crataegus monogyna 25 → mieszanka samosiewu klonu jesionolistnego i klonu zwyczajnego, nie aleja jednogatunkowa.
- Wymiary maksymalne (Ebben, sufit): lipa drobnolistna 20–25/10–15 m, klon pospolity 20–30/15–20, jawor 25–30/20–25, brzoza 15–20/6–12, jesion 25–30/20–25, topola kanadyjska 25–30/15–20, dąb szypułkowy 25–35/20–30, świerk 30–55/8–10. W mieście skalować w dół (G7 + własne pomiary).
- Brak lata dla ulic osiedla, brak zdjęć Skidelskiej/Świsłockiej → sesja zdjęciowa właściciela lub Mistral.

### 0167 — budynki (z P3; ostrożnie)
- **Nie używać** kolumn `kondygnacje` / `lod1_measuredHeight_m` / adresów ESTIMATED z `p3-building-typology/manifest.csv` — w próbie 5/9 dopasowań LoD1 do złego budynku (punkt kamery zamiast fotografowanego obiektu). Wysokości brać z naszego importu LoD1/BDOT10k.
- Przyjęte reguły: blok 5-kond. ≈ 15,4–15,7 m LoD1 (Sokólska 11 15,47; Broniewskiego 6C 15,65; Wierzbowa 15 15,41 — z README, nie w próbie) → ~3,1 m/kond. brutto; kondygnacja wielkiej płyty 2,70 (OWT-67) / 2,80 m (W-70); rytm okien ESTIMATED 2,4–2,8 m (siatki systemów). System per osiedle — UNVERIFIED.
- LoD1 2024: wszystkie dachy płaskie (roofType=1000) → dachy skośne domów z OSM `roof:shape` lub reguł typu; drewniane domy podlaskie (Bojary, Prowiantowa, Chmielna, Wąska, Olecka, Choroszczańska, Ślusarska, Słonimska 31) — materiał tylko ręcznie (`authored_overrides`).
- Galeria referencyjna typów: `research/gptpro/p3-building-typology/files/` (lokalnie); garaże przy Zwierzynieckiej 21 są **murowane** (P3-044), nie blaszane.
- Biazet S.A. = **Andersa 44** (way 236603303, industrial, 2 kond.) — nie Andersa 38.

### Model ciężarówki (truck-artist / docs/07) — z P4
- **Ciągnik N3 4×2 (siodłowy):** BEZ tylnego i bocznego konturu R104, BEZ żółto-czerwonych tablic wyróżniających, BEZ tylnej osłony przeciwwjazdowej R58; **Z** odblaskami bocznymi (pojazd > 6 m wymieniony z nazwy w WT §12.1 pkt 11), 2 tylnymi odblaskami nietrójkątnymi klasy IA/IB, bocznymi kierunkowskazami kat. 6 (N3), obrysowymi 2 przód + 2 tył, 1–2 tylnymi przeciwmgłowymi. Osłony boczne R73 tylko jeśli dotyczy (listwy ≤ 300 mm odstęp, ≥ 100 mm wys., dolna krawędź ≤ 550 mm).
- **Lusterka N3 (R46 seria 04):** klasa II 1+1, klasa IV 1+1, klasa V 1+1 (montaż ≥ 2 m), klasa VI przednie 1 (≥ 2 m), klasa I wewnętrzne opcjonalne, klasa III niedopuszczalna. **Uwaga:** nowsze serie R46 dopuszczają systemy kamera-monitor zamiast luster — M44.
- **Naczepa O4 kurtynowa 13,6 m, 3 osie:** pełny kontur R104 z tyłu + częściowy z boku; tablice wyróżniające z tyłu (WT zał. 10: tło żółte odblaskowe, obrzeże czerwone fluorescencyjne; dolna krawędź ≥ 250 mm, górna ≤ 2100 mm, ≤ 400 mm od obrysu bocznego) — R48 6.21.7.4 dopuszcza liczenie tablic R70 jako części konturu; trójkątne odblaski tylne wierzchołkiem do góry; 2 światła cofania (naczepa > 6 m); osłona R58: ≤ 200 mm od tyłu przed próbą; boczne R73: przednia krawędź ≤ 250 mm za płaszczyzną podpór, dolna ≤ 550 mm.
- **Wymiary (96/53/WE):** zestaw ≤ 16,50 m, szer. ≤ 2,55 m, wys. ≤ 4,00 m, sworzeń–tył naczepy ≤ 12,00 m, sworzeń–dowolny punkt przodu naczepy ≤ 2,04 m (promień), oś napędowa ≤ 11,5 t, DMC zestawu **40 t** (44 t tylko 3-osiowy ciągnik intermodalnie — nie nasz przypadek).
- **Tablica rejestracyjna tył:** miejsce 520×120 mm, dolna krawędź ≥ 0,30 m, górna ≤ 1,20 m, czarne znaki na białym tle (wymiar 520×114 z rysunku — UNVERIFIED). Brak wymogu: klinów pod koła (negatywne ustalenie), żółtego koguta (tylko pojazdy robót/pomocy), znaku 80/90 na naczepie (brak podstawy prawnej w PL — UNVERIFIED), tablic ADR (pojazd nie-ADR). Tachograf: obowiązek z UTD (kara 10 000 zł), miejsce w kabinie UNVERIFIED.
- Źródło: `research/gptpro/p4-truck-regulations/manifest.csv` (P4-011…079 tabela R48, P4-080… lusterka, P4-093… osłony, P4-107… wymiary, P4-136… WT).

## 6. Pliki do `git add` (lider) i `.gitignore`

(uzupełniane po każdej paczce)

- `research/gptpro/p6-next-regions-2/{README.md,manifest.csv,sources.md,audit_20_percent.json}`, `files/P6-C00-osm.txt`, `files/P6-G00-osm.txt`, `files/P6-K00-kafle.txt`, `files/P6-R00-trasy.txt`, `files/P6-R00-trasy.json`, `files/P6-U01.pdf`, `files/P6-U04.pdf`
- `research/gptpro/p9-street-furniture-2/{README.md,manifest.csv,sources.md,audit_20_percent.json}`, `files/P9-001.pdf` … `files/P9-006.pdf`, `files/P9-007.docx`
- `research/gptpro/p10-street-greenery-2/{README.md,manifest.csv,sources.md,audit_20_percent.json}`
- `research/gptpro/p7-s8-signs-2/{README.md,manifest.csv,asset_manifest.csv,mapillary_recheck.csv,LICENSE-DATA.md,sources.md,audit_20_percent.json,REVIEW-NOTE.md}` (REVIEW-NOTE = uwaga o fałszywej tezie bramownicy A)
- `research/gptpro/p1-route-photos/{README.md,manifest.csv,sources.md,audit_20_percent.json}`
- `docs/reports/REVIEW-2026-11-13-s16-research-pack-02.md`, `docs/owner/RESEARCH-PACK-03-MISTRAL.md`

**Proponowany `.gitignore`** (dopisać w `research/gptpro/.gitignore` albo w głównym; G3 ma JPG w gicie — tego nie zmieniamy):
```
# binaria paczek GPT Pro — lokalnie, poza gitem (s17)
research/gptpro/p*/files/*.jpg
research/gptpro/p*/files/*.jpeg
research/gptpro/p*/files/*.png
research/gptpro/p*/files/*.mp3
research/gptpro/p*/files/*.ogg
research/gptpro/p*/files/*.opus
research/gptpro/p*/files/*.wav
research/gptpro/p*/files/*.csv
research/_incoming/
```
Uwaga: reguła `files/*.csv` wyklucza `P9-401.csv` (GTFS bez licencji — celowo). PDF/HTML/DOCX/TXT/JSON w `files/` zostają śledzone (wszystkie urzędowe ≤ 5 MB albo dane OSM). Kopie w `research/gptpro/p*/` są 1:1 z ZIP (P6 sprawdzone `diff -r`: identyczne); `research/_incoming/` nie usunięto.
- `research/gptpro/p5-audio-refs-2/{README.md,manifest.csv,download_list.csv,sources.md,audit_20_percent.json}`
- `research/gptpro/p3-building-typology/{README.md,manifest.csv,sources.md,audit_20_percent.json,REVIEW-NOTE.md}`, `docs/mpzp_bialostoczek_uchwala.pdf`
- `research/gptpro/p2-surfaces/{README.md,manifest.csv,sources.md,audit_20_percent.json}`, `files/P2-034.pdf` … `files/P2-037.pdf`
- `research/gptpro/p8-truck-restrictions-2/{README.md,manifest.csv,sources.md,audit_20_percent.json}`, `files/P8-012.pdf`, `P8-014.pdf` … `P8-017.pdf`, `P8-025.pdf` (alternatywa: merge `origin/research/p8-truck-restrictions-2` + same PDF-y)
- `research/gptpro/p4-truck-regulations/{README.md,manifest.csv,sources.md,audit_20_percent.json}`, `files/P4-001.pdf` … `files/P4-005.pdf`, `files/P4-010.pdf`, `files/P4-006.html` … `files/P4-009.html`

## 7. Braki → paczka 03 (Mistral)

Zamienione na bloki w `docs/owner/RESEARCH-PACK-03-MISTRAL.md`: P6 → M49, P9 → M50, P10 → M51, P2 → M52, P3 → M53, P8 → M54, P5 → M55; P1 → już w M46; P4 → do potwierdzenia w M44; P7 → M45 (+ korekta pkt 2).

- P6: szerokości bram 12/14 i promienie łuków 14/14 (pomiar na ortofoto GUGiK); RS16 dokładna pozycja; adres PZZ (Elewatorska vs Zbożowa); organizacja ruchu na końcówkach Myśliwska/Karpińskiego/Dojlidy Fabryczne (uchwały/projekty organizacji ruchu BIP).
- P9: zdjęcia z poziomu kierowcy (11 typów mebli, kafel Andersa) z licencją komercyjną; OCR skanów (OPZ ZMK stojaki, STO ZDM Warszawa P9-005, zał. 4 Dz.U. 2019 poz. 2311 rys. s. 370); model Glasdon (ławki/kosze 2019); białostocki standard latarni (wysokości wg klasy drogi); karta żerdzi ZPUE E-12 (potwierdzenie 12,0 m).
- P4 → **M44 (już zlecone) ma potwierdzić:** (1) aktualną serię/rewizję R48 (Rev.13+/seria 07–08) i czy zmieniły się dla N3/O4: wyjątek konturu dla „tractors for semi-trailers” (6.21.1.2), liczby i wysokości świateł P4-015…079, kąty obrysowych 80°/5°/20° (6.13.5); (2) aktualną serię R46 (05–07) — tabela obowiązkowych klas lusterek N3 (15.2.1.1) i dopuszczenie CMS zamiast lusterek klas II/IV; (3) R58 seria 03 nadal aktualna, pkt 1.2.2; (4) status rewizji 96/53/WE (rzekome „rozporządzenie (UE) 2024/5450” — sprawdzić numer/istnienie); (5) rysunek tablicy 520×114 mm (rozp. 8.11.2024, Dz.U. 2024 poz. 1709); (6) miejsce tachografu (rozp. 2016/799 / 165/2014); (7) aktualny t.j. WT (po Dz.U. 2024 poz. 502) — §12, §42, zał. 10.
- P5: nagranie retardera (hydrokinetyczny/elektromagnetyczny) i hamulca silnikowego pojedynczego pojazdu z kabiny i z zewnątrz; AMT z przerwą momentu (np. autobus/ciężarówka z I-Shift/Opticruise/TraXon); R6 12–13 l z nazwanym modelem; cykliczna regeneracja osuszacza powietrza pojazdu — wszystkie tylko z licencją komercyjną (CC0/BY); jeśli brak — potwierdzenie negatywne z listą przeszukanych źródeł.
- P3: poprawne dopasowanie zdjęć do budynków (obrys LoD1/BDOT10k **fotografowanego** obiektu, nie punktu kamery) dla min. 30 budynków w kaflu Andersa/Białostoczek; system wielkiej płyty per osiedle (Białostoczek, Bacieczki, Zielone Wzgórza, Wysoki Stoczek — monografie, BIP spółdzielni); kolory elewacji po termomodernizacji (STWiOR spółdzielni/TBS, zdjęcia 2024+); tekst MPZP Białostoczek z warstwą tekstową; pełne zdjęcie i adres stacji paliw przy Andersa (Circle K).
- P2: zdjęcia (wolna licencja) kafla startowego Jaroszówka, azyli, płytek dotykowych, ścieków/wpustów; szerokości P-2…P-6 z rysunków zał. 2 (Dz.U. 2019 poz. 2311, PDF c2 s. ~530–545) i P-12/13/14/21/23/25 z rysunków (zamiast tioman.pl); rodzaj kostki Rynku Kościuszki; kolor pasów vs dróg rowerowych na trasie startowej; aktualny katalog standardów ZDM Białystok (nowszy niż „wytyczne” BIP 99308).
- P8: zdjęcia/inwentaryzacja znaków B-16 i rzeczywistej skrajni pod wiaduktami Putry, Andersa, Al. Tysiąclecia, Wolnej Ukrainy, Żołnierzy Wyklętych, Niepodległości (S8); podstawa prawna (zarządzenie/projekt organizacji ruchu) zakazów: Bitwy Białostockiej `hgv=no`, Sokólska `hgv=no`, Branickiego/Zwierzyniecka `maxweight=8`, Warszawska 12 t vs `hgv=no`; nośności 8 wiaduktów S19 (11,5 t/oś — GDDKiA) w OSM po aktualizacji.
- P1: zdjęcia z poziomu kierowcy 2024–2026 (wolna licencja) dla ronda Putry, Al. Tysiąclecia po przebudowie i Andersa; zero zdjęć Batorego/Brzeskiej/Buskiej/Olsztyńskiej; drugi sezon dla Grodzieńskiej, Kowieńskiej, Wołkowyskiej, Świsłockiej, Lidzkiej, kładki i mostów Maczka (tylko lato 2019). Najprościej: sesja zdjęciowa właściciela (lista punktów z P1).
- P7 → **M45 (już zlecone, ten sam temat) ma jeszcze sprawdzić:** (1) bramownica A — potwierdzić niezależnie, że „675 Centrum” to wiersz tej samej tablicy (my: tak, P7-001 + G3-P013), a nie osobna tablica; (2) portal C — czy mały środkowy panel „↑ 675 Centrum” (G3-P005) nadal stoi; (3) stan 2025–2026 bramownicy A i portalu C (brak kadrów po 09.2024; potrzebne zdjęcie 2025/26 z wolną licencją); (4) DK19 SE / DK65 E / DK8 N — wynik negatywny P7 z **jawnymi kluczami kadrów/zdjęć**; (5) tablice S19 węzeł Białystok Zachód i Dobrzyniewo (projekt stałej organizacji ruchu, klauzula 1249/2024 — czy dostępny w BIP GDDKiA/ZDM); (6) **bez używania cudzego tokenu Mapillary**.
- P10: lato (VI–VIII) dla 9 ulic osiedla (Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka, Wileńska, Grodzieńska, Racławicka, Łańcucka) — wolne licencje; gatunki żywopłotów (zdjęcia z poziomu ulicy); reprodukowalna detekcja koron (plik wynikowy GeoJSON + metoda) dla całego kafla, w tym Andersa (lon > 23,156); obwody/wysokości drzew Al. Tysiąclecia (projekt zieleni z dokumentacji Strabag/ZDM, jeśli w BIP).
