# ADR 0018: niweleta z lokalnymi ograniczeniami i test korytarza trasy

Status: przyjęta (2026-11-09). Kontekst: blokada trasy `route_start` na s = 571 m w r4 (DEVICE-RUN-2026-11-09, sekcja r4).

## Problem
W v3 generator dobierał jedną wagę wygładzania λ dla całego łańcucha i podnosił ją, aż promień pionowy spełniał minimum klasy wszędzie. Prześwit nad drogą pod wiaduktem był twardą równością. Na zachodniej jezdni Andersa przy Rondzie Bieżeństwa dało to λ = 2,8·10⁹, czyli praktycznie prostą od wiaduktu do końca łańcucha. Rampa szła 2,2 m nad NMT jeszcze 250 m za wiaduktem. Reguła murów oporowych z v3.1 uznała ją za rampę na murach. Kapa, mur i bariera tej rampy weszły na łącznicę z ronda, która w rzeczywistości biegnie tuż obok na poziomie terenu.

## Decyzja
1. λ dobieramy tylko do szumu danych (wiersze ograniczeń mają przy tym wagę 1). Zbyt ostre zagięcia usztywniamy lokalnie, tylko w wierszach, które łamią promień (±1 m). Prześwit jest dolnym ograniczeniem `z ≥ wymagane`. Jest egzekwowany przez przypinanie stacji, które spadły poniżej (`profile.bounded_curvature_fit`).
2. Jezdnia, która dotyka krawędzią innej, równoległej drogi naziemnej rozwiązanej wcześniej, bierze jej wysokość na wspólnej krawędzi jako dane o wadze 400 (`profile.adjacent_targets`).
3. Generator sprawdza otoczenie dróg: pobocze, rów lub chodnik nie mogą sięgać na sąsiednią jezdnię. Nos wyspy powstaje tylko przy prześwicie ≥ 0,5 m. Spadek poprzeczny łańcuchów przechodzących przez węzeł jest w węźle wspólny.
4. Nowy test `tests/gis/test_route_corridor.py` sprawdza na całej trasie korytarz 3,55 × 4,0 m i profil kół (≤ 3 cm na 0,5 m) na tej samej geometrii kolizji, którą buduje import Unity.

Wartości liczbowe (wagi, okna, 0,5 m, 20 m) to `WORKING_VALUE` w `tools/worldgen/roads/standards.py`.

## Konsekwencje
- Zmieniają się niwelety wszystkich łańcuchów, które wcześniej wymagały zwiększenia λ. Rampy Andersa schodzą do terenu po ok. 90 m przy pochyleniu ≤ 5,2 %. Mury oporowe są krótsze.
- Build trwa ok. 3,5–4 min zamiast 2,5 min, bo zagęściła się kolizja łat skrzyżowań.
- Rzeczywista długość i kształt ramp nadal nie są zmierzone (NMT to grunt). Zdjęcia z sesji właściciela mają zweryfikować miejsce, w którym rampa styka się z łącznicą.
