"""Test mutacyjny każdej metryki (weryfikacja B zadania M38).

Dla każdej mutacji z tests/mutations.py uruchamia pełny zestaw pytest
z PERFGATE_MUTATION=<nazwa>; mutacja jest ZABITA gdy odpowiednie testy
kończą się FAIL (returncode != 0). Wypisuje tabelę.

Uruchomienie: uv run --project tools/perf python tools/perf/mutation_check.py
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tests"))
from mutations import MUTATIONS  # noqa: E402


def run_suite(mutation: str | None) -> tuple[int, list[str]]:
    env = dict(os.environ)
    if mutation:
        env["PERFGATE_MUTATION"] = mutation
    else:
        env.pop("PERFGATE_MUTATION", None)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "--tb=no", "-rf"],
        cwd=HERE,
        env=env,
        capture_output=True,
        text=True,
    )
    failed = [ln.split("::")[-1].split(" ")[0] for ln in proc.stdout.splitlines() if ln.startswith("FAILED")]
    return proc.returncode, failed


def main() -> int:
    rc0, _ = run_suite(None)
    if rc0 != 0:
        print("BŁĄD: baza (bez mutacji) nie przechodzi testów — przerwano.")
        return 1
    print(f"{'mutacja':32} {'zabita?':8}  testy FAIL")
    all_killed = True
    for m in MUTATIONS:
        rc, failed = run_suite(m)
        killed = rc != 0
        all_killed &= killed
        print(f"{m:32} {'TAK' if killed else 'NIE':8}  {', '.join(failed) if failed else '-'}")
    print()
    print("WSZYSTKIE MUTACJE ZABITE" if all_killed else "SĄ NIEZABITE MUTACJE — popraw definicje/testy")
    return 0 if all_killed else 1


if __name__ == "__main__":
    sys.exit(main())
