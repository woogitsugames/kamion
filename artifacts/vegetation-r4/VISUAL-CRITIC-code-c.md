# Recenzja kodu C, przed wynikiem testów i renderów

Niezależny vegetation_critic przeczytał kod pokrywy i testy bez uruchamiania ciężkich narzędzi. Nie znalazł oczywistego błędu deterministycznego próbkowania, kontroli odstępów ani barycentrycznego osadzenia korzeni. To dopuszczenie do próby, bez wizualnego PASS i bez potwierdzenia kosztu.

Najważniejsze ryzyko wyglądu: tilt 0,15–0,65 rad oznacza głównie pionowe karty, które mogą dać szczotkę zamiast niskiej pokrywy. Odstęp 28 cm i szerokość 12–22 cm mogą też zostawić gładki blat między skupiskami. Nie zwiększać automatycznie wysokości w odpowiedzi na brak pokrycia. Odrzucać widoczne prostokąty, rzędy, duże wystające płaty lub wiszące podstawy. Jitter i minimalny odstęp nie dowodzą jeszcze braku rytmu na renderze.

Recenzent wskazał samopotwierdzający test obrysu konstruowanego przez wszystkie wierzchołki capu. Poprawiono go przed wykonaniem testów: obszar pochodzi z unii rzeczywistych trójkątów, pokrywa jest sprawdzana na wszystkich czterech rabatach, a E1 dodatkowo potwierdza brak punktów wewnętrznych. Dodano przypadek wysokości na dwóch różnych nachyleniach. Korzeń na powierzchni nadal nie jest dowodem osadzenia całej szerokości karty; ocena podstaw i obrysu pozostaje obowiązkiem próby wizualnej.
