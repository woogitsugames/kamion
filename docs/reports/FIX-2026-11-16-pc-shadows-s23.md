# FIX 2026-11-16: pc-shadows-s23 (brak cieni drzew na PC Low/Medium)

Agent: rendering-perf `pc-shadows-s23`, worktree `.claude/worktrees/win-build-0261` (Library Win64), gałąź `pc-shadows-s23` z `origin/main` `ade885234`.
Maszyna: RTX 5070 / Ultra 7 270K Plus (maszyna deweloperska, **nie referencja**, ADR 0260).

## 1. Wynik: DONE dla przyczyny i poprawki w danych, PARTIAL dla weryfikacji
Przyczynę potwierdzono w playerze Windows przez A/B na istniejącym exe. Poprawka jest w tabeli tierów PC i ma test regresji (czerwony na starej wartości, zielony na nowej). Nowego buildu Windows z poprawką nie zrobiono.

## 2. Ustalenia
1. **Przyczyna: maska LOD cieni drzew na PC Low/Medium = 1 (rzuca tylko LOD0)** — `game/Assets/_Project/Rendering/Runtime/PcTierTable.cs:192` (Low) i `:206` (Medium) w `ade885234` (na gałęzi po dodaniu komentarza pola: `:195` / `:209`), stan przed poprawką: `treeShadowLodMask = 1`. Wartość przeszła z mobilnych tierów (tam to świadomy budżet A16, komentarz w `WorldInstances.cs:639-640`). High i Ultra mają 3.
2. **Mechanizm.** `WorldInstances.Flush` (`game/Assets/_Project/World/Runtime/WorldInstances.cs:641-644`) daje `ShadowCastingMode.On` tylko LOD-om z maski. LOD drzewa wybiera `Render` (`:436`, `:440`) ze skalą `ls = min(lodBias, treeCardLodScale)`. Końce LOD drzew to 20 / 60 / 1000 m (`game/Assets/_Project/World/Import/InstanceImporter.cs:110`), a prototyp dopuszcza cień LOD0+1 (`:138`).
   - Low: `ls = min(1,0; 0,5) = 0,5`.
   - Medium: `ls = min(1,25; 0,5) = 0,5`.
   - LOD0 kończy się więc 10 m od kamery, a **drzewo rzuca cień tylko bliżej niż 10 m**. Z kabiny drzewa przy drodze stoją dalej, więc na jezdni nie ma żadnego cienia drzewa.
   - High: `ls = 0,75` i maska 3, więc cień sięga do 45 m. To tłumaczy, czemu `-tier High` na scenie Low ma cienie.
3. **Odrzucone podejrzenia:**
   - ADR 0240 / `ThinShadowCasterPolicy` jawnie pomija `tree_` (`ThinShadowCasterPolicy.cs:49`, test `ThinShadowCasterTests.cs:90`).
   - Materiały: `simpleFoliage = true` na każdym tierze. Medium i High używają tych samych materiałów liści (`forestFast` tylko na Low, i to tylko dla HLOD w `DrawMesh`). `heroLeafHigh` dotyczy tylko `M_fire_station_thuja_shell`.
   - Ustawienia URP_PC_Low/Medium: cienie działają, bo z `-rq_treeshadow 3` na tych samych assetach URP cienie są.
   - Importer: drzewa (prototypy instancji, shader Kamion/Vegetation) nie mają przełącznika per tier w imporcie; maska siedzi w `WorldInstanceSet.Prototype.shadowLodMask`. `_LowNoShadow` z `RegionImporter.cs:305-310` (ADR 0123/0240) dotyczy materiałów Kamion/World PBR kafli, nie drzew. Rozstrzygające: z `-rq_treeshadow 3` ta sama scena Low z tymi samymi materiałami rzuca cień drzew.
