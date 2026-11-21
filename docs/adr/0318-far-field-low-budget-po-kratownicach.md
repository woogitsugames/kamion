# ADR 0318 — Budżet Low tła po wprowadzeniu kratownic

Status: Proposed, 2026-11-21, c-regress-cli.
Powiązane: ADR 0085, 0141, 0311 (kratownice i własność tła), 0316.

## Przyczyna

Przebudowa C ujawniła 67 421 trójkątów Low przy budżecie 30 000 oraz skyline
3 174 przy budżecie 3 000. `bd8af626a` zastąpił pełne płaszczyzny słupów
prętami trójkątnymi również na Low; korekta `3a3719771` pozostawiła 204
trójkąty na słup. W C 190 słupów Low kosztowało 38 760 trójkątów.
`33db1f4cf` poprawnie zamknął dachy i dodał pasy bez okien, lecz pozostawił
stary dobór odległych budynków oraz nadbudówki dachowe Low.

## Decyzja

- Budżety 30 000 / 3 000 pozostają bez zmian. Dachy i pasy bez okien pozostają.
- Low zachowuje wszystkie słupy wybrane dotychczasową regułą odległości.
  Każdy ma cztery nogi, trzy panele ukośnego kratowania na dwóch sąsiadujących
  ścianach i dwa poprzeczniki. Pręty są paskami zwróconymi ku kaflowi:
  16 pasków, 32 trójkąty. High zachowuje przestrzenne pręty, 204 trójkąty.
  Paski są skierowane do środka własnego kafla. Przy patrzeniu z jego rogów
  ich szerokość kątowa maleje zgodnie z kosinusem odchylenia, lecz nogi nie
  znikają; test obejmuje wszystkie rogi, osiem położeń wokół kafla i cztery
  obroty słupa. Widok dokładnie od boku poza własnym kaflem może zaniknąć;
  tło tego kafla nie jest przeznaczone do oglądania z sąsiedniego kafla.
- Dobór budynków Low uwzględnia rozmiar po kompresji. Poza 900 m od krawędzi
  pomijamy koperty o najdłuższej krawędzi poniżej 20 m i wysokości poniżej
  10 m. Wartości `WORKING_VALUE`; zachowujemy pobliską zabudowę i wysokie
  dominanty. Nie losujemy według identyfikatora ani nie zmieniamy inwentarza
  źródłowego. W C reguła usuwa 366 małych kopert, 5 152 trójkąty.
- Nadbudówki dachowe są detalem High. Zamknięcie głównego dachu pozostaje Low.
- Kominy pomijają ściany niewidoczne z całego kafla, tą samą regułą co
  elewacje budynków. Geometria widoczna i zastępniki kominów regionalnych
  pozostają. W C zwykłe kominy Low: sektory 660 → 460, skyline 348 → 288.

Zliczenie na istniejącym cache C, bez zapisu świata, przewiduje Low 29 161,
skyline 2 966. Wynik pełnej przebudowy i pytest będzie w raporcie c-regress-cli.
Testy sprawdzają otwory kratownicy w dwóch rzutach, cztery obroty, obie
jakości, brak trójkątów zdegenerowanych oraz zachowanie dachów i dominant.
Oglądanie w Unity wyłączono na wyraźne polecenie właściciela; ocena obrazu
w grze pozostaje poza zakresem tego zadania.
