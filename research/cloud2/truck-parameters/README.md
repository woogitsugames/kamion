# R3 — parametry ciągnika 4x2 (~480 KM) + naczepy kurtynowej 13,6 m z otwartych źródeł

**Data:** 2026-11-14 · **Gałąź:** `research/cloud2-truck-parameters` · **Wierszy manifestu:** 157 (142 SOURCED, 11 ESTIMATED, 4 UNVERIFIED) · **Dokumentów otwartych:** 24 (+6 zablokowanych, tylko link) · **Kadrów zdjęciowych:** 0 (pakiet liczbowy); **stron PDF obejrzanych jako obraz:** 4 (R13 s. 43, AT2612 s. 3, ATO2612F s. 3, MB Powertrain s. 29) + 3 ponowne obejrzenia w samokontroli · **Samokontrola:** 33/157 wierszy (21 %, seed 20261114) — 1. przebieg 32 PASS / 1 FAIL (R3-153, przeliczenie jednostek w kolumnie „wartość”), po korekcie **33 PASS / 0 FAIL** (`audit_20_percent.json`).

Nie zmieniano kodu gry — tylko raport. Opisy przeznaczone do gry są bez marek: „ciągnik 4x2 klasy 13 l / 480–500 KM”, „AMT 12 OD”, „opona 315/80 R22.5”. Marki i modele występują wyłącznie w kolumnach `cytat`/`autor` jako identyfikacja źródła danych technicznych.

## Cel i metoda

Cel: zakresy realnych parametrów (min–max z 2–3 niezależnych źródeł) dla fizyki zestawu i porównanie z wartościami w grze (`game/Assets/_Project/Vehicle/Physics/Definitions/Data/*.json`, `docs/VEHICLE_REFERENCE_DATA.md` = VRD, `docs/PHYSICS_VALIDATION.md` = PV).

1. Przeczytane: docs/04, docs/07, VRD, PV, ADR fizyki (0004, 0014, 0019, 0024, 0082, 0134, 0151, 0176), research `mistral/p4-truck-regulations`, `gptpro/p4-truck-regulations`.
2. Źródła: akty prawne (96/53/WE skonsolidowana, 2020/740, UN R13 Rev.3 i 02/MLIT, FMVSS 121), karty techniczne producentów (silniki, skrzynie, mosty, ciągnik 4x2, naczepy, opony), prace dyplomowe z otwartego repozytorium Chalmers ODR. Bez Google/Bing, bez blogów i ogłoszeń sprzedaży.
3. `build_manifest.py` sprawdza automatycznie, że każdy cytat SOURCED występuje dosłownie w tekście pobranego PDF (pdftotext; `…` = pominięte kropki wypełniające w kartach) i zapisuje stronę PDF. Wartości z grafik (wykresy przełożeń, wzory R13) odczytano z wyrenderowanej strony, obejrzanej (`files/_view/`), co zaznaczono w kolumnie `metoda`.
4. `audit.py` — ponowne pobranie każdego wylosowanego dokumentu z `url_pliku` (świeża kopia, porównanie sha256), ponowne wyszukanie cytatu i liczb na stronie, ponowne obejrzenie stron-obrazów, ponowne przeliczenie wierszy ESTIMATED.

## Wynik główny — tabela „gra vs źródło”

Ocena: **OK** = w zakresie źródeł; **poza** = poza zakresem; **brak** = brak w grze / brak testu.

