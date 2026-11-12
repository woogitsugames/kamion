# GPT-BACKLOG — przekazania sesji GPT (Codex) → zadania dla agentów Claude

Aktualizacja: **2026-11-12 16:30 CET** (sesja 12, agent zbierający; main `39068ac2c`).
Źródła: `docs/owner/gpt-handovers/*.md` (kopie 1:1), `docs/owner/GPT-FEEDBACK-S10.md` (s12), `docs/reports/visual/REVIEW-2026-11-12-s12-*.md`, D51 w `docs/11_DECYZJE_WLASCICIELA.md`.
Numeracja sesji wg `docs/owner/GPT-TASK-05-24H.md`: 1 light, 2 vegetation, 3 asphalt, 4 sbs, 5 cab, 6 truck, 7 landmarks, 8 furniture, 9 edge, 10 life.

## Zebrane przekazania (10)

| Sesja | Dziedzina / runda | Kopia | Gałąź @ HEAD (16:29) | Stan rundy |
|---|---|---|---|---|
| 1 | light r6 | `gpt-handovers/light-r6.md` | `gpt-light-r6` @ `48f55d254` | wstrzymana; brak REPORT; kod Assets niezmieniony; 16:34 proces zakończył się sam, zmiany generatora tylko w worktree (bez world checkpoint) |
| 2 | vegetation r4 | `gpt-handovers/vegetation-r4.md` | `gpt-vegetation-r4` @ `fc398161b` | wstrzymana; REPORT-DRAFT; **NIE SCALAĆ** |
| 4 | sbs r4 | `gpt-handovers/sbs-r4.md` | `gpt-sbs-r4` @ `e2ce37d6e` | wstrzymana; REPORT-DRAFT |
| 5 | cab r4 | `gpt-handovers/cab-r4.md` | `gpt-cab-r4` @ `9b474d04e` | wstrzymana; REPORT-DRAFT, „nie gotowa do scalenia” |
| 6 | truck r4 | `gpt-handovers/truck-r4.md` | `gpt-truck-r4` @ `b52587089` | wstrzymana; nowy FBX nie wygenerowany |
| 7 | landmarks r4 | `gpt-handovers/landmarks-r4.md` (z `HANDOFF.md`) | `gpt-landmarks-r4` @ `1f56c8471` | PARTIAL; REPORT.md = raport zatrzymania, nie zamknięcia (brak testów) |
| 8 | furniture r3 | `gpt-handovers/furniture-r3.md` | `gpt-furniture-r3` @ `b679ed350` | wstrzymana; brak REPORT |
| 9 | edge r6 | `gpt-handovers/edge-r6.md` | `gpt-edge-r6` @ `a84f8c3d0` | wstrzymana; produkcja = baza (diff pusty) |
| 3 | asphalt r3 | `gpt-handovers/asphalt-r3.md` | `gpt-asphalt-r3` @ `eb9c5fc42` | wstrzymana WIP; brak kandydata produktu i REPORT |
| 10 | life r5 | `gpt-handovers/life-r5.md` | `gpt-life-r5` @ `4e685b6ea` | wstrzymana; palety niezaaplikowane |

Wszystkie 10 sesji (1–10) zakończone na polecenie właściciela (limit tygodniowy); każda runda wstrzymana, żadna nie wznawia się sama.

## Do scalenia przez lidera

| Gałąź | SHA | Stan | Uwagi |
|---|---|---|---|
| `gpt-light-r5` | `00e03bb14` | REPORT gotowy (`artifacts/light-r5/REPORT.md`), niescalona | Batch E: **SCAL warunkowo** — po merge usunąć z runtime `KamionOpaqueTone`/`TEXTURE3D(_KamionOpaqueGradeLut)`/include `Color.hlsl` z `KamionAtmosphere.hlsl`, `KamionMixFog` → `KamionTone(c)`, `Sky.shader:219` jak main; przenieść do include'a labu (`REVIEW-2026-11-12-s12-gpt-batch-e.md` §2). Albo scalić bez zmian po pomiarze A16. Light r6 nie wykonał tej poprawki (Assets niezmienione). |

