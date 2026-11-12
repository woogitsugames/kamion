# ADR 0150: mapa, minimapa i GPS z własnego grafu

Status: proponowany (2026-11-12, gałąź `gps-map`, gameplay-ui). Polecenie właściciela 12.11 20:5x: „trzeba dodać mapę, żeby
ustawić trasę, i podgląd mały mapy, żeby wiedzieć, gdzie jest, i żeby GPS kierował”; doprecyzowanie 21:0x: „głos GPS potem,
teraz aby było sobie można ustawić”. Etap 5 (`docs/03`): „HUD + GPS z własnego grafu + nazwy ulic” — tu najmniejsza
kompletna wersja dla regionu `bialystok-industrial-c`. Bez zmian ProjectSettings / Packages / asmdef.

## Decyzja

### 1. Graf routingu z naszych danych (KRTG v1)
- Nowy moduł `tools/worldgen/navgraph/build_route_graph.py` (stdlib; odświeżenie zakazów skrętu przez pyosmium):
  `roads.graph.json` (OSM ODbL + BDOT10k, z provenance) → `game/Assets/_Project/UI/Resources/CabDisplay/Nav/<region>_route.bytes`
  (36,2 KB: 550 węzłów, 646 krawędzi, 277 jednokierunkowych, 26 nazw ulic). `oneway=-1` odwrócone w generatorze, ronda =
  jednokierunkowe, `access=no` / `hgv=no` / `service=emergency_access` = zakaz dla ciężarówki (dozwolone tylko jako cel),
  `access=private|destination|customers|delivery` i `service=driveway` = kara 600 s (wjazd tylko gdy trzeba).
  Prędkość: limit z OSM (źródło zapisane; limit domyślny potoku nie jest pokazywany jako znak — UNVERIFIED).
- **Zakazy skrętu:** 7 relacji `type=restriction` z OSM dotykających dróg regionu (`Data/Regions/<id>/turn_restrictions.json`,
  z sha256 ekstraktu), wszystkie zmapowane na krawędzie (from way / via node / to way). Pozostałe skręty: brak danych =
  dozwolone, **UNVERIFIED** z ulicą.
- Odtwarzalność: pytest `tools/worldgen/navgraph/tests` sprawdza, że plik w repo == świeży build (bez ręcznych zmian).
  Regeneracja: `uv run --project tools/worldgen python tools/worldgen/navgraph/build_route_graph.py --region <id> [--refresh-restrictions --pbf <ekstrakt>]`.
  Nie wpięte do `build_world.py` (równolegle pracują agenci świata; tak jak `tools/ui/build_nav_map.py`) — lider może dopisać krok.

### 2. Routing (C#, `Game.Core.Navigation`, testowany w EditMode)
- `RouteGraph` (parser + przyciąganie do drogi), `RoutePlanner` (A* po **skierowanych krawędziach**: dokładne zakazy skrętu
  i zakaz zawracania zestawem 16,5 m — zawracanie tylko na ślepym końcu, kara 240 s), `RoutePath` (prealokowane tablice:
  linia trasy, nazwy, limity, manewry), `RouteTracker` (rzut na trasę, następny manewr, „potem”, zjazd z trasy).
- Koszt = czas przejazdu ciężarówki: 80 % limitu OSM (max 80 km/h), bez limitu: klasa drogi 15/30/40/55 km/h; skręt w prawo
  6 s, w lewo 10 s, ostry 20 s; kierunek startu przeciwny do osi pojazdu +300 s. Wszystko **WORKING_VALUE** (brak
  zmierzonych czasów przejazdu).
- Manewry z topologii (nie z krzywizny linii): skręt tylko na węźle z wyborem; „trzymaj się lewej/prawej” na rozwidleniu;
  rondo = jeden manewr z numerem zjazdu; dwa skręty w tę samą stronę < 30 m (przejazd przez pas dzielący) = jeden.
- Przeliczenie po zjechaniu z trasy: > 25 m od linii lub jazda pod prąd trasy przez 2,5 s → A* od bieżącej pozycji
  i kierunku. Nieudane przeliczenie zostawia starą trasę. Plan Kombatantów ↔ Andersa: **0,24 ms** w edytorze (średnio z 20),
  212–413 rozwiniętych stanów; **0 B GC** dla 10 planów + 2000 kroków śledzenia (test). Telefon: do zmierzenia przez lidera.
- Region przycięty do 2 km ma części połączone tylko poza kaflem (np. Olsztyńska/Buska, 55 węzłów) — tam „Brak dojazdu”.

### 3. Pełna mapa (`UI/Navigation/FullMapView`)
- Otwierana dotknięciem minimapy. **Gra pauzuje** (Time.timeScale 0 + AudioListener.pause): mapa zasłania drogę, a
  nawigacje ciężarowe przyjmują cel tylko na postoju; jazda „na ślepo” pod mapą byłaby nieuczciwa. Wstecz (Android) zamyka.
