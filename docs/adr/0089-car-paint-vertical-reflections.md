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

Wybrano C, wygląd PARTIAL; końcowy GIS jeszcze nieodebrany. R3 zawiera fazy felg A, opt-in odbicia czerni B i poszerzony osad tyłu C. Eksperyment D odrzucono po oględzinach; nie jest częścią wybranego shadera. Kanoniczne pary: artifacts/life-r3/before i after-c.

Gałąź gpt-life-r3 dołączyła main 14ccbaf1 tylko do własnej gałęzi (ee348bf2), zachowując life-r2. Lider Claude jest jedynym integratorem main, po restarcie komputera kontynuuje jako S12. Nowe uwagi do osobówek: brud tyłu, fazy felg, czerń w clear, sheet_far. Nie zmieniono rozmieszczenia, dróg, budynków, świateł, jakości ani pojazdu gracza.

### Baseline i zakres geometryczny

Kanoniczny baseline odtworzono ze złączonych źródeł: materiały 519 s, World 552,1 s, bez fallback=True. Wszystkie 192 raw zgodne z manifestem, 15 zasobów Fab/Megascans i 151 przygotowanych map. Świeży import Low/High i po 123 kamery w czterech warunkach dały 492 PNG. Dziewięć nowych kadrów obejmuje tył/bok/koło rzeczywistego czarnego hatchbacka i białego kombi oraz rząd 22 aut z 20/35/45 m. Odległość do celu rear5/side5/wheel2 wynosi rzeczywiście 5,6703/6,0252/2,3569 m. Czarny tył częściowo zachodzi na vana; kadr 45 m przecina słup. Kamery oglądano po imporcie, bez przestawiania świata.

LifeExactStats pozostaje opt-in Editor QA, bez player path. Zapisuje też rzeczywistą pozycję, rotację i projekcję kamer; porównanie wymaga ich równości oraz każdego legacy licznika. Inwentarz jest sumą ControlCamera w scenach i dodatkowego packet. Wszystkie 59 kontroli trasy pozostają w każdym warunku; High używa WorldC_High.

A (846c446e) zmienia tylko koła LOD0: cienkie ramiona felgi dostają dwa czoła, szerokie wyraźniejszy grzbiet. Globalny crease_normals pozostaje 38°, bez zmian opony, piasty, kontaktu, kolizji lub globalnych materiałów rim. Test pięciu stylów po obu stronach po rzeczywistym eksporcie potwierdza odrębne normalne (10/10). Wszystkie 81 siatek aut: grupy bez zmian, LOD0 max 4170, LOD1 max 854, LOD2 max 90. Dotychczasowe limity 4200/900/96 bez zmiany. Biblioteka aut ma łącznie +960 tris, nie jest to koszt klatki.

GLB baseline/A: 471 węzłów, 22 zmienione wyłącznie w rim/rim_dark/rim_dusty aut. B/C: 30 zmienionych węzłów, dodatkowo wyłącznie extras.flake_lift czarnego lakieru, bez zmiany pozostałych danych tej podsiatki. Zero zmian poza osobówkami, w kolizjach/contact i we wszystkich 192 raw. Nie doszedł nowy materiał, keyword, przebieg lub mapa.

### Lakier i wybrany osad C

B (5fb5f28b) dodaje flake_lift=0,025 tylko car_paint_black. WorldPbrMaterials czyta flagę wyłącznie dla car_paint_, clamp 0…0,08 i default 0,08 zachowują pozostałe kolory oraz kabiny. Steruje istniejącym _CarFlake.z, dodatkowym podbiciem odbicia płatków; nie jest to całe F0. Pigment, Pearl, roughness bez zmian. Natywny audyt 28 materiałów potwierdza dokładnie jedno zmienione pole czerni 0,08→0,025; pozostała część pliku czerni i wszystkie inne materiały identyczne.

C (9c7c8c53) zachowuje rozkład 10/35/35/20, affine UV1 i monotoniczny zanik od rzeczywistego progu. W gałęzi osobówek, dla level 0…1, do falloff 0,16+0,06*level dodaje deposition*(0,12+0,12*level)+rearFace*0,10*(0,25+0,75*level)+rearFace*(0,18+0,18*level). Amount=saturate(0,08+0,92*level+rearFace*0,16*(0,25+0,75*level)); dotychczasowy mnożnik 0,5 ogranicza opacity. Kolor beżowo-szary i dawne odtwarzanie górnych powierzchni pozostają. WORKING_VALUE, bez nowej próbki tekstury. Statyczne w=2 zachowuje C placowe z r2.

