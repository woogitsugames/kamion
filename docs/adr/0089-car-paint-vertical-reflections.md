# ADR 0089: parked-car paint, wheels, deposition and plate variation

Status: bounded R4 repair selected after independent ROOT/E visual review; dust realism PARTIAL. Historical R3 visual acceptance is withdrawn, not a calibration reference.

Keep the earlier causal Pearl Color-property upload correction, neutral tyres/rims and 22-segment existing LOD0 wheels. No pigment/exposure lift, fourth runtime LOD or unrelated quality reduction.

Export affine signed height above the actual class sill and longitudinal axle coordinate in UV1 after normal splitting. All 81 car LOD meshes keep positions/normals/indices/UV0/groups; native stride 20 to 24 adds an estimated 584576 payload bytes, not total allocation, including nonpaint vertices sharing each stream.

Use bounded broad wheel/rear weights and exponential height decay in CARPAINT. Minimal dust at level 0; deterministic GI-relative float32 origin hash selects 10/35/35/20 levels. No detached height envelope, inverse legacy-film division, new geometry or texture sample. Deposition colour, falloff and opacity are WORKING_VALUE rather than measured albedo.

Only seven active paint materials use car_grime_clean. Preserve legacy calibration and wrap gutter; Mask.R carries removed legacy-film coverage for forward upper-role restoration, with smoothness subtraction. Green/beige stay legacy; actual metallic override remains separate. Initial un-restored bonnet +14.543% was rejected before import.

Reuse the existing plate atlas with 27 eligible cells. Add exact local plate UV1 corners to 54 LOD0/1 primitives inside the already-present stream, with unchanged UV0 fallback. One shared URP Lit forward vertex wrapper retains original fragment and auxiliary passes; no new texture, material instance or draw split. LOD2 has no plate.

Enable the local vertex keyword only after fresh-library and actual native indexed-corner validation. Reject old/mixed payloads and unsupported pipeline eligibility; shader lightmap or invalid-GI paths keep UV0. GI validity uses texel size, independently of visibility strength. No whole-fleet uniqueness claim.

Preserve LightMode-tag pass state around exact car_plate factory switches. The inherited Lit CustomEditor rewrote unknown-shader MotionVectors on load; remove that generated-only inspector association. Persisted replay proves disabled motion, Opaque queue 2000 and existing texture/ST/roughness.

Final 368 CPU records are unchanged; source adds ALU and data, not a measured GPU-time saving. Scene dependency texture union is 7 versus counterfactual R3 4: +170368 ASTC mip payload bytes; desktop Profiler delta +1813016 includes overhead. A16 residency/timing remain UNVERIFIED. Evidence and limitations: artifacts/car-paint-r1/REPORT.md, SELF-CRITICISM.md, r4-final-validation.json, r4-plate-native-parity.json and GPU proofs. Preserve canonical fixtures/pose packets; shared shader/material/importer integration requires a bounded union and canonical regeneration.
## Sesja life, r1 — 24 godziny od 11 listopada 2026

Gałąź gpt-life-r1 powstała z main 5f2aa277 w osobnym worktree gpt-life. Z gpt-car-paint przeniesiono selektywnie wyłącznie naprawy osobówek R4 i ich niezbędne zależności: kanał UV1 eksportera/importera, lokalny shader tablic, opt-in materiałów i wariant car_grime_clean. Bieżące zmiany dróg, budynków, mebli i generatów z main zachowano. Nie scala się całej starszej gałęzi z dokumentami innych strumieni.

Nowe dowody powstają w artifacts/life-r1; historyczne 368 par i testy R4 nie są nowymi wynikami tej gałęzi. Wykonano kanoniczny baseline przez regenerację źródeł main 5f2aa277, import i 92 kamery w czterech warunkach; skopiowane wcześniej sceny zachowano tylko jako main-cache-before, bez użycia do budżetu. Następnie przywrócono źródła kandydata, ponowiono generator i import oraz wykonano 368 świeżych renderów AFTER. High używa WorldC_High. Wszystkie wywołania Unity są chronione slotem gpt-life, a ciężkie zadania po wprowadzeniu reguły heavy — slotem gpt-life-r1. Nowe wyniki: testy ukierunkowane 50 passed, EditMode 274/274 passed; końcowy GIS 543 passed, 1 xfailed (718,81 s), exit 0. Manifest przed i po teście identyczny; siedem źródeł i produktów nadal zgodnych z dowodem importu. We wszystkich 368 rekordach CPU SceneStats maksymalna delta draws i łącznych trójkątów wynosi 0; brak przekroczeń w 59 kontrolach trasy na warunek. Obejrzano 28 plansz autora: brak dawnych oderwanych plam na drzwiach, realizm kurzu częściowy. Niezależny odbiór należy do integratora.

Ograniczenia przejęte z recenzji: subtelny i gładki kurz nie jest jeszcze pełnym odwzorowaniem zdjęcia; czerń w clear i płaskie felgi pozostają do oceny. Nie deklaruje się unikalności tablic całej floty ani pomiaru kosztu GPU na A16. Nie zmienia się ekspozycji, profili jakości ani skali renderowania.
## Sesja life, r3 — ponowna ocena osobówek po recenzji S11

Gałąź gpt-life-r3 powstała z life-r2, następnie dołączono main 14ccbaf1 do własnej gałęzi (ee348bf2). Jedyny integrator main pozostaje lider Claude, kontynuujący po restarcie komputera jako S12. Nowe uwagi to czytelny brud tyłu, fazy felg, czerń w clear i sheet_far. Palety pozostają dalszym backlogiem, nie wykonanym zakresem r3.

