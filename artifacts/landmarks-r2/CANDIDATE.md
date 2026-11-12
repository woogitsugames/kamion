# Kandydat po obejrzeniu baseline

Plan zapisany przed wdrożeniem. Pierwszy wariant zastosowano w d56c3db7,
po ukończeniu baseline i kontroli pozy. Wyniki wykonania śledzi STATUS.md.

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

## Ewentualna następna iteracja po obejrzeniu after

Recenzja HIL L2 wymienia również ciemniejszy dół 0,5–0,8 m i pionowe zacieki.
Nie są jeszcze wdrożone w pierwszym wariancie pigmentu/faz. Istniejący
WorldPBR obsługuje splash_h i runoff bez zmian shaderów (WorldPbrMaterials
wiersze około 302/328, WorldPBR około 635/648). UV0.y oznacza metry ponad
gruntem; UV1=(u w metrach, 1+głębokość poniżej głowicy/skala długości).
Kandydat może użyć istniejącego concrete_precast jako modulacji pod pigmentem,
splash_h=0,8 m i krótszego runoff, wyłącznie za kolejną własną flagą danych.
Zachować kontrakt _Tile, tint liniowy i weather lub runoff. Nie zmieniać
materiałów betonu ani innych fasad. Kolizja powinna zachować stare V/UV/T,
nawet gdy wizualny pigment dostanie UV pogody. Nie mnożyć czarnych geometrycznych
zacieków i teksturowych w tym samym miejscu; rozważyć zastąpienie tylko własnych
krótkich zacieków kolumn. Sprawdzić na Low/High przed wyborem rozwiązania.
Koszt dodatkowych próbek PBR na Low pozostaje UNVERIFIED bez telefonu;
nowych przebiegów i draws nie wolno dodawać. Najpierw ocenić pierwszy wariant.
