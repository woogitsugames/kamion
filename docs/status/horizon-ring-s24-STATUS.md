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

## Krok 2 — wdrożenie (kod napisany, przed kompilacją)
- Decyzja (c): przycinanie na piksel w shaderze + własność „najbliższy wczytany prostokąt”. `FarRing.cs` (bliźniak C#),
  `KamionFarRing.hlsl`, `WorldSurface` (`_FAR_RING_CLIP`, klon materiału per kafel) i `Vegetation` (`_HLOD_EDGE`),
  znacznik = renderer user value; `WorldStreamer.PushFarRects` przy każdej zmianie stanu/rebase; całe sektory
  wyłączane konserwatywnie (`FarRing.SectorVisible`). Przełącznik A/B: `-farRing off` / `KAMION_FAR_RING=off`.
- Testy: `Tests/EditMode/FarRingTests.cs`.

## Następny krok
`pwsh -NoProfile -File artifacts/horizon-ring-s24/vqa-ab.ps1` (w tle) — kompilacja + render przed (off) | po (on).
