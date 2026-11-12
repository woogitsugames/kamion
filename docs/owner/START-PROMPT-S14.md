# Prompt startowy — sesja 14 (przejęcie po s13)

Skopiuj całość poniżej do nowej sesji Claude Code (zakładka Code, katalog `C:\Users\matma\Documents\Claude\kamion`).

---

Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Przejmujesz pracę po sesji 13, którą przerwał limit. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj, w tej kolejności:**
1. `HANDOVER.md`, górna sekcja „SESJA 13” (tabela agentów, wpisy godzinowe, „Jeśli sesja padnie”).
2. **`artifacts/live/*.md`**. Każdy agent s13 nadpisywał tu swój stan po każdym kroku: sha, zadania w tle, NASTĘPNY KROK jako komenda, gotowość do scalenia. To najświeższa prawda, nowsza niż HANDOVER.
3. `CLAUDE.md`, `docs/owner/AGENT-RULES.md`, `docs/11_DECYZJE_WLASCICIELA.md` (D49–D53).
4. Recenzje s13: `docs/reports/visual/REVIEW-2026-11-12-s13-*.md`.
5. `docs/owner/MISTRAL-TASKS-2.md` (runda 2 Mistrala, M6–M15; wyniki przychodzą jako PR-y `mistral/*`).

Pamięć projektu: `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md`.

**Na starcie, w tej kolejności:**
1. **Ochrona maszyny.** Sprawdź, czy `artifacts/logs/ops-watchdog.log` rośnie, czyli czy watchdog żyje (s13 uruchomił go z `MaxHeavy=4`). Jeśli nie żyje, uruchom w tle `pwsh -NoProfile -File scripts/ops-watchdog.ps1`. Nie uruchamiaj drugiej kopii i nie zabijaj go `taskkill /F`, bo wtedy nie wznowi wstrzymanych zadań. Potem `pwsh scripts/unity-slot.ps1 -Status` oraz `-Status -Pool heavy` (heavy = 4 sloty). Sprawdź, czy `artifacts/locks/PHONE_RUN` nie wisi bez pomiaru, i porównaj z `tasklist` (Unity.exe, adb, python).
2. Uruchom `get_usage` i ustaw triggery CronCreate:
   - **:17** limit → `artifacts/live/*.md` i STATUS.md agentów → krytyk dla gotowych → scalenie → HANDOVER (godzina z `date`) → push;
   - **:47** PR-y Mistrala (`gh pr list`; recenzja w komentarzu po polsku; scala tylko lider; drafty też recenzuj, gdy właściciel powie, że sesja skończyła);
   - **:07** przekazania GPT (zwykle bez zmian, sesje GPT zakończone).
3. **Wznów agentów s13** z ich `artifacts/live/<gałąź>.md` / STATUS.md. Zadania w tle poprzedników mogą jeszcze żyć: najpierw sprawdź procesy, nie dubluj i nie zabijaj żywych.

| ADR | zadanie | model | worktree / gałąź |
|---|---|---|---|
| 0123 | węzły r6 (b7) | Fable | `junctions-r6` |
| 0128 | wysepka + D-3/D-6 ronda Bieżeństwa (**scalać PO 0123**) | Fable | `biezenstwa-island` |
| 0129 | pierzeja r2 (prawie gotowe: pytest/EditMode) | Fable | `frontage-r2` |
| 0132 | zabudowa r9, wysoka zieleń (koszt Low!) | Fable | `buildings-r9` |
| 0139 | poprawki G3-B z recenzji 0127 (ekran-szkło, słup WN, tablice) | Fable | `g3b-r2` |
| 0141 | krawędź mapy i tło (przejęte z GPT edge r6) | Fable | `edge-r6c` |
| 0133 | pomost Putry, latarnie w pasie dzielącym | Opus | `putry-deck` |
| 0136 | regresja GPU A16 (jedyny agent telefonowy) | Opus | `a16-perf` |
| 0140 | pozy SBS G3-B po portalu 14 m + komenda pełnego SBS | Opus | `sbs-poses-r2` |
| 0142 | efekty audio C–G, turbo, miks kabiny, **„syrena”**, REGEN-02 | Opus | `audio-fx` |

Worktree tworzy `pwsh scripts/new-agent-worktree.ps1 -Name <x>`. Robi kopie danych i junctiony. Przed usunięciem worktree: artifacts do main, potem `cmd /c rmdir` na junctionach `Data/raw/{gugik,osm,refs,mapillary,fab}`, potem `git worktree remove --force --force`.

