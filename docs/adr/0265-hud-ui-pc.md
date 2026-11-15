# ADR 0265 — HUD i UI na monitor (PC): kontrolki dotykowe, skala 16:9…32:9, nawigacja myszą i padem, okna lusterek

Status: proponowany (chmura H3, gałąź `pc-ui-0265`), 2026-11-15. Napisane i sprawdzone na czystej logice poza Unity
(dotnet + NUnitLite ze stubami UnityEngine); **kompilacja w Unity, testy EditMode/PlayMode i pętla wizualna — NIE
uruchomione** (chmura bez Unity). Rozszerza ADR 0079 (adaptacyjny HUD dotykowy) — nie zmienia go na telefonie.

## Kontekst
D73 / ADR 0260: Windows jest platformą główną. HUD i menu były zrobione pod kciuki (kierownica na ekranie, pedały
GAZ/HAMULEC, R/N/D, dźwignia zwalniacza, kierunkowskazy), skala z krótszego boku i DPI telefonu (na monitorze 1080p
przy 96 dpi wychodziło ~0,64 px/jednostkę — mały HUD), menu bez fokusu dla pada, a lusterka (D70: stałe okienka)
miały rozmiar w jednostkach telefonu. Sterowanie klawiaturą/padem/kierownicą robią ADR 0261/0263/0264.

## Decyzja
1. **Dwa „form factory” jednym źródłem prawdy.** `TouchControlsPolicy` (Game.Controls): ustawienie
   „Kontrolki dotykowe” `auto/zawsze/nigdy` (`UiPreferences`, klucz `ui.touchControls`; poza schematem
   `ControlSettings`, żeby nie kolidować z H1/H2). Auto = build Android/iOS (`UNITY_ANDROID || UNITY_IOS`, także edytor
   z tym targetem) → pokazane; PC → pokazane dopiero, gdy ekran dotykowy istnieje **i** został dotknięty w tej sesji
   (laptop z dotykiem). `UiViewport` wybiera tryb monitora = kontrolki ukryte; HUD bierze stan z `UiViewport.Desktop`.
2. **Skala monitora** (`HudScaleModel`, czysta): treść ma zawsze **1440 jednostek wysokości** → 1080p 0,75 px/j,
   1440p 1,0, 4K 1,5 (ten sam układ, tylko ostrzejszy). Skalowanie Windows (DPI/96) może HUD powiększyć
   (podłoga 0,75·dpi/96 px/j), ale nigdy poniżej 1080 j wysokości; min. 1680 j szerokości (monitor pionowy).
   Suwak gracza „Skala HUD (monitor)” 80–140 % (`ui.hudScale`). Telefon: wzór ADR 0079 bez zmian (przeniesiony
   1:1, `UiScale` jest fasadą).
3. **Ultrawide:** obszar treści (rect „SafeArea”) zwężony do **16:9 i wycentrowany** (2560×1080 → 1920 px treści,
   3440×1440 → 2560, 5120×1440 → 2560); widok 3D i pad rozglądania nadal na całej szerokości. Wszystkie monitory
   dostają ten sam układ 2560×1440 j.
4. **HUD bez dotyku** (`HudLayoutInput.HideTouchControls`): strefy 8–13 (kierownica/gyro, kierunkowskazy,
   zwalniacz, hamulec, gaz, skrzynia) nieaktywne (PedalWidget/SteeringWheelWidget zwalniają się w OnDisable),
   tekst deweloperski na dole pośrodku, minimapa GPS sięga do dołu. Klaster, ostrzeżenie P, kamera cofania,
   przycisk „Panel” bez zmian. Przyciski HUD są tylko-myszowe (`Navigation.None`) i HUD co klatkę zrzuca swoją
   selekcję — inaczej Enter / A pada „klikałby” ponownie np. Reset w trakcie jazdy.
5. **Okna lusterek (D70)** — `MirrorWindowLayout` (Game.Cameras, czysta): wysokość = **30 % wysokości treści**,
   szerokość = wysokość × **aspekt tekstury lusterka** (`RenderTexture` width/height, domyślnie 0,55) — nigdy
   rozciągane; po obu stronach klastra, wyrównane do góry; przy braku miejsca zmniejszane proporcjonalnie, poniżej
   200 j ukryte; skrajne 162 j zostają wolne (przycisk „Panel”). 16:9/21:9/32:9 → to samo okno.
