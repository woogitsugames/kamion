# mistral-p19-hospital-gate — brama szpitala (Żurawia 14, Dojlidy), kadr referencyjny P11-129

**Projekt:** Kamion — realistyczny mobilny symulator ciężarówki z naczepą; świat Białegostoku 1:1 (OSM + GUGiK); gra komercyjna, budżet 0 zł.
**Zadanie M62:** kadr referencyjny P11-129 (brama szpitala w Dojlidach) jest dziś najgorzej odwzorowany w regionie — brak muru z cegły z tablicami, ceglanych słupów z daszkiem, znaków STOP/B-33 „20”/C-2 i tablicy izby przyjęć; w tle generyczny blok. Cel: komplet danych do odtworzenia bramy rozpoznawalnej dla gracza z Białegostoku (decyzja D60, region Dojlidy).
**Gałąź:** `research/mistral-p19-hospital-gate` (od najnowszego origin/main). **Data:** 2026-11-13. **Język:** polski.

---

## 1. Cel
Ustalić z OSM/BDOT10k dokładne położenie wjazdu na teren szpitala przy ul. Żurawiej 14 (Dojlidy, Białystok) wraz z identyfikatorami obiektów, a z kadrów (Commons; Panoramax/KartaView/Openverse — patrz sekcja metody) odczytać: mur (materiał, wysokość, tablice), słupy bramy z daszkami, szlaban, znaki (B-20, B-33 „20”, C-2, prawdopodobny B-2) z wysokościami zamocowania wg Dz.U. 2019 poz. 2311, tablicę izby przyjęć, nawierzchnię przed bramą i tło za bramą — w konwencji statusów SOURCED/ESTIMATED/UNVERIFIED/REJECTED (zgodnie z research/mistral/p6-dojlidy-gates).

## 2. Metoda
- **OSM (ODbL):** eksport API 0.6 `map?bbox=23.1870,53.1070,23.1950,53.1120` (2026-11-13); transformacja WGS84→EPSG:2180 własnym modułem TM/GRS80 (zwalidowany w P6/M49 na parach kontrolnych, Δ<0,5 m); układ lokalny: środek bramy = (0,0), oś X = wschód, oś Z = północ.
- **Kadry:** Wikimedia Commons (geosearch + kategorie + katalog Rakoon); każdy kadr pobrany przez `commons.wikimedia.org/w/thumb.php` (JPG ≤1600 px) i **OBEJRZANY** analizą obrazu (pytania tematyczne, po kilka na kadr kluczowy); liczby z wizji traktowane wyłącznie jakościowo — wymiar wymaga kotwicy (krawężnik 0,15 m, płyta chodnikowa 0,5 m, wzrost człowieka ~1,7 m, wymiary znaków z Dz.U.) lub ≥2 niezależnych odczytów (lekcja P6: wizja niepowtarzalna liczbowo). Każdy wymiar: ESTIMATED z jawną metodą albo SOURCED z dokumentem (cytat + strona).
- **Rozporządzenie o znakach:** Dz.U. 2019 poz. 2311 (ELI), tekst + załączniki z eli.gov.pl (PDF), ekstrakcja tekstu własnym parserem; cytaty ze stronami w manifest.csv.
- **Ortofotomapa:** GUGiK WCS `Orthoimagery_High_Resolution` (nalot 2025 wg skorowidza WFS, GSD 0,05 m) — wycinki 120×120 m i 80×80 m wokół bramy (PNG do analizy programowej + JPG); klasyfikacja pikselowa okazała się mało miarodajna (niski kontrast nalotu — asfalt/trawnik różnią się minimalnie), więc orto służy jako potwierdzenie jakościowe (droga wewnętrzna, chodnik/krawężnik wzdłuż ulicy, brak widocznej kreski szlabanu).
- **Źródła niestosowane:** Google Maps/Street View/Earth/3D Tiles — ZAKAZ (D43), nieużyte. Mapillary — brak tokenu, nie sondowano. Panoramax — 0 wyników w bbox (API panoramax, sprawdzone). KartaView — 0 zdjęć w promieniu 5 km (kontrola pozytywna: API działa, zwraca dane w innych lokalizacjach). Openverse — API niedostępne z sesji (HTTP 504, następnie challenge Cloudflare) — 0 kadrów. BDOT10k/WFS wysokości — odcinki/pakiety PZGIK poza zasięgiem sesji (patrz sekcja 9).
- **Licencje:** CC0 (Rakoon, 20 kadrów), CC BY 3.0 pl (Podlaski Urząd Wojewódzki — szpital tymczasowy, 6 kadrów, „referencja, nie tekstura” z atrybucją), ODbL (OSM), otwarte dane (GUGiK), dokument urzędowy (Dz.U.). Nazwy marek/instytucji z tablic NIE trafiają do opisów odtwarzanych w grze — zapisane jako „napis instytucji, nie odtwarzamy”.

