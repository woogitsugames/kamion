# INTEGRATION 2026-11-16 — int-stream-s23 (PR #157 streaming kafli na PC)

Gałąź `int-stream-s23` = `origin/main` (a6c713a8f) + `origin/streaming-pc-s23` (#157) + poprawki integracji + `git merge origin/main`
(16.11 wieczór). Worktree `.claude/worktrees/int-stream-s23`, Library skopiowana z win-build-0261 (Win64), `Data/raw/*` jako
junctions do main (`derived` = ReparsePoint, świat nieprzebudowywany).

## Werdykt
**Gotowe do scalenia: TAK** (EditMode po `merge origin/main`: 41/41 z filtrem streamingu, 17:00; zrzuty dokładnie na szwie
i PlayMode — otwarte, niżej).
**#112 (`regionpacks-0234`) do zamknięcia jako wchłonięty** (kontrakt `ITileSceneSource` + testy kontraktu są w #157). #114 zastąpiony.

## Wynik
| krok | wynik |
|---|---|
| Merge #157 | bez konfliktu (hak `stream` w `DrivingLabBootstrap.cs` jedna instrukcja; po merge main l. 241) |
| Kompilacja Unity 6000.3.28f1 Win64 | czysta (kod chmury pierwszy raz w Unity) |
| EditMode całość (przed importem) | 959/1004; 6 porażek środowiskowych świeżego worktree (brak `_Generated/Truck`, brak importu C) — po skopiowaniu Truck/Trailer i imporcie C: zielone |
| EditMode streaming | Policy 25, Contract 8, Hook0273 6 + 2 nowe (kontynuacja trasy, PathFollower) — wszystkie PASS, w tym `GcAllocCounter` 600 klatek `Update` = 0 B (także z ustawioną trasą) |
| PlayMode `WorldStreamingPlayModeTests` | **pominięty** (`Assert.Ignore`: `CanStreamedLevelBeLoaded` w edytorze wymaga scen dk65-03/04 w `EditorBuildSettings` — `ProjectSettings/` zmienia tylko lider). Tę samą ścieżkę (wczytanie addytywne, aktywacja, rebase, autopilot przez szew) pokrywa przejazd run2 w buildzie gracza |
| Import Win64 (`-BuildTarget Win64`, Low+High, sceny `_Tile` + `Apron_N/E/S/W`) | 19/19: bialystok-industrial-c, -maczka, -kleeberga, -knyszynska, dk65-01..11, knyszyn-s, knyszyn, knyszyn-w, dw671-tykocin-01 |
| Build Windows (`-Regions <19> -Slot`) | exit 0, `artifacts/win/kamion-0.1.0-a920cfb35b-regions` (worktree) |
| Przejazd run2 (`-stream 1`, High, 60 fps, 70 km/h, knyszynska `route_s` 2300 → dk65-01 → dk65-02 → dk65-03 → dk65-04) | **`stream-report.py --gate` PASS** |

### Liczby run2 (RTX 5070, Ultra 7 270K; FPS dev, nie referencja D74)
- Kafle: 4 wczytane, 4 gotowe, 2 wyładowane (start knyszynska — tylko root, i dk65-01), 0 ponad budżet, **0 zamkniętych szwów**, 2 rebase
  floating origin (1,57 ms i 0,47 ms).
- Ładowanie kafla High: p50 233 ms / max 267 ms; aktywacja (64 chunki, budżet 2 ms/klatkę): p50 232 ms / max 365 ms; kafel gotowy,
  gdy pojazd był ≥ 377 m od niego (promień 400 m) — przy 70 km/h zapas ~19 s.
- Klatki: 15 364, p50 / p95 / p99 = 16,7 / 16,7 / 16,7 ms (cap 60), > 33,3 ms: **1 — klatka nr 1 (t = 0,5 s, 531 ms) = start
  sceny, nie szew**. Na szwach i przy ładowaniu zero zawieszek.
- Pamięć: szczyt working set 1202 MB (budżet świata High PC 1450 MB, rezydentne 3 kafle 437–565 MB ESTIMATED).
- Autopilot przejechał 4 szwy ciągiem: `[STREAM] route continued into dk65-01 / -02 / -03 / -04`; reset siatki bezpieczeństwa: 0.
- run1 był nieważny (błąd mojego skryptu: `pwsh -File … -ExtraPlayerArgs a b` przekazał tylko `-stream` bez `1`); poprawione.

## Zmiany integracji (poza #157)
1. **Autopilot przez szwy** — w #157 `AppendPath` wołał tylko test PlayMode; w grze autopilot zatrzymałby się przed zaporą kafla
   startowego. `Game.Core.IStreamedRoute` (`Core/StreamedRoute.cs`), `PathFollowerDriverInput.TryGetPathEnd` (false przy
   `route_end` — odcinki pomiarowe bez zmian), `WorldStreamer.ContinueRoute` (co decyzję 0,25 s, bez alokacji: dokleja trasę
   startową gotowego kafla, gdy zaczyna się ≤ 3 m od końca ścieżki). Trasy D67 łączą się koniec→początek z odstępem 0 m od maczka
   do knyszyn (pomiar z `route_start.json`). Bez zmian w `DrivingLabBootstrap` / asmdef (sterownik z `Target` delegata `Offset` haka).
2. **`Kamion-korytarz.cmd`** — `scripts/postbuild-windows.py` (main przeniósł tam launchery, ADR 0276) pisze go, gdy w buildzie są
   knyszyn i knyszyn-s: `-screen-fullscreen 1 -window-mode borderless -scene knyszyn -stream 1 %*`; `package-windows.py` dołącza go
   jak inne launchery z `-scene`. Test `tests/dist/test_postbuild_windows.py` (+1, 35/35).
3. Przy imporcie: `asphalt_detail_photo/*/T_*_Detail*.png` nie są generowane przez `build_all.py`, więc test „stale” w
   `import-region.ps1` odpalał `build_all.py` przed każdym regionem (+8 min). Lokalnie dotknięty mtime; **do poprawki w main**
   (wyjątek w teście świeżości albo generator tych dwóch plików).

## Dla właściciela — ciągła jazda
W folderze buildu: **`Kamion-korytarz.cmd`** (pełny ekran bez ramki, start Knyszyn, streaming włączony). Równoważnie:
```
Kamion.exe -screen-fullscreen 1 -window-mode borderless -scene knyszyn -stream 1
Kamion.exe -scene bialystok-knyszynska -stream 1          # start od strony Białegostoku
```
Build korytarza od zera (lider):
```
foreach ($r in 'bialystok-industrial-c','bialystok-maczka','bialystok-kleeberga','bialystok-knyszynska','dk65-01','dk65-02','dk65-03','dk65-04','dk65-05','dk65-06','dk65-07','dk65-08','dk65-09','dk65-10','dk65-11','knyszyn-s','knyszyn','knyszyn-w','dw671-tykocin-01') { pwsh scripts/import-region.ps1 -Region $r -BuildTarget Win64 }
pwsh scripts/build-windows.ps1 -Slot -Regions 'bialystok-industrial-c,bialystok-maczka,bialystok-kleeberga,bialystok-knyszynska,dk65-01,dk65-02,dk65-03,dk65-04,dk65-05,dk65-06,dk65-07,dk65-08,dk65-09,dk65-10,dk65-11,knyszyn-s,knyszyn,knyszyn-w,dw671-tykocin-01'
```
Pomiar: `pwsh scripts/build-windows.ps1 -SkipBuild -Exe <exe> -Run -Tier High -Scene bialystok-knyszynska -Autopilot route -Speed 70 -Fps 60 -RunSeconds 260 -ShotSeconds 38 -ExtraPlayerArgs '-stream','1','-route_s','2300'`
(w tym samym procesie PowerShell — nie przez `pwsh -File`), potem `uv run --no-project python scripts/stream-report.py --log <player.log> --frames <frametimes.csv> --memory <mem.csv> --threshold-ms 33.3 --memory-limit-mb 6144 --gate`.

## Ograniczenia / otwarte
- **Autopilot** trasy jedzie tylko w kierunku Białystok → Knyszyn i staje na końcu trasy knyszyn: trasy knyszyn → knyszyn-w (596 m
  przerwy) i → dw671-tykocin-01 (2164 m) się nie łączą, a C → maczka ma 700 m przerwy. **Jazda ręczna** po korytarzu nie ma tych
  ograniczeń (szwy otwierają się niezależnie od autopilota).
- Szwy narożne (sąsiad po przekątnej, np. dk65-02 ↔ knyszynska) nie otwierają zapór — streamer otwiera tylko boki N/E/S/W; na trasie
  D67 przejazd idzie przez boki (run2: 0 zamkniętych szwów).
- Zewnętrzne krawędzie korytarza (np. knyszyn ↔ dk65-monki-01, poza buildem) zostają zamknięte (`SetUnavailable`), ale bez
  ostrzeżenia „Koniec mapy” do czasu poprawki ADR 0273 §10 pkt 5.
- **Zrzuty dokładnie na szwie — otwarte.** Jedyny zrzut run2 jest z t = 38 s (przed pierwszym szwem); drugiego przejazdu nie
  puszczałem, bo właściciel gra na tym PC. Do zrobienia: 2–3 przebiegi z `-ShotSeconds` dobranym z logu `[STREAM] origin rebase`
  i ocena `visual-critic` (szczelina terenu / skok asfaltu na szwie, fartuch `Apron_*`).
- Budżety pamięci (640/800/1450/2000 MB) i progi bramki to `WORKING_VALUE`; klasa „min” D74 (iGPU, 2 kafle High) niezmierzona.
- PlayMode `WorldStreamingPlayModeTests` do uruchomienia przez lidera z dk65-03, dk65-04 (+ `_Tile`) w `EditorBuildSettings`
  (np. tymczasowo, jak build), inaczej zawsze `Ignored`.
- `docs/10` §3 nadal mówi o Addressables (do ujednolicenia z ADR 0234).
- Merge `origin/main` (wieczór 16.11) skompilowany ponownie tylko w EditMode z filtrem streamingu (postmerge); build po merge'u nie
  był powtórzony.

## Dowody
- `artifacts/int-stream-s23/run2/` (worktree; kopia w main `artifacts/int-stream-s23/`): `stream-report.txt`, `player.log`,
  `frametimes.csv`, `mem.csv`, `shot.png`, `summary.json`.
- Statusy kroków: `artifacts/live/int-stream-s23-step{1,2,3}.status`, `-run1/-run2.status`, `-postmerge.status`.
- Testy: `artifacts/tests/editmode-*.xml`, `playmode-*.xml` (worktree).
