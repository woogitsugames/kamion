# Prompt startowy — sesja 24 (SZKIC r2; wklej do nowej sesji Claude Code w C:\Users\matma\Documents\Claude\kamion)

> Szkic r2: sesja chmurowa P r7 (16.11 ok. 18:0x). Źródła: `HANDOVER.md`, blok SESJA 23 do wpisu „[16.11 17:5x] Zlecenia”
> (main `8a4de955a`), i `docs/11_DECYZJE_WLASCICIELA.md` (D76–D84). Wcześniejsza wersja (r1, stan 10:30) jest w historii gita.
> **Sekcje oznaczone „DO UZUPEŁNIENIA PRZEZ LIDERA” lider wypełnia na końcu s23**: sha main, stan agentów i łańcuchów,
> limity, dysk, scalenia po 17:5x. Reszta to stan z 16.11 ~17:5x — przed wklejeniem sprawdź, czy się nie zmienił.

```
Kontynuujesz projekt Kamion (realistyczny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1 → DK65 → Knyszyn → pierścień Mońki/Tykocin) w C:\Users\matma\Documents\Claude\kamion. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion. Komunikacja po polsku. Godziny z zegara systemowego (Get-Date).

NAJWAŻNIEJSZE ZMIANY s23 (15.11 22:5x → 16.11):
- Windows = platforma główna (D73/ADR 0260). CLAUDE.md „Komendy” zaczyna się od build-windows.ps1, pc-metrics.ps1 i package-windows.py; telefon 🔒 odroczony.
- CIĄGŁA JAZDA DZIAŁA: streaming kafli scalony (int-stream-s23, b2fb6303c; #157, #112 zamknięty jako wchłonięty). `Kamion-korytarz.cmd` = `-scene knyszyn -stream 1`, pełny ekran. Bramka streamingu PASS: knyszynska→dk65-01→02→03, 0 zamkniętych szwów, load p50 233 ms, p99 klatki 16,7 ms, 1×531 ms, 1,2 GB. Exe korytarza (19 regionów): `.claude/worktrees/int-stream-s23/artifacts/win/kamion-0.1.0-a920cfb35b-regions`.
- FEEL TEST BRAMKI 2 ZALICZONY 5/5 (D84; klawiatura, DrivingLab, exe e28533ca31). Uwagi właściciela:
  - kabina na PC „brzydka” — to GRAYBOX: DrivingLab buduje makietę (GrayboxTractorBuilder), prawdziwy model wstawia tylko WorldTruckInstaller w scenach regionów;
  - HUD i menu „AI slop” → redesign ADR 0283 (#166);
  - lusterka za małe.
- Naczepa: sworzeń–środek tridemu 7,63 m (D79 z korektą; ADR 0280 przyjęty). Pierścień skrętu 96/53/WE PASS (wewn. 5,309 m, szer. 7,177 m). Pełzanie na 12 % spadło z 5,04 do 0,69 mm po poprawce relaksacji postoju naczepy. swept_path.py:43 zmieniony przez lidera. Model Blendera — jeszcze NIE.
- Emulacja PC (D76) w parserze: `tools/pcperf/budgets/pc-machines.json`, measurement_kind, gate_eligible przy zgodnej konfiguracji. Pomiar wymaga `-VSync 0`.
- CRASH D3D12 u właściciela: exe 13104cf215, knyszyn, pełny ekran borderless, RTX 5070, sterownik 32.0.16.1088. Log `d3d12: Device failed error (887a0001)` → device removed. Dump w `%LOCALAPPDATA%\CrashDumps\Kamion.exe.73136.dmp`. Doraźnie gra działa z `-force-d3d11`. Research: sesja P r7 → `docs/reports/RESEARCH-2026-11-16-d3d12-device-removed.md` (gałąź d3d12-crash-research, jeśli jeszcze nie w main).
- MODEL AGENTÓW: nowi agenci na Opusie (limit Fable: 69 % tygodnia o 16:19). Fable zawieszał się przy czekaniu na łańcuchy.

PRZECZYTAJ NAJPIERW:
- HANDOVER.md: blok „SESJA 23” — najnowsze wpisy tuż nad linią „Ostatni przydzielony ADR” (**0283**; następny wolny **0284**). Zakresy s23:
  - 0262 spawn-fix, 0268 znaki przejazdów;
  - 0269–0271 chmura H r2, 0276–0277 chmura H r3;
  - 0272–0273 chmura D r4, 0274–0275 chmura D r5, 0278–0279 chmura D r6, 0281–0282 chmura D r7, 0283 chmura D r9;
  - 0280 pierścień skrętu (sesja P).
- CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md, docs/owner/S20-PR-REVIEW-BRIEF.md;
- docs/11_DECYZJE_WLASCICIELA.md (D63–D84), docs/owner/OPEN-DECISIONS.md (r2: P1 otwarte = 0), docs/reports/GATES-STATUS-2026-11-16.md;
- docs/owner/JAK-GRAC-PC.md (instrukcja gracza; r2 z sesji P r7 — korytarz, pełny ekran, -force-d3d11), docs/owner/FEEL-TEST.md;
- artifacts/live/*.md (stan każdego agenta z NASTĘPNYM KROKIEM).

DECYZJE WŁAŚCICIELA s23 (nie pytać ponownie):
- D75: rondo Knyszyn — jasna kostka z fakturą; przejezdność (5,0 + 3,2 m) ważniejsza niż wierność.
- D76: klasy PC min/zalecany mierzone emulacją na RTX 5070. Raporty z adnotacją „emulacja”. Prawdziwy sprzęt przed obietnicą wymagań.
- D77 → D84: feel test bramki 2 na exe PC — ZALICZONY 5/5. Pad i kierownica FFB nietestowane.
- D78: Rynek Knyszyn (#139) przejęty lokalnie, +64 draw calls Low przyjęte — SCALONE.
- D79 (+ korekta): naczepa 7,63 m + uczciwa poprawka hamulca postojowego — SCALONE (ADR 0280).
- D80: pad — warstwa „przytrzymaj Back + przycisk”; Back przestaje być R. Implementacja: chmura H r4 / agent UI.
- D81: trasa C ↔ Dojlidy DK19 Piastowska–pl. Antonowicza–Branickiego, skręt w Ciołkowskiego. Bez zdjęć znaków → WORKING_VALUE.
- D82: Podlasie — najpierw pętla S8 ↔ DW671 ↔ Tykocin (15 kafli, zgoda na S8 mimo D64); Grajewo później.
- D83: budżety kafli PC mierzone per tier (2 M High było z telefonu). Gęste kafle Białegostoku (2,6–3,75 M) i Grajewo czekają na pomiar.
- Wcześniejsze z s23: nowi agenci na Opusie; pierścień #115 w d67-full; start dk65-06 za rondem; sprzątanie dysku (08:4x); praca do 90 % limitu 5 h.

ZASADY (z s22–s23, obowiązują):
- najwyżej 5 lokalnych agentów naraz, nowi na Opusie. Agenci ZAWSZE uruchamiają długie kroki ODŁĄCZONE (Start-Process) i od razu kończą turę (watchdog 10 min); agent czekający w turze na bezczynną maszynę zostaje ubity (pc-budget 13:2x). Po każdym kroku: commit WIP + push + live;
- sloty maszyny `heavy` (build_world) i `unity` (import, EditMode, buildy): `scripts/unity-slot.ps1`, `-Slot`; jeden proces Unity na katalog;
- łańcuchy w tle: **nie ufać .done ani „CHAIN DONE”** — czytać `exit=` każdego kroku w `*.status`. exit=-1073741502 (0xC0000142) = proces nie wystartował;
- **ZASADA DERIVED (od 16.11 12:2x — błąd procesu):** `Data/raw/derived` w worktree bywał KOPIĄ, nie junction. Nocne przebudowy zapisały świeże GLB tylko w kopiach, które usunięto razem z worktree.
  - Nowe worktree budujące świat: derived = **junction do main**.
  - Przed usunięciem worktree budującego świat: `robocopy <wt>\Data\raw\derived\<kafel> <main>\Data\raw\derived\<kafel> /MIR` dla każdego przebudowanego kafla.
  - Przed reimportem: sprawdzić datę najnowszego pliku w `derived\<kafel>\world`.
  - **win-build-0261 miał STARĄ kopię derived (15.11)** — przed pełnym buildem junction do main albo robocopy /MIR 39 kafli (int-ui ma to zrobić).
  - Zasadę do AGENT-RULES dopisuje chmura D r10 (D43).
- procedura usuwania worktree:
  1. robocopy artifacts (pełne PNG VQA, raporty) i derived (wyżej) do main;
  2. odpiąć junctions Data/raw: [System.IO.Directory]::Delete na każdym ReparsePoint w <wt>\Data\raw, NIE rekurencyjnie;
  3. sprawdzić, że main\Data\raw jest cały;
  4. git worktree remove --force;
  5. wpisać C: do HANDOVER.
  NIE usuwaj win-build-0261 (Library Win64);
- generated/* przy scalaniu: wersja z JEDNEJ wspólnej regeneracji (nie łatać ręcznie), overrides.yaml = suma bloków;
- crony: :07 (ZIP-y w Downloads), :17 (agenci, dysk, kolejka, HANDOVER + push), :47 (PR-y) — najpierw CronList. Cron pomiaru budżetów PC: 17.11 00:33 (watch.ps1);
- decyzje właściciela zawsze klikalne (AskUserQuestion), obrazy najpierw (SendUserFile);
- zakazy: Google Maps/Street View/Earth/3D Tiles — także zrzuty Street View od właściciela; jego zgoda nie daje licencji Google (16.11 15:5x). Marki i logo w grze i w nazwach zasobów. Zdjęcia właściciela tylko jako referencja;
- ciągły zapis: po każdym scaleniu, starcie i końcu agenta aktualizuj HANDOVER i push.

SCALONE W s23 (z HANDOVER):
- noc i rano: c-regen-s22 (#95 #120), spawn-fix-0262 ×2, int-pc-s23 (#129–#136), c-regen2-s23 (#109 #110 #111 #122 #124 #125), lamp-test-s23, int-dk65-s22 (#97 #98 #101 + rondo kompaktowe), pc-shadows-s23, rail-dk65-s22 (#102 + 0268 + #138), sesja P r1 + #85, #140, chmura D r6 (#145 #146 #148 #149);
- popołudnie:
  - c-regen3-s23 (5fe8a3a7f; #123 #119 #93 rebased + fix płotu);
  - derived 11 kafli DK65 odświeżony w main (42ddd470b);
  - chmura D r7 (#151 #152 #155);
  - sesje P r2–r6: #92 i #116 (stan na GitHubie — DO UZUPEŁNIENIA PRZEZ LIDERA), physics-validation, player-guide, start-prompt-s24, turning-circle (ADR 0280), docs-fixes, feel-test-pc, open-decisions-r2, gates-status, trailer-763-d79, pc-emulation-d76, review-rynek-s23;
  - **knyszyn-rynek-0227 (752696676; #139 Rynek + #144 rondo r2)**;
  - **int-h3-s23 (0761e7f6a; #118 #117 #141 #142 + fix P1 pętli scen; BEZ #113 — FIX: nieaktualne stałe KerbStrikeParity)**;
  - #156 (złote trasy nav), #159 (dachy, test typologii), **int-stream-s23 (b2fb6303c; #157 streaming + Kamion-korytarz.cmd)**, #161 (docs/10 bez Addressables), #160 (analiza K3b).
DO UZUPEŁNIENIA PRZEZ LIDERA: scalenia po 17:5x (world2? int-ui? #163?), sha main na koniec s23: ________

OTWARTE PRACE (stan 17:5x — DO UZUPEŁNIENIA PRZEZ LIDERA: exit= ostatnich kroków):
| praca | gdzie | stan 17:5x | następny krok |
|---|---|---|---|
| world2-s23 (#115 pierścień + #143 szwy) | worktree world2-s23 | WORLD DONE r2 (16:47), unity r2 (dk65-11 VQA) | raport → robocopy derived 25 kafli do main → scalić (sprawdzić poszerzony `osm_extract.BBOX_WGS84` 22,60/53,50 — czy nie zmienia generated innych regionów) → zamknąć #106 (zastąpiony przez #143) |
| world3 (jedna przebudowa) | nowy agent po world2 | nierozpoczęte | #147 → #154 → #158 → #153 → #150 + #164 (dachy, wariant agenta) + #165 (chodniki Knyszyna +21,8 km, Południowa×Szkolna; `pavement_rules` także w knyszyn-w) + K3b (warunek §7 raportu #160) + świetliki hal + OD-005 (`overrides.pending-od005.yaml` → overrides C) + fidelity C raz na końcu; budżet: Knyszyn Low ~639 k tris → czeka na D83 |
| int-ui-s23 (Opus) | win-build-0261 | start 17:3x | derived → junction do main; merge #163 („Koniec mapy”), #166 (HUD/menu ADR 0283), #162 (navgraph eps); EditMode/PlayMode; regeneracja nav .bytes + golden; sceny dk65-03/04 do EditorBuildSettings (decyzja lidera TAK); zrzuty HUD/menu/lusterek 16:9 i 21:9 + krytyk anti-slop |
| model naczepy 7,63 m | agent truck-artist (Opus) | nierozpoczęte | ADR 0280 §9: Blender `trailer_export.py` → `check_export`/`regs_audit`/`regs_check` → `TrailerAssetBuilder.BuildBatch` → prefab `Trailer_Curtainsider_Graybox` (GrayboxTrailerBuilder) → `TruckExterior.shader:63` `_CurtainAxles` → visual QA |
| DrivingLab z prawdziwym modelem + HUD PC | agent UI (po int-ui) | nierozpoczęte | ta sama ścieżka co WorldTruckInstaller; HUD PC zamiast dotykowego w DrivingLab (D84) |
| pomiar budżetów PC (D83) | pc-budget-s23 | wstrzymany przez lidera (0 przebiegów) | cron 17.11 00:33, tylko na bezczynnej maszynie, `-VSync 0`, emulacja D76 → pc-budgets.json + PERFORMANCE_BUDGETS + PC-BUDGET-2026-11-16.md |
| crash D3D12 | lider + research P r7 | doraźnie -force-d3d11 | kroki weryfikacji z RESEARCH-…-d3d12…; ewentualnie D3D11 jako domyślne API Windows (ProjectSettings — lider) |
| skróty i okno | build-windows.ps1 + ProjectSettings (lider) | zgłoszone 15:2x | skróty gracza: pełny ekran bez ramki (`-screen-fullscreen 1 -window-mode borderless`), skróty testowe 1600×900 osobno; resizableWindow + Alt+Enter |
| chmura D r10 | `docs/owner/CLOUD-D10-PROMPT-S23.md` | zlecona 17:5x | D41 Rynek P1 + override promienia ronda + uskok S; D42 determinizm fizyki (flaky `SameScenario_Twice_IsBitIdentical(lane_change_80@laden40)`) + park_brake_hold (55,2/150 mm); D43 importer bez zbędnego build_all + zasada derived; D44 streaming Low→High na desktopie („Low content, budget 800 MB”) |
| #113 jackknife | PR | FIX (KerbStrikeParity) | odesłać / nowa runda chmury H |
DO UZUPEŁNIENIA PRZEZ LIDERA: worktree istniejące na koniec s23 (int-stream-s23 zostaje do oceny właściciela; knyszyn-rynek-0227 do usunięcia po robocopy artifacts), procesy w tle.

OTWARTE PR (DO UZUPEŁNIENIA PRZEZ LIDERA — lista z GitHuba na koniec s23). Stan znany z HANDOVER 17:5x:
#113 FIX · #147 #150 #153 #154 #158 #164 #165 → world3 · #162 #163 #166 → int-ui · #143 #115 → world2 · #106 zamknąć po world2 · #100 Codex (NIE) · #79 światła (po modelu naczepy; rendery z playera).

CZERWONE / ZNANE W MAIN:
- flaky determinizm fizyki `RobustnessTests.SameScenario_Twice_IsBitIdentical(lane_change_80@laden40)` — raz w CI (#165); D42 chmury;
- navgraph `.bytes` ±0,5 m między Windows a Linuxem (searchsorted 1e-14) — #162 w int-ui;
- `test_knyszyn_ring_sectors_clear_the_u_turn` — pada niezależnie od osi naczepy (raport P r6), niezbadane;
- `test_gate3_meta.py::test_evidence_apk_info_legacy_and_dirty` (od s22); `test_world_v31` forest HLOD (znany);
- ADR 0269 otwarte: crash przy zamykaniu 1/5 (pc-shadows), cienie lasu/HLOD.
DO UZUPEŁNIENIA PRZEZ LIDERA: wynik pełnego EditMode/pytest gis na końcu s23.

LIMITY I DYSK (DO UZUPEŁNIENIA PRZEZ LIDERA): 5 h __ % (reset __), tydzień wszystkie __ %, Fable __ %, C: __ GB (17:19: 499 GB).

PIERWSZE KROKI:
1. CronList → crony :07/:17/:47 i cron pomiaru budżetów (00:33).
2. git worktree list, artifacts/live/*.md, `*.status` łańcuchów (exit= per krok!), sloty; zbierz raporty agentów (world2, int-ui).
3. Scal w kolejności:
   a. world2-s23 (robocopy derived 25 kafli najpierw!);
   b. int-ui-s23 (#163 #166 #162);
   c. world3 — jedna przebudowa, potem robocopy derived;
   d. pełny build Windows d67-full ze ŚWIEŻYM derived (win-build-0261 → junction);
   e. pomiar budżetów PC (D83) na bezczynnej maszynie.
4. Daj właścicielowi exe korytarza (`Kamion-korytarz.cmd`, w razie crasha `-force-d3d11`) + docs/owner/JAK-GRAC-PC.md.
5. Zlecenia: model naczepy (truck-artist), DrivingLab z prawdziwym modelem i HUD PC, diagnoza D3D12 wg RESEARCH; przejrzyj PR chmury D r10 i sesji P r7.
```
