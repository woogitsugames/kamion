# ADR 0135: kierownica dotykowa „przesuw kciukiem” i orientacja ekranu na składanym telefonie

Status: proponowany (2026-11-12, gałąź `steer-fold`). Źródło: test właściciela na Samsungu Galaxy Fold (APK `11db0552`,
ekran wewnętrzny, film 82 s): (1) „ciężko, nieprzyjemnie się kieruje kierownicą”, (2) „na foldzie obraca obraz
o 45° w lewo, tak jakby na normalnym zmieniało z pionu na poziom”. Zakres: tylko kierownica i orientacja; pełne
dopasowanie HUD do Folda po bramce 3 (decyzja właściciela). Fizyki napędu/zawieszenia nie ruszano (ADR 0134).

## 1. Kierownica — diagnoza

Kod przed zmianą (ADR 0058): kierownica ekranowa 400×400 jednostek w lewym dolnym rogu, gest = kąt palca wokół
środka koła 1:1, zakres ±270° ekranu = pełny skręt (±800° w kabinie) do 20 km/h; kolumna z limitem rąk 540/480°/s
przy 0/10 km/h; samopowrót dopiero od 2 km/h.

- **Zasięg (główna przyczyna).** Kciuk zakotwiczony w rogu ekranu nie zatoczy łuku wokół środka koła — dolna połowa
  okręgu leży pod krawędzią ekranu / pod nasadą kciuka. Na klatkach filmu palec nie przechodzi poniżej linii
  3/9 h (WORKING_VALUE: wygodny zakres ±120° ekranu). ±120° z 270° = **44 % skrętu** przy manewrach; resztę trzeba
  „przekładać” (puścić i chwycić), a od 2 km/h puszczone koło wraca do środka, więc przekładanie gubi kąt.
  Ciasny zakręt placu (10–20 km/h) był praktycznie nieosiągalny jednym ruchem → „ciężko”.
- **Gest zależny od promienia.** Ten sam ruch palca blisko środka daje duży kąt, przy obręczy mały; na Foldzie koło ma
  ~35 mm (UiScale: 1680 jednostek na szerokość 2184 px), na S24+ ~20 mm — czułość różna na każdym telefonie.
- **Opóźnienie rąk przy manewrach.** Pełny skręt przy 540°/s = 1,6 s + rozpęd; przy 5–10 km/h ciągnik jedzie
  szeroko, zanim koło w kabinie dojdzie.
- Filtr (τ 50 ms) i martwa strefa (1 %) nie są przyczyną (test `SmallFingerMotion_TrackingLag_Below80ms`).
- Przełożenie układu kierowniczego (20:1, ±800° = 4,4 obrotu) zostaje — to dane pojazdu (agent fizyki).

## 2. Kierownica — decyzja

- **Nowy gest „przesuw” (domyślny):** poziomy ruch palca w milimetrach (piksele / `Screen.dpi`, rezerwa 420 dpi)
  obraca kierownicę ekranową względnie: `dragScreenDegPerMm = 10,8` (zakres 270° w **25 mm**) → pełny skręt kciukiem
  bez odrywania. Dotyk w dowolnym miejscu koła nie powoduje skoku; ruch pionowy nie skręca; po dojściu do oporu
  cofnięcie palca działa od razu (przyrostowo, bez martwego ruchu). Niezależne od promienia i skali UI.
- **Przy prędkości:** `dragHighSpeedHandwheelDegPerMm = 5` (od 60 km/h 1 mm = 5° w kabinie = 0,25° kół; zmiana
  pasa 20–30° = 4–6 mm). Przejście smoothstep 20→60 km/h jak w ADR 0058 (`WheelGain` z jawnym stosunkiem dla gestu).
  Dla porównania stary gest na obręczy S24+ dawał ~6,5°/mm przy prędkości (CSV niżej).
- **Gest „obrót” zostaje** jako opcja (Ustawienia → Kierownica dotykowa → „Chwyt: obrót / przesuw”).
- **Obszar chwytu** = kwadrat koła + niewidoczny pas do krawędzi bezpiecznego obszaru po lewej (40 j.) i u dołu (32 j.);
  nic innego tam nie leży (strefy HUD bez zmian, ADR 0079).