**Stan na koniec s13 (ok. 18:00, 12.11):**
- Scalone w s13: 0135 r3 (Fold: orientacja `fullUser`, chwyt kierownicy), 0138 audio REGEN-01, 0127 czytelność G3-B Low (portal Andersa 16→14 m), Mistral PR #1–#5 (CI LFS skip, testy fizyki 214, audyty GC/źródła fizyki/docs; uwagi lidera dopisane do raportów).
- Najnowszy APK: `artifacts/apk/kamion-0.1.0-1fa46ca6ad.apk` (czysty Low; Fold r3 + REGEN-01).
- **Bramka 3 (D51):** G3-B 6/10 rozpoznawalnych (2 słabe), 4 częściowo; G3-A warunkowo OK. **A16 Low: FAIL GPU** (p95 35,2–35,5 ms przy budżecie 33,3). 0136: drzewa przy drodze to 6,6–8,7 ms w oknach z lasem (skoki p99); reszta to rozproszone ~+3 ms.
- **Dźwięk (opinia właściciela):** silnik ElevenLabs wyraźnie lepszy od syntezy, przejścia gładkie. Do poprawy: turbo, za głośny silnik w kabinie i „syrena”, czyli gwizd narastający co kilka sekund w obu trybach (film `C:/Users/matma/Downloads/Screen_Recording_20261112_174853_Kamion.mp4`). REGEN-02 (28 WAV) jest gotowe w `art-source/audio/elevenlabs/` → 0142. Po 0142: APK „ze wszystkimi dźwiękami” dla właściciela.
- Otwarte z recenzji Mistrala M1: hashe fidelity liczą surowe bajty (CRLF lokalnie, LF w CI). Trzeba znormalizować w `tools/worldgen/fidelity/run.py:50` i `tests/gis/test_road_fidelity.py:40`, potem zregenerować `fidelity_qa.json`.

**Ścieżka do bramki 3:**
1. visual-critic D51 dla gotowych.
2. Scalenie: 0129, 0133, 0123 → 0128, 0139, 0141, 0132.
3. 0136 naprawia GPU.
4. **Jedna integracja:** regeneracja, import, testy, kamery kontrolne, SBS Low render-only (komenda od 0140).
5. Krytyk D51: „czy kierowca rozpozna to miejsce?”.
6. Czysty APK Low i gate3 na A16 (A+B).
7. Pakiet zdjęcie | render dla właściciela: najpierw obrazy, potem klikalna akceptacja.

Po bramce 3: UI pod Folda (D52), raport luk do bramki 4.

**Zasady (skrót, całość w AGENT-RULES/HANDOVER):**
- **Limit:** do 10 agentów naraz (Fable: geometria i modelowanie; Opus: rendering, fizyka, UI, audio, krytyk). Od 85 % limitu 5 h nowy agent tylko wtedy, gdy działa mniej niż 2. Od 95 % agenci zapisują WIP, a lider aktualizuje HANDOVER i pushuje. Jeśli właściciel każe nie uruchamiać nowych, słuchaj go.
- **Konflikty i Unity:**
  - `generated/*.json`, `*.glb`, `*_meta.json` → `--ours` + regeneracja.
  - Po każdym Unity `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`.
  - **Nie uruchamiaj `setup-project.ps1` przed buildem**, bo przepisuje sceny i prefaby.
  - Commit regeneracji obejmuje `art-source/world/landmarks`.
- **Telefony:**
  - Tylko lider albo jeden agent telefonowy, zawsze z `-Serial`.
  - `PHONE_RUN` zakładaj tylko na czas pomiaru.
  - A16 = RFGL34SJYDZ.
  - S24+ (RZCX60VE8ZY) to telefon właściciela do rozmów: bateria nigdy poniżej 20 %, pomiar przy ≥ 40 % i < 36 °C.
  - Fold testuje właściciel.
  - Nie usypiaj i nie blokuj telefonów, nie wpisuj PIN-u.
- **Decyzje właściciela:** zawsze klikalne (AskUserQuestion, po polsku). Gdy dotyczą obrazów, najpierw pokaż obrazy (SendUserFile, ≤ 960 px).
- **ElevenLabs:** przegenerowania zawsze jako nowy plik `docs/owner/ELEVENLABS-REGEN-NN.md` (następny będzie 03).
- **Zakazy:** Google Maps, Street View, Earth i 3D Tiles. Fab/Megascans nigdy w gicie.
- **Ostatni przydzielony ADR: 0142.**
