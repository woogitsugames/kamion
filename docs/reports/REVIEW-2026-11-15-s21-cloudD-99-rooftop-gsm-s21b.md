# Przegląd PR #99 — M67 (K67) uzupełnienie s21b: kadry naziemne i proporcja do kondygnacji — s21 cloud D, 2026-11-15

**Werdykt: SCAL z erratą.** Uzupełnienie robi to, co obiecuje.
- 60 kadrów naziemnych jest obejrzanych i uczciwie sklasyfikowanych: 4 przypisane do wieżowca, reszta to negatywy z powodem.
- Pomiar proporcją do kondygnacji (metoda B) na wieżowcu daje niezależną drugą metodę obok LIDAR. Arytmetykę odtworzyłem dla 3 z 3 wierszy, a odczyt pikseli sprawdziłem na 2 wycinkach z linijką.
- **10 z 10 obejrzanych obrazów ma opis zgodny z obrazem.**
- Pakiet wnosi konkretny wniosek dla gry. Kadry KartaView z 2019 i 2021 rozstrzygają konflikt z ADR 0200 przy narożniku S wieżowca: nie stoi tam maszt kratowy 6,5 m, są tylko panele na elewacji (§4).

Errata:
- 93 wiersze manifestu mają status `VERIFIED_WIZJA`, którego README sam nie dopuszcza.
- Errata z przeglądu r2 (kadr Cieszyńska, „ciemnoszara sylwetka”) **nie została naniesiona**.
- Zdjęcia są w gicie. Wcześniejsza wersja tego katalogu została scalona w takiej samej formie, a blok M67 każe zrobić ZIP.

- Gałąź `origin/research/rooftop-gsm-s21` @ `ea8ac1318`: 2 commity (`bac47dd14`, `ea8ac1318`) na `efda3890a`, który jest już na `origin/main` (katalog `research/rooftop-gsm-s21/` scalony po r2).
- `git diff --stat origin/main...` daje 90 plików (+6928 / −8), wszystkie w `research/rooftop-gsm-s21/` ✓. Z tego 65 plików w `files/`: 49 miniatur Commons ≤ 960 px oraz 16 kadrów i wycinków KartaView.
- Manifest ma 148 wierszy (było 82). Nowe są K67-083…148, stare id bez zmian.
- Wcześniejsze przeglądy: `REVIEW-2026-11-15-s20-cloudB-rooftop-gsm.md` (FIX) i `REVIEW-2026-11-15-s20-cloudB-rooftop-gsm-r2.md` (SCAL z erratą).

## 1. Kompletność (MISTRAL-TASKS-10 §M67, GPT-CHROME-RESEARCH-S20 zad. 2, luka 1 z r2)
| Kryterium | Stan po s21b | Ocena recenzenta |
|---|---|---|
| katalog ≥ 8 typów z wymiarami i kolorem | 13 typów (bez zmian) | ✓ (r2) |
| ≥ 5 dachów z rozkładem min/mediana/max i metodą | 6 dachów, wszystkie ESTIMATED (LIDAR jako dolna granica). Na wieżowcu dodatkowo metoda B | ✓. Zmiana statusu LIDAR z „MEASURED” na ESTIMATED jest poprawna. **Nowe K67-148:** Zwierzyniecka 4 to maszt **radiowy UKF**, nie GSM (OSM, sprawdzone), więc rozkład „GSM” ma realnie 4 dachy z urządzeniami, z czego 3 z rozkładem |
| ≥ 15 obejrzanych kadrów | +60 naziemnych (KartaView 11, Commons 48, Panoramax 1) | ✓ |
| kadry naziemne i sylwetka na tle nieba (luka 1 z r2) | **CZĘŚCIOWO**: 4 kadry z instalacją, wszystkie z wieżowca. Pozostałe dachy mają 0 kadrów (pokrycie Panoramax 0, KartaView zasłonięte, Commons bez celu, geosearch z błędem 429) | uczciwie zgłoszone (K67-145…147). Luka zostaje dla innych dachów |
| odsyłacz do M57, bez powielania | ✓, metoda B dla wieżowca jest kontrolą, a nie nową lokalizacją | ✓ |
| brak nazw producentów i operatorów w opisach | ✓ (operator A/B/C; marki maszyn w tle nieopisane) | ✓ |
| samokontrola ≥ 20 % | r3: 14 z 66 nowych (seed 2026111521), 13 PASS / 1 FIX (K67-137) | ✓ |
| tylko własny katalog | ✓ | ✓ |
| errata r2 (Cieszyńska) | **nienaniesiona** (README l. 107 bez zmian) | E2 |
| statusy SOURCED / ESTIMATED / UNVERIFIED | README tak deklaruje, ale manifest ma `VERIFIED_WIZJA` ×93 (59 nowych), `SOURCED_SECONDARY` ×2, `VERIFIED` ×2 | E1 |

