Kontynuujesz projekt Kamion (realistyczny mobilny symulator ciężarówki, Unity 6000.3.28f1 URP, Białystok 1:1) w `C:\Users\matma\Documents\Claude\kamion`. Przejmujesz pracę po sesji 12. Jesteś liderem i jedynym integratorem main. Repo: https://github.com/woogitsugames/kamion.

**Najpierw przeczytaj, w tej kolejności:**
1. `HANDOVER.md`, górna sekcja „SESJA 12”: to prawda o stanie, z tabelą agentów i wpisami godzinowymi.
2. `CLAUDE.md`
3. `docs/owner/AGENT-RULES.md`
4. `docs/11_DECYZJE_WLASCICIELA.md` (D49–D53)
5. `docs/owner/GPT-BACKLOG.md` oraz `docs/owner/gpt-handovers/`: przekazania sesji GPT, które skończyły tygodniowy limit.
6. `docs/owner/MISTRAL-TASKS.md`: 5 sesji Mistral w chmurze; ich wyniki przychodzą jako PR-y `mistral/*`.
7. Recenzje `docs/reports/visual/REVIEW-2026-11-12-s12-*.md` i `docs/reports/REVIEW-2026-11-12-s12-0134-0135.md`.

Pamięć projektu jest w `C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\MEMORY.md`. Jeśli jej nie widzisz, kluczowe zasady są w HANDOVER, CLAUDE.md i AGENT-RULES.

**Na starcie, w tej kolejności:**
1. **Ochrona maszyny.** Sprawdź, czy `pwsh -NoProfile -File scripts/ops-watchdog.ps1` nadal pisze do `artifacts/logs/ops-watchdog.log`. Jeśli nie, uruchom go w tle, ale nie uruchamiaj drugiej kopii. Potem sprawdź sloty: `pwsh scripts/unity-slot.ps1 -Status` i `-Status -Pool heavy`.
   - Skrypt slotów (s12) ma kolejkę FIFO, `-Priority` działa tylko dla `lead-*`, a `PHONE_RUN` blokuje tylko pulę `unity`.
   - Sprawdź, czy `artifacts/locks/PHONE_RUN` nie wisi bez pomiaru, i porównaj z `tasklist` (Unity.exe, adb).
2. Uruchom `get_usage` i ustaw triggery (CronCreate, minuty inne niż :00 i :30):
   - **:17** limit → agenci (STATUS.md w worktree) → krytyk dla gotowych → scalenie → regeneracja → HANDOVER (godzina z `date`) → push;
   - **:47** PR-y Mistrala (`gh pr list`; recenzja w komentarzu po polsku, scala tylko lider);
   - **:07** przekazania GPT (`.claude/worktrees/gpt-*/artifacts/*/PRZEKAZANIE.md`) → `docs/owner/GPT-BACKLOG.md` → zadania dla agentów Claude według priorytetu.
3. **Agenci Claude z s12.** Mogli zostać przerwani albo jeszcze pracować. Wznów ich z ich STATUS.md (tabela w HANDOVER). Każdy przed scaleniem robi `git merge main`; pliki `generated/*.json`, `*.glb`, `*_meta.json` bierze z main (`--ours`) i regeneruje.
   - 0123 `junctions-r6`: węzły, b6 nasyp na wyspie ronda Bieżeństwa.
   - 0127 `g3b-lowread`: czytelność G3-B na Low (LOD bramownicy, słup WN, ekrany) oraz wysokość portalu na Andersa i typ ekranu przy Tysiąclecia.
   - 0128 `biezenstwa-island`: wysepka i znaki D-3/D-6; gałąź oparta na `junctions-r6`, więc scalać PO 0123.
   - 0129 `frontage-r2`: pierzeja, runda 2.
   - 0132 `buildings-r9`: wysoka zieleń przy posesjach.
   - 0133 `putry-deck`: latarnie w pasie dzielącym pomostu Putry.
   - 0136 `a16-perf`: regresja GPU na A16, jedyny agent telefonowy.
4. **Czysty APK do testu na Foldzie** (scalone 0134 jazda 24 t, 0135 kierownica i orientacja, 0137 dźwięk ElevenLabs). Sprawdź `artifacts/integration-s12/run-h.log`.
   - Jeśli nie ma `APK EXIT 0` i nazwy bez `-dirty`, uruchom ponownie w tle: `pwsh -NoProfile -File artifacts/integration-s12/run-h.ps1 > artifacts/integration-s12/run-h.log 2>&1`.
   - Daj właścicielowi ścieżkę APK i listę kontrolną: obraz się nie obraca, przesuw kciukiem, jazda 24 t, dźwięk synteza/ElevenLabs, a z logcat linie `[SCREEN]` i `[CONTROLS]`.
   - **Nie uruchamiaj `setup-project.ps1` przed buildem:** przepisuje sceny i prefaby (ok. 17 tys. linii samych identyfikatorów).

