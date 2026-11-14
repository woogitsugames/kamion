# BRAND-SWEEP-S20 — przegląd marek i logo (CLAUDE.md zasada 8)

Agent X2, sesja 20, gałąź `docs/brand-sweep-s20` od `f2d50b6a9`. Bez Unity, telefonów i `Data/raw` — tylko pliki w gicie.
Status: **gotowy do przeglądu**. Każdy wiersz sprawdzony `git grep -n` / odczytem pliku; czego nie dało się sprawdzić bez
Unity lub LFS, jest oznaczone „możliwe” / `UNVERIFIED`.

## Podsumowanie

- **P0: 1** — napis **„AdBlue”** (zarejestrowany znak towarowy VDA dla płynu AUS 32) na ekranie zegarów kabiny, rysowany
  w runtime (`CabDisplayText.cs:16` → `ClusterLayout.cs:203`).
- **P1: 5** — „AdBlue” w statycznej teksturze ekranu (możliwe), nazwa obiektu komercyjnego **„Kwadrat Park”** w menu
  startowym, **granatowy owal na maszcie** przy salonie samochodowym (możliwy trade dress), własna marka **TRAKT** bez
  badania znaków towarowych, oraz **ścieżka OSM `destination` → drogowskazy** (dziś czysta, bez filtra).
- **P2: 17** — nazwy marek tylko w danych QA/raportach, identyfikatorach, nazwach obiektów, cytatach źródeł; napisy
  instytucji publicznej (PSP) bez godła; splash Unity (wymóg licencji); tablica rejestracyjna i częstotliwość FM do sprawdzenia.
- **Napisy sklepów/stacji w świecie gry: brak.** Nazwy z OSM (`Biedronka`, `McDonald's`, `Circle K`, `Moya`, `BP Wygoda`,
  firmy lokalne) są w danych regionu, ale żaden generator nie zamienia `name`/`brand`/`operator` budynku ani POI na
  geometrię, teksturę, `TextMesh` ani tekst UI (ślad niżej). Szyldy fasad to wyłącznie słowa funkcjonalne
  (`life_props.SIGNS`, pilnowane testem `tests/gis/test_streetscape.py:224`), a `overrides.yaml` konsekwentnie pomija
  napisy i panele marek (l. 2041, 2073–2075, 2371, 2427, 2488; dojlidy l. 4, 44, 62).
- Zmienione w tym PR: tylko ten raport (§ „Zmienione”).

## Ustalenia

Ryzyko: **P0** = cudza marka/logo trafia na ekran gry; **P1** = trafia albo może trafić (stan niezweryfikowany, trade dress,
mechanizm bez filtra, własna marka bez badania); **P2** = nie trafia na ekran (dane, raporty, identyfikatory, cytaty) albo
napis nie jest cudzym znakiem.

