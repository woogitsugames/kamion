# Przegląd PR-ów Mistrala r8: #46 M49 (P6 bramy Dojlidy), #44 M54 (P8 ograniczenia), #45 M50 (P9 meble), #47 M55 (P5 audio), #48 M52 (P2 nawierzchnie) — ZAKOŃCZONY

Metoda: `git fetch origin`, `git show origin/<gałąź>:…`, `gh pr diff --name-only`, próba z seedem (Python `random.Random('<seed>')`), API OSM 0.6, WebFetch źródeł, oglądanie JPG (wycinki wokół węzłów OSM przeliczonych do EPSG:2180, pasek 10 m). Nic nie scalone, brak komentarzy na GitHubie, brak commitów.

## PR #46 — M49 `research/mistral-p6-dojlidy-gates` — PRZYJĄĆ CZĘŚCIOWO (po M49-FIX)

Formalnie: diff tylko `research/mistral/p6-dojlidy-gates/` (5 plików), JPG poza gitem (`.gitignore files/*.jpg`), ZIP rozpakowany w `research/_incoming/mistral-p6-dojlidy-gates/` (35 JPG 1600×1600 = 0,1 m/px, PFU 2015 PDF). Brak Google/Mapillary. Węzły bram zgodne z API OSM co do 1e-7°.
Próba: seed `s17-M49-review-1113` → M49-006, 009, 016, 022, 027, 028, 029, 030 (8/35 = 23 %) + dodatkowo 010, 012, 031–035 (ważne dla 0166).

| id | Teza Mistrala | Sprawdzenie | Wynik |
|---|---|---|---|
| 006 G06 Browar, szer. 9,0 ±2 | obejrzany wycinek: brama ze szlabanem, 2× STOP, prześwit ogrodzenie–portiernia ≈ 10 m | OK |
| 014/028 G14 Bravilor, 7,0 m / R 4,5 | wycinek: przerwa w płocie ≈ 6,5 m; łuki zjazdu małe | OK (ESTIMATED) |
| 022 G08 DPD, R 6,4 | wycinek: lift_gate (OSM access=delivery), lewy łuk mały, prawy ~20 m; raportowany mniejszy | OK |
| 009 G09 Raben ~26 ±7 | „korytarz”, nie brama; samo przyznane | OK jako ESTIMATED, mało użyteczne |
| 010/024 G10 PZZ ~11 m, R 8,3 | „wjazd drogowy” = way 248109974 to **`service=parking_aisle`** (3 węzły, kończy się ok. 80 m od Elewatorskiej). Wycinek: koniec aisle to **pusty piaszczysty plac** przy biurowcu z parkingiem — brak bramy, brak asfaltu. Teza „node 3465808562 = brama na torze railway=disused” — **prawdziwa** (API: way 339393639 railway=disused) | **ODRZUCIĆ wartości 010/024**; obserwacja o błędzie P6 OK |
| 012 G12 EC, 5,0 m | node 3954799626 (barrier=gate, **access=no**) leży na płocie EC (fence 392226284, landuse 392226308) i service 177903959 — prawdziwy. Ale to północna furtka, ~400 m NNE od celu P6; „brama dla ciężarówek” bez źródła. **Wycinek `M49-G12.jpg` (bbox P6 778428,594942…) NIE obejmuje tej bramy** (węzeł 455 m poza kadrem) — pomiar zrobiono na innym oknie, nieudostępnionym | UNVERIFIED (brama ciężarowa EC nadal nieustalona) |
| 029 RS16 SOURCED ±25 m | PFU 2020 (docx z BIP, pobrany): „oddalona jest od **stałego punktu kontroli** w odległości ok. 1295m”, „obsługuje ruch… **na kierunku do Miasta**”. Mistral mierzył 1295 m od **skrzyżowania** ze Stoczni Gdańskiej (to tylko miejsce szafki), a manifest pisze „kier. Zabłudów, strona prawa” — sprzeczne z PFU. Lokalizację pokazuje „załącznik nr 5” PFU — nie pobrany | **ESTIMATED ±50 m**, pas **wjazdowy do miasta**; obniżyć z SOURCED |
| 030 PZZ = Elewatorska 14 | WebFetch pzz.bialystok.pl/kontakt: „ul. Elewatorska 14, 15-959 Białystok”, „Zbożowa” nie występuje | OK |
| 031 Dojlidy Fabryczne + Suchowolca >3,5 t | komunikat bialystok.pl 19.11.2025 (E. Bilewicz-Roszkowska) — potwierdzony; **daty wejścia w życie w nim brak**. TVP3: dostępny tylko tytuł „Dojlidy bez tranzytu ciężarówek od stycznia” — cytat „powyżej 3,5 tony… w styczniu” nieweryfikowalny | OK z zastrzeżeniem (data = tytuł TVP3) |
| 032 Mickiewicza >8 t Kuronia–Ciołkowskiego | komunikat potwierdza dosłownie | OK |
| 033 rondo Meyera bez hgv | API: ways 552379031/623410840 bez hgv/maxweight; jest `maxaxleload=11.5` | OK |
| 034 Myśliwska | API way 353943959: hgv=no, maxweight=3.5 — tylko OSM | OK jako UNVERIFIED urzędowo |
| 035 Karpińskiego | API way 275237230: **highway=unclassified** (Mistral: tertiary) | drobny błąd |
| 016/027 R G02 4,3 / G13 | metoda RANSAC na masce asfaltu, niski udział inlierów (0,20); nieobejrzane narożniki R-* nie są w ZIP | ESTIMATED, niska wiarygodność |

