# Zadania dla Mistral — runda 8: paczka badawcza 03 (s17, 2026-11-13) — pierwsze 5 zleceń (M44–M48)

Decyzja właściciela (s17): kolejne paczki badawcze robi **Mistral zamiast ChatGPT Pro**. Repo `woogitsugames/kamion`. **5 sesji, każda dostaje jeden blok (skopiuj całość z ramki).** Kolejne bloki (od M49, luki z przeglądu P2–P10) dopisze agent przeglądu w `docs/owner/RESEARCH-PACK-03-MISTRAL.md`.

Kolejność: M44 (przepisy ciężarówki, P4 nieoddane) → M45 (tablice, P7 nieoddane) → M46 (luki zdjęć trasy P1) → M47 (zdjęcia regionu Dojlidy/Krywlany) → M48 (landmarki i wyposażenie regionu Dojlidy/Krywlany).

**Uwaga do r7 (M39–M43, jeszcze nie zlecone):** M39 (nawigacja: numer zjazdu, komunikaty, ETA) robi teraz agent Claude 0168 — **M39 pominąć**. M40–M43 aktualne.

Zasady wspólne są wpisane w każdy blok (Mistral w osobnej sesji nie widzi tego nagłówka).

---

## M44 — przepisy: wygląd i widok z kabiny ciężarówki (dawne G8/P4)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p4-truck-regulations od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin — rzetelność ważniejsza niż tempo; używaj subagentów, jeśli masz.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki z naczepą (Unity), świat Białegostoku 1:1 z OSM i GUGiK, gra komercyjna, budżet 0 zł. Jedna fikcyjna ciężarówka bez marki: ciągnik siodłowy 4×2 + naczepa firanka 13,6 m, 3 osie. Piszesz po polsku.

ZADANIE: Zbierz wymagania przepisów wpływające na wygląd ciężarówki i widok z kabiny, z cytatem (≤ 25 słów) i numerem punktu:
1. Regulamin EKG ONZ R48 — światła: pozycyjne, obrysowe, boczne, kierunkowskazy, odblaski; tabela „element → liczba obowiązkowa → min/max wysokość nad jezdnią → odległość od krawędzi → kolor”, osobno dla ciągnika (N3) i naczepy (O4). Podaj serię poprawek i datę wersji.
2. R104 i R70 — oznakowanie odblaskowe konturowe i tablice tylne (wymiary, położenie, kiedy obowiązkowe).
3. R46 — lusterka klas II, IV, V, VI: pola widzenia z wymiarami (rysunki opisz słowami + liczby).
4. R58 i R73 — osłony przeciwwjazdowe tylne i boczne: wysokości, prześwity, odległości.
5. Dyrektywa 96/53/WE z aktualizacjami (2015/719 i nowsze) — dopuszczalne wymiary i masy dla naszego zestawu 5-osiowego (ciągnik 4×2 + naczepa 3 osie: masa całkowita, długość zespołu, wysokość, szerokość, naciski osi) — z punktem i wartością.
6. PL: tablice rejestracyjne (wymiary, położenie), tabliczki znamionowe, tachograf, kliny pod koła, gaśnica, trójkąt, apteczka — co obowiązkowe dla N3/O4 (rozporządzenie o warunkach technicznych pojazdów, ISAP/ELI — sprawdź, że akt nie jest uchylony).
7. Osobna sekcja: tablice na pojeździe spotykane w PL (tablica „długi pojazd”, znak ograniczenia prędkości na naczepie, tablice odblaskowe ostrzegawcze) — z podstawą prawną albo „zwyczaj, brak obowiązku” ze źródłem.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: UNECE (pełne teksty regulaminów), EUR-Lex, ISAP/ELI, GDDKiA, ITS. Bez marek i logo producentów.
- Nie zmyślaj: każda liczba ma źródło (link + data dostępu + cytat ≤ 25 słów albo strona/tabela). Czego nie da się potwierdzić — UNVERIFIED; szacunki — ESTIMATED z metodą. Źródła wtórne (blogi, fora) NIE potwierdzają przepisu.
- Samokontrola: losuj ≥ 20 % pozycji z jawnym seedem, sprawdź ponownie (link działa, cytat zgadza się z PDF, akt obowiązuje) — wynik w README i audit_20_percent.json.

