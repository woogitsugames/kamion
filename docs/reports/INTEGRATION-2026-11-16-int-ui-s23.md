# Integracja int-ui-s23 — #163 + #166 + #162 + #168 (2026-11-16, s23)

- Worktree `.claude/worktrees/win-build-0261` (Library Win64), gałąź `int-ui-s23` (push), baza `origin/main` + merge `origin/main` (#167).
- Merge commity (kolejno): `10d833012` safetynet-corridor-s23 (#163) · `571c3d109` hud-redesign-0283 (#166) · `6df092ec8` navgraph-eps-s23 (#162) · `c978aef9b` stream-desktop-s23 (#168, polecenie lidera) · `e78a3d7c1` origin/main. `STATUS.md` = main. Konflikt ADR 0273: §11 D36 (#163) + §12 D44 (#168) — obie sekcje (`292b8160d`).
- `Data/raw/derived`: stara kopia z 15.11 usunięta, junction do main. Library i `_Generated/World` (z kaflami `_Tile`) skopiowane z `int-stream-s23` (`robocopy /MIR` usunął dk65-monki-01 i dojlidy → 4 skipy StartClearance).

## Werdykt: **TAK warunkowo** (#166, #162, #168 — TAK; #163 — TAK z otwartym testem)

Warunki: (1) lider decyduje o resecie `ui.touchControls` (§4) — bez tego właściciel **nie zobaczy** nowego HUD; (2) #163: test `OuterEdgeOfTheCorridor_WarnsThenStops` czerwony (reset na krawędzi działa, ostrzeżenia „Koniec mapy” brak — §3), komunikatu w exe nie udało się sfotografować; (3) PlayMode korytarza wymaga lokalnie scen dk65-03/dk65-04_Tile w EditorBuildSettings (decyzja lidera, §1).

## 1. Kompilacja i testy (Win64)

| przebieg | wynik |
|---|---|
| EditMode pełny (po scaleniach #163/#166/#162) | 1144: 1139 / 0 / 5 skip |
| EditMode pełny (po #168 + poprawkach testów) | **1167: 1162 / 0 / 5 skip** (`editmode-20261116-182700.xml`) |
| EditMode filtr po poprawce #168 P1 | **91/91** (`StreamingContentChoice` 26, `WorldStreamerHook0273`, `WorldStreamingPolicy`, `MenuOverlayLayout`, `CorridorEdge`) |
| PlayMode pełny, przebieg 1 | 203: 191 / **4 fail** / 8 skip |
| PlayMode pełny, przebieg 2 (po poprawkach) | 203: 194 / **1 fail** / 8 skip (`playmode-20261116-183642.xml`) |
| PlayMode korytarz + streaming | 3: 2 / 1 fail (`OuterEdgeOfTheCorridor_WarnsThenStops`) |
| `dotnet test tools/hud-runner/Tests` | 11/11 |
| `dotnet test tools/nav-runner/Tests` | 94/94 |
| pytest `tools/worldgen/navgraph/tests` | 55/55 (w tym `test_region_file_is_reproducible`) |
| pytest `tools/licenses/tests` | 27/27 |

Kompilacja Unity bez błędów (kod chmury #163/#166/#168 kompiluje się bez poprawek). Faile i przypisanie (dowód: te same testy zielone w `playmode-20261116-152556.xml` przed scaleniem):

| test | PR | przyczyna | poprawka |
|---|---|---|---|
| `HudLayoutTests.Hud_DeveloperPanel_CollapsedByDefault_OneButton` | #166 | edytor Win64 → HUD monitora; ADR 0283 pokazuje „Panel” tylko w trybie rozszerzonym | test wymusza form factor dotykowy (`OverrideDesktop(false)`), `312fe1843` |
| `MenuOverlayUiTests.MenuBlock_HasTheGeometryThePureTestsUse` | #166 | usunięty osobny wiersz ustawień PC: dół bloku −302 → −272 | obie stałe (EditMode `MenuBlock3Starts` + PlayMode) = −272, `312fe1843` |
| `WorldSafetyNetCorridor…` ×2 („safe poses” = 0) | #163 | trasa startowa dk65-03 biegnie ≤ ~85 m od szwu z dk65-02 (spoza buildu = krawędź zewnętrzna) → żadna poza ≥ 120 m od krawędzi | rozgrzewka z `safeEdgeDistance` 5 m, potem wartość produkcyjna; `312fe1843` → Seam zielony |
| `WorldSafetyNetCorridor.OuterEdgeOfTheCorridor_WarnsThenStops` | #163 | **otwarte**: reset `OutOfBounds` przy krawędzi jest (inside 4,6 m), ostrzeżenia brak; w logu `speed=0 km/h` — warunek ostrzeżenia `|SpeedKmh| > 15` nie jest spełniony przy skryptowym przesuwaniu (`SetPose` co krok). Próba `SetMoving` w kroku nie pomogła (cofnięta `b25155934`). Do rozstrzygnięcia przez autora #163: test vs produkt | — |

EditorBuildSettings: dodałem World_dk65-03 + World_dk65-04_Tile (`52ebb036f`) i **cofnąłem** (`0274114db`) — sceny z EditorBuildSettings trafiają do każdego buildu (PC i APK), a dk65-04 tylko z `_Tile` (Low) po poprawce #168 P1-2 wymuszał `FALLBACK Low` w każdym buildzie PC (zmierzone, `shots/endofmap-high-16x9.log`). Propozycja dla lidera: dokładać je tylko w kolejce testów (np. `test.ps1 -ExtraScenes`) albo zaimportować dk65-04 z `-Tiers Low,High`.

## 2. #162 — trasy nawigacji (Windows)

`build_route_graph.py` dla 12 regionów (C, dojlidy, knyszynska, maczka, dk65-01…05, dk65-07, dw671-tykocin-01, knyszyn) → `*_route.bytes` (rozmiary bez zmian), `--write-golden`: 36 par, 0 nieplanowanych. `git diff -w`: zmienione tylko 8 par regionu C (`lengthM` +0,4…+0,5 m, `costS` +0,1…+0,2 s), manewry bez zmian — zgodnie z prognozą PR. Diff 3214 linii to wcięcia (runner pisze 2 spacje, poprzedni plik 1). Commit `f8fc92bdc`. Uwaga środowiskowa: `dotnet` z PATH nie ma SDK; działa `%LOCALAPPDATA%\Microsoft\dotnet\dotnet.exe` (SDK 10.0.403).

## 3. Build Windows i zrzuty z exe

Build: `kamion-0.1.0-25a66cf98f-regions` (`-Regions knyszyn-s,dk65-11`, exit 0) + przebudowa `0274114db` (§6). Zrzuty bez wstrzykiwania klawiszy: nowe argumenty dowodowe `-ui_touch auto|always|never`, `-ui_hud minimal|extended`, `-ui_mirror size,drop,inset,yaw,pitch`, `-ui_settings_tab N` (`cfd0b15e0`, `UiCaptureArgs` + `OverrideForSession` — tylko sesja, **bez zapisu PlayerPrefs**). Zapis właściciela (`HKCU\Software\woogitsugames\Kamion`) zrzucony `reg export` przed, porównany po; różnił się (Unity zapisuje `Screenmanager*` przy wyjściu) → przywrócony z kopii (`prefs-before.reg`).

Pliki: `artifacts/int-ui-s23/shots/*.png` (+ `.log`), podgląd 1280 px `artifacts/int-ui-s23/view/*.jpg`; kopia w `C:\Users\matma\Documents\Claude\kamion\artifacts\int-ui-s23\`.

| zrzut | 1920×1080 | 2560×1080 |
|---|---|---|
| menu startowe | `menu-16x9` | `menu-21x9` |
| ustawienia: Grafika / Sterowanie / Dźwięk / Rozgrywka / Lusterka | `settings-tab0…4-16x9` | `settings-tab4-21x9` |
| HUD minimalny (kabina) | `hud-minimal-16x9` | `hud-minimal-21x9` |
| HUD rozszerzony (I) | `hud-extended-16x9` | `hud-extended-21x9` |
| lusterka po regulacji (56 %, 15 %, 30 %, +3°, +1,5°) | `mirrors-adjusted-16x9` | `mirrors-adjusted-21x9` |
| HUD z zapisem właściciela (bez `-ui_*`) | `hud-ownerprefs-16x9` | — |
| „Koniec mapy” (próby) | `endofmap-probe-16x9`, `endofmap-high-16x9` — **brak komunikatu** | — |

„Koniec mapy”: w zestawie knyszyn, knyszyn-s, dk65-11 żadna trasa startowa nie kończy się na krawędzi zewnętrznej, więc zbudowałem knyszyn-s + dk65-11 (trasa knyszyn-s kończy się na krawędzi N, knyszyn poza buildem). Oba przejazdy (`-stream 1 -autopilot route -route_s 1900` i `2080 -route_end 2420`) zatrzymały się w tym samym miejscu przy 0 km/h, bez linii `[SAFETY]` i bez komunikatu (zrzut: koniec drogi przed ścianą lasu, widoczne „wiszące” korony drzew). Autopilot staje przed końcem ścieżki, więc warunek „zbliżanie > 15 km/h” nie zachodzi. Komunikat w exe **niezweryfikowany**; do zrobienia ręcznie (jazda klawiaturą do krawędzi) albo z autopilotem ignorującym koniec trasy.

## 4. `ui.touchControls` z zapisu właściciela (krok 4)

- Zapis właściciela: `ui.touchControls = 1` = „zawsze” (odczyt rejestru, tylko do odczytu).
- `UiViewport`: `desktop = !TouchControlsPolicy.Current` → „zawsze” przełącza **cały** układ na dotykowy, nie tylko dokłada kontrolki. Potwierdzone zrzutem `hud-ownerprefs-16x9`: kierownica, pedały, R/N/D, małe lusterka u góry — stary HUD, a nie ADR 0283. Właściciel po scaleniu zobaczy to samo i oceni, że „nic się nie zmieniło”.
- Pochodzenie: w kodzie **nie ma migracji** piszącej ten klucz — piszą go tylko dwa panele ustawień (`ControlSettingsPanel` segment „Pokazuj”, `PcSettingsPanel` „Kontrolki dotykowe”). Kto i kiedy wybrał „zawsze” — `UNVERIFIED` (prawdopodobnie ręcznie w starym panelu ADR 0265).
- Propozycja (decyzja lidera, nie wdrożona): jednorazowa migracja `ui.prefsVersion` < 2 → gdy `touchControls == Always`, build nie-handheld i `Touchscreen.current == null` → `Auto` + log `[CONTROLS] migrated touchControls zawsze→auto (no touch screen)`. Alternatywa: rozdzielić „form factor” od „pokazuj kontrolki” (zawsze = kontrolki na HUD monitora), co jest zgodne z nazwą ustawienia.

## 5. D44 / #168

- Zapis właściciela ma **Medium**: `[STREAM] content Low, budget 800 MB: desktop tier Medium; quality tier Medium from saved choice Medium (menu / PC settings)` (`endofmap-probe-16x9.log`, bez `-tier`). Przyczyna „Low content, 800 MB” = zapisany wybór gracza, nie błąd kodu (zgodnie z ADR 0269/0270). Menu startowe na zrzucie też pokazuje „Medium”.
- Poprawki recenzji `REVIEW-2026-11-16-pr168.md` P1-1/P1-2 (`25a66cf98`): `StreamingContentChoice.HighCoversLow` — High tylko gdy region startowy ma `_High_Tile` i każdy kafel dostępny w Low ma też High; inaczej `FALLBACK Low` z nazwą kafla. +3 testy EditMode. Zadziałało na żywo: build z dk65-04 tylko Low → `FALLBACK Low: tile dk65-04 has a Low tile scene but no _High_Tile`.
- Wynik `-tier High` po usunięciu dk65 z EditorBuildSettings: High content, 1450 MB (§6).

## 6. Kontrola High po przebudowie

Build `kamion-0.1.0-0274114dbc-dirty-regions` (bez dk65-03/04 w EditorBuildSettings; „dirty” = `M_Sky.mat` dotknięty przez Unity), `-tier High -scene dk65-11 -stream 1 -autopilot route` (`shots/stream-high-16x9.log`):

```
[STREAM] content High, budget 1450 MB: desktop tier High; quality tier High from launch -tier (saved choice Medium), start scene World_dk65-11_High
[STREAM] on: start dk65-11, 1/3 neighbour tile scenes available (0 from packs), ... budget 1450 MB (High content, desktop)
[STREAM] ready World_knyszyn-s_High_Tile: load 275 ms, activation 128 ms (64 chunks), ... resident 2 tiles / 220 MB (ESTIMATED)
```

Oczekiwane „High content” — **potwierdzone**. Bez `-tier` gra bierze zapisany wybór właściciela (Medium → Low/800 MB) — to wybór gracza; „auto” w ustawieniach PC przywraca autodetekcję (RTX 5070 → High). Klatki w tym przebiegu: p50 16,67 ms, p99 ≤ 22,6 ms po rozgrzewce (60 fps cap, maszyna obciążona innymi agentami — liczby orientacyjne, nie pomiar budżetu).

## 7. Ocena wizualna wg docs/06 §2 i §7 — co nadal wygląda „jak AI slop” / gra mobilna

Dobre: ustawienia (spokojne, matowe, Inter, odwrócony wybrany segment, czytelne nagłówki z bursztynowym znacznikiem), pasek rozszerzony (duże liczby, wyciszone jednostki), HUD minimalny w kabinie = pusty ekran + żywe zegary (najlepszy stan). Do poprawy (lista na kolejną rundę):

1. **Menu startowe bez tła** — tekst wisi nad szachownicą placu; tytuł, nagłówki „WYBIERZ START” / „OPCJE”, etykiety „Pora dnia”, „Jakość grafiki” i stopka są praktycznie nieczytelne (jasny tekst na jasnym niebie i kafelkach). Potrzebny matowy panel albo render z gry jako tło (docs/06 §7) — dziś wygląda najgorzej z całego UI.
2. **Stopka menu na PC mówi „przycisk Menu”** (wariant dotykowy) mimo `-ui_touch auto` — `m_View.Desktop` jest jeszcze false przy budowie menu.
3. **Nakładka diagnostyczna** („Cel: 60 FPS”, „Jakość: Medium”, „Ukryj”) — szare kafle w rogu menu i ustawień wyglądają jak debug z gry mobilnej; na PC schować domyślnie.
4. **Pasek rozszerzony nachodzi na kierownicę i żywy zegar kabiny** — podwójna prędkość („42” w pasku i prześwitujące „42” zegara pod spodem); w widoku z kabiny tryb rozszerzony powinien ominąć zegar albo nie dublować prędkości.
5. **Strzałki kierunkowskazów** jako dwa pływające kwadraty nad paskiem i samotny przycisk „Panel” w prawym dolnym rogu — wyglądają przypadkowo; zgrupować z paskiem.
6. **Okna lusterek** — czarna ramka 6 j. + ostre prostokąty wyglądają jak „picture-in-picture”; na 21:9 prawe okno wchodzi na prawy pas drogi (przy domyślnym 0 % odsunięcia — ok, po regulacji 30 % zasłania drogę). Rozważyć cieńszą ramkę w kolorze plastiku obudowy i zakaz wejścia w wolny widok drogi przy odsunięciu.
7. **Zakładka „Sterowanie”** prawie pusta, a tekst „Ustawienia sterowania otwierasz z menu startowego” jest mylący, gdy jesteśmy w menu startowym (przy otwarciu przez `-ui_settings_tab` brak przycisku, bo `OpenControlSettings` nie ustawione — artefakt ścieżki dowodowej; w normalnym kliknięciu przycisk jest). Do sprawdzenia ręcznie.
8. **Ustawienia: tekst mały** przy 1080p (opis klawiszy, opisy pod opcjami ~11–12 px), panel w połowie pusty (Grafika, Dźwięk) — można powiększyć font o 1 stopień.
9. **Fokus vs wybór** w segmentach: bursztynowa ramka fokusu na „wyłączone” obok odwróconego „włączone” — dwa różne wyróżnienia obok siebie mylą; fokus subtelniej.
10. **Kafel „ZWOLNIJ POSTOJOWY”** (czerwony) położony dokładnie na zegarze kabiny — zasłania żywy ekran; przesunąć nad deskę.
11. Poza UI (do zespołu świata): „wiszące” korony drzew na krańcu knyszyn-s (far-field/impostory bez pni) — klasyczny czerwony znak docs/06 §2.

## 8. Inne obserwacje

- Autopilot w 2 z 6 przejazdów `-autopilot route -speed 40` stał przy 0 km/h z „ZWOLNIJ POSTOJOWY” (ten sam argument, ten sam build) — niestabilny start autopilota (`UNVERIFIED` przyczyna; maszyna obciążona 91 % CPU).
- Jeden przebieg `mirrors-adjusted-16x9` zawiesił się po `[START]` (zabity po 138 s), powtórka OK.
- Rozdzielczość w zakładce Grafika: „3440 × 1440 · 99,98 Hz” — monitor fizyczny przy skalowaniu Windows (okno 1920×1080).

## Commity (gałąź `int-ui-s23`)

`10d833012` `571c3d109` `6df092ec8` merge · `f8fc92bdc` #162 .bytes + golden · `52ebb036f`/`0274114db` EditorBuildSettings (+/−) · `c978aef9b` #168 · `292b8160d` ADR 0273 · `312fe1843` testy #166/#163 · `cfd0b15e0` argumenty dowodowe UI · `25a66cf98` #168 P1-1/P1-2 · `b25155934` cofnięcie nieskutecznej poprawki testu.

## Dla lidera

- ProjectSettings/Packages/asmdef: bez zmian (EditorBuildSettings dodane i cofnięte, §1).
- Decyzje: §4 (reset `touchControls`), §1 (sceny testowe streamingu), #163 OuterEdge (test vs produkt).
- Komendy: `pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64 -Filter 'Game.Tests.WorldSafetyNetCorridorPlayModeTests'` (z dk65-03/04_Tile w EditorBuildSettings); zrzuty powtarzalne: `pwsh artifacts/int-ui-s23/step3.ps1 -SkipBuild [-Only <wzorzec>]` (skrypt poza gitem, kopia w main artifacts).