Ocena: 8 próby → 6 OK, 1 obniżony (029), 1 częściowo (016/027 bez wycinków narożników). Poza próbą: 010/024 odrzucone, 012 niepotwierdzony. Samokontrola Mistrala (6/7 OK) — rzetelniejsza niż w poprzednich PR (sama znalazła korektę G12), ale nie wyłapała błędu kierunku RS16 ani parking_aisle przy PZZ.

**Fakty dla agentów 0166 (Dojlidy):** szerokości bram do użycia (ESTIMATED): G03 8,0 · G04 7,7 · G05 7,0 · G06 9,0 · G07 15,4 · G08 12,6 · G11 7,8 · G13 16,5 (±3) · G14 7,0 m; promienie łuków ESTIMATED ±2 m z tabeli README (nie dla G10). G10 PZZ: adres Elewatorska 14 pewny, brama drogowa **nieustalona** (node P6 to brama kolejowa) — nie modelować bramy z M49. G12 EC: brama ciężarowa nieustalona. Zakazy: Dojlidy Fabryczne + część Suchowolca hgv>3,5 t (od ~01.2026), Mickiewicza Kuronia–Ciołkowskiego >8 t, Myśliwska hgv=no/3,5 t (tylko OSM) — **zgodne z OSM, graf może je brać z tagów**. Rondo Meyera: brak zakazu, 2 pasy na wprost z wlotu Dojlidy Fabryczne. RS16: pas wjazdowy DK19 do miasta, ~1,3 km od punktu kontroli, ±50 m.

M49-FIX dopisany do `docs/owner/MISTRAL-FIXES-8.md`.

## PR #44 — M54 `research/mistral-p8-restrictions-3` — PRZYJĄĆ (wyniki głównie negatywne, rzetelne) po drobnym M54-FIX

Formalnie: diff tylko `research/mistral/p8-restrictions-3/` (8 plików). PDF-y w gicie jako `.b64` (3 pliki, obejście uszkodzonego pushu binarnego) — **dekodowanie daje `%PDF-1.7` i SHA256 zgodne 3/3** z sources.md. Zdjęcia poza gitem (`files/photos/` w .gitignore); ZIP w `research/_incoming/mistral-p8-restrictions-3/` (40 JPG Panoramax, 4 Commons, metadane, kopie stron). **Zdjęcia mają 2048×1536 (limit 1600 px — przekroczony 40/40)**; metadane Panoramax mają `az: null` — przypisanie kadrów tylko po odległości. Brak Google/Mapillary.
Próba: seed `s17-M54-review-1113` → M54-003, 008, 010, 013, 023, 026 (6/28 = 21 %) + 007, 016–019 (S19).

