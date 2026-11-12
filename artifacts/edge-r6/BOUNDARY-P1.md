Odczyt architektury zapór końca mapy, r6; bez edycji runtime lub geometrii zapór.

WorldEdgeBuilder stawia zapory i collidery 60 m wewnątrz prostokąta regionu, a asfaltowe przedłużenia należą do apron bez kolizji. WorldBoundary opisuje prostokąt danych. WorldSafetyNet ostrzega około 260 m przed jego krawędzią i odzyskuje pojazd po wyjeździe, braku gruntu lub upadku. Powstało to po nagraniu właściciela z wypadnięciem zestawu poza świat przy 105 km/h (ADR 0082).

Usunięcie samych rendererów zostawiłoby niewidzialną przeszkodę. Usunięcie rendererów i colliderów ujawniłoby brak drivable collision oraz reset zestawu na krawędzi. Dodanie lasu lub ekranu w poprzek rzeczywistej drogi wymagałoby potwierdzenia źródłowego; nie jest poprawną metodą ukrycia problemu.

Pełna kontynuacja przejazdu wymaga spójnego rozszerzenia danych, kolizji i granicy/recovery. Alternatywą projektową jest jawny koniec dema z kontrolowanym przejściem, zamiast udawania dostępnej dalszej drogi. Oba rozwiązania wykraczają poza samą poprawkę wyglądu tła i wymagają koordynacji z właścicielem runtime/granic/dróg. R6 nie zmienia WorldBoundary, WorldSafetyNet ani cudzych generatorów dróg.

P1 z recenzji pozostaje otwarte. Własne numeryczne poprawki apron i shaderów nie będą przedstawiane jako jego rozwiązanie. Nie zmieniono żadnej kamery SBS ani nie ukryto zapór tylko dla QA.
