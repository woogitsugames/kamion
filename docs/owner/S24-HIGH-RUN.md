# S24+ High: pomiar bramki 3 z buildem po ADR 0046 (checklista, NIE uruchomiona)

S24+ (`RZCX60VE8ZY`, SM-S926B) to **telefon roboczy właściciela** (połączenia, SMS). Ten plik tylko opisuje przebieg. Nic z niego
nie wolno uruchomić bez wyraźnej zgody właściciela w tej sesji. Każdy krok adb ma `-s RZCX60VE8ZY`. Skrypty nie wpisują PIN-u,
nigdy `KEYCODE_SLEEP/POWER`. Zablokowany telefon = pomiar odrzucony (exit 5), nie obchodzimy tego.

Cel: liczby G3-A i G3-B dla High 60 FPS z buildem zawierającym ADR 0046 (adaptacyjny render scale, fallback termiczny 30 FPS,
cienie soft Low), kadry kamer z telefonu i klipy jazdy przez DK8 (wcześniejsze klipy były z kamery statycznej `dk8_dk19_exit`, a
oryginały zginęły z worktree; MSAA 2x vs domyślne = UNVERIFIED).

## 0. Warunki wstępne (wszystkie muszą być spełnione, inaczej STOP)

| Warunek | Komenda | Wymóg |
|---|---|---|
| Zgoda właściciela | wiadomość w czacie | jest, w tej sesji |
| Telefon podłączony do portu USB-C komputera, widoczny | `adb devices` | `RZCX60VE8ZY device` |
| Bateria | `adb -s RZCX60VE8ZY shell dumpsys battery` (`level`) | **>= 40 %** na starcie; w trakcie < 30 % = koniec pracy; nigdy < 20 % |
| Temperatura baterii | to samo (`temperature`, dziesiąte części °C) | **< 36 °C** (360) na starcie każdego przebiegu |
| Keyguard | `adb -s RZCX60VE8ZY shell dumpsys window \| findstr isKeyguardShowing` | `isKeyguardShowing=false` (właściciel odblokowuje ręcznie; PIN nigdy z komputera) |
| Ekran aktywny | `adb -s RZCX60VE8ZY shell dumpsys power \| findstr mWakefulness` | `Awake` |
| Brak połączenia w toku | `adb -s RZCX60VE8ZY shell dumpsys telephony.registry \| findstr mCallState` | `mCallState=0` (zero = bezczynny) |
| Jeden proces Unity | Menedżer zadań / `tasklist \| findstr Unity.exe` | żadnego innego buildu/testu w tym projekcie |
| Czysty checkout | `git status` | czysty, `git log -1` = sha do wpisania w raporcie |

Przed każdym kolejnym przebiegiem (G3-B, klipy) powtórz bateria / temperatura / keyguard. Przy temperaturze >= 36 °C odczekaj
na ostygnięcie (nie śpij w pętli blokującej, sprawdzaj co kilka minut), potem dopiero kolejny przebieg.

## 1. Natywna rozdzielczość: QHD+ czy FHD+ (zrób najpierw, jedna minuta, nic nie uruchamia gry)

```
adb -s RZCX60VE8ZY shell wm size
adb -s RZCX60VE8ZY shell wm density
adb -s RZCX60VE8ZY shell dumpsys display | findstr /i "mBaseDisplayInfo real"
```

- `Physical size: 1440x3120` = natywna QHD+. `Override size` obecny lub `1080x2340` = tryb FHD+ ustawiony w Ustawieniach (Wyświetlacz,
  Rozdzielczość ekranu); wtedy dowody High są liczone na ok. 3,2 Mpx zamiast 4,49 Mpx i **nie wolno ich porównywać** z wcześniejszym
  pomiarem QHD+ (ADR 0046: 3120x1440, render scale 1.0 = 4,49 Mpx).
