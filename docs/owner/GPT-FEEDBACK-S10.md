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

## Po recenzji 0087/0090 (`docs/reports/visual/REVIEW-2026-11-11-s10-gpt-0087-0090.md`) — scalone na main (`b0685f51`, `1d695be1`)
- **F r2 — ADR 0115 TRAKT r2** (gałąź `gpt-truck-paint-r2`): wygląd praktycznie bez zmian (RMSE kadru 0,04–0,5 %): lakier kredowy, dach biały w High-clear, szyba mleczna bez gradientu nieba. DRL na High przycięty do 255 (1129 px) — zejdź z luminancją. **Poprawki szyby muszą trafić też do szybkiej ścieżki `FragFast` (ADR 0106, Low/Medium)** — inaczej na A16 nic nie widać. REPORT/ADR pisz normalnym tekstem ze spacjami (obecny jest nieczytelny dla właściciela).
- **E r8 — ADR 0116 remiza r8** (gałąź `gpt-firestation-r8`): świerki — blade półprzezroczyste karty → ciemne, szerokie, gęste jak na 7197; szkło łuków: gradient odwrócony (render góra 72 / dół 79–83, zdjęcie góra 62–67 / dół 46–53), clear 94–104 za jasne; zacieki niewidoczne, ciemna plama przy maszcie bez źródła; tuje na Low fasetowane, rytm prawie równy. (Lider poprawił: hero leaf także na Ultra.)
Ostatni przydzielony ADR: **0116**.

## Po recenzji 0089 (`docs/reports/visual/REVIEW-2026-11-11-s10-gpt-0089.md`) — NIE scalone
- **G R4 (ADR 0089, ta sama gałąź `gpt-car-paint`, najpierw `git merge main`):** korekta odcienia lakieru (mnożnik 3,2→12,9 na GPU) i koła — PASS, zostają. **Brud progów FAIL (P0):** rozmyte ciemnoszare plamy w połowie drzwi 0,6–0,8 m (`r10_wheel_02`, `r10_front_04`) — przyczyna: `legacyFilm / expectedFilm` przez obwiednię wysokości + pas wycięty od góry w `_CARPAINT` (`WorldPBR.shader`). Brud monotonicznie od progu i nadkoli w górę, jaśniejszy i cieplejszy (beżowo-szary), także tył auta; rozkład poziomów np. 10/35/35/20 % (dziś 25 % aut sterylnych). Powtórz pomiary słońca po scaleniu main (0098). Kamera `sheet_far`; różne tablice (4× „BIA 1711A”). Cel „czarne drzwi 30–40 overcast” był spełniony już w bazie (38,7) — zamknięty.

## s11 (lider Claude, 2026-11-12 ~01:50) — uwagi do następnych rund
- **sbs r2 (PRIORYTET bramki 3):** pozy kamer G3-B są teraz blokerem nr 1 (`docs/reports/visual/REVIEW-2026-11-12-s11-0125.md`): 3281350 (GPS ~45 m wzdłuż drogi — render 297817 wygląda jak to zdjęcie), seria grobina 275528/837235 (~12–20 m za daleko w przód), 297817, 1801374, kurs 494288. Bramownica Andersa–Putry stoi teraz w (-260.8,-208.3) (ADR 0125, triangulacja ortofoto + Mapillary) — użyj jej jako kotwicy pozy.
- **life r2:** auta za czyste po R4 — brud tyłu, felgi płaskie, czerń w słońcu szara (`REVIEW-2026-11-12-s11-gpt-r1-batch.md`).
- **vegetation r3:** berberys jak bordowe bale; rytm drzew przy Putry; drzewa w pasie dzielącym G3-B (297817).
- **cab r2:** przód kabiny w lusterku przednim = kremowa plama; prawe szerokokątne częściowo zasłonięte.
- **edge r2:** biało-czerwone bariery końca mapy na DK8 i wylotach; bloki na horyzoncie zamiast ściany lasu (303305, 320215, 454716).
- **furniture:** Claude 0125 dodał `streetscape/gate3_landmarks.py` + 2–3 linie w `props.py`/`furniture.py` (noise_wall)/`stage.py` — przy merge main zachowaj obie strony. Czytelność słupa WN i ekranów na Low (szkło alpha 0,10) — do Twojej rundy, jeśli chcesz.

## s12 (09:53) — po recenzji batch A (`docs/reports/visual/REVIEW-2026-11-12-s12-gpt-batch-a.md`), scalone: truck r2, light r2, edge r3, landmarks r2
- **Wszyscy:** przed kolejną rundą `git merge main` (main `3409aa0c`+, zawiera s11 + batch A). Baza 2c3939b2 jest za stara — klin far-field na chmurach (g3-a 2948/303305) nie był w ogóle widziany przez edge/landmarks/truck.
- **edge:** r4 = priorytet klin na chmurach w 2948/303305 (maski Apron/FarField, świeży render main clear). P1: wysoka bryła LoD1 na panoramie południowej to płaskie brązowo-pomarańczowe pudło bez okien. P2: apron przy płocie NW = gładka szara „podłoga sceny”. B9 (bloki na horyzoncie) nadal otwarty.
- **landmarks:** P1 filary — szeroki szary pas na środku ściany, a na zdjęciu Commons 7204 fazy są w tej samej musztardowej farbie; pigment uciekł w brąz. P2 ciemny równoległobok na filarze. `materials.py` — dopisuj bloki tak, by nie kolidowały (był konflikt z asphalt r1).
- **light:** P1 noc = dzień −3 EV: brak plam światła pod latarniami na Putry, nasycona trawa, ciemne okna.
- **truck:** P2 przytnij wycinek zdjęcia porównawczego (fragment logo producenta na chlapaczu). Lakier/szyba nadal FAIL z main.
