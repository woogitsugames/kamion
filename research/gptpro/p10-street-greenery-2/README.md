# P10 — street-greenery-2 (uzupełnienie G7: zieleń przyuliczna Białegostoka)

Pakiet: `gptpro-p10-street-greenery-2.zip` · data: 2026-11-13 · zadanie P10 (slug: street-greenery-2), uzupełnienie pakietu `research/g7-street-greenery/`.

## Cel

Uzupełnić dane o zieleni przyulicznej dla świata gry Kamion (Białystok 1:1):
1. rejestr drzew w pasach drogowych Białegostoku w otwartych źródłach (liczby gatunków i wieku/obwodu) — a w razie braku: gotowy wniosek o informację publiczną do ZDM (nie wysłany);
2. drugi sezon zdjęć dla ulic: Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka, Wileńska, Grodzieńska, Racławicka, Łańcucka;
3. żywopłoty/ogrodzenia zielone przy domach jednorodzinnych (Łańcucka i podobne) — gatunki, wysokości, gęstość pokrycia na ≥20 odcinkach po 100 m;
4. młode drzewa przy Andersa/Al. Tysiąclecia — liczba na 100 m dla ≥10 odcinków, wiek sadzenia, gatunek (zamknięcie statusu UNVERIFIED liczbą z metodą);
5. wymiary dojrzałych drzew 10 najczęstszych gatunków przyulicznych Podlasia (katalogi szkółek tylko jako źródło wymiarów).

## Metoda

**Dane przestrzenne.** Oś ulic: `roads.graph.json` (graf OSM/BDOT10k, EPSG:2180, tile `bialystok-industrial-c`, bbox [776971, 595199, 779019, 597247]). Korony: detekcja na ortofotomapie GUGiK z 2024-05-27 (GSD 0,25 m, licencja CC BY 4.0) — 3500 koron, promień 0,7–6,5 m, flaga iglaste/liściaste. Transformacja EPSG:2180↔WGS84: wzory*Snydera, zwalidowane na narożnikach tile (roundtrip 0,004 m).

**Segmentacja (zad. 3).** Dla każdej ulicy oś dzielono na odcinki po 100 m wzdłuż skonsolidowanej polilinii (licząc kilometraż od południowego końca, tj. rosnąco ze współrzędną N; ulice o 2 komponentach w tile numerowano łącznie po sortowaniu po szerokości geograficznej). Z odcinków <20 m (fragmenty przecięcia tile) zrezygnowano. Metryka **gęstości pokrycia**: na osi odcinka próbkowanie co 5 m; odsetek próbek, w których w buforze 8 m od punktu osi leży ≥1 korona (r≥0,7 m) = % pokrycia odcinków. Dodatkowo liczba unikalnych koron w buforze 8 m odcinka. Bufor 8 m odpowiada pasu drogowemu z ogrodami przed domami jednorodzinnymi. 9 ulic z zadania ma w tile łącznie tylko 1921 m osi (20 pełnych odcinków) — dlatego, zgodnie z „Łańcucka i podobne", dodano ulice **Buska** (living_street), **Olsztyńska** i **Michała Motoszko** (obie residential, rejon Białystoczka, w całości w zasięgu detekcji): razem **27 pełnych odcinków 100 m** (w manifeście 37 wierszy: pełne + końcowe ≥20 m). Charakter zabudowy jednorodzinnej ulic dodatkowych: ESTIMATED wg OSM/BDOT10k/ortofoto — dedykowanych zdjęć brak (weryfikacja wzrokowa UNVERIFIED). Uwaga: ul. Kombatantów (642 m) odpada — biegnie poza zasięgiem detekcji koron (patrz „Braki i niepewności").

