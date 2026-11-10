# Lista ujęć zdjęciowych — trasa startowa (D41)

Trasa: **Kwadrat Park → ul. gen. Andersa → Rondo Putry → Al. Tysiąclecia (DK8/DK19)**, kandydat C, ok. 2,4 km.
Lista jest wygenerowana z danych projektu (pozycje kamer gate3/photo_match, geometria trasy, OSM, BDOT10k) skryptem
`tools/worldgen/photolist/build_photo_list.py`. **{{N}} ujęć** w kolejności trasy + Załącznik A (wszystkie pozy kamer).
Mapa z numerami: ![mapa ujęć](img/photo-list-map.png)

Źródło mapy i tła: © OpenStreetMap contributors (ODbL), budynki GUGiK BDOT10k. Linki prowadzą do openstreetmap.org i mapillary.com. **Nie używamy Google (Maps, Street View, Earth) w żadnej formie** — także jako ściąga na miejscu.

## 1. Najkrócej

1. Wybierz dzień **pochmurny** (rozproszone światło, brak ostrych cieni), najlepiej 10:00-14:00. Pora roku: listopad-luty, słońce nisko cały dzień, więc nawet przy słońcu dobre są poranki i popołudnia — ale **do tekstur tylko pochmurno**.
2. Jedna osoba lub dwie: kierowca + pasażer robi **wideo i kadry z fotela pasażera** na Andersa (to trasa szybkiego ruchu, nie wolno się zatrzymywać na jezdni).
3. Drugi termin: **zmierzch** (ok. 20-40 min po zachodzie słońca, niebo jeszcze niebieskie) — tylko ujęcia oznaczone `Z` (latarnie, oświetlone rondo).
4. Telefon: **główny obiektyw 1×, bez zoomu**, aparat poziomo, rozdzielczość maksymalna, format JPEG/HEIC lub RAW (RAW/oryginał zachowaj). Wyłącz HDR „agresywny”/tryb portretowy/upiększanie/filtr.
5. Zdjęcia wrzuć do `Data/raw/photos/owner/` (poza gitem), nazwy wg sekcji 4. Daj znać liderowi — dopisze manifest i licencję.

## 2. Zasady fotografowania (ważne)

- **Tekstury fasad i nawierzchni — PROSTOPADLE**: aparat równolegle do ściany/ziemi, ściana wypełnia kadr, pion bez przechyłu. Nie „szeroki kąt z ukosa”.
- **Bez ostrych cieni**: pochmurno albo cień budynku na całej powierzchni. Nie fotografuj połowy ściany w słońcu i połowy w cieniu.
- **Skala i kolor**: w kadrze (w rogu) kartka białego papieru A4 (297 × 210 mm) lub linijka/miarka zwijana; jeśli masz kartę szarości (18%), zrób jedno zdjęcie karty w tym samym świetle co serię. Kartka jest też wzorcem bieli.
- **Seria zamiast jednego**: dla każdej fasady/nawierzchni: 1× całość, 2-3× zbliżenia (materiał, spoina, detal), 1× z nieco inną ostrością. Mało kadrów = nie da się zrobić tekstury.
- **Bez ludzi, bez tablic rejestracyjnych, bez twarzy.** Poczekaj lub zrób kadr od innej strony. Tablice: nie fotografuj, albo zakryj/odwróć kadr. Niczego nie pokazuj ze zbliżenia, co identyfikuje firmę (logo), bo w grze marki są fikcyjne.
- **Prywatność i bezpieczeństwo**: nie wchodź na jezdnię; na Andersa i Al. Tysiąclecia (drogi krajowe, 3 pasy, wiadukty) wyłącznie z chodnika, bezpiecznej zatoki lub jako pasażer. Teren Kwadrat Parku jest **prywatny** — zdjęcia tylko z drogi publicznej albo za zgodą zarządcy (oznaczone `[PRYWATNE]`). Nie fotografuj z drona (przepisy i zasady projektu). Jeśli coś jest niebezpieczne — pomiń, lista jest zapasowa.
- **Ogniskowa**: 1× (ok. 24-26 mm w przeliczeniu na pełną klatkę). Kamery gate3 w grze mają pionowe FOV 55-65° (to szerszy kadr niż 1× w telefonie); dla ujęć „kadr gate3” zrób 1× oraz, jeśli telefon ma, jeden kadr 0,5× z tego samego miejsca. Nie używaj zoomu, bo zmienia perspektywę.
- **Wysokość**: standardowo **1,5 m** (oczy pieszego, telefon trzymany przy oczach). Gra ma kamerę kierowcy na 2,5 m; jeśli masz dostęp do kabiny ciężarówki, dodatkowo jedno ujęcie z 2,5 m (opcjonalnie, nie wchodź na dach ani na przyczepę). Pod nogi/pionowo w dół: ok. 1,3 m nad ziemią.
- **Orientacja**: zapisz kierunek (kompas telefonu w aplikacji, pokaż azymut), albo zrób zdjęcie ekranu mapy ze swoją pozycją. Włącz zapis lokalizacji w EXIF (GPS).

