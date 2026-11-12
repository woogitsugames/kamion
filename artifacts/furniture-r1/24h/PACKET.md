# Materiały do integracji rundy 1

Gałąź: `gpt-furniture-r1`. Zweryfikowany kod i zasoby: `7adbe982`.
Późniejsze commity zapisują diagnostykę, referencje i wyniki testów.
Baza sesji: `5f2aa277`. Poprzednia runda ADR 0102 jest w `../legacy-0102/`.

Podmurówka podąża za terenem krótkimi, zamkniętymi deskami, a słupki zachowują
niezależny moduł do 2,5 m i narożniki. Siatka ma niewielkie wygięcia; redukcja
podziałów renderowanej siatki zachowuje jej wcześniejszą kolizję. Beton otrzymał
przetworzony skan CC0 i miejscowy osad przy gruncie. Trzon starej latarni jest
szerszy u dołu, a skan powtarza się w skali metrycznej zamiast rozciągać przez
całe 9 m. Obudowa lampy ma ścięte narożniki. Tył znaku otrzymał szary metal,
etykietę i miejscowe rdzawe zacieki pod mocowaniami, z poprawionym mapowaniem UV.

## Dowody obrazu i budżetu

`before/` i `after/`: po 55 kamer × 2 poziomy × 2 oświetlenia = 220 obrazów.
`compare/`: 40 arkuszy przed/po o szerokości do 960 px. Niezależna ocena całego
zestawu znajduje się w `iteration4/REVIEW.md`. Zbliżenia: `after4-detail.jpg`.
Para referencja/render: `reference-sign-after.jpg`; poza pozycją roboczą nie
potwierdzono kalibracji kadru. `daylight-reference-sheet-final.jpg` zawiera
referencje dzienne z opisami; manifesty źródeł zachowują autorów i licencje.

W 220 wariantach zmiana CPU DrawEst mesh wynosi 0 i instancji osobno 0.
Liczniki są estymacją widocznej geometrii przed SRP batching, nie pomiarem GPU.
Dokładne liczniki po zmianie zweryfikowano z zapisami wszystkich 110 wariantów
Low. Baseline zachował zaokrąglenia w dół do tysięcy, dlatego raportujemy górną
granicę wzrostu, a nie dokładny przyrost. Pełne wyniki są w `exact-after4/`,
`iteration4/budget-summary.json` oraz tabelach metryk wszystkich kamer.

102/110 wariantów Low ma udowodnioną granicę ≤2%. Kamery trasy:
driver-andersa-to-putry ≤1,68194%, fire-station-route ≤1,70853%,
fire-station-abeam ≤1,60041% w obu oświetleniach. Nierozstrzygnięte pozostają
fire-station-above ≤2,10065%, edge-east ≤2,67349%, edge-north ≤3,10753%
i edge-west ≤3,01395%, po dwa warianty. Są to kadry z góry i krawędzi świata;
nie ukryto ich ani nie uznano całego zestawu za PASS budżetu.

Chronione payloady geometrii: 6833 przed i po, 0 różnic
(`protected-geometry-comparison.json`). Kolizje ogrodzeń: 80 przed i po,
0 różnic w bajtach accessorów (`fence-collision-comparison.json`), ale ten drugi
dowód dotyczy wyłącznie optymalizacji iteracja 3 → 4, nie całej rundy.
Importowane dane mesh/instancji/kolizji: Low 117,0 → 120,0 MB,
High 259,1 → 262,1 MB; furniture 8,2 → 11,1 MB. To nie jest PSS urządzenia.
Build: 64 chunki, brak `fallback=True` w logu końcowego generatora.

## Integracja i otwarte ograniczenia

Zmiany wspólne są addytywne: flaga `furniture_plinth_detail` w `materials.py`,
jej obsługa w `WorldPbrMaterials.cs` i lokalny keyword `_FURNITURE_PLINTH`
w `WorldSurface.shader`. Marker COLOR0 ogranicza detal do naszych desek;
nieoznaczony beton zachowuje wcześniejszy wynik. Nie dodano przebiegu shadera,
pola QualityProfile ani nowego materiału na deskę. Zachowano liniowy kontrakt
_Tint, dotychczasowy _Tile i rozdzielenie weather/runoff. Przy scalaniu należy
zachować równoległe flagi innych dziedzin w tych trzech plikach. Pliki
wygenerowane i GLB wymagają regeneracji po połączeniu zmian przez lidera.

Nie potwierdzono dokładnej rodziny istniejącej betonowej latarni lokalnym
zbliżeniem; wymiary i parametry osadu pozostają WORKING_VALUE/UNVERIFIED.
Dodatkowe fotografie nie są dowodem identyfikacji konkretnego słupa.
Pozostał ostry cokół i czysty styk z gruntem, niepotwierdzony fotograficznie
ukośny wierzch sztywnego panelu oraz aliasing drutów na Low. Obrazy statyczne
nie potwierdzają braku migotania w ruchu. Nie mierzono telefonu, czasu GPU,
PSS ani wariantów APK; nie używano adb ani nowych pikseli Fab/Megascans.

## Testy

Testy własne po iteracji 4: `test_furniture_0120.py` 17/17 i
`test_furniture_r1.py` 9/9. Testy GPU/fabryki FurniturePlinthTests: 7/7,
bez pominięć. Sprawdzają kontrakt flagi, kanałów, liniowego detalu i brudu;
nie zastępują pomiaru kosztu GPU na urządzeniu.

Końcowy GIS: 509 passed, 1 xfailed, 1 failed w 599,84 s.
Porażka: `test_road_fidelity.py::test_report_not_stale`. Niezmieniony od bazy
raport fidelity_qa.json nie zgadza się z siedmioma hashami wejść spoza furniture.
Audyt `fidelity-input-audit.json` i `fidelity-baseline-audit.json` dowodzi,
że wszystkie 23 wejścia oraz raport zachowały bloby Git z bazy sesji;
normalizacja LF nie usuwa niezgodności. Nie poprawiano źródeł dróg ani
overrides i nie aktualizowano samych hashy w celu uzyskania PASS.
Wyniki physics/gate3 i końcowego EditMode należy odczytać z
`closing-test-exits.json` i ich logów po zakończeniu bieżącej sekwencji.


