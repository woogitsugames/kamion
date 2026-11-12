# R5 — przegląd rodzica: świat native LUT

Obejrzano wszystkie144 obrazy na12 kontaktówkach clear/overcast/night po4 arkusze, cztery warianty na kamerę: High HDR reference, High legacy, Low baseline i Low native32. Render źródłowy402f3401. Jest to12 kamer x3 presety, a nie końcowa kontrola całej trasy.

Clear: po native32 asfalt, kostka i bliskie ściany są bliższe High, bez powrotu płasko białych chmur z odrzuconej v3. Na kwadrat-park-gate i cab-driver widać zachowaną gradację nieba. Szkło kabiny i ekrany pozostają inne; Low ma miększe krawędzie, inne cienie i modele aut/naczep. Biały dach ciężarówki pozostaje bardzo jasny. Nie ma podstaw do uznania detalu lakieru za rozwiązany.

Overcast: ziemia i ściany zyskują kontrast zbliżony do High, ale niebo Low nadal ma dużo gładszą, rozmytą strukturę chmur niż High. Szczególnie cab-driver i g3a-eye-s0262 pokazują utrzymujące się różnice. LUT nie naprawia różnic tworzenia samego nieba. Różne okna, auta i szczegół naczep nie są dowodem błędu gradingu ani jego zgodności.

Night: poziom rozświetlonej nawierzchni jest bliższy High, a dominanty zieleni mniejsze. Pozostają ciemne doki i office1, zbyt jasny bliski plan wobec ciemnej dalszej trasy, cienkie białe głowice bez halo oraz różnice instrumentów i kompozycji szkła. Zmiana tonów nie rozwiązuje rozmieszczenia światła lub jazdy nocnej.

Budżety36 porównań Low: draws i tris +0, z instancing policzonym osobno. Wszystkie36 par fizycznych kostek mip0 ma RGB mean/max0. Każdy z36 High HDR ma rzeczywisty pre-post R16G16B16A16_SFloat. Średni wholeframe błąd wobec High HDR maleje Clear10,981→6,070, Overcast10,185→6,363, Night5,101→2,221; poprawa34/36 kamer. To orientacyjna różnica kodów RGB całych klatek o odmiennej geometrii/cieniach/skali/alpha, nie fotometria ani kryterium akceptacji. Dwa pogorszenia Overcast muszą pozostać jawne.

Kierunek native32 jest lepszy niż próba dopasowania Low do ograniczonej referencji ARGB32. Nie zatwierdzam całej klatki, GPU, telefonu ani domyślnego włączenia produktu. Następne kroki: obserwacja legacy pre-post, rozszerzenie na LowSun/Dusk i jawny, domyślnie wyłączony kandydat runtime z kontrolą klucza oraz życia kamery. Bez nowego przebiegu Low.
