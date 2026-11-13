# Źródła — paczka P11 „Dojlidy / Krywlany"

Data dostępu do wszystkich zewnętrznych źródeł: **2026-11-13**. Wszystkie współrzędne WGS84 (EPSG:4326).

Zgodnie z zasadami zadania **nie użyto** Google Maps / Street View / Earth / 3D Tiles (zakaz źródeł Google). Nie zgadano kluczy API: Mapillary pominięto z powodu braku tokenu.

## 1. Wikimedia Commons API — materiał podstawowy

* Endpoint geosearch: `https://commons.wikimedia.org/w/api.php?action=query&list=geosearch&gscoord=…&gsradius=…&gslimit=…`
* Endpoint metadanych: `https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|extmetadata|size&…`
* Sonda geosearch obejmowała kafel oraz korytarze przydrożne (promień do 2 km poza bbox); łącznie przeanalizowano metadane ~1230 plików.
* Z każdego pliku pobierano: EXIF GPS (szerokość/długość), `DateTimeOriginal`, licencję, autora, wymiary.
* Kryteria akceptacji: pozycja ≤ 25 m od osi drogi OSM, JPG, licencja komercyjna, rozdzielczość skalowana do ≤ 1600 px.
* Wynik: **143 zdjęcia w statusie SOURCED** (wykorzystane w paczce) + 8 odrzuconych z Commons (duplikaty detali, PNG, przekroczenie 25 m od osi, poza kaflem).
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
* API **nie zwróciło azymutu ani daty** dla tych pozycji → status **UNVERIFIED** (wiersze P11-146, P11-149, P11-150 w manifest.csv). Nie są częścią materiału SOURCED.

## 4. KartaView

* Endpoint publiczny: `https://api.kartaview.org/…` (sondy bbox w kaflu i korytarzach, 20 zapytań).
* **0 sekwencji / 0 zdjęć** w badanym zakresie → brak materiału.

## 5. Openverse API — tylko referencje

* Endpoint: `https://api.openverse.org/v1/images/?q=…` (sondy: „Dojlidy Białystok", „Lotnisko Krywlany", „Plaża Miejska Dojlidy").
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

## Licencje materiału SOURCED (143 zdjęcia)

| Licencja | Liczba |
|---|---|
| CC0 | 122 |
| CC BY-SA 4.0 | 7 |
| CC BY-SA 3.0 | 6 |
| CC BY-SA 3.0 (pl) | 4 |
| CC BY 3.0 (pl) | 2 |
| CC BY 3.0 | 2 |

Wszystkie dopuszczalne komercyjnie (bez NC/ND). Atrybucja: autorzy ujęć wpisani w `manifest.csv` (kolumna `autor`); dla CC BY-SA materiał dziedziczy wymóg share-alike przy derywatach.

## Paczka plików (poza gitem)

* Archiwum: `mistral-p11-dojlidy-photos-files.zip` — **57 387 487 B** (54,7 MB), 143 pliki `files/P11-NNN.jpg`, każdy ≤ 1600 px na dłuższym boku.
* SHA256: `13f22c268abbd15ff1834caca07c83f33e5825a59d6d84c5028a108fc650686c`
* Katalog `files/` jest w `.gitignore` — zdjęcia nie trafiają do repozytorium; archiwum publikowane jest poza gitem (karta pobrania załączona do PR).

## Kontrola jakości

* Samokontrola 20 % z jawnym seedem: `audit_20_percent.json` (seed **20261113**, 31 z 154 wierszy = 20,1 %, wynik 31/31 OK).
* Reguły opisów: bez marek producentów ciężarówek; pozycja WGS84, `kierunek_deg` (UNVERIFIED), `sezon`, `pora_dnia` — obowiązkowe w każdym wierszu manifestu.
