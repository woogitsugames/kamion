# STATUS — fences-0239 (F6, B-082 płoty panelowe, ADR 0239)

- [15.11] Krok 1: shader `Kamion/World FenceMesh` (URP Lit + pokrycie z dystansem: ostre odcięcie blisko, ~15 % „mgiełka” daleko;
  A2C pod MSAA, szum ekranowy bez), polityka `Game.Rendering.FenceMeshCoverage`, importer (zwykłe mipy box tylko dla
  `fence_mesh.png`, podmiana shadera, bez cienia siatki), testy EditMode `FenceMeshCoverageTests` (NIEskompilowane w chmurze),
  pytest `tests/gis/test_dojbld_0185.py` 7/7 (xfail płotu zdjęty).
- NASTĘPNY KROK: ADR 0239 + PERFORMANCE_BUDGETS + PR; potem lider:
  `pwsh scripts/test.ps1 -Platform EditMode` → `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -SkipCopy`
- [15.11] Krok 2: ADR `docs/adr/0239-plot-panelowy-pokrycie-z-dystansem.md` (komendy weryfikacji, koszt ESTIMATED, otwarte O-1..O-5),
  `docs/PERFORMANCE_BUDGETS.md` (sekcja ESTIMATED). PR otwarty do main.
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode` → reimport C i Dojlid (`-SkipCopy`) → visual-qa kamer z ADR → APK + A16.