## 3. Położenie wjazdu (OSM, STAN 2026-11-13)

| Obiekt | Identyfikator OSM | Ustalenie |
|---|---|---|
| **Brama (szlaban)** | **node 2448457849** (barrier=lift_gate, foot=yes, fee=yes, payment:coins=yes) | **środek bramy: 53.109457, 23.190647** (WGS84, 6 miejsc); EPSG:2180 E=780370,119 N=590887,441 |
| Azymut osi wjazdu | way 73881452 + 883955523 | **62,3°** (Żurawia→brama 62,8°; brama→szpital 62,1°) |
| Droga dojazdowa | way 73881452 (service) | node 874174701 (na Żurawiej) → szlaban; 8,4 m |
| Droga za bramą | way 883955523 (service) | szlaban → node 3323248759 → node 874174759; 16,4 m; dalej parking 276840492 (diagonal, 20,4 m) |
| Obrys szpitala | **way 239477156** (amenity=hospital, Żurawia 14, loc_name „Szpital Zakaźny”, operator: Uniwersytet Medyczny) | przechodzi przez node bramy |
| Budynek przy bramie | **way 296211509** (name=Portiernia) | narożnik przy bramie node 3000014175 (+0,68 E, +3,52 N); node 3000014181 łączy portiernię z ogrodzeniem 883955508; w ścianie skrzynka pocztowa (node 10202945270) |
| Ogrodzenie od południa | **way 883955509** (barrier=fence) | biegnie wzdłuż granicy działki; **kończy się przy bramie** — node 8220895799 (+1,42 E, −3,02 N); w OSM brak odcinka ogrodzenia/muru między tym węzłem a osią bramy |
| Ogrodzenie od portierni na północ | way 883955508 (barrier=fence) | od narożnika portierni (node 3000014181) na północ |
| Ulica | way 73881451 (Żurawia, unclassified, surface=paved, **hgv=no, maxweight=3,5**) | oś jezdni ~16,4 m na S/SW od bramy; dojazd = jedyny wlot na teren szpitala od Żurawiej przy tej bramie |
| Budynek główny za bramą | way 236884780 (building=hospital, name=A) | najbliższy punkt 43,9 m od bramy |
| Inne przy dojeździe | node 3323248741 (barrier=gate, access=private, 32,8 m E — bramka piesza); node 14123795058 (highway=traffic_mirror, 14,2 m E) | |
| **Mur (barrier=wall) przy bramie** | **BRAK w OSM** | ways wall 1552407068/69/70 leżą ~120 m na południe (szpital tymczasowy) — NIE są murem bramy; mur z cegły potwierdzony kadrami (sekcja 5) = luka w OSM |

**Szerokość światła wjazdu: 6,6 m** (cięciwa: koniec ogrodzenia node 8220895799 → narożnik portierni node 3000014175 = 6,58 m; metoda jak P6 G07/G08, SOURCED z geometrii OSM); odczyt drugi — rzut na kierunek prostopadły do osi wjazdu: **6,1 m**. Odczyt wizyjny „3–4 m” odrzucony (niepowtarzalność modelu wizyjnego — lekcja P6). Wjazd jednokierunkowy, z szlabanem.

## 4. Kadry — inwentarz oględzin (kryterium „kadry bramy”: patrz sekcja 10)

Wszystkie kadry pobrane (JPG ≤1600 px, files/ w archiwum ZIP — patrz sekcja 11) i **obejrzane** 2026-11-13 (analiza obrazu, pytania tematyczne). Pozycje z EXIF/API Commons; kierunek deg — UNVERIFIED (Commons nie udostępnia GPSImgDirection).

