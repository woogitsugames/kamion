# Przejazdy bocznych dróg — kontrola pokrycia Mapillary

Odczyt: 15.11.2026, Europe/Brussels (CET). Wynik: **0 nowych kwalifikowanych kadrów przejazdu, 0 pobranych fotografii, 0 potwierdzonych urządzeń**. Manifest pozostaje bez rekordów zdjęciowych. Nie przypisano kategorii A–D ani znaków G-3/G-4, rogatek, sygnalizatorów, materiału paneli lub podsypki.

Punkty przejazdowe pochodzą z istniejącego K1 i `../data/osm-crossing-and-voltage-evidence.json` oraz rekordów 05-O01…O03. Bez nowego zapytania OSM/Overpass. Zwykły viewer Mapillary, jawny OpenStreetMap, bez API, tokenów, logowania, pobrań i zapisanych zrzutów. Pozycje w linkach poniżej to **centra mapy ustawione z danych OSM**, nie pozycje zdjęć. To rozpoznanie pokrycia, nie nowa inwentaryzacja przejazdów.

| Punkt K1/OSM | Sprawdzony publiczny widok | Wynik UI |
|---|---|---|
| 038 010 194, node 2070722551 | [Fasty, okolica Łyskowskiej](https://www.mapillary.com/app/?lat=53.1675484&lng=23.0564732&z=17&focus=map&mapStyle=OpenStreetMap) | Podkład pokazuje przecięcie bocznej drogi i toru; zielone linie pokrycia widoczne na Szosie Knyszyńskiej, brak widocznej sekwencji na tej drodze przez tor. Nie otwarto kadru przejazdu. |
| 038 010 956, node 2559254736 | [Okolica św. Franciszka z Asyżu](https://www.mapillary.com/app/?lat=53.1706241&lng=23.0464631&z=17&focus=map&mapStyle=OpenStreetMap) | Zielone linie na Szosie Knyszyńskiej, brak widocznej sekwencji na bocznej ulicy przez tor. Sąsiedni kadr Szosy `3989804994444440` załadował tylko mały podgląd; nie obejrzano go osobno w dużym widoku i nie opisano jako dowodu przejazdu. |
| 038 012 443, node 2335160489 | [Okolica Dzikowskiej, tryb All captures](https://www.mapillary.com/app/?lat=53.1755275&lng=23.0263884&z=17&focus=map&mapStyle=OpenStreetMap&captures=all) | Dodatkowo wybrano All captures; zaznaczenie w panelu i parametr `captures=all` były widoczne. Nadal brak widocznego pokrycia odcinka bocznej drogi przez tor; zielone linie biegną Szosą Knyszyńską. |

Nazwy ulic powyżej są odczytem podkładu UI, nie niezależnym potwierdzeniem aktualnej ewidencji. Brak zielonej linii w tych widokach **nie dowodzi nieistnienia fotografii w całym serwisie**. Ograniczony wynik obejmuje pokazane miejsca i sposób prezentacji viewera. Nie wnioskowano o stanie przejazdu z braku zdjęć.

Licencja obrazów Mapillary: odsyłacz do istniejącego audytu `../../04-dk65/mapillary-browser-round2/licence-check.json`; nie kopiowano audytu. Ponieważ nie uzyskano obrazu przejazdu, nie przypisywano daty ekspozycji z sąsiedniej sekwencji. Kategoria, aktualność i urządzenia pozostają UNVERIFIED.
