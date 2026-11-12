# 0115 — Zewnętrze TRAKT-a i naczepy

## Runda 1 — lakier, szkło i światła dzienne

Status: runda zakończona z ograniczonymi poprawkami technicznymi; cel wyglądu lakieru i szyby pozostaje otwarty. Start 11 listopada 2026, 21:31 CET. Gałąź `gpt-truck-r1`.

Punktem wyjścia jest main `5f2aa277` oraz recenzja `REVIEW-2026-11-11-s10-gpt-0087-0090.md`. Dawne pomiary 0087 nie stanowią pomiaru tej rundy. Obowiązują D30, D34, D35 i D44, a także budżet Low bez dodatkowych przebiegów i wzrostu liczby wywołań rysowania. Czas GPU na telefonie pozostanie UNVERIFIED, ponieważ telefony należą do zakresu lidera.

Najpierw zapisujemy aktualny baseline Low i High, przy zachmurzeniu i słońcu. Ocenę lamp opieramy na tej samej masce i rozkładzie jasności, ocenę szyby na jej górnej i dolnej części oraz widoczności wnętrza, a lakieru na drzwiach i deflektorze. Zdjęcia Commons są wyłącznie odniesieniem do zachowania materiału, nie projektem do skopiowania. Przesłane obrazy AI nie są zdjęciami ani źródłem tekstur.

Pierwsza uzasadniona poprawka techniczna dotyczy mgły w `FragFast`: szkło używa mieszania premultiplied, więc jego wkład rozproszonego światła atmosfery powinien być pomnożony przez alfę. W szybkim wariancie wierzchołek już oblicza transmitancję atmosfery, dlatego fragment nie może ponownie liczyć wykładnika. Osobno należy zachować zgodność filtrowania capture z pełną ścieżką.

DRL zachowuje kodowanie 1000 nitów na jednostkę RGBAHalf. Luminancja jest WORKING_VALUE i wymaga porównania przed i po. Nie zmieniamy ekspozycji całej sceny ani presetów oświetlenia należących do innej sesji. Lakier wymaga aktualnego dowodu rozdzielającego refleks od jasności białego pigmentu; nie przyjmujemy z góry, że capture nie zawiera podłoża.

Nie ogłaszamy PASS wyglądu. Wyniki i ograniczenia zapisano poniżej oraz w raporcie rundy.

### Decyzje i dotychczasowe dowody r1

Zachowujemy poprawkę mgły w `FragFast`: wkład atmosfery jest pomnożony przez alfę tafli, a transmitancja obliczona w wierzchołku pozostaje bez zmian. Wariant pełny High nie został zmieniony. Niezależny recenzent nie stwierdził regresji w parach widoku kierowcy i zewnętrza. Zmiana jest mała wizualnie: Low `truck-34` ma medianę jasności próbki szyby 19,86 → 19,05% i odchylenie 5,885 → 6,065 punktu. Nie jest to rozwiązanie mleczności ani spełnienie D34.

Stała redukcja surowej luminancji DRL nie dała właściwego kompromisu pogodowego. Wariant 2000 usunął przycięcie, ale recenzent wskazał wygląd jasnego plastiku. Wariant 4000 pozostawił 1209 przyciętych pikseli High-overcast wobec 1214 w bazie. Wariant 3000 usunął clipping, lecz mocno osłabił pasek w słońcu. Te warianty są dowodami porównawczymi, a nie wybranymi ustawieniami kontrolera.

Kandydat końcowy zachowuje surowe ustawienia sterownika 160000/56000 oraz skalę kodowania 1000 nitów na jednostkę. Wyłącznie grupa DRL o identyfikatorze 1 dostaje w `TruckExterior.shader` lokalną kompresję luminancji `E / (1 + Y / k)`. Wspólny mnożnik RGB zachowuje barwę; maska emitera jest stosowana po korekcie. Obliczenie odbywa się w `float` przed konwersją do `half`. Parametr materiału `_DrlHighlightShoulder` ma roboczą wartość 0,8 w odsłoniętych jednostkach sceny, a 0 wyłącza korektę. To jawna kalibracja obrazu dla istniejącej krzywej D23, nie pomiar fizycznej fotometrii lampy.

Nie zmieniamy F0, amplitudy wypukłości drzwi, geometrii, pozostałych grup lamp ani ustawień światła i postprocessingu. Korekta nie dodaje tekstur, próbek, przebiegów ani wariantów shaderowych. Dodatkowa arytmetyka dotyczy fragmentów DRL; jej czas na A16 pozostaje UNVERIFIED. Liczniki wszystkich kamer oraz instancji będą porównane osobno po kanonicznej regeneracji.

