# Recenzja niezależna — pakiet D rund GPT (sbs r3, landmarks r3, asphalt r2, light r4) — s12

Data: 2026-11-12 · Recenzent: visual-critic (Opus), niezależny od autorów i ich self-review. Tylko odczyt (jedyny zapisany plik: ten).
Pytanie: czy każdą gałąź można **scalić do main** (`333c7ca3`, po pakietach A–C i regeneracji d). Kryteria jak w `REVIEW-2026-11-12-s12-gpt-batch-{a,b,c}.md`: (a) brak regresji rozpoznawalności trasy wg D51 i obrazu, (b) Low draws nie rośnie, tris ≤ +2 %, (c) docs/06 — poprawa albo brak pogorszenia, (d) licencje/marki. Wszystko to render edytora; koszt GPU A16 i kompilacja shaderów na Androidzie **UNVERIFIED** dla wszystkich czterech.

Metoda własna: `git merge-tree --write-tree main <gałąź>` (bez refów), `git log --no-merges --name-only main..<gałąź>` (własne pliki rundy, bez szumu merge-base), przegląd diffów konfliktów. Dla sbs własne zestawienia **zdjęcie | render r3-baseline (epoka 14ccbaf1) | render main-d (`artifacts/integration-s12/sbs-d/renders/Low-overcast/`) | najlepszy wariant C r3** dla każdej pozy G3-B (źródła: `artifacts/sbs-r3/evidence/sheets/Low-overcast/sbs-g3-b-*.png`, `artifacts/sbs-r3/pose-refinement1/pairs/sbs-refine1-*.png`). Landmarks: `review/pier-final-native-pair.jpg`, `review/photo-{before,after-corrected}/Low-overcast-{heads,ec-ref073128}.jpg`. Asphalt: `material-review-candidate2-960/*`, `candidate2-reference-960/*`. Light: `native-review/dim-colour-*`, `reference-pairs/night-*`, `native-review/day-extreme-*`. Kontrola nieba i asfaltu na main-d: `vqa-d/Low-clear/g3a-rondo-bie-approach.png` (+ wycinek jezdni).

## Podsumowanie

| Runda | Werdykt | Jakość | (a) trasa D51 | (b) Low draws / tris | (c) anti-slop | (d) licencje |
|---|---|---|---|---|---|---|
| **sbs r3** (rejestr D51 r3, ranking priorytetów, diagnostyka póz C) | **SCAL** (czysto; tylko narzędzie/rejestr/ADR) | narzędzie PASS; **pozy produkcyjne NIEZMIENIONE** | **G3-B bez zmian: 2/10** (7 częściowych, 1 nie). Dwa warianty C w mojej ocenie gotowe do awansu | 0 / 0 (brak zmian runtime) | n/d | OK (zdjęcia tylko referencje z atrybucją) |
| landmarks r3 (kominy EC, korekta filarów) | **SCAL warunkowo** (unia `LICENSES.md`; `materials.py`, generaty, `street_props.glb` → `--ours` + regeneracja) | PARTIAL+; filary naprawione, kominy wyraźnie bliżej zdjęcia | poprawa tła G3-A (kominy); bez regresji | +0 / −0,32…+0,37 % (122 pomiary Low) | usunięty szary pas i „pływający równoległobok” na filarach; białe pasy kominów nadal szare | OK (Rakoon CC BY 3.0, Hiuppo CC BY-SA 2.5 tylko referencja; bez logo); brakujące spacje w tekście (P2) |
| asphalt r2 (krawężnik, kostka) | **SCAL warunkowo** (ręczna unia `materials.py`; generaty `--ours`; `git rm` 3 × 8,5 MB `geometry-*.json` i 3,2 MB oryginału PCRT) | PARTIAL, mały, realny plus | bez zmian | 0 / 0 (2952 liczniki) | usunięte duże „mokre chmury” na kostce; kostka nadal sterylna i regularna | OK (referencje CC BY/BY-SA 3.0 tylko w artefaktach) |
| light r4 (desaturacja ciemnych tonów Night) | **SCAL warunkowo** (ręczna unia `LP_Night.asset`) | PARTIAL; mały, poprawny krok Night | bez zmian w dzień | +0 / ≤ +2 % (654 kamery) | Night mniej „zielono-żółty”; nadal day-for-night bez hierarchii plam światła | OK (Rakoon CC0 tylko referencja) |

