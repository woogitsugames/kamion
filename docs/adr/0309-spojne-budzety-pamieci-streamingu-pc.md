# ADR 0309 — Spójne budżety pamięci streamingu PC

Status: wdrożone w gałęzi `tier-budget-cli`, do integracji przez lidera, 2026-11-19.
Wszystkie progi: **WORKING_VALUE**. Numer: HANDOVER.md wskazuje ostatni przydzielony 0308;
0309 przydzielony w zleceniu właściciela. Powiązane: D89, ADR 0235, 0273 §6 i dopisek D81, 0290.

## Źródła i przyczyna

Budżet to suma `WORLD_MEMORY` rezydentnych kafli (w tym przypiętego kafla odrodzenia),
nie RAM całego procesu ani dedykowany VRAM. `StreamingSettings.BudgetForTier` jest źródłem runtime;
`PcTierTable` i assety URP nie przechowują tego limitu. `StreamingContentChoice` pobiera go z polityki.

| Tier PC | Pierwotna wartość (ADR 0273 §6) | Stan po D89 / ADR 0290 | Źródło |
|---|---|---|---|
| Low | 640 MB | 850 MB | 434,1 + przypięty C 124,2 + ~10% → 640; DK19: 796,2 → 850 |
| Medium | 800 MB | 800 MB | Low + kafel narożny DK65 ≤76,1 MB i zapas; D89 nie zmieniła Medium |
| High | 1450 MB | 2000 MB | 1044,2 + przypięty C 267,0 + ~10% → 1450; DK19: 1935,2 → 2000 |
| Ultra | 2000 MB | 2000 MB | ADR 0273: 4 kafle High w narożniku + przypięty, pod przyszły dłuższy look-ahead; propozycja bez osobnego pomiaru Ultra |

D89 („budżety 850/2000”, `docs/11_DECYZJE_WLASCICIELA.md`) zatwierdziła wzrost Low i High po pomiarze
GTX 1070: korytarz High VRAM 1,07–1,87 GB z 8 GB, pamięć prywatna 2,1–3,3 GB
(źródła historyczne: ADR 0273 dopisek D81, ADR 0290, `artifacts/pc/DOM/20261118-*`, `artifacts/d3d-ab`).
Nie wykonano ponownego pomiaru w tym zadaniu. Te pomiary procesu nie są pomiarem samego budżetu świata.
Medium < Low jest skutkiem pozostawienia wcześniejszej wartości po D89.

`tools/pcperf/budgets/pc-budgets.json` dotąd nie zawierał budżetu pamięci świata per tier:
`classes.*.checks` określają limity całego procesu/VRAM z ADR 0266, `tileBudgetsD83` — geometrię i draw calls.
Nie należy podmieniać tych odrębnych limitów liczbami 850/2000.

## Decyzja

Drabinka PC: **Low 850 ≤ Medium 850 ≤ High 2000 ≤ Ultra 2000 MB** (`WORKING_VALUE`).
Podnosimy tylko Medium o 50 MB (6,25%). Low/Medium wybierają treść Low, High/Ultra treść High;
wspólny limit w każdej parze zachowuje ustalone wartości D89 i usuwa odwrócenie tierów bez arbitralnego zapasu.
Próg Medium 850 daje, jak Low, 53,8 MB ponad historyczną obwiednię DK19 796,2 MB;
High/Ultra mają 64,8 MB ponad 1935,2 MB. Nie deklarujemy gwarancji dla wszystkich przyszłych kafli/narożników.

Warianty: obniżenie Low do 800 przeczyłoby D89; Medium 1000/1200 zwiększałoby limit bez nowego pomiaru.
Równość jest dozwolona przez warunek Low ≤ Medium ≤ High ≤ Ultra.
Nie zmieniamy selekcji treści, promienia, liczby kafli, przypięcia ani wyjątku `allowOneOverBudget`;
limit nadal jest progiem polityki, a nie twardą gwarancją szczytu pamięci.
Telefon zachowuje 200/400/600/600 MB (ADR 0235), nieznany tier wraca do Low.

Dodajemy `streamingWorldMemory` w JSON pcperf jako jawny rejestr z pochodzeniem i jednostką;
pytest sprawdza monotoniczność oraz zgodność z tabelą C#. Parser nie ocenia tego limitu,
ponieważ jego CSV nie zawiera sumy `WORLD_MEMORY`. Nie powstaje zależność runtime od narzędzi Python.
Tabela docs/03 i uzupełnienie D89 wskazują bieżące wartości; historyczne ADR pozostają zapisem poprzednich decyzji.
Nie potrzeba zmian `ProjectSettings/`, assetów URP ani regeneracji świata.

## Weryfikacja i ograniczenia

- `uv run --no-project --with pytest python -m pytest tools/pcperf -q` — wynik w raporcie zadania.
- EditMode: aktualizacja `WorldStreamingPolicyTests` i `StreamingContentChoiceTests`,
  jawny warunek monotoniczności PC/telefon oraz regresja wczytania 825 MB dla Low/Medium
  z wyłączonym wyjątkiem ponad budżet (stare Medium 800 blokuje wczytanie).
- Unity, EditMode i buildów nie uruchamiano na polecenie właściciela; wykonanie EditMode,
  przegląd lidera i przejazd z telemetrią pozostają do integracji. Brak nowych pomiarów RAM/VRAM/FPS.
