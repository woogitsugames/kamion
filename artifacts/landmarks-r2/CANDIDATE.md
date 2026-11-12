# Kandydat po obejrzeniu baseline

Nie zastosowano. Źródła muszą pozostać bez zmian do ukończenia baseline.

W konfiguracji underdeck jawne `set.stairs_enabled=false` z uzasadnieniem braku
potwierdzonego dojścia. Plan zapisuje dwie puste listy zamiast biegu. Emisja wymaga
równocześnie true w bieżącej konfiguracji i parametrach spec, aby stary cache
nie odtworzył schodów przecinających ekran. Nie przesuwać ekranów ani kapy.

W `_prism` opcjonalny argument `bevel_mat`, domyślnie bez zmian. Pierścień ma
szerokie boki 0/2/4/6 i ścięcia 1/3/5/7. Rozdzielić istniejące trójkąty ścian
na dotychczasowy pigment i istniejący `bridge_concrete`; wierzch zostaje dotychczasowy.
Nie dodawać powierzchni ani trójkątów. Kolizja zachowuje jeden kompletny zestaw
V/UV/T, niezależnie od rozdziału wizualnego. Flaga `set.unpainted_chamfers` dotyczy
tylko własnych kolumn underdeck, nie głowic ani oryginalnych podpór generycznych.

Pigment dopiero po sprawdzeniu świeżych ROI: propozycja liniowa [0.46,0.34,0.135]
wobec [0.46,0.40,0.17], WORKING_VALUE. Ewentualny blok w materials.py wyłącznie
addytywny, za flagą własnej konfiguracji `pier_paint.enabled`, z bezpiecznym
domyślnym pigmentem, bez zmian innych materiałów. Nie używać SD mieszanego ROI
jako celu dla proceduralnego szumu. Zdjęcie nie mierzy reflektancji.

Testy: zachować tożsamość obiektów części pomostu i V/T/UV/UV1/COL; testować
stary spec ze schodami i wyłączoną bieżącą flagą, również odwrotną rozbieżność;
sprawdzić rozdział ścięć (8 trójkątów betonu), niezmienny komplet kolizji,
normale na zewnątrz, brak degeneracji, ten sam zestaw nazw materiałów.
Test wygenerowanego spec ma akceptować jawne wyłączenie schodów, sprawdzając
puste listy zamiast wymagać dodatniej liczby biegów. Uruchomić pojedynczy plik
pod heavy po regeneracji, a pełny GIS dopiero na końcu rundy.

Budżet: pełny kontrolny inwentarz + 10 własnych kamer, Low i High w obu światłach;
draws mesh +0 i draws instancji osobno, suma tris <=+2% w KAŻDEJ kamerze Low.
Materiały ścięć są już obecne w głowicach, ale +0 draws trzeba zmierzyć w Unity.
