# ADR 0114: Zabudowa r7 — działki „wąsko i dobrze”: geometria chunka w jednym materiale, płoty wg typologii, zjazd z obniżonym krawężnikiem, trawnik, zacieki od końców parapetu

Status: propozycja (world-builder, gałąź `buildings-r7`, z main `dd45e00c`), 2026-11-11. Kontynuacja ADR 0107; odpowiedź na
`docs/reports/visual/REVIEW-2026-11-11-s10-0107.md` (P1-r7-a..g, P2-r7-a/b/d/g). Referencje: `docs/refs/posesje-bialystok.md`
(33 klatki Mapillary CC BY-SA + 7 Commons — oglądane, żaden piksel nie wchodzi do tekstur). Nic z telefonu.

## Kontekst
Recenzja 0107: działki jako instancje kosztowały na Low do +45 instancjonowanych draws na kamerę (ADR podawał „+0,0 %”),
wszystko znikało naraz na 60 m, siatka „ocynk” świeciła na biało, podjazd z płyt schodkował i stał na krawężniku,
trawnik nie różnił się od łąki, tuje były rzędem identycznych stożków, a ślady spod parapetów — bladym prostokątem.

Pomiar własny (ten sam kod, świat bez działek jako odniesienie — `KAMION_NO_PLOTS=1`, runda `noplots`): działki r6
= **+152 instancjonowanych draws** na 67 kamerach Low, **maks. +45** (`r10_house_2`), 0 draws MeshRendererów. Zgodne z recenzją.
Przyczyna: `WorldInstances` rysuje komórka 64 m × prototyp × submesh, więc koszt rośnie z liczbą komórek, nie prototypów.

## Decyzja
1. **Zero instancji — cała działka jest geometrią chunka** (`streetscape/plots.py`, przepisany):
   - płoty, bramy, słupki, skrzynki, śmietniki, tuje, świerki, drzewka, krzewy, byliny → warstwa `furniture`, **jeden materiał
     `plot_kit`** = jeden atlas alfa 2048² (`streetscape/plot_kit.py`, rysowany z prymitywów): 7 wierszy ogrodzeń, mur,
     cegła, próbki stali/drewna/betonu, tuja, świerk, karty jabłoni/krzewu/bylin. Jedna działka = jedna część siatki;
   - trawnik + podjazd + dojście → nowa warstwa chunka **`plot_ground`** (jak `paved`: drape na wygładzonym NMT, teren
     dopasowany pod spodem, kolizja), ale pokazywana tylko w LOD0/LOD1 chunka i bez rzucania cieni. Materiały:
     `plot_lawn` (nowy) i istniejący `yard_paving`;
   - zasięg: warstwy `furniture` / `plot_ground` są w LOD0 i LOD1 chunka, czyli do ok. 300 m od krawędzi chunka na każdym
     tierze (było: cull 60 m na Low). Przejścia łagodnego (dither) NIE ma — `LODGroup.fadeMode = None` jak dla całego
     chunka; znikanie następuje poza zasięgiem, w którym płot 1,5 m ma ≥ ~5 px.
2. **Typologia ogrodzeń wg klasy wieku domu** (reguła z powierzchni / kondygnacji / wysokości — BDOT nie ma roku budowy;
   20 % domów przesunięte o klasę): *old* — sztachety rdzawe (C04, P06), deski pełne rdzawe / brązowe (P08, P09),
   siatka zielona w ramie (P10, C03); *prl* — słupki ceglane ze sztachetami / deskami (C01), pręty czarne na podmurówce
   (P12), siatka, deski, płyty betonowe; *new* — słupki ceglane z prętami (P24), mur grafitowy (P13, P14), lamele
   poziome (P15), beton. Boki i tył: głównie siatka albo tańszy wariant frontu. Wysokości z dokumentu referencji.
   `plot_kit` jest matowy (rough 0,85, metal 0); siatka = ciemna zieleń w teksturze, bez materiału „ocynk”.
