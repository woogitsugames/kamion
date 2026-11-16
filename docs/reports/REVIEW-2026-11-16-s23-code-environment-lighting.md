# REVIEW s23 code — `EnvironmentLighting.OnDisable` oddaje kolor LED regionu (D18, temat 3)

- Merge: `dbfe8c60e` „Merge lamp-test-s23” (pierwszy rodzic `55265b430`). 2 pliki, +42/−1:
  `game/Assets/_Project/Rendering/Runtime/Sky/EnvironmentLighting.cs:86-93`,
  `game/Assets/_Project/Tests/EditMode/RegionLightingProfileTests.cs:109-141` (nowy test).
- Kontekst: ADR 0216/0216b (kolor LED per region, statyczny stan `StreetLamps.k_Led`), błąd zależny od kolejności
  `StreetLampOpticsTests.SodiumTint_HasTheLedLuminance` (0,94206 zamiast 0,93694) po scenie Dojlid.

## Werdykt: OK (z dwiema uwagami P2 na później)

## Poprawność
- `Apply()` (`:136`) zapisuje `StreetLamps.SetLedColour(ledColour)` w stanie statycznym, ale wcześniej nic go nie
  przywracało. Teraz `OnDisable` przy `Instance == this` woła `SetLedColour(alpha 0)`, a `StreetLamps.cs:46-49`
  zamienia `alpha 0` na `k_LedDefault`. Mechanizm jest poprawny i zgodny z konwencją ADR 0216 („alpha 0 = default”).
- `OnDisable` zamiast `OnDestroy` jest właściwym wyborem: przy rozładowaniu sceny, `SetActive(false)` i przeładowaniu
  domeny w edytorze (`[ExecuteAlways]`) `OnDisable` wywołuje się zawsze. Następne `OnEnable` i tak zawoła `Apply()`
  i ustawi kolor z powrotem, więc w edytorze nie ma migotania.
- Warunek `Instance == this` chroni przypadek ze starszym środowiskiem wyłączonym po włączeniu nowszego: kolor
  nowszego regionu zostaje. Test sprawdza to w tej kolejności (A → B → zniszcz A → kolor B → zniszcz B → domyślny).
- `SetLedColour` przy zmianie koloru iteruje `s_Glass` i woła `LampGlare.Invalidate()`. To zdarzenie jednorazowe
  przy rozładowaniu regionu, nie należy do pętli jazdy. Zero GC: `new Color` to struktura.

## Test
`RegionLedColour_IsGivenBack_WhenTheEnvironmentGoesAway`: warunek wstępny „default LED” ma czytelny komunikat.
`try/finally` niszczy oba GO i preset oraz przywraca kolor domyślny, więc test sam niczego nie zostawia.
`NewEnv` tworzy GO nieaktywny z `HideAndDontSave`, a `SetActive(true)` wywołuje `OnEnable` → `Apply`. Jest poprawny.
Nieuruchomiony w chmurze (brak Unity), nieskompilowany w chmurze. Według HANDOVER lider uruchomił EditMode po scaleniu.

## Uwagi (P2, nie blokują)
1. **`EnvironmentLighting.cs:86-93`: wyłączenie nowszego środowiska przy żywym starszym.** Jeśli B (Instance)
   zniknie, a A nadal jest aktywne (dwie sceny addytywnie, np. przyszły streaming regionów ADR 0235), kolor wraca
   do domyślnego zamiast do koloru A, a `Instance` staje się `null`, choć A żyje. To było już wcześniej
   (`Instance = null`), a teraz obejmuje też kolor. **Poprawka (przy streamingu):** statyczna lista aktywnych
   środowisk. W `OnDisable` należy ją zdjąć i, jeśli coś zostało, ustawić `Instance = ostatnie` oraz `Instance.Apply()`
   (albo samo `SetLedColour(Instance.ledColour)`).
2. **Inne stany statyczne z `Apply()` nadal przeciekają.** Chodzi o `StreetLamps.SetSunElevation` (`:134`)
   i `NightWindows.Apply(...)` (`:135`) z zegarem regionu (ADR 0216). Po scenie z zmierzchem i innym `duskClockHour`
   kolejne testy dziedziczą te wartości. Może się to objawić tak samo jak ten błąd w innym teście optyki.
   **Poprawka:** w tym samym bloku `if (Instance == this)` przywrócić wartości domyślne albo dodać `[TearDown]`
   w testach optyki latarni, które ustawiają stan jawnie. Do decyzji lidera, gdy pojawi się następny fail kolejnościowy.
3. Drobne: `OnBeginRendering` każdego aktywnego środowiska woła `Apply()` po zmianie override'ów A/B, więc przy
   dwóch środowiskach wygrywa ostatni subskrybent, a nie `Instance`. Ten problem istniał wcześniej, odnotowuję go
   tylko razem z punktem 1.

## Zgodność z CLAUDE.md
Bez zmian w `ProjectSettings/`, `Packages/` i asmdef. Kod renderingu, nie fizyki. Brak alokacji w pętli. Test EditMode
dodany w istniejącym katalogu.
