# ADR 0105 — DK8 / Rondo Putry: konstrukcja pod pomostem

Status: implementacja; weryfikacja wizualna i EditMode w toku. 2026-11-11.

## Zakres i źródła

Strumień L pakietu S10-B. Dotyczy wiaduktu DK8 przy rondzie Putry, nie wcześniejszego
hero assetu Bieżeństwa (ADR 0067, `artifacts/viaduct-r9`). Osie, szerokości i niweleta
pochodzą z wygenerowanych łańcuchów OSM i terenu GUGiK NMT. Obejrzano:

- zdjęcie `Data/photos/nowe/7204_May_2021_in_Białystok.jpg` (Rakoon, CC0):
  żółte podpory, głowice, spód konstrukcji; istniejący wpis w `docs/REFERENCES.md`;
- kadry Mapillary p42/p45/p47 z zestawu lidera (CC BY-SA, tylko referencja),
  w szczególności p45: płaszczyzna sufitu i podpora;
- `artifacts/junctions-r2/plan_after/viaduct_putry.jpg`: ortofoto GUGiK / plan
  generatora; przebieg obydwu pomostów, nie źródło wymiarów pod spodem;
- lokalne LoD2 `Data/raw/gugik/lod2-2017-2061/2061_lod2_gml.zip`: audyt 33 GML,
  brak przestrzeni nazw CityGML Bridge; nie wyprowadzamy z niego konstrukcji spodu.

Brak rysunków wykonawczych i pomiaru geodezyjnego. Przekrój, rozstaw podpór,
głowice, łożyska, rury, skrzydła, schody, zacieki i położenie plam farby są
**WORKING_VALUE**. Nie twierdzimy, że dokumentują rzeczywisty układ konstrukcyjny.

## Decyzja

1. Osobny `Data/Regions/bialystok-industrial-c/viaduct_underdeck.json`, czytany przez
   `streetscape/hero_bridge.py`. Nie zmieniamy `overrides.yaml` ani `roads/*`.
   Lista OSM pochodzi z istniejącego `andersa-viaduct-putry-style`.
2. Planowanie osobno dla obu łańcuchów; zapis odtwarzalnych specyfikacji w
   `generated/landmarks/viaduct_putry_underdeck.spec.json`. Podpory omijają maskę
   jezdni dolnego poziomu; grunt i otoczenie schodów próbkowane z terenu po conform.
3. Zastępujemy wyłącznie generyczny spód i podpory: skrzynkowy przekrój ze skośnymi
   wspornikami i kroplownikami, fazowane słupy/głowice, łożyska, kolektor/rury
   spustowe, przyczółki ze skrzydłami, osadzone w gruncie stopnie. Główny spód
   pozostaje w dotychczasowej obwiedni 1,20 m pod górną krawędzią pomostu.
   Głowice/łożyska występują przy podporach poza jezdnią dolnego poziomu.
4. Nie przebudowujemy wstęg jezdni. Oryginalne części pomostu, ekrany, balustrady,
   bariery, krawężniki i oznakowanie pozostają tymi samymi obiektami siatek.
   SHA256 ich V/UV/T przed i po jest zapisywane w `hero_bridges.underdeck` QA.
5. Detale trafiają do istniejących chunków warstwy `bridge`, bez nowych prototypów
   konstrukcji i bez nowych materiałów. Używamy `bridge_concrete`, `bridge_soffit`
   i istniejącego `pier_yellow`. Bez zmian `_Tint`, shaderów, światła i ProjectSettings.
   Ciemne nieregularne nakładki z istniejącego materiału podsufitki oznaczają
   lokalne zacieki/plamy. Graffiti wyłącznie jako abstrakcyjne plamy farby,
   bez napisów, znaków i marek; lokalizacje WORKING_VALUE.
6. Istniejąca roślinność Megascans pozostaje. Próba dodatkowych 8 kęp przy
   przyczółkach używała wyłącznie `fab_grass_clumps`, ale kosztowała +1 draw Low
   w dwóch kamerach. Dlatego `add_grass=false`: nowych instancji nie dodajemy.
   Żadna pochodna Fab nie trafia do git. Bez zmian generatora roślinności (0088).

## Walidacja

- Testy `tests/gis/test_viaduct_underdeck.py`: niezmienność pomostu, prześwit,
  normalne, kontakt z gruntem, brak proceduralnego zamiennika roślin Fab.
- Generacja r3: dwa łańcuchy, 7 + 5 linii podpór, identyczne SHA pomostów.
  Generator Low: maks. +0,628% trójkątów; delta liczby materiałów 0.
  64/64 bazowych chunków Low zweryfikowano po SHA; delta grup siatka/materiał 0.
  Szacunek CPU, **nie** pomiar draw calls ani GPU. Wyniki końcowe w REPORT.
- Testy lokalne 7/7 PASS, w tym obniżanie stopni co 0,18 m, podparcie końca biegu
  i wyłączenie dodatkowej trawy dla budżetu Low.
  Obejrzany podgląd geometrii Blendera (porównanie trzech kamer): głowice i łożyska
  są rozdzielone, bieg schodów dochodzi do gruntu. Płaskie materiały podglądu i
  gruby LOD terenu nie pozwalają ocenić końcowego materiału ani kontaktu w Unity.
  Końcowy GIS r4: **377 PASS / 1 XFAIL**, 663,87 s, w tym deterministyczny eksport;
  `artifacts/viaduct-r10/final-gis-r4.log`.
- Unity uruchomiono dopiero po zwolnieniu PHONE_RUN (~11:54). Pierwszy import
  przeszedł, EditMode 226/226 PASS. Para before/after ujawniła +1 draw od dodatkowej
  trawy; finalny import i rendery bez nowych kęp są w toku. Bez uruchamiania adb.

Dowody i aktualny stan: `artifacts/viaduct-r10/STATUS.md`, `REPORT.md`,
`generator-budget.json`, `lod2-audit.json`, logi i PNG przed/po po zwolnieniu telefonu.
Brak telefonu w tym strumieniu; pomiar urządzeń i niezależny visual-critic po stronie lidera.
