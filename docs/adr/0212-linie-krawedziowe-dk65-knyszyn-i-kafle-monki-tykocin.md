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
     jasności w przekroju (krok 0,05 m, mediana wzdłuż odcinka), 4 + 8 + 12 + 7 przekrojów (knyszyn, knyszyn-w,
     knyszyn-s, dk65-monki-01). Linie są po obu stronach we wszystkich czterech kaflach; piki 3,0–4,0 m od osi OSM, ale
     piki ≥ 3,7 m leżą na krawędzi asfaltu/poboczu. Najczystsza seria (way 305910042, 5 przekrojów): linie −3,65…−3,70
     i +3,05…+3,15 przy linii środkowej −0,2…−0,35 → **6,8 m linia–linia** (jak ADR 0204/0209), ok. 3,4 m od osi.
     Generator: 3,55 m od osi → **7,1 m linia–linia**, +0,3 m = granica tolerancji pomiaru — `WORKING_VALUE`
     (wspólna stała `EDGE_LINE_INSET_MINOR` z dk65-01…05, zmiana = przebudowa 5 kafli; do szlifu). Szerokości linii
     z 0,1 m/px nie da się rozróżnić (0,12 vs 0,24 m) — wzięta z przepisu.
   - Ramiona ronda DK65/DW671 w `knyszyn` (way 1464342634/-635/-638/-640: jednokierunkowe, 1 pas, 16,7–17,3 m, przy
     wysepkach rozdzielających) zostają bez override i bez linii krawędziowych — jak dotąd (test je nazywa).
   - We wlotach linia przechodzi w przerywaną przez wylot (obejrzane na planach: Legionowa, widełki Goniądzkiej, oba
     skrzyżowania w `dk65-monki-01`); brak na rondzie. Kościelnej i Polnej nie oglądano z góry.
2. **Kafel (−9,9) = region `dk65-monki-01`**: EPSG:2180 [758539, 613631, 760587, 615679], origin (759563, 614655),
   powiat 2008, wspólna krawędź y = 613631 z `knyszyn-w`. DK65 (way 232511647 → 98070954) wchodzi szwem w (759428,1;
   613631) — ten sam punkt co koniec trasy `knyszyn-w` — i wychodzi **zachodnią** krawędzią (758539; 614412,8) do kafla
   (−10,9) (niezbudowany). 1,18 km DK65, dwa przesunięte skrzyżowania z drogami polnymi (żwir SW 98072355; krótki
   łącznik 98072389 → asfalt na N i żwir 179127761 na E) — zgodne z ortofoto 0,1 m (crop 758870 613990 – 759030 614150).
   Graf 9 węzłów / 8 krawędzi, 42 budynki. Override: przekrój i linie jak `knyszyn-w`, bez latarni (orto: brak słupów).
3. **NMT pin roku z dwoma dniami nalotu** (zmiana wspólnego `tools/worldgen/ingest.py`). Seria 2022 kafla (−9,9) to 2022-07-29 (3 arkusze) + 2022-08-27 (1 arkusz);
   `ingest.pick_latest` grupował po `akt_data`, więc pin `nmt_year: 2022` kończył się „no NMT 1 m series fully covers
   the tile”. Teraz przy pinie grupuje po `akt_rok` (jeden arkusz na godło, najnowszy dzień). Bez pinu zachowanie
   bez zmian; dla `knyszyn-w` (drugi region z pinem) nowa ścieżka wybiera te same 4 arkusze co jego manifest (test).
   Kolumna/wiersz szwu z `knyszyn-w` identyczne (test, < 2 mm).
4. **Kafel (−9,7) = region `dw671-tykocin-01`**: EPSG:2180 [758539, 609535, 760587, 611583], origin (759563, 610559),
   powiat 2008, NMT pin 2022 (jak oba sąsiedzi). Szwy: północny z `knyszyn-w` (DW671 way 70329870 w (760129,2; 611583)
   + droga serwisowa), wschodni z `knyszyn-s` (way 98071886 w y 610278,8) — te same punkty i ten sam teren (test).
   DW671 2,61 km do południowej krawędzi (758587,2; 609535 → kafel (−9,6), niezbudowany), przez wieś z fermą (144
   budynki LoD1/LoD2), skrzyżowanie 4-wlotowe z przejściem dla pieszych na wlocie S (zgodne z orto), dwa wloty T na
   południu. DW671 bez linii krawędziowych (orto: tylko oś przerywana; w 25 przekrojach brak stałej linii) i z
   szerokością BDOT 6,5–7,0 m (jak ta sama droga w `knyszyn-w`, bez override).
5. **Trasy kontrolne** (`route_endpoints.json`): `dk65-monki-01` 1185 m (szew S → krawędź W), `dw671-tykocin-01` 2609 m
   (szew N → krawędź S). Kamery miejsc: 6 + 8 (`control_cameras_place.authored.json`) + kamery trasy.

