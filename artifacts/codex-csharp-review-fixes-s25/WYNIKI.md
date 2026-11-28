# Wyniki codex-csharp-review-fixes-s25

Gałąź `codex-csharp-review-fixes-s25`. Poprawki day27 w commitach `c3faab177` (shader) i `8fc67526a` (streamer).

| Zmiana i kod | Test | Kompilacja |
| --- | --- | --- |
| Wspólny próg i pokrycie w ForwardLit, VegetationDepth i DepthOnly. Na MSAA sprzęt przelicza alfę A2C na maskę próbek. Na jednopróbkowym DepthOnly piksel zapisuje głębię po przejściu tego samego programowego odcięcia. ShadowCaster używa helpera z dotychczasowym twardym progiem. [Vegetation.shader:249](../../game/Assets/_Project/Rendering/Shaders/Vegetation.shader#L249) | Odtworzone asercje .NET Regex odrzucają bazę i akceptują 4 przebiegi po zmianie. W przykładzie z recenzji (A2C wył., alfa 0,4) próg kolor/głębia zmienia się z 0,2/0,5 na 0,2/0,2. [ShaderAlphaClippingUsesSharedCoverage](../../game/Assets/_Project/Tests/EditMode/VegetationCrownLodTests.cs#L67) | HLSL i EditMode **UNVERIFIED**. |
| Zwalnianie klonów przy wyładowaniu i zniszczeniu streamera, łącznie z kaflem startowym. [WorldStreamer.cs:1037](../../game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs#L1037), [WorldStreamer.cs:1279](../../game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs#L1279) | Test tworzy klony w dwóch syntetycznych kaflach i oczekuje 2 → 0 żywych klonów po zniszczeniu streamera. Pomiar w Unity **UNVERIFIED**. [DestroyStreamer_ReleasesFarRingClonesOfStartAndNeighbour](../../game/Assets/_Project/Tests/EditMode/WorldStreamerHook0273Tests.cs#L83) | Roslyn potwierdził składnię trzech zmienionych plików C#. Kompilacja C# i EditMode **UNVERIFIED**. W `win-build/game` brak wygenerowanych `.csproj`. |

Cztery bramki GIS przeszły **62/62 w 63,15 s** przez `wgpy.cmd`. [Log GIS](gis-tests.txt) · [kontrola statyczna](static-checks.txt).

W tej sesji pominięto Unity, build, EditMode oraz rendery i inspekcję PNG High clear/overcast zgodnie z blokadą fali 14. Pokrycie na GPU, wynik wizualny i zużycie pamięci materiałów pozostają **UNVERIFIED**.

Polecenie dla lidera po fali 14, z katalogu worktree i po sprawdzeniu blokady `PHONE_RUN`.

```powershell
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner codex-csharp-review-fixes-s25
try { pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter 'Game\.Tests\.(Vegetation.*Tests|WorldStreamer.*)' }
finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner codex-csharp-review-fixes-s25 }
```

Po EditMode porównać PNG przed i po dla High clear i overcast oraz maskę koloru i głębi na Low/High z A2C w obu stanach.

## R2 — punkty 4 i 8 recenzji s25

Gałąź `codex-csharp-review-fixes-s25`, kod w commitach `ea3d2a943` (shader) i `2bdb2ef41` (streamer).

| Punkt | Zmiana | Wynik przed → po |
| --- | --- | --- |
| 4 | `DepthOnly` ma twarde odcięcie i wspólny próg kamery z `ForwardLit` oraz `VegetationDepth`. Lokalny URP ustawia `_AlphaToMaskAvailable` z deskryptora kamery podczas rysowania obiektów nieprzezroczystych. Flaga warunkuje A2C w dwóch przebiegach współdzielących ten cel. Osobny prepass może dostać teksturę 1×, więc `DepthOnly` zawsze używa twardego progu. [Shader](../../game/Assets/_Project/Rendering/Shaders/Vegetation.shader) · [Test źródła](../../game/Assets/_Project/Tests/EditMode/VegetationCrownLodTests.cs) | Dla alfy 0,48, progu 0,50 i `fwidth=0,08`, `DepthOnly` przechodził programowe odcięcie z pokryciem 0,25 → odrzuca fragment. Wspólny próg bez A2C pozostaje 0,2/0,2 w przykładzie r1. Asercje NUnit na źródle odrzucają r1 i akceptują r2 dla 4 przebiegów. GPU **UNVERIFIED**. |
| 8 | `OnDestroy` osobno sprząta klony i próbuje zwolnić dzierżawę każdego kafla. Log zawiera nazwę kafla i wyjątek dostawcy. Test obejmuje trzy kafle, `Clear(t0)` i wyjątek w `Release(t1)`. [Streamer](../../game/Assets/_Project/World/Runtime/Streaming/WorldStreamer.cs) · [Test EditMode](../../game/Assets/_Project/Tests/EditMode/WorldStreamerHook0273Tests.cs) | Próba .NET z wydzielonymi metodami produkcyjnymi i atrapami Unity dała 3 → 2 → 1 żywy klon w r1 i 3 → 2 → 0 w r2. Próby zwolnienia objęły t0 i t1 → t0, t1 i t2. Dostawca po sprzątaniu trzymał t1 i t2 → tylko t1, dla którego zgłosił błąd. W r2 wyjątek został zalogowany raz, a pętla dobiegła końca. EditMode **UNVERIFIED**. |

GIS **62/62 w 57,06 s**. Roslyn potwierdził składnię **3/3** zmienionych plików C#. Pełna kompilacja C#, kompilacja HLSL, EditMode oraz rendery i inspekcja PNG przed/po High clear i overcast pozostają **UNVERIFIED** podczas fali 14. [Log GIS](gis-tests-r2.txt) · [Weryfikacja statyczna i próba .NET](static-checks-r2.txt).

Po fali 14 lider może uruchomić z katalogu worktree poniższe polecenia, po sprawdzeniu blokady `PHONE_RUN`. Następnie porównać PNG przed i po w High clear i overcast oraz kolor i głębię z wymuszonym prepasem 1× przy obu stanach A2C, także z kolorem MSAA.

```powershell
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner codex-csharp-review-fixes-s25
if ($LASTEXITCODE -ne 0) { throw 'Nie udało się zająć slotu Unity' }
try {
    pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter 'Game\.Tests\.(Vegetation.*Tests|WorldStreamer.*|TileSceneSourceContractTests)'
    if ($LASTEXITCODE -ne 0) { throw 'EditMode zakończył się błędem' }
}
finally {
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner codex-csharp-review-fixes-s25
}
```

## R3 — regresja EditMode po r2

**EditMode Win64 52/53 → 53/53**, Unity 6000.3.28f1, kod wyjścia 0. Cztery bramki GIS **62/62 w 63,23 s**. Oba przebiegi Unity wykonano z podanym filtrem pod slotem heavy. Slot zwolniono.

- Błąd był w teście `DestroyStreamer_CleansAllTilesAfterClearAndLeaseReleaseFailure`. Liczył on referencje do trzech konkretnych klonów. `Clear(t0)` niszczył pierwszy klon natychmiast. `DestroyImmediate(streamer.gameObject)` w EditMode nie wywołał `OnDestroy` ręcznie zainicjalizowanego komponentu, więc dwa pozostałe klony przeżyły. [XML lidera](editmode-r2-leader.xml) · [Dokumentacja callbacków Unity](https://docs.unity.com/en-us/engine/6000.3/script-reference/unityengine/executealways)
- W `WorldStreamerHook0273Tests.cs` test wywołuje produkcyjne `OnDestroy` jawnie i wskazuje ID kafla przy błędzie asercji. Pierwszy przebieg po tej zmianie ujawnił format logu Unity. `LogAssert` oczekuje teraz dokładnego komunikatu wewnętrznego wyjątku `Release(t1)`. Stos wywołań zawiera też kontekst streamera. [XML przebiegu pośredniego](editmode-r3-first.xml)
- Liczba żywych klonów po utworzeniu, `Clear` i sprzątaniu zmieniła się z **3 → 2 → 2** na **3 → 2 → 0**. Test potwierdził próby zwolnienia `t0`, `t1`, `t2` w tej kolejności, jedną pozostałą dzierżawę `t1` po jego wyjątku oraz zachowanie materiału bazowego. [XML końcowy](editmode-r3.xml) · [Log Unity](unity-editmode-r3.log) · [Log GIS](gis-tests-r3.txt)

W r3 zmieniono test i `STATUS.md` oraz dopisano raport i podsumowania przebiegów. Osiem zmian `.wav.meta` obecnych przed r3 pozostaje poza commitami. Weryfikacja Unity objęła wyłącznie wskazany EditMode. PlayMode, build, regeneracja oraz rendery High przed i po dla clear i overcast wraz z inspekcją PNG pozostały poza tym przebiegiem.

Następny krok lidera to przegląd zmian r3 przed integracją.

```powershell
git diff bdb2b459d..codex-csharp-review-fixes-s25 -- game/Assets/_Project/Tests/EditMode/WorldStreamerHook0273Tests.cs
```
