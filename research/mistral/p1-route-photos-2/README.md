# P1B — uzupełnienie luk paczki P1: zdjęcia tras (Białystok), wersja 2 po poprawkach M46-FIX

**Gałąź:** `research/mistral-p1-route-photos-2` (zrebasowana na najnowszy `main`; baza PR @ 16a7797b)
**Autor badania:** Vibe (Mistral) — paczka M46/P1B, poprawka M46-FIX
**Data poprawki:** 2026-11-13 (przegląd: `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p1b.md`)

Wersja 2 naprawia błędy wykryte w przeglądzie: systematycznie błędne przypisanie kadrów do ulic
(26 z 33 kadrów „OK” pokazywało inną ulicę niż w manifeście), opisy `punkt_opis` nieodpowiadające
treści zdjęć, fałszywe twierdzenie o braku manifestu P1 oraz zmyślonego autora „Hollyfeld”.
Zdjęcia NIE są w repo: katalog `files/` jest ignorowany (`.gitignore`); archiwum
**`mistral-p1-route-photos-2-files-v2.zip` (46 plików JPG ≤1600 px)** dostarczono poza git —
lokalizacja w opisie PR.

**Liczniki po poprawce: 48 wierszy = 32 OK / 10 ODRZUCONE / 4 DUPLIKAT_P1 / 2 REFERENCJA**
(w wersji 1 było 47 wierszy = 33 OK / 3 REFERENCJA / 11 ODRZUCONE; zmiany: P1B-016 OK→ODRZUCONE,
P1B-034/036/037 REFERENCJA→DUPLIKAT_P1, P1B-039–042 ODRZUCONE z poprawnym autorem, dodany P1B-048).

## 0. Ważne ustalenia (skorygowane w M46-FIX)
- **Manifest P1 ISTNIEJE w repo**: `research/gptpro/p1-route-photos/manifest.csv` (origin/main).
  W wersji 1 twierdzono błędnie, że nie istnieje, przez co nie wykonano deduplikacji z P1.
  Po porównaniu plików/URL: **P1B-034 = P1-004, P1B-036 = P1-033, P1B-037 = P1-052, P1B-042 = P1-053**
  — oznaczone statusem `DUPLIKAT_P1` (pozostają w manifeście dla kompletności źródłowej, nie wliczają się do pokrycia).
- **Autor P1B-037, 039–042 to Rakoon** (Commons API, CC0) — w wersji 1 podano błędnie „Hollyfeld”. Poprawione.
- **Panoramax: świeże wyszukiwanie 2026-11-13 — 186 obiektów w bbox (23.095–23.185 E, 53.135–53.172 N),
  żaden nie wypełnia luk** → kolumna `panoramax_id` pozostaje pusta.
- **Mapillary: pominięty — brak tokenu API (UNVERIFIED), nie zgadywano kluczy. Openverse: 0 wyników** (sources.md §4–5).
- **Google Maps / Street View / Earth / 3D Tiles: nie użyto w żadnym kroku.**

## 1. Reguła przypisania kadru do ulicy (nowa, obowiązująca w tej wersji)

Kadr należy do ulicy X **tylko wtedy, gdy**:
1. odległość punktu kadru do osi way X (OSM) ≤ **25 m**, ORAZ
2. **|azymut kamery − kierunek odcinka X| (mod 180°) ≤ 30°** (kamera patrzy wzdłuż osi ulicy).

Jeśli inna ulica jest **bliżej** (lub **lepiej współliniowa**), kadr przypisuje się do niej —
nawet jeśli obie ulice spełniają oba warunki. Kadry z przejazdu arterią, mijające wloty ulic
bocznych, przypisuje się do **arterii**, nie do bocznej ulicy (to był błąd główny wersji 1).

- **Kolumny nowe w `manifest.csv`**: `os_way_id` (id way OSM, do którego przypisano kadr)
  i `delta_azymutu_deg` (wartość warunku 2; dla Commons bez EXIF GPSImgDirection → `UNVERIFIED`,
  przypisanie wyłącznie po odległości).
