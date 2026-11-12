# Prompt startowy — sesja 15 (przejęcie po s14)

Skopiuj całość poniżej do nowej sesji Claude Code (zakładka Code, katalog `C:\Users\matma\Documents\Claude\kamion`).

---

Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Przejmujesz pracę po sesji 14, którą zakończył limit. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj, w tej kolejności:**
1. `HANDOVER.md`, górna sekcja „SESJA 14”: blok „KONIEC S14”, tabela agentów, wpisy godzinowe.
2. **`artifacts/live/*.md`**. Każdy agent nadpisuje tu swój stan po każdym kroku: sha, zadania w tle, NASTĘPNY KROK jako komenda, gotowość do scalenia. To najświeższe źródło, nowsze niż HANDOVER.
3. `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/11_DECYZJE_WLASCICIELA.md` (D49–D53).
4. Recenzje s14: `docs/reports/visual/REVIEW-2026-11-12-s14-*.md` i `docs/reports/REVIEW-2026-11-12-s14-mistral-r2.md`.

Pamięć projektu: `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md`. Nowa pozycja: `feedback-disk-space`.

**Na starcie, w tej kolejności:**
1. **Dysk.** `(Get-PSDrive C).Free`. W s14 dysk C: spadł do 0,9 GB, bo uzbierało się ok. 45 worktree, każdy z cache Unity ~9 GB. Sprzątanie podniosło wolne miejsce do ~400 GB. Poniżej ~100 GB uruchom `pwsh scripts/cleanup-disk.ps1` (najpierw `-WhatIf`). Skrypt omija worktree używane przez procesy i te z commitem młodszym niż 2 h. **Po każdym scaleniu usuwaj worktree od razu.**
2. **Ochrona maszyny.** Watchdog: czy `artifacts/logs/ops-watchdog.log` rośnie i czy żyje proces `pwsh … ops-watchdog.ps1`. Jeśli nie żyje, uruchom w tle `pwsh -NoProfile -File scripts/ops-watchdog.ps1`. Nie uruchamiaj drugiej kopii i nie zabijaj go `taskkill /F`. Potem `pwsh scripts/unity-slot.ps1 -Status` i `-Status -Pool heavy`. Sprawdź, czy nie wisi `artifacts/locks/PHONE_RUN`, i porównaj z `tasklist`.
3. **Limit i triggery.** Uruchom `get_usage`. Ustaw CronCreate:
   - **:17**: limit i wolne miejsce na C:; potem `artifacts/live/*.md` → krytyk dla gotowych → scalenie → usunięcie worktree → HANDOVER → push.
   - **:47**: PR-y Mistrala.
   - **:07**: przekazania GPT (zwykle bez zmian).
4. **Agenci s14.** Mogą jeszcze kończyć pracę albo mieć żywe zadania w tle. Najpierw sprawdź procesy (`Get-CimInstance Win32_Process`, linie poleceń z `worktrees\<nazwa>`), nie dubluj i nie zabijaj żywych. Wznawiaj tylko te, które nie są gotowe, każdego z jego `artifacts/live/<gałąź>.md`.

| ADR | zadanie | model | worktree / gałąź |
|---|---|---|---|
| 0132 | zabudowa r9, runda r4: budżet High wg decyzji B (pełne bryły roślin ≤ 12 m od frontu) | Fable | `buildings-r9` |
| 0136 r2 | GPU A16 na G3-A (brakuje ~1,2 ms) + weryfikacja orientacji 0147 na A16; jedyny agent telefonowy | Opus | `a16-perf` |
| 0141 | krawędź mapy i tło (far_skyline; kominy EC w SBS 297817/150280) | Fable | `edge-r6c` |
| 0144 | węzły r7: W-beam przez poręcz, filary z danych, żwir, spód pomostu, tablica F-10 w 482392 | Fable | `junctions-r7` |
| 0146 | Putry/Andersa: wysokość latarni Y, pobocze 494288, mur 810896, tablice portalu Andersa (~0,6 m za wysoko), gzyms, dwuteowniki | Fable | `putry-andersa` |

**Fable tygodniowo ~90 % (reset 15.11 11:59).** Nowe zadania świata dawaj na Opus. Agentów Fable dokończ na Fable tylko wtedy, gdy limit na to pozwala.

**Stan na koniec s14 (ok. 20:00, 12.11):**
- **Scalone w s14:**
  - 0133 latarnie Putry
  - 0123 węzły b7
  - 0128 wysepka Bieżeństwa
  - 0139 poprawki G3-B
  - 0143 pozy SBS r3
  - 0145 dźwięk opon: szuranie + pisk z REGEN-03
  - 0147 orientacja: telefony w landscape, Fold bez regresji
  - fix fidelity CRLF
  - `scripts/cleanup-disk.ps1`
