# Kamion — przenosiny na nowy komputer (s23, 17.11.2026)

Nowa maszyna: i5-10400F, 64 GB DDR4, GTX 1070, NVMe, Windows (świeża instalacja). Ten plik czyta **nowa sesja Claude** (lider) i robi wszystko sama; właściciel tylko się loguje i klika zgody.

## 0. Co gdzie leży

| Co | Gdzie | Uwagi |
|---|---|---|
| Kod, dane wygenerowane (`generated/*`), dokumenty, ADR, HANDOVER | GitHub `woogitsugames/kamion`, gałąź `main` (+ gałęzie agentów, tabela w §5) | `git lfs` — tekstury/FBX w LFS |
| Dane źródłowe poza gitem `Data/raw/*` | ZIP-y `kamion-A-dane-male.zip`, `kamion-B-gugik.zip`, `kamion-C-derived.zip` | A = zdjęcia właściciela (refs, **niezastąpione**), Fab, Mapillary, OSM, CC0 + pamięć Claude; B = GUGiK 19 GB (do pobrania ponownie, ale długo); C = zbudowany świat 34 GB (generator odbuduje, ale kilkanaście godzin) |
| Dowody agentów (rendery) i ostatni exe | `kamion-D-ostatni-exe.zip`, `kamion-E-artefakty-agentow.zip` | opcjonalne |
| Unity `Library`, `_Generated`, venv Pythona | — | NIE przenosimy: odtwarzają się (pierwszy import Win64 to kilka godzin) |

Paczki tworzy na starym komputerze: `pwsh scripts/pack-migration.ps1 -Out C:\KAMION-PRZENOSINY` → `MANIFEST.txt` z SHA-256.

## 1. Właściciel (ręcznie, ~15 min)
1. Konto Windows **`matma`** (ścieżki w pamięci Claude: `C:\Users\matma\...`).
2. Skopiuj `C:\KAMION-PRZENOSINY` z pendrive/dysku na nowy komputer.
3. Zasilanie: bez usypiania przy zasilaniu sieciowym (agenci pracują w nocy). Windows Update: restart tylko w nocy.
4. Zainstaluj aplikację Claude (claude.ai/download), zaloguj, zakładka Code, folder `C:\KAMION-PRZENOSINY`, napisz:
   > Przeczytaj C:\KAMION-PRZENOSINY\NOWY-PC-KAMION.md i wykonaj wszystko. Ja tylko się loguję, gdy poprosisz.

## 2. Instalacje (robi Claude, PowerShell; UAC — właściciel klika „Tak”)
```
winget install Microsoft.PowerShell Git.Git GitHub.GitLFS GitHub.cli astral-sh.uv OpenJS.NodeJS Gyan.FFmpeg Microsoft.DotNet.SDK.10 Microsoft.DotNet.Runtime.8 BlenderFoundation.Blender.LTS.4.2 Unity.UnityHub ImageMagick.ImageMagick
winget install Microsoft.VisualStudio.2022.BuildTools --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```
- Wersje ze starej maszyny: Unity **6000.3.28f1** (zamrożona w `game/ProjectSettings/ProjectVersion.txt`), Blender 4.2.9 LTS, uv 0.12.5, git-lfs 3.7.1, gh 2.101, Node 26, .NET SDK 10.0.403 + runtime 8.0. Blender musi być w PATH (`blender --version`).
- **Unity:** w Unity Hub zaloguj (właściciel), zainstaluj edytor **6000.3.28f1** z modułami: *Windows Build Support (IL2CPP)*, *Android Build Support* (+ OpenJDK, Android SDK & NDK — telefon odroczony D73, ale projekt nadal kompiluje się pod Androida). Licencja Personal aktywowana w Hub.
- VS Build Tools z C++ są potrzebne do IL2CPP Windows.
- `git lfs install`; `gh auth login` (właściciel, przeglądarka).
- **Pomocnicze CLI do zlecania pracy (właściciel chce ich używać — zainstaluj wszystkie, loguje właściciel):**
  1. **Claude Code CLI (drugie konto):** `irm https://claude.ai/install.ps1 | iex` (zwykły PowerShell, nie admin). Skrót `C:\Users\matma\.local\bin\claude-alt.cmd`:
     ```
     @echo off
     set CLAUDE_CONFIG_DIR=%USERPROFILE%\.claude-alt
     "%USERPROFILE%\.local\bin\claude.exe" %*
     ```
     Logowanie: `claude-alt.cmd` → `/login` (właściciel, drugie konto Team). Zlecanie: osobny worktree, `Get-Content prompt.txt -Raw | claude-alt.cmd -p --model claude-opus-5-5 --max-turns 120 --output-format json --permission-mode acceptEdits --allowedTools "Read,Edit,Write,Grep,Glob,Bash(git *),Bash(uv *),Bash(python *),PowerShell" > out.json` uruchomione odłączone (Start-Process). Nie kompiluje Unity — lider robi EditMode przed scaleniem.
  2. **Codex CLI:** `winget install OpenJS.NodeJS` (już), `npm install -g @openai/codex`, logowanie `codex login` (właściciel). Zawsze **`-m gpt-6.1-sol`** (polecenie właściciela) i `--sandbox read-only` do recenzji; do zmian kodu worktree + `--sandbox workspace-write` — **sandbox nie zapisze do wspólnego `.git`**, commit/merge robi lider. Limity: ostatnie `rate_limits` w najnowszym `%USERPROFILE%\.codex\sessions\YYYY\MM\DD\rollout-*.jsonl` (5 h i tydzień). Uwagi Codexa weryfikuj (raz fałszywy alarm o API Unity).
  3. **Mistral Vibe CLI:** `uv tool install --python cpython-3.14+gil mistral-vibe` (install.sh nie działa na Windows); klucz API: właściciel `vibe --setup` (keyring), model `mistral-large-4-0-3`. Headless 2/2 razy się zawiesił (`--worktree` i zapis pliku) → do zleceń używaj tylko z **własnym worktree** (`--workdir`, bez `--worktree`), `--max-price`, `--time-limit`, i pilnuj postępu; duże pakiety badawcze lepiej zlecać właścicielowi do interaktywnego Vibe (pętla S8 wyszła dobrze).
  - Zasady: kluczy i haseł nie wpisujesz ani nie czytasz; wszystko z tych CLI przechodzi przegląd lidera przed scaleniem. Szczegóły w pamięci: `reference-extra-clis.md`, `reference-mistral-vibe-cli.md`.