**P1 z batch B (`sbs-gate3.ps1`) — NIE naprawione.** r3 nie zmienia `scripts/sbs-gate3.ps1` względem main (`git diff main gpt-sbs-r3 -- scripts/sbs-gate3.ps1` pusty). Nadal: (a) `-ComposeOnly` bierze heavy na cały batch — nie wołać z procesu, który już trzyma heavy; (b) `Save-EvidenceInputs` rzuca wyjątek przy rozjechanym SHA `world_manifest.json`/`materials_spec.json`/`sbs_*.json` względem capture — compose na main po cudzej regeneracji się wysypie. Lider: compose SBS tylko na czystym drzewie generated z tej samej epoki co render.

**Smog nad horyzontem (P1 z batch C dla light r4) — NIE ruszony.** Light r4 zajął się wyłącznie Night. Na main-d `g3a-rondo-bie-approach` Low-clear dół nieba jest bladobiały/szarawy, bez twardego pasa — w tym kadrze akceptowalnie; uwaga z batch C dla yaw 0–135/270–315 i 180–225 pozostaje otwarta (tych kątów na main-d nie weryfikowałem).

## 1. sbs r3 — NAJWAŻNIEJSZE: pozy G3-B

### Co faktycznie zmienia gałąź
Własne pliki rundy (poza `artifacts/`): `Data/Regions/bialystok-industrial-c/sbs_recognition.json` (rejestr: bieżący przegląd r3 + `history` r1, związane z SHA zdjęcia i renderu), `docs/adr/0111-sbs-evidence-confidence.md` (+18), `docs/refs/sbs-priorities.md` (nowy ranking), `tools/refs/sbs_report.py`, `sbs_report_template.html`, `tests/gis/test_sbs_report.py`. **`sbs_cameras.json` i `sbs_authored_overrides.json` bez zmian** — żadna produkcyjna poza nie została przesunięta. Autor mówi to wprost („zero akceptacji do produkcji”). Render przed = render po dla wszystkich póz G3-B; „po” w tabeli to najlepsze warianty C z diagnostyki (kod dd92f5c7, ten sam świat co baseline).

### Pozy: zdjęcie | produkcja (r3-baseline = main-d) | najlepszy wariant C
„3281350” i „328135” z zadania to ta sama poza `B3281350541967811` (r3 skraca do B328135). Unikalnych póz jest 6.

