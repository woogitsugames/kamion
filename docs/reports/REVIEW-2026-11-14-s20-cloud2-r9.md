# Przegląd R9 next-region-ring (chmura #2, PR #66) — s20, 2026-11-14

**Werdykt: FIX (mały).** To, co pakiet zebrał, jest rzetelne:
- długości i tagi dróg głównych w OSM odtworzyłem z lokalnego PBF z dokładnością do 0,2 km;
- 6 z 6 sprawdzonych plików GUGiK ma rozmiar, datę lub kod HTTP zgodny z manifestem;
- 11 obejrzanych kadrów ma opisy zgodne z obrazem.

Pakiet jest jednak **niekompletny w zakresie zadania** („OSM kompletność”). Brakuje dróg poniżej primary i budynków. Dane z Commons są błędne: zera to artefakt błędów 429. Do tego **7 skryptów wysyła User-Agent z nazwą projektu** (`kamion-research/1.0`, `KamionResearch/1.0`). Zasada „UA tylko ogólny” pochodzi z bloku „Dokończenie” w CLOUD2-PROMPT, dodanego po zamknięciu R9 (`docs/owner/AGENT-RULES.md` jej nie ma). Nie jest to więc złamanie reguły w chwili pracy, ale **trzeba to poprawić przed każdym ponownym uruchomieniem**.

Brakujące liczby OSM i Commons policzyłem sam (§4). Autor może je wkleić jako pomiar recenzenta albo powtórzyć zapytanie. Blok FIX jest w §6.

- Gałąź `origin/research/cloud2-next-region-ring` @ `e2a3b671f`. `git diff --shortstat origin/main...`: 56 plików, +129 339, wszystkie w `research/cloud2/next-region-ring/` ✓.
- Manifest: 371 wierszy. Nic nie scalono, nic nie scommitowano, PR bez komentarza. Raport nie jest scommitowany.
- Brak wewnętrznej recenzji (`REVIEW.md`). Ten przegląd ją zastępuje.

## 1. Kompletność wg CLOUD2-PROMPT (R9)

| Wymóg | Wynik | Dowód |
|---|---|---|
| OSM: kompletność | **CZĘŚCIOWO** | motorway/trunk/primary ✓, obiekty (mosty, ekrany, MOP, latarnie) ✓. **Brak klas < primary i budynków** (przerwane po 10/16 kafli) → §4 |
| GUGiK: ortofoto (rok), NMT, BDOT10k, LoD | **TAK** | skorowidze WFS, HEAD plików; 6/6 zgodne (§3) |
| Zdjęcia: Commons / Panoramax / KartaView / Mapillary | **CZĘŚCIOWO** | Panoramax i KartaView ✓. **Commons 7/24, a zera są błędne** (§4). Mapillary pominięte (brak tokenu, uczciwie) |
| Punkty rozpoznawalne do bramki | **TAK** | 24 punkty z OSM id i oceną danych |
| Raport planistyczny | **TAK** | bbox 461 km² na siatce regionów, kolejność pozyskania (§10 README) |
| Samokontrola 20 % | **TAK** | `Random(20261114).sample(sorted(ids), 75)` daje ten sam zbiór ✓; 74/1 |
| Licencje, zakaz Google | **TAK** | CC BY-SA 4.0 z dopiskiem „referencja, nie tekstura”; GUGiK; ODbL. Nie ma Google/Bing/Apple/Yandex |
| UA bez nazw organizacji/repo (blok „Dokończenie”, dodany później) | **NIE** | `fetch.py`, `tools/audit.py`, `tools/commons_landmarks.py`, `tools/gugik_skorowidze.py`, `tools/kartaview_corridor.py`, `tools/ovp.py`, `tools/panoramax_search.py` |
| Tylko własny katalog | **TAK** | diff jak wyżej |

## 2. Co obejrzałem sam (11 kadrów + 1 wycinek 3×)

Pobrałem przez `fetch.py` z podmienionym UA na ogólny: 38/38, 24,9 MB, sha256 zgodne. Każdy kadr oglądałem osobno, ≤ 880 px.

