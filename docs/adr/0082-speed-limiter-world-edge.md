# ADR 0082: ogranicznik prędkości na zjeździe, krawędź regionu (zamknięcia dróg, teren do horyzontu, powrót na drogę) i kamera kabiny w kabinie

Status: przyjęty (2026-11-10). Źródło: nagranie właściciela z Galaxy Z Fold, 127 s, trasa Kwadrat Park → Rondo
Bieżeństwa → al. Tysiąclecia Państwa Polskiego (`Screen_Recording_20261110_210126_Kamion.mp4`; klatki i arkusze:
`artifacts/drive-fold-r10/video/`).

## Kontekst — co widać na nagraniu (zweryfikowane na klatkach 1 kl./s i gęstych wycinkach)
| czas | obserwacja | przyczyna |
|---|---|---|
| 62–109 s | pełny gaz, 86 → 89–90 km/h, potem stałe 89–90 | ogranicznik **już był** (`driveline.speedLimiterKmh = 90`, pasmo 2 km/h); runner: 89,2 km/h (40 t), 89,4 (pusta) |
| 110–116 s | 90 → 94 km/h przy pełnym gazie, w trakcie zmiany pasów | **przyczyna nieustalona (UNVERIFIED)**. Pierwsza hipoteza „zjazd przed krawędzią” nie potwierdziła się: zmierzony profil jezdni wylotowej (kolizja `col_asphalt`, 960 m do krawędzi, `tysiaclecia-north-profile.csv`) wznosi się +1,1…+2,8 %, ostatnie 150 m +1,3 %, największy spadek −0,3 %. Ogranicznik w adapterze Unity trzyma 88,9–89,4 km/h także przy zmianach pasa i na trawie (test niżej). Toru jazdy właściciela z nagrania nie da się odtworzyć co do metra (możliwy zjazd z nasypu / inna jezdnia); potrzebna telemetria z telefonu (przycisk „Nagraj”) |
| 116,5–127 s | biała pustka, 97 → 179 km/h, widok na deskę i kierownicę | koniec danych regionu (bbox ±1024 m, tu N = +1024, E ≈ −857), brak czegokolwiek za krawędzią; spadek swobodny; widok „w deskę” to przeciąganie palcem po polu rozglądania (pitch do limitu szyi 50° w dół + yaw) podczas spadku |
| 69,9–72,3 s | u góry czarny pas z kropkami (fryta / podsufitka), horyzont nisko | **nie ruch głowy**: skok widoku ~30° w górę w < 0,25 s, trzymany 2 s, powrót 60°/s = `lookReturnDelay`/`lookReturnRate` rozglądania; palec lewej ręki wylądował obok kierownicy na `LookPad` |
| 31,5–34,5 s | przejazd przez wysepkę rozdzielającą (szary blok kostki) i wyspę środkową Ronda Bieżeństwa (ziemia / żwir z berberysem) | wyspa ma kolizję, ale klasy „kostka” (tarcie 0,85, opór ×1,3); krawężnik ~0,14–0,2 m działa tylko na koła |

Krawędź regionu: `Data/Regions/bialystok-industrial-c/region.yaml` bbox 2048 × 2048 m, wszystkie 64 chunki mają
teren i kolizję — to **koniec danych, nie dziura w kolizji**. `roads.graph.json` ma 37 węzłów `boundary`
(36 krawędzi dróg przyciętych na bbox), m.in. obie jezdnie al. Tysiąclecia (E −856,5 wylotowa / −868,7 wlotowa,
N +1024; jezdnie biegną skośnie, ok. 12° na zachód od północy), Maczka, Andersa.

## Decyzja

### 1. Ogranicznik prędkości (fizyka, `VehicleModel`)
- Ustawienie bez zmian: 90 km/h (S3: dyrektywa 92/6/EWG zm. 2002/85/WE, N3 — brzmienia art. 3 nie otwierano w tej
  sesji, pozycja w `docs/VEHICLE_REFERENCE_DATA.md` bez zmian), odcięcie dawki w paśmie 2 km/h (WORKING_VALUE) →
  na płaskim 89,2–89,4 km/h. „Typowo 89 km/h” z briefu: UNVERIFIED jako praktyka warsztatowa; model daje tę wartość
  z pasma, nie z osobnej nastawy. Tolerancja scenariuszy `top_speed_flat*` zaostrzona do 88–90 (89 ± 1).
