# gptpro-p6-next-regions-2 — uzupełnienie paczki G2 (2-next-regions)

**Projekt:** Kamion — realistyczny mobilny symulator ciężarówki z naczepą; świat Białegostoku w skali 1:1 z danych OSM i GUGiK; gra komercyjna (budżet 0 zł).
**Zadanie P6:** uzupełnienie paczki research/gptpro/2-next-regions (region bialystok-industrial-c, bbox EPSG:2180 776971–779019 × 595199–597247, 57 miejsc, 5 kafli G2).
**Data wykonania:** 2026-11-13. **Język:** polski. **Autor:** agent researchowy (dane OSM/ODbL, GUGiK, BIP, TED, GDDKiA).

---

## 1. Cel

1. Zaproponować 3–5 kafli 2×2 km (siatka EPSG:2180, rogi jako liczby całkowite w metrach) przylegających do bboxu regionu lub do poprzedniego kafla — wokół Dojlid, Krywlan i Fabrycznej/Suchowolca (E/SE) oraz na północ (DK8, Tykocin/Złotoria) — z oceną celów dla ciężarówek, kilometrażem dróg ≥ secondary, ciągłością korytarza i punktami orientacyjnymi; porównanie z kaflami G2 i kolejność dla gry.
2. Domknąć pozycje UNVERIFIED z G2: RS16 (WIM Zabłudowska), Panattoni (403), Biazet (certyfikat), TED 213042-2026, S19 Krynice–Białystok Zachód (20.10.2026?), MOP Haćki (29.10.2026?).
3. Zweryfikować trasy dojazdu od S8 do 10 najważniejszych celów G2 na danych OSM (kolejne ulice z highway/maxweight/hgv/maxheight, wersje way, ograniczenia z G10).
4. Bramy i place manewrowe ≥ 10 zakładów z TAK na ortofoto GUGiK (bez Google).

## 2. Metoda

- **Dane OSM:** wycinek `podlaskie-latest.osm.pbf` (Geofabrik, 2026-11-13, md5 `90516bf6fae1d3cac01c60b3cfd7fd01`); własny parser PBF (czysty Python) → ways (id, version, timestamp, geometria) + nodes z barrier/entrance. **Overpass nie był używany** (masowe zapytania wykluczone); weryfikacje pojedynczych obiektów przez `api.openstreetmap.org` (UA: KamionResearch/1.0).
- **Transformacja EPSG:2180:** własny moduł geo.py (zweryfikowany), wszystkie bboxy i chainage liczone w metrach.
- **Routing (część 3):** graf ways (spójność po współrzędnych węzłów), Dijkstra; koszty = długość × współczynnik klasy drogi + kary za ograniczenia (hgv=no/maxweight ≤ 3,5 → ×25; maxheight < 4,5 → ×25; maxweight ≤ 8 → ×3). Start: węzeł S8 na zachodnim skraju wycinka; 10 celów G2. Pełne listy ulic i way id + wersje: `files/P6-R00-trasy.txt` (skrót) i `files/P6-R00-trasy.json` (pełny przebieg).
- **Ortofoto (część 4):** GUGiK WCS `Orthoimagery_High_Resolution` (otwarte dane), wycinki 160×160 m = 1600×1600 px (10 cm/px), bbox EPSG:2180 dokładnie podany w manifeście; skorowidz WFS dla każdego bboxu (arkusze 5 cm z 2024 i 2025 — mozaika WCS, dokładny arkusz piksela UNVERIFIED).
- **Pomiar bram:** ograniczenie sesji — limit analizy obrazu (vision) 20 wywołań, wyczerpany przez wcześniejsze etapy paczki (weryfikacje ortofoto RS16). Zastosowano metodę zastępczą: **szerokość przejazdu = odległość końców ways `barrier=fence` naprzeciw wjazdu** w EPSG:2180 (ESTIMATED ±1 m, dokładność mapowania OSM); tam, gdzie ogrodzenie zmapowane ciągłe albo brak bramy w OSM — UNVERIFIED. Promień łuku wjazdu UNVERIFIED (wymaga pomiaru na ortofoto); **wycinki ortofoto są w paczce** do pomiaru ręcznego lub powtórnej analizy automatycznej w kolejnej sesji.
- **Ograniczenia TIR:** z research/g10-truck-restrictions (Myśliwska 3,5 t/hgv=no — osiedle Dojlidy Górne; Dojlidy Fabryczne hgv=no 3,5 t od XII 2025; Adama Mickiewicza maxweight=8; rondo Meyera hgv=no; rondo Putry maxheight; maxaxleload=11,5 na kafach zachodnich).
- **Zakaz Google:** zachowany — użyto wyłącznie OSM, GUGiK, BIP, TED, GDDKiA, stron firmowych (faktografia, tylko referencja).