| id | Teza | Sprawdzenie | Wynik |
|---|---|---|---|
| 003 | Al. Tysiąclecia ways 197904073/74 nad linią nr 6 | API: oba `bridge=yes, layer=1`, trunk ref 8;19; rail way 34171047 ref=6 — droga NAD koleją | OK (wniosek dla gry: **na Al. Tysiąclecia nad linią 6 brak ograniczenia skrajni**) |
| 008 | „wiadukt nad jezdnią widoczny, brak znaków” (tysiac_412f2d02) | obejrzany: kamera jedzie **po** obiekcie (balustrady, latarnie, las), nad jezdnią nic nie ma | opis błędny (obiekt pod kołami, nie nad); wniosek „brak B-16” trywialnie prawdziwy |
| 007 | „na 6ded8ec0 widoczne B-19 i E-67” | obejrzany: tablice 8/19 + E67 (OK) i znak **B-26 zakaz wyprzedzania przez ciężarówki** + B-33 70 — **nie B-19** | błąd odczytu znaku |
| 007 | putry_35224dcb (15 m) — brak B-16 | obejrzany: poziom ronda pod estakadą Andersa/Maczka (filary, Browar Miejski, kominy EC); brak B-16 w kadrze | OK |
| 010 | Bitwy Białostockiej hgv=no+goods=delivery od v1 2012-08-27 cs 12883607 cyunczykg | historia API zgodna (v1 nazwa „I Armii Wojska Polskiego”) | OK |
| 013 | Branickiego maxweight=8 od v1 2018-03-24 cs 57486579 | historia API zgodna (pawka007) | OK |
| 014 (dod.) | Zwierzyniecka maxweight dodane v4 2014-08-05 cs 24555223 cyunczykg | historia API zgodna | OK |
| 016–019, 023 | S19 Krynice–Białystok Zachód: 20.10.2026, 10,2 km, 8 wiaduktów, 4 mosty, 12 przejść, 11,5 t/oś, S8 1,9 km, PORR+Unibep 405,6 mln, sąsiednie Q1 2029 | WebFetch gov.pl/web/infrastruktura — wszystkie liczby zgodne dosłownie | OK |
| 026 | brak nowych odcinków e-TOLL w promieniu 40 km | `pdftotext` na zdekodowanym PDF **działa** (Mistral: „tekst nieekstraktowalny”); lista nowych: DK8 Augustów–Janówka, S8 Zambrów… — nic w 40 km; pełna lista: S8 Rzędziany–Tykocin 5470 / Tykocin–Choroszcz 3490 / węzeł Choroszcz 960 m | OK (teza o nieekstraktowalności fałszywa) |

Ocena: próba 6 → 5 OK, 1 błędny opis zdjęcia (008); poza próbą 1 błędny odczyt znaku (007). Samokontrola „6/6 PASS” sprawdzała HTTP/API/pliki, nie treść kadrów — ten sam wzorzec co w poprzednich PR (opisy kadrów niesprawdzone). Wyniki negatywne (brak B-16, brak numerów zarządzeń) mają listę przeszukanych źródeł — akceptowalne.

**Fakty dla grafu/nawigacji:** (1) Wiadukty Putry, Wolnej Ukrainy, Żołnierzy Wyklętych, S8/Choroszcz: **brak potwierdzonego B-16** → w grafie skrajnia ustawowa (4,50 m; drogi klasy A/S 5,00 m), `maxheight` nie dodawać. (2) Al. Tysiąclecia nad linią 6 — droga na obiekcie, bez ograniczenia. (3) Korekta G10: w Starosielcach nad al. Niepodległości jest rondo Kmicica (bridge), nie S8. (4) Zakazy Bitwy Białostockiej (hgv=no+delivery), Sokólska (hgv=no od 2026-10-22, bez źródła — **niska pewność**), Warszawska 12 t+hgv=no, Branickiego/Zwierzyniecka 8 t — **brać z tagów OSM, podstawa prawna nieustalona** (rejestr ZDM niepubliczny). (5) S19 Krynice–Białystok Zachód: 11,5 t/oś, bez opłaty e-TOLL na 13.11.2026, OSM ma 5 z 8 wiaduktów. (6) e-TOLL w promieniu 40 km: tylko S8 Rzędziany–Choroszcz (3 odcinki, 9,92 km); DK8/19/65 bezpłatne; bez zmian po 1.02.2026.

M54-FIX dopisany do `docs/owner/MISTRAL-FIXES-8.md`.

## PR #45 — M50 `research/mistral-p9-furniture-3` — PRZYJĄĆ CZĘŚCIOWO: dokumenty TAK, zdjęcia NIE (M50-FIX)

