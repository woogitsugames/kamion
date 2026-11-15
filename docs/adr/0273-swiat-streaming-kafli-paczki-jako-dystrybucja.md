# ADR 0273 — jeden model świata: ciągły streaming kafli, paczka regionu = jednostka dystrybucji (PC główny, A16 Low drugorzędny)

Status: Proposed (chmura D r4, zadanie D12, gałęzie `regionpacks-0234` = PR #112 i `streaming-0235` = zamknięty PR #114),
2026-11-15. Kod C# **nieskompilowany w Unity** (czysta logika uruchomiona pod .NET 8 + NUnit, patrz „Testy”). Do weryfikacji
i scalenia przez lidera. Rozstrzyga konflikt koncepcyjny z recenzji `docs/reports/REVIEW-2026-11-15-s22-code-112.md` i `-114.md`.
Powiązane: D67 (korytarz, docelowo paczki), D73 (Windows = platforma główna, ADR 0260), D74 (wymagania PC jak w dwóch
symulatorach ciężarówek SCS, ADR 0260 uzup.), ADR 0234 (paczki, AssetBundles), ADR 0235 (streaming kafli, floating origin),
ADR 0229 (`-Regions`, menu), ADR 0261 (build Windows), ADR 0082 (safety net), `docs/10` §3 (Core + Region Packs, regiony
spinane przez punkty wejścia).

## Kontekst
- #112 zakładał „jeden region naraz, pełna scena, szwy zamknięte”: `Prepare` robił globalne `UnloadAll(true)`, paczka
  zawierała tylko `World_<id>[_High]`. #114 zakładał „kilka regionów naraz, sceny `World_<id>[_High]_Tile` addytywnie”, ale
  tylko z buildu. Razem: streamer uznałby sąsiada z paczki za „nie w buildzie”, a przygotowanie sąsiada z paczki
  zniszczyłoby bieżący region.
- D73: platformą główną jest Windows; D74: wymagania jak w ETS2/ATS (minimalne 8 GB RAM, GPU 2 GB VRAM, tier Low 30 fps;
  zalecane 12 GB RAM, tier High 60 fps; dysk ≤ 25 GB — WORKING_VALUE). Gracz takiej klasy gier jedzie setki kilometrów
  bez ekranów ładowania.
- Jak robią to symulatory ciężarówek z otwartą mapą (opis ogólny, bez cudzego kodu): mapa jest podzielona na sektory
  wczytywane w tle wokół pojazdu w promieniu zależnym od prędkości; świat bazowy i dodatki mapowe to archiwa danych
  montowane przy starcie, a system streamingu nie rozróżnia, z którego archiwum pochodzi sektor — dodatek „dokleja” sektory
  na granicy mapy bazowej. Ekran ładowania jest tylko przy starcie / wczytaniu zapisu.
- Dane w gicie: kafle korytarza 2048 m (`tile_graph.json`, 21 kafli, korytarz D67 = 17), `WORLD_MEMORY` Low/High każdego
  regionu z logów importu cytowanych w ADR regionów (tabela ADR 0234 §7; C 124,2 / 267,0 MB, Maczka 153,2 / 420,4 MB …).

## Rozważone warianty
| wariant | ocena |
|---|---|
| A. tylko paczki, jeden region naraz (#112 bez zmian) | **odrzucony**: na PC nie ma powodu pamięciowego, żeby zatrzymywać jazdę na szwie co ~2 km; korytarz D67 = 16 ekranów ładowania; sprzeczne z D74 |
| B. tylko streaming, cały świat w buildzie (#114 bez paczek) | dobry na start PC (korytarz High ≈ 2,4–3,4 GB ESTIMATED wobec 25 GB), ale bez ścieżki dodatków (docs/10 §3), poprawek pojedynczego kafla i bez wersji telefonowej (APK ≤ 2 GB, D67) |
| **C. połączenie (wybrany)** | jeden runtime (streaming), dwa źródła treści (build lub paczka), paczka niesie dokładnie te sceny, które streaming otwiera |

## Decyzja
1. **Region = jednostka treści** o scenach {pełna `World_<id>`, kafel `World_<id>_Tile`} × tier treści {Low, High}
   (`RegionScenes`). Pełna scena służy tylko startowi z menu (ciężarówka, kamera, światło, bootstrap); każdy inny region
   w trakcie jazdy przychodzi jako scena kafla (ADR 0235 §2).
2. **Runtime = ciągły addytywny streaming kafli** (ADR 0235) nad sumą regionów dostępnych w danej instalacji. Region
   niedostępny (brak w buildzie i brak paczki) = szew zamknięty jak dziś (bariera + zamknięcie 60 m przed krawędzią) —
   zawsze bezpieczny fallback, nigdy dziura.
3. **Źródła treści** (`ITileSceneSource`, kolejność): (a) build gracza (`-Regions`, `RegionBuildList` dokłada `_Tile`),
   (b) zainstalowana paczka (AssetBundle). Paczka zawiera **pełną scenę i scenę kafla w jednym bundlu** (wspólne zasoby
   regionu zapisane raz; `RegionPackCommands`, manifest `scenes[]` = obie). Streamer przed `LoadSceneAsync` kafla z paczki
   woła `IRegionPackProvider.Acquire(region, tier)`, po zakończonym `UnloadSceneAsync` — `Release`.
4. **Liczenie referencji zamiast globalnego zwalniania** (`RegionPackLeases`): każdy bundel ma licznik dzierżaw kluczy
   `<region>|<tier>`; `common` (ciężarówka, PBR, shadery) zwalniany dopiero, gdy nie jest trzymany żaden region. Menu ma
   własną dzierżawę (zwalnianą, gdy aktywna scena opuści region), streamer — po jednej na kafel. Brak `UnloadAll` w ścieżce
   ładowania.
5. **Dystrybucja per platforma:**
   - **PC (główna):** gra bazowa = build Windows z regionami bazowymi w `-Regions` (bez pobierania, bez hashowania przy
     starcie, najkrótsze ładowanie). Paczki `-Target Win64` (`build-region-packs.ps1 -Target Win64 -InstallLocal`) to
     dodatki mapowe (kolejne regiony/kraje, docs/10 §3) i poprawki pojedynczych regionów. Pakowanie instalatora PC — H9
     (ADR 0271) bierze build + opcjonalny katalog paczek.
   - **Android (drugorzędny, tier Low):** APK z C (224 MB) + paczki Low przez `adb push` (ADR 0234 §5); streaming na A16
     dopiero po pomiarze (pkt 7).
6. **Budżety pamięci świata per tier** — suma `WORLD_MEMORY` kafli rezydentnych, tier treści High liczony wartościami High
   (`tile_graph.json` dostaje `worldMemoryHighMB`). Najgorsze zestawy z danych (`tile_graph.json` × tabela ADR 0234 §7):
   2 kafle Low 309,9 / High 777,2 MB (Maczka + Kleeberga); 3 kafle Low 434,1 / High 1044,2 MB (C + Maczka + Kleeberga).
   Budżet = najgorsze 3 kafle + przypięty kafel odrodzenia (pkt 8, w najgorszym razie C) + zapas ~10 %, zaokrąglone:

   | platforma / tier | treść | budżet świata (WORKING_VALUE) | wyprowadzenie |
   |---|---|---|---|
   | PC Low (min. 8 GB RAM, 2 GB VRAM) | Low | **640 MB** | 434,1 + 124,2 = 558,3 → +10 % ≈ 615 → 640 |
   | PC Medium | Low | **800 MB** | jak Low + jeden kafel narożny DK65 (≤ 76,1) i zapas |
   | PC High (zal. 12 GB RAM) | High | **1450 MB** | 1044,2 + 267,0 = 1311,2 → +10 % ≈ 1442 → 1450 |
   | PC Ultra | High | **2000 MB** | 4 kafle High w narożniku + przypięty; pod dłuższy look-ahead po pomiarze |
   | A16 Low / Medium / tel. High | Low / Low / High | **200 / 400 / 600 MB** | bez zmian, ADR 0235 §4 |

   Cel procesu na PC (WORKING_VALUE, do pomiaru): working set ≤ **4 GB** przy klasie 8 GB RAM (Low), ≤ **6 GB** przy 12 GB
   (High); baza procesu bez świata NIEZMIERZONA na Windows — pierwszy przejazd `-stream 1` ją poda (log `[STREAM]` + próbki
   pamięci procesu). VRAM 2 GB klasy minimalnej: tekstury świata są częścią `WORLD_MEMORY` — ryzyko do pomiaru na iGPU (D74).
7. **Streaming opt-in** do czasu pomiaru: launch argument `stream=1` (Windows `-stream 1`, Android `adb … -e stream 1`).
   Kryterium włączenia domyślnego na danej platformie/tierze (lider, z logów):
   przejazd korytarza C → Knyszyn autopilotem 90 km/h: **0 resetów safety net**, **0 kafli gotowych za późno**
   (`[STREAM] ready …, vehicle 0 m from the tile` = pojazd już w kaflu; `scripts/stream-report.py --gate`), klatki: PC ≤ **12 klatek > 33,3 ms** na przejazd przy celu 60 fps (analogia D69
   dla A16: ≤ 12 klatek > 40 ms) — WORKING_VALUE; pamięć: szczyt working set ≤ cel z pkt 6 (PC), PSS ≤ 1000 MB (A16 Low).
8. **Odrodzenie nigdy nad pustką** (recenzja #114 P1-2) — warunek tylko po stronie streamera, bez zmian spawn/route_start:
   `StreamingPolicy` ma **kafel przypięty**, którego nie wyładowuje ani nie eksmituje (pamięć liczy się do budżetu). Streamer
   przypina kafel, w którym leży punkt, do którego safety net może dziś przywrócić zestaw: najnowsza bezpieczna poza starsza
   niż `safeMinAge` (`WorldSafetyNet.SafePoses`), a gdy takiej nie ma — kafel startowy (scena spawnu). Bezpieczna poza jest
   zapisywana co ~1 s na utwardzonej drodze, więc w normalnej jeździe przypięty jest bieżący lub poprzedni kafel (koszt 0);
   kafel startowy zostaje w pamięci tylko dopóty, dopóki nie ma bezpiecznej pozy.
9. **Czas wczytania** `t_load = 8 s` (A16, UNVERIFIED) zostaje na wszystkich platformach (promień 400 m, zachowawczo);
   po pierwszym pomiarze `[STREAM] ready … load … ms` na PC — osobne ustawienie per platforma (nowy ADR nie jest potrzebny,
   wartość w `StreamingSettings` z komentarzem pomiaru).

## Kolejność scalania
**#112 → #114 (nowy PR / ponowne otwarcie).** #112 nie zmienia gry (serwis nie jest tworzony, menu bez załącznika A) i
wnosi kontrakt `Acquire/Release` + `RegionScenes.TileSceneNameFor` (hunk identyczny z #114 — scalenie bez konfliktu).
Gałąź `streaming-0235` ma scalone `regionpacks-0234` i `origin/main`; po scaleniu #112 jej diff względem main to sam
streaming. Załącznik A ADR 0234 (menu) — po obu, osobnym commitem lidera.

## Konsekwencje
- Jeden model na PC i telefon; telefon różni się tylko budżetem i źródłem treści (paczki zamiast buildu).
- `common` w paczkach dubluje zasoby obecne w buildzie (ciężarówka, PBR) — na PC (gra bazowa w buildzie, paczki tylko jako
  dodatki) to +44–74 MB dysku i pamięci przy pierwszym regionie z paczki (ESTIMATED, ADR 0234 §7); na A16 do pomiaru.
- Kafel przypięty bez bezpiecznej pozy może zatrzymać C w pamięci na A16 Low (124,2 MB z 200) — wtedy polityka wczyta
  jeszcze jeden kafel ponad budżet i zamknie dalsze szwy; ujawni się w logu `[STREAM] pinned … over budget`.
- Wymaga reimportu regionów (sceny `_Tile`, `Apron_*`) przed budową paczek z kaflami; paczka bez sceny kafla działa
  tylko z menu (ostrzeżenie `[PACKS] … no tile scene`).

## Testy
- EditMode `RegionPackTests` (+7: dzierżawy dwóch regionów, ta sama paczka menu + streamer, plan z kaflem w jednym bundlu,
  kopie z `Resources/`, nazwy przez `RegionScenes`, cel Win64/Android) — 50/50 pod .NET 8 z zaślepką `JsonUtility`.
- EditMode `WorldStreamingPolicyTests` (+8: przypięty kafel, budżety PC z danych, pamięć High, korytarz D67 przy 90 km/h dla
  PC Low…Ultra z przypiętym C — 0 decyzji ponad budżet, maks. 434,1 MB Low / 1044,2 MB High; źródło build/paczka) —
  24/25 pod .NET 8 (`Decide_AllocatesNothing`: 24 B jednorazowo w runtime .NET także na kodzie sprzed FIX, 0 B na wywołanie).
- Python `tests/gis/test_tile_graph_0235.py` (świeżość + `worldMemoryHighMB`), `tests/gis/test_stream_report_0273.py`.

## Komendy dla lidera (Windows = główny pomiar, A16 Low = drugi)
```powershell
pwsh scripts/test.ps1 -Platform EditMode
uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py --check
# import korytarza (sceny _Tile) — dla każdego regionu D67:
pwsh scripts/import-region.ps1 -Region bialystok-maczka   # ... kleeberga, knyszynska, dk65-01..11, knyszyn-s, knyszyn (Tiers Low,High)
pwsh scripts/build-windows.ps1 -Regions 'd67' -Slot
pwsh scripts/build-windows.ps1 -SkipBuild -Run -Tier High -Scene bialystok-industrial-c -Autopilot route -Speed 90 -Fps 60 -RunSeconds 1500 -ShotSeconds 60 -ExtraPlayerArgs '-stream','1'
# w drugim oknie pwsh, w trakcie przejazdu (próbki pamięci procesu co 1 s):
$o='artifacts/win/mem.csv'; 't_s,working_set_mb,private_mb' | Set-Content $o; $t0=Get-Date; while ($p = Get-Process Kamion -ErrorAction SilentlyContinue) { '{0:F0},{1:F1},{2:F1}' -f ((Get-Date)-$t0).TotalSeconds,($p.WorkingSet64/1MB),($p.PrivateMemorySize64/1MB) | Add-Content $o; Start-Sleep 1 }
uv run python scripts/stream-report.py --log artifacts/logs/win-run-<ts>.log --frames "$env:USERPROFILE/AppData/LocalLow/woogitsugames/Kamion/diag/frametimes.csv" --memory artifacts/win/mem.csv --threshold-ms 33.3 --memory-limit-mb 6144 --gate
# paczki PC (dodatek): pwsh scripts/build-region-packs.ps1 -Target Win64 -Regions dk65-06,dk65-07 -Tiers Both -InstallLocal
# A16 Low:
pwsh scripts/build-android.ps1 -Regions 'bialystok-industrial-c,bialystok-maczka,bialystok-kleeberga' -Install -Serial RFGL34SJYDZ
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -DurationSeconds 180 -Tier Low -Scene WorldC -Autopilot route -Speed 50 -Extra 'stream=1'
```
