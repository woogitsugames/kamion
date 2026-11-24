# ADR 0333 — Płynność PC: sonda obciążenia systemu, opt-out z power throttlingu Windows, przejazdy bramkowe bez ramki

Status: **Proposed** (agent pacing-s24, rendering-perf, 24.11.2026; wdrożenie w gałęzi `pacing-s24`). Powiązane: D69 (bramka 3: ≤ 12 klatek > 40 ms na
przejazd), ADR 0266 (pomiar PC), 0261 (build/uruchomienie Windows), 0291 (D3D11 domyślne), 0273 (streaming kafli).

## Kontekst
Przejazd C → Tykocin buildu #5 na „pustym” PC (runs/20261123-223724) dał 597 klatek > 40 ms (p99 32,8 ms, max 746 ms),
więcej niż przebieg z obciążeniem (222). Hipoteza zlecenia: oczekiwanie na present/VSync/OS (klatki ~48–50 ms = „3 vsynce”).

## Analiza (dane: `artifacts/pacing-s24/analysis/`)
1. **Kwantyzacji nie ma.** VSync wyłączony, limit `targetFrameRate = 60`. Klatki 18–70 ms mają rozkład ciągły — ani
   wielokrotności 16,67 ms (vsync), ani 15,625 ms (domyślny zegar Windows). Present/swap chain/rozdzielczość timera
   odpadają jako przyczyna główna. Skoki przychodzą seriami (klatka przed/po skoku śr. 23–31 ms), nie pojedynczo.
2. **Skupiska pokrywają się z pracą innych agentów, nie z trasą.** 579 z 597 klatek leży w dwóch oknach czasu:
   t 2160–2308 s (23:13:24–23:15:52) i t 2820–3660 s (23:24–23:38). Library worktree `banks2-s24` powstał 23:13:35,
   `monument2-s24` 23:15:27, `haze-s24` 23:36:19 (kopiowanie artifacts od ~23:24); lider startował wtedy 5 agentów
   (robocopy ~9 GB małych plików + skan Defendera + importy Unity). „Pusty PC” nie był pusty.
3. **Ten sam kadr, inny wynik.** Pojazd stoi przy celu (Pl. Czarnieckiego): t 3540–3660 s → 54–59 klatek > 40 ms na
   minutę i GPU gry śr. 10,7 ms; t 3720+ s → 0 klatek > 40 ms i GPU 4,9 ms. Treść świata się nie zmienia, zmienia się
   obciążenie maszyny — spowalnia zarówno CPU główny, jak i GPU gry (współdzielony GPU / rdzenie).
4. **Build #6** (artifacts/full-build-6-s24/run, 152 klatki > 40 ms): ten sam wzór — skupiska t 1020–1080 s (dk65-04)
   i 2340–2520 s (dw671-tykocin-03) przy CPU tła 36–47 % (dane lidera), poza nimi pojedyncze skoki.
