# ADR 0283 — HUD monitora, menu ustawień i okienka lusterek: przeprojektowanie (D84)

Status: Proposed (chmura D r9, zadanie D40, gałąź `hud-redesign-0283`), 2026-11-16. Do weryfikacji w Unity (EditMode,
PlayMode, build Windows, visual-qa + krytyk) i scalenia przez lidera. **Kod C# nieskompilowany w Unity** (chmura bez Unity);
czysta logika sprawdzona w .NET (`tools/hud-runner`, 11/11), składnia wszystkich zmienionych plików C# sprawdzona Roslynem
(26 plików, 0 błędów). Dokument projektowy z makietami: `docs/design/HUD-MENU-PC-0283.md`.

Powiązane: D84 (`docs/11_DECYZJE_WLASCICIELA.md`), D70 (lusterka = okienka), ADR 0079 (HUD dotykowy — bez zmian),
ADR 0243 (okienka lusterek, schemat 5), ADR 0264 (przypisania PC), ADR 0265 (HUD/menu PC, `HudScaleModel`, `UiFocus`),
ADR 0270 (ustawienia PC), ADR 0276 (menu vs nakładka), ADR 0042 (celowanie lusterek R46), docs/06 §2 i §7.

## Kontekst
D84 (feel test bramki 2 zaliczony 5/5): „HUD i menu zbyt AI slop — poziom gier symulacyjnych ciężarówek, styl własny; menu
niewygodne; lusterka za małe / złe”. Diagnoza (HANDOVER s23 13:4x/15:4x): (1) na PC HUD to pływający panel u góry
(klaster 440×156 j) z bladymi tekstami, plus — przez zapisane `ui.touchControls=1` — dotykowa kierownica i pedały;
(2) menu: dwa osobne ekrany ustawień („Ustawienia sterowania” + „Ekran, grafika, dźwięk”), blade nagłówki (`k_Muted` 0,70),
napis „brak w tym APK” na PC, wybrany segment wyróżniony tylko zielonkawym odcieniem; (3) lusterka: okienka 30 % wysokości
(1080p: 324×178 px), przy klastrze u góry, a na ciężarówce placowej (graybox) obraz w ~25–33 % szerokości zajmuje bok
naczepy (oś kamery tylko 1,7° na zewnątrz przy polu 13,3°).

## Decyzja
1. **Jedna paleta i typografia** (`Game.Controls.UiPalette`, `UiContrast`): matowy, prawie czarny ekran jak wyświetlacz w
   desce, ciepła biel tekstu, jeden akcent (bursztyn = fokus i znaczniki sekcji), kolory kontrolek tylko z ich znaczeniem
   ISO 2575. Bez gradientów, poświaty, szkła, neonów, ikon-emoji. Wybrany segment/zakładka = **odwrócenie** (jasne pole,
   ciemny tekst SemiBold) — czytelne bez koloru. Font: Inter Regular (było) + **Inter SemiBold** (nowy, OFL 1.1,
   `docs/LICENSES.md` `font-inter-semibold`) na tytuły, nagłówki, liczby HUD i kafle ostrzeżeń (`UiFonts.Strong`).
   Nagłówki sekcji: SemiBold w kolorze tekstu + krótki bursztynowy znacznik (nie blady podpis).
2. **Kontrast WCAG 2.x AA dla każdej pary** (tabela niżej; test `HudRedesign0283Tests.Contrast_EveryPalettePair_MeetsWcagAA`
   i port .NET). Półprzezroczyste tło HUD liczone **w świetle liniowym** (projekt w Linear, uGUI miesza tam) nad
   najgorszym tłem (białe niebo/śnieg), nie nad czernią — stąd krycie paska 96 % (przy 85 % tekst drugorzędny spada do 2,5:1).
