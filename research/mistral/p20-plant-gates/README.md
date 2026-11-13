# P20 — Hala A i zakład B (Dojlidy/Krywlany, Białystok): bramy, podziały ścian i wysokości segmentów

Gałąź: `research/mistral-p20-plant-gates` · Katalog: `research/mistral/p20-plant-gates/`
Data opracowania: 2026-11-12 / 2026-11-13 · Autor: agent badawczy (Mistral)

**STAN OPRACOWANIA: CZĘŚCIOWY (commit pośredni).** Zakończono: identyfikacja, wysokości segmentów (NMPT−NMT), ściana wschodnia hali A z bramami, ogrodzenie i otoczenie A, typowe wymiary bram, kadry A (oględziny + eliminacje).
**W toku:** oględziny 14 kadrów zakładu B z 2019 r. (Kuronia/Mickiewicza) i 3 kadrów Kuronia z 2023 r. — po ich obejrzeniu uzupełnione zostaną sekcje 5–7 dla B oraz wiersze manifestu; samokontrola 20 % zostanie wtedy domknięta (plik `audit_20_percent.json`).

Wyniki dla gry: **hala A** = zakład przy ul. Jacka Kuronia (kadr referencyjny P11-094); **zakład B** = róg Mickiewicza/Kuronia (kadr referencyjny P11-063). W opisach przeznaczonych do odtwarzania w grze nie używamy nazw firm ani logo — „napis firmowy, nie odtwarzamy”.

---

## 1. Identyfikacja (OSM / EGiB / LoD1 / BDOT10k)

