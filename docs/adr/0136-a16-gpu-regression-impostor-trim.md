# ADR 0136: Regresja GPU A16 Low s10 → s12 — rozkład kosztu, ciasne impostory drzew

Status: propozycja (rendering-perf, gałąź `a16-perf`, z main `8b0d6ec7`), 2026-11-12; runda 1 scalona, runda 2 (s14) — sekcja „Runda 2”.
Powiązane: ADR 0106 (rozkład GPU A16, `rq_ab`), 0113 (las szybki, PSO), 0023 (impostory), D49 (A16 = Low), D50 (bez obniżania
skali renderu), D51 (rozpoznawalność).

## Kontekst
Gate3 A16 Low (APK `11db0552`, s12) vs s10 (`21a55c3fe4`, przed 0113): GPU p95 G3-A 31,8 → 35,5 ms, G3-B 33,3 → 35,2 ms,
p99 klatki G3-B 33,7 → 50,0 ms (`artifacts/gate3-a16-s12/REPORT-DATA.md`). Budżet 33,3 ms (30 FPS).

## Diagnoza (telefon A16 SM-A165F RFGL34SJYDZ; `artifacts/a16-perf/diag1/*`, `summarize.py`, `abwin.py`)
Ustawienia jakości/URP (`QualityProfile.asset`, `URP_Low`, renderer) s10 → s12 bez zmian poza `forestFast` (0113). Regresja = treść.
Bez limitu FPS (`rq_pacing=0`, skala 0,75) GPU p50 dziś ≈ 29,7 ms, tyle co s10 z limitem; realny przyrost ~+3 ms
(0113: bez limitu ~26,7 ms). Przy limicie 30 FPS governor Mali dodaje ~1,5–2 ms (G3-B t=40–90 s: s12 31,1–32,6 vs bez limitu 29,4–29,8).

**A/B przeplatane** (G3-B, bez limitu, 12+12 okien 4 s, APK diag `24ab345392`, Δ GPU p50 = A wysyłka − B bez elementu):

| element | Δ GPU p50 (ms) | uwagi |
|---|---|---|
| ciężarówka (warstwa Vehicle) | +4,03 | = 0106 po szybkiej szybie; nie regresja |
| drzewa (instancje + HLOD) | +2,53 | **okna 3–4 (las przy drodze, s≈1300–1450): +8,7 / +6,6** |
| — impostory | +1,37 | **okna 3–4: +6,6 / +4,8** → piki p99 50 ms |
| — ściany HLOD | +1,81 | równomiernie ~2 ms; ≈ 0106 (1,8) |
| — korony HLOD (Forest Canopy) | +0,16 | (0106: 0,9 przed 0113) |
| lusterka (1 render/klatkę) | +0,93 | = 0106 (0,75–1,25) |
| cienie (dystans 0) | +0,64 | ≈ 0106 (0,9) |
| płoty działek `plotkit` (0114) | +0,38 | nowe s11 |
| asfalt Low zużycie (0118) | +0,27 | nowe s12 |
| far field (0121) | +0,23 | nowe s12 |
| propsy | +0,16 | |
| żywopłoty / decale / ekrany+bramownice / znaki | +0,14 / +0,12 / +0,08 / +0,06 | nowe s11–s12 |
| budynki, Fab, lakier aut, przechwyt env | −0,34 / −0,12 / −0,12 / +0,05 | ≈ szum (±0,3) |

Wniosek: brak jednego winowajcy; nowa treść s11–s12 dokłada ~1,5–2 ms rozproszone po wielu materiałach, a najdroższe
pojedyncze miejsce to impostory drzew w gęstym lesie przy G3-B (tam GPU 35–37 ms, piki 50 ms). Atlasy impostorów
(`art-source/world/vegetation/impostor_tree_*.png`, 6 widoków 256×384) pokrywają tylko **6–13 % quada** (alfa > 128): ~90 %
fragmentów impostora (przebieg głębi z discard + przebieg koloru) jest rasteryzowanych tylko po to, by je odrzucić.