**Młode drzewa (zad. 4).** Kadry 2022–2026, z których liczono drzewa: ortofoto GUGiK 2024-05-27 („kadr 2024") uzupełnione zdjęciami Commons 2022–2024 (P10-109..114, P10-106/107). Liczenie: korony liściaste (conifer=0) o promieniu 0,7–2,0 m ze środkiem w buforze 20 m od osi jezdni, w oknach ~100 m (deduplikacja dwóch jezdni alei: grupowanie po zaokrąglonej szerokości, w grupie maksimum). Wiek sadzenia: zima 2021/22 (zakończenie przebudowy Al. Tysiąclecia 31.01.2022, posadzono 74 drzewa i 109 krzewów — patrz ustalenia) oraz potwierdzenie na zdjęciu G7-P10 z 25.07.2022 (młode drzewko 4–5 m, trzy paliki). Status poprzedni UNVERIFIED zamknięto jako ESTIMATED z podaną metodą (liczby w kolumnie `gęstość_na_100m`).

**Sezon i pora dnia (zasada B).** Fenologia wg daty EXIF (DateTimeOriginal, czas lokalny fotografa): V–IX = „liście", X–XI = „bez liści (jesień)", XII–II = „bez liści (zima)", III–IV = „bez liści (przedwiośnie)". Obecność śniegu na kadrze zimowym nie była weryfikowana wzrokowo — oznaczono „UNVERIFIED". Pora dnia: 05:00–11:00 rano, 11:00–15:00 południe, 15:00–20:00 wieczór, 20:00–05:00 zmierzch/noc. Wszystkie zdjęcia w manifeście mają obie kolumny wypełnione (lub jawnie UNVERIFIED dla ortofoto).

**Współrzędne i kierunek.** WGS84, 6 miejsc. Zdjęcia Commons: pozycja z API Wikimedia (prop=coordinates, szablony {{Location}}) — wszystkie 13 pozycji pobrano i potwierdzono API. Kierunek patrzenia: Commons nie podaje azymutu — kierunek_deg = UNVERIFIED (opis w uwagach). Ortofotomapa: nadir (UNVERIFIED jako kierunek patrzenia). Segmenty: pozycja = środek odcinka na osi.

**Licencje.** Do `files/` pobrano wyłącznie zdjęcia Wikimedia Commons na licencji **CC0 1.0** (Rakoon) — dopuszczalne komercyjnie; pomniejszone do 1600 px dłuższego boku, JPG. Ortofotomapa GUGiK: CC BY 4.0 (dane.gov.pl); osie OSM: ODbL. Dokumenty urzędowe BIP: art. 4 ust. 2 ustawy o prawie autorskim. Artykuły prasowe i naukowe oraz karty Ebben: tylko fakty i cytaty (≤25 słów) w manifeście — plików nie pobrano.

## Najważniejsze ustalenia

- **Rejestru drzew przyulicznych Białegostoku w otwartych danych miasta nie ma** — potwierdzone bezpośrednio przeglądem usług ArcGIS miasta (folder Środowisko zawiera wyłącznie warstwy: Pomniki przyrody, Cieki, Lasy, Ogródki działkowe, Parki, Rezerwaty, Skwery i zieleńce, Wody stojące; brak warstwy drzew; usługi Hosted/WFS wymagają tokenu). Obwieszczenia BIP o usunięciu drzew nie zawierają gatunków ani obwodów (przykład: 11 szt. drzew, Mazowiecka 41/Zwierzyniecka, sygn. DGK-II.6131.1014.2026.JG). Wniosek o informację publiczną przygotowano (poniżej) i **nie wysłano** zgodnie z zadaniem.
- **Jedyne dostępne zestawienie z liczbami gatunków i dendrometrią to publikacja naukowa** (Łaska 2015, DOI 10.1515/biorc-2015-0013): inwentaryzacja 2011 — 837 drzew/krzewów, 36 gatunków w 4 transektach przy głównych drogach. Transekt Andersa (DK8, 53°8′57.33″N 23°10′25.44″E): 178 osobników, 15 gatunków (dominują Acer negundo 35, Acer platanoides 30, Crataegus monogyna 25); obwody na 120 cm: 0–50 cm — 22,2%, 51–100 cm — 77,8%; wysokości 2,1–5 m — 27,8%, 5,1–10 m — 72,2%; szpalery 3-rzędowe w odległości 2/10/15 m od jezdni.
- **Nasadzenia miejskie są, ale bez rejestru**: przebudowa Al. Tysiąclecia (Strabag, zakończona 31.01.2022) — „posadzono 74 drzewa oraz 109 krzewów"; program „Spacer wśród drzew" (BO 2025) — grusza 'Chanticleer' i wiśnia 'Amanogawa' przy Sienkiewicza/Sikorskiego/św. Jerzego; II edycja w BO 2026 (3 mln zł) zakwalifikowana do głosowania.
- **Młode drzewa Al. Tysiąclecia (zad. 4)**: w 12 badanych oknach ~100 m (od południa, lat 53,1498–53,1605) detekcja ortofoto 2024 wykryła łącznie **64 małe korony liściaste (0,7–2,0 m) w buforze 20 m**, w tym 16 w buforze 10 m od osi; największe zagęszczenia: 18 szt./100 m (okno przy 53,1575), 12 (53,1558), 10 (53,1524). Rząd wielkości spójny z 74 drzewami Strabaga na całym odcinku inwestycji (detektor nie odróżnia młodych drzew od krzewów — wartości mogą zawierać część z 109 krzewów). Okna na północ od 53,161 (poza odcinkiem inwestycji): 0 szt./100 m. **Andersa**: w zasięgu detekcji (skrzyżowanie z aleją) — 0 młodych koron w buforze 20 m; większa część Andersa w tile biegnie na wschód od zasięgu detekcji ortofoto — szpalery Andersa potwierdza dopiero publikacja Łaski (2011). Wiek nasadzeń alei: zima 2021/22 (SOURCED); gatunek: UNVERIFIED (liściaste wg klasyfikatora).
- **Żywopłoty (zad. 3)**: pokrycie zielenią przydomową (bufor 8 m) jest wysokie na większości odcinków ulic osiedla: 100% odcinka Racławicka-1 i Wołkowyska-2/Lidzka-1/Kowieńska-1 (~95%), a najniższe na Busce (0–59% w 3 środkowych odcinkach), Grodzieńskiej-2 (26%), Olsztyńskiej-1 (22%) i Kowieńskiej/Motoszko-2 (10–36%). Gatunek żywopłotu rozpoznano (ze zdjęć G7: proporcja do płotu, ±0,5 m) tylko przy wlotach Łańcuckiej/Racławickiej: **żywotnik (Thuja), 2,0–3,0 m**; pozostałe odcinki: gatunek i wysokość UNVERIFIED (kandydatury: żywotnik/ligustr/grab/świerk — rozpoznanie wymaga wizji).
- **Drugi sezon zdjęć (zad. 2)** — dostępność w otwartych źródłach:
  - **Skidelska, Świsłocka: brak jakichkolwiek zdjęć** (0 sezonów; w promieniu 80 m od osi nie ma ani jednego kadru Commons),
  - **Kowieńska, Lidzka, Wileńska, Wołkowyska, Grodzieńska, Racławicka: tylko jeden sezon** (kwiecień 2024, seria Rakoon CC0 — drzewa bez liści),
  - **Łańcucka: dwa sezony „bez liści"** — kwiecień 2024 oraz **zima 2020-12-23** (P10-101, nazwa pliku „ul. Łańcucka", kadr z geotagu na skrzyżowaniu z Al. Tysiąclecia); pełnej zieleni (lato) nadal brak,
  - wzdłuż **Al. Tysiąclecia** (tło ulic zadania) sezony są: jesień 2021 (P10-103/104), zima 2022/2024 (P10-105/112), lato V/VI 2024 (P10-106/107), VII 2022 (G7-P10, nie duplikowano), zima XII 2020 (P10-102),
  - **Andersa**: kadry zimowe 2022/2024, letni 2023, jesienny 2024 (P10-109..114) — do dyspozycji dla zad. 4.
  - Rekomendacja dla produkcji: ulice osiedla domów jednorodzinnych wymagają własnej sesji zdjęciowej (lato) — jedyne wolne źródło wielosezonowe to Mapillary, do którego nie było tokenu ani przeglądarki (patrz braki).
