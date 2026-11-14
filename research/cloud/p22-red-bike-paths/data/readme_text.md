# M65 — drogi dla rowerów z czerwonego asfaltu: trasa C i Dojlidy (cloud p22-red-bike-paths)

Gałąź `research/cloud-p22-red-bike-paths`. Blok: `docs/owner/MISTRAL-TASKS-10.md` § M65 (z różnicami z briefu zespołu cloud: id `C65-NNN`, bez ZIP — `fetch.py` + sha256). Plik generowany: `python3 -I tools/build_readme.py` (tekst: `data/readme_text.md`).

## 0. Najważniejsze ustalenia (dla generatora nawierzchni)

1. **W Dojlidach DDR NIE są z czerwonego asfaltu.** Wszystkie obejrzane odcinki przy ul. Dywizjonu 303, Kuronia, Mickiewicza, Hake, Ciołkowskiego, Karpińskiego to **szary asfalt** z białą linią osiową przerywaną i symbolami P-23, obok chodnika z jasnej kostki. Czerwone są tam wyłącznie **pola przejazdów przez wloty** (9 z 21 przecięć z jezdniami), m.in. przejazd z kadru P11-056 (wlot ul. Spadochroniarzy, C65-144). Założenie z recenzji 0179 („DDR z czerwonego asfaltu” przy Kuronia / P11-001) **nie potwierdza się na ortofotomapie 5 cm** — do rozstrzygnięcia na kadrze P11-001, którego w tej sesji nie dało się pobrać (§9).
2. **W regionie C czerwonobrązowy (bordowy, spłowiały) asfalt DDR występuje** — w rejonie ronda pod estakadą (Al. Tysiąclecia/Maczka/łącznice), przy ul. Bitwy Białostockiej koło ronda Pamięci Bieżeństwa i na ciągach wzdłuż estakady Andersa: 9 odcinków, ok. 1,71 km w kaflu (+ 1 spłowiały różowoszary, 270 m). Wzdłuż Al. Tysiąclecia na południe od ronda DDR są szare; ciągi pieszo-rowerowe przy ul. Andersa to jasna kostka (10 odcinków) albo wąskie pasy z czerwonej kostki (4 odcinki).
3. **Czerwone pole przejazdu ≠ kolor DDR.** Tam, gdzie DDR jest czerwonobrązowa (rondo pod estakadą), przejazdy przez jezdnie są tylko białe (P-11); tam, gdzie DDR jest szara (Sokólska, Wileńska, Hake, wloty w Dojlidach), przejazdy mają jaskrawoczerwone pole. Standard miasta: **RAL 3020, masa chemoutwardzalna uszorstniona** (wytyczne ZDM, str. 16) — to powłoka na asfalcie jezdni.
4. **Przez wjazdy do posesji** w Dojlidach DDR się urywa (zjazd z kostki/betonu przecina ją, P-23 po obu stronach, bez czerwieni); w C spotyka się czerwone prostokąty bez białych kwadratów na wyjazdach z parkingu/posesji (C65-153, C65-157).
5. **OSM nie ma tagów `colour`/`width` na żadnym z 93 odcinków** — kolor i szerokość trzeba brać z tej paczki (ESTIMATED z orto), nie z OSM.

## 1. Zapytanie Overpass i metoda