3. **HUD monitora** (`DesktopHudLayout` — czysta, + `DrivingHud.Desktop.cs`): zamiast klastra u góry **jeden niski pasek na
   dole na środku** jak wyświetlacz w desce (720×112 j): prędkość (SemiBold 68 j), bieg, oba obwody powietrza (liczba z
   przecinkiem + pasek; czerwony przy niskim ciśnieniu). Nad nim **rząd kontrolek** (720×52 j): strzałki kierunkowskazów
   na końcach (własna ikona rysowana w kodzie), między nimi kafle ostrzeżeń (maks. 3, kolejność: ruszanie na postojowym,
   niskie ciśnienie, hamowanie naczepy, postojowy, usterka ABS, ABS naczepy, ABS działa — `HudWarnings`). **Tryb
   rozszerzony** (klawisz **I**, akcja `HudDetail` w katalogu przypisań — do zmiany; pad bez domyślnego) dokłada jeden
   wiersz: obroty, zwalniacz (0/HS/R1–R4), tempomat zjazdu; wtedy widać też przycisk „Panel” (strona laboratorium).
   **Widok z kabiny** (`HudVisibility`): gdy ciężarówka ma żywe ekrany kabiny (`CabScreens.LiveClusters > 0`, TRAKT), na
   ekranie zostaje tylko rząd kontrolek (strzałki dopiero gdy migają) — prędkościomierzem są zegary w desce; graybox placu
   bez ekranów → pasek. Ustawienie „HUD w widoku z kabiny”: auto / pasek / tylko ostrzeżenia. Pasek kończy się poniżej 25 %
   wysokości (deska, nie droga). HUD dotykowy telefonu (ADR 0079) **bez zmian**.
4. **Okienka lusterek** (`DesktopHudLayout`): na zewnętrznych krawędziach treści (pole widzenia lusterek kl. II), nie przy
   klastrze; domyślnie **42 %** wysokości (1080p: 454×249 px, +40 % względem 30 % ADR 0265), regulowane w ustawieniach:
   rozmiar 30–60 %, położenie w pionie, odsunięcie od krawędzi; nigdy nie wchodzą w **wolny widok drogi** (środkowe 40 %
   szerokości, min. 760 j); ten sam rozmiar na 16:9, 21:9 i 32:9 (treść 16:9 na środku — `HudScaleModel`). Ramka matowa
   6 j. Ustępują tylko nakładkom deweloperskim (telemetria, panel).
5. **Bez zasłaniania korpusem**: (a) graybox placu celuje lusterka główne **7,5 % na zewnątrz** (4,3°, jak lusterko prawe
   TRAKT w ADR 0042) zamiast 3 % — bok naczepy z ~25–33 % do ~5–14 % szerokości okienka (5–15 m za lusterkiem);
   (b) gracz może obrócić widok obu lusterek głównych: „Na zewnątrz / do środka” ±6°, „W dół / w górę” ±3° (`HudPreferences`,
   `RenderTextureMirror.AdjustYawOutDeg/AdjustPitchDownDeg`, lokalny obrót kamery przy zmianie, bez dodatkowego renderu;
   szkło 3D w kabinie pokazuje tę samą teksturę). Domyślnie **0°**: celowanie TRAKT jest dobrane pod pola R46 (ADR 0042).
6. **Ustawienia: jeden ekran z zakładkami** (`PcSettingsPanel`): **Grafika** (ekran + jakość), **Sterowanie** (przejście do
   panelu kierownica/pedały/kamera; przypisania gdy dostępne), **Dźwięk**, **Rozgrywka** (skala HUD, szczegóły HUD, HUD w
   kabinie, kontrolki dotykowe, jednostki), **Lusterka** (okienka wł./wył., rozmiar, pion, odsunięcie, regulacja,
   **podgląd układu** liczony tym samym `DesktopHudLayout`). Kopie robocze wszystkich zakładek; „Zastosuj” zapisuje
   wszystko, „Przywróć domyślne” dotyczy otwartej zakładki, przejście do „Sterowanie” najpierw stosuje zmiany. Menu
   startowe na PC ma jeden przycisk „Ustawienia” (telefon: „Ustawienia sterowania” jak dotąd).