4. **Poprawka:** `treeShadowLodMask = 3` na PC Low i Medium (`PcTierTable.cs`). Mobilny `QualityProfile` bez zmian (A16). Zasięg cieni drzew wynosi teraz:

   | Tier | Zasięg cieni drzew | Deklarowany dystans cieni |
   |---|---|---|
   | Low | 30 m | 60 m |
   | Medium | 30 m | 100 m |
   | High | 45 m | 150 m |
   | Ultra | 60 m | 250 m |

5. **Nadal brak (nie naprawione, wymaga decyzji i pomiaru):**
   - Drzewa dalej niż koniec LOD1 nie rzucają cienia na żadnym tierze, bo impostory (LOD2) i HLOD lasu mają `ShadowCastingMode.Off` (`WorldInstances.cs:603`).
   - Na Medium pas 30–100 m jezdni zostaje bez cieni drzew, choć `[PC_TIER]` deklaruje 100 m.
   - Opcje dla lidera (obie wymagają pomiaru na klasie GTX 660): wyższy `treeCardLodScale` na PC (koszt także w widoku głównym: overdraw kart) albo osobny caster LOD1 tylko dla passu cieni. Dopisane do „Otwarte” w ADR 0269.

## 3. Zmienione pliki
- `game/Assets/_Project/Rendering/Runtime/PcTierTable.cs`: maska Low/Medium 1 → 3 oraz komentarz pola.
- `game/Assets/_Project/Tests/EditMode/PcTreeShadowReachTests.cs` (+ `.meta`): nowy test regresji z 3 przypadkami:
  - zasięg cieni drzew ≥ 25 m (WORKING_VALUE) na każdym tierze PC;
  - zasięg monotoniczny Low ≤ Medium ≤ High ≤ Ultra;
  - bit LOD1 w masce.

  Test liczy zasięg tym samym `WorldInstances.LodAt` i `InstanceImporter.Policy` (przez refleksję, jak w `InstancePolicyShelterTests`). Jest w osobnym pliku, bo `PcGraphicsTierTableTests` chodzi też w harnessie .NET.
- `docs/adr/0269-tiery-grafiki-pc.md`: wiersz „Cienie drzew” (LOD0+1 na wszystkich tierach PC, z uzasadnieniem) i punkt „Otwarte”.

## 4. Dowody
- **Player A/B** na exe `artifacts/win/kamion-0.1.0-8701306fd1-regions/Kamion.exe` (build integracji int-pc-s23, `8701306fd1-dirty`, bez poprawki), `-scene World_knyszyn-s`, 1920×1080, zrzut po 15 s:
  - przed: `artifacts/pc-shadows-s23/before-Low-mask1.jpg`, `before-Medium-mask1.jpg` (kopie z `int-pc-s23/tiers-shadow`) oraz `Low-base-r3.jpg` z tej sesji: brak cieni drzew;
  - po (`-rq_treeshadow 3`, czyli to samo co nowa wartość tabeli przez `RenderOverrides.ApplyTo`): `Low-rq3.jpg`, `Low-rq3-r3.jpg`, `Medium-rq3.jpg`. Cienie koron na jezdni i poboczu do ok. 30 m przed kabiną, dalej jezdnia bez cieni (zgodnie z pkt 5). Uwaga: w kadrze Medium ciężarówka jedzie 27 km/h mimo `autopilot=off` (do okna trafiało obce wejście, w `Low-rq3.log` `[CONTROLS] in ... thr=0.08`), więc `Medium-rq3.jpg` nie jest z tej samej pozycji co `before-Medium-mask1.jpg`; para Low (`Low-base-r3.jpg` / `Low-rq3-r3.jpg`) jest z tej samej pozycji;
  - logi: `artifacts/pc-shadows-s23/*.log` (`[PC_TIER]` oraz `[BOOT] render overrides ... treeshadow=3`).