- Endpoint `https://maps.mail.ru/osm/tools/overpass/api/interpreter`, 2026-11-14T16:49:07Z, `timestamp_osm_base` 2026-11-14T16:48:34Z; treść: `overpass-query.ql`; surowy wynik: `overpass-result.json` (1,41 MB).
- Definicja odcinka DDR/CPR (`tools/inventory.py`): `highway=cycleway` **albo** `highway=path|footway|pedestrian` z `bicycle=designated`; way musi mieć ≥ 5 cm długości w kaflu regionu (kafle z `Data/Regions/*/region.yaml`, przeliczenie `tools/geo.py`). Długość: haversine po węzłach (całe way) + długość części w kaflu (przycięcie w EPSG:2180, skala lokalna).
- Jezdnia równoległa: próbki co 5 m wzdłuż DDR; kandydaci = odcinki `highway` klasy motorway…service w promieniu 40 m o kierunku ±30°; wygrywa way z największą liczbą próbek (drogi `service` tylko gdy nie ma innej), wymagany udział ≥ 30 %; odległość = mediana odległości punkt DDR → oś najbliższej jezdni (przy drogach dwujezdniowych jest to oś BLIŻSZEJ jezdni).
- Przecięcia (`tools/crossings.py`): wspólne węzły OSM odcinka DDR i jezdni (`kind=jezdnia`) lub drogi `service` (`kind=wjazd`).
- Kolor, szerokości, rozdzielenie: **ortofotomapa GUGiK 5 cm** (WMS HighResolution; nalot 2025-04-18 albo 2024-03-30 — patrz `sources.md` §2): przekroje `tools/transect.py` (obrót do osi DDR, linijka co 1 m, odczyt ±0,3 m), wycinki przejazdów `tools/crossing_crop.py` + profil jasności `tools/crossing_profile.py` (±0,15 m; przejazdy ukośne ±0,5 m). Kolor wyłącznie opisem słownym.
- Brakujące tagi wpisane jako „brak tagu”. Typ rozdzielenia od jezdni — z przekroju orto (kolumna „układ od jezdni”); wysokości krawężników z orto nie da się odczytać.

## 2. Inwentarz odcinków (kontrola sum)

{{SUMY}}

Tagi kontrolne w OSM (93 odcinki): `colour` 0, `surface:colour` 0, `width` 0, `oneway` 0, `lit` 3, `smoothness` 2, `segregated` 63, `surface` 86. Dwa odcinki regionu C (1562298579, 1562298580) to `highway=cycleway` + `surface=dirt` + `access=forestry` — leśne drogi gruntowe, nie DDR miejskie (zostawione w inwentarzu, bo spełniają definicję).

{{INWENTARZ}}

Pełne tagi (JSON), końce WGS84, min/max odległości osi i lista brakujących tagów — w `manifest.csv` (wiersze `odcinek`) i `inventory.json`.

## 3. Szerokości i geometria (ESTIMATED, orto 5 cm, linijka 1 m, ±0,3 m)

{{SZEROKOSCI}}

Wnioski: DDR asfaltowe dwukierunkowe mają zwykle **2,1–2,8 m** (Dojlidy) i **2,2–3,3 m** (C, czerwonobrązowe); chodnik obok **1,7–3,0 m**; pas zieleni między krawężnikiem jezdni a ciągiem **1,9–4,7 m** (bywa 0 — DDR/chodnik przy samym krawężniku). Wytyczne ZDM: DDR dwukierunkowa min. 2,0 m, jednokierunkowa min. 1,5 m (str. 18).

Krawężnik: wytyczne ZDM, rys. nr 9 (str. 18) — krawężnik/obrzeże najazdowe „k1” 25×12×100 cm z odsłonięciem „+3” (cm — jednostka niepodana na rysunku); 16 cm tylko przy przystankach (str. 4). **Wysokość krawężnika jezdni przy DDR i skosy wjazdów: UNVERIFIED** (brak w dokumentach, nieczytelne z orto).

## 4. Przejazdy dla rowerzystów (przez jezdnie)

Przepis: Dz.U. 2019 poz. 2311, zał. 2, pkt 4.2.2 — „nie może być mniejsza niż: – 1,8 m – w przypadku przejazdu jednokierunkowego, – 3,0 m – w przypadku przejazdu dwukierunkowego” (str. 569); „zaleca się dodatkowe oznaczenie powierzchni przejazdu barwą czerwoną” (str. 570); przejazd połączony z przejściem „oznacza się barwą czerwoną” (str. 571). „s” = odległość między zewnętrznymi krawędziami rzędów kwadratów P-11 (przy przejeździe połączonym: od rzędu kwadratów do krawędzi zebry).

{{PRZEJAZDY}}