7. **Wejście w menu** (`MenuCommandMap`, stały układ jak w ADR 0265 P2-3): strzałki/krzyżak/lewa gałka, Enter/A/lewy przycisk
   myszy, Esc/B/prawy przycisk myszy, **Q/E i LB/RB = zakładki**, PgUp/PgDn/prawa gałka/kółko = przewijanie. Klawisze
   wspólne z jazdą (strzałki, E/Q, bumpery, krzyżak, A, B) są bezpieczne tylko dzięki bramce #131: ekran ustawień jest
   właścicielem fokusu (`UiFocus.Push`) → `DriverInputMixer.MenuOpen`; test sprawdza listę wspólnych klawiszy i bramkę.
8. **Teksty** w tabelach (`HudTexts`, `PcSettingsTexts`), po polsku, bez marek (test regex), liczby z przecinkiem.
   „Region niedostępny w tym APK” → „Region niedostępny w tej wersji gry”.

Wartości 720×112, 52, 42 %, 30–60 %, 40 % wolnego widoku, 96 % krycia, 7,5 %, ±6°/±3° — **WORKING_VALUE** (ocena właściciela).

### Tabela kontrastu (WCAG 2.x, wymagane: tekst 4,5:1, elementy graficzne 3:1)
| Para | Kontrast | Wymagane | AA |
|---|---|---|---|
| tekst / panel | 14,66 : 1 | 4,5 | TAK |
| tekst / wiersz | 13,32 : 1 | 4,5 | TAK |
| tekst / przycisk | 11,10 : 1 | 4,5 | TAK |
| tekst / przycisk wciśnięty | 9,60 : 1 | 4,5 | TAK |
| tekst / przycisk włączony (starsze panele) | 7,22 : 1 | 4,5 | TAK |
| tekst drugorzędny / panel | 8,68 : 1 | 4,5 | TAK |
| tekst drugorzędny / wiersz | 7,88 : 1 | 4,5 | TAK |
| tekst drugorzędny / przycisk | 6,57 : 1 | 4,5 | TAK |
| tekst wybranego segmentu (ciemny na jasnym) | 14,66 : 1 | 4,5 | TAK |
| akcent (nagłówek, licznik) / panel | 8,24 : 1 | 4,5 | TAK |
| akcent / wiersz | 7,49 : 1 | 4,5 | TAK |
| ramka fokusu / panel | 8,24 : 1 | 3,0 | TAK |
| ramka fokusu / wiersz | 7,49 : 1 | 3,0 | TAK |
| ramka najechania / panel | 8,68 : 1 | 3,0 | TAK |
| przycisk wyłączony / przycisk | 3,32 : 1 | 3,0 | TAK |
| HUD tekst / pasek 96 % nad białym niebem | 9,00 : 1 | 4,5 | TAK |
| HUD tekst drugorzędny / pasek nad białym niebem | 5,33 : 1 | 4,5 | TAK |
| HUD akcent / pasek nad białym niebem | 5,06 : 1 | 4,5 | TAK |
| HUD kierunkowskaz / pasek nad białym niebem | 3,67 : 1 | 3,0 | TAK |
| HUD światła drogowe / pasek nad białym niebem | 3,70 : 1 | 3,0 | TAK |
| HUD wskaźnik ciśnienia / tor | 5,32 : 1 | 3,0 | TAK |
| ostrzeżenie czerwone: tekst / pole | 4,93 : 1 | 4,5 | TAK |
| ostrzeżenie bursztynowe: tekst / pole | 7,30 : 1 | 4,5 | TAK |
| ramka lusterka / biały obraz | 19,58 : 1 | 3,0 | TAK |

Wzór: luminancja względna WCAG 2.x (sRGB → liniowe, 0,2126/0,7152/0,0722), (L1+0,05)/(L2+0,05). Kontrolny przypadek
#767676/biały = 4,54:1 (test). Kolory: `game/Assets/_Project/Input/Display/UiPalette.cs`.

