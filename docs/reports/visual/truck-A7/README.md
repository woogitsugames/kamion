# A7: ciężarówka TRAKT w Unity (zewnętrze A6 LOD0–2 + wnętrze koniak) — 2026-11-09

Właściciel: `rendering-perf`. Graybox ciągnika zastąpiony w scenach świata (`WorldC`, `WorldC_High`) ciężarówką TRAKT z eksportów A6.
Naczepa zostaje graybox. Fizyka bez zmian (te same kolizje, ten sam model; wymiary zgodne z ADR 0014 po `git merge main`).

## Jak odtworzyć (wszystko kodem, nic ręcznie)

```
# 1. wnętrze LOD0 (8,6 MB FBX, poza gitem: art-source/truck/interior/.gitignore; ~65 s)
uv run --no-project --with pillow --with numpy python tools/blender/truck/interior/make_textures.py
blender -b --factory-startup --python tools/blender/truck/interior/a6_export.py -- --lods 0 --out <tmp> --manifest <tmp>/cab_interior_manifest.json
#    skopiuj <tmp>/SM_CabInterior_LOD0.fbx do art-source/truck/interior/export/ (atlas AO LOD0 w gicie pasuje: różnica 0,4 %/px, szum bake)
# 2. prefab + materiały per tier + podmiana w WorldC/WorldC_High (+ kamery kontrolne A7)
Unity -batchmode -executeMethod Game.World.Import.WorldTruckInstaller.InstallBatch      # albo menu Kamion/Setup/Rebuild TRAKT truck
# 3. kamery kontrolne
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low|Medium|High -Lighting overcast|lowsun|dusk -Cameras cab-driver,cab-dash,cab-left,cab-right,truck-34 [-CabFill off]
pwsh scripts/device-metrics.ps1 -Serial <s> -Launch -Scene WorldC -QaCamera cab-dash -Extra lighting=lowsun
```
Wynik generatora (`TruckAssetBuilder`) leży w `game/Assets/_Generated/Truck/` (poza gitem, jak świat — ADR 0011): kopie FBX i atlasów,
materiały `Materials/<Tier>/`, zestawy `Resources/TRAKT/TruckMaterials_<Tier>.asset`, prefab `Tractor4x2_TRAKT.prefab`.

## Co zrobione
- **Import:** FBX skala 1, convert units, bez bake osi, bez animacji, tangenty MikkT; tekstury sRGB/linear/normal wg kontraktu,
  ASTC na Androidzie wg manifestu (C 6×6/8×8, N 5×5/6×6, M 8×8, decal 6×6; wnętrze analogicznie).
- **Shadery (własne, URP, SRP batcher):** `Kamion/Truck Exterior` (atlasy C/N/M, lakier biel flotowa + napis TRAKT z decala uv1, brud 0,5,
  światła z uv2 w cd/m² × ekspozycja sceny), `Kamion/Truck Glass` (cienka szyba, Fresnel z probe/cubemapy, frit to geometria eksportu),
  `Kamion/Cab Interior` (kontrakt danych wierzchołków: tint, chropowatość, detal, AO uv1, zużycie, perforacja, metal; naklejki z clip i AO z uv1).
- **Prefab z `rig_parent`:** korzeń z grayboxa (Rigidbody, VehicleBody, VehicleVisuals, te same BoxCollidery, kamera siodła) → fizyka identyczna.
  Koła i zwrotnice pod pivotami kół z fizyki (obrót i skręt z solvera), kabina na pivocie zawieszenia kabiny w `mountCenter` z fizyki
  (pitch, roll i nowy heave), drzwi/wycieraczki/szyba/lusterka pod CAB_Body, LOD1–2 pod transformem LOD0 tej samej roli, kierownica na
  osi kolumny (kąt koła kierownicy z fizyki), `DriverEyePoint` = `EYE_POINT` z manifestu (−0,55; 2,50; 4,15).
- **Tiery:** High = zewn. LOD0–1 + wnętrze LOD0 + tekstury High; Medium = LOD1–2 + LOD1 + Medium; Low = LOD2 + LOD2 + Low (`TruckVisualRig`).
  Prefab trzyma tylko zestaw Low; Medium/High ładują się z Resources na żądanie.
- **Review r2 A6:** #1 (czarna kabina) — patrz niżej; #2 biały pas u podstawy szyby — usunięty: wnętrze traci `CAB_ShellPlaceholder`
  i `CAB_Glass_Windows`, jedyne szyby to `GLASS_*` zewnętrza z czarnym fritem (widoczny w `r2-High-overcast_cab-dash.jpg`);
  #4 lusterka — główne L/P z render texture (kamera w obrazie lustrzanym oka, FOV z rozmiaru szkła), szerokokątne/krawężnikowe/przednie:
  metaliczne odbicie probe zamiast białej karty; #5 świecące szwy — naklejki dostają AO z uv1 (`cab-right`: szwy fotela nie świecą).
- **Światła:** `TruckLights` (DRL, auto mijania przy słońcu < 6°, stop z pedału, cofanie) — jedna globalna tekstura 16×1, bez lamp URP.

## Światło kabiny przy niskim słońcu (A6 #1 P0)
Pomiar (wartość wyświetlana sRGB, średnia regionu, `artifacts/cabstats.py`), słońce 9°, za kabiną z lewej (najtrudniejszy przypadek):

