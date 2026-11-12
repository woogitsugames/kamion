# M7 — weryfikacja „błędów fizyki z testów M5” (gałąź `mistral/7-physics-bugfix`)

Data: 2026-11-12. Autor: Vibe Code (sesja M7).

## Wniosek

**Wejście (PR #5, gałąź `mistral/5-physics-tests`) nie zawiera żadnego testu oznaczonego `Skip`. Nie ma więc błędu produkcyjnego do naprawy — tabela błąd → przyczyna → poprawka jest pusta.** Nie wprowadzono żadnej zmiany w rdzeniu fizyki (`game/Assets/_Project/Vehicle/Physics/**`) ani w testach.

## Weryfikacja wejścia

1. `git diff origin/main...origin/mistral/5-physics-tests --stat` → **1 plik**: `tools/physics-runner/Tests/CorePhysicsTests.cs` (+1025 linii). Żadnych zmian w kodzie produkcyjnym.
2. `grep -rn "Skip *="` na pliku testów w **każdym z 3 commitów** gałęzi (`50e734a1`, `f0d5a1a5`, `38bc1dd4`) → **0 trafień**. Jedyny „Skip” w pliku to `maxSkip` (asercja `amt.TargetGear <= 3 + amt.Def.maxSkip`, linia 270) — to limit skip-shiftu AMT, nie atrybut xUnit.
3. Treść PR #5 (sekcja „Znalezione błędy”): cytat — „**Brak.** … Żaden test nie został oznaczony `Skip`.”, a w sekcji weryfikacji: CI run 43249694761, job `physics`: `dotnet test` — **Failed: 0, Passed: 214, Skipped: 0, Total: 214**, następnie `dotnet run --project tools/physics-runner/Runner` — wszystkie scenariusze PASS.
4. Komentarze i review PR #5 (`gh api .../pulls/5/reviews`, `.../issues/5/comments`) → puste.
5. Na `main` również `grep -rn "Skip" tools/physics-runner/Tests/*.cs` → 0 trafień (poza `maxSkip`).

## Skąd wzięło się zamieszanie

Podczas pisania testów autor gałęzi znalazł 4 rozbieżności i **wszystkie 4 okazały się złymi oczekiwaniami testów, nie błędami produkcji** — poprawione w commicie `38bc1dd4` („fix 4 wrong test expectations”):

| Pozycja | Złe oczekiwanie testu | Poprawka w `38bc1dd4` |
|---|---|---|
| over-rev upshift z 3. biegu | `Assert.Equal(4, amt.TargetGear)` | `TargetGear > 3 && <= 3 + maxSkip` (upshift, ew. skip-shift) |
| czas grzania sprzęgła do przepalenia | pętla 2000 iteracji (20 s) | 20000 iteracji (200 s) przy 50 kW poślizgu |
| `LowPressureWarning` po opróżnieniu układu | oczekiwane od razu po `Charge(0)` | dodatkowe `air.Update(...)` — warning jest liczony w `Update` |
| `MathUtil.MoveTowards(0, 5, 2)` | oczekiwane 5 | oczekiwane 2 (delta = krok, nie cel) |

## Tabela zadania (pusta)

| Błąd | Przyczyna (plik:linia) | Poprawka | Wpływ na scenariusze |
|---|---|---|---|
| — brak: 0 testów `Skip` w PR #5 | — | — (brak zmian w rdzeniu) | brak — goldeny nietknięte |

## Weryfikacja lokalna / CI

- Sandbox tej sesji nie ma SDK .NET (`which dotnet` → brak), więc lokalne `dotnet test` nie było możliwe — oznaczone jako niemożliwe lokalnie, zweryfikowane przez CI.
- CI gałęzi `mistral/7-physics-bugfix` (job `physics`, `.github/workflows/ci.yml`): `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` oraz `dotnet run -c Release --project tools/physics-runner/Runner` — wyniki w PR.
- Dodatkowo, jako źródło zewnętrzne: CI PR #5 (run 43249694761) już wykonało pełny zestaw 214 testów (w tym 50 nowych metod z `CorePhysicsTests.cs`) z wynikiem **Skipped: 0** — potwierdza, że żaden test fizyki nie jest pomijany.
