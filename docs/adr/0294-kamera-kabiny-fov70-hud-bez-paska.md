# ADR 0294 — Kamera z fotela: FOV 70° domyślnie, pasek HUD ukryty w widoku z kabiny

Status: **Accepted** — decyzja właściciela (klik) 2026-11-18 (D90 w `docs/11`) po wariantach agenta `cab-view-s24`
(`artifacts/cab-view-s24/WARIANTY.md`, rendery `przed-d90/`). Wdrożenie: gałąź `cab-view-s24`.
Powiązane: D84 / recenzja `docs/reports/REVIEW-2026-11-17-s23-cabin-pc.md` P1-4 („kadr FPP pusty”), ADR 0052 (głowa kierowcy,
punkt oczu R46), 0135 (FOV w portrecie), 0243 / D70 (okienka lusterek), 0283 (HUD monitora), D85 (jednorazowa migracja ustawień).

## Kontekst
- Gra miała domyślnie pionowe FOV 55° (`ControlSettings.cabFov`), kamera QA `cab-driver` 62° — kabina zajmowała ok. 20 % kadru.
- Pomiar z siatek LOD0 (`WARIANTY.md`): lusterka boczne leżą 54–63° (L) i 72–76° (P) od osi; całe lewe lusterko główne wymaga
  poziomego FOV ≥ ~127°. Żadne FOV z suwaka (45–75°) nie wstawi lusterek do kadru — robią to okienka D70.
- W renderach z HUD dolny pasek (prędkość, bieg, ciśnienie) zasłaniał prawdziwe zegary w okienku kierownicy. W grze logika
  ADR 0283 (`HudVisibility`, tryb `Auto` + żywe ekrany kabiny) już chowa pasek w kabinie, ale render QA nie znał trybu kamery
  (brak `CameraRig` → zawsze „nie kabina”), więc pokazywał stan nieodpowiadający grze.

## Decyzja
1. **Domyślne pionowe FOV kamery kabiny = 70°** (`ControlSettings.DefaultCabFovDeg`; poziome 102,4° przy 16:9), wzrok 6° w dół
   bez zmian (`DriverHead.RestPitchDownDeg`), oko bez zmian. Kamera QA `cab-driver` = ta sama stała. Suwak 45–75° co 5° zostaje.
   WORKING_VALUE (brak zdjęcia z fotela, docs/07 §4).
2. **Migracja zapisów: schemat 5 → 6**, jednorazowo: `cabFov` równe staremu domyślnemu 55° → 70°; każda inna wartość (gracz
   zmienił) zostaje. Zapis v6 z 55° to wybór gracza — nie migruje się ponownie. Zapisy bez pól kamery (v0/v1) dostają 70°.
3. **Pasek HUD (prędkość / bieg / ciśnienie) ukryty w widoku z kabiny, widoczny w kamerach zewnętrznych** — zachowanie ADR 0283
   (`CabHudMode.Auto`): w kabinie z żywym zestawem wskaźników tylko rząd kontrolek; „Pasek zawsze” w preferencjach i szczegóły
   rozszerzone (klawisz I) nadal działają jak dotąd. Tryb kamery dla HUD: `DrivingHudContext.IsCabView` → `HudVisibility.IsCabView`
   (żywy rig decyduje; bez rigu `CameraModeOverride` z renderu QA; brak obu = nie kabina). Visual QA: kamery `cab-*` / `*-cab-*`
   renderują HUD kabiny, pozostałe (np. nowa `chase-hud`) — zewnętrzny (`CabViewQa.IsCabCameraId`).

## Konsekwencje
- Telefon (odroczony, D73) dziedziczy domyślne 70° — `ControlSettings` jest wspólne; do ponownej oceny przy powrocie na telefon.
- Szerszy kadr = więcej geometrii kabiny i świata na brzegach; koszt GPU niezmierzony (oczekiwany mały: ta sama scena, inny
  frustum) — do sprawdzenia `pc-metrics.ps1` przy najbliższym pomiarze PC.
- Kamery QA `cab-view-*` (`Game.Cameras.CabViewVariants`) zostają jako narzędzie porównań; `-qaTruckPose` / `-qaCabViewAudit`
  w `visual-qa.ps1`.

## Dowody
`artifacts/cab-view-s24/` (start + rondo, z HUD i bez, 1920×1080 i ≤ 960 px), testy `Tests/EditMode/CabView0294Tests.cs`.
