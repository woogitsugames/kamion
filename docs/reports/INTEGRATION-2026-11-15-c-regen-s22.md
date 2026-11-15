# Integracja 2026-11-15 — jedna regeneracja C i Dojlid (c-regen-s22)

Gałąź `c-regen-s22` (z main `a7a704287`, po scaleniu budget-fix 0221). Weszły: **#95 qa-tools-0219** (ADR 0219) i
**#120 summer-cd-0216b** (ADR 0216 §0216b, D68). Nie weszły: #122–#125, nic z torem / DK65. Bez telefonu.

## Scalenia
- `origin/qa-tools-0219` → `1c8c4576c`, `origin/summer-cd-0216b` → `9e0adb2cd`: bez konfliktów (także `STATUS.md`,
  `docs/LICENSES.md`). `Data/Admin/powiaty_prg.geojson` po ponownym wyjęciu: sha256 = manifest.
- `origin/main` (125 commitów: fix-pr80, tunel 0211, rail-fix 0217, win-build 0261, dk65-r4 0233) → `ebcbbc45b`,
  bez konfliktów; main nie zmieniał `generated/` C ani Dojlid.

## Regeneracja (slot heavy, 20:48–21:15, wszystkie kroki exit=0)
`build_region` → `build_world` (zawiera far_field) → `fidelity/run.py` → `export-route.py` → `lamp_family_audit.py`,
dla C, potem Dojlid. Skrypt: `artifacts/c-regen-s22/tools/regen.ps1`, logi `artifacts/c-regen-s22/regen/`.

| | C | Dojlidy |
|---|---|---|
| kamery `frame_estimate` | 23, identyczne z main | 17, wszystkie mniejsze niż w main |
| max High | 1 986 314 (`stretch_04`) | 1 768 028 (`photo_P11-063`; było 1 790 621) |
| Low vs main | 0 % (`stretch_04` 938 349) | −0,8 … −4,8 % |
| far_field Low (limit testu 30 000) | 24 548 → 25 389 | 20 680 → 23 907 |
| far_field High | 118 588 → 122 016 | 99 315 → 119 759 |
| `ring_powiaty` / `ring_powiaty_missing` | [2061, 2002] / [] | [2061, 2002] / [] |
| fidelity | exit 0, 30 węzłów, 0 cięć pominiętych | exit 0, 18 węzłów, 2 cięcia `tile_boundary` |

- Budżet: wszystkie kamery High < 2 M; Low bez wzrostu. far_field nie wchodzi do `frame_estimate`; nawet doliczony w
  całości do najcięższej kamery C daje 1 986 314 + 3 428 = 1 989 742 (ESTIMATED, górna granica).
- Spadek w Dojlidach jest tylko w kategorii `roads` (np. `route_s0152` 430 700 → 397 403): generated Dojlid w main
  pochodziły sprzed 0221 (P-23 32-kąt, decymacja obrzeży).