Formalnie: diff tylko `research/mistral/p9-furniture-3/` (5 plików), `files/` w .gitignore, ZIP rozpakowany w `research/_incoming/mistral-p9-furniture-3/` (66 kadrów KartaView 1280 px, 27 dokumentów). Licencja KartaView CC BY-SA 4.0 (referencja, nie tekstura) — poprawnie. Brak Google/Mapillary.
Próba: seed `s17-M50-review-1113` → M50-004, 016, 017, 018, 036, 041, 044, 047, 048, 049 (10/49 = 20 %) + dodatkowo kadry hydrantów/słupka/bariery/żerdzi (9 kadrów obejrzanych łącznie) i OPZ.

| Zakres | Sprawdzenie | Wynik |
|---|---|---|
| OPZ ZMK DZ.26.2.8.2026.JO (025/026) | obejrzany skan s. 1: U 80×80 nierdzewny, 110 cm (80 nad gruntem), szer. 80, rura 48,3×2, 2 stanowiska, 54 szt. | OK dosłownie |
| Glasdon 2019 (044) | obejrzane zawiadomienie 26.06.2019 DGK-IV.271.58.2019: Glasdon Europe AB, 17 146,20 zł, jedyna oferta, art. 4 pkt 8 | OK; model Glasdon słusznie UNVERIFIED |
| Dz.U. 2019 poz. 2311 cz. 2 (033, 036, 041) | pobrany PDF (41 MB), `pdftotext`: s. 754 „4,5-5,5 m nad jezdnią”, s. 760 „1,5-1,7 m”, s. 843 U-12a „od 0,80 m do 1,20 m”, U-12b „1,10 m… 1,5 m lub 2,0 m… do 0,10 m” | OK; korekta zadania (zał. 3, nie 4; rys. 7.2.1 s. 756) — trafna |
| Żerdź E-12 (047/048) | karty Solbet/Gislebork — nie pobierano (zasada „pliku nie pobieraj”); spójne z P9-023 ZPUE | przyjąć jako VERIFIED-wtórne |
| 049 hydranty | negatywny: zał. 4 nie reguluje hydrantów | OK |
| 004 sygnalizator 5062571 | obejrzany: sygnalizatory na wysięgnikach przy estakadzie (Putry) | OK |
| 016 szafka 219382225 | obejrzany: skrzyżowanie z sygnalizatorem, szafki nie widać | **NIE potwierdzam** |
| 017 ławka 1326673717 | **kadru nie ma w ZIP** | nieweryfikowalne |
| 018 ławka NOT_FOUND 219382277 | obejrzany: brak ławki | OK |
| hydranty 5062587, 1326673477, 1326673829 (VERIFIED_WIZJA) | obejrzane: przejście dla pieszych / jezdnia z ekranami / estakada z ekranami — **hydrantu brak na 3/3** | **FAŁSZ** |
| U-5a 219381941, żerdź 1326673805, bariera 993066622 | obejrzane: autobus na jezdni (słupka nie widać), latarnie stalowe + słup kratowy WN (żerdzi brak), sygnalizatory + płot posesji (nie U-12) | **nie potwierdzam** |

Ocena: dokumenty 7/7 OK (najlepsza część paczki r8). Zdjęcia: z 9 obejrzanych kadrów „potwierdzonych wizją” zgodne 1–2 (sygnalizatory, latarnie), 6 niezgodnych — **ten sam wzorzec co P11/P1B: „VERIFIED_WIZJA” bez oglądania** (README sam podaje limit „20 wywołań” na 14 VERIFIED_WIZJA + 10 NOT_FOUND + skany). Samokontrola „all-pass” sprawdzała tylko format pól. Kadry z lat 2016–2021, wymóg „≥ 2 kadry na typ” niespełniony.