- **Wskaźnik kąta:** biała kreska na obręczy = kąt koła w kabinie (`ColumnScreenDeg`, odwrotność mapowania); rysunek
  z pomarańczowym znacznikiem = polecenie palca. Rozjazd pokazuje opóźnienie ciężkiego koła; po ustaleniu się pokrywają.
- **Limit rąk przy manewrach:** 720/600°/s przy 0/10 km/h (było 540/480; od 30 km/h bez zmian — skarga z S24+
  z ADR 0058 dotyczyła 41–90 km/h). Od oporu do oporu na postoju ~2,3 s (było ~3,1 s), ≈ 2 obr./s „z dłoni”.
  WORKING_VALUE (bez cytowanego pomiaru dla ciężarówek).
- Fizyka bez zmian: kolumna (`SteeringColumn`) → `Steering` → siły z opon; samopowrót z momentu powrotnego jak w 0058.
- **Zapis ustawień:** schemat 4, pole `wheelDragGrab` (domyślnie `true`); migracja v3→v4 włącza przesuw (jak v2→v3:
  stary gest był przyczyną zgłoszenia), pozostałe wybory właściciela zostają; jawne v4 „obrót” zostaje. Linia
  `[CONTROLS]` dostała `grab=drag|rotate`.

## 3. Orientacja — diagnoza

Manifest z ostatniego buildu (`Library/Bee/Android/.../unityLibrary/src/main/AndroidManifest.xml`, main):
`screenOrientation="userLandscape"`, `resizeableActivity="true"`, `android:appCategory="game"`, `configChanges` ze
wszystkimi flagami (`orientation|screenSize|smallestScreenSize|screenLayout|density…`). Target SDK 36.
- Android 16 przy target SDK 36 ignoruje `screenOrientation` na ekranach sw ≥ 600dp (Fold wewnętrzny), ALE gry
  (`android:appCategory="game"`) są wyłączone z tej zmiany
  (developer.android.com/about/versions/16/behavior-changes-16, „Exceptions”). U nas flaga jest (`AndroidIsGame: 1`),
  więc blokada poziomu działa — i to ona jest problemem.
- Ekran wewnętrzny Folda jest prawie kwadratowy (~1,1:1, np. 2184×1968) i trzymany jak książka ma orientację
  naturalną pionową (UNVERIFIED dla tego modelu — zweryfikuje linia `[SCREEN]` w logcat). `userLandscape` każe wtedy
  systemowi obrócić obraz o 90° względem tego, jak właściciel trzyma telefon — dokładnie „jak na zwykłym telefonie
  zmiana z pionu na poziom”. Na ekranie ~1:1 poziom i pion są równie użyteczne, więc blokada nic nie daje, a obraca.

## 4. Orientacja — decyzja

- **`Game.Gameplay.ScreenOrientationPolicy` + `ScreenOrientationGuard`** (runtime, tylko urządzenia mobilne,
  `DontDestroyOnLoad`, przed pierwszą sceną): okno o proporcji max/min ≤ **1,25** (WORKING_VALUE) → wszystkie
  4 orientacje dozwolone (`Screen.autorotateTo*` + `AutoRotation`; zachowanie „User” = blokada obrotu systemu
  respektowana) → obraz idzie za trzymaniem, nie obraca się wbrew niemu. Okna wydłużone (telefony ≥ 1,78, ekran
  zewnętrzny Folda ~2,3+, tablety 16:10 i 4:3) → tylko LandscapeLeft/Right jak dotąd. Decyzja z max/min, więc ta sama
  w obu orientacjach (bez przełączania tam i z powrotem). Sprawdzana przy każdej zmianie `Screen.width/height`
  (złożenie/rozłożenie to zmiana rozdzielczości bez restartu aktywności — `configChanges`). Log jednej linii:
  `[SCREEN] <w>x<h> aspect <a> -> orientations PULR|--LR (ADR 0135)`.