Baseline odtworzono ze złączonych źródeł: materiały 519 s, World 552,1 s; 192 produkty raw zgodne, 15 zasobów Fab/Megascans i 151 map Medium, brak fallback=True. Natywny import Low/High poprzedził cztery serie po 123 kamery (492 PNG), w tym 59 kamer trasy. Dziewięć dodatkowych kadrów pochodzi z rzeczywistych instancji: tył/bok/koło czarnego hatchbacka i białego kombi oraz rząd 22 aut z 20/35/45 m. Przybliżone nazwy rear5/side5/wheel2 oznaczają odległości do celu 5,6703/6,0252/2,3569 m. Widok tyłu czarnego auta częściowo zachodzi na vana; słup częściowo przecina kadr floty z 45 m. Nie zmieniono rozmieszczenia świata.

LifeExactStats, nadal opt-in Editor QA bez player path, zapisuje rzeczywistą pozycję/rotację i projekcję kamer. Porównanie r3 wymaga równości pozy i każdego legacy licznika. Inwentarz oczekiwanych kamer to suma ControlCamera w natywnych scenach i dodatkowego packet; nie sztywna historyczna liczba 114.

### Wariant A — geometria i zanik osadu

Kod 846c446e. Cienkie ramiona felgi dostają dwa czoła, a grzbiety szerokich ramion wyraźniejszy przekrój. Globalny crease_normals pozostaje 38°. Nowy test w rzeczywistym eksporcie potwierdza dwa kierunki normalnych ramion pięciu stylów po obu stronach auta (10/10). Nie dodano grup materiałów ani nie zmieniono globalnych rim/tyre.

W CARPAINT osobówek falloff z 0,16+0,06*level jest poszerzany o deposition*(0,12+0,12*level)+rearFace*0,10*(0,25+0,75*level), WORKING_VALUE. Zachowuje monotoniczny zanik od rzeczywistego progu, kolor beżowo-szary, ograniczenie opacity 0,5, affine UV1 i rozkład 10/35/35/20. Bez nowej próbki, keywordu czy przebiegu. Statyczne kabiny w=2 zachowują C z r2.

World A: 503,8 s, brak fallbacków. Rzeczywisty GLB: 471 węzłów, zmienione 22, wyłącznie podsiatki rim/rim_dark/rim_dusty aut; 0 poza osobówkami, 0 zmian kolizji/contact, wszystkie 192 raw identyczne z nową bazą. Łączna zmiana biblioteki +960 tris; nie jest to koszt jednej klatki. Pojedyncze testy: fazy 10, cars_r9 5, cars_r11 5, deposition 17, plate payload 27 — wszystkie passed. Pełny GIS i EditMode dopiero po końcowym wyborze wariantu.

Po świeżym imporcie A wykonano 492 PNG. Trasa: maks. Low +0,067613% tris, High +0,155216%; wszystkie 123 kamery: Low +0,323992%, High +0,164056%. WorldDraws i instanceDraws osobno +0, brak brakujących kamer i przekroczeń. To dokładne liczby istniejącego szacunku CPU przed SRP batching; world-frustum po przywróceniu targetu i instancje podczas renderowania, nie GPU counters.

Diagnostyka Direct3D12 adaptuje kopię rzeczywistego WorldPBR oraz natywne siatki/macierze do liczbowego float RT: 1005 instancji, CPU/GPU 99/366/331/209 poziomów, błąd poziomu 0; 81 LOD lakieru, maks. błąd opacity 0,00004215, wysokości 0,00091553 i współrzędnej osi 0,00064707. Oba nowe cele black/white mają GPU poziom 2. Materiał tablic zachował SHA. To dowód danych/obwiedni GPU edytora, bez pomiaru czasu lub urządzenia.

Obejrzano cztery siatki dziewięciu kadrów, pełne podglądy kół/tyłu i komplet 68 stron before/A w dwunastu przeglądach do 960 px. Fazy są czytelniejsze; brud tyłu poziomu 2 nadal subtelny i jakość PARTIAL. Miniatury całości służą kontroli regresji, nie ocenie drobnego detalu. Referencje i ograniczenia pogody/licencji: artifacts/life-r3/refs/REFERENCES.md. Nie deklaruje się dopasowania zimowej fotometrii do zdjęcia z błyskiem ani unikalności wszystkich tablic.

### Próba B — czarny lakier, w toku

Nowe ręcznie obejrzane ROI drzwi/asfalt life3_black_side5: baseline clear 0,9703 Low / 0,9769 High; A 0,9889 / 0,9954. Dla baseline overcast 0,7252 / 0,7433, A 0,7450 / 0,7618. To display-encoded RGB, inne kadry/ROI niż zamknięty dawny cel drzwi 30–40; bez deklaracji regresji tamtego ROI. Osad A rozjaśnia dół ciemnego auta, więc czystą warstwę i pył należy oceniać osobno.

B (5fb5f28b) dodaje tylko opt-in flake_lift=0,025 do car_paint_black i odczyt przez WorldPbrMaterials dla car_paint_, clamp 0…0,08, default 0,08. Dotychczasowy _CarFlake.z steruje podbiciem odbicia płatków; nie jest to całość F0. Pigment, Pearl, roughness, shader A i pozostałe lakiery/kabiny pozostają bez zmian. Walidator po imporcie wymaga 28 materiałów bez zmian poza jednym polem czerni. B nie jest jeszcze przyjęty: generator wstrzymany przez watchdog, następnie wymagane import, 492 kadry i te same ROI/RGB. A16 i niezależny odbiór pozostają UNVERIFIED, wykonuje lider.
