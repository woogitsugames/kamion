# Samokontrola obrazu, r1b / candidate2

Obejrzano 6 arkuszy zdjęcie | render w `review-candidate2-960`: po 3 referencje dla Low i High, overcast. Obejrzano też pełne podglądy Low starej drogi, nowej drogi, świeżej i starej łaty oraz SBS 150280503737744. Dokończono oględziny wszystkich 8 arkuszy przed | po w tym katalogu. Pełne contact sheets wszystkich kamer obejrzano po analizie liczników; szczegóły poniżej.

Stara jezdnia ma wyraźniejsze ciemne ślady kół. W SBS 150280503737744 ślady są teraz widoczne z kamery trasy, lecz na zdjęciu kontrast i lokalne ciemne plamy nadal są mocniejsze. Tonu nie można porównywać jako fizycznego albedo: zdjęcie ma inne światło, ekspozycję, datę i pozę. Referencje 303305168125936 i 454716650857984 pokazują bardziej równy, ciemny asfalt wiaduktu; render ma mocniejsze powtarzalne pasma. Ujęcia mają różne horyzonty, więc nie są dowodem dokładnego dopasowania do zdjęcia.

Nowe P-10 zachowuje pełną warstwę farby zamiast czarnych ubytków z wariantu r1a. Widoczne są jeszcze cienkie linie spękań na części pasów; nie traktujemy tego jako dowodu idealnie nowej farby. Klasyfikacja źródła jest zachowawcza: części mieszane i nieznane nie dostają znacznika świeżej nawierzchni.

Obie łaty są jednoznacznie widoczne z własnych kamer bliskich. Szew i różnica tonu poprawiły czytelność, lecz wnętrza są dość płaskie, a kształty prostokątne i regularne. Nie zgłaszamy fotorealizmu ani poprawy rozmieszczenia. Liczba łat nie została zwiększona. Własne kamery napraw nie są pozami ze zdjęcia.

Przy prawym krawężniku starej drogi pozostaje drobny falisty wzór. Próby wyłączenia foto-warstwy, spękań, normalnej i brudu rynsztoka go nie usunęły. Stan shadera Low został sprawdzony bezpośrednio w czasie renderowania. Przyczyna nieustalona, problem pozostaje otwarty.

Wynik: poprawa czytelności części materiałów, ale jeszcze nie pełny wizualny PASS. Niezależna recenzja, pomiary z masek i pełna kontrola kamer są zakończone; wyniki końcowych testów zapisano w REPORT.md. Ocena obrazu pozostaje warunkowa. Koszt A16 UNVERIFIED, bez telefonu.


Obejrzano wszystkie 28 contact sheets comparison-candidate2-960: po 7 stron dla Low/High i overcast/clear. Obejmują 312 par obrazów ze wszystkich 78 kamer. Na małych miniaturach nie widać przesunięcia geometrii, zmian kadru ani rozległych usterek poza opisanymi materiałami. W clear różnica asfaltu jest mniej kontrastowa niż w overcast; w ujęciach pod wiaduktem ślady są mocno podłużne. W kamerach kabiny i pojazdów nawierzchnia zajmuje niewielką część obrazu, więc ten przegląd wykrywa tylko duże regresje; nie potwierdza jakości drobnej faktury. Drobny wzór przy krawężniku oceniono osobno w natywnych wycinkach. Wszystkie liczniki candidate2 mają delta 0, ale budżet GPU nadal UNVERIFIED.


Obejrzano próbę siły 0,80 i porównano ją z candidate2 0,45 w tym samym kadrze Low overcast. Wzmocnienie daje mocne równoległe pasma, uwydatnia też drobny falisty wzór po prawej. Wariant nie jest wybrany. Do dalszej poprawy potrzebna jest zmienność zależna od lokalnej nawierzchni, nie tylko większa globalna wartość. Materiał przywrócony do źródłowej wartości 0,45; kolejne testy nadal dotyczą candidate2.


Korekta 2026-11-12: wcześniejsza akceptacja masek i pomiarów proporcji pól jest wycofana. Odtwarzanie anchor z wejściowej wysokości kamery było niepoprawne przy seat=road. Patrz CORRECTION-2026-11-12.md. Ocena oglądanych obrazów i liczniki są zachowane, wielkość kontrastu renderu pozostaje UNVERIFIED.