| Kadr | Ocena opisu R9 |
|---|---|
| PX02 (S8, obiekt żółto-zielony w głębi, zielony i żółto-pomarańczowy ekran po lewej, pole po prawej) | ✓ |
| PX05 (wiadukt Podleśna: żółto-zielony dźwigar, podpora w pasie rozdziału, plac z białymi ciężarówkami) | ✓ (na ciężarówkach jest nazwa firmy, do gry się nie nadaje) |
| PX08 (ekran brązowo-oliwkowy z poziomymi przetłoczeniami, schodkowa krawędź, pylon reklamowy) | ✓ |
| PX14 (biały łuk z krzyżującymi się wieszakami, maszt, słup WN, rząd młodych drzew, niebieski billboard) | ✓ |
| PX17 + wycinek 3× (biały cokół betonowy, ciemne panele z pionowym żłobieniem, górna część przezroczysta na jasnozielonych słupach) | ✓ (perforacji w tej rozdzielczości nie da się rozstrzygnąć) |
| PX18 (2 niebieskie łuki, czerwona balustrada, zielony ekran z niebieskimi szybami na blokach betonowych, niebieski drogowskaz) | ✓ |
| PX20 (pod słońce, las, bramownica, dodatkowy pas z prawej) | ✓ (po korekcie z audytu) |
| PX26 (żółto-zielony wiadukt, bramownica, zielone lamele, niebiesko-biała hala) | ✓ |
| PX29 (wykop z gładkimi murami, zielony pas i balustrada na koronie, płaski wiadukt, pole wyłączone z ruchu po lewej) | ✓ |
| KV03 (mur oporowy z jaskrawozielonym oczepem, 2 kominy biało-czerwone, łuk w głębi) | ✓ |
| KV04 (wjazd na estakadę, 70 po obu stronach, tablica ze schematem ronda, ciężarówka z czerwoną kabiną) | ✓ |

Azymuty PX17–PX19: API podaje 59°, 58° i 49°, a kurs z toru 5°, 6° i 358°. R9 sam pokazuje tę rozbieżność w kolumnie `kurs_z_toru_deg` ✓. Do kamer kontrolnych należy brać kurs z toru.

## 3. Liczby sprawdzone u źródła (12)

**OSM, drogi główne.** Lokalny `Data/raw/osm/podlaskie-261108.osm.pbf` (2026-11-08), przycięcie geometrii do bboxu R9 w EPSG:2180, długość po obu jezdniach. Skrypt recenzenta (pyosmium + shapely, `uv run --project tools/worldgen`) jest poza repo, metoda jest opisana tutaj.

| klasa | R9 km (Overpass 11-14) | recenzent km | lanes / maxspeed / surface / lit % R9 → recenzent |
|---|---|---|---|
| motorway | 19,25 | 19,29 | 100/100/100/0 → 100/100/100/0 ✓ |
| trunk | 80,79 | 80,88 | 96,3/95,8/96,6/16,8 → 96,3/95,8/96,6/16,8 ✓ |
| trunk_link | 15,28 | 15,28 | ✓ |
| primary | 39,05 | 38,89 | 99,8/90,4/97,9/44,8 → 99,8/90,3/97,9/45,0 ✓ |
| primary_link / motorway_link | 8,14 / 4,56 | 8,14 / 4,56 | ✓ |

**GUGiK, HEAD z 2026-11-14:**

| Wiersz | R9 | Recenzent |
|---|---|---|
| R9-212/213 BDOT10k `2002_GPKG.zip` | 90,3 MB, Last-Modified Sat, 03 Oct 2026 00:52:51 | 90 330 053 B, ta sama data ✓ |
| R9-215 LoD1 2024 `2002.zip` | 23,9 MB | 23 868 560 B ✓ |
| R9-219 LoD2 `2002_gml.zip` | 34,1 MB | 34 064 429 B ✓ (Last-Modified 2018-11-14) |
| R9-220 Drzewa3D LoD1 2023 `2002.zip` | 45,77 GB | 45 767 823 237 B ✓ |
| R9-221 LoD1 2025 `2002.zip` | 404 | 404 ✓ |
| LoD1 2024 `2061.zip` | 12,8 MB | 12 781 738 B ✓ |

