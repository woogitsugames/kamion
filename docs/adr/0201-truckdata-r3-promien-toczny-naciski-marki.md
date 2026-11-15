# ADR 0201 — Dane ciężarówki z R3: promień toczny vs geometryczny, naciski osi, marki, errata R13

Status: Proposed (agent vehicle-physics, gałąź `truckdata-0201`), 2026-11-15. Scalenie: lider.
Dotyczy: ADR 0004 (rdzeń fizyki w czystym C#), 0019 (siodło 0,68 m), 0195 (autopilot prosta 0–80–0), `docs/04` §2.4 i §6.3/§6.5,
`docs/VEHICLE_REFERENCE_DATA.md` (VRD), `docs/PHYSICS_VALIDATION.md` (PV). Źródło liczb: pakiet R3 `research/cloud2/truck-parameters/`
(VRD S9, przegląd `docs/reports/REVIEW-2026-11-14-s20-cloud2-r3.md`).

## Kontekst
Przegląd R3 wskazał w danych gry: (a) jeden promień opony 0,51 m do geometrii i kinematyki, a karty 3 producentów dają promień
toczny (obwód toczenia / 2π) 0,521–0,528 m dla 315/80 R22.5 i 0,522–0,526 m dla 385/65 R22.5 (R3-108…118); (b) rozkład nacisków
ciągnika solo 64/36 % vs 73/27 % karty (R3-012…014); (c) docs/04 podawał opony 315/70, gra używa 315/80; (d) VRD/PV cytowały dla
hamulca awaryjnego kat. N wzór M2/M3 (/130, 60 km/h); (e) nazwy marek w danych/kodzie gry.

## Decyzja
1. **Dwa promienie opony** (`TireDefinition`): `radius` = promień geometryczny (w modelu kontaktu: sztywny dysk; ugięcie opony dodawane szeregowo, więc środek koła statycznie = radius − ugięcie — patrz „Recenzja drugim modelem”) — promienie kontaktu, punkt mocowania
   zawieszenia, płaszczyzna styku wizualnego koła (`tyreFlatRadius`); `rollingRadius` = efektywny promień toczny — ω ↔ v (poślizg),
   Fx ↔ moment koła (napęd, hamulec, opór toczenia), `WheelRadiusRef` (AMT, obroty, dźwięk wału), `InitializeMoving`, trzymanie
   postojowe naczepy. Ten sam promień dla kinematyki i momentu = zgodność mocy (Fx·v = T·ω przy zerowym poślizgu).
   `rollingRadius = 0` → `radius` (stare dane); walidacja: [radius, 1,15·radius].
   Wartości: 315/80 R22.5 **0,524 m** (R3-108: 3294 mm / 2π = 0,5243; zakres R3-117), 385/65 R22.5 **0,524 m** (R3-114…116:
   0,5216–0,5255; R3-118) — DERIVED (S9). Promień geometryczny bez zmian: 0,51 / 0,515 m (WORKING_VALUE, między promieniem
   statycznym przy nośności 0,498–0,507 m a swobodnym 0,536–0,546 m).
   Przegląd konsumentów (grep `Radius`/`RollingRadius`/`WheelRadiusRef`): `WheelGroup` (kontakt 129 → `Radius` ✔; hardpoint 62 →
   `radius` ✔; moment 345, poślizg 368, opór toczenia 429, przyspieszenie bieżnika 457 → `RollingRadius` ✔), `VehicleModel`
   (`_wheelRadiusRef`, `InitializeMoving` → toczny ✔), `TrailerModel` (135, 236 → toczny ✔), `TruckAssetBuilder`/`TrailerAssetBuilder`
   `tyreFlatRadius` i graybox → `Radius` ✔ (geometria), `VehicleVisuals`/`TrailerVisuals` obrót = ∫ω dt (koło wizualnie toczy się
   jak realna opona — obwód toczny > 2π·r_obciążony), `TruckAudioController` `ShaftRpm` ← `WheelRadiusRef` (−2,7 % wysokości tonu wału
   przy danej prędkości — fizycznie poprawne).
2. **Naciski osi — sprawdzone, NIE zmienione** (WORKING_VALUE): gra solo 4,81 / 2,69 t z paliwem 600 kg; bez paliwa 4,52 / 2,38 t
   (65,5/34,5 %) vs karta 5,03 / 1,82–1,84 t (73/27 %, 0 l paliwa, R3-013/014) — przód −10 %. Masa bez paliwa 6900 kg vs 6845–6870
   (+0,4 %, OK). Laden40 6,62 / 10,76 / 22,62 t mieści się w limitach SOURCED (R3-008/009/010/016: 10 / 11,5 / 24 t, tabliczka przód
   7,5 t). Eksperyment przesunięcia mas (rama z 1,6→2,0, osprzęt 1,5→2,3, silnik+skrzynia 3,3→3,7, kabina 3,9→4,0 m → solo 5,24/2,26 t,
   bez paliwa przód 4,94 t = −1,7 % vs karta; `artifacts/truckdata-0201/exp-axleloads-n1/summary.md`) zmienił solo 0–80 o +7 %
   i obalił 4/135 scenariuszy strzegących odczucia/stabilności (krawężnik 14 cm: czas lotu koła 0,23 > 0,15 s i Fz 4,31 > 4,2;
   kiwnięcie oka przy zmianie biegu 4,37° > 4° (ADR 0134, test właściciela); wykrycie pierwszego oderwania koła w rollover R50 = NaN;
   dryf energii soak 30 min 44,9 J > 5 J). To wymaga strojenia zawieszenia/kabiny i oceny odczucia — osobne zadanie, nie ta runda.
3. **Errata dokumentów** (commit `bd686b017`): docs/04 §2.4 opony 315/80 R22.5 (dane gry); VRD S5 i PV w.6: hamowanie awaryjne kat. N
   0,15 v + 2v²/115 z 40 km/h (N3) = 33,8 m; hamowanie resztkowe po awarii przenoszenia N3 obciążony 0,15 v + (100/30)·v²/115 =
   **52,4 m** (R3-151, 161, 162); scenariusz `air_leak_rear_circuit` max 52,4 m (był 64,4 m z wzoru M2/M3).
4. **Marki usunięte z danych/kodu gry** (commit `3977d5280`): skrzynia `amt12_od_class` (GUID `.meta` zachowany), opisy silnika
   i ciągnika, `DrivingLabSceneBuilder`, `ContactShadowCaster`, scenariusze i testy runnera. Grep (`volvo|scania|traxon|daf|mercedes|
   actros|iveco|renault|kässbohrer|krone|schmitz|michelin|bridgestone|dunlop|goodyear|continental|nokian|intarder|VEB|I-Shift|…`)
   po `tools/physics-runner`, `tests/physics`, `game/Assets/_Project/{Vehicle,Audio,Gameplay}` = 0 trafień. Marki zostają tylko
   w VRD/research jako identyfikacja źródła danych.
5. **Goldeny** (`tests/golden/`): 4 przebiegi czasowe nagrane ponownie (`launch_0_80_flat`, `launch_6pct_uphill_comb_laden40`,
   `brake_80_0_wet_abs_comb_laden40`, `jackknife_wet_curve_noabs_empty`) — były nagrane z r = 0,51 m dla kinematyki; to była
   przyczyna 4/274 FAIL. Tolerancje `tolerances.json` bez zmian. Pozostałe 5 goldenów przechodzi bez zmian.

## Walidacja (RUNNER .NET, nie telefon; dt 0,01 s, 4 sub-kroki)
Baseline `origin/main` 5724a161b (`artifacts/truckdata-0201/before-main/`) vs gałąź (`after-r3/`): **135/135 scenariuszy PASS
(789 kontroli) w obu**. Scenariusz autopilota `straight_0_80_0` (= definicja bramek 1–2, ADR 0195):

| wariant | metryka | bramka (A16, telefon) | runner main | runner R3 | Δ runner | wyjaśnienie |
|---|---|---|---|---|---|---|
| solo | 0–80 | 13,66 s | 13,60 s | 13,58 s | −0,15 % | przełożenie efektywne −2,7 % (v = ω·0,524): siła −2,7 % na bieg, ale zmiany biegów przy +2,7 % prędkości i niższe obroty w paśmie mocy — netto ~0; 0–60 −1,0 % (9,94→9,84 s, 9→11 później) |
| solo | 80→0 | 35,85 m | 35,69 m | 35,77 m | +0,22 % | ta sama presja → siła hamowania T/r −2,7 %; na suchym z ABS liczy się tylko w narastaniu ciśnienia i fazach ABS; MFDD 7,46→7,48 |
| 40 t | 0–80 | 47,79 s | 47,52 s | 47,54 s | +0,04 % | jak solo; zestaw ograniczony mocą |
| 40 t | 80→0 | 40,72 m | 40,52 m | 41,02 m | +1,23 % | jw.; średnio w hamowaniu a 6,28→6,23 m/s², MFDD 7,04→6,92 (−1,7 %); w paśmie 35–61,2 m (R13 typ 0 N3, SOURCED) |
| pusty | 0–80 / 80→0 | – | 20,53 s / 39,49 m | 20,53 s / 39,59 m | 0 / +0,25 % | jw. |

`launch_0_80_flat` 13,60→13,58 s; `brake_80_0_dry` 34,69→34,75 m; `brake_80_0_dry_abs_comb@laden40` 40,80→41,06 m. Obroty w 12. biegu
przy 89 km/h 1230→1195 rpm (−2,8 %, wykres `plots/shift-launch_0_80_flat.png`). Inne ruchy > 2 %: `launch_6pct_uphill_light_comb@laden40`
czas do 10 km/h 18,07→20,13 s (+11 %, pasmo PASS): ruszanie na poślizgu sprzęgła przy 900 rpm, siła napędowa ~30,3 kN −2,7 % = −0,8 kN przy oporze wzniesienia 23,5 kN → przyspieszenie netto 0,17→0,15 m/s² (różnica dużych liczb; wykres `plots/shift-launch_6pct_uphill_light_comb@laden40.png`), mikro-metryki (µm/mm/s) siodła i dryfu.
Wykresy obejrzane (`artifacts/truckdata-0201/plots/`): nakładki biegów (solo, 40 t, 6 % 40 t), jackknife bez ABS (koło odblokowuje się
~0,4 s wcześniej — moment hamulca / r mniejszy), hamowanie mokre 40 t z ABS (inna faza cykli ABS), `straight_0_80_0@solo` (statycznie
23,6 kN/koło przód, 13,2 kN/strona tył; nurkowanie kabiny ~3,4°). Testy .NET **274/274** (po goldenach; przed: 270/274).
Bramki telefonu (13,66 / 35,85 / 47,79 / 40,72) zmierzone na APK z main — runner przesuwa się o −0,15 / +0,22 / +0,04 / +1,23 %;
na telefonie oczekiwane analogicznie, **niezmierzone** (lider: APK + `gate12-phone.ps1`).

## Otwarte
- Rozkład mas ciągnika (73/27 % karty) — osobne zadanie ze strojeniem zawieszenia/kabiny i testem odczucia właściciela (pkt 2).
- Siodło 0,68 m vs karta 0,375 m przed osią (R3-019, jedno źródło; ADR 0019) — bez zmian.
- EditMode/PlayMode i APK nieuruchomione w tej rundzie (chmura bez Unity); scena/prefaby nie zmieniane — `tyreFlatRadius` dalej = `radius`.
- Bramki 1–2 na telefonie po scaleniu (lider).


## Recenzja drugim modelem (2026-11-15)
Darmowe modele OpenRouter (`nvidia/nemotron-3-ultra-550b-a55b:free`, `cohere/north-mini-code:free`; zasady: `docs/owner/OPENROUTER-FREE-MODELS.md`), każde zgłoszenie zweryfikowane w kodzie. Potwierdzone: wszyscy konsumenci używają właściwego promienia (kontakt/hardpoint → `radius`; moment, poślizg, opór toczenia, AMT, audio, naczepa → `rollingRadius`), Fx·v = T·ω. Poprawione opisy: `radius` to promień geometryczny modelu kontaktu (środek koła statycznie = radius − ugięcie opony), nie „obciążony”; tooltipy `tyreFlatRadius` (to promień geometryczny, nie toczny); numer linii `TrailerModel`. Otwarte: (1) jeśli 0,51 m pochodzi z karty jako promień statyczny OBCIĄŻONY, model odejmuje ugięcie drugi raz (środek koła niżej o refLoad/radialStiffness) — do sprawdzenia w zadaniu strojenia nacisków (gałąź `axleloads-tuning-0201b`); (2) sprzed tego PR: `TireDefinition` nie odrzuca `radius = NaN` (`double.IsFinite`).
