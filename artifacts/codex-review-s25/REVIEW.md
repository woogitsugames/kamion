# Recenzja kodu scaleń s25 i gałęzi oczekujących

Migawka `main` to `590851327e4e1cf9cede799614ee398c68e395a0`. Zakres `ec226c4ef..590851327` obejmuje 9 scaleń i 93 zmienione ścieżki. Porównałem scalenia z pierwszym rodzicem oraz sprawdziłem poprawki lidera `b704a86bf`, `b0a5fcf74`, `74d159d81`. Gałęzie oczekujące porównałem z `main` od wspólnego przodka. Linie odnoszą się do wskazanej migawki lub SHA gałęzi.

**4 ważne i 5 drobnych.** Przed falą 15 pierwszeństwo mają geometria przęseł OSM/BDOT, zgodność audytu z eksportem i zachowanie prepassu głębi przy A2C. Wznowienie fali 14 wymaga osobnej kontroli kompletności wyników danego kafla.

## Ważne

### 1. OSM dubluje istniejące przęsło BDOT, gdy wspólny odcinek kończy się wewnątrz segmentu OSM

**Plik** `tools/worldgen/streetscape/furniture.py:3528`, `:3536`, `:3541`, `:3568` · `agy-poles-wires-s25` (`7a255eb45`).

**Dowód i scenariusz.** Wywołałem produkcyjne `power_lines` z BDOT od 0 do 60 m, pojedynczym segmentem OSM od 0 do 120 m i słupami na 0, 60 i 120 m. Warunek `has_unwired or not covered` przyjmuje cały segment OSM. OSM emituje po 3 przewody na 0–60 i 60–120 m, a BDOT już emituje 3 na 0–60 m. Wynik to **3 → 9 części przewodów**, z czego **3 są duplikatami**. Oczekiwany wynik po dodaniu brakującego przęsła to 6. Test kontynuacji na gałęzi wpisuje punkt styku jako osobny wierzchołek OSM, więc omija ten przypadek. [Reprodukcja](probe.txt)

**Poprawka.** Dzielić przebieg według nakładania się odcinków lub porównywać przęsła po snapie, z uwzględnieniem klasy napięcia. Zachować odcinek 60–120 m i sprawdzić także wariant z przesunięciem osi BDOT względem OSM.

### 2. Audyt zalicza podłączenie wież, których generator nie używa

**Pliki** `tools/worldgen/qa/hv_wires_audit.py:115`, `:124`, `:132` oraz `tools/worldgen/streetscape/furniture.py:1214`, `:1223`, `:3529` · `agy-poles-wires-s25`.

**Dowód i scenariusz.** Na syntetycznej linii OSM 110 kV o długości 60 m są dwa punkty BDOT „słup energetyczny” i brak linii BDOT. Audyt klasyfikuje oba punkty jako `pylon` na podstawie OSM i raportuje **2 wieże, 0 niepodłączonych**. Produkcyjne `misc_points` klasyfikuje oba jako `power_pole`, bo rozpoznaje WN wyłącznie z BDOT. Plan WN szuka wyłącznie `pylon`, więc eksport tworzy **2 słupy i 0 części przewodów**. [Reprodukcja ścieżki produkcyjnej](probe-branches.txt)

**Poprawka.** Współdzielić klasyfikację i rozmieszczanie podpór między eksportem a audytem. Dodać przypadek OSM WN z podporami dostępnymi tylko w BDOT. Audyt geometrii powinien stosować tę samą maskę jezdni albo jawnie podawać, że mierzy plan bez niej.

### 3. Wznowienie fidelity może oznaczyć stary świat jako ukończony

**Pliki** `artifacts/regen-wave-14-s24/fidelity-resume.ps1:7`, `:8`, `:12`, `:14` oraz `artifacts/regen-wave-14-s24/common.ps1:103`, `:119`, `:131`, `:163` · `74d159d81`.

**Dowód i scenariusz.** Uruchomiłem rzeczywisty blok warunkowy z AST skryptu w lokalnym katalogu próby. Jedyny podstawiony udany etap to fidelity. Blok utworzył znacznik `.world` bez potwierdzenia wcześniejszego `build_world`, `far_field` i `export-route`. Przy istniejących GLB i trasie z poprzedniej fali łańcuch przejdzie prosto do importu. Skrypt wznowienia omija też blokadę `tiles/$Tile`, więc zwykły łańcuch i wznowienie mogą równocześnie użyć tego samego właściciela slotu. [Reprodukcja PowerShell](probe-wave.txt)

**Poprawka.** Wznowienie oprzeć na zapisanym sukcesie poszczególnych etapów dla bieżącego przebiegu, pod blokadą kafla. Zweryfikować parę kafel–łańcuch i stan przygotowania przed oznaczeniem gotowości. W obecnej fali przed ręcznym wznowieniem sprawdzić odpowiednie wpisy `END … exit=0` w logu kafla i zakończenie poprzedniego procesu.

### 4. Jednopróbkowy prepass URP przyjmuje częściowe pokrycie A2C jako cały piksel głębi

