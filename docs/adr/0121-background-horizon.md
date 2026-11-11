# ADR 0121 — Tło i ciągłość horyzontu

## Runda r1 — 11 listopada 2026

Recenzja HIL wskazała brak widocznej kontynuacji jezdni w tle wschodnim i południowym. Istniejące przedłużenia mają 420 m i są częścią tej samej siatki apron, bez dodatkowych rendererów.

Audyt modelu wysokości wykazał, że ukośne przedłużenie używało profilu wysokości przy początku drogi na całej długości. Rzeczywisty apron pod dalszym odcinkiem pochodzi z innych punktów granicy. Dla południowego wyjazdu Tysiąclecia model wskazał różnicę do około 4,75 m poniżej terenu; jest to diagnoza modelowa, nie pomiar renderu ani gotowej siatki.

WorldEdgeBuilder próbkuje teraz wysokość istniejących trójkątów apron pod obiema krawędziami pasa asfaltu. Wyższa z wysokości wyznacza koronę przedłużenia. Pozostaje dotychczasowe łagodne połączenie z poziomem jezdni przy granicy. Liczba segmentów, submeshy, rendererów, materiałów i przebiegów nie zmienia się. Bariery, geometria dróg regionu i ustawienia mgły pozostają własnością innych sesji.

Pomiar bezpośrednio z zapisanej siatki Unity potwierdził minimum −4,6413 m dla południowego przedłużenia Tysiąclecia w środkach trójkątów asfaltu. Siatka bazowa ma 6000 wierzchołków i 576 trójkątów asfaltu w 24 przedłużeniach. Kontrola obejmuje wszystkie ich środki względem oryginalnych trójkątów apron, bez poboczy. Dane: `artifacts/edge-r1/mesh-clearance-before.json`.

Samo dopasowanie stacji nie wystarczyło: kontrola prototypu wykazała resztkowe zakrywanie w początkowym przejściu i przy zmianach nachylenia pomiędzy stacjami. Korona otrzymuje więc minimum 0,04 m nad podłożem (WORKING_VALUE), a segment jest sprawdzany w ośmiu odstępach na trzech śladach poprzecznych. Wymagane podniesienie obu końców zachowuje topologię. Zmieniana jest wysokość istniejących wierzchołków; kontrola odbywa się wyłącznie podczas importu. Prototyp na zapisanej siatce nie wykazał zakrywania poniżej tolerancji −0,02 m w środkach trójkątów. Jest to sprawdzenie geometrii proponowanej poprawki, nie dowód wykonania kodu C# ani ocena wizualna.

Walidacja renderów i budżetu Low jest w toku. Wynik jakości: UNVERIFIED. Ujęcie w osi DK8 jest z wysokości kabiny; nazwa lasu wymaga osobnego potwierdzenia źródłowego i widocznej sylwetki.
