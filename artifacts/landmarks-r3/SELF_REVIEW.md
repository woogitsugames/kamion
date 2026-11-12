# Samokontrola r3 — w toku

Obejrzano 16 arkuszy baseline: wszystkie 244 obrazy, Low/High i clear/overcast.
Trasa, remiza i podpomost pozostają kontrolami zachowania wcześniejszych rund.
Zdjęcie EC i kadry detalu pokazują zbyt małą szerokość górnego trzonu wieloprzewodowego,
zbyt gęste pasy, brak trzech wylotów i galerii na Low oraz identyczne uproszczone głowice.
Nie ocenia się r3 jako PASS przed renderem zmienionego modelu.

Runtime Unity odczytano sondą SyncOrigin: dwie instancje, up=(0,1,0), odchylenie0°.
W macierzach nie ma pochylenia do naprawienia. Przesunięcie wysokości świata wynika
z originu regionu; nie należy porównywać worldY6,1 z absolutną wysokością NMT137,2.
Submeshe LOD0/LOD1:4/3; progi650/20000 m przed lodBias. Low z bliska używa LOD0,
więc nie twierdzi się, że każdy kadr Low ma tylko trzy submeshe komina.

Fotograficzna poza jest WORKING_VALUE, nie pozycją geodezyjną. Dopasowanie osi i głowic
nie uzgadnia automatycznie dróg ani pobliskich budynków — pozostają poza tą dziedziną.
Nie stosuje się osobnego skalowania/przesuwania kominów w obrazach porównawczych.
Średnica góry trzonu wieloprzewodowego, głowice i galerie pozostają robocze.
Pełny oryginał fotografii nie jest lokalnie zweryfikowany. Próba pobrania o09:28 została
odrzucona przed wykonaniem przez automatyczną kontrolę (blocked by policy), bez pobrania.

Pomiar pasów to heurystyka chromy sRGB: R-G>25, R-B>25, B-G>-8. Ostatni warunek
wyklucza żółtobrązowy brud z klasy czerwonej farby. Stałe okna omijają galerie i dach.
Baseline Low-overcast: rozbieżność czerwone/nie-czerwone49,0% /55,5% (multi/single).
Te liczby są diagnozą układu barw przy roboczej pozie, nie bramką jakości geometrii,
odbiciem fizycznym ani niezależną oceną fotograficzną. Wynik kandydata jest jeszcze nieznany.
