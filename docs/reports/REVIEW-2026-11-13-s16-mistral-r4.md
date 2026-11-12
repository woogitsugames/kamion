# Recenzja i integracja Mistral — runda 4 (s16, 2026-11-13)

Gałąź integracyjna: `mistral-r4-int` (od `origin/main` 700517b22), worktree `.claude/worktrees/mistral-r4-int`.
Zadania: `docs/owner/MISTRAL-TASKS-4.md` (M21–M25). Wzór: `REVIEW-2026-11-12-s15-mistral-r3.md`.
Komentarze po polsku są na każdym PR (`gh pr comment`). PR-y niescalone na GitHubie — zamknie je lider po scaleniu gałęzi.

## Tabela PR

| PR | Zadanie | Gałąź | Werdykt | Poprawki integratora (osobne commity / merge) |
|---|---|---|---|---|
| #24 | M24 wymiary znaków + duplikat `concrete_pole` | `mistral/24-signs-sizes` | **SCAL po poprawce** | `SIGN_SIZE["diamond"]` 0,60 → **0,60·√2 = 0,849 m**: w siatce (`props.plate`, `gate3_landmarks._outline`, `furniture`) wartość to przekątna rombu, więc 0,60 dawało bok D-1 = 0,42 m zamiast 0,60 m; test audytu porównuje bok (`/√2`) |
| #25 | M25 P-11 0,50/0,50 m, nowelizacje zał. 2, łącznice ≤ 6 % | `mistral/25-markings-p11` | **SCAL** | — |
| #21 | M21 limity ciężarówki w routingu (KRTG v2) | `mistral/21-nav-truck-limits` | **SCAL po poprawkach** | brak `using System;` w `NavTruckLimitsTests` (`FormatException` — błąd kompilacji); limity tylko z tagów `src=osm`; wspólny format v2 z #23 |
| #23 | M22 pasy `turn:lanes` (KRTG v2) | `mistral/22-nav-lanes` | **SCAL po poprawkach** | ręczne połączenie z #21 w jeden KRTG v2; semantyka pasów (niżej); `BuildAdjacency` uzupełnia tablice pasów/limitów (bez tego `IndexOutOfRange` w planerze we wszystkich istniejących testach budujących graf w kodzie) |
| #22 | M23 HUD bez alokacji, bez TMP | `mistral/23-hud-zero-alloc-text` | **SCAL po poprawce testu** | `HudTextAllocTests`: `ProfilerRecorder` jest w `Unity.Profiling` (plik miał tylko `using UnityEngine.Profiling` → błąd kompilacji), a dla markera liczy czas, nie liczbę próbek → licznik `Profiling.Recorder("GC.Alloc").sampleBlockCount` jak w r3; odjęta baza `FieldInfo.SetValue` (uprząż testu); dodany test kontrolny „stara konkatenacja alokuje”; overlay: etykieta jakości bramkowana `QualitySettings.GetQualityLevel()` (`QualityTiers.Current` → `QualitySettings.names` = 5 GC.Alloc na odświeżenie) |

## Kontrola zakazów

Żaden PR nie dotyka `Data/**/generated/**`, `*.glb`, `*_meta.json`, `game/ProjectSettings/**`, `game/Packages/**`,
`.gitattributes`, LFS ani asmdef. #25 tylko czyta `generated/roads_qa.json`. Plik gry `*_route.bytes` **nie jest
regenerowany w tej gałęzi** (w repo zostaje KRTG v1 — czytany przez oba czytniki; testy reprodukowalności porównują
serializację v1). Regeneracja do testów: v2 = 42,7 KB (v1 36,2 KB), 182 bloki pasów (78 z kierunkami), 0 krawędzi z
limitem, 0 `hgv=destination` — przywrócona do v1 po testach.

## KRTG v2 — jeden format (#21 + #23)