WYNIK w gałęzi: katalog research/mistral/p4-truck-regulations/ z README.md (cel, metoda, ustalenia wypunktowane, tabele R48, braki, samokontrola), manifest.csv (utf-8; kolumny: id P4-NNN, element, przepis, punkt, wartość, jednostka, kategoria_pojazdu, warunek, cytat, wersja_przepisu, url_źródła, licencja, data_dostępu, status SOURCED/ESTIMATED/UNVERIFIED, uwagi), sources.md, audit_20_percent.json. PDF-y tylko urzędowe i ≤ 5 MB w files/ — w gicie tylko jeśli ≤ 5 MB; większe: tylko link.
NIE ZMIENIAJ niczego poza research/mistral/p4-truck-regulations/.
ODDANIE: commit + push gałęzi co ok. godzinę; na końcu jeden PR do main (nie draft) z raportem po polsku i SUROWYM wyjściem `git diff --stat origin/main` oraz `ls -R research/mistral/p4-truck-regulations | head -50`. NIE scalaj, NIE śledź PR — napisz „M44 gotowe, PR #<numer>” i zakończ.
```

## M45 — tablice kierunkowe: aktualność 2025–2026, epoki portali Andersa, DK19/DK65/S19 (dawne P7)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p7-signs-2 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK, gra komercyjna. Piszesz po polsku. Istniejąca paczka: research/gptpro/3-s8-signs/ (152 pozycje, głównie 2024) — PRZECZYTAJ README i manifest, NIE powtarzaj istniejących tablic.

ZADANIE:
1. Aktualny stan (zdjęcia 2025–2026, z datą) bramownic i tablic w rejonie ronda Putry / Andersa / Al. Tysiąclecia w obu kierunkach. Dla każdej bramownicy panele (lewy górny, lewy dolny, prawy górny, prawy dolny): tekst dokładnie jak na tablicy, numery dróg (E67, 8, 19, 65, 675…), strzałki. Czy treść 2024 jest nadal aktualna.
2. Epoki bramownic Andersa: gra ma tablicę pasa 2 jako jedną (Augustów / Kuźnica / Centrum, stan 2020), zdjęcia 2024 mają „Centrum” osobno. Oś czasu zmian 2019–2026 z rokiem zmiany (decyzja GDDKiA/ZDiT z numerem, jeśli jest; inaczej przedział ze zdjęć).
3. Nowe obszary: DK19 (do 15 km od miasta), DK65 (do Bobrownik), DK8 na północ do Tykocina, S19, S8 do węzła Zawady/Wasilków — tablice E-1, E-2, E-3, E-4, E-14, E-15, przeddrogowskazy, numery węzłów, odległości.
4. Dla każdego nowego znaku: numery_dróg jako JSON (numer / kolor tła zielony|niebieski|żółty / litery), strzałki, grupa_tablic, pole_tablicy — ten sam schemat co research/gptpro/3-s8-signs/manifest.csv (sprawdź nagłówek), by dało się dołączyć do generatora bez konwersji.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła zdjęć: Panoramax (api.panoramax.xyz, CC BY-SA 4.0), KartaView, Wikimedia Commons, Openverse (tylko CC0/BY/BY-SA), BIP/GDDKiA/ZDiT (dokumenty urzędowe — art. 4 pr. aut.). Mapillary wymaga tokenu, którego nie masz — nie zgaduj kluczy, oznacz UNVERIFIED.
- Pobieraj tylko pliki z licencją komercyjną (CC0, CC BY, CC BY-SA, urzędowe); NC/ND/bez licencji — tylko link „tylko referencja, nie pobrano”. CC BY-SA: „share-alike: referencja, nie tekstura”.
- Nie zmyślaj: każdy tekst tablicy odczytany ze zdjęcia z id zdjęcia; nieczytelne — UNVERIFIED. Pozycje WGS84 (6 miejsc) i kierunek patrzenia, jeśli źródło je ma.
- Zdjęcia: JPG ≤ 1600 px dłuższego boku. Obowiązkowe kolumny sezon i pora_dnia.
- Samokontrola 20 % z jawnym seedem — README + audit_20_percent.json.

WYNIK w gałęzi: research/mistral/p7-signs-2/ z README.md, manifest.csv (id P7-NNN; kolumny: lat, lon, kierunek_deg, droga, typ_znaku, tekst_wiersze rozdzielone „|”, numery_dróg, piktogramy, strzałki, grupa_tablic, pole_tablicy, data_zdjęcia, panoramax_id, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json, timeline_andersa.md. ZDJĘCIA NIE DO GITA: dodaj files/ do research/mistral/p7-signs-2/.gitignore, a zdjęcia spakuj w ZIP mistral-p7-signs-2-files.zip i podaj w PR, gdzie leży (np. załącznik do PR / release). 
NIE ZMIENIAJ niczego poza research/mistral/p7-signs-2/.
ODDANIE: commit + push gałęzi co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M45 gotowe, PR #<numer>” i koniec.
```

