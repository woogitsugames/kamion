# Przegląd PR #41 (Mistral M44/P4 — przepisy wyglądu ciężarówki i widoku z kabiny) — s17, 2026-11-13

**Status:** GOTOWE (NASTĘPNY KROK dla lidera: decyzja o scaleniu PR #41 + poprawki z §4; nic nie scalono, nic nie skomentowano, nic nie zacommitowano).

## Werdykt: **CZĘŚCIOWO** (przyjęta jako źródło dla modelu ciężarówki; 2 tezy odrzucone, 3 punkty kontrolne nadal otwarte)

Mistral poprawnie zaktualizował R48 do serii 07 i uzasadnił wersje R46/R58/R73/R104 załącznikiem II GSR2 — zgodnie z najnowszą konsolidacją 2019/2144 (02.08.2026). Sprawdziłem cytaty w źródłach pierwotnych: 32/35 potwierdzone. Odrzucone: (a) „ostatnia nowelizacja merytoryczna 96/53/WE to 2015/719” — **fałsz** (są jeszcze 2019/984 i 2019/1242); (b) P4-134 „22,5 t/oś przy 38 t” — cytatu nie ma w tekście jednolitym 96/53/WE.

## 0. Formalnie
- PR #41 OPEN, gałąź `research/mistral-p4-truck-regulations` (baza 26f62c3dd), 3 commity. `gh pr diff --name-only`: tylko 4 pliki w `research/mistral/p4-truck-regulations/` (README, manifest.csv 171 wierszy, sources.md, audit_20_percent.json) — **nic poza katalogiem**. Brak binariów: wszystkie PDF tylko jako linki. Zadanie dopuszcza pliki ≤ 5 MB, a Mistral tłumaczy ich brak ograniczeniem konektora — to akceptowalne.
- Statusy: SOURCED 170, UNVERIFIED 1 (P4-157 rysunki tablic wyróżniających). Licencje: decyzja 2011/833/UE (EUR-Lex), © UNECE (fragmenty z atrybucją), Dz.U. (dokument urzędowy, art. 4 pr. aut.) — OK. Deklarowana samokontrola: seed 20261113, 43/171 = 25 %, „pełna weryfikacja 171/171 — 0 niezgodności”. Ta ostatnia deklaracja jest **zawyżona** (patrz P4-134).
- Uwaga metodyczna: EUR-Lex (`legal-content`) i unece.org odpowiadają HTTP 202/403. Źródła pierwotne pobrałem przez Cellar Urzędu Publikacji (`publications.europa.eu/resource/celex/…` + SPARQL), API ELI Sejmu (`api.sejm.gov.pl/eli`), Wayback (`id_`) oraz z plików urzędowych GPT P4 w main. Pobrane do scratchpada sesji, nie do gita.

## 1. Próba (seed 4417, Python `random.Random(4417).sample`, 35/171 = 20,5 %)
Wylosowane wiersze: P4-008, 019, 025, 030, 035, 036, 038, 046, 047, 058, 072, 073, 076, 078, 082, 089, 090, 094, 100, 107, 111, 112, 121, 130, 134, 139, 143, 148, 152, 155, 156, 164, 168, 169, 171.
Metoda: segmenty cytatu znormalizowane (małe litery, tylko [a-z0-9], ł→l; dla PL OJ — usunięte znaki diakrytyczne, bo pdftotext je gubi) i wyszukane w pełnym tekście źródła. Źródła tekstów:
- R48 07 PL: OJ L 347/2021 (CELEX 42021X1718), 7,4 MB;
- R46 04 PL: OJ L 237/2014 (CELEX 42014X0808(02)), 7,6 MB;
- R58 03: OJ EN, plik GPT P4-003;
- R73 01: OJ EN, plik GPT P4-004;
- R104: OJ EN P4-005 + UNECE Rev.2/Add.103/Rev.1 z Wayback;
- R70 01: UNECE z Wayback;
- 96/53/WE: tekst skonsolidowany PL 14.08.2019 (P4-006);
- WT: Dz.U. 2024 poz. 502 (P4-007);
- rozporządzenie o rejestracji: Dz.U. 2024 poz. 1709 (P4-008);
- GSR2: tekst skonsolidowany EN z 02.08.2026.

Wyniki:
- **Potwierdzone: 32.**
  - 28 automatycznie.
  - P4-030 i P4-058: ręcznie — układ tabeli R48 (komórki „Liczba Dwa”, „Żółta samochodowa” rozbite).
  - P4-076: R104 4.1.2 — „TOP” co 0,5 m tylko dla materiału **nie-omnirotacyjnego**; README pomija ten warunek.
  - P4-008: B13 = R46 w zał. I GSR2, sprawdzone w wersji EN.
- **Nie znaleziono: 1.** P4-134: „nacisk na każdą oś potrójną … nie przekracza 22,5 tony”. W t.j. 96/53/WE pkt 3.3.2 jest tylko „1,3 < d ≤ 1,4 — 24 tony” → **wartość 22,5 t odrzucona**.
- **Niesprawdzone: 2.** P4-148 (561/2006: Cellar HTTP 300, EUR-Lex 202) i P4-168 (konwencja wiedeńska, weryfikacja negatywna — nie pobierano).
- **Sprzeczności z GPT P4: 0 w liczbach R48/R73/R70/WT.** Różnice wynikają z serii albo doprecyzowania (§3).

## 2. Siedem punktów kontrolnych (§P4/§7 przeglądu pack-02)

| # | Punkt | GPT P4 | Mistral M44 | Źródło pierwotne (sprawdzone 2026-11-13) | Rozstrzygnięcie |
|---|---|---|---|---|---|
| 1 | Seria R48 | Rev.12 = seria 06 (2014). Sugestia: Rev.13/07, propozycje 08 | Seria 07 + Suplement 1, OJ L 347 z 30.9.2021 | GSR2 zał. II (konsolidacja 02.08.2026): „48 … **07 series of amendments** OJ L 347, 30.9.2021”. Cellar: brak nowszej publikacji R48 w OJ po 2021/1718. W R48 07 PL potwierdzone: 6.21.1.2.1 a) „N3 (z wyjątkiem podwozi z kabiną, pojazdów niekompletnych i ciągników siodłowych…)” oraz kąty obrysowych „80° na zewnątrz; 5° powyżej i 20° poniżej” | **Mistral rację ma.** Seria 07 obowiązuje w UE. Wyjątek konturu dla ciągnika i kąty bez zmian względem 06. Seria 08 na forum UNECE — UNVERIFIED, nieistotna dla UE |
| 2 | Seria R46 i CMS | Seria 04 (Rev.5). Sugestia: serie 05–07 i CMS | Seria 04 + Suplement 1 (OJ L 237/2014). CMS pominięte | GSR2 zał. II (02.08.2026): „46 … **04 series** OJ L 237, 8.8.2014”. Brak nowszej publikacji R46 w OJ. R46 04 pkt 2.1 i 2.1.2 definiuje „urządzenie typu kamera-monitor” jako urządzenie widzenia pośredniego. Przy klasie VI dla N3: „lusterka przedniego lub urządzenia typu kamera-monitor” | **Seria 04 potwierdzona dla UE.** Teza o seriach 05–07: UNVERIFIED (brak w OJ i GSR2). CMS dopuszczone jako typ urządzenia. **Czy CMS może zastąpić klasy II/IV — OTWARTE** (żadna paczka tego nie wykazała). Gra: lusterka |
| 3 | R58 seria 03 i punkt wyłączenia ciągnika | Seria 03; w manifeście pkt 1.2.1 (przegląd: 1.2.2) | Seria 03; P4-106 pkt 1.2.1 | GSR2 (02.08.2026): „58 … **03 series** OJ L 49, 20.2.2019”. OJ EN: „1.2. This Regulation does not apply to: 1.2.1. 1.2.2. Tractive units for articulated vehicles” — numeracja niejednoznaczna po ekstrakcji | **Seria 03 aktualna; wyłączenie ciągnika potwierdzone.** Numer punktu (1.2.1 vs 1.2.2) zostaje niejednoznaczny — bez wpływu na model |
| 4 | Status 96/53/WE i „rozporządzenie (UE) 2024/5450” | Twierdzi, że 2024/5450 zastąpi dyrektywę | Pomija 2024/5450. „Ostatnia nowelizacja merytoryczna 2015/719” | Cellar SPARQL `amends 31996L0053`: 2002/7, 2015/719, **2019/984**, **2019/1242**; ostatnia konsolidacja 01996L0053-**20190814**. Brak późniejszych zmian. `celex/32024R5450` → **HTTP 404** (`32024R3110` istnieje, `32024R3200` → 404, czyli numeracja 2024 kończy się poniżej 3200). Rozporządzenie 2019/1242 dodało do pkt 2.2: masy zespołu + do 2 t dla pojazdów na paliwo alternatywne/bezemisyjnych | **„2024/5450” nie istnieje — teza GPT odrzucona. Teza Mistrala „ostatnia = 2015/719” odrzucona.** Dla naszego zestawu (diesel, nieintermodalny) dalej **40 t**. 96/53/WE obowiązuje, rewizja nieprzyjęta (stan Cellar 2026-11-13) |
| 5 | Tablica 520×114 mm | UNVERIFIED (rysunek) | UNVERIFIED (zał. 12, rysunek 1). Akt opisany jako „t.j.” i „rejestracji i zabezpieczeń” | ELI: Dz.U. 2024 poz. 1709 to **oryginał** z 8.11.2024 („rejestracji i oznaczania pojazdów, wymagań dla tablic…”), nie tekst jednolity. W mocy. **Zmieniony** Dz.U. 2025 poz. 939 i 2026 poz. 891 — Mistral tego nie sprawdził | **Nadal OTWARTE** (obie paczki). Miejsce na tablicę 520×120 (WT zał. 5) — SOURCED. Do sprawdzenia, czy zmiany 2025/939 i 2026/891 ruszają zał. 12 |
| 6 | Miejsce tachografu | UNVERIFIED | Pominięte („poza zakresem”). Podany tylko zakres obowiązku z 561/2006 | Nie sprawdzono (2016/799 > 5 MB; EUR-Lex 202) | **OTWARTE.** Dla modelu: tachograf w gnieździe DIN deski rozdzielczej — ESTIMATED (praktyka), nie przepis |
| 7 | Aktualny t.j. WT §12/§42/zał. 10 | t.j. Dz.U. 2024 poz. 502 | t.j. Dz.U. 2024 poz. 502 („akt obowiązuje”) | ELI: 2024/502 IN_FORCE, nadal najnowszy t.j. Zmiany po t.j.: Dz.U. 2024 poz. 983 (przesunięcie terminu w rozporządzeniu zmieniającym z 2019, nauka jazdy) i 2024 poz. 1417 (§1 ust. 1 pkt 5). Żadna nie dotyka §12, §42 ani zał. 10 | **Potwierdzone:** §12, §42 i zał. 10 w brzmieniu z t.j. 2024/502 są aktualne |