- Nie zmieniaj rozdzielczości sam (to ustawienie systemu telefonu właściciela). Zapisz wartość w raporcie.
- Po starcie gry sprawdź w logcat rozdzielczość renderu: `adb -s RZCX60VE8ZY logcat -d -s Unity | findstr /i "control camera"` (wiersz
  `[LAB] control camera <id> active (WxH)` podaje pixelWidth x pixelHeight kamery) oraz `[CONTROLS] session lighting=... tier=...`.
  Oczekiwane High: `tier=High`, szerokość/wysokość = natywna x render scale (1.00 do 0.80, adaptacyjnie).

## 2. Build i G3-A + G3-B (jedna komenda na segment, sama kolejkuje build)

Ten sam build instaluje się raz; segment B używa `-SkipBuild`. `-WorldHigh` buduje APK z treścią świata High (scena `WorldC_High`).

```
pwsh scripts/gate3-run.ps1 -Serial RZCX60VE8ZY -Tier High -Fps 60 -WorldHigh -Segment A
pwsh scripts/gate3-run.ps1 -Serial RZCX60VE8ZY -Tier High -Fps 60 -WorldHigh -Segment B -SkipBuild
```

Wyniki: `C:\Users\matma\Documents\Claude\kamion\artifacts\gate3\<ts>\RZCX60VE8ZY\` (`gate3-result.json`, `drive\metrics.json`,
`drive\frametimes.csv`, `cam\*.png`, `logcat-run.txt`). Uruchamiaj z głównego checkoutu albo ustaw `ArtifactsDir` tak, żeby dowody
trafiły pod absolutną ścieżkę głównego repo (nie do worktree, który zostanie usunięty).

Segment A zawiera dodatkowo kadry z telefonu `truck-34` i `cab-dash` w oświetleniu overcast / lowsun / dusk
(`cam\truck-34_<oświetlenie>.png`, `cam\cab-dash_<oświetlenie>.png`).

Zapisz do raportu z `gate3-result.json`:
- `gitSha`, `apk.sha256`, `apk.sizeMB`, `valid` (musi być `true`), `driveLog.autopilotStartedLine`, `driveLog.suspiciousLines`;
- `frameTime` p50 / p95 / p99 (budżet High WORKING_VALUE: p95 <= 17,0, p99 <= 20 ms), `gpuMs`, `cpuMainMs`, `pssMb` (<= 2000),
  `batteryTempBeforeC` / `batteryTempAfterC`, `thermalStatus`;
- `cameras` (CAPTURED / MISSING_IN_SCENE / NO_SCREENSHOT / REJECTED_LOCKED) i `camerasCaptured/camerasPlanned`.
  Poprzedni przebieg S24+: 17/21 w G3-A (2x MISSING_IN_SCENE `s0012`, `s0362`; 2x NO_SCREENSHOT `s0262`, `s0312`). `s0012` jest już
  przesunięty poza kabinę (r6 W-N10), więc ma być CAPTURED.
- Czy adaptacyjny render scale i fallback 30 FPS zadziałały: `adb -s RZCX60VE8ZY logcat -d -s Unity | findstr /i "adaptive thermal scale"`.
  Jeśli `thermalStatus >= 2` przez > 30 s, gra przechodzi na 30 FPS i pomiar 60 FPS nie jest ważny dla reszty przebiegu (zapisz to).

Interpretacja bez udawania: jeden przebieg to jedna próbka. Różnica p95 między przebiegami przy innej temperaturze jest szumem
termicznym, dopóki nie ma 3 przebiegów w podobnej temperaturze (UNVERIFIED do tego czasu).

## 3. Klipy DK8 w jeździe (nie statyczna kamera)

Trasa autopilota (`route_start.json`, 2402,8 m) przechodzi przez wyjazd DK8/DK19: najbliższy punkt do kamery `dk8_dk19_exit`
to s = 2252 m (1,6 m od kamery; liczone z `points_en`, krok 2 m). Klip jazdy zaczyna się ok. 110 m wcześniej.

Dla każdej wersji MSAA osobny przebieg, ten sam build, ta sama temperatura (±2 °C), po jednym przebiegu na wersję, minimum dwa
na wersję jeśli czas pozwala. Nagrywanie ekranu (limit systemowy 180 s, bez dźwięku):

```
# terminal 1: start gry w jeździe (autopilot po trasie od s=2140, stop w s=2400), High 60 FPS
pwsh scripts/device-metrics.ps1 -Serial RZCX60VE8ZY -Launch -DurationSeconds 40 -WarmupSeconds 12 -Tier High -Fps 60 `
     -Scene WorldC_High -Autopilot route -Speed 40 -Trailer 40 -Extra "telemetry=1,route_s=2140,route_end=2400,lighting=overcast"
# terminal 2, od razu po starcie gry (czas ok. 30 s):
adb -s RZCX60VE8ZY shell screenrecord --time-limit 30 --bit-rate 16000000 /sdcard/dk8_drive_msaa_default.mp4
adb -s RZCX60VE8ZY pull /sdcard/dk8_drive_msaa_default.mp4 C:\Users\matma\Documents\Claude\kamion\artifacts\gate3\<ts>\dk8\
adb -s RZCX60VE8ZY shell rm /sdcard/dk8_drive_msaa_default.mp4
```