| # | plik:linia | co (dokładny ciąg) | kategoria | do buildu / na ekran (dowód) | ryzyko | proponowana neutralna nazwa |
|---|---|---|---|---|---|---|
| 1 | `game/Assets/_Project/UI/CabDisplays/CabDisplayText.cs:16` | `public const string AdBlue = "AdBlue";` | znak towarowy (płyn SCR) | **tak** — `ClusterLayout.cs:203` `Bar(d, 494f, T.AdBlue, ad, …)` rysuje etykietę paska na ekranie zegarów (CabScreens → DisplayCanvas, runtime) | **P0** | `"AUS 32"` albo sam piktogram (kropla) bez napisu; ew. `"SCR"` |
| 2 | `tools/blender/truck/interior/make_textures.py:427` | `(("D", 0.62, white), ("AdBlue", 0.80, blue))` → `display_cluster.png` (l. 444) | znak towarowy | **możliwe** — materiał `MI_Cab_Display:DISPLAY_Cluster` bierze `art-source/truck/interior/export/textures/Displays/T_Display_cluster.png` (`TruckAssetBuilder.cs:412–415`); plik jest wskaźnikiem LFS — nie sprawdziłem, czy zawiera napis ani czy runtime'owe CabScreens zawsze go zasłaniają | P1 | jak #1, regeneracja tekstury |
| 3 | `game/Assets/_Project/Gameplay/GameBootstrap.cs:112` | `"Trasa G3-A — Kwadrat Park, brama, Bieżeństwa"` | nazwa obiektu komercyjnego (park handlowo-magazynowy; `docs/REFERENCES.md:13` wymienia jego szyldy obok logo sieci) | **tak** — pozycja menu startowego (`BootMenu.Create`, l. 123), gdy WorldC jest w buildzie; czy to zarejestrowany znak — `UNVERIFIED` | P1 | `"Trasa G3-A — baza, brama, Bieżeństwa"` |
| 4 | `Data/Regions/bialystok-industrial-c/overrides.yaml:2063`, `:2092` | „a lattice mast with a dark blue oval board at the north corner” → `{kind: sign_mast, … board_w_m: 4.6, board_h_m: 1.3, … material: bin_plastic_blue}` (salon samochodowy, wpis `g3b-frontage-furniture-showroom` l. 2042) | możliwy trade dress marki samochodowej (kształt + kolor tablicy) | **tak** — `tools/worldgen/streetscape/frontage.py:370` `sign_mast` buduje owalną tablicę z jasnym obrzeżem, bez napisu; której marki salon — `UNVERIFIED` | P1 | tablica prostokątna / pylon w neutralnym kolorze albo usunięcie masztu |
| 5 | `docs/plan/TRACK-A.md:93`; użycie: `tools/blender/truck/exterior/a6_export.py:222`, `exterior/build.py:72`, `interior/build_interior.py:1792–1794`, `docs/ART_BIBLE.md:40` | własna marka **TRAKT** (`art-source/truck/brand/trakt.svg`); TRACK-A: „wymagają … wyszukania w bazach znaków towarowych (EUIPO eSearch, UPRP) — **nie zrobione**” | własna marka bez badania kolizji | **tak** — emblemat i napis na grillu, napis na piaście kierownicy | P1 | bez zmiany nazwy; badanie EUIPO/UPRP (klasy 9/12/28/41) przed wydaniem — wymaga zgody właściciela na zapytania |
| 6 | `tools/worldgen/streetscape/signs_route.py:130` | `dest = (a.get("destination") or {}).get("v") or ""` | ścieżka OSM → napis | **tak (mechanizm)** — tag OSM `destination` drukowany na drogowskazach; obecne wartości w `roads.graph.json` są bez marek (`Centrum handlowe`, `Lotnisko`, miasta, osiedla) | P1 (kolejne regiony) | filtr (allowlista miejscowości/kategorii) + test |
| 7 | `Data/Regions/bialystok-industrial-c/buildings.geojson:1` (plik jednowierszowy) | `"name": "Biedronka"` (osm:way/1537575627), `"McDonald's"` (osm:way/1537575626), `"Circle K"` (osm:way/236606116), `"Moya"` (osm:way/236606117), `"Centrum Handlowe (w budowie)"`, `"Zielona Wiata"` | sklep / gastronomia / stacja | **nie** — `name` nie jest czytane przez `buildings_mesh.py` ani eksport; `build_world.preview_buildings` (l. 634–647) je pomija; `tools/ui/build_nav_map.py` zapisuje obrysy bez nazw (`strings` w `Nav/*.bytes`: tylko nazwy ulic); jedyny odczyt: `tools/worldgen/validate/common.py:168` → raport w `docs/` | P2 | nie przenosić `name` (budowane w `tools/worldgen/buildings.py:206`) albo zostawić jako dane QA pod strażnikiem |
| 8 | `Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json:1` (+ `bialystok-dojlidy/…:1`) | `"name":"BP Wygoda"`, `"name":"Circle K"`, `"operator":"Circle K"`, `"Biazet S.A."`, operator `Enea Ciepło`, `PGE Dystrybucja`, `masterpress`, `Redkom Development`, `PUHP Lech`, `BKM` | stacje / firmy lokalne | **nie** — `streetscape/sources.py:54` wybiera tagi `amenity` do geometrii; w `streetscape/*` brak odczytu `name`/`operator` z POI (jedyne `get("name")`: `signs_route.py:132` = nazwa ulicy z grafu) | P2 | — |
| 9 | `Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json:2297, 2304, 3397, 3434` | `"destination:lanes": "\|\|stacja paliw BP"` | stacja | **nie** — raport QA; `signs_route` czyta tylko `destination`; `roads.graph.json` nie ma `destination:lanes` | P2 | — (ale uwzględnić w filtrze z #6, gdyby kiedyś czytać `destination:lanes`) |
| 10 | `Data/Regions/bialystok-dojlidy/landmarks_d51.authored.json:69, 111`; `generated/landmarks_d51.json:35, 128, 231, 327, 363` | `"BISON"`, `"browar Dojlidy"`, `"Rosti Poland"`, `"KAN - Centrum Logistyczno Produkcyjne - magazyn"`, `"Bravilor Bonamat"`, `"Masterpress"` | firmy lokalne | **nie** — czyta je tylko `tools/worldgen/qa/region_landmarks.py` (raport) | P2 | nie przenosić do UI ani napisów (np. cele dostaw: neutralne „zakład tworzyw”, „browar”) |
| 11 | `docs/reports/world-validator/bialystok-industrial-c/world_validator.json:2584, 3144`; `docs/reports/map/candidates.json:343, 536` | `"Circle K"`, `"Moya"`, `"Browar Dojlidy"`, `"Centrum Handlowe Fasty"` | stacja / firma | **nie** (raporty) | P2 | — |
| 12 | `art-source/world/landmarks/kwadrat_park/kwadrat_park_meta.json` (`landmark_depot_kwadrat_park_00…15`, `_roof`); `game/Assets/_Project/World/Import/WorldSceneBuilder.cs:118` `"Spawn_KwadratParkGate"`; `Data/Regions/bialystok-industrial-c/region.yaml:2` | nazwa obiektu komercyjnego w identyfikatorach | firma | **nie na ekran** — nazwy GameObjectów/assetów w hierarchii sceny (są w buildzie jako dane) | P2 | `landmark_depot_base_*`, `Spawn_DepotGate` przy następnej regeneracji |
| 13 | `art-source/world/materials/_src/sets_fire_station.py:756` | `("lettering", "PAŃSTWOWA  STRAŻ  POŻARNA"), ("number", "998")`; godło celowo pominięte (l. 771–772, ADR 0070) | instytucja publiczna (napis), nie znak firmowy | **tak** — tekstura fasady JRG 2 | P2 | zostawić; nie dodawać emblematu PSP |
| 14 | `tools/worldgen/streetscape/props.py:407–418`, `furniture_textures.py:135–139` | wiata BKM wg „Wzór plastyczny wiaty przystankowej”; tablica „no operator logo, no invented stop text” | wzór miejski bez logo | **tak** (geometria i atlas) | P2 | zostawić; logo BKM nie dodawać |
| 15 | `tools/blender/truck/exterior/materials.py:472` | `("BI 4K271", …)` przednia tablica ciągnika | inne — numer w realnym formacie | **tak** | P2 | `UNVERIFIED`, czy numer jest przydzielony; rozważyć układ, który nie wskaże istniejącego pojazdu |
| 16 | `game/Assets/_Project/UI/CabDisplays/CabDisplayText.cs:45–46`; `tools/blender/truck/interior/make_textures.py:499` | `RadioBand = "FM"`, `RadioFreq = "98,4"`; `"FM  98,4"` | inne — możliwa częstotliwość realnej stacji w Białymstoku | **tak** (ekran DIN) | P2 | `UNVERIFIED` — sprawdzić w wykazie UKE; ew. częstotliwość niezajęta w regionie |
| 17 | `game/ProjectSettings/ProjectSettings.asset:20–21` | `m_ShowUnitySplashScreen: 1`, `m_ShowUnitySplashLogo: 1` | logo silnika | **tak** (splash) | P2 — wymóg licencji Unity Personal, nie wada | — |
| 18 | `game/Assets/_Project/UI/Diagnostics/DiagnosticsOverlay.cs:174–178` | `"  ·  Unity "`, `SystemInfo.deviceModel`, `SystemInfo.graphicsDeviceName` | nazwy producentów z urządzenia | **tak**, ale tylko nakładka diagnostyczna | P2 | ukryć nakładkę w buildzie wydaniowym |
| 19 | `game/Assets/_Project/Rendering/Runtime/QualityProfile.cs:158–166` (+ `Rendering/Resources/QualityProfile.asset:321`) | `note = "Galaxy A16 (Helio G99): …"`, `"Snapdragon 8 Gen 1-3 - UNMEASURED"`, `"Galaxy Z Fold (Adreno 840…)"` | nazwy urządzeń | **możliwe** — `reason = r.note` (l. 182) wraca do wołającego (log/diagnostyka) | P2 | — (użycie opisowe) |
| 20 | `CabDisplaySource.cs:12, 20–23, 43`; `DisplayPalette.cs:23`; `ClusterLayout.cs:15, 196`; `TruckAssetBuilder.cs:1300`; `tools/blender/truck/exterior/chassis.py:3, 194–199`; `exterior/materials.py:654` (`adblue_blue`); `exterior/a6_export.py:118, 128` (`adblue_cap`, `adblue_tank`); `concepts.py:457, 463`; `interior/sightline_test.py:11, 36` | `AdBlue…` w identyfikatorach, komentarzach i nazwach obiektów FBX | znak towarowy | **nie na ekran** (kod, nazwy GameObjectów) | P2 | razem z #1: `Def…`/`Scr…`, `def_tank`, `def_cap` |
| 21 | `docs/ART_BIBLE.md:45, 54, 58`; `docs/07_CIEZAROWKA_3D.md:17`; `docs/plan/TRACK-A.md:65, 151`; `docs/prompts/REFERENCE_IMAGE_PROMPTS.md:15` | „AdBlue” w specyfikacji ekranu i podwozia | znak towarowy w dokumentacji | nie | P2 | po decyzji lidera ws. #1 ujednolicić („płyn AUS 32”) |
| 22 | `docs/VEHICLE_REFERENCE_DATA.md:18, 19, 24`; `docs/REFERENCES.md:13, 38–40, 60–77`; `docs/LICENSES.md:143`; `art-source/truck/interior/BACKLIGHT.md:9`; ADR `0044:181`, `0048:46`, `0056:49–51`, `0087:11`, `0104:60`, `0122:11`, `0134:29`; `docs/11_DECYZJE_WLASCICIELA.md:51, 55`; `docs/owner/*`, `docs/reports/*` | Volvo D13K500 (S1), ZF TraXon (S2), Bridgestone M-STEER 001 (S7), zdjęcia Scania/Volvo/DAF/Krone/Wielton, sklepy w opisach zdjęć (Biedronka, Orlen, Circle K, Shell, Poczta Polska…) | marki w cytatach źródeł, atrybucjach, recenzjach | nie | P2 — użycie opisowe/atrybucja, dozwolone | bez zmian |
| 23 | `docs/reports/visual/REVIEW-2026-11-10-r7.md:101`, `REVIEW-2026-11-10-r8.md:130`, `REVIEW-2026-11-09.md:124, 126` | „Skojarzenie z DAF XF z lat 2002–2006 zostaje”, „nadal DAF XF z lat 2002–2006”, „DAF 95 / EuroStar era”, „1980s Jelcz” | podobieństwo bryły kabiny do realnego modelu | **możliwe** — dotyczy kształtu kabiny w grze; stanu po B2/A8 nie sprawdziłem (brak Unity) | P2 | krytyk wizualny: ocenić bieżącą kabinę wg `docs/07_CIEZAROWKA_3D.md:39` |

Poza zakresem (pliki agenta 0201, jedna linia): `game/Assets/_Project/Vehicle/Physics/Definitions/Data/amt12_od_traxon_class.gearbox.json`
— „TraXon” (nazwa handlowa ZF) w nazwie pliku danych pojazdu; do oceny przez 0201/lidera.

### Ścieżka „nazwa z OSM → ekran” (dowód)

1. `tools/worldgen/osm_extract.py:110` i `buildings.py:206` przenoszą `name` do `buildings.geojson`.
2. Geometria budynków: `streetscape/buildings_mesh.py` nie czyta `props["name"]` (jedyne `name` w l. 922 to pole
   override'u przepisane do `props`, bez dalszego użycia); `terrain_mesh/gltf.py:105–167` nadaje węzłom nazwy z kodu
   (chunki/prototypy), nie z OSM.
3. Mapa nawigacji: `tools/ui/build_nav_map.py:12–15, 164–189` zapisuje tabelę nazw **ulic** z `roads.graph.json`;
   `strings -n 6` na `Nav/bialystok-industrial-c{,_route}.bytes` daje wyłącznie nazwy ulic.
4. Napisy w świecie: `life_props.SIGNS` (HALA A–D, BIURO, RECEPCJA, DOSTAWY, PORTIERNIA, MAGAZYN, SERWIS),
   `overrides.yaml` `text:`/`lines:`/`top`/`left`/`right` (nazwy ulic/rond, kierunki, czasy przejazdu), `signs_route.py`
   (`destination`, `ref`, nazwa ulicy) — marek brak; jedyny kanał bez filtra to `destination` (#6).
5. Tekstury z tekstem: `sets_fire_station.py` (#13), opony (`exterior/materials.py:416–439`, `trailer_build.py:526–532`:
   rozmiar, indeksy, „M+S”, fikcyjny DOT, bez marki), ekrany kabiny (`make_textures.py`: #2, #16), tablica (#15).

## Nazwy plików z marką (`git ls-files`, poza `research/`)

| plik | uwaga |
|---|---|
| `artifacts/cab-r1/reference-daf-xf-cockpit-960.jpg` | Commons CC0 (`artifacts/cab-r1/REFERENCES-0112.md:12`), „Nie trafia do tekstur gry” — nie w buildzie |
| `docs/reports/visual/truck-A8/ref-volvo_vs_truck-34.jpg` | montaż ze zdjęciem Volvo FH (licencje w `docs/REFERENCES.md`) — nie w buildzie |
| `artifacts/kwadrat-r9/*`, `artifacts/kwadrat-r11/*`, `docs/reports/visual/world-c/*kwadrat*` | nazwa obiektu w nazwach dowodów — nie w buildzie |
| `game/…/amt12_od_traxon_class.gearbox.json` | poza zakresem (0201), patrz wyżej |

## Fałszywe trafienia

- `\bMAN\b`: zmienne `MAN` (manifest) w `tests/gis/test_cc0_scans.py:22`, `tools/audio/el_verify.py:28`; `MAN-MISMATCH`
  w `tools/nav-runner/Runner/Program.cs:56`; z `-i` — angielskie „man”.
- `Iveco` (-i, 117 z 119): podciągi innych słów. `\bZF\b`: tablica `ZF` w `tools/blender/truck/interior/build_interior.py:1599–1650`.
- `\bVW\b`: szerokość pobocza `VW` w `tools/worldgen/roads/meshing.py:216–247`.
- `Shell`/`shell`: powłoka (`hedge_shell_*.png`, „Shell point” w `life_cars.py:1062`, „Shell:” w ADR 0041, „Shell =” w overrides).
- `Orange`: „orange peel” (`TruckExterior.shader:59, 617`, ADR 0038). `Netto`: „netto” w recenzjach.
- `Dojlidy`, `Fasty`, `Krywlany`, `Białostoczek`: nazwy dzielnic/osiedli/lotniska (toponimy), nie marki — z wyjątkiem
  „Browar Dojlidy”/„browar Dojlidy” (#10, #11).
- `Retarder`, `Tachograph`, `AMT`, `ABS`, `PTO`, `ECO`: terminy ogólne (nie znaki).
- `Samsung`, `Galaxy`, `Snapdragon` w `docs/`, `scripts/`, `CLAUDE.md`: opis sprzętu testowego (nie w grze; w grze #18–19).
- `Unity` w asmdef/komentarzach; `Google` w `ProjectSetup.cs:26` (wymóg Google Play) i `BuildCommands.cs:74` (API Unity).
- `\bbrand\b`: prawie wyłącznie komentarze „no brand”/„brand-neutral” i własna marka (SVG `bielik/narew/trakt`).
- `BKM` (operator komunikacji miejskiej) w komentarzach wiat — opis źródła wzoru, nie napis.

## Zmienione

Brak zmian treści poza dodaniem tego raportu. Przejrzałem kandydatów do neutralizacji w dokumentacji poza `research/`:
wszystkie wystąpienia marek pojazdów to cytaty źródeł (S1/S2/S7), atrybucje zdjęć referencyjnych, zapisane decyzje
właściciela (D30/D34) albo historyczne recenzje, w których marka jest treścią ostrzeżenia (#23). Przepisanie ich
zatarłoby proweniencję, więc nie jest „oczywistym przypadkiem”. „AdBlue” w specyfikacji (#21) zależy od decyzji lidera
ws. #1 — zmiana samej dokumentacji rozjechałaby ją z kodem.

## Rekomendacje dla lidera

1. **#1 (P0) przed bramką z ekranem kabiny:** zamienić etykietę na `AUS 32` lub piktogram; w tym samym zadaniu #2
   (regeneracja `T_Display_cluster.png`), #20 (identyfikatory, nazwy obiektów FBX) i #21 (docs). Wymaga regeneracji
   assetów kabiny — zadanie dla agenta z Unity/Blenderem.
2. **#3:** neutralna etykieta trasy w menu (nazwa „Kwadrat Park” zostaje w danych/QA). Decyzja właściciela, jeśli
   nazwy realnych obiektów w UI mają zostać.
3. **#4:** ocena wizualna salonu G3-B: czy granatowy owal na maszcie wskazuje konkretną markę; jeśli tak — zmiana kształtu
   lub koloru tablicy w `overrides.yaml` (+ ADR 0129 aktualizacja).
4. **#5:** badanie TRAKT w EUIPO eSearch/UPRP przed jakimkolwiek wydaniem (zgoda właściciela na zapytania zewnętrzne).
5. **#6:** filtr `destination` w `signs_route.py` (allowlista miejscowości, osiedli i kategorii jak „Centrum”, „Lotnisko”;
   reszta odrzucona z logiem) + test w `tests/gis`.
6. **#15, #16:** sprawdzić numer tablicy i częstotliwość FM; oznaczyć `UNVERIFIED` w kodzie, dopóki nie sprawdzone.
7. **Strażnik w CI (tylko opis, nie dodany):** skrypt `scripts/brand-guard.py` uruchamiany w jobie `gis` w
   `.github/workflows/ci.yml`:
   - **lista zakazana** w pliku danych (np. `tools/brand-guard/denylist.txt`) — wzorce PCRE z § „Metoda” + `AdBlue`,
     `TraXon`, `I-Shift`, nazwy z tagów `brand`/`operator` regionów (generowane z `streetscape_sources.json` przy budowie);
   - **sprawdzane tylko źródła tekstu, który trafia do gry**: literały `"…"` w `game/Assets/**/*.cs` poza `Editor/` i
     `Tests/`; pola `m_Text`/`text:` w `*.unity`/`*.prefab`/`*.asset`; w `overrides.yaml` pola `text`, `lines`, `top`,
     `left`, `right`, `sign`; `life_props.SIGNS`; wartości `destination`/`name`/`ref` krawędzi `roads.graph.json`
     (te trafiają na drogowskazy i mapę); tabela nazw w `UI/Resources/CabDisplay/Nav/*.bytes`; napisy w generatorach
     tekstur (`ImageDraw.text`, `render_text_texture` — eksport listy napisów do JSON przez generator i grep tej listy);
   - **wyjątki** w pliku `tools/brand-guard/allow.txt` (ścieżka + wzorzec + uzasadnienie), np. cytaty w
     `docs/VEHICLE_REFERENCE_DATA.md`, `docs/REFERENCES.md`, `docs/LICENSES.md`; `research/**` w ogóle poza zakresem;
   - wynik: exit 1 i lista `plik:linia: ciąg` przy nowym trafieniu; raport dołączany jako artefakt joba.
   Uzupełnieniem jest rozszerzenie istniejącego `test_facade_signs_are_functional_text_only` o tablice bramownic
   (`overrides.yaml`) i etykiety `signs_route`.
8. Nazwy POI z OSM (`name`/`operator`) można zostawić w danych QA, ale **nie** dodawać ich do napisów, celów dostaw,
   UI ani nazw zleceń bez neutralizacji — warto to zapisać jednym zdaniem w `docs/06_GRAFIKA_ANTI_AI_SLOP.md` §7
   (decyzja lidera, ten PR jej nie wprowadza).

## Metoda (do powtórzenia)

Zakres: wszystkie śledzone pliki tekstowe (`git grep -I`) **poza** `research/**`, `artifacts/**` (treść — tylko nazwy plików,
§ „Nazwy plików”), `HANDOVER.md` oraz plikami lokalnego agenta 0201: `game/**/Vehicle/**/*.json`,
`tools/physics-runner/Tests/**`, `DrivingLabSceneBuilder.cs`, `ContactShadowCaster.cs`.

```bash
EXCL=(':!research/**' ':!game/**/Vehicle/**/*.json' ':!tools/physics-runner/Tests/**' ':!**/DrivingLabSceneBuilder.cs' \
      ':!**/ContactShadowCaster.cs' ':!artifacts/**' ':!HANDOVER.md')
# liczniki: case-sensitive i -i dla każdego wzorca z listy niżej
git grep -I -P -c  "<wzorzec>" -- . "${EXCL[@]}"
git grep -I -P -ci "<wzorzec>" -- . "${EXCL[@]}"
# trafienia z linią
git grep -I -P -n "<wzorzec>" -- . "${EXCL[@]}"
# nazwy plików z marką (w tym artifacts/)
git ls-files | grep -v '^research/' | grep -i -P 'scania|volvo|daf|mercedes|iveco|renault|krone|wielton|schmitz|kogel|man_|orlen|shell|circle|biedronka|lidl|mcdonald|bp_|moya|bison|rosti|adblue|bridgestone|michelin|zf_|traxon'
```

Lista wzorców (PCRE, case-sensitive; `-i` tylko jako licznik pomocniczy):

- Producenci pojazdów i części: `Scania` `Volvo` `\bMAN\b` `\bDAF\b` `Mercedes` `\bBenz\b` `Actros` `Iveco` `Renault`
  `K(ö|oe)gel` `\bKrone\b` `Schmitz` `Wielton` `Michelin` `Bridgestone` `Continental` `Goodyear` `Allison` `\bZF\b`
  `Eaton` `Voith` `Knorr` `WABCO` `\bBosch\b` `Cummins` `Jacobs` `Jake ?brake` `Webasto` `Garmin` `Kenworth` `Peterbilt`
  `Freightliner` `\bMack\b` `Tatra` `\bJelcz\b` `Solaris` `Autosan`; nazwy handlowe: `AdBlue` `TraXon` `I-Shift`
  `Intarder` `Opticruise` `PowerShift` `Tautliner` `Cargobull`; modele: `Golf|Passat|Octavia|…|Actros|TGX|XF|CF|FH|FM`.
- Stacje: `Orlen` `Lotos` `\bBP\b` `\bShell\b` `Circle ?K` `Statoil` `\bMoya\b` `\bAmic\b`.
- Handel i usługi: `Biedronka` `\bLidl\b` `Kaufland` `Auchan` `Carrefour` `(Ż|Z)abka` `\bNetto\b` `\bDino\b` `Stokrotka`
  `Leroy` `Castorama` `\bOBI\b` `Media ?Markt` `RTV ?Euro` `Rossmann` `\bHebe\b` `Pepco` `McDonald` `\bKFC\b`
  `Burger King` `InPost` `Paczkomat` `\bDPD\b` `\bDHL\b` `Poczta Polska`.
- Firmy lokalne / z OSM regionów: `Pronar` `Samasz` `Agrobud` `(Ż|Z)ubr` `Kompania Piwowarska` `Dojlidy` `Polmos`
  `Biaglass` `Fasty` `Biazet` `Enea` `PGE` `BKM` `PUHP` `Społem` `Rosti` `Bison|BISON` `Masterpress` `Bravilor` `Biawar`
  `Bieldruk` `Cefarm` `Arsenal` `Kwadrat` `Browar` `Redkom` `Mitex|MITEX` `Bocaro` `TEDi` `Sinsay` `KiK` `Giełda Rolna` `KAN`.
- Banki, telekomy, auta osobowe, inne: `\bOrange\b` `T-Mobile` `Polsat` `\bPKP\b` `\bPKO\b` `Pekao` `Santander` `mBank`
  `Toyota` `Volkswagen` `\bVW\b` `Skoda|Škoda` `\bOpel\b` `\bFord\b` `\bFiat\b` `Peugeot` `Citro(ë|e)n` `\bAudi\b`
  `\bBMW\b` `Hyundai` `\bKia\b` `Dacia` `Nissan` `\bHonda\b` `Samsung` `Galaxy` `Snapdragon` `Unity` `RMF` `Radio ?ZET`.
- Tagi OSM i logo: `brand:wikidata` `\bbrand\b` `\boperator\b` `logo` `emblem` `herb` `godło` `Straż|STRAŻ` `PSP`.

Dodatkowo (poza grep): skrypt Pythona (`python -I`, tylko odczyt) wypisał wszystkie wartości kluczy `name`, `brand`,
`operator`, `shop`, `amenity`, `destination`, `destination:lanes` ze śledzonych `*.json`/`*.geojson` w `Data/`,
`art-source/`, `game/`, `tools/`, `docs/reports/{world-validator,map}`, osobno atrybuty krawędzi `roads.graph.json`
(`name`, `ref`, `destination`) i `strings` z wysyłanych plików nawigacji
`game/Assets/_Project/UI/Resources/CabDisplay/Nav/*.bytes`. Ścieżkę „czy napis trafia na ekran” śledziłem w kodzie
(konsumenci `buildings.geojson`, `streetscape_sources.json`, `roads.graph.json`; generatory tekstur z `ImageDraw.text`,
`render_text_texture`, `TextMesh`, `UnityEngine.UI.Text`, `CabDisplayText`).

## Inwentaryzacja (liczba linii, case-sensitive / `-i`; tylko wzorce z ≥ 1 trafieniem)

| wzorzec | CS | -i | uwaga |
|---|---:|---:|---|
| Scania | 25 | 25 | docs (referencje zdjęć, recenzje) |
| Volvo | 61 | 63 | docs (źródło S1, referencje, recenzje, decyzje D30/D34) |
| `\bMAN\b` | 8 | 168 | CS: 3 to zmienna `MAN` (manifest) w kodzie; -i: słowo „man” |
| `\bDAF\b` | 11 | 11 | docs |
| Mercedes / Benz / Actros | 4 / 3 / 1 | | docs |
| Iveco | 2 | 119 | -i: fałszywe (podciąg) |
| Renault | 3 | 3 | docs |
| Krone | 4 | 4 | docs, ADR 0122 |
| Wielton | 7 | 9 | docs |
| Bridgestone | 5 | 5 | docs (źródło S7) |
| `\bZF\b` | 23 | 273 | CS: docs + zmienna `ZF` w `build_interior.py`; -i: „zf” w innych słowach |
| Voith / Bosch | 1 / 3 | | docs (źródła literaturowe) |
| Peterbilt / Freightliner / Mack / Jelcz / Solaris | 2 / 2 / 3 / 2 / 1 | | docs |
| Orlen | 4 | 4 | docs (recenzje M52) |
| `\bBP\b` | 8 | 59 | `fidelity_qa.json`, `streetscape_sources.json`, docs |
| `\bShell\b` | 8 | 244 | 2 × docs-recenzje; reszta „shell” (powłoka) |
| Circle K | 10 | 10 | `buildings.geojson`, `streetscape_sources.json`, raporty |
| Moya | 3 | 3 | `buildings.geojson`, raport walidatora |
| Biedronka | 6 | 6 | `buildings.geojson`, recenzje |
| Netto | 4 | 19 | wszystkie: słowo „netto” |
| Pepco | 1 | 1 | `docs/REFERENCES.md` |
| McDonald | 2 | 2 | `buildings.geojson` |
| DPD / Poczta Polska / Pronar | 2 / 4 / 1 | | recenzje |
| Dojlidy | 87 | 481 | głównie nazwa dzielnicy/regionu (fałszywe); „Browar Dojlidy” osobno |
| Fasty | 4 | 4 | nazwa osiedla (fałszywe) |
| Orange | 4 | 57 | „orange peel”, kolor (fałszywe) |
| PKP | 2 | 2 | recenzje |
| Toyota / Ford | 2 / 1 | | recenzja ZIP-ów |
| `\bVW\b` | 11 | 39 | zmienna `VW` w `meshing.py` (fałszywe) |
| Samsung | 60 | 61 | docs/skrypty (telefony testowe) |
| `\bbrand\b` | 79 | 79 | komentarze „no brand”, własna marka TRAKT |
| `\boperator\b` | 43 | 43 | C# `operator`, tag OSM w `streetscape_sources.json` |
| AdBlue | — | 48 | kod UI kabiny, generatory Blendera, docs |

Zero trafień: Kögel, Schmitz, Michelin, Goodyear, Allison, Knorr, WABCO, Cummins, Jacobs, Webasto, Garmin, Kenworth, Tatra,
Autosan, Lotos, Statoil, Amic, Lidl, Kaufland, Auchan, Carrefour, Żabka, Dino, Stokrotka, Leroy Merlin, Castorama, OBI,
Media Markt, RTV Euro AGD, Rossmann, Hebe, KFC, Burger King, Paczkomat, DHL, Samasz, Agrobud, Żubr, Kompania Piwowarska,
Polmos, Biaglass, T-Mobile, Polsat, PKO, Pekao, Santander, mBank (CS), Volkswagen, Opel, Fiat, Peugeot, Citroën, Audi, BMW,
Hyundai, Kia, Dacia, Nissan, Honda, `brand:wikidata`.