- **EditMode, Win64, filtrowany:** `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter "PcTreeShadowReachTests;PcGraphicsTierTableTests;PcGraphicsTierAssetTests;ThinShadowCasterTests;InstancePolicyShelterTests;VehicleLodFloorTests"`.
  - Wynik: **80/80 zaliczonych** (`artifacts/pc-shadows-s23/editmode-green-20261116-082722.xml`).
  - Czerwony przebieg kontrolny z przywróconą maską 1 (cofniętą przed commitem): `PcTreeShadowReachTests` 1/3, komunikat „Low: trees cast only up to 9,8 m from the camera” (`editmode-red-mask1-20261116-082820.xml`).

Wszystkie ścieżki są w main: `C:\Users\matma\Documents\Claude\kamion\artifacts\pc-shadows-s23\`.

## 5. Napisane / zbudowane / uruchomione / zmierzone
| Status | Co |
|---|---|
| Napisane | poprawka tabeli, test, ADR |
| Uruchomione | testy EditMode (Win64); player z main z override `-rq_treeshadow 3` (równoważny poprawce) |
| Niezbudowane | exe z poprawką. Render playera z samą poprawką (bez override) jest **UNVERIFIED** |
| Niezmierzone | koszt passu cieni z kartami LOD1 na PC Low/Medium. **ESTIMATED**: na A16 karty LOD1 w passie cieni podwajały koszt lasu (`WorldInstances.cs:639`); na klasie GTX 660 (D74 Low, 30 fps) nie ma liczby. Na RTX 5070 obie wersje stoją na limicie vsync 60 fps (`[DIAG]` p50 16,67 ms), więc pomiar stąd nic nie mówi |

## 6. Ryzyka i znane braki
- **Stabilność, UNVERIFIED i nieprzypisane:** w 5 uruchomieniach z `-rq_treeshadow 3` dwa były nieczyste:
  - `Low-rq3`: crash przy zamykaniu, już po zrzucie i `[AUTOSHOT] quit`. Dump: `artifacts/pc-shadows-s23/crash-Low-rq3-run1.dmp`;
  - `Low-rq3-r2`: log urywa się na t = 9 s, proces zabity po 90 s.

  Pozostałe trzy (Low r3, Low r4, Medium) były czyste, podobnie dwa uruchomienia bazowe Low. `runInBackground: 0` (`game/ProjectSettings/ProjectSettings.asset:89`), więc urwany log r2 to najpewniej pauza po utracie fokusu okna, nie freeze (UNVERIFIED). Na maszynie działały też procesy Unity innych agentów. Przebiegi bazowe nie miały żadnego `rq_`, więc anomalii nie da się rozdzielić między maskę 3 a samą ścieżkę override; potrzebna kontrola `-rq_treeshadow 1` (pkt 7). Próba za mała, żeby wiązać to z poprawką.
- ADR 0222 (szpalery DK65) zapisuje „Cień: tylko LOD0” w kontekście tierów mobilnych. Na PC to już nie obowiązuje, co trzeba dopisać przy najbliższej zmianie tego ADR.
- Zmiany w ProjectSettings, Packages i asmdef nie były potrzebne.

## 7. Proponowany następny krok (lider)
```
git merge --no-ff origin/pc-shadows-s23
pwsh scripts/build-windows.ps1 -Slot -Regions d67-full
pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene World_knyszyn-s -Tier Low -Width 1920 -Height 1080 -RunSeconds 18 -ShotSeconds 15
pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene World_knyszyn-s -Tier Medium -Width 1920 -Height 1080 -RunSeconds 18 -ShotSeconds 15
```
Następnie dwa kroki:
- 5–10 powtórzeń Low z poprawką (okno na pierwszym planie, bez obcego wejścia) plus kontrola z `-ExtraPlayerArgs '-rq_treeshadow','1'`, żeby wykluczyć crash/freeze;
- pomiar kosztu passu cieni (`pc-metrics.ps1`, `-Fps 1000`) A/B z `-rq_treeshadow 1`, a docelowo na klasie GTX 660.
