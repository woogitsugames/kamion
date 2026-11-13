# Źródła — paczka P11 „Dojlidy / Krywlany” (v2, M47-FIX)

Data dostępu do wszystkich zewnętrznych źródeł: **2026-11-13**. Wszystkie współrzędne WGS84 (EPSG:4326).

Zgodnie z zasadami zadania **nie użyto** Google Maps / Street View / Earth / 3D Tiles (zakaz źródeł Google). Nie zgadano kluczy API: Mapillary pominięto z powodu braku tokenu.

## 1. Wikimedia Commons API — materiał podstawowy

* Endpoint geosearch: `https://commons.wikimedia.org/w/api.php?action=query&list=geosearch&gscoord=…&gsradius=…&gslimit=…`
* Endpoint metadanych: `https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|extmetadata|size&…`
* Sonda geosearch obejmowała kafel oraz korytarze przydrożne (promień do 2 km poza bbox); łącznie przeanalizowano metadane ~1230 plików.
* Z każdego pliku pobierano: EXIF GPS (szerokość/długość), `DateTimeOriginal`, licencję, autora, wymiary.
* Kryteria akceptacji: pozycja ≤ 25 m od osi drogi OSM, JPG, licencja komercyjna, rozdzielczość skalowana do ≤ 1600 px.
* Wynik: 143 kandydatów pobranych w v1; **po oględzinach (2026-11-13, M47-FIX) 135 zdjęć w statusie SOURCED** — 8 dodatkowo odrzuconych po obejrzeniu (P11-008 zbliżenie roślinności; P11-084 tablica z planem osiedla; P11-090/091/092 zdjęcia produktowe zabawkowego robota; P11-124/125 wnętrza Archiwum; P11-132 wnętrze szpitala) + 8 odrzuceń z etapu naboru (duplikaty detali, PNG, >25 m, poza kaflem).
* Kierunek zdjęcia: Commons **nie przechowuje GPSImgDirection** dla tych plików → `kierunek_deg` = UNVERIFIED we wszystkich wierszach manifestu (reguła: nie zgadujemy).

## 2. OpenStreetMap API — geometria dróg (ODbL)

* Endpoint: `https://api.openstreetmap.org/api/0.6/map?bbox=…`
* Zakres pobrania: bbox **23.155–23.235 / 53.088–53.122** (kafel + bufor 400 m), 6 chunków XML.
* Wyekstrahowano osie dróg `highway=trunk/primary/secondary/tertiary` oraz `highway=service` (strefa przemysłowa, `hgv=yes/designated`) — użyte do przypisania zdjęć do dróg (kryterium ≤ 25 m od osi) i do tabeli dróg w README.
* Licencja danych: ODbL (OpenStreetMap contributors).

## 3. Panoramax (CC BY-SA 4.0)

* Endpoint: `https://api.panoramax.xyz/api/items/search?bbox=…` (bez tokenu, warunki API pozwalają na dostęp publiczny).
* **0 kadrów w kaflu i korytarzach.** Najbliższe 3 kadry leżą ok. 3 km od bbox:
  * `68ed5b23-adc6-44de-a6f1-6ff4a060c5dc` — 42 Pułku Piechoty (ok. 53.1365, 23.2495)
  * `b8b97887-e204-4c13-8764-ae49241ad5a7` — 42 Pułku Piechoty (ok. 53.1365, 23.2495)
  * `4d84fb34-70b1-4921-b941-bd84697dd8da` — ok. 53.1260, 23.1520
* API **nie zwróciło azymutu ani daty** → status **UNVERIFIED** (wiersze P11-146, P11-149, P11-150). Nie są częścią materiału SOURCED.

## 4. KartaView

* Endpoint publiczny: `https://api.kartaview.org/…` (sondy bbox w kaflu i korytarzach, 20 zapytań).
* **0 sekwencji / 0 zdjęć** w badanym zakresie → brak materiału.

## 5. Openverse API — tylko referencje