W stałym natywnym ROI lewej lampy liczba pikseli z każdym kanałem RGB ≥254 wynosi 1214 → 0 na High-overcast; w pozostałych trzech warunkach kandydat również ma 0. ROI zawiera obudowę i otoczenie lampy. Recenzent rozpoznaje włączone DRL w obu pogodach, nie widzi regresji reflektorów i kierunkowskazu; zaznacza, że gradient pozostaje subtelny. To akceptacja kandydata do walidacji, nie PASS całego truck.

Testy rzeczywistego dekodowania/stanu oraz nowego ograniczenia HDR i bypassu przeszły 11/11, bez pominięć. Nowe próby GPU obejmują zerową i dużą ekspozycję. Wyniki pełnego EditMode i końcowego GIS są poniżej.

Kontrole lakieru zachowały szorstkość i tłumienie podłoża przy wyłączaniu samego wkładu powłoki. High-overcast: wkład powłoki w średnią jasność próbki drzwi wynosi 1,62 punktu na bieli i 4,66 na ciemnym pigmencie. To wyniki po przetwarzaniu obrazu, nie surowe HDR. Potwierdzają obecność odbicia, lecz nie zamykają celu połysku białej kabiny. W tej rundzie nie wzmacniamy sztucznie F0.

Pozostają otwarte: kredowy lakier i dach w słońcu, mleczność szyby oraz D44. Stara baza ma stosunek odchyleń szyby do widoku bez przedniej tafli 0,475 Low i 0,526 High, przy celu 0,7. Końcową próbę bez tafli wykonano na identycznej wersji kandydata. Brak pomiarów telefonów zgodnie z zakresem właściciela.

Po pilnej aktualizacji właściciela wszystkie ciężkie zadania Pythona korzystają z puli `heavy` (max 3), a pełny GIS jest uruchamiany wyłącznie na końcu rundy. Wcześniejszy bazowy GIS, wykonany przed tą aktualizacją i przed zmianami produkcyjnymi, dał 488 passed, 5 failed, 1 xfailed. Pięć błędów dotyczy far-field, wiaduktu, przeterminowanego fidelity, brakującego prototypu i deterministyczności świata; pliki tych dziedzin nie są poprawiane w sesji truck.

### Końcowa kontrola renderowania i EditMode

Po kanonicznym zbudowaniu obu pojazdów i instalacji w scenach zapisano 28 kadrów końcowych, dodatkowo 6 Medium, 6 o zmierzchu i 6 kontrolnych bez przedniej szyby. Pełny EditMode zakończył się kodem 0: 266 passed, zero failed i skipped. Wszystkie 96 wierszy kamer (48 × Low/High, overcast) ma identyczne liczniki rendererów, cieni i instancji oraz raportowane tysiące trójkątów. Dowód: `artifacts/truck-r1/all-cameras-counters.csv`. Trójkąty są zaokrąglone, wywołania rendererów są estymatami przed SRP, a nie pomiarem GPU telefonu.

Końcowy D44 według tej samej próbki i skalowania do 1024 px: 0,490 Low i 0,526 High, nadal poniżej 0,7. Rozrzut profilu drzwi pozostaje identyczny: overcast 3,362 Low i 2,437 High; clear 5,261 Low i 3,661 High. Przy celu 4–10 większość warunków nadal nie przechodzi. Końcowe ROI lewej lampy potwierdza 1214 → 0 przyciętych pikseli High-overcast i 0 → 0 w pozostałych trzech warunkach.

Decyzja o podłodze szorstkości capture w `FragFast`: nie dodajemy nominalnej wartości 0,09 z pełnej ścieżki. Obecne Low i Medium mają capture 64 px; wzór `mip = clamp(log2(max(pr² × size / 2, 1)), ...)` daje mip 0 zarówno przed, jak i po takim ograniczeniu dla pr < 0,09 (największy footprint 0,2592). Dla większego pr ograniczenie nic nie zmienia. Ta równoważność dotyczy aktualnych profili, a nie dowolnej przyszłej rozdzielczości. Medium-overcast i Medium-clear zostały wyrenderowane po zmianie mgły.