Żadna runda z dzisiejszych przekazań (r4–r6) **nie** jest gotowa do scalenia. Stare niescalone gałęzie (`gpt-car-paint`, `gpt-firestation-r7`, `gpt-tint-gamma`, `gpt-truck-paint`, `gpt-vegetation-r2`, `gpt-light-r12`, `codex/s10-coordination`) to archiwalne strumienie S10 — wg HANDOVER skonsumowane przez późniejsze rundy/scalenia (UNVERIFIED per gałąź; nie scalać bez sprawdzenia).

Opcjonalnie (lider, małe): z każdej wstrzymanej rundy można wyciągnąć gotowe narzędzia/kandydatów do agentów Claude przez `git checkout <gałąź> -- <ścieżka>` — ścieżki podane w zadaniach niżej.

## Zadania do przejęcia przez agentów Claude

Priorytet: 1 = blokery bramki 3 (D51 rozpoznawalność), 2 = wydajność A16 Low/budżety, 3 = jakość wizualna / anti-slop P1, 4 = reszta.

### Priorytet 1 — D51

**1. SBS r4: domknięcie dowodu G3 (kompozycja, audyt, ocena C) na aktualnym main** — sbs (sesja 4)
- Źródło: `gpt-handovers/sbs-r4.md` §„Potwierdzone wyniki r4”, §„Nowszy main”, §„Co zostało do zamknięcia r4”.
- Opis: r4 wyrenderowała 168 raw (42 kamery × 4 stany) na bazie sprzed ADR 0130; świeży D51 Low-overcast = **FAIL: 13 rozpoznawalnych / 11 częściowych / 1 nie**. Przegląd C częściowy (20/68 raw, 5/17 źródeł). Nowa runda ma scalić main (pozy 0130), wygenerować świat i wyrenderować 4 stany; P1 narzędzie `sbs-gate3.ps1` (ComposeOnly re-entrant, guard SHA — już w gałęzi), P2 pitch B150280.
- Stan: gałąź `gpt-sbs-r4`; narzędzia `tools/refs/sbs_gate3.py` (`--inputs`), `scripts/sbs-gate3.ps1`, `artifacts/sbs-r4/audit_baseline.py` (nieuruchomiony), `run-heavy.ps1`, `deliver.ps1`, rejestr `sbs_recognition.json`. Kompozycja (PID 70780) może jeszcze skończyć w worktree.
- Agent: **Opus** (kalibracja/QA). Rozmiar: **M**.
- Zależności/konflikty: zależy od scaleń 0127/0128/0129/0133/0123 (zmieniają świat) — renderować po nich. Nie zmieniać póz 0130 bez recenzji. Wysokie ryzyko konfliktu z narzędziem SBS lidera (`scripts/sbs-gate3.ps1`) — przejąć zmiany narzędzi przez lidera.

**2. Edge r6: apron NW (statyw pod gruntem) + pierścień 280→220 m + zapory końca mapy** — edge (sesja 9)
- Źródło: `gpt-handovers/edge-r6.md` §„Ustalenie kamery NW”, §„Kandydaty”.
- Opis: „szara podłoga” przy NW to najpewniej kamera diagnostyczna 0,397 m pod NMT (hipoteza, niepotwierdzona renderem). Kandydat: zastąpienie pierścienia apron 280 m → 220 m bez wzrostu budżetu (testy `WorldEdgeApronTransitionTests.candidate.cs`, Red/Green nie wykonane). P1 batch E: biało-czerwone zapory końca mapy na osiach widoku — wymaga koordynacji z drogami/runtime (`BOUNDARY-P1.md`). B9 bloki na horyzoncie to obiekty w regionie (`artifacts/edge-r3/next-round-review/near-city-ownership.json`).
- Stan: produkcja r6 = baza; kandydaci i narzędzia w `artifacts/edge-r6/` (`test-apron.ps1`, `run-after.ps1`, `audit_contact.py`, …), STOP.requested aktywny.
- Agent: **Fable world-builder** (apron/zapory) . Rozmiar: **M**.
- Konflikty: zapory/końce dróg ↔ **0123 węzły** i drogi lidera; B9 ↔ **0132 zabudowa r9**. Średnie ryzyko.

