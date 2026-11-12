# Oględziny autora — life r2, wariant C

Wybrano C do zamknięcia tej rundy, z oceną brudu i realizmu PARTIAL. To nie jest niezależna recenzja visual-critic ani odbiór bramki 3. Kod zmiany shadera: d47d3d72; geometria i materiały biblioteki B: 86dab638. Lider Claude S11 pozostaje jedynym integratorem.

Obejrzano wszystkie 56 arkuszy porównań C: zmiany placowe Low/clear i Low/overcast bezpośrednio na stronach 06–13, pozostałe strony w przeglądach c-overview (≤960 px). Dodatkowo obejrzano pełne zbliżenia białej/niebieskiej kabiny oraz powiększenia B/C, dwie pary zdjęcie/render i pięć arkuszy protected-c-review. High pochodzi z WorldC_High. Dwie odziedziczone kamery side35 ciągników mają zasłoniętą kabinę i nie są dowodem jej LOD; zastępują je widoki lod22.

Najważniejsza poprawa: w Low dalsze naczepy mają trzy oddzielne koła zamiast jednego długiego bloku. W ciągnikach widoczne są czoła kół zamiast otworów. Zmiana jest czytelna w widokach side35 i lod22 obu pogód. W bliskim LOD geometria kół pozostaje uproszczona, z płaskimi felgami. Nie zaobserwowano nowego przesunięcia obiektu ani utraty osi. Nominalny kontakt z gruntem pochodzi z audytu prototypu, nie pomiaru każdej instancji na terenie.

Plandeka ma fizyczny kafel 4,8×2,7 m i różną fazę tekstury między kolorami. Nie ma nowej błyszczącej warstwy. Ciemne plandeki, szczególnie czerwona w cieniu, nadal tracą detal; pigmentów nie podnoszono bez kalibracji. Lakier kabin korzysta z opt-in CARPAINT i szerszej warstwy kurzu C, lecz efekt na obejrzanych kabinach pozostaje delikatny. Płaskie bryły kabin, szkło i felgi nadal odstają od fotografii. Nie deklarujemy rozkładu zabrudzenia całej floty na podstawie dwóch kontrolowanych kolorów.

Kontrola osobówek A/C: 59/76 pełnych PNG jest identycznych bajtowo. Obejrzano wszystkie 17 różnych na pięciu arkuszach z maskami zmian. Duże skupiska różnic dotyczą plandek i ciągników w tle, np. g_dirt_level_1; występują też małe punkty na krawędziach/połyskach. Nie stwierdzono widocznej na arkuszach regresji sylwetki ani lakieru osobówek. Nie oznacza to identyczności każdego ich piksela. Maksimum całego kadru: 66 798 zmienionych pikseli i różnica kanału 82/255, z lokalizacjami w protected-c-pixel-audit.json. Źródła GLB osobówek są niezmienione, a materiał tablic ma dokładnie SHA z r1, z zachowanym wyłączonym MotionVectors.

Budżet CPU: 114 kamer × cztery warunki, w tym 59 kamer trasy, bez braków. Na trasie Low maks. +1,7636713% tris, High +0,3365433%; draws świata i instancji +0. Wszystkie kamery: maks. Low +2,2356205%, High +0,5341565%. World liczy ten sam frustum SceneStats po przywróceniu targetu (aspect 4:3), instancje są odczytem render-time. To porównanie szacunków CPU, nie pomiar GPU/telefonu.

Native: sześć materiałów kabin, siedem lakierów osobówek i sześć plandek zgodne z zamierzonymi flagami; 12 LOD kabin zachowuje Half2 z maks. błędem komponentu 0,0007813. EditMode 280/280. Pełny GIS pozostaje końcowym sprawdzeniem tej zamrożonej wersji. Niezależną ocenę i ewentualny pomiar urządzenia zleca lider; autor nie scala ani nie pushuje.

Fotografie są referencją ogólnej konstrukcji, z innych miejsc i świateł; Krone ma otwartą plandekę. Par nie używano do kalibracji albedo ani deklarowania zgodności GPS. Szczegóły i licencje w refs/YARD-REFERENCES.md. Preflight palet i zdjęć Mapillary dotyczy dopiero r3; palet w r2 nie zmieniono.
