# P11 — zdjęcia referencyjne regionu Dojlidy / Krywlany (Białystok)

Zadanie **M47** z paczki 03 (`docs/owner/MISTRAL-TASKS-8-RESEARCH.md`), kontynuacja serii paczek referencyjnych (kolumny manifestu jak w paczce P1).
Gałąź: `research/mistral-p11-dojlidy-photos` (od `origin/main` = `d3982818`). Zakres zmian w repo: **wyłącznie** katalog `research/mistral/p11-dojlidy-photos/`.

## 1. Kafel

`Data/Regions/bialystok-dojlidy/region.yaml` **nie istnieje** na `main` (jest tylko `bialystok-industrial-c`); ADR 0166 w toku. Przyjęto założenie z zadania: kafel 2×2 km zawierający strefę SSSE Dojlidy i wschodni skraj lotniska Krywlany.

**Bbox (WGS84):** `lat 53.0960–53.1140`, `lon 23.1760–23.2060` (środek 53,1050 N; 23,1910 E).
**Bbox (EPSG:2180 / PL-CS92):** narożniki X (wsch.), Y (płn.):

| narożnik | lat | lon | X | Y |
|---|---|---|---|---|
| SW | 53,0960 | 23,1760 | 779 478,0 | 589 334,7 |
| SE | 53,0960 | 23,2060 | 781 484,7 | 589 452,3 |
| NW | 53,1140 | 23,1760 | 779 361,2 | 591 335,0 |
| NE | 53,1140 | 23,2060 | 781 367,1 | 591 452,6 |

W kaflu mieszczą się w całości: strefa SSSE Dojlidy (way 234838470), browar Dojlidy (way 221826898), osiedla Borsucza/Kormoranów/Niedźwiedzia, Park Centralny z pałacem Lubomirskich (NE) oraz **wschodni fragment lotniska Krywlany** (way 234838628 — pas/ogrodzenie od 23,176 do 23,1887; terminal, hangary i apron leżą na zachód, poza kaflem).

**O drogach z założenia zadania:** wg OSM w tym rejonie oznaczone są **DK19** (ref=19: Ks. Suchowolca, Dojlidy Fabryczne, rondo Meyera) i **DK678** (ref=678: Konstantego Ciołkowskiego). **DK65 nie jest oznakowana w bbox** (przebiega zachodnią częścią miasta), a **S19** (obwodnica) biegnie daleko poza kaflem — najbliższe węzły poza zakresem.

## 2. Drogi ciężarówek w kaflu (wg OSM, ODbL; eksport API 23,155–23,235 / 53,088–53,122)

