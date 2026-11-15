# ADR 0234 — osobne paczki regionów (AssetBundles bez nowych pakietów), APK bazowy z regionem C
Status: Proposed (chmura D, zadanie F1, gałąź `regionpacks-0234`), 2026-11-15. Do weryfikacji i scalenia przez lidera.
**Zmieniony przez ADR 0273 (FIX s22, D12):** paczka niesie też scenę kafla `World_<id>[_High]_Tile` (ADR 0235), bundle są
liczone referencjami (wiele regionów naraz — streaming), cel budowy `-Target Android|Win64` (D73). Sekcje niżej poprawione.
Powiązane: D67 (`docs/11` — „docelowo regiony jako osobne paczki do pobrania”, APK ≤ 2 GB, instaluje właściciel),
D24 (świat w APK ≤ 110 MB, bez Play Asset Delivery), ADR 0011 (import, `_Generated` poza gitem), ADR 0012 (tiery treści
Low/High, „Addressables — wrócić przy streamingu”), ADR 0229 / PR #104 (wybór regionu w buildzie i menu, katalog regionów).

## Kontekst
- Dziś region trafia do gry jako scena `Assets/_Generated/World/<id>/World_<id>.unity` (`scripts/import-region.ps1`,
  poza gitem); APK zawiera sceny z `EditorBuildSettings` (Boot, DrivingLab, WorldC), PR #104 dokleja sceny regionów do
  listy buildu (`-Regions`). APK z samym C = **224 MB** (HANDOVER, D67). Korytarz D67 w APK: ADR 0229 szacuje
  **≈ 1,2–1,7 GB** (ESTIMATED) — blisko limitu właściciela 2 GB, każda poprawka kafla = nowy APK całości.
- Każda scena regionu zawiera ciężarówkę + naczepę (prefaby z `WorldSceneBuilder`, `Assets/_Generated/Truck|Trailer`),
  wspólne materiały PBR świata (`Kamion/World Surface`, tekstury ADR 0063), biblioteki rekwizytów/drzew, shadery URP.
- Unity: „Assets and scenes aren't shared between different builds, so the same content might be duplicated both in the
  Player build and a content-only build that you make using AssetBundles” oraz „If that asset isn't explicitly assigned to
  an AssetBundle then Unity copies its content inside each AssetBundle that references it” (Unity 6000.3 Manual,
  *Avoiding asset duplication*, docs.unity.com/en-us/engine/6000.3/manual/assets-and-media/assets-managing-runtime/assets-avoid-duplication).
- Ograniczenia zadania: bez nowych pakietów w `Packages/` (moduły `com.unity.modules.assetbundle` i
  `com.unity.modules.unitywebrequest` już są w `Packages/manifest.json`), bez zmian `ProjectSettings/`, asmdef, wspólnych scen.

## Decyzja

