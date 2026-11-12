# Prompt dla sesji GPT (Codex): diagnoza i sprzątanie dysku C:

Skopiuj wszystko poniżej linii do nowej sesji GPT uruchomionej na tym komputerze (Windows 11, PowerShell 7).

---

Jesteś administratorem dysku na komputerze właściciela (Windows 11, `C:` ma 1,81 TB). Właściciel mówi, że ciągle brakuje miejsca, choć nie trzyma tu gier ani dużych plików. Wolnego miejsca było 0,9 GB. Po usunięciu scalonych worktree projektu Kamion jest ok. 446 GB, ale to nadal dużo za mało. **Twoje zadanie: ustalić, co zajmuje ~1,36 TB, i bezpiecznie to zwolnić.**

## Kontekst
- Projekt `C:\Users\matma\Documents\Claude\kamion` to gra w Unity 6, a obok niej narzędzia w Pythonie. Pracuje w nim kilku agentów Claude naraz, każdy w osobnym git worktree w `.claude\worktrees\<nazwa>`.
- Każdy worktree ma własny cache Unity `game\Library` (~9 GB) i kopie danych świata. Katalogi `Data\raw\{gugik,osm,refs,mapillary,fab}` w worktree to **junctiony do main**.
- Pomiar sprzed sprzątania: worktree zajmowały razem ok. 520 GB. Najwięcej kopie GPT: `gpt-life` 35 GB, `gpt-light`, `gpt-truck`, `gpt-landmarks` i `gpt-car-paint` po ok. 20 GB.
- Dysk `G:` to Google Drive for Desktop. Pokazuje tyle samo wolnego miejsca co `C:`, bo jego cache leży na C:. Nie jest osobnym problemem.

## Pomiar lidera Claude (12.11, ok. 20:10, po sprzątaniu; punkt startowy)
| GB | ścieżka |
|---|---|
| 553 | `C:\Users\matma\Documents\Claude` (w tym kamion `.claude\worktrees` **293**, kamion `artifacts` **226**, `game` 10, `.git` 8, `Data` 4) |
| 84 | `C:\Users\matma\AppData\Local\Temp` |
| 45 | `C:\Users\matma\AppData\Local\uv` (cache uv) |
| 33 | `C:\Program Files\Unity` |
| 25 | `C:\hiberfil.sys` |
| 25 | `C:\pagefile.sys` |
| ~10 | ProgramData, Roaming, Packages, LocalLow, Downloads (razem) |

Razem to ok. 780 GB. Zajęte jest ok. 1,36 TB, więc **ok. 600 GB jest nierozpoznane**. Najpierw szukaj tam: inne katalogi w `C:\Users\matma` (OneDrive, `.cache`, `.nuget`, `.gradle`, `.android`, `AppData\Local` poza zmierzonymi), inni użytkownicy, `C:\Windows` (WinSxS), kopie cieni i punkty przywracania, `C:\$Recycle.Bin`. Pozostałe katalogi w `Documents\Claude` (553 GB) poza kamion też mierz osobno.

W `kamion\artifacts` (226 GB) są rendery, logi i stare APK z wielu sesji. Pokaż podkatalogi > 2 GB. Kandydaci do usunięcia za zgodą właściciela: stare rendery (`renders*`, `vqa*`, `sbs*`) z zakończonych zadań. Zostaw `artifacts\live`, `artifacts\locks`, `artifacts\apk` (skrypt sam przycina APK) i katalogi aktywnych agentów.