## Decyzja
1. **Ciasny wielokąt impostora** `Game.World.ImpostorTrim` (czysta matematyka, testy EditMode) + `Game.World.Import.ImpostorTrimBake`
   (wywołanie w `InstanceImporter` dla każdego `tree_*.lod2` — przeżywa reimport; batch `ImpostorTrimBake.RunBatch` przepisuje
   istniejące `Instances.asset` w miejscu): zamiast quada 6 poziomych pasm, których lewa/prawa krawędź obejmuje **sumę alfy
   wszystkich 6 widoków** (jedna siatka dla każdego widoku i przenikania dwóch widoków na Medium+), z dylatacją 6 tekseli
   (mipy alfy) i progiem alfy 4/255. Każdy teksel > 4/255 leży w wielokącie (test `ShippedImpostorAtlases_AreEnclosed`), więc obraz
   się nie zmienia; powierzchnia ~34 % quada (14 wierzchołków, 12 trójkątów zamiast 4/2). Konwencja wierzchołków shadera
   `Kamion/Vegetation _IMPOSTOR` bez zmian: `|x|` = półszerokość quada, `y` liniowo z `uv.y` jak na quadzie źródłowym.
   Wszystkie tiery (bez przełącznika: zero zmiany obrazu, mniej pracy na każdym GPU).
2. Bez zmian: skala renderu (D50), dystanse/przerzedzanie drzew, lusterka, cienie (koszty = 0106).

## Wynik (A16, APK diag `kamion-0.1.0-0e68ff8c5e-dirty.apk` = gałąź @ 0e68ff8c + bake, Low, `artifacts/a16-perf/final1`)
Bake: 18 impostorów, średnio 37 % quada (24–52 %). Kamery kontrolne Low overcast WorldC + gate3 (78): PSNR ≥ 58,2 dB, ≤ 0,014 %
pikseli różni się o > 8 poziomów (pojedyncze piksele A2C) — `artifacts/a16-perf/vqa/psnr.txt`, `vqa/960/*-before-after.jpg`.

| przejazd (limit 30 FPS) | FPS | p50 / p95 / p99 (ms) | >40 | GPU p50 / p95 / p99 | CPU p50 / p95 | PSS MB | T °C |
|---|---|---|---|---|---|---|---|
| G3-B s10 (gate3 20261111-154538) | 29,87 | 33,3 / 33,5 / 33,7 | 20 | 29,5 / 33,3 / 37,4 | 21,5 / 28,6 | 826 | 25,8 |
| G3-B s12 (gate3 20261112-145646, APK 11db0552) | 29,70 | 33,3 / 33,5 / **50,0** | 41 | 31,8 / 35,2 / 37,6 | 21,2 / 28,9 | 910 | 29,2 |
| **G3-B po (trim)** | 29,88 | 33,3 / 33,5 / **33,7** | **16** | 31,4 / **33,9** / 36,7 | 20,7 / 29,2 | 897 | 28,1 |
| G3-A s10 (gate3 20261111-154331) | 29,70 | 33,3 / 33,5 / 50,0 | 38 | 29,9 / 31,8 / 33,7 | 22,8 / 30,1 | 835 | 25,6 |
| G3-A s12 (gate3 20261112-142003) | 29,61 | 33,3 / 33,5 / 50,0 | 42 | 32,3 / 35,5 / 36,7 | 23,2 / 31,8 | 880 | 26,5 |
| G3-A po (trim) | 29,78 | 33,3 / 33,5 / 50,0 | 26 | 32,4 / 35,5 / 36,7 | 23,1 / 30,9 | 871 | 28,0 |

A/B bez limitu na G3-B (ten sam APK): impostory **1,37 → 0,51 ms** średnio, w oknach lasu **6,6 / 4,8 → 1,9 / 2,3 ms**.
„Przed” na tym samym APK/dniu nie dało się zmierzyć: release nie instaluje się z niższym versionCode (`INSTALL_FAILED_VERSION_DOWNGRADE`,
`-d` nie działa) — baza = gate3 s12 z tego samego dnia (ta sama treść). Jeden przejazd na wariant.

Ocena: **G3-B — p99 50 → 33,7 ms (jak s10), klatki > 40 ms 41 → 16, GPU p95 35,2 → 33,9 ms (cel 33,3: brakuje 0,6 ms).**
**G3-A — bez zmiany GPU** (brak lasu: drzewa/impostory/HLOD na G3-A ≈ 0, `artifacts/a16-perf/diagA`); regresja G3-A
(GPU p50 +2,5 ms przy limicie) nie jest w lesie: A/B G3-A bez limitu — asfalt Low (pęknięcia + detal, 0118) +0,96 ms (szum okien ±3 ms,
w G3-B +0,27), far field +0,36, płoty −0,44 (szum), ciężarówka +4,14 (bez zmian), **propsy (instancje: auta/przyczepy/meble/znaki) +2,48 ms GPU i +7,0 ms CPU**
(na G3-B tylko +0,16), cienie +1,44, lusterka +1,32 (propsy także w lusterkach i cieniach). Główny kandydat regresji G3-A = instancjonowane
propsy na placach/podwórzach (s11–s12: gpt-life r1–r3, furniture r2, static yard vehicles 0122). Do dalszej rundy: rozbicie `rq_ab off:m.<prefiks>` per prototyp na G3-A.

