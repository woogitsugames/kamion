# Recenzja Mistral runda 2 (PR #6–#14) — 2026-11-12, s14

Recenzent: Claude (subagent lidera). Zakres: `docs/owner/MISTRAL-TASKS-2.md` M6–M15. Drafty #9, #10, #12, #13, #14 oceniane jako wersje końcowe (właściciel: sesja Mistrala zakończona). Na każdym PR jest komentarz z uwagami (plik:linia).
**M9 (znaki pionowe) nie ma PR-a**, więc zadanie nie zostało dostarczone.

Uruchomione lokalnie (worktree w `%TEMP%`, potem usunięte):
- #10: `uv run --project tools/audio --with pytest pytest tools/audio/tests -q` → 36 passed, 1 skipped.
- #12: `uv run --project tools/worldgen pytest tests/gis -q -m unit` → 30 passed, 811 deselected (6 s).
- #14: `uvx ruff check tools tests --select F` → 3 znaleziska (F541 ×2, F601). Łącznie 552.

Ciężkich testów (pełne `tests/gis`, Unity, telefon) nie uruchamiałem. Czerwony job `gis` we wszystkich PR to znany błąd z `main` (`test_road_fidelity.py::test_report_not_stale`, stary `fidelity_qa.json`).

## Werdykty

| PR | Zadanie | Werdykt | Poprawka: kto | Najważniejsza uwaga |
|---|---|---|---|---|
| #6 | M6 GC HUD | **SCAL** | — | Throttle 0,2 s poprawny, nie zmienia UI, alokacja co klatkę → 5 Hz (nadal 2–3 stringi co 0,2 s, poza zakresem). Lider kompiluje w Unity przy scaleniu (DoD). |
| #7 | M7 bugfix fizyki | **SCAL** (dokument) | — | Potwierdzone: PR #5 nie ma `Skip` (jedyne trafienie to `maxSkip` w l. 270), więc nie było czego naprawiać. |
| #8 | M14 licencje | **SCAL** | — | Wszystkie 3 wpisy sprawdzone z faktami (SVG z `make_logos.py`, commit `4ce63ae05`, `door_interface.json:5` generator, 9 skryptów QA). Brak Google i Fab. Kosmetyka: miks PL/EN w tabeli. |
| #9 | M15 scenariusze | **SCAL po poprawkach** | drobna, lider (JSON + tekst); pkt 2 opcjonalnie osobno | `circle_r50_50kmh_comb`: limit przegubu 6° jest fizycznie zły (geometrycznie R50 → ≈ 8–9°, rachunek orientacyjny), więc „oczekiwana porażka” jest częściowo złym oczekiwaniem. Usunąć ten check i zostawić `radius_error_m`. `ExpectedFailureTests` asertuje tylko `!Passed` (dowolny check). Błąd arytmetyczny w `grade_6pct_steady_comb` (44,6, a nie 46 km/h). |
| #10 | M11 testy audio | **SCAL po poprawkach** | drobna, lider | Błąd `comb_estimate` (korekta oktawy liczona, ale nieużywana) potwierdzony, tylko numer linii jest zły: `el_analyze.py:146-160`, a nie `117-127`. Naprawa błędu to osobne zadanie (audio). |
| #11 | M8 propozycje parametrów | **SCAL po poprawkach** | drobna, lider (tekst dokumentu); weryfikacja R13/AMT osobno | To tylko propozycje: JSON-y i kod gry nietknięte, runner dostaje opcjonalny `DefinitionSet`. Źródła są przeszacowane: P3 „6,5 bar R13, pewność wysoka” bez paragrafu (audyt na `main` l. 164 mówi „bez cytatu”), P2 „1,24” bez źródła (audyt l. 161), P8 Pacejka to książka o oponach, a P10 i P5 nie mają źródeł. Nic nie wdrażać bez weryfikacji. |
| #12 | M12 testy worldgen | **SCAL po poprawkach** | drobna, lider | Konflikt `tests/gis/conftest.py` z `main`: zostawić helpery LFS i `pytest_configure`. CI nie uruchomiło się przez konflikt. Lista „błędów produkcji” to stare artefakty, a nie błędy. Testy dobre (niezmienniki, nie tautologie). |
| #13 | M10 oznakowanie PL | **SCAL po poprawkach** | drobna, lider (statusy w raporcie); weryfikacja z PDF zał. 2/PTB osobno | Brak zmian stałych (dobrze). Statusy „ZGODNE” oparte na serwisach wtórnych (tioman, kalkulatorxxl, rankomat…). Zdanie o „uchyleniu 2022” jest sprzeczne. Wątpliwe: P-10 max 16 m, P-13 h = 0,70 m, progi 70 km/h P-1a/P-1b/P-8, numery paragrafów PTB2022. Testy tylko przypinają stałe. |
| #14 | M13 lint | **SCAL po poprawkach** | drobna, lider (ci.yml) | Usunięcia bezpieczne: brak re-eksportów i `import *`, wywołania z efektem ubocznym zostały. Job formalnie nieblokujący, ale zawsze ❌, więc `--exit-zero` i bez `exit 1`. Wersje ruff/PSSA nieprzypięte. Przeoczony F601: `streetscape/materials.py:108/163` ma zdublowany klucz `concrete_pole` z różnymi kolorami. Zmienia 7 plików `tools/worldgen/roads/*.py`, więc `fidelity_qa.json` znów będzie nieaktualny. |

