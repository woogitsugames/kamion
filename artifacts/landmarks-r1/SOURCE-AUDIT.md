# Audyt źródeł przed zmianą

Model `make_fire_station.py` zapisuje każdy narożnik ściany osobno w `MB.face`.
Samo `polygon.use_smooth = True` nie łączy normalnych pomiędzy tak rozdzielonymi
ścianami. Iglaki mają już jawne normalne radialne w `core_normals`, ale tuje ich
nie przekazują. To konkretna przyczyna pozostawania ostrych faset na Low przy
czterech bokach. Pierwszy kandydat poprawy: normalne radialne dla istniejącej
siatki tui, z pochyleniem według profilu. Bez nowych trójkątów i slotów materiału.
Wynik w renderze jeszcze niezweryfikowany.

W `sets_fire_station.py` tafle hali mają mnożnik wysokości 0,90–0,96, czyli tylko
6,7% różnicy albedo. Nie jest to mocny sygnał góra–dół wymagany przez fotografię.
Po baseline należy dobrać zakres osobno dla szkła hali, bez zmian tafli biur,
tynku i kontraktu `_Tint`. Wartości kandydata pozostają WORKING_VALUE.

Własne źródła igliwia `twig_diff.png` i `twig_alpha.png` są obecne i przeszły SHA-256
z `conifer_source.json`. Nie ma potrzeby pobierania nowego skanu. To pochodna
fir/conifer CC0, bez udawania zweryfikowanego skanu botanicznego świerka.

Produkcja remizy pozostaje bez zmian do ukończenia świeżego baseline.