## Runda 2 (s14, 2026-11-12): G3-A — zaparkowane auta, lusterka, brud pojazdów na Low
**Uwaga pomiarowa.** Od 18:32 A16 leżący płasko uruchamiał grę w **portrecie 1080×2340** (ADR 0135 AllowAuto, `[SCREEN] ... orientation=Portrait`,
pionowy `screen.png`) — `diagA2`, `diagA3`, `baseA` są w portrecie (węższy kadr, GPU p50 ~24,5 zamiast ~29–32 ms) i służą tylko jako
rozbicie względne. Obejście pomiarowe `rq_landscape=1` (`Game.Rendering.DiagLandscape`, tylko z argumentem) w `r2b`/`r2c`/`diagA4`;
po ADR 0147 (main) A16 płasko sam przechodzi do landscape (`Lock (elongated portrait window: force landscape)` →
`Portrait -> LandscapeLeft 2340x1080` t = 7,5 s → `AllowAuto (landscape reached)`), więc `r2d` jest bez obejścia.
Porównania tylko **przeplatane w jednym APK**: zmiany Low mają override launch-arg przywracający stan sprzed rundy
(`rq_vehcull=300 rq_mirror_res=1 rq_grime=1`), bo starszego release'u nie da się zainstalować (versionCode) i dryf termiczny/DVFS
między sesjami sięga kilku ms.

**Rozbicie propsów G3-A** (nowe klucze A/B `rq_ab pp:<prefiksy>` = nie rysuj, `ps:<prefiksy|all>` = bez cienia, `vc:<m>` = cull aut,
`vl:<x>` = skala LOD aut, `vm` = auta poza lusterkami; `WorldInstances.SyncAbMasks`, tylko diagnostyka; Δ A−B p50 GPU / CPU ms, bez limitu,
skala 0,75; `diagA2`/`diagA3` portret, `diagA4` landscape po cull 150):

| B | GPU | CPU | | B | GPU | CPU |
|---|---|---|---|---|---|---|
| auta osobowe + vany + contact (`diagA2`) | +1,29 | +4,44 | | lampy / znaki / fab | −0,15 / −0,13 / −0,04 | +0,65 / +0,30 / +0,13 |
| ciągniki/naczepy/bus | +0,10 | +1,13 | | landmark/fasady / drobne | +0,21 / −0,66 | +0,93 / −0,72 |
| cull aut 300 → 150 m | +0,35 | +2,41 | | cienie propsów (`ps:all`) / aut | 0,00 / −0,46 | +0,04 / −0,11 |
| LOD aut ×0,5 / contact / auta w lusterkach | +0,22 / +0,13 / +0,06 | +0,66 / +0,41 / +0,86 | | (landscape) lusterka całe / tekstura ×0,75 | +1,46 / +0,47 | +2,74 / +0,26 |
| (landscape) brud pojazdów (grime) / clear coat | +0,68 / +0,15 | +0,61 / −0,03 | | (landscape) cienie całe / 25 m / 512 px | +1,11 / +0,39 / +0,31 | +2,37 / −0,53 / +0,15 |

Koszt propsów G3-A = **zaparkowane auta** (~370 w promieniu 300 m trasy wobec ~50 na G3-B; 24 prototypy × 12/11/7 submeshy LOD0/1/2 =
setki wywołań `RenderMeshInstanced` na kamerę). Koszt jest głównie po stronie CPU/sterownika (zgłaszanie), GPU-czas Mali rośnie razem z nim;
LOD aut i ich cienie prawie nic nie dają. Pozostałe propsy (znaki, latarnie, bariery, landmarki) ≈ 0 — zostają bez zmian (D51).

**Decyzja r2 (tylko Low; Medium/High/Ultra bez zmian, każdy przełącznik w `QualityProfile`):**
1. `Tier.vehicleCullM` = **150 m** na Low (0 = wspólne `WorldInstances.VehicleCullM` 300 m; dotyczy aut i ich plam kontaktowych;
   override `rq_vehcull`). Auto 4,4 m w 150 m ≈ 20 px w kadrze Low — świadome odejście od „te same pojazdy na każdym tierze” (REVIEW r6 W-N6) tylko na Low.
