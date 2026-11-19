# ADR 0235 — płynne przejście między kaflami: addytywne wczytywanie sąsiednich regionów w trakcie jazdy

Status: Proposed (chmura D, zadanie F2, gałąź `streaming-0235`, stacked na `region-select-0229` / PR #104), 2026-11-15.
Kod C# **nieskompilowany w Unity**; Python uruchomiony. Do weryfikacji i scalenia przez lidera.
**FIX s22 (D12, ADR 0273):** streaming **opt-in** (`stream=1`), kafel odrodzenia przypięty (nigdy pustka pod resetem),
budżety PC osobno (Low 640 / Medium 800 / High 1450 / Ultra 2000 MB) i pamięć High per kafel, kafle także z paczek
regionów (#112: `ITileSceneSource`, dzierżawy `Acquire/Release`). Gałąź ma scalone `origin/main` i `regionpacks-0234`;
PR #114 zamknięty — do ponownego otwarcia / nowego PR po scaleniu #112 (ADR 0273 „Kolejność”).
Powiązane: ADR 0003 (skala, floating origin > 2 km), 0011 (import glTFast, sceny `_Generated`), 0012 §6 (cooking kolizji
przy wczytaniu), 0082 (krawędź regionu, safety net), 0085 (far field, kontrakt hierarchii), 0169 (jedno źródło zamknięć,
60 m przed krawędzią), 0205/0207/0214 (kafle korytarza), 0224 (szwy ±0,10 m), 0229 (sceny regionów w buildzie, menu).

## Kontekst
Korytarz D67 (C → Maczka → Kleeberga → Knyszyńska → DK65 01…11 → Knyszyn-S → Knyszyn, 17 kafli) to osobne sceny
`World_<id>`; każda ma na krawędziach zamknięcia dróg (bariery + collider 60 m przed krawędzią), apron do horyzontu i far
field, a scena zawiera też słońce, wolumen, kamerę, ciężarówkę i bootstrap. Stan kodu przed zmianą:
- `WorldRegionRoot.ShiftOrigin` istnieje, ale **nic go nie woła** — floating origin nie był zaimplementowany.
- `WorldInstances.SyncOrigin` już śledzi ruch roota regionu (instancje i HLOD idą za originem).
- `WorldCollisionCooker` piecze kolizje w `Awake` synchronicznie (`.Complete()`): C 265 meshy = 250–259 ms na A16
  (`docs/PERFORMANCE_BUDGETS.md`) — przy streamingu to przycięcie.
- Kafle to siatka 2048 m (`region.yaml` bbox), anchor = środek kafla; `route_endpoints.json` podaje punkty wejścia/wyjścia
  trasy na krawędziach (portale).

## Decyzja
1. **Graf sąsiedztwa jako dane.** `tools/worldgen/streaming/tile_graph.py` (bbox + origin z `region.yaml`, portale z
   `route_endpoints.json`, `--check`) → `game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json`
   (schema `truck-sim-pl/tile-graph/1`, tylko tablice obiektów — JsonUtility). Sąsiad = wspólna krawędź > 1 m (N/E/S/W) albo
   tylko narożnik (NE/…). Portal = wyjście trasy A ≡ wejście B na wspólnej krawędzi (≤ 2 m, WORKING_VALUE: dk65-02/03 mają
   1,0 m różnicy w `route_endpoints`). Wynik: 21 kafli, 17 portali, korytarz `bialystok-industrial-c..knyszyn` = 17 kafli
   (dokładnie D67) + `knyszyn-w..dk65-monki-01`. `worldMemoryMB` = WORLD_MEMORY Low z tabeli ADR 0229 (ESTIMATED).
2. **Scena kafla `World_<id>[_High]_Tile`** (`RegionScenes.TileSceneNameFor`, `WorldSceneBuilder.BuildTileScene`): ta sama
   scena po zapisaniu pełnej, zredukowana do roota regionu i `Route_start`; chunki zapisane **nieaktywne**, `WorldInstances`
   wyłączone, `WorldCollisionCooker.deferCook = true`. Bez świateł/wolumenu/kamery/ciężarówki (wczytanie pełnej sceny
   addytywnie zdublowałoby bootstrap i pojazd w `Awake`). Sky bake (ADR 0064) dopisuje mapy także do scen `_Tile`.
   `RegionBuildList` (`-Regions`) dokłada `_Tile` regionu, jeśli zaimportowano (stare importy: brak = bez błędu).
3. **Logika decyzyjna — czysta klasa** `Game.World.Streaming.StreamingPolicy` (bez MonoBehaviour, zero alokacji po
   konstrukcji, test EditMode `Decide_AllocatesNothing`):
   - promień wczytania **wyprowadzony**: v_max × (t_load + t_aktywacja + t_cook) + margines = 25 × (8 + 1 + 1) + 150 =
     **400 m**; v_max = 25 m/s = 90 km/h — ogranicznik prędkości N3 (dyrektywa Rady 92/6/EWG zm. 2002/85/WE); szybszy
     pojazd używa własnej prędkości. t_load = 8 s **UNVERIFIED** (wczytanie sceny na A16 niezmierzone — streamer loguje
     `load … ms`), t_cook = 1 s (zmierzone 0,26 s × 4), t_aktywacja 1 s i margines 150 m — WORKING_VALUE;
   - kafel chciany: bieżący (histereza 30 m) + sąsiad krawędziowy/narożny w promieniu albo ≤ 150 m od odcinka
     look-ahead p → p + v × 10 s;
   - wyładowanie: niechciany i dalej niż promień + **histereza 300 m** (= 700 m) — jazda wzdłuż szwu nie miele
     (test `DrivingAlongTheSeam_DoesNotThrash`: 10 min zygzaków ±200 m = 1 wczytanie, 0 wyładowań);
   - kolejka: najbliższy pierwszy, **1 wczytanie naraz**, maks. **4 kafle** (bieżący + 3 w narożniku), budżet pamięci
     sumą `worldMemoryMB`; brak miejsca → wyrzucenie najdalszego kafla z pasma histerezy; kafel niedostępny w buildzie
     nigdy nie jest chciany (szew zostaje zamknięty).
4. **Budżet pamięci per tier (WORKING_VALUE; PC: ADR 0273 §6 — `BudgetForTier(tier, desktop)`, tier High liczony
   `worldMemoryHighMB`):** cel PSS − (PSS C − WORLD_MEMORY C). A16 Low: 1000 − (899,8…926,2 − 124,2)
   = 198…224 → **200 MB**; A16 Medium (cel 1,2 GB) **400 MB**; High/Ultra **600 MB**. Para C + Maczka (277), Maczka +
   Kleeberga (310), Kleeberga + Knyszyńska (273) **przekracza 200 MB Low**: polityka wczytuje wtedy jeden kafel przed
   pojazdem ponad budżet (`allowOneOverBudget`, log `[STREAM] over budget`) — zamknięta droga jest gorsza niż przekroczenie,
   które pomiar na A16 ma potwierdzić albo obalić. Odcinek DK65 mieści się w 200 MB (maks. 3 kafle ≈ 187 MB przy dk65-03).
5. **Runtime `WorldStreamer`** (instaluje go `DrivingLabBootstrap` **tylko z launch argumentem `stream=1`** — ADR 0273 §7,
   do czasu pomiaru na Windows i A16 — gdy w buildzie albo w zainstalowanej paczce jest choć jedna scena `_Tile` sąsiada): decyzja co 0,25 s; `SceneManager.LoadSceneAsync(…, Additive)` z `allowSceneActivation = false`,
   aktywacja przy 90 % i tylko gdy żaden kafel się nie aktywuje; `Application.backgroundLoadingPriority = Low` na czas
   streamingu (przywracane); w `sceneLoaded` (po Awake/OnEnable, przed renderem) root ustawiany dla bieżącego originu i
   start bake joba kolizji; chunki włączane ≤ **2 ms/klatkę** (Stopwatch, min. 1 chunk), collidery 16/klatkę
   (`WorldCollisionCooker.BeginCook/PollCook`, job bez `.Complete()` na głównym wątku). **Szew otwiera się dopiero gdy
   oba kafle są Ready** (zamknięcia ADR 0169 tej strony, grupa barier gdy wszystkie jej zamknięcia otwarte, sektor far
   field tej strony, apron: cały → kawałki `Apron_N/E/S/W` bez strony z sąsiadem) — spóźnione wczytanie = zamknięta droga,
   nigdy dziura. Wyładowanie: najpierw zamknięcie szwów sąsiadów, potem `UnloadSceneAsync` (start scenę: tylko root i
   trasa — `Destroy`), `Resources.UnloadUnusedAssets` najwyżej co 20 s i nigdy w trakcie wczytywania.
6. **Floating origin** (`TilePlacement`, `FloatingOrigin` w Game.Core): kotwica świata W w double; root kafla na
   (Ax − Wx, −Wz, Ay − Wy), `originShift` = W − A (spójne z `ToUnity/ToGlobal/ShiftOrigin`; test: punkt szwu
   dk65-03/04 z obu rootów < 2 mm). Gdy pojazd jest ≥ 100 m w nowym kaflu, W → anchor tego kafla (poziomo; Wz stałe):
   w `FixedUpdate` (kolejność −950) przesunięcie wszystkich rootów scen (bez UI), pozy ciał dynamicznych przez
   `Rigidbody.position`, roota regionów ustawiane dokładnie z double (bez dryfu), `Physics.SyncTransforms`, potem
   zdarzenie `FloatingOrigin.Moved` → kamera pościgowa (`CameraRig`), autopilot (`PathFollowerDriverInput.Offset`), bufor
   bezpiecznych póz (`SafePoseBuffer.Offset`). Pojazd jest zawsze ≤ ~1,5 km od (0,0,0), zgodnie z ADR 0003 (2 km).
7. **Safety net** (ADR 0082) przy streamingu liczy odległość do krawędzi **sumy kafli Ready** (`EdgeSides.UnionInsideDistance`:
   otwarte szwy się nie liczą, narożnik bez kafla po przekątnej liczy się jako punkt).
8. **Zero GC w pętli jazdy:** decyzja, postęp wczytywania/aktywacji/wyładowania bez alokacji; alokacje tylko przy
   zdarzeniu kafla (rejestracja obiektów krawędzi, logi, rebase), jak samo `LoadSceneAsync` Unity.

## Testy
- Python: `tests/gis/test_tile_graph_0235.py` — **7/7** (świeżość json, siatka 2048 m, symetria, łańcuch D67 z portalami,
  brak fałszywych sąsiadów, JsonUtility-friendly).
- FIX s22: EditMode +8 (przypięty kafel, budżety PC z danych, pamięć High, korytarz PC z przypiętym C dla Low…Ultra,
  źródło build/paczka) — **24/25 pod .NET 8** (harness bez Unity, bez testów z `GameObject`/`RegionBuildList`); jedyny
  czerwony `Decide_AllocatesNothing` to 24 B jednorazowo w runtime .NET — pomiar per wywołanie `Decide` = 0 B, ten sam wynik
  na kodzie sprzed FIX; w Unity (Mono) do potwierdzenia przez lidera.
- EditMode `WorldStreamingPolicyTests` (20, **nieuruchomione**): dane z Resources, promień, histereza, kolejka, narożnik,
  budżet/eksmisja, look-ahead, przejazd całego korytarza D67 przy 90 km/h dla Low i Medium (nigdy w kaflu nie-Ready),
  zero alokacji, placement/rebase, strony krawędzi, lista scen buildu.
- PlayMode `WorldStreamingPlayModeTests.Dk65_03_To_04_RouteAutopilot_LoadsTheNeighbourAdditively` (**nieuruchomione**):
  autopilot 50 km/h z dk65-03 do dk65-04, CSV klatek `artifacts/streaming-0235/dk65-03-04-frames.csv` (dt, GC B/klatkę,
  stany kafli), asercje: Ready przed szwem, zamknięcia szwu wyłączone, brak resetu safety net, 300 m w dk65-04, rebase.

## Konsekwencje i otwarte
- Wymaga **reimportu** regionów (scena `_Tile`, `Apron_*`); stare sceny działają, ale apron nachodzi na sąsiada (log).
- Nakładanie aprona sąsiada w narożnym klinie (dwa aprony o różnej wysokości) i far skyline (sylwetki z sąsiedniego
  kafla dublują wczytane budynki) — do oceny na kamerach; `StreetLamps.SetHeads` jest globalne (ostatni region wygrywa
  — plamy świateł nocą tylko jednego kafla); GPS/ekrany kabiny (`NavigationInstaller`) znają tylko region startowy.
- Odbiorcy `FloatingOrigin.Moved` poza tymi trzema (cząsteczki w world space, ślady, audio) — przegląd po pierwszym
  przejeździe; obiekty `DontDestroyOnLoad` nie są przesuwane. Interpolacja Rigidbody przy rebase — UNVERIFIED (PlayMode
  loguje skok).
- ~~Po wyładowaniu startowego kafla `RecoverToSpawn` postawiłby zestaw nad pustką~~ — **naprawione (ADR 0273 §8):**
  `StreamingPolicy.Pinned` = kafel najnowszej bezpiecznej pozy (starszej niż `safeMinAge`) albo kafel startowy, gdy jej brak;
  nigdy nie wyładowany ani eksmitowany (log `[STREAM] pinned …`). Bez zmian w spawn/route_start.
- Do BACKLOG (lider nadaje numery; recenzja #114 P2): (P2-3) `StreetLamps.SetHeads` globalne — ostatni kafel wygrywa;
  (P2-5) GPS/ekrany kabiny tylko region startowy — graf nawigacji per kafel; (P2-4) po `build_region` nowych kafli uruchomić
  `uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py` (+ `--check`) — dopisać do kroku
  „Regeneracja mapy” w CLAUDE.md (plik lidera).
- (P2-6) Interpolacja `Rigidbody` przy rebase: PlayMode ma teraz asercję skoku pozy renderowanej < 0,05 m (WORKING_VALUE).
- Liczby do zmierzenia na A16: czas `load`/`activation` z logu `[STREAM] ready`, hitch `UnloadUnusedAssets`, PSS przy
  2–3 kaflach (zwłaszcza C + Maczka + Kleeberga), p95/p99 klatki w oknie wczytania.

## Uzupełnienie s23 (D30, chmura D r8) — wejście do main jako opt-in na PC (ADR 0273 §10)
- Nowy PR z gałęzi `streaming-pc-s23` (= `streaming-0235` + merge `origin/main` 16.11), zastępuje zamknięty #114.
  Streaming **opt-in**: `stream=1` (Windows `-stream 1`, Android `-e stream 1`); bez flagi scena jak dziś.
- **Styk z grą = jedna instrukcja** w `DrivingLabBootstrap.Start`: `WorldStreamer.TryInstallFromLaunch(...)` (ADR 0273 §10
  pkt 3). Okablowanie przeniesione do streamera: przypięty kafel z `SafePoseBuffer` sieci bezpieczeństwa, przesunięcie tego
  bufora przy rebase (przed `FloatingOrigin.Notify`), subskrypcja `PathFollowerDriverInput.Offset` na czas życia streamera.
  `WorldSafetyNet.cs` = main; prostokąt sieci regionu startowego poszerzany do sumy połączonych kafli dostępnych
  (`WidenStartBoundary`, ADR 0273 §10 pkt 4 — skutki i dokładna poprawka po int-h3 tamże, pkt 5).
- `ITileSceneSource` zostaje; domyślne źródło to `BuildTileSource` (tylko build). Wstawki `RegionPackService.Existing`
  usunięte — streamer nie zna `Game.World.Packs` (tego katalogu nie ma w grze).
- Testy dodane: `WorldStreamerHook0273Tests` (hak wyłączony = brak komponentu i nietknięty prostokąt; region spoza grafu;
  poszerzenie prostokąta; przypięcie z bufora póz + słuchacz origin; **zero GC** 600 klatek `Update` + zapytań sieci),
  `TileSceneSourceContractTests`; `Decide_AllocatesNothing` na `GcAllocCounter` (Recorder; wcześniejszy pomiar bajtów był
  pod Mono zawsze 0 — test nie mógł spaść). Pod .NET 8: 32/32, `Decide` 0 B (wcześniejsze 24 B znikło po rozgrzewce).
- Otwarte bez zmian: P2-3 (`StreetLamps.SetHeads` globalne), P2-5 (GPS tylko region startowy), pomiar szwu z dwoma kaflami
  High w C (recenzja #114 P1-1), baza pamięci procesu Windows.

## Uzupełnienie 2026-11-19 — harmonogram po analizie pauz DK65-10

- Slot `maxConcurrentLoads` obejmuje Loading **i Activating**, do końca gotowania i aktywacji chunków.
  Kafel Activating nie podlega wyładowaniu/eksmisji: unikamy czekania na job w `WorldCollisionCooker.OnDestroy`.
- `Resources.UnloadUnusedAssets` ma śledzony uchwyt. Dopóki nie zakończy się operacja, streamer nie wydaje
  kolejnych decyzji load/unload. Czyszczenie startuje po zakończeniu wszystkich operacji scen.
- Logowane są początek/koniec czyszczenia, focus/pause oraz luki Update >= 1 s ze stanami streamingu i przyrostem
  liczników GC. Zwykła klatka nie alokuje na potrzeby tej diagnostyki.
- Okresowe dowody `DesktopAutoShot` (`-shot_every`) pracują w tle i pomijają utracone terminy zrzutów,
  aby po wznowieniu nie zapisywać serii tych samych nazw plików. Zwykła gra zachowuje dotychczasowe ustawienie fokusu.
- To uszczelnienie harmonogramu, **nie potwierdzenie przyczyny pauz 21/2/166 s**; load dk65-10 był gotowy
  wcześniej (267 + 183 ms). Dowody, testy i ograniczenia: [raport stream-hitch-cli](../reports/stream-hitch-cli.md).
