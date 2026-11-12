# Recenzja i integracja Mistral — runda 6 (s16, 2026-11-13)

Gałąź integracyjna: `mistral-r6-int` (od `origin/main` 5921ac06c), worktree `.claude/worktrees/mistral-r6-int`.
Zadania: `docs/owner/MISTRAL-TASKS-6.md` (M34–M38, obowiązkowa weryfikacja A–E). Wzór: r4/r5.
PR-y niescalone na GitHubie — zamknie je lider po scaleniu gałęzi. Komentarz po polsku jest na każdym PR.

## Tabela PR

| PR | Zadanie | Werdykt | Poprawki integratora (osobne commity) |
|---|---|---|---|
| #33 | M35 nav-runner | **SCAL po poprawkach** (najwięcej w rundzie) | **Nie kompilował się** (CS0119 w shimie mimo commita „fix CS0103”; CS1503 ×2 — NUnitowe `Assert.Equal(…, msg)` w xUnit). Po kompilacji **17/80 testów czerwonych**: `NavVoice.BandFor` brał największe pasmo (450 m → „za 2 km”); nazwa ronda dla B14 z `ManName` (to ulica wylotowa); `GraphReport` podawał nieskierowane id krawędzi do `StartNode/EndNode` (7 fałszywych „podejrzanych” zakazów); test ETA z błędnym oczekiwaniem; test 0 GC mierzył asercje xUnit (2688 B); Runner mierzył własny `Stopwatch` (40 B). **Trasy wzorcowe z „wiernego portu” planera w Pythonie** — 11/36 niezgodnych z C# (28/36 po grafie M27/M28 z main); nagrane z C# (`Runner -- --write-golden`), 5 uzasadnień poprawionych po kontrfaktach; nowy test kontrfaktyczny no-truck (G02); komentarz `SignedAngle` w shimie odwrócony (+ = przeciwnie do zegara); brak raportu `NAV-RUNNER-*.md` |
| #34 | M36 audyt przepisów | **SCAL po drobnych poprawkach** | stała `SHOULDER_W` była **nieużywana** — profil RURAL czyta teraz `SHOULDER_W["GP"]` zamiast literału 0.75 (ta sama wartość, bez regeneracji); raport: P-10 to **§ 35** (nie § 34), przejazd rowerowy 1,80/3,00 m to **§ 45 ust. 2** („§ 34 ust. 6” nie istnieje), pasy wyłączania **§ 63 ust. 4** z 2,0 m/s² dla klas innych niż A/S (region = GP); docstring testu krawężnika (§ 89 to warunek odległości bariery, nie wymóg wysokości); Dz.U. 2020 poz. 862 (korekta t.j.) odnotowana |
| #35 | M38 perfgate | **SCAL po poprawkach** | twierdzenie „ADR 0152 nie ma w repo” — **fałsz** (jest w main i w bazie gałęzi); „naprzemienność” zdefiniowana na `frame_ms`, a ADR 0152 mierzy pozę kamery (`campose.py`) — na pomiarach A16 z ADR metryka M38 daje 60,5 % (z błędem) vs 63,0 % (po poprawce); dodany port `campose.py` + test na prawdziwych danych A16 (15,6 % / 10,6 % → 0,0 %); warm-up domyślnie z `metrics.json` (stałe 5 s dawało inne liczby niż `metrics.json`, np. base0 n 3217 vs 2603) |
| #36 | M37 walidator świata | **SCAL po poprawkach** | top błędów na trasie G3 to **fałszywe alarmy**: 5 tablic bramownic/portali (`kind: sign_gantry`, wiszą nad jezdnią) i latarnia z `skipped: carriageway` (niezbudowana); „ADR 0146 nie istnieje” — **fałsz**; jego Open (4 ściany terenu 0,32–0,35 m) walidator pomijał (próg 0,50 vs 0,15 generatora) + format `verge_strips.worst` (4 pola) odrzucany warunkiem `len >= 5`; precyzja „40/40, 0 FP” niepotwierdzona; 2 nowe testy |
| #37 | M34 odporność fizyki | **SCAL** (poprawka tylko raportu) | liczby A–D zgodne co do sztuki; oba repro odtwarzają się; **F1** = miękki ogranicznik z założenia (komentarz `Limit` w `FifthWheel.cs`) → decyzja o tolerancji, nie dowód błędu; **F2** potwierdzony (275 km/h w powietrzu bez napędu); odwołanie `FifthWheel.cs:214-216` → `:210` |

