# Przegląd PR #61 — R3 truck-parameters (cloud2) — s20, 2026-11-14

**Werdykt: SCAL** (z dwiema drobnymi uwagami redakcyjnymi, które nie blokują). Recenzja wewnętrzna (`REVIEW.md`) wskazała cztery P1 i wszystkie są poprawione w gałęzi. Liczby sprawdziłem sam na rastrze źródeł (R13 Rev.3 s.43, MLIT s.27–31) i arytmetycznie: 36,7 / 60,9 / 33,8 / 52,4 / 61,2 m. Zgadzają się. Wnioski „gra vs źródło” też się zgadzają z JSON-ami gry.

- Gałąź `origin/research/cloud2-truck-parameters` @ `9c3e381b9` (PR #61, OPEN, nie draft). Commit z poprawkami P1 to `9c3e381` (17:38 UTC).
- `git diff --stat main...`: 13 plików, wyłącznie w `research/cloud2/truck-parameters/`. Są tekstowe, `.gitignore` = `files/` ✓.
- `python -I fetch.py` z pustego `files/`: **24/24 OK, 70,1 MB, 0 błędów sha256** (exit 0). Manifest ma 162 wiersze.
- Nic nie scalono, nic nie scommitowano, PR bez komentarza.

## 1. P1 z REVIEW.md — czy naprawdę poprawione

| P1 | Wymóg | Stan na `9c3e381` | Wynik |
|---|---|---|---|
| 1 | Próba z podłączonym silnikiem: 72→0 ≤ 60,9 m, dm ≥ 4,0; dodać 60→0 ≤ 36,7 m; 80→0 = ekstrapolacja | README l.52–53: „72 km/h; s ≤ 0,15·72 + 72²/103,5 = 60,9 m”, „60→0 ≤ 36,7 m”, „80→0 ≤ 61,2 m to tylko **ekstrapolacja**”. Nowe wiersze R3-158 (ESTIMATED, rachunek jawny) i R3-160 | **TAK**. Policzyłem sam: 10,8 + 5184/103,5 = 60,89; 9 + 3600/130 = 36,69; 12 + 6400/130 = 61,23 ✓ |
| 2 | Awaryjne N: /115, N3 z 40 km/h; resztkowe 2.4.1 ≤ 52,4 m; errata VRD S5 / PV w.6 | R3-151 (cytat EN „0.15 v + (2v2/115) … dm = 2.2”), R3-161 (resztkowe N3 40 km/h, 1,3), R3-162 (N3 40 km/h). README l.57 i l.91 zawierają erratę dla docs | **TAK**. Obejrzałem MLIT s.29 (EN: /115; JA: /130, rozbieżność w samym PDF) i s.31 (tabela 2.4.1: N3 40, (100/30)·v²/115, 1,3) ✓. Rachunek: 6 + 3200/115 = 33,83; 6 + 3,333·1600/115 = 52,38 ✓ |
| 3 | Drugie źródło typ-0 (MLIT s.27–28) w manifeście; luka 5 przeformułowana | R3-159/160 SOURCED z adnotacją „obraz obejrzany s.27–28”. README l.80: „Sprawdzono Rev.3 (1996, seria 08) i tekst MLIT (seria 10): liczby identyczne; serii 11 nie otwarto” | **TAK**. Obejrzałem s.27 (v N3 60 km/h) i s.28 (0,15v + v²/130, 5,0; 0,80 vmax, N3 90 km/h; 0,15v + v²/103,5; 4,0; F ≤ 70 daN) ✓. `pdftotext` znajduje w PDF „10 series of amendments” (przykład znaku homologacji) ✓ |
| 4 | Kolumny naczepy MEGA / STANDARD / MAXIMA | R3-037 = STANDARD 2750–2800. README l.32: „MEGA 0,95/0,98; STANDARD 1,05–1,15; MAXIMA 1,10–1,18”. l.33: „MEGA/STANDARD 6,24 t, MAXIMA 6,56 t” | **TAK**. Obejrzałem kartę s.3: STANDARD = K.SCS X+, sprzęg 1.050–1.100–1.150, wysokość wewn. 2.750–2.800, tara 6.240; MAXIMA = K.SCX: 1.100–1.150–1.180, 2.690–2.710, 6.560 ✓ |

Recenzja zgłosiła też dziesięć uwag P2. Według STATUS wykonawca poprawił P2-1 (marki usunięte z `przedmiot`: README l.5 ma teraz poprawny opis kolumn), P2-2, P2-3, P2-4, P2-5, P2-8 i P2-9. Sprawdziłem sam:
- grep nazw marek w kolumnie `przedmiot` wszystkich 162 wierszy daje 0 trafień;
- `sources.md` nie zawiera już KASS22.

Pozostałych P2 nie sprawdzałem pojedynczo.

**Uwagi redakcyjne (nie blokują):**
- (a) Ten sam PDF MLIT jest opisany jako „R13 (02)” (R3-151, R3-161, R3-162, README l.57/91) i jako „seria 10” (R3-159/160, README l.80). Numer „02” pochodzi z nazwy pliku, a seria wynika z tekstu („10 series of amendments”). Warto to ujednolicić. Ta sama pomyłka „02 series” siedzi w `docs/VEHICLE_REFERENCE_DATA.md:22` (S5).
- (b) Przedział obwodu 315/80 (3272–3319 mm) bierze po jednej linii z każdej karty. Ta sama tabela Dunlop s.34 ma dla 156/150 zakres 3294–3324 mm, a górna granica r = 0,529 m. Wniosek się nie zmienia.

## 2. Tezy zlecone przez lidera

### 2a. Promień toczenia
- Gra: `game/Assets/_Project/Vehicle/Physics/Definitions/Data/tire_315_80_r22_5.tire.json:5` `"radius": 0.51`. 385/65 ma 0,515.
- Źródła (obejrzane):
  - Dunlop s.34: 315/80 SP346 156/150 L, Ø 1084 / stat. 502 / obwód 3294;
  - Bridgestone M-STEER: 315/80 156/150 K, Ø 1092 / stat. 507 / obwód 3319 „@ 90 km/h”;
  - z obwodów r_toczenia = 0,521–0,528 m (R3-117, ESTIMATED; rachunek się zgadza).
- **Jak gra używa promienia** (moja analiza kodu, ESTIMATED; do potwierdzenia przez vehicle-physics):
  - `WheelGroup.cs:50` `Radius = tdef.radius` to jedna wartość do kinematyki (`ω·r`, l.367), momentu (l.344) i oporu toczenia (l.428);
  - jest też geometrią kontaktu: `s = hit.Distance − r·cos` (UpdateContact, ~l.141). Ugięcie opony jest liczone szeregowo z zawieszeniem: „solve F = f_susp(s_geo + F/k_tire)”, `TireDeflection = F/kt` (~l.172–185). Punkt mocowania ma wysokość `radius + SStatic − tireDefl` (l.61). Model traktuje więc `radius` jak **promień swobodny**, a promień pod obciążeniem wynosi `r − F/k`;
  - przy jednym obciążeniu, nominalnym 4000 kg (39,2 kN) i k = 1,0e6 N/m: gra 0,51 − 0,039 = **0,471 m**, karty 0,502–0,507 m (Dunlop s.34, M-STEER). Różnica ~3 cm;
  - VRD (`docs/VEHICLE_REFERENCE_DATA.md`, sekcja Tire 315/80) opisuje to jako świadome uproszczenie: „single value for both uses”.
- **Wniosek:** 0,51 m jest za małe dla kinematyki (−2…−3 %: prędkościomierz, obroty, przełożenia). Jeśli powyższy odczyt kodu jest poprawny, jest też za małe jako promień swobodny geometrii: koło pod obciążeniem siedzi ~3 cm niżej niż w kartach. Rekomendacja pakietu („radius ≈ 0,52 m kinematyka; statyczny 0,50–0,51 tylko dla kontaktu”) wskazuje dobry kierunek, ale w tym modelu kontakt prawdopodobnie potrzebuje promienia swobodnego, a nie statycznego. To **pytanie do vehicle-physics**: rozdzielić promień toczenia i promień geometryczny. Wymaga to ADR, ponownego `physics-validation` (wszystkie liczby PV się przesuną) i regeneracji tabel w VRD. Samo podbicie 0,51 → 0,52 też przesuwa PV.

### 2b. Rozkład nacisków 65/35 vs 73/27
- Gra: `tractor_4x2_generic.vehicle.json` ma 9 elementów masy, razem 7500 kg, w tym `fuel_tanks_partly_full` 600 kg przy z = 1,8. Oś przednia jest przy z = 3,7, tylna przy z = 0.
- Mój rachunek momentów:
  - z paliwem: 4812 / 2688 kg (64/36);
  - **bez paliwa (6900 kg): 4520 / 2380 kg (65,5/34,5)**. Zgadza się z pakietem (4,52 / 2,39 t, README l.28).
- Karta (obejrzana, FH 42T 3A s.1), WB 3700: oś przednia 5030, tylna 1835, kerb 6865 kg (73/27). Nota karty: „includes oil, water, AdBlue, 0 litres fuel and without driver. Kerb weight can vary ± 3 %”. Porównanie jest więc uczciwe: oba stany bez paliwa i bez kierowcy, ten sam rozstaw. To jedno źródło, co pakiet zaznacza.
- **Wniosek:** gra ma ~0,5 t za mało na przedniej osi. Dla laden40 przód urośnie do ≈ 7,1 t (limit tabliczkowy 7,5 t z tej samej karty), a napęd straci. To wpływa na trakcję i hamowanie, więc PV też trzeba powtórzyć. Rekomendacja: przesunąć masę kabiny lub zespołu napędowego do przodu, z ADR i PV.

### 2c. Opony 315/70 (docs/04) vs 315/80 (dane gry)
- `docs/04_FIZYKA.md:19`: „Parametry dla opon ciężarowych (np. 315/70 R22.5 prowadzące/napędowe, 385/65 R22.5 naczepa)”.
- Gra: `tire_315_80_r22_5.tire.json`, VRD S4/S7 i karta ciągnika („Front/Drive Axle Tyres: 315/80R22.5”, obejrzane) mają 315/80.
- **Wniosek:** to miękka niespójność, bo docs/04 podaje tylko przykład. Należy poprawić docs/04 na 315/80 (lider, jednym zdaniem w ADR fizyki lub w docs/04). Gry nie zmieniać, bo 315/80 jest lepiej uźródłowione. Dla porównania 315/70 ma r_toczenia 0,492–0,497 m (R3-119, ESTIMATED z obwodów 3093–3129 Dunlop s.34 ✓).

### 2d. Nazwy marek w danych gry (wskazane pliki)

| Plik:linia | Treść |
|---|---|
| `game/Assets/_Project/Vehicle/Physics/Definitions/Data/amt12_od_traxon_class.gearbox.json:3` | `"id": "amt12_od_traxon_class"` |
| jw. `:4` | `"description": "… Ratios = ZF TraXon standard 12-speed ratio set (ZF product data sheet …)"` |
| `…/Data/diesel_r6_13l_368kw.engine.json:4` | `"description": "… VEB+ engine-brake rating from the Volvo D13K500 fact sheet …"` |
| `…/Data/tractor_4x2_generic.vehicle.json:6` | `"gearboxId": "amt12_od_traxon_class"` |
| `game/Assets/_Project/Editor/Setup/DrivingLabSceneBuilder.cs:271` | ścieżka `amt12_od_traxon_class.gearbox.json` |
| `tools/physics-runner/Tests/ParamComparisonTests.cs`, `ValidationTests.cs` | odwołania do id `amt12_od_traxon_class` |
| `game/Assets/_Project/Rendering/Runtime/Truck/ContactShadowCaster.cs:58` | komentarz „photo Volvo FH” |

Pliki opon i naczepy są czyste. Trafienia binarne grepa (PNG, WAV, `.bytes`) są fałszywe, to przypadkowe bajty. **Wniosek:** marki w `id` i `description` nie są widoczne dla gracza, ale łamią zasadę „bez marek” w danych gry (CLAUDE.md, zasada 8). Proponuję zadanie lidera:
- id `amt12_od_class` (zmiana nazwy pliku razem z `.meta` przez `git mv`, bez kasowania `.meta`, plus 3 odwołania wyżej);
- opisy w stylu „class reference: see docs/VEHICLE_REFERENCE_DATA.md S…”;
- provenance z markami zostaje w VRD (dokument źródeł, nie dane gry).

## 3. Moja kontrola (10 obrazów, ≥ 5 liczb u źródła)

| # | Obraz | Sprawdzone | Wynik |
|---|---|---|---|
| 1 | karta ciągnika s.1 | WB 3500–3800; osie 5030 / 1815–1840; kerb; Ø zawracania 13 400 (WB 3700); 7500/11 500 tabliczkowe; opony 315/80; nota o paliwie | ✓ R3-011, 013, 014, 016, 017 |
| 2 | R13 Rev.3 s.43 | N3: 60 km/h, 0,15v + v²/130, 5,0; silnik podłączony 90 km/h, v²/103,5, 4,0; F 70 daN | ✓ R3-139…142 |
| 3 | MLIT s.27 | v N3 60 km/h (pkt 2.1.1) | ✓ R3-159 |
| 4 | MLIT s.28 (wycinek EN) | wzory typ-0, vmax N3 90 km/h | ✓ R3-159/160 |
| 5 | MLIT s.29 | 2.2.1: N: 2v²/115, dm 2,2 (EN); JA: /130 | ✓ R3-151, errata VRD |
| 6 | MLIT s.31 | 2.4.1: N3 40 km/h, (100/30)·v²/115, 1,3 | ✓ R3-161 |
| 7 | karta naczepy s.3 | MEGA/STANDARD/MAXIMA: sprzęg, wysokość wewn., tara | ✓ R3-027, 028, 037 |
| 8 | Dunlop s.34 | 315/80 i 315/70: Ø, stat., obwody; 385/65 | ✓ R3-108, 119 |
| 9 | Bridgestone M-STEER | 315/80: 1092 / 507 / 3319; 385/65: 1086 / 502 / 3302 | ✓ R3-109, 115 |
| 10 | Karisaari tab. 7 s.32 | CZT 315/80 = 880,3 kN/m @ 850 kPa; 385/65 = 1033,4 @ 900 | ✓ R3-125/127 (gra 1,0e6: +14 %) |
| + | TraXon s.4 | 2610: 12,92 … 1,00 / 0,77; R 12,03 | ✓ R3-059 i gearbox JSON (most 3,40 → 12. bieg 1158 rpm przy 85 km/h, r 0,51: 85/3,6/0,51 · 3,40 · 0,77 · 60/2π = 1158 ✓) |

Licencje i zakazy: karty producentów są w manifeście jako referencja danych technicznych i nie trafiają do gita. Grep google/bing/yandex/apple/mapillary daje 0 trafień. Źródła zablokowane (403) mają tylko status UNVERIFIED. User-Agent `Mozilla/5.0 (research fetch)` jest ogólny ✓.

## 4. Wnioski dla gry (lider → vehicle-physics, dokumentacja)

1. **Errata docs (bez zmiany fizyki):**
   - `docs/VEHICLE_REFERENCE_DATA.md:22` (S5): „2 v²/130” → „2 v²/115” (kat. N). N3 to 40 km/h. „02 series” → „tekst zawiera przykład 10 series”. Typ-0 N3 może przejść z UNVERIFIED na SOURCED (Rev.3 s.43 + MLIT s.27–28);
   - `docs/PHYSICS_VALIDATION.md:110` (PV w.6 `air_leak_rear_circuit`): limit „≤ 64,4 m z 60 km/h” → właściwy jest pkt 2.4.1, resztkowe N3 obciążony 40 km/h ≤ 52,4 m, dm ≥ 1,3 (albo awaryjne 40 km/h ≤ 33,8 m). Gra (33,1 m z 60 km/h) przechodzi oba z zapasem;
   - `docs/04_FIZYKA.md:19`: 315/70 → 315/80.
2. **Nowe scenariusze PV:** 60→0 ≤ 36,7 m (silnik odłączony, 40 t i solo), 72→0 ≤ 60,9 m (silnik podłączony), awaria obwodu 40 km/h ≤ 52,4 m, postój 18 % solo.
3. **Zmiany parametrów** (każda z ADR i ponownym `physics-validation`; kolejność wg wpływu):
   - promień: toczenie ~0,524 m; promień geometryczny ustala vehicle-physics po potwierdzeniu modelu kontaktu (§2a);
   - masa: ~0,5 t do przodu (§2b);
   - sztywność pionowa 315/80: 1,0e6 → 0,88e6 N/m (385/65: 1,1e6 → 1,03e6);
   - tara naczepy 7,0 → 6,2–6,6 t (opcjonalnie).
4. **Marki w danych gry:** zadanie porządkowe z §2d (id skrzyni, 2 opisy JSON, 3 odwołania, komentarz w `ContactShadowCaster.cs:58`).
