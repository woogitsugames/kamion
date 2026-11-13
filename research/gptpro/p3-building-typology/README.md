# P3 — building-typology: typy zabudowy Białegostoku dla projektu „Kamion"

**Paczka:** gptpro-p3-building-typology.zip · **Data:** 2026-11-13 · **Autor researchu:** agent Vibe (research dla projektu Kamion)

## 1. Cel

Katalog typów zabudowy widocznych z jezdni w Białymstoku dla realistycznego generatora świata 1:1 (dane OSM + GUGiK). Priorytet: okolice **53,152 N 23,168 E** (osiedla przy Andersa, Wileńskiej, Sokólskiej, Białostoczek, Wysoki Stoczek), potem typy typowe dla całego miasta.

Zbadane typy (każdy ≥ 5 pozycji ze zdjęciem, adresem i współrzędnymi):
**bloki wielkopłytowe (10), domy jednorodzinne (7), drewniane domy podlaskie (10), pawilony handlowe (8), hale i magazyny (7), garaże blaszane (5), stacje paliw (8), budynki usługowe (7)** — łącznie **62 pozycje** (P3-001…P3-062).

## 2. Metoda

1. **Wybór pozycji:** przegląd ~1 800 plików Wikimedia Commons dot. Białegostoku (API MediaWiki, kategorie uliczne i typologiczne); wybór 62 plików z metadanymi GPS (pozycja wg opisu autora — `commons-desc-page`) i datą. Kategoria/opis autora = podstawa statusu SOURCED dla typu obiektu.
2. **Geometria:** dla każdej pozycji: najbliższy budynek OSM (eksport API `map` dla 5 stref; adres, `building:levels`, `height`, `roof:*`, `building:colour` — ODbL) oraz dopasowanie LoD1 GUGiK 2024 (pacza 2061.zip, EPSG:2180 → własna transformacja Gaussa-Krügera; wybór najmniejszego obrysu zawierającego punkt kamery; fallback: najbliższy środek obrysu ≤30 m).
3. **Parametry typów:** dokumentacja systemów wielkiej płyty (Wikipedia, POIIB, Inżynier Budownictwa), dokumenty termomodernizacji (BZP/przetargi TBS), MPZP (BIP). Każda liczba ma źródło w `sources.md`; wartości niepotwierdzalne oznaczono UNVERIFIED, szacunki ESTIMATED z podaną metodą.
4. **Zdjęcia:** pobieranie miniatur z upload.wikimedia.org w standardowych rozmiarach (≤1600 px dłuższego boku, JPG); licencja i autor zapisane per plik. Mapillary pominięto (brak tokenu API — patrz zasada A; w tym środowisku nie było przeglądarki).
5. **Statusy:** SOURCED (typ potwierdzony kategorią/opisem autora lub dokumentem), ESTIMATED (wniosek z OSM/LoD1 z metodą), UNVERIFIED.

## 3. Najważniejsze ustalenia

