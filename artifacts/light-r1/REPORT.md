Runda 1, gałąź gpt-light-r1, SHA wyniku c740ce5b59a1253e08488355a20561400ac6bb1a; baza main 4c9905b1. Runda zakończona z ustawieniami roboczymi, bez deklaracji PASS całej bramki.

- High: RCAS 0 → 0,75 po ablacji 40 PNG; HF asfaltu 3,437 → 5,700 w ablacji, końcowo 5,676. Jawne nadpisanie RCAS=0 nadal działa.
- Wyłączono końcowy dither tylko High. Końcowy HF czystego błękitu 0,232 (cel ≤0,6), wobec 0,572 z ditherem; wzmocnienie kontrastu ×16 ujawnia stopnie 8-bitowego gradientu, telefon pozostaje UNVERIFIED.
- Clear ma fotograficzne chmury CC0 Poly Haven, liniową mapę RG 4096×2048 i chromę 2 wybraną spośród 1/2/3/4. Naprawiono obrót horyzontu i szew pochodnych UV. Pochodzenie i hashe: ClearCloudsSource.json oraz docs/LICENSES.md.
- Clear whiteClip 1,2 → 1,8, bez zmiany EV: w natywnym ROI furgonetki maksimum RGB 250/250/250 → 245/244/245, udział kanałów ≥250 około 73,82/73,82/64,80% → 0/0/0%. Detal płaskiego lakieru nadal nie jest odzyskany.
- Tylko High/LowSun: flagą LightingPreset.highSunShadowFilter=3 włączono łagodniejszy filtr, atlas pozostaje 2048; inne presety i tiery wracają do dziedziczenia. Próg ≤1 px/10 m: niespełniony; maksymalne odchylenie High 1,44/1,27 px wobec legacy 1,55/1,54 px przy dwóch promieniach; wszystkie 936 kolumn.
- Dowody: [160 par przed](sbs/before/index.html) i [160 par po](sbs/after/index.html), każda ≤960 px. Stan przed odtwarza dawne parametry na tej samej świeżej geometrii. Wszystkie pary przejrzane; niezależny krytyk ocenił 80 końcowych par High.
- Spośród 40 referencji 27 dziennych dopuszczono do ostrożnej oceny ROI; 13 wykluczono przez błędną pozę lub zachód słońca. Żadna poza nie otrzymuje PASS. Metryki masek heurystycznych nie są kalibracją całej klatki.
- Budżet wszystkich 160 wpisów kamer: draws +0, tris +0%, instancing osobno w [sbs-budget-all.json](sbs-budget-all.json). To estymaty CPU; koszt GPU dodatkowego odczytu nieba oraz filtra High wymaga pomiaru lidera na urządzeniu.
- Testy końcowe: [EditMode 264/264](tests/editmode-final.xml); GIS: 493 passed, 1 xfailed w 753,56 s na świeżo regenerowanym świecie i raporcie fidelity. Pełny GIS wykonany tylko na końcu rundy, w heavy po analizie, bez równoległego własnego ciężkiego zadania.
- Model EV, radiancja SH, natężenie słońca i skala renderowania bez zmian. Brak nowego przebiegu ani efektu pełnoekranowego Low; nie dodano pól QualityProfile ani migracji.
- Pozostają: płaskie wnętrza dużych chmur, różnice tonów drogi i zbyt jednorodny overcast w części porównań. Komin należy do landmarks, mikrodetal ścian i materiał drogi do ich właścicieli; tych źródeł nie zmieniono.
- Wyniki bazowej regeneracji spoza light zachowano w generated-baseline-rebuild.patch i przywrócono do bazy przed następną rundą; nie są zmianą produkcyjną light. Log build_world nie zawiera fallback=True.
- Przewidywane konflikty: addytywne QualityProfileApplier/RenderOverrides, EnvironmentLighting/LightingPreset/WorldAtmosphere/Sky.shader, presety Clear/LowSun i dopisek LICENSES. Niezależne recenzje są w review-rcas; decyzje i ograniczenia w ADR 0108.
- Integruje wyłącznie lider z gpt-light-r1; po integracji regeneracja/import w slotach i pomiar A16. Bez merge do main, pushowania i telefonów w tej sesji. Kolejna runda: gpt-light-r2, merge aktualnego main, zmierzch i lampy.