| Poza | Zdjęcie (kotwice) | Produkcja | Wariant C r3 | Mój werdykt D51 |
|---|---|---|---|---|
| **275528** (grobin 2019) | bramownica kratowa w środku, 2 trójkąty ostrzegawcze po obu stronach jezdni, latarnia lewa-środek, horyzont ~45 % | kamera **pod** bramownicą: portal gigantyczny, ucięty u góry, trójkątów brak → PARTIAL | **-04** (−10 m po osi spojrzenia, oko 1,7 m): portal w tym samym miejscu i skali (zdjęcie x≈135–360/470, render ≈150–365/470), **oba trójkąty w zgodnej pozycji i wysokości** (L x≈100 vs 105, P x≈428 vs 385), horyzont zgodny | **-04 = RECOGNISABLE.** Dwie niezależne kotwice (portal + para znaków) są — nie zgadzam się z recenzentem GPT. Różnice (drugi pas, latarnie) nie przekreślają rozpoznania. **Awansować.** |
| **837235** (grobin 2019) | duży szewron czerwono-biały przy prawym nosie, odległy portal w środku, biały blok z lewej, latarnia lewa-środek | brak szewronu w bliskim planie, portal mały w osi → PARTIAL | **-12** (−16 m, −2 m w lewo, oko 2,2 m): szewron + tablica przy prawym nosie, portal w środku (x≈230/470 jak na zdjęciu), biały blok z lewej, latarnia w zgodnym miejscu | **-12 = RECOGNISABLE** (szewron ma ~½ wysokości ze zdjęcia — sprawdzić skalę/odległość obiektu, nie pozę). **Awansować.** |
| **297817** (zsolt 2017) | brak portalu w kadrze, jezdnia z pasami i strzałkami po prawej, pierzeja usługowa po prawej, kominy EC w tle | portal blisko po lewej nad drugą jezdnią — na zdjęciu go nie ma → PARTIAL | **-26** (−75 m po osi jezdni): portal daleko w środku, niebieska hala z lewej; geometria pasów (pas dzielący z lewej, szeroka jezdnia) nie odpowiada zdjęciu | PARTIAL (bez zmiany). Bloker: świat (pierzeja — 0126 w toku) + oś kamery. |
| **3281350 / 328135** (zsolt 2017) | **tył portalu kratowego blisko po lewej**, biały van, jezdnia w prawo | brak portalu w kadrze, „ogólna” droga → NOT_RECOGNISABLE | **-21** (−75 m po osi jezdni): portal jest, ale w **środku** nad jezdnią, frontem; na zdjęciu po lewej, tyłem, blisko | PARTIAL z -21 (lepiej niż NOT, ale relacja portal↔kamera błędna). Nie awansować bez próby yaw/bok. Pełna szara rama na Low zamiast kratownicy (LOD — 0127) dodatkowo psuje kotwicę. |
| **1801374** (gpsmapper 2019) | wysoki ekran akustyczny blisko po prawej, billboard z lewej, latarnia prawa | ekran daleko i niski, domy jednorodzinne zamiast pustego pobocza → PARTIAL | brak prób w r3 | PARTIAL (bez zmiany). |
| **494288** (szurek 2017) | ekran szklany z ciemnymi słupami dominuje po prawej, prosta jezdnia, **latarnie po lewej** (pas dzielący) | ekran niższy i jaśniejszy, jezdnia wyraźnie w łuku w lewo, **latarnie po prawej** | brak prób (r3: ray trafił tylko kolizję) | PARTIAL. Latarnie po złej stronie = kamera na złej jezdni albo zły kurs — najmocniejszy dowód błędu pozy. Pierwsza rzecz w r4. |

### Nowa ocena G3-B
- **Na main teraz: 2/10 RECOGNISABLE, 7 PARTIAL, 1 NOT** — identycznie jak r3-baseline (rendery main-d tych póz są wizualnie tożsame z baseline 14ccbaf1). Bramka 3 G3-B: **FAIL**.
- **Po awansie 275528-04 i 837235-12: 4/10 RECOGNISABLE, 5 PARTIAL, 1 NOT**; z dodatkowym awansem 328135-21: 4/6/0. Nadal FAIL (bez pierzei 0126 i czytelności Low 0127 próg nieosiągalny), ale to największy skok od 0125.
- Awans to zmiana danych (`sbs_authored_overrides.json`), nie kodu — zlecić GPT sbs r4 jako pierwszy krok albo zrobić po ponownym renderze tych dwóch póz na main-d (świat wokół portalu G3-B nie zmienił się od dd92f5c7).

### Uwagi do sbs r4
1. **Awansować 275528-04 i 837235-12** (jawny `authored_overrides`), przerenderować 4 stany, D51. Kryterium „dwie niezależne kotwice” jest spełnione — recenzja GPT była zbyt ostrożna.
2. 494288: najpierw strona jezdni/kurs (latarnie po lewej na zdjęciu), potem yaw/pitch. 3281350: kamera na **prawej** jezdni, portal po lewej i tyłem — nie po osi do przodu.
3. Naprawić P1 `sbs-gate3.ps1`: `-ComposeOnly` z flagą typu `-HeavyHeld`/sprawdzeniem właściciela slotu (bez ponownego Acquire); guard SHA ma wypisać listę rozjechanych plików i podpowiedź „renderuj ponownie”, nie sam `throw`.
4. Ograniczyć wnoszone do gita artefakty (`contract-fixture-*`, `prestage-source-bindings` z 3000-liniowymi kopiami JSON) — 2,4 MB teraz OK, trend rośnie.

