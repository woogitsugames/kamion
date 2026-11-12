# R4 — hipoteza do próby, nie wynik wizualny
Fotografia CC0 7197: korony mają widoczne, nieregularne poziome gałęzie i przerwy.
Zbliżenie r3 pokazuje pełne, szerokie spódnice rdzenia; igliwie nie zmienia ich obwiedni.
Zamiast dokładać geometrię: przesunąć budżet z ośmiu szerokich pierścieni do czterech
węższych, a odzyskane trójkąty przeznaczyć na mniejsze i liczniejsze gałęzie.
Low: core 5 boków × 7 segmentów × 2 = 70 tris, 12 kart × 2 = 24, pień4 →98/drzewo.
Próba Low: core 5 × 3 × 2 = 30, 32 karty × 2 =64, pień4 →98/drzewo.
High: core 8 × 7 × 2 =112, 54 karty × 2 =108, pień4 →224/drzewo.
Próba High: core 8 × 3 × 2 =48, 86 kart × 2 =172, pień4 →224/drzewo.
Nowe gałęzie mają być wyraźnie węższe niż stare pionowe kurtyny; suma pola kart
musi być policzona dla każdego drzewa i LOD, żeby nie zamienić oszczędności tris
na niekontrolowane nakładanie alfa. Pomiar pola nie zastępuje pomiaru GPU A16.
Rdzeń bez pełnych naprzemiennych półek; obwiednia i wysokości drzew zachowane.
Liczby są projektem, do potwierdzenia na rzeczywistym GLB i renderze.
Nie ruszać globalnej roślinności, materiałów innych dziedzin ani tynku D48.
Jeżeli próba daje cienkie palmy/lizaki albo jasne karty, odrzucić i zachować dowody.
