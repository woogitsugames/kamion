# Przegląd wyników ChatGPT 6 Pro: G2 (next-regions) i G3 (s8-signs), s16, 2026-11-13

Przeglądający: agent geo-worldgen (tylko odczyt; worktree usunięte). Gałęzie: `origin/gptpro/2-next-regions`, `origin/gptpro/3-s8-signs`. Nic nie scalono ani nie zmieniono.

## Werdykty

| Zlecenie | Werdykt |
|---|---|
| G2 next-regions | **PRZYJĄĆ częściowo** (katalog celów i dowody dobre; rekomendacja kolejności kafli słabsza od katalogu) |
| G3 s8-signs | **PRZYJĄĆ** (z zastrzeżeniem licencyjnym CC BY-SA dla wycinków zdjęć) |

## 1. Format

- G2: README.md, manifest.csv (81 wierszy: 57 miejsc, 9 obrazów, 7 dokumentów, 5 kafli, 3 opracowania), sources.md (216 URL), files/ (38 plików). Wszystkie wymagane kolumny są (id, url_źródła, licencja, autor, data_dostępu, status, kolumny G2 i dodatkowe statusy). Zgodne.
- G3: README.md, manifest.csv (152 wiersze, kolumny wymagane plus ok. 25 dodatkowych), sources.md, files/ (172 pliki: 144 wycinki JPG do 1600 px, metadane, pliki OSM, PDF), osm_destination.csv (187 obiektów OSM), records.json, audit_20_percent.json, validation.json, LICENSE-DATA.md, asset_manifest.csv (SHA-256). Zgodne i ponad wymagania.
- Drobiazg G3: identyfikatory niejednolite (`G3-P001`, `G3-MLY-S8-010`, `MN009`, `MX002` bez prefiksu G3-). `id` i `mapillary_key` importować jako tekst.
- Samokontrola 20 % opisana w obu (G3: 31/152 = 20,4 %, jawny seed; G2: G2-Q01.json).

## 2. Licencje

Brak plików NC/ND/Google (grep po sources/manifest/README: słowo Google występuje wyłącznie w zdaniach "nie użyto"). Brak plików do usunięcia ze względu na zakaz. Ryzyka:

- G3, wycinki Mapillary (113 rekordów CC BY-SA 4.0): zgodne ze zleceniem, ale share-alike. Wycinek zdjęcia użyty jako tekstura znaku w grze byłby utworem zależnym na BY-SA. Zalecenie: używać wyłącznie odczytanej treści (fakty), tarcze rysować własne (tak już robi `overrides.yaml`: "our own schematic drawings"); wycinki trzymać jako referencję z atrybucją. 31 wycinków Commons (Rakoon) to CC0 (zweryfikowane live, 4/4).
- G3, `G3-MUN-001..008` (plan 2014 BPBK/Eutra i zdjęcia bez licencji): tylko link, nie pobrano. Poprawnie.
- G3 LICENSE-DATA.md: baza faktograficzna na ODbL 1.0. Dopisać do `docs/LICENSES.md` (atrybucja OSM, Mapillary, autorzy) i do ekranu licencji w grze.
- G2: `G2-D01.geojson` (2,6 MB, wycinek OSM) ODbL; `G2-A01..A09` ortofoto GUGiK (otwarte dane PZGIK, komercyjnie OK); D02/D03/D04/D05/D06/D09 dokumenty urzędowe (art. 4). `G2-D07.pdf` (ogłoszenie Poczty Polskiej SA na TED): Poczta Polska to spółka, uznanie za materiał urzędowy jest dyskusyjne. Niskie ryzyko, ale pominąć (jest link).
- G2: 29 rekordów "brak jawnej licencji, tylko referencja" faktycznie nie ma plików. Poprawnie.

## 3. Prawdziwość: wyniki próby