- Ogranicznik **nie hamuje**. Nowe: ochrona przed rozpędzaniem na zjeździe (`driveline.overrunBrakeOffsetKmh = 4`,
  WORKING_VALUE; 0 = wyłączona): gdy prędkość przekroczy nastawę + 4 km/h, hamulec silnikowy i retarder są włączane
  i modulowane tym samym regulatorem PI co „stała prędkość zjazdu” (cel = 94 km/h). Stopa na gazie tego nie
  wyłącza (pedał i tak jest odcięty przez ogranicznik); pedał, który ogranicznik jeszcze przepuszcza, wyłącza.
  ABS osi napędowej i bieg R wyłączają jak dotąd. Że seryjne ciężarówki same włączają hamulec długotrwały przy
  przekroczeniu nastawy ogranicznika o kilka km/h: UNVERIFIED (znane z instrukcji kilku producentów, bez cytatu).
- Telemetria / HUD: `VehicleModel.SpeedLimiterFactor`, `OverrunBrakeActive`.

### 2. Krawędź regionu
- **Dane:** `Game.World.WorldBoundary` na korzeniu regionu (prostokąt E/N, lista zamknięć), budowany przy imporcie
  przez `WorldEdgeBuilder` (wywołany z `WorldSceneBuilder.Build`).
- **Zamknięcia dróg:** na każdej drodze przyciętej przez bbox (36), 60 m przed krawędzią wzdłuż osi drogi — odcinek
  cofania przechodzi przez węzły stopnia 2 (graf dzieli drogę przy zmianie atrybutu; krawędzie brzegowe mają 4–200 m);
  gdy bliżej jest skrzyżowanie, zapora stoi w 80 % długości odcinka od krawędzi (najmniej ~3 m): rząd
  betonowych barier (0,6 × 0,81 m, elementy 2 m) + tablica zapory U-20 (pola biało-czerwone 0,5 m, wysokość 0,25 m,
  na słupkach) + `BoxCollider` (szerokość jezdni + 5 m, 2,5 m wysokości). Wymiary WORKING_VALUE (nie zmierzone
  z rozporządzenia o znakach). Brief mówił „U-21”; U-21 to tablice kierujące, poprzeczne zamknięcie to U-20.
- **Teren do horyzontu:** „fartuch” — obrzeże terenu wyciągnięte na zewnątrz na 2600 m (za `farClipPlane` 1400 m),
  pierścienie 0 / 60 / 300 / 2600 m, wysokość z kolizji terenu przy krawędzi, na końcu wygładzona do średniej;
  materiał `terrain_grass`. Za każdą przeciętą drogą prosty odcinek asfaltu 420 m na niskim nasypie. Bez kolizji.
- **Powrót na drogę (`Game.Gameplay.WorldSafetyNet`, krok stały, co 0,1 s, zero alokacji):**
  `WorldExitMonitor` zgłasza: poza prostokątem (margines 3 m), brak kolizji pod pojazdem w 60 m przez 0,35 s,
  opadanie > 18 m/s przez 0,25 s. Wtedy zestaw wraca, zaparkowany, na ostatnią bezpieczną pozę z `SafePoseBuffer`
  (co 1 s: ciągnik prosto, na utwardzonej kolizji, ≥ 120 m od krawędzi; przywracana poza ma ≥ 2,5 s), a pasek
  statusu mówi dlaczego („Koniec mapy: zestaw ustawiony z powrotem na drodze”). Bez bezpiecznej pozy: spawn sceny.
  260 m przed krawędzią jednorazowe ostrzeżenie „Koniec mapy za ok. 250 m”. To jest awaryjne odtworzenie stanu
  po opuszczeniu świata, nie sposób poruszania pojazdem (żelazna zasada 6 nie jest naruszona w jeździe).
  Działa też w scenach zaimportowanych przed tym ADR (granice z `WorldRegionRoot.chunks`).
- Progi monitora i odległości: WORKING_VALUE (zabezpieczenie rozgrywki, nie dane pojazdu).

### 3. Kamera kabiny
- `CabSuspension`: twarde ograniczniki 1,5 × limit miękkich odbojów (pitch/roll 6°, skok 75 mm) + odporność na NaN;
  w normalnej jeździe nieosiągane (złote przebiegi runnera bez zmian).
- `CameraRig`: przyspieszenie wejściowe kołysania głowy ograniczone do 12 m/s², oko zawsze w pudełku
  ±0,20 / ±0,12 / ±0,20 m wokół punktu oczu (paralaksa szyi do 0,14 m + kołysanie), pozycja z NaN nie trafia do
  renderera, `ResetView()` po odtworzeniu pojazdu.
