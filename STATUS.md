# STATUS trailer-rims-s23 (P1 recenzji s23: czerwone felgi naczepy, atlas Metal) - GOTOWE do przeglądu lidera
Gałąź `trailer-rims-s23` z origin/main 0fd0e048a.
- Przyczyna: UV lathe felgi/opony (cylindrical_atlas) bez zaznaczenia UV -> `pack_islands` nic nie pakował (błąd ADR 0061, naprawiony tylko w ciągniku); felga leżała w (0,0) pod wyspami podwozia (30 024 wspólnych tekseli @1024). Zapas miał własne wyspy.
- Fix (trailer_export.py): `uv.select_all` + margines 4 px atlasu High, strażnik (raise przy overlap kół/statyki), priorytet tablicy 2.0, `--uv-only` raport. Gęstość High px/m: Paint 386->400, Curtain 361->339, Trim 132->187, Metal 308->227, Lights 659->523.
- check_export.py: reguły kół (overlap 0 we wszystkich LOD, czerwone R-G>0,2 = 0 w Metal_C każdego tieru) PASS; test EditMode TrailerWheelAtlasTests (0 czerwonych: High 0/18 940, Medium 0/11 882, Low 0/5 533; na starej sztuce FAIL 490) + TrailerAxleSync 9/9.
- P2: `gora` doświetlona (światło pod przekrojem); tablica: w Unity była poprawna, wyblakła tylko w podglądzie Blendera (płaska emisja) -> emisja = albedo x lampa; promień opony: opisany, bez zmian.
- Unity przed/po: artifacts/trailer-rims-s23/{before,after}/unity (kamera `trailer-wheels`).
- NASTĘPNY KROK (lider): visual-critic na artifacts/trailer-rims-s23/, scalenie, w main `TrailerAssetBuilder.BuildBatch` + `WorldTruckInstaller.InstallBatch`.
