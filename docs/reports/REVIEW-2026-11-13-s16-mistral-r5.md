# Recenzja i integracja Mistral — runda 5 (s16, 2026-11-13)

Gałąź integracyjna: `mistral-r5-int` (od `origin/main` 0332f7d41, po scaleniu r4), worktree `.claude/worktrees/mistral-r4-int`
(ten sam katalog co r4). Zadania: `docs/owner/MISTRAL-TASKS-5.md` (M26–M32) i `docs/owner/MISTRAL-TASK-33.md` (M33).
Wzór: `REVIEW-2026-11-13-s16-mistral-r4.md`. Komentarze po polsku są na każdym PR. M30 jeszcze nie oddany.

## Tabela PR

| PR | Zadanie | Werdykt | Poprawki integratora |
|---|---|---|---|
| #26 | M31 audyt licencji | **SCAL po poprawkach** | wzorce `*photo*`/`*plan*`/`*sheet*`… bez katalogu pokrywały też zasoby gry (np. `compare_street_vs_photo.jpg` w art-source dostawał licencję „zdjęcie referencyjne Mapillary”) → zawężone do `artifacts/**/`; nowy test na zbyt szerokie wzorce; test pokrycia z `xfail` na **twardy fail** (przy 0 niepokrytych xfail niczego nie chronił) |
| #27 | M32 audyt GC | **zmiana kodu ODRZUCONA, test przyjęty po poprawkach** | `RenderParams` to **struct** (refleksja na `UnityEngine.CoreModule.dll`: `IsValueType=True`): `new` nie alokuje, a `m_Rp == null` się nie kompiluje → `WorldInstances.cs` przywrócony. Test: brak `using Unity.Profiling`, niejednoznaczny `Object`; `Render` bez `Allocate()` → NRE (rozgrzewka przez `OnBeginCamera`); materiał bez `enableInstancing` → `InvalidOperationException`; licznik `Recorder("GC.Alloc")` |
| #28 | M28 oś trasy GPS | **SCAL po poprawce testu** | test reprodukowalności porównywał plik z buildem bez osi, a `main()` zapisuje z osiami (po regeneracji test by padł) |
| #29 | M27 zasięg nawigacji | **SCAL po poprawkach** | „poza zasięgiem” = nie da się dojechać z głównej SCC (domknięcie w przód), nie „poza SCC” — PR oznaczał 144 krawędzie, w tym jednokierunkowe jezdnie al. Tysiąclecia/Andersa/Maczka i wjazdy z krawędzi kafla, a planer je pomijał; teraz 115. Planer nie pomija krawędzi poza zasięgiem (start na wjeździe z krawędzi kafla). **EditMode się nie kompilował** (CS0234: asmdef testów EditMode nie ma `Game.UI`) → testy `NavigationService` przeniesione do PlayMode. `SetPin`: najpierw osiągalna droga w promieniu snapu. Pusta asercja `… or True` usunięta |
| #30 | M26 test oktawy audio | **SCAL** | — (legacy dosłownie z `b54a33bd~1`; obecna 63 passed, legacy 17/17 FAIL — powtórzone) |
| #31 | M29 końce barier | **SCAL po poprawkach** | cytaty § 80 / § 129 / § 262 pochodzą z rozporządzeń z 1999 i 2000 r., **uchylonych** § 117 PTB 2022 → reguła przejścia = `WORKING_VALUE`/`UNVERIFIED`; zdublowane **zapory** edge-west buduje C# `WorldEdgeBuilder` — PR ich nie naprawia (poprawiony powód xfail); marker `unit` |
| #32 | M33 pokrycie walidacji fizyki | **SCAL po jednej poprawce** | `reverse_dock_s_maneuver_comb` nie dowodził cofania: z selektorem D przechodziły wszystkie checki (`final_z_m = −7,5`) → `min_speed_kmh ≤ −2` |

## Kontrola zakazów

Żaden PR nie dotyka `Data/**/generated/**`, `*.glb`, `*_meta.json`, `ProjectSettings`, `Packages`, asmdef, LFS. #32 nie dotyka
`game/Assets/**` (0 plików). Plik `*_route.bytes` nie jest commitowany — regenerowałem go tylko do testów (v2 + osie M28 + flagi
M27 = 54,8 KB); w repo został plik z main.

## Kontrola źródeł (2026-11-13)

