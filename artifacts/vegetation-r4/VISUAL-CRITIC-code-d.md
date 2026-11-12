# Recenzja kodu D, przed formalnymi testami i renderami

Niezależny vegetation_critic nie znalazł oczywistego naruszenia legacy. Argument bury zachowuje domyślnie 25%, tylko pokrywa przekazuje 45%. Korzenie, atlas i liczba kart pozostają takie jak C. Pochylenie zwiększa rzut powierzchni ku górze i zmniejsza wystawanie nad płaski cap. To dopuszczenie do próby, bez akceptacji wyglądu ani budżetu.

P1: test podstaw odnosi się do poziomej płaszczyzny korzenia, nie do całej rzeczywistej powierzchni capu. Szersza, pochylona karta może lokalnie wystawać albo prawie cała znikać w reliefie. Wartość 5,5 cm dotyczy płaskiego capu. P2: większy rzut pojedynczego quada nie dowodzi zachodzenia pokrywy na siebie ani likwidacji luk. Przezroczystość atlasu i schowana część karty dodatkowo zmniejszają widoczną powierzchnię. Nazwę testu poprawiono z overlaps na spreads, zgodnie z rzeczywistym zakresem sprawdzenia.

Na renderach trzeba sprawdzić narożniki i zakończenia: korzeń 2 cm od brzegu nie gwarantuje pozostania całej karty w rabacie, a szerokie wystające płaty mogą wyglądać jak naklejone kartki. Atlas pędów może ujawnić powtarzalne gałązki po pochyleniu. D musi jednocześnie ograniczyć sterczące pędy i zmniejszyć ilość widocznego gładkiego blatu; samo spełnienie pierwszego warunku oznacza nadal PARTIAL. Recenzent nie wykonywał testów ani ciężkich narzędzi.