| Kadr | Plik (Commons) | Pozycja kamery | Odległość od bramy | Data / sezon | Licencja | Co widać (1 zdanie) | Rola |
|---|---|---|---|---|---|---|---|
| **F01 = P11-129** | 6739 Uniwersytecki Szpital Kliniczny… November 2019 | 53.109464, 23.190654 | **0,9 m** | 2019-11-10, jesień | CC0 (Rakoon) | brama od frontu: dwa ceglane słupy z płaskimi daszkami, szlaban biało-czerwony opuszczony, ceglany mur z tablicami, zestaw znaków (STOP, „20”, nakaz w prawo) twarzą do kamery, tablica izby przyjęć na słupie, asfalt z łatami, portiernia w kadrze, drzewa bez liści | **kadr referencyjny** — 6 niezależnych odczytów tematycznych |
| F02 | 8858 November 2022 | 53.110204, 23.190304 | 86 m | 2022-11-03, jesień | CC0 | ulica Żurawia: jezdnia i chodnik, przystanek z wiatą, ogrodzenie terenu, latarnie | kontekst ulicy |
| F03 | 20230814 182338 August 2023 | (EXIF w archiwum) | ~83 m | 2023-08-14, lato | CC0 | ulica/przystanek, bramy szpitala brak | kontekst (odrzut bramy) |
| F04 | 20230814 181655 August 2023 | ~ | ~83 m | 2023-08-14, lato | CC0 | ulica/przystanek, bramy szpitala brak | kontekst |
| F05 | 20200726 084447 Białystok July 2020 | 53.109104, 23.191705 | 81 m | 2020-07-26, lato | CC0 | brama dwuskrzydłowa + mur ceglany po **południowej** stronie Żurawiej, za nimi bloki osiedlowe | **REJECTED dla bramy szpitala** (zła strona ulicy) |
| F06 | 8860 November 2022 | 53.109221, 23.191886 | 87 m | 2022-11-03, jesień | CC0 | zielona siatka ogrodzeniowa szpitala, budynek szpitala (białe ściany, ciemny dach), maszt antenowy | tło za bramą; ogrodzenie dalej od bramy |
| F07 | 20230814 180637 August 2023 | ~ | ~95 m | 2023-08-14, lato | CC0 | ulica/przystanek, bramy szpitala brak | kontekst |
| F08 | 8861 November 2022 | ~ | 119 m | 2022-11-03, jesień | CC0 | brama WORD (inny obiekt) ze znakiem STOP | odrzut (inny obiekt) |
| F09 | Szpital tymczasowy…01.png | — | — | 2020-12-10 | CC BY 3.0 pl | **REJECTED: PNG** (poza pipeline JPG); nie oglądnieto | odrzut |
| F10 | 20200726 084816 WORD | ~ | 132 m | 2020-07-26, lato | CC0 | WORD (inny obiekt) | odrzut |
| F11 | Szpital tymczasowy…03.jpg | — | ~120 m S | 2020-12-10, zima | CC BY 3.0 pl | wnętrze/konferencja szpitala tymczasowego | odrzut (nie brama) |
| F12 | 20221117 130338 | ~ | ~ | 2022-11-17, jesień | CC0 | ulica/osiedle, bramy szpitala brak | kontekst |
| F13 | 20221117 122654 | ~ | ~ | 2022-11-17, jesień | CC0 | ulica/osiedle | kontekst |
| F14 | 20200726 084417 Żurawia Street | 53.108217, 23.191792 | 158 m | 2020-07-26, lato | CC0 | ulica Żurawia wzdłuż, ogrodzenie terenu | kontekst ulicy |
| F15 | 8857 November 2022 | 53.110066, 23.188321 | 170 m | 2022-11-03, jesień | CC0 | front szpitala, **ogrodzenie z siatki metalowej**, dwa samochody przed budynkiem | ogrodzenie (nie mur przy bramie) |
| F16 | 20221117 122456 | 53.110134, 23.188270 | 176 m | 2022-11-17, jesień | CC0 | front szpitala/ulica | kontekst |
| F17 | Szpital tymczasowy…05.jpg | — | ~120 m S | 2020-12-10 | CC BY 3.0 pl | wnętrze szpitala tymczasowego, za oknem zima | odrzut |
| F18 | Szpital tymczasowy…06.jpg | — | ~120 m S | 2020-12-10 | CC BY 3.0 pl | konferencja/wnętrze | odrzut |
| F19 | 20200726 084355 ul. Żurawia | 53.107934, 23.191925 | 190 m | 2020-07-26, lato | CC0 | od południa: **mur ceglany po szpitalnej stronie ulicy (wysokość ~człowieka) z tablicami (czerwona z białym napisem, żółta z czarnym)**, brama, daszki na słupach widoczne, budynki szpitala (min. 4 kondygnacje, jasne) | **2. niezależny odczyt muru i tła** |
| F20 | 20221117 124435 | 53.110669, 23.187871 | 230 m | 2022-11-17, jesień | CC0 | ulica/ulica osiedlowa | kontekst |
| F21 | 20221117 124436 | 53.110793, 23.187706 | 247 m | 2022-11-17, jesień | CC0 | ulica osiedlowa | kontekst |
| F22 | Szpital tymczasowy…03.jpg | — | ~120 m S | 2020-12-10 | CC BY 3.0 pl | wnętrze szpitala tymczasowego | odrzut |
| F23 | Szpital tymczasowy…05.jpg | — | ~120 m S | 2020-12-10 | CC BY 3.0 pl | szpital tymczasowy (za oknem zima) | odrzut |
| F24 | Szpital tymczasowy…07.jpg | — | ~120 m S | 2020-12-10 | CC BY 3.0 pl | dwóch mężczyzn przed budynkiem szpitala tymczasowego (prasa, mikrofony) — elementów bramy szpitala brak | odrzut (tło niezwiązane z bramą) |

