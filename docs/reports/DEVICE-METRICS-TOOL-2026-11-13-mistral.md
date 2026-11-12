# M38 — narzędzie perfgate (tools/perf): raport bramki wydajności z pomiarów telefonu

Data: 2026-11-13 · Gałąź: `mistral/38-device-metrics-analysis` · Agent: Mistral (M38)

## Co powstało

Jedno narzędzie Python `tools/perf` (uv, `perfgate`), które z surowych plików pomiaru
(`artifacts/device/<serial>/<ts>/` i równoważnych katalogów, np. `artifacts/perf-low-r1|r2`)
daje **powtarzalny raport bramki wydajności** — liczby w ADR liczone zawsze tak samo.

```
tools/perf/
  pyproject.toml            uv; zależności: numpy, matplotlib; dev: pytest
  src/perfgate/
    formats.py              parsery + rejestr formatów (wersje w README); nieznane kolumny -> ParseError
    metrics.py              definicje metryk (niżej)
    compare.py              porównanie przebiegów: bootstrap CI (stałe ziarno 20261113)
    quality.py              wykrywanie pomiarów do odrzucenia
    report.py               raport MD + wykresy PNG (matplotlib)
    cli.py                  perfgate report | compare | history | check | formats
  tests/                    38 testów pytest na danych syntetycznych o znanych własnościach
  mutation_check.py + tests/mutations.py   test mutacyjny (weryfikacja B)
  README.md                 formaty + wersje + definicje metryk + metoda + założenia
```

Komendy:

```powershell
uv run --project tools/perf perfgate report artifacts/device/<serial>/<ts> [--out <dir>] [--warmup-s 5] [--target-fps 30|60]
uv run --project tools/perf perfgate compare <dirA> <dirB> [--boot 20000]
uv run --project tools/perf perfgate history artifacts/perf-low-r1 artifacts/perf-low-r2 --out <table.md>
uv run --project tools/perf perfgate check <run_dir>          # exit 1 = do odrzucenia
uv run --project tools/perf pytest tools/perf/tests -q
```

**Propozycja linii do `scripts/device-metrics.ps1` (propozycja tylko — skrypt bez zmian)**, wstawić po zapisaniu `metrics.json` (gdzie `$out` = katalog pomiaru):

```powershell
uv run --project tools/perf perfgate report $out --out (Join-Path $out 'perfgate-report')
```

## Formaty wejściowe (wszystkie znalezione w gicie; `git ls-files 'artifacts/**'`)

| plik | wersja | uwagi |
|---|---|---|
| `frametimes.csv` | v1 | jeden nagłówek we wszystkich 62 plikach: `frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab`; ms oprócz `t_s` [s]; puste końcowe kolumny = brak wartości; `gpu_ms`/`cpu_main_ms`=0 = „nie raportuje” |
| `metrics.json` | v1 | wyjście `scripts/device-metrics.ps1` |
| `summary.json` | v1 | wyjście diagnostyki gry (targetFps, qualityTier, pssKb, ...) |
| `diag-logcat.txt` / `logcat.txt` / `logcat-run.txt` | v1 | logcat threadtime; `[BOOT]`/`[DIAG] t=Ns ... temp=27.5C thermal=0 pss=889MB scale=0.75 ...` |
| `battery.txt` | v1 | `level:` [%], `temperature:` w 0.1 °C (276 = 27.6 °C — zgodne z `batteryTempC` w metrics.json) |
| `thermal.txt` | v1 | `Thermal Status: N`, `Temperature{mValue=°C, mStatus=}` |
| `meminfo.txt` | v1 | wiersz `TOTAL` — pierwsza liczba = PSS total kB (825305 kB = 806.0 MB = `pssMb` ✓) |
| `gfxinfo.txt` | v1 | bez sekcji „Janky frames” w zrzutach z repo |
| `gate3-result.json` | `truck-sim-pl/gate3-result/1` | metadane przejazdu |

Uwaga: `artifacts/fold-flicker/fold-run.ps1` i ADR 0152 **nie są w żadnej gałęzi repo**
(sprawdzone: `git ls-tree` po wszystkich branchach) — stąd definicja naprzemienności
została sformalizowana w narzędziu na podstawie opisu w HANDOVER.md („naprzemienność
100 % klatek … → 0 %, okna do 100 %”), oznaczona jako formalizacja M38.

## Definicje metryk (pełna wersja w tools/perf/README.md)

- Percentyle **nearest-rank** (`rank=ceil(p·n)`), identycznie jak `Get-Percentile` w `device-metrics.ps1` — zweryfikowane numerycznie przeciw `metrics.json` (patrz A).
- FPS średni = `n/(t_last−t_first)` po warm-up (jak `metrics.json`); + FPS harmoniczny.
- Cel: 30 FPS = 33.333 ms / 60 FPS = 16.667 ms (`--target-fps`, domyślnie `targetFps` z summary.json gdy 30/60).
- Frame pacing: MAD/RMS odchylenia od celu. > 1.5× celu: procent klatek. Janky: `> 2× cel` (definicja lokalna — gfxinfo nie raportuje własnej liczby w tych zrzutach).
- **Naprzemienność**: klatka `i≥1` naprzemienna gdy `|frame_ms[i]−frame_ms[i−1]| ≥ 0.5×cel`; `alternation_pct = 100·Σ/(n−1)`. Test: syntetyczna 15.6 % → 15.6 % dokładnie; pełne 16.7/50 ms → 100 %.
- Termika: trend = nachylenie LSQ `temp=` [°C/min]; **throttling** = pierwsze `t` z `thermal ≥ 2` (MODERATE+) lub `scale ≤ 0.95×skala_startowa`. Test: throttling w 120. s wykryty jako 120. s.
- PSS: min/max/trend [MB/min] z `pss=`; wyciek gdy trend > 0.5 MB/min przy ≥ 300 s (WORKING_VALUE).
- Okna przesuwne 10 s (krok 1 s, min 5 klatek i ≥ 1 s rozpiętości) — najgorsze okno wg p95 / FPS / naprzemienności.

