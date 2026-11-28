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