## M46 — zdjęcia trasy: luki paczki P1 (ulice bez zdjęć, drugi sezon, kierunki)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p1-route-photos-2 od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1. Piszesz po polsku. Paczka P1 (141 kadrów; 50 Panoramax z poziomu kierowcy, 91 Commons z poziomu pieszego) ma luki — uzupełnij TYLKO je (manifest P1, jeśli jest w repo: research/gptpro/p1-route-photos/manifest.csv — nie dubluj kadrów; porównuj po panoramax_id i URL).

LUKI:
1. Zero zdjęć: ul. Stefana Batorego, Brzeska, Buska, Olsztyńska (Białystok, kafel wokół 53,152 N 23,168 E) — ≥ 3 ujęcia każda, oba kierunki.
2. Drugi sezon (dziś tylko jeden): Grodzieńska, Kowieńska, Wołkowyska, Świsłocka, Lidzka (tylko bez liści → szukaj liści/śniegu); wiadukty Maczka nad torami (obie jezdnie), mosty Maczka nad Białą (obie jezdnie), łącznica DK8 węzeł Andersa/Maczka, wiadukt Al. Tysiąclecia nad torami (tylko liście → szukaj zimy/późnej jesieni).
3. Rondo Pamięci Bieżeństwa 1915 r.: 0 kadrów z poziomu kierowcy — po jednym z każdego wlotu i wylotu, z azymutem.
4. Poziom kierowcy dla ulic, które mają tylko kadry pieszego (Commons): Bitwy Białostockiej, Białostoczek, Kombatantów, Motoszko, Bełzy, Wileńska, Sokólska, Sitarska, Skidelska — po ≥ 2 kadry z jezdni z azymutem.
Priorytet: 2023+, dzień, bez rozmycia, bez dużych pojazdów zasłaniających widok; odrzucone (noc, pod słońce) wpisz z powodem.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: Panoramax (api.panoramax.xyz/api/search — bbox, azymut z properties, data captured_at; CC BY-SA 4.0), KartaView (licencja z API), Wikimedia Commons (CC0/BY/BY-SA), Openverse. Mapillary — brak tokenu: nie zgaduj kluczy, UNVERIFIED.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. CC BY-SA: „referencja, nie tekstura”, atrybucja autora.
- Pozycja WGS84 (6 miejsc), kierunek_deg (z EXIF/API albo UNVERIFIED), sezon (liście / bez liści / śnieg) i pora_dnia obowiązkowe. Przypisanie do ulicy: dystans do osi way OSM ≤ 25 m (podaj metodę).
- JPG ≤ 1600 px. Samokontrola 20 % z jawnym seedem (README + audit_20_percent.json).