**Fakty dla następcy 0162 (meble):** stojak rowerowy ZMK 2026 („U 80x80”): **U z rury Ø48,3×2 mm, szer. 0,80 m, wys. 0,80 m nad gruntem**, stal nierdzewna, wbetonowany, dwustronny. Sygnalizatory: dodatkowe nad jezdnią 4,5–5,5 m; pomocnicze obok jezdni 0,8–1,5 m; dla pieszych 1,5–1,7 m (Dz.U. 2019/2311 zał. 3). U-12a 0,80–1,20 m (szare/żółte), U-12b 1,10 m, rozstaw słupków 1,5/2,0 m, słupki biało-czerwone pasy 25 cm; U-5a 0,90–1,20 m, szer. 0,20–0,30 m, żółty. Żerdź E 12: L=12,0 m, D podstawy 353–443 mm, d wierzchołka 173–263 mm (E 12/6 i 12/12: 398/218). Ławki/kosze Glasdon 2019: 4+3 szt. przy pomniku ks. Popiełuszki — model nieustalony, wygląd: listwy drewnopodobne + czarne odlewane boki, kosz czarny walec. **Wysokości latarni Andersa/Tysiąclecia/Sokólska: nadal UNVERIFIED** (Al. Tysiąclecia: słupy aluminiowe podatne, oprawy sodowe — projekt 2015). Zdjęć z PR nie używać jako potwierdzenia obecności obiektów.

M50-FIX dopisany do `docs/owner/MISTRAL-FIXES-8.md`.

## PR #47 — M55 `research/mistral-p5-audio-3` — PRZYJĄĆ (głównie wynik negatywny; drobny M55-FIX)

Formalnie: diff tylko `research/mistral/p5-audio-3/` (6 plików tekstowych); **audio nie trafiło do gita** (`.gitignore`: `files/`, `*.zip`); ZIP rozpakowany w `research/_incoming/mistral-p5-audio-3/files/` (13 plików, 74,8 MB). Licencje: 8× Freesound CC0/CC BY 4.0, 5× Commons CC BY-SA 2.5/3.0 — **zero NC/Sampling+**. Duplikaty z `research/gptpro/9-audio-refs` i `p5-audio-refs-2`: 0/8 ID Freesound (grep manifestów origin/main).
Próba: seed `s17-M55-review-1113` → M55-004, 005, 007, 011 (4/13 = 31 %) + 001, 002, 009 (licencja/opis) + **długości wszystkich 13 plików `ffprobe`**.

| id | Sprawdzenie | Wynik |
|---|---|---|
| wszystkie 13 | `ffprobe`: długości zgodne z manifestem (±0,1 s, np. 1320,7 / 1428,0 / 188,8 / 71,1 s); sample rate zgodne. Podglądy MP3 mają ~175–190 kb/s (README: „128 kbps”) | OK (drobna nieścisłość bitrate) |
| 004 MaxxForce 475829 | WebFetch: CC0, otohoanglong, „International Maxxforce Engine Sound”, 9,705 s; odmiana silnika niepodana | OK, UNVERIFIED słusznie |
| 005/007 Volvo 8900 (valimaa) | WebFetch 659587: CC0, „Driveby sound of a relatively modern Volvo bus”, Tampere, telefon OnePlus, 5,098 s, 48 kHz/16 bit | OK (to autobus Volvo, silnik niepodany — nie spełnia kat. 4) |
| 011 Orion VII Hybrid | Commons API: CC BY-SA 2.5, Michael P., 3 567 926 B = plik w ZIP; opis „Recording of an Orion VII Hybrid-Electric Bus… Q10” | OK jako analog; **nie jest retarderem** |
| 001 kyles 637922 | WebFetch: CC0, tytuł „truck mack peterbilt … idle nearby air release and pass rev … slow and stop”; brak słowa engine/jake brake | OK, UNVERIFIED słusznie |
| 002 Volvo B8R 846043 | WebFetch: CC0, ElevatorFan2020, „THACO Bluesky 120S \| Volvo B8R”, 22:00,7; skrzyni nie nazwano | OK, UNVERIFIED słusznie |
| 009 Beeld en Geluid | Commons API: CC BY-SA 3.0, „afremmen, stoppen, stationair en motor afzetten (interieur)” — bez hamulca silnikowego | OK, UNVERIFIED |

Wyniki negatywne (retarder, hamulec silnikowy pojedynczego pojazdu, AMT, R6 12–13 l z modelem silnika, osuszacz) mają w `sources.md` listę zapytań per źródło (Freesound, Commons 913 tytułów, OGA, Sonniss ~34 tys. plików, IA, Openverse — limit wyczerpany). Samokontrola (4/13, link+licencja+długość) — zgodna z moją. **Najrzetelniejszy PR tej rundy**, ale wartość praktyczna niska: 12/13 UNVERIFIED.

