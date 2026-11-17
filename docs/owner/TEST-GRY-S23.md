# Test gry po sesji 23 — checklista na następny build PC

Dla właściciela. Stan: `origin/main` z 16.11.2026 wieczór (po scaleniu `alt-window-s23`). Wszystko poniżej wyczytane z kodu
i skryptów; źródła (`plik:linia`) są w komentarzu na dole. Klawisze, argumenty i foldery: **`docs/owner/JAK-GRAC-PC.md`**
(tu ich nie powtarzam). Punkty oznaczone **(po scaleniu int-ui — gałąź `int-ui-s23`)** dotyczą kodu, którego jeszcze nie ma
w `main` — sprawdzasz je tylko, jeśli lider zbudował grę z tej gałęzi albo po jej scaleniu.

**Przy każdym problemie zgłoś:** zrzut ekranu (Win+Shift+S), **godzinę**, numer punktu, launcher i argumenty (np.
`Kamion-korytarz.cmd -force-d3d11`), a zaraz po teście zip z **`Zbierz-logi.cmd`** (zawiera `Player.log`; uruchom przed
kolejnym startem gry). `Zbierz-logi.cmd` jest tylko w paczce zip — w gołym folderze buildu skopiuj ręcznie
`%USERPROFILE%\AppData\LocalLow\woogitsugames\Kamion\Player.log` (JAK-GRAC-PC §5–6).

## A. Pełny ekran i okno (alt-window, w `main`)

- [ ] **1. Start bez argumentów.** Jak: `Kamion.exe`. Oczekuj: pełny ekran bez ramki w rozdzielczości monitora.
  Jeśli otwiera się okno: masz zapisany tryb okna w ustawieniach (plik ustawień wygrywa) — zmień w menu (pkt 4) i zgłoś
  tylko, gdy po zmianie nadal okno. Zgłoś: zrzut, godzina.
- [ ] **2. Alt+Enter.** Jak: w grze naciśnij Alt+Enter dwa razy. Oczekuj: pełny ekran → okno → pełny ekran, bez czarnego
  ekranu i bez crasha. Nikt tego nie sprawdził na buildzie (UNVERIFIED). Zgłoś: czy działa, czy po restarcie gra pamięta tryb.
- [ ] **3. Okno zmienialne.** Jak: `Kamion-okno.cmd` (okno 1600 × 900), przeciągnij róg okna myszą. Oczekuj: okno się
  powiększa, obraz się dopasowuje. Uwaga: w `main` plik ustawień projektu ma jeszcze „okno niezmienialne”; zmieni się
  dopiero, gdy lider przed buildem uruchomi `setup-project`. Jeśli okna nie da się powiększyć — zgłoś (to znaczy, że tego
  kroku nie było). Zgłoś: zrzut, godzina, `build-id` z menu.
- [ ] **4. Tryb ekranu z menu.** Jak: menu startowe → „Ekran, grafika, dźwięk” → „Tryb okna” → Zastosuj. Oczekuj:
  pytanie „Zachować nowy tryb ekranu?” i powrót po 15 s bez odpowiedzi. Zgłoś: gdy tryb się nie zmienia albo obraz znika.

## B. HUD, menu z zakładkami, lusterka — **(po scaleniu int-ui — gałąź `int-ui-s23`)**

- [ ] **5. Ustawienia z zakładkami.** Jak: menu startowe → przycisk **„Ustawienia”**. Oczekuj: zakładki Grafika /
  Sterowanie / Dźwięk / Rozgrywka / Lusterka; przełączanie Q / E albo LB / RB na padzie; Esc / B wraca. Zgłoś: co jest
  niewygodne, co nieczytelne (zrzut 16:9, a jeśli masz — 21:9).
- [ ] **6. Nowy HUD w jeździe.** Jak: dowolny region, kamera pościgu (C). Klawisz **I** przełącza tryb rozszerzony HUD.
  Oczekuj: niski pasek na dole ekranu; w kabinie przy działających zegarach na ekranie tylko ostrzeżenia i kierunkowskazy.
  Zgłoś: czy nadal wygląda „AI slop” (D84), co zasłania drogę.
- [ ] **7. Większe lusterka.** Jak: w jeździe L (okienka lusterek wł./wył.); zakładka „Lusterka”: Rozmiar, Położenie w
  pionie, Odsunięcie od krawędzi, Na zewnątrz / do środka, W dół / w górę. Oczekuj: domyślnie 42 % wysokości obrazu (było
  30 %), regulacja 30–60 %. Zgłoś: czy widać naczepę i pas obok przy skręcie, przy jakim rozmiarze najlepiej.

