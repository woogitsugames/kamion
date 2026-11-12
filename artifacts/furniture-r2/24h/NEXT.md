# Dalsza walidacja r2

1. Odczytać żywą sekwencję candidate-build.ps1 (sesja 58010); nie uruchamiać
   duplikatu. Pojedyncze testy nowego pliku i dwóch dawnych, następnie world
   after1, brak fallback=True i porównanie chronionych payloadów. Baseline ma
   6833 payloady i 330 PNG (55 × Low/High × clear/overcast/dusk).
2. Po budowie import w slocie Unity gpt-furniture, kontrola rzeczywiście
   przypisanych materiałów/tekstur/keywordów oraz zachowania jawnych definicji
   innych dziedzin. Nie twierdzić, że wszystkie 36 lic aktywowało się w scenie
   wyłącznie na podstawie testu rodziny w osobnym Result.
3. Rendery kandydata we wszystkich sześciu wariantach, wszystkie kamery i
   osobno draws mesh/instancji. Narzędzie compare_frames.py z r1 trzeba
   dostosować do ścieżki r2 i dodatkowego dusk; nie ukrywać niekompletnych par.
4. Odrębny kontrolowany kadr z PRAWDZIWYM riggiem pojazdu przy znaku jest
   konieczny. Kamery kontrolne nie dowodzą ustawienia pojazdu/reflektorów przy
   każdej kamerze. Użyć rzeczywistych socketów i stanów off/low/high, nie
   wymyślonej lampy przy kamerze. Sprawdzić API VisualQaRunner/WorldInstances
   przed utworzeniem własnego, odwracalnego fixture w _Generated. Dusk (-5°)
   jest zmierzchem; pełna noc wymaga osobnego stanu diagnostycznego, bez
   modyfikowania plików właściciela light. Parametry nadal WORKING_VALUE.
5. Formuła analityczna nie ma przesłaniania od reflektora. Zachować ten limit
   w ocenie; nie zastępować go testem kąta ani nazywać fizycznie skalibrowaną.
6. Obejrzeć obrazy ≤960 px i referencje, po czym zlecić niezależny przegląd
   istniejącemu /root/furniture_review zgodnie ze skillem visual-qa. Bez nowego
   agenta i bez jego Unity/Pythona. Dopiero potem pełne testy na końcu rundy,
   REPORT, robocopy, r3. Pełnego GIS nie uruchamiać podczas iteracji.

Zadania ciężkie: absolutny skrypt slotu main, pool heavy, owner gpt-furniture-r2;
Unity: owner gpt-furniture. Żadnych cudzych blokad, telefonów, main merge/push.
