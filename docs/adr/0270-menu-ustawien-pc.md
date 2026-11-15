# ADR 0270 — menu ustawień PC (ekran, grafika, interfejs, dźwięk)
Status: Proposed (chmura H r2, zadanie H8, gałąź `pc-settings-0270`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
Powiązane: ADR 0260 (D73: Windows platformą główną), ADR 0261 (build Windows: desktop High / 60 fps), ADR 0265 (#131 HUD PC:
`UiPreferences`, `ui.hudScale`, `UiFocus`), ADR 0264 (#133 pad/klawiatura), ADR 0269 (H7 tiery PC, `PcGraphicsTiers`), D74.

## Kontekst
Na PC gracz oczekuje typowego ekranu ustawień: rozdzielczość, tryb okna, synchronizacja pionowa, limit klatek, jakość grafiki,
skala HUD, głośności. Do tej pory menu startowe miało tylko szybkie przyciski tier/30-60 fps (PlayerPrefs `diag.*`).
Panel sterowania (`ControlSettingsPanel`) dotyczy kierownicy/pedałów/kamery i zostaje osobny.

## Decyzja
1. **Logika w czystych klasach `Game.Core.Settings`** (Game.Core, bo asmdef testów EditMode go widzi, a Game.UI nie;
   bez zmian asmdef): `PcSettingsData` (model, zakresy, domyślne, `Sanitize`), `PcSettingsJson` (kodek + migracje),
   `PcSettingsStore` (plik), `ResolutionList` / `DisplayMode`, `FramePacing`, `DisplayConfirmTimer`, `StartupDisplayPolicy`.
   Warstwa Unity: `Game.UI.Settings.PcSettingsRuntime` (stosowanie), `PcSettingsPanel` (widok), `PcSettingsTexts` (tabela tekstów PL).
2. **Zapis:** `Application.persistentDataPath/settings_pc.json`, JSON (`JsonUtility`) z `schemaVersion` = 1. Zapis atomowy:
   `.tmp` + flush na dysk → `File.Replace` (poprzednia wersja jako `.bak`; fallback Move gdy Replace niedostępny). Odczyt:
   plik → `.bak` → stare PlayerPrefs → domyślne. Nieczytelny plik przemianowany na `.bad` (do diagnozy). Każda wartość
   **spoza zakresu / nieznana → domyślna** (nie najbliższa granica: uszkodzony plik nie zostawi 0 % głośności ani okna 10×10).
3. **Migracje:** (a) brak pliku → z kluczy PlayerPrefs `diag.qualityTier`, `diag.targetFps` (menu startowe / `-tier`) i
   `ui.hudScale` (#131); (b) plik bez `schemaVersion` (0) → układ jak 1, brakujące pola = domyślne; (c) plik z nowszej wersji →
   znane pola czytane, raport `newer=True` w logu. Kolejne wersje: bloki `if (fileVersion < N)` w `PcSettingsJson.Migrate`.
4. **Pola i zakresy:** rozdzielczość (0×0 = natywna; lista `Screen.resolutions` bez duplikatów — ten sam rozmiar i odświeżanie
   z dokładnością 0,01 Hz, posortowana rosnąco; zapis jako ułamek `RefreshRate`), tryb okna `windowed` / `borderless` /
   `exclusive` (→ `FullScreenMode.Windowed` / `FullScreenWindow` / `ExclusiveFullScreen`; domyślnie `borderless` = obecne
   `fullscreenMode: 1`), vsync (domyślnie wył.), limit klatek **30/60/75/120/144/bez limitu** (domyślnie **60** jak ADR 0261),
   tier **auto**/low/medium/high/ultra (auto = High jak ADR 0261), skala HUD 0,8–1,4 (zakres `HudScaleModel.UserScale*` z #131),
   jednostki `metric` (patrz 7), głośności 0–1 co 5 %.
5. **Tempo klatek:** vsync wł. → `vSyncCount = 1`, `targetFrameRate = -1` (na desktopie Unity ignoruje targetFrameRate przy
   vsync; w menu limit pokazuje „jak monitor” i jest nieaktywny). Vsync wył. → `vSyncCount = 0`, limit N → N, bez limitu → −1.
   Szybkie przyciski menu startowego (`StartMenuOptions.SetTier/SetFps`) aktualizują plik (`NoteTierChanged/NoteFrameRateChanged`),
   więc oba miejsca się zgadzają.
6. **Stosowanie przy starcie** (`GameBootstrap.Awake`, po dotychczasowym wyborze tier/fps): w playerze desktop — tryb ekranu
   (tylko gdy ustawienia pochodzą z pliku i brak argumentów Unity `-screen-*`, `-window-mode`, `-popupwindow`: przebieg
   dowodowy `build-windows.ps1` w oknie 1600×900 z ADR 0261 nie jest nadpisywany), tempo klatek i tier (oba pomijane, gdy
   podano `-fps` / `-tier` — pomiary wygrywają bez zmiany pliku); wszędzie — głośności i skala HUD. Telefony i edytor bez
   zmian tieru/okna.
7. **Jednostki:** HUD i wyświetlacze kabiny pokazują wyłącznie km/h (`CabDisplayText.KmH`, `DrivingHud` „km/h”, NavLayout).
   Model przyjmuje `imperial`, ale menu pokazuje tylko „km/h” (pole tylko do odczytu). **Propozycja:** mph dopiero gdy
   powstanie wersja eksportowa — formatowanie prędkości przez jedną funkcję w `CabDisplayText` + znaki ograniczeń bez zmian (PL).
8. **Głośności** wg tego, co istnieje (brak AudioMixer): ogólna → `AudioListener.volume`; silnik → `EngineAudio.ChannelGain`
   (pętle, turbo, klekot, zdarzenia start/stop); otoczenie → `AmbientAudio.ChannelGain` (tło placu, ptaki); „sygnały kabiny” →
   `ClusterChime` (UI nie ma dźwięków kliknięć). Wartości w `Game.Core.AudioMixLevels` z licznikiem `Version`;
   `TruckAudioController` porównuje jedną liczbę na klatkę (zero GC w pętli jazdy). Dźwięki pojazdu (opony, wiatr,
   pneumatyka) idą tylko przez ogólną — osobny kanał „pojazd” to ewentualne rozszerzenie.
9. **Panel `PcSettingsPanel`** (przycisk „Ekran, grafika, dźwięk” w menu startowym, poza telefonami): edytuje kopię;
   „Zastosuj” zapisuje i stosuje, „Anuluj” / Esc / pad B odrzuca, „Przywróć domyślne” wczytuje domyślne do kopii.
   Zmiana rozdzielczości/trybu → okno „Zachować nowy tryb ekranu?” z odliczaniem **15 s** (WORKING_VALUE) i powrotem do
   poprzedniego trybu (domyślny fokus na „Przywróć”). Nawigacja: każdy element to `Selectable` z jawną nawigacją
   (wiersze w kolejności czytania, lewo/prawo w wierszu), zaznaczenie przewija się w widok, ramka fokusu (obrys).
   Styl: ten sam płaski ciemny panel co `ControlSettingsPanel`, bez ikon, neonów i rozmyć (docs/06 §7).
10. **Adapter tierów (H7):** `IGraphicsTierApplier` + `QualityLevelTierApplier` (domyślnie `QualityTiers.Apply` po nazwie).
    Po scaleniu H7 podmiana jednej linii w `QualityLevelTierApplier.Apply`:
    `PcGraphicsTiers.Apply((PcTier)System.Array.IndexOf(QualityTiers.Names, qualityLevelName)); return true;`
    (opcjonalnie `PcSettingsRuntime.AutoTier` → wybór sprzętowy H7).

## Zależności od otwartych PR
- **#131 (pc-ui-0265):** ten sam klucz `ui.hudScale` i zakres 0,8–1,4; po scaleniu: w `PcSettingsRuntime.ApplyHudScale`
  dopisać `UiPreferences.HudScale = scale;` (lub `UiPreferences.Reload()`), w `PcSettingsPanel` zastąpić `Decorate` →
  `UiFocus.Decorate(b, Cancel)`, `WireNavigation` → `UiFocus.ApplyGrid`, usunąć `PcFocusOutline.cs`; skala HUD w
  `ControlSettingsPanel` (#131) i tutaj zapisują ten sam klucz — do decyzji lidera, czy zostawić jeden wiersz.
  Konflikty tekstowe: `BootMenu.cs` (#131 zmienia blok przycisków ustawień/„Informacje”; tu dodany wiersz pod nim i parametr
  `openPcSettings` w `Create`).
- **#133 (gamepad-0264):** brak wspólnych plików poza `ControlSettingsPanel.cs` (tu nietknięty). Esc/B obsłużone w panelu
  bezpośrednio przez Input System (jak `InputBindingsPanel`).
- **H7 (pc-tiers-0269):** pkt 10.

## Budżet
Brak wpływu na treść i pętlę jazdy: panel i zapis tylko w menu; w jeździe jedno porównanie `int` na klatkę w
`TruckAudioController` i mnożenie przez `ChannelGain` (domyślnie 1). Brak nowych zasobów (docs/LICENSES.md bez zmian).

## Walidacja
- Testy EditMode `PcSettingsTests` (27): round-trip JSON i pliku, zapis atomowy (.bak, brak .tmp), uszkodzony plik → .bak / domyślne,
  migracja z PlayerPrefs, schemat 0, nowszy schemat, wartości poza zakresem → domyślne, deduplikacja i dopasowanie rozdzielczości,
  mapowanie vsync/limit, odliczanie, polityka startu, poziomy głośności. **Uruchomione poza Unity** (dotnet 8 + NUnit 3, atrapa
  `Mathf`/`JsonUtility` na System.Text.Json): 27/27. **W Unity: NIEuruchomione** (chmura bez Unity).
- Kompilacja Game.UI / Game.Gameplay / Game.Audio w Unity: **NIEsprawdzona** (brak edytora); kod przejrzany ręcznie.
- Wygląd panelu, Screen.SetResolution na Windows, pad: **UNVERIFIED** — do zrzutu z buildu Windows przez lidera.

## Otwarte
- Odliczanie 15 s, skok głośności 5 %, minimalny rozmiar okna 640×360 — WORKING_VALUE.
- Kanał „pojazd” (opony, wiatr, pneumatyka) osobno od silnika — decyzja właściciela po odsłuchu.
- mph — patrz pkt 7.
