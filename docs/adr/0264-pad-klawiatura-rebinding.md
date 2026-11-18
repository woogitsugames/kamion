# ADR 0264 — Pad i klawiatura „pełne”: krzywe, limit skrętu od prędkości, rebinding, zapis

Status: przyjęty (scalony do main 2026-11-16, `3e9ef52fc`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (agent H2 w chmurze, s22, gałąź `gamepad-0264`), 2026-11-15. Do scalenia przez lidera po EditMode + jeździe na buildzie Windows.

## Kontekst
D73/ADR 0260: Windows jest platformą główną. Dotychczas sterowanie PC = `KeyboardDriverInput` (stałe klawisze, rampa, edytor). Agent win-build-0261 robi lokalnie minimalne mapowanie klawiatura/pad; jego gałęzi nie ma w `origin`. Zadanie H2: pełny pad (Xbox/PS przez generyczny `<Gamepad>` Unity Input System), klawiatura z narastaniem osi, rebinding w ustawieniach, zapis nadpisań, konfiguracja krzywych jako dane, logika w czystych klasach testowalnych bez runtime Unity, zero GC w pętli jazdy.

## Decyzja

### 1. Stabilne nazwy akcji (kontrakt dla 0261, 0263 kierownica, zapisu nadpisań)
Dwie mapy o identycznych nazwach akcji — po jednej na rodzinę urządzeń, żeby każde źródło czytało tylko swoje urządzenie i kształtowało je po swojemu (rampa dla klawiszy, krzywa dla gałek); 0263 może dodać trzecią mapę `DrivingWheel` o tych samych nazwach:

| Mapa | `DrivingKeyboard`, `DrivingGamepad` (`DrivingActionCatalog.KeyboardMap/GamepadMap`) |
|---|---|

| Akcja | Typ | Klawiatura (domyślnie) | Pad (domyślnie, `<Gamepad>`) | `DriverIntent` / cel |
|---|---|---|---|---|
| `Steer` | Axis | A/D, ←/→ (1DAxis) | `leftStick/x` | `Steer` (+ = prawo) |
| `Throttle` | Axis | W, ↑ | `rightTrigger` | `Throttle` |
| `Brake` | Axis | S, ↓ | `leftTrigger` | `Brake` |
| `Clutch` | Axis | — | — | zarezerwowane (AMT bez pedału; 0263) |
| `ShiftUp` / `ShiftDown` | Button | E / Q | `rightShoulder` / `leftShoulder` | `ShiftDelta` |
| `SelectDrive` / `SelectNeutral` / `SelectReverse` | Button | 1 / 2 / 3 | `buttonWest` / `buttonEast` / `select` | `Selector` |
| `ToggleManual` | Button | M | — (do przypisania) | `ToggleManual` |
| `ParkingBrake` | Button | Spacja | `buttonSouth` | `ToggleParkingBrake` |
| `RetarderMore` / `RetarderLess` | Button | X / Z | `dpad/down` / `leftStickPress` | `RetarderDelta` |
| `IndicatorLeft` / `IndicatorRight` / `Hazard` | Button | , / . / H | `dpad/left` / `dpad/right` / `dpad/up` | `TurnSignal` |
| `Horn` | Button | K | `rightStickPress` | `AudioCues.HornHeld` |
| `CycleCamera` | Button | C, Tab | `buttonNorth` | `CameraRig.NextMode` |
| `MirrorInsets` | Button | L | — | lusterka w oknach (D70) |
| `ReverseCamera` / `BrakeCruise` / `Couple` / `LandingGear` | Button | V / B / T / G | — | odpowiednie pola `DriverIntent` |
| `Look` | Vector2 | — | `rightStick` | `CameraRig.AddLookDelta` |

Domyślne = mapowanie ADR 0261 z main (klawisze `KeyboardDriverInput`: C kamera, T sprzęg; pad jak w ADR 0261 §6) + Tab/L (tabela po scaleniu z main, patrz „Scalenie”). Escape (menu/wstecz) i `start` pada (menu, ADR 0265) nie są przypisywane. `DriverIntent` bez zmian; kamera/lusterka/rozglądanie/klakson idą osobną strukturą `ViewCommands`.

### 2. Asset akcji z JSON ze stabilnymi id
`DrivingActions` buduje `InputActionAsset.FromJson(DrivingActionCatalog.BuildAssetJson())` — bez importowanego assetu i bez edycji szablonu `InputSystem_Actions.inputactions`. **Id map/akcji/powiązań = MD5(`"kamion.driving/" + mapa/akcja/indeks`)**: `LoadBindingOverridesFromJson` dopasowuje nadpisania wyłącznie po id powiązania (źródło: `InputActionRebindingExtensions.LoadBindingOverridesFromJsonInternal`, repo Unity-Technologies/InputSystem, gałąź develop), więc losowe id z `AddBinding` gubiłyby zapis po restarcie. Zmiana kolejności powiązań w akcji = zmiana id → wpis w `InputBindingsStore.ActionRenames` albo akceptacja resetu tej akcji.

### 3. Kształtowanie (czyste klasy, dane w JSON)
- `PadSteeringMath`: martwa strefa wewnętrzna + saturacja zewnętrzna z przeskalowaniem (bez skoku), krzywa `|x|^e` (1..4), tablice odcinkowo-liniowe, ogranicznik prędkości zmiany (powrót ku środkowi nigdy wolniejszy niż skręt), rampy klawiszy.
- **Amplituda od prędkości** (pad i klawiatura): pełna gałka/trzymany klawisz prosi najwyżej o kąt kół dający `maxLatAccelMs2` na modelu rowerowym kinematycznym: `δ = atan(L·a/v²)`, ułamek = `δ/δmax`, z podłogą `minAmplitude` (manewr awaryjny). L = 3,70 m (`art-source/truck/dims.json`, tam WORKING_VALUE), δmax = 40° (`tractor_4x2_generic.vehicle.json`). Pełny skręt do ~15 km/h, przy 80 km/h ok. 0,05 zakresu. Gracz skaluje a_lat (50–200 %).
- **Limit prędkości skrętu** z tablicy (km/h → ułamek zakresu/s), osobno pad i klawiatura; przy postoju 1,2/s (powyżej limitu rąk kolumny 720°/s przy 800° zakresu — wtedy fizyczna kolumna ADR 0058/0135 zostaje ograniczeniem), przy prędkości ciaśniejszy niż kolumna.
- **Powrót do środka**: domyślnie `padReleaseToPhysics = true` — gałka w martwej strefie = ręce zdjęte (`SteerActive=false`), kierownica wraca z momentu samonastawności w `SteeringColumn` (zasada „samopowrót z momentu z fizyki”); ponowny chwyt startuje od bieżącej pozycji koła (`VehicleFeedback.RoadWheelAngleNormalized`), bez skoku. Opcja `false` = rampa do zera. Klawiatura: rampa powrotu 2,0/s (jak dotąd).
- Spusty: martwa strefa 0,04 / saturacja 0,02, krzywa liniowa (pedały dotykowe mają własne 1,6/1,4 w `ControlSettings`).
- Wszystkie liczby w `Resources/Controls/pad_keyboard_feel.json` = domyślne C# `PadKeyboardFeel` (test pilnuje zgodności) i są **WORKING_VALUE** do testu feelingu właściciela na PC; `Sanitize()` naprawia zepsute tablice i przycina skalary.

### 4. Zapis nadpisań i strojenia gracza
`InputBindingsStore` → `Application.persistentDataPath/input_bindings.json`:
`{"schema":1,"stickDeadZone":..,"stickExponent":..,"speedLimitScale":..,"keySteerScale":..,"overrides":"<JSON SaveBindingOverridesAsJson, escapowany>"}`.
Schemat 0 = goły dokument `{"bindings":[...]}` → migracja z domyślnym strojeniem; nowszy schemat → znane pola zachowane; zepsuty plik → domyślne (nigdy wyjątek); zapis atomowy (plik tymczasowy + `File.Replace`; fallback delete+move, UNVERIFIED na każdym celu IL2CPP), bo proces może zostać zabity. Parser własny, płaski (bez `JsonUtility`), żeby round-trip testować poza Unity. Mapa zmian nazw akcji (`ActionRenames`) migruje zapisane nadpisania przy scaleniu nazewnictw.

### 5. Rebinding i UI
`InputBindingsPanel` (Game.UI, ten sam płaski ciemny panel co `ControlSettingsPanel`): strony Klawiatura/Pad, steppery strojenia, wiersz na akcję, przycisk na każde powiązanie (części kompozytu „w lewo/w prawo”). `PerformInteractiveRebinding` ograniczony do `<Keyboard>` albo `<Gamepad>`, Escape wykluczony, anulowanie Backspace / środkowy prawy przycisk pada / 10 s; ostrzeżenie o konflikcie z inną akcją; „Przywróć domyślne” dla bieżącej strony. Nazwy przycisków pada **pozycyjne i generyczne** („przycisk dolny”, „lewy spust”, „krzyżak w lewo”, „lewy bumper”) — bez liter A/B/X/Y i kształtów producentów, bez logo (test). Wejście: wiersz „KLAWIATURA I PAD → Przypisania i czułość…” w `ControlSettingsPanel`, widoczny tylko gdy zainstalowano wejście PC (`ControlSettingsPanel.OpenInputBindings`). Teksty PL w `DrivingActionCatalog`/panelu (projekt nie ma jeszcze tabel lokalizacji).

### 6. Integracja bez dotykania kompozycji (0261/0262)
`PcInputBridge` (Game.Gameplay) dołącza się sam po załadowaniu sceny (`RuntimeInitializeOnLoadMethod(AfterSceneLoad)` + `sceneLoaded`) do każdego `DrivingLabBootstrap`: wczytuje plik, buduje akcje, wstawia `GamepadDriverInput` i `KeyboardBindingsDriverInput` **przed** `bootstrap.Keyboard` w mikserze (nowe `DriverInputMixer.InsertBefore`; zawsze aktywne koło dotykowe jest dalej w kolejce, więc nie przejmuje sterowania), wyłącza stare `KeyboardDriverInput` (te same klawisze), co klatkę stosuje `ViewCommands` (kamera, rozglądanie, klakson OR z K bootstrapu, lusterka przez `PcInputBridge.ToggleMirrorInsets`).

## Scalenie z win-build-0261 — rozstrzygnięcie (agent H6, s22, merge `origin/main` do `gamepad-0264`)
0261 jest już na main z własnym, minimalnym `Game.Controls.GamepadDriverInput` (statyczne `ShapeAxis`/`ShapeTrigger`,
pole `DrivingLabBootstrap.Pad` w mikserze po klawiaturze) i obsługą pada/klawiatury w `DrivingLabBootstrap.Update`
(Y / C = kamera, prawa gałka = rozglądanie, klik prawej gałki = klakson, Start = menu). Bez rozstrzygnięcia jeden pad
byłby czytany dwa razy (`ShiftDelta`/`RetarderDelta` sumują się → podwójna zmiana biegu), a domyślne przyciski 0261 i 0264
się wykluczały (np. Y = kamera w 0261, hamulec postojowy w 0264; C = kamera w 0261, sprzęg w 0264).
1. **Jedna implementacja pada:** `GamepadDriverInput.cs` = wersja 0264 (akcje z rebindingiem, krzywe, amplituda i limit
   skrętu od prędkości, powrót z fizyki); `.meta` z main (GUID `e2c8359a…`, klasa nie jest komponentem). Minimalna klasa
   0261 usunięta. Z `DrivingLabBootstrap` usunięte pole `Pad`, `m_Mixer.Add(Pad)`, kamera z Y, rozglądanie i klakson
   z pada. Jedynym źródłem pada w mikserze jest `PcInputBridge` (wstawia pad i klawiaturę z akcjami przed `Keyboard`
   i wyłącza `KeyboardDriverInput`). Bootstrap zostawia: Esc / Start = menu, K = klakson (bridge dokłada akcję `Horn`
   przez OR), C = kamera **tylko gdy** `Keyboard.Enabled` (bridge jeszcze niezainstalowany) — bez podwójnego `NextMode`.
   Dodana linia `PcInputBridge.ToggleMirrorInsets = …` (L przełącza lusterka w oknach). Auto-hook bridge zostaje.
2. **Wspólne nazwy i domyślne przyciski = mapowanie ADR 0261** (opisane właścicielowi w ADR 0261 §6 na main): klawiatura
   C (+ Tab) = kamera, T = sprzęg; pad: A/dolny = hamulec postojowy, X/lewy = D, B/prawy = N, Back = R, Y/górny = kamera,
   krzyżak ↑ = awaryjne, ↓ / klik lewej gałki = retarder +/−, klik prawej gałki = klakson; lusterka na padzie bez
   przypisania (do ustawienia w panelu). Nazwy akcji 0264 bez zmian (id powiązań zależą od mapy/akcji/indeksu, nie od
   ścieżki, więc zapisane nadpisania zostają ważne). Test `Catalogue_…` pilnuje tego układu.
3. `WindowsBuildTests` (0261): testy kształtu gałki i spustu przepisane z `GamepadDriverInput.ShapeAxis/ShapeTrigger` na
   `PadSteeringMath.Shape(raw, dz, 0, curve)` — te same przypadki i liczby (jedna funkcja kształtu).
4. Konflikty z innymi PR rundy 1: `DriverInputMixer.cs` (#132 wheel-0263 dodaje źródło kierownicy) i
   `ControlSettingsPanel.cs` (#131 pc-ui-0265) — opis i rozwiązanie w komentarzach PR #129–#133 (scalanie w kolejności
   #129 → #130 → #131 → #133 → #132).

### Pierwotna analiza ryzyk (przed scaleniem)
| Plik / obszar | Ryzyko | Co wybrać |
|---|---|---|
| `Input/KeyboardDriverInput.cs` | 0264 go nie edytuje; bridge go wyłącza | Zachować plik (edytor bez bridge, testy). Jeśli 0261 dodał tam nowe klawisze, dopisać je do `DrivingActionCatalog.All`. |
| Nowy plik pada w 0261 (np. `GamepadDriverInput.cs`) | **add/add** lub duplikat klasy `Game.Controls.GamepadDriverInput` | Wziąć wersję 0264 (rebinding, krzywe, limit od prędkości); minimalne mapowanie 0261 usunąć. Jeśli 0261 ma inną nazwę klasy, a oba źródła trafią do miksera: `ShiftDelta`/`RetarderDelta` sumują się → podwójne zmiany biegów. **Zostawić jedno źródło pada.** |
| `InputSystem_Actions.inputactions` | 0264 nie dotyka | Jeśli 0261 dodał mapę „Driving” z innymi nazwami — przenieść ścieżki do katalogu 0264, mapę usunąć; zapis nadpisań 0261 (jeśli był) migrować przez `ActionRenames`. |
| `Gameplay/DrivingLabBootstrap.cs` | 0264 nie edytuje | Jeśli 0261 dodał tam `m_Mixer.Add(<pad>)` — usunąć tę linię. Opcjonalnie (zalecane przez 0264): zastąpić auto-hook jedną linią `gameObject.AddComponent<PcInputBridge>()` w `Awake` po `m_Mixer.Add(Touch)` i dodać `PcInputBridge.ToggleMirrorInsets = () => { m_MirrorInsets = !m_MirrorInsets; PlayerPrefs.SetInt(PrefMirrorInsets, m_MirrorInsets ? 1 : 0); };`. |
| `Input/DriverInputMixer.cs` | 0264 dodaje tylko metodę `InsertBefore` | Konflikt tekstowy mało prawdopodobny; przy konflikcie zachować obie zmiany. |
| `UI/ControlSettingsPanel.cs` | 0264: pole statyczne + 1 blok wiersza; H3 (0265) też może zmieniać panel | Zachować oba. |

## Propozycje dla lidera (asmdef / ustawienia — nie zmieniane przez agenta)
- Brak wymaganych zmian asmdef: test EditMode nie odwołuje się do typów Input System (API `DrivingActions` na stringach; kompilacja bez referencji sprawdzona Roslynem na zaślepkach). Opcjonalnie: `Unity.InputSystem` w `Game.Tests.EditMode.asmdef`, jeśli dojdą testy z `InputTestFixture` (wirtualny pad) — wtedy także test kierunku na prawdziwym `Gamepad`.
- Test PlayMode alokacji `GamepadDriverInput.Sample` z wirtualnym padem (InputTestFixture) — do dopisania po decyzji o asmdef.

## Budżet
CPU: kilka `ReadValue`/`WasPressedThisFrame` na klatkę (~30 akcji × 2 mapy), bez alokacji (API Input System bez alokacji; kształtowanie sprawdzone testem GC w EditMode — do uruchomienia). Pamięć: jeden asset akcji. Brak zmian renderingu.

## Walidacja
- Napisane: 12 nowych plików C# (Input 10, Gameplay 1, UI 1), JSON strojenia, testy `PadKeyboardInputTests` (21 testów); zmiany: `DriverInputMixer.InsertBefore`, wiersz w `ControlSettingsPanel`.
- Uruchomione poza Unity: 18/21 testów czystej logiki w harnessie .NET 8 + NUnit 3.14 (shim `Mathf`) — **18/18 PASS**.
- NIEuruchomione: kompilacja w Unity 6000.3.28f1, 3 testy wymagające runtime Unity (GC recorder, JSON z Resources, round-trip nadpisań przez `InputActionAsset`), jazda z padem/klawiaturą na buildzie Windows, UI rebindingu (zrzut).

## Otwarte
- Test feelingu właściciela na PC (wszystkie WORKING_VALUE), szczególnie `maxLatAccelMs2`, wykładnik gałki, `padReleaseToPhysics`.
- Nawigacja menu padem (H3/0265): przy kliknięciu przycisku powiązania padem ten sam przycisk może zostać od razu złapany — do sprawdzenia na urządzeniu (`OnMatchWaitForAnother` 0,1 s).
- Wskazówki przycisków w HUD (H3), kierownica i FFB (H1/0263, mapa `DrivingWheel`), sprzęgło (`Clutch` zarezerwowane).
