# Przegląd PR #72 — M68 ściana lasu przy Krywlanach (cloud p25) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Paczka spełnia kryteria M68 i ma solidną część pomiarową. Sprawdziłem u źródła BDL, NMPT−NMT, OSM, licencje i regulamin BDL. Wszystko się zgadza. Obejrzałem 16 kadrów i 3 wycinki. Jeden opis kadru jest błędny (C68-213) i ten błąd wpływa na punkt 3 przepisu. Dwa wiersze zbiorcze są źle zestawione (K3, udziały gatunków). Żaden z tych błędów nie podważa danych. Errata w §5.

- Gałąź `origin/research/cloud-p25-krywlany-forest` (PR #72, otwarty), katalog `research/cloud/p25-krywlany-forest/`. `git diff --name-only origin/main...` zwraca 49 plików, **0 poza katalogiem paczki**.
- Kryteria wziąłem z bloku M68 w `docs/owner/MISTRAL-TASKS-10.md`, prefiks „cloud” wg `CLOUD-FABLE-PROMPT-S20.md`.
- Nic nie scalono, nic nie zacommitowano, PR bez komentarza. Raport nie jest zacommitowany.
- Zlecenie podaje ścieżkę recenzji 0170 `REVIEW-2026-11-14-s20-0170.md`. Taki plik nie istnieje. Właściwy to `docs/reports/REVIEW-2026-11-13-s20-0170.md`.
- Pliki robocze recenzenta (poza repo): `C:\Users\matma\AppData\Local\Temp\claude\65a86252f72ba2de\44810253-4f54-463a-b591-9868ed7d4a4f\scratchpad\m68\`. Są tam `files/` (42 kadry z `fetch.py`), `v960/`, wycinki `crop*.jpg`, arkusz NMPT, kafle NMT/NMPT WCS i skrypty `..\m68tools\`.

## 1. Kryteria M68

| Kryterium | Wynik | Dowód recenzenta |
|---|---|---|
| Kompleksy przy trasie z id i powierzchnią | **TAK** | K1–K5: OSM id, PTLZ lokalnyId, oddziały BDL, ha (README §1). OSM relation 11022876 sprawdzona w API 0.6: `landuse=forest`, `leaf_type=mixed`, `name=Las Solnicki`, `operator=Nadleśnictwo Dojlidy` ✓ |
| Wysokość z NMPT−NMT (percentyle) dla każdego kompleksu | **TAK** | 55 odcinków w `data/chm_edges.csv`, 715 stacji w `chm_stations.csv`. Metodę przeliczyłem niezależnie (§3) |
| Gatunek panujący (BDL lub UNVERIFIED) | **TAK / częściowo** | K4 w większości UNVERIFIED, co uczciwie opisano. Pięć opisów taksacyjnych pobrałem ponownie (§3) |
| Profil krawędzi z liczbami z ≥ 8 kadrów | **TAK** | 30 kadrów „krawędź” plus 383 profile CHM. Jedno zdanie o pniach jest niezgodne z obrazem (C68-213, §2) |
| ≥ 20 kadrów, ≥ 10 z okolicy | **TAK** | 42 kadry, w tym 29 lokalnych (Commons, 28 × CC0 Rakoon, 1 × CC BY-SA 3.0) i 13 z DK19 (Panoramax, BY-SA) |
| Przepis 5–8 punktów ze źródłem | **TAK** | 8 punktów. Pkt 3 i 6 wymagają korekty (errata 1, 2, 7) |
| Samokontrola ≥ 20 %, seed | **TAK** | `random.Random(20261114).sample(range(277), 56)` odtwarza dokładnie listę z `audit_20_percent.json`. Ponownie obejrzano 19 kadrów i poprawiono 5 opisów. Poprawiono też URL-e w 109 wierszach CHM |
| Zdjęcia nie w gicie, `fetch.py` | **TAK** | `.gitignore` obejmuje obrazy, `.asc` i `.zip`. `python -I fetch.py --tries 1` na czystym katalogu: `RAZEM: 42 plików; oryginały ok=15; tylko miniatura=27; niezgodne=0; błędy=0`, exit 0. Dwa oryginały Commons (C68-207, C68-210) przeszły już weryfikację sha1. Wszystkie 27 miniatur ma sha256 zgodne z `files_index.csv` |
| JPG ≤ 1600 px | częściowo | Panoramax ma 2560 px. `fetch.py` nie pomniejsza. Do korekty lokalnie przy imporcie, nie blokuje |
| Zakaz Google, tylko licencje komercyjne | **TAK** | Grep po hostach w `tools/`, `data/`, `fetch.py`, `manifest.csv`: geoportal/opendata GUGiK, bdl.lasy.gov.pl (ogcapi, mapserver ArcGIS = serwer BDL, nie obrazy Esri), commons/upload.wikimedia, panoramax, openstreetmap, kartaview, `maps.mail.ru` (mirror Overpass, który zwraca dane OSM ODbL; nie jest zakazany, odnotowuję). Brak Google, Bing, Apple, Yandex i Mapillary |

## 2. Co obejrzałem sam (16 kadrów + 3 wycinki)

Kadry z `fetch.py` pomniejszyłem do ≤ 960 px. Wycinki zrobiłem z miniatury 1280 px (×1,6–3).

| Kadr | Zgodność z opisem |
|---|---|
| C68-207 (oryginał 4080 px) | ✓ Brama lotniska, żółta tabliczka, tył znaku A-7, dwie latarnie, słupki. Po prawej młody drzewostan brzozowo-osikowy z krzewami do ziemi. Szacunek ~2,3× latarnia jest zgodny z obrazem |
| **C68-213** | **✗ częściowo.** Lewa ściana (za drogą rowerową) jest zamknięta liśćmi od ziemi, z dębem i klonem na pierwszym planie, zgodnie z opisem. **Prawa ściana (za jezdnią) ma wyraźnie widoczne smukłe pnie w dolnej ~1/4–1/3 wysokości, podszyt < 1 m i ciemne wnętrze** (wycinek `crop213.jpg`, x 700–1280, y 250–480 px miniatury). Opis mówi „pni nie widać”. Poza tym korony prawej ściany to głównie liściaste, a sosny są w tle |
| C68-216 | ✓ Klapowane liście klonu od ziemi, sosna w lewym górnym rogu, pas piaszczystej gleby |
| C68-217 | ✓ Po lewej pochylone jasne pnie gołe do kilku metrów i krzewy. Po prawej „schodek”: młodnik, a za nim wyższe drzewa. Uwaga: stożkowe korony po prawej wyglądają na **świerki**, a opis podaje „brzozy i sosny” (drobne) |
| C68-220 | ✓ Po lewej brzozy, świerki i sosny, pnie widoczne do ~1/3 wysokości. Po prawej zwarty młodnik do ziemi o równej górnej linii |
| C68-240 | ✓ Wierzby z wąskimi zwisającymi liśćmi do ziemi, ciąg C-13/C-16, studzienka |
| C68-246 | ✓ Pięć świerków z koronami prawie do ziemi przy budynku 3-kondygnacyjnym. Zmierzyłem ~1,75× wysokość budynku w px, opis podaje 1,5–2× |
| C68-249 | ✓ Bór sosnowy z rudymi pniami, pas krzewów 2–3 m u podstawy, bramownica i bloki w tle |
| C68-255 | ✓ Ciemne auto po lewej, dwa jasne po prawej, jasnozielony pas młodnika u podstawy, jeden rudy pień sosny |
| C68-261 | ✓ Przedwiośnie: sosny gołe do ~2/3, liściaste jako szarobrązowa prześwitująca masa, B-33 „70” |
| C68-263 | ✓ Prześwietlony rząd sosen, pawilony targowe, auta |
| C68-269 = P11-056 (+ 2 wycinki ×3) | ✓ Po lewej ciągły ciemny pas o gładkiej, falistej linii z jaśniejszymi zaroślami u podstawy. Na prawym końcu pasa cienka wieża i czerwone dachy. Po prawej luźny rząd pojedynczych koron nad żółtozielonym łanem. Commons: 2023-08-14 17:57, CC0. Słońce na W, więc „patrzy na N” jest wiarygodne |
| C68-271 | ✓ Rondo, cienka równa ciemna linia lasu przez całą szerokość, cumulusy, duża korona po prawej |
| C68-185, C68-188, C68-205 (DK19) | ✓ Sosny „kolumny” na skarpie z siatką. Bór z pniami od ziemi, brzozy dalej, świerk z koroną do ziemi po lewej. Linia lasu za łąką z drobnymi ząbkami |

**Wniosek z kadrów Mickiewicza (213, 217, 220, 216):** pnie są widoczne mniej więcej na połowie obejrzanych ścian (213 P, 217 L, 220 L), w dolnej 1/4–1/3 wysokości, za niskim podszytem ≤ 1–2 m. Ściany zamknięte od ziemi to głównie młodniki i podrost (213 L, 216, 220 P). Przepis pkt 3 („pnie widoczne najwyżej na 1/4–1/3 długości krawędzi”) powołuje się na C68-213, a ten kadr pokazuje coś przeciwnego (errata 1).

## 3. Liczby sprawdzone u źródła

**BDL — opis taksacyjny pobrałem ponownie dla 5 wydzieleń** (`StandDescriptionData`, ten sam endpoint co `tools/bdl_fetch.py`). Wszystkie pięć zgadza się z `data/bdl_*.csv`:
- 162-a (108012947): `9SO 76 l. H28 D36`, `1DB 101 l. H27 D43`, podszyt 0,9, nagłówek „Nadleśnictwo Dojlidy / Solnicki Las / PUL 2017-2026” ✓. Opis BDL ma też domieszki „miejscami”: grab, **modrzew**, brzoza, osika, lipa.
- 143-a (108031318): `9SO 162 l. H26 D50`, `1KL 82 l. H25`, podszyt 0,6 ✓.
- 149-a -01 (108032455): `10SO 99 l. H29 D40`, podszyt 1,0, „KO: klasa odnowienia”, podsadzenia dębu szypułkowego 0,3 ✓.
- 0424-r (−2061001264, gminne 2023): `5BRZ 80 l. H26`, `2OS 35 l. H18`, GB H17/H14, KL H15, zwarcie luźne, podszyt 0,8 ✓.
- 0324-k (−2061000432, inne SP 2013): **topola biała** 50 l. H25, zwarcie przerywane ✓.

**Regulamin BDL** (`/portal/regulamin`, pobrany dziś). Cytaty z cz. III („powszechny i nieodpłatny”) i z cz. V a („poinformować o źródle, czasie wytworzenia i pozyskania…”) są dosłowne ✓. `sources.md` **pomija cz. V b**: „dalej udostępnić innym użytkownikom informacje w pierwotnie pozyskanej formie” (errata 4). Dla gry to nie przeszkoda. Używamy liczb pochodnych jako parametrów generatora i nie redystrybuujemy opisów taksacyjnych.

**NMPT 2023 (arkusz N-34-107-C-b-3-2).** Pobrałem plik, 149 583 751 B. sha256 `82987a06…b8b367d` jest **identyczne** z `sources.md` ✓. Nagłówek: `xllcenter 777969.5`, `yllcenter 590165.5`, 0,5 m.

**Profil CHM przeliczyłem niezależnie.** Wziąłem kopię algorytmu `chm_edges.py`: NMPT 2023 z arkusza − NMT z WCS `DTM_PL-KRON86-NH_TIFF`, kafle pobrane od nowa.
- **Lot ulistniony, wszystkie 71 stacji** D303/CIOL/MICK w zasięgu arkusza. |różnica| moje − CSV:
  - `d_sciany`: mediana 0,0 m, 93 % ≤ 1 m, max 9,5 m (jedna stacja: próg znalazł inny skok);
  - h30 p50: mediana 0,12 m, 90 % ≤ 1 m, max 2,3 m;
  - h30 p90: mediana 0,16 m, 97 % ≤ 1 m, max 1,15 m;
  - h30 max: mediana 0,08 m, 97 % ≤ 1 m, max 1,6 m;
  - h5 p50: mediana 0,13 m, 82 % ≤ 1 m, max 11,6 m (stacje z ostrym skokiem na okapie, np. CIOL 299926239 s300: 7,9 vs 4,5).
- **Lot bezlistny, wszystkie 76 stacji** MICK i AERO w kafelku gry: WCS `DSM_PL-KRON86-NH`, ściana z CSV. |różnica| h30off p50: mediana 0,22 m, 78 % ≤ 1 m; h30off p90: mediana 0,04 m, 91 % ≤ 1 m. Odstępy pojedyncze, np. MICK 977514047 s30 (23,0 vs 20,2) i s60 (2,5 vs 12,9).
- Prawdopodobna przyczyna odstępów (**hipoteza, niesprawdzona**): azymut normalnej w CSV zaokrąglony do 1° i próbkowanie nearest-pixel.
- Wniosek: liczby CHM w paczce są odtwarzalne ✓.

**Drobna niespójność metody.** `tools/which_dsm.py` porównuje arkusze z pokryciem WCS `DSM_PL-EVRF2007-NH`, a obliczenia „bez liści” używają `DSM_PL-KRON86-NH`. Wniosek „WCS = lot 2025-04-18” jest więc dla KRON86 wnioskiem przez analogię. Moje przeliczenie na KRON86 daje te same wartości co CSV, więc dane są spójne. Brakuje tylko jawnego testu (errata 5).

**Licencje kadrów (API Commons):** P11-056 (`20230814_175724`) CC0 Rakoon; C68-213 (`20240623_140200`) CC0 Rakoon; C68-237 CC BY-SA 3.0 Krzysztof Kundzicz, w manifeście oznaczony „referencja, nie tekstura” ✓.

## 4. Analiza recenzenta: co z tych danych wynika (liczby nowe, policzone z plików paczki i arkusza 3-2)

**Zasięg względem gry.** Kafelek `bialystok-dojlidy` ma x 779019–781067 i y 589055–591103 (EPSG:2180). W kafelku leży **253 z 715 stacji: 174 MICK i 79 AERO**. Są to oddz. 149, 151, 152, gminne 0424-r oraz lasy K4 przy S granicy lotniska. K2, K3, Ciołkowskiego, oddz. 162/163 i wszystkie stacje Dywizjonu 303 z paczki leżą **poza kafelkiem** (far-field). Część Dywizjonu 303 w kafelku biegnie w otwartym terenie. Paczka nie identyfikuje obiektu, który tworzy horyzont P11-056: najbliższy PTLZ jest 561 m dalej, a linia drzew to nie las PTLZ. Robi to dopiero forest-0187 (ROD i zadrzewienia poza PTLZ). Liczby dla tych obiektów są w pkt H poniżej.

**A. Wysokości K1 w kafelku (MICK i AERO ≤ 80 m).**
- BDL, gatunek główny: SO H 24–29 (mediana ważona powierzchnią 29), BRZ 23–29 (27), DB 20–28, ŚW 23–31.
- CHM na 174 stacjach MICK w kafelku:
  - h30 p50 (mediana stacji) 20,6 m, h30 p90 24,4 m;
  - **h30_max** (najwyższe drzewo na 30 m profilu) **p50 26,0 / p90 29,1 m**, max 33,3 m (w kafelku).
- AERO w kafelku (79 stacji): h30_max p50 19,9 / p90 28,1 m.
- CHM p50 pikseli (20 m) nie jest wysokością drzew, bo zawiera boki koron i luki. Jako wysokość wierzchołków przyjmuję h30_max i BDL H.

**B. Krawędź: skos to bok korony drzew pełnej wysokości, nie pas niższych drzew.**
- Mediana 383 profili: 8,8 m na okapie, +2 m → 13,1, +5 m → 18,1, +8 m → 20,2.
- Ale **p75 dochodzi do 19,8 m już przy +2 m i ~22 m przy +4 m**.
- Stacje MICK w kafelku: h5_p50 13,0 m; dojście do 0,8 · p90 po 4,5 m (p50) / 12,5 m (p90).
- Wartość 8,8 m przy d = 0 zależy od progu definicji okapu (CHM ≥ 5 m).
- Wniosek: na większości stacji drzewa skrajne mają (prawie) pełną wysokość i stoją kilka metrów za okapem. Ich gałęzie po stronie drogi schodzą do 8–10 m. Na mniejszości (p90 dojścia 12,5 m) przed starym drzewostanem stoi pas niższych drzew.

**C. Płaszcz zewnętrzny jest rzadki. Metryka paczki łączy dwa różne zjawiska.** Stacje w kafelku z roślinnością ≥ 1 m przed okapem na szerokości ≥ 2 m: MICK 14 %, AERO 30 %. Rozbiłem je na dwie grupy.
- **Wąski płaszcz krzewów, 2–10 m szerokości:**
  - MICK: 7 % stacji, szerokość p50 4,0 m, wysokość h50 4,6 m / h90 5,4 m;
  - AERO: 19 % stacji, szerokość p50 3,5 m, wysokość h50 3,4 m / h90 3,9 m.
  - Zgadza się z pkt 4 przepisu (3–5 m) i z kadrami C68-249/255 (2–4 m).
- **Pas młodnika > 10 m szerokości:**
  - MICK: 7 % stacji, szerokość p50 19,5 m, wysokość h50 7,6 m / h90 9,6 m;
  - AERO: 11 % stacji, szerokość p50 16 m, wysokość h50 7,6 m / h90 10,4 m.
  - Odpowiada np. 151-a (zagajnik) i młodnikowi w C68-217/220 P.

**D. Podszyt (BDL).**
- Pokrycie, mediana ważona powierzchnią: 0,9 (MICK ≤ 80 m), 1,0 (w kafelku). Na CIOL 0,6.
- Gatunki podszytu, liczba wydzieleń na 23 przy MICK: leszczyna 21, kruszyna 14, brzoza 13, świerk 11, dąb 9, grab 9, klon 3, jarząb 3. **Sosny w podszycie nie ma w żadnym z 316 wydzieleń** (141 LP + 175 poza LP; sprawdzone grepem `podszyt_gat`).
- Kadry pokazują ścianę zamkniętą od ziemi na ~½ długości (§2).

**E. Skład gatunkowy.** Liczyłem `sklad` (dziesiąte) × powierzchnia. Paczka podaje udział „gatunku panującego wg powierzchni”, czyli inną miarę.
- MICK ≤ 80 m (102 ha): **SO 57 %, DB 20 %, BRZ 11 %, ŚW 8 %, MD 2 %, OL 2 %**. README podaje SO 76 / BRZ 11 / ŚW 6 / DB 4.
- W kafelku (MICK|AERO ≤ 80 m, 41 ha LP): **SO 64 %, BRZ 26 %, OL 4 %, DB 4 %, ŚW 2 %, MD 1 %**.
- Gminne przy AERO: OL.S 30, BRZ 24, OS 18, GB 9, TP 9.

**F. Kategoria BDOT ≠ BDL.** To ważne dla gry, bo kategoria wybiera `MIX`.
- PTLZ `12617d4f…` jest w BDOT „las/liściasty”, a obejmuje 152-a `7SO 1DB 1ŚW` (41 stacji MICK SW), 152-i `4SO…`, 152-j `5SO 3DB 2ŚW` oraz 0424-r (brzoza).
- PTLZ `1ac1a146…` jest w BDOT „**zagajnik**/mieszany”, a obejmuje 151-b `10BRZ 85 l. H27` i 151-a `10SO 99 l. H29`. CHM: p90 27,6–29,9 m.
- PTLZ `1260e10f…` „las/iglasty” = 149-a `10SO 99 l. H29` jest zgodny.
- PTLZ `146d3d3e…` i `a8b011e5…` „las/mieszany” = 162/163, sosna z dębem, zgodne (poza kafelkiem).

**G. Sylwetka okapu z drogi.**
- Metoda: max CHM 2023 w pasie 0–40 m za okapem, co 0,5 m wzdłuż drogi, na odcinkach w arkuszu 3-2 (skrypt `m68tools/sky.py`).
- CIOL NW (K2 mieszany, 480 m): linia p10/p50/p90 20,3/24,3/27,6 m. Odchylenie od mediany kroczącej 60 m: p10/p90 −2,2/+1,3 m, std 2,3 m (9 %). Wierzchołki z wybitnością ≥ 1,5 m co **13 m** (p25–p75 10–21 m).
- CIOL SE (K3/K2, 130 m): std 7 %, wierzchołki co 8 m (6–13).
- D303 SW (K3, 100 m): linia p50 18,5 m, std 10 %, wierzchołki co 14 m (13–17).
- Wniosek: modulacja **±2–2,5 m (~±10 %) co 8–14 m** jest zmierzona. Potwierdza kierunek recenzji 0170 P1-1 (±1,5 m co 8–15 m) i ADR 0187 (±9 % co 12–16 m). Amplitudę można dać nieco większą.

**H. Horyzont P11-056: obiekty `tree_stand` z forest-0187**, zmierzone NMPT 2023-09-15 − NMT, siatka 1 m.
- Pokrycie = udział pikseli z CHM ≥ 2 m.
- „Wierzchołki” = maksima w komórkach 10 × 10 m.
- **Zastrzeżenie:** w ogrodach działkowych CHM ≥ 2 m obejmuje też altany i żywopłoty, więc pokrycie i wierzchołki ROD to nie są wyłącznie drzewa (górne oszacowanie pokrycia). Obrysy z overrides mają tolerancję ±15 m.

| override (forest-0187 `overrides.yaml`) | WORKING_VALUE | pokrycie | wierzchołki p50 / p90 / p99 [m] |
|---|---|---|---|
| `allotment-gardens-north-of-krywlany` [0] (16,9 ha) | 4,0–8,5 | 0,43 | 5,9 / 9,7 / 13,8 |
| `allotment-gardens-…` [1] (10,7 ha) | 4,0–8,5 | 0,45 | 5,7 / 10,8 / 17,6 |
| `allotment-gardens-…` [2] (1,5 ha) | 4,0–8,5 | poza arkuszem (6 % próbki) — niezmierzone | — |
| `wood-north-west-of-the-meadow` (2,7 ha) | 10–17 | 0,58 | 8,3 / 18,5 / 20,9 |
| `wood-north-of-krywlany-skatepark` (1,3 ha) | 8,5–14,5 | **0,28** | 6,1 / 10,8 / 17,0 |

## 5. Errata (do naniesienia przez autora albo przy scaleniu — nie blokuje)

1. **C68-213, opis i pkt 3 przepisu.**
   - W opisie zamienić „Prawa ściana: … do samej ziemi — pni nie widać” na: „Prawa ściana (za jezdnią): korony liściaste, sosny w tle; w dolnej ~1/4–1/3 wysokości widoczne liczne smukłe pnie, podszyt < 1 m, ciemne wnętrze. Lewa ściana (za drogą rowerową): liściasta (dąb, klon) zamknięta od ziemi”.
   - Pkt 3 przepisu: „pnie widoczne na ok. połowie długości krawędzi przy Mickiewicza (dolna 1/4–1/3 wysokości ściany, za podszytem ≤ 1–2 m); druga połowa zamknięta liśćmi od ziemi, głównie młodnik i podrost (C68-213 L, 216, 220 P)”.
2. **README §3, wiersz „ul. Dywizjonu 303 (K3)”.**
   - 14 stacji obejmuje 2 stacje K2 (way 548967903, PTLZ 146d3d47, p90 23,8–24,3).
   - Dla samego K3 (12 stacji, PTLZ 6C19): mediana h30 p50 ≈ 11,5 m, h30 p90 12,0–22,4 (mediana ≈ 15), max ≤ 23,0.
   - Przeliczyć wiersz i rozdzielić K2 od K3.
3. **README §2, udziały gatunków.**
   - Dopisać skład ważony `sklad` × ha obok udziału „gatunku panującego”: MICK ≤ 80 m SO 57 / DB 20 / BRZ 11 / ŚW 8 / MD 2 / OL 2 %.
   - Nazwać obie miary jawnie.
4. **sources.md, BDL.** Dopisać cz. V b regulaminu („dalej udostępnić … w pierwotnie pozyskanej formie”) i odesłanie regulaminu do przepisów o ponownym wykorzystywaniu informacji publicznej.
5. **sources.md / README §3, WCS bez liści.** Dopisać, że `which_dsm.py` testował `DSM_PL-EVRF2007-NH`, a obliczenia użyły `DSM_PL-KRON86-NH`. Dla KRON86 data lotu wynika przez analogię. Najlepiej powtórzyć test na KRON86.
6. **manifest.csv, sha256 oryginałów, które już się pobierają:**
   - C68-207 `df07f7112c701c32ffc7d41de1baed470c2f53ca63d2de7a69bb7ac4dbfa2482` (3 357 621 B);
   - C68-210 `6aaf6cf4ac2ec092caa8ca91e8c6b85204d0863f51e6435bfcb69dbcdd44bec2` (3 551 761 B).
7. **Pkt 2 i 6 przepisu.**
   - Pkt 2: dopisać, że skos 8–10 m → pełna wysokość to na większości stacji bok korony drzew pełnej wysokości (p75 = 19,8 m już przy +2 m), a pas niższych drzew tylko na mniejszości (p90 dojścia 12,5 m).
   - Pkt 6: „pojedyncze starsze drzewa do ~25 m”. W samym K3 CHM daje max 23,0 m (D303) i 25,8 m (CIOL SE). Wartość 25 m przy lotnisku NW to osobne wydzielenie Skarbu Państwa 0324-k, topola biała 50 l. H25. Rozróżnić te dwa źródła.
8. **README §5, P11-056.**
   - Dopisać, że linia drzew na horyzoncie to nie las PTLZ (najbliższy PTLZ 561 m) i że obiekt nie został zidentyfikowany.
   - Zamiast „pas lasu” pisać „linia drzew”.
9. **C68-217 (drobne).** Stożkowe korony po prawej opisać jako „świerk (ESTIMATED)” zamiast „brzozy i sosny”.

## 6. Wnioski dla gry: konkretne liczby dla generatora (forest-0187, prowadzi Argon)

Odniesienia:
- ADR 0170 (`docs/adr/0170-horizon-forest-stand-near-crowns.md`, scalone): `kind: forest_stand` z polami `height_m`, `mix`, `spacing_m`, `emergent`.
- Recenzja `REVIEW-2026-11-13-s20-0170.md`: P1-1 palisada, P1-2 świerk ≤ 3 m.
- Szkic `.claude/worktrees/forest-0187/docs/adr/0187-sciana-lasu-swierk-mlodnik-plaszcz-horyzont.md`.
- Kod `forest-0187/tools/worldgen/streetscape/vegetation.py` (`HEIGHT`, `MIX`, `UNDERSTOREY`, `MANTLE`, zagajnik × 0,7) i `forest_hlod.py` (`SKIRT_OFF_M` 3,5).

Wszystkie wartości poniżej to **pomiar (NMPT/BDL) + WORKING_VALUE recenzenta** w odwzorowaniu na bibliotekę gry.

| # | Element | Gra dziś (forest-0187) | Pomiar M68 / recenzja | Działanie |
|---|---|---|---|---|
| 1 | Wysokość okapu K1 w kafelku | `HEIGHT` pine 14–24, spruce 14–25, birch 9–19 (klasa domyślna) | BDL SO H 24–29 (med 29), BRZ 27; CHM wierzchołki h30_max p50 26,0 / p90 29,1, h30_p90 24,4 | `forest_stand` dla PTLZ w kafelku. Klucze sprawdzone w `forest-0187/Data/Regions/bialystok-dojlidy/generated/streetscape_sources.json` (id bez sufiksu `:0`): **`1260e10f-a825-11ef-9e0c-1866da21c735` (las/iglasty, 149-a) `height_m [24, 29]`; `12617d4f-a825-11ef-b23a-1866da21c735` (las/liściasty, 152-a/i/j + 0424-r) `[20, 28]`; `1ac1a146-d200-4920-9fd4-9ac2b70023a0` (zagajnik/mieszany, 151-a/b) `[22, 29]`** (patrz #3: pas młodnika od ulicy) |
| 2 | Emergenty | `emergent` nieużywany | h30_max p90 29,1, max 33,3 m | `emergent {share 0.03, height_m [29, 32]}` w K1. Share to WORKING_VALUE. 6BC0 (P1-1, topola) poza zasięgiem M68, zostaje UNVERIFIED |
| 3 | **Kategoria BDOT ≠ BDL** | `liściasty` = bez sosny (ADR 0170); `zagajnik` = wysokości × 0,7, bez podszytu | `12617d4f` liściasty, a 152-a to `7SO 1DB 1ŚW`. `1ac1a146` zagajnik, a 151-b/151-a mają 85–99 lat i H 27–29 | Override `mix` na `12617d4f`: pine 0,55 / birch 0,25 / oak→linden 0,10 / spruce 0,05 / alder 0,05. **Na `1ac1a146` zdjąć skalę zagajnika (override `height_m`)**. Bez tego gra rysuje zagajnik 10–17 m tam, gdzie stoi las 27–29 m. **Zachować przy tym pas młodnika 5–10 m od strony ulicy**, widoczny w C68-217 i C68-220 P (151-a: pas 15–35 m). Override nie może go spłaszczyć do jednej wysokości. Na przykład podzielić poligon albo dać `MANTLE` pasmo młodnika tylko po stronie NE Mickiewicza |
| 4 | `MIX` iglasty / mieszany | iglasty pine 0,64 / spruce 0,20 / birch 0,10; mieszany pine 0,36 / spruce 0,14 / birch 0,24 / alder 0,10 / maple 0,08 / linden 0,08 | Kafelek: SO 64, BRZ 26, OL 4, DB 4, ŚW 2 %. MICK: SO 57, DB 20, BRZ 11, ŚW 8 % | Dla Krywlan **świerk 0,05–0,08** (nie 0,14–0,20), **sosna 0,55–0,65**, brzoza 0,15–0,25. Dąb 0,10–0,20 zastępczo jako lipa lub klon (biblioteka nie ma dębu): WORKING_VALUE, do ADR. Domyślnego `MIX` całego regionu tym nie zmieniać. Lepiej użyć overrides per PTLZ albo osobnego miksu „bór mieszany Solnicki” |
| 5 | Krawędź (wnętrze) | Siatka okapu na całym `full` i do tego **dodatkowe** pasma `MANTLE` [−5, 0] młodnik 2,5–9 m oraz [−11, −5] 6–15 m (cap 0,6 × okap). Sprawdziłem `vegetation.py` l. 280–327: pasma nie usuwają drzew okapu | Okap 8–10 m, +2 m → 13, +5 m → 18, +8 m → 20 (mediana); **p75 19,8 m już przy +2 m**; MICK w kafelku: h5_p50 13,0 m, dojście do 0,8 · p90 po 4,5 m (p50) / 12,5 m (p90) | **Zgodne z pomiarem jako drugie piętro**: drzewa okapu stoją do krawędzi, a pasma dodają niższe piętro. Do sprawdzenia w renderze: czy ściana HLOD (`forest_hlod.py`, tekstura krawędzi z płaszczem) nie pokazuje skosu dłuższego niż 4–8 m. Pełna wysokość ma być po ~5 m od okapu (mediana), a nie po 11 m |
| 6 | Płaszcz zewnętrzny + spódnica HLOD | Pasmo [0, +4] krzewy 1–3,5 m na każdej krawędzi; spódnica 3,5 m przed każdą zewnętrzną ścianą | Wąski płaszcz krzewów (2–10 m szer.): **7 % (MICK) / 19 % (AERO)** długości, szer. p50 3,5–4 m, wys. h50 3,4–4,6 / h90 3,9–5,4 m. Pas młodnika > 10 m: 7 % / 11 %, szer. 16–20 m, wys. h50 7,6 / h90 ~10 m. Na reszcie (~80 %) przed okapem jest koszona trawa | Płaszcz i spódnicę włączać **per odcinek: krzewy 3–5 m wys. i 3–4 m szer. na ~0,1 (drogi w lesie) / ~0,2 (granica lotniska) długości**, wybór haszem, a nie na każdej ścianie. Pas młodnika 6–10 m tylko tam, gdzie jest w danych (151-a / NE Mickiewicza). Obecne krzewy 1–3,5 m są o ~1–2 m za niskie (WORKING_VALUE) |
| 7 | Podszyt | `UNDERSTOREY` shrub 0,38 / spruce 0,30 / birchyoung 0,16 / pineyoung 0,16; 1 / 30 m² | BDL pokrycie 0,9–1,0. Leszczyna 21/23, kruszyna 14, brzoza 13, świerk 11, dąb 9, grab 9; **sosny w podszycie brak**. Wysokość 2–5 m (kadry, ESTIMATED) | shrub (leszczyna/kruszyna) **0,55**, birchyoung 0,15, spruce 0,15, młody liściasty (klon/grab/dąb → `shrub`/`maple` młody) 0,15, **pineyoung 0**. Gęstość wystarczy na pokrycie ~0,8. Pnie przy krawędzi widoczne na ~½ długości (§2) |
| 8 | Sylwetka okapu (HLOD, wypiek krawędzi) | Kopuły ±9 % co 12–16 m (0187); P1-1 chciało ±1,5 m co 8–15 m | Linia wierzchołków: std 7–10 %, p10/p90 −2,2…+2,8 m, wierzchołki co 8–14 m (p25–p75 6–20 m) | Zostawić **±10 % (±2–2,5 m) co 8–16 m**, odstęp losowany zamiast stałego. Pnie w teksturze krawędzi tylko w dolnej 1/4–1/3 i tylko na ~½ długości (reszta zakryta), zgodnie z P1-1 |
| 9 | Horyzont P11-056 `tree_stand` (forest-0187) | ROD 4–8,5; wood-NW 10–17 (mantle); skatepark 8,5–14,5, spacing 5,5 (mantle) | Wierzchołki: ROD p50 5,7–5,9 / p90 9,7–10,8 / p99 14–18, pokrycie 0,43–0,45 (z altanami i żywopłotami); wood-NW p50 8,3 / p90 18,5, pokrycie 0,58; skatepark p50 6,1 / p90 10,8, **pokrycie 0,28** | ROD: `[4, 10]` + emergent ~0,02 do 14–17 (w `verify` dopisać „NMPT 2023: zmierzone, recenzja M68”). wood-NW: `[8, 19]`, spacing tak, by pokrycie ~0,6. **skatepark: w obrysie jest rzadko i nisko** (`[5, 11]`, pokrycie ~0,3). Ten stand domyka szczerbę horyzontu w parze P11-056, więc najpierw sprawdzić na parze, czy drzewa linii horyzontu nie stoją głębiej, poza obrysem. Dopiero potem zmniejszać gęstość albo zdejmować `mantle`. Pierścień 3 ROD jest poza arkuszem 3-2 (potrzebny arkusz 3-4) |
| 10 | Kolor/ton (sezon) | — | Bez liści ÷ lato = 0,64 (kafelek), 0,56 (AERO): duża część okapu to liściaste | Na przyszły wariant zimowy: korony liściaste prześwitujące, sosny zostają (C68-261) |
| 11 | P1-2 (świerk ≤ 3 m) | Otwarte | Kadry potwierdzają tylko korony świerka do ziemi (C68-188, 246) | Nic nowego poza „spódnica do gruntu”. Bez zmian |
| 12 | Licencje | — | BDL: wymóg atrybucji (źródło, czas wytworzenia i pozyskania) | Do `docs/LICENSES.md`: „Bank Danych o Lasach (BULiGL/PGL LP), opisy taksacyjne Nadl. Dojlidy PUL 2017–2026 i lasy gminne stan 2023, pozyskano 2026-11-14 — parametry pochodne generatora roślinności”. GUGiK NMPT/NMT bez zmian |

**Kolejność dla Argona:**
1. #3 i #1: overrides PTLZ w kafelku. Największy błąd widoczny z Mickiewicza.
2. #5: kontrola skosu ściany HLOD w renderze.
3. #9: liczby horyzontu P11-056 zastępują WORKING_VALUE.
4. #6 i #7.
5. #8 i #4: strojenie.

## 7. Dla lidera

- **Scalić PR #72** (diff tylko w `research/cloud/p25-krywlany-forest/`). Errata 1–9 można nanieść przy scaleniu albo w poprawce autora. Najważniejsze to 1, 2 i 7.
- Gra: tabela §6 trafia do forest-0187 (Argon) jako dane wejściowe do ADR 0187. Pozycje #1, #3 i #9 mają pomiar zamiast WORKING_VALUE.