## 3. Repo i dane
```
mkdir C:\Users\matma\Documents\Claude
cd C:\Users\matma\Documents\Claude
gh repo clone woogitsugames/kamion
cd kamion; git lfs pull
```
Rozpakuj ZIP-y A, B, C w katalog repo (zachowują ścieżki `Data\raw\...`). Z A przenieś `_pamiec-claude\memory\*` do
`C:\Users\matma\.claude\projects\C--Users-matma-Documents-Claude-kamion\memory\` (nazwa katalogu = ścieżka repo; ta sama ścieżka repo = pamięć działa od razu).
Kontrola: `(Get-ChildItem Data\raw\derived -Directory).Count` ≈ 48+, `Data\raw\refs\owner-knyszyn-2026-11-15` istnieje.

## 4. Pierwsze uruchomienie
1. `pwsh scripts/doctor.ps1` → wszystko zielone (telefon/adb — opcjonalne).
2. `pwsh scripts/setup-project.ps1` (ustawienia projektu jako kod; commit zmian ProjectSettings, jeśli są).
3. Worktree buildowy na gałęzi **nigdy nie scalanej** (patrz §6): `git worktree add .claude/worktrees/win-build -b build/win origin/main`; tam pierwszy import Win64 (kilka godzin, w tle).
4. Testy: `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` (znane porażki środowiskowe: StartClearance przed reimportem regionów, 2× CarPaintMaterialTests).
5. Import regionów + build: `docs/reports/CHECKLIST-2026-11-16-full-build-windows.md`.
6. **GTX 1070 ≈ klasa „min”/„zalecany” z D74** — pierwszy *prawdziwy* pomiar PC (nie emulacja): `pwsh scripts/pc-metrics.ps1 ... -Class min` i `-Class zalecany` (budżety `tools/pcperf/budgets/pc-budgets.json`, tileBudgetsD83). Porównaj D3D11 vs D3D12 (decyzja właściciela: „najpierw pomiar”).

## 5. Praca w toku (gałęzie na GitHubie, stan 17.11 ~13:40)
Szczegóły: góra `HANDOVER.md` (SESJA 23) i `STATUS.md` w każdej gałęzi.

| Gałąź | Stan | Następny krok |
|---|---|---|
| `s8-loop-s23` | 15 kafli zdefiniowanych, s8-01/02/03/05 zbudowane z poprawnym przekrojem S8, ADR 0288 | `pwsh tools/worldgen/qa/s8_loop_continue.ps1` (przebudowa s8-04 i dk65-01, import, szwy, pytest) → przegląd → scalenie. Ciągła trasa Białystok→S8 wymaga kafla `dk8-s8-jeroniki`. |
| `seams-fix-s23` | uskok zach. ronda Knyszyn 0,506→0,218 m, linia DW671 na szwie, autopilot z `-scene knyszyn` (route_links) | obejrzeć rendery vqa2 (paczka E), **przenumerować ADR 0288 → 0289** (0288 = S8), scalić |
| `dk19-tiles-s23` | kafle mickiewicza/bojary/wygoda zbudowane, linki DK19 | przebudować bojary + mickiewicza (STATUS), import, render mickiewicza; brak kafla `bialystok-krywlany` |
| `full-build-s23` | **scalone do main** (AO kabiny BC4 = przyczyna czarnych bloków, kaskada 3 m, parser, menu_bg). Exe `kamion-0.1.0-80da043258-dirty-regions` (39 regionów, 8,7 GB) w paczce D. D3D11 vs D3D12: p95 równe (16,7 ms), bez limitu D3D11 p50 2,97 vs 3,09 ms, pamięć 2,65 vs 3,04 GB, 0 crashy w 3 cyklach | na nowym PC: `setup-project.ps1` + commit ProjectSettings (diff w paczce E: `full-build-s23/projectsettings-at-build.diff`), build bez `-dirty`, `scripts/d3d-ab.ps1` (popraw katalog wyjściowy) przy bezczynnej maszynie, visual-critic cieni kabiny, potem exe dla właściciela |
| `build/win-s23` | gałąź worktree buildowego | **nie scalać** |
| `research/codex-refs-s21` (#100) | WIP Codexa | audyt licencji 99 obrazów |

Decyzje właściciela czekające na wykonanie:
- **D-17.11 (klik): pobrać teksturę desek CC0** z Poly Haven dla domów drewnianych Knyszyna — proponowany `raw_plank_wall` (Dimitrios Savva, CC0, ~10 MB 2k) przez `art-source/world/materials/_src/cc0_fetch.py`, zestaw `wood_siding`, wpis LICENSES, przebudowa knyszyn (Dom Klattów).
- Pytania do właściciela o Knyszyn (zdjęcia): HANDOVER, wpis 17.11 09:2x.
- Exe dla właściciela dopiero po ocenie visual-critic poprawki **czarnych bloków w kabinie** (przyczyna: AO BC1 → teraz BC4; scalone) i buildzie bez `-dirty` — `docs/reports/REVIEW-2026-11-17-s23-cabin-pc.md`. Do decyzji właściciela: miękkie cienie słońca w kabinie na PC.

## 6. Zasady, które uratują dysk i RAM (nauczka z s23)
- **Sprzątanie codziennie:** `pwsh scripts/maintenance-daily.ps1` (scalone worktree → usuń, stare buildy → zostaw 2, artefakty nieruszane 10 dni → usuń, temp > 7 dni, `uv cache prune`; exit 2 = ALARM < 150 GB). Ustaw jako zadanie zaplanowane aplikacji Claude codziennie o 03:30 **oraz** w cronie lidera `:17` sprawdzaj wolne miejsce. Najpierw `-WhatIf`.
- **Po scaleniu gałęzi agenta usuń jej worktree** (procedura w `scripts/cleanup-disk.ps1`: najpierw odłącz junctiony `Data\raw\*` przez `[System.IO.Directory]::Delete`, potem `git worktree remove`). Każdy worktree z Unity to ~10–20 GB.
- **Worktree buildowy na gałęzi nigdy nie scalanej** — 16.11 o 22:05 zniknęły automatycznie 4 worktree scalonych gałęzi (w tym buildowy z Library Win64).
- **RAM:** najwyżej 2 edytory Unity naraz (`scripts/unity-slot.ps1`, pula unity = 2, heavy = 3; nadpisanie `$env:KAMION_UNITY_SLOTS`). Nie puszczać pytest równolegle z Unity. Gra (Kamion.exe) tylko jedna naraz, w oknie, ze slotem heavy.
- **Agenci:** maks. 8 naraz (właściciel); krótkie kroki (watchdog 10 min); długie polecenia odłączone (Start-Process, status `exit=`).
- `Data/raw/derived` w worktree = junction do main (nie kopia).

## 7. Start nowej sesji (po instalacji)
> Jesteś liderem projektu Kamion. Przeczytaj CLAUDE.md, górę HANDOVER.md (SESJA 23) i docs/owner/NOWY-PC-KAMION.md §2 i §5–§6. Ustaw crony :07/:17/:47 jak w HANDOVER, zadanie zaplanowane maintenance-daily 03:30, potem kontynuuj gałęzie z §5 (maks. 8 agentów, Opus/Fable wg limitów), część pracy zlecaj przez claude-alt / Codex (Sol) / Mistral Vibe wg §2, po każdym scaleniu sprzątaj worktree.

## 8. Stary komputer
Właściciel go sformatuje — **dopiero gdy nowa sesja potwierdzi**: sumy SHA-256 z MANIFEST.txt zgodne, `doctor.ps1` zielony, EditMode przeszedł, pierwszy build zrobiony, Kamion.exe uruchomiony. Do tego czasu stary komputer = jedyna kopia zapasowa (zdjęcia właściciela w paczce A są niezastąpione).