5. **Część własna gry (czyste okno t 10–2150 s #5, 13 kafli): 18 klatek > 40 ms**, prawie każda w chwili zdarzenia
   streamingu (aktywacja/zwolnienie kafla, 40–87 ms, ~1 na kafel). Ekstrapolacja ~30 na 28 kafli trasy → bramka 3
   bez obciążenia nadal FAIL, ale z innego powodu: koszt jednej klatki aktywacji kafla (zadanie dla streamingu, poniżej).

## Pomiary A/B (build #5 `770ea8d900`, dw671-tykocin-06, High, limit 60, VSync 0, autopilot 50 km/h, 80 s po rozgrzewce)
Maszyna dewelopera i5-10400F / GTX 1070 / 64 GB, D3D11 (o ile nie podano), 24.11 09:24–10:02. „Inne CPU” = średnie
obciążenie maszyny przez inne procesy z `sysload.csv`. Gra nigdy nie miała fokusu (pierwszy plan: aplikacja Claude).
Dane: `artifacts/pacing-s24/runs/<hhmmss>-E*/` (pc-report.md, frames.csv, sysload.csv, pacing.json).

| przebieg | tryb okna | tło | inne CPU | p95 / p99 / max [ms] | kl. > 33,3 | kl. > 40 | CPU główny p95 |
|---|---|---|---|---|---|---|---|
| E1 | bez ramki 1920x1080 | czysto | 6,6 % | 16,67 / 16,67 / ≤ 33 | 0 | 0 | — |
| E2 | bez ramki | robocopy Library + 4 pętle CPU | 40,6 % | 16,67 / 16,68 / 23,3 | 0 | 0 | 7,9 |
| E3 | bez ramki, **D3D12** | czysto | — | 16,67 / 17,79 / 202,9 | 4 | 4 | — |
| E1 r2 | bez ramki | agenci: Unity + 2× worldgen | 28,4 % | 16,67 / 17,00 / 64,3 | 7 | 3 | — |
| E6 | bez ramki | drugi player na GPU (GPU ~80 %) | — | 16,67 / 16,99 / 67,9 | 7 | 5 | — |
| E4 r2 | **okno 1600x900** | agenci (j.w.) | ~25 % | 28,11 / 45,98 / 101,3 | 167 | 73 | 25,2 |
| E8 | okno 1600x900 | agenci | 28,5 % | 35,42 / 52,91 / 126,0 | 246 | 147 | 30,5 |
| E7 | okno + **opt-out throttlingu** | agenci | 25,5 % | 16,69 / 24,49 / 53,3 | 28 | 16 | 8,7 |
| E9 | okno + opt-out | agenci (cięższe) | 40,5 % | 23,53 / 42,05 / 82,0 | 115 | 64 | 15,9 |
| E5 | bez ramki, **VSync 1** | czysto | 7,9 % | 16,70 / 16,77 / 791,1 | 4 | 4 | — |

Wnioski:
- Samo obciążenie CPU/dysku do ~40 % maszyny nie psuje gry w trybie bez ramki (E2). Agenci z Unity/worldgen dają kilka
  skoków (E1 r2, E6) — mało.
- **Okno 1600x900 bez fokusu przy tym samym tle jest 25–50× gorsze** (E4 r2, E8: 73–147 kl. > 40 ms), a CPU głównego
  wątku rośnie z ~5 do 25–30 ms p95 — praca gry trwa dłużej, czyli proces jest spowalniany przez system. Dokładnie tak
  uruchamiano przejazdy #5/#6 (`build-windows.ps1 -Run`: `-screen-fullscreen 0`, 1600x900, okno pod innymi oknami).
- Wyłączenie power throttlingu (EcoQoS: szybkość wykonania + ignorowanie rozdzielczości zegara) dla procesu gry
  (`scripts/set-power-throttling.ps1`, z zewnątrz, bez buildu) przy porównywalnym tle: 147 → 16 kl. > 40 ms, p99
  52,9 → 24,5 ms, CPU główny p95 30,5 → 8,7 ms (E8 vs E7). Przy cięższym tle (E9, 40 %) nadal 64 — opt-out pomaga,
  ale okno w tle pozostaje gorsze niż bez ramki. Mechanizm (EcoQoS vs brak priorytetu pierwszego planu) — częściowo
  UNVERIFIED; kierunek i skala potwierdzone 3 przebiegami przeplatanymi, n małe.
- VSync 1 (E5): narastające zacięcia 157→791 ms w pierwszych 35 s (przyczyna UNVERIFIED); domyślne VSync 0 zostaje.
  D3D12 (E3) gorszy niż D3D11 — zgodne z ADR 0291.

## Decyzja
1. **Gra (Windows player):** `Game.Rendering.WindowsPowerThrottling` przy starcie (`RuntimeInitializeOnLoadMethod`,
   `BeforeSplashScreen`) woła `SetProcessInformation(ProcessPowerThrottling)` z ControlMask = EXECUTION_SPEED |
   IGNORE_TIMER_RESOLUTION, StateMask = 0 (nigdy nie dławić). Linia `[PACING]` w logu. Furtka A/B:
   `-power_throttling default`. Edytor i inne platformy bez zmian. Gra symulacyjna działająca w tle (np. podczas
   przełączania okien) nie powinna być dławiona jak aplikacja biurowa; koszt: wyższy pobór energii, gdy gra jest w tle.
2. **Przejazdy bramkowe** (D69) uruchamiać bez ramki: `build-windows.ps1 -Run -WindowMode borderless` (nowy parametr,
   domyślnie nadal `windowed` dla zgodności) albo `pc-metrics.ps1` (już bez ramki), na wolnej maszynie.
3. Każde uruchomienie pomiarowe (`build-windows.ps1 -Run`, `pc-metrics.ps1`) startuje w tle
   `scripts/sysload-sampler.ps1` → `sysload.csv` (co 1 s: CPU całej maszyny, gry, reszty, top-5 innych procesów, okno na
   pierwszym planie, GPU util/zegar/P-state/moc z nvidia-smi). Koszt ~21 ms CPU jednego rdzenia na próbkę + jedno
   wywołanie nvidia-smi, priorytet BelowNormal. Wyłącznik `-NoSysload`. Liczniki WMI odrzucone (~2,9 s/próbkę).
4. `tools/pcperf/pacing_attribution.py` dzieli klatki > progu na **czyste / zakłócone / bez próbki** (`pacing.json`).
   Zakłócona sekunda: inne procesy ≥ 10 % CPU maszyny albo GPU w stanie P3+ (WORKING_VALUE); reguła „gra nie na
   pierwszym planie” tylko na żądanie (`--require-foreground`) — sam brak fokusu w trybie bez ramki nie szkodził (E1/E2).
5. **Protokół bramki 3 (propozycja dla lidera/właściciela):** przejazd bez ramki, z sondą; ważny, gdy ≤ 2 % sekund
   zakłóconych (WORKING_VALUE); liczenie klatek > 40 ms do zdarzenia „Cel” (bez postoju). Na czas przejazdu bramkowego
   lider nie startuje agentów ani worktree.
6. ProjectSettings: bez zmian.

## Konsekwencje
- Wyniki przejazdów #5/#6 nie są dowodem regresji gry; trzeba je powtórzyć z sondą na naprawdę wolnej maszynie.
- Zostaje realny problem: ~1 klatka 40–90 ms na aktywację/zwolnienie kafla. Do zbadania profilerem na buildzie
  `-Development` (znacznik klatki aktywacji: `allowSceneActivation` → integracja sceny, `[WORLD] collision cooked`,
  włączanie chunków w budżecie 2 ms/klatkę — pojedynczy ciężki chunk przekracza budżet, bo budżet sprawdzany jest po
  włączeniu chunka).
- Opt-out w grze nie był jeszcze zmierzony w buildzie (pomiar E7/E9 = ten sam mechanizm ustawiony z zewnątrz);
  walidacja: build #7 + `pc-metrics` w oknie z tłem, porównanie z `-power_throttling default`.
- Przejazd #5/#6 trzeba powtórzyć bez ramki z sondą; dopiero wtedy liczba klatek > 40 ms jest miarą gry.