- **Zastrzeżenie wysokości (2D)**: reguła jest płaska — ring ronda (way `junction=roundabout`)
  leży **pod estakadą Andersa**, więc kadr z estakady może formalnie spełniać kryteria dla osi
  ringu. W takich przypadkach rozstrzyga **weryfikacja obrazu** (patrz P1B-048 w §5).
- Geometria: odległość equirectangular (R=6371000) do lokalnego XY, punkt–odcinek z clampem t∈[0,1];
  ways z OSM API `map.json` (25 kafli; Overpass niedostępny — 502/timeout). Przykład: kandydat
  „ring ronda” dla P1B-013 (12,4 m, Δ 9,6°) odpada, bo estakada Andersa jest bliżej (5,6 m, Δ 0,6°).

**Wynik przeliczenia wszystkich wierszy:** P1B-001–003 → **Andersa** (przy wlocie Batorego; do Batorego
12–21 m i Δ~75° — poza regułą); P1B-006–009 → **wiadukt Al. Tysiąclecia, wszystkie jezdnia A**
(wersja 1 przypisywała 009 do jezdni B — fałsz: ta sama sekwencja KV 1155711 i azymut 142°);
P1B-010–015 → **estakada Andersa NAD rondem** (way 177895177, `bridge`; ringu nie widać na zdjęciach);
P1B-017–033 (+038) → **Aleja Tysiąclecia Państwa Polskiego** (kamera jedzie arterią i mija wloty
Bitwy/Białostoczek/Kombatantów/Sokólskiej/Motoszko/Wileńskiej/Skidelskiej; do „swoich” ulic Δ 61–90°).

## 2. Manifest
`manifest.csv` — **48 wierszy** (32 OK, 10 ODRZUCONE, 4 DUPLIKAT_P1, 2 REFERENCJA). Kolumny zgodne z P1
plus dwie nowe: `id, ulica, punkt_opis, lat, lon, kierunek_deg, os_way_id, delta_azymutu_deg,
data_zdjęcia, sezon, pora_dnia, panoramax_id, jakość_1_5, odrzucone_powód, url_źródła, licencja,
autor, data_dostępu, status, uwagi`.
- **Pozycje WGS84** z 6 miejscami po przecinku (KartaView 2.0 API / EXIF Commons) — zweryfikowane wobec API.
- **Kierunek_deg**: `heading` KartaView (azymut kamery) albo `UNVERIFIED` (Commons bez EXIF GPSImgDirection).
- **Punkt_opis przepisany po OBEJRZENIU każdego dostępnego JPG** (46/48 obejrzał model wizyjny w sesji
  poprawki; P1B-016 i P1B-043 mają obrazy trwale niedostępne — patrz §5). Opisy opisują to, co faktycznie
  widać (obiekt, skrzyżowanie, drogowskaz), a nie metadane.
- **Licencje**: KartaView = CC BY-SA 4.0 (referencja, nie tekstura; atrybucja w kolumnie `autor`);
  Commons = CC0. Żadnych licencji NC/ND.

## 3. Tabela pokrycia po poprawkach (ulica × kierunek × ujęcia × sezony)

### Luka 1 — ulice z zerem zdjęć (cel: ≥3 ujęcia, oba kierunki)
| Ulica | Ujęcia P1B | Status luki |
|---|---|---|
| Stefana Batorego | **0** (P1B-001–003 to kadry z **Andersa** przy wlocie Batorego — poprawione w M46-FIX) | **pozostaje** (0 kadrów ze wszystkich źródeł) |
| Brzeska | 0 | **pozostaje** (0 kadrów we wszystkich źródłach ≤60 m) |
| Buska | 0 | **pozostaje** (0 kadrów, jw.) |
| Olsztyńska | 2 (Commons, poziom drogi: P1B-004 śnieg jakość 3; P1B-005 bez liści jakość 2 — silne rozmycie ruchu) | **częściowo** — 2/3 ujęcia, jeden punkt, brak azymutu, nie z fotela kierowcy |

