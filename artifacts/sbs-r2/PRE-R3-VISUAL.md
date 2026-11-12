# Przegląd sześciu par ADR 0125 przed r3

Obejrzano gotowe pairs-after sześciu kamer: 837235, 275528, 328135, 297817, 180137, 494288. To materiał Claude z ADR 0125, nie własny render nowego main i nie uzupełnienie rostra r2. W arkuszach górny rząd to starszy stan, dolny nowy.

275528: nowy portal jest duży i ucięty u góry renderu, na zdjęciu mieści się wyraźnie dalej. To wspiera próbę cofnięcia kamery, ale nie dowodzi konkretnej liczby metrów. 837235: portal pojawił się w oddali; pobliski szewron i nos wyspy nadal nie odpowiadają zdjęciu. Należy oddzielić pozę od geometrii nosa.

328135/297817: w nowym renderze 297817 widać bliski tył portalu podobny do zdjęcia 328135, natomiast render 328135 go nie pokazuje. Obejrzano też oba natywne rectified PNG 1280x960. WAŻNE: zdjęcie 297817 zawiera portal daleko w tle przy środkowym pasie drzew; nie należy opisywać go jako całkowicie nieobecnego. Wcześniejsza kolejność 297817, potem 328135 jest zgodna ze zbliżaniem się do portalu w zdjęciach.

Manifest źródłowy: ta sama sekwencja iyhzyp7y42u1p2e3p2djji, 297817 captured_at_ms=1501336718724, 328135=1501336721402 (różnica 2678 ms). Współrzędne manifestu zgadzają się z referencjami; nie znaleziono dowodu zamiany identyfikatorów przez SBS. Nie wnioskować o 180 stopniach odwrócenia kursu. Wspólna próba cofnięcia wzdłuż własnych kierunków nadal ma sens, z kontrolą portalu i osobnej kotwicy (np. trwały narożnik jezdni). Około 45 m pozostaje hipotezą, nie pomiarem.

180137: ekran i włączenie łącznicy są w innym miejscu względem kamery. 494288: po usunięciu lewego ekranu widok jest otwarty, lecz oś obrazu nadal skręca w lewo względem zdjęcia. Oba wymagają prób po aktualizacji świata, bez wyciągania nowego FOV wyłącznie z jednego obiektu.

Nie zmieniono produkcyjnych kamer, referencji ani klas. Nie zastąpiono formalnej recenzji D51. GIS r2 nadal działa w swojej dzierżawie heavy.
