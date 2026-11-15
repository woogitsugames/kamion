# ADR 0235 — płynne przejście między kaflami: addytywne wczytywanie sąsiednich regionów w trakcie jazdy

Status: Proposed (chmura D, zadanie F2, gałąź `streaming-0235`, stacked na `region-select-0229` / PR #104), 2026-11-15.
Kod C# **nieskompilowany w chmurze** (brak Unity i .NET); Python uruchomiony. Do weryfikacji i scalenia przez lidera.
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
4. **Budżet pamięci per tier (WORKING_VALUE):** cel PSS − (PSS C − WORLD_MEMORY C). A16 Low: 1000 − (899,8…926,2 − 124,2)
   = 198…224 → **200 MB**; A16 Medium (cel 1,2 GB) **400 MB**; High/Ultra **600 MB**. Para C + Maczka (277), Maczka +
   Kleeberga (310), Kleeberga + Knyszyńska (273) **przekracza 200 MB Low**: polityka wczytuje wtedy jeden kafel przed
   pojazdem ponad budżet (`allowOneOverBudget`, log `[STREAM] over budget`) — zamknięta droga jest gorsza niż przekroczenie,
   które pomiar na A16 ma potwierdzić albo obalić. Odcinek DK65 mieści się w 200 MB (maks. 3 kafle ≈ 187 MB przy dk65-03).
5. **Runtime `WorldStreamer`** (instaluje go `DrivingLabBootstrap`, gdy w buildzie jest choć jedna scena `_Tile` sąsiada;
   `stream=0` wyłącza): decyzja co 0,25 s; `SceneManager.LoadSceneAsync(…, Additive)` z `allowSceneActivation = false`,
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
- Po wyładowaniu startowego kafla `RecoverToSpawn` (brak bezpiecznej pozy) postawiłby zestaw nad pustką — rzadkie,
  do poprawienia razem z zapisem pozycji.
- Liczby do zmierzenia na A16: czas `load`/`activation` z logu `[STREAM] ready`, hitch `UnloadUnusedAssets`, PSS przy
  2–3 kaflach (zwłaszcza C + Maczka + Kleeberga), p95/p99 klatki w oknie wczytania.
