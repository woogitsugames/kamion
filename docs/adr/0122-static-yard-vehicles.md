# ADR 0122 — statyczne pojazdy placowe

Status: life r2, wybrany wariant C; oględziny autora zakończone, końcowy GIS w toku. Brud i realizm PARTIAL. Bez scalenia do main i bez push.

## Runda life r2 — problem i zakres

Gałąź gpt-life-r2 powstała z life r1 i dołączyła main 765145c5 do własnej gałęzi. Wyjściowy LOD1 naczepy zastępował trzy koła jednym długim blokiem na stronę. Ciągniki miały otwarte czoła kół i fasetowany obwód unoszący się nominalnie nad gruntem. Kabiny miały prosty lakier bez kontrolowanego nalotu. Nie zmieniamy rozmieszczenia, dróg, budynków, barier, profili jakości ani pojazdu gracza.

Referencje konstrukcji: Krone Tautliner, Jk20301, CC BY-SA 4.0 oraz WieltonCurtainSider, Cekay, CC0. To inne miejsca i oświetlenie; Krone ma otwartą plandekę. Pary w artifacts/life-r2/refs mają zbliżony kierunek obserwacji, nie dopasowanie GPS lub kalibrację albedo. Logo i napisów nie przenosimy do gry. Szczegóły: refs/YARD-REFERENCES.md.

## Geometria i materiał

Koło LOD1 ma sześciokątny bieżnik, zamknięte zewnętrzne czoło i felgę; jeden wierzchołek wskazuje pionowo w dół. Naczepa ma trzy oddzielne osie po obu stronach. Felgi LOD1 naczepy korzystają z istniejącego trailer_alu, więc nie powstaje nowa grupa materiałowa.

| Prototyp LOD1 | Przed | Po | Grupy przed/po |
|---|---:|---:|---:|
| Plandeka | 220 | 316 | 6/6 |
| Box | 180 | 276 | 5/5 |
| Chłodnia | 194 | 290 | 7/7 |
| Ciągnik | 254 | 286 | 7/7 |

Wszystkie hashe kolizji są zachowane; LOD0 nie ma nowej geometrii. Nominalny odstęp opony od płaszczyzny gruntu: naczepa 0,12→0 m, ciągnik około 0,0683→0 m. To wynik prototypu, nie pomiar każdej instancji na terenie. Historyczne limity pojedynczego LOD1 naczepy w test_streetscape i test_yard_wear ujednolicono odpowiednio 250→320 i 260→320 po pomiarze maksimum 316. Limit kamer trasy pozostaje draws +0 i tris najwyżej +2%.

Plandeki mają UV0 w metrach, wysokość 2,53 m i różną fazę poziomą między kolorami/stronami. Sześć trailer_curtain_* dostaje set_tile=true, dając natywne _Tile 4,8×2,7 m. Wcześniejsza hipoteza o zawijaniu starego UV 2,75 m przy kaflu 2,7 m była błędna: pierwotny materiał miał domyślne _Tile 4×4 m. Korektę i dowód zachowano w tile-baseline-proof.json; sama granica UV nie dowodziła skali runtime.

Sześć tractor_paint_* opt-in yard_paint=true używa istniejącego car_grime_clean. UV0 lakieru to lokalne (y,z) w metrach. Eksportowy adapter dodaje UV1 po podziale normalnych: wysokość od rzeczywistego dołu kabiny 1,05 m oraz (y+0,55)/3,70 względem osi. Sam adapter zachowuje V/N/T/UV0; przed nim projekcja UV0 kabiny jest celowo ujednolicona. Istniejący eksport wywołuje adapter dla każdego LOD, więc r2 nie zmienia export.py.

WorldPbrMaterials zachowuje UV1 i włącza CARPAINT tylko dla wskazanego prefiksu, bool yard_paint, właściwego zestawu i listy paint. _CarFlake.w=2 wyłącza odtwarzanie historycznego nalotu dachu osobówek. Po zbyt delikatnym obrazie B wybrano C: ilość 0,25+0,75*poziom i zanik 0,32+0,16*poziom m, WORKING_VALUE. Osobówki w=1 zachowują formuły 0,08+0,92 oraz 0,16+0,06 i dawny górny film. Cztery poziomy hasha pozostają; nie deklarujemy zmierzonego rozkładu zabrudzenia całej floty kabin. Nie zmieniono kontraktu liniowego _Tint ani nie dodano keywordu, mapy lub przebiegu. GPU/A16 nie zmierzono.

Zmiany wspólne są ograniczone do powyższych flag w materials.py, predykatu/obsługi kabin w WorldPbrMaterials.cs oraz bloku CARPAINT w WorldPBR.shader. LifeExactStats to nowy opt-in Editor QA (-qaLifeExact), bez ścieżki w playerze i bez zmiany wspólnego SceneStats/VisualQaRunner. Bez flagi nie rejestruje callbacków.

## Dowody i budżet

