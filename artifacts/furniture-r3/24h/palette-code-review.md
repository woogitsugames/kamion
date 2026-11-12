# Niezależny przegląd scalania materiałów wiat

furniture_review przeczytał props.py, dane palety, fabrykę, shader i testy, wyłącznie do odczytu. Nie znalazł blokera obecnej optymalizacji. Przesunięcia indeksów są poprawne, indeks receptury stały na trójkącie, a szkło i kolizje pozostają osobne. Bieżące cztery nieprzezroczyste źródła korzystają ze wspólnego domyślnego stylu WorldSurface; wartości metalu ≤0,5 także wcześniej trafiały do tej ścieżki. Wybór receptury w vertex shaderze nie dodaje samplera ani przebiegu.

Po odczycie rzeczywistych danych root uzupełnił zachowanie sky_occ: trzy źródła generic mają [0,5; 0], a czerwona rama domyślne zero. Recenzent sprawdził tę poprawkę ponownie i nie znalazł blokera: XYZ nadal normalizuje normalną, W przenosi skyDown, bez keywordu używana jest dotychczasowa wartość `_SkyOcc.x`. Wszystkie źródła mają wspólne `_SkyOcc.y=0`.

Rzeczywiste focused testy materiału zakończyły się 18/18, bez pominięć. Obejmują odczyty GPU albedo/smoothness dla czterech receptur i dwóch wariantów detalu oraz cztery odczyty skyDown, fabrykę, wyłączenie flagi i liczbę przebiegów. Nie są porównaniem końcowego oświetlonego obrazu.

Granice dowodu wskazane przez recenzenta:

- GPU probe zmienia końcowy return diagnostycznego shadera; nie potwierdza sortowania szkła, cieni, APK, urządzenia ani czasu GPU.
- Test GIS porównuje surowe Mesh.out() i scalony wynik tego samego bieżącego modelu. Sprawdza zachowanie trójkątów/normali podczas scalania, nie historyczną zgodność całej geometrii z wcześniejszym commitem. Jego wykonanie nadal czeka na slot heavy.
- Lista czterech źródeł jest zamkniętym kontraktem obecnej implementacji. Bieżące źródła nie mają decal, alpha-cutoff lub innych specjalnych flag; rozszerzenie listy wymaga ponownej oceny kompatybilności.
- Wariant lokalnego keywordu wymaga osobnej weryfikacji builda. Odczyt projektowego strippera nie jest dowodem APK.
- Samo scalanie 4/3 slotów do 2/2 nie dowodzi draws +0. Obowiązuje pełne porównanie wszystkich 236 kadrów i 118 dokładnych Low przy zasięgu 60/300 m. Szczególnie sprawdzić generic oraz g3b-eye-s1482, gdzie iteracja 2 miała +3 draws.

Dodatkowy odczyt ścieżki importu potwierdził, że RegionImporter najpierw wypełnia wszystkie MaterialDefs z manifestu, a dopiero potem wywołuje fabryki materiałów. Odczyt czterech receptur przez nową fabrykę nie zależy więc od kolejności ich tworzenia. Nie zmieniano RegionImporter.