**G2** (13 losowych miejsc z 57 = 23 %, seed 1613: WL03, RS14, IC05, WL06, RS05, IC11, RS07, WL05, RT02, RS16, RT03, IC09, IC03):
- OSM (API): 12/12 obiektów istnieje, nazwa/typ zgodne z manifestem, punkt 4-101 m od centroidu geometrii (największe: Pronar stacja 101 m, BIAWAR 68 m; oba opisane jako punkty orientacyjne). Błędnych 0.
- RS16 (waga WIM Zabłudowska): jawnie UNVERIFIED bez współrzędnych; uczciwe, niesprawdzalne.
- Źródła WWW: GEODIS Żółtki 204 potwierdzone. Panattoni (403), Biazet (błąd certyfikatu), TED 213042-2026 (PDF nieczytelny dla narzędzia): niesprawdzone. S19 Krynice-Białystok Zachód: otwarcie jesienią 2026 potwierdzone, dokładnej daty 20.10.2026 nie znalazłem. MOP Haćki leży na S19 (nie S8; README to podaje), daty 29.10.2026 nie znalazłem.
- Razem G2: 13 OK / 0 błędnych / 6 niesprawdzalnych (RS16 plus 5 źródeł WWW). Zmyśleń nie stwierdzono.
- Mapa G2-D08.png obejrzana: podkład OSM, kafle 2000x2000 m w EPSG:2180; T01 (774971-776971) przylega od zachodu do bboxu obecnego regionu (776971-779019 x 595199-597247). Geometria zgodna.

**G3** (moja próba niezależna od audytu autora):
- Wzrokowo 6 kadrów vs manifest (P001 jako P001-P004, P009, P010, P015, MN009, MLY-S8-010): 6/6 OK co do litery, kartuszy i strzałek (w tym "Kuźnica B.", "Kowno (Kaunas) LT", żółty 675).
- Commons live (API): 4/4 (licencja CC0, współrzędne i czas EXIF identyczne: C005, C006, C007, C012).
- OSM live: 8/8 losowych z osm_destination.csv (wersja i tagi destination/destination:ref identyczne).
- Mapillary: API wymaga tokenu, nie sprawdzałem bezpośrednio. Klucze 1783751488818497 i 1911352299378570 (kino 2024-07-26) w `overrides.yaml` gry to te same zdjęcia, z których pochodzi G3.
- Razem G3: 18 OK / 0 błędnych / 0 niesprawdzalnych w próbie (Mapillary tylko pośrednio). Pozycje oznaczone przez autora UNVERIFIED (np. zaklejony P020) są uczciwie oznaczone.

## 4. Użyteczność

**G3, porównanie z grą** (`Data/Regions/bialystok-industrial-c/overrides.yaml`, `landmarks.py`; w `signs_route.py` nie ma tekstów, treści pochodzą z overrides i z tagów OSM destination):
- Bramownica Putry potwierdzona: cztery panele (P001-P004, Mapillary 465521806237924, kino, 2024-07-26): lewy górny `8 E67 Warszawa / 65 Ełk` strzałka w górę; lewy dolny `675 Centrum` w lewo; prawy górny jak lewy górny; prawy dolny `8 E67 Augustów / 19 Kuźnica PL BY` w prawo. Zgodne z `andersa-putry-portal-p40`.
- Rozbieżność: portal `andersa-gantry` w grze ma tablicę pasa 2 jako jedną (`Augustów / Kuźnica / Centrum`, kadr 2020, G3-P015 to potwierdza dla 2020). Zdjęcia 2024 mają Centrum osobno. To różnica epok, nie błąd G3. Decyzja: wybrać rok odniesienia (rekomendacja 2024) i ujednolicić oba portale.
- Nowe treści, jeszcze nieobecne w grze: E-1 od północy przed rondem `675 Centrum | 65 Bobrowniki PL BY | Kuźnica B. PL BY | Lublin | 8 E67 Warszawa | 65 Ełk` z diagramem (P009); tablica zmiennej treści `CENTRUM PRZEZ: TYSIĄCLECIA P.P. 5 MIN | ŚWIĘTOKRZYSKĄ 7 MIN` (P010); `65 Bobrowniki PL BY | 19 Lublin` (P015, 2020); E-14 na DK8 na północ `8 E67 | Suchowola 42 | Augustów 80 | Suwałki 119 | Kowno (Kaunas) LT 236` (MN009); przeddrogowskaz S8 `S8 Warszawa | Tykocin Złotoria | 500 m` z ograniczeniem 60 (MLY-S8-010).
- Dla generatora: `numery_dróg` (JSON numer/tło/litery), `strzałki`, `grupa_tablic`, `pole_tablicy` pozwalają zbudować board-spec 1:1; osm_destination.csv uzupełnia ścieżkę `from_osm`.
- README G3 koryguje punkt ze zlecenia (53,152 N 23,168 E leży na innym odcinku Andersa).
- Zasięg: 2017-2026, głównie 2024 (83/152); tylko 3 zdjęcia 2026. To nie jest inwentaryzacja aktualna na 11.2026 (autor to zaznacza).