**Plik** `game/Assets/_Project/Rendering/Shaders/Vegetation.shader:183`, `:249`, `:255`, `:638`, `:679` · `codex-csharp-review-fixes-s25` (`46c5fd32a`). Lokalny URP `Runtime/UniversalRendererRenderGraph.cs:1929`, `Runtime/UniversalRenderer.cs:1180`, `ShaderLibrary/ShaderVariablesFunctions.hlsl:194`.

**Dowód i scenariusz — UNVERIFIED na GPU.** `ForwardLit`, `VegetationDepth` i `DepthOnly` korzystają z tego samego progu kamery. Przy wyłączonym A2C wcześniejszy przykład z recenzji daje próg 0,2 w obu ścieżkach zamiast 0,2/0,5. Z włączonym A2C gałąź stosuje `clip(coverage - 0.0001)` również w jednopróbkowym `DepthOnly`, który lokalny URP tworzy na tej ścieżce prepassu. Dla progu 0,50, alfy 0,48 i `fwidth(alpha)=0.08` shader zwraca pokrycie 0,25 i przepuszcza fragment w programowym `clip`. Poprzedni twardy próg `DepthOnly` go odrzucał. Jeżeli sprzętowa maska próbek jest niedostępna, wspólny helper kwalifikuje taki piksel do zapisu całej głębi. `ShadowCaster` świadomie zostaje przy twardym progu mapy cieni.

**Poprawka.** Zachować wspólne liczenie progu, a rozgałęzienie A2C uzależnić od liczby próbek rzeczywistego celu lub jawnie przypisać twardy próg prepassowi 1×. Nie opierać informacji o prepassie wyłącznie na MSAA kamery. Po fali 14 porównać głębię i kolor dla wymuszonego prepassu 1× oraz koloru z MSAA, przy włączonym i wyłączonym A2C.

## Drobne

### 5. Odświeżenie OSM łączy odległe punkty przez brakujący węzeł

**Plik** `tools/worldgen/streetscape/sources.py:167`, `:169`, `:285`, `:292` · `agy-poles-wires-s25`.

**Dowód i scenariusz.** Podstawiłem handlerowi trzy referencje węzłów: poprawną, brakującą i poprawną. Odświeżenie zwróciło **1 prostą łączącą pierwszą i trzecią referencję**, o długości około 671,5 m po projekcji. Pełny ekstraktor odrzuca taki way po `InvalidLocationError`. To różnica między pierwszą ekstrakcją a migracją schematu i może dopisać przęsła przez nieznany fragment linii. Występowanie takiego wejścia w przypiętym PBF jest **UNVERIFIED**. [Reprodukcja](probe.txt)

**Poprawka.** Ujednolicić walidację współrzędnych i klipowanie. Odrzucać niekompletny way lub rozciąć go na osobne ciągi poprawnych węzłów.

### 6. Krótkie cięcie przy narożniku bbox nadal wypada z sieci

**Plik** `tools/worldgen/roads/network.py:313`, `:321`, `:352`, `:354` · `codex-sadowa-seam-s25` (`28a5288c0`).

**Dowód i scenariusz.** Dla bbox od `(100, 0)`, syntetycznego końca `(100, 0.01)` i wewnętrznego `(100.04, 0.01)`, `load` widzi `boundary=True` i geometrię długości 0,04 m. `_seam_dir` rozpoznaje obie osie w tolerancji i zwraca `None`. Sieć ma **0 łańcuchów**. Ten koniec leży dokładnie na jednej krawędzi, 1 cm od drugiej. Na rzeczywistym grafie Sadowej poprawka działa. Kafel dk65-05 przechodzi z 0 do 1 końca `w176274699`, odzyskany łańcuch ma **0,04884 m**, trym **0/0** i współrzędne zgodne z dk65-04. [Reprodukcja](probe.txt)

**Poprawka.** Rozdzielić rozpoznanie cięcia na bbox od wyboru kierunku ścinania przekroju. Preferować krawędź zgodną z dokładnością danych grafu. Dodać wariant narożny i utrzymać test zwykłego odcinka wewnętrznego poniżej 0,05 m.

### 7. Audyt szwów może zgłosić dwa brakujące końce mimo dostępnego dopasowania

**Plik** `tools/worldgen/qa/seams.py:416`, `:423`, `:433` · `36767c08e`.

**Dowód i scenariusz.** To pozostałość zachłannego parowania, które już wcześniej występowało. Dla jednego `osm_way` i współrzędnych na szwie A = 1, 4 m, B = −4, 2 m, limit 5 m dopuszcza pary (1, −4) oraz (4, 2). `match` bierze (1, 2) i zwraca dwa samotne końce. Korekta priorytetu OSM usuwa błąd Sadowa/Szkolna, ale wielokrotne przecięcie szwu jednym way nadal może dać fałszywy brak przejścia. [Reprodukcja](probe.txt)

**Poprawka.** W pierwszym przebiegu maksymalizować liczbę par z tym samym way, a przy remisie minimalizować sumę odległości. Dopiero potem dopasować pozostałe końce.

