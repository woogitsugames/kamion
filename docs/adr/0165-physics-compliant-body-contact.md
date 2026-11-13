# ADR 0165 — Podatny kontakt nadwozia z ziemią (4 Hz, ζ 1), limity penetracji, F1 3,5°
Status: Proposed (agent fizyki, s17, gałąź `phys-0165`), 2026-11-13. Wynika z decyzji właściciela D58 i D59 (ADR 0158).

## Kontekst
ADR 0158 dodał do runnera .NET kolidery nadwozia (lustro BoxColliderów z `GrayboxTractorBuilder`/`GrayboxTrailerBuilder`)
ze sztywnym kontaktem. Zostały dwie otwarte sprawy:
- **D58, krawężnik 27 cm**: zderzak (dolna krawędź 0,35 m) uderza w jezdnię. Sztywny kontakt daje skok prędkości w
  jednym kroku **0,572 m/s** przy limicie szarpnięcia 0,35 m/s (`kerb_step_27cm_42kmh_comb@laden40`). Na `main`
  scenariusz biegał bez koliderów. Właściciel wybrał podatny (tłumiony) kontakt, a limity szarpnięcia zostają.
- **D59, F1**: miękki ogranicznik przegubu bez zmian, tolerancja nadmiaru ≤ 3,5°.

## Decyzja
1. **Kontakt narożnika jako sprężyna z tłumikiem, całkowana niejawnie** (soft constraint, E. Catto, GDC 2011; Box2D v3).
   Dla każdego narożnika boxa pod jezdnią F_n = max(0, k·pen + c·ṗen). Wartość jest liczona na koniec kroku i
   rozwiązywana razem z tarciem Coulomba (stożek kołowy, μ 0,6 jak domyślny PhysicsMaterial) metodą PGS, 10 iteracji.
   Kontakt jest stabilny dla każdego k, c i dt. Szczelina spekulatywna: narożnik nad jezdnią dochodzi do niej bez tłumika,
   a sprężynę czuje tylko przez tę część kroku, którą spędza pod powierzchnią.
2. **Parametryzacja częstotliwością na masę efektywną narożnika**: k = m_eff (2πf)², c = 2ζ m_eff (2πf). Ustawienie
   f = **4 Hz**, ζ = **1,0**, status **WORKING_VALUE**: dla tej fikcyjnej ciężarówki nie istnieje zmierzona sztywność
   zgniotu. Stałe k w N/m nie obsłuży jednocześnie lekkiego zderzaka (potrzebny miękki kontakt, limit szarpnięcia) i
   leżącej naczepy 30 t (potrzebny sztywny, żeby nie tonęła). Stała częstotliwość daje każdemu narożnikowi to samo
   osiadanie statyczne a/(2πf)². Sweep wartości: CLI runnera `--body-hz` / `--body-zeta`.
3. **Siodło widzi kontakt nadwozia**: `CombinationModel.External{Tractor,Trailer}{Force,Torque}` (rdzeń,
   `game/Assets/_Project/Vehicle/Physics`). Runner podaje siłę kontaktu z poprzedniego kroku, z opóźnieniem jednego
   kroku jak impulsy PhysX. Wartości domyślne są zerowe, więc jazda bez kontaktu nadwozia się nie zmienia.
4. **Limity penetracji wyprowadzone** zamiast „0”: szczyt przy uderzeniu bokiem 0,10 m
   (v/(e·ω) + n·g/ω² = 0,061 + 0,031 = 0,092 m dla v = 4,18 m/s), spoczynek 0,035 m (n·g/ω² = 0,031 m), zderzak na
   krawężniku 0,05 m. F1: `articulation_limit_excess_deg ≤ 3,5°` (D59), 3 scenariusze F1 wróciły z `scenarios_expected_fail`.
5. **Unity: PhysX ignoruje kontakty ciągnik–naczepa** (`VehicleBody.ConnectTrailer` → `Physics.IgnoreCollision` dla
   każdej pary koliderów; przywraca pary poprzedniej naczepy). Bryły sprzęga solver siodła, a runner nie ma kontaktu
   ciągnik–naczepa (parzystość). Asercja w PlayMode `CombinationLabTests.MassProperties_Trailer_IncludeCargo`.

## Liczby przed / po (runner .NET, dt 10 ms, 4 substepy)
| scenariusz / metryka | main (bez koliderów na krawężniku) | sztywny kontakt (ADR 0158) | k 1e6 N/m, c 5e4 | **4 Hz, ζ 1** | limit |
|---|---|---|---|---|---|
| kerb 27 cm @laden40, max_dv_step [m/s] | 0,193 (zderzak przenika jezdnię) | **0,572 FAIL** | 0,292 | **0,325** | 0,35 |
| kerb 27 cm, penetracja zderzaka [m] | — | ~0 | — | **0,038** | 0,05 |
| fulllock (wywrotka), max_dv_step [m/s] | 2,04 | 2,04 | 0,519 | **0,715** | 4,2 |
| fulllock, penetracja szczyt / leżenie [m] | 0,0004 | 0,0004 | **0,295** / — | **0,090 / 0,030** | 0,10 / 0,035 |
| free_fall_drop_comb, penetracja [m] | 0 | 0 | 0,028 | **0,025** | 0,05 |

Pełny pakiet: **Runner 132/132 PASS (750 checks)** (`artifacts/phys-0165/runner-run2.log`, przed: 129/129 na main
62ba224f5, k 1e6: 2/129 FAIL). **dotnet test 266/266** (`artifacts/phys-0165/dotnet-test.log`).