## Kontrola zakazów

Żaden PR nie dotyka `Data/**/generated/**`, `*.glb`, `*_meta.json`, `ProjectSettings`, `Packages`, asmdef, `.gitattributes`, LFS.
#33 zmienia `game/Assets/_Project/Core/Navigation/*` (dozwolone) i dodaje `NavEta.cs`/`NavVoice.cs` (+ `.meta`). #34 zmienia tylko
`standards.py` (+ moja poprawka w `network.py`, wartość bez zmian). #36 zapisuje wyjście do `docs/reports/world-validator/`.
#37 nie dotyka `game/**`. `*_route.bytes` nie commitowany (regeneracja do testu dała plik identyczny z main).
**Uwaga:** #33 rozgałęził się od `abe711ade` (przed scaleniem r5), choć PR pisze „brak origin/mistral-r5-int” — gałąź istniała.

## Kontrola źródeł (ELI/ISAP, 2026-11-13)

| Cytat | Źródło | Wynik |
|---|---|---|
| PTB2022 § 23 ust. 10 pkt 1–5 i ust. 3 pkt 2 (GP: opaska zewnętrzna + gruntowa) (#34) | api.sejm.gov.pl/eli/acts/DU/2022/1518 text.html | zgodne — 0,75 m dla GP jednoznaczne |
| § 20 ust. 2, § 29 ust. 1, § 33, § 62 ust. 2, § 80 ust. 1, § 89 ust. 2 pkt 1 (#34) | jw. | cytaty zgodne (§ 89 użyty ponad treść — poprawione w docstringu) |
| § 34 / „§ 34 ust. 6” / § 62 (pasy wyłączania) w raporcie #34 | jw. | **błędne numery**: § 35, § 45 ust. 2, § 63 ust. 4 (+ 2,0 m/s² poza A/S) |
| Dz.U. 2025 poz. 1352: § 13 ust. 1 pkt 3, § 23 ust. 10 pkt 5, § 34 ust. 2–3 (#34) | DU/2025/1352 text.pdf | zgodne |
| Zał. 1 Tab. 1.11 po Dz.U. 2021 poz. 2066 (2,00 / 2,20 / 5,00 m) (#34) | DU/2021/2066 text.pdf | zgodne |
| Dz.U. 2021 poz. 438 zmienia tylko zał. 1 (#34) | DU/2021/438 text.pdf | zgodne; tekst powołuje też **Dz.U. 2020 poz. 862** (skreśla rys. 5.2.6.11/12 zał. 1) — nieuwzględnione w zadaniu ani PR |
| PTB2022 § 79 ust. 1 — pasy bezpieczeństwa skrajni 0,50 m (`SKRAJNIA_M`, #36) | jw. | zgodne (PR nie podał paragrafu) |
| Profil 80/70/50 km/h, art. 20 PoRD (#33 `NavEta`) | — | PR oznacza UNVERIFIED (uczciwie); dalej niesprawdzone |
| Wartości regionu: maxspeed 90/70/50 = 3/63/454 krawędzi, `trunk_link` 31 (#34) | `roads.graph.json` | zgodne (50 obejmuje 379 domyślnych) |

## Testy z liczbami (gałąź `mistral-r6-int`, ac1781123)

| Zestaw | Wynik |
|---|---|
| `dotnet test tools/nav-runner/NavRunner.sln -c Release` | PR: **nie kompiluje się** → po poprawkach kompilacji 63/80 → **81/81** |
| `dotnet run … nav-runner/Runner` | PR: 11 niezgodności golden, 40 B GC, exit 2 → **36/36 golden, 0 B GC, ALL OK** |
| Unity EditMode pełny (po #33) | **467: 444 passed, 8 failed, 10 skipped** — 8 znanych środowiskowych jak r5; **Nav\* 25/25** (NavVoice/NavEta kompilują się w Unity) |
| Unity PlayMode (`NavReachabilityServiceTests`, `NavHudTests`, `HudTextAllocTests`, `HudLayoutTests`, `CabScreensTests`) | **56/56** |
| `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` | 234 (main) → **256/256** (zgodne z PR) |
| physics Runner | **127 scenariuszy / 707 checków, ALL PASSED** (zgodne z PR); `scenarios_expected_fail`: oba repro FAIL zgodnie z opisem (91,418°; 275,37 km/h) |
| `pytest tests/physics` | **26 passed** (4,6 min; PR: 12 passed, 14 skipped — środowisko Mistrala bez części danych) |
| `uv run --project tools/perf pytest tools/perf/tests` | 38 (PR, zgodne) → **43 passed**; `mutation_check.py` **15/15 zabitych** (zgodne); `history` na 2 korzeniach = 62 pomiary (zgodne) |
| gis `pytest tests/gis -m unit` | 82 (main) → **97 passed, 3 xfailed** (zgodne z PR #34) |
| gis pełne | **937 passed, 33 skipped, 4 xfailed, 1 failed** — `test_report_not_stale` (znane; czeka na regenerację świata); `test_every_gate3_sign_is_placed` przechodzi w tym worktree |
| navgraph + roads tests | **25 passed** |
| licenses | **9 passed** |
| walidator świata (region) | PR: 558 (error 61, 61 na trasie) → **558 (error 56 / warn 88 / info 414, 56 na trasie)**, 0,7–0,9 s |

## Testy mutacyjne (lokalne, niecommitowane)

| PR | Mutacja | Wynik |
|---|---|---|
| #33 | `IsOneway` → false | 5 FAIL (golden G22/G31, raport grafu, 2 routing) |
| #33 | zakazy skrętu wyłączone | **1 FAIL** (tylko syntetyczny) — żadna z 36 tras wzorcowych nie zależy od zakazu skrętu |
| #33 | `BandFor` jak w PR | 2 FAIL |
| #33 | nazwa ronda z `ManName` (jak w PR) | 1 FAIL |
| #33 | `HasExit` nie liczy wylotów | 32 FAIL |
| #33 | ETA bez limitu OSM | 2 FAIL |
| #33 | planer ignoruje no-truck | 7 FAIL (w tym nowy test kontrfaktyczny G02) |
| #34 | GP 0,75 → 1,25 / Z 1,00 → 1,25 / `SIGN_H_MIN` 1,50 / skrajnia A 4,50 / krawężnik 0,10 | FAIL / FAIL / FAIL / FAIL / FAIL (5 z tabeli PR, zgodne) |
| #35 | znak `a*b>0` w `pose_alternation_frac` | 3 FAIL |
| #35 | warm-up bez `metrics.json` | 2 FAIL |
| #36 | pomijanie bramownic wyłączone | 1 FAIL |
| #36 | `len(wv) >= 5` / próg 0,50 m | 1 FAIL / 1 FAIL |
| #37 | seed PRNG z zegara | 4 FAIL (w tym `SameScenario_Twice_IsBitIdentical`) — zgodne z M9 |
| #37 | `DtSweep` substepy = 1 | 6+ FAIL — zgodne z M10 |
| #37 | metryka friction ratio ×0,5 | 1 FAIL (test metryki) |

## Trasy wzorcowe #33 — kontrola 6 tras na grafie (kontrfakty: bez zakazów skrętu / bez flag no-truck)

| Para | Twierdzenie PR | Wynik |
|---|---|---|
| G02 | „zakaz zawracania przez pas dzielący” → rondo Bieżeństwa zjazd 4 | trasa zgodna; przyczyną jest **flaga no-truck** na przejeździe przez pas dzielący (bez niej 1706 m zamiast 3785 m) — doprecyzowane, nowy test |
| G03 | Putry zjazd 2., al. Tysiąclecia | **zgodne** |
| G05 | „only_* 274→279 wymusza wejście” | **fałsz** — trasa nie jedzie krawędzią 274; bez zakazów identyczna |
| G08 | „Wileńska, potem ostry w lewo” | **fałsz** — w lewo (−88°) w Grodzieńską, potem w prawo w Kowieńską |
| G17 | „trasa omija zakaz no-truck” | **puste** — bez flag no-truck trasa identyczna |
| G18 | „hgv=no omijany, zakaz 135→141 respektowany” | **puste** — start na krawędzi 141; bez zakazów i flag identyczna |

## r6 vs r4/r5

| Runda | PR-y | Odrzucone | Wymagały poprawek lidera | Błędy kompilacji / nieuruchamialne | Fałszywe twierdzenia o weryfikacji |
|---|---|---|---|---|---|
| r4 | 5 | 0 | 4 | 3 | 1 |
| r5 (+M33) | 7 | 1 częściowo | 5 | 2 | 3 |
| **r6** | 5 | 0 | **4** (#33 duże, #35 #36 średnie, #34 drobne; #37 tylko raport) | **1** (#33: projekt i testy się nie kompilowały, 17 czerwonych po kompilacji) | **4**: #33 (A–E „patrz raport”, którego nie ma; golden „verified against the C# runner in CI” — nie były), #35 (ADR 0152 „nie istnieje”), #36 (ADR 0146 „nie istnieje”, precyzja 100 %), #34 (3 błędne numery paragrafów w raporcie — cytaty w testach poprawne) |

Wniosek: zadania „bez Unity, w całości uruchamialne” (M34, M36, M38) dały liczby zgodne co do sztuki z PR (testy, mutacje,
runner) — wyraźna poprawa wobec r4/r5. Słabe punkty się powtarzają: (1) twierdzenia o nieistnieniu plików bez sprawdzenia
(`ADR 0146`, `ADR 0152`, `mistral-r5-int`) — dwa z nich sprawiły, że kontrola czułości/definicja poszła obok tego, co
naprawdę mierzył ADR; (2) M35 — jedyne zadanie z kodem C#, który Mistral mógł skompilować dzięki nowemu nav-runnerowi —
i tak oddane bez uruchomienia (wynik jak w r4). (3) Uzasadnienia tras/znalezisk pisane „z intencji”, nie z danych
(G05/G08/G17/G18, top fałszywych alarmów walidatora). Zalecenie na r7: wymagać w opisie PR **surowego wyjścia** komend C
(nie tabel) i listy plików, których „nie ma”, z komendą `git ls-tree origin/main <ścieżka>`.

## Otwarte (dla lidera)

1. Regeneracja świata (już zaplanowana): `test_report_not_stale` obejmuje teraz też `network.py`/`standards.py`; geometria
   z #34 bez zmian (ta sama wartość 0,75).
2. #37 F1: decyzja o tolerancji miękkiego ogranicznika przegubu (0,6–3,3° nadmiaru; `jackknife_wet_curve_noabs` też 92,1°)
   lub sztywniejszy stop; F2: wstrzykiwanie energii przy wywrotce — zadanie dla fizyki (przyczyna niepotwierdzona).
3. #33: `HasExit` liczy wszystkie wyloty ronda („any vehicle”), zadanie mówiło „tylko dostępne dla pojazdu” — kod nie zmieniony,
   komentarz testu twierdził inaczej; do decyzji (kierowca liczy fizyczne wyloty). Golden nie pokrywa żadnego zakazu skrętu.
   `RouteTracker.Update` liczy ETA w O(liczby punktów trasy) co klatkę (0 GC, koszt CPU niezmierzony na telefonie).
   Pasma głosowe: 6 komunikatów na manewr (2 km…100 m + teraz) — do oceny „na ucho”. `--write-golden` zapisuje wcięcie 2
   (plik ma 1) — duży diff przy pierwszym nagraniu. Raport `NAV-RUNNER-*.md` nie powstał.
4. #36: „drzewa w jezdni” (53) liczone z koron `plot_canopy.json` i pasa wokół osi grafu — sprawdzić na kamerach;
   `duplicate_parallel` (342 info) porównuje linie wejściowe OSM/BDOT, nie wygenerowane chodniki.
5. #35: `history`/`compare` dla starych pomiarów zmieniają liczby, jeśli ktoś cytował wyniki z warm-up 5 s przy
   `metrics.json` z 25 s (base0). Naprzemienność ADR 0152 w raporcie tylko, gdy w katalogu jest `campose.csv`.
6. M30 (r5) nadal bez PR.

Gotowe do scalenia: **TAK** (`git merge --no-ff origin/mistral-r6-int`; po scaleniu zamknąć #33–#37).
