# Obserwacje źródłowe — wiata, bez zmiany modelu przed baseline

Źródło: Mapillary1911352299378570,2024-07-26, autor kino,CC BY-SA4.0.
Pełne metadane/hash w artefaktachr2/bus-reference-preview/provenance.json.
Wycięto450×430px z oryginału2048×1536, x1180,y880; bez generowania nowych pikseli.
Obejrzano crop450px. Rodzinę przy OSM5802408812 potwierdza też zdjęcie2018
214816220453640. To identyfikacja rodziny, nie pomiar metryczny obiektu.

Widoczne:czerwona rama, przeszklone boki i tył, lekko wygięty profil dachu,
poziome podziały ramy i niewielka ławka. ZnakD15 jest osobnym elementem,
podobnie hydrant po prawej. Reklamy/napisy i osoby nie są zasobem do gry.
Model bus_shelter obecnie:W4,D1,5,H2,5 m (wartości zastane, bez deklaracji
zgodności z lokalną wiatą), sześć pionowych podpór, płaski dach, ciemne
nieprzezroczyste shelter_glass i ciemna wspólna stal. Jeden pełnybox kolizji.

Największe kandydatury do korekty:profil i kolor rodziny przy potwierdzonych
lokalizacjach oraz widoczność przez szkło. Nie zmieniać globalnego steel_painted,
nie kolorować wszystkich23wiat z dwóch zdjęć. Wariant musi wynikać z jawnego
powiązania istniejącej instancji z referencją, bez zmian overrides/roads.
Nie usuwać wiat/koszy tylko dlatego, że brak tagu lub obiekt zasłania zdjęcie.
Budżet:porównać wszystkie236kadry, draws mesh/instancji osobno, Lowtris≤+2%.
Nie dodawać świateł ani przebiegów. Wymiary,alpha i barwa pozostają WORKING_VALUE
przed dopasowaniem zdjęcia; nie udawać fotometrycznej ani metrycznej kalibracji.

NASTĘPNY KROK:obejrzeć baselinefront/corner obu istniejących instancji,
potwierdzić ich położenie/orientację i zestaw materiałów. Dopiero wtedy kod r3.

Dodatkowo obejrzano983799980108126 (Wodociągi), podgląd960px:wiata nie jest wystarczająco widoczna, więc to nie jest potwierdzenie jej rodziny/koloru. Nie rozszerzać czerwonego wariantu na wszystkie instancje na podstawie tego ujęcia. Metadane ihash zachowano osobno.
