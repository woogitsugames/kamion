# Expected-failure physics scenarios

Scenariusze z `tests/physics/scenarios_expected_fail/*.json` to **znane, niezaspokojone wymagania** z
`docs/04_FIZYKA.md` §6 (lub warianty, których fizyka jeszcze nie spełnia). Nie są uruchamiane przez
`Runner` ani `ScenarioTests` (oba czytają tylko `tests/physics/scenarios/`), więc nie łamią CI.

Test `ExpectedFailureTests.KnownFailures_FailExactlyTheExpectedMetrics` (xUnit) uruchamia każdy plik stąd i
**asertuje, że padają dokładnie metryki z pola `expectedFailMetrics`** (np. `["radius_error_m"]`), a wszystkie
pozostałe checki przechodzą. Wypisuje też niezdanie checki i opis z pola `expectedFailReason`.
Gdy fizyka zostanie poprawiona (oczekiwana metryka zacznie przechodzić), test pada z komunikatem
„naprawione? zdejmij expectedFail”: przenieś plik do `tests/physics/scenarios/` i usuń
`expectedFailReason` oraz `expectedFailMetrics` — test wtedy zacznie wymagać przejścia przez zwykły `ScenarioTests`.

`ring_96_53_comb.json` (pierścień 12,50/5,30 m z 96/53/WE zał. I pkt 1.5, ADR 0280) był tu znaną porażką przy rozstawie
sworzeń–środek tridemu 7,70 m. Po D79 (7,60 m w danych gry) jest zwykłym scenariuszem w `tests/physics/scenarios/`
(generator `generate_stage2_scenarios.py`, wyjście domyślne); scenariusz propozycji `ring_96_53_comb_rwb760` usunięty
jako duplikat. Generator nadal przyjmuje drugi katalog (`out=OUT_XFAIL`) dla przyszłych generowanych znanych porażek.
