# Prompt startowy — sesja 24 (SZKIC; wklej do nowej sesji Claude Code w C:\Users\matma\Documents\Claude\kamion)

> Szkic przygotowała sesja chmurowa P r3 (16.11 ok. 10:3x) z `HANDOVER.md` (blok SESJA 23 do wpisu „[16.11 10:19 :17]”) i listy
> otwartych PR na GitHubie. **Sekcje oznaczone „DO UZUPEŁNIENIA PRZEZ LIDERA” lider wypełnia na końcu s23** (sha main, stan
> agentów i łańcuchów, limity, dysk). Wszystko, co niżej nie ma takiej etykiety, to stan z 16.11 ~10:30 — przed wklejeniem
> sprawdź, czy się nie zmieniło.

```
Kontynuujesz projekt Kamion (realistyczny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1 → DK65 → Knyszyn) w C:\Users\matma\Documents\Claude\kamion. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion. Komunikacja po polsku. Godziny z zegara systemowego (Get-Date).

NAJWAŻNIEJSZE ZMIANY s23 (15.11 22:5x → 16.11):
- Windows = platforma główna (D73/ADR 0260); CLAUDE.md „Komendy” ma Windows na górze (build-windows.ps1, pc-metrics.ps1, package-windows.py), telefon 🔒 odroczony.
- Starty regionów naprawione (spawn-fix-0262 scalony 2×; rendery 20/20 + 7 zrzutów z exe). Bezpiecznik startu v2 = #141 (ADR 0277) w integracji.
- PR chmury H r1–r2 (#129–#136) scalone przez int-pc-s23: tiery PC (dev RTX 5070 1920×1080: Low 535 / Medium 379 / High 334 / Ultra 194 fps — maszyna dev ≠ referencja), menu ustawień PC, pad/klawiatura, kierownica FFB, HUD PC, dystrybucja zip (ADR 0271).
- Rondo Knyszyn DK65×Tykocka: tryb „rondo kompaktowe” (roads/compact_roundabout.py), nowy jasny materiał `apron_paving_light` (D75), `island_sand`; dopracowanie = #144 (ADR 0274).
- Linia 38 + znaki dojazdu do przejazdów (ADR 0268) + pobocza dróg zamiejskich (ADR 0272, #138) + JEDNA regeneracja 17 kafli — scalone (rail-dk65-s22, feb542757). Start dk65-06 za rondem (decyzja właściciela).
- MODEL AGENTÓW: **nowi agenci na Opusie** (limit tygodniowy Fable się kończy — polecenie właściciela 16.11; Fable 58 % o 10:19). Fable zawieszał się przy długim czekaniu na łańcuchy — domykanie zawsze Opus.

PRZECZYTAJ NAJPIERW:
- HANDOVER.md: blok „SESJA 23” — wpisy chronologicznie, najnowsze tuż nad linią „Ostatni przydzielony ADR” (**0279**; zakresy s23: 0262 spawn-fix, 0268 znaki przejazdów, 0269–0271 chmura H r2, 0272–0273 chmura D r4, 0274–0275 chmura D r5, 0276–0277 chmura H r3, 0278 plan mapy + 0279 audyt oznakowania = chmura D r6). Następny wolny: **0280**.
- CLAUDE.md, docs/owner/AGENT-RULES.md, docs/owner/S20-AGENT-PREAMBLE.md, docs/owner/S20-PR-REVIEW-BRIEF.md;
- docs/11_DECYZJE_WLASCICIELA.md (D63–D75) i docs/owner/OPEN-DECISIONS.md (jeśli chmura D r6 D23 już scalona);
- docs/reports/PR-TRIAGE-2026-11-16-s23.md, docs/reports/REVIEW-2026-11-16-s23-code-H3.md, docs/reports/ANALYSIS-2026-11-16-regionpacks-pc.md (gałąź analysis-regionpacks-s23, jeśli jeszcze nie w main);
- artifacts/live/*.md (stan każdego agenta z NASTĘPNYM KROKIEM; kopie w main, oryginały w worktree).

DECYZJE WŁAŚCICIELA s23 (wpisane w HANDOVER; nie pytać ponownie):
- D75: rondo Knyszyn — nowy jasny materiał kostki z fakturą; przejezdność (pierścień 5,0 m + opaska 3,2 m) przed wiernością zdjęciu.
- Nowi agenci na Opusie zamiast Fable (limit Fable).
- Pierścień #115 (Mońki/Tykocin/Jaświły) wchodzi do d67-full.
- Start dk65-06 za rondem.
- Sprzątanie dysku (08:4x): usunięte rendery pośrednie 41 kat. 30,9 GB (lista artifacts/cleanup-s23/deleted-renders-s23.txt), worktree verify-s21-ui (gałąź na origin), Library Bee/Android + PlayerDataCache/Android w main i int-dk65 (30 GB). Ekran przypisań pada zostaje (wskaźnik/Esc).
- Praca do 90 % limitu 5 h: wznawiać agentów, sprawdzać prace chmur (D/H/P, Codex) i scalać; od 90 % — bez nowych, działający kończą krok (commit WIP + push + live); decyzje do właściciela → lista w HANDOVER.

ZASADY (z s22–s23, obowiązują):
- najwyżej 5 lokalnych agentów naraz; nowi na Opusie; agentom ZAWSZE każ uruchamiać długie kroki ODŁĄCZONE (Start-Process) i od razu kończyć turę (watchdog 10 min); po każdym kroku commit WIP + push + live;
- sloty maszyny: `heavy` (build_world/regeneracje) i `unity` (import, EditMode, buildy) — `scripts/unity-slot.ps1`, `-Slot` w skryptach; jeden proces Unity na katalog; PHONE_RUN blokuje Unity (telefon drugorzędny);
- łańcuchy w tle: **nie ufać znacznikom .done / „CHAIN DONE”** — czytać `exit=` każdego kroku w `*.status`; exit=-1073741502 (0xC0000142) = proces nie wystartował (np. przy zamykaniu sesji) → ponowić odłączonym Start-Process;
- nie zabijaj działających procesów; skończonych agentów nie wznawiaj bez zgody właściciela; martwych przejmuj nowymi w tym samym worktree TYLKO za zgodą (AskUserQuestion);
- procedura usuwania worktree: (1) robocopy artifacts (pełne PNG VQA, raporty) do main, (2) odpiąć junctions Data/raw ([System.IO.Directory]::Delete na każdym ReparsePoint w <wt>\Data\raw — NIE rekurencyjnie), (3) sprawdzić, że main\Data\raw jest cały, (4) git worktree remove --force, (5) C: do HANDOVER; NIE usuwaj win-build-0261 (Library Win64 — buduj PC stamtąd);
- `Data/raw/derived/knyszyn` jest wspólny przez junction z worktree Codexa knyszyn-rynek-0227 — nie przebudowywać knyszyna równolegle;
- generated/* przy scalaniu: wersja z JEDNEJ wspólnej regeneracji po scaleniu (nie łatać ręcznie), overrides.yaml = suma bloków;
- crony: :07 (ZIP-y w Downloads), :17 (agenci, dysk, kolejka, HANDOVER+push), :47 (PR-y) — najpierw CronList;
- decyzje właściciela zawsze klikalne (AskUserQuestion), obrazy najpierw (SendUserFile);
- zakazy: Google Maps/Street View/Earth/3D Tiles; marki i logo w grze i w nazwach zasobów; zdjęcia właściciela tylko jako referencja;
- ciągły zapis: po każdym scaleniu/starcie/końcu agenta aktualizuj HANDOVER i push.

SCALONE W s23 (z HANDOVER): c-regen-s22 (1ab7e9b63; #95 #120), spawn-fix-0262 kod (5f51007ee) + r2 (3c4979f90), #137 recenzje H, int-pc-s23 (3e9ef52fc; #129–#136), c-regen2-s23 (e4fad6868; #109 #110 #111 #122 #124 #125 + fix magenty płotu), lamp-test-s23 (dbfe8c60e), int-dk65-s22 (5824464bd; #97 #98 #101 + rondo kompaktowe), fidelity C (872af4846, 2103926bc), pc-shadows-s23 (4bad31dae), rail-dk65-s22 (feb542757; #102 + 0268 + #138), sesja P r1 (docs-windows-s23, pr-triage-s23, licenses-s23) + #85, #140 recenzje nocnych scaleń (d4ea01a16).
DO UZUPEŁNIENIA PRZEZ LIDERA: scalenia po 10:19 (build-s23? c-regen3? world2? łańcuch H r3? sesja P r2/r3?), sha main na koniec s23: ________

OTWARTE GAŁĘZIE / WORKTREE (stan 10:19 — DO UZUPEŁNIENIA PRZEZ LIDERA: aktualny stan, exit= ostatnich kroków):
| worktree / gałąź | agent | stan 10:19 | następny krok |
|---|---|---|---|
| win-build-0261 / build-s23 | int-pc (Opus) | reimport 21 regionów Win64 ~10 min/region (≈ 3,5 h, exe ok. 14:00), potem EditMode + build d67-full + zrzuty (rondo, knyszyn-s Low, tykocin, dk65-06, Ełcka) | exe dla właściciela; potem integracja H r3 (#113 → #118 → #117 → #141 → #142) w tym worktree |
| c-regen3-s23 (origin @ e2a4282bd) | Fable→Opus | #123 typology-fix-s23 + #119 + #93 `putry-ring-0198b-rebased` + fix płotu `ShaderHasError` (RegionImporter:464, InstanceImporter:679) → przebudowa C + Dojlidy; łańcuch od 10:09 | czekać na `CHAIN END|STOP`, budżet C < 2 M, VQA Low overcast + High clear, raport → scalić (zamyka #123 #119 #93) |
| world2-s23 (origin @ 6e0fc8f25) | Fable→Opus | #115 pierścień + #143 szwy (7 kafli), prep: ingest + build_region 18 kafli | budowa pierścienia, d67-full, VQA, testy (`test_dk65_seam_knyszyn_0233` czerwony w main — naprawia #143) |
| typology-fix-s23 (91490b0fe) | — (DONE) | wchodzi do c-regen3 | usunąć worktree po scaleniu c-regen3 |
| knyszyn-rynek-0227 (#139) | Codex (wstrzymany, limit) | FIX (REVIEW-…-139.md: P0 fidelity C stale, generated knyszyn nieaktualne, targowica bez budżetu/renderów; P1 43 pliki w artifacts/, moduły knyszyn_*_0227 piszą „skipped” do QA wszystkich regionów); wiaty z ortofoto, nie z OSM way 704368699 | przejęcie lokalne TYLKO za zgodą właściciela, po scaleniu rail (zrobione) — czyszczenie artifacts/, bramkowanie QA, fidelity C, przebudowa knyszyn, budżet + VQA |
| codex-refs-s21 (#100) | Codex (wstrzymany) | NIE do scalenia; ostrzeżenia dla generatorów w docs/owner/GPT-BACKLOG.md | zostaje do recenzji #100 |
| knyszyn-gis-0227 | Codex | slot heavy zajęty — „wisi?” (10:19) | DO UZUPEŁNIENIA PRZEZ LIDERA: sprawdzić proces, zwolnić slot |

OTWARTE PR (16.11 ~10:30, z werdyktami):
| PR | co | werdykt / stan | następny krok |
|---|---|---|---|
| #150 map-plan-0278 | D19 plan rozbudowy mapy + 3 kafle (ADR 0278) | chmura D r6, nowy | recenzja |
| #147 signs-audit-0279 | D21 audyt oznakowania (ADR 0279) | chmura D r6, nowy | recenzja |
| #144 roundabout2-0274 | D14 rondo Knyszyn: pasy, promienie, wyspa, P-13/P-10 | chmura D r5 | recenzja → po c-regen3/world2 przebudowa knyszyn (nie równolegle z #139) |
| #143 seam-taper-0275 | D15 szwy + qa/seams.py | w world2-s23 | scalić z world2; potem zamknąć #106 (zastąpiony) |
| #142 pc-polish-0276 | H10 menu/diag, content hash, skróty | SCAL (REVIEW-…-H3) | łańcuch H r3, ostatni |
| #141 spawn-safety-0277 | H13 bezpiecznik startu | SCAL warunkowo, **P1**: pętla scen `GameBootstrap.cs:173-174` (`-scene` czytane przy każdym wejściu do Boot) → statyczna flaga „argument użyty” + test | FIX przy integracji |
| #139 knyszyn-rynek-0227 | Codex Rynek | FIX | patrz worktree wyżej |
| #123 typology-0238 | F5 typologia | FIX → w c-regen3 (typology-fix-s23) | zamknąć po c-regen3 |
| #119 tests-hygiene-0245 | G3 testy bez Data/raw | po D16 → w c-regen3 | zamknąć po c-regen3 |
| #118 perf-loop-0244 | zero GC pętli jazdy | SCAL warunkowo (asmdef: `Unity.InputSystem` w Game.Tests.EditMode — decyzja lidera TAK) | łańcuch H r3 |
| #117 controls-0243 | kierownica 270/900°, lusterka (D70) | SCAL | łańcuch H r3 |
| #116 g3-poses-0246 | zrzuty 42 póz G3 — teraz tryb `-Exe` playera Windows (P r2) | TAK po EditMode + `-Only 1-2` na Windows | `pwsh scripts/g3-poses.ps1 -Exe artifacts/win/<build>-dev/Kamion.exe -Only 1-2 -Lighting overcast` (build Development) |
| #115 ring-0231 | pierścień Mońki/Tykocin/Jaświły | w world2-s23 (decyzja: do d67-full) | scalić z world2 |
| #113 jackknife-0228 | ogranicznik przegubu kabina–naczepa | SCAL warunkowo (P2: ADR „0,61 mm” vs 71–79 kN w 1. kroku; wygładzanie FFB) | łańcuch H r3, pierwszy |
| #112 regionpacks-0234 | paczki AssetBundles (0234/0273) | **PRZEROBIĆ** (ANALYSIS-…-regionpacks-pc.md): nie scalać osobno; nowy PR z `streaming-0235` (zawiera #112; konflikt z main tylko DrivingLabBootstrap.cs), paczki uśpione na PC | po łańcuchu H r3 (wspólne pliki); reimport `_Tile`, pomiar `-stream 1` |
| #106 seams-0224 | stare QA szwów | ZAMKNĄĆ po #143 | — |
| #100 codex-refs-s21 | research Codex | NIE (wstrzymany) | — |
| #93 putry-ring-0198b | wyspa Putry | scalamy gałąź `putry-ring-0198b-rebased` w c-regen3 | zamknąć po c-regen3 |
| #92 P16 lampy (research) | M59-FIX r2 plan B (P r2) | TAK (pkt 4 jawnie niespełniony; #55 już zamknięty) | scalić |
| #79 lights-0197 | światła R148/R48 | SCAL po weryfikacji: eksport naczepy (Blender) + BuildBatch + EditMode + rendery z playera Windows | po łańcuchu H r3 (TruckLights) |
DO UZUPEŁNIENIA PRZEZ LIDERA: PR otwarte/zamknięte po 10:30 (sesja P r3: physics-validation-s23, player-guide-s23, start-prompt-s24; chmura D r6: D20 CI gis, D22 profil build_world, D23 OPEN-DECISIONS, D24 indeks ADR).

CHMURY (DO UZUPEŁNIENIA PRZEZ LIDERA: co oddane do końca s23):
- D r6 zlecona 10:0x (docs/owner/CLOUD-D6-PROMPT-S23.md, agenci Opus): D19 0278 (#150), D20 CI gis zielone (LFS forest), D21 0279 (#147), D22 profil build_world (analiza), D23 docs/owner/OPEN-DECISIONS.md, D24 higiena statusów ADR + indeks. Zablokowane dla chmury: kafle C/Dojlidy/DK65/Knyszyn/pierścień, roads/* (poza D14), game/**.
- H r3 oddana (#113 #117 #118 #141 #142), recenzja REVIEW-2026-11-16-s23-code-H3.md — integracja lokalna.
- Sesja P: r1 scalona; r2 (#92 FIX, #116 -Exe, analiza #112) i r3 (walidacja fizyki, instrukcja gracza PC, ten szkic) — DO UZUPEŁNIENIA PRZEZ LIDERA: scalone?

CZERWONE / ZNANE W MAIN:
- `test_dk65_seam_knyszyn_0233` (szew dk65-11|knyszyn-s 0,26 m/stronę) → naprawia #143 w world2.
- 3× stan wspólnego Data/raw C w pytest gis (środowiskowe).
- `test_gate3_meta.py::test_evidence_apk_info_legacy_and_dirty` (znany od s22).
- ADR 0269 otwarte: log cieni 60/100 m vs realne 30 m, las/HLOD bez cieni, koszt GTX 660 ESTIMATED, crash przy zamykaniu 1/5 (dump artifacts/pc-shadows-s23).
DO UZUPEŁNIENIA PRZEZ LIDERA: wynik pełnego EditMode/pytest gis na końcu s23.

LIMITY I DYSK (DO UZUPEŁNIENIA PRZEZ LIDERA): 5 h __ % (reset __), tydzień wszystkie __ %, Fable __ %, C: __ GB.

PIERWSZE KROKI:
1. CronList → załóż crony :07/:17/:47.
2. git worktree list, artifacts/live/*.md, `*.status` łańcuchów (exit= per krok!), sloty; zbierz raporty.
3. Scal gotowe w kolejności: build-s23 (exe właściciela) → łańcuch H r3 (#113 → #118 → #117 → #141 z P1 → #142; konflikt BootMenu.cs = wersja #142 + etykieta komunikatu #141 pod m_Block) → c-regen3-s23 → world2-s23 (+ #143) → #144 (przebudowa knyszyn, nie równolegle z #139) → streaming-0235 (nowy PR, ANALYSIS) → #79.
4. Daj właścicielowi exe (Kamion-okno.cmd / Kamion-knyszyn.cmd) + instrukcję docs/owner/JAK-GRAC-PC.md (sesja P r3).
5. Przejrzyj PR chmury D r6 (#147 #150 + reszta), scal SCAL, FIX odeślij; zamknij zastąpione (#106 po #143; #93/#119/#123 po c-regen3) — zamykanie za zgodą właściciela.
```