### Test energii przy zrzucie na bok
`BodyContactTests.Body_DroppedOnSide_ComesToRest_WithoutEnergyGain` padał z wynikiem „max step gain 189,96 J”.
Przyczyną jest miara, a nie przyrost energii. Przy podatnym kontakcie zachowuje się E = KE + PE + Σ½k·pen²
(`BodyGroundContact.SpringEnergy`). KE + PE rośnie tylko wtedy, gdy obciążona sprężyna się rozpręża. W krokach 147–149
KE + PE rośnie o +189 J/krok, a jednocześnie E_całk spada o −340 J/krok (`artifacts/phys-0165/droptest-diag.log`). Po
dodaniu energii sprężyn największy przyrost w kroku wynosi **0,000 J**. Tolerancja testu jest bez zmian (0,1 % m·g·1 cm + 1 J).

### Polowanie na wywrotki (siatka z ADR 0158)
72 biegi po 30 s: empty/cargo24/laden40 × gaz 0,2/0,4/0,6 × skręt ±1 × 20/30/40/50 km/h
(`artifacts/phys-0165/hunt/`, generator `gen_hunt.py`):

| wariant | wywrotki | spadki przez drogę | min CoM [m] | maks. prędkość | zysk E w locie | nadmiar przegubu | maks. dv | błąd siodła | penetracja szczyt |
|---|---|---|---|---|---|---|---|---|---|
| ADR 0158 (sztywny) | 36 | 0 | — | 50,6 km/h | 0 | 2,77° | 2,71 m/s | 36,9 mm | 0,0004 m |
| **ta gałąź** | 36 | **0** | 1,017 | 50,6 km/h | **0 J** | **2,77°** | **0,91 m/s** | **10,9 mm** | **0,131 m** |

Szczyt penetracji przekracza 0,10 m w 24 biegach (cargo24/laden40 przy 40–50 km/h, maks. 0,131 m). Zawsze dotyczy
narożnika dachu naczepy przy uderzeniu bokiem: wywrotka przy większej prędkości ma prędkość przechyłu 87–115°/s, więc
naroże na wysokości ~4 m uderza z prędkością ~8 m/s, a nie 4,18 m/s jak przy upadku z punktu równowagi. Z modelu
v/(e·ω) = 8,0/(e·25,1) = 0,118 m + obciążenie statyczne, co zgadza się z pomiarem. Szczyt trwa ~0,1 s, a w spoczynku
penetracja wynosi ≤ 0,030 m (wykres `artifacts/phys-0165/png/body_penetration.png`). Prawdziwa reling dachu firanki
zgniata się przy wywrotce o decymetry (UNVERIFIED). Limit 0,10 m w repro `fuzz_shrink_speed_runaway_fulllock` (30 km/h)
zostaje, bo dla tego scenariusza jest wyprowadzony.

### `--robustness`
Determinizm BIT-IDENTICAL (6 scenariuszy), 0 biegów z NaN, skoki pozycji ≤ 4e-14 m, soak 30 min dv ≤ 0,19 m/s
(`artifacts/phys-0165/robustness/robustness.md`). Kerb fuzz (40 biegów, ziarno 20261113): maks. dv 0,42 m/s i maks.
przegub 7,1° (bieg 38: próg 0,24 m przy 30 km/h). To nie jest scenariusz z limitem i nie ma tu kontaktu nadwozia, bo
próg leży niżej niż zderzak. Do sprawdzenia przez lidera przy porównaniu z main na tym samym ziarnie.

### Unity
EditMode (świeży worktree): 495 testów, 469 PASS, 8 FAIL, 13 skip. Wszystkie 8 porażek wymaga zbudowanych assetów
(„Build canonical truck…”, „build TRAKT…”, bake UV1, szkło latarni) i nie dotyczy fizyki. Testy fizyki/pojazdu przeszły:
19 PASS, 4 skip, 2 FAIL (te dwa to `MirrorPresentationTests`, brak assetu TRAKT). PlayMode (nowa asercja
IgnoreCollision, `KerbStrikeParityTests`) zleca lider.

Wykresy (`tools/telemetry/plot.py`, obejrzane): `artifacts/phys-0165/png/` — krawężnik 27 cm, fulllock, free fall,
najgorszy bieg polowania (laden40, 50 km/h), penetracja nadwozia w czasie.

## Konsekwencje
- Krawężnik 27 cm mieści się w limicie szarpnięcia. Na telefonie będzie twarde, ale jednorazowe uderzenie zderzaka
  (0,325 m/s w kroku), bez „ściany”.
- Leżący zestaw zapada się w jezdnię o ~3 cm. Na ekranie telefonu to poniżej grubości opony bocznej, ale do oceny w
  feel teście.
- Odczucie: przy wywrotce przy 50 km/h naroże dachu na ~0,1 s wchodzi w jezdnię do 13 cm. Bez iskier i deformacji
  wygląda to jak wgniecenie. Do oceny przez właściciela.

## Otwarte
- **Unity nie podaje `External*Force`** do `CombinationModel` (impulsy PhysX z `OnCollisionStay` / contact modification).
  Dopóki tego nie ma, siodło w Unity nie przewiduje kontaktu nadwozia, tak jak runner przed tą zmianą.
- Unity używa sztywnego kontaktu PhysX (BoxCollidery). Podatny kontakt w grze wymagałby contact modification albo
  własnego kontaktu nadwozia w adapterze. Parzystość krawężnika 27 cm runner ↔ Unity sprawdza `KerbStrikeParityTests`
  (PlayMode, lider).
- Brak kontaktu ciągnik–naczepa przy złożeniu ≥ 90° (kabina vs ściana czołowa) w obu implementacjach.
- Jedno źródło geometrii koliderów (runner kopiuje stałe z builderów Unity, ADR 0158).
- Nie ruszano zawieszenia ani odbojów (Mistral M40).