3. **Front posesji**: furtka 1,0 m + brama 3,5 m skrzydłowa (przesuwna 4,0 m u 19 % bram, nie przy starych domach),
   wspólny słupek, skrzynka na listy, śmietniki za płotem; podjazd = jeden wielokąt od krawędzi jezdni przez bramę
   obok domu (do garażu, gdy stoi w osi); dojście od furtki do ściany domu; pas trawy 1,5 m między śladem drogi a płotem.
   **Obniżony krawężnik**: plan działek powstaje raz na geometrii przebiegu 1 `build_world`; `plots.apply_drops`
   (przez nowy parametr `pipeline.build(side_edit=)`) obniża `side['h']` łańcucha do 3 cm na szerokości bramy + 0,4 m
   z rampami 1 m — profil chodnika wisi na wysokości krawężnika, więc chodnik i siatka kolizji obniżają się razem.
   Rów profilu zamiejskiego jest zasypywany do 6 cm. Odcinek między śladem drogi a krawędzią jezdni domyka pas kostki
   2 cm nad powierzchnią pobocza. Działka bez drogi w zasięgu: sama furtka (P2-r7-a).
4. **Ogród**: trawnik `plot_lawn` (zestaw `grass_verge`, ta sama baza fotograficzna co pobocza, jaśniejszy tint),
   rabata bylin pod ścianą frontową i czasem za płotem, rzędy tuj o rozstawie ±20 %, wysokości ±30 %, z lukami (7 %)
   i zbrązowiałymi sztukami (4 %), świerk kłujący 2,5–9 m (P02, P17, P18), jabłoń 3–4,4 m, krzewy. Roślinność ogrodu
   to statyczna siatka chunka (bez wiatru, bez własnego LOD).
5. **P1-f od nowa**: generator tnie ścianę także **obok** końców parapetu (pasek 12 cm, `sill_strip_uv1`, |u| ≥ 2),
   więc wąs jest wyśrodkowany na końcu parapetu, a nie ucięty na krawędzi kolumny pod oknem. Shader (`WorldPBR`,
   blok `_RUNOFF`, tryb v ≥ 112): wąs 9 cm → 4 cm, miękkie boki, długość 0,55–1,0 skali; pas pod kapinosem tylko
   wewnątrz parapetu i gaśnie w 0,25 skali; siła ≥ 0,5 (mnożnik tynku ×0,6 zostawiał ~3 poziomy).
6. Kolizja: ogrodzenia i zamknięte bramy mają ściany `collision_fence` (P2-r7-d).

Pliki wspólne (addytywnie): `materials.py` (blok na końcu: `plot_kit`, `plot_lawn`), `standards.py` (`SURFACE_OF`),
`paved.py` (`item['layer']`, `item['edging']`), `export.py` (tekstura atlasu), `stage.py` (`plan_plots`, lista
`plot_paved`), `pipeline.py` (`side_edit`), `build_world.py` (plan po przebiegu 1, warstwa `plot_ground`),
`props.py` (usunięte 2 linie prototypów 0107), `RegionImporter.cs` / `WorldSceneBuilder.cs` / `WorldSkyBake.cs` /
`Gate3Audit.cs` (warstwa `plot_ground`), `RegionImporter.cs` (alias bazy trawy dla `plot_lawn`),
`WorldPbrMaterials.cs` (`plot_lawn` w `_GRASS_DETILE`), `InstanceImporter.cs` (atlas 2048 na Androidzie),
`WorldPBR.shader` (blok wąsów). `furniture.py`, `QualityProfile`, `WorldSurface.shader` — bez zmian.

WORKING_VALUE: wszystkie udziały typologii i progi klas wieku, wysokości ogrodzeń, 19 % bram przesuwnych, krawężnik
3 cm / rampa 1 m, pas 1,5 m, tint trawnika, kształt i siła wąsów, kolory atlasu.

## Liczby (edytor, szacunek przed batchingiem SRP; nic z telefonu)
Rundy w `artifacts/buildings-r15/`: `noplots` (świat bez działek), `base` (= main, działki r6), `r5` (stan końcowy).
Skrypt `budget2.py`, 67 kamer kontrolnych; pliki `budget_low_r5.txt`, `budget_high_r5.txt`.