## 4. Luki uzupełnione przez recenzenta (do wklejenia jako ESTIMATED, pomiar recenzenta)

**Drogi poniżej primary.** Ten sam PBF, bbox i metoda co w §3. Tagi w % długości:

| klasa | km | lanes | maxspeed | surface | name | lit | sidewalk | width |
|---|---|---|---|---|---|---|---|---|
| secondary | 148,0 | 97,1 | 72,0 | 87,7 | 84,5 | 34,9 | 4,1 | 0,2 |
| tertiary | 252,1 | 43,5 | 36,6 | 89,6 | 76,6 | 18,4 | 6,2 | 0,1 |
| unclassified | 189,5 | 9,6 | 12,3 | 89,2 | 43,0 | 4,0 | 1,8 | 0,0 |
| residential | 948,3 | 4,8 | 15,0 | 84,3 | 84,1 | 11,8 | 5,2 | 0,3 |
| living_street | 133,8 | 0,8 | 52,8 | 71,2 | 27,6 | 12,8 | 1,1 | 1,0 |
| service | 912,8 | 1,5 | 8,1 | 48,4 | 2,8 | 1,9 | 0,5 | 0,1 |
| track | 864,1 | — | 0,1 | 42,1 | 11,9 | 0,1 | — | 0,5 |

**Budynki.** Liczone tylko jako `way` z `building=*` i środkiem wierzchołków w bboxie. Relacji `building` w całym pliku jest 129, nie liczono ich.
- Liczba: **83 505**.
- `building:levels`: **22,9 %**; `height`: **0,3 %**.
- `building=` najczęściej: `yes` 55 426 · `house` 8 454 · `outbuilding` 7 393 · `detached` 2 021 · `apartments` 1 755 · `residential` 1 410 · `semidetached_house` 925 · `allotment_house` 663 · `retail` 525 · `terrace` 489 · `service` 463 · `industrial` 419.

**Commons geosearch** (promień 1 km, `gslimit=500`, 2026-11-14, UA ogólny):

| Punkt | R9 | Recenzent |
|---|---|---|
| L01 | 0 | **37** |
| L03 | 0 | **82** |
| L05 | 0 | **116** |
| L19 | — | 7 |
| L23 | — | 357 |

Zera R9 są artefaktem odpowiedzi z błędem (429/`error`). Te liczby oznaczają tylko pliki w promieniu, nie trafność do punktu. Pozostałych 17 punktów nie sprawdzałem.

## 5. Co R9 daje grze / planowi regionu (pliki, liczby)

| Temat | Wniosek | Działanie |
|---|---|---|
| Nazwa regionu i zakres | „Ring S8” nie istnieje. S8 kończy się na węźle Białystok Zachód, dalej jest DK8 trunk `8;65` / `8;19`, a S19 to `S19;65` (9,6 km) | w `docs/03`/HANDOVER nazywać „obrzeża: S8 Choroszcz–Białystok Zachód, S19, Trasa Generalska, DK8/19 N” |
| Pozyskanie GUGiK | powiat **2002**: BDOT10k 90 MB, LoD1 2024 24 MB, LoD2 2017 34 MB, NMT 1 m 2025 ≈ 4,4 GB (ESTIMATED), ortofoto 0,25 m 2024 jak w pipeline; **nie pobierać** Drzewa3D 2002 (45,8 GB) | geo-worldgen: `Data/SourceManifests/gugik-*-2002.json` na wzór 2061 |
| Wysokości budynków | OSM `height` 0,3 %, `building:levels` 22,9 % → wysokości z LoD1 2024 (96 708 budynków w paczce 2002) | jak w regionach C/Dojlidy (LoD1 jako źródło H) |
| Drogi niższe | `width` ≈ 0 % we wszystkich klasach. `lanes`: secondary 97 %, tertiary 44 %, residential 5 %. `lit` 2–35 % | szerokości i pasy z reguł `standards.py`; oświetlenie z `highway=street_lamp` (1891) |
| Ekrany akustyczne | `barrier=wall` + `wall=noise_barrier`: 27,8 km, 0 % `height`/`material`/`colour` | wygląd z kadrów (PX01, PX08, PX15, PX17, PX18): typy jak w §2 |
| Kadry referencyjne | Panoramax 2019 (sprzed S19), KartaView do 2021; S19 0–6 %, L19/L23 bez kadrów | Mapillary przez `tools/refs` (lider ma token) dla S19 i DW669; zdjęcia właściciela L02, L03, L19, L23 |
| Kamery kontrolne | azymut API PX17–19 odbiega o 50°+ | kurs z toru |

