# Jeżeli B nie poprawi sylwetki — hipoteza kolejnej próby
Nie zmieniać modelu przed obejrzeniem B. A odrzucono za wąski stożek i płaskie kliny.
B zachowuje pierwotne karty, a usuwa jednolite półki rdzenia; jego obraz jest nieznany.
Jeśli nadal dominuje bryła, można sprawdzić drobniejsze spraye z pierwotną orientacją
pionowych kart (UP*cos roll), zamiast bocznej z A (UP*sin roll).
Uściślone C:27 kart Low /78 High, szerokość0,18 /0,27, roll jak baseline ±0,25 rad,
pięć węższych pierścieni i fill0,60. To98/224 tris na drzewo, a240 narożników
normalnych trzech rdzeni Low zachowuje oryginalny próg216 bez osłabiania testu.
proposal_c.py policzył pole kart na prawdziwych kluczach: wszystkie6 przypadków
poniżej baseline. To powierzchnia3D, nie koszt GPU i nie dowód wyglądu.
B produkcyjne pozostaje nietknięte. Decyzja dopiero po jego renderze.
Nie przyjmować wariantu tylko za poprawne hashe; brak poprawy = odrzucenie/NO-OP.
