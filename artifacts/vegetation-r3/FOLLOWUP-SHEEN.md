# Hipoteza do kolejnej rundy — jasność koron, bez zmiany bieżącej próby

Nie jest to wdrożenie ani wynik wizualny. Podczas kolejki heavy prześledzono inną przyczynę otwartego Putry: Vegetation.shader dodaje bezbarwny składnik _KamionLeafAmbient.y do albedo w oświetleniu nieba. Komentarz opisuje go jako pomoc dla ciemnych igieł, ale dotyczy wszystkich dwustronnych liści, także impostorów liściastych. Odrzucona wcześniej zmiana occA działała tylko na bliskie karty, stąd brak efektu Putry.

W następnej niezależnej próbie należy porównać ograniczenie tego składnika dla liściastych z przyciemnieniem samych palet. Istniejące dane materiału rozróżniają sosnę (_CrownShade 0,25) od zwykłych liściastych (0,50); hero shell ma 0. HLOD wymaga osobnego zachowania, ponieważ conifer edge także ma 0,50 i działa ForestFastPath. Nie można uznać dowolnego materiału 0,50 za bliskie drzewo liściaste bez wyłączenia _HLOD_EDGE.

Kierunek pomiaru: ten sam kadr Putry Low/High clear/overcast, stała maska z baseline, DK8 jako kontrola; bez globalnej ekspozycji i bez shaderowego przyciemnienia lasu. Zakres zdjęć z wcześniejszej recenzji 47–65 jest celem roboczym, bo nowe kadry mają klasę B. Nie wystarczy zmniejszyć średniej całego obrazu ani zmienić selekcji maski.

Każda zmiana musi objąć wspólną logikę pełnej i VEG_FAST, bez nowej próbki lub przebiegu. Pomiary GPU A16 pozostają niepotwierdzone. Test tej hipotezy dopiero po zamknięciu danych D51; nie zmieniać źródeł shaderów podczas obecnych renderów/generacji.