## Budżet i GC
Pętla jazdy: `DesktopHudLayout.Solve` tylko przy zmianie ekranu/stanu/`HudPreferences.Version`; co klatkę porównania i
wyszukanie gotowych napisów (`HudTexts`), `HudWarnings.Collect` do bufora z pola. Testy: EditMode
`PerFrameHudMaths_DoesNotAllocate` (2000 iteracji układu, widoczności, ostrzeżeń, napisów; `GcAllocCounter`), PlayMode
`PcHudGc0244Tests.DesktopStrip_Extended_PrefsChanging_ZeroGcAlloc` (500 odświeżeń paska + wiersza rozszerzonego na 16:9 i
32:9, ze zmianą preferencji). Render: bez nowych kamer i tekstur poza strzałką 96×80 px (raz); lusterka — bez zmiany liczby
renderów (regulacja to obrót istniejącej kamery). Większe okienka powiększają RT na ekranie, nie RT
(`MirrorHeight` bez zmian) — przy 60 % na 4K możliwe rozmycie (patrz Otwarte).

## Zmienione pliki spoza UI (minimalnie)
- `Gameplay/PcInputBridge.cs`: 1 linia — `ToggleHudDetail` → `HudPreferences.ToggleDetail()` (bez `DrivingLabBootstrap`).
- `Vehicle/Runtime/RenderTextureMirror.cs`: statyczne `AdjustYawOutDeg/AdjustPitchDownDeg`, czysta `AdjustEuler`, obrót
  kamery lusterek głównych tylko przy zmianie wartości.
- `Vehicle/Runtime/GrayboxTractorBuilder.cs`: celowanie lusterek 3 % → 7,5 % na zewnątrz.
- `UI/CabDisplays/CabScreens.cs`: licznik `LiveClusters`.
- `Input/` (własność gameplay-ui): akcja `HudDetail` (I), `ViewCommands.ToggleHudDetail`, nowe czyste klasy w `Input/Display/`.

## Walidacja
- `tools/hud-runner` (dotnet 8 + xUnit, źródła z gry): **11/11** — kontrast (24 pary), układ HUD na 9 monitorach
  (1920×1080, 2560×1080, 3440×1440, 5120×1440, 3840×1080, 4K, 720p, 1920×1200, pionowy 1080×1920) × 3 rozmiary × 3 piony ×
  2 odsunięcia × 128 stanów = **20 736 układów** (w treści, bez nakładania, wolny widok drogi, aspekt szkła, symetria),
  ten sam układ 16:9/21:9/32:9, ostrzeżenia, widoczność, teksty, preferencje, mapa wejść menu.
- `tools/licenses` pytest 27/27, audyt 3827/3827 (font pokryty).
- EditMode `HudRedesign0283Tests` (18) i PlayMode `PcHudGc0244Tests` (+1) — **NIEuruchomione** (brak Unity).
- Wygląd — **UNVERIFIED** do zrzutów z buildu: makiety SVG (`docs/design/hud-0283-*.svg`, generator
  `tools/ui/hud_mockups_0283.py`) to rysunki układu, nie rendery.

## Otwarte
- Ocena właściciela na buildzie (styl, rozmiary, domyślne 42 %, „auto” w kabinie). Krytyk wizualny wg docs/06.
- Pole widzenia R46 przy regulacji ≠ 0 na TRAKT — niesprawdzone (`MirrorFieldOfVisionTests` liczy celowanie z buildera);
  domyślnie 0°, więc bez zmian.
- Rozdzielczość RT lusterek na 4K przy 60 % (ADR 0265 P2-5, `mirrorResolutionScale` tieru PC) — pomiar lidera.
- `ControlSettingsPanel` nadal pokazuje sekcje dotyk/gyro na PC (ADR 0265 Otwarte) — poza zakresem.
- Brak modelu „usterka ABS naczepy” (kafel gotowy, wejście `false`).
- `PcFocusOutline.cs` nieużywany po przejściu na `UiFocus.Decorate` — do usunięcia przez lidera (z `.meta`).