D rozdzielało maskę ochrony dachu od odtwarzania dawnych górnych powierzchni, żeby dopuścić osad na pochylonej klapie. Wszystkie jego capture i GPU przeszły, lecz różnice tyłu względem C były mało czytelne; hipotezy nie ogłaszamy rozwiązaniem. Przywrócono dokładne bajty shadera C z gita (SHA jak after-c), odrzucone D zachowano osobno. Przejściowy CRLF po git restore zatrzymał strażnik przed testami; usunięto wyłącznie różnicę końców linii i ponownie potwierdzono siedem SHA/GLB.

Nowe, ręcznie obejrzane ROI life3_black_side5 mierzą display-encoded RGB, nie albedo: baseline drzwi/asfalt clear 0,9703 Low / 0,9769 High; C 0,9236 / 0,9308. Overcast baseline 0,7252 / 0,7433, C 0,6706 / 0,6902. W C drzwi clear 84,97 / 90,85, overcast 39,81 / 44,71 sRGB. Barwa pozostaje neutralna; cel clear 0,4–0,7 nadal niespełniony. To inne ROI i kadr niż dawny zamknięty cel 30–40; nie przenosi się między nimi wniosku o regresji.

### Dowody i ograniczenia

Wybrany C: wszystkie 492 rekordy liczbowe/PNG, identyczne pozy. Trasa max Low +0,067613% tris, High +0,155216%; wszystkie 123 kamery max Low +0,323992%, High +0,164056%. WorldDraws i instanceDraws osobno +0, bez braków i przekroczeń. Dokładne CPU-estymaty przed SRP batching: world-frustum po przywróceniu targetu, instancje z render-time; nie GPU counters. Pełny zestaw: c-all-camera-budget.json i c-budget-summary.json.

Nowy proof GPU C (Direct3D12) adaptuje kopię rzeczywistego shadera i natywne siatki/macierze do liczbowego float RT: 1005 instancji, CPU/GPU 99/366/331/209 poziomów i błąd poziomu 0; 81 LOD lakieru, maks. błąd opacity 0,00004215, wysokości 0,00091553, osi 0,00064707. Oba główne cele black/white mają potwierdzony GPU poziom 2. SHA tablic bez zmiany. Nie jest to dowód oświetlenia, czasu GPU ani A16; dodatkowy koszt ALU niezmierzony na telefonie.

Obejrzano komplet 164 stron before/C w 28 przeglądach do 960 px, nowe siatki w czterech warunkach, pełne podglądy kół/tyłu i dwie pary zdjęcie/render. Przeglądy służą kontroli szerokiego kontekstu; drobny detal oceniano osobno. Felgi czytelniejsze, czerń częściowo poprawiona; brud nadal gładki i za delikatny, szczególnie na tylnej klapie. Nie deklarujemy fotorealizmu ani unikalności wszystkich tablic. Referencje mają inne miejsce, model, obiektyw i pogodę; brak kalibracji listopadowego overcast. Licencje/ograniczenia: refs/REFERENCES.md; pary refs/sbs-black-c.jpg i refs/sbs-tail-c.jpg.

Pojedyncze pliki testów A/B: 10 faz, 5 cars_r9, 5 cars_r11, 17 deposition, 27 plate payload — passed. Końcowy EditMode C 323/323, brak skipped; ustawienia przywrócone, źródła i natywne materiały ponownie sprawdzone. Końcowy pełny GIS trwa, widoczna jedna porażka; wynik i przyczyna muszą zostać uzupełnione przed REPORT. Wszystkie ciężkie zadania pod heavy gpt-life-r3, każde Unity pod gpt-life; cudzych blokad/telefonów nie ruszano.

Następna r4 po REPORT/kopii: świeże main do własnej gałęzi i baseline. Nowa recenzja S12 r2 wskazuje koła/osprzęt naczep; najpierw zweryfikować faktyczny LOD, bo osprzęt istnieje już w LOD0. Palety pozostają dalszym backlogiem. Konflikty integracji: life_cars, CARPAINT, opt-in materials.py/WorldPbrMaterials.cs, generaty i testy; zachować inne domeny. Niezależny odbiór oraz telefon należą do lidera, autor nie scala do main i nie pushuje.