- **Wymiary dojrzałych drzew (zad. 5)** — karty Ebben TreeEbb (sufitowe wymiary osobników dorosłych, nie średnia miejska): lipa drobnolistna 20–25 m wysokości / 10–15 m szerokości, klon pospolity 20–30/15–20, klon jawor 25–30/20–25, brzoza brodawkowata 15–20/6–12, jesion wyniosły 25–30/20–25, topola kanadyjska 25–30/15–20, dąb szypułkowy 25–35/20–30, kasztanowiec 20–30/16–20, jarzębina 8–12/6–8, świerk pospolity 30–55/8–10. Pełne cytaty i kształty koron w manifeście (P10-401..410).

## Braki i niepewności

- **Mapillary niedostępne**: brak tokenu API i przeglądarki w środowisku wykonawczym — zgodnie z zasadą A paczki 02 kluczy nie zgadywano; pozycje z Mapillary nie powstały. Panoramax (CC BY-SA 4.0) ma 55 kadrów z 2019-09-01 wzdłuż Andersa (przed nasadzeniami — tylko referencja „before"; uwaga share-alike: używać jako referencji, nie jako tekstury).
- **Treści kadrów nie oglądano** (środowisko bez podglądu obrazu): pozycje, daty i licencje są SOURCED (API Commons), ale to, co faktycznie widać na kadrze (gatunki, śnieg, obecność młodych drzew) — UNVERIFIED.
- **Detekcja koron obejmuje tylko zachodnią część tile** (EPSG:2180 e ≤ ~777 670, tj. lon ≤ ~23,156) — wyniki dla Andersa za tym pasem są poza zasięgiem metody.
- Klasyfikator koron nie rozróżnia młodych drzew od krzewów (r 0,7–1,25 m) ani gatunków liściastych.
- Obwieszczenia BIP to skany bez warstwy tekstowej (OCR nie wykonano); treść odczytano z wersji DOCX jednego obwieszczenia.
- Wymiary Ebben to sufit dla hodowli szkółkarskiej (drzewa przyuliczne rzadko osiągają te wartości) — traktować jako maksimum, nie średnią.
- Seria Commons 2025-02-08 (7 kadrów) nie ma współrzędnych w metadanych — nie przypisano ich do ulic.

## Samokontrola 20% (jawny seed)

- Seed: **20261113**; losowanie: `random.Random(seed).sample(ids, ceil(0.2*n))` po WSZYSTKICH 82 pozycjach manifestu; sprawdzono **17 pozycji (20,7%)**.
- Sprawdzono: dostępność URL (HTTP 200; dla pozycji bez URL — n/d zgodnie z opisem), obecność licencji, współrzędne w granicach Białegostoka, obecność pliku w `files/` (dla zdjęć), zgodność statusu.
- Wynik: **17/17 OK, 0 uwag** (plik `audit_20_percent.json`). Kontrola dodatkowa: żadna pozycja manifestu nie ma szerokości geograficznej poza pasem 53°N (test programowy zamiany lat/lon).
- Dodatkowo: wszystkie 13 pozycji zdjęciowych miały współrzędne potwierdzone z API Wikimedia niezależnie od losowania.

## Wniosek o informację publiczną (NIE WYSŁANO)

> **Wniosek o udostępnienie informacji publicznej**
> (ustawa z dnia 6 września 2001 r. o dostępie do informacji publicznej, t.j. Dz.U. z 2022 r. poz. 902)
>
> Do: Zarząd Dróg Miejskich w Białymstoku (za pośrednictwem BIP: bip.bialystok.pl; opcjonalnie: Wydział Geodezji i Kartografii / Wydział Ochrony Środowiska, Urząd Miejski w Białymstoku)
>
> Zwracam się z wnioskiem o udostępnienie informacji publicznej w zakresie **wykazu drzew rosnących w pasach dróg miejskich (ulicach) w granicach administracyjnych Białegostoku**, a w szczególności następujących danych dla każdego drzewa:
>
> 1. **gatunek** (nazwa łacińska i/lub polska);
> 2. **obwód pnia** (preferowana wysokość pomiaru 130 cm; jeżeli inna — proszę o wskazanie wysokości);
> 3. **współrzędne geograficzne** drzewa (WGS84 lub EPSG:2180; w razie braku — numer ulicy i nr porządkowy/nazwa najbliższej posesji);
> 4. **ulica** (nazwa), przy której rośnie drzewo, wraz z orientacyjnym położeniem (np. km/początek ulicy, strona);
> 5. jeżeli dostępne: szacowany **wiek/rok nasadzenia** oraz **wysokość**.
>
> Jeżeli zwierzchnictwo nad drzewami w pasach drogowych dzieli się pomiędzy jednostki (np. ZDM a Zarząd Zieleni Miejskiej), proszę o udostępnienie wykazu w części dotyczącej Pana/Pani jednostki oraz o wskazanie, do której jednostki skierować wniosek w pozostałym zakresie.
>
> Formę udostępnienia proszę: plik w formacie otwartym (CSV/XLSX/GEOJSON/SHP) przesłany pocztą elektroniczną na adres: ________________ (wariant: wydruk/dysk do odbioru).
>
> Proszę o bezpłatne udostępnienie informacji w terminie ustawowym (art. 13 ustawy).
>
> Podstawa prawna: art. 1, art. 2 i art. 13 ustawy z dnia 6 września 2001 r. o dostępie do informacji publicznej.
>
> Imię i nazwisko: ________________ · Adres do korespondencji: ________________ · Data: ________________ · Podpis: ________________
>
> (Wniosek przygotowany w ramach researchu pakietu P10 zgodnie z poleceniem zleceniodawcy — **nie wysłano**.)

## Zawartość paczki

- `README.md` — niniejszy plik;
- `manifest.csv` — 82 pozycje (21 kolumn); ID w konwencji `P10-<nr>`: 001–009 (rejestr/nasadzenia), 101–114 (zdjęcia Commons; brak 108 — zwolniony numer po rezygnacji z kadru bez geotagu), 201–237 (odcinki żywopłotów, 12 ulic), 301–313 (młode drzewa), 401–410 (wymiary gatunków);
- `files/` — 13 zdjęć JPG (max 1600 px, CC0 1.0, autor: Rakoon) — miniatury Commons przeskalowane z 1920 px (LANCZOS, JPEG q88);
- `sources.md` — lista źródeł z datą dostępu;
- `audit_20_percent.json` — wynik samokontroli (seed 20261113).

## Zastrzeżenia

Zdjęcia Commons są CC0 (domena publiczna) — dowolne użycie komercyjne. Ortofotomapa GUGiK: CC BY 4.0 — wymagane podanie źródła („© GUGiK"). Osie OSM: ODbL — przy użyciu danych wymagana atrybucja „© OpenStreetMap contributors". Mapillary/Panoramax (nie pobrano do paczki): CC BY-SA — używać jako referencji, nie jako tekstur. Brak marek/logo producentów ciężarówek w paczce.