**Kadry „bramy” wg interpretacji zaakceptowanej przez właściciela (2026-11-13):** kadry, na których widoczna jest brama/front szpitala, z odległością jawnie w uwagach. Spełniają: **F01 (0,9 m), F06 (87 m, tło/ogrodzenie), F15 (170 m, front), F19 (190 m, mur z tablicami + brama z daleka)** — 4 kadry z 3 kierunków (front/przód, ukos z południa, front z północnego zachodu). Kadrów z odległości ≤40 m jest tylko F01 — niedobór wynika z braku materiału foto w dozwolonych źródłach (Commons jedyny; Panoramax/KartaView 0; Openverse niedostępne; Mapillary bez tokenu) — patrz sekcja 10 (luki).

## 5. Tabela elementów — element → wymiar → metoda → źródło → status

| Element | Wymiar/cecha | Metoda | Źródło | Status |
|---|---|---|---|---|
| Brama — środek | 53.109457, 23.190647 | node szlabanu | OSM node 2448457849 | SOURCED |
| Brama — szerokość światła | **6,6 m** (cięciwa) / 6,1 m (prostopadle) | cięciwa koniec ogrodzenia→narożnik portierni (jak P6 G07/G08) | OSM nodes 8220895799, 3000014175 | SOURCED |
| Brama — typ | szlaban jednostronny, ramię biało-czerwone | oględziny (2 niezależne odczyty) | F01 | ESTIMATED |
| Mur — materiał | cegła (ceramiczna, czerwono-brązowa) | oględziny (2 odczyty) | F01 | ESTIMATED |
| Mur — wysokość | **1,7–2,0 m** | kotwica: wzrost człowieka (F19) + relacja do znaku STOP (F01) — 2 niezależne odczyty | F01+F19 | ESTIMATED |
| Mur — nakrywa | płaska płyta | oględziny | F01 | ESTIMATED |
| Mur — tablice | **4** (prostokątne pionowe, czerwone tło; ≥2 potwierdzone niezależnie); wymiary UNVERIFIED | oględziny 2 kadrów | F01+F19 | ESTIMATED |
| Słup — materiał/przekrój | cegła / prostokątny; 2 szt. | oględziny (2 odczyty) | F01 | ESTIMATED |
| Słup — wysokość | UNVERIFIED (brak kotwicy; słup nieco ponad mur) | — | F01 | UNVERIFIED |
| Daszek — kształt/materiał | prostokątny, płaski; beton, szary | oględziny (3 odczyty) | F01+F19 | ESTIMATED |
| Daszek — wymiary | UNVERIFIED | — | — | UNVERIFIED |
| Znak B-20 | obecny; średnica 900/800 mm (duży/średni; tylko te rozmiary) | oględziny (3 odczyty) + tabela 3.1 (Dz.U. str. 92) + str. 91 (koło wpisane) | F01 + Dz.U. 2019 poz. 2311 | ESTIMATED (obecność) / SOURCED (wymiary) |
| Znak B-33 „20” | obecny, 20 km/h; średnice 900/800/600 mm | oględziny + tabela 3.1 | F01 + Dz.U. | ESTIMATED / SOURCED |
| Znak C-2 | obecny (strzałka w prawo, najwyżej w zestawie); wymiary kategorii C: 900/600/600 mm | oględziny + tabela 1.1 (Dz.U. str. 4) | F01 + Dz.U. | ESTIMATED / SOURCED |
| Znak B-2 (zakaz wjazdu) | obecność prawdopodobna — 2 odczyty wizyjne, symbol niejednoznaczny | oględziny | F01 | UNVERIFIED |
| Wysokości zamocowania znaków | min. 2,00 m (w obszarze zabudowanym, na słupkach; 2,20 przy chodniku) lub 0,90–1,20 m (na/za urządzeniami BRD); nad jezdnią min. 5,00 m; od krawędzi jezdni 0,50–2,00 m | tabela 1.11 (Dz.U. str. 32) + str. 26; dokładne wysokości tej instalacji UNVERIFIED | Dz.U. | SOURCED (zakresy) |
| Tablica izby przyjęć | prostokątna, biała z niebieskimi elementami, niepodświetlana, na słupie bramy; logo i napis instytucji — **nie odtwarzamy** | oględziny | F01 | ESTIMATED |
| Nawierzchnia dojazdu | asfalt z łatami; krawężnik betonowy niski (~0,15 m — kotwica standardowa), przejazd płytowy; chodnik przy bramie — nawierzchnia UNVERIFIED (odczyty wizyjne niespójne: płyty vs kostka; patrz sekcja 8) | oględziny + kotwice | F01 | ESTIMATED (dojazd/krawężnik) / UNVERIFIED (chodnik) |
| Nawierzchnia za bramą | asfalt (droga wewnętrzna/plac) | oględziny + orto 2025 | F01 + GUGiK | ESTIMATED |
| Tło — budynki szpitala | wielokondygnacyjne (min. 4), elewacja jasna/gładka, dachy płaskie/ciemne | oględziny 2 kadrów | F06+F19 | ESTIMATED |
| Tło — zieleń | drzewa liściaste przy murze (bez liści XI) | oględziny | F01+F05/F19 | ESTIMATED |

