# ADR 0212 — linie krawędziowe DK65 w Knyszynie (knyszyn, knyszyn-w, knyszyn-s) i kafle dalej: Mońki (−9,9), Tykocin (−9,7)
Status: Proposed (agent world-builder, s20, gałąź `knyszyn-edges-0212`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D64 (`docs/11`), ADR 0203 (siatka kafli), 0204 (`knyszyn`, `knyszyn-s`), 0205 (mechanizm
`edge_lines` dla klasy < GP), 0209 (`knyszyn-w`, otwarte p. 1–2), brief `docs/owner/S20-REGION-RING-BRIEF.md`.

## Kontekst
ADR 0209 zostawił: (1) koniec świata na kaflach (−9,9) (DK65 na Mońki) i (−9,7) (DW671 na Tykocin), (2) linie
krawędziowe DK65 widoczne na ortofoto, do dodania razem w `knyszyn` i `knyszyn-w`, żeby szew został spójny.

## Decyzja
1. **Linie krawędziowe DK65 = override, bez zmiany generatora.** `edge_lines: both` dopisane do istniejącego
   `dk65-carriageway-width` w **trzech** kaflach: `knyszyn`, `knyszyn-w` i także `knyszyn-s` — way 286990127 przechodzi
   przez szew `knyszyn`/`knyszyn-s` (y = 611583) na trasie Białystok → Knyszyn; bez niego urwanie linii przesunęłoby się
   tylko na drugi szew. Wszystkie trzy mają identyczny `set` (test).
   - DK65 ma klasę G (`highway=primary`), więc działa gałąź ADR 0205: linia 0,12 m, oś 0,20 m od krawędzi jezdni
     7,5 m = **3,55 m od osi**. Szerokość 0,12 m wg rozporządzenia [ZNAKI-Z2] pkt 2.2.2 (0,24 m tylko na drogach
     dwujezdniowych i trasach międzynarodowych; DK65 nie jest żadną z nich).
   - Pomiar położenia (narzędzie `artifacts/knyszyn-edges-0212/tools/linew.py`): ortofoto GUGiK 0,1 m 2025, całka nadwyżki
     jasności w przekroju (krok 0,05 m, mediana wzdłuż odcinka) — piki linii 3,0–4,0 m od osi OSM, mediana ~3,55 m
     (knyszyn-w 8 przekrojów, knyszyn 4, knyszyn-s 12, dk65-monki-01 7). Rozstaw osi linii 7,1 m wobec „6,8 m linia–linia”
     z ADR 0204/0209 (±0,3 m) — w tolerancji, różnica = sposób odczytu (krawędź vs oś linii). Szerokości samej linii
     z 0,1 m/px nie da się rozróżnić (0,12 vs 0,24 m) — wzięta z przepisu.
   - Linie przerwane we wlotach (Legionowa, Kościelna, widełki Goniądzkiej, Polna; render z góry), brak na rondzie.
2. **Kafel (−9,9) = region `dk65-monki-01`**: EPSG:2180 [758539, 613631, 760587, 615679], origin (759563, 614655),
   powiat 2008, wspólna krawędź y = 613631 z `knyszyn-w`. DK65 (way 232511647 → 98070954) wchodzi szwem w (759428,1;
   613631) — ten sam punkt co koniec trasy `knyszyn-w` — i wychodzi **zachodnią** krawędzią (758539; 614412,8) do kafla
   (−10,9) (niezbudowany). 1,18 km DK65, dwa przesunięte skrzyżowania z drogami polnymi (żwir SW 98072355; krótki
   łącznik 98072389 → asfalt na N i żwir 179127761 na E) — zgodne z ortofoto 0,1 m (crop 758870 613990 – 759030 614150).
   Graf 9 węzłów / 8 krawędzi, 42 budynki. Override: przekrój i linie jak `knyszyn-w`, bez latarni (orto: brak słupów).
3. **NMT pin roku z dwoma dniami nalotu.** Seria 2022 kafla (−9,9) to 2022-07-29 (3 arkusze) + 2022-08-27 (1 arkusz);
   `ingest.pick_latest` grupował po `akt_data`, więc pin `nmt_year: 2022` kończył się „no NMT 1 m series fully covers
   the tile”. Teraz przy pinie grupuje po `akt_rok` (jeden arkusz na godło, najnowszy dzień). Bez pinu zachowanie
   bez zmian. Kolumna/wiersz szwu z `knyszyn-w` identyczne (test, < 2 mm).
4. **Kafel (−9,7)** — patrz sekcja „Tykocin” niżej.

## Budżet (edytor, Low, overcast, `stats.txt`; A = stan main, B = z liniami)
| kafel | max draws A→B | max tris A→B | WORLD_MEMORY Low A→B |
|---|---|---|---|
| knyszyn-w | 227 → 227 (kamery świata 202 → 203) | 287k → 287k | 53,9 → 54,0 MB (markings 0,3 MB) |
| knyszyn | 429 → 429 | 370k → 370k | 95,5 MB (markings 0,4 MB) |
Linie dokładają ≤ 1 draw i ≤ 1 tys. trójkątów na kamerę. Pomiar na telefonie — lider.

## Walidacja
- `tests/gis/test_region_knyszyn_edges_0212.py`: ten sam `set` w 3 kaflach, linie 0,12 m na 3,55 m we wszystkich
  sekcjach DK65, `pick_latest` po roku, siatka (−9,9), szew dróg i punktów, przekrój, teren szwu identyczny.
- Rendery: `artifacts/knyszyn-edges-0212/vqa/<region>/e1-Low` (knyszyn, knyszyn-w, knyszyn-s), `r1-Low` (dk65-monki-01).
- Ocena `visual-critic` nie wykonana (subagent nie tworzy subagentów) — do lidera.

## Otwarte
1. Zatoka autobusowa na DK65 w `knyszyn-s` (762500 609950): na orto linia krawędziowa przerywana (P-7c/d) — u nas ciągła.
2. Kafel (−10,9) dalej na Mońki — dziś koniec świata na zachodniej krawędzi `dk65-monki-01`.
3. `dk65-inlet-south` (knyszyn): szara plama przed kamerą — była już w r3 (ADR 0204), nie od linii.
