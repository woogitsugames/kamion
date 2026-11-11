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

Kolejność: po bieżących (0087, 0089, 0090, 0099) — najpierw C r13 (P0), potem B r3. Numery ADR: 0108, 0109.

## Po recenzji J/K (`docs/reports/visual/REVIEW-2026-11-11-s10-gpt-JK.md`) — dla sesji J i K (mogą kontynuować w tych samych worktree po scaleniu, z AKTUALNEGO main)
- **J r2 — ADR 0111** (gałąź `gpt-sbs-gate3-r2`): P0 — 6 par z błędną pozą (810896, 339463, 962702, 182011, 326454, 1406) + pole `pose_confidence` i odrzucanie par; P1 — seria richlv 2020 przesunięta bocznie 3–8 m, horyzont 2948, brak zdjęć na pierwszych ~300 m G3-A. Po poprawkach: ponowny render wszystkich par na aktualnym main (po 0101/0102/0105/0085r2).
- **K r2 — ADR 0112** (gałąź `gpt-cab-r2`): K1 — lusterka przednie/krawężnikowe pokazują wnętrze kabiny z góry (bez dachu) — popraw kamery/culling lusterek i sprostuj ADR 0104; K2 — ramię lewego lusterka zasłania ~25–30 % szkła szerokokątnego; P2 — ramka szkła, smuga tekstury deski, podłokietnik przez fotel, ziarno plastiku/zużycie z pozycji kierowcy.

## Priorytety bramki 3 z porównań side-by-side (do uwzględnienia w 0108/0109/0099)
1. Niebo/ekspozycja: płaski gradient bez chmur, render skupiony w półtonach (~32 pary) → **0108**.
2. Trawa/pobocza: „trawnik golfowy” zamiast żółtozielonej nierównej trawy z chwastami (~24) → **0109**.
3. Asfalt za jasny i jednolity, bez kolein/łat/spękań (~21) → **0099** (w toku).
4. Bariery na pomoście / przy łącznicach (14) → Claude (węzły r4).
5. Pod wiaduktem: kruszywo zamiast trawy, spód, słupy (13) → sprawdzić po ponownym renderze z 0105.
Ostatni przydzielony ADR: **0112**.
