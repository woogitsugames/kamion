# Szlabany krawędzi i magentowe domy — s24

Gałąź: `edge-barriers-cli`, baza `f08172268`, implementacja `e6184e7b2`. Praca i zapisy wyłącznie w tym worktree. Unity, player i buildy nie były uruchamiane. Obejrzano dostarczone `top/p1_t0510.png` i `top/p1_t2560.png`.

**Stan:** naprawione wykryte błędy kodu zamknięć i wysokości; dodana walidacja materiałów. Dokładna przyczyna magenty z t=510 pozostaje **UNVERIFIED**. Nie ma podstaw do deklarowania naprawy strippingu ani konkretnego brakującego shadera tej klatki.

## Przyczyny i zmiany

Lokalizacje „przed” odnoszą się do bazy `f08172268`; lokalizacje „teraz” do implementacji.

| Problem | Przyczyna w kodzie | Zmiana |
|---|---|---|
| Widoczny szlaban mimo otwartego szwu | Przed: `WorldEdgeBuilder.cs:180` grupował wszystkie zamknięcia w promieniu 150 m, niezależnie od strony. `WorldStreamer.cs:903` wyłączał indywidualne obiekty kolizji, ale `:909` wyłączał wspólną siatkę dopiero, gdy **wszystkie** zamknięcia w jej AABB były otwarte (`EdgeSides.cs:130`). Przy grupie obejmującej różne szwy otwarty przejazd zachowywał widoczną zaporę. | Teraz: `WorldEdgeBuilder.cs:187` / `:1098` budują renderer i collider na jednym `Closure_*`. Nie ma zbiorczej widoczności zależnej od sąsiednich zapór. `WorldStreamer.cs:908` przełącza cały obiekt po osiągnięciu Ready przez oba kafle; opuszczany/brakujący/niedogotowany kafel pozostawia szew zamknięty. Nie czeka na zmianę kafla pod pojazdem. |
| Zła strona otwierania na zakręcie przy narożniku | Przed: `WorldStreamer.cs:839` zgadywał szew z przedłużenia tangenta przy odsuniętym szlabanie. Droga może skręcić między szlabanem a granicą. | `ReadExits` zapisuje faktyczną stronę przecięcia granicy w `exitSide`, `PlanClosures` przenosi ją do danych, streamer preferuje ją względem zgadywania. Zamknięcia różnych znanych stron nie są scalane. Stare dane None mają fallback. |
| Szlaban na wysokości dachu / obcego kafla | Przed: `WorldEdgeBuilder.cs:597` wykonywał globalny RaycastAll, a `:600` brał najwyższy collider. Generator oznacza także dachy budynków jako beton (`tools/worldgen/streetscape/materials.py:518`); importer nazywa je `col_concrete` (`WorldSceneBuilder.cs:387`). Brak filtrowania właściciela dopuszczał geometrię innego root. Po `ResolveClosures` przesunięty środek zachowywał stare Y. | `WorldEdgeBuilder.cs:581` wybiera tylko kolizję nawierzchni pod bieżącym root, odrzuca dachy/przeszkody i strome trafienia, preferuje drogę, następnie teren. `EdgeClosureRules.cs:20` definiuje źródła. Ponowne próbkowanie po resolve (`WorldEdgeBuilder.cs:125`). Siatka pojedynczego zamknięcia jest lokalna, a Y/heading nakładane raz przez Transform. `col_asphalt` jest właściwą kolizją także dla drogi betonowej: `tools/worldgen/roads/meshing.py:134,1194`. |
| Szlabany bez otaczającego terenu podczas ładowania | `BuildTileScene` zapisuje chunki wyłączone, lecz WorldEdge aktywny. Przed: nowy edge był widoczny podczas rozłożonej na klatki aktywacji chunków. | `WorldStreamer.cs:631` ukrywa WorldEdge w czasie Activating; `:664` pokazuje go dopiero po Ready i przeliczeniu szwów. |
| Możliwość zapisania magentowych ścian | Przed: `RegionImporter.cs:715–716` pozostawiał null przy nieznanym ID materiału, tylko wypisując warning. Materiały tworzone przez Shader.Find nie przechodziły wspólnej kontroli błędów kompilacji. To potwierdzona luka, **nie dowód przyczyny t=510**. | `RegionImporter.cs:354,716` wymaga poprawnego materiału; `WorldMaterialValidation.cs:14` odrzuca brak materiału, InternalErrorShader i znane błędy kompilacji z kontekstem region/chunk/warstwa/slot/material/shader/keywords. Guard scen playera kontroluje też wcześniej zaimportowane renderery i materiały instancji. |

`TerrainY` ograniczono również do własnego root, aby obcy kafel nie kształtował fartucha. Tooltip `WorldBoundary.Closure.localPos` poprawiono: Y to absolutna wysokość lokalnej geometrii (EVRF2007), a nie wysokość nad anchorem. Kod TilePlacement zachowuje wspólne odniesienie pionowe; nie znaleziono dowodu błędu floating origin.

## Magenta t=510 — co wiadomo

