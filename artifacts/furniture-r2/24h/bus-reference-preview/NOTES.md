# Przygotowanie referencji przystanków do r3

To analiza do następnej rundy; implementacja r2 pozostaje zamrożona.
Źródło metadanych: Data/raw/mapillary/bialystok-industrial-c/manifest.jsonl.
Oryginały i ich licencje pozostają w istniejącym katalogu tylko do odczytu.

Obejrzano po zmniejszeniu do szerokości960:1628542400678420,339463879238809,
214816220453640,1109648749531087,518260422864360; dodatkowo kadr wycinka
214816220453640-shelter.jpg ma500px szerokości. Dwa pierwsze, mimo bliskości,
patrzą już za przystanek. Dwa ostatnie są nocne i nie pozwalają stwierdzić
braku wiaty. Proximity-only jest niewystarczającym kryterium selekcji.

214816220453640 pokazuje przystanek odpowiadający OSM5802408812: czerwona
rama i czerwony dach, oszklona ściana boczna, tablica przystankowa, ławka
oraz osobny czerwony obiekt po prawej. Nie utożsamiać go z koszem/słupkiem
bez lepszego ujęcia. Dach i proporcje obecnego prostego modelu wymagają
porównania w tej samej pozie; z tego zdjęcia nie wyprowadzono wymiarów.

Generator misc_points obecnie bezwarunkowo dokłada wiatę i kosz do każdego
przystanku dopasowanego do drogi. Źródła mają20 punktów OSM i dodatkowe BDOT;
nie wszystkie posiadają shelter/bin. Brak tagu nie oznacza braku obiektu.
Plan r3: rozpoznać kilka rodzin wiat ze zdjęć, zachować pochodzenie wariantu,
nie dodawać brakujących obiektów na podstawie samego typu przystanku,
sprawdzić Low/High, kolizje i budżet. Bez zmian barier drogowych.

Uzupełnienie po dalszych oględzinach: zdjęcie1911352299378570 z2024-07-26
potwierdza utrzymanie czerwonej ramy wiaty przy5802408812. Czerwony obiekt
po prawej ma kształt hydrantu z bocznym przyłączem; nie zaliczać go do koszy
ani słupków. Zdjęcia580726859527979 i258203226048198 z2020-08-15 pokazują
inną wiatę przy Fabryce Dywanów dopiero przy prawej krawędzi kadru; częściowe
ucięcie nie pozwala jeszcze ustalić pełnego profilu.1134567850380236 jest
nocne i nie stanowi wystarczającego dowodu konstrukcyjnego.
Shortlista zawiera teraz osobne kandydatury z UTC08–14. To tylko heurystyka
wyboru metadanych: jasność i widoczność zawsze wymagają obejrzenia zdjęcia.
