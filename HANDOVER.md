# HANDOVER — kamion, SESJA 11 (start 2026-11-11 23:05)

## Stan na żywo (s11)
- 23:05 start: ops-watchdog uruchomiony w tle przez lidera (log `artifacts/logs/ops-watchdog.log`). Usage: 5 h 0 % (reset 04:00), tydzień 33 %, Fable 62 % (reset 17.11 04:00). Trigger godzinny :17 (CronCreate, tylko w sesji lidera). Właściciel 23:4x: tempo normalne (Fable 62 % tygodniowo na tym koncie); rano zmiana na konto po resecie → wtedy Fable na maksa.
- Agenci Claude (3/3):
| zadanie | ADR | worktree / gałąź | STATUS | stan |
|---|---|---|---|---|
| węzły r6 bariery — dokończenie b3 (Fable) | 0123 | `.claude/worktrees/junctions-r6` / `junctions-r6` | `artifacts/junctions-r6/STATUS.md` | w toku od 23:08 (post.sh b3 full → EditMode/PlayMode → pairs → poprawki → ADR) |
| zabudowa r8 — runda r2 (Fable) | 0124 | `.claude/worktrees/buildings-r8` / `buildings-r8` | `artifacts/buildings-r16/STATUS.md` | w toku od 23:08 (pytest/fidelity → EditMode → r2 → ADR) |
| G3-B bramownice, znaki, ekrany akustyczne, linia WN (Fable) | 0125 | `.claude/worktrees/gate3-signs` / `gate3-signs` | `artifacts/gate3-signs/STATUS.md` | **GOTOWE `56824a54`** (01:40): portal (-260.8,-208.3), A-30, szewron U-4a, tabliczki ronda, ekrany Putry tylko prawa, pełny pas 1,8 m; gis 504/1 (fidelity stale)/1 xfail, EditMode 261/261; D-3/D-6 ronda Bieżeństwa stale (brak wysepki) → krytyk `REVIEW-2026-11-12-s11-0125.md` w toku → scalenie + build_world + import |
| pierzeja handlowa G3-B (Fable) | 0126 | `.claude/worktrees/g3b-frontage` / `g3b-frontage` | `artifacts/g3b-frontage/STATUS.md` | start 01:42 (bloker 6) |
- **Recenzja D51 sbs-r1 (`docs/reports/visual/REVIEW-2026-11-11-s11-sbs-r1-D51.md`): bramka 3 FAIL** — 25 kadrów B Low-overcast: 12 rozpoznawalnych / 11 częściowo / 2 nie; G3-A 11/15 OK warunkowo, G3-B 1/10. Blokery: 1 bramownice G3-B, 2 brak filarów s≈351–359, 3 ekrany akustyczne (strona), 4 słup WN, 5 znaki pionowe, 6 pierzeja handlowa G3-B, 7 pod wiaduktem (bariera łuku, nasyp), 8 drzewa w pasie dzielącym, 9 bloki na horyzoncie. B2+B7 dopisane do 0123; B1,3,4,5 → 0125; B6 → zabudowa po 0124; B8 → GPT vegetation, B9 → GPT edge.
- **23:26 trigger:** 5 h 22 %, tydzień 36 %, Fable 68 %. Watchdog żyje. **GPT sbs r1 SCALONE `7cfd05b6`** (tylko narzędzie/dowody, świat bez zmian; test_sbs_gate3 40/40 na main; sesja GPT ruszyła r2). **GPT edge r1 GOTOWE** (`gpt-edge-r1` 6a06c6c8: kontynuacje jezdni 24→35, apron +792 tris, Low draws +0; EditMode 267/267, GIS 492/1 fail = nieaktualny fidelity_qa) → czeka na visual-critic, gdy zwolni się slot (max 3). Pozostałe GPT w toku.
- **00:26 trigger:** 5 h 49 % (reset 04:00), tydzień 41 %, Fable 77 %. Watchdog żyje. 0123 → b4 (B2 filary już są w gałęzi — recenzja oglądała main; B7 fartuch kostki → asfalt, szyna separatora DK8). 0124 → full_round r2. 0125 → build 2 (portal G3-B przesunięty do (-260.8,-208.3), A-30, tabliczki ronda), import. GPT gotowe: life r1, vegetation r1, cab r1, edge r1 → **jeden krytyk zbiorczy (Opus, tylko odczyt — 4. agent na krótko, świadomie)** → `docs/reports/visual/REVIEW-2026-11-12-s11-gpt-r1-batch.md`. asphalt r1 kończy walidację. Pytanie sesji GPT 10 o podział ról: odpowiedź „kontynuuj life, scala tylko lider Claude”.
- **00:35:** recenzja zbiorcza `REVIEW-2026-11-12-s11-gpt-r1-batch.md`: life r1 SCAL (PARTIAL — auta teraz za czyste), vegetation r1 SCAL (PARTIAL), cab r1 SCAL (lusterka bez wnętrza PASS), edge r1 SCAL warunkowo (+792 tris, ≤2 %). **Wszystkie 4 SCALONE** (`206e22b5` veg, potem life/cab/edge). Brudne pliki main (generated/*.json, artifacts/cab-r1) zbackupowane do scratchpadu i cofnięte. Regeneracja `bash artifacts/integration-s11/regen.sh gpt-r1` → `artifacts/logs/s11-regen-gpt-r1.log` (build_all, build_world, export-route, fidelity, pytest gis+physics+gate3; slot heavy). Uwaga: life i vegetation obie zmieniają WorldPBR.shader → po imporcie kamery kontrolne Low/Medium na wspólnym stanie. Uwagi do GPT (następne rundy): life — brud tyłu, felgi, czerń w słońcu; veg — berberys „bale”, rytm drzew Putry; cab — przód kabiny w lusterku przednim kremowa plama, prawe szerokokątne zasłonięte; edge — bariery końca mapy DK8.
- **01:26 trigger:** 5 h 60 % (reset 04:00), tydzień 43 %, Fable 81 %. Regeneracja lidera (start 00:34) nadal CZEKA na slot heavy (3/3 zajęte przez GPT/agentów). 0125 gotowe do scalenia po pełnym pytest gis (EditMode 261/261, test_gate3_landmarks 12/12; portal G3-B przesunięty, A-30, tabliczki ronda; otwarte D-3/D-6 przy rondzie Bieżeństwa, czytelność ekranów Low). 0123 → b4 build, 0124 → full_round r2. GPT gotowe r1: asphalt, landmarks, light, truck → krytyk zbiorczy batch2 w toku (`REVIEW-2026-11-12-s11-gpt-r1-batch2.md`).
- **01:50:** krytyk 0125 (`REVIEW-2026-11-12-s11-0125.md`): SCAL; G3-B 2/10 rozpoznawalnych (było 1/10). Nowy bloker nr 1 G3-B = pozy kamer SBS (domena GPT sbs; uwagi dopisane do `docs/owner/GPT-FEEDBACK-S10.md`). P1: LOD bramownicy 40–120 m traci kratownicę, słup WN/ekrany słabo widoczne na Low. Scalenie 0125 PO zakończeniu regeneracji gpt-r1 (trwa build_all) — potem jedna regeneracja dla 0125 + batch2 GPT.
- Następne: po krytyku D51 → agenci na blokery (Fable geometria) → krytyk 0123/0124 → scalenie → jedna regeneracja → integracja Unity + czysty APK Low → gate3 A16 A+B.
- Ostatni przydzielony ADR: 0126.

---
# HANDOVER — kamion, ZAMKNIĘCIE sesji 10 (2026-11-11 ~22:50; właściciel zmienia konto → limity od zera)

## Prawda o stanie (czytaj to, niżej jest dziennik s10)
- **main = ten commit, wypchnięty.** Start s11: `docs/owner/START-PROMPT-S11.md`.
- **Bramka 3 — kryterium D51 (właściciel):** rozpoznawalność trasy (układ jezdni, pasy, skrzyżowania, ronda, wiadukty, znaki/bramownice, budynki i obiekty charakterystyczne — „z grubsza podobne” do zdjęć). Niebo/ekspozycja, odcień trawy, tekstury, dziury NIE blokują bramki (dopracujemy później).
- **Scalone w s10 (wszystko po visual-critic, recenzje `docs/reports/visual/REVIEW-2026-11-11-s10-*.md`):** 0086+0101 `_Tint`/kalibracja · 0088 roślinność · 0098 światło · 0097/0107/0114 zabudowa r5–r7 + działki · 0100/0110/0117 węzły r3–r5 + bariery · 0102 meble · 0103 side-by-side (40 par Mapillary) · 0104 kabina/lusterka · 0105 wiadukt pod pomostem · 0085 r2 tło · 0087 TRAKT · 0090 remiza r7 · 0106/0113 wydajność A16 Low · `.venv` odśledzony · fix `build-android.ps1 -Apk` · fix `device-metrics.ps1` (CSV przed screencap) · fix sondy Tint.
- **NIE scalone:** GPT 0089 osobówki (brud progów FAIL → R4 w toku w sesji GPT „life”), GPT 0099 asfalt (cel FAIL → przejęte przez sesję GPT „asphalt”).
- **Telefon A16 Low (ostatni ważny, APK `kamion-0.1.0-21a55c3fe4.apk`, po 0106):** G3-A 29,7 fps p95 33,5 / p99 50 (część to artefakt starego device-metrics — naprawiony później), GPU p95 31,8; G3-B 29,9 fps p99 33,7, GPU p95 33,3; PSS ~830 MB; termika 0. Po 0113 (prewarm, las) agent zmierzył G3-A p99 33,6 bez końcówki. **Ważny pomiar po wszystkich scaleniach jeszcze nie zrobiony.**
- **Decyzje właściciela s10:** D48 tynk remizy 110/126/145 zostaje · D49 A16 = Low dla bramki 3 · D50 bez obniżania skali renderu · D51 bramka 3 = rozpoznawalność.

## Agenci na zamknięciu s10
| zadanie | ADR | worktree / gałąź | STATUS | stan |
|---|---|---|---|---|
| węzły r6 bariery (Fable) | 0123 | `.claude/worktrees/junctions-r6` / `junctions-r6` | `artifacts/junctions-r6/STATUS.md` (RAPORT KOŃCOWY — przerwane) | **PRZERWANE na polecenie właściciela, `13852fdb`**: b3 zbudowany/zaimportowany/wyrenderowany (Low/High × clear/overcast); Low/High draws max +0, tris ≤ +0,7 %. Zrobione: cień poręczy (szachownica), kapa ciemniejsza + bariera bliżej, murek → skarpa, latarnie RING-B przeniesione między pomosty. Częściowo: ocynk (w cieniu za jasny, białe refleksy), filar w r4_pier_bz, ~6 m szyny przed pomostem łącznicy, nos Putry N. Niezweryfikowane: swept path, pełny pytest + EditMode/PlayMode (zmieniony shader/importer/WorldInstances), przegląd 102 kamer, ADR szkic. s11: `bash artifacts/junctions-r6/scripts/post.sh b3 full` (w worktree) → krytyk → scalenie |
| zabudowa r8 działki (Fable) | 0124 | `.claude/worktrees/buildings-r8` / `buildings-r8` | `artifacts/buildings-r16/STATUS.md` (RAPORT KOŃCOWY) | **PRZERWANE limitem po r1, `4147f032`** — budżet lepszy od r7 (Low −12 / najgorsza +3, High −56, cienie −123), 43/43 bram z obniżonym krawężnikiem, kostka nie na jezdni, 0 kolizji płot–schody/garaż, nowy atlas roślin CC0, krawężnik osiedlowy 10 cm, przewody. NIE zrobione: klin trawy na skośnych zjazdach, pomiar zacieków, MirrorCostProfiler (uwaga: `cab-mirror-*` w stats to widok główny, nie RT lusterek), pełny pytest gis + fidelity/run.py + EditMode, kamery r16_door/garden złe. s11: dokończyć r2 (agent Fable z STATUS) → krytyk → scalenie |
| **10 sesji GPT 24 h** (od ~21:25, właściciel) | 0108, 0109, 0118, 0111, 0112, 0115, 0116/0119, 0120, 0121, 0089/0122 | `.claude/worktrees/gpt-<dziedzina>` / `gpt-<dziedzina>-rN` | `artifacts/<dziedzina>-rN/REPORT.md` | pracują; `docs/owner/GPT-TASK-05-24H.md`, uwagi `docs/owner/GPT-FEEDBACK-S10.md` |
Stare worktree GPT z dnia (`gpt-cab-r1`, `gpt-edge-r2`, `gpt-firestation-r7`, `gpt-furniture-r1`, `gpt-light-r12`, `gpt-megascans`, `gpt-sbs-gate3`, `gpt-surface-wear`, `gpt-tint-gamma`, `gpt-truck-paint`, `gpt-vegetation-r2`, `gpt-viaduct-r1`, `gpt-car-paint`) — scalone/zastąpione; usuwać tylko za zgodą właściciela (GPT może z nich korzystać). `argon-edge` zastąpiony przez 0085 r2.

## Ochrona maszyny (WAŻNE — 64 GB RAM, 24 wątki, RTX 5070, ~13 sesji)
- 22:13 kilkanaście równoległych pytest/build_world zawiesiło PC. Od tego czasu:
  - `scripts/unity-slot.ps1 -Acquire|-Release -Owner <x> [-Pool unity|heavy]` — Unity max 4, ciężki Python max 3; respektuje `artifacts/locks/PHONE_RUN`.
  - **`scripts/ops-watchdog.ps1`** — wymusza limit bez współpracy sesji (BelowNormal, 4 rdzenie dla Windows, max 3 ciężkie zadania Pythona: nadmiarowe WSTRZYMUJE i wznawia; < 8 GB RAM → wstrzymuje). Log `artifacts/logs/ops-watchdog.log`. **Ginie z sesją lidera — s11 musi go uruchomić od razu:** `pwsh -NoProfile -File scripts/ops-watchdog.ps1` (w tle). Sesje GPT nie znają `-Pool heavy` (wystartowały wcześniej; właściciel nie może do nich pisać) — watchdog to za nie pilnuje.
  - Właściciel dodał wykluczenie Defendera dla folderu repo.

## Następne kroki (s11)
1. Uruchom `ops-watchdog.ps1` w tle. Ustaw godzinny trigger (CronCreate, minuta nie :00/:30).
2. 0123 i 0124 PRZERWANE (patrz tabela) — dokończ (agent Fable z ich STATUS.md: 0123 weryfikacja b3, 0124 runda r2), potem visual-critic (kryterium D51) → scalenie → JEDNA regeneracja (build_all, build_world, export-route, fidelity/run.py, pytest gis+physics+gate3 z `-Pool heavy`).
3. Co godzinę: rundy GPT (`gpt-<dziedzina>-rN` z REPORT.md) → visual-critic (można łączyć) → scalenie (generated → ours) → regeneracja → uwagi do `GPT-FEEDBACK-S10.md`.
4. **Ścieżka do bramki 3 (D51):** świeży zestaw sbs na aktualnym main (sesja GPT „sbs” r2) → visual-critic z pytaniem „czy kierowca rozpozna to miejsce?” → lista blokerów rozpoznawalności → poprawki (Claude: geometria/obiekty) → integracja Unity (import, Truck/Trailer BuildBatch, InstallBatch, EditMode/PlayMode, czysty APK Low) → gate3 A16 Low A+B z kamerami → pakiet porównań dla właściciela do akceptacji kierunku.
5. Otwarte: wideo migotania lasu (`artifacts/perf-low-r2/shimmer.ps1`), ponowne nagranie PSO po scaleniach, Kwadrat r13 (po zdjęciach bramy), S24+ High (bateria ≥ 40 %).
6. **Ostatni przydzielony ADR: 0124.**

---
# HANDOVER — kamion, sesja 10 (2026-11-11 od ~10:05 lokalnie)

## Najpierw (dla następnej sesji)
- **Tempo (właściciel, s10):** dalej max 3 agentów naraz. Limit tygodniowy Fable zresetował się (0 % o 10:05, reset 15.11); 5 h reset 15:00 lokalnie.
- GPT J 0103 i K 0104 SCALONE (`8b176456`, `1c894f25`); `.venv` odśledzony. Regeneracja HIL zielona (494/1 znane). Integracja s10b na main w toku: `artifacts/integration-s10/run2.log` (czeka na PHONE_RUN agenta 0106; import, truck, EditMode, PlayMode, gis, commit reserializacji, czysty APK Low). Priorytety bramki 3 z side-by-side (top 5): niebo/ekspozycja, trawa/pobocza, asfalt bez zużycia, bariery na pomostach/łącznicach, pod wiaduktem → GPT 0108/0109/0099 i Claude 0110.
- **D51 (właściciel, ~22:40): bramka 3 = rozpoznawalność trasy** (geometria, pasy, skrzyżowania, wiadukty, znaki/bramownice, budynki i obiekty charakterystyczne — „z grubsza podobne”), NIE perfekcja nieba/trawy/tekstur/dziur. Recenzje i priorytety Claude odtąd ważone tym kryterium; sesje GPT light/vegetation/asphalt robią swoje, ale nie blokują bramki.
- **22:13 PRZECIĄŻENIE MASZYNY:** ~13 równoległych pytest/build_world (10 sesji GPT + Claude) → 99 % CPU, zawieszenie. Działa **`scripts/ops-watchdog.ps1`** (uruchomiony przez lidera w tle; log `artifacts/logs/ops-watchdog.log`): priorytet BelowNormal + 4 rdzenie zostawione dla Windows, max 3 ciężkie zadania Pythona naraz — nadmiarowe są WSTRZYMYWANE (nie zabijane) i wznawiane po kolei; przy < 8 GB wolnego RAM wstrzymuje kolejne. **Jeśli sesja lidera padnie, watchdog znika — uruchom ponownie:** `pwsh -NoProfile -File scripts/ops-watchdog.ps1`. Unity ograniczone `scripts/unity-slot.ps1` (max 4). Sesje GPT nie znają `-Pool heavy` (właściciel nie może do nich pisać) — watchdog wymusza limit za nie.
- Trigger 21:21: 5 h 33 %, tydzień 40 %, **Fable 55 %** (3,5 dnia do resetu — przy 2 agentach Fable wystarczy na ok. 1,5 dnia; potem Opus). 0123/0124 na starcie (regeneracja bazy). Regeneracja main 0117+0114 w toku. Sesje GPT 24 h URUCHOMIONE przez właściciela ~21:25 (10 dziedzin, `docs/owner/GPT-TASK-05-24H.md`) — trigger scala ich rundy po REPORT.md (gałęzie `gpt-<dziedzina>-rN`).
- **~21:15:** **0114 SCALONE `3540bbdf`** (recenzja s10-0114: PASS, jakość warunkowa; r8: zjazdy/kostka na jezdni, szwy, schody przed płotem, tuje/jabłonie/kute pręty, ulica bez przewodów, zacieki, koszt działek w lusterkach High). Regeneracja 0117+0114 `artifacts/logs/s10-regen-0117-0114.log`. Start (Fable): **0123 węzły r6** (`junctions-r6`) i **0124 zabudowa r8** (`buildings-r8`) — oba używają `unity-slot.ps1`.
- **~21:00:** **0117 SCALONE `6be0d8f6`** (recenzja s10-0117: PASS warunkowy, bariery pkt 4 bramki NIE zamknięte — r6: szachownica cienia poręczy na kapie Low clear, taśma W za ciemna w słońcu (albedo 0,13 metal 0 → cynk), kapa najjaśniejsza w kadrze, bariera przy filarze wg pomiaru, murek r2_fork_link (3. runda!), samotny słupek p0_kerb_merge, RING-B prześwit 1,31 m — 2 nowe propy na fartuchu wyspy E571 N−716 / E558 N−733). **0114 GOTOWE `2622bda0`** (działki bez instancji, Low najgorsza +11, High +29 / suma +359, cienie +189) → krytyk w toku; po nim scalenie i JEDNA regeneracja dla 0117+0114 (+ fidelity/run.py). Potem węzły r6 (0123, Fable) i A16 na r10_house_1/2, r10_shed_2. GPT 24 h — 10 sesji czeka na start przez właściciela (`docs/owner/GPT-PROMPTS-24H.md`).
- **~20:45:** recenzja GPT 0099 (`REVIEW-2026-11-11-s10-gpt-0099.md`): scalenie PASS warunkowy, cel asfaltu FAIL (kadry trasy bez zmian) — NIE scalone; przejmuje sesja GPT „asphalt” (r1 z tej gałęzi po merge main).
- **20:31 po resecie:** 5 h 2 %, tydzień 34 %, Fable 46 %. Wznowione 0114 i 0117 (przerwane limitem ~19:30). GPT 0099 zużycie nawierzchni gotowe (PARTIAL APPEARANCE) → krytyk w toku. GPT 0089 R4 w toku.
- **Trigger 19:21: limit 5 h 93 %** (reset 20:30 lokalnie), tydzień 33 %, **Fable 43 %** (szybko rośnie — 2 agentów Fable). Bez nowych agentów do resetu. Agenci 0114 (buildings-r7) i 0117 (junctions-r5) dostali polecenie WIP+STATUS; jeśli limit ich przerwie → wznowić po resecie (SendMessage do tego samego agenta albo nowy z ich STATUS.md). Regeneracja 0110 zielona (519/1 znane; 14 błędów swept przejściowe). GPT: 0089 R4 i 0099 w toku, nic do scalenia.
- **19:05:** **0110 SCALONE `60705006`** (recenzja s10-0110: scalenie PASS warunkowy, bramka węzłów FAIL; bariera na pomoście jak biały płotek na Low clear, 1,8 vs 1,25 m od krawędzi; latarnia p0_lamp_putry_eye zniknęła — sprawdzić po regeneracji). Regeneracja `artifacts/logs/s10-regen-0110.log`. **0117 węzły r5 start** (`junctions-r5`, Fable): profil/materiał bariery, odległość od jezdni, braki z recenzji.
- **18:50:** referencje posesji zebrane (`docs/refs/posesje-bialystok.md`, 33 Mapillary + 7 Commons; luki: zjazdy, bramy przesuwne, skrzynki — zdjęcia właściciela nadal mile widziane). **0114 zabudowa r7 start** (`buildings-r7`, Fable): budżet instancji działek ≤ +15 draws, płoty wg typologii, front (furtka/brama/podjazd/zjazd), ogród, zacieki. **0110 GOTOWE `3c97dcf8`** → krytyk w toku (EditMode 7× Tint w gałęzi = stary błąd sondy, na main naprawiony).
- Trigger 18:21: 5 h 48 %, tydzień 25 %, Fable 30 %. Push działa (sieć wróciła ~18:20). 0110 b11 czeka na Unity (GPT_UNITY_HOLD zdjęty) → potem krytyk + scalenie. Nowy: zbieranie referencji posesji (geo-worldgen Sonnet) → `docs/refs/posesje-bialystok.md`, odblokowuje zabudowę r7 (0114). GPT 0099 DRAFT, 0089 R4 w toku.
- **18:10:** run5 gate3 A16 (APK `1b2f2618a4`, po 0087/0090/0107; valid): G3-A 29,68 fps p99 50,0, GPU 30,1/31,8, PSS 849; G3-B 29,75 fps p99 50,0, GPU 29,5/33,8 — kamery 57/57 + 46/46 (`artifacts/gate3/20261111-171555`, `…-175115`); pomiar STARĄ wersją device-metrics (artefakt końcówki). **0113 wydajność r2 SCALONE `33e80073`** (las fast path Low −0,68 ms, prewarm PSO: G3-A >40 ms w pierwszych 5 s 17→3, skok CPU Bieżeństwa znikł; GPU p95 nadal 31,7/32,2 — ≤28 wymaga mniej pikseli = decyzja D50). **Odkrycie 0113: device-metrics.ps1 sam dodawał ~12 klatek >40 ms na końcu każdego pomiaru (screencap/dumpsys przed pobraniem CSV) → naprawione `scripts/device-metrics.ps1` (CSV najpierw).** Dotychczasowe p99 50 ms na G3-A były w dużej części artefaktem pomiaru. Otwarte z 0113: wideo migotania lasu (`artifacts/perf-low-r2/shimmer.ps1`), ponowne nagranie PSO po 0107/0110, Medium/High PSO na S24+. GPT 0089 osobówki: recenzja FAIL (brud progów) — NIE scalone, feedback R4.
- Trigger 17:21: 5 h 39 %, tydzień 24 %, Fable 27 %. Regeneracja EF zielona (gis 476/0). Integracja run5: import/truck OK, EditMode 261/261, PlayMode 110/0/7, APK `kamion-0.1.0-1b2f2618a4.apk`; gate3 A16 A+B z kamerami w toku (`run5.log`). Claude 0110 (b9) i 0113 (raport końcowy w drafcie) w toku. GPT 0089, 0099 — REPORT w trakcie, nie gotowe.
- **17:00:** regeneracja 0107 zielona (gis 471/0). **GPT 0090 remiza r7 SCALONE `b0685f51`** (WorldInstances.cs: unia VegetationCanopyPolicy + heroLeaf; hero leaf też na Ultra), **GPT 0087 TRAKT SCALONE `1d695be1`** (wygląd FAIL wg krytyka). Regeneracja `artifacts/logs/s10-regen-EF.log` w toku. Feedback F r2 (0115), E r8 (0116) w `docs/owner/GPT-FEEDBACK-S10.md`. Po regeneracji: integracja Unity (import + Truck BuildBatch/Install — 0087 zmienia ciężarówkę) + EditMode/PlayMode + APK + zrzuty A16.
- Trigger 16:21: 5 h 29 %, tydzień 22 %, Fable 25 %. Claude: 0110 (Fable) i 0113 w toku (0113 trzyma PHONE_RUN). Regeneracja 0107 w toku. GPT gotowe: 0087 truck-paint (PARTIAL, sami przyznają FAIL wyglądu), 0090 remiza r7 → krytyk w toku. GPT w toku: 0089 car-paint, 0099 surface-wear.
- **15:45 PIERWSZY WAŻNY gate3 A16 Low (APK `kamion-0.1.0-21a55c3fe4.apk`, main po 0106, valid=True):** G3-A 29,72 fps, p95 33,5 / **p99 50,0** (OVER), GPU p50/p95 29,9/31,8, PSS 835; G3-B 29,88 fps, p95 33,5 / p99 33,7 (OK), GPU 29,5/33,3, PSS 826; termika 0. EditMode 248/248, PlayMode 110/0/7. (`artifacts/gate3/20261111-154331`, …)
- 0107 recenzja: scalenie PASS warunkowy (działki +152 draws Low, najgorsza kamera +45 — ADR do poprawy; pomiar A16 na r10_house_2/r10_shed_2), jakość FAIL (siatka świeci, podjazd schodkuje, ogród = łąka, popping 60 m, zacieki P1-f cofnięte). **SCALONE `615d7e6e`** (materials.py — unia z 0102), worktree usunięty, regeneracja `artifacts/logs/s10-regen-0107.log`. G3-B kamery 46/46 valid (`artifacts/gate3/20261111-154538`). **Brak zdjęć polskich posesji w repo — poprosić właściciela o zdjęcia płotów/bram/podjazdów domów jednorodzinnych.**
- **15:20 (po resecie):** wznowione 0107 i 0110. **0106 SCALONE `1791a0ed`** (konflikty QualityProfile: migracje 98 + 106 obie, CurrentRevision 106). Integracja po 0106 + gate3 A16 Low A/B w tle: `artifacts/integration-s10/run4.ps1` → `run4.log` (sam bierze PHONE_RUN). **0113 wydajność r2** start (`perf-low-r2`, rendering-perf Opus). **0107 zabudowa r6 GOTOWE `064ac73a`** (Fable; 97 działek / 4737 instancji, spody balkonów 0,38→0,63, MultiRoof bez szczelin) → visual-critic w toku. Uwaga: w worktree 0107 EditMode 7× Tint — to ten sam błąd sondy, naprawiony na main `276d2205`.
- **14:40 — LIMIT 5 h WYCZERPANY** (reset 15:00 lokalnie). Agenci Fable 0107 (buildings-r6) i 0110 (junctions-r4) przerwani przez limit — praca zapisana w ich worktree (WIP commity + STATUS.md); **wznów ich (SendMessage do tego samego agenta albo nowy agent z ich STATUS.md)** po resecie.
- **Integracja s10b ZIELONA:** EditMode 245/245 (po poprawce sondy `276d2205`), PlayMode 110/0/7, czysty APK Low `artifacts/apk/kamion-0.1.0-276d2205f5.apk` (190,9 MB) — jeszcze NIE na telefonie.
- **0106 wydajność Low GOTOWE** (`perf-low-r1` c528c4ec; NIEscalone, raport w STATUS/ADR 0106): szybka ścieżka szyby kabiny `_KAMION_GLASS_FAST` (−0,9 ms Low, −1,5 ms Medium, obraz identyczny). A16 Low: G3-B p99 50→33,7 ms; G3-A p99 nadal 50 (14/27 pików w pierwszych 5 s — pipeline/zegar GPU; skok CPU t≈55 s); GPU p95 31–34 ms. Medium 21,7 FPS. Koszty GPU: szyba kabiny 3,6–4,3 ms, las HLOD 1,8 + korony 0,9 + impostory 1,6 ms, lusterka ~1 ms, cienie 0,9. Scalić → EditMode/PlayMode → gate3 A16 Low A+B. Konflikty: QualityProfile(.asset)/ProjectSetup migracje (0098 + rev 106 — zachować obie), TruckGlass.shader (0104), WorldInstances.cs.
- **Decyzje D49/D50:** A16 = Low dla bramki 3; bez skali 70 % — najpierw druga runda wydajności (**ADR 0113**: las HLOD jednym przebiegiem, korony Lambert, tańsze impostory, prewarm shaderów, CPU G3-A t≈55 s; weryfikacja wideo z telefonu na migotanie).
- GPT 0087 truck-paint ma REPORT → recenzja + scalenie.
- Trigger 14:21: limit 5 h **84 %** (reset 15:00) → bez nowych agentów do resetu; tydzień 14 %, Fable 12 %. Claude 0106/0107/0110 w toku. GPT: 0087 truck-paint REPORT gotowy (do recenzji), 0089 car-paint REPORT (WIP?), 0090/0099 w toku. Integracja s10b: import/truck OK, PlayMode 110/0/7, **EditMode 238/245 — 7× WorldPbrTintTests GPU: sonda shadera 0086 nie przepisywała include VegetationGround (0088)** → poprawione w `WorldPbrTintProbe.cs` (niezacommitowane do końca run2), potem powtórzyć EditMode.
- Trigger 13:21: limit 5 h 40 % (reset 15:00), tydzień 7 %. Claude: 0101 GOTOWE `e6baa1f7` (critic w toku), 0106 perf w toku (PHONE_RUN jego), critic B+C w toku; regeneracja 0100 — pytest w toku. GPT S10-B gotowe do recenzji: J 0103 sbs (40 kamer, 160 arkuszy), K 0104 kabina/lusterka, H 0085 r2 tło, I 0102 meble, L 0105 wiadukt → kolejność scalania: J (narzędzia) → H → I → L → K, każdy po visual-critic. GPT koord.: 0087 truck-paint, 0089 car-paint, 0090 remiza, 0099 surface-wear w toku.
- Trigger 12:21: limit 5 h 28 %, tydzień 5 %. GPT B 0088 GOTOWE (EditMode 218/218) → scalenie B, potem C 0098 po zakończeniu regeneracji 0097 (w toku); visual-critic B+C gdy zwolni się miejsce. Claude: 0100, 0101, 0106 w toku.
- **A16 gate3 Low (11:25, APK 43bc53a769-dirty → valid=False tylko z powodu „dirty”; liczby orientacyjne):** G3-A 29,7 fps p95 33,5 / p99 50,0 ms (budżet p99 40 — OVER), GPU p50/p95 30,7/32,9 ms, CPU 22,5/29,0 ms, PSS 826 MB; G3-B 29,8 fps p95 33,5 / p99 49,9, GPU 30,0/34,5, CPU 21,6/28,7, PSS 829 MB; termika 0; kamery 57/57 + 46/46 (`artifacts/gate3/20261111-104851`, `…-112456`). GPU bez zapasu → potrzebna runda wydajności Low przed bramką; ważny pomiar = czysty APK po scaleniach. Naprawiono `build-android.ps1 -Apk` (901c427f).
- Trigger 11:21: limit 5 h 20 %, tydzień 4 %. Claude: 0097/0100/0101 w toku (WIP). GPT: C 0098 REPORT „zakończone” (czeka na B wg kolejności), B 0088 REPORT bez EditMode (czeka na zwolnienie PHONE_RUN), nowe sesje S10-B (edge-r2, furniture-r1, sbs-gate3, cab-r1, viaduct-r1) wystartowały. A16 gate3 G3-A Low: 29,7 fps, p95 33,5 / p99 50 ms (OVER), GPU p50 30,7 ms, CPU 22,5 ms, PSS 826 MB — budżet GPU na granicy; G3-B w toku.
- Trigger 10:21: limit 5 h 8 %, tydzień 2 %; 3 agentów w toku, GPT B/C bez REPORT; regeneracja 0086 ZIELONA (gis 370/0), zacommitowana.
- Trigger godzinny w sesji (CronCreate, :17) — ginie z sesją.
- Regeneracja main po 0095: zielona (gis+physics+gate3 413/1 — znana `test_generator_reproduces_committed_scenarios` z 0082) → `48ac6b75`.
- **Scalone w s10:** 0086 `_Tint` gamma (GPT A) `0e73211a` — konflikty generated → --ours; regeneracja (build_all → build_world → export-route → pytest gis) w toku: `artifacts/logs/s10-regen-0086.log`.

| zadanie | ADR | worktree | STATUS | stan |
|---|---|---|---|---|
| recenzja 0095 | — | — | docs/reports/visual/REVIEW-2026-11-11-s10-0095.md | ZROBIONA `503c89ae`: scalenie PASS warunkowy, bramka wizualna węzłów FAIL (połamana P-21, Putry N/MA-010 gołe) |
| węzły r3 | 0100 | .claude/worktrees/junctions-r3 (gałąź junctions-r3) | artifacts/junctions-r3/REPORT.md | SCALONE (REVIEW s10-0100: scalenie PASS warunkowy, bramka węzłów FAIL mniejszy; r4: pole płn. n100, nosy/koryta median, szwy łat, rozdział wsch. geometrią, zatoka zach., bariery E −782; materiały dróg = osobna runda ze zdjęciami); worktree usunięty; regeneracja `artifacts/logs/s10-regen-0100.log`; PO NIEJ: import-region + visual-qa kamery p0_/r2_/r3_ na main (stan po 0088/0098) |
| recenzja B 0088 + C 0098 | — | — | docs/reports/visual/REVIEW-2026-11-11-s10-0088-0098.md | ZROBIONA: zostają na main, jakość FAIL; P0 RCAS-off rozmywa asfalt → GPT `docs/owner/GPT-FEEDBACK-S10.md` (0108 światło r13, 0109 roślinność r3) |
| kalibracja r2 0101 | 0101 | (worktree tint-r2 do usunięcia) | artifacts/tint-r2/REPORT.md | SCALONE `4c63f4c4` |
| GPT H 0085r2 / I 0102 / L 0105 | — | gpt-edge-r2, gpt-furniture-r1, gpt-viaduct-r1 | REVIEW-2026-11-11-s10-gpt-HIL.md (scalenie PASS, jakość FAIL) | SCALONE `4a2eea8c`, `85e19ebf`, `68ca9fd8` (LICENSES/materials.py — unia); regeneracja `artifacts/logs/s10-regen-HIL.log`; po niej sprawdzić roads_qa (4 wpisy mostów) i 806 chronionych elementów (I) |
| węzły r4 + bariery | 0110 | usunięty | artifacts/junctions-r4/REPORT.md | SCALONE `60705006` |
| węzły r5 bariery | 0117 | usunięty | artifacts/junctions-r5/STATUS.md | SCALONE `6be0d8f6` |
| zabudowa r7 | 0114 | usunięty | artifacts/buildings-r15/STATUS.md | SCALONE `3540bbdf` |
| węzły r6 | 0123 | .claude/worktrees/junctions-r6 | artifacts/junctions-r6/STATUS.md | w toku (Fable) |
| zabudowa r8 | 0124 | .claude/worktrees/buildings-r8 | artifacts/buildings-r16/STATUS.md | w toku (Fable) |
| zabudowa r6 + działki | 0107 | usunięty | artifacts/buildings-r14/REPORT.md | SCALONE `615d7e6e`; r7 (ADR 0114) po zdjęciach posesji: siatka, zjazd/podjazd, ogród, LOD działek, zacieki, koszt draws |
| recenzja 0086 | — | — | docs/reports/visual/REVIEW-2026-11-11-s10-0086.md | ZROBIONA: kontrakt OK, kalibracja FAIL (hala kp_wall przepalona, ekrany za ciemne); D48: tynk remizy 110/126/145 zostaje |
| kalibracja r2 | 0101 | .claude/worktrees/tint-r2 (gałąź tint-r2) | artifacts/tint-r2/STATUS.md | w toku (rendering-perf) wg recenzji s10-0086 |
| zabudowa r5 | 0097 | .claude/worktrees/buildings-r5 (gałąź buildings-r5) | artifacts/buildings-r13/REPORT.md | SCALONE (recenzja `REVIEW-2026-11-11-s10-0097.md`: PASS, jakość warunkowa; lista r6 P1-e..h); worktree usunięty; regeneracja `artifacts/logs/s10-regen-0097.log` |
| wydajność Low A16 r1/r2 | 0106/0113 | usunięte | artifacts/perf-low-r1, perf-low-r2 | SCALONE `1791a0ed`, `33e80073` |
| GPT B roślinność r2 | 0088 | gpt-vegetation-r2 | artifacts/vegetation-r2/REPORT.md | SCALONE `6b8f9123` (generated → ours) |
| GPT C światło r12 | 0098 | gpt-light-r12 | artifacts/light-r12/REPORT.md | SCALONE `bfdde95f`; regeneracja B+C ZIELONA (gis 389/0); visual-critic B+C gdy wolne miejsce |
| GPT 0087 lakier TRAKT | 0087 | gpt-truck-paint | — | GPT w toku |
| Argon 0085 | 0085 | argon-edge | artifacts/edge-far-r1 | czeka na poprawkę |

## Następne kroki
1. Integracja na main ZROBIONA (10:30–10:39, main 584f2cd4 + _Generated): import OK (Fab bez fallbacku), Truck/Trailer BuildBatch + InstallBatch OK, EditMode 226/226, PlayMode 110/0/7 skip, APK Low `artifacts/apk/kamion-0.1.0-43bc53a769-dirty.apk` 186,9 MB SHA256 a15d182d8fc3ab038bdf0b69f63dd1b279d3f8b92a05d35514fe5b6e790ee41d („dirty” = reserializacja LP_*.asset przez Unity, cofnięta). Log `artifacts/integration-s10/run.log`. Telefon A16 Low: `artifacts/integration-s10/phone.ps1` → `phone.log` (lock `artifacts/locks/PHONE_RUN`; jeśli sesja padła — usuń lock).
2. Integracja na main z Megascans + 0086 (import-region, Truck BuildBatch/InstallBatch, EditMode/PlayMode, APK Low) → telefon A16 Low gate3.
3. Scalanie GPT B 0088 → C 0098 po REPORT.md; 0097 po REPORT.md.
4. Węzły r3 wg recenzji 0095; Kwadrat r13 po zdjęciach właściciela; raport bramki 3.
5. **GPT pakiet S10-B** `docs/owner/GPT-TASK-03-S10.md` (5 nowych sesji właściciela, po 1 strumieniu): H 0085 r2 tło (gpt-edge-r2 z argon-edge), I 0102 meble uliczne (gpt-furniture-r1), J 0103 side-by-side bramki 3 (gpt-sbs-gate3), K 0104 kabina/lusterka (gpt-cab-r1), L 0105 wiadukt pod pomostem (gpt-viaduct-r1). Scalać po REPORT.md.
6. Następni w kolejce Claude: zabudowa r6 (0107, na Fable — lista r6 z REVIEW s10-0097 + działki domów P1-h), Kwadrat r13.
7. **GPT: 10 długich sesji na 24 h `docs/owner/GPT-TASK-05-24H.md`** (zastępuje 04; dziedziny: light 0108, vegetation 0109, asphalt 0118, sbs 0111, cab 0112, truck 0115, landmarks 0116/0119, furniture 0120, edge 0121, life 0089/0122; gałęzie `gpt-<dziedzina>-rN`, REPORT po każdej rundzie → lider scala co godzinę). **Limit Unity na maszynie: `scripts/unity-slot.ps1` (max 4 naraz, respektuje PHONE_RUN) — agenci Claude też go używają.** (stary opis: pakiet S10-C `docs/owner/GPT-TASK-04-S10.md` (10 strumieni wg priorytetu bramki 3; 0108, 0109, 0118, 0111, 0112, 0119, 0115, 0116, 0120, 0121).
8. Ostatni przydzielony ADR: **0124** (0113 wydajność r2, 0114 zabudowa r7, 0115/0116 GPT) (0107 zabudowa r6, 0108/0109/0111/0112 GPT feedback `docs/owner/GPT-FEEDBACK-S10.md`, 0110 węzły r4).

---
# HANDOVER — kamion, sesja 9 (2026-11-11 00:30 → ~10:30 lokalnie; zamknięta na polecenie właściciela przy końcu limitu 5 h)

## Najpierw (dla sesji 10)
- **Start: `docs/owner/START-PROMPT-S10.md`.** Ta sekcja = prawda o stanie.
- **main = ten commit, wypchnięty.** pytest gis 355/0 po 0096. **Po scaleniu 0095 (`471438fb`) regeneracja main trwała w tle przy zamknięciu s9** — sprawdź `artifacts/logs/s9-main-regen-0095.log` (build_world → export-route → fidelity → pytest gis+physics+gate3; oczekiwane ~356 ✓ gis, 47/1 physics — 1 znana z 0082); przy `PYTEST EXIT` 0 lub tylko ta znana porażka → `git add Data/Regions && git commit`; inaczej zdiagnozuj.
- **Żaden agent Claude nie działa** (wszystkie worktree Claude usunięte). Działają: **GPT 6.1 Sol** (worktree `gpt-s10-coordination`, `gpt-tint-gamma`, `gpt-vegetation-r2`, `gpt-light-r12` — pakiet `docs/owner/GPT-TASK-02-S10.md`; NIE ruszać, scalać po REPORT.md w kolejności A 0086 → B 0088 → C 0098) i ewentualnie Argon (tylko poprawka 0085, `argon-edge`).
- **Limity (08:00):** 5 h — 65 % (reset 09:30 UTC); **tygodniowy Fable 51 %** (reset 17.11) — przy 3 agentach naraz skończy się ok. 12.11. Właściciel zamknął s9 przed decyzją o tempie — **zapytaj go na starcie s10** (max 2 agentów / Sonnet do lżejszych zadań / dalej 3).
- **Megascans (0084) działa na main tylko dzięki lokalnym produktom** (`pwsh scripts/prepare-megascans.ps1` → ignorowane `art-source/world/megascans/_generated`). **Każdy nowy worktree musi mieć te produkty** (robocopy `art-source/world/megascans` z main albo prepare), inaczej po cichu fallback.
- **Determinizm naprawiony (0096):** generator świata daje identyczne hashe niezależnie od PYTHONHASHSEED (stan: 1526 stanowisk / 908 aut). Test `tests/gis/test_determinism.py`.
- **`uv run pytest` bywa zepsuty („trampoline failed”) — używaj `uv run --project tools/worldgen python -m pytest …`.**
- **APK Low `artifacts/apk/kamion-0.1.0-ad4062539c.apk`** (179,5 MB, SHA256 ad514a8bf6e6bfd795a72b2fcf5c645106e21fccc45682814789a7e1faffbf82; z integracji s9, BEZ Megascans, przed 0094/0096) — NIE był jeszcze na telefonie. Telefon tylko gdy żaden Unity nie działa (`artifacts/locks/PHONE_RUN`).
- **Testy fizyki: 7× swept path czerwone = regresja z 0076** (linia trasy ścina narożnik na wyjazdach z rond Bieżeństwa E 559 N −689 i Putry E −535 N 52; prześwit naczepy do −2,94 m) — przekazane agentowi 0095. 1× `test_generator_reproduces_committed_scenarios` znane z 0082 (scenariusz zaostrzony ręcznie, generator nie).
- **GPT/Codex i Argon bezczynni od ~02:00** — wznawia właściciel ręcznie. GPT: Q1 0086 (`_Tint` gamma), Q2 0088 (drzewa Megascans). Argon: najpierw „UWAGI LIDERA s9” do 0085 w `docs/owner/ARGON-TASK-01-WORLD-EDGE.md` (budynek regionu zdublowany halą far-field na `edge-south`; stan Argona zacommitowany przez lidera na `argon-edge` 293c5f69, NIEscalony), potem Q1 0087, Q2 0089.
- **GPT 6.1 Sol — pakiet S10 (2026-11-11):** `docs/owner/GPT-TASK-02-S10.md` — jedna sesja GPT z 3 agentami: A 0086 `_Tint` gamma (`gpt-tint-gamma`), B 0088 roślinność r2 (`gpt-vegetation-r2`), C 0098 światło/post r12 (`gpt-light-r12`); potem D 0099 zużycie nawierzchni (po scaleniu 0095), E 0090 remiza r7 (`gpt-firestation-r7`). Scalanie A → B → C po REPORT.md. 0090 przeszło od Claude do GPT. **Argonowi zostało ~8 % limitu** → robi tylko poprawkę 0085; 0087 i 0089 przeniesione do GPT (strumienie F, G). Właściciel zlecił pakiet GPT (11.11 ~08:40).
- **Prośba do właściciela (otwarta):** zdjęcia bramy Kwadrat Park z ziemi (tablica, czym zamknięte boki, krawężniki, trawnik) — do tego czasu płot/słupki przy bramie = WORKING_VALUE.

## Scalone w s9 (wszystkie z recenzją visual-critic w `docs/reports/visual/REVIEW-2026-11-11-s9*.md`)
0080 światło r11 · 0071 Kwadrat r11 · 0081 zabudowa r2 · 0070 remiza r6 · 0078 auta r10b · 0076 korytarz trasy · 0084 Megascans R1 (GPT) · 0077 wysepki z OSM · 0091 zabudowa r3 · 0092 Kwadrat r12 · 0093 węzły r1 · integracja s9 (dowody) · 0094 zabudowa r4 · 0096 determinizm.
Integracja Unity (worktree, stan po 0093): import OK, Truck/Trailer BuildBatch+InstallBatch OK, EditMode 212/212, PlayMode 109/0/8 skip, rendery 3×59 kamer bez regresji integracji (`artifacts/integration-s9/REPORT.md`). **Na main `_Generated` (Unity) NIE jest zaimportowane po s9** — import-region + BuildBatch do zrobienia.

| zadanie | ADR | worktree | STATUS | stan na koniec s9 |
|---|---|---|---|---|
| węzły r2 | 0095 | usunięty | artifacts/junctions-r2 (ADR 0095 „Otwarte”) | SCALONE `471438fb`: pasy/szerokości Andersa z ortofoto 0,08 m, zatoka s1060, n10015785253, wiadukt DK8 2 pasy + rozdział łącznicy E −782 (miejsce z filmu), rozwidlenie Putry; **swept path naprawiony** (G3-A −0,10/−1,12, G3-B −0,14/−0,14; physics+gate3 47/1 znane z 0082); fidelity krawędź p95 2,52→2,30, wysepki 1→0; gis 356/0 w gałęzi. Ortofoto 0,08 m (2 komórki) skopiowane do `Data/raw/refs/gugik-ortho-hr/bialystok-industrial-c/` + manifest. **visual-critic NIEzrobiony → s10.** Regeneracja main w tle `artifacts/logs/s9-main-regen-0095.log` (gis+physics+gate3). Otwarte: końce zatoki, przejazdy rowerowe n100…, separator rozwidlenia, SE s1440 4 pasy, Putry N, dół MA-010, szew łaty, krawężniki, sprzątanie linii |
| tło za krawędzią | 0085 | argon-edge | artifacts/edge-far-r1/REPORT.md | NIEscalone — czeka na poprawkę Argona |
| import Megascans R1 | 0084 | gpt-megascans | artifacts/megascans-r1 | scalone; worktree zostawiony dla Codex (nie usuwać bez właściciela) |

## Następne kroki (kolejność)
1. 0095 SCALONE — zrób visual-critic na `artifacts/junctions-r2` (renders_b12, plan_after) i sprawdź wynik regeneracji main (`artifacts/logs/s9-main-regen-0095.log`; zacommituj Data/Regions przy PYTEST EXIT 0). Następna runda węzłów (r3) = „Otwarte” w ADR 0095.
2. Integracja na main: build_all → build_world → import-region → `Game.Editor.Setup.TruckAssetBuilder.BuildBatch` (+ naczepa) → `Game.World.Import.WorldTruckInstaller.InstallBatch` → EditMode/PlayMode → czysty APK Low z Megascans.
3. **Telefon A16 Low gate3** (pierwszy pomiar po s9), potem S24+ High (bateria ≥ 40 %, < 36 °C).
4. **0097 zabudowa r5** wg `REVIEW-2026-11-11-s9-0094.md` „Następna runda”.
5. ~~0090 remiza r7~~ → GPT (pakiet S10, strumień E).
6. Kwadrat r13 (krawężnik bramy wspólny z 0095 #6, hierarchia plam/śladów, zużycie słupków) — po zdjęciach właściciela.
7. Raport bramki 3.
8. **Ostatni przydzielony ADR: 0099** (0098, 0099 → GPT).

---
# HANDOVER — kamion, sesja 8 (2026-11-10 ok. 22:00 UTC start; limit 5 h reset 2026-11-11 03:00 UTC)

## Najpierw
- **Polecenie właściciela (s8, ~00:10): następna sesja DOKŁADA PRACĘ GPT i Argonowi** — dopisując kolejne zadania na końcu ich plików w sekcji „KOLEJKA” (`docs/owner/GPT-TASK-01-MEGASCANS.md`, `docs/owner/ARGON-TASK-01-WORLD-EDGE.md`), z numerem ADR z góry, gałęzią, worktree i STATUS. Zawsze trzymaj w kolejce każdego co najmniej 1–2 niezrobione zadania. Obecnie: GPT Q1 = ADR 0086 (`_Tint` gamma globalnie), Q2 = ADR 0088 (Megascans r2 drzewa); Argon Q1 = ADR 0087 (lakier/szyba/reflektory ciągnika). Scalaj ich gałęzie po REPORT.md jak każdego agenta.
- **Polecenie właściciela (s8, ~23:55 UTC): lider s8 NIE wznawia agentów po ich zakończeniu — pracę przejmuje sesja 9 wg `docs/owner/START-PROMPT-S9.md`: max 3 agentów naraz + zewnętrzny trigger co godzinę wybudzający sesję.** Agenci, którzy skończyli, zostają z raportem w STATUS.md swojego worktree.
- **Limit 5 h na 83 % o ~23:50 UTC** (reset 03:00 UTC) — od teraz bez nowych agentów, dopóki działa ≥ 2.
- main = ten commit. Start s8: 8 agentów Fable przejmuje/uruchomionych (tabela). GPT/Codex pracuje nad importem Megascans (ADR 0084, `gpt-megascans`, STATUS `artifacts/megascans-r1/STATUS.md`) — nie ruszać, scalić po REPORT.md. Antigravity (Argon 4) — zadanie `docs/owner/ARGON-TASK-01-WORLD-EDGE.md` (tło za krawędzią świata, ADR 0085, gałąź `argon-edge`).
- Decyzja właściciela D47: firanka bez pasa (B), osłony boczne zostają (ADR 0083).
- Decyzja właściciela D46: ogranicznik na zjeździe dopuszcza ~94 km/h (`overrunBrakeOffsetKmh = 4` zostaje, ADR 0082).
- Decyzja lidera s8 (0076): ratchety fidelity — abreast oceniane na ortofoto; jeśli bliżej rzeczywistości, osobna metryka i nowy baseline z uzasadnieniem w ADR 0076; inaczej abreast ograniczony do osi p95 ≤ 0,13 m.

| zadanie | ADR | worktree (`.claude/worktrees/`) | STATUS | stan |
|---|---|---|---|---|
| P0 korytarz + ratchety | 0076 | agent-ad6af5501cb259d76 | artifacts/roads-p0-r10 | s8: agent Fable w toku |
| wysepki z OSM | 0077 | agent-a2afb96d89584cca6 | tools/worldgen/fidelity/STATUS_islands_r10.md | s8: agent Fable w toku (merge main po 0076) |
| straż JRG2 | 0070 | agent-aa9c74c62497e5d1f | artifacts/firestation-r9 | GOTOWE do scalenia `ff40d3e` (r6: tynk P0 spełniony 103/119/135, okna z ramami, tuje/świerki; LOD 9944/2828/164). Przed scaleniem: pełny pytest gis + EditMode (nie powtórzone po r6), ponowny visual-critic `unity/r6/view`. Otwarte: 2 świerki na kostce (`dims.json` spruce.items), pokrój stożek |
| osobówki r10 | 0078 | agent-a2215bcc98d109edc | artifacts/cars-r10 | s8: GOTOWE do scalenia `032af23` (mora usunięta, lakier jaśniejszy; bok czarnego auta nadal ciemniejszy od opony; Low +0,69 %) — recenzja visual-critic m3 do zrobienia |
| zabudowa r10 | 0081 | agent-ac404823e7d8b56e7 | artifacts/buildings-r10 | s8: GOTOWE do scalenia `70ef3ba` (r2, facade_atlas High 17,4 MB). Znalezisko: `_Tint` (Color) linearyzowany 2× we WSZYSTKICH zestawach World PBR — poprawione tylko dla budynków (`tint_linear`); globalnie → osobne zadanie ADR 0086 po scaleniach |
| zewnętrze TRAKT + naczepa | 0083 | agent-a4049e15e1ab8c681 | artifacts/truck-ext-r10 | SCALONE `68e5335` (r8, wariant B, dach < 90 % luminancji). Na main wymagane TruckAssetBuilder.BuildBatch + WorldTruckInstaller.InstallBatch. Otwarte → nowe zadanie: lakier kabiny, szyba czołowa, reflektory w dzień (TruckExterior.shader/TruckLights.cs). Worktree do usunięcia |
| Kwadrat Park r11 (recenzja) | 0071 | kwadrat-r11 | artifacts/kwadrat-r11 | GOTOWE do scalenia `bd28b1e`: kostka P0 = błąd GLOBALNY (importer nie zapisywał `_Tile`, kostka 2,08× za duża; zmienia też chodniki/parkingi wszędzie), zużycie placu, zacieki hali, naczepy, wyspa szlabanu; Low +0,7 % draws. Po scaleniu na main KONIECZNE `build_all.py` (PNG na main stare) → build_world → import-region. Decyzja lidera: `_Tile` 4 m dla zestawów bez `elements_per_tile` |
| światło r11 (recenzja) | 0080 | light-r11 | artifacts/light-r11 | GOTOWE do scalenia `195eb5a` (niebo 6800 K, korony, mgiełka 2,4/40 m, szyba); zmienia WorldCarGlass.shader (możliwy konflikt z 0078). A/B telefon: komendy w STATUS |
| import Megascans | 0084 | gpt-megascans | artifacts/megascans-r1 | GPT/Codex w toku — runda 3 (r1 sam ocenił FAIL: krawężnik bez brudu, Low +19 draw/+4k tris; poprawia) |
| tło za krawędzią | 0085 | argon-edge | artifacts/edge-far-r1 | Antigravity w toku — r0-before gotowe, generator far_field.py; zmienia WorldSurface.shader + streetscape/materials.py (konflikt z 0081 `tint_linear` → unia ręcznie) |

## Następne kroki
1. Scalanie: 0076 → 0077 → 0070 → 0078 → 0081 → 0083 → Kwadrat r11 → światło r11 → 0084 → 0085; po drogach: build_world → pytest gis → import-region → PlayMode WorldCBarrier|DepotBarrier|WorldCRoute.
2. Sprzątanie ZROBIONE: worktree 0071/0080/0082 usunięte (artifacts skopiowane), 7 osieroconych katalogów usuniętych (junctiony odpięte, artifacts → artifacts/orphans/), nagranie → artifacts/owner/.
3. Integracja, czyste buildy Low/High/Ultra, telefony, raport bramki 3.
4. Ostatni przydzielony ADR: **0088** (0086 = `_Tint` gamma → GPT Q1; 0087 = lakier/szyba/reflektory TRAKT → Argon Q1; 0088 = Megascans r2 drzewa → GPT Q2).

---
# HANDOVER — kamion, sesja 7 (2026-11-10 ok. 23:00; LIMIT WYCZERPANY ok. 23:10; wszyscy agenci (0070, 0076, 0077, 0078, 0081, 0082, 0083) zapisali WIP i są zatrzymani; agenci dostali polecenie: commit WIP + STATUS.md i stop; nowa sesja startuje z docs/owner/START-PROMPT-S8.md)

## Najpierw
- **main wypchnięty (ten commit).** Scalone w s7: **0082 ogranicznik/krawędź świata** `65e24d9`, **0080 oświetlenie** `5439ddf` (wariant 3 overcast wybrany przez właściciela: lookToe 0,9/0,4/0,6 + EV −0,2, kompensacja kabiny `rq_cabtoe`), **0071 Kwadrat Park** `c132f56` (szlaban działa i ma kolizję — test WorldCBarrierTests; plac bez osobówek, naczepy przy dokach). Main NIE zregenerowany po scaleniach (czeka na 0076: P0 korytarza s1432–1480 nadal czerwony na main).
- **Fab Megascans (D45): 19/19 pobrane** (EULA zaakceptowana na koncie Epic właściciela za jego zgodą) → `Data/raw/fab/<id>/*.zip` (poza gitem, ok. 1,7 GB), manifest SHA256 `Data/SourceManifests/fab-megascans-2026-11-10.json`, tabela w `docs/LICENSES.md`, test `tests/gis/test_fab_not_tracked.py`. Jakość: 3D/rośliny `_high` FBX, dekale/kora `4k`, Urban Trash `mid`. **Jeszcze nieużyte** — następny agent: import do generatorów (krawężniki, studzienki, kosze, trawa, krzewy, kora, kamienie), wyniki w `_Generated`, nic do gita.
- **Zdjęcia właściciela:** 10 własnych z centrum → `Data/photos/owner-2026-11-10-centrum/` (poza gitem; osoby/dzieci w kadrze — tylko referencja), wpis w `docs/REFERENCES.md`. ~25 zdjęć z internetu wklejonych w czacie — tylko opis `docs/refs/owner-aerials-2026-11-10.md` (Putry: latarnie na krawędziach/pasie dzielącym; P-21 przed nosem wyspy; S8/DK8).
- **Recenzja visual-critic** (`docs/reports/visual/REVIEW-2026-11-10-0071-0080.md`): 0071 **FAIL jakości** (bez regresji blokującej) — P0: kostka placu ~0,4–0,5 m zamiast ~0,2 m (sprawdzić, czy to 0071 czy materiał globalny; inna skala w renderach 0080), plac bez zużycia/łat/śladów, elewacja hali bez zacieków/AO; P1: naczepy-pudełka, brak cieni kontaktowych, szlaban bez wyspy/krawężnika, paleta zbyt jednolita. 0080 **PASS warunkowy** — P1: asfalt overcast o 25–50 poziomów za ciemny vs zdjęcia, ciemne auta i korony drzew w czerni (brak odbić nieba, mgiełka 100–500 m), niebo neutralne zamiast chłodnego, smuga/prążki na szybie kabiny w clear. Wymagane: render stanu połączonego z main (hala pod wariantem 3) i zrzuty z telefonu. → przydzielić w s8 (agent Kwadrat r11 + agent światło r11).

| zadanie | ADR | worktree (`.claude/worktrees/`), gałąź `worktree-<id>` | STATUS | stan |
|---|---|---|---|---|
| P0 korytarz trasy + MA-001/002/012 + latarnia/krawężnik z filmu | 0076 | agent-ad6af5501cb259d76 | artifacts/roads-p0-r10 | STOP na 95 %, `fcd74f9`, NIEscalone: korytarz 4790 stacji 0 uskoków/0 przeszkód, krawężniki w poprzek 29→0, latarnie na jezdni 2→0 (Putry OK), spójność 103→69. pytest gis 203/5 czerwone: ratchety fidelity (oś p95 1,745 m vs baseline 0,032 — skutek łącznic „abreast”; krawędzie 2,57; wysepki 7>4) = DECYZJA lidera/właściciela, `test_terrain_walls` szczelina przy j:n10015785253 (E −239 N −236) do naprawy. Brak ADR 0076. |
| wysepki z OSM, MA-010, krawędzie | 0077 | agent-a2afb96d89584cca6 | artifacts/islands-r10 | STOP, `5cba6a3`, NIEscalone: `roads/gores.py` + 8 override paved_gore (P-21), MA-010 = przesunięta oś OSM (center_offset +2,9 m), 7 odcinków center_offset; fidelity: krawędź p50 0,76→0,46, p95 2,52 (cel 0,75 ✗), wysepki bez pokrycia 4→3. Brak: regeneracja, pytest, import Unity, ADR 0077 wynik. BASELINE w test_road_fidelity.py nieaktualny (sprzed 0074). Komendy: `tools/worldgen/fidelity/STATUS_islands_r10.md`. Konflikty z 0076: network.py/pipeline.py/overrides.yaml (różne funkcje), generated → regen. |
| straż JRG2 r4 | 0070 | agent-aa9c74c62497e5d1f | artifacts/firestation-r9 | STOP, `31976e3`, NIEscalone (merge main OK). LOD 8864/2720/164. Runda r4b zakończona (ROUND_DONE), efekty uboczne Unity cofnięte; obejrzeć r4b (kolor prętów płotu), uzupełnić ADR 0070. Następny krok w STATUS.md. |
| osobówki r10 | 0078 | agent-a2215bcc98d109edc | artifacts/cars-r10 | STOP, `f1c73fc`, NIEscalone: film drogowy, lampy/szwy na poszyciu, drzwi vs nadkole, poprawka mory płatka (NIEobejrzana). LOD0 3936–4158 (limit testu podniesiony do 4200 — do akceptacji), 0/81 dziur. W tle mógł zostać Unity High (`unity_after2.log`) — potem `git checkout -- M_Sky.mat QualitySettings.asset`. WorldPBR.shader: bloki `_CARPAINT` rozdzielne od 0080. |
| zabudowa r10 | 0081 | agent-ac404823e7d8b56e7 | artifacts/buildings-r10 | STOP, `c953bc7`, NIEscalone (runda r1 zakończona, rendery w worktree `artifacts/buildings-r10/r1/*/960/`): facade_atlas LOD0/LOD1 spójne, typologia biur/bloków, balkony/klimatyzatory, płot betonowy (558 m). Low tris maks. +0,07 %, nowy koszt tekstur facade_atlas 39,8/7,8/1,4 MB (High/Med/Low). Rendery r1 NIEobejrzane. Czerwony przez niego: test_cc0_scans (przebudować `build_all.py --only fence_concrete`). ~60 niezacommitowanych plików regeneracji = szum. Komendy: `tools/worldgen/streetscape/STATUS-buildings-r10.md`. |
| ogranicznik 90, koniec świata, kamera, rondo | 0082 | agent-acc0299ca0b0081b1 | artifacts/drive-fold-r10 | SCALONE 65e24d9 — po scaleniu na main wymagany import-region (zapory przy imporcie) + `test.ps1 -Platform PlayMode -Filter WorldEdgeRecoveryTests`; asfalt 89,4 km/h, zjazd 5 % 40 t ustala się na 94 (retarder od 94, `overrunBrakeOffsetKmh=4` WORKING_VALUE — decyzja właściciela); +4 km/h z filmu UNVERIFIED (potrzebna telemetria „Nagraj”); teren za krawędzią pusty (las/zabudowa do zrobienia) |
| zewnętrze TRAKT + naczepa r10 (start s7) | 0083 | agent-a4049e15e1ab8c681 | artifacts/truck-ext-r10 | STOP na 95 %, `672893a`, NIEscalone: osłony boczne, owiewki, lampy tylne, wyposażenie pod naczepą, pas na firance (LOD0 104,5k/89k, w budżecie). Otwarte: r4 nieobejrzane (dach naczepy albedo 0,36), Low lowsun exit 1, EditMode nieuruchomione, ADR 0083 szkic; decyzja właściciela: pas na firance + osłony boczne. Następny krok w STATUS.md. |
| oświetlenie r10 | 0080 | agent-ac7c9571184d27443 | STATUS.md | SCALONE (worktree do usunięcia) |
| Kwadrat Park r10 | 0071 | agent-a1409e374f8c12b4f | artifacts/kwadrat-r9 | SCALONE (worktree do usunięcia) |

Prompt startowy następnej sesji: `docs/owner/START-PROMPT-S8.md`. Przejęcie po ubiciu: jak w s6 — nowy agent Fable z briefem „pracuj WYŁĄCZNIE w <wt>, najpierw docs/owner/AGENT-RULES.md i STATUS.md, dokończ”.

## Następne kroki
1. Scalać w miarę kończenia: 0076 → 0077 → 0070 → 0078 → 0081 → 0082 → 0083. Po 0076: na main build_world → pytest gis → import-region → `pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCBarrierTests|DepotBarrierTests"`.
2. Telefon: A/B oświetlenia na Samsungu A (`-e rq_clouds -1 -e rq_haze 0 -e rq_look 0 -e rq_cabtoe 0`), tylko gdy żaden Unity nie działa.
3. Agent importu Megascans (po resecie limitu). Usunąć worktree 0080/0071 (kopia artifacts, junctiony).
4. Ostatni przydzielony ADR: **0084** (0084 = import Megascans, zlecony agentowi GPT/Codex: `docs/owner/GPT-TASK-01-MEGASCANS.md`, gałąź `gpt-megascans`, worktree `.claude/worktrees/gpt-megascans`, STATUS `artifacts/megascans-r1/STATUS.md`).

---
# HANDOVER — kamion, sesja 6 (2026-11-10 ok. 21:45 czasu właściciela; lider zapisuje po każdym scaleniu/starcie/końcu agenta)

## Najpierw
- **main = `ba74b1e`, wypchnięty.** Scalone w s6: HUD 0079, refs 0066, auta r9 (ADR 0073, generated = ours → wymagana regeneracja), fidelity dróg (ADR 0075). Main NIE zregenerowany po scaleniach; pytest gis na main: 2 czerwone P0 korytarza (agent 0076).
- Polecenie właściciela s6: **max 10 agentów, wszystkie Fable 5.2**, mocny skok jakości wyglądu. Limit 5 h: reset 01:20 (start s6 0 %).
- Zgłoszenia właściciela s6: (1) HUD na Fold 8 Ultra (ekran ~1:1) rozjechany, ustawienia ucięte → ADR 0079; (2) film jazdy `Screen_Recording_20261110_210126_Kamion.mp4` (127 s, klatki `artifacts/owner/fold-video-2026-11-10/`): brak ogranicznika (95–105 km/h), koniec świata ~116 s — biała pustka, spadek do 179 km/h, kamera w desce; przejazd po wyspie ronda Bieżeństwa ~30 s → ADR 0082.
- Przejęcie po ubiciu sesji: worktree w `.claude/worktrees/<id>`, STATUS.md w `<wt>/artifacts/<dir>/` (dir z kolumny dowody); nowy agent Fable z briefem „pracuj WYŁĄCZNIE w <wt>, najpierw docs/owner/AGENT-RULES.md i STATUS.md, dokończ”. Agenci commitują WIP co krok (przypomnienie wysłane 22:xx).
- Nowe worktree agentów: Data/raw/derived ma być KOPIĄ (robocopy), nie junction — inaczej build_world nadpisuje main.
- Ostatni przydzielony ADR: **0083**. D45 Fab (Megascans + CC BY, pliki poza gitem) — przyjęta; właściciel pobiera na koncie Epic do 12.11. 0066 scalone; pusty katalog worktree agent-ab1fb0a47d2f0a491 (kopie Data/raw) do ręcznego usunięcia.
- Dodatkowe zgłoszenia właściciela s6 przekazane: latarnia na lewym pasie estakady (~93–100 s) i krawężnik w poprzek jezdni (~105–112 s) → 0076; szlaban Kwadrat Park nie otwiera się, brak kolizji → 0071.

| zadanie | model | ADR | worktree / gałąź | dowody | stan |
|---|---|---|---|---|---|
| P0 korytarz trasy s1432–1480 + MA-001/002/012 | Fable | 0076 | agent-ad6af5501cb259d76 / worktree-agent-ad6af5501cb259d76 | artifacts/roads-p0-r10 | w toku |
| wysepki z OSM (compute_corners), MA-010, krawędzie p95 | Fable | 0077 | agent-a2afb96d89584cca6 / worktree-agent-a2afb96d89584cca6 | artifacts/islands-r10 | w toku |
| straż JRG2 dokończenie + merge main | Fable | 0070 | agent-aa9c74c62497e5d1f | artifacts/firestation-r9 | w toku |
| Kwadrat Park dokończenie + brama/naczepy | Fable | 0071 | agent-a1409e374f8c12b4f | artifacts/kwadrat-r9 | w toku |
| HUD adaptacyjny (Fold, 1:1–21:9) | Fable | 0079 | usunięty | artifacts/hud-r10 | SCALONE (test na telefonie UNVERIFIED; dev pod przyciskiem „Panel”) |
| auta r10 (lampy, płatek, LOD2) | Fable | 0078 | agent-a2215bcc98d109edc / worktree-agent-a2215bcc98d109edc | artifacts/cars-r10 | w toku |
| oświetlenie/atmosfera r10 + warianty ekspozycji ov | Fable | 0080 | agent-ac7c9571184d27443 / worktree-agent-ac7c9571184d27443 | artifacts/light-r10 | w toku |
| zabudowa typologia r10 | Fable | 0081 | agent-ac404823e7d8b56e7 / worktree-agent-ac404823e7d8b56e7 | artifacts/buildings-r10 | w toku |
| licencja Fab/Patch + refs 0066 | Fable | 0066 | usunięty | docs/reports/FAB-PATCH-LICENSE-2026-11-10.md | SCALONE |
| zewnętrze TRAKT + naczepa r10 | Fable | 0083 | agent-a895ad2cc01f155bd / worktree-agent-a895ad2cc01f155bd | artifacts/truck-ext-r10 | w toku |
| ogranicznik 90, koniec świata, kamera, rondo (film Fold) | Fable | 0082 | agent-acc0299ca0b0081b1 / worktree-agent-acc0299ca0b0081b1 | artifacts/drive-fold-r10 | w toku |

## Następne kroki
1. Scalać po kolei w miarę kończenia: 0076 → 0077 → 0070/0071 → 0078 → 0081 → 0080 → 0079/0082 → 0066. Po każdym: regeneracja świata na main, pytest gis.
2. Pełna integracja + czyste buildy Low/High/Ultra, telefony (A16 Low gate3, S24+ High A/B) — tylko gdy żaden Unity nie działa.
3. Decyzje klikalne: Fab/Patch (D40), ekspozycja ov (warianty z 0080), D23 vs dach N-17, wynik audytu mapy. Recenzja r9/r10, raport bramki 3.

---
# HANDOVER — kamion, sesja 5 (aktualizacja 2026-11-10 ok. 22:10; lider zapisuje ten plik po każdym scaleniu/starcie agenta)

## Najpierw (sesja 5 → następna)
- **P0 po scaleniach (regeneracja main 22:15, log `artifacts/logs/s5-main-regen.log`): pytest gis 192/195.** `test_route_corridor_is_clear` — 64 stacje trasy zablokowane przy s≈1432–1480 (chunk_2_4: collision_asphalt/curb 0,4–0,5 m nad profilem, E −345 N −131) i `test_route_profile_has_no_steps` — 9 uskoków do 0,53 m tamże: ciężarówka uderzy w krawężnik. Podejrzenie: połączenie 0074 (`network.align_forks`, nos pasa dzielącego) z 0067/0069 — bisect po merge'ach `cf0c625`/`a94940a`/`ef2e870`. Trzeci (CC0 spec) naprawiony. Wyniki regeneracji w `git stash@{0}` (main czysty). Potem dopiero import-region i APK.
- **Przejęcie agentów zabitych limitem (właściciel: przejmie je inna sesja na innym koncie):** worktree zostają na dysku. Dla każdego wiersza „w toku”: (1) `git -C .claude/worktrees/<id> status` — niezacommitowane zmiany obejrzyj i zacommituj jako `wip(...)`, (2) przeczytaj `<wt>/artifacts/<dir>/STATUS.md` (ostatni wpis = NASTĘPNY KROK jako komenda), (3) sprawdź, czy nie wisi Unity/Blender/python tego worktree (`tasklist`), (4) uruchom nowego agenta (ten sam model co w tabeli) z briefem: „pracuj WYŁĄCZNIE w istniejącym worktree <ścieżka>, najpierw docs/owner/AGENT-RULES.md i STATUS.md, dokończ”. Pamięć Claude z innego konta może się nie załadować — przeczytaj ręcznie `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md` i pliki.
- **Prompt startowy następnej sesji:** `docs/owner/START-PROMPT-S6.md`.
- **main = `cf0c625`, wypchnięty.** Limit 5 h: WYCZERPANY ok. 22:30 (reset 01:10) — przy 95 % nie startujemy agentów (reset 01:10) — od 85 % max 2 agentów naraz. Scalone w sesji 5: świat r8 ADR 0060 (p10 ov 32–34, cel ≤ 28 NIE — potrzebna decyzja właściciela o ekspozycji ov), skany CC0 ADR 0063. Przód 0061 i źródła 0066 (WIP) scalone wcześniej.
- **Zgłoszenie właściciela:** pas ze strzałką wjeżdża w wysepkę z trawą (`artifacts/owner/bugs/2026-11-10-lane-into-island.webp`) + wymaganie: „drogi dosłownie jak w OSM, żeby mieszkaniec wiedział jak jechać” → agenci 0074/0075/audyt.
- Zasady dla agentów: `artifacts/handover/AGENT-RULES-S5.md`. Ostatni przydzielony ADR: **0075**.
- Przy przejęciu worktree: `git -C <wt> log main..HEAD`, STATUS.md (ścieżka poniżej), dokończ albo scal. Przed usunięciem: skopiuj `<wt>/artifacts`, `cmd /c rmdir` junctiony `<wt>/Data/raw/*`, `git worktree unlock`, `git worktree remove --force --force`, sprawdź `du -sh Data/raw/*` w main.

| zadanie | model | ADR | worktree `.claude/worktrees/` | gałąź | STATUS / dowody | stan |
|---|---|---|---|---|---|---|
| otwarte źródła + Kwadrat Park/straż | Sonnet | 0066 | agent-ab1fb0a47d2f0a491 | worktree-agent-ab1fb0a47d2f0a491 | artifacts/refs-opensources, artifacts/refs/{kwadrat-park,fire-station} | w toku |
| straż pożarna hero (ref. `Data/photos/nowe/7197_May_2021_in_Białystok.jpg`) | Fable | 0070 | agent-aa9c74c62497e5d1f | worktree-agent-aa9c74c62497e5d1f | artifacts/firestation-r9 | GOTOWE częściowo 183e56b, NIEscalone: JRG 2 Andersa 46 (OSM 211035271), override `kind: hero_building`, LOD 8,2k/3,0k/164; otwarte: dach w Unity za jasny, okna szczytu płaskie, visual-critic. Scalanie: w worktree `git merge main` (konflikty build_all.py, materials.py, InstanceImporter.cs, build_world.py; `viaduct_concrete` oznaczyć `atlas`), potem `pwsh artifacts/firestation-r9/scripts/unity_round.ps1 -Tag r3` |
| Kwadrat Park hero | Fable | 0071 | agent-a1409e374f8c12b4f | worktree-agent-a1409e374f8c12b4f | artifacts/kwadrat-r9 | GOTOWE częściowo d19f8a9, NIEscalone: hala jako hero (`kind: hero_depot`, LOD 13,6k/2,0k/0,65k, 11 doków jak dotąd); otwarte: brama/portiernia/ogrodzenie/oznakowanie placu generyczne, brak naczep przy dokach (zbadać), visual-critic; scalanie: konflikty addytywne (InstanceImporter.cs, build_world.py, materials.py, overrides.yaml, test_streetscape.py) — wspólny mechanizm landmarków z 0067/0070 ujednolicić; potem `pwsh artifacts/kwadrat-r9/cycle.ps1 -Phase merged`; w worktree `git lfs checkout` |
| auta r9 sylwetki | Fable | 0073 | agent-adeef0c396335e1ed | worktree-agent-adeef0c396335e1ed | artifacts/cars-r9 | GOTOWE 01af90f, NIEscalone: nowe bryły 5 typów (LOD0 3,2–3,5k), 0/81 dziur, budżet OK, lakier rough→gładkość w WorldPbrMaterials.cs; otwarte: lampy/grill płaskie, LOD2 pudełko, brak płatka metalicznego; po scaleniu build_world + import-region |
| zgodność dróg z OSM/ortofoto | Opus | 0075 | agent-aee7234325983b8dc | fidelity-r9 | artifacts/fidelity-r9/DIFFS.md | GOTOWE 17262e8, NIEscalone (czeka na koniec regeneracji main): oś p95 0,03 m ✓, pasy 25/25 ✓, krawędzie p95 2,04 m ✗ (cel 0,75), 4 fałszywe wysepki ✗ + 18 brakujących; przyczyna: `junctions.compute_corners` stawia wysepkę na zbiegu osi OSM; scalić `git merge fidelity-r9`, test unieważnia się po zmianie roads/*.py → po każdej poprawce `tools/worldgen/fidelity/run.py` |
| SCALONE w s5: 0060 świat, 0063 CC0, audyt mapy, 0072 toe Low, 0069 ulica r9e, 0067 wiadukt, 0074 spójność dróg | | | usunięte | | artifacts/{world-r8,cc0-r8,map-audit-r9,truckshade-r9,street-r9,viaduct-r9,roadgeo-r9} | |

**Otwarte po scaleniach:** mapa — MA-001/002 (krawężnik w poprzek łącznicy do Andersa), MA-010 (wysepka pod wiaduktem Putry; kontrola 0074 jej NIE łapie), MA-011/012/015, 2 przypadki na trasie (brama Kwadrat j:n1882954015, droga straży j:n4103450295); MA-005 częściowo. Miejsce ze zrzutu właściciela = wyjazd straży pożarnej na Andersa (s≈1330), naprawione w generatorze (0074). Wiadukt: prześwit 3,3–5,0 m vs ok. 6 m na zdjęciu (niweleta). `_Tile` w WorldPbrMaterials naprawione tylko dla `set_tile` — decyzja o globalnej naprawie. Pierścień Bieżeństwa = `gravel` (0067) zamiast `stones` (0060). Zebra N-21 i linia postojowa 1,35 — decyzja §9-3 / ciemniejsza kostka.
**UWAGA: agenci przez junction `Data/raw` nadpisują `Data/raw/derived/bialystok-industrial-c/world/*` w main swoim build_world** — po zakończeniu WSZYSTKICH agentów powtórz build_world na main przed import-region. `_Tile` w WorldPbrMaterials: 0067 naprawił dla `set_tile`, 0070 dla `atlas` — ujednolicić i zdecydować o naprawie globalnej (zmienia wygląd całego świata, osobny przegląd). **Regeneracja świata na main uruchomiona** (log `artifacts/logs/s5-main-regen.log`: cc0_fetch → build_region → build_world → pytest; koniec = `EXIT n`). Jeśli nie ma EXIT 0 — powtórz. Potem import-region + Unity (punkt 2 niżej).

## Następne kroki
0. **Źródła assetów do sprawdzenia: `docs/ASSET-SOURCES-CANDIDATES.md` (Fab, Patch, Sand3D, YuE).** Fab (fab.com) — decyzja właściciela: najpierw sprawdzić licencję; Patch (patch.gg) sprawdzić tym samym agentem (agent Sonnet, bez logowania i pobierania): Fab Standard License + Megascans + CC BY na Fab — użycie w Unity, gra komercyjna Android, publiczne repo (pliki źródłowe poza gitem?), atrybucja; lista przydatnych darmowych pozycji (sosny, lipy, krzewy, trawa, kamienie, krawężniki, śmieci). Wynik → pytanie klikalne do właściciela o rozszerzenie D40. YuE: notatka w docs/08 (po bramce 3).
1. Scalanie pozostałych: 0073 → 0075 → 0070/0071 → 0066 (konflikty: generated/*.json = `--ours` + regeneracja; shadery/QualityProfile/RenderOverrides/LICENSES = unia).
2. Pełna integracja na main: build_region → build_world → import-region (CC0: najpierw `cc0_fetch.py`), Truck/Trailer BuildBatch, InstallBatch, pytest/EditMode/PlayMode/physics, czysty build Low + High. Uwaga: EditMode 2 inconclusive `TruckCabGlassTierTests` — sprawdzić.
3. Telefony pod `artifacts/locks/PHONE_RUN` (S24+ 46 %/33 °C o 21:15; A16 80 %): A16 Low gate3 + kabiny × 3 pory + świat ov; S24+ High A/B (cel 60 kl./s).
4. Decyzje właściciela do zebrania w r9: ekspozycja ov (p10, ADR 0060), D23 biel 0,7 vs przepał dachu N-17 (ADR 0072). APK High właścicielowi (FEEL-TEST), recenzja r9 (visual-critic) + decyzje (ekspozycja ov dla p10, wynik audytu mapy), raport bramki 3.

---
# HANDOVER — kamion (TRUCK SIM PL), stan 2026-11-10 ok. 20:00 (sesja 4, limit 86 %)

## Najpierw (sesja 4 → następna)
- **main = `1ff9fb5`, wypchnięty** (po 0e45111 doszły lusterka ADR 0068).** Scalone w sesji 4: metadane gate3 (gitSha z APK, `-Apk`, duplikaty md5), kamery gate3 jedna poza edytor/telefon + kadry kabiny na telefonie, auta r8 (0/81 dziur, LOD0 16 m, ADR 0041 r8), szkło r8 (ADR 0059: brak stożka/prążków lowsun, szyba drzwi), skala 0,70 + FSR + pacing 30 + plamy latarni dusk −5° (ADR 0062), wypiekana widoczność nieba + dalekie cienie (ADR 0064), Mapillary (ADR 0065, `tools/refs`), lista ujęć + pokrycie, recenzja r8, różnice gra vs Mapillary (`docs/reports/visual/REFS-MAPILLARY-FINDINGS-2026-11-10.md`).
- **Decyzje D36–D44** w `docs/11` (skala 0,70; próg farby względny; albedo trawy 35–40; panel dev zostaje; CC0 tak; właściciel NIE robi zdjęć — tylko otwarte źródła; Mapillary tak; σ szyby ≥ 8 tylko przy słońcu). Google Maps/3D Tiles/Street View — odmowa wyjaśniona właścicielowi (ToS + koszt + jakość).
- **Pomiary:** A16 Low e3671b4 `artifacts/gate3/20261110-a16-low-e3671b4/` (G3-A p99 50 ms > 40; cab-dash czerń 2,8–3,8 %; 0 duplikatów). S24+ High e3671b4: 43–47 kl./s (G3-A/G3-B w `artifacts/gate3/20261110-172908`, `-175241`).
- **Token Mapillary** w `C:\Users\matma\.kamion\secrets.env` (czyta `tools/refs/mapillary_fetch.py`; nigdy nie wypisywać).
- **Blokada telefonu:** `artifacts/locks/PHONE_RUN` — agenci nie startują Unity, gdy plik istnieje. Zakładaj przed pomiarem, zdejmij po.

## Agenci w toku przy końcu sesji 4 (worktree `.claude/worktrees/agent-<id>`, gałąź `worktree-agent-<id>`, STATUS.md w `<wt>/artifacts/<dir>/`)
| id | model | zadanie | ADR | dowody |
|---|---|---|---|---|
| a9eaaeb7a945e26bb | Opus | ciemne akcenty p10 ≤ 28, berberys (+ rozmieszczenie wg Mapillary: żwir pod wiaduktem), albedo trawy D38, próg farby D37 | 0060 | world-r8 |
| a6fd2182039af9a34 | Fable | przód TRAKT Low lowsun + aliasing napisu/wycieraczek + E7 obudowy lusterek + N-17 deflektor | 0061 | front-r8 |
| a173ed44d3c378718 | Opus | skany CC0 (Poly Haven/ambientCG) jako baza materiałów świata | 0063 | cc0-r8 |
| ab1fb0a47d2f0a491 | Sonnet | otwarte źródła referencji (KartaView, Panoramax, Commons, Openverse, ortofoto GUGiK, dane miasta) | 0066 | refs |
| a1ec6028c4e13f527 | Fable | wiadukt jako hero asset wg Mapillary | 0067 | viaduct-r9 |
| ~~a165b14c05122bf57~~ | Opus | lusterka — SCALONE 1ff9fb5 (A/B na S24+: `rq_ab mirrorcfg|mirrors|envcap|shadows|shadowcasc`, `rq_scale 1.0 rq_pacing 0`, ≥ 90 s) | 0068 | mirror-r9 |
| a6651051778fa221f | Opus | wyposażenie drogi wg Mapillary (ekrany, bramownice, bariery, sygnalizacja, strzałki) | 0069 | street-r9 |
Przy przejęciu: `git -C <wt> log main..HEAD`, przeczytaj STATUS.md, dokończ albo scal; konflikty możliwe w `tools/worldgen/build_world.py`, `WorldSurface.shader`, `QualityProfile.cs`/`RenderOverrides.cs` (unia pól). Przed usunięciem worktree: skopiuj artifacts, `cmd /c rmdir` junctiony Data/raw, potem `git worktree remove --force --force`.

## Następne kroki
1. Scal pozostałych agentów (kolejność: świat 0060 → CC0 0063 → ulica 0069 → wiadukt 0067 → przód 0061 → lusterka 0068).
2. Pełna integracja na main: build_region → build_world → import-region (zawiera WorldSkyBake), Truck/Trailer BuildBatch (szyba drzwi ADR 0059 — bez tego 3 testy `TruckDoorGlassTests` czerwone), InstallBatch, pytest/EditMode/PlayMode/physics, czysty build Low + High.
3. Telefony (blokada PHONE_RUN, bez Unity): A16 Low gate3 (koszt LOD aut 16 m, plamy latarni, WorldSkyBake: `rq_worldgi 0` A/B), S24+ High A/B wg ADR 0062/0068 (`rq_scalemin`, `rq_mirror_*`, `rq_shadow 60`). Przy `gate3-run` używaj `-Apk` i `pwsh -Command` dla parametrów tablicowych.
4. Recenzja r9 (visual-critic) z kadrami telefonu + montaże Mapillary; raport bramki 3 (`docs/reports/GATE-3-draft.md`) do decyzji właściciela.
5. Właściciel testuje jazdę (P + kierownica ADR 0058) na S24+ — APK e3671b4 High zainstalowany; poproś o wynik/logi `CONTROLS`.

---
## Najpierw (sesja 3 → następna)
- **main = `166fa76`, wypchnięty.** Scalone w sesji 3: crash visual-qa D3D12 (ADR 0051), kamera fotela/H-point (ADR 0052), belka maski r7b + przód r7c (ADR 0047), AO aut (ADR 0050), żywopłoty + kontrast farby (ADR 0049 r7), hale Low/High (ADR 0012 r7), capture odbić na wszystkich tierach (ADR 0056), przetarcia skóry (ADR 0044 r8), **ciemna kabina tylko w kadrach QA** (ADR 0044 r9, `ViewCameraResolver`), kierownica — model ręki/szybkość (ADR 0058), **hamulec postojowy trzyma + blokada ruszania AMT** (ADR 0004 addendum), Log bez stack trace, audyt albedo bez szkła/łat AO, `import-region` przebudowuje tekstury gdy `_src` nowsze.
- **Decyzje właściciela D30–D35** (progi r7) w `docs/11`. Zgoda na pomiar S24+ High **jest** (sesja 3), warunki z `docs/owner/S24-HIGH-RUN.md`.
- **Scalone po 16:00:** nowa kierownica r8b (Fable, ADR 0044 r8b; wnętrze LOD0 sha1 2ff350fb… w `art-source/truck/interior/export/`), ostrzeżenie P w HUD + gong + kontrolka (767ba9f).
- **W toku przy końcu sesji 3 (przejmij):** (1) build-qa na **main**: pełna integracja → czysty build Low+High → A16 Low gate3 → S24+ High (zgoda jest); status krok po kroku w `artifacts/handover/final-integration-status.md`, commity na main. (2) Fable, auta: dziura w aucie w `cab-dash` + LOD aut Low 8–12 m; worktree w `.claude/worktrees/agent-aeb4c025dbb5eae0c` (gałąź `worktree-agent-aeb4c025dbb5eae0c`, commity `wip(cars):`), status `artifacts/world-fixes/cars-r8/STATUS.md`. Sprawdź `git -C <wt> log main..HEAD`, dokończ, scal, odepnij junctiony Data/raw przed usunięciem worktree.
- Zablokowane (lock pid) puste worktree po scalonych agentach: `agent-a2435fdaafe42d6e9`, `agent-a6929d46dce94eb64`, `agent-a140cf18e9d148e78` — wszystkie scalone; usuń `git worktree remove -f -f` (najpierw odepnij Data/raw).
- **Tekstury PBR na main przebudowane** (asfalt 0,080), ale świat NIE zaimportowany po tym — zrób pełną integrację.
- **Pomiary telefonów:** A16 G3-A/G3-B na `f6abb8b` w `artifacts/gate3/20261110-a16-low-f6abb8b/` (p95 33,5 ms, PSS 739/769 MB, CPU p99 41,8–42 ms > 40). **cab-dash z telefonu nieważne** (błąd QA kamery, naprawiony w r9). A16 bywa `offline` → właściciel przepina kabel.
- **ADB: daemon zabija Unity** (każdy batch Unity). Pomiary telefonów tylko gdy ŻADEN Unity nie działa. `env.ps1` przypina adb z SDK Unity. `gate3-run -SkipBuild` instaluje NAJNOWSZY plik z `artifacts/apk` — pilnuj.
- Owner feel-test S24+ (f6abb8b): hamowało przez P (naprawione), kierownica za szybka (naprawione ADR 0058) — do ponownego testu.

## Następne kroki
1. Jeśli build-qa nie skończył: pełna integracja na main: build_region → build_world → import-region, Truck/Trailer BuildBatch, InstallBatch, wszystkie testy; **czysty (nie -dirty) build** Low + High.
2. Bez innych Unity: A16 Low gate3 G3-A + G3-B + kamery kabiny (cab-dash ≤ 8 % czerni, logcat `[CAB] view camera … cabView=True`), gate3-evidence. Potem S24+ High wg checklisty (bateria ≥ 40 %, < 36 °C, am force-stop na końcu).
3. Recenzja r8 (visual-critic) z kadrami telefonu; zainstaluj APK właścicielowi do testu jazdy (FEEL-TEST.md: P, kierownica).
4. r7 cz. 2 top (docs/reports/visual/REVIEW-2026-11-10-r7.md §9–14): auto z dziurą w cab-dash + toporny LOD aut na Low 8–12 m; szyba drzwi od środka + **regres: stożek/prążki w szybie przy lowsun (ADR 0056?)**; ciemne akcenty świata p10 ≤ 28; przód Low lowsun + aliasing TRAKT/wycieraczek; berberys kształt; σ szyby ≥ 8, jasny prostokąt w szybie, chrom lusterek.
5. Metadane gate3: `gitSha` = sha APK, nie HEAD; `g3b_eye_s1532` == `s1482` (duplikat); `putry_approach` poza.
6. Otwarte z sesji 2 (pkt 7 niżej) częściowo zrobione: żywopłoty, kontrast, ślady w dokach (nie odtworzone), hale, kamera fotela, lusterko kl. VI (OK), crash visual-qa.

---

# (sesja 2)
## Najpierw (sesja 2 → następna)
- **main = `0eb8b84`, wypchnięty.** Scalone w sesji 2: lusterka R46 + High 2 RT/klatkę (ea8ba23), druty WN min. px + łańcuchówka + zacieki attyki v2 (e7c6bae), shadery zewn. (firanka, niebo High, szyba, fp16 glint; 28f9a64), geometria TRAKT r6 (2e12e8c), wnętrze r6 kierownica (03e539d), auta v4 + naprawiony test budżetu (bb7549d), gate3 W-N10 + S24 checklista (29f4dfd), ulice r6 ADR 0049 + TRAKT r6b (8eb64fe), szkło aut + toe parity (0eb8b84).
- **Integracja na main zrobiona:** świat zregenerowany, Truck/Trailer BuildBatch, import-region, WorldTruckInstaller. Testy: pytest 185/185, EditMode 112/112, PlayMode 63+5 skip, physics 147/147. APK Low `artifacts/apk/kamion-0.1.0-0eb8b84a74.apk` (164,6 MB, SHA256 442ed5a6…a936e) — kompiluje się, **NIE zainstalowany**.
- **A16 `RFGL34SJYDZ` OFFLINE w adb** od ok. 12:40 (po przebiegu gate3; możliwe, że gra nadal działa — po podłączeniu `am force-stop com.woogitsugames.kamion`). Właściciel musi przepiąć kabel / zatwierdzić debugowanie USB. Demon adb bywa zabijany przez równoległe adb (scrcpy vs Unity SDK) — używaj tylko `$Adb` z `scripts/env.ps1`, jeden agent telefonowy naraz.
- **Dwa agenty w toku (worktree od 8eb64fe, jeszcze niescalone):** `agent-a6910633040021c05` (Fable: dziura w belce maski `grille_bar_mask` LOD0/LOD2, r6 E-N2 — ADR 0047 addendum r7) i `agent-ae69268ea41cf7bcc` (Opus: AO kontaktowe pod zaparkowanymi autami). **Oba zapisały WIP (niezweryfikowane):** belka `10dc12e` (ADR 0047 „Addendum r7b WIP”, kroki dalej tam; nowe wnętrze LOD0 w `artifacts/owner/modern-front/r7-maskbar/export/` → skopiuj do `art-source/truck/interior/export/`), AO aut `1b14744` (ADR 0050 + ADR 0041 „AO aut — WIP”; overcast p5 8–11 % > 8 %; sprawdź `test_parking_mix_and_neighbours` KeyError). Sprawdź `git -C <wt> log main..HEAD`, skopiuj `artifacts/`, scal `--no-ff`, potem regeneracja świata + BuildBatch/InstallBatch. **Uwaga przy sprzątaniu worktree:** agenci robią junctiony `Data/raw/gugik` i `Data/raw/osm` do main — najpierw `cmd /c rmdir` na junctionach, dopiero potem `git worktree remove --force`.
aw\gugik`/`osm` do main — najpierw `cmd /c rmdir` na junctionach, dopiero potem `git worktree remove --force`.
- `SM_CabInterior_LOD0.fbx` (poza gitem) skopiowany do `art-source/truck/interior/export/` z r6b — nie nadpisuj starszym.
- Stash `stash@{0}` = lokalne wyniki regeneracji sprzed sesji 2 (do wyrzucenia).
- Do usunięcia ręcznie (auto-mode zablokował): gałąź zdalna `origin/wip/wires-streaks` (zastąpiona), puste katalogi w `.claude/worktrees/`.

## Następne kroki
1. Scal dwa agenty powyżej, regeneruj, testy, build Low.
2. A16 Low: `pwsh scripts/gate3-run.ps1 -Serial RFGL34SJYDZ -Tier Low -Fps 30` (G3-A, G3-B) + `-TruckCameras`/`-TruckLightings` (truck-34, cab-dash × overcast/lowsun/dusk); potem `gate3-evidence.ps1 -PhoneDir <nowe>`. Ostatni pomiar A16 (`ecfd03b`, sprzed poprawek r6): p50/p95/p99 33,3/33,5/33,7 ms, PSS 675–701 MB, thermal 0; CPU main p99 42–45 ms (> 40, przyczyna UNVERIFIED); cab-dash z telefonu 30–47 % czerni (sprzed poprawek wnętrza).
3. Recenzja **r7** (`visual-critic`, Opus): kadry edytora już są — `artifacts/gate3/r7-editor-0eb8b84/` (246 renderów Low/High × overcast/lowsun/clear, wszystkie frame_exposure PASS; FAIL tylko albedo_histogram — głównie szkło, które audyt powinien wyłączyć — i texel_density płotów). Dorzuć kadry A16 i montaże ze zdjęciami (Scania R/S730, Bieżeństwa).
4. **Decyzje do właściciela (klikalnie) po r7:** progi r6 E2 szyba ≥60 % i E1 lakier ≥15 pkt (agent: fizycznie nieosiągalne w tym kadrze; szyba 38–41 %, akwarium zniknęło); szyby aut ≤20/≥40 % (jest 23–31/31–44 %, fizyczne odbicie nieba — albo przyciemnić model nieba ADR 0010); kierownica przy lowsun sat 18–19 % (próg 15; to kolor słońca LP_LowSun przy WB 0,5, D27).
5. S24+ High za zgodą (`docs/owner/S24-HIGH-RUN.md`; bateria ≥ 40 %; przy ostatnim sprawdzeniu 62 %).
6. Raport bramki 3 (`docs/reports/GATE-3-draft.md`) → APK do testu jazdy (D25, `docs/owner/FEEL-TEST.md`).
7. Otwarte: żywopłoty Bieżeństw wyglądają jak bryły; kontrast farba/asfalt 1,5 (krytyk chce ≥ 1,8 → ciemniejszy asfalt); ślady opon w dokach nie renderują się na Low; przetarcia kierownicy niewidoczne przy limicie albedo czarnego 0,05 (decyzja rendering-perf); Low/High różna geometria hal (rynny/doki tylko High); kamera na fotel kierowcy; lusterko kl. VI w całości pod osłoną przeciwsłoneczną w `cab-mirror-front` (sprawdzić po r6 geometry); visual-qa High lowsun crash przy zamykaniu Unity (−1073741819, kadr zapisany).


---

# (poprzednia wersja, sesja 1)

Dla nowej sesji Claude Code na tym samym komputerze (`C:\Users\matma\Documents\Claude\kamion`), inne konto Claude. Czytaj w kolejności: ten plik → `CLAUDE.md` → `docs/11_DECYZJE_WLASCICIELA.md` (D1–D29) → `docs/reports/GATE-3-draft.md` → `docs/reports/visual/REVIEW-2026-11-10-r5.md` → `docs/REFERENCES.md`.
Pamięć poprzednich sesji: `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\` (MEMORY.md + pliki) — jeśli nowe konto jej nie ładuje automatycznie, przeczytaj ją ręcznie.

## Stałe polecenia właściciela
- Autonomicznie (bypass), wolno instalować narzędzia. **Jakość, nie cena** — „realistyczne na maksa i piękne”.
- Agenci równolegle (właściciel pozwalał na 10–20; każdy w swoim worktree, lider = jedyny integrator, `git merge --no-ff`, push na https://github.com/woogitsugames/kamion, potem `git worktree remove` + `git branch -D`).
- Modele: **Fable 5.2 (`model: "fable"`) do modeli 3D** (truck-artist, Blender, auta), **Opus** do grafiki/shaderów/świata/fizyki, Sonnet średnie, Haiku proste.
- Decyzje dla właściciela **klikalne** (AskUserQuestion), po polsku. Na koniec większego kroku: commit, push, krótki raport po polsku.
- **Zakaz Google Street View/Maps/Earth** (ADR 0002). Referencje: Wikimedia Commons (`data/photos/nowe/`, poza gitem, licencje w `docs/REFERENCES.md`), GUGiK/OSM. Zdjęcia prasowe/AI od właściciela = tylko wzór stylu, nigdy kopiowanie cudzej marki (CLAUDE.md §8).
- Telefony: zawsze `-Serial`; przed każdym przebiegiem `isKeyguardShowing=false` i temp. baterii < 36 °C; **nigdy KEYCODE_SLEEP/POWER, nigdy PIN**.
- **S24+ `RZCX60VE8ZY` to telefon roboczy właściciela (odbiera połączenia/SMS):** bateria nigdy < 20 %; przebieg tylko przy ≥ 40 %, < 30 % — koniec pracy na nim; po pomiarze `am force-stop` gry; tylko za zgodą właściciela. Ładuje się wolno z USB komputera (port USB-C bezpośredni). A16 `RFGL34SJYDZ` (Low) bez ograniczeń.
- **Przed usunięciem worktree skopiuj jego `artifacts/`** do głównego checkoutu (2026-11-10 straciliśmy tak zrzuty S24+ i klipy DK8). W briefach każ zapisywać dowody pod ścieżkę absolutną `C:\Users\matma\Documents\Claude\kamion\artifacts\...`.
- Po buildach cofaj efekty uboczne: `game/ProjectSettings/ProjectSettings.asset` (preloadedAssets), `QualitySettings.asset`, `M_Sky.mat`, pusty `game/Assets/Resources(.meta)`.

## Gdzie jesteśmy (main = ok. HEAD z 2026-11-10 ok. 11:30)
- **Etap 3 (bramka, odcinki G3-A i G3-B: brama Kwadrat Parku → Rondo Putry)** — pomiary zrobione (`docs/reports/GATE-3-draft.md`):
  - A16 Low (sha `c59209e`): G3-A/G3-B p50/p95/p99 33,3/33,5/33,6 ms, PSS ~690 MB, bez grzania — **PASS**.
  - S24+ High (stary build `fefd804`): p95 50/33,5 ms — **FAIL**; poprawka ADR 0046 (adaptacyjna skala 1,00/0,85/0,80 + FSR1/RCAS, zejście do 30 FPS przy thermal ≥ 2, lżejsze cienie) scalona, **niezmierzona na telefonie**.
  - Zrzuty A16 37/37: `artifacts/gate3/final/` (+ `small/`). Zrzuty S24+ i klipy DK8 MSAA — **do powtórzenia** (za zgodą właściciela, bateria ≥ 40 %).
  - Narzędzie dowodów `scripts/gate3-evidence.ps1` (6 kontroli docs/06 §5); ostatnio FAIL tylko „obiekty vs teren” (7 latarni 12 m do 0,35 m nad terenem, 5 słupków znaków zakopanych do 0,86 m na wysepkach rond).
  - E6 limit świata w APK podniesiony do **≤ 110 MB** (D24, bez Play Asset Delivery); zmierzone ~94 MB górnej granicy.
  - Przejazd zestawu po rondach: `tests/physics/test_swept_path_gate3.py` (zjazd z ronda Bieżeństwa wymaga szerszego toru).
- **Ciężarówka TRAKT — nowy nowoczesny front** (D28, D29: pochylenie 1,5°, ADR 0047) w grze; eksport LOD0 102k / LOD1 43k / LOD2 15,3k, koła LOD2 okrągłe (ADR 0039). Wnętrze dopasowane (ADR 0045 szyba od środka). Lakier/brud ADR 0038, cień kontaktowy ADR 0021, lusterka ×6 ADR 0042, kierunkowskazy + żywe zegary (fuel/coolant/clock WORKING_VALUE).
- **Świat C** v3.4 + materiały PBR, zaparkowane auta (1076 → 921, generator `tools/worldgen/streetscape/life_cars.py`, ADR 0041), ekrany akustyczne, kosze, wiaty, rowy 1:1,5 (ADR 0033, ratchet 103 ścianek), zadaszenia na wszystkich tierach.
- **Wygląd:** D23 „jak zdjęcie z telefonu”; balans bieli 0,5 przy niskim słońcu (D27, ADR 0043); cab lift ADR 0029.
- **Menu testu jazdy właściciela** + `docs/owner/FEEL-TEST.md`, log `[CONTROLS]` bez alokacji. Test jazdy (D25) **po raporcie bramki 3**.

## Prace w toku w chwili przekazania (sprawdź `git -C <worktree> log main..HEAD`, skopiuj `artifacts/` do main, scal albo dokończ)
Scalone dziś już: TRAKT r3 (słupek A 7,0°), r4 (lamele grilla 20° w dół, lusterko kl. VI na ziemię, węższe lusterko 11,25°), shader czarnego plastiku (ADR 0047 r3), strażnik jednej warstwy szkła (ADR 0048; „podwójna szyba na Low” niepotwierdzona — sprawdzić dwa poziomy GLASS_* naraz albo szybę z CabInterior). Diagnoza „akwarium”: wnętrze ma fizycznie poprawną jasność, kabina jest przezroczysta na wylot (dowody `artifacts/owner/aquarium/`).

| Zadanie | Worktree (`.claude/worktrees/…`) | Uwagi |
|---|---|---|
| (scalone `ffbe6cf`) wnętrze: polerowanie wieńca/wybieraka, listwa u stopy słupka A, zasłony koi i drzwi pasażera; **sprawdzić**: przy lowsun zasłona pasażera przyciemnia piastę/konsolę (próg czerni `cab-dash` ≤ 8 %), połysk addytywny w CabInterior.shader do przeglądu rendering-perf; fotel/mata/drzwi poza kadrem — nieocenione | — | gotowe |
| (scalone `65f3acd` + regeneracja świata na main) latarnie/słupki: 0 zakopanych słupków, 3 latarnie wiszą 0,301–0,305 m (próg 0,30; podejrzenie: rzadsza kolizja terenu), ratchet ścianek 103 → 14, jedna prawdziwa ścianka `j:n1847044961` przy Rondzie Putry otwarta | — | gotowe |
| Opus: druty WN min. szerokość w px (P0 z r6) + zacieki pod attyką | `agent-a00eb437b0f666944` (kopia: `origin/wip/wires-streaks`) | **WIP `a1d4e81`, NIE scalać bez weryfikacji**: kod drutów (`_ScaledScreenParams`, rdzeń ≥1,2 px, AA) i zacieków (`parapet_runoff`, UV1, `_RUNOFF`) jest, ale rendery nie potwierdzają efektu; część ścian `hall_wall` bez TEXCOORD_1; addendum ADR 0022 opisuje to jako działające — poprawić. Dowody `artifacts/world-fixes/wires-streaks/` |

Scalone też: auta v3 (`b8c93ca`; felgi LOD1 „rim_dusty” przyciemnione w kodzie, nieprzerenderowane). Konflikty w `Data/Regions/bialystok-industrial-c/generated/*.json`: bierz `--ours` i wygeneruj świat ponownie po scaleniu wszystkich gałęzi świata.

**Czerwony test na main:** `tests/gis/test_world_v31.py::test_frame_budget_with_forest_hlod` (po autach v3, LOD0 aut 3,3–3,6 k tris) — napraw uczciwie (dystanse LOD aut / oszacowanie), bez luzowania limitu.

## Recenzja r6 (docs/reports/visual/REVIEW-2026-11-10-r6.md) — top poprawek
1. **P0** build ≥ obecny main na A16 (Low) i nowe 37 kadrów gate3 + `truck-34`/`cab-dash` (stare kadry są sprzed nowego frontu i aut). Akceptacja `cab-dash` < 3 % luma ≤ 8 %.
2. **P0** druty WN (w toku). 3. **P1** kierownica beżowa przy niskim słońcu / czarna dziura na Low (CabInterior lighting). 4. **P1** naczepa: ciemna plama na firance, jasna łata pod naczepą. 5. **P1** szyba z zewnątrz, odbicie ziemi w lakierze drzwi, narożniki maski jak dziury; lakier matowy/kredowy. 6. **P1** auta: rozrzut brył/kolorów/kątów, wolne miejsca, ta sama liczba na Low i High. 7. **P1** farba linii na A16 ≤ 217 sRGB (teraz 246–249), kamera `g3a_eye_s0012` w geometrii, automatyczna kontrola 37 kadrów. 8. **P2** napis TRAKT na Low, gradient nieba High (pochmurne = biel 254), żywopłoty Bieżeństwa, ślady w dokach, kadry lusterek nowej kabiny.

## Następne kroki (kolejność)
1. Dokończ/scal dwie prace powyżej; przebuduj prefab (`Game.Editor.Setup.TruckAssetBuilder.BuildBatch`), testy EditMode + PlayMode + `uv run --project tools/worldgen --with pytest --with scipy pytest tests/ -q` + dotnet runner (`%LOCALAPPDATA%\Microsoft\dotnet\dotnet.exe test tools/physics-runner -c Release`).
2. Recenzja wizualna **r6** (`visual-critic`, Opus) nowego frontu, aut, wnętrza na klatkach URP i A16.
3. Za zgodą właściciela: S24+ High z nowym buildem (ADR 0046) — G3-A/G3-B, zrzuty kamer, klipy DK8 (jazda, nie statyczna kamera), 30-min test termiczny; sprawdź natywną rozdzielczość buildu (QHD+ vs FHD+).
4. Raport bramki 3 do końca (sekcje wizualne, werdykt) → APK do testu jazdy właściciela (D25).
5. Otwarte: auta — mleczne szyby LOD0 na High, brud progów, przody kanciaste; latarnie/słupki vs teren; ścianki terenu na skrzyżowaniach (ratchet 103); linie WN rwą się subpikselowo (min. szerokość w px); zacieki pod attyką hal; lusterko przednie celuje w niebo; przetarcia na kierownicy/fotelu (generator wnętrza); lusterka 3→2/klatkę na High (propozycja w ADR 0046); lamele grilla pochylone czołem w dół (geometria, zamiast obejścia w shaderze — ADR 0047 r3); szyba z zewnątrz wciąż „akwarium”.

## Narzędzia
Unity 6000.3.28f1 (`scripts/env.ps1`), Blender 4.2.9 `C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe -b` (**nigdy `Mesh.materials.clear()`**), .NET SDK user-local, uv/Python, ImageMagick, scrcpy, adb. Komendy w `CLAUDE.md`.

## Prompt startowy dla nowej sesji
Patrz `docs/owner/START-PROMPT.md` (do wklejenia jako pierwsza wiadomość).
