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
  (`:900`), 2134,71 ms (`:906`) i 165917 ms (`:934`). Następny load to
  dopiero dk65-11 (`:938–940`), 250 ms + 129 ms.
- `frametimes.csv:120282`, `:120708`, `:122715`: klatki 120281, 120707,
  122714, odpowiednio t_s=2031,9634 / 2041,9558 / 2241,3096 i
  frame_ms=21106,152 / 2134,708 / 165917. CPU main z FrameTimingManager:
  6,069 / 4,741 / 3,892 ms; GPU 7,715 / 0 (brak pomiaru) / 5,334 ms.
  Te próbki CPU/GPU mogą być opóźnione — nie dowodzą czasu pracy konkretnej
  zawieszonej klatki. `t_s` i `frame_ms` mają różne momenty próbkowania:
  nie należy wyliczać początku pauzy prostym odejmowaniem tych kolumn.
- `:897–901`, `:915–933`: po luce w aktualizacjach AUTOSHOT nadrabia terminy;
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

- `StreamingPolicy.cs:291` limituje tylko Loading, zwalniając slot przed końcem
  aktywacji/gotowania (nakładanie widoczne w `player.log:1049–1058`).
- `StreamingPolicy.cs:274,308` pozwala usuwać Activating. Destrukcja cookera może
  wtedy czekać synchronicznie w `WorldCollisionCooker.OnDestroy` na JobHandle.Complete.
- `WorldStreamer.cs:709` porzuca AsyncOperation z UnloadUnusedAssets; kolejna
  decyzja może zacząć load zanim czyszczenie się zakończy. Obecne czyszczenie
  ma w tym logu milisekundy, nie sekundy.

## Zmiana i weryfikacja

- `StreamingPolicy.cs:292`: limit obejmuje Loading + Activating. Warunki wyładowania
  (`:275`) i eksmisji (`:309`) dopuszczają tylko Ready, więc streamer nie niszczy
  cookera z trwającym jobem. Nie usunięto zabezpieczenia Complete w OnDestroy:
  przy zamknięciu całego świata nadal trzeba bezpiecznie zwolnić NativeArray.
- `WorldStreamer`: śledzony uchwyt UnloadUnusedAssets i blokada nowych decyzji
  do isDone; czyszczenie nie nakłada się również na Unloading. Log start/done
  pokazuje wall-clock czyszczenia. Log focus/pause i update gap >= 1 s pokazuje
  realtime, fokus, runInBackground, liczby Loading/Activating/Unloading, cleanup
  i przyrost liczników GC od poprzedniej aktualizacji. Bez alokacji w zwykłej klatce
  z tej diagnostyki (przegląd kodu; pomiar w Unity odroczony).
- `DesktopAutoShot.cs:43,49–53`: okresowy przebieg dowodowy pracuje w tle;
  po zrzucie termin jest planowany od teraz, bez nadrabiania utraconych obrazów.
  To eliminuje potwierdzoną serię zrzutów po wznowieniu i usuwa domyślną pauzę
  po utracie fokusu dla tego trybu. Domyślna zwykła gra nie jest zmieniona.
- Dodano 6 testów EditMode w `StreamingWorkSchedulingTests.cs`: slot do Ready,
  mieszany limit Loading/Activating, daleki unload i eksmisja dopiero po Ready,
  brak długu zrzutów po 166 s, warunki wyłączenia/terminu/quit.
- Bez Unity wykonano **6/6 PASS** tych samych ciał testów przez in-memory C#
  harness: `pwsh -NoProfile -File tools/streaming-check/check-logic.ps1`.
  To **nie jest wynik Unity EditMode/NUnit**: harness ma minimalne atrapy API Unity
  i asercji NUnit; nie implementuje ładowania, gotowania, renderu ani cleanup.
  `-Before` używa StreamingPolicy z bazowego `f08172268` i przywraca stary
  przyrost terminu zrzutów (`+= every`) w wydzielonej funkcji: 5 FAIL, 1 PASS.
  Wyniki lokalne: `artifacts/stream-hitch-cli/logic-before.txt`, `logic-after.txt`.
- `git diff --check`: PASS. Nie uruchamiano edytora Unity, test runnera Unity,
  playera, buildów ani narzędzi generujących świat. Nie kopiowano dowodów do main
  (polecenie użytkownika: pracować wyłącznie w tym worktree).

## Co wymaga weryfikacji w buildzie

1. Po integracji: `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`
   oraz PlayMode streamingu, w osobnej autoryzowanej sesji. Sprawdzić brak regresji
   testu zerowych alokacji `WorldStreamerHook0273Tests`.
2. Powtórzyć Windows High C → Tykocin tym samym playerem/hardware, z `-stream 1`
   i `-shot_every 10`. Celowo przełączyć fokus na >= 30 s i >= 166 s: jazda powinna
   trwać, log ma rejestrować focus=false, background=true, bez serii zrzutów po powrocie.
3. Osobny pomiar bez zrzutów, przy utrzymanym fokusie, obejmujący dk65-08 → knyszyn-s.
   Porównać wszystkie surowe klatki CSV, pamięć i gotowość kafli przed dojazdem
   (zwłaszcza skrzyżowania, gdzie serializacja Loading + Activating opóźnia następną scenę).
4. Jeśli pauza wróci: skorelować update gap z focus/pause, gcDelta i cleanup start/done;
   profilerem playera ustalić blokujące I/O / wątek / native engine. Liczba GC mówi,
   czy wystąpiła kolekcja, ale sama nie mierzy czasu GC. Nadal nie można ogłosić
   usunięcia pierwotnej pauzy 165,9 s bez takiego przejazdu.
5. W środowisku posiadającym `_Generated` porównać rozmiary rzeczywistych scen,
   meshy i tekstur z manifestami; lokalne dane nie dowodzą zgodności ze starym buildem
   `edeb582320` z badanego przejazdu.
