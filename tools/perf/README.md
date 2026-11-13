# tools/perf — perfgate (M38): raport bramki wydajności z pomiarów telefonu

Jedno narzędzie Python, które z surowych plików pomiaru (`artifacts/device/<serial>/<ts>/`
i równoważnych katalogów, np. `artifacts/perf-low-r1/...`) daje **powtarzalny** raport
bramki wydajności — liczby w ADR liczone zawsze tak samo.

Uruchomienie (z katalogu repo, jak pozostałe narzędzia `uv`):

```powershell
uv run --project tools/perf perfgate report artifacts/device/RFGL34SJYDZ/20261111-122732
uv run --project tools/perf perfgate compare <dirA> <dirB>            # przed/po lub telefon A vs B
uv run --project tools/perf perfgate history artifacts/perf-low-r2/final --out artifacts/perf-low-r2/final/perfgate-history.md
uv run --project tools/perf perfgate check artifacts/perf-low-r1/diag0/base0   # exit 1 = do odrzucenia
uv run --project tools/perf perfgate formats                           # lista formatów + wersje
uv run --project tools/perf pytest tools/perf/tests -q                 # testy
```

Propozycja linii do wpięcia w `scripts/device-metrics.ps1` (propozycja tylko — skrypt
bez zmian; wstawić po zapisaniu `metrics.json`, gdzie `$out` = katalog pomiaru):

```powershell
uv run --project tools/perf perfgate report $out --out (Join-Path $out 'perfgate-report')
```

## Formaty wejściowe i wersje (parser: `perfgate/formats.py`)

Nieznane kolumny w `frametimes.csv` → błąd z komunikatem (żadnych cichych pominięć).

| plik | wersja | opis |
|---|---|---|
| `frametimes.csv` | v1 | nagłówek dokładnie `frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab`; `t_s` [s], reszta [ms]; `gpu_ms`/`cpu_main_ms` = 0.000 = „sterownik nie raportuje” (odrzucane przy percentylach, jak w `device-metrics.ps1`) |
| `metrics.json` | v1 | wyjście `scripts/device-metrics.ps1` (serial, timestamp, device, pssMb, batteryTempC, thermalStatus, frameTime, gpuMs, cpuMainMs, gameSummary) |
| `summary.json` | v1 | wyjście diagnostyki gry (build, qualityTier, targetFps, meanFps, p50Ms..., pssKb, renderScale, capFallback) |
| `diag-logcat.txt` / `logcat.txt` / `logcat-run.txt` | v1 | `adb logcat -v threadtime`; linie `[BOOT] k=v ...` i `[DIAG] t=3s ... temp=27.5C thermal=0 headroom=0.50 pss=889MB scale=0.75 ...` (wartości z jednostkami typu `27.5C`, `889MB`, `3s` — parser bierze wiodącą liczbę; `gpu=-` = brak) |
| `battery.txt` | v1 | `dumpsys battery`: `level:` [%], `temperature:` [0.1 °C] — dzielone przez 10 |
| `thermal.txt` | v1 | `dumpsys thermalservice`: `Thermal Status: N`, `Temperature{mValue=°C, mType=, mName=, mStatus=}` (mStatus = throttling czujnika) |
| `meminfo.txt` | v1 | `dumpsys meminfo <pkg>`: wiersz `TOTAL PSS: <kB>` lub `TOTAL <kB> ...` (pierwsza liczba = PSS total) |
| `gfxinfo.txt` | v1 | `dumpsys gfxinfo <pkg>`; opcjonalnie `Janky frames: N (P%)` / `Total frames rendered: N` (w zrzutach z repo sekcja statystyk nie występuje) |
| `gate3-result.json` | `truck-sim-pl/gate3-result/1` | metadane przejazdu gate3 |

## Definicje metryk (jedne dla wszystkich raportów; `perfgate/metrics.py`)

