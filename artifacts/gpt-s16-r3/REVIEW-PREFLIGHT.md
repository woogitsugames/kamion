# ADR 0155 — niezależny preflight diagnostyki

**Wynik: PARTIAL / diagnoza otwarta.** Nie ma jeszcze pasujących renderów baseline ani dowodu przyczyny plam na głównej wyspie. Nie akceptuję na tym etapie zmiany produkcyjnego renderu. Poniższe uwagi dotyczą jakości rozumowania i granic narzędzi diagnostycznych, nie potwierdzonej usterki cieniowania.

Przeczytano ADR 0155, PutryShadowProbe.cs, trace_island.py, STATUS.md oraz owning sources dla RenderOverrides, zastosowania profilu, WorldSurface ShadowCaster i KamionFarShadow. Obejrzano reference-sheet.jpg. Bez Unity, adb, generatorów, testów i zmian kodu.

## Co wynika z fotografii

Oba zdjęcia richlv pokazują rzeczywisty pomost, podpory oraz obszerny cień na żwirowej wyspie. Zarazem bliski żwir i część skraju wyspy są wyraźnie jasne mimo położenia pod obrysem wiaduktu na obrazie. Nie można więc przyjąć reguły „cały żwir pod wiaduktem powinien być ciemny”. Perspektywa, otwarte boki pomostu i kierunek słońca decydują o miejscu granicy. Pozy klasy B i niekalibrowane światło nie pozwalają wskazać każdego poprawnego piksela ani docelowego poziomu albedo.

## Konkretne granice i potencjalne błędy diagnozy

1. **Promienie dotyczą innego fragmentu.** trace_island.py bada mały północny nos E534–540 / N−700…−690 w dwóch chunkach; wyklucza hero. Korekta została jawnie zapisana. Wynik nie dowodzi osłonięcia głównej wyspy E558 / N−734. Przeniesienie wniosku „większość próbek blocked” na główną wyspę byłoby błędem. Nie ma potrzeby powtarzać tego małego testu przed natywnym baseline.
2. **Blocked w ray teście nie oznacza udziału w shadow mapie.** Test przecina trójkąty GLB bez wybranego runtime LOD, shadow mask, wyłączeń materiału, zasięgu kaskad, rastryzacji i bias. Klasyfikacja front/back używa średnich zapisanych normalnych, a nie faktycznego stanu rasteryzera i orientacji trójkąta po pełnym imporcie. To użyteczny sygnał geometryczny, nie symulacja Unity Cull Back. Ograniczenie 30 m i odbiornik +0,05 m są dodatkowymi warunkami testu.
3. **HeroLods w probe nie dowodzi aktywnego castera nad wyspą.** Odczytywane są prototypy pasujące do prefixu, ich lokalne mesh.bounds i maski. Nie ma macierzy konkretnej instancji, jej world bounds, faktycznie wybranego LOD dla kamery ani potwierdzenia zgłoszenia do shadow pass. Lista materiałów oznacza noShadowMaterials, lecz nie przedstawia stanu wszystkich shaderów/passów i ewentualnych dodatkowych wyłączeń. Nie wolno z samego wpisu On wnioskować, że dana płyta rzeczywiście osłania wyspę w konkretnym renderze.
4. **Raport profilu nie jest odczytem efektywnego renderu.** Probe otwiera sceny Low/High i wypisuje pola profilu oraz Sun, ale nie ustawia środowiska, jakości i aktywnego URP jak runner VQA. Nie odczytuje też efektywnego przełącznika używania ustawień pipeline przez światło. Ostatecznym dowodem działania rq_shadowbias/rq_shadownormal ma być log `[RQ_PIPELINE]` z właściwego renderu i rzeczywiste ustawienie światła, nie sam diagnostic-report.json.
5. **rq_shadow=0 nie oznacza „wszystkie cienie wyłączone”.** W funkcji KamionFarShadow w KamionWorldGI.hlsl brak realtime shadow keyword daje fade=1, a wynik nadal uwzględnia bakedSun. Taka ablacja przełącza analizę w stronę cienia wypieczonego; nie izoluje całkowitego braku occluderów. Jeśli plamy zostaną, nie dowodzi to błędu albedo. Jeśli znikną, również trzeba rozdzielić realtime od wypieku, zamiast od razu poprawiać geometrię.
6. **TwoSided jest węższym testem, a restore ma założenie.** Probe zmienia tylko MeshRenderer nazwany bridge w określonym zakresie, nie hero instancje. Brak reakcji nie wyklucza problemu cullingu hero. Tryb restore ustawia On, nie odtwarza zapisanej wartości każdego renderera; jest prawidłowy wyłącznie po potwierdzeniu, że wszystkie zmienione renderery miały On w baseline. W przeciwnym razie trzeba wrócić do zachowanego stanu/importu. Nie przyjmować TwoSided jako naprawy przed wykazaniem, że odpowiednia powierzchnia trafia do badanego castera.