## C. „Koniec mapy”

- [ ] **8. Krawędź regionu bez strumieniowania (w `main`).** Jak: `Kamion-knyszyn.cmd`, jedź do brzegu mapy. Oczekuj:
  napis „Koniec mapy za ok. 250 m: droga zamknięta, zwolnij”, zamknięta droga; za krawędzią zestaw wraca na drogę
  („Koniec mapy: zestaw ustawiony z powrotem na drodze”). Zgłoś: miejsce, czy napis przyszedł na czas.
- [ ] **9. Krawędź korytarza** **(po scaleniu int-ui — gałąź `int-ui-s23`, #163)**. Jak: `Kamion-korytarz.cmd`, zjedź z
  trasy w bok, poza pas kafli. Oczekuj: na szwie z wczytanym sąsiadem **bez** napisu; „Koniec mapy” tylko na zewnętrznej
  krawędzi wczytanych kafli. W `main` granica to jeden duży prostokąt wokół wszystkich kafli — w bok od korytarza napis
  może nie przyjść. Zgłoś: zrzut + godzina, gdy napis pojawi się na szwie albo nie pojawi się na pustym terenie.

## D. Ciągła jazda korytarzem (w `main`)

- [ ] **10. Start korytarza.** Jak: `Kamion-korytarz.cmd` (Knyszyn, `-stream 1`). Jedź DK65 na południe (przez szew z
  knyszyn-s). Oczekuj: droga otwarta na szwie, bez zamknięcia i bez skoku obrazu; w `Player.log` linia `[STREAM] on: …`.
  Jeśli `[STREAM] off: …` — build nie ma sąsiednich kafli, zgłoś. Zgłoś: godzinę każdego przycięcia (> pół sekundy).
- [ ] **11. Odcinek zmierzony.** Jak: `Kamion.exe -scene bialystok-knyszynska -stream 1`, jedź trasą GPS. Oczekuj: przejazd
  do dk65-01 → 02 → 03 bez zamkniętych szwów (jedyny dotąd zmierzony odcinek). Zgłoś: każdą dziurę w drodze, ścianę,
  znikające budynki na szwie (zrzut + godzina).
- [ ] **12. Znane przerwy.** Jak: lista w JAK-GRAC-PC §1.4 „Przerwy” (knyszyn ↔ knyszyn-w, dw671-tykocin-01, Dojlidy bez
  sąsiadów, końce mapy). Oczekuj: tam zamknięcie albo „Koniec mapy” — to znany stan. Zgłoś: tylko, czy przejazd ręczny
  przez szew knyszyn ↔ knyszyn-w działa (nikt nie sprawdził).
- [ ] **13. Jakość kafli w korytarzu.** Jak: tier High (menu „Jakość grafiki”), potem `Kamion-korytarz.cmd`. Oczekuj w
  `main`: treść High tylko, gdy region startowy wczytał się w wersji High. Poprawka „treść z tieru PC” (D44) jest dopiero
  w gałęzi `int-ui-s23`. Zgłoś: czy sąsiednie kafle wyglądają gorzej niż start (zrzut na szwie).

## E. Kabina

- [ ] **14. Prawdziwa kabina w regionie.** Jak: `Kamion-knyszyn.cmd`, kamera kabiny (C). Oczekuj: model TRAKT z wnętrzem
  (jak na telefonie). Import regionu wstawia go tylko, gdy model był zbudowany — jeśli widzisz szarą makietę, zgłoś. Zgłoś: zrzut kabiny na Low i High, co jest brzydkie.
- [ ] **15. Plac testowy = nadal makieta.** Jak: `Kamion-okno.cmd -scene DrivingLab`. Oczekuj: szary ciągnik-makieta
  (graybox) — w `main` i w `int-ui-s23` plac nadal buduje makietę; prawdziwy model jest tylko w regionach. Nie oceniaj tu
  wyglądu kabiny. Zgłoś: nic, chyba że makieta przeszkadza w teście jazdy.

## F. Naczepa 7,63 m

- [ ] **16. Okrąg R50 na placu.** Jak: `Kamion-okno.cmd -scene DrivingLab -trailer 40`, okrąg „OKRĄG R = 50 m”, 20 i
  30 km/h w obie strony (jak próba 3 w FEEL-TEST.md). Oczekuj: naczepa ścina do środka, zestaw stabilny. Fizyka ma już
  7,63 m, ale model 3D naczepy jeszcze 7,70 m — w kamerze orbity sprawdź, czy koła naczepy stoją w nadkolach. Zgłoś: ocenę
  1–5, zrzut kół.
- [ ] **17. Rondo w Knyszynie (DK65 × Tykocka).** Jak: `Kamion-knyszyn.cmd`, trasa z południa prowadzi przez to rondo;
  zrób pełny objazd. Oczekuj: koła naczepy nie wjeżdżają na krawężnik wyspy (krawężnik działa na koła — najechanie widać
  jako podskok naczepy). Zgłoś: zrzut z kamery pościgu, przy jakiej prędkości i torze jazdy koło wjechało.

## G. Zmierzch

- [ ] **18. Zmierzch w regionie.** Jak: `Kamion-knyszyn.cmd -lighting dusk` albo menu startowe → „Pora dnia (trasy)” =
  Zmierzch → „Jedź w wybranym regionie” (wybór z menu działa tylko przy starcie z menu; z launcherem użyj argumentu).
  Oczekuj: zmierzch, światła mijania włączają się same (słońce nisko). Nocy jako osobnej pory nie ma (są: Pochmurno,
  Niskie słońce, Zmierzch); plac testowy ma stałe światło. Zgłoś: zrzuty latarni, świateł ciężarówki, nieba.

## H. Dźwięk

- [ ] **19. Suwaki głośności.** Jak: „Ekran, grafika, dźwięk” → Głośność ogólna / Silnik / Otoczenie / Sygnały kabiny,
  Zastosuj; jedź z retarderem (X / Z) i hamuj. Oczekuj z kodu: „Silnik” ścisza silnik, „Otoczenie” tło, „Sygnały kabiny”
  gong; **retarder, piski hamulców i sprężarka idą tylko za „Głośność ogólna”** (nie za „Silnik”). Zgłoś: czy to
  przeszkadza i co jest za głośno / za cicho (godzina, kamera kabina czy zewnętrzna).

## I. Direct3D 11 a domyślne API (crash D3D12)

- [ ] **20. Domyślne API.** Jak: `Kamion-korytarz.cmd`, 10 min jazdy, w tym kilka razy Alt+Tab i powrót. Sprawdź w
  `Player.log` linię `[BOOT]` z `api='…'` (16.11 crash był na Direct3D 12). Oczekuj: brak crasha. Zgłoś: każdy crash
  (godzina, `Zbierz-logi.cmd`, plik `%LOCALAPPDATA%\CrashDumps\Kamion.exe.*.dmp` — dołącz ręcznie).
- [ ] **21. Ten sam test na Direct3D 11.** Jak: `Kamion-korytarz.cmd -force-d3d11` (osobnego launchera D3D11 nie ma).
  W `Player.log` ma być `api='Direct3D 11…'`. Porównaj z pkt 20: crash tak/nie, płynność (dane klatek w `diag\` w zipie
  z `Zbierz-logi.cmd`), różnice wyglądu (cienie, światła). Zgłoś: oba zipy, podpisane „d3d12” / „d3d11”.

## J. Pad

- [ ] **22. Pad — warstwa Back (D80) jeszcze nie w kodzie.** Ani w `main`, ani w `int-ui-s23` nie ma warstwy „przytrzymaj
  Back + przycisk”; Back nadal = wsteczny R. Jak: zagraj padem wg JAK-GRAC-PC §2. Oczekuj: przypisania jak w tabeli.
  Zgłoś: których akcji brakuje Ci na padzie najbardziej (do D80).

## Na koniec

- [ ] **23. Zbierz logi.** Jak: `Zbierz-logi.cmd` zaraz po teście. Oczekuj: zip na Pulpicie. Zgłoś: zip + ta lista
  z zaznaczonymi punktami i godzinami.

<!-- źródła (main: plik:linia | fragment; gałąź: gałąź:plik:linia — sprawdzane osobno)
scripts/package-windows.py:507 | out["Zbierz-logi.cmd"]
scripts/collect-logs.ps1:9 | Player.log, Player-prev.log, diag\ (summary.json, frametimes.csv)
docs/owner/JAK-GRAC-PC.md:339 | Zbierz-logi.cmd
game/Assets/_Project/Editor/Setup/ProjectSetup.cs:290 | PlayerSettings.fullScreenMode = FullScreenMode.FullScreenWindow;
game/Assets/_Project/Editor/Setup/ProjectSetup.cs:291 | PlayerSettings.defaultIsNativeResolution = true;
game/Assets/_Project/Editor/Setup/ProjectSetup.cs:294 | PlayerSettings.resizableWindow = true;
game/Assets/_Project/Editor/Setup/ProjectSetup.cs:295 | PlayerSettings.allowFullscreenSwitch = true;
game/Assets/_Project/Editor/Setup/ProjectSetup.cs:284 | A saved PC settings file
game/Assets/_Project/Core/Settings/DisplayModes.cs:146 | if (!fromSettingsFile) return false;
game/ProjectSettings/ProjectSettings.asset:102 | resizableWindow: 0
game/ProjectSettings/ProjectSettings.asset:113 | allowFullscreenSwitch: 1
HANDOVER.md:325 | Lider przy najbliższym buildzie: `pwsh scripts/setup-project.ps1` → commit ProjectSettings (resizableWindow 0→1)
scripts/postbuild-windows.py:52 | WINDOW_ARGS = "-screen-fullscreen 0 -screen-width 1600 -screen-height 900"
scripts/postbuild-windows.py:53 | WINDOW_LAUNCHER = "Kamion-okno.cmd"
scripts/postbuild-windows.py:58 | CORRIDOR_NEEDS = ("knyszyn", "knyszyn-s")
scripts/postbuild-windows.py:59 | -scene knyszyn -stream 1 %*
scripts/postbuild-windows.py:184 | launcher_text(f"-scene {rid}")
docs/owner/JAK-GRAC-PC.md:144 | **Alt+Enter**
docs/owner/JAK-GRAC-PC.md:261 | Po zmianie trybu ekranu gra pyta „Zachować nowy tryb
game/Assets/_Project/Gameplay/WorldSafetyNet.cs:35 | Koniec mapy za ok. 250 m: droga zamknięta, zwolnij
game/Assets/_Project/Gameplay/WorldSafetyNet.cs:36 | Koniec mapy: zestaw ustawiony z powrotem na drodze
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:290 | safety-net rectangle of {0} widened to the union of {1} tiles
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:180 | [STREAM] on: start {start.regionId}
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:169 | [STREAM] off: no neighbour tile scene
game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:208 | EndsWith("_High"
Data/Regions/knyszyn/route_endpoints.json:3 | DK65 Obozowa northbound from the south tile edge (seam with knyszyn-s
Data/Regions/knyszyn/route_endpoints.json:3 | -> roundabout DK65/DW671 -> DW671 Tykocka -> Rynek.
docs/owner/JAK-GRAC-PC.md:113 | **Przerwy (z danych w `origin/main`):**
docs/owner/JAK-GRAC-PC.md:128 | Jedyny pomiar przejazdu (HANDOVER 16.11 16:5x): knyszynska → dk65-01 → 02 → 03, 0 zamkniętych szwów.
HANDOVER.md:311 | **int-stream-s23: GATE PASS** (run2: knyszynska→dk65-01→02→03, 4 kafle, 0 zamkniętych szwów
game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:41 | GrayboxTractorBuilder.RootName
game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:346 | var body = GrayboxTractorBuilder.Build(data, dims, mats);
game/Assets/_Project/World/Import/WorldSceneBuilder.cs:111 | Track A7: the TRAKT art truck when it has been built (TruckAssetBuilder), else the graybox.
game/Assets/_Project/World/Import/WorldTruckInstaller.cs:17 | puts the TRAKT tractor (TruckAssetBuilder prefab)
HANDOVER.md:290 | to GRAYBOX — `DrivingLabSceneBuilder.cs` buduje makietę ciągnika
art-source/truck/dims.json:48 | "trailer_axle_z_m":           {"value": [-6.32, -7.63, -8.94]
docs/adr/0280-pierscien-skretu-96-53-rozstaw-sworzen-tridem.md:295 | Model 3D, prefab i shader mają jeszcze −6.39 / −7.70 / −9.01.
game/Assets/_Project/Vehicle/Runtime/Prefabs/Trailer_Curtainsider_Graybox.prefab:543 | z: -7.7}
game/Assets/_Project/Rendering/Shaders/TruckExterior.shader:63 | (-6.39, -7.7, -9.01, 0)
game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:127 | OKRĄG R = 50 m
docs/owner/FEEL-TEST.md:56 | | 3 | **Rondo / okrąg R = 50 m** |
game/Assets/_Project/World/Runtime/WorldCollisionCooker.cs:45 | Layer of kerb collision: hit by the wheel rays
game/Assets/_Project/World/Import/WorldSceneBuilder.cs:386 | Kerbs: wheel rays only
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:248 | string lighting = platform.GetLaunchArgument("lighting");
game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs:249 | if (string.IsNullOrEmpty(lighting)) lighting = menuLighting;
game/Assets/_Project/Gameplay/GameBootstrap.cs:235 | StartRequest.SetRegion("region " + id, id, s, options.LightingId);
game/Assets/_Project/UI/StartMenuOptions.cs:17 | LightingIds = { "overcast", "lowsun", "dusk" };
game/Assets/_Project/UI/StartMenuOptions.cs:18 | LightingLabels = { "Pochmurno", "Niskie słońce", "Zmierzch" };
game/Assets/_Project/UI/BootMenu.cs:270 | Segments("Pora dnia (trasy)"
game/Assets/_Project/UI/BootMenu.cs:295 | DrivingLab ma stałe światło.
game/Assets/_Project/Vehicle/Runtime/TruckLights.cs:19 | below which the automatic low beam switches on
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:31 | VolumeMaster = "Głośność ogólna";
game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:34 | VolumeUi = "Sygnały kabiny";
game/Assets/_Project/Core/AudioMixLevels.cs:8 | engine = <c>EngineAudio.ChannelGain</c>, ambient =
game/Assets/_Project/Gameplay/TruckAudioController.cs:287 | m_Engine.ChannelGain = AudioMixLevels.Engine;
game/Assets/_Project/Gameplay/TruckAudioController.cs:288 | if (m_Ambient != null) m_Ambient.ChannelGain = AudioMixLevels.Ambient;
game/Assets/_Project/Gameplay/TruckAudioController.cs:614 | if (m_Retarder.Valid) m_Retarder.Set(m_RetarderGain * cabRet
game/Assets/_Project/UI/Settings/PcSettingsRuntime.cs:194 | AudioListener.volume = AudioMixLevels.Master;
game/Assets/_Project/Input/DrivingActionCatalog.cs:78 | K("<Keyboard>/x")
game/Assets/_Project/Input/DrivingActionCatalog.cs:79 | K("<Keyboard>/z")
game/Assets/_Project/Gameplay/GameBootstrap.cs:118 | api='{SystemInfo.graphicsDeviceVersion}'
HANDOVER.md:300 | `d3d12: Device failed error (887a0001)`
game/ProjectSettings/ProjectSettings.asset:538 | m_BuildTargetGraphicsAPIs:
docs/adr/DRAFT-d3d11-default.md:176 | (Alt+Tab / klik na drugim monitorze; repro UUM-148214)
docs/owner/JAK-GRAC-PC.md:158 | **nie mają** wariantu D3D11
game/Assets/_Project/Input/DrivingActionCatalog.cs:75 | "Wsteczny (R)", K("<Keyboard>/3"), K("<Gamepad>/select")
docs/11_DECYZJE_WLASCICIELA.md:146 | Back przestaje być wstecznym (R)
-->
<!-- gałąź int-ui-s23 (origin/int-ui-s23 @ 25a66cf98, nie w origin/main; format gałąź:plik:linia | fragment)
int-ui-s23:game/Assets/_Project/UI/BootMenu.cs:291 | tabbed ? Game.UI.Settings.PcSettingsTexts.MenuButton : "Ustawienia sterowania"
int-ui-s23:game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:15 | Tabs = { "Grafika", "Sterowanie", "Dźwięk", "Rozgrywka", "Lusterka" };
int-ui-s23:game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:11 | Q / E lub LB / RB: zakładki
int-ui-s23:game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:53 | Auto: gdy w kabinie działają zegary, na ekranie zostają tylko ostrzeżenia i kierunkowskazy.
int-ui-s23:game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:65 | MirrorSize = "Rozmiar";
int-ui-s23:game/Assets/_Project/UI/Settings/PcSettingsTexts.cs:70 | Klawisz L w jeździe włącza i wyłącza okienka.
int-ui-s23:game/Assets/_Project/Input/Display/HudPreferences.cs:95 | ADR 0265 had a fixed 0.30
int-ui-s23:game/Assets/_Project/Input/Display/HudPreferences.cs:97 | MirrorSizeMin = 0.30f, MirrorSizeMax = 0.60f, MirrorSizeDefault = 0.42f
int-ui-s23:game/Assets/_Project/Input/DrivingActionCatalog.cs:88 | "HUD: tryb rozszerzony", K("<Keyboard>/i")
int-ui-s23:game/Assets/_Project/Gameplay/WorldSafetyNet.cs:85 | streamer.TryInsideDistance(p, out float streamed)
int-ui-s23:game/Assets/_Project/World/Runtime/Streaming/CorridorEdge.cs:20 | ("Koniec mapy", stop) unless it is a seam with a cardinal neighbour
int-ui-s23:game/Assets/_Project/World/Runtime/Streaming/StreamingContentChoice.cs:42 | public static class StreamingContentChoice
int-ui-s23:game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:346 | GrayboxTractorBuilder.Build
-->
