# S10 — raport koordynatora (WIP)

Stan: 2026-11-11, 13:54 CET. Pakiet nie jest jeszcze zamknięty.
Repozytorium: `C:/Users/matma/Documents/Claude/kamion`.
Koordynacja: `.claude/worktrees/gpt-s10-coordination`, `codex/s10-coordination`.
Nie scalano ani nie pushowano main z tej sesji. Integrację prowadzi lider Claude.
Maksymalnie trzech wykonawców pracuje równolegle, każdy we własnym worktree.

| Strumień | Gałąź / ostatni zweryfikowany punkt | Wynik i pozostałe prace |
|---|---|---|
| A / 0086 | gpt-tint-gamma / 1317afba | Kontrakt koloru i test GPU potwierdzone. GIS 359 passed, 2 xfailed; EditMode 226/226. Krytyk wykrył błędną kalibrację hali i ekranów; wcześniejsze zatwierdzenie wyglądu wycofane. Korektę prowadzi lider w tint-r2 / ADR 0101. |
| B / 0088 | gpt-vegetation-r2 / 4db366ad | Scalony przez lidera; niezależny krytyk: jakość FAIL, kontynuacja0109. GIS 364 passed, 2 xfailed; EditMode 218/218. Wszystkie 236 porównań: delta draws 0, Low tris -8..0k. Ograniczenia stylu i brak pomiaru GPU na telefonie zapisane w raporcie. |
| C / 0098 | gpt-light-r12 / 5db77e9d | Scalony przez lidera; jakość FAIL, P0 rozmycia asfaltu do0108. GIS 355 passed, 2 xfailed; EditMode 221/221. 236 wierszy stats identycznych bajtowo. Jawnie opisano kompromis ostrości przy skalowaniu i brak pomiaru urządzenia. |
| F / 0087 | gpt-truck-paint / 4559296e | Pierwszy kandydat: naprawione przepełnienie RGBAHalf lamp, rzeczywisty odczyt GPU poprawny. Połysk drzwi i mediana szkła nadal poniżej progów. Trwa diagnoza odbicia; brak akceptacji wyglądu. |
| G / 0089 | gpt-car-paint / a1853369 | Świeża baza już spełnia cel czarnych drzwi. Osobno zmierzona poprawka Pearl; trwają koła, neutralna opona i cztery poziomy brudu per instancja. |
| E / remiza r7 | gpt-firestation-r7 / 75a729f5 | 160 obrazów bazowych. Produkcyjny kandydat roślin w przebudowie; właściwe kadry i kalibracja pozostałych elementów jeszcze przed nami. |
| D / 0099 | gpt-surface-wear / d00807ed | Bramka 0095 potwierdzona na main. Przygotowano świeży świat, źródła i audyt UV; implementacja czeka na wolne miejsce. |

## Wyniki wymagające zachowania przy integracji

- B: surowe, przypięte hashem mapy CC0 sosny nie są w Git. Po scaleniu B, PRZED generacją, należy uruchomić `uv run --project tools/worldgen python artifacts/vegetation-r2/restore_cc0_inputs.py --root .`. Pakiet i bezpieczny skrypt są skopiowane do głównego `artifacts/vegetation-r2`. Po scaleniu B przez lidera koordynator wykonał ten krok: obie brakujące mapy odtworzone bez nadpisywania, zgodność manifestu i hashy potwierdzona (B-main-input-restore.json).
- E: analogiczny pakiet CC0 fir_tree_01 jest przygotowany w prywatnym worktree. Taksonomia źródła nie potwierdza Picea; nie jest opisywany jako zweryfikowany skan świerka. Ostateczna instrukcja odtwarzania trafi do raportu E.
- A: kontrakt `_Tint` i kalibracja wyglądu są oceniane oddzielnie. Wykrycie przepalonej hali oraz za ciemnych ekranów jest jawne w REVIEW-A-0086.md. Pomiary z jednego zacienionego fragmentu nie wystarczają do zamknięcia kalibracji.
- Każdy zamknięty strumień ma własny REPORT, ADR, wyniki i ograniczenia. Pary porównawcze używają niezmiennej bazy; późniejsza kanoniczna przebudowa ciężarówki jest opisana osobno.
- Nie mierzono czasu GPU na urządzeniu ani nie używano telefonu/ADB. Stats z edytora nie są dowodem wydajności GPU telefonu.

## Współbieżność i okno telefonu

PHONE-RACE.md dokumentuje krótkie nakładanie uruchomień w przerwach zmiennej blokady lidera. Wprowadzona własna blokada zatrzymała nasze Unity do rzeczywistego końca gate3B o 11:54:10. Po stabilnym braku blokady wykonano kontrolowany pełny retry B i dopiero o 11:56:56 jawnie wznowiono F/G/E. Każdy kolejny start sprawdza obie wspólne blokady. Nie dotykano telefonu ani procesów innych wykonawców.

## Następny etap

Dokończyć i niezależnie obejrzeć F/G/E, uruchomić D po zwolnieniu miejsca, zebrać pełne testy i budżety oraz zastąpić ten raport końcowym zestawieniem rzeczywistych wyników i otwartych ograniczeń. Zachować zakaz scalania do main.

Aktualizacja: lider zewnętrzny scalił B (6b8f9123) i C (bfdde95f); trwa jego regeneracja. Ponowne okno telefonu perf-low-r1 od 12:27:10 wstrzymuje nasze Unity. Pełne GIS F i G działają podczas tej blokady.

Stan uzupełniający: G 375 passed / 1 xfailed, zapisany czysty 75082bd1; D nieaktywny patch dba4855d, bez zmiany bazy. Lider zregenerował B+C na main14790c48: 389 passed / 1 xfailed. E pierwszy wariant koron odrzucony jako zbyt rzadki, następny .55R w przygotowaniu. F następna próba obejmuje uzasadnioną źródłowo krzywiznę normalnych drzwi; nadal brak akceptacji. Nowe okno telefonu diag2 blokuje Unity; próba wznowienia została poprawnie zatrzymana przez powrót PHONE_RUN.

Najnowszy stan: F finalne238/238 EditMode i102 kadry zweryfikowane, jakość właścicielska częściowa; G pełne324R3 gotowe, EditMode zatrzymała blokada telefonu; E przyjęta ograniczona poprawa koron z ujawnioną wąskością, dalsza kalibracja elewacji przed nami. D nieaktywne patche92bc26af, produkcja i baza nienaruszone. Kolejka po F/G/E/D:0108 światło r13, następnie0109 roślinność r3 według GPT-FEEDBACK-S10.md. B/C historyczne testy i scalenia nie oznaczają pełnego zaliczenia jakości.