**Fakty dla audio (agent `audio`):** w wolnych źródłach brak nagrań retardera, jake brake pojedynczego pojazdu, AMT z nazwaną skrzynią, R6 12–13 l z nazwanym silnikiem i regeneracji osuszacza — **trzeci niezależny negatyw (G9, P5, M55): te warstwy syntezować / ElevenLabs (D-reference-elevenlabs) albo nagrać samodzielnie**. Użyteczne referencje: M55-002 (22 min jazdy autokarem Volvo B8R z kabiny, CC0 — zmiany biegów, prawdopodobnie I-Shift, UNVERIFIED), M55-001 (spust powietrza + przejazd Mack/Peterbilt, CC0), M55-003 (whine przekładni autobusu, CC BY 4.0 — wymaga atrybucji). Pliki CC BY-SA (Commons, 5 szt.) — **tylko referencja**, nie wkładać do buildu (ShareAlike). Oryginały Freesound: `download_list.csv` (8 poz., wymaga konta).

M55-FIX dopisany do `docs/owner/MISTRAL-FIXES-8.md`.

## PR #48 — M52 `research/mistral-p2-surfaces-2` — PRZYJĄĆ CZĘŚCIOWO; zadanie 1 (wymiary P-*) ODRZUCIĆ (M52-FIX)

Formalnie: diff tylko `research/mistral/p2-surfaces-2/` (4 pliki; **brak `.gitignore`**, ale zdjęć w gicie nie ma). ZIP rozpakowany w `research/_incoming/mistral-p2-surfaces-2/` (24 Jaroszówka, 30 trasa, 23 przejścia, 3 Rynek). KartaView CC BY-SA 4.0 jako referencja — poprawnie.
Próba: seed `s17-M52-review-1113` nie użyty do losowania wierszy — sprawdzono **całe zadanie 1** na źródle (Dz.U. 2019/2311 cz. 2 pobrana, strony 538/540/541 wyrenderowane PyMuPDF i obejrzane), 4 kadry Jaroszówki (jar-01/07/12/20), zadanie 6 (PDF BIP 103311 pobrany, `pdftotext`).

| Zakres | Sprawdzenie | Wynik |
|---|---|---|
| P-3a (rys. 2.2.1.8, s. 538) | rysunek: linie 0,12 / odstęp 0,12 / 0,12, linia przerywana **kreska 4,00 m, przerwa 2,00 m** (etykiety wymiarowe), podpis „**0,20 m²/mb**” | Mistral: „odstęp osi 0,20 m (podpis)” i „kreska ~2,0–2,4 / przerwa ~0,56–0,62 ESTIMATED” — **FAŁSZ** (podpis to zużycie farby m²/mb; wymiary 4,00/2,00 są na rysunku) |
| P-4 (s. 540) | 0,12 / 0,12 / 0,12; podpis „0,24 m²/mb” | „odstęp osi 0,24 (podpis)” — wartość przypadkiem zgodna, uzasadnienie błędne |
| P-5 (s. 540) | 0,12 / 0,12 / 0,12; **kreska 4,00, przerwa 2,00**; „0,32 m²/mb” | „odstęp 0,2 m (podpis)”, „kreska ~1,77 / przerwa ~0,91 ESTIMATED” — **FAŁSZ** |
| P-6 (s. 541) | 0,12; **kreska 4,00, przerwa 2,00**; „0,08 m²/mb” | przerwa 2,00 OK; „kreska ~4,00 ESTIMATED” (a jest etykieta); „podpis 0,08 — semantyka UNVERIFIED” — to m²/mb |
| P-3b, P-12 „0,5”, P-13 „0,2825”, P-14 „0,375” | ten sam typ podpisu (m²/mb lub m² na element) | interpretacje jako wymiary **niewiarygodne** — do ponownego odczytu |
| P-2a/b 0,12/0,24, P-21a/b (tabela 5.3), P-11 1,8/3,0 m | wartości z etykiet/tekstu | prawdopodobnie OK (nie każdą sprawdziłem) |
| Jaroszówka 24 kadry | obejrzane 4: wszystkie z **estakady Andersa** (bariery mostowe, kominy EC, latarnie dwuramienne) — ani ronda, ani chodników/krawężników | „kafel startowy z poziomu jezdni” — tylko estakada; ten sam błąd co P1B |
| Kolor jezdni (mediana RGB dolnych 45 % kadru) | w dolnej części kadrów jest maska auta/deska rozdzielcza, różne kamery i balans bieli | metoda bez wartości — odrzucić RGB |
| Zad. 3/6 wytyczne ZDM 2025 (BIP 103311) | PDF: nagłówek „13 LIPCA 2018 R./2025 R.”; „1 rząd płytek gładkich a następnie 2 rzędy płytek profilowanych (o powierzchni guzowatej)”; „Na wyspie dzielącej… przejazd rowerowy” | OK |
| Zad. 5 Rynek | granit płyty + kostka (Tofiluk 2015, DOI) — nie sprawdzałem; wymiary UNVERIFIED uczciwie | przyjąć warunkowo |