Niezależna kontrola po rebuildzie nie wykazała nowej regresji sylwetki, ustawienia pojazdu ani widoku kierowcy w ośmiu arkuszach. Lakier, dach i szyba nadal nie spełniają celu materiałowego. Zmierzch jest kontrolą jakościową bez bazy: Low i High pokazują płaskie jasne moduły reflektorów; nie przypisujemy ich tej rundzie. Pełna ocena jest w `artifacts/truck-r1/FINAL-REVIEW.md`.

Końcowy GIS pod slotem heavy: 488 passed, 5 failed, 1 xfailed w 688,34 s, dokładnie te same pięć testów co w bazie. Porównanie nazw i wyników jest w `gis-comparison.json`. Sześć zmienionych przez test plików generated zachowano w patchu i przywrócono do wersji gałęzi. Nie poprawiano błędów innych dziedzin.

Kompilacja Android z zawartością Low i High zakończyła się powodzeniem: 0 błędów, 12 ostrzeżeń, 289 s. APK ma 375305009 bajtów; log, SHA i metadane w `artifacts/truck-r1/build/`. Wśród ostrzeżeń są potencjalnie niezainicjalizowane wartości w niezmienionym `KamionVehicleEnv.hlsl`; brak błędów shaderów. Nie instalowano ani nie uruchamiano aplikacji na telefonie. Wygenerowane ustawienia przywrócono; tymczasowe Resources usunął sam pipeline Unity. Kod źródłowy builda jest wskazany przez SHA w nazwie APK, późniejsze commity zapisywały jedynie dowody i dokumentację.

## Runda 2 — zabrudzenia i zużycie

Start po dostarczeniu r1. Gałąź gpt-truck-r2, merge main 2c3939b2 do własnej gałęzi bez konfliktów. Najpierw świeże wejścia i import po zmianach innych sesji, następnie kontrola ilości brudu i baseline Low/High w obu pogodach. Pełny GIS wyłącznie na końcu rundy. Źródła innych dziedzin pozostają bez zmian.

### Decyzja materiałowa r2

Pozostaje wyłącznie mniejsza proceduralna retencja na górnych, niepolakierowanych metalowych powierzchniach. Maska z atlasu nadal ma pierwszeństwo przez max, a AO nadal cieniuje wnękę. Wypukłe kratki stopnia miały niskie AO razem z całą wnęką: uzależnienie czyszczenia od wysokiego AO nie dawało widocznej poprawy. Diagnostyka rzeczywistych materiałów pokazała dominację brudu proceduralnego, dlatego niezależne osłabienie jego retencji do 0,25 na metalowych powierzchniach skierowanych w górę przywraca kratkę. Wartość 0,25 i progi normalnej są WORKING_VALUE, bez deklaracji fizycznego modelu śladów butów. Lakier i koła są wykluczone. Nie dodano tekstur, przebiegów, słów kluczowych ani geometrii; koszt dodatkowej arytmetyki na telefonie pozostaje UNVERIFIED.

Niezależna kontrola czterech zbliżeń Low/High, clear/overcast zaakceptowała czytelniejszy ciemnoszary stopień przy zachowanym cieniu wnęki i bez jasnego halo. Testowane zacieki plandeki i jaśniejszy suchy plastik odrzucono jako niewidoczną korzyść przy dodatkowej arytmetyce. Krótsze plamy rozbryzgu poprawiały charakter brudu, lecz pogarszały czytelność dolnego pomarańczowego elementu, więc także zostały wycofane. Wszystkie odrzucone próby mają osobne obrazy i oceny w artifacts/truck-r2.

Korekta założenia o profilach: aktualny main ma vehicleGrimeDetail=true również na Low. Stąd wcześniejsze wpisy robocze o niezmienionym Low height-only były błędne; wykryto to przy kontroli krótszego rozbryzgu i zapisano korektę w STATUS oraz REVIEW-SPLASH-017.md. Nie zmieniano profili jakości. Błotniki i plandeka nie są zgłaszane jako rozwiązane. Walidacja końcowa w toku.

### Wyniki końcowe r2

Po kanonicznym rebuildzie zapisano 40 par (7 całych kadrów i 3 zbliżenia × 4 warunki) oraz wszystkie kamery Low/High-overcast. Wszystkie 96 wierszy mają identyczne liczniki rendererów, cieni, raportowanych tysięcy trójkątów i osobnych instancji; to estymaty CPU przed SRP, nie GPU telefonu. W stałym natywnym ROI stopnia [800,810,1080,855] sigma wyświetlanej luminancji wzrosła: Low-overcast 2,090 → 8,351, High-overcast 2,482 → 9,754, Low-clear 2,925 → 5,722, High-clear 3,157 → 6,742 punktu. ROI zawiera grzbiety, otwory i cień, nie jest miarą fizycznego pokrycia brudem.

