# 0191 — Plamy latarni: rozsył oprawy drogowej (asymetryczny, wzdłuż jezdni) per oprawa, sód/LED, odblask GGX na High

Status: kandydat (gałąź `lamppool-0191`), nie scalone. Data: 2026-11-13 (s20). Dotyczy: ADR 0062 (analityczne pule), 0108 (noc),
0182 (zmierzch, „Otwarte P1-4”), recenzja `REVIEW-2026-11-13-s19-0182` P1-4.

## Kontekst
Recenzja s19 P1-4: o zmierzchu „pul nie ma” — plac w `chase` równo jasny 32–35 %, na trasie (route_putry) pod latarniami brak plamy.
Przyczyna w `KamionLampPools.hlsl` (ADR 0062): oprawa okrągła, stała do 60° od nadiru (dysk o promieniu 1,73 h) + okno 35 m, a do
shadera szedł środek bryły słupa (nie oprawa na wysięgniku), bez kierunku wysięgnika i bez sodu. Przy rozstawie z danych (najbliższy
sąsiad p50 28,9 m, `standards.LAMP` 30–36 m przy h 8–11 m; 698 słupów w regionie: 660 reguła, 21 authored, 11 OSM, 6 override)
4–8 dysków nakładało się w jednolitą łunę.

## Decyzja
1. **Rozsył oprawy drogowej** zdefiniowany śladem na jezdni w jednostkach wysokości montażu h: `E = I0/h² · (1−ρ²)²`,
   `ρ² = (wzdłuż/2,4)² + (w poprzek/RC)²`, RC = 1,5 h po stronie jezdni (kierunek wysięgnika), 0,7 h za słupem; oprawa bez wysięgnika
   symetryczna 1,8 h. Równoważna bryła fotometryczna `I(γ,C) = I0·F·(d/h)³`: „bat-wing” ze szczytem ~2,2·I0 przy ~54° wzdłuż drogi,
   pełne odcięcie powyżej ~67° — więc ściany i pojazdy dostają tę samą I·cos/d². Strumień w dół 2,76·I0 = 6,9 klm przy I0 2500 cd
   (oprawa 8–12 klm × utilance ~0,6). WORKING_VALUE, kształt typowy dla EN 13201, bez kopiowania fotometrii produktu.
   Równomierność przy rozstawie z danych: min/szczyt 0,49 (h 9/S 29), 0,44 (10/33), 0,46 (11/36), 0,20 (8/30 — ulice osiedlowe).
2. **Jedna pula = jedna oprawa**: `WorldInstances` czyta granice podsiatki `M_lamp_glass*` prototypu (SubMeshDescriptor.bounds, działa
   bez read/write) → pozycja oprawy na końcu wysięgnika, kierunek wysięgnika, dwie oprawy dla `lamp_double_*`/`lamp_y`, sód gdy
   materiał `*_sodium` (`StreetLampOptics.LuminairesFromGlass`). Do shadera `_KamionLampAxis[8]` obok `_KamionLampPos[8]`.
3. **Sód**: barwa puli `_KamionLampSodium` = (sód/LED) przy równej luminancji Rec.709 (natężenie w cd jest fotometryczne).
4. **Odblask GGX lamp** (smuga na asfalcie) w `KamionLampPoolsLit` za flagą profilu `lampPoolSpecular`: High/Ultra tak, Low/Medium nie.
   Override A/B `rq_lampspec 0|1`. Revision QualityProfile 113 → 191 (migracja w `ProjectSetup`).
5. Brak świateł realtime, brak wariantów, brak nowych draw calli; nadal pętla z gałęzią jednorodną, tylko przy zapalonych lampach.

## Budżet (A/B, WorldC, `stats.txt`)
- Draws / shadow draws / tris: **identyczne** before/after (Low i High, 6 kamer; np. Low chase 416 / 89 / 308 k, Low route 297 / 48 / 277 k).
- ALU (szacunek z kodu, UNVERIFIED): pula dyfuzyjna ~16 → ~24 ALU/lampę; Low 4 pule ≈ +32 ALU/px świata, tylko zmierzch/noc;
  High +~14 ALU/lampę za GGX × 8. GPU ms na A16/S24+ — **niezmierzone** (zakaz adb w tym zadaniu); pomiar przy najbliższym APK:
  `device-metrics.ps1` o zmierzchu, A/B `rq_lampspec`, `rq_lamppools 0`.

## Walidacja
- Kamery: chase, trailer-34, route_putry_approach, driver_andersa_to_putry, putry_above, kwadrat_park_gate × Low/High × dusk/night
  (`artifacts/lamppool-0191/{before,after1}/`, arkusze `sheet-*.jpg`, `lum.tsv`; preset `night` dodany do `visual-qa.ps1`).
- Pas jezdni (wiersze 55–95 %), p90/p10 luma: noc High chase 6,1 → 16,4, route 2,6 → 5,6, driver_andersa 3,1 → 7,0, gate 3,2 → 12,1;
  zmierzch High chase 4,7 → 8,2, gate 3,3 → 4,8. p50 kadru zmierzch −4,1…+1,9 pp (route 20,3 → 20,4, trailer-34 16,6 → 12,5), noc −0,4…−3,6 pp (mniej łuny między słupami).
- Referencja: Mapillary CC BY-SA 4.0, grobin, 2019-10-18 ~20:54, DK8/Andersa (`refs/mapillary-night-ids.tsv`, arkusz
  `refs/mapillary-night-2019-10-18.jpg`, zestawienie `ref-sbs-night.jpg`): wydłużone plamy wzdłuż jezdni, ciemniejsze doły między
  słupami, pobocza szybko gasną — po zmianie zgodne; barwa: na zdjęciach 2019 sód, w świecie DK8 LED (stan dzisiejszy UNVERIFIED).
- EditMode: `StreetLampOpticsTests` (nadir 1/h², asymetria, kształt okrągły post-top, doły przy rozstawie z danych, bat-wing + odcięcie,
  strumień numeryczny vs wzór, wysięgnik pojedynczy/podwójny/post-top, lustro stałych HLSL↔C#, luminancja sodu, flaga tylko High/Ultra).

## Otwarte
- **kwadrat-park-yard (override)**: dwie latarnie łukowe przy `chase` (E 712,5 / 731,7) mają wysięgniki skierowane do siebie
  (yaw −2,06 vs 1,05); ta przy E 731,7 świeci na plac, nie na pas — ciężarówka w `chase`/`trailer-34` stoi teraz w cieniu
  (trailer-34 p50 zmierzch 16,6 → 12,5). Pule wiernie oddają geometrię; do sprawdzenia `face` w `overrides.yaml` (world-builder).
- Kamery lotnicze (putry_above) widzą tylko pule przy ognisku 30 m przed kamerą (limit 8 pul) — nie dotyczy jazdy.
- Pojazdy nadal oświetlane symetrycznymi światłami punktowymi (High) / wcale (Low) — zgodność z rozsyłem w Truck Exterior: follow-up.
- Pomiar GPU na A16 i S24+ (wyżej), ocena właściciela barwy sód/LED, glare opraw (P2-8), okna (P2-6) — poza zakresem.