## 3. Rozbieżności GPT P4 ↔ Mistral M44 (poza tabelą)
- **Lusterko klasy V (N3):** GPT podaje 1+1. Mistral podaje 1 obowiązkowe po stronie pasażera + opcjonalne po stronie kierowcy. Tabela R46 04 15.2.1.1.2 (wiersze N2 > 7,5 t / N3) potwierdza wersję **Mistrala**.
- **Klasa VI:** obowiązkowa dla N3 z wysuniętym do przodu układem kierowniczym (kabina nad silnikiem — nasz przypadek). Montaż ≥ 2 m. Możliwy zamiennik: kamera-monitor albo system wspomagający (wykrycie obiektu 50 cm × Ø 30 cm).
- **R58 dla naczepy:** GPT opisuje odległość osłony od tyłu (≤ 200 mm przed próbą). Mistral opisuje prześwit (≤ 450 mm przy zawieszeniu pneumatycznym, ≤ 500 mm przy innym). OJ potwierdza oba parametry (Część III, pkt 25.1, i Część II, pkt 16.2) — to się uzupełnia, nie wyklucza.
- **R104:** Mistral pisze „seria poprawek 01”. Źródło to Revision 1 (Rev.2/Add.103/Rev.1, 2010), a GSR2 podaje „Original version of the Regulation”. Błąd etykiety, bez wpływu na wartości.
- **96/53 oś napędowa:** dla pojazdów z pkt 2.2.2 właściwy jest pkt **3.4.1**, nie 3.4.2. Wartość 11,5 t ta sama.
- **README Mistrala:** podaje konsolidację GSR2 07.07.2024, a istnieją 2025-09-01, 2026-01-07 i 2026-08-02. Dla R46/48/58/73/104 treść zał. II jest bez zmian (sprawdzone).