Bilans (54 przecięcia DDR z jezdniami wg OSM): C — 16 czerwonych, 5 tylko białych, 2 bez oznakowania, 10 nieoglądanych (drobne uliczki osiedlowe); Dojlidy — 9 czerwonych, 11 tylko białych, 1 bez oznakowania. Zmierzone „s”: czerwone mediana 2,83 m (1,55–3,10; n=18), białe mediana 2,70 m (2,30–4,00; n=9) — około połowy poniżej normatywnych 3,0 m.

Znaki pionowe: D-6b potwierdzony na kadrach ulicznych tylko przy rondzie pod estakadą (C65-208, C65-218, C65-221); dla pozostałych przejazdów C-13/C-16, D-6a/D-6b — **UNVERIFIED** (z ortofotomapy nieczytelne). Sygnalizacja — z tagu OSM `crossing` (maszty widoczne na orto na skrzyżowaniach x00, x12, x16, x18).

### 4a. Przecięcia DDR z wjazdami (38 węzłów OSM, 12 obejrzanych)

{{WJAZDY}}

## 5. Czerwona nawierzchnia — wygląd (do tekstur)

- **Asfalt barwiony DDR (C):** czerwonobrązowy/bordowy, matowy, mniej nasycony i ciemniejszy od pól przejazdów; miejscami spłowiały do różowoszarego; białe P-1d/P-23 na czerwonym tle; krawędź prosta przy obrzeżu, obok chodnik z jasnej kostki. Kodu RAL/Munsell dla masy barwionej **nie ma** w wytycznych ZDM (jest tylko wymóg „wyraźnie inny kolor”, str. 19) → UNVERIFIED.
- **Pola przejazdów:** jasna, żywa czerwień — **RAL 3020** wg wytycznych ZDM (str. 16: „Przejazdy rowerowe w kolorze czerwonym – kolor RAL 3020, wykonane z masy chemoutwardzalnej ze środkiem uszorstniającym.”). Granica ostra: rząd białych kwadratów albo krawędź zebry; kształt prostokąt/trapez. **Zużycie:** czerwień wytarta do ciemnego asfaltu w śladach kół (C65-100, C65-101, C65-149).
- **Czerwona kostka:** pasy rowerowe 2,1–2,2 m przy ul. Andersa, pas separacyjny ok. 0,4 m między DDR a chodnikiem (Bitwy Białostockiej), krótkie pola przy krawężnikach przed przejściami.
- Faktura kruszywa, plamy oleju, łaty, uszczelnienie spoiny czerwony/szary, wygląd zimą — **UNVERIFIED** (wymaga kadrów z poziomu pieszego; patrz §9).

## 6. Kadry

Manifest: {{LICZBY}}. Kadry uliczne obejrzane w pomniejszeniu do 960 px (+ wycinki 130–300 % dla znaków): 7 Panoramax + 8 KartaView = **15, wszystkie z regionu C**; z przejazdem rowerowym w kadrze: 3 pewne (D-6b) + 2 niepewne. Dodatkowo obejrzano 17 wycinków zbiorczych ortofotomapy (6 C, 11 Dojlidy; 15 z przejazdem), 64 przekroje odcinków, 32 wycinki przejazdów i 12 wycinków wjazdów (pliki przy wierszach `odcinek`/`przejazd`).

{{KADRY}}

Uwaga: kadry KartaView z 2018 r. (C65-215…C65-218) pokazują stan sprzed pojawienia się czerwonych pól na skrzyżowaniach Al. Tysiąclecia — nie używać ich jako dowodu „braku czerwieni” dziś. Kadry z estakady (C65-214, C65-219, C65-220, C65-222) są dalej niż 25 m od osi DDR albo nad nią — kadry kontekstowe (czerwona opaska na estakadzie to chodnik techniczny, nie DDR).

## 7. Rozbieżności OSM ↔ zdjęcie/ortofotomapa

{{ROZBIEZNOSCI}}

