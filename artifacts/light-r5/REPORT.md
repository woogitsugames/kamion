Gałąź gpt-light-r5; stan dowodów 6c0fb71c79c055990522d3a4890b21c8c3a9becd, baza main 889201d5 (merge 8a76b69b).
Runda diagnostyczna spójności tonów Low/High: natywna kostka High URP 32³ w RGBAHalf, domena LogC, bez bindera runtime i domyślnego włączenia.
Wykryto ograniczenie dotychczasowego QA: High mimo HDR=true zapisuje kolor R8 sRGB już przed post. Jawna referencja HDR zachowuje R16 half-float przed post przy końcowym ARGB32; telefonu nie badano.
Czysty bake v6: 65 PNG, pięć presetów; 192 pola testowe na preset, maksimum błędu 1 poziom RGB; rampy po 12288 próbek, maksima 3/2/3/3/3. Pięć kostek po 256 KiB, fizyczny capture bez różnic.
Pierwsza racjonalna LUT miała błąd zieleni do 14/15 poziomów; natywna usuwa duże odchylenie. Białe chmury odrzuconej v3 naprawiono przez zachowanie tego samego ograniczenia jasności nieba co High.
Nieudany shader_feature v6 oraz obserwator v4/v5 z wyjątkiem inicjalizacji pozostają odrzuconą diagnostyką. Końcowy native v6 jest czysty; 65/65 PNG jest identycznych z wcześniej obejrzanymi.
Final-native-v2: 654 PNG, 109 kamer × 3 presety × 2 tiery, wszystkie obejrzane przez rodzica i krytyka. Pierwszy final z 402 PNG odrzucono; poprawiona specyfikacja wymaga 109 kamer na zadanie.
Budżet wszystkich 327 Low: draws/tris +0, instancing osobno. W 36 parach statycznych kostek z ablacji mip0 średnia i maksimum różnicy RGB wynoszą 0; nie rozszerzamy tego na niezmierzony capture całej trasy.
W ablacji 12 kamer błąd całych klatek wobec HDR maleje w 34/36; Overcast cab-dash 4,731→5,648 i cab-driver 6,694→9,245 pozostają regresjami. Różnią się tiery, geometria, skala i alpha; to nie fotometryczne kryterium akceptacji.
Dodatkowe 24 ręczne ROI zawężają problem Overcast: deska i kierownica poprawiają zgodność, badane obszary za szybą pogarszają. To nie dowód wyłącznej winy szkła; szczegóły w cab-roi-comparison.json i niezależnej recenzji.
Pary foto|render: reference-day (4) i reference-night (6), po 956 px; hasze i licencje w sources.json. Inne warunki, miejsca i pory, bez zaliczenia pozy lub fotometrii.
Pełny EditMode 341/341; końcowy GIS: 690 passed / 1 xfailed w 865.12 s, kod 0. Ciężki Python tylko przez heavy; pełny GIS wyłącznie na końcu rundy.
Pozostają: gładkie chmury Overcast Low, szkło i instrumenty, płaski detal białych aut, nierówny Night, ciemne doki/okna i brak halo. Brak GPU/A16, runtime i pełnego Night/wholeframe PASS.
Konflikty możliwe w KamionAtmosphere.hlsl, Sky.shader, EnvironmentLighting, LightQaBatch i ADR 0108. Pliki Cab, Truck, Vegetation, WorldPBR, WorldSurface oraz Claude bez edycji w tej rundzie.
Własne efekty generatora zachowano w patch i GLB, następnie przywrócono. Odtworzenie wymaga generatora/fidelity/importu w slotach; artefakty dostarczone do main bez merge/push.
Następna runda: izolacja przyczyny Overcast i kandydat native grade runtime domyślnie OFF według NEXT-ROUND-CANDIDATE.md; najpierw nowa gałąź z poprzedniej i merge aktualnego main.
