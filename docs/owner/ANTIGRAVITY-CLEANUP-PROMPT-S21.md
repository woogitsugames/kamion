# Zlecenie dla sesji Antigravity (lokalnie): sprzątanie dysku C:, s21, 15.11 wieczór

Wklej:
```
Repo: C:\Users\matma\Documents\Claude\kamion (Kamion, Unity). Na tej maszynie RÓWNOLEGLE pracują: lider Claude, 5 jego agentów, 2 sesje Codex. Twoje zadanie: odzyskać miejsce na C: bez utraty danych i bez przeszkadzania działającym sesjom. Komunikacja po polsku, godziny w czasie Brukseli. Nie zmieniaj kodu, nie pushuj na main, nie uruchamiaj Unity ani adb.

STAN: 15.11 18:2x C: miał 237 GB wolne, rano 489 GB. Główna przyczyna to worktree agentów w .claude/worktrees/*: każdy ma własne game/Library (~9 GB, z buildem Androida do ~14 GB) i kopie danych świata. Uwaga: G: to Google Drive for Desktop, a jego cache leży na C:. G: pokazuje to samo wolne miejsce, to nie jest osobny dysk.

ZASADY BEZPIECZEŃSTWA (twarde):
1. Używaj PowerShell (nie Git Bash) do usuwania i `cmd /c rmdir`.
2. JUNCTIONS: worktree mają junctions Data\raw (całe albo podkatalogi gugik/osm/mapillary) wskazujące na Data\raw w głównym katalogu. To godziny pobrań spoza gita. Przed usunięciem worktree: `Get-ChildItem <wt> -Recurse -Attributes ReparsePoint -ErrorAction SilentlyContinue` (Data/, game/, art-source/, tools/), każdy reparse point odłącz `cmd /c rmdir "<ścieżka>"` (najgłębsze najpierw), sprawdź, że nie ma już żadnego, i dopiero wtedy usuwaj. Po każdym usunięciu sprawdź, że C:\Users\matma\Documents\Claude\kamion\Data\raw nadal istnieje i ma tę samą liczbę podkatalogów co przed startem (zapisz ją na początku).
3. ARTEFAKTY: przed usunięciem worktree skopiuj jego `artifacts\` (robocopy /E /XO) do C:\Users\matma\Documents\Claude\kamion\artifacts\ (scal; nie nadpisuj nowszych), a niezacommitowane pliki (`git -C <wt> status --short`) zapisz jako patch do artifacts\cleanup-s21\<nazwa>\uncommitted.patch (+ kopie plików nieśledzonych poza Library/Temp/obj). Zdjęcia z telefonu i nagrania są bezcenne.
4. Usuwanie worktree: `git worktree unlock <wt>` (jeśli zablokowany), `git worktree remove --force --force <wt>`, na końcu `git worktree prune`. GAŁĘZI nie usuwaj (ani lokalnie, ani na origin).
5. NIE DOTYKAJ (aktywne, nawet ich Library): budget-fix-s21, tunnel-0211, summer-led-0216, verify-cloud-c, rail-fix-s21, fix-pr95-96-s21, knyszyn-rynek-0227, codex-refs-s21, ani żadnego worktree utworzonego lub zmienionego w ostatnich 2 godzinach (sprawdź LastWriteTime plików poza Library) ani żadnego, w którym działa proces Unity/python/pwsh (sprawdź `Get-Process | ? Path` i `Get-CimInstance Win32_Process` CommandLine z jego ścieżką). Nie ruszaj głównego katalogu repo poza artifacts\cleanup-s21\ i opisanymi niżej kopiami.

LISTA A — worktree do usunięcia (gałęzie scalone do main albo zakończone weryfikacje; sprawdź jeszcze raz `git merge-base --is-ancestor <gałąź> main` dla scalonych):
ddr-0188, dk65-tiles2-0214, dojgreen-0186, forest-0187, gates-s19, hospgate-0189, mistral-fix-s21, sigplate-0193, stains-0194, truckdata-0201, water2-0213 (scalone); verify-a, verify-cloud-b (weryfikacje zakończone, gałęzi nie scalać — tylko zachować na origin; jeśli verify-cloud-b ma niewypchnięte commity, zrób `git -C <wt> push origin HEAD` przed usunięciem).
gpt-edge-r2: to NIE jest zarejestrowany worktree, tylko osierocony katalog (ma tylko artifacts/). Skopiuj artifacts do artifacts\cleanup-s21\gpt-edge-r2\ i usuń katalog.
Przed każdym usunięciem zapisz rozmiar (GB) i wynik kroków 2–3 w raporcie.

LISTA B — tylko zmierz i zaraportuj, NIE usuwaj bez zgody lidera:
- top 25 największych katalogów na C: (poza Windows i Program Files), m.in. C:\Users\matma\AppData\Local\Temp, Unity cache (%LOCALAPPDATA%\Unity\cache, ...\Unity\Caches\GiCache), Gradle (%USERPROFILE%\.gradle\caches), uv cache (`uv cache dir`), npm/pip cache, cache Google Drive, artifacts\ w repo (podział na podkatalogi), artifacts\apk (stare APK), Data\raw;
- dla każdej pozycji: rozmiar, czy da się bezpiecznie odtworzyć, rekomendacja.
Wyjątek (wolno usunąć od razu): pliki w %TEMP% starsze niż 3 dni, których nie trzyma żaden proces (pomijaj zablokowane), oraz `uv cache prune` (bez `clean`).

RAPORT: docs/reports/CLEANUP-2026-11-15-s21.md (tylko plik w głównym katalogu, bez commitu; lider zacommituje): wolne GB przed/po, tabela usuniętych worktree (rozmiar, artefakty skopiowane, patch, junctions odłączone), liczba podkatalogów Data\raw przed/po (musi być równa), lista B z rekomendacjami. Postęp dopisuj na bieżąco w artifacts\live\antigravity-cleanup-s21.md (godzina, co zrobione, następny krok). Na końcu wypisz, ile GB odzyskano.
```
