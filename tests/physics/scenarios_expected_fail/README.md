# Expected-failure physics scenarios

Scenariusze z `tests/physics/scenarios_expected_fail/*.json` to **znane, niezaspokojone wymagania** z
`docs/04_FIZYKA.md` §6 (lub warianty, których fizyka jeszcze nie spełnia). Nie są uruchamiane przez
`Runner` ani `ScenarioTests` (oba czytają tylko `tests/physics/scenarios/`), więc nie łamią CI.

Test `ExpectedFailureTests.KnownFailure_StillFails_WithReason` (xUnit) uruchamia każdy plik stąd i
**asertuje, że nadal nie przechodzi**, wypisując niezdanie checki i opis z pola `expectedFailReason`
w JSON. Gdy fizyka zostanie poprawiona: przenieś plik do `tests/physics/scenarios/` i usuń
`expectedFailReason` — test wtedy zacznie wymagać przejścia przez zwykły `ScenarioTests`.