Ocena: zadanie 1 — **systematyczny błąd metody** („programowy odczyt glifów” zamiast obejrzenia rysunku: podpis „m²/mb” wzięty za wymiar, pominięte etykiety 4,00/2,00), samokontrola 24/116 tego nie wykryła. Zadania 3 (wymogi) i 6 — dobre. Zadanie 2/4 — kadry tylko z estakady, kolory bezużyteczne.

**Fakty dla agentów (linie, nawierzchnie):** P-3a/P-5/P-6: **kreska 4,00 m, przerwa 2,00 m** (rys. 2.2.1.8/11/12, s. 538/540/541); szerokość linii 0,12 m; linie podwójne P-3a/P-4/P-5: 0,12 + odstęp 0,12 + 0,12 (osie co 0,24 m); zużycie farby P-3a 0,20, P-4 0,24, P-5 0,32, P-6 0,08 m²/mb. P-11 przejazd dla rowerzystów 1,8/3,0 m. Płytki dotykowe przy zejściach: 1 rząd gładkich + 2 rzędy guzowatych (wytyczne ZDM 2025). Wytyczne ZDM aktualne: BIP 103311 „2018/2025”. Brak czerwonego asfaltu w kadrach trasy — **niepotwierdzone** (metoda słaba), nie zmieniać obecnego stanu.

M52-FIX dopisany do `docs/owner/MISTRAL-FIXES-8.md`.

## Podsumowanie

| PR | Zadanie | Werdykt | Główne błędy |
|---|---|---|---|
| #46 | M49 bramy Dojlidy | częściowo (po FIX) | G10 PZZ = parking_aisle w pustym placu; RS16 kierunek odwrotny do PFU; brama EC bez źródła |
| #44 | M54 ograniczenia | przyjąć (po drobnym FIX) | opisy 2 kadrów błędne; zdjęcia 2048 px |
| #45 | M50 meble | dokumenty tak, zdjęcia nie | VERIFIED_WIZJA bez oglądania (hydranty 0/3) |
| #47 | M55 audio | przyjąć (drobny FIX) | bitrate; wynik praktycznie negatywny |
| #48 | M52 nawierzchnie | częściowo; zad. 1 odrzucić | podpis m²/mb wzięty za wymiar; kadry tylko z estakady |

Wzorzec rundy r8 potwierdzony: Mistral rzetelnie obsługuje API/teksty/licencje, ale **nie ogląda obrazów** (zdjęcia, rysunki) i deklaruje wizję, której nie było. Przy kolejnych zleceniach wymagać w samokontroli zdania „co widać” per obraz.

KONIEC PRZEGLĄDU (wszystkie 5 PR). NASTĘPNY KROK dla lidera: przekazać M49/M54/M50/M55/M52-FIX Mistralowi; niczego nie scalono.

## Ponowny przegląd po M52-FIX (s17)

PR #48, commit `2e1ed8c`; `gh pr diff --name-only` = 5 plików, wszystkie w `research/mistral/p2-surfaces-2/` (OK). Sprawdzone na źródle: Dz.U. 2019/2311 zał. 2 wyrenderowane PyMuPDF 150 dpi i obejrzane strony 539 (P-3b), 540 (P-4/P-5), 571 (P-12), 572 (P-13), 573 (P-14); kadry jar-03/10/16/24 obejrzane; seed samokontroli odtworzony w `python -I`. Mistral sam przyznaje w komentarzu PR, że w sesji FIX **nie renderował PDF i nie oglądał rysunków ani kadrów** (oparł się na tym przeglądzie + arytmetyce).