- far_field C: przyrost w sektorze N (Low 3 949 → 4 726) i W (3 248 → 3 312) — BDOT/LoD1 powiatu 2002 zamiast samego OSM
  (FIX 2 z recenzji #95 wykonany). Dojlidy: S 1 425 → 3 973, E 2 884 → 3 326.
- Lampy: C `by_family` bez zmian, 0 `*_led_*`. Dojlidy `policy = led-target`, `led_target_ways = 64`,
  `led_target_stale = 0`; 56 głowic LED na starych słupach (`lamp_old_concrete_led_9m` 21, `lamp_old_steel_led_8m` 35),
  sód zostaje na 123 (50 + 73) — zgodnie z oczekiwaniami ADR 0216b.
- `fidelity_qa.json` C: różnica tylko w `inputs_sha256` (overrides.yaml dostał wpis-rekord 0216b). Dojlidy: nowy plik
  (wcześniej `run.py` padał na id `Bw…`).
- Poza `generated/`: `art-source/world/props/props_meta.json` + `street_props.glb` (prototypy `lamp_old_*_led_*`;
  dodane za zgodą lidera) i manifesty far_field obu regionów.

## Import i rendery (slot unity)
- `import-region` C exit 0 (21:21), Dojlidy exit 0 (21:31); log obu: `[IMPORT] lighting profiles for <id>:
  summer-bialystok-cd,led-white-4000k-bialystok`.
- visual-qa Low/High × clear/dusk, C + Dojlidy: before (kod main, przed merge) i after, 16 przebiegów exit 0.
  `artifacts/c-regen-s22/{before,after}/<region>/<Tier>-<lighting>/`, pary `artifacts/c-regen-s22/view/ab_*.jpg`.
- Zmierzone tris edytora (`stats.txt`, `trisExact`), High clear: C `stretch-04` 1 092 789 → 1 067 263,
  `route-onramp-andersa-above` 835 918 → 822 940; Dojlidy `photo-P11-063` 758 129 → 741 454, `route-s0761`
  809 353 → 787 526. Low clear: C `stretch-04` 318 876 → 312 831. Draws bez zmian (`stretch-04` High 1085, Low 463).
  Uwaga: scena „before” C pochodziła z importu 16:59 (sprzed 0221), więc spadek C to 0221, nie ta integracja.
- Oględziny (27 par): dzień bez widocznych różnic (RMSE ≤ 0,006). Zmierzch: wyraźnie mniej oświetlonych okien biur
  (zegar 21:00 zamiast 16:10) w obu regionach; latarnie regułowe białe LED przed i po; stare słupy bocznych ulic C
  nadal sodowe (zamierzone, typ UNVERIFIED). Brak regresji (dziur, migotania decali, brakujących obiektów).
- **Niepotwierdzone wzrokiem:** horyzont far_field (kamery `edge-*` zasłania las; zmiana tylko w liczbach) i głowice
  LED na starych słupach Dojlid (żadna kamera kontrolna nie patrzy na ulicę z przetargu ze starym słupem). Lato w
  dzień nie zmienia obrazu — drzewa były zielone już przed zmianą.

## Testy
- pytest `tests/gis` (pełny, po regeneracji, przed merge main): 1496 pass / 1 fail / 5 xfail. Fail:
  `test_qa_tools_0219::test_tile_powiaty_match_the_registry_except_known_gaps[dk65-09]` — region dodany do main po
  napisaniu #95: rejestr `2002`, PRG 17,89 % kafla w 2008. Dopisany do `KNOWN_REGISTRY_GAPS` (jak `knyszyn-s`);
  poprawka rejestru wymaga regeneracji dk65-09 (strefa DK65). Trzy „znane” faile main nie wystąpiły.
- EditMode po merge PR (2 przebiegi): 629 = 626 pass / 2 fail / 1 skip; oba faile
  `CarPaintMaterialTests.DepositionChannel_RequiresScopedYardOptInOrExistingCar` (opisane jako znane z main w
  `artifacts/live/verify-cloud-b.md`; na czystym main w tej sesji niesprawdzane).
__POSTMERGE__

## Otwarte
1. Telefon niemierzony (A16) — wg zadania bez adb.
2. Kamera kontrolna na horyzont N kafla C i na ulicę przetargową Dojlid ze starym słupem (zmierzch) — brak; dodać,
   żeby FIX 2 #95 i głowice LED 0216b były widoczne w pętli wizualnej.
3. Rejestr `regions.py` dla `dk65-09` (brak 2008) i `knyszyn-s` (brak 2002).
4. `build_region` na Windows przepisuje `manifest_sha256` w `region.yaml` Dojlid (CRLF checkoutu manifestów NMT/orto;
   blob w gicie ma poprawny hash) — cofnięte; do naprawy `.gitattributes -text` jak dla geojsona PRG.
5. Nieśledzony `art-source/world/textures/chain_bollard.png` powstaje przy build_world (z 0183) — nie dodany.
6. 2 faile EditMode CarPaint (BuildBatch truck/trailer wg HANDOVER).