**3. Landmarks r4: domknięcie iglaków remizy (model B) + kominy EC/głowice** — landmarks (sesja 7)
- Źródło: `gpt-handovers/landmarks-r4.md` §„Runda r4 — stan modelu B”, §„Czego brakuje”.
- Opis: model B (nieregularne rdzenie 3 iglaków) to częściowa poprawa; Low nadal zbyt pełny stożek. 244 PNG after-b gotowe, **nieprzejrzane**; brak pytest/GIS/EditMode. Otwarte: kominy EC (powierzchnia, głowice), pozycja rury pod pomostem; z kalibracji póz (s12 14:19) portal Andersa ~27 % za niski (przekazany do 0127).
- Stan: `gpt-landmarks-r4`, `artifacts/landmarks-r4/{analyze.ps1,final-python.ps1,final-editmode.ps1}`, wariant C tylko analiza (`proposal_c.py`).
- Agent: **Fable world-builder** (geometria). Rozmiar: **S–M**.
- Konflikty: remiza/kominy — niskie; wiadukt pod pomostem ↔ **0133 latarnie Putry** (pomost) — uzgodnić. Kominy EC za pierzeją ↔ **0129**.

### Priorytet 2 — wydajność A16 Low / budżety

**4. Furniture r3: czerwona wiata z Mapillary — pomiar budżetu kandydata 3 (paleta jednego slotu)** — furniture (sesja 8)
- Źródło: `gpt-handovers/furniture-r3.md` §„R3: co zmieniono”, §„Czego jeszcze nie ukończono”, §„Końcowy potwierdzony stan”.
- Opis: iteracja 2 przekroczyła **Low +3 draws** (`g3b-eye-s1482`); kandydat 3 scala nieprzezroczyste części w jeden slot palety (keyword `_FURNITURE_SHELTER_PALETTE` w `WorldSurface.shader`). After3 wygenerowany (64 GLB, 0 zmian chronionej geometrii), ale import i 236+118+8 renderów nie wykonane. Kryterium: Low draws ≤ 0, tris ≤ +2 %.
- Stan: `gpt-furniture-r3` @ `b679ed350` (produkty `816d1c55f`), helpery `artifacts/furniture-r3/24h/{unity-step,heavy-step,candidate2}.ps1`. Python estymator roads nie zna nowej rodziny (UNVERIFIED widoczność).
- Agent: **Opus rendering-perf** (shader keyword + budżet). Rozmiar: **M**.
- Konflikty: nowy keyword w `WorldSurface.shader` ↔ **0136 regresja GPU A16** (ten sam shader/warianty) — wysokie; przystanek przy G3-B ↔ **0127**. Puścić po 0136.

**5. Light r6: noc (plamy pod latarniami, głowice) + pas „smogu” na horyzoncie** — light (sesja 1)
- Źródło: `gpt-handovers/light-r6.md` §„Ważne ustalenia”, §„Przygotowane materiały”; batch E §2.
- Opis: P1 szaro-beżowy pas przy horyzoncie (SkyModel daje osobny kolor horyzontu; sprawdzić słońce 9/25/42/60°). P0 noc: Low 4 pule / 0 point, głowica lamp ciemna, w 15 kamerach brak sondy pod lampą w kadrze. R6 przygotowała tylko plany i niekompilowane prototypy (`horizon-prototype/`, `horizon-triage.json`, `night-pool-ablation.json`, `baseline.json` 1090 obrazów); Materials gotowe, World w kolejce, dalsze fazy zablokowane STOP.
- Agent: **Opus rendering-perf**. Rozmiar: **L**.
- Konflikty: `KamionAtmosphere.hlsl`/`Sky.shader` ↔ **0136** (koszt GPU) i ↔ scalenie light r5; lampy Putry ↔ **0133**. Najpierw scalić light r5 z poprawką lidera.

### Priorytet 3 — jakość wizualna / anti-slop P1

