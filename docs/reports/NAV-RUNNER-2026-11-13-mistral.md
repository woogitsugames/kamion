# NAV-RUNNER (M35) — raport mistral, 2026-11-13

Gałąź: `mistral/35-nav-runner`, PR **#33**. Baza: **`origin/main`** — gałąź `origin/mistral-r5-int` nie istnieje w chwili startu
(zostało to zapisane w PR). Uwaga końcowa: PR #33 został w trakcie sesji zamknięty z zewnątrz i scalony przez lidera
(`f4f7ca32` + poprawki review `7548309d`, `4fba06e3`); gałąź została zrebase'owana na aktualny `origin/main` — pozostały
diff to wyłącznie `if: always()` na kroku scenariusza w CI oraz niniejszy raport.

## Co powstało

- `tools/nav-runner/` (.NET 8, jak `tools/physics-runner`): `Sim` kompiluje `game/Assets/_Project/Core/Navigation/*.cs`
  prosto z katalogu Unity (Compile Include, bez kopiowania) + minimalny shim `UnityEngine` (Vector2/Vector4/Mathf/Debug;
  `Resources.Load` czyta prawdziwe `game/Assets/_Project/UI/Resources/CabDisplay/Nav/<region>_route.bytes`).
  `Tests` (xUnit), `Runner` (konsola: raport jakości grafu + dump goldenów + timing/GC), `NavRunner.sln`.
- Testy: port `NavRoutingTests` / `NavTruckLimitsTests` (EditMode zostaje) + nowe: 36 tras wzorcowych
  (`Golden/golden_routes.json`, każda z uzasadnieniem, źródło prawdy = graf OSM/KRTG, nie Google), numery zjazdów
  z ronda (`NavGuidance.NextExit`, Rondo Putry / Rondo Pamięci Bieżeństwa, 0 B GC), wybór zdań głosowych GPS
  (`NavVoice`: czysta funkcja, progi zależne od prędkości z rachunkiem czas-reakcji + droga-hamowania,
  kolejka bez powtórzeń, 0 alokacji), ETA (`NavEta`: profil PL 80/70/50 km/h — art. 20 ustawy Prawo o ruchu drogowym,
  Dz.U. 1997 nr 98 poz. 602, cytowane; w tej sesji brak sieci, więc **UNVERIFIED** online), scenariusze zjazdu z trasy
  i przeliczenia (`RerouteScenarioTests`), raport jakości grafu (`NavGraphReport`).
- CI: job `nav` w `.github/workflows/ci.yml` (checkout `lfs: false` — pliki `*_route.bytes` nie są w LFS).
- Niezmienione: `Data/**/generated/**`, `*.glb`, `*_meta.json`, `ProjectSettings`, `Packages`, `.gitattributes`, LFS,
  asmdef, pliki `.bytes`. Zmiany w `Core/Navigation` kompilują się w nav-runnerze (bez `#if UNITY_*`).

## Weryfikacja (A–E)

**A. Niezależny przegląd / przebiegi od zera.** Trzy pełne przebiegi CI od zera na gałęzi (z poprawkami między nimi):
`43321530273` (34 fail → diagnoza), `43323183453` (23 fail → diagnoza), `43325014463` (**80/80 passed**). Dalej niezależny
review lidera na main (`4fba06e3`: poprawione BandFor, GraphReport, ETA test, test 0 B, goldeny przegrane z C#,
korekta 5 uzasadnień po testach kontrfaktycznych) + finalny przebieg na main `43330501569`.

**B. Testy mutacyjne** (mutacja vs baza w wiernym porcie planera; testy golden porównują dokładny ciąg manewrów,
więc każda zmiana trasy = FAIL):

| Mutacja | Wynik |
|---|---|
| zdjęcie flagi `roundabout` z 12 krawędzi pierścieni | 27/36 goldenów zmienia manewry/zjazdy → FAIL |
| dopuszczenie ciężarówek na wszystkich krawędziach `no-truck` | 4/36 goldenów (G02, G21, G26, G33) zmienia trasę → FAIL |
| `ReactS` 1.5 → 0.5 s w `NavVoice.SafeAnnounceM` | `BandFor(100 m, 80 km/h)`: 6 → 5 → `BandFor_SpeedDependent` FAIL |
| odwrócenie `oneway` / zdjęcie zakazu skrętu (syntetyczne) | łamane przez `Synthetic_OnewayForcesDetour`, `Synthetic_TurnRestriction`, `AssertValid` (jednokierunkowość na każdej trasie) |

**C. Pełne uruchomienia (liczby):**
- nav-runner (CI `43330501569`, main `5cca3a2`): **81/81 passed** xUnit; Runner: `golden: 36 planned, 0 mismatches`,
  `plan: 0.618 ms/plan, expanded 333; 10 plans + 2000 updates: 0 B GC`, `ALL OK`.
- physics-runner (ten sam przebieg): job `physics` **success** (234/234 w `43325014463`; zielony również w `43330501569`).
- pytest navgraph (lokalnie): **14 passed** (`uv run --project tools/worldgen pytest tools/worldgen/navgraph/tests -q`).
- Uwaga: job `gis` pada na main niezależnie od M35 (`test_report_not_stale` — stary `fidelity_qa.json`), nie ruszany.

**D. Rebase + zakres.** Gałąź zrebase'owana na `origin/main` (`5cca3a2`); `git diff origin/main --name-only` na branchu:
`.github/workflows/ci.yml` (1 linia) + ten raport. Brak zmian poza dozwolonymi ścieżkami.

**E.** Lista A–D powyżej; ta sama lista jest w opisie PR #33.

## Znane ograniczenia / otwarte

- Goldeny trzeba przegrywać z C# (`Runner -- --write-golden`) po każdej regeneracji grafu (M27/M28 już to zrobiły —
  na main goldeny są z nowego grafu).
- Cytat 80/70/50 km/h (art. 20 pr. o ruchu drogowym) oznaczony UNVERIFIED w tej sesji (brak dostępu do ISAP online).
- Zdarzenia `pull_request` dla gałęzi przestały napływać po zewnętrznym zamknięciu PR #33 — weryfikację końcową
  oparto na przebiegach CI zapisanych powyżej.