| droga | highway | ref | hgv | rola dla ruchu ciężarówek |
|---|---|---|---|---|
| Jacka Kuronia | trunk | — | brak ograniczeń | oś W–E kafla, dojazd do SSSE i browaru |
| Dywizjonu 303 | trunk → primary | — | brak ograniczeń | krawędź zach./wsch., płd. ogrodzenie lotniska |
| Konstantego Ciołkowskiego | trunk/primary | 678 | brak | narożnik NW, wjazd od ronda Meyera |
| Księdza Stanisława Suchowolca | secondary → trunk | 19 | no (odcinki lokalne) | DK19, wlot wsch. + korytarz E |
| Dojlidy Fabryczne | secondary | 19 | no (odcinki) | DK19 północ, rondo Hasbacha |
| Adama Mickiewicza | tertiary | — | brak | oś N–S kafla (Sąd, Archiwum, SSSE) |
| Wiewiórcza | tertiary | — | no | północ kafla, zakłady |
| Myśliwska (tertiary N + unclassified S) | tertiary/unclassified | — | no (tertiary) | oś SSSE — bramy zakładów |
| Franciszka Karpińskiego | unclassified | — | brak | SSSE — bramy, place manewrowe |
| Karola Modzelewskiego | unclassified | — | brak | SSSE północ |
| Pułkownika Czesława Hake | unclassified | — | brak | zachód kafla |
| Żurawia | unclassified | — | no | szpital, BPN-T |
| Borsucza, Kormoranów, Sępia, Ptasia, Niedźwiedzia | residential | — | no (Kormoranów, Sępia, Ptasia, Niedźwiedzia) | osiedla SSSE — place manewrowe |
| service (bez nazw, np. #572484394, #482308216) | service | — | — | bramy zakładów, place składowe |

Ronda w obrębie/z przy granicy kafla: **rondo Artura Hasbacha** (19; Suchowolca × Fabryczne × Myśliwska — w kaflu), rondo Wünschego (zach., korytarz), rondo Meyera (19;678 — płn., korytarz). Wiadukty: w bbox **brak** — mosty na rzece Białej leżą tuż za płn. granicą (Dojlidy Fabryczne ~53,1147) i w korytarzu płn.

## 3. Metoda naboru

- **Źródła (zgodnie z twardymi zasadami):** Wikimedia Commons API (geosearch `gscoord`+`gsradius` po kaflu i korytarzach, `imageinfo` z EXIF GPS/licencją; dominujące licencje CC0/BY/BY-SA — wszystkie komercyjne), OSM API map (osie dróg, tagi), Panoramax API, KartaView API, Openverse API. GUGiK ortofoto nie było potrzebne do lokalizacji (OSM wystarczył). **Zakaz Google/Street View/Earth/3D Tiles dotrzymany.**
- **Wyniki sondaży ujemnych:** Panoramax — 0 kadrów w kaflu (3 w promieniu ~3 km, poza kaflem — wiersze UNVERIFIED w manifestie); KartaView — 0; Openverse — 2 kandydatów bez geolokalizacji (odrzucone) + 2 pliki Flickr **NC** (tylko referencja). Mapillary — brak tokenu w środowisku: **UNVERIFIED**, nie sondowano, kluczy nie zgadywano.
- **Pozycja:** WGS84 z EXIF GPS Commons (`lat`/`lon`, 6 miej. po przecinku).
- **Przypisanie do drogi:** odległość punkt–polilinia (equirectangular, φ0=53,105°; 111 132 m/° lat, 111 320·cos(53,105°) m/° lon) do osi OSM; kategorie `droga`/`skrzyżowanie`/`wlot`/`wylot`/`korytarz` — **≤ 25 m**; kategoria `rondo` — ≤ 27 m z powodu dokładności GPS EXIF (±10 m; dwa kadry wlotowe: 25,1 m i 26,3 m — adnotacja w wierszu). Kategorie `brama_zakład` i `obiekt` to POI (bramy, place manewrowe, dominanty) — bez reguły ≤ 25 m, rzeczywisty dystans do osi wpisany w `uwagi`.
- **Kierunek (`kierunek_deg`):** `UNVERIFIED` — EXIF `GPSImgDirection` nieobecny w 100 % plików Commons, a API Panoramax nie zwraca azymutu. **Luka podstawowa** — kierunki jazdy wymagają odsiewu z kamery produkcyjnej.
- **Poziom kamery:** kadry Commons to zdjęcia **piesze (~1,5–1,7 m nad jezdnią)**, nie 2,5 m oczu kierowcy — zapisane w `uwagi` każdego wiersza. To główna luka całego naboru; kompensowana liczbą ujęć i gęstością serii spacerowych.
- **Sezon** (z miesiąca EXIF): lato VI–VIII, jesień IX–XI, zima XII–II, wiosna III–V; faza liści adnotowana w `uwagi`. Status **ESTIMATED**.
- **Pora dnia** (z czasu EXIF, czas lokalny aparatu — strefa nieznana): rano 5–9, dzień 9–17, wieczór 17–21, noc 21–5. Status **ESTIMATED**.
- **Jakość 1–5:** heurystyka metadanych: baza 3, +1 za rozdzielczość ≥2500 px, −1 za <1200 px, +1 za ≤8 m od osi, −1 za >20 m (kategorie drogowe). Bez podglądu zawartości w procesie naboru — do weryfikacji wzrokowej przy montażu kamer.
- **JPG ≤ 1600 px:** miniatury `thumb.php …width=1600` (kadry pionowe skalowane do wys. ≤1600); wymiary potwierdzone parserem SOF, wszystkie pliki ≤1600 px na dłuższym boku.
- **Opisy bez marek producentów ciężarówek** — dotrzymane (jeden kadr z pojazdem pomocniczym opisany neutralnie, bez oznaczeń).

## 4. Tabela pokrycia (kategorie: droga, skrzyżowanie, wlot/wylot, rondo, brama_zakład, obiekt, korytarz)

143 kadry zaakceptowane + 11 wierszy odrzuconych/UNVERIFIED = **154 wiersze manifestu**; **143 pliki JPG** (bez duplikatów tytułów).

| droga / obiekt | kadry | kategorie | sezony | lata |
|---|---|---|---|---|
| Jacka Kuronia (+ browar, zakłady) | 27 | droga 13, skrzyż. 2, brama 8, obiekt 4 | jesień, lato, zima | 2012–2024 |
| Adama Mickiewicza (+ Sąd, Archiwum) | 20 | droga 13, skrzyż. 4, obiekt 3 | jesień, lato, zima | 2012, 2018–2024 |
| Wiewiórcza | 9 | droga, skrzyż. | jesień, lato | 2019, 2020, 2022, 2023 |
| Myśliwska | 3 | wlot, droga | jesień | 2022 |
| Franciszka Karpińskiego | 7 | droga, skrzyż. | lato | 2010, 2024 |
| Borsucza (+ Starostwo) | 8 | droga, obiekt | jesień, lato | 2020, 2022, 2023 |
| Kormoranów | 2 | droga | lato | 2020 |
| Żurawia (+ szpitale, BPN-T) | 5 | droga, obiekt | jesień, lato, zima | 2019, 2020 |
| Niedźwiedzia | 6 | droga | lato | 2022 |
| Karola Modzelewskiego | 3 | droga, skrzyż. | jesień | 2022 |
| Pułkownika Czesława Hake | 1 | droga | jesień | 2022 |
| Dywizjonu 303 (+ rondo Wünschego, Krywlany) | 12 | droga 2, skrzyż. 1, wlot 1, rondo 3, korytarz 2, obiekt 3 | lato | 2012, 2020, 2023 |
| Konstantego Ciołkowskiego | 4 | droga, korytarz | jesień, lato | 2015, 2022, 2023 |
| Rondo Artura Hasbacha (+ pałac) | 7 | rondo 5, obiekt 2 | lato, zima | 2008, 2012, 2020, 2022, 2023 |
| Rondo Meyera (+ Nowowarszawska) | 6 | rondo, korytarz | lato | 2021, 2023 |
| Ks. Suchowolca (rondo, domy przyfabryczne, korytarz E, park) | 12 | korytarz, obiekt | lato, zima | 2008, 2013–2015, 2020–2023 |
| Dojlidy Fabryczne | 5 | droga, korytarz | lato | 2020, 2021, 2023 |
| Dojlidy Górne (korytarz SE) | 4 | korytarz | lato | 2024 |
| Grabowa (korytarz S) | 2 | korytarz | lato | 2024 |

Wymóg „≥ 3 ujęcia na drogę (początek/środek/skrzyżowanie)" spełniają drogi główne z pełnymi seriami (Kuronia, Mickiewicza, Wiewiórcza, Karpińskiego, Borsucza, Żurawia, Niedźwiedzia, Dywizjonu 303 z korytarzem, Fabryczne z korytarzem). Wymóg „≥ 6 kadrów na rondo" spełnia rondo Hasbacha (7) i rondo Wünschego (6 z korytarzem zachodnim); rondo Meyera — 4 (korytarz). „Oba kierunki" — **nieweryfikowalne** (brak azymutów); zamiast tego zróżnicowane pozycje i serie.

## 5. Luki (uczciwie)

1. **Poziom kamery ~1,5–1,7 m (pieszo)** — brak materiału z 2,5 m oczu kierowcy we wszystkich dozwolonych źródłach dla tego kafla. Do kamery kontrolnej: kadry pomocnicze, nie kalibracyjne.
2. **Kierunki jazdy UNVERIFIED** — zero azymutów w EXIF/Panoramax API.
3. **Dywizjonu 303 w kaflu — tylko 3 kadry** (wschodni fragment nowy w OSM; seria zachodnia w korytarzu).
4. **Konstantego Ciołkowskiego w kaflu — 1 kadr** (NW narożnik; reszta poza bbox).
5. **Pułkownika Hake — 1 kadr**, **Kormoranów — 2**, **Myśliwska — 3 bez drugiego sezonu i bez pozycji południowej ≤25 m**, **Modzelewskiego — 3 (jeden sezon)**.
6. **Jeden sezon:** Karpińskiego, Kormoranów, Niedźwiedzia, Hake, Dywizjonu 303 (zima tylko narożnik Sądu przy Mickiewicza), Dojlidy Fabryczne, rondo Meyera, rondo Wünschego, Nowowarszawska, Dojlidy Górne, Grabowa.
7. **Lotnisko Krywlany: 0 kadrów w kaflu** (płoty/pas bez serii); jedynie 3 kadry hangarów z zachodu jako referencja poza kaflem.
8. **Wiadukty: 0** — w bbox nie ma obiektów mostowych; mosty na Białej tuż poza granicą płn. (potrzebny osobny mini-nabór przy rozszerzeniu kafla).
9. **Panoramax/KartaView: 0** w kaflu; **Mapillary: niesprawdzony** (brak tokenu).
10. Dwa kadry wlotowe ronda Hasbacha na granicy 25–26,3 m od obrysu (dokładność GPS EXIF; adnotacje w wierszach P11-081/P11-082).

## 6. 15 najlepszych kadrów do kamer kontrolnych (które miejsca gracz rozpozna)

| # | id | miejsce | dlaczego |
|---|---|---|---|
| 1 | P11-084 | rondo Hasbacha — wlot od DK19 | jedyne duże rondo w kaflu; charakterystyczny kształt i zieleń |
| 2 | P11-136 | Pałac Hasbachów przy rondzie | dominanta DK19, punkt nawigacyjny gracza |
| 3 | P11-094 | brama browaru od ul. Kuronia | rozpoznawalny wjazd na plant browarny |
| 4 | P11-121 | kominy browaru XIX–XX w. | widoczne z daleka nad drzewami — orient w całym kaflu |
| 5 | P11-063 | narożnik Sądu Rejonowego (Mickiewicza × Dywizjonu 303) | ciężki węzeł z charakterystyczną bryłą |
| 6 | P11-125 | Sąd zimą (II 2021) | ten sam węzeł bez liści — kontrola sezonowości |
| 7 | P11-059 | skrzyżowanie Kuronia × Mickiewicza | wjazd do SSSE od zachodu |
| 8 | P11-056 | ogrodzenie lotniska przy Dywizjonu 303 | wschodnia krawędź kafla, odlot pasa Krywlanów |
| 9 | P11-078 | zjazd z ronda Wünschego | pierwsze rondo po wjeździe od zachodu — punkt orientacyjny |
| 10 | P11-133 | hangar Krywlany (poza kaflem) | ikona lotniska; referencja dla modelu terminalu |
| 11 | P11-142 | pałac Lubomirskich od południa | widok z DK19 na Park Centralny |
| 12 | P11-128 | Starostwo Powiatowe przy Borsuczej | obiekt administracyjny SSSE, rozpoznawalna bryła |
| 13 | P11-129 | szpital uniwersytecki (Żurawia) | duży gmach przy skrzyżowaniu, punkt orientacyjny |
| 14 | P11-106 | brama cmentarza Proroka Eliasza | charakterystyczny łuk w korytarzu wschodnim (zima) |
| 15 | P11-092 | hala zakładu przy Kuronia — styczeń | SSSE zimą: place manewrowe bez liści, śnieg |

## 7. Pliki

- `manifest.csv` — 154 wiersze (143 SOURCED + 11 odrzucone/UNVERIFIED), kolumny jak paczka P1, id `P11-001…P11-154`.
- `sources.md` — źródła, licencje, daty dostępu, wyniki sondaży ujemnych, suma kontrolna archiwum.
- `audit_20_percent.json` — samokontrola 20 % (31/154), **seed 20261113**, wszystkie kontrole OK (SHA256, wymiary ≤1600 px, licencje komercyjne, dystanse, HTTP 200).
- `.gitignore` — `files/` wykluczone z gita (zdjęcia NIE trafiają do repo).
- **ZIP zdjęć:** `mistral-p11-dojlidy-photos-files.zip` — 143 pliki JPG, ~57 MB; **poza gitem** — publikowany przez kartę pobrania w opisie PR (SHA256 w `sources.md`). Wewnątrz: `files/P11-NNN.jpg` zgodne z manifestem.

## 8. Legenda statusów

`SOURCED` — pozycja/data z EXIF źródła (Commons), plik pobrany i zweryfikowany; `ESTIMATED` — wartość wyliczona (sezon, pora dnia, jakość) lub pozycja przybliżona; `UNVERIFIED` — nie do zweryfikowania w dostępnym API (kierunek dla wszystkich kadrów; pozycja/data Panoramax); `ODRZUCONE` — kadr odrzucony z powodem w kolumnie `odrzucone_powód` (licencje NC, brak GPS, duplikaty, poza zakresem, PNG).

---
*Data naboru: 2026-11-13. Wykonanie: Mistral (M47). Wszystkie licencje komercyjne (CC0 / CC BY / CC BY-SA); NC/ND wyłącznie jako linki „tylko referencja".*
