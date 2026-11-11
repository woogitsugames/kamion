# ADR 0120 — Meble uliczne, sesja 8

Data rozpoczęcia: 2026-11-11. Status: praca w toku, bez zgody na integrację.

## r1 — Podmurówki, betonowe latarnie i tyły znaków

Źródło problemów: `docs/reports/visual/REVIEW-2026-11-11-s10-gpt-HIL.md`, I1–I5.
Punktem odniesienia jest main `5f2aa277`, a nie stare rendery ADR 0102.
Czysty poprzedni worktree przeniesiono do `.claude/worktrees/gpt-furniture`;
istniejąca gałąź `gpt-furniture-r1` została przesunięta fast-forward do main.
Dowody tej sesji są w `artifacts/furniture-r1/24h`, wcześniejsze ADR 0102 w katalogu nadrzędnym.

Zakres obejmuje wyłącznie ogrodzenia posesji, prototypy lamp i znaki.
Funkcje barier, ekranów, mostów, drogi oraz cudze pliki pozostają poza zakresem.

Plan sprawdzenia: baseline generatora i importu, wszystkie kamery Low/High przy słońcu
i zachmurzeniu, zmiana, ponowna generacja/import, porównanie każdej kamery.
Draws instancji należy raportować osobno. Liczniki edytora nie są pomiarem telefonu.
Budżet Low: draws +0, trójkąty do +2%; wynik wymaga pomiaru.

Podmurówka ma otrzymać krótsze poziome przęsła tam, gdzie skarpa powoduje
nadmierną odsłoniętą wysokość. Detal betonowych żerdzi powinien wynikać
z istniejącej bazy skanu CC0 i masek zależnych od wysokości oraz okuć.
Aluminiowa tarcza znaku nie otrzymuje korozji żelaza na całej powierzchni:
rdza może spływać od stalowych mocowań, a blacha ma utlenienie i brud.
Wymiary i zasięgi zużycia pozostają WORKING_VALUE do porównania ze zdjęciami.

Referencje lokalne: Mapillary p12/p15/p20/p26/p30 (ADR 0069/0102),
`docs/refs/posesje-bialystok.md` oraz Commons z istniejących manifestów.
Dotychczasowe klatki nie potwierdzają rodziny każdej lampy bocznej ulicy:
mapowanie pozostaje UNVERIFIED. Piksele referencji nie wchodzą do builda.

Przed każdym procesem Unity `unity-slot.ps1 -Acquire -Owner gpt-furniture`,
po nim `-Release`; bardzo wysoki próg StaleHours zapobiega usuwaniu cudzych slotów.
Telefony, push i scalanie do main nie są częścią tej sesji.

## Aktualizacja protokołu obciążenia, 2026-11-11 wieczorem

Po pilnym poleceniu właściciela także build_world, build_all, pełny GIS,
physics/gate3 i fidelity wymagają puli `heavy`, maksymalnie trzy zadania na maszynie.
`artifacts/furniture-r1/24h/heavy-step.ps1` pobiera tę pulę dla aktualnej gałęzi
i zwalnia ją w `finally`. Pełny GIS jest uruchamiany wyłącznie na końcu rundy.
W trakcie stosujemy pojedyncze pliki testów. Bieżący import ma już gotowe produkty
świata i PBR; następne importy sprawdzają ich kompletność przed slotem Unity,
aby skrypt importu nie uruchomił ciężkiego generatora poza pulą.
Gate jest wywoływany z aktualnego main; nie zmieniono wspólnego skryptu w gałęzi.

## Stan przed renderami r1

Baseline generatora: exit 0, 64 chunki, brak `fallback=True` w logu.
Przygotowanie cache PBR: exit 0; wersjonowana specyfikacja materiałów bez zmian.
19 testów mebli przechodzi, w tym krótka stroma skarpa, zakres UV pięciu kształtów
oraz rejestracja maski rdzy pod rzeczywistymi mocowaniami A-7 i C-12.
Niezależne ustalenia kodowe zapisano w `24h/REVIEW-CODE.md` i uwzględniono
w geometrii oraz UV. Nie jest to jeszcze zatwierdzenie wyglądu ani budżetu.

Koszt prototypów lamp i znaków pozostaje bez zmian; stara betonowa lampa Low
ma 91 trójkątów i 4 sloty. Lokalny koszt ogrodzeń wzrasta i wymaga pomiaru
na wszystkich kamerach. Przygotowano 6833 hashe chronionych prymitywów baseline.
Jaśniejszy cokół ma oddzielną teksturę; dane zmieniono addytywnie wyłącznie
w aliasie `furniture_footing` w `materials.py`. Nie dodano slotów prototypu.

Cztery dzienne źródła i atrybucje są w `24h/reference-selection.json`.
Zdjęcie SBS 297817221966185 nie pokazuje czytelnej rdzy; wzór zużycia w modelu
pozostaje propozycją do oceny, nie pomiarem tego konkretnego znaku.
Brak pewnego zbliżenia dokładnie tej okrągłej betonowej latarni nadal pozostaje luką.

## r1 — Detal podmurówki bez dodatkowego materiału

