# REVIEW-ARGON: ADR 0194 — Plamy i brud na asfalcie sterowane ruchem (`stains-0194`)

Recenzent: Argon (niezależny recenzent, nie autor).
Materiał:
- ADR: `.claude/worktrees/stains-0194/docs/adr/0194-plamy-i-brud-asfaltu.md`
- Wymagania bazowe: `docs/reports/REVIEW-2026-11-13-s19-0179.md` (P2 asfalt)
- SBS runda 4 (`artifacts/stains-0194/sbs4/`): `after3_vs_after4_D-Low_route-s0457.jpg`, `after3_vs_after4_D-Low_route-s1370.jpg`, `after3_vs_after4_D-High_photo-P11-056.jpg`, `photo_vs_after4_D-High_photo-P11-129b.jpg`, `photo_vs_after4_D-High_photo-P11-001.jpg`, `photo_vs_after4_C-High_sbs-g3-a-2818555625124739.jpg`, `before_vs_after4_C-Low_chase.jpg`, `before_vs_after4_C-High_route-putry-approach.jpg`, `before_vs_after4_D-Low_route-s1066.jpg`
- Widoki i zbliżenia (`artifacts/stains-0194/view4/`): `D-Low_photo-P11-129b_zoom.jpg`, `D-High_route-s0457_zoom.jpg`, `D-High_route-s1370_zoom.jpg`, `C-High_g3-a-281855_zoom.jpg`, `D-Low_photo-P11-056_zoom.jpg`, `D-Low_route-s0761_zoom.jpg`, `C-High_chase.jpg`, `D-High_route-s1066.jpg`
- Kod i statystyki: `KamionRoadStains.hlsl`, `WorldPBR.shader`, `tools/worldgen/roads/decals.py`, `artifacts/stains-0194/{before,after4}/*/stats.txt`

**Brak zrzutu z telefonu** — dla zmiany shadera/worldgen akceptowalne do scalenia, wymagane przed bramką (szczególnie pomiar kosztu ALU na telefonie przy najbliższym APK).

## Werdykt: SCAL

Wszystkie wymagania P2 z `REVIEW-2026-11-13-s19-0179.md` dla nawierzchni asfaltowych i placów zostały spełnione, a wszystkie artefakty wykryte w poprzednich rundach (`after`–`after3`) zostały czysto usunięte. Nie stwierdzono żadnych blokerów P0 ani P1 w zakresie ADR 0194, a budżet `drawsEst`, `trisExact` i `WORLD_MEMORY` na Low i High nie wykazuje regresji.

### Co zweryfikowano jako PASS
1. **Plamy oleju (`KamionOilStain`, `_OilLook`)**: w `sbs4/photo_vs_after4_D-High_photo-P11-129b.jpg` (prawa połowa, `x ≈ 1180–1380`, `y ≈ 460–530`) oraz `view4/D-Low_photo-P11-129b_zoom.jpg` (`x ≈ 200–370`, `y ≈ 200–350`) plamy przed szlabanem są wyraźnie ciemniejsze od otaczającego asfaltu, matowe (brak odbicia jasnego overcastu pod kątem ślizgowym) i mają ostrzejszy kontur zamiast jasnych, rozmytych „splatów”. Spójne również na `sbs4/before_vs_after4_C-High_route-putry-approach.jpg`.
2. **Łaty asfaltu (`roads/decals.py`, `_PatchSeam` 25 mm)**: w `view4/D-High_route-s1370_zoom.jpg` (`x ≈ 150–280`, `y ≈ 250–380`) oraz `view4/C-High_chase.jpg` (`x ≈ 340–390`, `y ≈ 640–780`) łaty mają ostre krawędzie z ciemnym szwem bitumicznym i inny odcień asfaltu. Rozkład jest ważony klasą drogi (`PATCH_RATE_CLASS`: A/S `0.35` … D `1.3`), strefą wlotu skrzyżowania (`30 m`, `×1.8` vs `×0.75` na środku odcinka) oraz osią koleiny (`±0.24` szer. pasa). Na nowej drodze Dywizjonu 303 (`P11-056`, `route-s0457`) łat praktycznie brak — zgodnie z rzeczywistością.
3. **Eliminacja artefaktów z rund 1–3**:
   - **Żółto-brązowy pas na płycie skrzyżowania (`route-s1370`)**: w `sbs4/after3_vs_after4_D-Low_route-s1370.jpg` i `view4/D-High_route-s1370_zoom.jpg` całkowicie usunięty; koleiny i pas kapania płynnie wygasają na płycie (`KAMION_PLATE_WHEEL_KEEP = 0.3`, `KAMION_PLATE_DRIP_KEEP = 0.4`).
   - **1-metrowe pręgi/zebra na poboczach `road_asphalt` (`route-s0457`, `P11-056`)**: w `sbs4/after3_vs_after4_D-Low_route-s0457.jpg`, `view4/D-High_route-s0457_zoom.jpg`, `sbs4/after3_vs_after4_D-High_photo-P11-056.jpg` i `view4/D-Low_photo-P11-056_zoom.jpg` opaski/pobocza (`UV1 = (-1, 5)` w `_emit_strip`) są jednorodne, bez poprzecznych prążków.
   - **Skośne zygzaki kolein na rozszerzeniach płyt (`route-s1370`, `g3-a-2818555625124739`)**: w `sbs4/after3_vs_after4_D-Low_route-s1370.jpg`, `sbs4/photo_vs_after4_C-High_sbs-g3-a-2818555625124739.jpg` i `view4/C-High_g3-a-281855_zoom.jpg` rozszerzenia zjazdów i płyty są czyste i gładkie.
   - **Gęste pasy na płycie skrzyżowania Kuronia/Mickiewicza (`route-s1066`)**: w `sbs4/before_vs_after4_D-Low_route-s1066.jpg` (`x ≈ 0–480` przed vs `x ≈ 960–1440` po) i `view4/D-High_route-s1066.jpg` intensywne równoległe smugi zostały wygaszone do naturalnego, delikatnego zużycia płyty.