### Liczby i testy
EditMode 317/317, GIS 665 passed / 1 xfailed, `test_sbs_report` 34/34; Low max 810 draws (445 + 365 inst.), High 1376 — estymaty edytora na epoce 14ccbaf1, nie pomiar A16. Brak zmian runtime → (b) neutralne.

## 2. landmarks r3 — kominy EC, filary DK8

1. **Filary — P1/P2 z batch A naprawione.** `pier-final-native-pair.jpg` (4 stany): przed — szeroki szary pionowy pas przez środek ściany i ciemny „równoległobok”; po — jednolita farba na wszystkich fazach, kontrast tylko z normalnych i światła. Dokładnie to, czego chcieliśmy. Pigment `color_linear [0,46; 0,40; 0,17]` ≈ sRGB 179/169/115, stosunek 1 : 0,94 : 0,64 vs zdjęcie (ROI 84/79/47) 1 : 0,94 : 0,56 — R/G trafione, niebieski minimalnie za wysoki → w overcast lekko oliwkowo/khaki zamiast musztardy (P2: B ~0,14).
2. **Kominy — wyraźna poprawa sylwetki i rytmu.** `photo-before|after-corrected/Low-overcast-heads.jpg`: przed — single z gołym szarym dolnym 40 %, multi z drobnym rytmem pasów; po — rytm pasów czerwono-białych bliski zdjęciu, multi ma głowicę z wylotami, single galerię. W `ec-ref073128` z odległości zmiana mała (obiekty mają kilka pikseli). PARTIAL autora potwierdzam.
3. **Pozostaje (P1 następnej rundy):** białe pasy renderują się jako **średnia szarość** — na zdjęciu przy tym samym zachmurzeniu są wyraźnie białe/kremowe. To albedo, nie światło: biel ~0,6–0,7 lin. Głowica multi: 2 krótkie kikuty zamiast trzech wylotów z balustradą; galeria single — włosowata linia, a na zdjęciu masywny pierścień + pomost w połowie wysokości (brak). Kominy bez zacieków pod galeriami — docs/06 „sterylność”.
4. Budżet: tris LOD0 700 → 676/636, materiały 4/3 → 3/3, Low draws +0. Testy: EditMode 317/317, GIS 643 / 1 xfail / **1 FAIL** (stale fidelity `overrides.yaml`/`roads/meshing.py` — zniknie po regeneracji na main), physics/gate3 48/48.
5. Licencje: wpis w `LICENSES.md` kompletny (Rakoon CC BY 3.0 z adnotacją o pomniejszonej kopii, Hiuppo CC BY-SA 2.5 tylko referencja, szachownica i logo nie przeniesione). P2: brak spacji („kopią3840×2160”, „ENEA2025”, „H120m”, „z2007r.”) — poprawić przy unii. Brak BOM.

## 3. asphalt r2 — krawężnik i kostka

