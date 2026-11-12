# Rozpoznanie przed zmianą geometrii

Baseline i buforowy dowód LOD są w toku. Poniżej odczyt źródeł oraz hipotezy do sprawdzenia, nie wynik renderu nowej rundy.

`life_props.wheel` LOD0 ma bieżnik jako otwartą rurę, pierścień boczny opony i niemal płaski fan felgi. Naczepa używa 10 segmentów, ciągnik 14. LOD1 ma zamknięte sześciokątne koło z r2; naczepa używa w nim `trailer_alu`, a nie `rim`. Nie zmieniać globalnego `rim`, bo materiał jest współdzielony z osobówkami i innymi obiektami. Dodanie nowego materiału lub rozbicie grup może zwiększyć draws nawet przy małym koszcie geometrii.

Zdjęcia pokazują kołnierz obręczy, głębszą miskę, środek oraz ciemne otwory; obecny dysk ich nie ma. Kandydat powinien uzyskać tę różnicę konstrukcją przestrzenną i istniejącymi grupami, nie samym przyciemnieniem całego materiału. Rozważyć profil obręczy z zagłębieniem i otworami w istniejącym materiale opony; dokładne wymiary są WORKING_VALUE. Zachować osie, szerokość, obrys nominalny, kolizję i patch kontaktu. Nie dodawać ponownie podpór/osprzętu, które już istnieją w LOD0.

Budżet źródłowy testu: naczepy LOD0 ≤1200, LOD1 ≤320; ciągniki ≤1500. To lokalne ograniczenia prototypów, a nie pomiar klatki na A16. Nie wybierać pozornej poprawki wyłącznie po to, aby zmieścić się pod historyczną liczbą. Jeżeli czytelna, uzasadniona zdjęciem konstrukcja wymaga zmiany tego ograniczenia, najpierw zmierzyć wszystkie prototypy, wszystkie kamery i trasę; zachować twardo draws świata/instancji +0 i trójkąty trasy ≤+2%, a zmianę lokalnego progu jawnie uzasadnić w ADR/REPORT. Nie podnosić go automatycznie do aktualnego maksimum.

Ostateczna decyzja dopiero po baseline, rzeczywistym LOD dla 13 kamer, oględzinach pięciu nowych detali felg i trzech widoków istniejących podpór. Czerń i brud osobówek z r3 nadal PARTIAL; ta runda ich nie uznaje za naprawione.