## 6. FIX — blok do wklejenia autorowi

```
R9 next-region-ring — FIX po przeglądzie lidera (REVIEW-2026-11-14-s20-cloud2-r9.md). Zmieniaj tylko
research/cloud2/next-region-ring/. Po poprawkach: build_manifest.py, audit.py (seed 20261114), README, PR.
F1 (P1, przed każdym ponownym uruchomieniem; zasada z bloku „Dokończenie” CLOUD2-PROMPT) User-Agent: w 7 plikach zamień "kamion-research/1.0" i "KamionResearch/1.0 (...)"
   na ogólny "research-fetch/1.0": fetch.py, tools/audit.py, tools/commons_landmarks.py,
   tools/gugik_skorowidze.py, tools/kartaview_corridor.py, tools/ovp.py, tools/panoramax_search.py.
   W sources.md dopisz: „do 2026-11-14 zapytania wysyłano z UA zawierającym nazwę projektu; poprawione”.
F2 (P1) Drogi < primary i budynki: dokończ Overpass (komenda z STATUS.md) ALBO wklej pomiar recenzenta
   jako ESTIMATED (metoda: PBF Geofabrik/podlaskie 2026-11-08, pyosmium, przycięcie do bboxu EPSG:2180,
   długość po jezdniach; budynki = way z building=*, środek wierzchołków w bboxie, relacji nie liczono):
   secondary 148,0 km (lanes 97,1 / maxspeed 72,0 / surface 87,7 / lit 34,9 / width 0,2 %);
   tertiary 252,1 (43,5 / 36,6 / 89,6 / 18,4 / 0,1); unclassified 189,5 (9,6 / 12,3 / 89,2 / 4,0 / 0,0);
   residential 948,3 (4,8 / 15,0 / 84,3 / 11,8 / 0,3); living_street 133,8; service 912,8; track 864,1.
   Budynki 83 505; building:levels 22,9 %; height 0,3 %. Jeśli wykonasz własne Overpass — podaj obie
   wersje i różnice (oczekiwane < 1 %, jak dla klas głównych: trunk 80,79 vs 80,88 km).
   Uzupełnij README §4 (tabela klas niższych + budynki) i §9 p. 1.
F3 (P1) Commons: zera L01/L03/L05 są błędne (recenzent 2026-11-14, r = 1 km: 37 / 82 / 116; L19 7;
   L23 357). W commons_landmarks.py sprawdzaj klucz "error" i kod 429, powtórz dla wszystkich 24 punktów,
   obejrzyj ≥ 1 plik na punkt bez kadru (L03, L19, L23) i dopisz licencję. Popraw README §6 i §9 p. 2.
F4 (P2) Opis PR: „4 z nich nie mają kadru” vs README §7: 3 (L03, L19, L23) — ujednolić.
```
(Uwaga recenzenta, bez poprawki: „TERYT 2010” i węzły Porosły/Księżyno/Dojlidy nie występują w CLOUD2-PROMPT
ani w repo. Pochodzą prawdopodobnie z rozpisania zadania przez sesję chmurową, którego nie widzę, więc ich
nie kwestionuję.)

## 7. Uwagi procesowe
- Brak `REVIEW.md` w katalogu pakietu. Ten przegląd go zastępuje.
- Raport jest przejrzysty i uczciwy co do luk (§9 README). Nie trzeba niczego cofać, wystarczy go dokończyć.
- Surowe wyniki Overpass zajmują 2,6 MB w gicie (`overpass/signs_furniture.json` ma 25 675 linii). To pochodna ODbL, dopuszczalna. Przy scaleniu można rozważyć przeniesienie ich do `files/`.