**6. Truck r4: regularna przednia tarcza koła (P1 „zabawkowa felga”)** — truck (sesja 6)
- Źródło: `gpt-handovers/truck-r4.md` §„R4 — dokładnie co jest gotowe”, §„Najbliższe kroki”.
- Opis: wariant za flagą `--regular-front-wheels` (domyślnie False): 10 otworów, płaski dekiel 40 mm, 10 nakrętek w Low. Native smoke, bake i FBX **nie uruchomione**; budżet LOD2 (limit 17 900) niezmierzony. Po akceptacji włączyć flagę domyślnie.
- Stan: `gpt-truck-r4` @ `b52587089`; `tools/blender/truck/exterior/{wheel_disc.py,wheel_disc_blender.py,chassis.py,a6_export.py}`, `artifacts/truck-r4/{baseline-captures.ps1,regenerate-exterior.ps1,INTEGRATION-PLAN.md}`. Przygotowanie (PID 54020) jeszcze żyło o 16:30.
- Agent: **Fable truck-artist**. Rozmiar: **M**.
- Konflikty: niskie (ciężarówka); 0134 truck-feel już scalony — fizyka kół bez zmian.

**7. Life r5/r6: P1 osobówek i felg placowych zamiast palet** — life (sesja 10)
- Źródło: `gpt-handovers/life-r5.md` §„R5”, końcowe „Otwarte P1”; batch E §3.
- Opis: z uwag r4 wykonano 0/5: czarne auto = szary metalik, szum płatków High, twardy prostokątny cień pod autem, czysty tył; opona 10-kąt (tris przenieść z otworów felgi do obrysu ≥ 20–24 seg.). Palety EPAL (`pallet-candidate.py`, `PALLET-DESIGN.md`, test `test_pallet_openings.py`) — szkic niezaaplikowany. Main miał 2 czerwone `CarPaintMaterialTests.DepositionChannel_*` (s12 15:37) — sprawdzić, czy naprawione.
- Stan: `gpt-life-r5` @ `4e685b6ea`; baseline capture 4 warunków zakończony (`DRAIN-RESULT.json`), diagnostyka LOD (`diagnose-lod.ps1`, `Life5PropLodProbe.cs`) nieuruchomiona.
- Agent: **Opus** (lakier/cień — rendering) + **Fable** (opona/palety — geometria). Rozmiar: **M**.
- Konflikty: `_CARPAINT` w `WorldPBR.shader` ↔ **0136**; niskie poza tym.

**8. Cab r4: czytelność legend Low + materiał „Plastic”** — cab (sesja 5)
- Źródło: `gpt-handovers/cab-r4.md` §„Runda 4”, §„Co jest zweryfikowane”.
- Opis: wybrano Low Decal 256 px, mip bias −0,75 (`cab_legend_atlas.json`) — ikony lepsze, P1 nie zamknięty; migotanie i GPU niezmierzone. Plastic (pochodna skanu Brown Leather) nadal wygląda jak tłoczona skóra; kandydaci hp03/hp06 (MaterialFine, PID 63712 zakończony — sprawdzić `material-prep/fine-verification.json`). Pasmo AO deski, podświetlenie legend nocą — otwarte.
- Stan: `gpt-cab-r4` @ `9b474d04e`; `material-variant.ps1`, `capture-0112.ps1`, `route-0112.ps1`, `LEGEND-REVIEW.md`. Przed oceną przebudować assety (ostatni BuildBatch = odrzucony eksperyment).
- Agent: **Opus** (materiały/UI kabiny). Rozmiar: **S–M**.
- Konflikty: niskie; zmiany ustawień Fold/HUD (0135) nie dotykają materiałów.

**9. Vegetation r4: berberys — kandydat D (pędy vs gładki blat)** — vegetation (sesja 2)
- Źródło: `gpt-handovers/vegetation-r4.md` §„Co jest rzeczywiście ukończone”, §„Wznowienie”.
- Opis: A/B2/C odrzucone (C: PARTIAL pokrywy, FAIL realizmu — gładki blat). D (WORKING_VALUE szerokość/pochylenie pędów) ma kod i 45 testów, bez World/importu/obrazów. Materiał berberysu to URP/Lit, nie WorldPBR (do wyjaśnienia). B8 (drzewa w pasie dzielącym) zależy od pozy 297817.
- Stan: `gpt-vegetation-r4` @ `fc398161b`; produkcja `tools/worldgen/streetscape/plantings.py` (SHA w przekazaniu), `candidate-d-probe.ps1`, `review_berberis.py`, `after-approved.ps1`. Sekwencja D (PID 57980) żyła o 16:30.
- Agent: **Fable world-builder**. Rozmiar: **M**.
- Konflikty: zieleń ↔ **0132 zabudowa r9** (wysoka zieleń, żywopłot) — średnie.