1. **Kostka (`Low-overcast-asphalt_paving_andersa_close-pair.jpg`):** przed — duże, miękkie, ciemne „chmury wilgoci” przez cały chodnik (kamuflaż, flaga docs/06); po — znikły, spoiny i kruszywo zostały. Realny plus. Ten sam artefakt jest jeszcze na podjeździe `light-r4/native-review/dim-colour-High-r10_house_2.jpg` — inny materiał (behaton posesji), poza zakresem r2 → asphalt r3.
2. **Krawężnik (`High-overcast-asphalt_kerb_andersa_close-crop-pair.jpg`):** różnica ledwo widoczna (nalot 0,16) — czytelniejsze spoiny; gładka przednia listwa nadal jak z plastiku. Bez regresji.
3. **Nadal (docs/06):** kostka idealnie regularna, bez wymienionych kostek, bez zapadnięć przy krawężniku, bez piasku w spoinach przy trawie; obrzeże jednakowo czyste na całej długości. Wygląda jak plac pokazowy producenta kostki, nie chodnik przy Andersa.
4. **Na main (nie z r2, ale domena asfaltu — P1 dla asphalt r3):** `vqa-d/Low-clear/g3a-rondo-bie-approach.png`, jezdnia przed rondem: **białe, kredowe zawijasy „wypełnienia rys”** z kółkami i plamkami — czytają się jak rysunek kredą albo rozlana farba. W Polsce zalewa rys to czarny, błyszczący bitum (ew. przysypany szarym piaskiem). Przyciemnić i nadać połysk albo usunąć.
5. Liczby: 2952 liczniki Δ = 0, 7315 prymitywów GLB identyczne, ASTC 40,9 MB bez zmian, +48 B stałych WorldPBR (ALU A16 UNVERIFIED). Testy: EditMode 312/312, GIS 604/1 xfail, physics/gate3 47/**1 FAIL** `top_speed_flat_comb.json` — gałąź ma starą bazę `4992c434` bez poprawki generatora z main (`b1c83d58`); po scaleniu powinno przejść (potwierdzić w pytest po regeneracji).
6. Wykluczenie Kwadrat (prostokąt E 400–850 / N −700…−250 w lokalnych metrach mesha) — słuszna ochrona cudzej domeny; granica nie jest widoczna w żadnym kadrze trasy (wg autora i krytyka GPT; własnej kamery na obwód nie mam).
7. **Rozmiar:** gałąź wnosi 55,6 MB artefaktów, w tym `geometry-{baseline,candidate,candidate2}.json` 3 × 8,5 MB i `backlog-r3-references/pcrt-20200711-065732-original.jpg` 3,2 MB → `git rm` po merge (zostawić podglądy 960 px i `SOURCES.json`).

## 4. light r4 — Night

1. `dimColourDesaturation 0,65` w KamionTone, tylko Night, zanik między lin. 0,02 i 0,25. Ablacja 0 / 0,35 / 0,65 / 1 (`native-review/dim-colour-*`): przy 0 trawa w nocy zielono-żółta (fałsz), przy 1 obraz popielaty; 0,65 rozsądne. Zgadzam się.
2. **Night nadal FAIL wizualnie** (`reference-pairs/night-1-Low.jpg`, `route-putry-approach`): cała jezdnia i pobocza równomiernie oświetlone jak przyciemniony dzień („day-for-night”), brak plam światła pod latarniami i ciemnych przerw, czarne okna, zero łuny. Na zdjęciu hierarchia odwrotna: jasne źródła, ciepłe plamy, czerń pomiędzy. To główny problem nocy, nie nasycenie.
3. Artefakt w każdym kadrze Putry (stan main, nie r4): **czarna elipsa na jezdni** (studzienka?) czyta się jak dziura — nocą jeszcze bardziej. P2 dla asfaltu/props.
4. Dzień: 436 porównań, max średnia ΔRGB 0,036, ale max kanał 194 — `day-extreme-diff8.jpg` (494288 High-clear) pokazuje zmianę tylko w koronach drzew (wiatr/LOD), nie w tonach. Nie przypisuję tego r4, ale capture nie jest w pełni deterministyczny — zamrozić czas wiatru w QA.
5. Testy: EditMode 332/332, GIS 640/1 xfail; budżet 654/654 kamer, draws +0. Dodatkowy ALU w KamionTone na Low — pomiar A16 przy APK.

## Konflikty `git merge-tree --write-tree main <gałąź>` i unia

- **sbs r3:** czysto. Wnosi tylko rejestr/narzędzie/ADR/ranking + 2,4 MB artefaktów. `sbs_recognition.json` zachowuje `history` (r1) — sprawdzone.
- **light r4:** 1 konflikt — `game/Assets/_Project/Rendering/Settings/Lighting/LP_Night.asset`. **Wziąć wersję main** (main przeserializował plik: `skyDisplayGain/skyDisplayDesaturation/projectedHeadlamps*` wyżej, doszły `clearCloudCover`, `highSunShadowFilter`, `clearSkySaturation`; bez pustych linii na końcu) i **dopisać jedną linię** `  dimColourDesaturation: 0.65` w ciągłym bloku pól — najlepiej między `clearSkySaturation: 1` a `projectedHeadlamps: 0` (kolejność deklaracji w `LightingPreset.cs` l. 52–58). **Nie** za pustymi liniami na końcu — dokładnie ten błąd r4 sam złapał (Unity czytało 0). Po scaleniu test serializacji Night z gałęzi (asset vs fabryka) musi przejść. Auto-merge: `LightingPreset.cs`, `WorldAtmosphere.cs`, `EnvironmentLighting.cs`, `KamionAtmosphere.hlsl`, `Sky.shader` (1 linia), ADR 0108.
- **landmarks r3:** 5 konfliktów.
  - `generated/streetscape_qa.json`, `generated/world_manifest.json`, `art-source/world/props/street_props.glb` (LFS) → `--ours` + regeneracja; `props_meta.json` (auto) → i tak regeneracja.
  - `tools/worldgen/streetscape/materials.py` → **`--ours` (cała wersja main).** Własne commity landmarks r3 nie dotykają tego pliku; konflikt to tylko przestawiony blok ADR0118 (asfalt) z merge-base, po stronie gałęzi **zdublowany** na końcu — nie wnosić. Kontrola: `road_asphalt` przypisany dokładnie raz; `_underdeck_pier_paint`, `_underdeck_pier_weather`, `furniture_sign_fronts` obecne. Zmiana pigmentu filarów jest w danych (`viaduct_underdeck.json`, auto-merge), nie w kodzie.
  - `docs/LICENSES.md` → **unia**: zostawić sekcje main (ADR 0112 Brown Leather … furniture r2) i dopisać sekcję „Kominy EC — uzupełnienie referencji ADR 0116 r3” z gałęzi (z poprawionymi spacjami).
  - Auto-merge kodu: `ec_chimneys.py` (nowy), `hero_building.py` (+4: `ec_chimneys.plan`), `landmarks.py` (+8: pomija generyczny stożek), ADR 0116/0119, `test_ec_chimneys.py`, `test_viaduct_underdeck.py`.
- **asphalt r2:** 4 konflikty.
  - `generated/fidelity_qa.json`, `generated/streetscape_qa.json`, `generated/world_manifest.json` → `--ours` + regeneracja.
  - **`tools/worldgen/streetscape/materials.py` — UNIA ręczna.** Wziąć wersję main (z blokami ADR 0119 filarów i ADR 0120 `plate_back`; gałąź jest na starej bazie i ich nie ma) i **dopisać na końcu pliku** (po bloku `plate_back` / `furniture_sign_fronts`) dwa bloki z gałęzi: (1) „ADR0118 r2: material-only road aliases” — pełne przypisania `curb_concrete` (z `kerb_wear`: joint_dirt 0.35, mineral_film 0.16, film_threshold 0.55) i `sidewalk_paving` (z `ground_grime`: damp_darkening 0.18, damp_threshold 0.65, joint_dirt 0.45, damp_gloss 0.15); (2) pętla `for _asphalt_ground_id in ("curb_concrete", "sidewalk_paving")` ustawiająca `ground_wear_exclude_local_en = [400.0, -700.0, 850.0, -250.0]` z komentarzem o zakresie Kwadrat. Bazowe pola (`color`, `rough`, `surface`, `texture_set`) są identyczne z `tools/worldgen/roads/build_world.py` l. 74–77 na main — pełne nadpisanie słownika bezpieczne. **Nie** usuwać `flake_lift` (main, life r3) — gałąź go nie ma. Kontrola grep: `kerb_wear`, `ground_grime`, `ground_wear_exclude_local_en`, `_underdeck_pier_paint`, `furniture_sign_fronts`, `flake_lift` — wszystkie obecne.
  - Auto-merge do weryfikacji kompilacją: `WorldPBR.shader` (bloki kerb_wear/ground_grime, 3 × float4), `WorldPbrMaterials.cs`, `WorldSurface.shader` (+2). Po merge EditMode musi zawierać `AsphaltScopeTests`.
- Między gałęziami: landmarks i asphalt dotykają `materials.py` i generatów; light i landmarks rozłączne. **Kod wymagający ręcznej unii: `LP_Night.asset` (light r4), `materials.py` (asphalt r2), `LICENSES.md` (landmarks r3).** Reszta → `--ours` + regeneracja.

## Kolejność scalania
**sbs r3 → light r4** (`LP_Night.asset`) → **landmarks r3** (`--ours` generaty/`materials.py`/`street_props.glb`, unia `LICENSES.md`) → **asphalt r2** (unia `materials.py`, `--ours` generaty; `git rm` 3 × `geometry-*.json` + oryginał PCRT) → jedna regeneracja (materials → build_world → fidelity → import) + `WorldTruckInstaller.InstallBatch` → EditMode + pytest gis + physics/gate3 (potwierdzić `top_speed_flat_comb`) → kamery kontrolne Low/High × clear/overcast + Night `route-putry-approach` → SBS Low-overcast **na czystym drzewie generated** (guard SHA) → APK (WorldPBR/KamionTone zmienione: warianty shaderów, SRP Batcher) → `device-metrics.ps1` na A16.
Równolegle (dane, bez kodu): awans `275528-04` i `837235-12` do `sbs_authored_overrides.json` + render 4 stanów + D51 — największy tani zysk G3-B (2 → 4/10).

## Oceny 1–10 (render edytora, kadry rundy)

| Kategoria | sbs r3 (pozy C vs produkcja) | landmarks r3 | asphalt r2 | light r4 |
|---|---|---|---|---|
| skala i proporcje | 7 (C-04/-12 trafiają skalę portalu) | 7 | 7 | 6 |
| światło i ekspozycja | n/d | 6 | 6 | 4 (day-for-night) |
| materiały | n/d | 5 (biel = szarość) | 6 | 5 |
| zużycie / osadzenie | n/d | 4 (kominy czyste) | 4 | 4 |
| powtarzalność | n/d | 6 | 4 (kostka idealna) | 5 |
| realia PL | 7 | 7 | 6 | 5 |
| czytelność | 6 | 7 | 7 | 5 |
| artefakty | 7 | 8 (pas i równoległobok usunięte) | 7 (mokre chmury usunięte; kredowe rysy na main) | 6 (czarna elipsa na jezdni) |

## Uwagi do następnych rund
- **sbs r4:** awans 275528-04, 837235-12; 494288 strona jezdni (latarnie lewe); 3281350 portal po lewej tyłem; P1 `sbs-gate3.ps1` (ComposeOnly re-entrant, czytelny guard SHA).
- **landmarks r4:** biel pasów kominów ~0,6–0,7 lin.; 3 wyloty z balustradą (multi), pierścień + pomost w połowie (single); zacieki pod galeriami; pigment filarów B ~0,14; iglaki remizy (plan autora).
- **asphalt r3:** kredowe zawijasy rys na jezdni (main) → czarny bitum; behaton posesji `r10_house_2` z tym samym kamuflażem plam; nieregularność kostki (wymienione, zapadnięte, piasek przy trawie); place przemysłowe poza Kwadratem (plan autora).
- **light r5:** hierarchia nocy — plamy pod latarniami i ciemne przerwy, świecące okna, łuna; smog/szary pas nieba (batch C P1) przy innych kątach i wysokościach słońca; deterministyczny wiatr w capture QA.
