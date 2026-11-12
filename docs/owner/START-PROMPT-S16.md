# Prompt startowy — sesja 16 (przejęcie po s15)

Skopiuj całość poniżej do nowej sesji Claude Code (zakładka Code, katalog `C:\Users\matma\Documents\Claude\kamion`).

---

Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Przejmujesz pracę po sesji 15, którą zakończył limit. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj, w tej kolejności:**
1. `HANDOVER.md`, górny blok „KONIEC S15” i sekcja „Stan na żywo (s15)”.
2. `artifacts/live/fold-flicker.md` i `artifacts/live/putry-andersa.md` — najświeższy stan dwóch agentów w toku (sha, NASTĘPNY KROK jako komenda, gotowość).
3. `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/11_DECYZJE_WLASCICIELA.md` (D49–D56).
4. Recenzje s15: `docs/reports/visual/REVIEW-2026-11-12-s15-0141.md`, `docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md`.

Pamięć projektu: `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md` (nowe: `project-other-vehicles`, `project-windows-port`).

**Na starcie:**
1. **Limit:** `get_usage`. Reset 5 h był 13.11 01:20. Ustaw CronCreate: **:17** (limit, wolne miejsce na C:, live → scalenia → usunięcie worktree → HANDOVER → push), **:47** (PR-y Mistrala), **:07** (przekazania GPT).
2. **Maszyna:** `(Get-PSDrive C).Free` (koniec s15: ~840 GB); watchdog `artifacts/logs/ops-watchdog.log` + proces `pwsh … ops-watchdog.ps1` (nie dubluj, nie zabijaj); `pwsh scripts/unity-slot.ps1 -Status` i `-Pool heavy`; `artifacts/locks/PHONE_RUN` vs `tasklist`; `adb devices -l` (A16 RFGL34SJYDZ był offline od 22:09 — może trzeba poprosić właściciela o przełożenie kabla; Fold RFGL80RXBPZ podłączony).
3. **Procesy agentów:** `Get-CimInstance Win32_Process` z `worktrees\fold-flicker` / `worktrees\putry-andersa` — nie dubluj żywych zadań w tle. Wznów agentów z ich plików live (0152 Opus, 0146 Fable).

**Kolejność pracy s16:**
1. **0152 fold-flicker** (Opus): dokończ pomiary (Fold High/30 i Ultra/60 z nowym kodem; A16 Low regresja po przełożeniu kabla) → przegląd → scal. Najważniejsze dla właściciela: „napierdzielający obraz” (sprężyna głowy w `CameraRig.UpdateCab`, fix pod-krokami), błędy odbić na Ultra, tier Folda (ekran 5,65 Mpx, renderScale 1,0 + MSAA 4x). Po scaleniu: czysty APK dla właściciela.
2. **0146 putry-andersa** (Fable): dokończ wg live → visual-critic D51 (kadry 494288, 810896, portal Andersa) → scal.
3. **Mistral r4** (agent Opus, gałąź `mistral-r4-int`, wzór: integracja r3): PR #21 (limity ciężarówki), #22 (HUD bez TMP — kompilacja + pomiar GC.Alloc), #23 (pasy ruchu), #24 (znaki + concrete_pole), #25 jeśli jest (M25 P-11). #21 i #23 oba zmieniają format KRTG na v2 → połączyć. Komentarze po polsku na PR, raport `docs/reports/REVIEW-2026-11-13-s16-mistral-r4.md`.
4. **Jedna integracja świata** (po scaleniu 0146): `build_all` → `build_world` → `export-route` → `fidelity/run.py` → `navgraph/build_route_graph.py` → `import-region` → `ImpostorTrimBake.RunBatch` → testy (pytest gis, EditMode) → kamery kontrolne → `pwsh scripts/sbs-low-pairs.ps1 -Before artifacts/sbs-poses-r2/after` → przeocena `sbs_recognition.json` (494288, 482392, 320326, 297817).
5. Krytyk D51 („czy kierowca rozpozna to miejsce?”) → czysty APK Low → gate3 na A16 (A+B) → pakiet zdjęcie | render dla właściciela (najpierw obrazy, potem klikalna akceptacja).
6. Otwarte do przydzielenia: LOD1/LOD2 aut (A16 brakuje ~0,7 ms, world-builder), zieleń ulic domów (D51 PARTIAL), drobne z HANDOVER.

**Zasady (skrót):**
- **Limit:** do 10 agentów; od 85 % nowy agent tylko gdy działa < 2; od 95 % WIP + HANDOVER + push. Polecenie właściciela ma pierwszeństwo.
- **Ciągły zapis:** HANDOVER i `artifacts/live/*.md` aktualne po każdym scaleniu/starcie/końcu agenta; push.
- **Scalanie:** `generated/*.json`, `*.glb`, `*_meta.json` przy konflikcie → `--ours` + regeneracja. Nie scalaj do main w trakcie buildu Unity w main (build czyta pliki). Przed usunięciem worktree: unlink junctionów `Data/raw/*` (`cmd /c rmdir` z PowerShell), kopia artifacts **bez nadpisywania śledzonych plików** (w s15 robocopy nadpisał `artifacts/edge-r6c/STATUS.md` i zablokował merge).
- Po każdym Unity: `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`. Nie uruchamiaj `setup-project.ps1` przed buildem. Build Unity w trakcie PHONE_RUN zrywa adb. Równoległe buildy mogą zatrzymać wspólny demon Gradle („stop command received”) — wtedy ponów.
- **Telefony:** zawsze `-Serial`; `PHONE_RUN` tylko na czas pomiaru. A16 = RFGL34SJYDZ. S24+ RZCX60VE8ZY i Fold RFGL80RXBPZ to telefony właściciela: bateria nigdy < 20 %, pomiar przy ≥ 40 % i < 36 °C. Zablokowany telefon = pomiar odrzucony.
- **Decyzje właściciela:** klikalne (AskUserQuestion, po polsku); przy obrazach najpierw SendUserFile (≤ 960 px). APK > 30 MB — podaj ścieżkę.
- **ElevenLabs:** przegenerowania jako nowy `docs/owner/ELEVENLABS-REGEN-NN.md` (REGEN-04 już istnieje, opcjonalny). Odrzuconych ujęć nie kasować (D54).
- **Zakazy:** Google Maps, Street View, Earth, 3D Tiles. Fab/Megascans nigdy w gicie.
- **Ostatni przydzielony ADR: 0152.**
