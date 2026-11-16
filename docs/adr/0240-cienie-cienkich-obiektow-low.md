# ADR 0240 — cienie cienkich obiektów na Low: bias 0,4 / 0,3 i wyłączenie cienkich casterów
Status: Proposed (agent rendering-perf, s21 runda 2, gałąź `shadows-0240`), 2026-11-15. Do scalenia przez lidera.
**Kod nieskompilowany w chmurze** (brak Unity); obraz i koszt na telefonie UNVERIFIED do przebiegu lidera.
Powiązane: B-088 (`docs/owner/BACKLOG-S21.md`), `docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md` P1-3, ADR 0010
(tiery), 0046 (High), 0098 (bias Medium/High 0,4 / 0,3), 0106 (rozkład GPU klatki A16 Low), 0123 (`_LowNoShadow`),
0155 (skala normal bias per materiał), 0239 (siatka płotu — F6, PR #109).

## Kontekst
Krytyk zrzutów z A16 (Low): cień wysięgnika sygnalizatora to „przerywana łukowata czarna smuga + 2 plamy głowic”
(`g3b_eye_s1682`), kreskowana smuga w poprzek pasa i schodkowy cień bariery (`g3a_eye_s0412`); w polu uwagi kierowcy
wygląda jak ubytki asfaltu. Low: 1 kaskada 1024 px na 35 m, twarde cienie, bias głębokości / normalnych 1,0 / 1,0
(wartość startowa ADR 0010; ADR 0098 zmienił tylko Medium/High i zostawił Low „bez zmian”).

## Diagnoza (pomiar z danych, bez Unity)
- Texel mapy cieni Low ≈ **7,8 cm** — ESTIMATED: sfera kaskady 0–35 m przy FOV pion. ~50° i proporcji ~2,2 ma promień
  ~40 m, 80 m / 1024 px (zakres 6–9 cm zależnie od FOV/proporcji). Medium: kaskada 0 (0–15 m) ~6,6 cm, kaskada 1
  ~26 cm; High: ~4,5 / 12 / 22 cm (kafle 1024 px) — wszystkie ESTIMATED tą samą metodą.
- URP `ApplyShadowBias` przesuwa wierzchołek castera wzdłuż −N o `normalBias × texel × (1 − N·L)`: na krawędzi sylwetki
  (N ⊥ L) i po stronie zacienionej to pełny texel. Przy 1,0 każda sylwetka traci ~7,8 cm z każdej strony = **~16 cm
  szerokości**. Wysięgnik 0,24 m zostaje z ~8 cm (1 texel) → przerywana linia. To jest główna przyczyna artefaktu.
- `tools/rendering/thin_shadow_audit.py` (153 prototypy LOD0 z `street_props.glb`, rzut cienia na ziemię, słońce 35°,
  raster 1 cm, mediana z 4 azymutów; wyniki: `docs/reports/shadows-0240/thin_shadow_audit_low_nb{1.0,0.3}.json`):

| Prototyp | śr. szer. cienia | pole po biasie 1,0 | po 0,3 | pole ≥ 2 texele („rozdzielane”) |
|---|---|---|---|---|
| `signal_mast` (wysięgnik) | 0,24 m | 33 % | 80 % | 98 % |
| `power_pole` | 0,29 m | 43 % | 83 % | 99 % |
| `plate_D-1` / `signal_head_red` | 0,30 / 0,60 m | 52 / 69 % | 85 / 91 % | 98 % |
| `lamp_10m` (rodzina `lamp_`: 0,16–0,23 m) | 0,17 m | 19 % | 71 % | 48 % (32–92 %) |
| `sign_gantry_10_72` (krata) | 0,14 m | 12 % | 65 % | 55 % |
| `signal_pole`, `sign_post`, `bollard*`, `railing_u12a`, `fence_u12` | 0,03–0,15 m | 0 % | 12–67 % | 0 % |

  Mediana po casterach, które zostają: 65 % pola cienia przy biasie 1,0 → 90 % przy 0,3.
- Przewody (`wires`) nie rzucają cienia na żadnym tierze (`WorldSceneBuilder.k_ShadowCasters` ich nie zawiera) —
  odpowiedź na pytanie krytyka o przewody WN. Belka bariery (`barrier_steel`) już ma `shadow_low: false` (ADR 0123).

## Decyzja
1. **Low: bias 1,0 / 1,0 → 0,4 / 0,3** (te same wartości co Medium/High po ADR 0098; bias jest w texelach, więc
   stosunek do rozmiaru texela jest ten sam co na sprawdzonym Medium). `QualityProfile.Defaults()`, migracja
   `revision 240` w `ProjectSetup.LoadTiers` (bias Low zmieniany tylko, gdy ma starą wartość 1,0), assety
   `QualityProfile.asset` i `URP_Low.asset` zsynchronizowane w YAML (to samo zapisze `setup-project`).
   Samozacienienie (acne) na Low **UNVERIFIED** — sprawdzić na visual-qa `clear` (ściany hal pod ślizgowym słońcem).
2. **Low: cienkie castery nie rzucają cienia** — `QualityProfile.Tier.thinCasterShadowsOff` (flaga odwrócona: stare
   profile zachowują się jak dotąd; Low `true`, Medium/High/Ultra `false`), reguła `ThinShadowCasterPolicy`:
   - kategoria (prefiks nazwy prototypu): `lamp_`, `signal_pole`, `sign_post`, `sign_g3_`, `sign_gantry_`,
     `sign_cantilever_`, `bollard`, `railing_`, `fence_`, `sliding_gate`, `barrier_arm`, `barrier_boom`, `chain_`,
     `wire_`, dokładnie `pylon`;
   - geometria (dla nazw spoza listy): środkowy wymiar bbox LOD0 < **0,20 m** WORKING_VALUE (pręt = dwa małe wymiary;
     ~2,5 texela Low). Płyty i bryły nie spełniają.
   Zostają casterami (≥ 90 % rozdzielane): `signal_mast`, głowice sygnalizatorów, tarcze `plate_`, tablice `board_`,
   `power_pole`, `lift_gate`, `cantilever_gate`, kosze, szafki, wiaty, pojazdy, drzewa (własna maska).
   `--check` audytu: reguła zgodna z pomiarem dla 153 prototypów (46 cienkich, 0 niezgodności; wyjątki rodzinne:
   `lamp_old_concrete_9m`, `sign_g3_G3518e7fb6`).
   Runtime: `WorldInstances` liczy flagę raz na prototyp przy ładowaniu (nazwa + `Mesh.bounds`, bez reimportu regionów,
   bez alokacji w klatce) i zeruje maskę cieni → `ShadowCastingMode.Off` (draw nie trafia do shadow passu).
   Materiały chunków (`furniture`, `plots`): `RegionImporter` ustawia `_LowNoShadow` także dla `fence_*` (słupki 4 cm)
   i `barrier_post` — działa po następnym imporcie regionu. **Siatka `fence_*_mesh` jest wyłączona z tej reguły**:
   jej caster wyłącza na wszystkich tierach ADR 0239 (`FenceMeshCoverage.CastsShadow`).
3. **Rozdzielczość / kaskady / dystans bez zmian** na wszystkich tierach (Low 35 m / 1024 / 1; Medium 60 / 1024 / 2;
   High 100 / 2048 / 3; Ultra 150 / 4096 / 4) — testy EditMode przypinają tabelę.
4. A/B: `rq_thinshadow 0|1`, istniejące `rq_shadowbias`, `rq_shadownormal`, `rq_shadowres`, `rq_shadowcasc`.
   `stats.txt` visual-qa dostaje `shadowCasterDraws` / `shadowCasterTriangles` instancji.

## Odrzucone (szacunki)
- **Low 2048 px**: texel 3,9 cm rozdzieliłby latarnie, ale mapa 16-bit 2 → 8 MB (+6 MB) i 4× więcej pikseli shadow
  passu na Mali-G57; całe cienie kosztują dziś 0,9 ms GPU p50 (ADR 0106), G3 ma GPU p95 31,7–32,2 ms przy budżecie
  33,3. ESTIMATED +0,3–0,8 ms — bez zapasu. Do sprawdzenia `rq_shadowres=2048`, jeśli lider chce cieni latarni na Low.
- **2 kaskady na Low**: +1 przebieg casterów (CPU cull + draw ×2), kafle 512 px → texel bliskiej kaskady podobny.
- **Screen-space contact shadows**: Low nie ma tekstury głębi (bez post, bez prepassu); kopia głębi + ray-march na
  0,75 skali to ESTIMATED ≥ 1–2 ms na G57 — ponad budżet cieni 1,0 ms. Kontakt pojazdów załatwia łata ADR 0050.
- **Skrócenie dystansu 35 → 30 m**: texel −14 %, nie zmienia klasyfikacji, zabiera cienie naczep.
- **Medium bez cienkich casterów**: brak dowodu z telefonu (bramka szła na Low); kaskada 1 Medium ma ~26 cm/texel,
  więc problem jest prawdopodobny — otwarte p. 2.

## Koszt (ESTIMATED, do pomiaru)
- Shadow pass Low: 46 z 153 prototypów mebli przestaje rzucać (LOD0 kończy się na 15–50 m przy lodBias 0,5; mapa sięga 35 m). Na kadr G3:
  ESTIMATED −10…−30 instancjonowanych drawów casterów (1 na submesh na prototyp w zasięgu) i −2…−10 k trójkątów
  (latarnia 92–302 tris, przęsło `fence_u12` 672, bramownica ~1 000). GPU ESTIMATED −0,0…−0,1 ms (całe cienie 0,9 ms),
  CPU bez zmiany poza mniejszą listą casterów. Dokładne liczby: `shadowCasterDraws` w `stats.txt` z `rq_thinshadow=1` vs domyślnie.
- Pamięć: 0 (mapa cieni bez zmian). Bias: 0 kosztu.

## Ryzyko / konflikty
- Jeśli Low 0,4 / 0,3 da acne i lider wróci do 1,0 (`rq_shadownormal=1` do porównania), wysięgnik znów będzie
  przerywany → dopisać `signal_mast` do prefiksów (jedna linia + test).
- F6 (#109, ADR 0239): `RegionImporter.cs` — inne hunki (F6 ~456, tu ~305), `InstanceImporter.cs` tu nietknięty;
  scalać **#109 przed tym PR**. F8 (przełączniki GPU): możliwy konflikt w `QualityProfile.CurrentRevision`, końcu
  łańcucha migracji `ProjectSetup.LoadTiers` (tu także `qp.revision = 191` zamiast `CurrentRevision` w kroku 191),
  `RenderOverrides` (`Any`, `Parse`, `ApplyTo` — po jednej dopisanej linii) i `QualityProfile.asset`.

## Otwarte
1. Weryfikacja lidera: visual-qa Low/High g3a/g3b (`clear`), EditMode, APK + device-metrics A16 (komendy w PR).
2. Medium: A/B `rq_thinshadow=0` na A16 Medium, gdy będzie zrzut referencyjny.
3. Schodkowy cień bariery na `g3a_eye_s0412` — słupki `barrier_post` znikną z shadow passu po reimporcie; krawędź
   cienia przyczółka zostaje schodkowa (twarde cienie 7,8 cm/texel) — poza zakresem.