## Krok 1: tylko pomiar, niczego nie usuwaj
1. Wolne miejsce: `(Get-PSDrive C).Free/1GB`.
2. Największe katalogi: najlepiej WizTree albo `du64` (Sysinternals), jeśli są zainstalowane. W przeciwnym razie PowerShell, rekurencyjnie od `C:\`, dwa poziomy w głąb, z `-Force -ErrorAction SilentlyContinue`. Policz koniecznie:
   - `C:\Users\matma\Documents\Claude\kamion`, osobno: `.git`, `.git\lfs`, `Data`, `Data\raw\fab`, `artifacts`, `game`, `art-source`, `.claude\worktrees\*` (każdy osobno);
   - `C:\Users\matma\AppData\Local`: `Temp`, `uv`, `Unity`, `Google\DriveFS`, `Docker`, `Packages`, `pip`, `npm-cache`, `Microsoft\WindowsApps`;
   - `C:\Users\matma\AppData\Roaming`, `C:\Users\matma\AppData\LocalLow`, `C:\Users\matma\Downloads`, `C:\Users\matma\Videos`;
   - `C:\ProgramData`, `C:\Program Files\Unity` (edytory w Hubie), `C:\Windows\SoftwareDistribution`, `C:\$Recycle.Bin`;
   - pliki w korzeniu `C:\`: `pagefile.sys`, `hiberfil.sys`, `swapfile.sys`;
   - pliki `*.vhdx` (WSL, Docker): `Get-ChildItem C:\Users\matma -Recurse -Filter *.vhdx -Force -ErrorAction SilentlyContinue`;
   - punkty przywracania i kopie cieni: `vssadmin list shadowstorage` (wymaga administratora, jeśli go nie masz, napisz o tym).
3. Pokaż właścicielowi **tabelę top 30** (GB i ścieżka), zanim cokolwiek usuniesz.

## Krok 2: sprzątanie, wyłącznie bezpieczne kategorie
Zanim usuniesz cokolwiek spoza listy niżej, **zapytaj właściciela**, podając ścieżkę i rozmiar.

Bez pytania wolno:
- `pwsh C:\Users\matma\Documents\Claude\kamion\scripts\cleanup-disk.ps1`, najpierw z `-WhatIf`. Skrypt usuwa scalone worktree, czyści `game\Library` w nieaktywnych i zostawia tylko najnowsze APK. Omija worktree używane przez procesy i te z commitem młodszym niż 2 h.
- `C:\Users\matma\AppData\Local\Temp\*` starsze niż 1 dzień (pomijaj pliki zablokowane i katalogi `claude\`).
- `uv cache prune`, `pip cache purge`, `npm cache clean --force`.
- Kosz: `Clear-RecycleBin -DriveLetter C -Force`.

**Pytaj właściciela** przed:
- usunięciem całego worktree `gpt-*`, który nie jest scalony do main. Ich praca nie trafiła do main, ale sesje GPT już się skończyły. Najpierw sprawdź `git -C <worktree> status` i `git log main..<gałąź> --oneline`, a jeśli właściciel się zgodzi, wypchnij gałąź `git push origin <gałąź>`, żeby nic nie zginęło;
- `git lfs prune`, zmianą punktów przywracania, wyłączeniem hibernacji, zmianą pliku stronicowania;
- usunięciem czegokolwiek w Downloads, Videos, Documents poza `kamion`;
- odinstalowaniem starych wersji edytora Unity (zostaje `6000.3.28f1`).

## Twarde zakazy
- **Nie usuwaj** `C:\Users\matma\Documents\Claude\kamion\Data\raw\*` w main ani `art-source`. To surowe dane świata, zależą od nich wszystkie worktree.
- **Nie usuwaj** worktree aktywnych agentów: `a16-perf`, `buildings-r9`, `edge-r6c`, `junctions-r7`, `putry-andersa`, `mistral-r2-int`, i żadnego, z którego korzysta działający proces (`Get-CimInstance Win32_Process` → `CommandLine` zawiera `worktrees\<nazwa>`).
- **Przed usunięciem worktree najpierw odepnij junctiony** w PowerShell (nie w Git Bash): `cmd /c rmdir "<worktree>\Data\raw\gugik"`, tak samo `osm`, `refs`, `mapillary`, `fab`. Sprawdź, że w `Data\raw` worktree nie zostały żadne reparse points. Dopiero potem `git worktree remove --force --force <worktree>`. Usunięcie rekurencyjne przez junction skasuje dane w main.
- Nie zabijaj procesów Unity, python, pwsh i bash (agenci i watchdog `ops-watchdog.ps1`).
- Nie ruszaj Google Drive (`G:`) ani plików właściciela w chmurze.
- Nie zmieniaj ustawień systemu bez zgody właściciela.

## Raport końcowy
Zapisz `C:\Users\matma\Documents\Claude\kamion\docs\owner\DISK-REPORT-2026-11-12.md`, po polsku. Zawartość:
- wolne miejsce przed i po;
- tabela top 30;
- co usunięto (ścieżka i GB);
- co czeka na decyzję właściciela (ścieżka, GB, ryzyko);
- rekomendacja, jak zapobiec nawrotowi.

Pliku nie commituj. Lider Claude go przeczyta.
