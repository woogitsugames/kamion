# ADR 0317: kontekst sąsiadów kafla z danych authored (D95)

Data: 2026-11-20. Status: przyjęte w zakresie zadania neighbour-ctx-cli.

## Problem i decyzja

`EdgeClosureRules.NeedsNeighbourContext` porównywało nazwę regionu z `knyszyn`.
Rondo znajduje się około 40 m od zachodniego szwu (obserwacja D95), dlatego
start PC potrzebuje rzeczywistych sąsiadów zamiast widocznej zapory krawędzi.

Źródłem reguły jest opcjonalny `Data/Regions/<id>/streaming.authored.json`:

```json
{
  "needs_neighbour_context": true,
  "neighbour_context_reason": "Uzasadnienie authored"
}
```

Osobny plik przeżywa regenerację `region.yaml` przez `build_region.py`.
Eksporter `tools/worldgen/streaming/tile_graph.py` zapisuje boolean
`needsNeighbourContext` w każdym kaflu `tile_graph.json`. Brak wpisu oznacza
false. True wymaga niepustego uzasadnienia oraz sąsiada ze wspólną krawędzią;
sam narożnik nie wystarcza. Typy inne niż boolean są odrzucane.

Runtime wyszukuje region w przekazanym grafie. Brak grafu, nieznany region
i starszy graf bez pola oznaczają false. Domyślne włączenie dotyczy PC i braku
argumentu stream; jawny argument i `EnabledOverride` zachowują pierwszeństwo.
`WorldStreamer` ładuje dane do tej decyzji tylko dla domyślnego startu PC.
Dostępność scen sąsiadów nadal sprawdza istniejące `TryInstall`.

Flagę otrzymuje **wyłącznie knyszyn** (1 z 54 kafli). Nie dodajemy automatycznej
heurystyki odległości ani nowego progu WORKING_VALUE. Katalog menu i jego
eksporter nie wymagają zmian, bo źródłem runtime jest graf streamingu.

## Walidacja

- `dotnet test tools/spawn-runner/Tests/Tests.csproj`: **48/48 PASS**;
  runner kompiluje rzeczywiste źródła reguł, grafu i `EdgeClosureRulesTests`.
- `uv run --no-project --with pyyaml --with pytest --with requests python -m pytest tests/gis/test_tile_graph_0235.py -q`:
  **20/20 PASS**, w tym flaga dla dowolnej nazwy, walidacja danych, ponowny
  eksport i zachowanie wpisu po nadpisaniu region.yaml.
- `uv run --no-project --with pyyaml python tools/worldgen/streaming/tile_graph.py --check`: **PASS**.
- Dodatkowa regresja `test_region_catalog_0267.py`: **2 PASS / 1 FAIL**;
  istniejący katalog ma `knyszyn.routeLengthM=1159.09`, a trasa daje 1159.28 m.
  Oba wejścia są poza zmianą tego zadania; katalogu nie regenerowano.
- Review innego agenta: po przeniesieniu wpisu z generowanego region.yaml
  brak uwag blokujących. `git diff --check`: PASS.
- Logi: `artifacts/logs/neighbour-context-*.log`; wynik NUnit/TRX:
  `artifacts/neighbour-context/neighbour-context.trx`.

Unity, buildów i playera nie uruchamiano zgodnie z zakresem zadania.
Kompilacja całego WorldStreamer w Unity i weryfikacja wizualna: UNVERIFIED.