**Zasady:**
- Do 10 agentów naraz (5 Fable + 5 Opus). Fable dostaje geometrię i modelowanie (world-builder, truck-artist), Opus rendering, kalibrację, fizykę, UI, audio i krytyka. Jakość jest ważniejsza niż oszczędzanie limitu.
- Od 85 % limitu 5-godzinnego nowy agent tylko wtedy, gdy działa mniej niż 2. Od 95 % żadnych nowych: agenci zapisują WIP, ty aktualizujesz HANDOVER i pushujesz. Właściciel przenosi pracę na inne konto, gdy limit się skończy.
- Każdy agent ma swój worktree z main: kopie `Data/raw/derived`, `Data/raw/cc0`, `art-source/world/cc0/_raw`, `art-source/world/megascans`, `game/Assets/_Generated`, `game/Library` oraz junctiony `gugik/osm/refs/mapillary/fab`.
  - Brief zaczyna się od AGENT-RULES. Unity tylko przez `unity-slot.ps1`; build_world, pytest, build_all i fidelity tylko przez `-Pool heavy`.
  - Agent commituje WIP i aktualizuje STATUS.md po każdym kroku.
- Przed usunięciem worktree: artifacts do main, odepnij junctiony (`cmd /c rmdir`), potem `worktree remove --force --force`.
- Konflikty: `generated/*.json`, `*.glb`, `*_meta.json` → `--ours` + regeneracja; kod → unia z myślą, a potem `grep` po znacznikach konfliktu.
- Przed scaleniem cofnij lokalne kopie `artifacts/*/STATUS.md` w main, które agenci kopiują. Zrób to wąsko, pojedynczymi plikami z kopią zapasową w scratchpadzie. Szerokie `git checkout -- artifacts/` jest zablokowane i słusznie.
- Po każdym Unity: `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`. Commit regeneracji musi obejmować także `art-source/world/landmarks` (kominy EC).
- Decyzje dla właściciela zawsze klikalne (AskUserQuestion), po polsku; gdy dotyczą obrazów, najpierw pokaż obrazy (SendUserFile, ≤960 px).
- Zakaz Google Maps, Street View, Earth i 3D Tiles. Fab/Megascans nigdy nie trafiają do gita (D45).

**Telefony:** tylko lider albo jeden agent telefonowy, zawsze z `-Serial`. Blokada `PHONE_RUN` zakładana tuż przed pomiarem i zdejmowana zaraz po nim; nigdy na czas buildu.
- **A16** (RFGL34SJYDZ): profil Low dla bramki 3 (D49).
- **S24+** (RZCX60VE8ZY), telefon właściciela do rozmów: bateria nigdy poniżej 20 %, pomiar przy ≥ 40 % i < 36 °C, potem `am force-stop`.
- **Fold:** testuje właściciel.
- Nie usypiaj i nie blokuj telefonów, nie wpisuj PIN-u. Serwer adb bywa ubijany przez Unity, więc przed każdym runem sprawdź `adb devices`.

**Audio:** właściciel generuje dźwięki w ElevenLabs (plan ElevenCreative Pro, 99 USD/mies., licencja komercyjna) według `docs/owner/ELEVENLABS-PROMPTS.md`. Pliki trafiają do `art-source/audio/elevenlabs/`.
- ElevenLabs ignoruje obroty podane liczbą; pętle są przestrajane offline (ADR 0137).
- Przegenerowania zawsze jako nowy plik `docs/owner/ELEVENLABS-REGEN-NN.md`, wysłany właścicielowi.
- Następny jest REGEN-01 (14 promptów).

**Cel:** **bramka 3 według D51, czyli rozpoznawalność trasy.**
- Stan: G3-A warunkowo OK; G3-B 6/10 rozpoznawalnych (3 słabo), 4 częściowo.
- Wydajność A16 Low: FAIL — GPU p95 35,2–35,5 ms przy budżecie 33,3 ms; p99 G3-B 50 ms.
- Ścieżka:
  1. Scalić 0127, 0128 (po 0123), 0129 i 0133 po recenzji visual-critic.
  2. 0136 naprawia GPU.
  3. Jedna integracja: regeneracja, import, testy, kamery kontrolne, SBS Low render-only.
  4. Krytyk D51: „czy kierowca rozpozna to miejsce?”.
  5. Czysty APK Low i pomiar gate3 na A16 (A+B).
  6. Pakiet porównań zdjęcie | render dla właściciela: najpierw obrazy, potem klikalna akceptacja.
- Po bramce 3: interfejs pod Folda (D52), raport luk do bramki 4 (pipeline świata 2×2 km).
- Ostatni przydzielony ADR: 0137.
