# D gate R2 — niezależny przegląd High, 2026-11-11

**Werdykt: rzeczywista poprawa względem r1; brak widocznej regresji starych scuffs; czytelność dwóch śladów tylko częściowa.** Nie nadaję bezwarunkowego PASS dla „dwóch wyraźnych śladów w każdym kadrze High”. Najsłabszy pozostaje drugi ślad wyjazdu w clear. Nie oceniam tutaj Low ani całego zadania D.

## Zakres

Oglądnięto wszystkie osiem R2 High: entry, exit, kerb_nose i kerb_outer w clear/overcast, oba kontakty oraz cztery pary r1/R2 w rozmiarze 960. Entry/exit porównano do `gate-pair-before` i `gate-pair-after` (r1), kerby do `gate-kerb-before`, korzystając z odpowiadających wersji `*-960`. Bez rozciągania kontrastu, retuszu czy alignowania obrazów. Źródło: D worktree `gpt-surface-wear/artifacts/surface-wear-r1/`. Nie zmieniono źródeł, nie wykonano Unity ani testów.

Przeczytano `gate-r2-screen-metrics.json`, `gate-r2-vs-r1-screen-metrics.json`, `gate-r2-kerb-negative-metrics.json`, `gate-r2-capture-proof.json` i `gate-r2-native-proof.json`. Są to dowody autora odczytane przez recenzenta, nie nowy odczyt meshów/GPU przez tę sesję. Native proof podaje 154 meshe, niezmienioną geometrię/UV0/age, dwa zmienione bufory UV1 i po 72 signed vertices na tier, minimum długości−4.19921875, keyword `_DECAL_TYRE`. To potwierdza zakres techniczny, nie wizualny PASS.

## Co rzeczywiście widać

| Kadr High | Ocena widocznego R2 względem r1/bazy |
|---|---|
| Entry clear | Dwie podłużne, nierówne smugi dają się odróżnić po obu stronach pętli indukcyjnej; krótszy fade ujawnia więcej ich środka. To poprawa obrazu, nie tylko różnica w masce. Nadal delikatne, lecz nie wymagają interpretowania całej jezdni jako mokrej plamy. |
| Entry overcast | Para jest widoczniejsza niż w r1, choć bardziej zlewa się z ciemniejszym asfaltem. Oglądana obok bazy daje czytelny kierunek przejazdu; bez pary nadal jest subtelnym śladem eksploatacji, nie mocnym akcentem. |
| Exit clear | Jeden ślad jest czytelny, drugi — bliżej lewej strony przejazdu/wysepki, w kierunku dolnego środka kadru — jest bardzo słaby. W pełnym960 może zostać pomylony ze zwykłą wariacją asfaltu. R2 poprawia go, ale nie daje mi przekonującej, samodzielnej czytelności obu pasów. To główny brak P1 w tej ograniczonej bramce. |
| Exit overcast | Słabszy pas daje się wyśledzić lepiej niż w clear, nadal z wyraźną asymetrią pary. Postęp względem r1 jest realny, lecz nie jest to mocny dowód „dwóch od razu oczywistych śladów”. Nierówne zużycie samo w sobie nie jest błędem fizycznym; ograniczenie dotyczy zadeklarowanej czytelności. |
| Kerb nose/outer, oba światła | Nie widzę nowego zaciemnienia całej krawędzi, rozlania ani zmiany starych ciemnych przetarć. Kontur, szerokość i wrażenie materiału scuffs wyglądają jak w historycznej bazie. Nie rozszerzam tego na nieoglądane kerby. |

W żadnym z ośmiu High kadrów R2 nie widzę czarnej, gładkiej „mokrej wstęgi” dodanej przez tę zmianę. Kruszywo i lokalna ziarnistość asfaltu pozostają czytelne pod smugami; przyciemnienie ma przerwy i miękkie zakończenia. To ocena tych obrazów, nie pomiar szorstkości ani dowód fizycznej ilości gumy. Czarne obwody pętli indukcyjnych i liniowe cienie szlabanu są innymi elementami — nie zaliczam ich do nowych śladów opon.

## Liczby jako wsparcie, nie zastępstwo oglądania

Odczytane średnie przyciemnienie RGB w maskach źródłowych trójkątów (LSB, R2 względem bazy; maski obejmują fade i niepokryte piksele, nie jest to fizyczna reflektancja):

| High | Pierwszy pas | Drugi pas |
|---|---:|---:|
| Entry clear | 4.04 (mediana 2.33) | 5.41 (4.67) |
| Entry overcast | 3.18 (2.00) | 4.19 (3.67) |
| Exit clear | 4.69 (3.67) | **1.27 (0.67)** |
| Exit overcast | 4.15 (3.33) | **2.19 (1.33)** |

R2 względem r1 zwiększa średnie przyciemnienie entry o 2.79/3.75LSB w clear i 2.16/2.88 w overcast; exit o 3.20/0.93 i 2.78/1.54. Dla słabego exit clear tylko około16% pikseli jego maski ciemnieje względem bazy o ponad 3 LSB. To jest zgodne z wizualnym ograniczeniem, ale same te liczby nie wyznaczają progu akceptacji.

Negative control starego kerb scuff podaje High mean-absolute RGB około0.444–0.472LSB, p95=1, udział różnic>3LSB=0. Średni signed RGB jest bliski zeru. Zgadza się to z brakiem widocznej zmiany starych przetarć, a nie z tezą o ich idealnej zgodności bajtowej. Poza maskami gate raportuje około0.50LSB mean-absolute różnicy High; nie nazywam całej sceny pixel-identical.

## Ograniczenia i decyzja do połączenia przez ROOT

Capture proof deklaruje dokładną zgodność rzeczywistych pakietów camera/vehicle dla entry/exit i równe zaokrąglone liczniki wszystkich 16 ujęć. Historyczne kerb BEFORE nie ma runtime packet: zachowuję zastrzeżenie, że zgodność authored kamery i oglądany brak regresji NIE dowodzą wstecz dokładnej zgodności macierzy. Liczniki są estymatami przed SRP, nie pomiarem GPU/telefonu.

Zakresowy **PASS braku widocznych czarnych mokrych wstęg i ubocznej zmiany starych kerb scuffs** w High 8. **PARTIAL dla czytelności pary**, z konkretnym brakiem exit-clear; entry osiąga wiarygodniejszy odczyt dwóch śladów niż r1. Nie zaleca się globalnego przyciemniania asfaltu lub starych scuffs dla zamknięcia tego punktu. Jeżeli wymaganiem końcowym pozostaje natychmiast rozpoznawalna para także przy exit-clear, tego warunku te obrazy jeszcze mocno nie dowodzą. ROOT łączy to z osobnym Low 8 i decyduje o zamknięciu D; ta recenzja nie uruchamia kolejnego tuningu.