Pełne dane (w tym pola: pozycja kamery, kierunek, odległość, licencja, autor, status, uwagi): **manifest.csv** (63 wiersze P19-001…063).

## 6. Szkic sytuacyjny (układ lokalny: środek bramy = (0,0); X = wschód [m]; Z = północ [m])

Linia wjazdu: azymut **62,3°** — od jezdni Żurawiej (SW) na plac szpitala (NE). Światło wjazdu między słupami biegnie ~N–S (353°/173°).

```
        Z (północ)
        ↑
        |   portiernia (way 296211509) ── narożnik 3000014175 = słup N: (+0,7; +3,5)
        |        L-budynek: (−3,9;+1,2)…(−2,1;+15,8)
        |   [tablica izby przyjęć na słupie bramy — słup N lub S: UNVERIFIED]
   ─────┼──────■ szlaban (0,0), ramię wzdłuż światła (kierunek 353°) ──────────
        |          [daszki na obu słupach]
        |   słup S: (+1,4;−3,0) ← koniec ogrodzenia (way 883955509, node 8220895799)
        |      \
        |       \ mur ceglany z tablicami (kierunek SSE, wzdłuż granicy — jak fence w OSM)
        |        \  fence 883955509: (+2,2;−4,7) → (+3,5;−6,0) → (+5,8;−6,9) → (+8,7;−6,4) …
        |   [zestaw znaków: C-2 / B-20 / B-33-20 / (B-2?) — wspólny słupek,
        |    prawa strona wjazdu patrząc od ulicy (UNVERIFIED), 0,5–2,0 m od krawędzi jezdni]
        |   [lampa na słupie: 1 oprawa — UNVERIFIED]
        |   node 874174701 = skrzyżowanie z Żurawią (−7,5;−3,8); oś jezdni ~16 m S/SW
        |   przejazd przez krawężnik płytowy; chodnik przy bramie (nawierzchnia UNVERIFIED — patrz sekcja 8)
        → X (wschód)
```

