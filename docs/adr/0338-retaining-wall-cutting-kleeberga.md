# ADR 0338 — mur oporowy wykopu DK8 pod rondem Szymańskiego (kafel `bialystok-kleeberga`): dylatacje, zacieki, cokół — samą teksturą, bez trójkątów

Status: PROPOSED (2026-11-24, agent `mistral-wall-s24`, gałąź `mistral-wall-s24`; numer zarezerwowany przez lidera)

## Kontekst
- Krytyk build #5 (`artifacts/critic-s24-build5/CRITIC.md` pkt 8, klatki `sheet_03` t0430–t0450 przejazdu
  `artifacts/full-build-5-s24/runs/20261122-181152/player.log`): „mur oporowy 150 m jednolitej jasnej płyty” obok
  Białegostoku — szare panele o powtarzalnym wzorze, bez zacieków, bez dylatacji, czystość absolutna.
- Lokalizacja z logu (t = sekundy, `shot_t0430` = 430 s): kafel **`bialystok-kleeberga`**, ul. Gen. Maczka,
  pos region-local (60,−101) → (−176,−226) — to ściany oporowe **wykopu DK8 pod rondem prof. Szymańskiego**
  (OSM `tunnel=yes layer=-1`, way 23982181 / 76073122, po 76,6/76,8 m; 2×2×77 m ≈ 150–308 m lica zależnie od
  strony) budowane przez `roads/tunnels.py` (ADR 0211) materiałem `ramp_wall_panels` — precastowe panele
  1.5×1.5 m z ADR 0159 ( dobrane pod rampy Bieżeństwa), kafel 3×3 m: powtarzalny wzór i nic więcej.
- Wymóg zadania: dylatacje co ~5–10 m, zacieki pod krawędzią i z odwodnień, ciemniejszy pas przy ziemi, drobne
  ubytki/plamy; **bez graffiti**; tanio — materiał/maska UV generowana w Pythonie + istniejące skany betonu CC0;
  **bez wzrostu trójkątów** (kaffel C na granicy 2 M — `test_budget_0221::test_region_c_frame_budget_has_margin`,
  `stretch_04` = 1 996 244 tris w tym checkoucie).

## Decyzja
1. **Nowy set tekstur `retaining_wall_cast`** (`art-source/world/materials/_src/sets_facade.py`, hybryda CC0
   `concrete_floor_worn_001` przez `sets_scan._retaining_wall`, ADR 0063): odlewany na miejscu beton żelbetowy —
   szalunek (słabe szwy płyt 2,4×2,0 m + otwory po ściągach 1,2×2,0 m, część z rdzą), **dylatacje co 6,0 m**
   (30 mm, cofnięte 10 mm, ciemny uszczelniacz — WORKING_VALUE w zakresie 5–10 m z zadania), **otwory
   odwodnienia** (fi 60 mm) na środku każdej działki 0,35 m nad podstawą z mokrym zaciekiem do dołu, **mokry
   brudny pas przy podstawie** (0–0,75 m), ubytki (wióry) i plamy, ton zalewowy per 6 m. Kafel **12 × 8 m**
   (2 dylatacje na kafel; 8 m w v pokrywa najwyższą ścianę wykopu — zmierzone 6,7 m w chunk_3_4 kleeberga —
   więc oś v się nie zawija). Rozdzielczość 2048×1364 (High) = 5,86 mm/px (było 2,93 mm przy panelach 3×3 m).
   Zacieki **spod górnej krawędzi NIE są w teksturze** (wysokość ściany zmienia się wzdłuż wykopu) — rysuje je
   shader: patrz pkt 3.
2. **Nowy materiał `retaining_wall`** (`tools/worldgen/streetscape/materials.py`):
   `texture_set: retaining_wall_cast`, `set_tile: true` (kaffel 12×8 m z UV0 w metrach), `splash_h: 0.55`
   (shader `_SPLASH`: pas ziemi/wilgoci przy podstawie na wszystkich tierach), `runoff: true` +
   `runoff_strength: 1.3` (shader `_RUNOFF` z warstwy `parapet_runoff`: zacieki spod krawędzi — patrz pkt 3).
   Kolor jak `ramp_wall_panels` (0,42 klasy — WORKING_VALUE).
3. **`roads/tunnels.py`: `WALL_MAT = "retaining_wall"`** i lico ściany dostaje **TEXCOORD_1 = (s m, 1 + m poniżej
   górnej krawędzi)** (`WALL_UV1`). Importer trzyma TEXCOORD_1 tam, gdzie materiał go czyta
   (`WorldPbrMaterials.Channels`: `runoff: true` → uv1), a `WorldPBR.shader` `_RUNOFF` próbkuje
   `T_parapet_runoff` w przestrzeni „pod gzymsem” — zacieki podążają za faktyczną górną krawędzią (w wykopie
   i pod płytą tunelu), na każdej wysokości ściany. **Zero nowych trójkątów**: dokładany jest tylko kanał
   wierzchołkowy UV1 na istniejących wertexach lica (weldowanie rozdziela wierzchołki tylko na skokach UV1,
   których tu nie ma — UV1 jest ciągłe wzdłuż ściany).
4. **Zakres**: tylko ściany z `tunnels.py` (wykopy/tunele). Ściany ramp na nasypach (`meshing.py`,
   `ramp_wall_blocks`) i panele Bieżeństwa (`ramp_wall_panels`, `test_barriers_0159` pinuje `wall_mat`) —
   bez zmian. Przebudowany tylko dotknięty kafel `bialystok-kleeberga` (+ import).
5. **Budżet tekstur**: nowy set = 12,9 MB PNG (High) / ~6,6 MB ASTC z mipami (High) vs 2,5 MB starego panelu;
   stary set zostaje (Bieżeństwa). Wzrost pamięci GPU High o ~4 MB na kafel z wykopem — przy limicie D24
   (świat ~100 MB / 110 MB w APK, ADR 0063) akceptowalne; do zmierzenia w raporcie.

## Konsekwencje / pomiary (dopisane po przebudowie)
- `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py` — zielone
  (ściana nie dodaje trójkątów; `stretch_04` C = 1 996 244 bez zmian).
- Poprawka po scaleniu fali 8 (`neon-testfix-s24`): `tests/gis/test_dojlidy_0242.py::test_runoff_strength_is_per_material`
  zaktualizowany o `retaining_wall` (`runoff_strength == 1.3`) obok materiałów z ADR 0242.
- Visual-QA przed/po: kamery `underpass_wb_szymanskiego`, `cut_wall_oblique_sw`, `tunnel_eb/wb_inside`
  (istnieją w `control_cameras.json` kleeberga), High, clear i overcast — dowody w
  `artifacts/mistral-wall-s24/` (przed: `artifacts/full-build-5-s24/sheets/sheet_03.jpg` t0430–t0450).
- Otwarte: graffiti celowo NIE (zadanie); dylatacje 6,0 m = WORKING_VALUE (rzeczywiste odcinki murów
  żelbetowych 5–10 m, brak referencji foto tego miejsca w repo).