Własny przegląd wszystkich 40 par oraz niezależny przegląd reprezentatywnych całych kadrów i czterech zbliżeń potwierdziły ograniczoną poprawę bez nowej regresji sylwetki ani widoku kierowcy. Szczegóły i granice pewności: artifacts/truck-r2/FINAL-REVIEW.md. Pełny EditMode przeszedł 300/300, bez failed/skipped, exit 0. Android Low+High: Succeeded, 0 błędów, 12 ostrzeżeń, 191 s; APK 384474361 bajtów, SHA256 1AF3EE29AB03783ACA1AC65EF451CAEE08E937EEC70BFF0AB72450B0C495416F. Kod wejściowy kompilacji 0b4b6237969c42cfce7ad9112ef4be44708946ef. Nie instalowano i nie uruchamiano telefonu. Ustawienia przywrócone, Resources usunięte przez pipeline. GIS oczekuje na slot heavy, bez omijania limitu.
Końcowy GIS r2 uzyskał slot heavy i zakończył się: 575 passed, 1 failed, 1 xfailed w 657,56 s. Jedyny błąd test_world_roads.py::test_export_is_deterministic dotyczy chunk 0_0, występował również w r1. Po scaleniu main zmieniły się testy i inne dziedziny; brak świeżej bazy r2 nie pozwala przypisywać usunięcia pozostałych błędów shaderowi truck. Zachowano patch i cztery surowe pliki zmienione przez test, przywrócono wszystkie cztery. Semantyczna różnica dotyczyła world_manifest.json; pozostałe były oznaczone w statusie przez zakończenia linii. Szczegóły: gis-result.json.

## Runda 3 — opony i felgi

Status: runda zakończona z ograniczoną poprawką, bez PASS wyglądu całego pojazdu. Gałąź gpt-truck-r3, baza main 9874d98c54219131f72ddfffa19060b6ea67eaf3, merge f92690f3. Materiały odświeżono w 445 s, świat w 542 s, bez fallback=True; świeży import i baseline Low/High clear/overcast. World_manifest pozostaje świeży do końcowego GIS; pliki innych dziedzin nie są commitowane. Ograniczenie poprzedniego GIS wyjaśnia artifacts/truck-r2/GIS-VALIDATION-CORRECTION.md: odtworzenie starszego manifestu przed testem r2 mogło wpłynąć na porównanie, przyczyny nie rozstrzygnięto.

### Rozdzielenie geometrii i atlasu

Podglądy flat, raw albedo, normalnych i CullOff oraz odczyt sześciu reprezentatywnych importowanych siatek rozdzieliły brak osłony osi od wad atlasu. LOD2_DROP usuwało hubcap/hub ciągnika i hubcap naczepy. Oryginalne przednie koła LOD2 odsłaniały 33/33 próbek osi, a sześć kół naczepy 17/17 próbek; odpowiadające LOD0/1 przechodziły. Testy rzeczywistych FBX mają czerwony baseline, nie zależą od jasności materiału ani normalmapy. Zachowano osłony w Low.

Przednie koło Low miało 47 trójkątów o rozpiętości UV >0,25 atlasu (LOD0/1 zero). Reduktor łączył rozłączne wyspy Smart UV. Test 76 wariantów rzeczywistej funkcji BMesh odtworzył 760 mostkujących trójkątów starej funkcji w grupie kątowej i 684 w mieszanej, po ochronie granic zero. To przypadki syntetyczne, nie liczby trójkątów auta. Naczepa nie miała tej samej zmierzonej wady UV.

Sama ochrona licznych szwów Smart UV przekroczyła budżet: ciągnik LOD2 24695>17900, wariant odrzucono bez instalowania. Wybrana metoda zachowuje pierwotne cylindryczne UV opon i rantów lathe, dopasowuje gęstość do innych wysp slotu i pakuje jedną ciągłą wyspę. Test authoringu obejmuje konwersję materiałów, pakowanie i redukcję; przechodzi wraz z regresją szwów. Wykonano pełny bake obu pojazdów, bez zwiększenia map.

### Eksporty i widoczna poprawa

Pełny bake v2 i natywne walidatory: ciągnik 273,62 s, LOD0 104514, LOD1 43000, LOD2 17689; naczepa 256,93 s, 89000/24500/7844. Zamknięcie osi i ciągłe UV poprawiły formę, lecz przednia tarcza Low nadal wyglądała jak trójkątna gwiazda. Zwiększenie wszystkich zewnętrznych tarcz do udziału 0,40 przekroczyło limit ciągnika 18284>17900, więc nie zostało zainstalowane.

