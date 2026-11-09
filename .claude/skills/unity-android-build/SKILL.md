---
name: unity-android-build
description: Zbuduj APK z projektu Unity w batchmode, zainstaluj na podłączonym telefonie przez adb, uruchom, zbierz logcat, zrzut ekranu i metryki. Używaj przy każdym buildzie testowym i każdej bramce etapu.
---
# Unity → Android: build, instalacja, pomiar

## Kroki
1. Upewnij się, że żaden inny proces Unity nie ma otwartego katalogu `game/` (kolejka buildów — jeden naraz).
2. `scripts/build-android.ps1 [-Development] [-Install] [-Profile Medium]`:
   - wywołuje `Unity.exe -batchmode -nographics -quit -projectPath game -executeMethod Game.Editor.Build.AndroidBuilder.Build -logFile artifacts/build/<ts>.log`,
   - sprawdza exit code i obecność `Build succeeded` w logu; przy błędzie wypisuje pierwsze błędy kompilacji i kończy się kodem ≠ 0,
   - zapisuje APK do `artifacts/apk/<version>-<sha>.apk` + SHA256.
3. Instalacja: `adb devices -l` (dokładnie jedno urządzenie lub `-s <serial>`), `adb install -r -g <apk>`, `adb shell am start -n <package>/<activity>`.
4. Logcat: `adb logcat -c` przed startem, potem `adb logcat -d -s Unity:V AndroidRuntime:E CRASH:E > artifacts/logs/<ts>.txt`. Szukaj `Exception`, `FATAL`, `Vulkan`.
5. Zrzut: `adb exec-out screencap -p > artifacts/screens/<ts>.png` — obejrzyj go (Read) i dołącz do raportu.
6. Metryki: overlay diagnostyczny gry zapisuje CSV (frame time, FPS, pamięć, temperatura z `BatteryManager`/thermal API jeśli dostępne) do pamięci aplikacji → `adb pull`. Dodatkowo `adb shell dumpsys gfxinfo <package>` i `dumpsys meminfo <package>`.
7. Raport: urządzenie (model, SoC, GPU, Android), wersja buildu, SHA, profil jakości, p50/p95/p99 frame time, pamięć PSS, temperatura start/koniec, czas sesji, błędy.

## Pułapki
- Wersje SDK/NDK/JDK tylko z Unity Hub. Jedna ścieżka SDK.
- Target API zgodny z aktualnym wymogiem Google Play (sprawdź).
- Development build zawyża koszty — pomiary wydajności na buildzie release-like z włączonym overlay.
- Rozgrzany telefon: pomiar wydajności po 30 min, nie z pierwszej minuty.
