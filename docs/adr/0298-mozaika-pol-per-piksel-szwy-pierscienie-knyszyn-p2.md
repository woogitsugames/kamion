# ADR 0298 — Mozaika pól per piksel, ciągłość szwów kafli, pierścienie na płytach skrzyżowań, nasadzenia działek (knyszyn-p2-s24)

Status: Proposed, 2026-11-19 (agent knyszyn-p2-s24; zmiana globalna — generator, shader terenu, import fartucha).
Powiązane: ADR 0295 (mozaika pól, swardCalm), 0085 (fartuch / far-field), 0064 (mapa nieba GI), 0110 / 0194 (UV1 płyt
skrzyżowań), 0132 / 0163 (korony z ortofoto → drzewa ogrodowe), 0287 (deski), D68 (lato wszędzie).
Recenzja: `docs/reports/REVIEW-2026-11-18-s24-cabin-lights-knyszyn.md` §3 (N1–N5, FAIL).

## Kontekst — przyczyny (zmierzone / odczytane z danych)

1. **N1 szwy kafli (skok 15–22 poziomów sRGB).** Trzy niezależne przyczyny:
   (a) fartuch poza kaflem (`WorldEdgeBuilder.ApronMask`) to sinusowy szum suchości B 0,35–0,82 i strefy lasu / gruntu
   wpisane dla Białegostoku — nic wspólnego z maską terenu przy krawędzi; (b) mapa widoczności nieba (`KamionWorldGI`)
   kończy się skokiem `inside` 1 → 0 dokładnie na krawędzi kafla (fartuch dostaje pełne niebo naraz); (c) mozaika
   ADR 0295 była zapisana w COLOR_0.b na siatce maski 1 m, ale pas terenu High ma wierzchołki 1 m tylko przy drogach
   (8 m dalej), Low 2 m — miedze 2 m znikały, pasy czytały się jak „blade smugi” (N3), a fartuch nie mógł jej nieść.
2. **N2 koncentryczne pierścienie na asfalcie wlotów.** `roads.meshing._patch_uv1` liczył współrzędną pasa (UV1.x) z
   odległości euklidesowej do najbliższego punktu łańcucha ramienia; za wolnym końcem okna łańcucha (krawędź kafla,
   rozdział jezdni) najbliższy punkt to wierzchołek końcowy, więc „odległość boczna” rosła promieniście, a koleiny
   (`frac(UV1.x)` w `WorldPBR` `_ROADWEAR`) rysowały pierścienie wokół niego (rastrowanie UV1 płyty przy zamknięciu
   DK65 W: `artifacts/knyszyn-p2-s24/u1-before.png`).
3. **N3 pola khaki.** Kolor pól = tekstura trawy × wzmocnienie suchości 0,70 przy niskim B — ciemna oliwka; jedyną osią
   zróżnicowania była suchość.
4. **N4 gołe działki, „brokuły”.** Knyszyn nie miał `plot_canopy.json` (korony z ortofoto, ADR 0132), więc 0 drzew
   ogrodowych z koron; jednocześnie reguła samosiewu sadziła drzewa co ~20 m (siatka 14 m, 45 %) na całym BDOT
   OT_PTTR_A — pola w użyciu — stąd pojedyncze młode drzewa i krzaki na polach.

## Decyzja

(uzupełniane w trakcie — patrz sekcje poniżej)
