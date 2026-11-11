# Uwagi lidera dla GPT (s10) — kolejne rundy po scaleniu A/B/C

Scalone na main: A 0086 (+ poprawka Claude 0101), B 0088, C 0098. Recenzje: `docs/reports/visual/REVIEW-2026-11-11-s10-0086.md`, `…-0101.md`, `…-0088-0098.md` (pełne listy P0/P1/P2 z kamerami). Zasady jak w GPT-TASK-02-S10.md.

## C r13 — ADR 0108 światło/post r13 (gałąź `gpt-light-r13`, STATUS `artifacts/light-r13/STATUS.md`)
- **P0:** RCAS wyłączony na High rozmywa asfalt przed kabiną (szczegół −38–40 %, gradient linii −44 %); zysk nieba pochodził z wyłączenia ditheringu przed LUT. Przywróć RCAS z ablacją 0,25/0,5/0,75 i wybierz po pomiarze.
- Cienie przy niskim słońcu: falisty brzeg (`r10_hall_3` lowsun); pieprz płaskich ścian (−5–8 % to za mało); mgiełka dalekich pionów; AO/cień pod wiaduktem — nieruszone w r12.
- Biały lakier aut przepalony w słońcu (`r10_hall_1`, `r10_hall_4`) — ekspozycja/tonemapping, nie pigment.
- Komin na `photo-biezenstwa-ground` pochylony (rotacja instancji) — sprawdź i napraw albo przekaż liderowi.

## B r3 — ADR 0109 roślinność r3 (gałąź `gpt-vegetation-r3`, STATUS `artifacts/vegetation-r3/STATUS.md`)
- Korony liściaste Putry za jasne (p50 72–83 vs zdjęcia 47–65) — skoryguj bez cofania DK8.
- Wariacja trawy w skali metrów nie istnieje (spadła 19,3→16,1 na `route-onramp-andersa-above`).
- Żywopłoty: bordowe wałki, szwy siatki (`g3a-rondo-bie-approach`).
- Sosny: sylwetka „lizak”, impostory z obłymi rozmytymi brzegami (docs/06), twardy poziomy szew kory na pniu.
- Tuje: Low 0,49–0,52 vs High 0,28 (spójność tierów).

Kolejność: po bieżących (0087, 0089, 0090, 0099) — najpierw C r13 (P0), potem B r3. Numery ADR: 0108, 0109. Ostatni przydzielony: **0109**.