### Luka 2 — drugi sezon
| Obiekt | Ujęcia P1B | Status luki |
|---|---|---|
| Wiadukt Al. Tysiąclecia nad torami | 4 (P1B-006–009, kierowca, **bez liści 2018-03-23**); **wszystkie jezdnia A** — jezdnia B: brak | **częściowo WYPEŁNIONE**; UWAGA: kadry sprzed przebudowy 2021/22 — geometria tak, oznakowanie/zieleń mogą być nieaktualne |
| Grodzieńska, Kowieńska, Wołkowyska, Świsłocka, Lidzka | 0 wypełniających (kandydaci KV 2018-03 i Commons 2024-04 — oba „bez liści”; P1B-039–042 w manifeście jako ODRZUCONE/DUPLIKAT_P1) | **pozostaje** — brak liści/śniegu we wszystkich dozwolonych źródłach |
| Wiadukty Maczka nad torami (A/B) | 0 bezlistnych (P1B-045: 2019-08, liście) | **pozostaje** |
| Mosty Maczka nad Białą (A/B) | 0 bezlistnych (P1B-044: 2021-06, liście; P1B-043: obraz trwale niedostępny) | **pozostaje** |
| Łącznica DK8 (węzeł Andersa/Maczka) | 0 bezlistnych (P1B-046: 2019-08, liście) | **pozostaje** |

### Luka 3 — Rondo Pamięci Bieżeństwa 1915 r. (sloty przedefiniowane wg OSM)
W OSM **ring ronda (`junction=roundabout`) leży pod estakadą Andersa** (way 177895177, `bridge`);
ruch z rondem obsługuje się łącznicami Andersa (SE/NW) i ramieniem Bitwy Białostockiej.
Kadry P1B-010–015 (azymuty 301–303°) to jazda **estakadą NAD rondem** — ringu nie widać na żadnym z nich
(w wersji 1 opisywano je fałszywie jako wloty/wyloty ronda, m.in. „na krawędzi ringu”).

| Slot (wg OSM) | Kadry | Status |
|---|---|---|
| Ring ronda (jezdnia `junction=roundabout`) | 0 z poziomu kierowcy | **pozostaje** (z poziomu pieszego: Commons CC0 — P1-002/P1-004 już w paczce P1; P1B-034 = duplikat P1-004) |
| Wjazd z łącznicy Andersa (SE) | 0 | **pozostaje** (kadry TMishaaa/gpsmapper999 są na estakadzie, nie na łącznicy) |
| Wjazd z łącznicy Andersa (NW) | 0 | **pozostaje** |
| Wjazd z Bitwy Białostockiej | 0 | **pozostaje** (kadry telenavdrives 2018 są na Al. Tysiąclecia, nie na ramieniu Bitwy) |
| Referencja z estakady (2016) | P1B-048 (KV 7119871, ziozzzzz) | **REFERENCJA** — geometrycznie 9,6 m od osi ringu (Δ 29,1°), ale obraz pokazuje estakadę/łącznicę; geometria tak, oznakowanie 2016 może być nieaktualne |

**Wniosek: rondo = 0 slotów z poziomu kierowcy** mimo że 2D-reguła formalnie wskazuje ring dla
2 kadrów KV (7119871/7119872) — oba wizualnie są z estakady/łącznicy.

### Luka 4 — poziom kierowcy dla ulic z kadrami tylko pieszymi (cel: ≥2 kadry z jezdni z azymutem)
| Ulica | Kadry P1B z poziomu kierowcy | Status |
|---|---|---|
| Bitwy Białostockiej, Białostoczek, Kombatantów, Michała Motoszko, Wileńska, Sokólska, Skidelska | **0/7** — 17 kadrów z wersji 1 to w rzeczywistości **Al. Tysiąclecia** (kamera jedzie arterią, mijając wloty; Δ do „swoich” ulic 61–90°) | **pozostaje** |
| Władysława Bełzy | 0 (P1B-036 = duplikat P1-033, poziom pieszy) | **pozostaje** |
| Sitarska | 0 (P1B-035 = fragment elewacji budynku, bez perspektywy ulicy) | **pozostaje** |

