# Przegląd wizualny sbs r1

Przejrzano wszystkie 100 zakwalifikowanych par B na 28 stronach overview: Low/High × clear/overcast. Dodatkowo obejrzano pełne arkusze wybranych B i C oraz wszystkie 16 galerii, łącznie 144 warianty pozy. Przegląd nie jest pomiarem wydajności telefonu ani akceptacją właściciela.

W sześciu J1 błędny kurs, pozycja, wysokość lub roll nadal uniemożliwiają pewne porównanie. Oryginalny kompas różniący się od SfM o około 50 stopni nie daje automatycznej poprawy. Dla 182011 oryginalny GPS przy stałej wysokości przenosi kamerę pod konstrukcję; warto później zbadać poziom jezdni względem NMT. To hipoteza, nie potwierdzony błąd świata.
W ośmiu J2 przesunięcie XY zmienia kadr, lecz nie uzyskano jednoczesnego dopasowania pomostu, podpór, bariery i krawędzi jezdni. Część rozbieżności może dotyczyć geometrii, więc nie wolno jej naprawiać dowolnym przesuwaniem kamery. Obrazy C zachowano diagnostycznie; ich wyłączenie z bramki nie oznacza usunięcia problemów świata.
Dla 326454 horyzont około 0,891 i heading +5 stopni poprawiają punkt zbiegu, ale pozostają roll, różnice skali i brak pewnych kotwic. Dla 2948 horyzont wyznaczono z dwóch krawędzi. Pojedynczy punkt zbiegu na obu panelach ujawnia dalszą różnicę kierunku; nie daje podstaw do klasy B.
Dwa Commons są rzeczywistymi, poprawnie opisanymi źródłami, ale próby heading/FOV nie dopasowały wiarygodnie układu obiektów. Same geotagi w okolicy s=230/249 m nie są potwierdzonym pokryciem trasy. Oba pozostają C; 0–200 m nadal bez referencji.

W całym zestawie widać nadal różnice świata: jednolite niebo clear, wyraźniejsza struktura chmur High overcast niż Low, jasne kruszywo na zdjęciach pod wiaduktem wobec ciemnego gruntu modelu, zbyt czyste lub mało zróżnicowane nawierzchnie, inne rodziny latarni i zasłaniający kadr znak przy 177786/178689. Pod wiaduktem Putry występują obrazy ciemnej, zamkniętej płaszczyzny zamiast prześwitu; dotyczą również niepewnych C, więc nie przypisujemy im formalnej liczby potwierdzonych błędów bez kalibracji.
Zdjęcia zachodu pozostają wyłącznie referencją geometrii. Wszystkie flagi photometric_use są nadal false. Nie wyciągamy zbiorczych wniosków o albedo lub ekspozycji z obecnych histogramów. Następna runda ma zweryfikować maski oraz zgodność oświetlenia, wprowadzić kontrast i raport trendu.

Niezależny recenzent potwierdził PASS narzędzia i kompletności dowodów: 168 renderów, 100 arkuszy B, 68 wykluczeń w czterech stanach, 28 stron overview, jeden renderowany HEAD d0dca81e. Klasy: 25 B, 17 C, brak A. To nie oznacza PASS bramki świata; kalibracja C pozostaje częściowa.