| Parametr | Gra (plik/dok.) | Zakres ze źródeł | Wiersze | Ocena | Rekomendacja |
|---|---|---|---|---|---|
| DMC zestawu | 40,0 t (laden40) | 40 t (96/53 zał. I 2.2.2 a; WT § 3) | R3-006 | OK | — |
| Długość / szer. / wys. | 16,47 / 2,55 / 4,00 m | ≤ 16,50 / 2,55 / 4,00 m | R3-001…003 | OK | — |
| Pierścień skrętu 12,50/5,30 m | brak testu | wymóg 96/53 pkt 1.5 | R3-004 | **brak** | dodać scenariusz walidacyjny zestawu 40 t w pierścieniu |
| Naciski laden40: przód / napęd / tridem | 6,62 / 10,76 / 22,62 t | ≤ 10 / ≤ 11,5 / ≤ 24 t (rozstaw 1,3–1,4 m) | R3-008…010 | OK | — |
| Rozstaw osi ciągnika | 3,70 m | 3,50–3,80 m | R3-011 | OK | — |
| Masa własna ciągnika (bez paliwa) | ≈ 6,90 t | 6,845–6,870 t (±3 %) | R3-012 | OK | — |
| **Rozkład nacisków solo (bez paliwa)** | **≈ 4,52 / 2,39 t (65/35 %)** | **5,03 / 1,82–1,84 t (73/27 %)** | R3-013, 014 | **poza** | przesunąć ~0,5 t w przód (zespół napędowy/kabina) — jedno źródło, traktować jako kierunek |
| Średnica zawracania (krawężnik) | ≈ 13,4 m (obliczona) | 13,4 m dla WB 3,7 (12,7–13,7) | R3-017, 018 | OK | — |
| Siodło przed osią napędową | 0,68 m | 0,375 m (jedno źródło) | R3-019 | **poza** | zostaje 0,68 m (ADR 0019, limit 16,50 m) albo krótszy zwis przedni modelu |
| Rozstaw kół przód / tył | 2,04 / 1,82 m | 2,046–2,153 / 1,802–1,910 m | R3-020, 021 | przód na granicy (−6 mm), tył OK | opcjonalnie przód 2,05–2,10 m |
| Wysokość siodła/sworznia | 1,15 m | 0,95–1,18 m (standard 1,10–1,18) | R3-027 | OK | — |
| **Masa własna naczepy** | **7,0 t** | **5,99–6,56 t standard; 4,98–7,81 t cała rodzina** | R3-028…031 | OK (górna część) | rozważyć 6,3–6,6 t |
| Sworzeń → środkowa oś naczepy | 7,70 m | 7,70 m | R3-034 | OK (dokładnie) | — |
| Rozstaw osi tridem | 1,31 m | brak karty z liczbą; prawo 1,3 < d ≤ 1,4 m | R3-036 | OK (prawnie) | UNVERIFIED |
| Nośność sworznia / osi naczepy | 9,88 t / 7,54 t na oś | 12 t / 27 t (3 × 9 t) | R3-032, 033 | OK | — |
| Silnik: moment / moc | 2500 Nm @ 980–1270; 368 kW @ 1530–1800 | 2300–2500 Nm (start plateau 900–1100 rpm); 338–375 kW @ 1400–1800 (4 karty, 3 producentów) | R3-039…042, 048, 049 | OK | — |
| Hamulec silnikowy | 375 kW @ 2300 | 375 kW; rodzina do 480 kW; sama przepustnica 200 kW | R3-046, 047, 050 | OK | opcjonalnie stopień „tylko przepustnica” 200 kW |
| Retarder | 4000 Nm / 600 kW | 3500–4000 Nm / 600–700 kW | R3-052, 053 | OK | — |
| Przełożenia AMT 12 OD | 12,92 … 0,77; R 12,03 | identyczne (karta); inne AMT: 11,64–14,94 (1. bieg), 0,775–1,00 (12.) | R3-054…103 | OK | — |
| Przełożenie mostu | 3,40 | 2,38 (direct) … 3,61 (OD) … 3,70 | R3-104…106 | OK | — |
| Obroty przy 85 km/h, 12. bieg | 1158 rpm (r 0,51) | pasmo optimum 1100–1300 rpm; z r_dyn 0,524 → 1127 rpm | R3-107, 045 | OK | — |
| **Promień toczenia 315/80 R22.5** | **0,510 m** | **0,521–0,528 m** (obwód 3272–3319 mm, 3 karty) | R3-107…109, R3-117 | **poza (−2…−3 %)** | radius ≈ 0,52 m (kinematyka); statyczny 0,50–0,51 m tylko dla kontaktu |
| **Promień toczenia 385/65 R22.5** | **0,515 m** | **0,520–0,526 m** | R3-114…116, R3-118 | **poza (−1…−2 %)** | radius ≈ 0,52 m |
| Rozmiar opon prowadzących/napędowych | 315/80 R22.5 | docs/04 §2.4 wymienia 315/70 (r_dyn 0,492–0,497 m) | R3-110…113, R3-119 | niespójność dokumentacji | zdecydować (ADR): 315/80 albo 315/70 |
| Nośność / Fz0 opon | Fz0 30 / 35 kN | LI 156 = 4000 kg, 160 = 4500 kg, 164 = 5000 kg | R3-120…124 | OK | S6 w VRD → potwierdzone przez kartę |
| **Sztywność pionowa opony** | **1,0e6 / 1,1e6 N/m** | **0,880 (315/80) / 1,033 (385/65) MN/m** (dane opon via praca dypl.) | R3-125…127 | 315/80 **poza (+14 %)**, 385/65 OK (+6 %) | 0,88e6 / 1,03e6 N/m |
| Współczynnik sztywności bocznej | 7,0 1/rad | 7,4 (N/rad)/N | R3-128 | OK | — (jedno źródło, wartość modelowa) |
| Relaksacja boczna / μ szczytowe | 0,50 m / 0,80 | 0,4 m / 0,8 | R3-129, 130 | OK | — |
| Współczynniki MF B,C,D,E z pomiaru | Cx 1,65, Cy 1,35, Ey −0,5 | brak otwartego źródła | R3-132 | brak | pozostaje WORKING_VALUE |
| Opór toczenia | 0,0055 / 0,0050 | klasy C3: A ≤ 4,0; B 4,1–5,0; C 5,1–6,0; D 6,1–7,0; E ≥ 7,1 N/kN | R3-133…138 | OK (klasa C / B) | — |
| **R13 N3 typ-0** | MFDD 7,07–7,48 m/s²; 80→0: 34,9–40,5 m | **60 km/h; s ≤ 0,15v + v²/130; dm ≥ 5,0 m/s²** (→ ≤ 61,2 m z 80 km/h) | R3-139…144 | OK | VRD S5: „N3 type-0 UNVERIFIED” → teraz SOURCED (Rev.3, 1996) |
| R13 typ-0 z podłączonym silnikiem | brak testu | 90 km/h; s ≤ 0,15v + v²/103,5; dm ≥ 4,0 | R3-142 | **brak** | scenariusz 90→0 (40 t): ≤ 91,8 m |
| Naczepa O4 — siła hamowania | brak testu osobno | ≥ 45 % obciążenia kół (laden i unladen) | R3-145 | brak | opcjonalny test samej naczepy |
| Ciśnienie na głowicach | 8,5 / 7,5 bar | 6,5–8,5 bar | R3-146 | OK | — |
| Czasy zadziałania | 0,25 / 0,31 / 0,53–0,54 s | ≤ 0,6 s (oś najmniej korzystna, 75 % siłownika); głowica 75 % ≤ 0,4 s; naczepa ≤ 0,4 s od 0,65 bar | R3-147…150 | OK | — |
| Hamulec pomocniczy / postojowy | 33,1 m z 60 km/h; 12 % | dm ≥ 2,2 m/s²; 18 % (pojazd), 12 % (zestaw) | R3-151, 152 | OK | dodać test 18 % dla ciągnika solo |
| Droga hamowania (USA, regulacja) | ≈ 50 m z 96,6 km/h (ESTIMATED) | ≤ 250 ft (76,2 m) z 60 mph, ciągnik obciążony | R3-153 | OK | — |
| Zmierzone drogi hamowania zestawu 40 t z EBS | 34,9–40,5 m | **brak** (źródła pomiarowe 403) | R3-154 | brak | pozyskać lokalnie (NHTSA 812176) |
| Częstotliwość własna nadwozia | 1,3 / 1,5 Hz | 1,32 Hz (symulacja, praca dypl.) | R3-155 | OK | — (jedno źródło, nie pomiar) |
| Masa nieresorowana | — | 12,05 Hz | R3-156 | brak | — |
| Skoki zawieszenia | 0,18 / 0,20 m | brak w otwartych kartach | R3-157 | brak | WORKING_VALUE |

