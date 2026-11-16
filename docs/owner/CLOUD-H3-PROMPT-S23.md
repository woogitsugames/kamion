# Zlecenie dla chmury „H” — runda 3 (s23, 16.11 rano) — PC

Wklej do TEJ SAMEJ sesji chmury H:
```
Runda 3. Zasady jak w rundach 1–2 (bez Unity/telefonów/Data/raw, do 5 agentów, każdy na swojej gałęzi z origin/main, NIE scalasz, raport ≤ 20 linii po polsku z DOKŁADNYMI komendami dla lidera i „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”). Najpierw HANDOVER.md (SESJA 23), CLAUDE.md, docs/reports/INTEGRATION-2026-11-15-int-pc-s23.md.
Stan main (16.11): WSZYSTKIE Twoje PR #129–#136 są scalone (lokalna integracja int-pc-s23 + pc-fix-s23, który naprawił P1 #131/#136 i błąd kompilacji CS0118 `Navigation` w Game.UI). Sprawdzone w playerze Windows: start wolny, klawiatura (W+spacja), HUD PC, tiery (dev RTX 5070: Low 535 / Medium 379 / High 334 / Ultra 194 fps — NIE referencja). Lokalnie w toku: cienie drzew Low/Medium (pc-shadows-s23) — nie dotykaj.
NIE dotykaj: generated/*, worldgen dróg, rail. Bez ProjectSettings/, Packages/, asmdef (propozycje opisz). Nowe ADR: H10=0276, H13=0277.

H10 P2 PC z integracji (gałąź pc-polish-0276, ADR 0276): (a) nakładka diagnostyczna nachodzi na tytuł i pierwszy przycisk menu — układ bez kolizji; (b) identyfikacja buildu: `Kamion.exe.sha256` jest identyczny dla każdego buildu → w build.json i nazwie zipu: git sha + hash zawartości Data (manifest sha256 plików), wypisany też w menu „Informacje” i w logu; (c) `scripts/build-windows.ps1`: generuj `Kamion-<region>.cmd` dla każdego regionu z `-Regions` (+ `Kamion-okno.cmd`); (d) małe i bezsporne P2 z REVIEW-2026-11-15-s22-code-129..136 i FIX-2026-11-15-pc-fix-s23. Testy EditMode (pisane).
H11 #113 jackknife-0228 (kontakt kabina–naczepa jako ogranicznik przegubu): merge origin/main, P1 z recenzji (docs/reports/REVIEW-2026-11-15-s22-code-*), zgodność z FFB #132; `dotnet test tools/physics-runner` musi przejść; komentarz w PR. Bez nowego ADR.
H12 #117 controls-0243 (kierownica 270/900°, lusterka jako stałe okienka, D70) i #118 perf-loop-0244 (zero GC / koszt CPU pętli jazdy): merge origin/main do obu; pogódź #117 z #131/#132/#133 (jedno źródło kąta kierownicy, lusterka spójne z HUD PC); #118 — testy GC dla nowych ścieżek wejścia PC. Komentarz w obu PR. Bez nowego ADR.
H13 bezpiecznik startu — P2 z recenzji 0262 (gałąź spawn-safety-0277, ADR 0277): docs/reports/REVIEW-2026-11-15-s23-code-spawn-fix-0262.md P2-2…P2-9 — gdy brak wolnego miejsca przed zestawem, nie stawiaj go w kolizji (szukaj wstecz do zamknięcia wjazdowego, potem komunikat dla gracza); test ścieżki starych scen bez menu i bez -route_s; test spawnu z importera; zero GC, ustawienie przed pierwszym krokiem fizyki. Testy PlayMode/EditMode (pisane).
Na końcu podsumowanie z numerami PR.
```