- North-up, wektorowo z danych regionu (siatka dróg i budynków wypiekana raz, ta sama co ekran w kabinie); nazwy ulic wzdłuż
  ulic (łańcuchy odcinków o tej samej nazwie, etykieta na najdłuższym prostym odcinku, obwódka, bez nakładania); przesuwanie
  palcem, szczypanie / kółko = zoom, +/−, „Pojazd”; tap = pinezka na najbliższej drodze (≤ 80 m), panel: cel (ulica),
  odległość w linii prostej, „Wyznacz trasę” / „Wyczyść”; z trasą: długość, czas (model kosztu), „Wyczyść trasę” / „Jedź”.
  Podziałka i atrybucja „© OpenStreetMap contributors” na mapie. Żadnych zewnętrznych kafelków.
- Cel przeżywa restart / zabicie procesu (PlayerPrefs `nav.dest.<region>`; po starcie trasa liczona ponownie).

### 4. Minimapa + prowadzenie w HUD (`MiniMapView`, `NavHudLayout`)
- Strefa: lewy górny róg między krawędzią bezpiecznego obszaru a lewym lusterkiem (lub zestawem wskaźników), nad grupą
  kierownicy — 340 × 440 jednostek (min. 220 × 250). Nowy solver obok ADR 0079 (bez zmian `HudLayout`); test: brak kolizji
  z każdą strefą HUD i z polem chwytu kierownicy (ADR 0135) na 6 ekranach × 4 DPI × wycięcie × 128 stanów; w stanie jazdy
  pokazana na wszystkich (telefon 2340×1080, Fold 1080×1200 / 2176×1812 / obrócony, tablet). Ukryta przy telemetrii dev.
- Treść: pasek manewru (piktogram, odległość, ulica skracana „...”; „potem” jako mały piktogram), mapa heading-up
  (zoom 1,7 px/m na postoju → 0,75 px/m przy 70 km/h), trasa przed pojazdem, flaga celu, strzałka pojazdu, znak limitu (tylko
  limit z OSM), róża N, pasek z bieżącą ulicą. Paleta jak ekran nawigacji w kabinie (dzień/noc razem ze światłami).
- Koszt: 1 rysowanie siatki regionu + 1 partia dynamiczna na odświeżenie; 15 Hz na Low, 30 Hz wyżej; **0 B GC** na
  odświeżenie (test PlayMode); CPU **0,138 ms** średnio (300 odświeżeń w edytorze, po rozgrzaniu), 484 wierzchołki partii.
  Draw calls: 2 rysowania do render texture na odświeżenie (podkład + partia) + generowanie mipmap, w kanwie HUD 2 obrazy
  (ramka + RawImage); render texture 334×434 px na telefonie 1080p. Pomiar na telefonie: lider.

### 5. Ekran nawigacji w kabinie
`NavLayout.Live`: gdy GPS jest aktywny, ekran pokazuje trasę gracza, ten sam manewr, pozostały dystans, przyjazd (z modelu
kosztu) i ulicę celu; bez trasy — mapę i bieżącą ulicę. Bez GPS (testy) — dotychczasowa trasa startowa G3.

### Głos
**Nie teraz** (decyzja właściciela 21:0x). Następny krok: komunikaty PL nagrane / syntezowane z licencją komercyjną
(np. ElevenLabs Pro właściciela — `reference-elevenlabs`), wyzwalane z `NavGuidance` (500 m / 200 m / teraz), kolejka audio
w `Game.Audio`; teksty w tabeli lokalizacji.

## Konsekwencje / otwarte
- `DrivingLabBootstrap`: 2 linie (instalacja GPS po HUD; Wstecz najpierw zamyka mapę). Plac testowy bez regionu = brak GPS.
- Pas ruchu: trasa = oś jezdni z OSM; brak prowadzenia pasami (`turn:lanes` jest w danych dla 174 krawędzi — następny krok).
- Zakazy dla ciężarówek z OSM są skąpe (6× `hgv=no`); brak ograniczeń tonażu/wysokości w koszcie (2× `maxheight` w danych).
- Wygląd: zrzuty `artifacts/gps-map/*.png` (Fold 1080×1200 i 2176×1812, telefon 2340×1080, ekran kabiny) — tło 3D to plac
  testowy (test nie ma sceny świata), mapa to region przy pozycji na trasie. Na telefonie: do oceny właściciela.

## Testy
- pytest `tools/worldgen/navgraph/tests` (5): odwrócenie `oneway=-1`, flagi, mapowanie zakazów na podzielone krawędzie,
  round-trip, determinizm, plik w repo == build, poprawność geometrii regionu.
- EditMode `NavRoutingTests` (11): wczytanie grafu (550/646/7/277), znane trasy Kombatantów → Andersa (jezdnia SE: 1640 m
  przez al. Tysiąclecia; jezdnia NW: zawrócenie na Rondzie Bieżeństwa), 300 losowych par (jednokierunkowe i zakazy
  przestrzegane na każdej trasie; 123/126 par z rdzenia ciężarowego zaplanowane — 3 wymagają zawracania), wybór kierunku
  wg osi pojazdu, syntetyczne: objazd jednokierunkowej, zakaz skrętu i `only_*`, manewr w lewo, numer zjazdu z ronda,
  zjazd z trasy → przeliczenie, nieudane przeliczenie zachowuje trasę, 0 B GC.
- PlayMode `NavHudTests` (3 + 1 zrzuty): strefy bez kolizji, minimapa 0 B GC, mapa pauzuje / ustawia / czyści trasę / Wstecz.
  Regresje: `CabScreensTests`, `HudLayoutTests` zielone (47/47 z `NavHudTests`).