## 2. Obejrzane obrazy (10, każdy osobno ≤ 960 px)
| Plik | Licencja | Ocena opisu |
|---|---|---|
| `kv_1326673605.jpg` (K67-083, pełny kadr) | CC BY-SA 4.0 (KartaView) | ✓ estakada, po prawej żółta górna część wieży nad drzewami, maszty na dachu |
| `kv_1326673605_wyc3x.jpg` | jw. | ✓ **zgodne w każdym elemencie**: wysoki maszt kratowy przy lewym końcu z białymi czaszami i odciągami, najwyższy maszt kratowy w środku z zastrzałami, między nimi krótkie wsporniki z białymi panelami, przy prawym końcu 4–5 krótszych masztów z panelami i czaszą. **Na lewym narożniku tylko drobne elementy na elewacji, około linii attyki** |
| `kv_1326673605_pomiar.jpg` (linijka) | jw. | ✓ mój odczyt: szczyt masztu środkowego / attyka / rozstaw pasm okien daje ≈ 182 : 63 px w podglądzie, czyli ≈ 2,9 kondygnacji. Zgodne z K67-094 (2,78–2,90) |
| `kv_1326673581_pomiar.jpg` | jw. | ✓ szczyt ≈ 1201, attyka ≈ 1288, pasma okien ≈ 29–30 px (z linijki), co daje 2,9–3,0 kondygnacji. Zgodne z K67-094 (87/30) |
| `kv_993062010_wyc3x.jpg` (K67-085, 2019) | jw. | ✓ ten sam układ: 2 wysokie maszty, 3 grupy białych paneli na krótkich wspornikach, czasze. Na lewym narożniku elementy na elewacji, bez masztu kratowego |
| `kv_993061738_wyc4x.jpg` (K67-086) | jw. | ✓ wieża za liśćmi. Nad attyką białe czasze (kropki) i cienkie szare kreski, wysokie maszty zasłonięte |
| `commons_s21b_7ecfa0059e_wyc3x.jpg` (K67-133) | CC0, Rakoon ✓ (API) | ✓ akademiki z ceglastymi cylindrycznymi klatkami i pionowym napisem uczelni. Na dachu najwyższego bloku 2 cienkie pręty. Identyfikacja jako Kopernika 5A jest uczciwie UNVERIFIED |
| `commons_s21b_5405ad7230.jpg` (K67-118) | CC0 ✓ | ✓ ulica z kostki, kamienice i domy, masztów brak |
| `commons_s21b_c629710ddd.jpg` (K67-127) | CC0 ✓ | ✓ drewniany dom i nowy blok, masztów brak |
| `commons_s21b_09038367d5.jpg` (K67-101) | CC0 ✓ | ✓ baner inwestycji na drewnianym ogrodzeniu, celu brak |

