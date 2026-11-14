# STATUS — R1 traffic-signs-catalog (cloud2, s20)

## 2026-11-14 17:15 UTC — krok 1: źródła i struktura
- Worktree /workspace/wt/traffic-signs-catalog, gałąź research/cloud2-traffic-signs-catalog (z origin/main 81c9bae).
- Pobrano z api.sejm.gov.pl (ELI): Dz.U. 2019 poz. 2310 (55 s.), 2019 poz. 2311 cz. 1 (525 s.; zał. 1 cały), nowelizacje 2020/862, 2021/433, 2021/438, 2021/2065, 2021/2066, 2022/2372, 2022/2377, 2026/132, 2026/133.
- Ustalono: 2310 = znaki i sygnały (znaczenie + barwne wzory), 2311 = szczegółowe warunki techniczne (wymiary, barwy CIE, folie, montaż). Tabela 1.11 zmieniona przez 2021/2066 i 2022/2377.
- C-1 vs C-2: rozstrzygnięte (C-2 = strzałka w górę i w prawo; 2311 s. 158–159, 398–399; 2310 s. 43).
- NASTĘPNY KROK: `python -I research/cloud2/traffic-signs-catalog/tools/build_catalog.py` (generator catalog/sizes/manifest)

## 2026-11-14 17:55 UTC — krok 2: catalog.csv
- catalog.csv: 265 znaków (A 42, B 46, C 21, D 76, F 30, T 50) z nowelizacjami 2021/433, 2021/2065, 2026/133; kształt SOURCED 116 / ESTIMATED 149; barwy ESTIMATED (odczyt wzorów 2310 s. 41–50) poza 3 opisanymi słownie.
- NASTĘPNY KROK: `python -I research/cloud2/traffic-signs-catalog/tools/build_manifest.py` (sizes.csv + manifest.csv)