- **main wymaga regeneracji świata.** Pliki generated po scaleniach brały wersję ours. Dotyczy 0123, 0128, 0129, 0133, 0139, 0143 i CRLF, do tego `ImpostorTrimBake.RunBatch` z 0136. Zrób to raz, w jednej integracji, po scaleniu gotowych gałęzi.
- **APK:**
  - z dźwiękiem opon: `artifacts/apk/kamion-0.1.0-139dc835cf.apk` (czysty, Low);
  - z orientacją 0147 (zawiera też opony): `artifacts/orientation/kamion-0.1.0-387a492d24.apk`.
  - **Właściciel testuje go na Foldzie (4 punkty w ADR 0147)** i ocenia progi i głośność opon.
- **Bramka 3 (D51):**
  - G3-B **5/10 RECOGNISABLE, 5 PARTIAL** (krytyk 0139). 297817 obniżony, bo kominów EC nie było widać na Low → 0141.
  - Kadru 810896 nie oceniaj, dopóki 0146 nie naprawi muru.
  - Po integracji przeoceń 494288, 482392 i 320326 w `sbs_recognition.json`.
  - A16 Low: G3-B GPU p95 33,9; G3-A 34,5 po vehicleCullM 150. Budżet 33,3.
- **Mistral:**
  - Runda 2 (#6–#14): **scalona w s14** (`fc500083`, gałąź `mistral-r2-int` z poprawkami lidera; PR-y zamknięte). Worktree `mistral-r2-int` usuń przez `scripts/cleanup-disk.ps1`.
  - **Runda 3 + M9: PR-y #15–#20, gotowe, niezrecenzowane** (M9 znaki pionowe, M16 oktawa audio, M17 źródła fizyki, M18 oznakowanie z ISAP, M19 expectedFailMetrics, M20 HUD zero-alloc). Zrecenzuj je (komentarz po polsku) i scal. M20 zmienia C#, więc najpierw kompilacja Unity i pomiar GC. Właściciel mówi, że Mistral skończył.
  - Osobne zadania z recenzji Mistrala: duplikat `concrete_pole` w `materials.py` (świat, regeneracja); po #14 przebieg fidelity.

**Ścieżka do bramki 3:**
1. Dokończ 0132, 0141, 0144, 0146 i 0136 r2. Dla każdego gotowego: visual-critic D51 → scalenie → usunięcie worktree.
2. **Jedna integracja:** regeneracja (`build_world` → `import-region` → fidelity → `ImpostorTrimBake`), testy, kamery kontrolne, `pwsh scripts/sbs-low-pairs.ps1 -Before artifacts/sbs-poses-r2/after`.
3. Krytyk D51: „czy kierowca rozpozna to miejsce?”.
4. Czysty APK Low i gate3 na A16 (A+B).
5. Pakiet zdjęcie | render dla właściciela: najpierw obrazy, potem klikalna akceptacja.

Po bramce 3: UI pod Folda (D52) i raport luk do bramki 4.

**Zasady (skrót, całość w AGENT-RULES i HANDOVER):**
- **Limit:** do 10 agentów naraz. Od 85 % limitu 5 h nowy agent tylko wtedy, gdy działa mniej niż 2. Od 95 % agenci zapisują WIP, a lider aktualizuje HANDOVER i pushuje. Jeśli właściciel każe nie uruchamiać nowych, słuchaj go.
- **Ciągły zapis (polecenie właściciela):** HANDOVER i `artifacts/live/*.md` mają być aktualne tak, aby inna sesja mogła w każdej chwili przejąć pracę.
- **Konflikty i Unity:**
  - `generated/*.json`, `*.glb`, `*_meta.json` → `--ours` + regeneracja.
  - Po każdym Unity: `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`.
  - Nie uruchamiaj `setup-project.ps1` przed buildem.
  - Build Unity w trakcie PHONE_RUN zrywa adb, więc czekaj.
- **Shell:** `cmd /c rmdir` uruchamiaj z PowerShell, nie z Git Bash, bo Git Bash przekręca `/s /q`. Katalog `artifacts/` jest w .gitignore, więc `git add` tylko dla plików już śledzonych.
- **Telefony:**
  - Tylko lider albo jeden agent telefonowy, zawsze z `-Serial`.
  - `PHONE_RUN` zakładaj tylko na czas pomiaru.
  - A16 = RFGL34SJYDZ.
  - S24+ (RZCX60VE8ZY) to telefon właściciela: bateria nigdy poniżej 20 %, pomiar przy ≥ 40 % i < 36 °C.
  - Fold testuje właściciel.
- **Decyzje właściciela:** zawsze klikalne (AskUserQuestion, po polsku). Gdy dotyczą obrazów, najpierw pokaż obrazy (SendUserFile, ≤ 960 px). Pliki > 30 MB (APK) widać tylko w aplikacji desktopowej, więc podaj ścieżkę.
- **ElevenLabs:** przegenerowania zawsze jako nowy plik `docs/owner/ELEVENLABS-REGEN-NN.md` (następny będzie 04). Surowe WAV są w `art-source/audio/elevenlabs/`, poza gitem.
- **Zakazy:** Google Maps, Street View, Earth i 3D Tiles. Fab/Megascans nigdy w gicie.
- **Ostatni przydzielony ADR: 0147.**
