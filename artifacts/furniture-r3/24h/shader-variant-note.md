# Odczyt reguł usuwania wariantów — nie test APK

Sprawdzono istniejące `game/Assets/_Project/Editor/Build/ShaderVariantStripper.cs` oraz `ShaderVariantCounter.cs`, bez ich edycji. Własny stripper usuwa wskazane shadery deferred/terrain oraz warianty lightmap/shadowmask/debug. Nie ma w jego liście `_FURNITURE_SHELTER_PALETTE` ani reguły odrzucającej nieznane lokalne keywordy. Counter tylko zlicza warianty.

To wąski odczyt konfiguracji projektu. Nie dowodzi obecności wariantu w końcowym APK, decyzji standardowego strippera URP, poprawności na Vulkanie ani kosztu GPU urządzenia. Edytorowe testy 18/18 i końcowe rendery także nie zastępują takiego dowodu. W tej sesji nie uruchamiano telefonu ani adb.
