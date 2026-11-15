# STATUS — fences-0239 (F6, B-082 płoty panelowe, ADR 0239)

- [15.11] Krok 1: shader `Kamion/World FenceMesh` (URP Lit + pokrycie z dystansem: ostre odcięcie blisko, ~15 % „mgiełka” daleko;
  A2C pod MSAA, szum ekranowy bez), polityka `Game.Rendering.FenceMeshCoverage`, importer (zwykłe mipy box tylko dla
  `fence_mesh.png`, podmiana shadera, bez cienia siatki), testy EditMode `FenceMeshCoverageTests` (NIEskompilowane w chmurze),
  pytest `tests/gis/test_dojbld_0185.py` 7/7 (xfail płotu zdjęty).
- NASTĘPNY KROK: ADR 0239 + PERFORMANCE_BUDGETS + PR; potem lider:
  `pwsh scripts/test.ps1 -Platform EditMode` → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -SkipCopy`