Wariant MSAA 2x: dodaj do `-Extra` nadpisanie profilowe (patrz `game/Assets/_Project/Rendering/RenderOverrides.cs`; nazwa `rq_msaa=2`
w poprzednim przebiegu). Sprawdź w logcat, że gra przyjęła nadpisanie, zanim uznasz klip za wariant MSAA 2x.
Uwaga: `screenrecord` dokłada obciążenie kodera, więc FPS z nagrywaniem **nie** idzie do tabeli budżetu; liczby bierz z przebiegów
gate3-run bez nagrywania i z `metrics.json` powyższego uruchomienia oznacz "z nagrywaniem".
Po pobraniu: sprawdź `ffprobe` (czas, rozdzielczość, fps) i obejrzyj klip (kilka klatek `ffmpeg -ss <t> -i klip.mp4 -frames:v 1`).
Ocena wizualna MSAA jest UNVERIFIED, dopóki ktoś nie obejrzy klipów i tego nie zapisze.

## 4. Zakończenie (obowiązkowo, także po błędzie)

```
adb -s RZCX60VE8ZY shell am force-stop com.woogitsugames.kamion
adb -s RZCX60VE8ZY shell dumpsys battery | findstr "level temperature"
adb -s RZCX60VE8ZY shell dumpsys window | findstr mCurrentFocus   # gra nie ma być na pierwszym planie
```

Zapisz do raportu bateria na koniec (nie < 30 %, jeśli tak, to przebieg przerwano) i potwierdzenie `force-stop`. Nie zamykaj
ekranu, nie blokuj telefonu (zero `KEYCODE_SLEEP/POWER`). Telefon ładuje się wolno z USB komputera, więc po 2-3 przebiegach zrób
przerwę zamiast kontynuować przy 30-35 %.

## 5. Kolejność i kryteria ważności

1. Warunki z sekcji 0 -> sekcja 1 (rozdzielczość) -> G3-A -> (warunki ponownie) -> G3-B -> (warunki) -> klipy DK8 -> sekcja 4.
2. Przebieg jest **ważny** tylko gdy `valid=true`, keyguard=false przed i po każdym kroku, temperatura startowa < 36 °C.
3. Wynik wpisz do `docs/reports/GATE-3-draft.md` jako dopisek z sha buildu i temperaturą. Werdykt bramki należy do właściciela.
4. Czego ta checklista nie rozstrzyga: jakości wizualnej (ocena `visual-critic` + właściciela) i odczucia jazdy (`docs/owner/FEEL-TEST.md`).