6. **Nawigacja menu** (`UiFocus`): jeden EventSystem + `InputSystemUIInputModule.AssignDefaultActions()` (mysz,
   strzałki/Enter/Esc, gałka/krzyżak/A/B pada); jawna kolejność `MenuNavGrid` (kolumny × wiersze: góra/dół w kolumnie,
   lewo/prawo w wierszu i dalej do sąsiedniej kolumny na tej samej względnej wysokości, bez zawijania); na monitorze
   pierwszy start zaznaczony od razu; fokus widoczny jako **cienka ramka 3 j** (bursztynowa = zaznaczenie,
   wyciszona biel = najechanie myszą; dotyk bez „hover”), bez poświaty i animacji (docs/06 §7). Właściciel fokusu
   jako stos (menu → ustawienia → informacje → powrót), po utracie selekcji nawigacja padem ją przywraca.
   Ustawienia: Esc/B zamyka, zaznaczony wiersz przewija się do widoku; Informacje: przewijanie prawą gałką /
   krzyżakiem / strzałkami / PgUp-PgDn. BootMenu: zmieniony tylko wygląd i nawigacja — delegaty startu bez zmian.

Wartości 1440, 0,75, 16:9, 30 %, 200, 3 j, 80–140 % — **WORKING_VALUE** (ocena właściciela na buildzie).

## Budżet
Bez nowych alokacji w pętli jazdy: `TouchControlsPolicy.Current` liczone raz na klatkę (cache po `Time.frameCount`,
`Touchscreen.current` bez alokacji), `UiViewport.Refresh` porównuje kilka floatów/booli, `ReleaseHudSelection` to
`IsChildOf`. Układ HUD tylko przy zmianie ekranu/stanu (jak w ADR 0079). Ramki fokusu tworzone leniwie raz.
Fizyka bez zmian.

## Walidacja
- Czysta logika: `Tests/EditMode/PcHudLayoutTests.cs` (24 przypadki: skala 1920×1080, 2560×1080, 3440×1440,
  2560×1440, 3840×2160, 5120×1440, 720p, monitor pionowy, DPI 120/144, telefon 2400×1080; polityka kontrolek;
  `UiPreferences` zapis/odczyt/uszkodzone wartości; lusterka; kolejność nawigacji) oraz
  `Tests/PlayMode/PcHudSolverTests.cs` (solver HUD na 10 monitorach × 5 DPI × 3 skale × 128 stanów: brak nakładania,
  w obrębie treści, GPS mieści się, lusterka ten sam rozmiar na 16:9 i 32:9; układ dotykowy domyślnie bez zmian).
  Uruchomione w chmurze przez dotnet 8 + NUnitLite na stubach UnityEngine: **27/27 zielone**.
- Do zrobienia przez lidera: EditMode + PlayMode w Unity (w tym istniejące `HudLayoutTests`/`NavHudTests` —
  `OverrideScreen(px, safe, dpi)` nadal oznacza ekran dotykowy), build Windows, zrzuty visual-qa 16:9/21:9/4K.

## Otwarte
- Rozdzielczość tekstur lusterek (`VehicleCameraBudget.MirrorHeight`) jest mobilna — okno 30 % wysokości na 4K
  (648 px) może pokazać rozmycie; tier PC poza zakresem (Vehicle/Runtime).
- Kierunkowskazy i dźwignia zwalniacza nie mają na monitorze wskaźnika w HUD (lampki HS/RET w klastrze są; strzałek
  kierunkowskazów brak) — do decyzji: kontrolka w klastrze 2D czy tylko zegary w kabinie 3D.
- Sekcje „KIEROWNICA DOTYKOWA” i „GYRO” w ustawieniach są widoczne także na PC (do przebudowy razem z H1/H2).
- Propozycja dla lidera (asmdef): dodać `Game.UI` do `Game.Tests.EditMode`, wtedy modele mogą wrócić do Game.UI,
  a `PcHudSolverTests` do EditMode.