4. **Brud na placach/zatokach (`KamionYardGrimeBias`, `_GrimeTraffic`)**: w `sbs4/before_vs_after4_C-Low_chase.jpg` i `view4/C-High_chase.jpg` otwarty środek placu manewrowego jest czystszy i suchszy (`+0.07` progu), a strefy przy dokach/ścianach (`< 18 m`) i krawędziach (`< 2.5 m`) zachowują więcej wilgoci i brudu (`-0.04` progu). Zero dodatkowych próbek tekstur.
5. **Budżet A/B (`before` vs `after4`)**:
   - `WORLD_MEMORY`: Dojlidy Low `103.8 MB → 98.3 MB`; C Low `123.2 MB`, C High `266.1 MB` (brak regresji; 0 nowych tekstur i 0 nowych wariantów shadera).
   - `drawsEst` / `trisExact`: na C-Low i C-High przyrost od `0` do `+2` draws i od `+21` do `+1882` tris (ok. +0.1% trójkątów z tytułu większej liczby łat `317 → 443`). Na D-Low od `-4` do `+4` draws (na `s0152`/`s0457` spadek `-34.8k`/`-36.0k` tris po merge `origin/main`). Brak regresji.

## Oceny (1–10)

| Kategoria | Ocena | Uzasadnienie |
|---|---|---|
| Realizm plam oleju | 8 | Ciemne, matowe, ostre brzegi zamiast jasnych splatów (`P11-129b`). |
| Realizm łat asfaltu | 8 | Wyraźny szew 25 mm, sensowny rozkład po klasach dróg, wlotach i koleinach (`s1370`, `chase`). |
| Spójność płyt skrzyżowań | 8 | Brak zygzaków, żółto-brązowych pasów i agresywnych smug na `route-s1066` i `route-s1370`. |
| Brud placów (`_GrimeTraffic`) | 7 | Wyraźna różnica między czystym środkiem placu a strefami przy ścianach i krawędziach (`chase`). |
| Budżet i czystość techniczna | 9 | 0 nowych fetchy/keywordów, śladowy narzut geometrii (+0.1% tris), izolacja zmian w `KamionRoadStains.hlsl`. |

## Problemy i uwagi

### W zakresie ADR 0194
Brak P0 i P1.
- **P2 (otwarte w ADR) — koleiny na nowych drogach (`photo-P11-056`, `route-s0457_zoom.jpg`, `route-s0761_zoom.jpg`)**: mimo braku łat na młodej nawierzchni Dywizjonu 303, przyciemnienie kolein (`wheel_darkening = 0.45`) jest tak samo wyraźne jak na starszych drogach, ponieważ parametr jest wspólny dla `road_asphalt`. Kandydat do osobnego wariantu materiału wg wieku nawierzchni (decyzja lidera w kolejnym kroku).
- **P2 (do weryfikacji przed bramką) — brak pomiaru ALU na telefonie**: `KamionRoadStains.hlsl` dodaje ok. 4–10 ALU na materiałach z danymi (`decal_oil`, płyty, `yard_*`); zmierzyć przy najbliższym buildzie APK.

### Poza zakresem ADR 0194 (odnotowane, nie blokują scalenia)
- **`photo-P11-129b.jpg`**: brak ceglanego muru bramy szpitala, znaków `STOP`/`20`/`C-2` i biały/szary placeholder bryły w tle (`x ≈ 1625–1700`, `y ≈ 220–320`) — dług z `REVIEW-2026-11-13-s19-0179.md`.
- **`photo-P11-001.jpg`**: brak DDR z czerwonego asfaltu na pierwszym planie, płaskie okna bloku i dominujący zielony płot — zakres innych zadań (`0179`, `0185`, `0196`).
- **`C-High_g3-a-281855_zoom.jpg` (`x ≈ 20–90`, `y ≈ 420–450`)**: drobna zielona plama/łatka trawy przebijająca na skarpie żwirowej przy krawężniku — drobny artefakt geometrii terenu poza zakresem `0194`.

## Warunki po scaleniu (dla lidera)
1. Po scaleniu gałęzi `stains-0194` zregenerować `generated/*` dla regionów `bialystok-dojlidy` i `bialystok-industrial-c` (gałąź jest gotowa, brak konfliktów z `0191` — wspólny plik `WorldPBR.shader` w osobnych liniach, sprawdzić tylko kolejność `#include`).
2. Przy najbliższym APK wykonać zrzut i pomiar wydajności na telefonie dla kadrów `P11-129b`, `route-s1370` i `chase`.
