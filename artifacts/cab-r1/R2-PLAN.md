# Kolejna runda kabiny

Po końcowym GIS i skopiowaniu raportu: gałąź gpt-cab-r2 od r1, następnie merge main w tym samym worktree. Zachować założenia lusterek oraz oddzielne statystyki instancji. Nie zmieniać szyb ani shaderów zewnętrza.

Najpierw poprawić sprzątanie diagnostyki powierzchni: przywrócić referencje oryginalnych siatek przed niszczeniem tymczasowych kopii. Audyt High clear zakończył renderowanie, lecz zawiesił się przy zamykaniu D3D12. Stos nie dowodzi, że przyczyną były kopie siatek; nie ukrywać exit 1.

Skóra: Brown Leather, Rob Tuytel, Poly Haven, CC0, pole 40 × 40 cm. Fabric Leather 02 ma duży rzeczywisty szew i zagniecenia, więc nie nadaje się jako ziarno nakładane na wszystkie części. Nie traktować żadnej skóry jako zeskanowanego tworzywa. Źródła, rozmiary i MD5 są w cc0-prep/downloads.json. Materiały Plastic001/003/005/006/010/013A z ambientCG opisano jako approximation/procedural; nie spełniają wymagania skanów.

Zachować dotychczasowe rozmiary gotowych map na Low i istniejący kontrakt Detail RGBA oraz normal OpenGL. Przed integracją ustalić skalę fizyczną: obecny detal skóry jest wypieczony w UV dla 12 cm, na kierownicy dla 5 cm; deska 10 cm. Pełny skan 40 cm na obecnym kaflu 12 cm zmniejszyłby ziarno ponad trzykrotnie. Obróbkę wielu map i eksport Blender obejmować heavy, z nazwą gpt-cab-r2.

K4: kontrolowane warianty roughness, wear, tint, AO i detail-off oraz pomiary rzeczywistego FBX nie wskazują szerokiego rozciągnięcia UV. Sprawdzić ciągłość AO, wierzchołkowe strefy polerowania oraz rzeczywisty odczyt detalu po mipach. Nie przebudowywać wszystkich UV bez wskazania konkretnego wadliwego fragmentu.

K5: brak przecięć źródłowych powierzchni nie jest testem zawierania brył ani FBX. Ocenić pozę i prześwit w grze. Nie przesuwać samej tapicerki drzwi, zostawiając osprzęt i szwy w dawnym położeniu.

K6: zużycie ograniczyć do kontaktu dłoni i ciała oraz kurzu w zagłębieniach. Bez globalnego szumu. Porównywać punkt oka Low i High w dwóch stanach światła, z materiałem bazowym i po zmianie. Pełny GIS dopiero przy końcu r2.
