# ANALIZA 2026-11-16 (s23) — paczki regionów (#112, ADR 0234/0273) po D73: czy na PC, czy sam streaming

Sesja chmurowa P r2, tylko analiza, bez zmian w kodzie i bez Unity. Baza `origin/main` @ `08c2e21f8`.
Gałęzie: [#112](https://github.com/woogitsugames/kamion/pull/112) `regionpacks-0234` @ `ea539a8bc`; zamknięty
[#114](https://github.com/woogitsugames/kamion/pull/114) → gałąź `streaming-0235` @ `36f96f993` (żyje, poprawiona w D12).
Źródła: ADR 0234 i 0273 (na gałęziach), ADR 0235 (gałąź streaming), ADR 0261, 0271, `docs/10` §3/§3a, `docs/12`, D67/D72/D73/D74,
recenzje `REVIEW-2026-11-15-s22-code-112.md` i `-114.md`, `PR-TRIAGE-2026-11-16-s23.md`.

## Werdykt
**PRZEROBIĆ.** Nie scalać #112 osobno ani go nie wyrzucać. Integrować go jako część streamingu: jeden nowy PR z gałęzi
`streaming-0235`, która **już zawiera całe #112** (merge `36f96f993`). Paczki zostają uśpioną ścieżką: kod jest w grze, ale nie jest
tworzony ani używany w grze bazowej. `build-region-packs.ps1` nie wchodzi do procesu wydania PC, dopóki właściciel nie odpowie na `docs/10` §3a
(model DLC i kanał). Po otwarciu nowego PR lider/właściciel zamyka #112 jako wchłonięty. Bez nowego ADR: ADR 0273 już opisuje model C
(„jeden runtime — streaming, dwa źródła treści — build lub paczka”). Trzeba tylko dopisać w nim, że na PC paczki są odroczone (patrz niżej).

## 1. Fakty

| Pozycja | Wartość | Źródło |
|---|---|---|
| Build Windows d67 + 4 regiony (21 regionów) | folder **4 923 MB**, 188 plików; świat przed kompresją 8 372 MB | ADR 0261 (zmierzone) |
| Cel dysku gry bazowej | ≤ 25 GB | D74, `WORKING_VALUE` |
| Szacunek paczek High korytarza D67 (16 regionów bez C) | 2 354–3 425 MB; dodatkowe 4: 468–681 MB; `common` 44–74 MB raz | ADR 0234 §7, `ESTIMATED` |
| Kanał PC | zip + itch.io (butler: łatki delta), Steam po decyzji właściciela; limit pliku na itch `UNVERIFIED` | ADR 0271, `docs/12` |
| Zgodność paczek | **dokładnie ta sama wersja Unity**, ten sam target, `versionCode` w zakresie; jeden zestaw = jeden przebieg budowy (sceny zależą od `common` z tego samego przebiegu) | ADR 0234 §3 |
| #112 w liczbach | 31 plików, +3 016 linii; runtime `Game.World.Packs` niepodpięty do menu/bootstrapu; **nieskompilowany w Unity** (testy pod .NET 8: `RegionPackTests` 50/50) | gałąź, ADR 0273 „Testy” |
| `streaming-0235` vs main | 60 plików w `game/` (+5 984), 317 commitów za main; konflikt tylko `Gameplay/DrivingLabBootstrap.cs` (1 hunk); FIX P1-1 (opt-in `-stream 1`) i P1-2 (przypięty kafel odrodzenia) zrobione | `git merge-tree`, ADR 0273 pkt 7–8 |
| Zależność streamingu od paczek | `Streaming/TileSceneSource.cs` (`BuildOrPackTileSource` przyjmuje `IRegionPackProvider`), `WorldStreamer.cs:146` (`RegionPackService.Existing`) | gałąź `streaming-0235` |

## 2. Czy paczki mają sens na PC teraz? — **nie jako mechanizm dystrybucji; tak jako kontrakt na przyszłe DLC**

Za odłożeniem paczek na PC:
- **Rozmiar nie wymusza paczek.** 4,9 GB folderu (21 regionów) to ok. 20 % limitu 25 GB z D74. Nawet cały korytarz z dodatkami
  w High mieści się w jednym buildzie z zapasem. Ograniczenie, które zrodziło #112 (APK ≤ 2 GB z D67, potem ~4 GB ZIP32 z D72),
  na PC nie istnieje.
- **Łatki robi kanał.** butler (itch.io) i depoty Steam wysyłają różnice plików. Poprawka jednego regionu w buildzie zmienia
  głównie pliki jego sceny (`level*`, `sharedassets*`). Wielkość takiej delty to `UNVERIFIED` — do zmierzenia, ale nie trzeba
  własnego formatu paczek, żeby jej nie wysyłać całej.
- **Paczki nie dają tanich poprawek jednego kafla.** Zestaw paczek jest spójny tylko w obrębie jednego przebiegu budowy, a każda
  zmiana `common` (ciężarówka, PBR, shadery) albo wersji Unity wymusza przebudowę wszystkich paczek (ADR 0234 §3).
- **Koszt utrzymania.** Osobny build treści Win64 (`-packTarget Win64`) i druga ścieżka ładowania. Do tego ryzyko braku wariantów
  shaderów w bundlach: `RegionPackCommands` włącza ten sam `ShaderVariantStripper` co player, a stripping zależy od scen buildu,
  więc grozi różowymi materiałami (`UNVERIFIED`, wymaga testu na buildzie). Dochodzi dublowanie `common` (+44–74 MB) i macierz testów
  z `docs/10` §3a (brak, uszkodzona, niezgodna paczka, przerwane pobieranie…), której nikt dziś nie uruchamia.

Za utrzymaniem kodu paczek (bez wdrażania):
- **DLC krajów i dalsze regiony** (`docs/10` §3, docs/01: Polska, kraje jako DLC) wymagają treści dokładanej po wydaniu. Do
  zbudowanego playera Unity nie da się dodać sceny bez AssetBundle/Addressables. Bez tego każdy region = nowy pełny build.
- **Wersja telefonowa** (Etap 9+, D73) potrzebuje paczek tak czy inaczej (APK z C 224 MB + paczki Low).
- **Streaming jest już spięty z kontraktem paczek** (`IRegionPackProvider`, dzierżawy `Acquire/Release`). Wycięcie paczek
  oznacza przeróbkę `TileSceneSource`/`WorldStreamer` i utratę przetestowanej logiki dzierżaw, bez zysku dla gracza.

## 3. Czy wystarczy sam streaming? — **na PC teraz tak, i to on jest priorytetem**
- D74 (gra „jak ETS2/ATS”): gracz jedzie korytarzem bez ekranów ładowania. Model #112 bez streamingu (wariant A w ADR 0273) dawał
  16 ekranów ładowania na korytarzu D67, co jest sprzeczne z D74. Dziś region wybiera się w menu, a szwy są zamknięte (ADR 0229).
- Streaming bierze sceny kafli z buildu (`-Regions`, `RegionBuildList` dokłada `_Tile`), więc na PC działa bez żadnej paczki.
- Do zrobienia przed włączeniem domyślnym (ADR 0273 pkt 7): przejazd C → Knyszyn 90 km/h w playerze Windows z `-stream 1`:
  0 resetów safety net, 0 kafli „za późno”, ≤ 12 klatek > 33,3 ms. Szczyt working set ≤ 6 GB (High) i ≤ 4 GB (Low); te liczby
  to `WORKING_VALUE`. Na szwie widać dwa kafle naraz: C ma już 1,98–2,02 M tris High, a kadru przy szwie nikt nie mierzył
  (recenzja #114 P1-1).

## 4. Warianty i koszty

| wariant | co | koszt (lider) | ryzyko |
|---|---|---|---|
| **A. scalić #112 teraz, osobno** | kontrakt paczek bez użycia | mały: kompilacja Win64 + EditMode `RegionPackTests` | martwy kod w main bez pomiaru. Nie przybliża ani streamingu, ani DLC. Kolejność 0273 (#112 → #114) ma sens tylko z natychmiastowym #114 |
| **B. PRZEROBIĆ (rekomendowany): nowy PR z `streaming-0235` (zawiera #112)** | streaming opt-in + uśpione paczki w jednym przeglądzie | średni: merge main (1 konflikt), reimport 21 regionów pod sceny `_Tile` (~90 s/region wg s23 ≈ 30–35 min), build Windows d67-full, EditMode (`WorldStreamingPolicyTests`, `RegionPackTests`) + PlayMode `WorldStreamingPlayModeTests`, przejazd `-stream 1` + `stream-report.py --gate`, rozmiar folderu przed/po (sceny `_Tile` — przyrost `UNVERIFIED`) | 72 pliki, w tym wspólne `WorldSafetyNet`, `CameraRig`, `PathFollowerDriverInput`, `WorldSceneBuilder`, `FloatingOrigin`. Są nieskompilowane w Unity, a main poszedł od tego czasu do przodu (spawn-fix 0262, wejście PC 0263–0265, rail). Recenzja kodu po merge'u obowiązkowa |
| **C. zamknąć #112, streaming tylko z buildu** | wyciąć `IRegionPackProvider` z `streaming-0235` | średni: przeróbka `TileSceneSource`/`WorldStreamer` + testów | DLC/telefon = ponowna implementacja (~3 000 linii). Tracimy przetestowane dzierżawy |
| **D. zamknąć oba** | zostaje menu + zamknięte szwy | zero teraz | sprzeczne z D74, blokuje Etap 7 (`docs/03`: przejazd przez granicę paczek, test DLC) |

## 5. Rekomendacja szczegółowa (B)
1. Agent/lider: `streaming-0235` → merge `origin/main` (konflikt `DrivingLabBootstrap.cs`: zachować main z 0262/0265, dołożyć
   opt-in `stream`). Potem nowy PR „streaming kafli + kontrakt paczek (ADR 0235/0234/0273)”, a #112 zamknąć jako wchłonięty.
2. Recenzja kodu (chmura) skupiona na wspólnych plikach i alokacjach w pętli jazdy (zero GC, CLAUDE.md).
3. Weryfikacja lokalna jak w ADR 0273 „Komendy dla lidera” (Windows najpierw, A16 tylko jako drugi pomiar).
4. **Bez** `build-region-packs.ps1` w procesie wydania PC. `package-windows.py` (ADR 0271) pakuje sam build. Paczki Win64 budować
   tylko w teście, który udowadnia, że ścieżka nie zgniła (np. 1 region `-InstallLocal` raz na rundę integracji).
5. Doprecyzowania tekstu bez nowego ADR:
   - ADR 0273 pkt 5: „PC: paczki odroczone do decyzji §3a”.
   - `docs/10` §3 mówi o Addressables, a ADR 0234 wybrał czyste AssetBundles bez nowych pakietów. Ujednolicić tekst `docs/10`.
6. Pytania do właściciela (już w `docs/10` §3a): model DLC na PC (pkt 2), regiony doinstalowywane na żądanie (pkt 3).

## 6. Ryzyka (niezależnie od wariantu)
- Kod #112 i `streaming-0235` **nie był kompilowany w Unity 6000.3**. Wszystkie liczby testów pochodzą z .NET 8 z zaślepką `JsonUtility`.
- Budżety pamięci świata PC (640/800/1450/2000 MB) i progi przejazdu to `WORKING_VALUE`. Bazy procesu bez świata na Windows nikt nie zmierzył.
- Klasa „min” (2 GB VRAM, Intel HD 630) przy dwóch kaflach High na szwie — największe ryzyko D74. Pomiar Low na iGPU przed obietnicą.
- Paczki: zgodność tylko przy identycznej wersji Unity. Każda aktualizacja silnika = przebudowa i ponowne wydanie wszystkich DLC.

## Komendy dla lidera (odtworzenie faktów)
```
git fetch origin main regionpacks-0234 streaming-0235
git merge-tree --write-tree --name-only origin/main origin/streaming-0235     # 1 plik: DrivingLabBootstrap.cs
git diff --stat origin/main...origin/regionpacks-0234 | tail -1                # 31 plików
git grep -n "IRegionPackProvider\|RegionPackService" origin/streaming-0235 -- game/Assets/_Project/World/Runtime/Streaming
```