- HUD: solver ADR 0079 już obsługuje oba układy ekranu ~1:1 (`HudLayoutTests`), safe area odświeżana co klatkę
  (`UiViewport.Refresh`). Bez przebudowy HUD.
- **Kamera kabiny w pionie (proporcja < 1):** pionowe FOV otwierane tak, by poziome FOV = ustawienie (55°) jak na
  ekranie kwadratowym (`CameraRig.CabVerticalFov`, maks. 90°); w poziomie bez zmian. Gyro: istniejący
  `GyroMath.DeviceToScreen` + rekalibracja przy zmianie orientacji (bez zmian).

### Zmiany ProjectSettings — dla lidera
**Wartości się NIE zmieniają.** `ProjectSetup.ApplyPlayerSettings` dostał `ApplyFoldableOrientationSettings()`, który
przypina jako kod to, na czym polega poprawka (stan main `afaa87c9`):
`androidResizeableActivity: 1`, `androidAutoRotationBehavior: 1` (User), `AndroidIsGame: 1` (manifest
`appCategory="game"` — bez tego Android 16 zignorowałby orientację na Foldzie). Domyślna orientacja startowa bez
zmian: `defaultScreenOrientation: 4` (AutoRotation), portret wyłączony, poziom L/R włączony (polityka runtime
dopuszcza portret tylko na ekranie ~1:1). Po `pwsh scripts/setup-project.ps1` diff `ProjectSettings.asset` w tych
kluczach powinien być pusty. Żadnych plików `ProjectSettings/*.asset` w tej gałęzi.

## Dowód / testy
- `SteerFoldTests` (EditMode): kierunek przesuwu (prawo/lewo) → koło ekranowe → kolumna → kąt kół przy 0/5/30/80 km/h
  dla 270° i 900°; pełny skręt w 25 mm przy 5 i 20 km/h; 5°/mm przy 80 km/h; brak skoku przy dotyku, ruch pionowy
  bez skrętu, NaN bez ruchu; natychmiastowe cofnięcie po oporze; znacznik kolumny (opóźnienie i zbieżność); px→mm;
  migracja v3→v4 i ApplyTo; polityka orientacji (Fold 2184×1968 w obu orientacjach, S24+, ekran zewnętrzny, tablety,
  0×0); FOV w pionie. `Evidence_ReachAndLag_Csv` → `artifacts/steer-fold/evidence/adr0135_reach_lag.csv`.
- Zaktualizowane: `SteeringFeelTests` (720°/s, od oporu do oporu 2,1–2,7 s, schemat), `ControlSettingsTests`
  (kierunek w obu gestach, `grab=drag`, domyślny przesuw).

## Do sprawdzenia przez właściciela na Foldzie (UNVERIFIED do tego czasu)
1. Rozłożony, trzymany jak książka: obraz nie obraca się; obrót telefonu obraca obraz tylko gdy blokada obrotu wyłączona.
   Złożenie → ekran zewnętrzny poziomo; ponowne rozłożenie — gra działa dalej bez restartu.
2. Kierownica: przesuw kciukiem w lewo/prawo; ciasny zakręt placu jednym ruchem; przy 50–80 km/h zmiana pasa bez
   nerwowości (jeśli za czułe/za mało: „Czułość” w ustawieniach albo `dragHighSpeedHandwheelDegPerMm` w
   `steering_feel.json`). Porównać z „Chwyt: obrót”.
3. Logcat: `adb logcat -d | grep -E "\[SCREEN\]|\[CONTROLS\]"` (rozmiar okna, proporcja, `grab=`).

## Konsekwencje
- Wszystkie nowe liczby (25 mm, 5°/mm, 720/600°/s, próg 1,25, ±120° zasięgu kciuka w dowodzie) = WORKING_VALUE.
- Przy target SDK 37 (przyszłość) wyjątek dla gier pozostaje deklarowany przez `appCategory`; opt-out
  `PROPERTY_COMPAT_ALLOW_RESTRICTED_RESIZABILITY` nie jest potrzebny i nie został dodany.
- Pełny HUD pod Folda (mniejsze koło/pedały, większe lusterka, zwinięty panel) — osobne zadanie po bramce 3.