## Co już było w repo / co nowe

| Temat | Było | Nowe w R3 |
|---|---|---|
| Wymiary i masy 96/53/WE | P4-123…P4-138 (mistral p4), VRD „96/53 UNVERIFIED” | ponownie potwierdzone w tekście skonsolidowanym z numerem strony (R3-001…010) — VRD może zmienić status „text UNVERIFIED” na SOURCED |
| Silnik, skrzynia, retarder | S1, S2 w VRD (jedna karta każdy) | 2–3 niezależne karty dla każdego (R3-039…103) |
| R13 | S5: N3 typ-0 UNVERIFIED | N3 typ-0 (obie wersje), O4 45 %, ciśnienia głowic, czasy z zał. 6 — SOURCED |
| Opony | S7 (jedna karta), LI UNVERIFIED | 3 karty × 3 rozmiary, promień toczenia, LI z tabel nośności, sztywność pionowa, klasy RRC 2020/740 |
| Ciągnik/naczepa: masy, rozstawy | WORKING_VALUE | karta ciągnika 4x2, karty naczep (rozstaw 7,70 m, sprzęg 0,95–1,18 m, masa własna) |

## Luki (UNVERIFIED / brak)

1. **Zmierzone drogi hamowania** zestawu 40 t z EBS — raporty NHTSA/FHWA/MDPI zablokowane (403) w tej sesji; do pozyskania w sesji z przeglądarką.
2. **Współczynniki Magic Formula z pomiaru** opon 22,5″ — brak w otwartym dostępie (UMTRI Deep Blue za Cloudflare; dane TNO płatne).
3. **Rozstaw osi tridem 1,31 m** — brak karty z liczbą (tylko przedział prawny).
4. **Częstotliwości zawieszeń i kabiny z pomiaru**, skoki zawieszeń — tylko jedna wartość symulacyjna.
5. **UN R13 w najnowszej serii** — otwarto Rev.3 (1996, seria 08) i 02/MLIT; wartości typ-0 N3 niezmienne w tych wersjach, ale serie 09–11 nieotwarte (unece.org 403, EUR-Lex 2016/194 za wyzwaniem JS).
6. Rozkład nacisków ciągnika i położenie siodła — tylko jedna karta producenta.