- **Percentyle**: nearest-rank — `rank = ceil(p*n)` (min 1), wartość `sorted[rank-1]`; identycznie jak `Get-Percentile` w `scripts/device-metrics.ps1`. **Nie** interpolacja liniowa.
- **FPS średni** = `n / (t_last - t_first)` po warm-up (jak `metrics.json`); dodatkowo FPS harmoniczny = `1000 / mean(frame_ms)`.
- **Warm-up**: domyślnie `frameTime.warmupSeconds` z `metrics.json` pomiaru (te same liczby co `device-metrics.ps1`), bez `metrics.json` 5 s (jak `-WarmupSeconds 5`); parametr `--warmup-s` nadpisuje.
- **Cel klatki**: `--target-fps 30|60`, domyślnie `targetFps` z `summary.json` gdy 30/60, inaczej 30 → 33.333 / 16.667 ms.
- **Frame pacing**: MAD i RMS odchylenia `frame_ms` od celu [ms].
- **> 1.5× celu**: procent klatek z `frame_ms > 1.5 * target_ms` (przy 30 FPS: > 50.0 ms).
- **Janky frames**: definicja lokalna (sekcja gfxinfo w tych zrzutach nie raportuje własnej liczby): `frame_ms > 2 * target_ms` — klatka pominęła ≥ 2 pełne vsynci (przy 30 FPS: > 66.667 ms).
- **Naprzemienność pozy kamery (ADR 0152)**: `campose_alternation(diag/campose.csv)` — port `campose.py` z ADR 0152 (krok pozy zmienia znak, oba kroki > 2 mm / 0,05°, warm-up 25 s); w raporcie, gdy w katalogu jest `campose.csv`. A16: 15,6 % → 0,0 %.
- **Skoki czasu klatki** (pole `alternation_*`; integracja r6 — to NIE jest naprzemienność ADR 0152, która jest w repo): klatka `i ≥ 1` jest naprzemienna, gdy `|frame_ms[i] - frame_ms[i-1]| >= 0.5 * target_ms`; `alternation_pct = 100 * Σ / (n-1)`. Pełna naprzemienność vsync (16.7/33.3 ms) daje 100 % („okna do 100 %”), stały render 0 %. Test: syntetyczna naprzemienność 15.6 % daje 15.6 %.
- **Trend termiczny**: nachylenie LSQ temperatury z `[DIAG] temp=` [°C/min]; **moment throttlingu** = pierwsze `t`, w którym `thermal >= 2` (MODERATE+, nazwy statusów Androida) **lub** skala renderu `scale` spadła poniżej `0.95 × skala startowa` (adaptacyjna skala = reakcja na temperaturę).
- **PSS**: min/max/trend (nachylenie LSQ [MB/min]) z `[DIAG] pss=`; podejrzenie wycieku gdy trend > 0.5 MB/min przy rozpiętości ≥ 300 s (próg `WORKING_VALUE`).
- **Okna przesuwne**: szerokość `--window-s` (domyślnie 10 s), krok 1 s; okno ważne przy ≥ 5 klatkach i rozpiętości ≥ 1 s. Raportowane najgorsze okno wg p95, wg FPS i wg naprzemienności.

## Porównanie przebiegów (`perfgate/compare.py`)

Dla metryk: mean_fps, p50/p95/p99/max ms, gpu_p95, pacing_mad, over_1_5x_pct, janky_pct,
alternation_pct. Metoda: **bootstrap na poziomie klatek** — `B` razy (domyślnie 20000,
ziarno stałe = 20261113, wynik powtarzalny) losowanie ze zwracaniem próbek z A i z B,
różnica `d = M(B) - M(A)`; 95 % przedział ufności = percentyle [2.5, 97.5] rozkładu `d`.
Werdykt: dla metryk czasowych/procentowych `regression` gdy CI leży w całości > 0,
`improvement` gdy < 0, inaczej `no-significant-difference` (dla FPS odwrotnie).
**Założenia**: klatki w przebiegu i.i.d. — narusza to drift termiczny i autokorelacja,
dlatego raport pokazuje też okna 10 s. „Brak regresji” = liczba (granica CI ≤ 0), nie wrażenie.

## Wykrywanie pomiarów do odrzucenia (`perfgate/quality.py`, `perfgate check`)

Progi ze zadania M38 i HANDOVER.md („telefon właściciela: ≥ 40 %, < 36 °C”):
bateria `< 40 %` (battery.txt), temperatura startowa `> 36.0 °C` (pierwsza próbka
`temp=` z `[DIAG]`, awaryjnie `battery.txt`), ekran wyłączony / telefon zablokowany
(utrzymane `fps < 1.0` przy rosnącym `t` przez ≥ 30 s w `[DIAG]`, lub 0 klatek po
warm-up), `thermal >= 3` (SEVERE) w którejkolwiek próbce. Każdy werdykt ma dowód
(konkretny wiersz). Brak danych = brak werdyktu.

## Struktura

```
tools/perf/
  pyproject.toml          (uv; zależności: numpy, matplotlib; dev: pytest)
  src/perfgate/
    formats.py            parsery + rejestr formatów (nieznane kolumny -> ParseError)
    metrics.py            definicje metryk (sekcja wyżej)
    compare.py            bootstrapowe porównanie przebiegów
    quality.py            wykrywanie pomiarów do odrzucenia
    report.py             raport MD + wykresy PNG
    cli.py                perfgate report|compare|history|check|formats
  tests/                  pytest na danych syntetycznych o znanych własnościach
```