### Priorytet 4 — reszta

**10. Narzędzie VQA: High zapisuje R8 przed post** — light (sesja 1, znalezisko r5)
- Źródło: batch E §2 (1); `gpt-handovers/light-r6.md` §„Co jest ukończone”; feedback s12 14:46.
- Opis: `VisualQaRunner` używa ARGB32 także dla High → kamery kontrolne High są obcięte przed tonemapem; fotometria High = UNVERIFIED we wszystkich dziedzinach. `LightHdrQaReference` (R16Half) w gałęzi light r5 to referencja. Mała zmiana narzędzia.
- Agent: **Opus rendering-perf**. Rozmiar: **S**. Konflikty: `VisualQaRunner` używany przez wszystkich agentów — scalać poza oknami renderów.

**11. Asphalt r3: materiały placów przemysłowych poza Kwadratem + szara łata na łuku** — asphalt (sesja 3)
- Źródło: `gpt-handovers/asphalt-r3.md` §„Aktualna runda 3”, §„Dowody i narzędzia”; feedback s12 14:46 (łata), 13:45 (maska zalewki P2).
- Opis: świat post-0131 zbudowany (exit 0, 624,7 s, manifest `BF4A2C8F…`) i zaimportowany (exit 0); próba 4 kamer PCRT padła na składni wrappera (poprawione `eb9c5fc4`, nie ponowiono). Brak baseline, kandydata, testów. Otwarte P2: pętle/kropki maski zalewki, czytelność ciemnej zalewki; szara prostokątna łata na łuku (Fold) — nieustalone, czy `decal_patch`.
- Stan: `run-unity-stage.ps1`, `audit-yard-poses.ps1`, `behaton_preview` (C# niekompilowany), `DIAGNOSTICS.md` (pre-0131, nieaktualne). Proces PID 13412 (`post-world-baseline.ps1`: YardProbe → GeometryAudit → ortofoto) czekał na heavy.
- Agent: **Opus** (materiał). Rozmiar: **M**. Konflikty: `WorldPBR.shader`/`_CRACKS` ↔ **0136**; łata na łuku ↔ drogi **0123**. Wg D51 nie blokuje bramki 3.

**12. Furniture r4 (notatka): dwuramienne latarnie z Mapillary 1484379768878742** — tylko notatka `24h/next-round-observations.md`; nie ruszać `lamp_arc` Kwadratu. Konflikt z **0133**. Fable, S.

## Uwagi operacyjne

Procesy GPT pozostawione bez ubijania (odczyt 16:30; sprawdzać PID **razem z CreationDate/CommandLine**):

| Sesja | PID (start) | Co robi | Kiedy się zatrzyma |
|---|---|---|---|
| edge (9) | 46048 (14:55:44) prepare-baseline; 74364 (14:56:07) run-baseline; 65152/28720 (14:56:43) ownership/maska; 11680 (14:56:43) audit-contact. 71536/55024 już zakończone | czeka na heavy; może zrobić 1× build_world | `STOP.requested` → import kończy się kodem 75 przed Unity (`PAUSED-BEFORE-IMPORT.json`); zależne czekają na `Baseline.ready`, który nie powstanie — mogą wisieć |
| truck (6) | 54020 (13:34:24); potomkowie 78320/40584/79792 zakończeni | prepare-baseline: generator świata, potem ewentualnie materiały + import Unity pod slotem | sam kończy po imporcie; nie uruchamia captures |
| light (1) | 73184 (14:06:09) kontroler; 76116 (16:29:02) `finish-requested-stop.ps1` | BuildWorld w kolejce heavy | Fidelity zatrzymane przez `STOP-REQUESTED.txt` (kod 130); 76116 zapisze `STOP-COMPLETED.json` + robocopy |
| sbs (4) | 70780 / 68916 / 59180 (15:02:07) | `compose-all.ps1` — 4 stany, każdy osobny heavy | sam, po `composition-completed.json`; bez Unity |
| vegetation (2) | 60052 / 57980 / 64772 (15:15:16–17) | `green-d-and-world.ps1`: 45 testów → build_world D → kolizje | sam; bez Unity/importu |
| cab (5) | 63712, 70644 — **zakończone** (16:29:36 status finished, `handoff-final-state.json`; kopia do main 769 plików) | MaterialFine hp03/hp06 | sprawdzić receipt `job-MaterialFine-*.json` i `fine-verification.json` (PASS wymagany, samo finished nie wystarcza) |
| life (10) | 72932 — **zakończony** 16:27 (kontrolowany STOP, `DRAIN-RESULT.json`) | — | — |
| furniture (8) | brak aktywnych (`safe-stop-proof.json`) | — | — |
| landmarks (7) | brak aktywnych (`shutdown-process-check.json`) | — | — |
| asphalt (3) | 13412 (`post-world-baseline.ps1`) | YardProbe → GeometryAudit → opcjonalna ortofotomapa, heavy | sam zwalnia slot, zapisuje WIP/STATUS; bez Unity |

- Te procesy zajmują/oczekują **slotu heavy** (FIFO) — konkurują z agentami Claude (0123/0127/0128/0132). Nie zwalniać cudzych slotów, biletów ani `PHONE_RUN`; nie używać Priority dla nich.
- Blokady STOP (nie usuwać — usuwa tylko sesja GPT po wznowieniu przez właściciela): `gpt-edge/artifacts/edge-r6/STOP.requested`, `gpt-furniture/artifacts/furniture-r3/24h/STOP_REQUESTED`, `gpt-life/artifacts/life-r5/STOP-REQUESTED.json` (+`STOP-DRAINED.json`), `gpt-light/artifacts/light-r6/STOP-REQUESTED.txt`.
- Nie ruszać: worktree `gpt-*` (brudne celowo: cab 5 plików, sbs 7, vegetation 7 — kopie w `preserved-world-state/`, `pause-generated/`, `owner-pause-backup-20261112/`), nie przełączać gałęzi, nie `git add -A`/reset, nie kasować `Data/raw/derived`. Kopie artefaktów w main (`artifacts/<dziedzina>-rN/`) to migawki z chwili przekazania — autorytatywny stan w worktree.
- Zadanie przejmowane przez Claude: nowa gałąź od main + `git checkout gpt-<…>-rN -- <ścieżki>` (nie merge całej gałęzi WIP z generated). Wszystkie liczby GPU A16 w przekazaniach = niezmierzone.

## s16 (2026-11-12 23:5x, lider)
- **Codex gpt-s16** (`docs/owner/CODEX-S16-12H.md`): r1 ADR 0153 LOD1/LOD2 aut w toku — baseline 114 kamer × 4 warunki, regeneracja B → import after; sha `0f3b14ef6`; gotowe do recenzji: NIE. Przekazanie: `artifacts/gpt-s16/PRZEKAZANIE.md`.
- **ChatGPT 6 Pro G1–G10** (`docs/owner/GPT-PRO-RESEARCH-01.md`) zlecone; wyniki: ZIP → `research/gptpro/` albo gałęzie `gptpro/*` (brak na 23:5x).

## s16 :07 (2026-11-13 00:4x)
- **ChatGPT 6 Pro:** oddane na gałęziach: **G2** `gptpro/2-next-regions` (38 plików), **G3** `gptpro/3-s8-signs` (187 plików). Gałęzie G4, G6, G7, G8, G9 utworzone, ale **puste** (sesje padły z błędem). G1, G5, G10 — brak. Do przeglądu lidera: G2, G3 (licencje, współrzędne, wyrywkowo 20 %). Pozostałe 8 zleceń → rano przydzielić innym (priorytet G10, G1, G7, G5).
- **Codex gpt-s16 r1** (0153 LOD aut): render after High-overcast, EditMode exit 0; recenzja otwarta; gotowe: NIE.
