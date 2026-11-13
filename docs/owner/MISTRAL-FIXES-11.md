# Poprawki dla Mistrala — runda 11 (s20, 2026-11-13)

Przegląd: `docs/reports/REVIEW-2026-11-13-s20-mistral-m52-fix3.md`. M52-FIX-3: punkty 1, 3, 4 i 5 przyjęte. Do poprawy jest tylko pkt 2 (oględziny kadrów) oraz resztki w uwagach.

## M52-FIX-4 — P2 nawierzchnie (`research/mistral-p2-surfaces-2`): opisy kadrów niezgodne z obrazem

```
Repo woogitsugames/kamion, gałąź research/mistral-p2-surfaces-2 (PR #48 scalony — dopisz commity do tej gałęzi, nie twórz PR). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p2-surfaces-2/.
Przegląd s20 (docs/reports/REVIEW-2026-11-13-s20-mistral-m52-fix3.md): przypisania ulic (M52-103…105 → Al. Tysiąclecia), liczby M46 (way_id, odległość, Δ — wszystkie 44 zgadzają się z OSM), P-5, M52-118 i seed 20261114 są przyjęte. Nie ruszaj ich. Do poprawy:
(1) „Niedostępne w CDN” jest nieprawdą. Kadry są w Twojej paczce ZIP i są identyczne bajtowo (md5) z innymi wierszami: cross-andersa-02 = jar-03 (M52-071 = M52-031), cross-andersa-06 = jar-05 (M52-075 = M52-033). cross-andersa-08 (M52-077) i cross-andersa-14 (M52-083) też są w ZIP. Obejrzyj te 4 pliki z ZIP i wpisz „co widać”. Uwaga: M52-077 i M52-083 są na POZIOMIE TERENU (jezdnia DK19, łącznica z zebrą, budynek mikomax), a NIE „z estakady”.
(2) Opisy kadrów przeczą obrazowi w ok. 40 % sprawdzonych wierszy. Przykłady: M52-061, M52-067, M52-068 (i M52-062) leżą na ESTAKADZIE (balustrady mostowe), a opis mówi „jezdnia na poziomie terenu”. M52-031, M52-039, M52-067 mają „podwójną ciągłą”, a na zdjęciu widać przerywaną linię pasa. M52-102 opisuje strzałki, przejście i sygnalizatory, a w kadrze ich nie ma. Ponownie obejrzyj WSZYSTKIE 80 kadrów z plików ZIP, jeden plik na jedno wywołanie modelu wizyjnego. NIE używaj szablonu zdania. Dla każdego kadru wpisz osobno: (a) poziom: estakada (balustrada mostowa) / teren; (b) linie: rodzaj linii osiowej i linii pasa (ciągła / przerywana / podwójna ciągła / brak); (c) przejście w kadrze: tak / nie; (d) 1–2 obiekty charakterystyczne. Przy limicie commituj po każdych 10 kadrach.
(3) Spójność duplikatów: 11 par plików jest identycznych bajtowo (policz md5 w ZIP). Każda para musi mieć ten sam opis „co widać”. Dopisz w uwagach „ten sam plik co M52-xxx”. Dotyczy to m.in. par 029/057, 041/062, 050/068, 046/079, 049/080, 064/076, 059/074, 065/072, 089/102.
(4) M52-036…M52-052 mają w opisie „sekw. KV 14055”, a należą do sekwencji 2769366 lub 3686129 (patrz kolumna url_źródła). Popraw.
(5) M52-071: wybór ronda 536419699 (9,6 m, Δ 29,1°) jest niespójny z M52-075 dla tej samej sekwencji. Najbliższa jest Andersa 177876107 (1,6 m, Δ 55,4°). Zastosuj taki sam zapis jak w M52-075 („reguła azymutowa niespełniona, azymut = artefakt…”). W M52-053/055/056/057 usuń „jezdnia estakady z barierami mostowymi” wszędzie, gdzie kadr jest na poziomie terenu. Usuń stare wpisy „N m od osi jezdni wg OSM” (30 wierszy, np. „-1 m”, „13 m”), bo przeczą liczbom M46 r3.
(6) M52-116: po nowych oględzinach powtórz wniosek o kolorze. Dodaj jedno zdanie o czerwonym pasie widocznym za lewą barierą estakady (jar-11, andersa-3686129-05): czy to gzyms, pas dzielący, czy droga rowerowa. Jeśli nie da się rozstrzygnąć, wpisz UNVERIFIED.
(7) Samokontrola: nowy seed (jawny), 24 wiersze. Dla każdego kadru porównaj swój opis z obrazem z ZIP (nie z poprzednim opisem). Wpisz liczbę zgodnych i niezgodnych.
W komentarzu PR #48 wklej SUROWE wyjście `git diff --stat origin/main`. NIE scalaj. Na końcu „M52-FIX-4 gotowe” i koniec.
```
