# Wczesny podgląd kandydata — tylko cztery kadry Low-clear

Root obejrzał wszystkie cztery JPG o szerokości 960 px: front i narożnik wiat Anders/1000-lecia oraz Fabryka Dywanów. Odświeżono także zdjęcie 1911352299378570 (crop 450 px) i wcześniejszy render Anders front. Render ma diagnostyczną pozę WORKING_VALUE, bez dopasowania kamery do fotografii.

Przez boki i tył widać tło. Usunięcie przedniego środkowego słupka, lżejsza ławka i czerwona rama poprawiają odczyt względem wcześniejszej ciemnej skrzyni. Narożniki pokazują płytki, dwusegmentowy profil dachu Low. W tych czterech obrazach nie widać szczeliny podpór ani wyraźnego błędu nakładania szyb.

Nie potwierdzono barwy i wymiarów z pomiaru zdjęcia, High, overcast, przeciwnego narożnika, zachowania w ruchu ani okluzji/sortowania pod innymi kątami. Kolizja wiaty nadal jest zastanym pełnym prostopadłościanem: wizualnie otwarte wejście nie oznacza przechodniej kolizji. Wiata stoi na zastanej trawie; nie zmieniono cudzej geometrii chodnika ani położenia obiektów.

Poniżej wyłącznie CPU DrawEst z `before/Low-clear/stats.txt` i `early-after1/Low-clear/stats.txt`, nie rzeczywiste wywołania ani czas GPU:

| Kamera | Mesh przed → po | Instancje draws przed → po | Cienie mesh przed → po |
|---|---:|---:|---:|
| Anders corner | 224 → 224 | 149 → 148 | 68 → 68 |
| Anders front | 113 → 113 | 110 → 109 | 68 → 68 |
| Factory corner | 364 → 364 | 550 → 550 | 39 → 39 |
| Factory front | 213 → 213 | 504 → 504 | 39 → 39 |

Liczba renderowanych instancji Factory zmieniła się 1255 → 1256 i 801 → 802; przyczyna nie została osobno zweryfikowana. Pełny audyt JSON potwierdził identyczne dane wszystkich instancji po normalizacji wyłącznie dwóch nazw prototypu. Zaokrąglone trisK nie są dowodem dokładnego przyrostu ani spełnienia limitu +2%.

Nie zastępuje to 236 wymaganych kadrów, 118 dokładnych liczników Low, ośmiu kadrów drugiego narożnika ani niezależnej oceny. Brak podstaw do zamknięcia rundy na tym podglądzie.