Potwierdzenia elementów szkicu: słupy (F01 ×2 odczyty + F19 daszki z daleka), mur (F01 ×2 + F19), szlaban (F01 ×2 + node OSM), znaki (F01 ×3 odczyty), krawężnik/przejazd (F01 ×2), portiernia (F01 + way OSM), przebieg granicy (way 883955509 OSM + F01). Pozycje liczbowe z geometrii OSM (EPSG:2180); strona zestawu znaków i tablicy izby przyjęć — chirality odczytów wizyjnych niepewna → UNVERIFIED.

## 7. Wymiary znaków — załącznik 1 do rozporządzenia (Dz.U. 2019 poz. 2311)
- Tabela 1.1 „Podstawowe wymiary znaków kategorii A, B, C i D (wymiary podane w mm)” (Dz.U. str. 4, PDF str. 9): kategoria B (zakaz) średnica — duże 900, średnie 800, małe 600, mini 400; kategoria C (nakaz) długość podstawy — duże 900, średnie 600, małe 600, mini 400.
- Tabela 3.1 „Wymiary znaków zakazu i znaków uchylających zakaz (w mm)” (Dz.U. str. 92, PDF str. 97): „duże: d=900, s=90, g=135, p=90; średnie: d=800, s=80, g=120, p=80; małe: d=600, s=60, g=90, p=60; mini: d=400, s=40, g=60, p=40”; przypis: „(*) Nie dotyczy znaku B-20, który występuje tylko jako duży i średni.”
- B-20 (Dz.U. str. 91, PDF str. 96): „wymiary średnicy dla ośmiokątnego znaku B-20 odnoszą się do średnicy koła wpisanego w ten ośmiokąt. Znak ten nie występuje w grupie znaków wielkich, natomiast na drogach, na których stosuje się znaki z grupy małych, znak B-20 powinien mieć wymiar znaku średniego.”
- B-33 (Dz.U. str. 135, PDF str. 140): „Liczbę podaną na znaku wyraża prędkość w km/h; podaje się ją z dokładnością do 10 km/h.”
- C-2 (Dz.U. str. 154, PDF str. 159): „Znak C-2 «nakaz jazdy w prawo za znakiem» …stosuje się w celu wskazania kierującemu obowiązku skręcenia w prawo za znakiem.”
- Wysokości i odległości (tabela 1.11, Dz.U. str. 32, PDF str. 37; Dz.U. str. 26, PDF str. 31) — cytaty w manifest.csv (P19-038/039/047).

## 8. Samokontrola 20% (seed 20261113)
Losowanie: `random.Random(20261113).sample(wiersze_manifestu, ceil(0.2·63))` → **13 wierszy** (20,6%): P19-001, -002, -004, -005, -007, -009, -012, -024, -030, -033, -041, -054, -060. Dla każdego: ponowne otwarcie URL (HTTP 200 / ponowny eksport OSM API), ponowna weryfikacja cytatu/strony dokumentu (ekstrakt PDF), ponowne OBEJRZENIE kadru (analiza obrazu, pytania kontrolne) i porównanie ze zdaniem „co widać”.

**Wynik: 11 PASS, 1 PASS z upgrade (P19-060 latarnia: UNVERIFIED→ESTIMATED — 2. niezależny odczyt), 1 KOREKTA (P19-054 chodnik: ESTIMATED→UNVERIFIED — odczyty wizyjne niespójne co do materiału: „płyty” vs „kostka brukowa”; korekta zastosowana w manifest.csv i sekcjach 5–6), 0 błędów krytycznych.** Szczegóły: **audit_20_percent.json** (z poleceniem odtwarzającym losowanie).

