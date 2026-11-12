# Raport furniture r1 — ADR 0120
Gałąź gpt-furniture-r1; zweryfikowany kod i zasoby: 7adbe982. Baza: 5f2aa277; końcowy commit raportu wskazuje historia gałęzi.
Obniżono podmurówkę względem terenu, dodano zamknięte deski, fugi, skan CC0 i osad. Słupki zachowują moduł do 2,5 m; siatka ma małe odkształcenia.
Betonowy słup ma większą zbieżność i skan w skali metrycznej; oprawa ścięte narożniki. Tył znaku otrzymał poprawione UV i miejscowe zacieki pod mocowaniami.
Dowody: [40 arkuszy przed/po](24h/compare/) obejmuje 220 par Low/High, clear/overcast. [Referencja i render](24h/reference-sign-after.jpg) oraz [zbliżenia](24h/after4-detail.jpg) mają do 960 px.
Niezależny przegląd 40/40 arkuszy nie wykazał nowej istotnej regresji furniture; pełna [ocena](24h/iteration4/REVIEW.md) zachowuje ograniczenia.
We wszystkich 220 wariantach CPU DrawEst mesh +0, instancji osobno +0. To estymacje, nie czas GPU ani rzeczywiste wywołania GPU.
Low: 102/110 wariantów ma udowodnioną górną granicę tris ≤+2%; driver ≤1,68194%, route ≤1,70853%, abeam ≤1,60041%, w obu oświetleniach.
Niepotwierdzone: above ≤2,10065%, edge-east ≤2,67349%, north ≤3,10753%, west ≤3,01395%, po dwa oświetlenia. [Wszystkie liczniki](24h/frame-budget.csv), [dokładne Low](24h/exact-after4/) i [metoda](24h/PACKET.md) są zachowane.
Chroniona geometria: 6833→6833, 0 różnic; kolizje ogrodzeń 80→80, 0 różnic wyłącznie dla optymalizacji iteracja 3→4.
Import mesh/instancji/kolizji: Low 117,0→120,0 MB, High 259,1→262,1 MB; nie PSS. Generator: 64 chunki, bez fallback=True.
Własne testy Python 17/17 i 9/9; FurniturePlinthTests 7/7. Końcowy EditMode 268/268, bez pominięć.
Pełny GIS na końcu rundy: 509 passed, 1 xfailed, 1 failed — zastany fidelity_qa.json nie odpowiada 7 hashom niezmienionych wejść dróg/overrides. Audyt i logi w [pakiecie](24h/PACKET.md).
Physics/gate3: 47 passed, 1 failed — znana niezgodność top_speed_flat_comb.json; test, generator i scenariusz niezmienione od bazy. Nie poprawiano cudzych źródeł ani tolerancji.
Otwarte: ostry cokół/styk z gruntem, aliasing siatki Low, niepotwierdzony lokalnym zbliżeniem typ latarni i ukośny sztywny panel. Brak pomiarów telefonu/GPU/PSS, ruchu i nocnego odblasku.
Wspólne pliki: materials.py, WorldPbrMaterials.cs, WorldSurface.shader — addytywna flaga furniture_plinth_detail i lokalny keyword; bez nowego przebiegu, QualityProfile i zmian kontraktów _Tint/_Tile.
Lider: scalać wyłącznie do własnej gałęzi integracyjnej; zachować unie flag w trzech wspólnych plikach, po połączeniu zmian regenerować produkty świata. Ta sesja nie scala do main i nie pushuje.
Pełne źródła, ograniczenia, wyniki i instrukcje odtworzenia: [PACKET.md](24h/PACKET.md). Stary raport ADR 0102 zachowano w legacy-0102/.
