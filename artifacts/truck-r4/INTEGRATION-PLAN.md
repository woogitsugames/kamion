# R4 — plan integracji prototypu, przed walidacją Blender

Priorytet po nowej recenzji lidera: P1 felgi Low (regularne otwory, rant, prześwit, kołpak), potem kolejne największe odstępstwo. Adapter kontrolek szkła jest gotowy na dalszą diagnozę, lecz nie zastępuje poprawki koła. Bazą pozostaje merge main f8b85fa2 do r4 (07bbd7c1), wykonany na początku rundy; nie zmieniać źródeł świata w połowie przygotowania.

Aktualne FBX i shadery produkcyjne pozostają bazowe. Nowe wheel_disc.py i wheel_disc_blender.py nie są jeszcze podłączone. Czysty checker potwierdza zamknięcie/topologię i syntetyczny transfer; nie dowodzi działania bpy, packera, bake, FBX ani wyglądu.

Wiring po świeżym baseline:
1. W chassis.wheel tylko przednia tarcza: make_authoring z regularnymi otworami16. Przedni kołpak rozważyć jako płaski dekiel stalowy zamiast półkuli: wysokość40 mm zamiast95, szeroka płaska część. Wartości robocze do oceny, próg pokrycia osi>150 mm musi przejść. Tył ciągnika/naczepa na razie bez tych zmian.
2. to_game_piece zachowuje pierwotne UV również przy parametric_disc_atlas. disc_parameter FLOAT_VECTOR/CORNER i disc_chart INT/FACE przetrwają reset warstw UV. Nie dodawać runtime UV kanału.
3. unwrap_atlases pomija Smart Project również dla tej flagi, dopasowuje jednolicie gęstość do pozostałego slotu. Oryginalny disc_parameter nie jest zmieniany. Packer/priority/widen mogą stosować różne afiniczne transformacje chartów, które replace_lod odtworzy i sprawdzi.
4. lod_pieces na kopii GAME front disc: replace_lod(...,8) dlaLOD2. decimate_pieces musi wyłączyć regular_disc_lod z COLLAPSE, inaczej regularne otwory znowu się rozpadną.
5. finalize_mesh usuwa disc_parameter i disc_chart przed FBX, tak jak prio. Jedna istniejąca paleta Metal, bez nowych draws/przebiegów/map.

Budżet i prześwit to nadal HIPOTEZY:
- Pełna zamknięta tarcza8 =680 tris,16 =1000. Obecny front Low ma około349 tris tarczy, więc potrzebne przesunięcie budżetu; nie podnosić limitu17900. Aktualny cel17690.
- Low usuwa _dish, co może odpowiadać jasnemu prześwitowi między tarczą a obręczą. Sprawdzić w flat; ewentualnie zachować TYLKO front dish z ciągłym UV i redukcją kolumn16. Profil przechować z kanonicznego C.wheel w metadanych, nie dublować wymiarów. reduce_round obecnie rozpoznaje tylko profil tyre/rim i musi otrzymać prawdziwy profil dish.
- Propozycja do próby, nie przyjęte ustawienia: front rim40 kolumn z profile_tol0,020; tylne zewnętrzne20 i0,020; wewnętrzne coarse0,030. Opona bez nowego resamplingu. wheel-profile-estimates.json zawiera wyłącznie wybór DP i estymaty nieprzyciętej siatki; culling/UVguards mogą zostawić więcej komórek. Natywny validator rozstrzyga.
- Regularna tarcza nie może próbkować pustych texeli High przy krawędzi otworu; obejrzeć albedo/flat i sprawdzić padding. Żadnego ślepego mapowania na sąsiednie wyspy.

Następne: przygotowanie69474 → import/baseline-captures → zdjęcia/zbliżenia i wybór kandydata → wiring → smoke rzeczywistego bpy/packera w tym samym slotowanym cyklu generowania → pełny bake ciągnika/check_export → installer i te same kamery/testy. Nie instalować częściowego eksportu. Naczepę badać osobno po największej przedniej wadzie. Końcowe EditMode/APK/GIS i REPORT/robocopy jak wcześniej, pełny GIS wyłącznie na końcu rundy.
