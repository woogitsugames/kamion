# Pauzy na DK65-10 — analiza 2026-11-19

Gałąź `stream-hitch-cli`. Bez uruchamiania Unity, playera ani buildów. Odczytano
`C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/win-build/artifacts/win/runs/20261119-140004/`.
Zmiany i artefakty wyłącznie we własnym worktree.

## Dowody

- `player.log:831–837`: dk65-10 High załadowany w 267 ms, aktywowany w 183 ms
  (64 chunki, 154 kolidery), 388 m przed pojazdem; suma trzech kafli 362 MB
  (ESTIMATED). `:838` umieszcza gotowość około t=1883 s.
- `:851–855`: przejście na dk65-10 i rebase 0,60 ms około t=1918 s.
- `:867–873`: unload dk65-08 i UnloadUnusedAssets **7,3043 ms**;
  `:879–885`: unload dk65-09 i UnloadUnusedAssets **4,6201 ms**.
- `:894–934`: pauzy bez nowych zdarzeń streamingu. DIAG zgłasza 21106,15 ms
  (`:902`), 2134,71 ms (`:907`) i 165917 ms (`:933`). Następny load to
  dopiero dk65-11 (`:938–940`), 250 ms + 129 ms.
- `frametimes.csv:120282`, `:120708`, `:122715`: klatki 120281, 120707,
  122714, odpowiednio t_s=2031,9634 / 2041,9558 / 2241,3096 i
  frame_ms=21106,152 / 2134,708 / 165917. CPU main z FrameTimingManager:
  6,069 / 4,741 / 3,892 ms; GPU 7,715 / 0 (brak pomiaru) / 5,334 ms.
  Te próbki CPU/GPU mogą być opóźnione — nie dowodzą czasu pracy konkretnej
  zawieszonej klatki. `t_s` i `frame_ms` mają różne momenty próbkowania:
  nie należy wyliczać początku pauzy prostym odejmowaniem tych kolumn.
- `:898–901`, `:916–932`: po luce w aktualizacjach AUTOSHOT nadrabia terminy;
  wielokrotnie zapisuje `shot_t2036.png`, `shot_t2245.png`, `shot_t2246.png` itd.
  `summary.json` opisuje końcowe okno 600 klatek, a nie maksimum całego przejazdu.
- Brak wyjątków w tym przedziale, brak telemetrii GC oraz zmian fokusu/pauzy.
  Nie ma podstaw do przypisania tych trzech pauz GC lub konkretnej funkcji Unity.

## Rozmiar danych

W tym worktree brak `game/Assets/_Generated` i produktów GLB w
`Data/raw/derived`; nie można zmierzyć rzeczywistych scen/assetów użytego buildu.
Poniżej dane z lokalnych manifestów (suma bytes, nie pamięć runtime) i grafu:

| Kafel | Pliki w Data/Regions (B) | Chunki | High GLB (B, manifest) | Low GLB (B, manifest) | RAM Low/High MB (ESTIMATED) |
| --- | ---: | ---: | ---: | ---: | ---: |
| dk65-08 | 664756 | 64 | 368445652 | 106918360 | 55,5 / 122,7 |
| dk65-09 | 572902 | 64 | 415437780 | 152603088 | 51,4 / 122,4 |
| dk65-10 | 566517 | 64 | 347254428 | 86998536 | 49,0 / 117,3 |
| dk65-11 | 417406 | 64 | 320568916 | 61707516 | 48,2 / 113,0 |

Każdy kafel ma 2048 × 2048 m. dk65-10 nie jest rozmiarową anomalią.

## Wnioski z kodu przed zmianą

`WorldStreamer.cs:565` używa LoadSceneAsync, priorytetu Low i porcjowania aktywacji.
`BuildTileSource` jest jedynym źródłem runtime; log mówi **0 from packs** (`:49`).
Brak Addressables, WaitForCompletion i synchronicznego wczytywania danych w tej
ścieżce. Synchroniczne LoadScene w bootstrapie/menu nie są przejściami kafli.

**Przyczyna 165,9 s pozostaje niepotwierdzona.** Najbardziej prawdopodobna jest
przerwa w pracy playera po utracie fokusu: `ProjectSettings.asset:89` ustawia
`runInBackground: 0`, a DesktopAutoShot nie nadpisuje tej opcji. Brak logowania
fokusu uniemożliwia dowód. Możliwe są także zewnętrzny postój procesu / I/O.
Potwierdzony skutek wznowienia to dług zrzutów:
`DesktopAutoShot.cs:63` zwiększa termin tylko o jeden okres na każdą klatkę.

Osobne, rzeczywiste luki streamingu, bez dowodu związku z tymi trzema pauzami:

- `StreamingPolicy.cs:320` limituje tylko Loading, zwalniając slot przed końcem
  aktywacji/gotowania (nakładanie widoczne w `player.log:1049–1058`).
- `StreamingPolicy.cs:294,343` pozwala usuwać Activating. Destrukcja cookera może
  wtedy czekać synchronicznie w `WorldCollisionCooker.OnDestroy` na JobHandle.Complete.
- `WorldStreamer.cs:709` porzuca AsyncOperation z UnloadUnusedAssets; kolejna
  decyzja może zacząć load zanim czyszczenie się zakończy. Obecne czyszczenie
  ma w tym logu milisekundy, nie sekundy.

## Zmiana i weryfikacja

W toku. Wymagany kolejny przejazd playera z rejestracją fokusu/pauzy i stanów
streamingu; samo przejrzenie kodu nie potwierdza usunięcia pauz 21/2/166 s.