### Bloki wielkopłytowe — systemy i wymiary
- **OWT-67:** siatka 540×540/540×480/480×270 cm; **kondygnacja 270 cm**; podziemna 250 cm; budynki 5- i 11-kondygnacyjne (Wikipedia „OWT-67", CC BY-SA). W Białymstoku potwierdzony użyciem (budynek biurowy byłego Miastoprojektu; POIIB: „OWT-67": moduł max 5,4×4,8 m, kondygnacja 2,7 m).
- **W-70:** siatka modularna 60×60 cm; rozstawy ścian 240/360/480/600 cm; **wysokość kondygnacji mieszkalnej 280 cm**; płyty stropowe 22 cm; ściany zewn. 27/40 cm; Wk-70: 300 cm i kondygnacja 330 cm (Wikipedia „Technologia wielkopłytowa").
- **Szczeciński (Szczecin-70):** siatka 480×480 i 480×240 cm; rozstaw ścian 480 cm; płyty stropowe 14 cm; ściany zewn. keramzytobeton 40/36 cm; budynki 5- i 11-kondygnacyjne (Wikipedia).
- **Przypisanie systemu do konkretnego osiedla w Białymstoku: brak źródeł** — oznaczono UNVERIFIED per adres; rytm okien 2,4–2,8 m i wysokość kondygnacji 2,7–2,8 m jako ESTIMATED wg siatek systemów.
- **Weryfikacja LoD1 przykładowo:** Sokólska 11 (5 kondygnacji wg OSM): measuredHeight **15,47 m** → 3,09 m/kondygnację — zgodne z wielką płytą (ESTIMATED). Władysława Broniewskiego 6C: 15,65 m / 5 kond. = 3,13 m. Wierzbowa/Broniewskiego 15: 15,41 m / 5 kond.
- **Rozbieżności danych (do ręcznej korekty):** Andersa 38 (Biazet, biurowiec): OSM height=41 m (11 kond.) vs **LoD1 measuredHeight=10,16 m** przy obrysie 217×199 m — obiekt LoD1 najpewniej zlepek segmentów; Aleja Tysiąclecia 10A: OSM building:levels=**13** vs LoD1 mh=14,04 m — dane OSM niespójne (13 kondygnacji ≁ 14 m).

### Termomodernizacja (dowody w BZP/BIP)
- Komunalne TBS: termomodernizacja 4 budynków — **H. Kołłątaja 67, 69, 71 + Pileckiego 4 (os. Bacieczki I)** (ogłoszenie BZP 2024/BZP 00352328 z 2024-06-05; wynik 2025/BZP 00108667 z 2025-02-18) — dowód, że bloki tego osiedla są ocieplane.
- Analogicznie: ks. Popiełuszki 72/73/75 (os. Zielone Wzgórza, TBS) oraz budynek usługowo-handlowy Bema 89D (TBS, 2026).
- Miasto Białystok: termomodernizacje szkół/przedszkoli (m.in. SP 43 ul. Stroma, ZSP nr 5 ul. Magnoliowa 13).
- **Kolory elewacji po termomodernizacji: UNVERIFIED** — konkretne kolory tynku są w STWiUR na platformach przetargowych niedostępnych bez logowania; w manifeście kolumna `kolor_srgb` z metodą.
- **MPZP Białostoczek** (uchwała + projekt tekstu planu, BIP): dla **nowej** zabudowy: max 3 kolory elewacji, odcienie bieli + barwy naturalne (drewno), pokrycia dachów w odcieniach ciemnej czerwieni, dachy 0–15° — przydatne do generatora dla strefy docelowej.

### Drewniane domy podlaskie
- Potwierdzone kategoriami Commons: Bojary (2 poz.), Prowiantowa, Chmielna, Wąska, Olecka, Choroszczańska, Ślusarska, Słonimska 31 (dom zabytkowy k. XIX w. — wg opisu autora; również Kraszewskiego 15A w kategorii). OSM podaje lv=2 przy Prowiantowej 6/1. LoD1 mh: 3,9–10,9 m (parterowe i piętrowe).

### Pawilony, hale, garaże, stacje, usługowe
- Pawilony: przy Białostoczku (13b — weterynarz, 1/1), Sokólska 9 (Lewiatan — opis autora), Zwycięstwa 18/26 (sklepy — opis autora), Andersa 40 (**Podlaskie Centrum Rolno-Towarowe**, hala targowa, OSM: retail+marketplace), Hala Zwycięstwa (mh=5,5 m — typowa bryła pawilonu handlowego).
- Hale/magazyny: ZWSE przy Andersa (desc), Spółdzielnia Obrotu Towarowego (mh=6,59), Supon Octowa 3 (mh=8,59), oczyszczalnia Składowa, hale Bacieczek (2021-10-17, mh 6,6–8,1 m).
- Garaże: zespoły przy Morelowej (OSM: building=roof), Zwierzynieckiej 21, Pogodnej, Sławińskiego, Izby Celnej (adresy z opisów autora H. Borawskiego; pozycje bez GPS — UNVERIFIED w kolumnie lat/lon).
- Stacje paliw: przy Andersa (2 poz. z kategorii Petrol stations; OSM: zadaszenie lv=1 w 13 m; Circle K Andersa 38 wg OSM — zdjęcie z 33 m od POI, ESTIMATED), Orlen Kawaleryjska 27, Shell Składowa, Statoil Słonecznikowa (opisy autora), 2 poz. z kategorii Petrol stations (rejon Poleskiej i Pietrasz/Zwierzyniec). Dachy: w OSM zadaszenia building=roof — **w LoD1 stacje są obiektami płaskimi ~4–10 m**.
- Usługowe: **Andersa 38 = biurowiec Biazet S.A.** (OSM: office, 11 kond., height=41 m — rozbieżność z LoD1 opisana wyżej), Zespół Szkół Mechanicznych (internat), Szkoła Podstawowa nr 4, Urząd Pocztowy nr 2 (Kolejowa 15), Bank Pekao (Rynek Kościuszki 7).

### LoD1 (GUGiK, CC BY 4.0) — co się rozpoznaje automatycznie, a co ręcznie
**Da się rozpoznać z obrysu + measuredHeight (generator świata):**
- blok wielorodzinny: obrys wydłużony/Z, mh 12–20 m (5 kond.) lub >25 m (10–12 kond.);
- dom jednorodzinny: mały obrys, mh 4–10 m;
- hala/magazyn: wielki prostokątny obrys, mh 5–10 m, roofType=1000;
- pawilon: obrys prostokątny, mh 4–8 m.

**Wymaga ręcznego przypisania (LoD1 nie niesie tej informacji):**
- **materiał** (dom drewniany vs murowany — identyczna bryła);
- **system wielkiej płyty** (OWT-67/W-70/Szczecin) — brak w LoD1 i OSM;
- pawilon vs garaż vs warsztat przy zbliżonej bryle;
- **kolory elewacji** (LoD1 nie ma tekstur);
- dachy skośne: **wszystkie obiekty LoD1 2024 mają roofType=1000** (płaskie) — geometria dachu domów jednorodzinnych wymaga OSM `roof:shape` lub zdjęć;
- stacje paliw: w LoD1 widoczny jest budynek/zadaszenie 4–10 m, ale funkcja (canopy stacji) — tylko z OSM (`amenity=fuel`, `building=roof`).

**Przykład identyfikatora:** Sokólska 11: `buildingId=2BE4B431-B0D6-1BF0-E053-CC2BA8C0D140`, `measuredHeight=15,47 m`. Wszystkie buildingId i mh w kolumnie `lod1_measuredHeight_m` + uwagach manifestu.

### Sezony i pory dnia
Pozycje mają obowiązkowe kolumny `sezon` (liście / bez liści) i `pora_dnia` (rano/południe/wieczór/zmierzch) wyliczone z daty i godziny z metadanych Commons (ESTIMATED — metoda w uwagach). Zestaw obejmuje **oba sezony**: liście (V–IX) i bez liści (X–IV); śnieg: UNVERIFIED (agent nie odczytuje treści obrazów). Różne pory dnia: rano/południe/wieczór/zmierzch wg godziny zdjęcia.

## 4. Braki i niepewności

- **Mapillary:** pominięty — API wymaga tokenu, którego nie było (zasada A); nie zgadywano kluczy. Pewne typy (garaże blaszane) mają tylko 5 pozycji, w tym 3 bez GPS.
- **Kolory elewacji (sRGB):** dla większości UNVERIFIED (brak publicznych STWiUR); metoda w kolumnie `metoda_koloru`. MPZP Białostoczek opisuje tylko nową zabudowę.
- **Przypisanie systemu wielkiej płyty do osiedli Białegostoku:** brak publicznych źródeł; OWT-67 potwierdzony tylko dla jednego budynku (były Miastoprojekt). System per adres: UNVERIFIED.
- **Kierunek patrzenia (azymut):** UNVERIFIED — Commons nie zapisuje GPSImgDirection (pojedynczy test extmetadata potwierdził brak).
- **Część adresów ESTIMATED** (najbliższy budynek OSM 40–60 m od punktu GPS) — oznaczone w uwagach.
- **Śnieg:** niezweryfikowany wizualnie; kolumna sezon dla XII–II zawiera adnotację.
- Zdjęcia z 2013 (H. Borawski) dokumentują stan przed termomodernizacjami — to zaleta (porównanie przed/po), ale kolory „po" wymagają osobnych dokumentów.
- zdjęcia P3-006/P3-011 (portret) pobierane są jako miniatury 960/500 px szerokości (limit Wikimedia) — dłuższy bok ≤1600 spełniony.

## 5. Samokontrola (20 %)

- **Seed:** 20261113 (Python `random.seed(20261113)`, `random.sample` z 62 pozycji).
- **Wylosowano 13 pozycji (21,0 % ≥ 20 %):** pełna lista w `audit_20_percent.json`.
- **Sprawdzono:** HTTP 200 na `url_źródła` (strona pliku Commons), licencja na liście dozwolonych, lat/lon w rejonie Białegostoku, plik `files/<id>.jpg` poprawnym JPG.
- **Wynik: 13/13 OK, 0 problemów.**

## 6. Zawartość paczki

- `README.md` — niniejszy opis.
- `manifest.csv` — 62 wiersze; kolumny: id, typ_budynku, adres, lat, lon, kondygnacje, wys_kondygnacji_m, rytm_okien_m, kolor_srgb, metoda_koloru, dach, materiał, lod1_measuredHeight_m, sezon, pora_dnia, url_źródła, licencja, autor, data_dostępu, status (SOURCED/ESTIMATED/UNVERIFIED), uwagi.
- `files/P3-001…P3-062.jpg` — 62 zdjęcia (≤1600 px dłuższego boku, JPG).
- `docs/mpzp_bialostoczek_uchwala.pdf` — uchwała RM Białystok w sprawie MPZP części os. Białostoczek (dokument urzędowy, art. 4 pr. aut.).
- `sources.md` — lista źródeł z datą dostępu.
- `audit_20_percent.json` — wynik samokontroli.

**Licencje plików:** CC0 (39, Rakoon), CC BY 3.0 (4, Rakoon), CC BY-SA 2.0/3.0/4.0 (19, H. Borawski/Adam63 — share-alike: używać jako referencji, nie jako tekstur; wycinki oznaczone w uwagach manifestu). Dane OSM: ODbL. LoD1 GUGiK: CC BY 4.0. Dokumenty urzędowe: art. 4 ustawy o prawie autorskim. Brak plików NC/ND. Brak marek/logo producentów ciężarówek.