### Hala A — zakład przy ul. Jacka Kuronia
| atrybut | wartość | źródło |
|---|---|---|
| OSM way | **471492583** (building=industrial, magazyn) | [OSM](https://www.openstreetmap.org/way/471492583), ODbL |
| obrys OSM | 15 wierzchołków / **14 segmentów**, obwód **515,7 m**; EPSG:2180: E[780648,2; 780790,8], N[590300,3; 590468,3] | OSM API /way/471492583/full |
| pełny obrys zakładu | **EGiB 206101_1.0021.1495_BUD** (47 wierzchołków; N[590209,9; 590468,5], E[780550,7; 780790,2]) — OSM pokazuje tylko główną halę | KIEG (GetFeatureInfo, 2026-11-12) |
| działka ewid. | 206101_1.0021.**767/20** (obręb Dojlidy) | KIEG |
| LoD1 2024 | **18,92 m** (152,06→170,98 m n.p.m.), gml:id `ID-2061-2BE4B431-BC59-1BF0-E053-CC2BA8C0D140` | [Modele 3D budynków GUGiK](https://www.geoportal.gov.pl/pl/dane/inne-dane/modele-3d-budynkow/) |
| LoD2 2017 | **brak obiektu w zbiorze** (luka kolekcji) | GUGiK |
| BDOT10k (kod funkcji) | **UNVERIFIED** — WFS PZGIK odrzuca zapytania anonimowe (HTTP Unauthorized); kodu nie pobrano | — |
| liczba kondygnacji | **UNVERIFIED** (brak danych EGiB/BDOT; hala wysokoskokowa — patrz sekcja 3) | — |

### Zakład B — róg Mickiewicza/Kuronia
| atrybut | wartość | źródło |
|---|---|---|
| OSM way | **513010463** (building=industrial, man_made=works; addr: Jacka Kuronia 2) | [OSM](https://www.openstreetmap.org/way/513010463), ODbL |
| obrys OSM | 7 wierzchołków / **6 segmentów**, obwód **450,9 m**; romb: seg1 **151,1 m** (az 64° — krawędź NW od Kuronia), seg2 **74,3 m** (az 154°), seg3 **138,8 m** (krawędź SE), seg4 4,4 m, seg5 12,3 m, seg6 69,8 m; EPSG:2180: E[780090,7; 780259,2], N[590353,1; 590482,1] | OSM API |
| pełny obrys | **EGiB 206101_1.0021.1580_BUD** (42 wierzchołki) | KIEG |
| działka ewid. | 206101_1.0021.**767/29** | KIEG |
| LoD1 2024 | **12,72 m**, gml:id `ID-2061-941cfc23-bd8b-40d5-a49b-d1bba751d5bd` | GUGiK |
| LoD2 2017 | **brak obiektu** (luka) | GUGiK |
| BDOT10k (kod funkcji) | **UNVERIFIED** (WFS Unauthorized) | — |

Transformacja EPSG:2180↔WGS84: klasyczne równania odwzorowania Mercatora poprzecznego (Snyder) dla układu PL-1992; zwalidowana na 3 punktach EXIF (błąd roundtrip < 5 mm; pozycje kamer zgodne z oczekiwaniami ±2 m).

---

## 2. Metoda wysokości

NMPT (DSM) − NMT (DTM), raster 1 m, EVRF2007-NH, okna GetCoverage z 2026-11-13:

- NMPT: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DSM_PL-EVRF2007-NH&SUBSET=x(E1,E2)&SUBSET=y(N1,N2)&FORMAT=image/x-aaigrid`
- NMT: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModel?...COVERAGEID=DTM_PL-EVRF2007-NH...`

Mediana wysokości (DSM−DTM) po segmentacji komponentów spójnych (próg 4 m; komórki 1 m) — hala A; dla B dodatkowo okna prostokątne (proste, powtarzalne). Wartości „attyki” = wysokość krawędzi dachu (mediana komponentu). Śródokna: A: E 780520–780840, N 590180–590500; B: E 780050–780300, N 590320–590510.

---

## 3. Segmenty wysokości — hala A

**Cztery poziomy dachu** (komponenty spójne; wszystkie współrzędne EPSG:2180, podane też WGS84 w manifest.csv):

| segment | opis | mediana H [m] | dach [m n.p.m.] | pow. [m²] | zasięg N / E |
|---|---|---|---|---|---|
| **A1** | wysoka hala wschodnia (od Myśliwej/Kuronia) | **18,19** | 171,05 | 9182 | N[590314; 590462] / E[780674; 780788] |
| **A2** | blok SW | **14,32** | 168,43 | 8048 | N[590227; 590314] / E[780553; 780702] |
| **A3** | pas W+S (kształt L, wzdłuż zachodniej krawędzi A1 i na południe) | **12,43** | 165,36 | 5715 | N[590278; 590468] / E[780605; 780725] |
| **A4** | pas południowy | **12,97** | 167,20 | 2843 | N[590210; 590252] / E[780550; 780697] |
| dodatkowy | element 16,65 m (przybudówka przy A) | 16,65 | 170,41 | 100 | N[590272; 590278] / E[780624; 780653] |

**Uskoki (położenie krawędzi skoku):**
- A1→A3: **18,2→12,4 m** wzdłuż E≈780674–780725 (zachodnia krawędź wysokiej hali);
- A1→A2: **18,2→14,3 m** wzdłuż N≈590314 (południowa krawędź wysokiej hali);
- A2→A4: **14,3→13,0 m** przy N≈590252.

**Wniosek dla gry:** LoD1 18,92 m nadaje jeden box całemu obrysowi — stąd ~12 % zawyżenia i brak schodka wschodniego w grze. Realnie: wysoka (18,2 m) jest tylko **wschodnia** część obrysu EGiB; dalej ku zachodowi 14,3 m, 12,4 m i 13,0 m. Kontrola niezależnym oknem (2026-11-13): A1 med 17,93–17,94 (okno zawiera krawędzie/mieszane komórki) — zgodne w granicach metody (komponent izoluje dach).

## 3b. Segmenty wysokości — zakład B

| część | mediana H [m] | dach [m n.p.m.] | okno N / E |
|---|---|---|---|
| **B-F** front zachodni (od Mickiewicza) | **10,97** | 168,39 | N[590380; 590470] / E[780091; 780150] |
| **B-M** część środkowa | **11,94** | 169,10 | N[590380; 590470] / E[780150; 780210] |
| **B-E** wschodnia biała hala | **12,03** | 169,24 | N[590360; 590465] / E[780210; 780260] |
| B-całość (komponent) | **12,04** | 169,29 | 8078 m², N[590359; 590468] / E[780113; 780257] |
| pas NW niski | **5,24** | 162,45 | N[590455; 590482] / E[780091; 780200] (wzdłuż NW krawędzi od Kuronia) |
| róg SW | **11,28** | 169,01 | N[590350; 590400] / E[780091; 780140] |
| aneks wschodni | **8,99** | 162,64 | N[590360; 590390] / E[780257; 780300] |

**„Ciemniejszy, wyższy front” z kadru P11-063:** wg NMPT front **nie jest wyższy** (10,97 m < 12,03 m hali). Wrażenie optyczne najpewniej wynika z kompozycji kadru / pionu ściany / ew. attyki — do rozstrzygnięcia po ponownych oględzinach P11-063 i serii z 2019 r. (sekcja „w toku”).

---

## 4. Okładzina i podział ścian — hala A

### Ściana wschodnia (widoczna z ul. Kuronia; kadry P11-094, P11-095, NEW 20230903_134854)
| parametr | wartość | status |
|---|---|---|
| okładzina | **panele warstwowe poziome, jasnoszary** | SOURCED (P11-094, oględziny 3×) |
| kierunek paneli | poziomy | SOURCED |
| moduł paneli | **~1,0 m** | ESTIMATED (proporcje do wysokości ściany 18,2 m i bram) |
| pas okien pod dachem | **BRAK** — ściana jednolita od gzymsu do cokołu; pas okien w grze jest nieistniejący — **do usunięcia** | SOURCED (P11-094 ×3; potwierdzone P11-095) |
| okna | **BRAK** | SOURCED (sugestia okien z P11-093 odrzucona — to łączenia paneli) |
| pas cokołu | ciemniejszy szary, **~1,0 m** (materiał najpewniej beton — UNVERIFIED) | ESTIMATED |
| attyka | brak wyraźnej attyki | SOURCED |
| napis firmowy | centralnie, białe litery z podpisem — **napis firmowy, nie odtwarzamy** | SOURCED |
| lampy ścienne | **4 szt. pod okapem**, równomiernie | SOURCED |
| drzwi przejściowe / zacieki | UNVERIFIED (nierozstrzygnięte na kadrach) | UNVERIFIED |

### Pozostałe ściany A
- **północna** (za narożnikiem, wzdłuż Kuronia): UNVERIFIED — kadr P11-094 pokazuje narożnik; nie zakładać identycznej okładziny;
- **południowa** (od Karpińskiego): UNVERIFIED — kadry P11-035/034 pokazują głównie przeciwną stronę ulicy (biurowce);
- **zachodnia**: UNVERIFIED — wnętrze zakładu, brak kadrów.

### Zakład B
UNVERIFIED — w toku (14 kadrów z 2019 r. pobranych, oględziny w kolejnym kroku). Uzupełnienie: okładzina frontu i białej hali, bramy, pasy okien, attyka, ogrodzenie.

---

## 5. Bramy segmentowe i wjazdy

### Hala A — ROZSTRZYGNIĘCIE (ściana wschodnia, kadr P11-094)
**Ile bram: 2. Gdzie: ~60 % i ~80 % długości widocznej ściany, licząc od końca północnego (narożnik od Kuronia). Rozstaw środków ≈ 20 % długości ściany (~27–30 m).**

| parametr | wartość | status |
|---|---|---|
| liczba bram | **2** (gra: 0 — korekta) | SOURCED |
| typ | **segmentowe** (nie rolowane) | SOURCED |
| wymiary (szer.×wys.) | **~4,5–5,0 × ~4,5–5,0 m** | ESTIMATED (proporcje: wys. bramy ≈ ¼ wys. ściany 18,2 m wg NMPT; szer. z ~5 paneli ~1 m) |
| liczba paneli | **~5** pionowych | ESTIMATED |
| okienka | **0** (brak) | SOURCED |
| kolor | szary, zbliżony do okładziny ściany | SOURCED |
| rampa/dok | **BRAK — płaski asfalt** przed bramami | SOURCED |

### Zakład B
UNVERIFIED — w toku (patrz sekcja „stan opracowania”).

### Typowe wymiary bram przemysłowych (liczby z kart katalogowych / specyfikacji — bez nazw producentów w opisach)
1. Karta produktu bramy segmentowej przemysłowej: *„Szerokość światła bramy Min.: 1200 mm Maks.: 8000 mm; Wysokość światła otworu Maks.: 6000 mm”* (grubość panelu 42 mm, wysokość sekcji 545 mm). URL w `sources.md`. Norma odniesienia: **PN-EN 13241** (bramy — wymagania i klasyfikacja).
2. Specyfikacja techniczna bram przemysłowych: *„szerokość maksymalna - 4500 mm, z kształtownikiem usztywniającym od 4500 mm do 8000 mm; wysokość maksymalna - 6000 mm”*; minimum dla samochodów osobowych 2300×2000 mm.

Wymiary szacunkowe bram A mieszczą się w typowym zakresie 4000–5000 × 4000–5000 mm.

---

## 6. Otoczenie

### Hala A
| element | wartość | status |
|---|---|---|
| ogrodzenie | **siatka na metalowych słupkach** (słupki szare), **~2,0 m** — **NIE biały płot panelowy** | typ SOURCED (NEW 20230903_134854; kamera 128,8 m od obrysu — poza progiem 60 m, kadr jednoznacznie pokazuje halę); wysokość ESTIMATED |
| skarpa | u podstawy ściany wschodniej, porośnięta trawą | SOURCED (P11-094) |
| żywopłot | niski, strzyżony, u podstawy skarpy (wysokość UNVERIFIED) | SOURCED |
| latarnie uliczne | 2 szt. przy Kuronia (typ UNVERIFIED) | SOURCED (P11-095) |
| lampy ścienne | 4 szt. na ścianie wschodniej pod gzymsem | SOURCED |
| D-6 / znaki | UNVERIFIED (na P11-093 nierozstrzygnięte). **Korekta z zadania:** znak w grze stoi ~2–3 m za blisko kamery — przesunąć przy budowie | UNVERIFIED |

### Zakład B
UNVERIFIED — w toku (kadry z 2019 r.).

---

## 7. Kadry

### Najlepsze kadry dla artysty — hala A (3)
1. **P11-094** — `20230903_135016` ([Commons](https://commons.wikimedia.org/wiki/File:20230903_135016_September_2023_in_Bia%C5%82ystok.jpg), CC0, Rakoon, lato): ściana wschodnia z obiema bramami segmentowymi, okładzina, cokół, lampy, skarpa. Podstawa odtworzenia ściany i bram (kamera 43,1 m od obrysu).
2. **NEW 20230903_134854** ([Commons](https://commons.wikimedia.org/wiki/File:20230903_134854_September_2023_in_Bia%C5%82ystok.jpg), CC0): hala od wschodu + ogrodzenie z siatki i teren zielony — jedyne dobre źródło ogrodzenia (kamera 128,8 m).
3. **P11-095** — `20230903_135017` ([Commons](https://commons.wikimedia.org/wiki/File:20230903_135017_September_2023_in_Bia%C5%82ystok.jpg), CC0): kontekst — parking przed halą, napis firmowy, latarnie, zieleń (kamera 34,0 m).

### Zakład B — do uzupełnienia po oględzinach serii 2019 (kandydaci: skrzyżowanie Mickiewicza×Kuronia i serie uliczne).

### Wykaz oględzin (w tej sesji; łącznie z P11 ~18 unikalnych kadrów — samokontrola i liczniki w `audit_20_percent.json`)
- A: P11-094 (×3 pytania), P11-095, P11-093, P11-122/8866, NEW 134854 (×2), NEW 124730, NEW 124756, NEW 151306, NEW 151248, 8865, 8870, 8872, 8873, 8877, 8880 (eliminacje: 8872/8873/8877/8880 to inne zakłady przy Kuronia; 8877 — hala sąsiednia z pasem okien, możliwe (spekulacja) źródło błędnego pasa okien w grze);
- B: P11-063 (wstępnie) — seria 2019 (14 kadrów) i Kuronia 2023 (3 kadry) do obejrzenia.

---

## 8. Luki

1. **≥10 nowych kadrów ≤60 m z GPS nieosiągalne**: kadry Commons w promieniu ≤60 m od A i B są już w manifeście P11 (porównanie URL). Sondy: **Panoramax** — 0 wyników w otoczeniu; **KartaView** — 0; **Openverse** — lustro Commons/Flickr, nic nowego; **Mapillary** — nie sondowano (wymaga tokenu; bez cudzego tokenu). Nowe kadry w manifeście: A — 134854 (128,8 m), 124730/124756/151306/151248 (odrzucone — nie pokazują A), 8865/8870 (niejednoznaczne); B — 14 kadrów z 2019 r. (Rakoon, CC0, bez GPS — pozycja UNVERIFIED z tytułu/kategorii ulicy) + P11-063 referencyjny.
2. **BDOT10k / EGiB atrybuty** (kod funkcji, kondygnacje): WFS PZGIK — HTTP Unauthorized; UNVERIFIED.
3. **LoD2 2017**: obu budynków brak w zbiorze — brak geometrii dachu z LoD2.
4. **Kierunki kamer**: brak EXIF GPSImgDirection we wszystkich kadrach — kierunek_deg UNVERIFIED.
5. **Ściany A poza wschodnią** (N/S/W): UNVERIFIED — brak kadrów pokazujących te ściany.
6. **Kadry z 2019 r. (B) i z 2023-09-10 (Kuronia)**: bez GPS — pozycja z tytułu/kategorii; przypisanie do B dopiero po oględzinach treści.
7. **Wysokość bram A**: ESTIMATED z proporcji (±0,5 m); pomiar w terenie niemożliwy w zadaniu zdalnym.
8. **Pozycje bram A na ścianie**: ułamkowe (~0,60/~0,80) — dokładne współrzędne absolutne UNVERIFIED (kamera 43 m, brak pomiaru geodezyjnego).

## 9. Samokontrola

Plik `audit_20_percent.json`: seed **20261113** (jawny), próba ≥20 % wierszy manifestu; w bieżącym cyklu zweryfikowano ponownie: odczyty NMPT (niezależne okna kontrolne: A1 17,93 vs 18,19 komponent — wyjaśnione metodą), ponowne oględziny P11-094 (3 niezależne pytania — zgodność), rozbieżność P11-093 („okna”) vs P11-094 rozstrzygnięta na korzyść kontroli szczegółowej. Domknięcie audytu po uzupełnieniu kadrów B.

## 10. Pliki

- `README.md` — niniejszy dokument;
- `manifest.csv` — 75 wierszy (P20-001…P20-075): segmenty, ściany, bramy, ogrodzenie, latarnie, znaki, kadry (statusy SOURCED / ESTIMATED / UNVERIFIED / REJECTED);
- `sources.md` — źródła z URL i cytatami (w tym sondy ujemne);
- `audit_20_percent.json` — samokontrola (seed jawny);
- `files/` — miniatury kadrów (≤1600 px) — **poza gitem** (patrz `.gitignore`); przekazane w archiwum `mistral-p20-plant-gates-files.zip`.
