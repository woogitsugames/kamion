# Próba D — ta sama liczba kart, niska pokrywa liści

C pozostaje odrzucone jako wersja końcowa. Snapshot-candidate-c, probe-c i obie serie 16 arkuszy zachowują dowód; sekwencje 4178 i 34215 zakończyły się kodem 0, brak aktywnego własnego heavy/Unity.

D zmieni wyłącznie dane i parametry pokrywy w plantings.py. Bez zwiększania gęstości, zmiany próbek, capów, materiału, atlasu i pędów brzegowych. Punkt próby: karta o szerokości 0,16–0,28 m i długości 0,12–0,22 m, odchylenie 1,10–1,45 rad od pionu, podstawa schowana na 45% długości. Wszystko WORKING_VALUE. Większa długość pochylonej karty nie oznacza większej wysokości: nad płaskim capem maksimum z tych danych to około 5,5 cm, wobec około 10,4 cm C. Zwiększy się udział widocznej z góry powierzchni przy tej samej liczbie trójkątów.

Dodać test faktycznie emitowanych kart: ta sama liczba trójkątów i UV atlasu co C, mniejsze wystawanie nad płaski cap, zagłębiona podstawa i większy rzut powierzchni w XY. Zachować 40 istniejących testów. Celowane testy, World i dekodowanie kolizji sekwencyjnie przez jeden heavy; potem lekkie piny, import przez Unity slot i osobne candidate-d/probe-d. Autor i krytyk obejrzą baseline–D oraz C–D. Kryteria odrzucenia: nadal pędy na blacie, prostokątne płaty, unoszenie podstaw, regularny dywan lub przekroczenie budżetu. Nie uznawać 40 testów C za testy D. Nie uruchamiać pełnego GIS przed końcem rundy.
