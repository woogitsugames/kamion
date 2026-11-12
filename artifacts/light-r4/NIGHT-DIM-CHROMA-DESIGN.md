Możliwa ablacja nasycenia ciemnych powierzchni po obejrzeniu baseline; nic nie jest jeszcze wdrożone.

KamionTone jest już wspólną końcową funkcją koloru dla WorldSurface, WorldPBR, Vegetation, TruckExterior oraz obu ścieżek TruckGlass. Można tam rozważyć domyślnie wyłączoną desaturację tylko ciemnego zakresu, zamiast globalnego obniżenia EV lub odbarwienia jasnych lamp i instrumentów.

Nowe dane należałyby do LightingPreset, nie QualityProfile: siła0 zachowuje dotychczasowe presety. Próbne0,35/0,65/1 należy ocenić na obu tierach; progi luminancji też są WORKING_VALUE, nie modelem fizjologicznym widzenia nocnego.

Luminancja liniowa powinna być zachowana przez mieszanie z Rec709; jasne pule/lampy powinny zachować kolor. Nie zmieniać SH, słońca, ekspozycji ani koloru instrumentów przez globalny Volume bez kontroli.

Uwaga na odbicia: VehicleReflectionCapture zeruje istniejący _KamionTone i ustawia _KamionSkyCapOff=1 podczas przechwytywania fizycznej sceny. Nowa prezentacyjna desaturacja musiałaby respektować to samo pominięcie, inaczej zostanie dwukrotnie zapisana/przeliczona na lakierze lub szkle. Nie wymaga to edycji pliku pojazdu.

Szkło wymaga osobnej oceny obu ścieżek, ponieważ część kolorów jest premultiplikowana przez alpha. To ogranicza wnioski z laboratoryjnej nieprzezroczystej planszy. Nie zmieniać shaderów kabiny lub geometrii.

Weryfikacja: poprawny chart z aktywnym gradingiem, rzeczywiste trasa/trawa/pule/kabina, Dusk i dzień bez zmian, porównanie istniejących kostek64/128 oraz pełne estymaty kamer. Zero nowych przebiegów i tekstur; dodatkowe ALU pozostaje kosztem do pomiaru A16, nie automatycznym PASS.