## 4. Poprawki do PR #41 przed scaleniem (lider albo Mistral w kolejnej rundzie)
1. Usunąć wartość 22,5 t z P4-134 i z README §5.
2. README §5: zamiast „ostatnia nowelizacja 2015/719” wpisać „zmiany: 2002/7, 2015/719, 2019/984, 2019/1242 (+ do 2 t dla zespołów na paliwo alternatywne/ZEV); konsolidacja 14.08.2019”.
3. Opis Dz.U. 2024 poz. 1709: „oryginał, zm. Dz.U. 2025 poz. 939 i 2026 poz. 891”.
4. Etykieta R104 („wersja pierwotna, Rev.1”). Warunek „nie-omnirotacyjny” przy znaku TOP.
5. Otwarte do paczki 03 albo dla Claude: CMS zamiast klas II/IV, rysunek tablicy 520×114, miejsce tachografu, zakres zmian 2025/939 i 2026/891.

## 5. Tabela wymagań dla modelu ciężarówki (truck-artist / docs/07)
Pewność: **P** = potwierdzone w źródle pierwotnym w tym przeglądzie albo w s16; **S** = SOURCED w paczce, nie sprawdzane wprost; **O** = otwarte / ESTIMATED.

| Obszar | Ciągnik N3 4×2 (siodłowy, kabina nad silnikiem) | Naczepa O4 firanka 13,6 m, 3 osie | Pewność |
|---|---|---|---|
| Kierunkowskazy przód/tył | 2 przód (kat. 1/1a/1b) + 2 tył; wys. 350–1500 mm (wyj. 2100); ≤ 400 mm od krawędzi; odstęp wewn. ≥ 600 mm; 90 ± 30/min | 2 tył (+2 dodatkowe O2–O4 wg Mistrala) | P (liczby 2+2), S (dodatkowe) |
| Kierunkowskazy boczne | kat. 6 (lub 5); 500–1500 mm (wyj. 2300) | 3× kat. 5 na stronę, chyba że ≥ 3 migające obrysowe boczne | S |
| Stop | 2× S1/S2; 350–1500 mm; S3 nieobowiązkowe dla N3 | 2× S1/S2 | P |
| Pozycyjne przód | 2 białe, 250–1500 mm | 2 białe (szer. > 1600), ≤ 150 mm od krawędzi | P/S |
| Pozycyjne tył | 2 czerwone, 350–1500 mm | 2 czerwone, 350–1500 mm | P |
| Obrysowe górne (> 2,10 m) | 2 białe przód — nie niżej niż górna krawędź szyby; 2 czerwone tył; ≤ 400 mm od krawędzi; kąty 80° / 5° / 20° | 2 przód + 2 tył, na możliwie największej wysokości | P |
| Obrysowe boczne SM1 (> 6 m) | obowiązkowe; żółte; co ≤ 3 m; pierwsze ≤ 3 m od przodu, ostatnie ≤ 1 m od tyłu | jw. | P (barwa, zakres), S (odstępy) |
| Odblaski tył | 2 nietrójkątne IA/IB; **trójkątne zakazane** | 2 **trójkątne** IIIA/IIIB (wierzchołek w górę) | P |
| Odblaski przód | opcjonalne | 2 białe IA/IB, 250–900 mm, ≤ 150 mm od krawędzi | P |
| Odblaski boczne | obowiązkowe (> 6 m; WT §12 ust. 1 pkt 11 wymienia ciągnik siodłowy), żółte, co ≤ 3 m | obowiązkowe | P |
| Cofania | wg R48 (GPT: obowiązkowe) | 2 (naczepa > 6 m) | S |
| Przeciwmgłowe tył | 1–2 | 1–2 | P (s16) |
| Oznakowanie konturowe R104 kl. C | **BRAK obowiązku** (R48 07 6.21.1.2.1 a) | tył pełny: ≥ 70 % szerokości, ≤ 600 mm od krańców, dolne 250–1500 mm, górne ≤ 400 mm od górnej krawędzi, elementy ≥ 60 mm, przerwy ≤ 50 %, > 200 mm od stopu; bok częściowy; tylne tablice R70 mogą liczyć się jako kontur (6.21.7.4); materiał żółty/biały/czerwony, „TOP” | P (zakres, 70 %), S (pozostałe) |
| Tablice wyróżniające (R70 / WT §42 + zał. 10) | **BRAK** (WT §42 wyłącza ciągnik siodłowy; R70 1.2 wyłącza „tractors for semi-trailers”) | **OBOWIĄZKOWE**: klasa 2, żółte odblaskowe tło + czerwone fluorescencyjne obrzeże; dolna krawędź ≥ 250 mm, górna ≤ 2100 mm; ≤ 400 mm od obrysu; ±5° od pionu; 1, 2 lub 4 sztuki; szer. 200 +30/−5 mm, łączna dł. 1130–2300 mm (R70 zał. 12); dokładne rysunki WT — O | P (obowiązek, wysokości), S (wymiary R70), O (rysunek WT) |
| Lusterka (R46 04) | kl. II 1+1; kl. IV 1+1; kl. V po stronie pasażera obowiązkowe, po stronie kierowcy opcjonalne (montaż ≥ 2 m); kl. VI przednie 1 (≥ 2 m); kl. I opcjonalne; kl. III niedozwolone; montaż ≤ 55°; wystawanie ≤ 250 mm poza obrys, gdy dolna krawędź < 2 m | brak (R46 dotyczy pojazdów silnikowych) | P (tabela N3), S (55°, 250 mm) |
| Pola widzenia (kamera kabiny / lusterka w grze) | kl. II: pas 5 m od 30 m za oczami kierowcy + 1 m od 4 m; kl. IV: 15 m na odcinku 10–25 m + 4,5 m od 1,5 m; kl. V: bok kabiny, 2 m na zewnątrz, 1,75 m za i 1 m przed oczami (3 m przy montażu ≥ 2,4 m); kl. VI: 2000 mm przed przodem, 2000 mm na zewnątrz po stronie pasażera, łuk R 2000 mm | — | P (IV, V, VI), S (II) |
| CMS (kamery zamiast lusterek) | dopuszczone jako typ urządzenia (R46 04 pkt 2.1.2); zamiana klas II/IV niepotwierdzona → **w grze lusterka** | — | O |
| Osłona tylna R58 | **BRAK** (ciągniki siodłowe wyłączone) | RUPD: poprzeczka ≥ 120 mm wysokości; prześwit ≤ 450 mm (zawieszenie pneumatyczne, R58 pkt 16.2/25.1); poziomo ≤ 200 mm od tyłu pojazdu przed próbą (s16, P4-093 GPT) | P |
| Osłony boczne R73 | **BRAK** (R73 2.1.4 wyłącza ciągniki siodłowe) | dolna krawędź ≤ 550 mm; przednia ≤ 250 mm za nogami podporowymi; tylna ≤ 300 mm przed oponą; listwy co ≤ 300 mm, wysokość ≥ 100 mm; powierzchnia ≤ 150 mm w głąb od obrysu | P |
| Wymiary zestawu (96/53/WE) | zestaw ≤ 16,50 m; szer. ≤ 2,55 m; wys. ≤ 4,00 m; okrąg skrętu R 12,50 / 5,30 m; sworzeń–tył naczepy ≤ 12,00 m; sworzeń–przód naczepy ≤ 2,04 m (promień) | jw. | P |
| Masy | DMC zestawu **40 t** (2 osie + 3 osie; +2 t tylko paliwa alternatywne/ZEV — 2019/1242); oś napędowa 11,5 t; oś pojedyncza nienapędowa 10 t | oś potrójna 24 t (1,3 < d ≤ 1,4 m); **nie** 22,5 t | P |
| Tablice rejestracyjne | przód + tył; miejsce z tyłu 520×120 (lub 340×240) mm; dolna krawędź ≥ 0,30 m, górna ≤ 1,20 m; czarne znaki na białym tle, niebieskie pole UE „PL” | **tylko z tyłu** (§ 33 ust. 1) | P (miejsce, kolory), O (płyta 520×114) |
| Wyposażenie PL (WT §11) | VIN + tabliczka znamionowa (zał. 4), trójkąt, gaśnica w łatwo dostępnym miejscu; apteczka i kliny **nieobowiązkowe** | VIN + tabliczka; kliny nieobowiązkowe | P (s16) / S |
| Tablice nieobowiązkowe | „DŁUGI POJAZD”, tarcza 80 km/h na naczepie, owalny „PL” (ten tylko w ruchu międzynarodowym) — **zwyczaj, nie obowiązek**; dopuszczalne jako dekoracja bez marek | jw. | S |
| Tachograf | obowiązek (561/2006, zespół > 3,5 t); miejsce: gniazdo DIN w desce rozdzielczej | — | S (obowiązek), O (miejsce) |