## 3. Najważniejsze ustalenia

### 3.1 Kafle (część 1)

Zaproponowano łańcuch 5 kafli **K1→K2→K3→K4→K5** (każdy 2000×2000 m, przylega krawędzią do bboxu regionu lub do poprzedniego kafla; konwencja jak w G2 — bbox regionu ma 2048 m, wspólne krawędzie 2000 m) plus alternatywę **K6** na północ (DK8). Ciągłość korytarza potwierdzona przecięciami krawędzi przez drogi ≥ secondary: bbox→K1 al. Tysiąclecia; K1→K2 Branickiego i Legionowa; K2→K3 Wiejska; K3→K4 Dywizjonu 303 i Ciołkowskiego; K4→K5 Kuronia.

| kafel | rogi EPSG:2180 (SW→NE) | km dróg ≥sec. | cele TAK | UNVERIF./NIE | korytarz | punkty orientacyjne |
|---|---|---|---|---|---|---|
| region G2 | 776971,595199→779019,597247 | 11,52 | 2 (BIAZET, Kwadrat) | — | — | — |
| G2-T01 | 774971,595199→776971,597199 | 9,37 | 0 | 0 | Maczka/Hallera/Świętokrzyska | rondo Nowaka-Jeziorańskiego |
| G2-T02 | 772971,595199→774971,597199 | 9,34 | 1 (Bunasta) | 1 (Selgros) | Maczka/Produkcyjna/Kleeberga | Antoniuk Fabryczny |
| G2-T03 | 770971,594899→772971,596899 | 7,79 | 3 (Panattoni I, DPD, WER) | 0 | Kleeberga/Knyszyńska/Ełcka | Szosa Knyszyńska |
| G2-T04 | 770971,592899→772971,594899 | 8,17 | 1 (PZZ) | 2 (PROMOTECH, MAKRO) | al. Jana Pawła II/DW676 | — |
| G2-T05 | 768971,593449→770971,595449 | 5,59 | 0 | 3 (GLS, DHL, Witraż) | 8;65/S8 | S8 |
| **P6-K01** | **777019,593199→779019,595199** | **11,53** | **3 (EC Białystok, Forte, ALBA)** | 1 UNVERIF. (Intrum), 1 NIE (Wodociągi) | al. Tysiąclecia (przylega do bboxu od S) | kominy Elektrociepłowni, kompleks Forte |
| **P6-K02** | **777019,591199→779019,593199** | **9,81** | **0** | 0 | Branickiego, Legionowa (do K1) | Las Zwierzyniecki |
| **P6-K03** | **777019,589199→779019,591199** | **8,21** | **0** | 2 UNVERIF. (Stadler, Skład pojazdów), 1 NIE (Aeroklub — punkt orient.) | Wiejska (do K2) | hangary Aeroklubu, apron lotniska Krywlany (zachód) |
| **P6-K04** | **779019,589199→781019,591199** | **4,44** | **5 (Rosti, KAN, Odlewnia, Bravilor, PSS DC)** | 2 UNVERIF. (BISON, Masterpress) | Dywizjonu 303, Ciołkowskiego (do K3) | wschodnia część lotniska Krywlany |
| **P6-K05** | **781019,589199→783019,591199** | **4,37** | **3 (browar Dojlidy, Bieldruk, Polfood)** | 2 UNVERIF. (NIBE-BIAWAR, Spod Igły) | Kuronia (do K4) | browar Dojlidy (silosy), Suchowolca |
| **P6-K06 (alt.)** | **776971,597247→778971,599247** | **4,60** | **0** | RS15 WIM (kandydat) | al. Tysiąclecia (przylega do bboxu od N), DK8 8;19 | skansen Podlaskiego Muzeum Kultury Ludowej, węzeł DK8/S8 |