Obejrzany baseline potwierdził płaskie deski. Rozważono osobny materiał PBR
z połączeniem materiałów słupków i siatki. Niezależny recenzent wskazał jednak
chunk z bramą: stary materiał pozostałby potrzebny, a nowy zwiększyłby draws.
Tego wariantu nie zastosowano.

Podmurówki z `panel_fence` zachowują nazwę `concrete_plinth` i dostają dane
`COLOR_0`: B=64/255, A=128/255 to zastrzeżony znacznik; R jest fazą detalu,
G to wysokość wierzchołka ponad lokalnym gruntem +0,25 m. Ten kontrakt przetrwa
pakowanie UNorm8. Bramy i ekrany nie dostają tych danych; helpery `Lin`
i ich geometria pozostają bez zmian. Wariant z dużą ujemną współrzędną UV
odrzucono, ponieważ importer pakuje UV do Float16.

Addytywna flaga `furniture_plinth_detail` w `materials.py` uruchamia ograniczoną
ścieżkę w `WorldPbrMaterials.cs`. Używa ona tej samej fabryki World Surface,
tych samych pigmentów i tożsamości materiału; jawnie zachowuje `_GroundMasks=0`.
`Has` oraz reguły `_Tile` i `_Tint` pozostają bez zmian. Lokalny keyword
`_FURNITURE_PLINTH` w WorldSurface modyfikuje wyłącznie oznaczone fragmenty,
korzystając z istniejącego interpolatora masek. Brak nowego pasa renderowania.
Materiał z keywordem jest zapisywany w wygenerowanej scenie; test edytorowy
nie jest jednak dowodem działania na urządzeniu ani wyniku strippingu gotowego APK.

Mikrostruktura pochodzi z istniejącego `brushed_concrete` (CC0, Dario Barresi /
Dimitrios Savva; źródło i hash w LICENSES/manifest). Nowy PNG ma 256×256 i 52 958 bajtów.
Jest to modulacja o średniej 0,5 liniowo, zakodowana do sRGB; pigment mnożony raz.
Rozmiar przetworzonego kafla 1 m, pas brudu 0,25 m i siła 0,55 to WORKING_VALUE,
a nie pomiar deski ze zdjęcia. Oryginalny skan opisano w LICENSES jako 2,5×2,5 m.

Test GPU/fabryki: 7/7 passed, bez pominięć. Porównano keyword off/on na
nieoznaczonym betonie, mnożenie detalu w przestrzeni liniowej, zanik brudu,
zachowanie kanałów i czyszczenie keywordu/samplera po usunięciu flagi danych.
Koszt GPU i ocena materiału pozostają do kontroli w renderach i późniejszym
pomiarze lidera na urządzeniu. Same identyczne próbki nie dowodzą zerowego kosztu.

### r1, korekta po niezależnym przeglądzie iteracji 1

Krótkie stopnie desek na skarpie nie wyznaczają już słupków. Podpory zachowują
moduł do 2,5 m i narożniki linii, a siatka podąża za spadkiem między nimi.
Podział betonu pozostaje niezależny; deski mają zamknięte końce i małe szczeliny.
Poprzedni wymóg poziomego wierzchu siatki zastąpiono kontrolą wysokości nad
pochyłym gruntem. To usuwa przyczynę błędnego rytmu gęstych pionowych podpór.
Ocena wizualna tej korekty i końcowy budżet nadal oczekują na przebudowę/render.

### r1, iteracja 3 i przygotowana iteracja 4

Rendery iteracji 3 potwierdziły naprawę gęstych słupków. Chronione payloady
geometrii: 6833 przed i po, bez różnic. Import zapisał Low 120,0 MB i High
262,1 MB danych mesh/instancji/kolizji; nie jest to pomiar PSS urządzenia.
W 220 kombinacjach kamer delta draws mesh i instancji wynosi zero.
Konserwatywna granica tris nadal nie potwierdza limitu +2% w kilku kadrach
trasy. Pełne dane i ograniczenia są w artifacts/furniture-r1/24h/iteration3/.

Niezależny przegląd zbliżeń wykazał włóknisty odczyt betonowego trzonu.
Przygotowana iteracja 4 zachowuje źródło CC0 brushed_concrete, ale pobiera
je w skali metrycznej zamiast rozciągać kwadratowy skan przez całe 9 m.
Kafel źródłowy ma 2,5 m; obwód atlasu odpowiada średniemu obwodowi obecnego
modelu roboczego. Mniejszy kontrast ziarna i półprzezroczysty pas brudu są
WORKING_VALUE do oceny obrazów, nie pomiarem konkretnej latarni.

Druga zmiana przygotowana do iteracji 4 ogranicza podziały siatki renderowanej
za krótkimi stopniami desek. Kolizja zachowuje poprzednie stacje. Minimum
terenu sprawdzane jest także wzdłuż uproszczonego wygięcia co najwyżej 0,25 m;
na nietypowym spadku poprzecznym pozostaje poprzednia geometria. Nowa dolna
krawędź nie schodzi poniżej istniejących desek. Ostateczne granice rendererów,
cienie, wygląd i budżet wymagają ponownej kontroli po eksporcie.