## Najkrótsza sensowna kolejność kolejnych testów

1. **Baseline jednej bliskiej kamery głównej wyspy, High-clear i Low-clear.** Stała kamera, słońce i ekspozycja. Oznaczyć na obrazie dokładne plamy oraz granicę cienia. Potwierdzić rzeczywiste occludery nad tym obszarem, world transform i wybrany LOD hero, a także aktualny zasięg realtime shadows. Nie zaczynać od zmiany wszystkich kontrolnych kamer naraz.
2. **Jeden render z rq_shadowbias=0 i rq_shadownormal=0.** Pozostałe ustawienia i odległość bez zmian. To krótki test, czy bias uczestniczy w zjawisku, nie proponowana wartość produkcyjna. Jeżeli efekt jest wyraźny, dopiero wtedy rozdzielić dwa rendery: sam depth bias 0 i sam normal bias 0. Przy braku efektu nie stroić tych dwóch parametrów na ślepo.
3. **Rozdzielić realtime i wypiek zmianą rq_shadow.** Dla tej samej kamery porównać 0 oraz odległość wystarczającą do objęcia całej wyspy realtime, z tym samym bias. rq_shadow=0 opisać jako far/baked branch. Duża odległość jest ablacją diagnostyczną, nie akceptacją kosztu Low. Zmiana plam wraz z odległością wskazuje na przejście realtime/baked lub zasięg, a nie automatycznie brak płyty.
4. **Dopiero zależnie od wyniku:** przy problemie pozostającym wewnątrz realtime i poprawnie zgłoszonym chunk bridge wykonać TwoSided tego castera. Przy problemie związanym z far branch obejrzeć próbki G/B oraz wysokość odbiornika z rzeczywistego GI map dla głównej wyspy i porównać z geometrią używaną do bake. Przy problemie wyłącznie hero badać jego faktyczny shadow pass/LOD zamiast powtarzać chunk TwoSided.

Overcast jest kontrolą ogólnego materiału/ambientu, lecz słabszy kontrast słońca może ukryć błąd bez jego usunięcia. Nie akceptować poprawki tylko dlatego, że plamy są mniej widoczne w overcast. Nie zmieniać albedo żwiru, nie zamykać szczeliny i nie dodawać zasłony bez dowodu geometrycznego.

## Warunek dalszej oceny

Czekam na natywne baseline i pasujące ablacje. Przed obrazami nie wydaję PASS wizualnego ani werdyktu o przyczynie. Każda późniejsza akceptacja powinna rozdzielić naprawę plam w tych kadrach od zgodności fotograficznej pozy B, od innych kamer/G3 oraz od urządzenia i przejazdu w ruchu.


## Uzupełnienie — odczyt baseline i aktualizacji probe

Obejrzano cztery obrazy `inspection/baseline`: `putry-island-1`, `putry-island-2` oraz SBS `2818555625124739` i `3970163613102941`.

