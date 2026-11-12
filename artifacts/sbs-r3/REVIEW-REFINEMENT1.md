# Niezależny przegląd drugiej serii prób pozy — r3

Recenzent sbs_visual_review obejrzał 28 z 28 natywnych renderów oraz cztery zdjęcia źródłowe. Sprawdził SHA czterech zdjęć i 28 raw: bez rozbieżności. Osobno obejrzałem wszystkie 28 gotowych par 960 px. Żaden wariant nie został zaakceptowany do produkcji; wszystkie pozostają C. To nie nowa ocena D51.

| Kamera | Najlepszy roboczy wariant | Wynik i następny krok |
|---|---|---|
| 275528 | 02: −8 m, bok 0, oko 1,7 m, h 0,55; alternatywa 04: −10 m, oko 1,7 m, h 0,52 | 02 lepiej łączy pionowe położenie portalu i dalszej jezdni, 04 ma bliższą skalę szerokości portalu. Własny przegląd preferuje 04 pod względem szerokości i lewego znaku, więc nie ma jednoznacznej akceptacji. Zaznaczyć kotwice portalu i niezależne krawędzie jezdni przed następną siatką. Boczne znaki są za nisko; nie dopasowywać całej kamery do ich wierzchołków. |
| 837235 | 12: −16 m, lewo −2 m, oko 2,2 m, h 0,52 | Portal ma bliską skalę i położenie poziome. Szewron jest nadal za mały i za nisko; przesunięcie do −20 m go dodatkowo zmniejsza. Nie dostrajać kamery tylko do U-3. Osobno sprawdzić osadzenie, wielkość znaku i narożnik nosa. Nominalne oko pozostaje robocze. |
| 328135 | 21: −75 m po osi drogi, lewo −2 m, oko 2,2 m, zachowany pitch | Portal cały i w rozsądnej skali, ale przesunięty w prawo. 18/19 są za blisko, 22 dodaje dominujący tył sygnalizatora. Ustalić zbieżność jezdni i pitch przy stałym XY 21; dalsza jezdnia w renderze jest wyżej niż na zdjęciu, mimo bliskiej wysokości belki. |
| 297817 | 26: −75 m po osi drogi, bok 0, oko 2,2 m, zachowany pitch | Najbliższa skala portalu i bezpieczna powierzchnia jezdni. Nadal różni się pionowe położenie dalszej drogi i układ prawego odgałęzienia. 24/25 mają większy portal; w 28/29 jego czytelność zanika. Sprawdzić punkt zbiegu i pitch przy stałym XY, geometrię odgałęzienia rozpatrywać osobno. |

Żaden kandydat nie ma dwóch niezależnych, jednoznacznie zgodnych kotwic. Wymiary portalu 16 m i 7,4 m są wartościami WORKING_VALUE modelu, nie pomiarem rzeczywistego obiektu. Jego skala sama nie potwierdza odległości kamery. Ocena nie zmienia świata innych dziedzin ani formalnego wyniku bazowej serii: FAIL 13/11/1.

Dwie próby 328135 z bokiem +2 m odrzucono przed renderem z powodu braku bezpiecznie ustalonej powierzchni na profilu przesunięcia. Nie wchodzą do 28 obejrzanych obrazów. Szczegóły i SHA są w pose-refinement1/inputs/probe_plan.json oraz pose-refinement1/pairs/audit.json.