**Wniosek: luka 4 = 0/9 ulic wypełnionych.**

## 4. Luki pozostałe (podsumowanie z dowodami, wyszukiwanie świeże 2026-11-13)
1. **Batorego, Brzeska, Buska**: 0 kadrów — KartaView: 50 zapytań `nearby-photos` wokół punktów celów,
   **554 unikalne kadrów**, żaden ≤25 m od osi z azymutem wzdłuż osi; Panoramax 186 obiektów w bbox — 0;
   Commons: 586 plików z geolokalizacją ≤1000 m od punktów celów — 0 ≤25 m od tych osi.
2. **Olsztyńska**: tylko 2 kadry Commons (XII 2022, CC0, poziom drogi, bez azymutu; 005 silnie rozmyty → jakość 2).
3. **9 ulic luki 4** (jw.): 0 kadrów z poziomu kierowcy; dostępny materiał KV to wyłącznie przejazdy
   Al. Tysiąclecia (2018-03), Andersa (2019/2021) i estakadą nad rondem (2016/2019/2021).
4. **Grodzieńska, Kowieńska, Wołkowyska, Świsłocka, Lidzka**: brak kadrów z liśćmi/śniegiem (KV tylko
   2018-03 bez liści; Commons 2024-04 przed rozwojem liści).
5. **Wiadukty Maczka, mosty Maczka, łącznica DK8**: brak kadrów bezlistnych (2016-08/10, 2019-08, 2021-06 — liście).
6. **Rondo**: 0 slotów z poziomu kierowcy (patrz §3 Luka 3); pełna analiza pozycja+azymut kadrów KV
   ≤250 m od ronda: azymuty wyłącznie 298–359° (jazda Andersa/estakadą), żaden wzdłuż łącznic czy Bitwy.
7. **Sitarska, Bełzy**: brak kadrów poziomu kierowcy (Commons wyłącznie piesze; KV 0 kadrów ≤25 m).
8. **Commons łącznie**: z 586 plików z geolokalizacją w promieniu ≤1000 m od punktów celów, ≤25 m od osi
   leży 5 (Sitarska ×3 — w tym plik P1B-035; rondo ×2 na poziomie pieszym — P1-002 z paczki P1 i plik
   sąsiedni); **0 plików z poziomu kierowca/azymutem** dla luk.

## 5. 10 najlepszych kadrów P1B (do kamer kontrolnych; przypisanie poprawione, kadry obejrzane)
| # | id | obiekt (faktyczny, z obrazu) | lat, lon | azymut | sesja / sezon |
|---|---|---|---|---|---|
| 1 | P1B-007 | wiadukt Al. Tysiąclecia nad torami, jezdnia A | 53.164496, 23.150108 | 142° | telenavdrives 2018-03-23, bez liści |
| 2 | P1B-020 | Al. Tysiąclecia — przejazd pod łukowym wiaduktem kolejowym z 1955 r. | 53.142129, 23.157632 | 165° | 2018-03-23, bez liści |
| 3 | P1B-019 | Al. Tysiąclecia — dojazd do wiaduktu 1955, drogowskazy „Centrum / 676 Supraśl” | 53.142291, 23.157583 | 177° | 2018-03-23, bez liści |
| 4 | P1B-027 | Al. Tysiąclecia × Sokólska/Kombatantów (sygnalizacja, Circle K) | 53.150993, 23.154613 | 160° | 2018-03-23, bez liści |
| 5 | P1B-018 | Al. Tysiąclecia × Bitwy Białostockiej/Radzymińska (światła, budynek „MITEX”) | 53.145710, 23.157239 | 175° | 2018-03-23, bez liści |
| 6 | P1B-010 | estakada Andersa nad rondem Bieżeństwa (jezdnia, bariery; ringu nie widać) | 53.151587, 23.168466 | 303,17° | TMishaaa 2021-06-23, liście |
| 7 | P1B-003 | Andersa przy wlocie Batorego, drogowskazy DK19 Kuźnica / DK65 Ełk | 53.149631, 23.173610 | 301,47° | gpsmapper999 2019-08-25, liście |
| 8 | P1B-004 | Olsztyńska z poziomu jezdni, śnieg (Commons CC0) | 53.149151, 23.151119 | UNVERIFIED | 2022-12-03, śnieg |
| 9 | P1B-014 | estakada Andersa nad rondem (2019; żółty budynek z antenami w tle) | 53.151597, 23.168389 | 301,67° | gpsmapper999 2019-08-25, liście |
| 10 | P1B-017 | Al. Tysiąclecia — skrzyżowanie z wlotem Bitwy Białostockiej/Radzymińskiej (sygnalizacja) | 53.145598, 23.157250 | 176° | 2018-03-23, bez liści |