WYNIK w gałęzi: research/mistral/p1-route-photos-2/ z README.md (tabela pokrycia: ulica × kierunek × ujęcia × sezony; luki pozostałe; 10 najlepszych kadrów do kamer kontrolnych), manifest.csv (id P1B-NNN; kolumny jak P1: ulica, punkt_opis, lat, lon, kierunek_deg, data_zdjęcia, sezon, pora_dnia, panoramax_id, jakość_1_5, odrzucone_powód, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA: files/ w .gitignore katalogu, ZIP mistral-p1-route-photos-2-files.zip — w PR napisz, gdzie leży.
NIE ZMIENIAJ niczego poza research/mistral/p1-route-photos-2/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M46 gotowe, PR #<numer>” i koniec.
```

## M47 — zdjęcia referencyjne regionu Dojlidy / Krywlany (następny region, D60)

```
Repo woogitsugames/kamion. Gałąź research/mistral-p11-dojlidy-photos od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK. Następny region gry: Dojlidy / Krywlany (Białystok, południowo-wschodnia część — dokładne ulice USTAL z OSM; lotnisko Krywlany, strefa przemysłowa Dojlidy, browar Dojlidy, DK65/DK19 i S19 przy mieście). Przeczytaj: research/gptpro/2-next-regions/README.md, docs/11_DECYZJE_WLASCICIELA.md (D60), a jeśli istnieje — Data/Regions/bialystok-dojlidy/region.yaml (granice kafla, ADR 0166 w toku); jeśli nie istnieje, przyjmij kafel 2×2 km zawierający lotnisko Krywlany i strefę Dojlidy i podaj bbox.
Piszesz po polsku.

ZADANIE: zdjęcia z poziomu kierowcy (oko ok. 2,5 m, widok wzdłuż jezdni) dla głównych dróg ciężarówek w kaflu: ≥ 3 ujęcia każdej drogi w obu kierunkach (początek / środek / skrzyżowanie), ≥ 6 dla każdego ronda i wiaduktu (wloty i wyloty), dojazdy do zakładów (bramy, place manewrowe), co najmniej jeden drugi sezon na drogę. Listę dróg zbuduj z OSM (highway primary/secondary/tertiary/trunk + industrial service z hgv) i podaj w README.

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: Panoramax (CC BY-SA 4.0, azymut z API), KartaView, Wikimedia Commons, Openverse (CC0/BY/BY-SA), OSM (ODbL), GUGiK ortofoto (do lokalizacji, nie do ZIP). Mapillary — brak tokenu: UNVERIFIED, nie zgaduj kluczy.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. Bez marek producentów ciężarówek w opisach.
- Pozycja WGS84, kierunek_deg, sezon, pora_dnia obowiązkowe; przypisanie do drogi ≤ 25 m od osi OSM.
- JPG ≤ 1600 px. Samokontrola 20 % z jawnym seedem.

WYNIK w gałęzi: research/mistral/p11-dojlidy-photos/ z README.md (bbox kafla, lista dróg, tabela pokrycia, luki, 15 najlepszych kadrów do kamer kontrolnych z uzasadnieniem — które miejsca gracz rozpozna), manifest.csv (id P11-NNN, kolumny jak paczka P1), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA (files/ w .gitignore, ZIP mistral-p11-dojlidy-photos-files.zip — w PR gdzie leży).
NIE ZMIENIAJ niczego poza research/mistral/p11-dojlidy-photos/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M47 gotowe, PR #<numer>” i koniec.
```

## M48 — landmarki, zabudowa i wyposażenie drogi regionu Dojlidy / Krywlany

```
Repo woogitsugames/kamion. Gałąź research/mistral-p12-dojlidy-landmarks od NAJNOWSZEGO origin/main. Zadanie badawcze na wiele godzin; subagenci mile widziani.

KONTEKST: Kamion — realistyczny mobilny symulator ciężarówki, Białystok 1:1 z OSM i GUGiK. Bramka rozpoznawalności (decyzja D51): gracz z Białegostoku ma rozpoznać miejsce po układzie, znakach i obiektach charakterystycznych. Następny region: Dojlidy / Krywlany (D60; granice kafla — Data/Regions/bialystok-dojlidy/region.yaml, jeśli istnieje, inaczej kafel 2×2 km z lotniskiem Krywlany i strefą Dojlidy — podaj bbox). Przeczytaj research/gptpro/2-next-regions/README.md, research/g5-street-furniture/README.md, research/g7-street-greenery/README.md (format i poziom szczegółu). Piszesz po polsku.

ZADANIE:
1. 25–40 obiektów charakterystycznych widocznych z drogi (lotnisko i hangary Krywlany, browar Dojlidy, kominy, zbiorniki, hale, stacje paliw, kościoły, wieże, mosty, charakterystyczne bloki): dla każdego pozycja WGS84, wysokość (źródło: LoD GUGiK / BDOT10k / dokument / ESTIMATED z metodą), kolor i materiał elewacji, z której drogi i z jakiej odległości widać, ≥ 1 zdjęcie z licencją.
2. Typologia zabudowy przy drogach regionu (hale przemysłowe, domy jednorodzinne, bloki, ogródki działkowe): wysokości, dachy, kolory — z odsetkami policzonymi z próby (podaj metodę i liczność).
3. Wyposażenie drogi: przystanki (wiaty — typ i kolor), latarnie (typ, wysokość), bariery, ekrany akustyczne, ogrodzenia zakładów, drogowskazy E-* na wlotach do regionu — z pozycjami.
4. Generatory ruchu ciężarówek (zakłady, magazyny, bazy, bramy wjazdowe z placami manewrowymi) — lista z pozycją bramy i źródłem (OSM / strona firmy — bez logo).

TWARDE ZASADY:
- ZAKAZ Google Maps / Street View / Earth / 3D Tiles. Źródła: OSM (ODbL), GUGiK (LoD1/LoD2, BDOT10k, ortofoto — dane otwarte), Panoramax, KartaView, Wikimedia Commons, Openverse, BIP Białystok / ZDiT (dokumenty urzędowe). Mapillary — brak tokenu: UNVERIFIED.
- Tylko licencje komercyjne; NC/ND — link „tylko referencja”. Bez logo i znaków towarowych w opisach do odtworzenia (opisz kształt i kolor, nie markę).
- Każda liczba ze źródłem albo UNVERIFIED/ESTIMATED z metodą. JPG ≤ 1600 px. Samokontrola 20 % z jawnym seedem.

WYNIK w gałęzi: research/mistral/p12-dojlidy-landmarks/ z README.md (bbox, ustalenia, tabela landmarków, typologia, luki), manifest.csv (id P12-NNN; kolumny: kategoria landmark|typologia|wyposażenie|generator_ruchu, nazwa_opisowa, lat, lon, wysokość_m, źródło_wysokości, kolor, materiał, widoczny_z_drogi, odległość_m, url_źródła, licencja, autor, data_dostępu, status, uwagi), sources.md, audit_20_percent.json. ZDJĘCIA NIE DO GITA (files/ w .gitignore, ZIP mistral-p12-dojlidy-landmarks-files.zip — w PR gdzie leży).
NIE ZMIENIAJ niczego poza research/mistral/p12-dojlidy-landmarks/.
ODDANIE: commit + push co ok. godzinę; PR do main (nie draft), raport po polsku, SUROWE wyjście `git diff --stat origin/main`. NIE scalaj, NIE śledź PR — „M48 gotowe, PR #<numer>” i koniec.
```