**G2:**
- Katalog (57 miejsc) dobrze udokumentowany i uczciwy co do UNVERIFIED (28 TAK / 28 UNVERIFIED / 1 NIE). Rozdzielenie adres/brama/punkt OSM, zaktualizowane adresy firm (Raben Żółtki 201, GEODIS Żółtki 204 itd.) i lista MOP z oficjalnego wykazu GDDKiA (530 stanowisk w 10 obiektach) są użyteczne od razu.
- Rekomendacja kafli słabsza od katalogu: kafel 1 (Maczka-Kleeberga) ma 0 celów (uczciwie, jako korytarz), kafle 2-5 razem 11 celów, w tym 5 TAK. Autor sam nazywa Dojlidy/Krywlany "bardzo mocnym następnym skupieniem" (browar i BIAFORM mają TAK), a nie proponuje tam kafla. Dane ruchu (SDRR 2025) dotyczą odcinków S8, nie kafli. Rekomendację traktować jako opcję do decyzji lidera/właściciela.
- Wszystkie 5 kafli leży na zachód od obecnego regionu.

## 5. Rozmiar i scalanie

Rozmiary: G2 `research/` 13 MB, G3 9,5 MB. Obie gałęzie zawierają cały snapshot repo; do scalenia brać tylko `research/gptpro/...`.

**Scalić:**
- G3: całość `research/gptpro/3-s8-signs/` (9,5 MB).
- G2: README.md, manifest.csv, sources.md, `files/G2-A*.jpg` + JSON, `G2-T01..T05.geojson`, `G2-D01.json`, `G2-D02.json`, `G2-D03.xlsx`, `G2-D04..D06.pdf`, `G2-Q01.json`.

**Pominąć przy scaleniu (G2):**
- `files/G2-D08.png`: PNG, a `.gitattributes` wymaga LFS dla `*.png` (git zgłosił "should have been a pointer"). Skonwertować do JPG albo dodać przez LFS.
- `files/G2-D07.pdf` (Poczta Polska SA, licencja dyskusyjna; jest link).
- `files/G2-D09.pdf` (4,6 MB, wyciąg GPR; zbędny przy D02) i `G2-D02.xlsx` (450 kB) opcjonalnie.
- `files/G2-D01.geojson` (2,6 MB OSM) opcjonalnie; jeśli scalone, dodać atrybucję ODbL.

## 6. Pięć najważniejszych ustaleń

1. G3 potwierdza bramownicę Putry (4 panele, kino 2024-07-26) i zgadza się z `andersa-putry-portal-p40`; pierwszy portal w grze (stan 2020: Centrum razem z Augustów/Kuźnica) różni się od układu 2024 (Centrum osobno): ujednolicić.
2. G3 dostarcza gotowe nowe treści tablic (E-1 z diagramem od północy z "Kuźnica B.", ITS "CENTRUM PRZEZ", E-14 z kilometrami do Kowna, przeddrogowskaz S8 "Tykocin Złotoria 500 m"); próba 18/18, zero zmyśleń.
3. Licencje: brak NC/ND/Google; jedyne realne ryzyko to CC BY-SA wycinków Mapillary (113): używać treści, nie wycinków jako tekstur; dopisać do `docs/LICENSES.md`.
4. G2 katalog: 12/12 sprawdzonych obiektów OSM istnieje i zgadza się z manifestem; uczciwe UNVERIFIED dla WIM i naczepy 13,6 m; nowe adresy firm i oficjalna lista MOP użyteczne od razu.
5. G2 rekomendacja kafli (5 okien 2x2 km na zachód, pierwsze z 0 celów) geometrycznie przylega do obecnego regionu, ale pomija Dojlidy/Krywlany, które raport sam nazywa silniejszym skupiskiem; to opcja do decyzji. S19 nie tworzy ciągłej obwodnicy.

## 7. Ograniczenia przeglądu

Nie otwierałem Mapillary (wymaga tokenu) ani wszystkich stron firm (część dała 403/błąd certyfikatu). Trasy `dojazd_od_S8` nie były weryfikowane na grafie. Pomiary długości naczep z ortofoto (ESTIMATED, ±1 m wg autora) nie były powtarzane.
