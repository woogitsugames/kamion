# ADR 0333 — Pomiar płynności PC z sondą obciążenia systemu; skoki przejazdu #5/#6 to głównie rywalizacja o maszynę

Status: **Proposed** (agent pacing-s24, rendering-perf, 24.11.2026). Powiązane: D69 (bramka 3: ≤ 12 klatek > 40 ms na
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

## Decyzja
1. Każde uruchomienie pomiarowe (`scripts/build-windows.ps1 -Run`, `scripts/pc-metrics.ps1`) startuje w tle
   `scripts/sysload-sampler.ps1` → `sysload.csv` (co 1 s: CPU całej maszyny, gry, reszty, top-5 innych procesów, okno na
   pierwszym planie, GPU util/zegar/P-state/moc z nvidia-smi). Koszt: ~21 ms CPU jednego rdzenia na próbkę + jedno
   wywołanie nvidia-smi, priorytet BelowNormal. Wyłącznik `-NoSysload`. Liczniki WMI odrzucone (~2,9 s/próbkę).
2. `tools/pcperf/pacing_attribution.py` dzieli klatki > progu na **czyste / zakłócone / bez próbki** (`pacing.json`).
   Zakłócona sekunda: inne procesy ≥ 10 % CPU maszyny, gra nie na pierwszym planie albo GPU w stanie P3+ (WORKING_VALUE).
3. **Protokół bramki 3 (propozycja dla lidera/właściciela):** przejazd ważny, gdy ≤ 2 % sekund zakłóconych; liczenie
   klatek > 40 ms do zdarzenia „Cel” (bez postoju). W czasie przejazdu bramkowego lider nie startuje agentów ani
   worktree (slot heavy + unity zajęte przez pomiar).
4. Zmian w ProjectSettings ani w kodzie gry ta decyzja nie wymaga (VSync/limit/tryb okna — wyniki A/B poniżej).

## Pomiary A/B (build #5, dw671-tykocin-06, High 60, autopilot 50 km/h, 90 s)
(uzupełniane — `artifacts/pacing-s24/runs/*/pc-report.md`, `pacing.json`)

## Konsekwencje
- Wyniki przejazdów #5/#6 nie są dowodem regresji gry; trzeba je powtórzyć z sondą na naprawdę wolnej maszynie.
- Zostaje realny problem: ~1 klatka 40–90 ms na aktywację/zwolnienie kafla. Do zbadania profilerem na buildzie
  `-Development` (znacznik klatki aktywacji: `allowSceneActivation` → integracja sceny, `[WORLD] collision cooked`,
  włączanie chunków w budżecie 2 ms/klatkę — pojedynczy ciężki chunk przekracza budżet, bo budżet sprawdzany jest po
  włączeniu chunka).