W obu detalach widać pojedynczy, niemal równomierny szereg jasnych krótkich czworokątów na środku zacienionego żwiru. Miejscami występują dodatkowe mniejsze plamy obok szeregu. Krawędzie są miękkie, a wzór wiąże się kierunkowo z powtarzalną konstrukcją wiaduktu. Regularność występuje również w obu SBS; nie przypomina losowej wariacji mineralnego albedo. To opis wzoru, nie rozstrzygnięcie między geometrią, rastryzacją realtime i bake.

Oddzielny szeroki jasny pas przy krawężniku ma charakter granicy dużego cienia. Nie należy go automatycznie usuwać wraz ze środkowym szeregiem plam: jasny bliski skraj żwiru występuje również na fotografiach, choć przy innym świetle i pozie.

Lider usunął nieużywane mutacje TwoSided/restore z probe, pozostawiając diagnostykę read-only. Wcześniejsza uwaga o przywracaniu stanu dotyczy pierwotnej wersji, nie bieżącego narzędzia. Odczytany diagnostic-report wskazuje dla profilu Low 35 m / 1 kaskadę / 1024 i bias 1/1; efektywne ustawienia ma osobno potwierdzać pipeline.txt z VQA. Werdykt pozostaje otwarty do porównania pasujących ablacji baseline / zero-bias / baked-only / no-baked / no-shadows.

## Uzupełnienie — ablacje i rozdzielenie biasu

Obejrzano wszystkie 10 arkuszy ablation-sheets (5 kamer × Low/High), wszystkie 6 split-bias-sheets (island-1, near i SBS 2818 × Low/High), a także pełne natywne PNG `ablations/{Low,High}-zero-normal/putry-island-1.png`.

Wynik jest spójny w obu profilach:

- **zero-normal usuwa regularne środkowe plamy**, zachowując duży cień pomostu i jasny skraj przy krawężniku;
- **zero-depth pozostawia plamy**, podobnie jak no-baked;
- baked-only nie zachowuje tego regularnego wzoru, ale zmienia również duży cień; nie jest poprawką produkcyjną;
- no-shadows oświetla żwir niemal w całości i stanowi kontrolę, nie docelowy wygląd.

To mocny dowód, że obserwowany wzór w tych kadrach zależy od **normal bias realtime shadow pass**, a nie od samego koloru żwiru. Nie ma uzasadnienia, aby na obecnym etapie dodawać hero do bake jako pierwszą poprawkę tych konkretnych plam. Globalne zero-normal nadal nie dowodzi, że wystarczy zmienić dokładnie jeden materiał — wymaga to pasującego produkcyjnego after z lokalnym opt-in.

Na pokazanym żwirze, jezdni, podporach i widocznym spodzie pomostu nie zauważyłem nowego oczywistego acne w zero-normal. Crop split obejmuje przede wszystkim odbiornik; pełne island-1 uzupełnia widok spodu. Nie certyfikuje to górnej jezdni pomostu, wszystkich kątów ani zachowania w ruchu.

Propozycja lokalnego `shadow_normal_bias_scale=0` wyłącznie dla istniejącego M_viaduct_concrete, przy zachowanym depth bias i bez zmiany globalnego QualityProfile, jest sensowną hipotezą minimalnej korekty. Przy ocenie implementacji należy sprawdzić: rzeczywisty caster i materiał, nietkniętą gałąź domyślną, reset opt-in po usunięciu flagi oraz wszystkie powierzchnie współdzielące materiał. Końcowy PASS pozostaje otwarty do produkcyjnych after, przeglądu regresji i testów.

## Uzupełnienie — przegląd kandydata produkcyjnego

Przeczytano WorldShadowCasterBias.cs, miejsce wywołania w WorldPbrMaterials.cs, flagę w materials.py, nowy wariant ShadowCaster w WorldPBR.shader oraz WorldShadowCasterBiasTests.cs. Bez uruchamiania testów.

