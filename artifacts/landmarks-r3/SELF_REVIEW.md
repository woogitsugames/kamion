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

## Pierwszy wariant EC — świadomie niekońcowy
Wszystkie32 arkusze przed/after-silhouette obejrzane (244 pary), 123 PNG identyczne.
Widać poprawę grubości trzonu wieloprzewodowego, liczby wylotów i rytmu pasów.
Z trasy zmiana czytelna w g3a-eye-s0262, rondo-bie-approach, photo-biezenstwa-ground,
stretch-03; remiza/kabina bez widocznej regresji. Brak niezależnego fotograficznego PASS.
Pierwszy układ galerii Low jest zbyt słabo widoczny od dołu, same płaskie annulusy
nie niosą sylwetki; dodano w następnym wariancie pionowe obrzeże0,25 m.
High miał za dużo drobnych rurek, co podniosło tris dwóch nowych kamer Low z bliska.
Draws+0; wyłącznie ec-multi-head i ec-single-head przekroczyły +2% (3,57%/6,90%).
Wariant poprawiony ogranicza oba LOD0 do700 tris starych prototypów; test przed buildem.

Pierwszy audyt: wszystkie128 chunków High/Low i125468 nie-EC instancji identyczne;
roads_qa i definicje materiałów identyczne. Dwa kominy zamiast dwóch, XY/yaw identyczne,
Z+3/+9 mm przez różne próbkowanie tego samego gruntu. Nie nazywać pozycji3D identycznymi.
Unity after-silhouette nadal ma dwie pionowe osie (0°).
Kolory i faktura kominów nadal są zbyt szare/jednolite w zestawieniu z fotografią;
nie korygować całego oświetlenia w tej dziedzinie. Zabrudzenia i szczegóły głowic otwarte.
Pomiar czerwone/nie-czerwone Low-overcast poprawił się49,0→21,1% (multi),55,5→0,0%
(single), ale próg chromy i robocza poza nie są geodezyjną walidacją pasów.

## Korekta filarów z niezależnej recenzji s12 — w trakcie
Własne szare fazy r2 okazały się błędną interpretacją cienia. Recenzja main wskazuje
jedną musztardową farbę na całym filarze. Przywrócono pigment sprzed brązowej korekty,
wyłączono unpainted_chamfers oraz niepotwierdzoną plamę paint_blobs.
Nie ma jeszcze PNG nowego wariantu: nie deklarować zamknięcia P1 ani P2.
Collector/downpipe istnieją w generatorze; nie dodano drugiej rury bez pomiaru położenia.
