# ADR 0147: orientacja ekranu — telefony zawsze w poziomie, Fold bez regresji

Status: proponowany (2026-11-12, gałąź `orientation`). Kontynuacja ADR 0135 r3. Zakres: tylko logika orientacji
(`game/Assets/_Project/Gameplay/ScreenOrientationPolicy.cs`); bez zmian ProjectSettings/manifestu.

## Błąd
Agent 0136 (pomiar A16, `artifacts/a16-perf/baseA/A_base1/logcat.txt`): Samsung A16 leżący płasko — gra po ADR 0135
startuje i zostaje w PORTRECIE 1080x2340:
`[SCREEN] AllowAuto (elongated: landscape only) window=1080x2340 aspect=2.17 allowed=--LR orientation=Portrait device=Unknown rotation=0 natural=portrait`
— po tej linii nie ma żadnego `[SCREEN] orientation changed`, czyli obrót nie nastąpił.

## Przyczyna
1. ADR 0135 r3 włączył portret w Player Settings → manifest `fullUser`: aktywność startuje w orientacji, w jakiej ekran
   już jest. Telefon leżący płasko (czujnik: `FaceUp`/`Unknown`) ma obrót 0 = naturalny portret → start w portrecie.
   To było zamierzone (Fold nie może być obracany przy starcie).
2. Skrypt dla okna wydłużonego wysyłał tylko `Screen.autorotateTo*` = L/R + `Screen.orientation = AutoRotation`.
   Autorotacja ograniczona do L/R nie wyprowadza okna z niedozwolonego portretu, gdy czujnik nie zgłasza
   orientacji poziomej (płasko). Zaobserwowane na A16; dokładny mechanizm wewnątrz Unity/Androida (czy Unity
   prosi o `userLandscape`, czy czeka na zdarzenie czujnika) — UNVERIFIED, nieistotny dla poprawki.
   Telefon trzymany w dłoni w poziomie obracał się (czujnik podał poziom), dlatego błąd wyszedł dopiero na stole.

## Decyzja (kod runtime, bez zmian manifestu)
`ScreenOrientationLock.Step(..., DeviceOrientation device)`:
- **Okno wydłużone (max/min > 1,25: telefony, ekran zewnętrzny Folda, tablety 16:10 i 4:3) w pionie**
  (`height > width`) przy nowej konfiguracji ekranu (start, złożenie) → komenda `Lock` na **konkretną orientację
  poziomą** (`Screen.orientation = LandscapeLeft|Right`) — konkretne żądanie obraca natychmiast, z czujnikiem czy bez.
  Wybór: `LandscapeRight`, jeśli czujnik mówi, że telefon jest tak trzymany; w każdym innym przypadku (płasko,
  nieznana, pion) `LandscapeLeft` (standardowy poziom). Nazwy `DeviceOrientation` i `ScreenOrientation` w Unity
  opisują tę samą pozycję fizyczną, więc trzymany poziomo telefon nie obraca się o 180°.
- **Gdy okno stało się poziome** → `AllowAuto` z L/R (jak dotąd): czujnik przełącza między poziomem lewym a prawym.
  Zachowanie systemu „User” (`androidAutoRotationBehavior: 1`) bez zmian: przy włączonej blokadzie obrotu Android
  trzyma bieżący poziom (nie odwraca L↔R) — portretu i tak nie ma, więc gra jest w poziomie niezależnie od blokady.
- Brak pętli: jedno żądanie na konfigurację; jeśli system je ignoruje (okno freeform/multi-window), skrypt czeka bez
  ponawiania (`Phone_OrientationRequestIgnored_NoLoop`).
- Gyro (ADR 0135): blokada bieżącego poziomu po 1,2 s od uzyskania poziomu, wyłączenie gyro → odblokowanie — bez zmian.
- Okno wydłużone już poziome przy starcie → `AllowAuto` od razu, jak w r3.
- **Okno ~1:1 (Fold otwarty, ≤ 1,25): bez zmian względem r3** — w pierwszej klatce blokada BIEŻĄCEJ orientacji, gra
  nigdy nie prosi o obrót. Rozłożenie w trakcie wymuszania anuluje wymuszanie (nowa konfiguracja → gałąź r3).
- Zmiana konfiguracji (złożenie/rozłożenie) bez restartu: jak w 0135 — posortowany rozmiar okna się zmienia, aktywność
  ma wszystkie `configChanges`.
- Próg 1,25 zostaje (zadanie mówiło „≥ ~1,5 → poziom”; przedział 1,25–1,5 to tablety 4:3, które już w r3 były tylko
  poziome — bez zmiany zachowania). WORKING_VALUE.

### ProjectSettings / manifest
Bez zmian. Rozważone i odrzucone: `fullSensor`/`sensorLandscape` w manifeście — zmieniłoby start na Foldzie
(r3 „obraz jak trzymam”, test właściciela OK) albo ignorowało blokadę obrotu użytkownika; poprawka runtime wystarcza.

## Testy
`Tests/EditMode/OrientationPhoneTests.cs`: polityka (A16, S24+, ekran zewnętrzny Folda, 16:9, 16:10, 4:3 → tylko L/R;
Fold wewnętrzny 2176×1812 / 2184×1968 w obu orientacjach → wszystkie); start w pionie płasko/Unknown/pion/FaceDown →
`Lock` LandscapeLeft → po obrocie `AllowAuto` L/R → L↔R bez komend; trzymany w LandscapeRight → LandscapeRight;
start w poziomie → `AllowAuto` jak dotąd; żądanie zignorowane → bez spamu; wymuszenie + gyro; Fold: zewnętrzny →
rozłożenie (blokada bieżącej, r3) → ponowne złożenie; rozłożenie w trakcie wymuszania; **0 B GC** na 10 000 kroków.
`SteerFoldTests.OrientationLock_FoldUnfold_PhoneLandscape_GyroLock` zaktualizowany (złożenie z pionem → `Lock` poziom).

## Do sprawdzenia
1. **A16 (pomiar lidera/a16-perf):** telefon płasko na stole, start → w logcat
   `[SCREEN] Lock (elongated portrait window: force landscape) ... lockTo=LandscapeLeft`, potem
   `[SCREEN] orientation changed Portrait -> LandscapeLeft window=2340x1080` i `[SCREEN] AllowAuto (landscape reached: allow L/R)`.
   Obejście pomiarowe `rq_landscape=1` (DiagLandscape) niepotrzebne. Z blokadą obrotu i bez.
2. **Właściciel na Foldzie:** (a) rozłożony, trzymany jak książka: obraz jak trzymasz, nic się nie obraca (jak r3);
   (b) złożony, ekran zewnętrzny trzymany pionowo → obraz raz obraca się do poziomu; (c) ponowne rozłożenie w trakcie
   gry → bez restartu, obraz jak trzymasz; (d) start na złożonym leżącym płasko → poziom.

## Konsekwencje
- Telefon trzymany pionowo przy starcie obraca się raz do poziomu (jak każda gra pozioma) — bez zmian wobec r3.
- Odczyt `Input.deviceOrientation` co klatkę przy Input System only: działa (logcat A16 `device=Unknown`), bez alokacji.