* Endpoint: `https://api.openverse.org/v1/images/?q=…` (sondy: „Dojlidy Białystok”, „Lotnisko Krywlany”, „Plaża Miejska Dojlidy”).
* Kandydaci **bez geolokalizacji w metadanych** (wymagane WGS84) — tylko referencja:
  * [Lotnisko na Krywlanach](https://commons.wikimedia.org/w/index.php?curid=20463837) — Commons, CC BY-SA 3.0 (P11-151)
  * [20140822 Dojlidy Białystok - 14807933740](https://commons.wikimedia.org/w/index.php?curid=139832849) — Commons, CC BY 2.0 (P11-152)
* Licencje **NC** — tylko referencja, wykluczone z materiału gry:
  * [Plaża Miejska (City Beach) Dojlidy — flickr 36250032293](https://www.flickr.com/photos/54182068@N00/36250032293) — CC BY-NC-SA 2.0 (P11-153)
  * [Plaża Miejska (City Beach) Dojlidy — flickr 37057453145](https://www.flickr.com/photos/54182068@N00/37057453145) — CC BY-NC-SA 2.0 (P11-154)

## 6. Mapillary

* **Brak tokenu API → status UNVERIFIED, nie sondowano.** Nie zgadywano kluczy. Ponowna próba możliwa po dostarczeniu tokenu.

## 7. GUGiK (ortofotomapa)

* Niewykorzystana w paczce zdjęć — geometrię i lokalizację w pełni pokrywa OSM; ortofoto służy w projekcie do weryfikacji lokalizacji obiektów, nie jako źródło kadrów.

## 8. Przeliczenie współrzędnych (M47-FIX)

* Kolumna `w_kaflu_0166` wymagała przeliczenia WGS84→**EPSG:2180 (PL-CS92)**. Pakiet **pyproj był niedostępny** w środowisku wykonawczym poprawki (instalacje zablokowane) → wykonano własną implementację odwzorowania Transverse Mercator (elipsoida GRS80, λ0=19°, k0=0,9993, FE=500 000 m, FN=−5 300 000 m), zweryfikowaną na narożnikach kafla (zgodność <0,05 m).
* Kafel `bialystok-dojlidy` = prostokąt **[779019, 589055, 781067, 591103]** w EPSG:2180; `w_kaflu_0166`=true, gdy X∈[779019, 781067] i Y∈[589055, 591103].

## Licencje materiału SOURCED (135 zdjęć, po oględzinach)

| Licencja | Liczba |
|---|---|
| CC0 | 119 |
| CC BY-SA 3.0 | 6 |
| CC BY-SA 3.0 (pl) | 4 |
| CC BY-SA 4.0 | 4 |
| CC BY 3.0 | 2 |

Wszystkie dopuszczalne komercyjnie (bez NC/ND). Atrybucja: autorzy ujęć wpisani w `manifest.csv` (kolumna `autor`); dla CC BY-SA materiał dziedziczy wymóg share-alike przy derywatach.

## Paczka plików (poza gitem)

* Archiwum **v2**: `mistral-p11-dojlidy-photos-files-v2.zip` — **62 921 246 B** (60,0 MB), **135 plików** `files/P11-NNN.jpg` (bez 8 kadrów odrzuconych po oględzinach), każdy ≤ 1600 px na dłuższym boku.
* SHA256 (v2): `8fdf147738eb5e5a64cf56c84fc535432bac6794243437b0cd538fefc94668f0`
* Archiwum v1 (`mistral-p11-dojlidy-photos-files.zip`, SHA256 `13f22c268abbd15ff1834caca07c83f33e5825a59d6d84c5028a108fc650686c`, 57 387 487 B, 143 pliki) **zastąpione archiwum v2**: oryginalny plik roboczy v1 nie był dostępny w środowisku wykonawczym poprawki, więc v2 zbudowano ponownie z miniatur Wikimedia Commons (≤1600 px). Pliki mogą się różnić bajtowo od v1 (re-download); identyfikatory, opisy, licencje i źródła bez zmian.
* Katalog `files/` i archiwa ZIP są w `.gitignore` — zdjęcia nie trafiają do repozytorium; archiwum publikowane jest poza gitem (karta pobrania załączona do PR).

## Kontrola jakości

* **Oględziny (M47-FIX):** każdy z 143 kadrów obejrzany przez model wizyjny (2026-11-13); `punkt_opis` przepisany wg treści (obiekt, kadr, poziom kamery); nowe kolumny `typ_kadru` i `w_kaflu_0166`.
* Samokontrola 20 % z jawnym seedem: `audit_20_percent.json` (seed **20261113**, 31 z 154 wierszy = 20,1 %, wynik 31/31 OK; dla każdego wiersza zdanie „co widać” zgodne z manifestem).
* Reguły opisów: bez marek producentów ciężarówek; pozycja WGS84, `kierunek_deg` (UNVERIFIED), `sezon`, `pora_dnia` — obowiązkowe w każdym wierszu manifestu.