Żaden PR nie dostał werdyktu NIE SCALAJ. Poprawki „drobne” to edycje JSON, tekstu i `ci.yml` do zrobienia przez lidera przy scaleniu. Treść każdej jest w komentarzu na PR.

## Konflikty między PR-ami

| Para | Plik | Rozwiązanie |
|---|---|---|
| #12 ↔ `main` | `tests/gis/conftest.py` | Zostawić oba bloki: `LFS_POINTER_MAGIC`/`is_lfs_pointer`/`require_lfs` z `main` i `pytest_configure` (marker `unit`) z #12. |
| #10 ↔ #14 | `.github/workflows/ci.yml` | Oba dopisują job na końcu. Zostawić `audio-tests` i `lint`. |
| #12 ↔ #14 | `ci.yml` | Brak konfliktu (#12 dodaje krok w jobie `gis`). |
| #9 ↔ #11 | `tools/physics-runner/Sim/*` | Brak konfliktu (`Scenario.cs` i `ScenarioRunner.cs`). Po obu sprawdzić `dotnet test` (CI physics). |
| #12 + #13 | `tests/gis/test_markings_pl_standards.py` | Bez konfliktu. Po scaleniu obu dodać `pytestmark = pytest.mark.unit` w pliku z #13. |
| #14 ↔ `fidelity_qa.json` | `tools/worldgen/roads/*.py` (SHA w raporcie fidelity) | Scalić #14 przed ponownym uruchomieniem `tools/worldgen/fidelity/run.py` na `main`. Potem jedno uruchomienie zazieleni `gis`. |

## Proponowana kolejność scalania

1. **#7**, potem **#8** (same dokumenty, bez konfliktów).
2. **#6**: kompilacja w Unity (EditMode/PlayMode HUD) przed scaleniem.
3. **#9**: z poprawką `circle_r50_50kmh_comb` (usunąć check przegubu 6°, zaktualizować `expectedFailReason`) i tekstem w `grade_6pct_steady_comb`.
4. **#11**: z poprawkami pewności i źródeł w dokumencie (P2, P3, P5, P8, P10). Potem CI physics po #9 + #11.
5. **#12**: rozwiązać `conftest.py` i sprawdzić, że krok „GIS unit tests” się wykonał.
6. **#13**: statusy „źródło wtórne” i UNVERIFIED w raporcie, `pytestmark = pytest.mark.unit` w teście.
7. **#10**: poprawić numer linii w reason Skip (`el_analyze.py:146-160`).
8. **#14**: rozwiązać `ci.yml` (oba joby), `--exit-zero`, bez `exit 1`, przypięte wersje ruff i PSSA.
9. Na `main`: ponownie `tools/worldgen/fidelity/run.py` (wymaga `Data/raw`, lokalnie), żeby zazielenić `gis`. Potem pełne `tests/gis` przez slot heavy.

## Osobne zadania wynikające z recenzji

- Audio: naprawić korektę oktawy w `el_analyze.py:146-160` (`comb_estimate`), potem zdjąć Skip z `test_comb_estimate_no_octave_error_on_wav_roundtrip`.
- Vehicle-physics: znaleźć paragraf R13 dla progu ostrzeżenia niskiego ciśnienia (P3) i źródło strategii biegu startowego AMT (P10), zanim cokolwiek zmieni się w JSON-ach.
- Physics-runner: `expectedFailMetrics` w `ExpectedFailureTests` (asercja konkretnych metryk).
- World: zdecydować o kolorze `concrete_pole` (`streetscape/materials.py:108` i `:163`). Zmiana wymaga regeneracji świata.
- World/docs: zweryfikować wymiary P-10/P-13/P-1/P-8 i numery paragrafów PTB2022 z PDF ISAP (zał. nr 2 do Dz.U. 2019 poz. 2311; Dz.U. 2022 poz. 1518).
- M9 (znaki pionowe vs rozporządzenie) nie zostało dostarczone, więc zadanie zostaje otwarte.
- GC HUD: pozycja 2 audytu (`BuildTelemetry`) i cache etykiety gyro, jeśli profil na telefonie pokaże GC.
