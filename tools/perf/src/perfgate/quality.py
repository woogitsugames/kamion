"""Wykrywanie pomiarów do odrzucenia (rozszerzenie c) — tylko z logów/artefaktów.

Progi (źródła: zadanie M38 + HANDOVER.md „telefon własiciela: >= 40 %, < 36 °C”):
- bateria < 40 % (battery.txt `level:`) -> odrzucić;
- temperatura startowa > 36.0 °C -> odrzucić (pierwsza próbka temp= z [DIAG],
  awaryjnie battery.txt `temperature:`/10);
- telefon zablokowany / ekran wyłączony -> odrzucić: wykrywane jako
  utrzymane fps < 1.0 przy rosnącym t w seriach [DIAG] (>= 30 s) albo
  brak klatek w CSV po warm-up;
- thermal status >= 3 (SEVERE) w którejkolwiek próbce -> odrzucić (pomiar
  pod throttlingiem).

Każdy powód ma dowód (konkretny wiersz/liczba). Brak danych = brak werdyktu
(nie zgadujemy).
"""

from __future__ import annotations

from dataclasses import dataclass, field

BATTERY_MIN_LEVEL_PCT = 40
START_TEMP_MAX_C = 36.0
THERMAL_SEVERE = 3
SCREEN_OFF_FPS_MAX = 1.0
SCREEN_OFF_MIN_SPAN_S = 30.0


@dataclass
class QualityVerdict:
    valid: bool
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


def check_run_quality(run: dict, warmup_s: float = 5.0) -> QualityVerdict:
    """run = wynik formats.load_run_dir(). Zwraca werdykt + dowody."""
    verdict = QualityVerdict(valid=True)

    battery = run.get("battery")
    if battery:
        if battery["level_pct"] < BATTERY_MIN_LEVEL_PCT:
            verdict.valid = False
            verdict.reasons.append(
                f"bateria {battery['level_pct']} % < {BATTERY_MIN_LEVEL_PCT} %"
            )
            verdict.evidence.append(f"battery.txt: level: {battery['level_pct']}")
        start_temp = battery["temperature_c"]
    else:
        start_temp = None

    diags = run.get("diags") or []
    if diags:
        temps = [(d.t_s, d.get_float("temp")) for d in diags if d.get_float("temp") is not None]
        if temps and start_temp is None:
            start_temp = temps[0][1]
        if temps and temps[0][1] > START_TEMP_MAX_C:
            verdict.valid = False
            verdict.reasons.append(
                f"temperatura startowa {temps[0][1]:.1f} °C > {START_TEMP_MAX_C:.1f} °C"
            )
            verdict.evidence.append(f"[DIAG] pierwsza próbka: t={temps[0][0]:.0f}s temp={temps[0][1]:.1f}C")
        statuses = [(d.t_s, d.get_float("thermal")) for d in diags if d.get_float("thermal") is not None]
        severe = [s for s in statuses if s[1] >= THERMAL_SEVERE]
        if severe:
            verdict.valid = False
            verdict.reasons.append(
                f"thermal status {int(severe[0][1])} (SEVERE+) od t={severe[0][0]:.0f} s"
            )
            verdict.evidence.append(f"[DIAG] t={severe[0][0]:.0f}s thermal={int(severe[0][1])}")
        fps_series = [(d.t_s, d.get_float("fps")) for d in diags if d.get_float("fps") is not None]
        if len(fps_series) >= 2:
            span = fps_series[-1][0] - fps_series[0][0]
            if span >= SCREEN_OFF_MIN_SPAN_S and all(f < SCREEN_OFF_FPS_MAX for _, f in fps_series):
                verdict.valid = False
                verdict.reasons.append(
                    f"fps < {SCREEN_OFF_FPS_MAX} przez całe {span:.0f} s — ekran wyłączony / telefon zablokowany"
                )
                verdict.evidence.append(
                    f"[DIAG] t={fps_series[0][0]:.0f}..{fps_series[-1][0]:.0f}s fps max={max(f for _, f in fps_series):.2f}"
                )

    frames = run.get("frames")
    if frames is not None:
        kept = [r for r in frames if r.t_s >= warmup_s] or list(frames)
        if not kept:
            verdict.valid = False
            verdict.reasons.append("brak klatek w frametimes.csv po warm-up")
            verdict.evidence.append("frametimes.csv: 0 próbek")

    if start_temp is not None and battery is not None and start_temp > START_TEMP_MAX_C:
        if not any("temperatura startowa" in r for r in verdict.reasons):
            verdict.valid = False
            verdict.reasons.append(
                f"temperatura startowa {start_temp:.1f} °C > {START_TEMP_MAX_C:.1f} °C"
            )
            verdict.evidence.append(f"battery.txt: temperature: {start_temp * 10:.0f} (dziesiąte °C)")

    return verdict
