Gałąź gpt-life-r2; zweryfikowany stan c6d1d2b0, kod wariantu C d47d3d72, generaty B 86dab638; ADR 0122.
Na placach LOD1 ma oddzielne trzy osie naczepy i zamknięte koła; nominalny odstęp od płaszczyzny gruntu naczepy 0,12→0 m, ciągnika 0,0683→0 m.
Tris LOD1: plandeka 220→316, box 180→276, chłodnia 194→290, ciągnik 254→286; grupy materiałów i kolizje bez zmian.
Sześć plandek ma UV w metrach i jawne set_tile; sześć lakierów kabin opt-in yard_paint korzysta z istniejącego CARPAINT/UV1 i delikatnego brudu od progu.
Finalne before-exact i after-c-exact: po 456 PNG, 114 kamer × Low/High × clear/overcast; 59 kamer trasy bez braków.
Trasa: maks. tris Low +1,7636713%, High +0,3365433%; draws świata +0 i draws instancji +0. Dokładne liczby w exact-c-all-camera-budget.json.
Wszystkie 114 kamer: maks. Low +2,2356205% (dodatkowe zbliżenie chłodni), High +0,5341565%; draws +0. To szacunki CPU, nie pomiar GPU.
GLB: 26 zmienionych węzłów wyłącznie tractor_/trailer_, 0 poza nimi; wszystkie 192 produkty raw identyczne z bazą, bez fallback=True.
Native: 12 LOD kabin z UV1 Half2, maks. błąd 0,0007813; materiały kabin/plandek i niezmieniony SHA tablic potwierdzone.
Testy: końcowy GIS 585 passed, 1 xfailed (612,19 s); EditMode 280/280; pojedyncze pliki 12/12, 59/59 i 8/8. Logi i wyniki JSON w katalogu rundy.
Pierwszy pełny GIS ujawnił stary limit LOD1 260; poprawiono wyłącznie oczekiwanie testu do 320 zgodnie z maksimum 316. Dowód porażki zachowany, budżet trasy 2% bez zmian.
Pary zdjęcie/render ≤960 px: refs/sbs-yard-rear34-c.jpg i refs/sbs-yard-side-c.jpg; źródła/licencje i ograniczenia pozy w refs/YARD-REFERENCES.md.
Obejrzano 56 arkuszy C i wszystkie 17 nieidentycznych kadrów osobówek; 59/76 PNG osobówek identycznych A/C, bez widocznej regresji, bez deklaracji identyczności wszystkich pikseli.
Ocena autora PARTIAL: osie i koła dalszego LOD poprawione, brud subtelny, felgi płaskie, kabiny i szkło uproszczone; GPU/A16 i niezależna recenzja UNVERIFIED.
Konflikty możliwe: materials.py (flagi), WorldPbrMaterials.cs (opcja kabin), CARPAINT w WorldPBR.shader, life_props/life_cars, testy i generaty. LifeExactStats to opt-in Editor QA.
Lider Claude S11 zleca recenzję i integruje; nie wykonano merge do main, push ani telefonu. Generaty po złączeniu źródeł wymagają regeneracji.
Następna r3 od razu po publikacji: aktualne main do własnej gałęzi, świeży baseline, uwagi lidera do tyłu osobówek/felg/czerni i sheet_far; preflight palet zachowany w NEXT-R3.md.