Małe domy mogą używać `M_plaster_beige`, `M_plaster_cream`, `M_plaster_light`, `M_plaster_grey` na **Kamion/World PBR** (`WorldPbrMaterials.cs:188`), w tym `_UV_MESH0`, `_SPLASH`, `_RUNOFF` (`:294,415,439`). Far-field używa **Kamion/World Surface** (`RegionImporter.cs:487`); ten shader renderuje również widoczne szlabany. Sam kadr nie identyfikuje materiału domu.

Materiały są serializowane w `sharedMaterials`, a nie znajdowane wyłącznie przez Shader.Find w playerze (`WorldSceneBuilder.cs:356`). `ShaderVariantStripper.cs:25` nie wymienia słów kluczowych fasad. Nie dodano Always Included ani Resources bez dowodu. Statyczny odczyt manifestów industrial-c/Maczka/Kleeberga nie wykazał brakującego ID w listach materiałów chunków; nie wyklucza to rozjazdu manifestu z rzeczywistym GLB/sceną użytymi przez build.

W worktree nie ma zaimportowanych `_Generated/World` ani GLB w Data/raw. Dostarczony raport i PNG nie zawierają logu kompilacji D3D11 / przypisania rendererów tych domów. Potwierdzenie konkretnego `M_*.mat`, błędu wariantu albo brakującego slotu pozostaje otwarte. Nowa walidacja wykrywa brakujące referencje i już zgłoszone błędy shaderów; nie dowodzi zachowania każdego wariantu po strippingu platformowym.

## Testy i review

- `dotnet test tools/spawn-runner/Tests/Tests.csproj --no-restore --logger "trx;LogFileName=edge-barriers.trx" --results-directory artifacts/edge-barriers-cli`: **30/30 PASS**, 0 pominiętych. Runner kompiluje rzeczywiste pliki z game/, tak jak istniejące runnery. W tym **17 nowych przypadków EdgeClosureRulesTests**: wszystkie stany sąsiada, brak root/unload, niezależne strony, dach/obcy root/przeszkody, priorytet droga–teren w obu kolejnościach, brak powierzchni i niezmienność Y po rebase.
- Wynik lokalny: `artifacts/edge-barriers-cli/edge-barriers.trx`.
- `EdgeClosureImportTests`: **6 dodatkowych przypadków EditMode, NIEURUCHOMIONYCH** zgodnie z zakazem startu Unity: raycast pod rootami -137/-155 m z dachem i cudzym kaflem, siatka bez podwójnego Y/heading, brak materiału, wspólne wyłączanie renderer/collider, zakrzywiony wyjazd z zachowanym exitSide.
- `git diff --check`: bez błędów białych znaków. Kompilacja całego projektu Unity i shadery D3D11: niezweryfikowane.
- Niezależny przegląd kodu przez agenta `review_materials`: bez wskazanych blokujących błędów implementacji. Uwaga z review wdrożona: build odrzuca stare `ClosureGroup_*`; wymagany pełny import regionów.

## Integracja i weryfikacja — osobna sesja z Unity/buildem

1. Dla **każdego regionu używanego w buildzie** wykonać pełny import: `pwsh scripts/import-region.ps1 -Region <id> -Tiers 'Low,High' -BuildTarget Win64`. Odtwarza pełne sceny i `_Tile`, materiały oraz krawędzie. Sam `RebuildEdgeBatch` nie wystarcza: zapisuje tylko pełne sceny, a usuwa stare współdzielone subassets siatek. Guard celowo zatrzyma build starych kafli zamiast ponownie wypuścić znany błąd.
2. `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`: nowe testy integracyjne oraz istniejące WorldEdge*, streaming i start clearance. Sprawdzić wysokości finalnych zamknięć po scalaniu/przycinaniu, zwłaszcza knyszyn-w i rejony wiaduktów.
3. Na domach z klatki t=510 odczytać renderer, slot, asset materiału, shader i keywords. Porównać z manifestem/GLB. Sprawdzić log kompilacji **D3D11**, szczególnie wariant fasady PBR z `_SPLASH/_RUNOFF`, oraz raport wariantów buildu. Jeśli guard zgłosi brak materiału, uzupełnić właściwy manifest/GLB i ponowić pełny import; nie zastępować go arbitralnym materiałem.
4. Powtórzyć przejazd Windows: industrial-c→Maczka, Maczka→Kleeberga, klatki odpowiadające t=680/920/2560. Zarejestrować `ready` i `edges open` przed dojściem do zapory, zgodność widoczności i kolizji, zamknięcie przy brakującym sąsiedzie i po unload, Y przy poziomym rebase. Wymusić wolne ładowanie sąsiada i sprawdzić brak zapór wiszących podczas Activating.
5. Zmierzyć koszt: geometria pojedynczego zamknięcia bez zmian, ale więcej niezależnych rendererów może zwiększyć draw calls (dwa submeshe na szlaban; jednocześnie dokładniejsze culling). Nie zmierzono FPS, VRAM ani budżetu buildu. Bramka wizualna pozostaje otwarta.
