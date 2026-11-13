# ADR 0177: Regresja p99 bramki 3 na A16 Low — telemetria na wątku głównym, nieaktualne kolekcje PSO, metryka „klatki > 40 ms”

Status: propozycja (rendering-perf, gałąź `perf-p99-0177`), 2026-11-13.
Powiązane: ADR 0113 (prewarm PSO, `GraphicsStateCollection`, sonda `[SPIKE]`), 0106, D49 (A16 = Low 30 FPS).

## Kontekst
Bramka 3, A16 (SM-A165F, Mali-G57 MC2, Vulkan), Low 30 FPS, odcinki G3-A i G3-B: s16 p99 33,6 ms, s17 (APK `3a60019ff1`) p99 49,9 ms.

## Diagnoza (telefon, okno od 25 s, `tools/perf/p99_spikes.py`)
1. **p99 jest metryką-klifem.** Okno ma 1840–2080 klatek, ranga 1 % = 18–20. Skok to prawie zawsze jedna klatka 50 ms
   (jeden pominięty vsync), więc p99 skacze z 33,7 na 50,0, gdy klatek > 40 ms jest więcej niż ~19. s17 (gate3) 23 i 22,
   s16 14 / 14 / 16. 1–2 klatki różnicy przełączają werdykt.
2. **Brak nowej pracy GPU/CPU.** GPU p50/p90 G3-B: s16 31,39 / 33,26 ms, s17 31,38 / 33,25; CPU main p50 ~20–21 ms w obu.
   GPU stoi ~1 ms pod budżetem 33,3 ms (p90 ≈ budżet) — każde zakłócenie > ~1–2 ms to pominięty vsync.
3. **GC nie jest przyczyną.** `spike_probe 1` (release): 1 GC na przejazd, przed oknem.
4. **Kod 0168/0165 nie jest przyczyną.** 0168: ETA z O(punkty trasy) na klatkę -> 1 Hz (taniej); NavVoiceDriver bez alokacji.
   0165: `IgnoreCollision` tylko przy podpięciu naczepy; +4 sumy Vec3 na krok.
5. **Efekt obserwatora — telemetria.** `DiagnosticsSampler` co 2 s w jednej klatce wołał na wątku głównym JNI: bateria
   (`registerReceiver`), `getCurrentThermalStatus`, `getThermalHeadroom` i `android.os.Debug.getPss()` (przejście po smaps
   procesu) + flush CSV. Klatka bezpośrednio po tym odpytaniu to 5–16 skoków na przejazd (s16 8 / 10 / 5, s17 8 / 10 / 5 / 16 / 8 / 14).
6. **Nieaktualne kolekcje PSO.** Kolekcje `pso_Vulkan_Low_g3{a,b}` nagrano 2026-11-11 (przed 0161–0169: meble, tablice,
   drzewa ogrodów, budynki). `pso_warm 0` vs `1` na APK s17: A 21 vs 17, B 28 vs 30 — prewarm prawie nic już nie daje
   (w 0113: 40 -> 14). Nadwyżka s17 siedzi w skokach „innych” niż sondowe: s16 6 / 4 / 11, s17 12–15.

## Decyzja
1. `DiagnosticsSampler`: domyślny tryb `diag_poll bg` — bateria / status termiczny / headroom po jednym w kolejnych klatkach,
   PSS na wątku w tle co 10 s (`PssIntervalBg`, WORKING_VALUE). `diag_poll main` = stare zachowanie (A/B), `off` = bez sensorów.
2. Kolekcje PSO nagrywane ponownie po każdej regeneracji świata / nowych materiałach, jednym poleceniem:
   `pwsh tools/perf/pso-refresh.ps1 -BeforeApk <czysty APK po regeneracji>` (build Development, trace na A16, kopia do
   `Rendering/Resources/Pso/`, build release, przed/po ×2 przeplatane, podsumowanie).
3. Narzędzia: `tools/perf/phone-p99.ps1` (przejazdy A16 z blokadą PHONE_RUN), `tools/perf/p99_spikes.py` (rozkład skoków).

## Wyniki przed/po
(uzupełniane w trakcie — patrz niżej)

## Propozycja dla właściciela: dodatkowa metryka bramki „klatki > 40 ms”
(decyzja właściciela — niżej tylko liczby)

## Konsekwencje
- PSS w `summary.json` / `[DIAG]` odświeża się co 10 s zamiast 2 s; `device-metrics.ps1` i tak bierze PSS z `dumpsys meminfo` po przejeździe.
- Kolekcje PSO starzeją się z każdą zmianą treści; bez odświeżenia wraca ~5–10 skoków na przejazd.
