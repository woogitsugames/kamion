# spawn-fix-0262 (ADR 0262) — live
## 15.11 diagnoza (przyczyna wspólna, potwierdzona na danych 21 regionów)
- W 20/21 regionów trasa startowa zaczyna się NA krawędzi kafla (węzeł `boundary`), a zamknięcie krawędzi (WorldEdgeBuilder, ADR 0169:
  zapory betonowe + deski U-20, 60 m w głąb kafla) stoi na trasie w s≈60 m (dk65-05: 14 m, knyszynska: 20 m, dk65-06 i knyszyn-w: 54 m).
  Start s=12 m (ADR 0229 `startS`, `WorldSceneBuilder.spawnS`) wypada więc PO ZEWNĘTRZNEJ stronie zapory: z tyłu koniec drogi, z przodu bloki.
  dk65-05: zapora w s=14 m -> ciągnik w rzędzie zapór (zrzut 3.webp). Region C nie ma zamknięcia na trasie (start w bazie), więc nikt tego nie widział.
- To NIE odwrócony kierunek (drugie zamknięcie jest przy len-60) i NIE plac budowy D65 (construction_site = piasek/hałdy w terenie + siatka poza pasem 4 m od dróg).
- Plan: (1) test EditMode na prawdziwych zamknięciach + pytest katalogu (czerwone na main); (2) startS w katalogu = za zamknięciem wjazdowym;
  importer spawn z tej samej funkcji; (3) runtime: start za zamknięciem z WorldBoundary sceny + OverlapBox (naprawia APK bez reimportu scen).
NASTĘPNY KROK: implementacja `SpawnClearance` (Gameplay) + testy; `pwsh scripts/test.ps1 -Platform EditMode` pod slotem unity.
