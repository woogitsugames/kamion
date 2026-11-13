# STATUS — gpt-s16
2026-11-13T01:06:30.1891820+01:00
R1 / ADR0153: ukończona i wypchnięta gpt-s16-r1@eb718b7f8, gotowa do recenzji statycznego edytora; GIS927passed3xfailed,EditMode452/452,616par,criticPASS.
R2 / ADR0154: gałąź gpt-s16-r2 po merge origin/main; GOTOWE DO RECENZJI: NIE.
Baseline597.2s bezfallback, importOK,90kamer×4warunki,12ujęć6ulic; autor obejrzał arkusz12ujęć i zdjęciaP07/P08/P10/P12/P14/P17.
Audyt bazowy:2151chronionychwęzłów,32grupplots,116drzewogrodowych,458natywnychmateriałów.
Kod: uzupełniające żywopłoty w istniejącym plot_kit,limit3600trisLow,bramy/dojściaotwarte,bez rozszerzania grup/obwiedni. Korony istniejących high: jawne garden_canopy_width,bez nowych instancji i shaderów.
Testy celowane:6GISpassed;8nowychprzypadkówEditMode czeka na uruchomienie. Zastąpione szkice i prototyp usunięto; kod tylko w źródłach i testach.
W tle: generator after, slotheavy gpt-s16. NASTĘPNY KROK: Get-Content artifacts/gpt-s16-r2/after-world.log -Tail 3
Dalej: audyt po generatorze, import/after/rzeczywisteobrazy,pełnyGIS/EditMode,recenzja,ADR/REPORT,push własnej gałęzi; potem r3.
Referencje6ulic są typologiczne: repo nie pokrywa fotograficznie bocznych ulic regionu. Bez udawania zgodnych lokalizacji/poz.
Telefon/GPUruch/ASTC: UNVERIFIED, lider. Nie dotykam telefonów ani main.
DECYZJA sprzątanie: clear-rejected r1(0.412GB) pozostał po blokadzie automatycznego przeglądu usuwania; bez obchodzenia blokady.
Limit sesji dookoło10:34 13.11.2026.

Celowany EditMode GardenCanopyWidthTests: exit0; szczegóły targeted-editmode.xml/log.

Celowany EditMode:8/8passed,0failed/skipped; skala koron zachowuje wysokość/początek i pakowaniecompactTRS. Przygotowano per-kamera porównanie z ostrożnym przedziałem kwantyzacji1ktris oraz limitemLow+2%; nie będzie podpisane jako GPU/device pomiar.

ADR0154 opisuje źródła, WORKING_VALUE i luki zdjęć. Audyt rozszerzono o6hashy bibliotek modeli/atlasu, aby potwierdzić brak ubocznej zmiany modeli i materiałów pojazdów/lasu. Generowanie after nadal w tle.

W świecie po zmianie przyjęto19posesji/34odcinki nowych żywopłotów:257.37m,3580trisHigh i3580trisLow. To wynik generatora, nie jeszcze pomiar kadru. Limit3600 nieprzekroczony. Dalej audyt i obrazy.

Świat after wygenerowany: 597.4228808 s, bez fallback=True. NASTĘPNY KROK: import i kamery after.

Audyt after:2151chronionych siatek i wszystkie rekordy nie-high identyczne,116drzewogrodowych zachowuje tożsamość/pozycje/tier;6bibliotek/atlasówbez zmian;32grupyposesjibeznowychmateriałów;0błędów. Delta bufórówplots High+Low łącznie7160tris, czyli3580na wariant. Generator595.7s.

Import after zakończony.

Przygotowano24arkusze zdjęcie|przed|po dla6ulic×4warunki (po2pozy na ulicę), z podpisami niezgodnej lokalizacji/pozy i autorami/licencjami. Recepty użyją oryginałów w repo bez ich kopiowania; czekają na afterPNG.