### 8. Wyjątek przy zwalnianiu dzierżawy przerywa sprzątanie dalszych kafli

**Pliki** `game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:684`, `:1037`, `:1279`, `:1288` oraz `game/Assets/_Project/World/Runtime/Streaming/TileSceneSource.cs:27`, `:58` · `codex-csharp-review-fixes-s25`.

**Dowód i scenariusz — UNVERIFIED w Unity.** `Clear` i `OnDestroy` używają jednego helpera, który czyści listę, więc normalna sekwencja `Clear → OnDestroy` nie zwalnia tego samego klonu ponownie. Kafel startowy jest w `m_Tiles` i trafia do pętli. Jeżeli jednak dostawca zgłosi wyjątek w `source.Release` jednego z kafli, pętla zakończy się przed zwolnieniem materiałów i dzierżaw następnych kafli. Dziś dostawca gry bazowej ma pusty `Release`. Scenariusz dotyczy wstrzykiwanego dostawcy i przyszłych paczek.

**Poprawka.** Zapewnić niezależne sprzątanie wszystkich klonów i próbę zwolnienia każdej dzierżawy. Dodać test z trzema kaflami, dostawcą rzucającym wyjątek dla środkowego oraz wcześniejszym `Clear` dla jednego z kafli.

### 9. Prawy i środkowy przycisk myszy uruchamiają klakson

**Pliki** `game/Assets/_Project/UI/Driving/TouchWidgets.cs:185`, `:188` i `game/Assets/_Project/UI/Driving/DrivingHud.Desktop.cs:136` · `4b124879e`.

**Dowód i scenariusz — UNVERIFIED w Unity.** `HornButtonWidget` zapisuje identyfikator każdego `PointerEventData` i ustawia `HornHudHeld`, bez sprawdzenia `e.button`. Kliknięcie prawym lub środkowym przyciskiem uruchamia tę samą ścieżkę co lewy przycisk. Istniejące testy naciskania obejmują zwykłe przytrzymanie.

**Poprawka.** W obsłudze wciśnięcia dopuścić lewy przycisk i odpowiadające mu zdarzenie dotykowe. Sprawdzić w testach zdarzenia lewego, prawego i środkowego przycisku.

## Weryfikacja i przekazanie

- Scalenia objęte zakresem: `0ed19d1a0` (raport s24), `4b124879e` (audio/HUD), `e8b5d5e8f` (testy ADR 0349/0351), `113984a9c` (WN, maska kukurydzy, szpalery, impostory), `36767c08e` (szwy), `48afddd3b` (audyt dalekiego planu), `38463f676` i `2df09cefd` (pomnik r3/r4), `8c8831b3a` (fala 15). Robocze zmiany generatorów i testów gałęzi wczytałem przez `git show` w pamięci.
- Po rozgałęzieniu zmiany z main i z trzech gałęzi dotykają wspólnie tylko STATUS.md w dwóch porównaniach. Ścieżki kodu nie nakładają się.
- GIS na bazie worktree `ec66c2df9`, identycznej kodowo z recenzowanym `main` (różnica w bazie obejmuje `HANDOVER.md` i `STATUS.md`): **231/231 PASS**, w tym **62/62** w czterech obowiązkowych zestawach budżetowych. [Polecenie i wynik](gis-tests.txt)
- Wykonałem też 7 istniejących przypadków gałęzi w pamięci: 6 dla przewodów, w tym Mickiewicza, Dojlidy i dk65-03, oraz 1 dla siatki i kolizji czterocentymetrowego cięcia. **7/7 PASS**. Reprodukcje błędów używają osobnych wejść. [Log](probe-branches.txt)
- Audyt Git dalekiego planu odtworzył wynik na 54 kaflach. Fala 12 → 13 High: **+3,48% do +20,91%**, mediana **+12,51%**. Low bez zmiany. [Log](far-audit-git.txt)
- Wrapper `wgpy.cmd` obsłużył uruchomione próby. Podstawiony blok Unity wykonał się raz po korekcie zasięgu `$unityWork`. Względna ścieżka `--art` przenosi fidelity pod katalog worktree wymagany przez `relative_to(REPO)`.
- Obejrzałem archiwalne porównania HUD i pomnika oraz High clear/overcast dla korytarza szwu. Archiwum szwu pochodzi sprzed naprawy Sadowej. [HUD i pomnik przed/po](archiwum-przed-po.png) · [Kadry High](archiwum-szew-high.png)
- Nie uruchamiałem Unity ani pełnego `build_world`/`far_field`. Dane GIS i istniejące artefakty świata były odczytywane. Nie zmieniałem kodu. Nowe rendery High, kompilacja shaderów i kodu C#, przejazd przez szew oraz pomiar pamięci klonów są **UNVERIFIED**.
- Lider po fali 14: zacząć od reprodukcji wyżej i sprawdzić poprawki przed kolejką fali 15. Przegląd z gita: `git show codex-review-s25:artifacts/codex-review-s25/REVIEW.md`.
