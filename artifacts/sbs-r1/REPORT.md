Runda sbs r1: PASS narzędzia i kompletności dowodów po niezależnej recenzji. Kalibracja pozy jest częściowa; bramka jakości świata pozostaje UNVERIFIED.

Gałąź gpt-sbs-r1. Kod i renderowany HEAD: d0dca81e; baza świata main: 4c9905b1. Do integracji jest cała gałąź. Nie scalano do main i nie pushowano.

Przed: 40 zdjęć i 160 archiwalnych par, bez jawnej klasy pozy, w tym sześć błędnych J1. Po: 42 zdjęcia i 168 świeżych renderów, 25 przybliżonych B × 4 = 100 arkuszy dowodowych oraz 17 C × 4 = 68 wykluczeń. Brak A. Sześć J1, osiem J2, 2948 i dwa Commons nadal są C. Obejrzano 144 próby w 16 galeriach; żadnej nie zatwierdzono automatycznie.
Horyzont 2948 wyznaczono z dwóch krawędzi: 0,5249381 wysokości. Dwa rzeczywiste Commons przy około 230/249 m mają odrębne licencje i SHA, ale niekalibrowane pozy. Pierwsze 300 m nadal bez zaakceptowanych par; 0–200 m bez kandydatów. Pełna atrybucja: docs/refs/sbs-gate3-attribution.md.

Walidacja: SBS 40/40, EditMode 261/261, końcowy GIS 523 passed / 1 xfailed w 663,68 s. Import 64 chunków Low+High. Generator świata kod 0, brak fallback=True; 64/64 SHA GLB zgodne. Audyt potwierdził jedną epokę wszystkich klatek i zero braków. Ciężkie zadania po zmianie polityki korzystają z puli heavy; pełny końcowy GIS wykonano na końcu rundy.
Low overcast, te same 42 kamery i świat przed/po: zmiany estymacji draws geometrii, draws instancji i trójkątów wynoszą 0. Największe zarejestrowane sumy: Low 812 = 445 + 367; High 1376 = 945 + 431. To estymacje CPU przed batchingiem, nie GPU telefonu. Wszystkie 168 wierszy i instancje osobno: [liczniki](counters/camera-counters.csv), [porównanie Low](low-counters-delta.json).

Dowody o szerokości 960 px: [100 arkuszy](evidence/sheets/), [28 stron przeglądu](overview/), [16 galerii prób](pose-galleries/), [przykładowa para](evidence/sheets/High-clear/sbs-g3-a-454716650857984.png). [Audyt](AUDIT.json), [migawka wejść](evidence/inputs.zip), [recenzja niezależna](REVIEW-INDEPENDENT.md), [opis oględzin](VISUAL-REVIEW.md).
Narzędzie odrzuca nieznane klasy, mieszane epoki i podmienione obrazy; adnotacje punktów wiążą się z SHA obu paneli. Pojedynczy punkt nie zatwierdza pozy. Wszystkie flagi fotometrii pozostają false, więc histogramy są diagnostyką, bez zbiorczego wyniku albedo lub ekspozycji.

Nie zakończono kalibracji C, kompensacji roll ani zebrania 2–3 pewnych kotwic; nie uzyskano początku trasy. W świecie nadal widać różnice nieba, podłoża pod wiaduktem, nawierzchni i wyposażenia. Nie zmieniano tych dziedzin ani nie używano telefonów. Lokalne produkty generatorów poza sbs przywrócono do HEAD bez commitowania.
Przewidywane konflikty: tools/refs/sbs_gate3.py, scripts/sbs-gate3.ps1, Data/Regions/**/sbs_*.json, tests/gis/test_sbs_gate3.py, ADR 0111 i atrybucja. Artefakty są odrębne. Następna runda: gpt-sbs-r2, merge main, metryki kontrastu i strona artifacts/sbs-gate3/latest/index.html z trendem oraz ponowny render aktualnego main.