| Low overcast, względem świata bez działek | r6 (main) | r7 (r5) |
|---|---|---|
| draws MeshRendererów, suma / najgorsza kamera | +0 / +0 | **+97 / +10** (`r10_house_1`, `r10_house_2`) |
| draws instancjonowane, suma / najgorsza | **+152 / +45** (`r10_house_2`) | +21 / +5 (`edge-north`) — instancji działek 0; różnica to przesunięte drzewa |
| razem MeshRenderer + instancje, suma / najgorsza | +152 / +45 | **+118 / +11** (`r10_house_1`) |
| `r10_house_2` / `r10_shed_2` / `r10_fence_2` (razem) | +45 / +36 / +26 | +10 / +9 / +5 |
| draws cieni MeshRendererów, suma / najgorsza | +0 | +44 / +6 (cienie instancji r6 nie były liczone w ogóle) |
| trójkąty siatek (k), suma / najgorsza — same działki | 0* | +169 / +19 (`g3b-rondo-putry-approach` 275 → 294) |
| trójkąty siatek (k), paski przy parapetach (P1-f)* | — | +69 (suma; budynki LOD0 przy trasie) |
| trójkąty instancji (k), suma | +18 | +0 |

\* runda `noplots` ma już paski ściany przy parapetach (P1-f), `base` ich nie ma: `noplots` − `base` = +69 k (Low) /
+145 k (High) trójkątów na 67 kamerach to koszt P1-f, a `r5` − `noplots` to same działki.

| High overcast, względem świata bez działek | r6 (main) | r7 (r5) |
|---|---|---|
| MeshRenderer + instancje, suma / najgorsza | +282 / +51 (`r10_house_2`) | **+359 / +29** (`r10_fence_1`) — suma GORSZA niż r6 |
| draws cieni MeshRendererów, suma / najgorsza | +0 | +189 / +27 (`r10_fence_3`) |
| trójkąty siatek (k), same działki, suma / najgorsza | 0 | +994 (+2,5 %) / +97 (`r10_fence_1` 665 → 762, +15 %) |
| trójkąty siatek (k), paski przy parapetach (P1-f), suma | — | +145 |

Rundy pośrednie (Low, razem suma / najgorsza): r1 (trawnik w `paved`, żwir, obrzeża) +241 / +20; r2 (bez żwiru i obrzeży)
+192 / +15; r3 (warstwa `plot_ground`) +118 / +11.

| inne | wartość |
|---|---|
| region Low: submeshe / mln tris | 3009 / 4,487 → 3066 / 4,609 (+57 / +2,7 %) |
| region High: submeshe / mln tris | 4028 / 14,09 → 4085 / 14,21 (+57 / +0,9 %; w tym paski przy parapetach) |
| `plot_kit`: trójkąty w regionie / chunki | 56 964 / 16 (ogrodzenia ~24 k, tuje ~16 k, bramy ~8 k, reszta ~9 k) |
| `plot_lawn` / `yard_paving` w `plot_ground`: trójkąty / chunki | 37 587 / 16 i 7 311 / 11 |
| szacunek klatki `stretch_04` High (test `test_hero_bridge`, limit 2,000 mln) | 1,929 → **1,992 mln** (zapas 7,6 k) |
| działki | 98 (old 21 / prl 51 / new 26), mediana 569 m²; 48 bram (9 przesuwnych), 144 furtki, 48 podjazdów |
| obniżenia krawężnika | 28 planowanych, 28 zastosowanych; `drop_check.py`: 26 z 35 zjazdów ma krawężnik < 6 cm (3,0–4,6 cm), 7 bez łańcucha (skrzyżowania, końce dróg) zostaje przy 13–15 cm |
| ogród | 435 tuj, 22 świerki, 54 jabłonie, 253 krzewy, 1100 kart bylin, 19 śmietników |
| zacieki, 5 m (`r15_sill_5m`, piksel 0,5 cm), para Runoff on/off, `sill_marks.py` | rdzeń wąsa 19,3 poziomu sRGB (1 ślad w kadrze); `r13_block3_close` (14 m): 22,0 (3 ślady) |
| zacieki, 20 m (`r15_sill_20m`, piksel 1,9 cm) | rdzeń wąsa mediana **10,2** (p10 5,2, p90 18,4), średnio po śladzie 7,1; 32 ślady; ściana ~130 |
| testy | `pytest tests/gis` 481 passed, 1 xfailed, 1 failed (`test_road_fidelity::test_report_not_stale`: raport sprzed zmian w `roads/*.py`) → po `fidelity/run.py` plik przechodzi (46 passed w plikach fidelity / hero_bridge / buildings r5–r7); EditMode 261 / 261 |

