# ADR 0111 — wiarygodność porównań zdjęcie | render bramki 3

## Zakres
Sesja 4, dziedzina sbs. Zmiany dotyczą narzędzia, danych pozy kamer i dowodów. Geometria świata oraz ustawienia runtime pozostają własnością pozostałych sesji.

## r1 — klasyfikacja pozy i odtwarzalność
Recenzja s10 J/K odrzuciła sześć par J1 i wskazała osiem przesuniętych par J2 oraz horyzont 2948. Wprowadzamy jawne `pose_confidence`: A — dobrze dopasowana, B — przybliżona, C — odrzucona lub niesprawdzona. Brak pola oznacza C. Domyślny zestaw dowodowy zawiera wyłącznie A i B; diagnozę C można złożyć przez `--include-rejected`. Samo włączenie pary B nie oznacza zaliczenia bramki.

Pary J1 pozostają C do potwierdzonej kalibracji. Początkowo również J2 i 2948 są C. Dla J2 przygotowano próbę przesunięć bocznych −6/−3/0/+3/+6 m przy niezmienionej wysokości. Bez porównania świeżych renderów nie przypisujemy rozbieżności geometrii ani GPS.

Horyzont zdjęcia 2948595898752384 wyznaczamy z przecięcia dwóch zaznaczonych krawędzi drogi w wyprostowanym zdjęciu: 0,5249381 wysokości obrazu. To pomiar punktu zbiegu wybranych odcinków, a nie pomiar geodezyjnego poziomu. Nachylenie drogi i roll nadal mają status WORKING_VALUE.

`photometric_use` jest domyślnie false do sprawdzenia masek nieba/asfaltu i wykluczenia maski samochodu. Zachodów słońca nie porównujemy fotometrycznie ze światłem dziennym. Wiek zdjęcia sprzed 2020 r. jest oznaczony jako historyczny; epoka danych świata pozostaje UNVERIFIED.

Każde uruchomienie Unity w skrypcie SBS ma osobne Acquire/Release slotu `gpt-sbs` w bloku finally. Efekty uboczne ustawień Unity są cofane. Dla każdej grupy proporcji obrazu zapisujemy commit gałęzi, commit main, SHA kamer i referencji, SHA poszczególnych renderów, czas, tier, światło i wymiary. Kompozycja odrzuca niespójny lub nieukończony zapis. Starsze rendery bez rejestru są oznaczone UNVERIFIED.

## Walidacja w toku
14 testów narzędzia SBS zaliczonych. Pełne GIS, regeneracja, import, EditMode i świeże rendery są w toku; nie ma jeszcze końcowego werdyktu. Skopiowane sceny Unity z main miały datę 17:11, dlatego wymagają odświeżenia przed raportem.

## Otwarte
Pierwsze 300 m G3-A bez lokalnych zdjęć; dodatkowe pobranie Mapillary zablokowane błędem DNS. Klasy C i fotometria wymagają dalszej kontroli. Nie wykonujemy testów telefonów; dowody edytora nie zastępują pomiaru A16.

## Limity zasob?w po pilnym poleceniu w?a?ciciela
Ci??kie generacje, fidelity i pojedyncze pliki pytest korzystaj? z puli `heavy` (max 3), z w?a?cicielem r?wnym bie??cej ga??zi i Release w finally. Pe?ny GIS tylko na ko?cu rundy, z jawnym `-EndOfRound`. Unity ma oddzieln? pul? max 4 i w?a?ciciela `gpt-sbs`. Wywo?ania u?ywaj? aktualnego skryptu z main; nie kopiujemy ani nie zmieniamy wsp??dzielonej implementacji. Nie usuwamy cudzych slot?w: du?y pr?g stale w naszych wywo?aniach wy??cza automatyczne sprz?tanie cudzych rekord?w. Sprawdzanie kolejki co 7 s nie zmienia limitu.

## Dalsza praca sesji
Cel czasowy: praca do oko?o 2026-11-12 21:31 Europe/Warsaw (24 h od rozpocz?cia). Runda r1 nie jest zamkni?ta bez raportu i ogl?dzin ?wie?ych render?w. Nast?pne rundy pozostaj? w tym samym worktree, z now? ga??zi? i merge main, bez scalenia do main ani pushowania.
