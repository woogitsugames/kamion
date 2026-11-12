Runda 4 — spójność tonów Low/High i nowy P1 nocy z recenzji s12.
Gałąź gpt-light-r4, merge main 67f6702c: 2e82dc46; stan początkowy czysty.
R3 dostarczone: 970 plików, REPORT i sześć par dodatkowo zweryfikowane w main przez hasze. GIS576+1xfail, EditMode310/310.
Nowy priorytet lidera: noc przypomina dzień −3EV, brak widocznych plam Putry, nasycona trawa i ciemne okna. Łączymy to z porównaniem tonów na obu poziomach jakości; P1 klina naprawiony w poprzedniej rundzie.
Najpierw plansza przy rzeczywistym EnvironmentLighting i mapowaniu KamionTone/post. Potem świeża regeneracja/import po merge main i pełny baseline Clear/Overcast/Night, bez nadpisania ekspozycji i bez domyślnych reflektorów.
Ograniczenia: brak nowego przebiegu/fullscreen na Low, nie obniżamy skali, nie zmieniamy geometrii ani materiałów innych właścicieli. Każdy Unity przez main slot owner gpt-light, każdy ciężki Python heavy owner gpt-light-r4, pojedynczo i numeryczne wątki1.
Następny krok: odświeżenie wejść surowych i przygotowanie diagnostyki planszy; żaden nowy wynik jakości nie jest jeszcze zadeklarowany.
Krok 0: przygotowano własną planszę24próbek (12szarości +12kolorów) ×4presety ×2tiery,8PNG. Wejście jest jawnie liniowe po ekspozycji; Low stosuje istniejący KamionTone, High rzeczywisty globalny Volume z EnvironmentLighting. To diagnostyka mapowania, nie próba oświetlenia/fotometrii. Wrapper sprawdza świeżość,24pola i rzeczywiste postLow/High oraz błędy shadera. Następny krok: refresh-inputs, potem tone-chart i pipeline świata.
Krok 1: surowe wejścia odświeżone z main przez robocopy bez usuwania i bez Library; git lfs checkout zakończony. Junctiony referencji pozostają tylko do odczytu. Następny krok: plansza i świeży generator/fidelity/import.