- **Rozglądanie w jeździe:** powyżej 20 km/h zakres pionowy +12° / −25° (zamiast +55° / −50°), powrót do drogi po
  0,8 s (zamiast 2 s); wejście w zakres płynne (60°/s). Yaw bez zmian (lusterka, skrzyżowania). WORKING_VALUE —
  pozycja do testu feelingu właściciela. Ruch głowy od przyspieszeń (±4–6 cm) zostaje bez zmian.
- Przyczyna źródłowa (dotyk obok kierownicy trafia w `LookPad`) jest w HUD (ADR 0079, inny agent) — zgłoszone:
  strefa martwa `LookPad` wokół kierownicy i pedałów albo rozglądanie tylko w górnej połowie ekranu.

### 4. Wyspa ronda
- Kolizja wyspy istnieje (`collision_paving` na całej wyspie, krawężnik w `collision_curb`, warstwa `WorldKerb`
  — tylko promienie kół), filary wiaduktu w środku mają kolizję. Zmiana tylko klasy podłoża (bez geometrii):
  luźne podłoża wysp (`soil`, `stones`, `gravel`) → `collision_grass` (tarcie 0,55, opór toczenia ×5,
  tak jak `yard_gravel`), tylko wyspy brukowane zostają twarde (`tools/worldgen/streetscape/plantings.py`).
  Wchodzi po regeneracji świata (`build_world.py`); nie regenerowano w tej gałęzi.

## Dowody
- Runner: `artifacts/drive-fold-r10/physics/limiter/` (CSV + PNG): `limiter_downhill_5pct_comb@laden40` maks. 95,1,
  ustalone 94,0 km/h (hamulec silnikowy 180 kW + retarder 190 kW, bieg 11, hamulec roboczy 0);
  `limiter_downhill_2pct_comb@laden40` 93,9–94,3; `top_speed_flat_comb` 89,2 / 89,4. `dotnet test` 153/153.
- Unity, ogranicznik: PlayMode `CombinationLabTests.SpeedLimiter_FullThrottle_LaneChanges` (3): pełny gaz 36 s,
  od 14 s zmiany pasa (okres 4 s): asfalt pusty maks. 89,40; 40 t 89,18; trawa 88,90 km/h.
- Unity, krawędź: EditMode `WorldEdgeLogicTests` (8), PlayMode `WorldEdgeRecoveryTests` (3): zestaw 25 m przed
  krawędzią na jezdni wylotowej, 105 km/h → `OutOfBounds` przy N = 1023,6 (97 km/h), po 0,5 s stoi zaparkowany na
  ostatniej bezpiecznej pozie, kamera w punkcie oczu; telemetria `artifacts/drive-fold-r10/world-edge-reset.csv`;
  profil jezdni `tysiaclecia-north-profile.csv`; kadry krawędzi `artifacts/drive-fold-r10/edge/`.
- Import: `import-region.ps1` w worktree wymaga `git lfs checkout` (inaczej `street_props.glb: not a GLB`).

## Otwarte
- **Skąd +4 km/h w nagraniu (90 → 94 na 110–116 s):** nieodtworzone. Model i adapter trzymają ≤ 89,4 km/h na płaskim
  i na trawie; jezdnia wylotowa się wznosi. Do sprawdzenia na telefonie z nagraną telemetrią (prędkość, pochylenie,
  `SpeedLimiterFactor`, `OverrunBrakeActive`). Ochrona przed rozpędzaniem ogranicza skutek do 94 km/h (na zjeździe);
  czy na zjeździe ma być twarde 90 (offset 0–1 km/h) — decyzja właściciela D46 (2026-11-10): dopuszczać ~94 km/h, `overrunBrakeOffsetKmh = 4` zostaje.
- Powrót ustawia zestaw przodem do krawędzi (ostatnia poza z jazdy); na jezdni jednokierunkowej trzeba użyć
  „Reset” / menu. Docelowo: graf pasów w runtime i powrót na pas w stronę mapy.
- Fartuch nie ma lasu ani zabudowy (goła trawa + mgła); przy zamknięciach brak znaków B-1 / U-3 i świateł U-35.
- Opór żwiru wyspy: wartości `SurfaceTable` to WORKING_VALUE bez źródła; brak osobnej klasy „żwir luzem”.
- Ograniczenie rozglądania w jeździe i komunikaty: do oceny właściciela na telefonie.