## Budżet (edytor, Low, overcast, `stats.txt`; A = stan main, B = z liniami)
| kafel | max draws A→B | max tris A→B | WORLD_MEMORY Low A→B |
|---|---|---|---|
| knyszyn-w | 227 → 227 (kamery świata 202 → 203) | 287k → 287k | 53,9 → 54,0 MB (markings 0,3 MB) |
| knyszyn | 429 → 429 | 370k → 370k | 95,5 MB (markings 0,4 MB) |
| knyszyn-s | 100 → 100 (kamery świata 90 → 90, `construction-back`; `dk65-side-road` 40 → 43) | 195k → 195k | 40,8 MB |
| dk65-monki-01 (nowy) | 92 (kamery świata) | 97k | 46,6 MB (High 113,6 MB) |
| dw671-tykocin-01 (nowy) | 163 (`route-s0163`, wieś) | 129k | 45,7 MB (High 119,4 MB) |
Linie dokładają ≤ 3 draws i ≤ 1 tys. trójkątów na kamerę. Wszystko w hipotezie `docs/06` §6 (Low ≤ 300–400 draws,
≤ 400–600 tys. tris; `knyszyn` 429 draws na kamerze miejskiej jak przed zmianą). Czas: build_world knyszyn-w 2,4 min,
knyszyn 12,6, knyszyn-s 1,0, monki 1,6, tykocin 2,2; import 8,5–10 min/region; ingest monki/tykocin po 1,4 GB (orto10).
Pomiar na telefonie — lider.

## Walidacja
- `tests/gis/test_region_knyszyn_edges_0212.py`: ten sam `set` w 3 kaflach, linie 0,12 m na 3,55 m we wszystkich
  sekcjach DK65, `pick_latest` po roku, siatka (−9,9), szew dróg i punktów, przekrój, teren szwu identyczny.
- Rendery: `artifacts/knyszyn-edges-0212/vqa/<region>/e1-Low` (knyszyn, knyszyn-w, knyszyn-s), `r1-Low` (dk65-monki-01,
  dw671-tykocin-01); podgląd JPG `view/`. Plany z góry obok orto: `plan/dk65-monki-01/r1` (2 skrzyżowania, szew, krawędź W),
  `plan/knyszyn-w/e1` (Goniądzka, Legionowa, szew ronda), `plan/dw671-tykocin-01/r1` (wieś N/S, ferma, skrzyżowania S, szew).
- Spójność nawierzchni: monki 0, tykocin 7 × `lane_blind_end` (drogi gospodarcze fermy), 0 na trasie; ściany terenu 0.
- Ocena `visual-critic` nie wykonana (subagent nie tworzy subagentów) — do lidera.

## Otwarte
1. Zatoka autobusowa na DK65 w `knyszyn-s` (762500 609950): na orto linia krawędziowa przerywana (P-7c/d) — u nas ciągła.
2. Kafel (−10,9) dalej na Mońki — dziś koniec świata na zachodniej krawędzi `dk65-monki-01`.
3. `dk65-inlet-south` (knyszyn): szara plama przed kamerą — była już w r3 (ADR 0204), nie od linii.
4. **Przejazd kolejowy na DW671** (linia kolejowa przecina DW671 ok. (758830, 610030), plan `south_junctions.jpg`):
   generator nie ma torów (jak 0205 p. 1) — droga przejezdna, przejazdu brak. Wlot NE tam ma na orto wysepkę i pas
   prawoskrętu — u nas zwykły wlot T.
5. Tykocin: wlot SE skrzyżowania 4-wlotowego we wsi (plan `village_s.jpg`) na orto asfalt, u nas brązowa nawierzchnia; drogi fermy jako
   obrysy; kamera `village_above` kadruje pole zamiast fermy (pozycja do poprawy przy szlifie); stawy rybne na E kafla
   jako teren (etap wody 0210 opt-in — `water=True` do decyzji); DW671 we wsi z krawężnikami i latarniami z reguły.
6. Kafle (−10,9) Mońki i (−9,6) Tykocin — dalej koniec świata.
7. **Szew `knyszyn-s` / `dk65-11`** (x = 762635, agent 0214): kafel `dk65-11` musi nieść ten sam `set` DK65
   (`lanes 2, lane_width 3.4, edge_strip 0.35, edge_lines both`), inaczej urwanie linii przesunie się tam.
8. Rozstaw linii 7,1 m vs 6,8 m (p. 1) — `WORKING_VALUE`.

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/ingest.py --region dk65-monki-01 --with orto10      # tak samo dw671-tykocin-01
uv run --project tools/worldgen tools/worldgen/build_region.py --region dk65-monki-01
pwsh artifacts/knyszyn-edges-0212/chain_edges.ps1                 # build_world --context + route + import + vqa Low: knyszyn-w, knyszyn, knyszyn-s
pwsh artifacts/knyszyn-edges-0212/chain_monki.ps1                 # to samo dla dk65-monki-01 (chain_tyk.ps1: dw671-tykocin-01)
pwsh artifacts/knyszyn-edges-0212/plan_monki.ps1; pwsh artifacts/knyszyn-edges-0212/plan_tyk.ps1   # plany z góry obok orto
uv run --project tools/worldgen python -m pytest -q tests/gis/test_region_knyszyn_edges_0212.py
```
