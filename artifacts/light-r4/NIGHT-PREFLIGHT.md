Hipotezy nocy do sprawdzenia po świeżym baseline, bez zmiany produkcji.

Recenzja s12: noc wygląda jak dzień −3 EV; Putry bez widocznych plam, trawa nasycona, głowice bez halo i ciemne okna. R4 obejmuje porównanie tonów Low/High oraz te bieżące uwagi lidera.

Kolor: Night dziedziczy lookSaturation=-3 z Dusk; High stosuje tę wartość w Volume, Low ma obecnie tylko shaderowy toe. Pierwsze niewłaściwe laboratoryjne High nie mogą posłużyć do doboru korekty. Potrzebne rzeczywiste grading stack, plansza i obrazy świata.

Latarnie: R2 Putry raportował cztery wybrane głowice i niezerowy kolor puli, co nie dowodzi widocznej plamy na drodze. Nowa sonda zapisze punkt pod głowicą i jego viewport, głębokość oraz emisję rzeczywistego klonu materiału. Sprawdzić zwłaszcza poziomy drogi pod/nad wiaduktem, odległość, wagę i widoczność punktu w kadrze, zanim zmienimy natężenie.

Ewentualna selekcja uwzględniająca drogę i przeszkody mogłaby użyć ograniczonej listy najbliższych głowic i kilku zapytań fizyki co0,25s. Nie testować kolizji dla wszystkich700głowic co klatkę; nie zwiększać liczby pul lub prawdziwych świateł. To hipoteza, nie decyzja ani zmiana runtime.

Halo na Low wymaga osobnego sprawdzenia istniejącego przebiegu: nowe billboardy zwiększyłyby draws, fullscreen bloom jest zabroniony. Nie skalować geometrii słupów ani zmieniać cudzych prototypów pod pozorem światła. Poświata w samym sky pass byłaby przybliżeniem ograniczonym głębokością i wymagałaby oceny kosztu ALU; jeszcze nie wdrożona.

Wybrane jasne okna można rozważyć wyłącznie w istniejącej procedurze masek okien, za flagą danych, bez zmiany albedo, atlasów lub geometrii innych właścicieli. Nie stosować globalnej emisji do wszystkich szklanych fasad.

Każdy wariant musi być porównany z aktualnym baseline na obu poziomach jakości, zachować czytelność kierowcy, zerowy przyrost draws i brak nowych przebiegów. KosztGPU/A16 pozostaje do weryfikacji lidera; telefonów nie używamy.
