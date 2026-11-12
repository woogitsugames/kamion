# Próby materiałów przed wyborem zmiany rundy 3

Stan źródeł: po merge lokalnego main i świeżej kanonicznej regeneracji. To próby diagnostyczne, a nie pełne porównanie baseline/candidate ani dowód budżetu GPU.

## Jasne ślady przed rondem

Obejrzano trzy PNG kamery `g3a-rondo-bie-approach`, Low, clear, 2340 × 1080. Przy wyłączeniu spękań przez `_CrackStrength=0` jasne pętle znikają. Przy wyłączeniu fotodetalu przez `_DetailFade=0.001` pozostają. Obie próby znalazły 44 aktywne sloty dokładnie materiału `M_road_asphalt.mat`. To potwierdza źródło defektu w warstwie spękań, ale nie rozdziela jeszcze wpływu jej kanałów i połysku.

Kod warstwy przyciemnia kanałem R i A; kanał G miesza albedo w stronę liniowego 0.03 i smoothness w stronę 0.55. Sama lektura nie dowodzi, który składnik odpowiada za jasność. Docelowa korekta powinna zachować drobne spękania, ziarno i ślady kół z rundy 1. Wyłączenie całej warstwy jest wyłącznie kontrolą diagnostyczną.

Arkusz `diagnostic-sheets/chalk-before-cracks-off-960.png`: u góry stan wyjściowy, na dole spękania wyłączone. Dwa natywne wycinki 960 × 350 z pozycji +700+730; bez skalowania.

## Podjazd domu

Własny alias `asphalt_r10_house2_material` odwzorowuje źródłową kamerę `r10_house_2` z pliku `buildings_r10_cameras.json`, włącznie z `seat=road`. Pierwsza próba z `seat=file` pokazała kadr ponad dachami i została odrzucona. Nie należy używać jej do oceny materiału.

Poprawiony kadr porównano z `house-grime-off`, gdzie `_Grime=0` zastosowano do `yard_paving` i `yard_behaton` (łącznie 37 slotów). Duże plamy podjazdu za bramą słabną, a układ kostki pozostaje. Plamy publicznej nawierzchni przed posesją nadal widać. Nie przypisujemy całej nawierzchni tym samym materiałom ani tej samej przyczynie.

Arkusz `diagnostic-sheets/house-before-grime-off-960.png`: u góry poprawiony stan wyjściowy, na dole brud wyłączony. Dwa natywne wycinki 960 × 350 z pozycji +450+730; bez skalowania.

Dodatkowa próba `house-public-grime-off` wyłączyła `_Grime` wyłącznie na `sidewalk_paving` (44 dopasowane sloty). Po obejrzeniu PNG dominujące plamy przed posesją nadal pozostają. Samo podobieństwo tekstury nie identyfikuje materiału: manifest zawiera również osobny `road_paving` z tym samym zestawem `paving_20x10_grey` i bez danych `ground_grime`. Następna próba osobno sprawdza ten identyfikator; na tym etapie to hipoteza, nie ustalona przyczyna.

Wynik następnej próby `house-road-paving-grime-off`: dopasowano 26 slotów `M_road_paving.mat`. Po obejrzeniu jej PNG duże ciemne pola na publicznej nawierzchni znikają, a podjazd za bramą zachowuje swój wcześniejszy wygląd. Potwierdza to osobne przypisanie tej części defektu do `road_paving`. Warstwa QA i audyt końcowy obejmują teraz także ten identyfikator; pełnego baseline jeszcze nie renderowano, więc nie ma zmiany schematu w połowie porównania końcowego.

## Zakres dowodu

Własna ocena wszystkich pięciu właściwych PNG i niezależna ocena krytyka są zgodne co do powyższej atrybucji. Nie przyznano końcowego PASS. Próby używają nieserializowanych MaterialPropertyBlock, więc ich liczników rysowania nie używamy do wykazania budżetu. Materiały na dysku nie zostały zmienione.

Nie wykazano jeszcze zgodności placu przemysłowego ze zdjęciem PCRT. Punktowa sonda GLB czeka w kolejce heavy. Fotografia ma nieustaloną dokładną pozę; nie jest kalibracją albedo ani szorstkości. Po sondażu trzeba ustawić i obejrzeć kamery placu, zapisać pełny plan kamer oraz zebrać baseline w Low/High i clear/overcast przed zmianą produktu.
