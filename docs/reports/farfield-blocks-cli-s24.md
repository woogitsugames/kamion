# Far-field na DK65 — raport s24, 2026-11-19

Gałąź: `farfield-blocks-cli`. Implementacja: `33db1f4cf`; baza: `35e9c3d122`.
Bez push. Wszystkie zapisy w tym worktree. Nie uruchamiano Unity ani `build_world`.

## Przyczyna i dowody

Obejrzano wskazany zrzut właściciela oraz `shot_t1200.png` i `shot_t1210.png` z
`win-build/artifacts/win/runs/20261119-140004`. Na pierwszej klatce bryły zasłaniają
jezdnię, na drugiej ich nie ma. To DK65/Ełcka, `dk65-04`, nie DK8.

Lokalizacje w **bazie `35e9c3d122`**, przed poprawką:

- `tools/worldgen/streetscape/far_field.py:166`: kompresja odległości do ≤660 m
  poza granicą kafla. Geometria dalekiego budynku może trafić na drogę sąsiada.
- `tools/worldgen/streetscape/far_field.py:383`: wykluczenie obejmuje tylko własny
  bbox i budynki regionu; brak własności innych kafli i korytarza tras.
- `game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs:953` i `:970`:
  sektor wyłączany dopiero przy Ready sąsiada, ponownie włączany po unloadzie.
- `tools/worldgen/streetscape/far_field.py:1357`, `:1427`, `:1451`: Low pomija
  dachy wyższych bloków/hal/biur; biura prowadzą okna do samej krawędzi dachu.
  Palety od `:80` są kopiami wcześniejszych wartości, rozjechanymi z materiałami kafli.

**Korekta hipotezy ze zgłoszenia:** log `player.log:544`→`:548` nie zawiera load/Ready
między t1200 i t1210. Rebase jest wcześniej (`:541`), a dk65-05 Ready dopiero `:595`
(między DIAG t1307 i t1312), 384 m od kafla. Nie przypisujemy więc dokładnego zniknięcia
z tej pary klatek przejściu Ready. ID konkretnej bryły i bezpośredni wyzwalacz zniknięcia
są UNVERIFIED bez inspekcji sceny/playera. Defekt własności oraz skokowa polityka sektora
wynikają bezpośrednio z kodu; poprawka usuwa oba niezależnie od tego wyzwalacza.

## Zmiana

- `far_field.py:382`: stałe wykluczenie bbox wszystkich zarejestrowanych kafli oraz
  ≥400 m od tras `route_start.json/points_en`. 400 m = domyślne 25×(8+1+1)+150
  streamera, WORKING_VALUE. Rezerwacja pozostaje przy niedostępnej scenie/małym budżecie.
- `far_field.py:1736`: sprawdzenie całego prostokąta raw i po kompresji przed
  generacją, również dla skyline. Odrzucone budynki nie zostawiają masek urban apron.
  Testowane są też obrysy, których centroid jest poza wykluczeniem.
- GIS cache i jego liczniki źródłowe pozostają nienaruszone; QA/manifest dostają osobny
  `streaming_building_policy` z licznikami i hashami tras/registry, niezależnymi od LF/CRLF.
  Zmiana trasy działa przy następnej generacji far-field nawet z istniejącym cache GIS.
- `EdgeSides.cs:75`, `WorldStreamer.cs:907` i `:976`: kierunkowe sektory w stronę
  sąsiadów grafu są ukryte już przy Register, przed pierwszym renderem; nie zależą od
  cyklu ładowania. Sąsiad diagonalny rezerwuje oba kierunki. Nie zmieniono gotowości
  zamknięć drogi/apron ani fizyki.
- `far_field.py:80`, `:1344`, `:1371`, `:1451`: palety z materiałów kafli, zamknięte
  dachy obu tierów, nieokienne pasy pod dachem także na Low i w biurach. Domy zachowują
  dachy dwuspadowe. Bez nowych materiałów, tekstur, shaderów, colliderów i draw calli
  wynikających z podziału siatek; sumy tris po realnej generacji pozostają UNVERIFIED.

Kompromis: przy aktywnym streamerze znika cały sektor w kierunku zarejestrowanego
sąsiada, także lasy i także gdy scena tego sąsiada jest unavailable. Przed doczytaniem
będzie mniej zastępczego tła. Gdy streamer nie jest instalowany (żadna scena sąsiada
nie jest dostępna), budynki nadal chroni filtr generatora. Zmiana nie realizuje
cross-fade zwykłych chunków ani skyline poza korytarzem. Wygląd i budżet wymagają
przejazdu po przebudowie; nie deklarujemy pełnej bramki wizualnej.