2. `Tier.mirrorResolutionScale` = **0,75** na Low → `MirrorOverrides.TierResolution` (lusterko klasy II 224 → 168 px, wypukłe proporcjonalnie):
   ta sama gęstość pikseli co główny widok Low (skala renderu 0,75). Pole widzenia R46, odświeżanie i far clip bez zmian; override `rq_mirror_res`.
3. `vehicleGrimeDetail` = **off** na Low (rozbryzg przy nadkolach + smugi; zostaje gradient wysokości), override `rq_grime`.

**Wynik (A16, G3-A, limit 30 FPS, landscape, przeplatane w jednym APK):**

| przejazd | APK | FPS | p50 / p95 / p99 (ms) | >40 | GPU p50 / p95 / p99 | CPU p50 / p95 | PSS MB | T °C |
|---|---|---|---|---|---|---|---|---|
| r2b przed (cull 300) ×2 | 23dc12142c | 29,7–29,8 | 33,3 / 33,5 / 50,0 | 26 / 40 | 32,5 / **35,7–35,9** / 36,9–37,5 | 22,8–23,0 / 29,4–30,0 | 880–898 | 29,6 |
| r2b po (cull 150) ×2 | 23dc12142c | 29,7–29,8 | 33,3 / 33,5 / 50,0 | 26 / 31 | 31,7–31,8 / **34,5** / 36,5–36,8 | 21,9–22,3 / 29,8–30,0 | 884–903 | 29,6 |
| r2c przed ×3 | 56b0df6b91 | 29,6–29,8 | 33,3 / 33,5 / 50,0 ×3 | 46 / 28 / 38 | 32,5 / **36,1 / 35,5 / 35,6** / 36,9–49,4 | 22,8–23,0 / 29,0–29,3 | 863–901 | 29,9–30,4 |
| r2c po (+ lusterka ×0,75) ×3 | 56b0df6b91 | 29,8–29,9 | 33,3 / 33,5 / 50,0 · 33,8 · 33,8 | 26 / 16 / 18 | 31,7–31,8 / **34,0 / 34,2 / 34,2** / 35,7–35,8 | 21,6 / 29,5 | 855–873 | 29,9–30,8 |
| **r2d przed** ×2 | 2080745dd4 | 29,6–29,8 | 33,3 / 33,5 / 50,0 | 30 / 50 | 32,4–32,5 / **35,7 / 36,1** / 36,8–39,7 | 22,7–23,0 / 29,2–30,1 | 906–934 | 30,6 |
| **r2d po (+ grime off)** ×3 | 2080745dd4 | 29,8–29,9 | 33,3 / 33,5 / 49,9 · 33,9 · 49,9 | 22 / 19 / 23 | 31,4–31,7 / **34,2 / 33,7 / 33,9** / 35,5–36,0 | 21,5–22,2 / 29,4–30,2 | 896–919 | 30,5–30,8 |

Ocena: **GPU p95 G3-A 35,9 → 34,0 ms (−2,0 ms, średnie r2d), klatki > 40 ms 40 → 21, CPU p50 −0,9 ms; cel 33,3 ms nieosiągnięty o ~0,6 ms**;
p99 klatki 50 ms nadal w 2 z 3 przejazdów (pojedyncze podwójne vsynci). Kamery kontrolne Low przed/po: VQA_PLACEHOLDER

## Otwarte
- **G3-A: brakuje ~0,6 ms do GPU p95 33,3** (r2). Kandydaci zmierzeni A/B: cull aut Low 100 m (+1,29 GPU w `diagA4`, szum ±0,7), cienie Low 25 m (+0,39) / 512 px (+0,31).
  Trwała poprawka zamiast cięcia: **LOD1/LOD2 aut z 1–2 submeshami** (atlas/kolor wierzchołka) w generatorze (`build_world.py`/`InstanceImporter`, world-builder) —
  7–12 submeshy × 24 prototypy to źródło kosztu CPU; wtedy Low może wrócić do 300 m.
- Blokada obrotu (rotation lock) przy ADR 0147 na A16 nie sprawdzona w r2 (wymaga zmiany ustawienia telefonu).
- Karty liści LOD0/LOD1 (`leaves_*.png` pokrycie 23–48 %) — ta sama technika na kartach w `trees.glb` (osobna siatka per karta).
- Ściany HLOD: górne ~12 % atlasu puste — przycięcie w `forest_hlod.py` (mały zysk).
- Treść s11–s12 (+1,5–2 ms rozproszone): budżet per runda dla agentów treści (pomiar `rq_ab off:m.<prefix>` na A16 przed scaleniem).