Zapisano after/High-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/Low-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/Low-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/High-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Nowy smoke po poprawie selekcji posesji zbiorowych: korony należące do wydłużonej grupy domów bywają >25m od centroidu, więc dobór używa także ich jawnego srcplot. Nie przesuwano drzew ani budynków. Wcześniejsza próba smoke bez pliku kamer zakończyła się błędem i nie jest dowodem; finalny zwykły render wymaga oględzin.

Zachowano mały pakiet iteracjiA:6arkuszy,pozy,liczniki i uczciwyPARTIAL; bez duplikowania pełnychPNG. Dalsza korekta obejmie relację do maksymalnej wysokości rzeczywistej geometrii dachów pobliskich domów i bliższe kadry. Sam LoD1 pierwszego domu w grupie nie opisuje kalenic sąsiadów.

IteracjaB: korony odnoszą się do maksymalnegoZ pobliskiej istniejącej geometrii dachów (odczyt,bez edycji domów), nie do LoD1 pierwszego domu grupy. Prześwit4.5m i dojrzale limity birch23/linden24/maple22m toWORKING_VALUE z proporcji zdjęć. 7testówGISpassed; nowytest obejmuje wyższy dach w grupie i pomija odległy dach. Dodano odtwarzalny opt-out KAMION_GARDENS_0154=0 wyłącznie do baseline, domyślnie funkcja działa. LicznikiVQA rozszerzono addytywnie o dokładne CPUtris,bez zmiany renderu. Nowe12póz zastąpi stare pliki przy ponownym baseline/after, bez duplikowaniaPNG.

Porównywarka końcowa wymaga teraz surowych dokładnych CPUtris ze SceneStats/VQA, bez kwantyzacji tysięcy. Przed i po będą zrekapturowane tym samym kodem. Nie zmienia to renderu ani interpretacji drawów jako estymaty CPU.

Przed nowymi renderami dobrano odległość28–45m od celu korony,po2rozłączne rzeczywiste pozycje na każdej ulicy,FOV50. Poprzedni smoke miał np06a zbyt blisko pnia; pełne korony nie mieściły się w kadrze. To korekta wyłącznie kameryQA, nie drzew/budynków. Before/after będą miały tę samą finalną listę.

Świat baseline wygenerowany: 592.1205654 s, bez fallback=True. NASTĘPNY KROK: import i kamery baseline.

Dodano test integracji natywnego importu: każdy zserializowany opt-in korony musi mieć właściwą skalęX/Y orazZ/Y w rzeczywistym WorldInstanceSet i zachować Compact. Zostanie uruchomiony na kandydacieB (na bazie bez flagi jawnie pomijany), obok8jużzielonych testów czystej transformacji. Nie jest to dowód wyglądu.

Import focus-baseline zakończony.

Rebaselineoff590.4s: audyt zgadza się z pierwotną bazą w2151chronionychwęzłach,grupach/trianglesplots,rekordachLow i116drzewogrodowych. ImportOK. Pierwszy render zatrzymał błąd kompilacji nowego testu integracji (Compactjestprywatne); poprawiono test na publiczne matrices/positions/rotations/scales. Nie zaliczono nieudanej próby. NASTĘPNY KROK: powtórzyćbefore4warunki,bez ponownej generacji bazy.

Zapisano before/Low-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/Low-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/High-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano before/High-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Świat after wygenerowany: 594.7261546 s, bez fallback=True. NASTĘPNY KROK: import i kamery after.

Import roof-aware-after zakończony.

Zapisano after/High-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/Low-clear; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/Low-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Zapisano after/High-overcast; każda kamera w stats.txt. Oględziny pozostają wymagane.

Wszystkie360parB mają pasujące kamery. Końcowe porównanie używa dokładnychCPUtris; szczegółyCAMERAS.md/camera-counts.json. Nowe zdjęcie|przed|po24arkusze odświeżone dlaB. Dalejpełne testy i recenzja; D51fotograficzny nadalwymaga odróżnieniaodkonkretnej poprawykoron/frontów.
