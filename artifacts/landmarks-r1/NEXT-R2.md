# Przygotowanie rundy wiaduktu

Nie zmieniono jeszcze źródeł wiaduktu. Runda r2 zaczyna się dopiero po REPORT r1,
kopii artefaktów, nowej gałęzi i merge main.

Schody: konfiguracja `viaduct_underdeck.json` ma wymiary WORKING_VALUE, a `plan()`
w `hero_bridge.py` próbuje wygenerować loty mimo braku potwierdzonej trasy do chodnika.
Recenzja HIL dopuszcza wyłączenie flagą. Dodać jawne `stairs_enabled: false` w danych,
nie generować stopni w spec i nie emitować ich ze starego spec przy wyłączonej fladze.
Nie projektować nowego biegu na oko i nie przesuwać ekranów.

Filary: obecny `pier_yellow` jest jednobarwnym World Surface; materiał istnieje także
na pierwotnych podporach. Najpierw świeży baseline po merge main, razem z własnymi
kamerami z `artifacts/viaduct-r10/{cameras,detail-cameras}.json` (kopie do r2).
Porównać do 7204 (CC0) i p45 (Mapillary, tylko referencja), zmierzyć ROI od nowa.
Stare pomiary HIL: render 107/99/58 i 80/75/47 sRGB, sd 9–13;
fotografia 79/67/37 i 81/69/42, sd 19–24. To różne warunki i orientacje, nie albedo.

Ważne nowe źródło: wcześniejszy reference7204.jpg ma tylko 960x640. Pobrano
oryginał reference7204-original.jpg 5520x3680 (10468810 B), SHA-1 zgodne z Commons
61364bef59ec622ecf0a89e5a4c6e9cf6678504a; source JSON z licencją CC0 i autorem.
Natywne wycinki underdeck-photo-details pokazują szerokie pionowe szare pasy na
ścięciach naroży filarów, obok ochrowych płaszczyzn, oraz słabsze zacieki od głowicy.
Znaczna część rozrzutu w ROI może wynikać z geometrii, różnych powierzchni i światła,
a nie z plam w samej farbie. Nie próbować osiągnąć sd 19–24 samym losowym szumem.
Sprawdzić po świeżym baseline przypisanie istniejących ośmiu ścian _prism:
odcinki 1/3/5/7 obwodu to bevel. Kandydat za flagą danych: odsłonięty beton na
potwierdzonych ścięciach, przy zachowaniu ochrowych głównych ścian. Reużycie
bridge_concrete powinno trafić do już istniejącej grupy oczepów w tym samym chunku;
potwierdzić draws +0 na wszystkich kamerach. Bez nowych trójkątów. Kolizja musi
pozostać jedną, niezmienioną pełną bryłą; nie zmieniać cudzych pierwotnych podpór.

Kandydat bez nowego shadera: `pier_yellow` z istniejącym skanem CC0 `plaster`
(modulation_set; painted_plaster_wall), flagą danych `weather`, `splash_h: 0.8`
i UV1 pod oczepem. W WorldPbrMaterials istnieją już _SPLASH oraz _RUNOFF na wszystkich
tierach; _Tile musi nadal spełniać set_tile || elementScan || atlas. Przed użyciem
sprawdzić źródło i pliki tego setu. Odcień i siła wariacji pozostają WORKING_VALUE.
Własny kod kolumn może przekazać UV0.y jako metry nad gruntem, UV1=(u,1+głębokość
poniżej oczepu). Zachować zerowe UV1 na powierzchniach bez źródła zacieków.
Materiał wspólny zmieniać tylko addytywnie za jawną flagą konfiguracji; nie zmieniać
kontraktu tint ani źródeł dróg. Nie zwiększać liczby materiałów ani przejść Low.

Uwaga: WorldMeshBake.Compact zeruje brakujące kolory w łączonym buforze. Ewentualny
wariant vertex-color wymagałby znacznika alfa i bezpiecznej wartości neutralnej;
nie dodawać go, jeśli istniejąca ścieżka PBR wystarczy.

Testy: rozszerzyć tylko `test_viaduct_underdeck.py`: brak schodów także ze starym
specem przy wyłączonej fladze, prawidłowe UV1 i brak uszkodzeń geometrii/kolizji.
SHA pomostu powinno objąć V/UV/T oraz zachować niezmienione UV1/COL istniejących
elementów. Sprawdzić wszystkie kamery trasy, draws instancji osobno i <=2% Low tris.
Nie usuwać pierwotnych podpór ani zmieniać ich kolizji bez potwierdzonego problemu.
