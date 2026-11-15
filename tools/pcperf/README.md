# tools/pcperf — pomiar playera Windows (ADR 0266)

Odpowiednik `scripts/device-metrics.ps1` + `tools/perf` (perfgate) dla platformy głównej PC (D73). Tylko biblioteka
standardowa Pythona.

| element | ścieżka |
|---|---|
| nagrywanie w grze | `game/Assets/_Project/Telemetry/PcFrameMetricsRecorder.cs` (włącza się argumentem `-metrics <dir>`) |
| czysta logika (percentyle, argumenty) | `game/Assets/_Project/Telemetry/PcMetricsMath.cs` + test `Tests/EditMode/PcMetricsMathTests.cs` |
| uruchomienie playera + liczniki Windows | `scripts/pc-metrics.ps1` |
| parser / raport / budżet | `tools/pcperf/pc_metrics.py` |
| budżety klas (wszystko `WORKING_VALUE`) | `tools/pcperf/budgets/pc-budgets.json` (= tabela w `docs/03`) |

```powershell
# pełny pomiar (lider, Windows): build -> run -> raport
pwsh scripts/pc-metrics.ps1 -Exe artifacts/windows/<build>/Kamion.exe -Scene knyszyn -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany
# sam parser na istniejącym katalogu
uv run --no-project python tools/pcperf/pc_metrics.py artifacts/pc/<maszyna>/<ts> --class zalecany
# testy
uv run --no-project --with pytest pytest tools/pcperf/tests -q
```

Argumenty playera (czyta `PcMetricsOptions.Parse`): `-metrics <dir>` (wymagany), `-metricsSeconds 90`, `-metricsWarmup 5`,
`-metricsStart boot|region` (domyślnie `region`, gdy podano `-scene`), `-metricsTimeout 300`, `-metricsVsync 0|1`,
`-metricsQuit 0|1` (domyślnie 1 — player sam się zamyka; kod wyjścia 0 = OK, 3 = brak regionu w czasie, 4 = błąd zapisu),
`-metricsMaxFps 1000` (rozmiar bufora), `-metricsLabel <tekst>`. Pozostałe argumenty gry jak dotąd (`-tier`, `-fps`,
`-scene`, standardowe Unity `-screen-width/-screen-height/-screen-fullscreen/-window-mode/-logFile`).

## Formaty (wersja 1)

| plik | źródło | kolumny / pola |
|---|---|---|
| `frames.csv` | gra | `frame,t_s,frame_ms,cpu_main_ms,gpu_ms,draw_calls,batches,setpass,tris,gc_count,scene`; `t_s` od początku okna; `cpu/gpu` 0 = sterownik nie raportuje; liczniki -1 = niedostępne w tym playerze; `scene` = numer sceny (0 = Boot) |
| `memory.csv` | gra, co 0,5 s | `t_s,allocated_mb,reserved_mb,mono_used_mb,mono_heap_mb,gfx_driver_mb,gc_count` (`gfx_driver_mb` -1 poza buildem development) |
| `run.json` | gra | `format: kamion/pc-metrics/1`, `system` (SystemInfo), `display` (rozdzielczość, VSync, limit, tier), `options`, `recording` (klatki, utrata fokusu, GC), `loads[]` (czas ładowania sceny: od klatki, która zleciła LoadScene, albo od `MarkRegionLoadStart()`, do końca pierwszej klatki nowej sceny), `inGame` (percentyle do kontroli krzyżowej) |
| `process.csv` | `pc-metrics.ps1` co 1 s | `t_s,working_set_mb,private_mb,gpu_dedicated_mb,gpu_shared_mb,gpu_temp_c,gpu_util_pct` (VRAM z licznika Windows „GPU Process Memory”; temp./obciążenie tylko z `nvidia-smi`, inaczej puste) |

Nieznane kolumny → błąd (exit 2), bez cichego pomijania. Kody wyjścia parsera: 0 PASS/INCOMPLETE/NO_BUDGET, 1 FAIL, 2 INVALID.

Pomiar jest **nieważny** (INVALID): edytor, < `minFramesAfterWarmup` klatek, utrata fokusu, przepełniony bufor, koniec
inny niż `duration`, warunki inne niż w klasie (rozdzielczość / tier / limit FPS; `--allow-context-mismatch` = tylko informacyjnie).
Maszyna spoza `referenceMachines` (dziś lista pusta) → `gate_eligible: false` — wynik informacyjny, nie zalicza bramki.
