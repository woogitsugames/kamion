Analiza możliwości przed baseline, 12 listopada 2026. Bez zmiany produkcji i bez deklaracji poprawy obrazu.

WorldSurface i zwykła ścieżka WorldPBR pobierają środowisko przez GlossyEnvironmentReflection z domyślnej kostki SkyModel. Istniejący KamionWetSurface zmienia albedo, smoothness i normalną; nie dodaje lokalnej treści odbicia. To konkretne ograniczenie porównania ze zdjęciem cm92458760, na którym w warstwie wody widać także otoczenie. Nie dowodzi samo w sobie przyczyny opisanego w ADR 0080 plastikowego wyglądu — wymaga aktualnych obrazów.

VehicleReflectionCapture ma już kostkę otoczenia pojazdu, dostępne Cube/Enabled i publiczny captureOffset. Place ustawia punkt z transform.TransformPoint(captureOffset). RenderFace zeruje _KamionVehicleCapture podczas przechwytywania i przywraca go w finally, równocześnie pomijając dodatkowy tone/cap. KamionVehicleEnv.hlsl używa tej flagi i opisuje istniejące mipmapy jako przybliżenie box-filter, nie GGX convolution. Nie ma obecnie publicznego odczytu m_LastCubePos; bieżący transform może różnić się od pozycji zachowanej kostki w ruchu.

Możliwy późniejszy eksperyment: opcjonalnie użyć istniejącej kostki dla mokrej powierzchni w pobliżu pojazdu. Nie wymagałoby to tworzenia kolejnych kamer ani zwiększania liczby capture faces. Nie jest jednak jeszcze wdrożone i nie oznacza zerowego kosztu GPU. Weryfikacja musi obejmować:

- flagę danych domyślnie wyłączoną, z neutralną ścieżką dawnych presetów;
- użycie rzeczywistego, znanego punktu przechwytywania, a nie kamery QA; ograniczenie odległości/paralaksy;
- poprawny fallback dla floating cameras daleko od pojazdu i przy wyłączonym capture;
- blokadę próbkowania tej samej kostki podczas jej zapisu przez istniejącą flagę capture;
- brak zwiększenia liczby kamer, przebiegów, rozmiaru, częstotliwości i zasięgu capture;
- zastąpienie istniejącego odczytu środowiska, jeśli to możliwe, zamiast bezwarunkowego podwajania próbek na Low;
- kontrolę rzeczywistej pozycji ciężarówki i counters FacesRendered w dowodach, bez udawania skalibrowanej pozy zdjęciowej;
- osobną ocenę Low/High, dalekiego pola, powierzchni suchych i wpływu na istniejące odbicia pojazdu. GPU A16 pozostaje do pomiaru lidera.

Najpierw baseline 36 ujęć wet i cztery clear po świeżej geometrii. Jeżeli problem da się rozwiązać poprawną odpowiedzią filmu/kałuż, nie dodawać mechanizmu bez potrzeby. Jeżeli brak lokalnej treści odbicia pozostaje głównym odstępstwem, nie nazywać samego wygładzenia powierzchni ukończoną rekonstrukcją mokrej drogi. Shaderowe pliki wspólne można zmieniać tylko addytywnie, za flagą danych i z opisem styku; geometria, materiały asfaltu i cudze pliki pozostają poza light.
