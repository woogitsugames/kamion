# horizon-ring-s24 — daleki plan jako pierścień za wczytanymi kaflami (ADR 0354)

Gałąź: `worktree-agent-af66c0475770b901e`, baza `f80b3a4a8`. Dowody: `artifacts/horizon-ring-s24/` (w worktree; poza gitem —
lider kopiuje do main). Środowisko Unity prywatne: Library + sceny `_Generated` 11 kafli skopiowane z `win-build`
(`artifacts/horizon-ring-s24/copy-env.ps1`); zmiana jest tylko w runtime (streamer + shadery) — bez reimportu, bez derived.

## Krok 1 — analiza (zrobione)
- Przyczyna pustego horyzontu: `EdgeSides.FarSectorMayShow` (ADR 0311) chowa sektor kafla w stronę każdego sąsiada z
  grafu, także narożnego; sektor `far_north` obejmuje narożnik NE, więc 03 (sąsiedzi E, S, NE, SW) traci wszystkie 4.
  Na północ od 03 nie ma żadnego kafla — tam zostaje sama mgła.
- Daleki plan jest skompresowany do pasa ≤ ~660 m za granicą kafla (ADR 0085), więc pokazany w stronę wczytanego
  sąsiada leżałby na jego geometrii; budynki w zarejestrowanych kaflach są już wycięte w generatorze (ADR 0311), lasy i WN nie.

## Krok 2 — wdrożenie (zrobione, kompiluje się)
- Decyzja (c): przycinanie na piksel w shaderze + własność „najbliższy wczytany prostokąt”. `FarRing.cs` (bliźniak C#),
  `KamionFarRing.hlsl`, `WorldSurface` (`_FAR_RING_CLIP`, klon materiału per kafel, wariant w
  `Resources/WorldStreaming/FarRingClipVariants.mat`) i `Vegetation` (`_HLOD_EDGE`), znacznik = renderer user value;
  `WorldStreamer.PushFarRects` przy każdej zmianie stanu/rebase; całe sektory wyłączane konserwatywnie
  (`FarRing.SectorVisible`). Przełącznik A/B: `-farRing off` / `KAMION_FAR_RING=off`.
- Poprawka narzędzia QA: `WorldNeighbourQa.StartRoot` (kamery `-Gate3`/`-qaTruckPose` względem kafla startowego).

## Krok 3 — dowody (zrobione)
- `vqa-ab.ps1`: 03 (7 kamer) i knyszyn-w (64 kamery), High clear, `-Neighbours auto`, off|on → `*/off`, `*/on`, `cmp-*.jpg`.
  03 edge-north i knyszyn-w edge-west: las zamiast mgły; reszta kamer bez zmian (≤ 0,9 % pikseli).
- `vqa-diag.ps1` + `ring-cams-03.json`: kamery diagnostyczne (narożnik 03/01, styk 03/04, widoki z 180 m i 1 km),
  High `diag-03-r2/`, Low `diag-03-low/`. (`diag-03/` = pierwszy przebieg z kamerami w losowym kaflu — błąd QA, poprawiony.)
- Koszt (03 High, stats.txt): +6…+14 draw, +65…+130 tys. trójkątów w kadrze; w budżecie docs/06 §6.
- ADR 0354 (Proposed).

## Krok 4 — testy (zrobione)
- r1: 20 fail — include `KamionFarRing.hlsl` względny (testy kopiują WorldSurface do `_Generated`) + zbyt ostrożny cull.
  Poprawione. r2 (`run-tests2.ps1`): **1447 pass, 0 fail, 153 skip** (`editmode-20261127-002815.xml`).

## Następny krok
Lider: visual-critic na `artifacts/horizon-ring-s24/**/cmp-*.jpg` (subagent nie tworzy subagentów), przegląd shaderów
przez rendering-perf, A/B w buildzie #10 wg ADR 0354 „Weryfikacja”. Nie scalać bez przeglądu.