## 9. Luki
- **≤1 kadr w promieniu 40 m** (tylko F01) — dozwolone źródła nie zawierają więcej kadrów bramy (Commons wyczerpane: geosearch + kategorie + katalog autora; Panoramax/KartaView: 0; Openverse: niedostępne; Mapillary: bez tokenu). Kryterium „≥12 kadrów ≤40 m" nieosiągalne — przyjęto interpretację właściciela (kadry z widoczną bramą/frontem, odległości jawnie; sekcja 4).
- **Wysokość słupa i wymiary daszka/tablic: UNVERIFIED** — brak kotwic skali na dostępnych kadrach; do pomiaru na miejscu (tyczka/szkic polowy).
- **Strona zestawu znaków (chirality): UNVERIFIED** — odczyty wizyjne nie rozstrzygają jednoznacznie lewej/prawej; pozycja słupka nie istnieje w OSM (brak node highway=traffic_sign).
- **Mur przy bramie nie istnieje w OSM** (fence kończy się 3 m przed osią bramy; brak barrier=wall) — do dodania w przyszłej edycji OSM; w grze mur odtwarzać z kadrów (sekcja 5).
- **Rytm przęseł/filarów muru: UNVERIFIED** — pojedynczy odczyt wizyjny, krótki widoczny odcinek.
- **Ortofotomapa 2025 ma niski kontrast** (asfalt/trawnik ledwie rozróżnialne) — pomiar pikselowy prześwitu niemożliwy; szerokość wjazdu z geometrii OSM (2 metody, sekcja 3).
- **BDOT10k/NMPT (wysokości budynków tła): nie pobrano** — usługi PZGIK dla Białegostoku nie odpowiadały w sesji (timeout WFS); wysokości tła z odczytów wizyjnych (kondygnacje) — do weryfikacji.
- **Znak B-2: obecność prawdopodobna, niepewna** — nie odtwarzać bez potwierdzenia na miejscu.
- **KartaView/Panoramax: 0 kadrów** — potwierdzone zapytaniami API (bbox/promień); kontrola pozytywna metodologii (API zwraca dane w innych lokalizacjach).

## 10. Zgodność z kryteriami akceptacji
- „≥12 obejrzanych kadrów bramy z ≥3 stron": **24 kadry obejrzane** (wszystkie pobrane z Commons), z tego kadry z widoczną bramą/frontem szpitala: **4** (F01, F06, F15, F19) z 3 kierunków; ≤40 m: tylko F01 — niedobór udokumentowany (sekcje 4, 9) i zaakceptowany przez właściciela (interpretacja 2026-11-13).
- „dla muru, słupa i daszka po ≥2 niezależne odczyty wymiaru": mur wysokość — 2 odczyty (F01, F19) ✓; słup — wymiar liczbowy UNVERIFIED (przekrój/materiał: 2 odczyty) — częściowo ✗ (sekcja 9); daszek — kształt/materiał: 3 odczyty, wymiar liczbowy UNVERIFIED — częściowo ✗.
- „wszystkie znaki z wysokością zamocowania": B-20, B-33, C-2 — SOURCED zakresy z Dz.U. (tabela 1.11) + relacje z kadru; dokładne wysokości tej instalacji UNVERIFIED (brak dalmierza na kadrach) — częściowo ✓.
- „środek bramy z OSM/BDOT z id": node 2448457849 (+ id dróg, portierni, obrysu, ogrodzeń) ✓.
- „brak wartości RGB z pikseli": ✓ (kolor wyłącznie opisowo).

## 11. Pliki i archiwum
Zdjęcia i wycinki poza gitem (`files/` w .gitignore): **ZIP `mistral-p19-hospital-gate-files.zip`** — nazwa, rozmiar i sha256 podane w opisie PR; archiwum zawiera: F01–F24 (JPG ≤1600 px), wycinki ortofotomapy (120×120 m JPG/PNG, 80×80 m PNG, kontekst 400 m JPG), eksport OSM (map.osm), skorowidz WFS, PDF-y Dz.U. 2019 poz. 2311, FILES.md ze skorowidzem i sumami kontrolnymi. Właściciel przekazuje archiwum liderowi.

## 12. Struktura
```
research/mistral/p19-hospital-gate/
├── README.md           (ten plik)
├── manifest.csv        (63 wiersze P19-001…063; UTF-8)
├── sources.md          (pełne URL-e źródeł + licencje + daty dostępu)
├── audit_20_percent.json (samokontrola 20%, seed 20261113)
├── .gitignore          (files/ + *.zip)
└── files/              (poza gitem — w archiwum ZIP; patrz sekcja 11)
```