Kadry Al. Tysiąclecia i Andersa z wersji 1 **pozostają w zbiorze jako OK pod poprawną nazwą ulicy** —
są cenne (zima 2018, łukowy wiadukt kolejowy z 1955 r., estakada nad rondem), tylko ich przypisanie
i opisy były fałszywe. Kadry Al. Tysiąclecia 2018 są sprzed przebudowy 2021/22 — używać do geometrii
wiaduktów/skrzyżowań, nie do oznakowania i zieleni.

## 6. Kontrola jakości i ograniczenia
- **Weryfikacja obrazów (M46-FIX)**: **46 z 48** wierszy ma obraz obejrzany modelem wizyjnym w sesji
  poprawki (wszystkie dostępne pliki, w tym wszystkie DUPLIKAT_P1 i ODRZUCONE z dostępnym obrazem).
  **P1B-016** i **P1B-043**: obrazy trwale niedostępne (Azure `BlobNotFound` na CDN KartaView
  i storage1–5, sprawdzone wielokrotnie 2026-11-13) — P1B-016 dodatkowo nie spełnia reguły
  (Δ 55,6° > 30°) → ODRZUCONE; sąsiedni kadr P1B-048 dodano jako zastępczą referencję estakady.
- **P1B-005**: jakość 3→**2** (silne rozmycie ruchu — kadr boczny z okna jadącego pojazdu).
- **Selekcja**: 2023+ spełnione tylko częściowo (najnowsze kadry kierowcy: 2021-06, 2019-08, 2018-03;
  2022-12 i 2024-04 to serie piesze Commons). Wszystkie OK: dzień, bez dużych pojazdów zasłaniających;
  jakość 2–4/5.
- **Samokontrola 20% (nowa, M46-FIX)**: świeże losowanie z jawnym seedem **20261114** (LCG +
  Fisher-Yates), 10 z 48 wierszy = 20,8%: P1B-003, 005, 010, 013, 015, 019, 023, 034, 035, 038.
  Dla każdego: jedno zdanie „co widać” + nazwa ulicy z OSM + delta azymutu — **sprawdzano
  przypisanie do ulicy i treść obrazu**, nie tylko zgodność metadanych z API. Wynik: 10/10 PASS
  (w tym 4 wiersze z korektą M46-FIX potwierdzoną obrazem). Plik: `audit_20_percent.json`.
- **Wymogi formalne**: JPG ≤1600 px (KartaView lth 1280×720, Commons thumb 1280×720) ✓;
  pozycje 6 dp ✓; licencje komercyjne ✓ (CC BY-SA 4.0 = referencja z atrybucją; CC0 bez ograniczeń).

## 7. Struktura
```
research/mistral/p1-route-photos-2/
├── README.md            (ten plik, v2 po M46-FIX)
├── .gitignore           (ignoruje files/ i *.zip)
├── manifest.csv          (48 wierszy: 32 OK / 10 ODRZUCONE / 4 DUPLIKAT_P1 / 2 REFERENCJA; nowe kolumny os_way_id, delta_azymutu_deg)
├── sources.md           (źródła, licencje, metody, endpointy; v2)
├── audit_20_percent.json (samokontrola 20%, seed 20261114, przypisanie+treść obrazu)
└── files/               (NIE w repo — 46× JPG w ZIP v2 poza gitem)
```