Kody w tabeli: **Typ** = kadr gate3 (zgodność z kamerą w grze), fasada, nawierzchnia, zieleń, latarnia/znak, auta, detal. **Pora**: `S` = pochmurno w dzień, `Z+S` = zmierzch (oraz wersja dzienna). **Pri**: P1 = konieczne, P2 = ważne, P3 = opcjonalne. **[PRYWATNE]** = teren prywatny. **[RUCH]** = droga o dużym ruchu, tylko z chodnika/zatoki/pasażera.
Współrzędne „authored” (fasady, nawierzchnie, zieleń itd.) są orientacyjne (± 10 m, WORKING_VALUE): wybierz najbliższe dobre miejsce. Współrzędne kamer gate3 są dokładne (poza zniekształceniem: wysokość 2,5 m w grze vs 1,5 m).

## 3. Mapillary (D42) — co fotografować najpierw

Mapillary (CC BY-SA 4.0) wolno używać jako referencji ulicznej z atrybucją. API `graph.mapillary.com` wymaga tokenu (konta), więc **pokrycia nie sprawdzono automatycznie**. W każdym wierszu jest link `Mapillary` (zoom 17) do ręcznego sprawdzenia, zielone/niebieskie linie na mapie = pokrycie.

Jak decydować: jeśli w miejscu jest **świeże (ostatnie 2-3 lata) i ostre** zdjęcie z właściwego kierunku → ujęcie zdobędziemy z Mapillary, Ty zrób je ostatnie (traktuj jako P2). **Brak pokrycia lub stare/rozmyte** → fotografuj najpierw. Mapillary zwykle **nie nadaje się do tekstur** (fasady z ukosa, kompresja, dziwne kąty), więc fasady i nawierzchnie fotografuj niezależnie od pokrycia. Własne zdjęcia nie wymagają atrybucji, zdjęcia Mapillary — tak (lider dopisze w `docs/LICENSES.md`). Google nadal zakazany.

Kolumnę `Mapillary?` możesz uzupełnić w manifeście (sekcja 4): `tak-swieze / tak-stare / brak / nie-sprawdzono`.

## 4. Gdzie wrzucić pliki i jak nazwać

Folder (poza gitem, jest już w `.gitignore`): **`Data/raw/photos/owner/`**. Jeden folder, bez podfolderów (lub jeden podfolder na dzień: `2026-11-12/`).

Nazwa pliku: `NR_TYP_krotki-opis_RRRRMMDD_GGMM[_wariant].jpg`, gdzie NR = numer ujęcia z tabeli (2 cyfry), TYP = K/F/N/Z/L/P/D.
Przykłady: `06_F_hala-rampy-sciana_20261112_1120.jpg`, `06_F_hala-rampy-sciana_20261112_1121_zblizenie2.jpg`, `48_N_zebra-putry_20261112_1305_gora.jpg`. Zdjęcia dodatkowe bez numeru: `X_TYP_opis_data.jpg`. Oryginały (HEIC/RAW) zostaw z tą samą nazwą bazową. Wideo: `V_andersa-pasazer_20261112_1210.mp4` (kierunek, data).

Manifest: plik **`Data/raw/photos/owner/manifest.csv`** — jedna linia na zdjęcie (lider/agent uzupełni, jeśli Ci łatwiej, możesz zostawić puste):
`plik, nr, data_czas, pogoda(pochmurno/slonce/zmierzch), wysokosc_m, azymut_deg, ogniskowa(1x/0.5x), mapillary(tak-swieze/tak-stare/brak/nie-sprawdzono), sa_ludzie_lub_tablice(nie/zakryte), uwagi`.
Agent doda SHA256 i wpis do `Data/SourceManifests/` (źródło: własne zdjęcia właściciela, licencja: własność autora, użycie komercyjne dozwolone przez autora). Dla `docs/LICENSES.md`: „zdjęcia własne właściciela, Białystok 2026”.

## 5. Kolejność i szacowany czas (WORKING_VALUE)

Trasa ma 2,4 km. Szacunek przy 2 osobach i samochodzie: **ok. 5-6 h łącznie w dwóch terminach** (dzień pochmurny ok. 4-5 h; zmierzch ok. 1 h).

| Etap | Co | Dojazd | Czas |
|---|---|---|---|
| A | Kwadrat Park + droga dojazdowa (jeśli jest zgoda) lub tylko z drogi publicznej | auto/spacer | 1,0-1,5 h |
| B | Rondo Bieżeństwa, wiadukt, zieleń wyspy, auta z parkingu | spacer 400 m | 1,0 h |
| C | Andersa: seria wideo z auta + chodnik przy bloku, strażą pożarną, przystankiem | auto + 3 przystanki | 1,0-1,5 h |
| D | Rondo Putry: kadry, wiadukt, zebra, zieleń | spacer wokół ronda | 1,0-1,5 h |
| E | Al. Tysiąclecia: wylot DK8/DK19, znak, zieleń | auto | 0,5 h |
| Zmierzch | Latarnie (nr oznaczone `Z+S`) na Andersa i Putry | auto | ok. 1 h |

Kolejność jazdy: od A do E (jak numery), wideo z Andersa po drodze. Przerwa na zdjęcia nawierzchni/kostki/studzienek w miejscach, gdzie akurat jesteś.

## 6. Tabele ujęć
Wiersze są posortowane wzdłuż trasy. `s` = odległość wzdłuż trasy startowej od początku (m). Link OSM pokazuje punkt na mapie openstreetmap.org.