## Porównanie przebiegów — metoda i założenia

Bootstrap na poziomie klatek: `B=20000` losowań ze zwracaniem (ziarno stałe 20261113),
`d = M(B) − M(A)`, 95 % CI = percentyle [2.5, 97.5]. Werdykt `regression` gdy CI w całości
po stronie regresji. **Założenie i.i.d. klatek** jest naruszane przez drift termiczny —
dlatego raport zawiera też okna 10 s. Przykład na prawdziwych danych
(`gate3-Low-A` r1 vs r2): `gpu_p95_ms` +0.589 ms, CI95 [0.36, 0.78] → **regression**
(zgodne z narracją ADR 0136); `p95_ms` −0.030 ms, CI [−0.055, 0.000] → brak istotnej różnicy.

## Wykrywanie pomiarów do odrzucenia (`perfgate check`)

Bateria < 40 %, temperatura startowa > 36.0 °C (zadanie M38 + reguła HANDOVER „≥ 40 %, < 36 °C"),
ekran wyłączony/zablokowany (fps < 1.0 przez ≥ 30 s przy rosnącym t, lub 0 klatek po warm-up),
thermal ≥ 3 (SEVERE). Każdy werdykt ma dowód (wiersz/liczba). Na 62 katalogach z repo:
wszystkie VALID (A16, bateria 80 %, 27.5 °C — zgodne z oczekiwaniem).

## Weryfikacja A–E (dowody)

- **A. niezależny przegląd** (bez subagentów = 2 przebiegi od zera): osobny skrypt numpy
  (nie importuje perfgate) przeliczył metryki dla **4 prawdziwych plików** z repo
  (`perf-low-r1/diag0/base0`, `perf-low-r1/final/gate3-Low-B`, `perf-low-r2/final/gate3-Low-A`,
  `perf-low-r2/diag1/ab_forest`) — wszystkie metryki (n, span, FPS, p50/p95/p99/max, GPU p95,
  CPU p95, >1.5×, naprzemienność) zgodne z perfgate **i** z `metrics.json` z repo
  (np. base0: p95 33.469 = metrics.json 33.469; over50ms 32 = 32). Drugi przebieg od zera:
  jednostki sprawdzone (ms vs s vs 0.1 °C vs kB — zgodne z metrics.json), percentyle
  nearest-rank, warm-up `t_s >= warmup` jak w ps1, próbki GPU=0 odrzucane; raport wygenerowany
  2× z zera → bajtowo identyczny.
- **B. test mutacyjny**: `uv run --project tools/perf python tools/perf/mutation_check.py`
  — **15/15 mutacji zabitych** (tabela: percentile-linear, alternation-threshold-0.9,
  over-1.5x-1.4, janky-1.5x, fps-span-off-by-one, warmup-strict-gt, gpu-zero-included,
  window-min-frames-1000, throttle-status-4, scale-drop-0.5, pss-leak-threshold-1000,
  battery-min-10, temp-max-100, verdict-swap, unknown-column-ok — każda kończy odpowiednie
  testy FAIL).
- **C. pytest**: `uv run --project tools/perf pytest tools/perf/tests -q` → **38 passed**.
- **D. rebase** na najnowszego origin/main tuż przed PR + ponowne C (wynik w PR).
- **E.** lista A–D w opisie PR.

## Historia bramek (rozszerzenie b)

`perfgate history artifacts/perf-low-r1 artifacts/perf-low-r2` → jedna tabela 62 pomiarów
(n, FPS, p50/p95/p99/max, GPU p95, >1.5× %, naprzemienność %, T start/trend, throttling,
PSS max/trend, werdykt jakości).

## Nie zmieniono

`scripts/*.ps1`, `game/**`, `Data/**`, `*.glb`, `*_meta.json`, `.gitattributes`, LFS —
diff dotyczy tylko `tools/perf/**` i tego raportu. Żadnych zmyślonych liczb: cele bramki
cytowane z `docs/PERFORMANCE_BUDGETS.md` jako WORKING_VALUE; progi odrzucania cytowane
z zadania/HANDOVER; reszta mierzona.

## Otwarte

- ADR 0152 nie istnieje w repo — definicja naprzemienności to formalizacja M38; przy scaleniu
  0152 warto zweryfikować zgodność progu 0.5×cel.
- `artifacts/fold-flicker/fold-run.ps1` (camlog=1) nie jest w gicie — parser logów kamery
  czeka na pierwszy zapisany przebieg (formát będzie dopisany jako v2 z błędem na nieznane kolumny).
- Prog wycieku PSS (0.5 MB/min / 300 s) to WORKING_VALUE.
