# Niezależna recenzja wizualna ADR 0155 — produkcyjny wariant B

## Werdykt

**PASS w zakresie poprawki regularnych jasnych plam cienia w statycznym edytorze.** Produkcyjny wariant B usuwa badany szereg na wyspie Putry, zachowując duży cień pomostu i jasny skraj żwiru. W dostarczonych widokach kontrolnych nie znalazłem nowej widocznej regresji na pozostałych mostach, górnych pomostach, podporach ani spodzie konstrukcji. Nie znalazłem konkretnej pary wymagającej kolejnej poprawki przed przyjęciem tego ograniczonego zakresu.

To nie jest akceptacja telefonu, ruchu, ASTC, wydajności GPU ani fotograficznego Gate 3. Fidelity B i pełny GIS nie były dostępne jako zakończone wyniki tej recenzji.

## Obejrzany materiał

Obejrzałem wszystkie 44 arkusze `overviews/`, obejmujące 122 kamery w czterech warunkach, czyli 488 par przed/po: Low-clear, Low-overcast, High-clear i High-overcast. Dodatkowo obejrzałem wszystkie 26 `target-crops/` oraz osiem `photo-pairs/`.

Wśród szczegółowych kadrów były oba SBS, obie wyspy, widoki biezenstwa-above i putry-above we wszystkich czterech warunkach oraz putry-island-near w Low-clear i High-clear. Sprawdziłem także pełne natywne PNG przed/po dla `sbs-g3-a-149248627179406` w Low-clear i High-clear oraz szczegółowe pary Low-clear `sbs-g3-a-500263111404933` i `sbs-g3-a-320326319617139`, wybrane spośród większych różnic obrazu.

Arkusze dają szeroki przegląd regresji, natomiast ocenę samych plam opieram na kadrach szczegółowych i natywnych obrazach, a nie na małym MAE ani miniaturach.

## Wynik obrazu

- **Putry: `putry-island-1`, `putry-island-2`, oba SBS i near.** W baseline na ciemnym żwirze występuje regularny szereg krótkich jasnych czworokątów, z mniejszymi plamami obok. W B ten wzór znika w obu profilach przy pogodzie clear. W overcast słabiej kontrastujący wzór również nie pozostaje jako widoczny szereg. Poprawka nie zamienia całej wyspy w jednolicie ciemną plamę: główny obszar cienia i jasny brzeg przy krawężniku pozostają czytelne.
- **Pozostałe widoczne zastosowania materiałów.** W parze `sbs-g3-a-149248627179406` usunięcie szeregu potwierdza się także na pełnych PNG, bez widocznego nowego acne na podporach i spodzie pomostu. W `sbs-g3-a-500263111404933` i `sbs-g3-a-320326319617139` znikają również nienaturalne jasne przerywane fragmenty przy jezdni/krawężniku. Nie widzę nowego uszkodzenia powierzchni w ich miejscu.
- **Górne pomosty i inne mosty.** `biezenstwa-above`, `putry-above` oraz pozostałe kadry kontrolne z kompletu nie pokazują nowego oczywistego acne, nowych regularnych dziur cienia ani zmiany dużej granicy cienia. Ocena dotyczy dostarczonych kierunków kamery i oświetlenia, nie wszystkich możliwych kątów padania światła.

## Diagnoza i zakres produkcyjnego rozwiązania

Wcześniejsze ablacje wskazały normal bias jako przyczynę badanego wzoru: wyzerowanie normal bias usuwało szereg, a wyzerowanie samego depth bias go pozostawiało. Produkcyjny B nie jest globalnym wyłączeniem biasu ani diagnostycznym `rq` override. Używa źródłowej polityki regionu dla trzech istniejących materiałów: bridge_concrete, bridge_kerb i road_asphalt, przy zachowanym depth bias.

Zakres jest materiałowy w regionie, a nie ograniczony do jednej wyspy. Dlatego widoki pozostałych mostów i górnych pomostów były częścią tej recenzji. Odrzucona próba A z samym hero M_viaduct_concrete nie usuwała plam i pozostaje **FAIL jako lokalizacja poprawki**; nie jest podstawą obecnego PASS. B obejrzano po generatorze i imporcie, z usuniętą odrzuconą flagą hero.

## Zjawiska istniejące w baseline i granice porównania fotograficznego

Wzory o wysokiej częstotliwości na asfalcie w okolicy Bieżeństwa są widoczne już przed zmianą; nie klasyfikuję ich jako regresji B. Uproszczona faktura żwiru i różnice materiałów/proporcji względem fotografii również nie powstały wskutek tej korekty cienia.

Osiem zestawień z fotografiami wspiera ocenę ogólnej czytelności dużego cienia i jasnego brzegu. Fotografie mają jednak inne, niekalibrowane światło i niepewność pozy. Nie dowodzą poprawności fotometrycznej ani pełnej zgodności sceny z rzeczywistością. Usunięcie regularnego szeregu poprawia ten konkretny artefakt; nie zamyka Gate 3.

## Dowody techniczne i ograniczenia

Przeczytane zestawienia wskazują identyczne pipeline przed/po oraz zerowe różnice scene/instance/shadow draws i dokładnych trójkątów dla wszystkich 122 kamer w każdym z czterech warunków. Audyt materiałów podaje 455 z 458 identycznych SHA i dokładnie trzy oczekiwane zmiany keyword/scale, bez nowych materiałów. Surowe 193 pliki pozostają identyczne. Te dane wspierają kontrolę zakresu i brak wzrostu zgłoszonych liczników; nie zastępują oceny obrazu ani pomiaru czasu GPU.

Wynik pełnego EditMode w dostarczonym XML to 493/493, bez failed i skipped. Nie uruchamiałem Unity, adb, generatora ani testów. Nie certyfikuję nieukończonych Fidelity B i pełnego GIS.

Statyczne obrazy edytora nie rozstrzygają stabilności cienia podczas jazdy, migotania, zachowania wszystkich wariantów shaderów w buildzie, kompresji ASTC, jakości na A16/S24+, FPS ani temperatur. **Końcowy PASS dotyczy usunięcia wskazanego artefaktu i braku zaobserwowanej regresji w dostarczonym komplecie statycznych obrazów produkcyjnego B.**
