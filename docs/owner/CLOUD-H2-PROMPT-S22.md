# Zlecenie dla chmury „H” — runda 2 (s22, 15.11 noc) — PC

Wklej do TEJ SAMEJ sesji chmury H:
```
Runda 2. Zasady jak w rundzie 1 (bez Unity/telefonów/Data/raw, do 5 agentów, każdy na swojej gałęzi, NIE scalasz, raport ≤ 20 linii po polsku z DOKŁADNYMI komendami dla lidera i „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”). Przeczytaj ponownie HANDOVER.md (wpisy SESJA 22 nad linią „Ostatni przydzielony ADR”), docs/11 D73 i D74 (wymagania PC jak ETS2/ATS: min i5-6400/GTX 660/8 GB → Low 1080p 30 fps; zalecane i5-9600/GTX 1660/12 GB → High 1080p 60 fps; WORKING_VALUE), docs/adr/0261-build-windows.md.
WAŻNE: w main jest już scalony win-build-0261 (BuildCommands.BuildWindows, scripts/build-windows.ps1, GamepadDriverInput, desktop domyślnie High/60 fps, DesktopAutoShot) oraz rail-fix-s21. Twoje PR #129–#133 powstały przed tym.
NIE dotykaj: start/spawn/route_start (spawn-fix-0262), generated/* regionów, torowisko (rail-dk65-s22). Bez ProjectSettings/, Packages/, asmdef (propozycje opisz). Nowe ADR: H7=0269, H8=0270, H9=0271.

H6 rebase rundy 1 na main (bez nowego ADR): #129, #130, #131, #132, #133 — po kolei merge origin/main do każdej gałęzi, rozwiąż konflikty z 0261 (szczególnie #133 vs `GamepadDriverInput` z 0261 — jedna implementacja pada, nazwy akcji wspólne; #131 vs `DesktopAutoShot`/tier High na desktopie), testy EditMode-bez-Unity niemożliwe → `dotnet build`/analiza, komentarz w każdym PR z listą konfliktów i kolejnością scalania. Jeden agent.
H7 tiery grafiki PC (gałąź pc-tiers-0269). Zdefiniuj jako dane profile Low/Medium/High/Ultra dla PC wg D74 (cienie: dystans/kaskady/rozdzielczość, LOD bias, gęstość roślinności i trawy, far clip, AA, SSAO, tekstury, MSAA/FXAA/TAA) — pliki URP w Assets/_Project/Rendering/Settings + kod wyboru w runtime; uzasadnij każdą wartość (źródło/ESTIMATED), nie psuj profili mobilnych (osobne assety PC albo warunek platformy). Kamery i komendy pomiaru dla lidera.
H8 menu ustawień PC (gałąź pc-settings-0270): rozdzielczość, tryb okna/fullscreen, vsync, limit FPS, tier grafiki, skala HUD, jednostki, głośności; zapis/odczyt; działa myszą, klawiaturą i padem; spójne z #131 (pc-ui-0265) i #133. Testy EditMode.
H9 dystrybucja PC (gałąź pc-dist-0271, tylko dokumenty + skrypty): co trzeba do wydania na PC bez kosztów (itch.io / Steam później — koszty i wymagania z oficjalnych źródeł, cytuj), struktura folderu buildu, instalator/zip, wersjonowanie, wymagania sprzętowe na stronie (z D74), licencje zasobów w buildzie (docs/LICENSES.md), crash log, IL2CPP vs Mono na PC (zalety/wady, zalecenie). Bez zakładania kont.
Na końcu podsumowanie z numerami PR.
```