### 1. Podział: baza vs paczki
| w APK (bez zmian) | w paczkach (`artifacts/regionpacks/<ver>/`) |
|---|---|
| Boot, DrivingLab, **WorldC** (+ `WorldC_High` z `-WorldHigh`) | każdy inny zaimportowany region: `<region>.bundle` (Low/Medium), opcjonalnie `<region>-high.bundle` |
| cały kod (skrypty są zawsze w playerze), shadery i materiały użyte przez sceny bazy | `common.bundle` — wspólne zależności scen paczek (ciężarówka, naczepa, PBR świata, biblioteki, shadery) |
| `Resources/` (katalog regionów #104, grafy nawigacji `CabDisplay/Nav/*_route.bytes` — małe) | `<region>-data.bundle` — tylko przy `-Tiers Both`: zasoby regionu używane przez obie sceny tieru (kolizja, instancje) |

Region C zostaje w bazie (start bez pobierania, pomiary gate3 bez zmian). Domyślny APK się nie zmienia (bez `-Regions`
z #104 = 224 MB). Region w APK ma pierwszeństwo przed paczką (`RegionPackState.InBase`) — nigdy dwie sceny o tej samej nazwie.

### 2. Budowa: `Game.Editor.Build.RegionPackCommands.BuildRegionPacks` + `scripts/build-region-packs.ps1`
- Nowa komenda batchmode (osobna od `BuildCommands`, której nie zmieniam). Argumenty: `-regions "all"|"dojlidy,dk65-01,…"`
  (`all` = wszystkie zaimportowane poza C; C tylko gdy wymieniony), `-packTiers Low|High|Both`, `-packOutput`,
  `-packSetVersion`, `-minAppVersionCode`, `-maxAppVersionCode`, `-noShaderStrip`. Wynik w logu:
  `REGIONPACKS_RESULT: Succeeded|Failed …`, exit 0/1/2/4 jak `BuildAndroidApk`.
- Nazwy bundli w pamięci (`AssetBundleBuild[]`), bez `assetBundleName` w `.meta` — import i sceny nietknięte.
- **Bundel sceny = pełna scena + scena kafla** tego samego regionu i tieru, jeśli zaimportowana (ADR 0273); brak kafla =
  ostrzeżenie `[PACKS] … no tile scene` (paczka działa tylko z menu, szwy zamknięte). Manifest `scenes[]` wymienia obie.
- Cel: `-packTarget Android|Win64` (skrypt `-Target`); manifest `buildTarget` = `Android`/`Win64`, player porównuje z
  `RegionPackManifest.TargetFor(Application.platform)` (Windows player i edytor = `Win64`).
- Plan zależności (`RegionPackPlanner`, czysta logika, testy): zasób idzie do `common`, gdy (a) używają go sceny ≥ 2
  regionów albo (b) leży poza `Assets/_Generated/World/<region>/` (ciężarówka, PBR, shadery, URP). Zasób folderu regionu
  używany przez obie sceny tego regionu (Low+High) → `<region>-data`; reszta zostaje niejawnie w bundlu sceny.
  Reguła (b) czyni `common` niezależnym od wybranego podzbioru regionów. Pomijane: `.cs`, `.dll`, `.asmdef`, `.unity`,
  foldery `Editor/`. Plan zapisywany do `regionpacks.plan.txt` (do przeglądu duplikatów).
- Kompresja **LZ4** (`ChunkBasedCompression`): „In case of LZMA compression, the file content will be fully decompressed
  into memory” (ScriptReference `AssetBundle.LoadFromFile`, 6000.3) — na 4 GB A16 niedopuszczalne. LZMA byłoby mniejsze do
  pobrania (Manual *AssetBundle compression formats*: „LZMA is the preferred format for … CDN”) i wymagałoby
  `RecompressAssetBundleAsync` po pobraniu — odłożone do pomiaru. `StrictMode` = każdy błąd przerywa build.
- `ShaderVariantStripper` działa też dla bundli (ten sam `IPreprocessShaders`).
- Skrypt: dot-source `env.ps1`, log `artifacts/logs/regionpacks-<ts>.log`, niezależna weryfikacja (rozmiar + SHA-256
  każdego pliku względem manifestu, `SHA256SUMS`), `-Push -Serial <s> [-Only <id>…]` = `adb push` do `incoming/`
  (bundle najpierw, manifest na końcu), `-SkipBuild -SetDir` = tylko weryfikacja/push.

### 3. Manifest `regionpacks.json` (schema `truck-sim-pl/region-packs/1`) i zgodność
Pola: `packSetVersion` (`<bundleVersion>-<sha>[-dirty]`, jak nazwa APK), `unityVersion`, `buildTarget`,
`minAppVersionCode` (domyślnie liczba commitów HEAD = `versionCode` APK z tego commita, `BuildInfoWriter`),
`maxAppVersionCode` (0 = brak), `gitSha`, `createdUtc`, `packs[]`: `id`, `region`, `tier`, `file`, `sizeBytes`, `sha256`,
`crc` (informacyjnie), `scenes[]`, `dependencies[]`. Walidacja (`RegionPackManifest.Validate`): schema, bezpieczne nazwy
plików (`[a-z0-9][a-z0-9._-]*.bundle`, bez `..` i separatorów — manifest może przyjść z sieci), sha256 64 hex, rozmiar > 0,
unikalne id/pliki, zależności istnieją, nie są scenami, lista jest domknięta przechodnio (jak
`AssetBundleManifest.GetAllDependencies`; `<region>-data` → `common` musi być też na liście sceny) — razem z zakazem
zależności od siebie wyklucza to cykle. Kolejność ładowania: `RegionPackManifest.LoadOrder` (najpierw pakiety z najmniejszą
liczbą własnych zależności: `common`, potem `-data`).
Zgodność (`RegionPackResolver.CompatibilityProblem`): **dokładnie ta sama wersja Unity**, ten sam target, `versionCode` w
zakresie. TypeTree zostają włączone (domyślnie), więc dodane/usunięte pola skryptów nie psują odczytu, ale zmiana
semantyki danych już tak — stąd `minAppVersionCode`. **Jeden zestaw = jeden przebieg budowy**; bundle różnych zestawów się
nie mieszają (sceny odwołują się do `common` z tego samego przebiegu).

### 4. Stany i weryfikacja (runtime `Game.World.Packs`, asmdef `Game.World` — bez zmian referencji)
`InBase` (scena w APK) · `NotInstalled` · `Installed` · `Incompatible` · `Corrupt` · `MissingDependency` · `Downloading` ·
`Loaded`. Kolejność: brak zestawu → NotInstalled; niezgodny → Incompatible; brak wpisu/pliku → NotInstalled (+ bajty do
pobrania); zły rozmiar → Corrupt; (głęboko) zły SHA-256 → Corrupt; zależność nie OK → MissingDependency; inaczej Installed.
Menu używa sprawdzenia płytkiego (rozmiary, bez hashowania); przed wczytaniem `Prepare` liczy SHA-256 paczki i zależności
na wątku roboczym (`Task.Run`), potem `AssetBundle.LoadFromFileAsync` (`LoadOrder`: common → data → scena) i zwraca nazwę sceny.
`Application.CanStreamedLevelBeLoaded`: „Verify if the named scene exists in either the Player build or currently loaded
AssetBundles” (ScriptReference 6000.3) — więc po `Prepare` działa istniejąca ścieżka `SceneManager.LoadScene` z #104.
**Liczenie referencji (ADR 0273, recenzja P1-2):** `Acquire(region, tier)` / `Release(region, tier)` na
`RegionPackLeases` — bundel ładowany przy 0 → 1 dzierżaw, zwalniany (`Unload(true)`) przy 1 → 0; `common` znika dopiero,
gdy nie jest trzymany żaden region. `Prepare` (menu) = `Acquire` pod dzierżawą menu, oddawaną, gdy aktywna scena opuści
region; streamer trzyma po jednej dzierżawie na kafel i oddaje ją po `UnloadSceneAsync`. Globalne `UnloadAll` zostało tylko
jako jawne „zwolnij wszystko” (testy/wyjście), nie w ścieżce ładowania. Brak `Update()` — pętla jazdy nie dotyka paczek;
streamer woła `Acquire/Release` tylko przy zdarzeniu kafla.

### 5. Instalacja i pobieranie
- Układ: `persistentDataPath/regionpacks/{regionpacks.json, *.bundle, incoming/}`. Na Androidzie
  `/sdcard/Android/data/com.woogitsugames.kamion/files/regionpacks/incoming/` (adb push przez skrypt; dostęp powłoki adb do
  `Android/data` na Androidzie 14 / A16 — **UNVERIFIED**, lider sprawdza pierwszym `-Push`).
- `RegionPackInstaller.InstallIncoming` (przy starcie serwisu i po pobraniu): manifest niepoprawny/niezgodny →
  `regionpacks.json.rejected`, zainstalowany zestaw bez zmian; każdy bundle z `incoming/` sprawdzony (rozmiar + SHA-256)
  zanim zastąpi plik; zły = usunięty; zainstalowane bundle nieobecne w nowym zestawie lub o innych bajtach = usunięte;
  identyczne zostają (bez ponownego hashowania, gdy sha w starym i nowym manifeście jest ta sama); manifest na końcu przez
  plik tymczasowy.
- Pobieranie opcjonalne: `RegionPackService.BaseUrl` (PlayerPrefs `regionpacks.url`) — **domyślnie puste = brak
  pobierania**, żadnego serwera w repo. `UnityWebRequest` + `DownloadHandlerFile` do `incoming/<file>.part`, SHA-256 przed
  przeniesieniem, potem ten sam instalator. Integralność, nie autentyczność: sha256 pochodzi z tego samego serwera — przed
  publicznym hostingiem podpis manifestu (otwarte). HTTPS wymagany przez Androida domyślnie (cleartext off).

### 6. Styk z menu wyboru regionu (PR #104, ADR 0229) — bez zmiany plików #104 w tej gałęzi
Interfejs `IRegionPackProvider` (`GetInfo`, `DownloadEnabled`, `Prepare`, `Download`, `InstallIncoming`, `Changed`),
implementacja `RegionPackService.Instance`, teksty `RegionPackLabels` (`Detail` do linii szczegółów, `Action` na
przycisk, `ActionDownloads`). Po scaleniu #104 lider (albo F-zadanie) nakłada diff z załącznika A (GameBootstrap +
BootMenu, ~35 linii). `RegionPackPlanner.SceneName/ScenePath/TileSceneName` delegują do `Game.World.RegionScenes`
(jest na main od scalenia #104; `TileSceneNameFor` dodany identycznie jak w #114).

### 7. Rozmiary paczek (ESTIMATED, `python scripts/estimate-region-packs.py`)
Metoda: paczka ≈ k × `WORLD_MEMORY` z importu (wartości cytowane w ADR regionów, różne daty), k = 0,81–1,18 (ADR 0229:
udział świata C w APK / pamięć świata). `common` ≈ 44–74 MB raz (PBR 21,1 + mesh ciężarówki/naczepy ≈ 22,6 + inne
tekstury ≈ 30 MB surowo, `PERFORMANCE_BUDGETS.md` audyt 2026-11-10, × 0,6–1,0). LZ4 bundli kompresuje gorzej niż LZ4HC
APK — górna granica bardziej prawdopodobna.

| region | WORLD_MEMORY Low / High MB (źródło) | paczka Low MB | paczka High MB |
|---|---|---|---|
| bialystok-industrial-c (baza) | 124,2 / 267,0 (0188) | w APK | w APK z `-WorldHigh` |
| bialystok-maczka | 153,2 / 420,4 (0208) | 124–181 | 341–496 |
| bialystok-kleeberga | 156,7 / 356,8 (0206) | 127–185 | 289–421 |
| bialystok-knyszynska | 116,0 / 260,2 (0208) | 94–137 | 211–307 |
| dk65-01 | 68,2 / 165,9 (0205) | 55–80 | 134–196 |
| dk65-02 | 60,2 / 139,3 (0210) | 49–71 | 113–164 |
| dk65-03 | 50,5 / 131,7 (0207) | 41–60 | 107–155 |
| dk65-04 | 76,1 / 181,5 (0207) | 62–90 | 147–214 |
| dk65-05 | 75,5 / 176,5 (0207) | 61–89 | 143–208 |
| dk65-06 … dk65-11 | 48,2–59,1 / 113,0–136,5 (0214) | 39–70 każdy | 92–161 każdy |
| knyszyn-s | 40,8 / 106,8 (0212/0204) | 33–48 | 87–126 |
| knyszyn | 95,5 / 216,7 (0204) | 77–113 | 176–256 |
| bialystok-dojlidy | 99,6 / 214,9 (0188) | 81–118 | 174–254 |
| knyszyn-w | 54,0 / 129,2 (0212/0209) | 44–64 | 105–152 |
| dk65-monki-01 | 46,6 / 113,6 (0212) | 38–55 | 92–134 |
| dw671-tykocin-01 | 45,7 / 119,4 (0212) | 37–54 | 97–141 |
| **suma D67 (16 bez C)** | | **985–1435** | **2354–3425** |
| **suma opcjonalnych (4)** | | **200–291** | **468–681** |

Wniosek: APK zostaje 224 MB (C), pojedynczy kafel DK65 to ~40–70 MB (+ `common` raz), cały korytarz Low ≈ 1,0–1,5 GB
na urządzeniu — tyle co wariant „wszystko w APK”, ale doinstalowywany i wymieniany kaflami. Miejsce na urządzeniu:
`common` dubluje kopie z APK (+44–74 MB). Tier High paczkami tylko dla flagowca (nie A16). Scena kafla w bundlu dodaje
niewiele (te same zasoby regionu; własne obiekty tylko root + trasa) — rozmiar do odczytu z `REGIONPACK:` w logu.

**Pamięć (recenzja P2-5):** przy przejściu C (z APK) → region z paczki materiały/tekstury PBR i ciężarówka są w pamięci
**drugi raz** (kopie z `common`, inne instancje niż w buildzie): +44–74 MB PSS ESTIMATED przy budżecie A16 Low ~1000 MB.
Zmierzyć pierwszym przebiegiem `-Push` (`device-metrics.ps1`: PSS sceny z paczki vs ta sama scena w APK). Na PC gra bazowa
jest w buildzie, a paczki są dodatkami (ADR 0273 §5) — dubel dotyczy tylko pierwszego regionu dodatku.
Zasoby spod `Resources/` użyte przez sceny regionów nie są wykluczane (niejawna kopia trafiłaby do każdego bundla sceny),
tylko wypisywane w `regionpacks.plan.txt [resources-copies]` i ostrzeżeniem — naprawa po stronie importera.

### 8. Propozycja dla lidera (NIE wdrażane): Addressables + Play Asset Delivery
Kiedy: dopiero przy publikacji w Google Play (zgoda właściciela, konto). Limity Play (support.google.com/googleplay/
android-developer/answer/9859372, odczyt 2026-11-15, „compressed download size”): base module **500 MB**, pojedynczy asset
pack **1,5 GB**, moduły + install-time łącznie **4 GB**, on-demand + fast-follow łącznie **30 GB**, całość **34 GB**.
developer.android.com/guide/playcore/asset-delivery: install-time „require at least two times the size of all the asset
packs” wolnego miejsca, fast-follow/on-demand „only a few hundred extra MBs” i nie wliczają się do rozmiaru w sklepie.
Koszt: dwa pakiety (`com.unity.addressables`, `com.unity.addressables.android` — „works in conjunction with the
Addressables package to support Play Asset Delivery”, docs.unity3d.com/Packages/com.unity.addressables.android@1.0),
pipeline AAB (`buildAppBundle`) zamiast APK — instalacja przez `adb install` przestaje działać wprost (bundletool
`build-apks --local-testing`), migracja scen regionów do grup, zmiana `build-android.ps1`/`device-metrics.ps1`.
Ryzyko: nowe zależności w lock-file, inny format testów na A16, więcej ruchomych części przy sideloadzie (dziś jedyny kanał).
Rekomendacja: zostać przy AssetBundles (ten ADR) w fazie sideload; jednostki (`common`, `<region>`, `<region>-high`)
mapują się 1:1 na grupy Addressables / asset packi on-demand, więc przejście nie zmienia podziału treści.

## Weryfikacja w chmurze (bez Unity)
- FIX s22 (ADR 0273): +7 testów (dzierżawy, kafel w bundlu, kopie z Resources, nazwy przez RegionScenes, cel Win64) —
  **50/50** pod .NET 8 + NUnit 3.14 (ten sam harness); `RegionPackService`/`RegionPackCommands` po zmianach kompilują się
  na zaślepkach API (Build succeeded) — nadal **nieskompilowane w Unity**.
- `RegionPackTests` (EditMode, 43 przypadki z TestCase): skompilowane i uruchomione pod .NET 8 + NUnit 3.14 z prawdziwymi
  plikami `Packs/*.cs` (bez `RegionPackService`) i `RegionPackPlanner.cs`, `JsonUtility` zastąpione System.Text.Json:
  **43/43 zielone**. `RegionPackService.cs` i `RegionPackCommands.cs` skompilowane na zaślepkach API Unity (sygnatury
  przepisane z dokumentacji) — **nieskompilowane w Unity**, nieuruchomione: build bundli, ładowanie sceny z bundla, adb push,
  pobieranie, telefon.

## Ryzyka / otwarte (UNVERIFIED do pomiaru lidera)
1. Warianty shaderów w bundlach: stripper i słowa kluczowe ustawiane w runtime (tiery) — bundle kompiluje warianty z
   materiałów; brakujący wariant = różowy/zastępczy materiał. Sprawdzić visual-qa / zrzut z A16 sceny z paczki.
2. Cache PSO/rozgrzewka shaderów bazy nie obejmuje kopii shaderów z `common` → możliwe przycięcia pierwszych klatek.
3. PSS sceny z bundla vs ta sama scena w APK (nagłówki LZ4, `common` w pamięci) — zmierzyć `device-metrics.ps1`.
4. Zasoby z `Resources/` użyte w scenach trafiają też do `common` (kopia, lista w planie); `unity_builtin_extra` dublowane w bundlach (małe).
6. Windows: instalator zastępuje pliki bundli w `incoming/` → zainstalowane; plik trzymany przez załadowany bundel jest na
   Windows zablokowany — instalacja tylko przy starcie (przed jakimkolwiek `Acquire`), pobieranie w trakcie jazdy nieobsługiwane.
5. Czas weryfikacji SHA-256 na A16 (~1 s / 100 MB — ESTIMATED) przy starcie regionu.

## Załącznik A — diff dla plików PR #104 (do nałożenia po scaleniu #104; nie w tej gałęzi)
```diff
--- a/game/Assets/_Project/Gameplay/GameBootstrap.cs   (stan region-select-0229)
+++ b/game/Assets/_Project/Gameplay/GameBootstrap.cs
@@ using
+using Game.World.Packs;
@@ BuildRegionChoices(RegionCatalog catalog, StartMenuOptions options)
+            var packs = RegionPackService.Instance;          // Awake instaluje incoming/ (adb push)
             foreach (var r in catalog.regions)
             {
                 string id = r.id, label = r.label;
                 bool inBuild = Application.CanStreamedLevelBeLoaded(RegionScenes.SceneNameFor(id));
+                string tier = RegionPackResolver.PreferredTier(QualityTiers.Current, packs.GetInfo(id, "High", inBuild).CanStart);
+                var info = packs.GetInfo(id, tier, inBuild);
                 float s = RegionStart.ClampStartS(r.startS, r.routeLengthM);
                 string km = (r.routeLengthM / 1000f).ToString("0.0", ci).Replace('.', ',');
-                string detail = inBuild ? $"{r.group} · trasa {km} km · start na początku trasy" : $"{r.group} · brak w tym APK";
-                list.Add(new BootRegionChoice(id, label, detail, inBuild, () =>
+                string detail = inBuild ? $"{r.group} · trasa {km} km · start na początku trasy"
+                                        : $"{r.group} · trasa {km} km · " + RegionPackLabels.Detail(info, packs.DownloadEnabled);
+                Action download = RegionPackLabels.ActionDownloads(info, packs.DownloadEnabled)
+                    ? () => packs.StartCoroutine(packs.Download(id, tier, err => { if (err != null) Debug.LogWarning("[PACKS] " + err); }))
+                    : (Action)null;
+                list.Add(new BootRegionChoice(id, label, detail, info.CanStart, () =>
                 {
                     StartRequest.SetRegion("region " + id, id, s, options.LightingId);
-                    SceneManager.LoadScene(RegionSceneForTier(id));
-                }));
+                    if (inBuild) { SceneManager.LoadScene(RegionSceneForTier(id)); return; }
+                    packs.StartCoroutine(packs.Prepare(id, tier, res =>
+                    {
+                        if (res.Ok) SceneManager.LoadScene(res.SceneName);
+                        else Debug.LogWarning("[START] region pack " + id + ": " + res.Error);
+                    }));
+                }, download, inBuild ? null : RegionPackLabels.Action(info, packs.DownloadEnabled)));
             }
@@ po BootMenu.Create(...)
+            RegionPackService.Instance.Changed += () => { if (m_Menu != null) m_Menu.SetRegions(BuildRegionChoices(m_Catalog, options)); };
+            // (odpiąć w OnDestroy GameBootstrap; menu żyje do LoadScene)
--- a/game/Assets/_Project/UI/BootMenu.cs   (stan region-select-0229)
+++ b/game/Assets/_Project/UI/BootMenu.cs
@@ void StartRegion()
-            if (!r.Available || r.Start == null) return;
+            if (!r.Available) { r.Download?.Invoke(); return; }   // ADR 0234: przycisk pobiera paczkę
+            if (r.Start == null) return;
@@ void RefreshRegion()
-            m_RegionStart.interactable = r.Available;
-            m_RegionStartText.text = r.Available ? RegionStartLabel : RegionMissingLabel;
+            m_RegionStart.interactable = r.Available || r.Download != null;
+            m_RegionStartText.text = r.ActionLabel ?? (r.Available ? RegionStartLabel : RegionMissingLabel);
@@ public int RegionIndex => m_RegionIndex;
+        /// <summary>Replaces the choices (same catalog order) after a pack download / install; keeps the shown index.</summary>
+        public void SetRegions(IReadOnlyList<BootRegionChoice> regions)
+        {
+            if (regions == null || m_Regions == null || regions.Count != m_Regions.Count) return;
+            m_Regions = regions;
+            RefreshRegion();
+        }
@@ public readonly struct BootRegionChoice
-        public readonly string Id, Label, Detail;
+        public readonly string Id, Label, Detail, ActionLabel;   // ActionLabel null = default texts
         public readonly bool Available;
-        public readonly Action Start;
+        public readonly Action Start, Download;                   // Download != null: the button fetches the pack
-        public BootRegionChoice(string id, string label, string detail, bool available, Action start)
+        public BootRegionChoice(string id, string label, string detail, bool available, Action start,
+                                Action download = null, string actionLabel = null)
         {
             Id = id ?? ""; Label = label ?? Id; Detail = detail ?? ""; Available = available; Start = start;
+            Download = download; ActionLabel = actionLabel;
         }
```
`m_Menu` / `m_Catalog` / `options` istnieją w #104 (`options` trzeba podnieść do pola). Testy PlayMode #104
(`StartMenuFlowTests`, `HudLayoutTests`) bez zmian semantyki: bez paczek `info.CanStart == inBuild`, napisy jak dotąd poza
linią szczegółów regionu spoza APK („brak paczki (wgraj przez adb)” zamiast „brak w tym APK”).

## Komendy dla lidera
```
pwsh scripts/import-region.ps1 -Region dk65-06                      # scena regionu (jeśli nie ma)
pwsh scripts/test.ps1 -Platform EditMode                             # RegionPackTests
pwsh scripts/build-region-packs.ps1 -Regions dk65-06,knyszyn         # → artifacts/regionpacks/<ver>/ + SHA256SUMS
pwsh scripts/build-android.ps1 -Install -Serial RFGL34SJYDZ          # APK z TEGO commita (minAppVersionCode)
pwsh scripts/build-region-packs.ps1 -SkipBuild -Push -Serial RFGL34SJYDZ   # adb push do incoming/, restart aplikacji
# logcat: "[PACKS] install set …: installed [common,dk65-06,…]"; start regionu wymaga diffu z załącznika A (po #104)
pwsh scripts/device-metrics.ps1 -Serial RFGL34SJYDZ -Launch -DurationSeconds 90   # PSS/FPS sceny z paczki vs w APK
```