| Cytat | Źródło | Wynik |
|---|---|---|
| PTB 2022 § 117 uchyla rozp. MTiGM 2.03.1999 (drogi publiczne) i 30.05.2000 (obiekty inżynierskie) (#31) | api.sejm.gov.pl/eli/acts/DU/2022/1518 text.html | zgodne — cytaty #31 są historyczne; PTB 2022 § 88–90 nie ma reguły „bariera z obiektu przechodzi na drogę” |
| 92/6/EWG art. 3 ust. 1: N2/N3 ≤ 90 km/h (#32) | EUR-Lex CELEX 01992L0006-20021204 | zgodne |
| ZF TraXon 12,92…0,77, R 12,03, Intarder 4000 Nm/600 kW (#32) | zf.com Product-data-sheet_TraXon-Torque_71520.pdf | zgodne |
| Volvo D13K500 2500 Nm @ 980–1270, 368 kW, VEB+ 375 kW @ 2300 (#32) | stpi.it.volvo.com D13K500 fact sheet | zgodne |
| R13 type-0 N3 0,15v + v²/130, dm 5,0 (GRRF-56-3) (#32) | unece.org — HTTP 403 | **niesprawdzone** (podstawa zmiany statusu na SOURCED) |
| Limity PL 80/70/50 km/h (#32) | PDF Policji (źródło wtórne) | **źródło wtórne** — wymaga art. 20 PoRD z Dz.U. |
| Wiki OSM: `lanes` = suma kierunków, `turn:lanes` (r4) | — | bez zmian |

## Testy z liczbami (gałąź `mistral-r5-int`)

| Zestaw | Wynik |
|---|---|
| `uv run --project tools/licenses pytest tools/licenses/tests -q` | **9 passed**; audyt: 2383 zasoby, 2383 pokryte, 0 UNVERIFIED, 0 podejrzanych |
| navgraph + roads `pytest tools/worldgen/navgraph/tests tools/worldgen/roads/tests` | **25 passed** |
| gis `pytest tests/gis -m unit` | **82 passed, 3 xfailed** (`p21_hatch`; M29: 32 wolne końce pomostów, 1 para zapór) |
| audio `pytest tools/audio/tests` | **63 passed** (13 s); `KAMION_COMB_IMPL=legacy` → nowe testy **17/17 FAIL** |
| `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` | baseline **230/230** → po #32 **234/234** |
| Runner | baseline **115 / 607** → **119 scenariuszy / 639 checków, 0 porażek** (także po poprawce dowodu cofania) |
| `pytest tests/physics` | **26 passed** (4,5 min) |
| Unity EditMode pełny (KRTG z M27/M28) | **458: 435 passed, 8 failed, 10 skipped** — 8 znanych środowiskowych (`TruckDoorCrownTests`×3, `MirrorPresentationTests`×2, `LightPostPolicyTests`×1, `CarPaintMaterialTests.DepositionChannel`×2); Nav: 25/25 także z plikiem `.bytes` z main |
| Unity PlayMode (`NavReachabilityServiceTests`, `NavHudTests`, `HudTextAllocTests`, `HudLayoutTests`, `CabScreensTests`) | **56/56** bez `WorldInstancesRenderGcTests`; `NavReachabilityServiceTests` 3/3 także z plikiem z main |
| Unity PlayMode `WorldInstancesRenderGcTests` (po poprawkach testu) | **1/1**: 60 renderów (1 draw/render) = **0 GC.Alloc**, kontrola `new byte[64]` = 1 |

## Testy mutacyjne (mutacja lokalna, niecommitowana → oczekiwany FAIL)

| PR | Mutacja | Wynik |
|---|---|---|
| #26 | usunięty wiersz `audit-sky-boot` z LICENSES.md | `test_all_tracked_assets_covered…` **FAIL** (przed poprawką: xfail = zielono) |
| #26 | bez zawężenia wzorców `*photo*` | nowy test szerokich wzorców **FAIL** |
| #27 | `new int[4]` w `WorldInstances.Render` | **60 GC.Alloc → FAIL** |
| #28 | generator ignoruje osie jezdni | `test_region_edges_on_carriageway_axis` + reprodukowalność **FAIL** |
| #29 | zasięg = sama główna SCC (jak w PR) | 2 testy `test_reachability` **FAIL** |
| #30 | stara `comb_estimate` (`KAMION_COMB_IMPL=legacy`) | **17/17 FAIL** |
| #31 | `ROW_DUP_GAP_M` 0,5 → 0,1 | **2 FAIL** |
| #31 | brak przedłużenia za końcem pomostu | **2 FAIL** |
| #32 | `steer = 0` (dok) | `max_articulation_deg = 0` **FAIL** (zgodne z PR) |
| #32 | selektor R→D (rampa) | `final_z_m = +41,4` **FAIL** (PR: +62,7 — inna wartość, ten sam werdykt) |
| #32 | selektor R→D (dok) | przed poprawką **wszystko PASS** (PR twierdził FAIL); po dodaniu `min_speed_kmh ≤ −2` **FAIL** |

## M33 vs wcześniejsze rundy

| Runda | PR-y | Odrzucone | Wymagały poprawek lidera | Błędy kompilacji / nieuruchamialne | Fałszywe twierdzenia o weryfikacji |
|---|---|---|---|---|---|
| r3 | 6 | 1 (#19 TMP) | 3 | 1 (#19) | 2 (#17 wnioski spoza cytatu) |
| r4 | 5 | 0 | 4 (#21 #22 #23 #24) | 3 (#21 `using`, #22 `ProfilerRecorder`, #23 `IndexOutOfRange` w istniejących testach) | 1 (#24 romb = 0,42 m przy „zgodnie z Tab. 5.1”) |
| r5 (bez M33) | 6 | 1 częściowo (#27 kod) | 4 (#26 #27 #28 #29, + adnotacje #31) | 2 (#27 test ×3 błędy, #29 cały EditMode CS0234) | 2 (#27 „realna alokacja”, #31 cytaty z uchylonych aktów jako obowiązujące) |
| **M33 (#32)** | 1 | 0 | **1** (dowód cofania) | **0** — `dotnet`, Runner i pytest uruchomione, liczby A/C/D zgodne co do sztuki | **1** (mutacja R→D na doku: deklarowany FAIL, w rzeczywistości PASS) + GRRF-56-3 niedostępne do sprawdzenia |

Wniosek: zadanie „jedno duże, w całości uruchamialne, z obowiązkową weryfikacją” dało wyraźnie lepszy wynik niż krótkie zadania
z kodem Unity, którego Mistral nie może skompilować. Pozostały błąd jest tego samego rodzaju co w #16 (test nie łapie tego, co
deklaruje), mimo tabeli mutacji. Wniosek dla kolejnych rund: wymagać wklejenia **surowego wyjścia** Runnera dla każdej mutacji,
a nie tylko tabeli.

## Osobne zadania wynikłe z recenzji

1. Lider: regeneracja `bialystok-industrial-c_route.bytes` (osie M28 + flagi M27; `uv run --project tools/worldgen python
   tools/worldgen/navgraph/build_route_graph.py --region bialystok-industrial-c`), potem usunąć wariant „legacy” w
   `test_region_file_is_reproducible`; ocena linii trasy na minimapie na rozwidleniach (19 węzłów z rozrzutem końców krawędzi
   > 1 m, maks. 8,2 m).
2. M28: planer C# liczy koszt z długości geometrii (`GeomLength`), nie z `length_m` — z osiami różnica do 5,64 m na krawędź
   (72 krawędzie > 1 m); twierdzenie „koszt A* bez zmian” dotyczy tylko Pythona.
3. Lider: regeneracja świata po #31 (przejście pomost → dojazd) + zdjęcie xfail wolnych końców; zdublowane **zapory** edge-west
   (ADR 0141 P2) — poprawka w C# `WorldEdgeBuilder.ReadExits` (nowe zadanie).
4. Fizyka: `reverse_dock_s_maneuver_comb` kończy się złożeniem na odboju (91,2–91,6°); `reverse_grade6pct_comb` przy celu 4 km/h
   cofa ~8,2 km/h — sprawdzić utrzymanie prędkości na wstecznym.
5. Źródła: GRRF-56-3 (unece.org 403) — potwierdzić tabelę type-0 N3 innym dostępem; limity PL z art. 20 PoRD (Dz.U.) zamiast
   PDF Policji; § 80/§ 262 (#31) — znaleźć obecną podstawę (wytyczne GDDKiA dla barier).
6. #27: pozostałe pozycje tabeli audytu GC nie były weryfikowane pomiarem — rozszerzyć testy `Recorder("GC.Alloc")` na fizykę,
   audio i kamerę w PlayMode.
7. Testy `ZeroGc_*` nawigacji nadal na `GC.GetAllocatedBytesForCurrentThread()` (z r4).
