# ADR 0310 — Końcowe przycinanie barier i P-10 do nawierzchni

Data: 2026-11-19. Status: przyjęta w gałęzi guardrail-zebra-cli; walidacja playera po integracji.

Przejazd s24 pokazał ukośną barierę na Kleeberga i nakładające się zebry przy wysepce w Knyszyn-w. Same offsety i scalanie stacji w jednym łańcuchu nie stanowią kontroli wynikowej geometrii.

Po wszystkich przesunięciach i łączeniach barier kontrolujemy całe odcinki względem trójkątów przejezdnej nawierzchni (warstwy road i bridge, także apron). Usuwamy odcinki naruszające bufor i dzielimy run bez ponownego łączenia końców. WORKING_VALUE: 0,25 m odstępu od nawierzchni + 0,20 m obwiedni osprzętu + 0,02 m tolerancji uproszczenia belki. To zabezpieczenie geometrii, nie nowa deklaracja zgodności z normą drogową. Kontrola obejmuje też bariery przy podporach; dalsza deduplikacja czyta tylko faktycznie zachowane runy.

Po oznakowaniu generowanym i authored P-10 przycinamy jego trójkąty do nawierzchni, odejmujemy wysepki z buforem 0,05 m (WORKING_VALUE) i wcześniej położone P-10 na tym samym poziomie, niezależnie od łańcucha. Triangulacja ograniczona zachowuje pole; interpolacja barycentryczna zachowuje Z, UV, UV1 i COL. Nieprzycięte siatki pozostają bez zmian.

Indeks STRtree filtruje zakresy wysokości trójkątów z tolerancją 1 m, dzięki czemu typowy przejazd pod wiaduktem pozostaje rozdzielony. Jest to konserwatywna kontrola planu z filtrem wysokości, a nie dokładne przecięcie brył 3D; na dużym pochyłym trójkącie może usunąć nadmiar bariery. Przycinanie nie zmienia osi ani szerokości dróg. Koszt występuje w generatorze offline. Pełna przebudowa i wizualna bramka playera pozostają osobnym krokiem.

## Uzupełnienie (21.11.2026, c-regress-cli)
Wyjątek `own_shoulder` (`tools/worldgen/roads/surface_safety.py`): przy przycinaniu barier z reguły asfaltowe pobocze **tej samej strony tej samej drogi** nie jest traktowane jak jezdnia (bariera stoi 0,25 m za nim). Pasy ruchu, inne drogi i bariery authored zachowują pełny bufor 0,47 m. Bez wyjątku ucinało przejścia most→dojazd (wolne końce barier mostowych).