| Punkt M52-FIX | Stan | Uwagi |
|---|---|---|
| (1) P-3a/P-5/P-6 kreska 4,00 / przerwa 2,00, linia 0,12, podwójne 0,12+0,12+0,12 | **zrobione** | M52-003…015 SOURCED, ESTIMATED z pikseli usunięte; osobna kolumna „zużycie m²/mb” w README |
| (1) kolumna zużycia farby | **zrobione** | 0,20/0,24/0,32/0,08 m²/mb poprawnie jako zużycie. Wątpliwość „P-5 0,32 vs 0,16” rozstrzygnięta oględziną s. 540: rysunek pokazuje **dwie** linie P-5 (obie krawędzie pasa zmiennego) → 2×0,16 = 0,32; Mistral zostawił otwarte |
| (1) „obejrzyj każdy rysunek, usuń szacunki tam, gdzie jest etykieta” | **nie** | rysunków nie oglądano; patrz P-3b i P-13 niżej |
| (2) P-3b | **częściowo — błąd** | „0,18” = m²/mb poprawnie, ale kreska/przerwa wpisane UNVERIFIED, a rys. 2.2.1.9 ma etykiety **kreska 1,00 m / przerwa 1,00 m** (pominięte; brak wiersza) |
| (2) P-12 | zrobione (proweniencja zła) | szerokość 0,50 m poprawna, ale to **etykieta „0,5”** na rys. 4.2.3.1, nie „arytmetyka podpisu”; tramwaj ≥ 1,5 m OK |
| (2) P-13 | **błąd** | etykiety czytelne: **podstawa trójkąta 0,50**, odstęp 0,25, **wysokość 0,70**; Mistral: „0,50 niepewny, arytmetyka wskazuje 0,75” — hipoteza 0,75 FAŁSZYWA (README l. 110, M52-019). „0,2625” (nie 0,2825) poprawnie |
| (2) P-14 | zrobione (proweniencja zła) | 0,75 długość / 0,25 odstęp / **0,5 głębokość — etykieta**, nie arytmetyka; odległości 2,0/0,5/8,0/2,0/1,5 m z tekstu OK |
| (3) Jaroszówka = estakada Andersa, ring negatywnie M52-117 | **zrobione** | jar-03/10/16/24: bariery mostowe estakady, kominy/zbiornik EC, latarnie dwuramienne; jar-24 = koniec estakady z ostrzegawczym znakiem włączania się pasa — opis zgodny. M52-117 BRAK KADRÓW (Panoramax bbox 0, KartaView 24/24 estakada) — przyjąć jako negatyw (nie weryfikowałem API) |
| (4) kolor_srgb | **zrobione** | wartości usunięte z M52-029…105 i 116; zostały tylko Rynek 106–108 (inna metoda, środek kadru). Zad. 4 przez obejrzenie kadrów **niewykonane** — jawnie UNVERIFIED (akceptowalne) |
| (5) `.gitignore` | **zrobione** | `files/`, `*.zip` |
| (6) samokontrola 20 % z seedem | **zrobione** | seed 20261113, `random.Random(20261113).sample(ids,24)` odtworzone 1:1 (24/117); kadry jawnie „nie obejrzano w sesji FIX” — uczciwie, ale samokontrola znów nie wykryła P-3b/P-13 |

**Werdykt: NADAL DO POPRAWY** (drobne, 1 runda): (a) P-3b dodać wiersz kreska **1,00** / przerwa **1,00** m (rys. 2.2.1.9, s. 539) SOURCED; (b) P-13 podstawa **0,50**, wysokość **0,70**, odstęp 0,25 (rys. 4.2.4.1, s. 572) SOURCED — usunąć hipotezę 0,75; (c) P-12 0,5 i P-14 głębokość 0,5 — proweniencja „etykieta”, nie arytmetyka; (d) P-5 0,32 = dwie linie na rysunku — zamknąć wątpliwość. Alternatywa dla lidera: scalić z erratą (a)–(d) wpisaną przez lidera — reszta paczki (zad. 1 linie, 2 negatyw, 3/6 wymogi, 4 UNVERIFIED) jest już poprawna. Nie scalono, nie skomentowano.

**Fakty dla agentów (uzupełnienie):** P-3b kreska 1,00 / przerwa 1,00 m; P-12 szerokość 0,50 m; P-13 trójkąt podstawa 0,50 × wysokość 0,70 m, odstęp 0,25 m; P-14 prostokąt 0,75 × 0,50 m, odstęp 0,25 m (Dz.U. 2019/2311 zał. 2, s. 539/571–573).
