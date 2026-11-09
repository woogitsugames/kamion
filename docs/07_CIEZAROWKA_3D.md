# 07 — Ciężarówka premium (model 3D wykonywany przez agentów)

Decyzja właściciela: **agenci modelują ciężarówkę sami** (Blender), budżet 0 zł. Właściciel ma dobre doświadczenia z jakością modeli tworzonych przez Opus w innych grach. Cel: model na poziomie, który wytrzyma kamerę w kabinie z bliska i zewnętrzne zbliżenia na flagowcu.

## 1. Specyfikacja pojazdu
- Nowoczesny europejski ciągnik siodłowy **4×2, kabina nad silnikiem (cab-over), wysoka kabina sypialna**, klasa long-haul.
- **Własna fikcyjna marka** — nazwa, logo, język stylistyczny do zaproponowania (3 warianty, wybór właściciela). Oryginalne wzornictwo: nie kopiujemy charakterystycznych kształtów grilla, świateł ani kabiny konkretnego producenta (Scania, Volvo, DAF, MAN, Mercedes-Benz, Iveco, Renault). Inspiracja klasą pojazdu, nie modelem.
- Gabaryty, rozstaw osi, wysokość siodła, rozmiary opon, pozycja oczu kierowcy — **z realnych danych klasy pojazdu** (źródła w `docs/VEHICLE_REFERENCE_DATA.md`) i zgodne z przepisami (wysokość ≤ 4 m, szerokość 2,55 m itd. — zweryfikuj).
- Naczepa: 3-osiowa firankowa 13,6 m (później kolejne typy jako dane).

## 2. Pipeline (skill `blender-hero-asset`)
Każdy krok kończy się **renderem kontrolnym** (stałe kamery, studio + plener HDRI), obejrzanym przez autora i agenta `visual-critic`.

1. **Brief i referencje**: tablica referencyjna (zdjęcia właściciela z parkingu/MOP — lista ujęć poniżej; publiczne zdjęcia tylko jako referencja, nie tekstury), rzuty wymiarowe z danych.
2. **3 koncepcje sylwetki** (szybkie bryły z charakterystycznym frontem, światłami, proporcjami) → wybór właściciela.
3. **Blockout w skali** z poprawną kabiną, rozstawem osi, kołami, siodłem, pozycją oczu kierowcy; test widoczności z kabiny i w lusterkach (już w Unity).
4. **High-poly zewnętrze**: modelowanie twarde (hard-surface) z kontrolowanymi bevelami, szczeliny paneli, uszczelki, klamki, stopnie, osłony, lusterka z ramionami, wycieraczki, reflektory z wewnętrzną strukturą (odbłyśniki, soczewki, LED-y DRL), lampy tylne, zderzak, grill z siatką, osłony boczne, zbiorniki paliwa i AdBlue, skrzynka akumulatorów, rama, osie, miechy, amortyzatory, wał, zbiorniki powietrza, przewody pneumatyczne i elektryczne do naczepy (spirale), błotniki, koła z bieżnikiem i oznaczeniami opon (fikcyjna marka opon).
5. **High-poly kabina**: deska rozdzielcza z panelami i przełącznikami, zestaw wskaźników (cyfrowy + elementy analogowe), ekran multimedialny/nawigacji, kierownica z przyciskami, dźwignie (kierunkowskazy, retarder, wycieraczki), pedały, fotel kierowcy i pasażera z szwami, pasy, kanapa/leżanka, schowki, półki, nawiewy, podsufitka, rolety, uchwyty, lusterko wsteczne, szyby z ramami, słupki A z głośnikami. Ergonomia zgodna z realną pozycją kierowcy.
6. **Low-poly + UV + bake**: retopologia (game-ready), UV bez rozciągania, spójny texel density (ADR), bake normal/AO/curvature z high-poly, osobne zestawy tekstur dla kabiny (najwyższa gęstość), zewnętrza, podwozia, kół.
7. **Materiały PBR**: lakier z warstwą bezbarwną (uproszczoną w URP), chrom/aluminium, tworzywa teksturowane, guma, szkło, tkaniny, skóra, ekrany emisyjne sterowane z gry. Zużycie: kurz w zagłębieniach, błoto na progach i błotnikach, ślady na stopniach, wytarcia na kierownicy — sterowane parametrem „brud” z gry.
8. **Rig i elementy ruchome**: koła, zwrotnice, kierownica, pedały, wycieraczki, drzwi, lusterka (regulacja), wskazówki/ekrany, światła (grupy emisji + światła Unity), kabina na zawieszeniu (pivot), zawieszenie osi, nogi naczepy, siodło.
9. **LOD0–LOD3 + impostor dla ruchu AI**, proste kolizje, punkty: oczy kierowcy, kamery, siodło, osie, światła, emitery dźwięku.
10. **Eksport** (FBX lub glTF — ADR), import do Unity skryptem, prefab generowany, walidator (skala, osie, pivoty, nazwy, materiały, liczba trójkątów, texel density).

**Unity (A7):** prefab TRAKT budowany kodem z manifestów (`Kamion/Setup/Rebuild TRAKT truck`, `TruckAssetBuilder`), hierarchia z
`rig_parent`, koła/kabina/kierownica sterowane stanem solvera, tiery High/Medium/Low = LOD i atlasy z manifestu. Szczegóły, pomiary
i otwarte punkty: `docs/reports/visual/truck-A7/README.md`.

## 3. Budżety (hipotezy — ratyfikuj na telefonie)
- Zewnętrze LOD0: 120–250 tys. trójkątów (kamera zewnętrzna, flagowiec); LOD0 Medium dla Samsunga A osobno, jeśli trzeba.
- Kabina (widok FPP): osobny budżet, wnętrze niewidoczne z zewnątrz w niskim LOD.
- Tekstury: dobrane do texel density, ASTC, nie „wszystko 4K”; kabina z najwyższą gęstością.
- Draw calle: łączenie materiałów/atlasy, bez rozdrobnienia.

## 4. Zdjęcia referencyjne do zrobienia przez właściciela (darmowe, kluczowe)
Dowolna nowoczesna ciężarówka (bez fotografowania tablic/osób, logo i tak nie przenosimy): przód, tył, oba boki, ¾ z czterech rogów, podwozie z boku (rama, zbiorniki, osie), siodło z góry, koło z bliska (bieżnik, felga), lampy z bliska, lusterka, stopnie i drzwi; **kabina**: widok z fotela kierowcy, deska z bliska (sekcjami), kierownica, dźwignie, pedały, fotel, leżanka, podsufitka, widok w lusterkach z fotela. Najlepiej w pochmurny dzień.

## 5. Zakazy
- Żadnych logo, nazw i charakterystycznych elementów prawdziwych marek ciężarówek i opon.
- Żadnych modeli/tekstur z niejasnym pochodzeniem („free model z internetu”).
- Obraz z generatora 2D nie jest modelem 3D; generatory 3D (jeśli użyte) tylko jako punkt wyjścia do pełnej retopologii i przebudowy, nigdy jako finalna siatka.

## 6. Checklista „quality-ready”
Wymiary i proporcje zweryfikowane · brak błędów normalnych, UV, prześwitów, pustych przestrzeni · każdy istotny element ma właściwy materiał · kabina w pełni jezdna z FPP (wskaźniki działają z fizyki: obroty, prędkość, bieg, ciśnienia, paliwo, kontrolki) · lusterka użyteczne · światła i ich grupy działają · LOD-y bez widocznego przeskoku · zrzuty z telefonu (Samsung A Medium) i z edytora (High) w raporcie · `visual-critic` PASS · akceptacja właściciela · budżet spełniony.