Licencje: 4 z 4 sprawdzonych plików Commons są CC0 według `extmetadata`. KartaView ma CC BY-SA 4.0, a autor jest podany jako „nazwa niepodana w API”. R2 (#62) podaje `userId 479` dla tej samej sekwencji 3686129, więc można to uzupełnić (E4). Google nie występuje.

## 3. Liczby sprawdzone u źródła (8)
- **KartaView API** (sekw. 3686129, strona 2): 1326673605 → (53,151072; 23,169827), heading 301,47, 2021-06-23 10:34:19 ✓. 1326673581 → (53,150468; 23,171384), 303,07, 10:34:13 ✓ (K67-083/084).
- **Spójność geometrii (wyliczenie recenzenta):** z par (odległość, kierunek do celu) w K67-083 (267 m, 333°), K67-084 (379 m, 324°) i K67-085 (248 m, 336°) wychodzi ten sam punkt wieży z rozrzutem < 5 m (≈ 53,15321 N, 23,16802 E) ✓.
- **Arytmetyka metody B:** K67-094: 128/46 = 2,78 i 87/30 = 2,90, × 3,5–3,8 m = **9,7–11,0** ✓. K67-095: 111/46 = 2,41 i 75/30 = 2,50, wynik **8,4–9,5** ✓. K67-096: 58–61/46 = 1,26–1,33, wynik **4,4–5,1** ✓ (1,33 × 3,8 = 5,05).
- **OSM API 0.6:** node 11285970200 ma `man_made=mast`, `tower:construction=guyed_tube`, `communication:radio=yes`, bez `communication:mobile_phone` ✓. Way 284157362: `building=dormitory`, `building:levels=11`, `height=34` ✓ (K67-148).

SOURCED / ESTIMATED: wszystkie wysokości są ESTIMATED z metodą (A LIDAR, B proporcja, C cień). Kondygnacja 3,5 m jako dolna granica ma status WORKING_VALUE. Statusów opisów kadrów dotyczy E1.

## 4. Wnioski dla gry (`Data/Regions/bialystok-industrial-c/overrides.yaml`, wpis wieżowca, `roof_masts`, ADR 0190/0200)
| Element (gra dziś) | s21b (metoda B, KartaView 2019 i 2021) | Działanie |
|---|---|---|
| maszt W: `lattice, u 0.20, height_m 9.5` | 8,4–9,5 m nad attyką, stopa zasłonięta, więc to dolna granica. LIDAR 2025 ≥ 10,95 | ✓ bez zmian (9,5 mieści się w obu) |
| maszt środkowy: `lattice, u 0.49, height_m 11.0` | 9,7–11,0 m (2019 i 2021). LIDAR 2025 w punkcie przy środku krawędzi SE daje 5,25 m, co jest **konfliktem**, którego pakiet nie rozstrzyga | ✓ zostaje 11,0. Konflikt z LIDAR zostaje UNVERIFIED (możliwy demontaż po 2021 albo inny punkt pomiaru). Rozstrzyga sesja zdjęciowa właściciela (pkt 6) |
| maszty NE: `lattice 5.0 / 4.6` | 4,4–5,1 m (K67-096) | ✓ zgodne |
| krótkie słupy SE: `pole 2.1–3.4` | 3 krótkie wsporniki z 1–2 panelami, 0,5–1 kondygnacji nad attyką (≈ 1,9–3,8 m, ESTIMATED z opisu) | ✓ zgodne |
| **narożnik S: `lattice, facing SW, u 0.90, height_m 6.5`** (ADR 0200: „CONFLICT … Height UNVERIFIED”) | na obu wycinkach (2021 `kv_1326673605_wyc3x`, 2019 `kv_993062010_wyc3x`) przy narożniku S **nie ma masztu kratowego**. Są białe panele przykręcone do elewacji, wystające nieznacznie ponad attykę (K67-083). To zgadza się z 073045 z ADR 0200 („only wall-mounted panels up to the attic line”) | **P2:** zamienić wpis 6,5 m `lattice` na panele ścienne (np. `pole`, `inset_m` ≈ 0, `height_m` ≈ 1,5–2,0 = WORKING_VALUE recenzenta, 2–3 panele). Rozstrzyga to otwarty konflikt ADR 0200 dwoma niezależnymi kadrami 2019 i 2021. Wymaga zmiany w `overrides.yaml` przez lidera lub agenta wieżowca, nie przez ten PR |
| wygląd z dystansu 250–380 m | panele białe/jasnoszare matowe, czasze białe jako najlepiej widoczne kropki, kraty szare, przez liście prawie znikają (K67-086) | LOD-y: czasze i panele zachować najdłużej, kraty i odciągi wyciąć wcześniej (zgodnie z r2 §3) |
| inne dachy (generator) | Zwierzyniecka 4 to maszt radiowy UKF na odciągach, nie GSM | przy losowaniu instalacji GSM na blokach nie brać Zwierzynieckiej jako wzorca stacji GSM. Rozkład GSM: maszt główny 7,7–11,6 m (Skorupska, Dobra, wieżowiec), wsporniki 2,5–5,3 m |

## 5. Errata (przy scaleniu albo w następnej paczce, nie blokuje)
1. **E1:** w manifeście status `VERIFIED_WIZJA` (93 wiersze), `VERIFIED` (2) i `SOURCED_SECONDARY` (2) zastąpić statusami dozwolonymi. Dla kadrów proponuję `SOURCED (obraz)`, tak jak w R2/R4/R6, a dla negatywów `SOURCED (obraz, cel niewidoczny)`. README §0 sam deklaruje 3 statusy.
2. **E2 (z r2, nienaniesiona):** README l. 107 i `commons_opisy.json`, kadr Cieszyńska: „na jasnym niebie wszystko czyta się jako ciemnoszara sylwetka” zmienić na „górna część wieży, panele i czasze jasne (biel/jasna szarość) na tle niebieskiego nieba zmierzchu; ciemniejsze tylko elementy w cieniu własnym”.
3. **E3 (proces, decyzja lidera):** blok M67 mówi „ZDJĘCIA NIE DO GITA … ZIP”. Katalog trafił na main z `files/` po r2, a s21b dokłada 65 plików. Albo świadoma akceptacja (miniatury ≤ 960 px, atrybucja w manifeście), albo `git rm --cached` nowych `files/*` przy scaleniu.
4. **E4:** autor KartaView („nazwa niepodana w API”): uzupełnić z `userId` w odpowiedzi `photo/?sequenceId=` (R2 #62 podaje 479 dla 3686129), bo CC BY-SA wymaga atrybucji.
5. **E5:** README §2a, wiersz Zwierzyniecka 4: dopisać, że rozkład „GSM” liczy tylko dachy z `communication:mobile_phone` lub z panelami sektorowymi. Zwierzyniecka (radio UKF, K67-148) idzie osobno.

## 6. Dla lidera
- **Scalić PR #99** (diff tylko w `research/rooftop-gsm-s21/`, 2 commity na main). E1–E5 można nanieść przy scaleniu albo w następnej paczce.
- Do gry: P2 dla narożnika S wieżowca w `roof_masts` (6,5 m lattice zamienić na panele ścienne) z dowodem K67-083/085. Pozostałe maszty gry mieszczą się w przedziałach metody B. Konflikt maszt środkowy vs LIDAR 2025 rozstrzyga sesja zdjęciowa właściciela.
