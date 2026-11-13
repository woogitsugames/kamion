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

## M47-FIX-3 — P11 zdjęcia Dojlidy (`research/mistral-p11-dojlidy-photos`): kody znaków nadal niezgodne z obrazem

Przegląd: `docs/reports/REVIEW-2026-11-13-s20-mistral-m47-fix2.md`. M47-FIX-2: pkt 1, 2, 3, 5 i erraty s17 przyjęte. Pkt 4 (audyt znaków) do powtórki.

```
Repo woogitsugames/kamion, gałąź research/mistral-p11-dojlidy-photos (PR #39 scalony — dopisz commity do tej gałęzi, nie twórz PR). Najpierw `git fetch && git rebase origin/main`. Zmieniaj tylko research/mistral/p11-dojlidy-photos/.
Przegląd s20 obejrzał 27 wierszy z poprawionymi znakami na wycinkach z pełnej rozdzielczości. 13/27 nadal ma błędny kod. Nie ruszaj: P11-001, 002, 005, 014, 037, 043, 057, 066, 081, 129, 143 ani erraty 026/027/115/042.
(1) Popraw te wiersze dokładnie tak (manifest + README §7/§8 + audit_20_percent.json):
 013: A-7 (×2: przy tablicy ulicy, od tyłu; w głębi nad D-6), D-6, C-13/16 (pieszy+rower). USUŃ A-16.
 022: A-7 (od tyłu) + żółta tablica informacyjna „zakaz wstępu” na ogrodzeniu. USUŃ B-2.
 030: B-2 (zakaz wjazdu) z tabliczką „Nie dotyczy pracowników …”.
 039: B-33 (30), B-36, D-6, D-18, niebieski kwadrat ze strzałką (D-3). USUŃ A-16 i D-40.
 054: C-13, C-9 (nakaz jazdy z prawej strony znaku), A-7 od tyłu, sygnalizacja. USUŃ C-1/C-2.
 073: A-7 (od tyłu), C-13/16, zebra bez znaku D-6 w kadrze. USUŃ B-9 i D-6.
 078: A-7, C-12 (×2), w głębi B-33 (70), B-36, D-3, D-6, C-13, tablice U-3 (szewrony). USUŃ „B-33 20” i A-16.
 079: B-33 (70), B-36, D-3, C-13 (okrągły), D-6. USUŃ B-2 i C-3/C-4.
 086: B-2, D-6 (×2), tablice z numerem drogi 678. USUŃ A-16.
 087: B-2 (zakaz wjazdu) pod A-7 widzianym od tyłu, D-6. USUŃ B-20 STOP.
 108: B-5 (zakaz wjazdu samochodów ciężarowych) z tabliczką, D-6, lustro drogowe. USUŃ B-2, „trójkąt ostrzegawczy” i „z sygnalizacją”. W uwagach dopisz „B-5 — ważne dla P8”.
 120: B-36, B-20 STOP przy bramie (przegląd s18 się mylił, STOP JEST), kegi. Początek punkt_opis „Jacka Kuronia —” zmień na „browar Dojlidy (ulica UNVERIFIED) —”.
 128: D-6, D-18. USUŃ A-16 (też w README §7 wiersz 14).
 131: B-36 (×2) z tabliczką T-24 (odholowanie) + tablica „Droga pożarowa”. USUŃ B-2 i B-35.
(2) Zasady dla pozostałych wierszy ze znakami (041, 056, 063, 067, 068, 069, 070, 071, 076, 083, 089, 096, 104, 105, 106, 110, 122, 126): niebieski kwadrat z pieszym to D-6, A-16 to CZERWONY TRÓJKĄT. Znak widziany od tyłu: wpisz „<kształt> od tyłu (prawdopodobnie A-7/B-20)” i go NIE usuwaj. Kod wpisuj tylko wtedy, gdy na wycinku 3× z pełnej rozdzielczości widać symbol. W innym przypadku napisz „znak nieczytelny”. Żółta skrzynka przy sygnalizatorze to przycisk dla pieszych, nie znak. W 063 dopisz sygnalizację i C-13. W 106 usuń „znak ostrzegawczy”.
(3) P11-082/085 (ulica = Myśliwska przy d = 26,3/25,3 m): dopisz w uwagach odległość do osi lub poligonu Myśliwskiej (16,7/22,9 m wg PR) i way_id OSM.
(4) P11-143, P11-122: punkt_opis nie może zaczynać się nazwą ulicy, skoro ulica = UNVERIFIED (143 ma szyld „Mickiewicza 49”).
(5) W audit_20_percent.json, w liście „usunięte_zmyślone_znaki”, usuń wpisy 013 A-7, 030, 078 „nakaz dookoła ronda” i 120 STOP (te znaki istnieją). Popraw licznik.
W PR #39 wklej komentarz z SUROWYM wyjściem `git diff --stat origin/main` (z gita, nie z difflib; jeśli nie masz gita, napisz to wprost) i listą poprawionych wierszy. NIE scalaj. Na końcu „M47-FIX-3 gotowe” i koniec.
```
