# ADR 0201b — Naciski osi ciągnika 73/27 % (karta S9), strojenie zawieszenia, dwie poprawki logiki AMT

Status: Proposed (agent vehicle-physics, gałąź `axleloads-tuning-0201b`, baza `truckdata-0201` = PR #77), 2026-11-15. Scalenie: lider.
Dotyczy: ADR 0201 (pkt 2 „naciski — osobne zadanie”), ADR 0134 (kiwnięcie oka przy zmianie biegu), ADR 0024 (strategia AMT),
`docs/VEHICLE_REFERENCE_DATA.md` (VRD), `docs/PHYSICS_VALIDATION.md` (PV §6g). Decyzja właściciela 2026-11-15: „osobne zadanie strojenia”.
Forma: osobny plik `0201b`, nie sekcja „R4” w 0201 — 0201 dokumentuje dane R3 (promienie, marki, errata) i jest w recenzji PR #77;
tu zmienia się model (masy, zawieszenie, AMT), więc decyzja ma własny ślad i można ją scalić lub odrzucić niezależnie.

## Kontekst
Ciągnik solo w grze: 4,81 / 2,69 t z paliwem 600 kg, bez paliwa 4,52 / 2,38 t (65,5/34,5 %). Karta producenta (S9 R3-012…014,
0 l paliwa): 5030 / 1815–1840 kg, udział przodu **73,2–73,5 %** w całym zakresie rozstawów 3500–3800 mm (dla 3700: 5030/1835 = 73,3 %).
Źródło nie podaje tolerancji; przyjęto pasmo karty (73,2–73,5 %). Eksperyment n1 z ADR 0201 (przesunięcie mas bez strojenia,
przód bez paliwa 4,94 t) obalił 4/135 scenariuszy. Powtórzony tu bit w bit (`artifacts/axleloads-0201b/exp-n1-repro/`).

## Decyzja
1. **Rozkład mas skalibrowany do karty** (WORKING_VALUE, kalibracja do SOURCED): rama środek 1,6→2,10 m, dł. 6,0→5,8 m (DERIVED z
   `art-source/truck/dims.json`: koniec ramy 0,80 m za osią tylną, przód ~0,15 m za zwisem 1,45 m); oś tylna z kołami 1300→1100 kg
   (R3-022: oś 13 t bez kół 680 kg SOURCED + 4 koła i wahacze); chłodnica/zderzak/osłona przeciwnajazdowa 300→500 kg; osprzęt
   (zbiorniki powietrza, akumulatory, oczyszczanie spalin, AdBlue) z 1,5→2,6 m. Masa całkowita 7500 kg bez zmian, paliwo 600 kg @ 1,8 m
   bez zmian (VRD). Wynik: **bez paliwa 5058 / 1842 kg = 73,3 / 26,7 %** (w paśmie karty), z paliwem 5350 / 2150 kg (71,3/28,7 %);
   pusty zestaw 5,65 / 3,45 / 5,40 t; **40 t: 7,20 / 10,26 / 22,55 t** — w limitach SOURCED (R3-008/009/010: 10 / 11,5 / 24 t)
   i w tabliczce przodu 7,5 t (R3-016, zapas 0,30 t). Środek masy y 1,089→1,102 m.
2. **Zawieszenie** (kryterium: częstotliwość własna):
   - przód resor: 213→**250 kN/m** — wzór VRD k = m_naroże(2π·1,5 Hz)² przy nowym nacisku daje 237 kN/m; 250 kN/m odtwarza sprzężony
     mod podskok/pochylenie solo ciągnika testowanego przez właściciela (ADR 0134): 1,483 / 1,80 Hz vs 1,489 / 1,78 Hz (model 2-DOF
     masy resorowanej z oponą szeregowo); przód „narożnie” 1,54 Hz. Tłumiki przodu ×1,11 (ζ≈0,3): 9000/18000→**10000/20000**.
   - tył miech: 91→**73 kN/m** przy nowym obciążeniu referencyjnym = **ten sam miech** (k/F 6,92 vs 6,90 1/m, 1,3 Hz przy każdym
     obciążeniu) — pusty/40 t bez zmian sztywności. Tłumiki tyłu bez zmian (sprzęt dobrany do osi obciążonej; ζ solo 0,35→0,43).
   - stabilizatory skalowane naciskiem solo (sztywność przechyłowa na jednostkę obciążenia osi): 200/300→**222/240 kN·m/rad**.
   - tył: odbój 25→**15 mm** (+10 mm wolnego skoku ugięcia, 85 mm od pozycji statycznej). WORKING_VALUE z uzasadnieniem pomiarowym
     (pkt „Przyczyny” 1); skoku nie ma w otwartych kartach (R3-157 UNVERIFIED).
   - kabina: **bez zmian** (1,5/1,6/1,8 Hz, ζ 0,5) — kiwnięcie wróciło poniżej progu po poprawce AMT.
3. **AMT — dwie luki logiki ujawnione przez lżejszą oś napędową** (`AmtController`, `VehicleModel`):
   - harmonogram zmian biegów z pedału kierowcy (po ograniczniku prędkości, **przed** cięciem ASR); ASR tnie moment, nie żądanie kierowcy.
     Wcześniej start z ASR przesuwał linię zmiany w górę z 1750 na ~1600 rpm (harmonogram „lekkiego gazu”) i blokował pominięcie biegu.
   - anty-zgaśnięcie sprzęgła w fazie Launch: otwieranie **8 /s** (było 2 /s cel + 4 /s narastanie; pełny skok ~0,125 s, rząd 0,15 s
     faz sprzęgła przy zmianie biegu).
   Sama poprawka AMT na starych masach: 135/135 PASS (`amtOnly/`), solo 0–80 13,58→13,40 s, 0–60 9,84→9,06 s; pusty i 40 t bez zmian.

## Przyczyny 4 scenariuszy obalonych przez n1 (CSV + wykresy, `artifacts/axleloads-0201b/`)
1. **Krawężnik 14 cm @ 50 km/h, pusty** (`max_wheel_airtime_s(1)` 0,23 > 0,15; Fz/stat 4,31 > 4,2): lewe tylne koło wchodzi w odbój
   (14 cm > 7,5 cm wolnego skoku) i podrzuca tył; oś napędowa w pustym zestawie lżejsza o 13 % (3,45 vs 3,99 t) → większa prędkość
   podrzutu, prawe tylne koło odciążone przez stabilizator i przechył, potem oba tylne w powietrzu. Szczyt Fz bezwzględny **spadł**
   (77→71 kN), stosunek do statycznego wzrósł, bo mianownik −13 %. Base 0,12 s był po części artefaktem: prawe koło dotknęło drogi na
   1 próbkę (2,55 kN przy t=2,44 s), co podzieliło ~0,17 s odciążenia na dwa odcinki. Dźwignie (przegląd `sub-*`): tłumik tyłu ↑ skraca lot
   ale Fz > 4,2; stabilizator tyłu 180 kN·m/rad = 0,15 (granica); **+10 mm wolnego skoku ugięcia: 0,11 s i 3,66** (lepiej niż base).
2. **Kiwnięcie oka przy zmianie biegu, pusty** (4,37 > 4°): łańcuch — lżejsza oś → start ograniczony ASR (współczynnik 0,5–0,7) →
   AMT dostawał pedał×ASR jako „gaz” → linia zmiany ~1600 rpm → bieg po pominięciu lądował 942 < 950 rpm → 4-5-7 zamiast 4-6-8 →
   mocniejsze przyspieszenie na 5. po zmianie → większy przysiad. Strojenie kabiny (ζ 0,7, 1,7 Hz) nie schodzi poniżej 4,04°.
   Po poprawce AMT: 4-6-8, **3,64°** (base 3,79°).
3. **Pierwsze oderwanie koła, rollover R50 CoG nisko** (NaN): to nie stabilność — sterownik pełnym gazem dochodzi do sufitu mocy
   55,1 km/h na R50 (opór znoszenia opon), a próg detekcji to Fz < 500 N; base oderwał przy 488 N na suficie, n1 zatrzymał się na 862 N
   (wewnętrzne koło 1. osi naczepy). Rozkład sztywności przechyłowej ciągnika (tył bierze mniej momentu naczepy) przesunął wynik o
   kilkaset N. Po przeskalowaniu stabilizatorów: **0,458 g** (base 0,460 g); wysoki CoG 0,337 g (0,340).
4. **Dryf energii soak 30 min** (44,9 > 5 J): **nie krok/integrator** — n1 przy dt 0,01/0,005 s i 4/8 sub-krokach: 44,9 / 46,0 / 44,9 J
   (`soak-dt/`). To fizyczne osiadanie po zatrzymaniu: zestaw pełznie 0,001 km/h z wygasaniem τ≈14 s, pochylenie wraca o 0,07°, a E =
   KE + PE grawitacyjna nie zawiera energii sprężyn opon/zawieszenia. Base 1,4 J to częściowe znoszenie się ciągnika (CoM w górę) i
   naczepy (w dół); przesunięcie CoM ciągnika do przodu zmieniło ramię i znoszenie. Wariant końcowy: −2,8 J (dt 0,005: −2,9 J).
5. Nowe obalenia w trakcie (kandydaci A–D), też wyjaśnione: zgaśnięcie przy cofaniu 40 t na ograniczniku przegubu (ASR + zbyt wolne
   anty-zgaśnięcie, base miał 427 rpm przy 350 granicy) → pkt 3; pełzanie naczepy 12 % pusty 5,05 > 5 mm: miech tyłu lżejszej osi ugina
   się bardziej od przeniesienia nacisku na spadku, przekracza strefę martwą zaworu poziomującego 8 mm, poziomowanie przy hamulcu
   sprężynowym obraca zablokowane koła → przesunięcie; przy 250 kN/m przodu 4,97 mm (zapas 0,6 %, cienki — jak base 4,72 = 94 %).

## Dlaczego 0–80 solo się wydłuża
Rozkład: same masy (bez AMT, kandydat C) 13,58→14,69 s (+8,2 %); sama poprawka AMT −1,3 %; razem **14,06 s (+3,5 %)**. Przyczyna:
trakcja osi napędowej. Granica przyczepności solo μ 0,8 z przeniesieniem nacisku (h 1,10 m, L 3,70 m): a ≈ 0,8·F_tył/m / (1 − 0,8·h/L)
= 3,7 → 2,95 m/s² (nacisk tył 26,4 → 21,1 kN). Siła z silnika na 4. biegu ~90 kN ≫ 17 kN przyczepności, więc start solo jest ograniczony
przyczepnością (ASR) do ~6.–7. biegu — oczekiwane fizycznie dla 73/27 %. 40 t: oś napędowa 10,26 t, zestaw ograniczony mocą — 0–80
47,54→47,58 s. **Danych prasowych 0–80 dla ciągnika solo w VRD nie ma** (VRD cytuje test prasowy tylko jakościowo — pomijanie biegów AMT);
porównanie z prasą pozostaje otwarte.

## Walidacja (RUNNER .NET, dt 0,01 s, 4 sub-kroki; nie telefon)
| | before (R3, `r3-base`) | after (`final`) |
|---|---|---|
| naciski solo bez paliwa / z paliwem | 4,52/2,38 t (65,5 %) / 4,81/2,69 t | **5,06/1,84 t (73,3 %)** / 5,35/2,15 t |
| 40 t przód / napęd / tridem | 6,66 / 10,79 / 22,55 t | 7,20 / 10,26 / 22,55 t |
| solo 0–80 / 80→0 (bramka A16: 13,66 s / 35,85 m) | 13,58 s / 35,77 m | **14,06 s / 35,39 m** (MFDD 7,48→7,73) |
| 40 t 0–80 / 80→0 (A16: 47,79 s / 40,72 m) | 47,54 s / 41,02 m | 47,58 s / 41,20 m |
| pusty 0–80 / 80→0 | 20,53 s / 39,59 m | 21,14 s / 39,99 m |
| f własne solo: mody podskok/pochylenie (masa resorowana) | 1,489 / 1,783 Hz | 1,483 / 1,800 Hz |
| f osi „narożnie” z oponą: przód / tył; przechył | 1,36 / 1,28; 1,38 Hz | 1,38 / 1,29; 1,37 Hz |
| kabina pochylenie / przechył / podskok | 1,5 / 1,6 / 1,8 Hz ζ 0,5 | bez zmian |
| krawężnik 14 cm pusty: lot koła ciągnika / Fz/stat | 0,12 s / 3,94 | 0,11 s / 3,66 (n1: 0,23 / 4,31) |
| kiwnięcie oka przy zmianie biegu, pusty | 3,79° | 3,64° (n1: 4,37°) |
| rollover R50 CoG nisko / wysoko | 0,460 / 0,340 g | 0,458 / 0,337 g (n1: NaN) |
| soak 30 min dryf E | 1,4 J | −2,8 J (n1: 44,9 J) |

Runner: **135/135 PASS (789 kontroli)**, tolerancje bez zmian. Goldeny: 6 nagranych ponownie (`brake_80_0_dry`,
`brake_80_0_dry_abs_comb_laden40`, `brake_80_0_wet_abs_comb_laden40`, `jackknife_wet_curve_noabs_empty`, `launch_0_80_flat`,
`launch_6pct_uphill_comb_laden40`) — przyczyny na nakładkach `artifacts/axleloads-0201b/plots/golden-*.png` (obejrzane): statyczne Fz
przód/tył (+2,1 / −2,0 kN na koło solo), ciśnienie EBS tyłu niższe (sygnał = siła miecha), inna sekwencja biegów solo (4-6-8-10-12
z pominięciem, poprawka AMT). 3 pozostałe goldeny przechodzą bez zmian. Testy .NET **273/274**: nie przechodzi
`BodyContactTests.F2_Repro_FailsWithoutChassisContact_PassesWithIt` — asercja `max_free_flight_energy_gain_j ≤ 1 J` w przebiegu
**mutacyjnym bez kolizji nadwozia** (pojazd spada przez grunt). Wynik jest chaotyczny względem trajektorii przed upadkiem: przód
237/245/249/250/251/255 kN/m → 93 / 0 / 218 / 92 / 198 / 1059 J; zysk występuje w 1–3 krokach tuż po utracie kontaktu (t≈4,91 s)
i odpowiada uwolnieniu energii sprężystej sprzęgu siodła (sprężyna przechyłu 1e7 N·m/rad, ~6 kJ zmagazynowane) i korekcji Baumgarte
pozycji sworznia (błąd 1,4 mm). Dodanie ½k·φ² siodła do bilansu usuwa część (255 kN/m: 1059→0 J, 249: 218→0), ale nie wszystko
(250: 95 J) — reszta to korekcja Baumgarte. Nie zmieniono testu ani metryki; decyzja lidera (pkt Otwarte).

## Uwaga z recenzji #77 (koordynator): hardpoint i promień 0,51 m
`WheelGroup` stawia hardpoint na `radius + SStatic − refLoad/k_opony`. Ugięcie opony nie jest liczone drugi raz: okrąg kontaktu jest
sztywny (promień `radius`), a ugięcie opony to sprężyna szeregowa doliczana do skoku (`sEff = S + F/k`). W położeniu statycznym przy
obciążeniu referencyjnym: S = SStatic − ugięcie, sEff = SStatic, środek okręgu kontaktu na wysokości `radius` = 0,51 m nad gruntem,
początek układu pojazdu na gruncie. Odjęcie ugięcia w hardpoincie tylko umieszcza punkt mocowania tak, by sprężyna szeregowa była
w pozycji statycznej. Masy są zadane względem gruntu (projektowa wysokość jazdy), więc wysokość CoM, naciski (dźwignia po z)
i częstotliwości (k_zaw szeregowo z k_opony) **nie zależą** od tej konwencji; 4 scenariusze też nie. Skutek modelowy: `radius`
działa jak **promień statyczny obciążony** okręgu kontaktu (stały przy każdym Fz), a ugięcie opony obniża nadwozie, nie środek okręgu.
Źródło 0,51 m: VRD — WORKING_VALUE między promieniem statycznym przy nośności 0,500–0,507 m (S9 R3-108…110, S7) a swobodnym 0,538 m.
Nowa oś przednia: ugięcie referencyjne 23,6→26,2 mm, hardpoint 2,6 mm niżej w ramie — tylko przestawienie projektowe.

## Otwarte
- **Feel test właściciela na telefonie** (start solo z ASR, przysiad/kiwnięcie, praca przodu na 250 kN/m, krawężnik) — wymagany.
- F2 mutacja (273/274): lider decyduje: (a) metryka lotu swobodnego z energią sprzęgu siodła i bez kroków korekcji pozycji, albo
  (b) asercja energii tylko w przebiegu z kolizjami. Bez decyzji nie scalać.
- Cienkie zapasy: pełzanie 12 % 4,97/5 mm, krawężnik Fz OK 3,66/4,2, `kerb_step_27cm` dv 0,32/0,35, MFDD solo 7,73/8.
- 0–80 solo vs testy prasowe — brak danych w VRD; bramki telefonu (A16) do ponownego pomiaru (solo 0–80 oczekiwane ~+3,5 %).
- EditMode/PlayMode, APK nieuruchomione (chmura bez Unity). Unity-adapter używa `VehicleModel` — poprawka AMT działa także tam.
