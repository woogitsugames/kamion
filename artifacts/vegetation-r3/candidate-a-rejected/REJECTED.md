Wariant A danych D51 jest odrzucony. Kod źródłowy: ce7ea7fa, po bazie gpt-vegetation-r1. Cztery środki koron dały dwa nowe drzewa i dwa odrzucenia blocked.

W B/120 Low-overcast wywołania instancji wzrosły z 205 do 209, a liczba wyświetlanych instancji z 129 do 132. Łączna liczba rzeczywistych rekordów wzrosła o dwa; inne rekordy oraz 130 GLB były bez zmian. Wynik przekracza budżet +0. Większe korony pozostają wizualnie niewystarczające w tym kadrze.

Ablacja z bazowymi rekordami po ponownym imporcie dała 205 wywołań, 129 instancji i PNG identyczny z pierwotnym baseline. Nie jest to więc wyłącznie efekt odświeżenia importu. WorldInstances stosuje odległościowy thinning według indeksu, a selekcję poprzedza odrzucanie komórek. Udział przesunięcia indeksów i granic komórek w dodatkowej instancji nie został osobno wyizolowany. Kod tego runtime nie należy do przydzielonych plików sesji i pozostał nietknięty.

Zachowano próbę, logi, źródłowy patch oraz snapshot-candidate-a z metadanymi i rekordami wejściowymi. B będzie osobną próbą zamiany pobliskiego losowego samosiewu; nie ma jeszcze jego oceny renderów ani PASS budżetu.