World B zakończył się kodem 0 po 424,7 s, bez fallback=True (86dab638). Audyt rzeczywistego GLB: 456 węzłów, 26 zmienionych, wszystkie tractor_/trailer_; poza nimi 0. Wszystkie 192 produkty raw są identyczne z bazą. Manifest ma oczekiwane zmiany definicji materiałów. Audyt 14 prototypów B potwierdza identyczne tris/grupy/kolizje jak A. C zmienia tylko shader (d47d3d72), bez ponownej generacji geometrii.

Finalne before-exact i after-c-exact mają po 456 PNG: 114 kamer × Low/High × clear/overcast; High używa WorldC_High. Bibliotekę baseline ponownie importowano z zachowanego GLB SHA c56cbe59b99b61d8cf15c605c6b0b78697c45e76af8bdaea404de7f5602d3cfd. SOURCE-MODE jawnie rejestrował tymczasowe przełączenie; źródło kandydata przywrócono w finally. Starsze A/B i odrzucone kadry zachowano, nie miesza się ich z finalną parą.

Zaokrąglone trisK początkowo wskazywały +2,0408% w r10_hall_3. Dokładne liczniki z natywnego renderu pokazały 246758→251110, +4352, czyli +1,7636713%. Każdy ze wszystkich 456 wierszy sprawdzono względem wspólnego loggera (obiekty, oba draws, instancje, komórki i obie zaokrąglone składowe tris). Sprawdzono też zamrożony hash kamer, FOV i aspect. Nie podniesiono limitu 2%.

Na 59 kamerach trasy: Low maks. +1,7636713%, High +0,3365433%; draws świata i instancji +0, bez brakujących kamer i przekroczeń. Wszystkie 114 kamer: maks. Low +2,2356205% (dodatkowy yard_trailer_reefer_0_side35), High +0,5341565%. World zachowuje frustum SceneStats po przywróceniu targetu (aspect 4:3), a instancje pochodzą z render-time. To szacunki CPU przed SRP batching, nie GPU lub telefon. Pełne liczby: exact-c-all-camera-budget.json i exact-c-budget-summary.json.

Native sprawdza sześć materiałów kabin, siedem lakierów aut, sześć plandek i 12 LOD kabin. Dane Half2 odczytano z rzeczywistych buforów po UploadMeshData(true), z maksymalnym błędem komponentu 0,0007813. Materiał tablic ma dokładnie SHA z r1: BB3C5F5C20719E5BF210C3227AB2341CEDB3A030E3DF02FA64CDAB040929574C. MotionVectors pozostaje wyłączony tak jak w r1. Pierwszy walidator błędnie wymagał true; poprawiono oczekiwanie, nie materiał, i zachowano zapis nieudanego etapu B.

Kontrola ramek osobówek A/C: 59/76 PNG identycznych bajtowo. Obejrzano wszystkie 17 różnych na pięciu arkuszach z maskami; duże obszary zmian są w tle pojazdów placowych, występują też drobne punkty przy krawędziach/połyskach. Nie stwierdzono widocznej na arkuszach regresji sylwetki/lakieru, ale nie deklarujemy identyczności każdego piksela osobówek. Źródłowe węzły GLB aut są identyczne. Metryki i lokalizacje: protected-c-pixel-audit.json.

Testy: pojedynczy test_yard_vehicle_lod 12 passed, test_streetscape 59 passed; EditMode 280/280. Pierwszy końcowy GIS: 584 passed, 1 xfailed, 1 failed w 619,59 s — drugi historyczny limit 260 w test_yard_wear nie był zsynchronizowany z opisanym limitem 320. Produkcja C pozostała bez zmian; po ujednoliceniu oczekiwania pojedynczy test_yard_wear zaliczył 8/8, a powtórny pełny GIS: 585 passed, 1 xfailed w 612,19 s. Końcowa walidacja natywna C również przeszła; SHA produkcji i biblioteki zgodne z capture.

## Ocena i przekazanie

Obejrzano komplet 56 arkuszy C (część w przeglądach ≤960 px), zbliżenia B/C i dwie pary zdjęcie/render. Największa poprawa to czytelne oddzielne koła dalszego LOD Low. Brud jest nadal delikatny; felgi pozostają płaskie, bryły i szkło kabin uproszczone, ciemne plandeki tracą detal. Ocena autora: geometria poprawiona, brud/realizm PARTIAL. Niezależną recenzję i pomiar urządzenia zleca lider Claude S11; autor nie scala do main, nie pushuje i nie używa telefonu.

Przewidywane konflikty: definicje wskazanych materiałów, CARPAINT, fabryka materiałów, biblioteka props i manifest. Zachować inne domeny; generaty przy integracji main wybrać z main i odtworzyć ze złączonych źródeł zgodnie z protokołem. Aktualne uwagi lidera s11 w GPT-FEEDBACK-S10 (~01:50) po scaleniu life r1 0978792e dopisują brud tyłu osobówek, felgi, czerń w słońcu i sheet_far. Zostaną uwzględnione w następnej r3 po dołączeniu aktualnego main do własnej gałęzi. Preflight palet i brak deklarowanego zestawu euro_pallet_side zachowano do dalszego backlogu; palet w r2 nie zmieniano, a brak zestawu PBR sam nie dowodzi braku BaseMap lub wyglądu na renderze.