**Nie znalazłem błędu kontraktu, resetu ani doboru keyword w tej implementacji.**

- Jawne liczby w zakresie [0; 1] są akceptowane; NaN, Infinity, wartości spoza zakresu, brak flagi i nieobsługiwane typy wracają do skali 1 oraz wyłączonego keyword. Usunięcie wcześniej aktywnej flagi zerowej resetuje skalę z 0 do 1.
- Dla niezmienianego materiału z domyślną właściwością 1 helper nie wykonuje SetFloat; nie dopisuje zatem nowej wartości domyślnej do każdej istniejącej instancji materiału. To rozumowanie wymaga jeszcze porównania natywnej serializacji po imporcie; test jednostkowy i planowany audyt mają właściwy cel.
- Wywołanie znajduje się po przypisaniu World PBR i po zbudowaniu podstawowych właściwości, przed końcowym oznaczeniem materiału do zapisu. Wcześniejsze wyczyszczenie keyword jest uwzględnione: helper ponownie włącza wyłącznie potrzebny opt-in.
- Keyword jest deklarowany lokalnie i tylko dla etapu vertex istniejącego ShadowCaster. Gałąź bez niego zachowuje ApplyShadowBias; Forward nie dostaje nowej operacji. Zmienia się układ CBUFFER i powstaje wariant shadera, ale nie nowy pass, materiał lub draw.
- Sprawdziłem wzór w zainstalowanym URP `Shadows.hlsl:533–541`: ApplyShadowBias dodaje `lightDirection * _ShadowBias.x` oraz osobny inset normalnej. `depthOnly = pw + ld * _ShadowBias.x`, a następnie lerp do zwykłego wyniku, zachowuje depth bias i skaluje wyłącznie składnik normalnej. Kod jest z tym kontraktem zgodny.
- Flaga w materials.py występuje wyłącznie w viaduct_concrete. To zakres materiałowy, nie punktowy: wszystkie powierzchnie i instancje współdzielące ten materiał otrzymają wariant. Produkcyjne after powinno zatem obejrzeć także pozostałe ujęcia hero, litą górę pomostu i podpory, a nie wyłącznie żwir pod Putrą.

Siedem przypadków testowych obejmuje brak zmiany legacy, opt-in/removal, nieprawidłowe liczby i natywny zakres materiałów. Nie zastępują obrazu acne ani dowodu obecności wariantu w buildzie urządzenia. Końcowy PASS nadal nie jest wydany: audyt, natywny import, produkcyjne after i testy są w toku.

## Odrzucona pierwsza lokalizacja opt-in

Obejrzano `inspection/candidate/sbs2818-Low-clear.jpg`: przed/po regularny szereg jasnych plam na żwirze pozostaje praktycznie bez zmian. **FAIL dla próby ograniczonej wyłącznie do M_viaduct_concrete.** Ta lokalizacja nie spełnia celu naprawy, mimo poprawnego kontraktu helpera/shadera i mocnego wyniku globalnego zero-normal.

Nie należy utożsamiać materiału widocznego spodu hero z materiałem faktycznie rysującym problematyczny cień. Następny test powinien rozdzielić caster M_bridge_concrete od M_road_asphalt na chunk bridge; pojedyncze ablacje są rozstrzygające, połączenie obu naraz na początku utrudni lokalizację. Czekam na wyniki. Nie wydano końcowego PASS.

## Uzupełnienie — pojedyncze materiały chunk bridge

Obejrzano `material-ablation-sheets/M_bridge_concrete.jpg` oraz `M_road_asphalt.jpg` (baseline / pojedynczy materiał / global normal=0). Bridge-concrete-only tworzy dodatkowy wyraźny szereg jasnych plam, więc pogarsza badany wzór. Road-asphalt-only zmienia i częściowo ogranicza pierwotny szereg, ale nadal pozostawia plamy. Żadna pojedyncza izolacja nie spełnia celu.

