# Pomysły do kolejnych kroków r1

1. Trawa: koszony pas drogi jest dziś wymuszany do 4 m, a pole suchości w tym pasie ma zakres zaledwie 0–0,18. Przywrócić silniejszą, przestrzennie spójną wariację bez automatycznego piaskowego rantu. Rozdzielić jawny trawnik OSM od zwykłego pobocza. Zmierzyć ten sam ROI route-onramp-andersa-above blokami 32 px.
2. Materiał: obecna suchość jest prawie wyłącznie mnożnikiem odcienia (1,22/1,10/0,92). Dodać mieszankę suchej źdźbłowej materii wyłącznie pod istniejącą flagą maski podłoża, w VegetationGround.hlsl współdzielonym przez oba shadery. Nie dokładać próbek tekstur.
3. Żywopłot: środek pokrywy bierze medianę wysokości całego obwodu, podczas gdy brzeg jest pofałdowany per roślina. Sprawdzić interpolację lokalnej wysokości zamiast globalnej mediany, zachowując tę samą topologię i liczbę trójkątów.
4. Korony: stały składnik sheen rozjaśnia także jasne liściaste. Szukać sterowania istniejącymi parametrami materiału albo paletami, bez przyciemnienia sosny DK8. Dopiero po pomiarze bazy.
5. Sosny: generatory Blender nie należą do przydziału plików sesji. W dozwolonym zakresie można korygować tekstury igieł i HLOD; zmianę szkieletu w make_trees.py opisać liderowi jako ograniczenie własności, chyba że da się ją wykonać przez dozwolone dane wejściowe.

To hipotezy robocze, nie wyniki ani potwierdzenie poprawy.
