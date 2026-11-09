---
name: visual-qa
description: Pętla samokontroli wizualnej — render stałych kamer kontrolnych w edytorze i zrzuty z telefonu, porównanie z referencjami i przegląd przez visual-critic wg standardu anti-AI-slop. Używaj po każdej zmianie wizualnej przed zgłoszeniem jej jako gotowej.
---
# Visual QA

## Kamery kontrolne
Zdefiniowane w `game/Assets/_Project/Editor/VisualQA/ControlCameras.asset` (pozycja, rotacja, FOV, pora dnia, pogoda, profil jakości): kabina-dzien, kabina-noc, deska-zblizenie, zewn-34-przod, bok-zestawu, tyl-naczepy, siodlo-podwozie, kolo-zblizenie, skrzyzowanie-oczy, ulica-perspektywa, krajobraz-dystans, deszcz-noc + kamery per lokalizacja (punkty kontrolne mapy z `docs/map-decisions.md`).

## Kroki
1. `scripts/visual-qa.ps1 -Scene <scena> [-Cameras all|<lista>] [-Profile High|Medium]` → Unity batchmode renderuje PNG do `artifacts/visual/<ts>/<kamera>.png` (stała rozdzielczość, np. 1920×1080 i 2400×1080).
2. Dla bramek: build na telefon i zrzuty z urządzenia z tych samych pozycji (tryb gry `--qa-camera <id>` uruchamiany przez `adb shell am start ... -e qa_camera <id>`).
3. Złóż contact sheet: render | zrzut z telefonu | referencja (ImageMagick `montage`) → `artifacts/visual/<ts>/sheet-<kamera>.png`.
4. **Obejrzyj każdy arkusz sam** (Read na PNG). Spisz, co widzisz — konkretnie.
5. Zleć ocenę `visual-critic` (subagent) z listą arkuszy. FAIL blokuje merge.
6. Kontrole automatyczne: histogram albedo materiałów, texel density, rozmiary tekstur vs budżet, brak brakujących UV/normalnych, obiekty pod/nad terenem.
7. Zapisz wynik do `docs/reports/visual/`.

## Zasada
Skrypt, który przeszedł, nie dowodzi niczego o wyglądzie. Gotowe = obejrzane, porównane z referencją, PASS od krytyka.