Wynik uzasadnia kolejny test obu sąsiednich materiałów z tym samym offsetem; sam nie dowodzi jeszcze, że kombinacja wystarczy ani że wymagany jest region-wide override. Jeśli wygra kombinacja, polityka regionu powinna jawnie wymieniać oba istniejące materiały i wszystkie ich zastosowania, usuwać odrzucony opt-in hero oraz resetować stan po usunięciu wpisu/pliku. Niezależnie należy obejrzeć pozostałe mosty, podpory i górne powierzchnie. Czekam na combined; końcowy PASS nadal otwarty.

## Uzupełnienie — deck-triple Low

Obejrzano wszystkie pięć `material-ablation-sheets/deck-triple-{kamera}.jpg` oraz pełne natywne PNG island-1 i near z `material-ablations/deck-triple-Low`.

W subsetcie bridge_concrete + road_asphalt + bridge_kerb, przy pozostałych materiałach z dotychczasowym normal bias, regularny szereg plam znika we wszystkich pięciu ujęciach. Duży cień pomostu i jasny skraj przy krawężniku pozostają. Nie zauważyłem nowego oczywistego acne na widocznym żwirze, jezdni, podporach i spodzie pomostu. Wynik odpowiada lokalnie pożądanemu fragmentowi global normal=0.

To pozytywne potwierdzenie kierunku korekty dla pięciu diagnostycznych kamer Low. Nie jest jeszcze PASS dla polityki regionu, High, wszystkich mostów ani urządzenia. Po implementacji resetu i trzech jawnych wpisów nadal wymagane są rzeczywiste produkcyjne after, zakres natywnych materiałów, przegląd regresji i testy. Odrzucona flaga hero nie powinna pozostawać aktywna w kandydacie końcowym.

## Uzupełnienie — regionowa polityka B

Przeczytano aktualne ApplyRegionPolicy/ApplyPolicy w WorldShadowCasterBias.cs, wywołanie po CreateMaterialCore w RegionImporter oraz `Data/Regions/bialystok-industrial-c/shadow_caster_bias.json`. Potwierdzono brak pozostałej flagi hero w SC i zerowy diff WorldPbrMaterials/materials.py względem r2 w tym zakresie.

**Nie znalazłem nowego blokera kodu dla obecnego pliku polityki.** Wywołanie po centralnej fabryce obejmuje istniejące trzy materiały niezależnie od ich źródła, bez kopiowania definicji dróg do streetscape. Ścieżka wskazuje Data/Regions względem rzeczywistego projektu Unity w tym worktree. Odczyt nie ma cache, więc następny import widzi usunięty plik lub wpis. Przy obecnych definicjach bez źródłowej flagi brak wpisu wraca do skali 1 i keyword off; helper oznacza zmieniony materiał jako dirty.

Schemat jest sprawdzany, a nieprawidłowa wartość dopasowanego materiału zatrzymuje import. Drobna granica tego kontraktu: parser sprawdza wartość wpisu dopiero podczas obsługi danego materiału wspierającego właściwość. Nie należy więc opisywać go jako pełnego walidatora wszystkich nieużywanych/nieznanych kluczy polityki. Obecny JSON zawiera trzy prawidłowo nazwane istniejące materiały, więc nie jest to wykazany błąd kandydata B.

Zakres polityki jest jawnie regionowy i materiałowy: bridge_concrete, bridge_kerb i road_asphalt. Nie oznacza to automatycznie zmiany wyglądu całej nawierzchni, ponieważ helper dotyczy ShadowCaster, a zwykła warstwa road nie rzuca cieni; nadal trzeba obejrzeć wszystkie zastosowania tych materiałów, które rzeczywiście są casterami. Hero viaduct_concrete pozostaje poza opt-in.

Testy usunięcia pliku/wpisu i natywny exact-three zakres mają właściwy cel. Nie uruchamiałem ich. Produkcyjny import, natywne SHA, pełne after i testy nadal pozostają wymagane przed końcowym PASS.