## Testy

- **pytest: 85 PASS, 1 SKIP** w sześciu plikach `test_far_field*.py`; pominięty test
  wymaga nieobecnego raw extraction cache. Nowy plik `test_far_field_streaming.py`:
  **28 PASS** — bbox przyszłych kafli, bufory całych obrysów i końców tras, kompresja
  przenosząca bryłę w wykluczenie, skyline, rzeczywiste trasy korytarza, dachy,
  palety, hashe oraz integracja generacji z maskami i audytem źródłowym.
- **.NET: 35/35 PASS**, `dotnet test tools/spawn-runner/Tests/Tests.csproj`.
  Kompilowane są rzeczywiste wspólne źródła C#9 i testy EditMode, w tym 5 nowych
  przypadków rezerwacji kierunków i cyklu Unloaded→Loading→Activating→Ready→Unloading.
  To nie wykonanie Unity EditMode ani kompilacja całego MonoBehaviour WorldStreamer.
- `git diff --check`: PASS. Niezależne review generatora, testów i runtime: bez blokera.
- Dowody lokalne: `artifacts/farfield-blocks-cli/{pytest.log,pytest.xml,dotnet.log,farfield.trx}`.

Powtórzenie pytest (środowisko lokalne `.venv`, bez uruchamiania generatora świata):

```powershell
. ./scripts/env.ps1
.venv/Scripts/python.exe -m pytest tests/gis/test_far_field_streaming.py tests/gis/test_far_field.py tests/gis/test_far_field_boundary.py tests/gis/test_far_field_industrial_facade.py tests/gis/test_far_field_lod1.py tests/gis/test_far_field_terrain_source_0227.py -q
dotnet test tools/spawn-runner/Tests/Tests.csproj
```

## Kafle do przebudowy

Zmiana dotyczy wszystkich backdropów. **49 istniejących manifestów far-field**, oba
tiery Low/High; nie wystarczy zmienić samego `dk65-04`, bo proxy może należeć do
innego załadowanego kafla. Lista dokładna, grupowana tylko dla czytelności:

- `bialystok-bojary`, `bialystok-dojlidy`, `bialystok-industrial-c`, `bialystok-kleeberga`,
  `bialystok-knyszynska`, `bialystok-maczka`, `bialystok-mickiewicza`, `bialystok-porosly`, `bialystok-wygoda`;
- `dk65-01`, `dk65-02`, `dk65-03`, `dk65-04`, `dk65-05`, `dk65-06`, `dk65-07`, `dk65-08`, `dk65-09`, `dk65-10`, `dk65-11`;
- `dk65-monki-01`, `dk65-monki-02`, `dk65-monki-03`, `dk65-monki-04`, `dk65-monki-05`, `dk65-monki-06`, `dk65-monki-07`;
- `dk8-s8-jeroniki`, `dw671-jasionowka-01`;
- `dw671-tykocin-01`, `dw671-tykocin-02`, `dw671-tykocin-03`, `dw671-tykocin-04`, `dw671-tykocin-05`,
  `dw671-tykocin-06`, `dw671-tykocin-07`, `dw671-tykocin-08`, `dw671-tykocin-09`;
- `knyszyn`, `knyszyn-s`, `knyszyn-w`, `monki`, `monki-e`, `s8-01`, `s8-02`, `s8-03`, `s8-04`, `s8-05`, `tykocin`.

W osobnej sesji uprawnionej do regeneracji/Unity: dla każdego kafla uruchomić sam
etap `tools/worldgen/streetscape/far_field.py --region <id>`, a następnie
`pwsh scripts/import-region.ps1 -Region <id> -Tiers Low,High -BuildTarget Win64`.
Wymagane sceny startowe i `_Tile` obu tierów, następnie nowy player Windows ze zmianą
runtime. Pełny `build_world` nie jest potrzebny do samej korekty backdropu, jeśli
istnieją wejściowe dane GIS, terrain_conformed i pozostałe wygenerowane warstwy.
Po imporcie sprawdzić QA source/retained/excluded, trójkąty Low/High i przejazd
DK65-03→04→05, w tym doczytanie oraz unload za pojazdem; wykonać też właściwy
Unity EditMode w sesji do tego przeznaczonej. Tych kroków tutaj nie wykonywano.
