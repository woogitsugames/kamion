# 09 — Agenci i workflow

> **D73 / ADR 0260:** platformą główną jest Windows — „build na urządzeniu” znaczy **player Windows x64** (`scripts/build-windows.ps1`, ADR 0261) i pomiar `scripts/pc-metrics.ps1` (ADR 0266). Praca na telefonie (APK, adb, logcat) jest 🔒 odroczona, ale ścieżka Androida musi się dalej kompilować.

## 1. Model pracy
- **Ty (sesja główna)** = lider, architekt, jedyny integrator. Planujesz etap, dzielisz na zadania atomowe, delegujesz, robisz review, scalasz, uruchamiasz buildy Windows i pomiary PC (D73; 🔒 telefon odroczony), piszesz raporty.
- **Maks. 10 agentów łącznie** (Ty + do 9 subagentów naraz). Limit to sufit, nie cel. Typowo 2–4 aktywnych; więcej tylko przy naprawdę rozłącznych zadaniach (np. równoległy tor F i tor A + worldgen).
- Subagenci: definicje w `.claude/agents/` (model `opus`). **Subagenci nie tworzą subagentów.**
- Agent teams (eksperymentalne w Claude Code) tylko gdy zadanie wymaga dyskusji agent–agent; domyślnie zwykli subagenci.

## 2. Role (pliki w `.claude/agents/`)

| Agent | Zakres i własność katalogów |
|---|---|
| `vehicle-physics` | `game/Assets/_Project/Vehicle/Physics/**`, `tests/physics/**`, `docs/VEHICLE_REFERENCE_DATA.md`, `docs/PHYSICS_VALIDATION.md` |
| `truck-artist` | `art-source/truck/**` (Blender), `game/Assets/_Project/Art/Truck/**`, `tools/blender/**` |
| `geo-worldgen` | `tools/worldgen/**`, `Data/**`, `game/Assets/_Project/World/Import/**` |
| `world-builder` | `game/Assets/_Project/World/Roads|Terrain|Streaming/**`, generatory zabudowy i otoczenia, `art-source/world/**` |
| `rendering-perf` | `game/Assets/_Project/Rendering/**`, profile jakości (tiery PC, ADR 0269), shadery, budżety PC (`docs/03`, `tools/pcperf/budgets/pc-budgets.json` — zmiana tylko po decyzji właściciela, ADR 0266), 🔒 `docs/PERFORMANCE_BUDGETS.md`, `docs/DEVICE_MATRIX.md` (zabezpieczenie mobilne, D73) |
| `gameplay-ui` | `game/Assets/_Project/Gameplay|UI|Input|Camera/**` (sterowanie PC: klawiatura, pad, kierownica FFB — ADR 0261/0263/0264; HUD pod monitor i menu ustawień PC — ADR 0265/0270; 🔒 dotyk i gyro; GPS, zlecenia, zapis) |
| `audio` | `game/Assets/_Project/Audio/**`, `tools/audio/**` |
| `build-qa` | `scripts/**`, `tests/**` (poza physics), build i uruchomienie playera Windows (ADR 0261), pomiar `pc-metrics` (ADR 0266), paczka dystrybucyjna (ADR 0271), CI; 🔒 APK, adb, raporty z telefonu (D73) |
| `visual-critic` | **tylko odczyt kodu + raporty** w `docs/reports/visual/**`; ocenia obrazy wg `docs/06`; nigdy nie ocenia własnej pracy, bo nie tworzy treści |

Pliki wspólne (`ProjectSettings/`, `Packages/`, sceny `Boot`/`Main`, wspólne prefaby, asmdef, `CLAUDE.md`) zmienia **wyłącznie lider**.

## 3. Kontrakt zadania (to, co dostaje subagent)
```
CEL: <jedno zdanie, mierzalne>
KONTEKST: <pliki/dokumenty do przeczytania, ADR-y>
WŁASNOŚĆ: <ścieżki, które wolno zmieniać>  ZAKAZ: <ścieżki/obszary poza zakresem>
WEJŚCIA: <dane, interfejsy, stan repo (SHA)>
KRYTERIA AKCEPTACJI: <testy, liczby, obrazy do wygenerowania>
WERYFIKACJA: <komendy do uruchomienia>
RAPORT: format z §4
```

## 4. Format raportu subagenta (zwięzły, bez wklejania całych logów)
1. Wynik: DONE / PARTIAL / BLOCKED
2. 3–8 ustaleń
3. Zmienione pliki
4. Dowody: testy (komenda + wynik), ścieżki do PNG/CSV/logów
5. Rozróżnienie: napisane / zbudowane / uruchomione / zmierzone
6. Ryzyka i znane braki
7. Proponowany następny krok

## 5. Git i Unity w pracy równoległej
- `git worktree` + gałąź na zadanie (`feat/<agent>/<opis>`); lider scala po review.
- **Jeden proces Unity na katalog projektu.** Każdy worktree z Unity ma własny `Library/` (koszt dysku i importu) — dlatego agenci pracujący głównie w C# czystym, Pythonie i Blenderze nie potrzebują otwierać Unity; testy EditMode/PlayMode i buildy idą przez **kolejkę lidera** (lub `build-qa`) sekwencyjnie.
- Testy czystego C# fizyki — także poza Unity (projekt .NET z tymi samymi źródłami), żeby `vehicle-physics` iterował bez edytora.
- Konflikt plików = stop, rebase, zgłoszenie liderowi.
- Review krzyżowe: kod jednego agenta przegląda inny (lub lider). `visual-critic` przegląda każdą zmianę wizualną.

## 6. Rytm pracy
- Początek sesji: przeczytaj `docs/STATUS.md`, `docs/ROADMAP.md`, ostatni raport bramki.
- Plan etapu w `docs/plan/STAGE-N.md` (checklista zadań atomowych z właścicielami i kryteriami).
- Koniec sesji: `docs/STATUS.md`, commit, push.
- Kontekst: subagenci zwracają wnioski, nie zrzuty plików. Duże logi do `artifacts/` z odnośnikiem.
- Koszt: nie wysyłaj kilku agentów na ten sam research. Jeden specjalista, ewentualnie recenzent.

## 7. Hooki (zalecane, w `.claude/settings.json` projektu)
- Przed commitem: szybka kompilacja C#/testy EditMode zmienionych modułów.
- Blokada zapisu do `ProjectSettings/`, `Packages/` przez subagentów (jeśli mechanizm uprawnień na to pozwala) — inaczej reguła w kontrakcie.
- Allow-lista narzędzi: git, gh, unity batchmode, pwsh (`build-windows.ps1`, `pc-metrics.ps1`), blender, python/uv, ffmpeg, astcenc; 🔒 adb, scrcpy (telefon odroczony, D73).