**Kolejność dla gry: K01 → K04 → K05 → K03 → K02** (K06 → pierwsza paczka P7).
Uzasadnienie: kryterium są **konkretne zakłady i ich bramy, nie tagi industrial**. K01 ma 3 nowe cele TAK o dużej powierzchni (Elektrociepłownia ~56 ha, Forte 8,4 ha, ALBA) i najlepsze drogi (11,5 km ≥ secondary); K04 to najgęstszy klaster celów (7 zakładów w SSSE Dojlidy/Krywlany); K05 domyka browar i K5 wschodni; K03 wprowadza lotnisko Krywlany jako silny punkt orientacyjny ( gameplay: nawigacja wizualna); K02 czysto korytarzowy — budowany przy okazji przebiegu. K06 (DK8 na Tykocin/Złotorię) ma 0 celów i niski kilometraż — lepszy jako temat osobnej paczki P7 z RS15.

### 3.2 Domknięcia UNVERIFIED z G2 (część 2) — wszystkie rozstrzygnięte

- **RS16 WIM Zabłudowska: ESTIMATED** — (53.088753, 23.246754) = EPSG:2180 (784259, 588808), ±150 m wzdłuż DK19. Metoda: PFU (BIP id.77056) podaje „1295 m od stałego punktu kontroli" przy skrzyżowaniu Zabłudowska × Stoczni Gdańskiej; chainage 1295 m wzdłuż DK19 (SE) daje punkt w Kurianach. Ortofoto (2024-03-30): bramownicy nie wykryto — pozostaje ESTIMATED. Wycinki: files/P6-U01-a…h.jpg; PDF PFU: files/P6-U01.pdf.
- **Panattoni: SOURCED** — wszystkie 3 URL-e z G2 zwracają HTTP 200 (403 nie odtwarza się). Cytaty potwierdzają: Park III 32 000 m² w Choroszczy przy węźle Białystok-Zachód; „ponad 41 tys. m kw." (2018). Treści tylko referencja (brak jawnej licencji).
- **Biazet: SOURCED** — HTTP 200 z pominięciem weryfikacji TLS (błąd łańcucha certyfikatów nadal po stronie serwera); cytat: „Biazet S.A. ul. Gen. Władysława Andersa 44 15-113 Białystok".
- **TED 213042-2026: SOURCED** — PDF czytelny (files/P6-U04.pdf): „WER Białystok, przy ul. Welurowa 6, 15-900 Białystok", OJ S 61/2026 z 27/03/2026.
- **S19 Krynice–Białystok Zachód: SOURCED — 20.10.2026 POTWIERDZONA** (komunikat GDDKiA ODD Białystok z 20.10.2026: „Kierowcy mogą już korzystać z drogi ekspresowej S19 Krynice - Dobrzyniewo - Białystok Zachód").
- **MOP Haćki: SOURCED — 29.10.2026 POTWIERDZONA** (komunikat GDDKiA z 29.10.2026: dwa MOP na S19 Deniski–Haćki, po 26 ukośnych stanowisk dla ciężarówek).

### 3.3 Trasy od S8 (część 3) — 10 celów G2

Wspólny korytarz ciężki (zgodny z G10): S8 → węzeł Porosły (8;65) → al. Jana Pawła II → al. Niepodległości → al. Paderewskiego → Wiadukt → Ciołkowskiego → Dywizjonu 303 → Kuronia (południowy wschód), lub Kleeberga → Maczka (północ) i Produkcyjna → Welurowa (północny zachód). Szczegóły (każda ulica z highway, maxweight/hgv/maxheight, way id + wersja) w files/P6-R00-trasy.{txt,json}. Kluczowe konflikty:

- **KAN (Karpińskiego 5):** optymalna trasa przechodzi 247 m **Adama Mickiewicza z maxweight=8 (G10)**; ominięcie wymaga wjazdu w Myśliwską (3,5 t/hgv=no). Do rozstrzygnięcia w grze (wyjątki dostawcze?).
- **BIAFORM (Fabryczne 24):** wyliczona trasa przechodzi **rondo Meyera (hgv=no, G10)** oraz końcówkę **Dojlidy Fabryczne (hgv=no/3,5 t od XII 2025, G10)**; ulice osiedlowe w środku trasy to artefakt wag routera. Rekomendacja: korytarz ciężki od północy + brama od Suchowolca do weryfikacji organizacji ruchu.
- **Rosti (Myśliwska 18) i browar (Fabryczne 28):** router sam omija strefy 3,5 t — wjazdy drogami wewnętrznymi od **Kuronia** (browar) i od północy (Rosti, doki od Karpińskiego).
- **S8/S19:** po otwarciu S19 (20.10.2026) i MOP Haćki (29.10.2026) pojawia się alternatywny dojazd od południowego zachodu — temat dla P7.

### 3.4 Bramy i place manewrowe (część 4) — 14 zakładów

| id | zakład | brama w OSM (node, wersja) | szerokość wjazdu | promień łuku |
|---|---|---|---|---|
| P6-G01 | BIAZET Andersa 44 | lift_gate 12126375017 v2 | UNVERIFIED | UNVERIFIED |
| P6-G02 | Kwadrat Andersa 38 | lift_gate 10024132807 v2 (private) | UNVERIFIED | UNVERIFIED |
| P6-G03 | Rosti Myśliwska 18 | gate 6596800253 v2 | UNVERIFIED | UNVERIFIED |
| P6-G04 | KAN Karpińskiego 5 | lift_gate 4656499172 v4 (customers) | UNVERIFIED | UNVERIFIED |
| P6-G05 | BIAFORM Fabryczne 24 | gate 2814000970 v1 (customers) | UNVERIFIED | UNVERIFIED |
| P6-G06 | Browar Dojlidy Fabryczne 28 | gate 6085185775 v2 (private) | UNVERIFIED | UNVERIFIED |
| P6-G07 | WER Poczta Welurowa 6 | lift_gate 9306871344 v1 | **15,5 m ±1 m** (ESTIMATED — przerwa w ogrodzeniu OSM) | UNVERIFIED |
| P6-G08 | DPD Welurowa | lift_gate 6448194342 v3 (delivery) | **12,6 m ±1 m** (ESTIMATED — przerwa w ogrodzeniu OSM) | UNVERIFIED |
| P6-G09 | Raben Żółtki | brak w OSM (150 m) | UNVERIFIED | UNVERIFIED |
| P6-G10 | PZZ Elewatorska/Zbożowa | gate 3465808562 v1 | UNVERIFIED | UNVERIFIED |
| P6-G11 | Masterpress Kuronia 4 | lift_gate 2999986083 v1 | UNVERIFIED | UNVERIFIED |
| P6-G12 | Elektrociepłownia Andersa 15 | brak w OSM (150 m) | UNVERIFIED | UNVERIFIED |
| P6-G13 | Bieldruk Kuronia 20 | gate 10875232003 v2 | UNVERIFIED | UNVERIFIED |
| P6-G14 | Bravilor Kuronia 2 | gate 6539179208 v1 | UNVERIFIED | UNVERIFIED |

Każdemu wierszowi odpowiada wycinek ortofoto GUGiK 10 cm/px (files/P6-G01…G14.jpg) z dokładnym bboxem EPSG:2180 — pomiar bramy i łuku można wykonać/dpowtórzyć bezpośrednio na załączonym materiale.

## 4. Braki i niepewności

- **Promienie łuków wjazdu: UNVERIFIED** — limit 20 wywołań analizy obrazu na sesję został zużyty przez wcześniejsze etapy (weryfikacje ortofoto RS16). Wycinki ortofoto są w paczce; pomiar wymaga sesji z analizą obrazu (kontynuacja możliwa od ręki).
- **Szerokości bram: ESTIMATED tylko tam, gdzie ogrodzenie przerwane w OSM** (WER, DPD). W pozostałych przypadkach ogrodzenia zmapowano ciągle przez bramę — szerokość UNVERIFIED.
- RS16: dokładna lokalizacja czujników (przecinek chainage 1295 m) ESTIMATED ±150 m; bramownicy nie widać na ortofoto 2024-03-30.
- Biazet: błąd TLS po stronie serwera (odczyt wymaga pominięcia weryfikacji certyfikatu).
- Trasy: routing własny na wycinku Geofabrik — to korytarze badawcze, nie gotowa nawigacja HGV; organizacja ruchu może się różnić (zwłaszcza końcówki: Myśliwska/Karpińskiego, Dojlidy Fabryczne).
- Nazwa ulicy przy PZZ w OSM to Zbożowa; adres „Elewatorska 14" (z G2) niepotwierdzony w OSM.
- Arkusze mozaiki WCS na wycinkach: skorowidz pokazuje arkusze 5 cm z 2024 i 2025 — który dokładnie serwuje dany piksel, UNVERIFIED (sezon: wiosna, bez liści/początek wegetacji).

## 5. Samokontrola (reguła F)

- **Seed: 20261113** (jawny), `random.Random(20261113).sample(ids, 10)` na **wszystkich 48 pozycjach** manifestu (nie tylko pobranych) → próba 10 pozycji = 20,8% ≥ 20%.
- Wylosowano: P6-C03, P6-C06, P6-G07, P6-G12, P6-K01, P6-K02, P6-K05, P6-R06, P6-R09, P6-U06.
- Kontrole: (a) współrzędne WGS84 → EPSG:2180 mieszczą się w bbox pozycji; (b) osm_id i wersja zweryfikowane **na żywo w API openstreetmap.org**; (c) pierwszy URL źródła odpowiada (HTTP; dla biazet.pl adnotacja o TLS); (d) licencja zapisana i merytoryczna.
- **Wynik: 10/10 OK** (szczegóły w audit_20_percent.json). Pierwsze losowanie wykazało 2 błędy (bbox P6-R06, wersja P6-U06) — poprawione przed oddaniem; wynik po poprawkach w pełni OK.

## 6. Licencje plików w paczce

- `files/P6-G*.jpg`, `files/P6-U01-a…h.jpg` — ortofotomapa: **otwarte dane PZGIK/GUGiK** (dowolne ponowne wykorzystanie, w tym komercyjne; warunek: podać źródło, czas wytworzenia i pozyskania, przetworzenie oraz twórcę, jeśli znany). Czas pozyskania: 2026-11-13; czas wytworzenia: nalot 2024-03-30 lub 2025-04-18 (zależnie od arkusza mozaiki — patrz §4).
- `files/P6-U01.pdf` (PFU, BIP m. Białystok), `files/P6-U04.pdf` (TED, Dz.Urz. UE OJ S) — **dokumenty urzędowe, art. 4 ustawy o prawie autorskim** (domena publiczna).
- `files/P6-*.txt/json` — opracowania własne na danych OSM: **ODbL 1.0, © OpenStreetMap contributors**.
- manifest.csv, README.md, sources.md, audit_20_percent.json — opracowanie własne (dane źródłowe wg licencji powyżej).
- Strony firmowe (Panattoni, Biazet, Forte, Bieldruk) — **tylko referencja, nie pobrano** do paczki (faktografia wolna od praw autorskich).

## 7. Struktura paczki

```
README.md, manifest.csv, sources.md, audit_20_percent.json
files/  P6-G01…G14.jpg (orto 10 cm/px, 1600 px), P6-U01.pdf, P6-U04.pdf,
        P6-U01-a…h.jpg (orto RS16), P6-R00-trasy.json, P6-R00-trasy.txt,
        P6-C00-osm.txt (rekordy OSM nowych celów), P6-K00-kafle.txt (pomiary km),
        P6-G00-osm.txt (analiza bram/ogrodzeń z OSM)
```