| Tier / wariant | dolna deska L | boczek drzwi pasażera | boczek drzwi kierowcy |
|---|---|---|---|
| Medium, bez fill (`-CabFill off`) | 34,7 % | 23,7 % | 36,4 % |
| Medium, z fill | 38,5 % | 25,0 % | 38,1 % |
| Low (A16, bez post) | 36,1 % | 9,7 % | 20,8 % |
| High | 24,1 % | 24,8 % | 36,3 % |

Kryterium review (> 8 % przy 9°) spełnione na wszystkich tierach. **Wniosek: w prawdziwym URP kabina nie jest czarna** — ambient SH × AO
atlasu wystarcza; czerń była cechą emulacji Cycles. `CabInteriorLighting` dodaje fizyczny (sfera całkująca) pierwszy odbłysk światła
wpadającego przez szyby — zależy od kierunku słońca względem kabiny (test `CabFill_FollowsSunThroughTheGlass`) — oraz +0,3 EV w widoku
z kabiny (lokalne mapowanie tonów telefonu, D23). Koszt: kilka flopów CPU, zero świateł i przejść.

## Wydajność (telefon, WorldC, kamera `cab-gate` — ta sama w obu APK; graybox = APK z main 1b4edcf, TRAKT = b218ce7590)
| | graybox | TRAKT |
|---|---|---|
| A16 Low, bez limitu (vsync 60) | 59,35 FPS, p95 16,73 / p99 33,30 ms, GPU 15,78 ms, PSS 560 MB | 59,49 FPS, p95 16,72 / p99 16,81 ms, GPU 15,94 ms, PSS 579 MB |
| S24+ High, bez limitu, **throttling (status 2, 43–44 °C)** | 44,85 FPS, GPU 21,88 ms, PSS 1001 MB | 47,43 FPS, GPU 20,02 ms, PSS 1074 MB |

A16 Low w widokach A7 (limit 30): 30,1 FPS, GPU 16,0–16,3 ms, PSS 571–581 MB. Koszt TRAKT na A16: GPU +0,16 ms, PSS +18 MB.
S24+ High `cab-dash` (patrzy w dół na deskę): GPU 29 ms pochmurnie, 39 ms w słońcu (cienie: `rq_shadow=0` → 29 ms; 8 m = 100 m, więc to
koszt cieni na pełnoekranowym wnętrzu, nie świata). Twarde cienie we wnętrzu: 39,2 → 36,2 ms (zostawione). Rzucanie cieni przez wnętrze
wyłączone = bez zmian (zostawione włączone). Wszystkie liczby S24+ z rozgrzanego telefonu (status termiczny 2 od początku sesji).
Build: zasoby ciężarówki 54 MB nieskompresowane, APK 220,6 → 232,7 MB (+12,1 MB). Trójkąty: zewn. 82,9k / 43,0k / 14,5k, wnętrze 75,4k / 34,9k / 19,0k.

## Model ↔ fizyka
Po ADR 0014 (scalone z main przed klatkami końcowymi): zaczep kabiny 1,15/3,925 = fizyka, siodło 1,15 = fizyka, rozstaw 2,04/1,82 = fizyka
(test `ExteriorRig_ParentsResolve_AndMatchThePhysics`, tolerancja 1 cm). Pozostaje: opona wolna 0,5378 m vs promień toczny 0,51 m —
koło stoi w środku z fizyki; od r2 (rendering-perf) `Kamion/Truck Exterior` spłaszcza oponę na promieniu tocznym (warstwa renderowania 8 kół,
`TruckVisualRig.tyreFlatRadius` z fizyki), więc bieżnik nie wchodzi w asfalt; knuckle obraca się wokół środka koła,
nie sworznia (5 cm), błąd < 2,5 cm przy 30°.

## Otwarte
1. ~~Czerń 21 % / prześwietlone ściany przy niskim słońcu / brak zmierzchu~~ — r2 (rendering-perf): ADR 0016 (krzywa tonalna,
   tabela EV od wysokości słońca). Wyświetlacze: `Kamion/Cab Display`, kontrast 67:1 (pochmurno) – 160:1 (niskie słońce).
   Wnętrze LOD0 na każdym tierze (A16 Low: GPU bez zmian, 16,1 ms). Klatki z telefonów: `device-r2/`.
2. Otwarte z recenzji r3: clear coat lakieru + odbicie nieba w szybie (E1/E2), cień kontaktowy/AO pod pojazdem (E3), lusterka wypukłe (C5).
3. S24+ High `cab-dash` w słońcu 36 ms GPU (rozgrzany): profil AGI/Frame Debugger cieni na flagowcu do zrobienia na zimnym telefonie;
   brak pomiaru 30 min (temperatura) dla TRAKT.
4. Lusterka szerokokątne/krawężnikowe/przednie: placeholder z probe, bez RT; lustra płaskie (realne klasy II/IV są wypukłe).
5. Brak: clear coat, światła punktowe reflektorów nocą, animacja drzwi/wycieraczek/pedałów (pivoty gotowe).
6. Przegląd `visual-critic` A7 nie wykonany w tej sesji.