- Nagłówek `u16 version = 2`; per krawędź po `nPts`: `u16 maxweight [0,01 t], u16 maxaxleload [0,01 t], u16 maxheight [cm],
  u16 maxlength [cm]` (0 = brak); po zakazach skrętu sekcja pasów `u32 n, n × (u32 edge, u8 nFwd, u8 nBwd, maski)`;
  flaga krawędzi bit5 = `hgv=destination`. Parser Python (`parse`, `serialize(version=1|2)`) i `RouteGraph.Parse` (C#)
  czytają v1 i v2, odrzucają v3.
- Poprawki semantyki pasów (#23): tylko tagi z `src=osm` (454 krawędzie mają `lanes` z domyślnej wartości potoku —
  to nie są dane); `lanes` na drodze dwukierunkowej to suma obu kierunków (wiki OSM Key:lanes) — nie dzielone; zwykłe
  `turn:lanes` na dwukierunkowej (wiki Key:turn wymaga tam `:forward/:backward`) — nie dzielone (w danych regionu
  dotyczy to tylko 7 krawędzi z pustą wartością); rondo bez tagu `oneway` = jednokierunkowe (brak pasów wstecz);
  na `oneway=-1` kierunek jazdy = `turn:lanes:backward`, jeśli brak zwykłego `turn:lanes`.
- Parametry pojazdu (#21) zgodne z `docs/VEHICLE_REFERENCE_DATA.md`: 40,0 t (laden40), dach naczepy 4,00 m, zestaw 16,47 m,
  oś napędowa 11,5 t (limit z 96/53/WE — cytowany UNVERIFIED w dokumencie danych). Limit równy parametrowi = dozwolone;
  liczbowy limit na krawędzi celu = brak trasy (świadomie; `hgv=destination` dozwolone tylko jako cel).
- Dane regionu: `maxweight`/`maxweight:hgv`/`maxaxleload`/`maxlength`/`hgv:conditional` = 0, `maxheight` = 2 (oba `default`
  = brak limitu), `hgv=no` = 6. Routing z limitami nic dziś nie zmienia w tym regionie — działa na danych syntetycznych.

## Kontrola źródeł (2026-11-13)

| Cytat | Źródło sprawdzone | Wynik |
|---|---|---|
| PTB 2022 = Dz.U. 2022 poz. 1518, MI 24.06.2022 (#25) | api.sejm.gov.pl/eli/acts/DU/2022/1518 | zgodne (ogł. 20.07.2022, w mocy 21.09.2022, obowiązujący) |
| § 62 ust. 2: łącznica WA ≤ 6 %, WB/WC ≤ 7 % (#25) | ten akt, text.html | zgodne |
| Dz.U. 2026 poz. 132 zmienia rozp. z 2003 (znaki i sygnały) (#25) | api.sejm.gov.pl/eli/acts/DU/2026/132 | zgodne (MI 14.01.2026, ogł. 4.02.2026); treść zmian zał. 2 (P-23/P-26) — nie sprawdzona przez integratora |
| P-11 0,5/0,5 m, rys. 4.2.2.1 str. 569 (#25) | PDF D2019000231102.pdf > 10 MB — nie odczytany narzędziem | **niezależnie niesprawdzone** w r4 (zgodne z raportem M18 i odczytem M25) |
| Tab. 1.1/5.1, pkt 3.1.1 (B-20 koło wpisane 800 mm), pkt 5.2.1.1 (D-1 bok 600 mm) (#24) | jw. (zał. 1) | wartości zgodne z recenzją r3 i audytem M9; **interpretacja w kodzie błędna dla rombu** — poprawiona |
| Wiki OSM Key:turn / Key:lanes (#23) | wiedza ogólna integratora | `lanes` = suma kierunków na dwukierunkowych — poprawione |

Uwaga: M25 sprawdził nowelizacje 2021/2066, 2022/2377, 2026/132; recenzja r3 wymienia też **Dz.U. 2021 poz. 438** —
nie objęta M25 (otwarte, niżej).

## Wyniki testów (gałąź `mistral-r4-int`)

| Zestaw | Wynik |
|---|---|
| pytest `tools/worldgen/navgraph/tests` | **14 passed** (v1 w repo i po regeneracji v2) |
| pytest gis `tests/gis -q -m unit` | **76 passed, 1 xfailed** (strict: `p21_hatch` — czeka na właściciela); łącznice: 18 łańcuchów `*_link`, max 5,13 % ≤ 6 % |
| Unity EditMode pełny (KRTG v2 na próbę, przed poprawkami serializatorów) | 456: **431 passed, 10 failed, 10 skipped** — 8 środowiskowych jak w r3 (brak zbudowanego prefabu ciężarówki/TRAKT: `TruckDoorCrownTests`×3, `MirrorPresentationTests`×2, `LightPostPolicyTests`×1; `CarPaintMaterialTests.DepositionChannel`×2) + 2 z łączenia formatów (`NavRoutingTests.Parse_KrtgV2LaneBlocks…`, `NavTruckLimitsTests.Parse_V1AndV2…` — ręczne serializatory testowe znały tylko „swoją” połowę v2) → poprawione w `2274ca493` |
| Unity EditMode `NavRoutingTests` + `NavTruckLimitsTests` (po poprawkach) | **23/23** z plikiem v2 i **23/23** z plikiem v1 w repo |
| Unity PlayMode `HudTextAllocTests`, `NavHudTests`, `HudLayoutTests`, `CabScreensTests` | przed poprawką overlayu 52/53 (overlay **2500 GC.Alloc / 500** — `QualitySettings.names`); po `2274ca493` **53/53** |
| Pomiar GC.Alloc (`Profiling.Recorder`, 500 aktualizacji) | `DrivingHud` zmienne gyro/tempomat: **0**; overlay (panel ukryty, stan bez zmian): **0**; kontrola — stara konkatenacja gyro: **1003** |

## Osobne zadania wynikłe z recenzji

1. Lider: regeneracja `game/Assets/_Project/UI/Resources/CabDisplay/Nav/bialystok-industrial-c_route.bytes` do v2
   (`uv run --project tools/worldgen python tools/worldgen/navgraph/build_route_graph.py --region bialystok-industrial-c`),
   commit + ocena paska pasów na telefonie (visual QA HUD; pasek dziś pojawi się tylko na 78 krawędziach z kierunkami).
2. Lider: regeneracja świata po #24/#25 (D-1, D-6/D-15, B-20, P-11) + visual QA kamer znaków i przejazdów rowerowych.
3. Nowelizacja **Dz.U. 2021 poz. 438** — sprawdzić, czy zmienia zał. 2 (poza M25).
4. Testy `ZeroGc_*` nawigacji (`NavRoutingTests`, nowy `ZeroGc_LaneGuidanceInDrivingLoop`, `NavHudTests.LaneBar_DrawsZeroGc`)
   mierzą `GC.GetAllocatedBytesForCurrentThread()`, które w edytorze zwraca 0 — przepisać na `Recorder("GC.Alloc")`.
5. HUD: telemetria dev i treść overlayu diagnostyki nadal alokują przy zmianie treści (`ToString` liczb w `StringBuilder`) —
   tylko ścieżki deweloperskie; etykiety jazdy (prędkość, bieg, obroty, gyro, ciśnienia, tempomat) bez alokacji.
6. `hgv=destination` nie zwalnia krawędzi startowej (ciężarówka stojąca na takiej krawędzi może ją opuścić, ale nie wrócić) —
   w regionie 0 takich krawędzi; do rozważenia przy kolejnych regionach. `hgv:conditional` nieobsługiwane (0 w danych).
