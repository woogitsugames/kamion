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

## Wyniki przed/po (A16, Low 30 FPS, okno od 25 s; dowody `artifacts/perf-p99-0177/{s17-probe,trace,ab}`)
Nowe kolekcje (build Development `7208ebff1a`, świat s17): g3a 85 wariantów / 159 stanów (stare 78/140), g3b 78/154 (stare 67/134)
— +19/+20 stanów nieobjętych prewarmem = hipoteza potwierdzona. Warm-up obu: 2,8 s w czasie ładowania.

| APK / wariant | G3-A >40 ms | G3-A p99 | G3-B >40 ms | G3-B p99 | p95 |
|---|---|---|---|---|---|
| s16 (gate3 11-13, odniesienie) | 14 | 33,61 | 14 / 16 | 33,59 / 33,69 | 33,45–33,46 |
| s17 `3a60019ff1` (gate3 + `spike_probe`) | 23 / 17 | 49,93 / 33,75 | 22 / 30 | 49,87 / 49,98 | 33,46–33,47 |
| `c5887f4fbb` nowe PSO, stara telemetria (`diag_poll main`) | 17 / 16 | 33,68 / 33,61 | 19 / 16 | 33,72 / 33,63 | 33,45–33,48 |
| `c5887f4fbb` nowe PSO + telemetria w tle (domyślnie) | **1 / 10** | 33,50 / 33,60 | **2 / 12** | 33,56 / 33,58 | 33,43–33,45 |

Zaplanowane przeplatane przebiegi starego APK po przebudowie nie odbyły się: A16 zniknął z USB o 19:26 (`device offline` ->
`not found`) przy reinstalacji starszego APK (uninstall + install); odniesieniem są 4 przebiegi tego samego APK s17 z tego dnia.
Rozrzut między przebiegami jest duży (B s17: 22 vs 30) — wniosek z kierunku każdej pary, nie z pojedynczej liczby.

## Propozycja dla właściciela: dodatkowa metryka bramki „klatki > 40 ms”
p99 na oknie ~1800–2100 klatek zmienia się skokowo 33,7 <-> 50,0 przy ~18–20 klatkach > 40 ms (ranga 1 %); 1–2 klatki zmieniają
werdykt, a pogorszenie 14 -> 23 jest niewidoczne, dopóki nie przekroczy klifu. Propozycja (decyzja właściciela):
- raportować obok p99 **liczbę klatek > 40 ms w oknie przejazdu** (i na minutę) z każdego przejazdu bramki;
- próg WORKING_VALUE dla A16 Low: **≤ 12 na przejazd G3 (~≤ 11/min, ~0,6 % klatek)** — przechodzi stan po 0177 (1–12),
  odrzuca s17 (17–30) i stan sprzed prewarmu 0113 (37–40); s16 (14–16) byłby tuż nad progiem.
- Historia (G3-A / G3-B): 11-12 przed PSO 40 / 37 · s16 14 / 14–16 · s17 23–17 / 22–30 · po 0177 1–10 / 2–12.

## Konsekwencje
- PSS w `summary.json` / `[DIAG]` odświeża się co 10 s zamiast 2 s; `device-metrics.ps1` i tak bierze PSS z `dumpsys meminfo` po przejeździe.
- Kolekcje PSO starzeją się z każdą zmianą treści; bez odświeżenia wraca ~5–10 skoków na przejazd.