Końcowy v3b reexportuje wyłącznie LOD2 z cache o sprawdzonym SHA. Zachowuje przednią tarczę ciągnika co najmniej 0,35 pierwotnej puli, tarczę naczepy 0,25, jej oponę 0,06 i rant 0,10; osłony mają własne minima. Są to WORKING_VALUE redukcji, nie wartości fizyczne. Globalne cele nie wzrosły. Oba natywne walidatory PASS: ciągnik 17690/17900, naczepa 7849/8000. Wszystkie mapy i LOD0/1 są byte-identyczne z pełnym v2; dowody lod2-*-preserved.json. Instalacja wymaga wspólnego generation_id i zgodności SHA wszystkich wyników, by nie mieszać częściowych eksportów.

W reprezentatywnej przedniej siatce Low UV-wide 47→0, trójkąty 907→1186, importowane wierzchołki 1086→1124. Koło naczepy Low 511→709 trójkątów i 849→967 wierzchołków. Reprezentatywne cztery koła LOD0/1 zachowały geometry+normal hash, celowo zmieniły UV i zmniejszyły liczbę importowanych wierzchołków. To nie jest pomiar pamięci ani czasu GPU całego pojazdu.

Na 12 świeżych zbliżeniach i 28 całych kadrach Low/High clear/overcast (High v2 ma identyczne mapy/LOD0/1 jak końcowy wariant) własny i niezależny przegląd potwierdzają pełniejszą przednią tarczę Low niż v2, z ograniczeniem dużych trójkątnych płatów. Osłony obu pojazdów są zamknięte. Brak nowej większej regresji kabiny, progów, lusterek, plandeki i jej mocowań w pokazanych obrazach. Nadal P1: nieregularne wielokątne otwory i ząbkowany rant przedniej felgi, ukośne fragmenty wnętrza felgi naczepy oraz kanciastość opon Low. Ruch i telefon pozostają niezweryfikowane. Zdjęcie koła Matti Blume CC BY-SA 4.0 jest odniesieniem ciągłości formy, nie kalibracji chromu/koloru/jasności. Pary i kontakty mają maksymalnie 960 px, szczegóły REVIEW-WHEELS-V3.md, REVIEW-WHOLE-LOW.md i REVIEW-HIGH-ATLAS.md.

### Końcowe kontrole

Testy geometrii kandydata 12/12, pełny EditMode 326/326, zero failed/skipped. Wszystkie 96 wierszy kamer mają zerowy wzrost draws rendererów i osobno instancji; trójkąty bez wzrostu, dziesięć wierszy Low spadło o 1–2 tysiące w zaokrąglonym liczniku. Pozostałe liczniki zgodne. To estymaty CPU przed SRP i zaokrąglone trójkąty, bez pomiaru GPU A16.

Audyt 580 plików i dwóch prefabów potwierdza identyczne pozycje. Zmieniła się kolejność slotów Paint/Trim dwóch drzwi Low; importer TruckAssetBuilder odczytuje nazwy aktualnych materiałów i rozwiązuje je w tej samej kolejności, a porównania nie wykazują zamiany powierzchni. Jawne różnice w fixture-final-semantic-diff.json. Bajty siatek i map celowo nie są identyczne z baseline. Android Low+High: Succeeded, zero błędów, 12 ostrzeżeń, 162 s. APK 389093741 bajtów, SHA256 AC52927339EC9DDA4CB4519591FC985D11E24E12682F125081CB5631AF7C0F14, kod wejściowy f3e79869dcea5b04ad03af0a9b93591e515508d5. Bez instalowania i uruchamiania, ustawienia przywrócone przez wrapper. Końcowy GIS pod heavy: 617 passed, 1 failed, 1 xfailed w 814,39 s. Jedyny błąd test_road_fidelity.py::test_report_not_stale wskazuje fidelity_qa nieaktualne względem overrides.yaml i roads/meshing.py. Deterministyczność świata przeszła na świeżych wejściach; brak świeżego bazowego GIS r3 ogranicza porównania między rundami. Zachowano patch i siedem surowych wygenerowanych plików z SHA, potem przywrócono dokładnie tę listę. Nie poprawiano dróg ani fidelity innych dziedzin. Wynik pozostaje Failed, nie pełny PASS repozytorium.