## Jak używać w grze

- Liczby do JSON: kolumny `wartość` / `rekomendacja` w `manifest.csv`, filtr `ocena` zaczynający się od „poza” lub „brak”. Zmiany w kodzie/danych wykonuje lider po decyzji (ADR) — ten pakiet nic nie zmienia.
- Priorytet (moja ocena): (1) promień toczenia opon 0,52 m, (2) rozkład nacisków solo, (3) sztywność pionowa 315/80, (4) testy: pierścień 12,5/5,3 m, 90→0 z silnikiem, postój 18 % solo, (5) decyzja 315/80 vs 315/70.
- Status do VRD: S5 typ-0 N3 → SOURCED (R3-139…141); S6 LI → potwierdzone (R3-120…123); 96/53 „text UNVERIFIED” → SOURCED (R3-001…010).

## Pliki

- `manifest.csv` — 157 wierszy; dodatkowe kolumny: `strona_pdf`, `plik`, `wartość_w_grze`, `źródło_w_grze`, `ocena`, `rekomendacja`. Kolumny `lat/lon/kierunek_deg` = n/d (brak kadrów). `duplikat_sha256` puste — wiele wierszy celowo cytuje ten sam dokument (sha256 w kolumnie `sha256`).
- `sources.md` — lista dokumentów, status prawny, źródła zablokowane.
- `fetch.py` — pobiera 24 pliki (≈ 70 MB) do `files/` i sprawdza sha256 (exit ≠ 0 przy niezgodności).
- `build_manifest.py` (+ `sources_def.py`, `textcheck.py`) — generuje manifest i weryfikuje cytaty.
- `audit.py`, `audit_manual.json`, `audit_20_percent.json` — samokontrola.
- `STATUS.md` — dziennik kroków.

Odtworzenie: `python3 -I fetch.py && python3 -I build_manifest.py && python3 -I audit.py`.