Dodatkowo (ogólne): (a) `highway=cycleway` + `foot=no` na ul. Mickiewicza (285876996) i innych, choć chodnik biegnie w tej samej płaszczyźnie tuż obok (w OSM brak osobnego `footway`); (b) wytyczne ZDM („DDR między chodnikiem a jezdnią”) a stan: na Kuronia, Mickiewicza i części Al. Tysiąclecia chodnik jest bliżej jezdni niż DDR; (c) P11-001 / P11-056: opis w manifeście p11 nie wspomina DDR ani przejazdu; wg pozycji P11-056 leży 5 m od way 538810153 i ok. 35 m od przejazdu C65-144 (czerwony), P11-001 — 2 m od way 212811563 (szary asfalt wg orto) i ok. 13 m od wjazdu C65-170.

## 8. Samokontrola 20 %

Seed `random.Random(20261114).sample(ids, 48)` (48/239 = 20,1 %). Sprawdzono: ponowne zapytanie OSM API 0.6 o 15 way i 19 węzłów (wszystkie istnieją, tagi zgodne), ponowne obejrzenie 30 obrazów pobranych niezależnie przez `fetch.py` (nowe arkusze z linijką), HTTP 200 dla 4 kadrów ulicznych, 5 cytatów w tekście PDF. Wynik: **38 PASS, 10 POPRAWIONO**. Najważniejsza poprawka: odczyty szerokości przejazdów „na oko” miały rozrzut do ±0,4 m → dla wszystkich 32 wycinków policzono profil jasności (`tools/crossing_profile.py`) i podmieniono wartości; 3 nieczytelne przejazdy dostały brak wartości. Szczegóły: `audit_20_percent.json`.

## 9. Luki (uczciwie)

1. **Wikimedia Commons niedostępne (HTTP 429 przez całą sesję)** → kadry **P11-001 i P11-056 NIE zostały obejrzane**, brak jakichkolwiek kadrów ulicznych z Dojlid (Panoramax i KartaView mają tam 0 zdjęć). Kryterium „≥ 10 kadrów z Dojlid, w tym P11-001 i P11-056” spełnione tylko zastępczo ortofotomapą (11 wycinków zbiorczych + przekroje). Do zrobienia przez lidera: pobrać oba pliki (adresy w `sources.md` §5) i porównać z C65-076 (way 212811563) oraz C65-144 (przejazd).
2. Region C: 15 kadrów ulicznych to ujęcia z kabiny samochodu, DDR widać w nich słabo; tylko 3 pewne kadry z przejazdem rowerowym (kryterium ≥ 5 — CZĘŚCIOWO; uzupełnione ortofotomapą).
3. Data ortofotomapy niejednoznaczna (2025-04-18 albo 2024-03-30).
4. Szerokości wyłącznie ESTIMATED z orto; dokumentów projektowych/przetargowych BIP dla tych odcinków nie znaleziono; OSM `width` — brak.
5. Wysokość krawężników, skosy wjazdów, znaki pionowe przy przejazdach (poza rondem pod estakadą), faktura i stan nawierzchni z bliska, lato/zima, RAL asfaltu barwionego DDR — UNVERIFIED.
6. 27 krótkich odcinków C (463 m łącznie) i 3 w Dojlidach (39 m) oraz 10 drobnych przecięć w C i 26 wjazdów — nieoglądane (tylko dane OSM).
7. Odcinki o niepewnym kolorze: 257367436 i 268470393 (cień lasu; możliwy spłowiały asfalt barwiony), 741639504, 946729187, 203348234, 614216218, 236110049, 173985180.

## 10. Pliki

`manifest.csv` (25 kolumn = kolumny bloku + `url_pliku`, `sha256`) · `fetch.py` (133 pliki, 68 794 874 B, w tym 2 PDF 29,6 MB; `--skip-pdf`) · `overpass-query.ql`, `overpass-result.json` · `inventory.json`, `crossings.json` · `data/` (indeksy wycinków, odczyty `observations.py`, opisy kadrów, cytaty) · `tools/` (geo, inventory, crossings, transect, crossing_crop, crossing_profile, build_manifest, build_readme) · `audit_20_percent.json` · `sources.md` · `STATUS.md`. Zdjęć i PDF w gicie nie ma (`.gitignore`).
