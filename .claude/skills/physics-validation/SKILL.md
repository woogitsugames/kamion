---
name: physics-validation
description: Uruchom pakiet walidacyjny fizyki pojazdu (scenariusze z docs/04 §6), zbierz telemetrię CSV, wygeneruj wykresy, porównaj z wartościami referencyjnymi i tolerancjami. Używaj po każdej zmianie fizyki i na bramkach Etapów 1–2.
---
# Walidacja fizyki

1. Scenariusze w `tests/physics/scenarios/*.json` (masa, ładunek, nawierzchnia, nachylenie, wejścia sterujące w czasie, warunek końca, metryki, wartość oczekiwana + źródło + tolerancja).
2. Uruchomienie:
   - szybko, bez edytora: runner .NET na czystym C# modelu (`tools/physics-runner`),
   - pełno: Unity PlayMode `scripts/test.ps1 -Category Physics` (przez kolejkę lidera),
   - na telefonie (bramki): build z flagą `-e physics_suite 1`, wyniki `adb pull`.
3. Telemetria → `artifacts/physics/<ts>/<scenariusz>.csv`; `python tools/telemetry/plot.py` → PNG (prędkość, RPM, bieg, siły kół, slip, ciśnienia, kąt przegubu).
4. **Obejrzyj wykresy** — szukaj oscylacji, skoków, dryfu energii, nienaturalnych przebiegów, nawet gdy liczby mieszczą się w tolerancji.
5. Porównaj z `tests/golden/` (regresja) i z wartościami referencyjnymi.
6. Raport `docs/PHYSICS_VALIDATION.md`: tabela scenariusz | oczekiwane (źródło) | wynik | tolerancja | status, wykresy, zmiany od poprzedniego przebiegu.
7. Feel test właściciela: lista manewrów do przejechania na telefonie + formularz uwag (co czuje: masa, hamowanie, kierownica, naczepa).