## Samokrytyka (docs/06)
- **Bez `visual-critic` i bez telefonu.** Oceny wyłącznie moje; koszt na A16 nieznany.
- **High jest droższy niż r6 w sumie** (+359 vs +282 draws, +2,5 % trójkątów, jedna kamera +15 %): siatki chunków
  rysują się w LOD0/LOD1 wielu chunków naraz. Cel „≤ +15” był postawiony dla Low i tam jest spełniony (+11).
- **Zapas budżetu trójkątów `stretch_04` High to 7,6 k** — następna zmiana zabudowy go przekroczy.
- **Brak łagodnego przejścia**: zamiast ditheru jest zasięg ~300 m. Z kabiny nie powinno być widać znikania, ale nie
  ma nagrania przejazdu (statyczne kadry `r15_dist_60/120` pokazują płoty na Low; `r15_dist_250` trafił pod wiadukt).
- **Działki nadal są regułą**, nie EGiB: prostokąty wg osi domu; klasa wieku to zgadywanie z bryły.
- **7 z 35 zjazdów bez obniżenia** (brama naprzeciw łaty skrzyżowania) i 13 bram bez dojazdu do jezdni (podjazd kończy
  się na śladzie drogi).
- **Tuje** są 6-kątnymi bryłami z dość ciemną, plamistą teksturą; z bliska czytają się jako low-poly. Świerk i jabłoń
  to spódnice / skrzyżowane karty — z góry widać konstrukcję.
- **Mur i płyty betonowe idą skosem po terenie** zamiast schodkami; tył płotu oświetlony jak przód tam, gdzie siatka
  jest pojedyncza (`Cull Off`, jedna normalna).
- **Dojście od furtki** prowadzi do ściany frontowej, nie do drzwi (pozycja drzwi nie jest znana planowi działki).
- **Żwirowe podjazdy i obrzeża usunięte dla budżetu** (ref. P20 pokazuje żwir) — wszystkie podjazdy to kostka.
- **Zacieki z 20 m**: mediana 10 poziomów, ale najsłabsze 10 % śladów ma ~5 — poniżej progu 6–8. Na Low (budynki LOD1
  poza trasą) śladów nie ma.
- Kamera `r14_plot2_eye_az160` stoi po zmianie działek w ścianie — do przestawienia.
- Baza (`base`) była importowana bez zestawu `asphalt_detail_photo` (brak w kopii worktree, dograny przed r2) — nie
  wpływa na draws ani na działki, zmienia detal asfaltu w parach base → r5.

## Otwarte / do decyzji lidera
- visual-critic + A16 Low: `r10_house_1`, `r10_house_2`, `r10_shed_2`; nagranie przejazdu wzdłuż domów (pop).
- EGiB jako źródło obrysów; drzwi jako cel dojścia; obniżenia w łatach skrzyżowań.
- LOD roślin ogrodu / uproszczona siatka `plot_kit` dla LOD1 chunka, jeśli High okaże się za drogi.
- Zdjęcia właściciela: bramy przesuwne, zjazdy z bliska, skrzynki (luki z dokumentu referencji).
- Po scaleniu: `build_world` → `import-region` (atlas `plot_kit.png` powstaje w `export`; zestawy PBR bez zmian).

## Przewidywane konflikty
- `gpt-furniture-r1` / bariery 0110: `streetscape/stage.py` (moje wstawki: `_yard_src`, `plan_plots`, lista `plot_paved`
  przy `paved`, blok „house plots”), `props.py` (usunięte 2 linie na końcu `build_all`), `export.py` (`textures()`).
- `materials.py`: blok na końcu pliku (po bloku 0107).
- `build_world.py`: `LAYERS` / `NODES` (+`plot_ground`), wstawka między przebiegiem 1 i 2; `pipeline.py`: sygnatura `build`.
- `WorldSceneBuilder.cs` (tabele LOD), `RegionImporter.cs` (`k_LowLayers` / `k_HighLayers`, blok bazy Fab),
  `WorldPBR.shader` (blok sill w `_RUNOFF`), `InstanceImporter.cs` (linia `maxTextureSize`).
- Testy: `tests/gis/test_buildings_r5.py` (ślady parapetów), `test_buildings_r6.py` (testy działek przeniesione do
  nowego `test_buildings_r7.py`).
