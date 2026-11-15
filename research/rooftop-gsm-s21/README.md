# K67 (blok M67) — dachowe instalacje GSM: geometria elementów

Sesja chmurowa s21, 2026-11-15. Gałąź `research/rooftop-gsm-s21` (PR #89). Wersja **FIX r2** — poprawki z
`docs/reports/REVIEW-2026-11-15-s20-cloudB-rooftop-gsm.md` §5.

## 0. Kryteria M67 — stan po FIX r2

| kryterium | stan | dowód |
|---|---|---|
| katalog ≥ 8 typów z wymiarami i kolorem | **SPEŁNIONE** | §1, K67-001…013 (13 typów, 6 z kart) |
| ≥ 5 dachów z rozkładem wysokości masztu (min / mediana / max, z metodą) | **SPEŁNIONE** | §2: 5 dachów z pomiarem LIDAR (Skorupska 17, Dobra 3, Zwierzyniecka 4, Kopernika 5A/7, wieżowiec M57 jako kontrola) + Hallera 19 jako zmierzony negatyw; 23 pomiary K67-036…058 |
| ≥ 15 obejrzanych kadrów | **SPEŁNIONE** (ortofoto 16 + 7 nowych wycinków + 6 map LIDAR + 23 profile boczne LIDAR + 9 naziemnych) | §5 |
| — w tym kadry naziemne / sylwetka na tle nieba | **CZĘŚCIOWO**: 9 kadrów Commons (5 negatywów dachów, 1 wieża wolnostojąca, 3 ulice Dobra/Kopernika — cel poza kadrem); kadrów z boku dachów z masztami 0 (Zwierzyniecka 2× nadal 429) | §3, §6 |
| odsyłacz do M57 bez powielania | **SPEŁNIONE**, wysokości wg M57-FIX #88: **9–12 m** | §2 |
| brak nazw producentów/operatorów w opisach | **SPEŁNIONE** (operatorzy A/B/C) | manifest |

## Uzgodnienie z M57
Uzupełnienie M57; lokalizacji ani układu masztów na wieżowcu przy Andersa nie powtarzam. Przyjmuję wysokości po
**M57-FIX (#88): maszt główny 9–12 m nad dachem**, maszty ok. 4–6 m przy końcu NE, maszt W z odciągami, panele wzdłuż SE.
Kontrola krzyżowa z LIDAR 2025-04-18 (tylko liczby, bez układu): najwyższy maszt (z odciągami, koniec SW / narożnik W)
**≥ 10,95 m**, pięć pozostałych 4,55–5,35 m. **Przy środku krawędzi SE w danych 2025 jest element 5,25 m, nie 10–12 m**
— sygnał dla M57 (K67-054), nie rozstrzygam tu.

## 1. Katalog elementów (13 wierszy, ≥ 8 typów)

| # | element | wymiary | kolor (opis) | status |
|---|---|---|---|---|
| 1 | antena sektorowa panelowa, długa | 2688 × 498 × 197 mm, 56,5 kg | jasnoszary matowy radom (RAL 7035) | SOURCED (karta) |
| 2 | antena sektorowa panelowa, krótka | 1499 × 498 × 197 mm, 35 kg | jw. | SOURCED |
| 3 | antena radioliniowa 0,6 m | Ø 0,6 m, 6,7 kg | czasza biała, radom szary | SOURCED |
| 4 | antena radioliniowa 0,3 m | Ø 0,3 m, 4,08 kg | jw. | SOURCED |
| 5 | antena radioliniowa 0,9 / 1,2 m | — | — | UNVERIFIED |
| 6 | moduł RRU przy antenie | 425 × 296 × 130 mm, 18,3 kg | UNVERIFIED | SOURCED (wymiary) |
| 7 | szafa/kontener na dachu | rzut ok. 2 × 1 m | jasnoszary | ESTIMATED (ortofoto) |
| 8 | rama krzyżowa (X) pod maszt | ramiona ok. 12 (11–13) m | stal szara | ESTIMATED |
| 9 | maszt rurowy z odciągami | 6–8 odciągów, kotwienie r ≈ 3–4 m; **≥ 8,55 m nad dachem (Zwierzyniecka 4, LIDAR)** | stal | ESTIMATED (LIDAR) |
| 10 | maszt kratowy | **9–12 m (wieżowiec, M57-FIX #88)**; 4–6 m | stal | SOURCED_SECONDARY (+ LIDAR) |
| 11 | koryto kablowe drabinkowe | szer. 0,4–0,5 m | stal ocynk., jasna | ESTIMATED |
| 12 | wysięgnik/maszt narożny przy attyce | **4,35–4,75 m (Skorupska 17), 7,65 m (Dobra 3 NW)** | szary | ESTIMATED (LIDAR, dolna granica) |
| 13 | rozmieszczenie sektorów | 3 × 120° — przyjęcie typowe | — | UNVERIFIED |

## 2. Dachy — wysokości urządzeń nad dachem

**Metoda główna: chmura punktów LIDAR GUGiK** (skorowidz WFS `DanePomiaroweLidarEVRF2007` →
`gugik:SkorowidzDanychPomiarowychLIDAR2025`, arkusze 1:1250, **nalot 2025-04-18, 12 p/m²**, PL-1992 / PL-EVRF2007-NH;
`out/skorowidz.json`). Ortofoto z tego samego dnia (`gugik:SkorowidzOrtofomapy2025`, 0,05 m).
- `tools/lidar_roofs.py` → mapa wysokości nad dachem 70 × 70 m (`out/lidar_<dach>.png`) i automatyczne skupiska > 1 m.
- Urządzenia wybrane po obejrzeniu map i ortofoto → `masts_xy.json`; `tools/lidar_masts.py` → `out/lidar_masts.json`
  i profile boczne `out/prof_<dach>_<id>_zS|zW.png` (obejrzane — maszty widać jako pionowe ciągi punktów, odciągi jako skosy).
- **Wzór:** h = Z_max (walec r = 1 m wokół osi) − Z_dachu (dominanta histogramu 0,1 m w pierścieniu 2–6 m).
  **Niepewność:** ± 0,15 m (ESTIMATED) i h jest **dolną granicą** — przy 12 p/m² odstęp punktów ≈ 1/√12 ≈ 0,29 m,
  szczyt cienkiej rury może nie mieć trafienia. Drugi najwyższy punkt (h2) podany w manifeście — różni się o 0,0–0,9 m.
- Czas skanu (gps_time → UTC): 08:26–09:12 UTC.

| dach | operatorzy (UKE) | urządzenia (n) | **min / mediana / max [m]** | uwagi |
|---|---|---|---|---|
| Skorupska 17 (4 kond., dach 19,3 m npt) | B | 4 | **4,3 / 4,5 / 11,6** | maszt na ramie X ≥ 11,55; wsporniki narożne NE/SW/W 4,35–4,75 |
| Dobra 3 (dach 16,8 m npt) | A | 2 | **7,7 / 8,6 / 9,6** | maszt przy węźle skrzydeł ≥ 9,55; narożnik NW ≥ 7,65 |
| Zwierzyniecka 4 (11 kond., dach 35,2 m npt) | — | 1 | **8,6** (n = 1) | maszt rurowy z odciągami ≥ 8,55; element przy krawędzi N 5,85 m — przynależność UNVERIFIED, poza statystyką |
| Kopernika 5A / 7 (12 kond., dach 34,5 m npt) | B / A | 6 | **2,5 / 2,7 / 3,4** | wsporniki/platformy przy końcach bloków 2,55–3,35 |
| wieżowiec M57 (kontrola, dach 41,1 m npt) | B, C | 6 | 4,5 / 5,1 / 10,9 | przyjęte do gry: **9–12 m (M57-FIX #88)** |
| Hallera 19 | — | 0 | **brak > 1,3 m** | nadbudówki 1,05–1,25 m; OSM `man_made=tower` niepotwierdzony w danych 2025 |

Łącznie 23 pomiary (19 telekom.). Zwierzyniecka 4: arkusz LAZ kończy się ok. 22 m na N od punktu — budynek w całości w arkuszu (mapa `out/lidar_zwierzyniecka4.png`). Rozkład dla gry: **dwie klasy** — (a) maszt główny 7,5–11,5 m (4 dachy),
(b) wsporniki/maszty przy attyce 2,5–5,3 m (wszystkie dachy ze stacją). Progi art. 29 Pb (3 m / 12 m) obejmują obie klasy.

**Metoda cieni (wymagana w FIX) — wykonana jako kontrola, nie jako metoda główna.**
`tools/sun.py` (algorytm NOAA) dla 2025-04-18: 08:30 UTC az 140,1° / el 41,8°; 09:00 UTC az 149,5° / el 44,4°
(zgodne z M64: 44,4°). Godzina nalotu ortofoto nie jest w skorowidzu → wyznaczona z azymutu cienia.
- Zwierzyniecka 4 (`files/shadow_zwierzyniecka4.jpg`): cień masztu na NW, az ≈ 319° → Słońce 139° → ≈ 08:30 UTC ± 20 min
  → el 41,8° ± 1,5°. Koniec cienia wchodzi w cień podwyższonej części dachu po ≥ 6,3 m → **h > 6,3 × tan 41,8° = 5,6 m**,
  zgodne z LIDAR ≥ 8,55 m (K67-059).
- Skorupska 17, Dobra 3, Kopernika: cień masztu pada w cień własny budynku / dziedziniec — **nieczytelny** (obejrzane
  `files/shadow_*.jpg`). Dlatego wysokości podaję z LIDAR (dopuszczony w FIX wariant „NMPT/model wysokości”;
  chmura LAZ jest źródłem NMPT, więc jest dokładniejsza niż siatka 0,5 m).

**Negatyw.** Na 8 innych blokach ≥ 12 kond. masztów w rzucie nie ma (K67-020…027; próba nielosowa). Waszyngtona 36
i Tysiąclecia 10A potwierdzone też z ziemi (Commons 2013).

**Oznakowanie przeszkodowe (ESTIMATED, nie pomiar świateł):** szczyt masztu nad terenem = Z_top − mediana gruntu w 70 m:
Zwierzyniecka 4 ≈ 196,5 − 150,8 = **45,7 m**, wieżowiec ≈ 193,3 − 141,4 = **51,9 m** — ≥ 45 m, czyli wg § 36 rozp. 2021/264
światła średniej intensywności; pozostałe < 45 m (§ 35: małej intensywności). Czy światła faktycznie są — UNVERIFIED.

## 3. Wygląd na tle nieba
Kadry Commons (9; CC BY-SA 3.0/4.0, CC BY 3.0, CC0 — atrybucja w manifeście K67-073…081; `files/commons_*.jpg`, opisy w `commons_opisy.json`):
- Wieża wolnostojąca (Cieszyńska, zmierzch 2014): na jasnym niebie wszystko czyta się jako ciemnoszara sylwetka —
  panele pionowe (wąskie prostokąty ok. 3–5 : 1), czasze jako krążki z boku, platformy prostokątne. Elementy ≤ 0,1 m
  (pręty, kable) znikają; panele i czasze pozostają czytelne. Na dachu budynku w tle: 2 cienkie pręty.
- Waszyngtona 36 (3 kadry) / Tysiąclecia 10A (2 kadry), 2013: attyki gładkie, na Waszyngtona 1 cienki pręt ok. 2–3 m (ESTIMATED), bez masztów.
- Ulica Dobra (2020) i Kopernika (2020, ok. 450 m od bloków): budynków z masztami w kadrze brak — nieprzydatne do sylwetki.
- **Dachów z masztami z boku nie pozyskano** (luka 1). Profile LIDAR (`out/prof_*`) dają sylwetkę geometryczną:
  Skorupska — maszt z głowicą paneli w górnych ~1,5 m; Dobra — maszt z gęstszym skupiskiem punktów w górnych ~1,5 m (głowica anten);
  Zwierzyniecka — pojedyncza rura bez głowicy w chmurze (anteny drobne); wieżowiec W — kratownica z odciągami.

## 4. Przepisy i UKE
- **Prawo budowlane art. 29 — POTWIERDZONE w tekście urzędowym**: t.j. **Dz.U. 2026 poz. 524** (obwieszczenie Marszałka
  Sejmu z 27.03.2026), pobrany z API ELI Sejmu `https://api.sejm.gov.pl/eli/acts/DU/2026/524/text.pdf`
  (sha256 `4a33b840…7826`; ISAP id `WDU20260000524` — strona isap.sejm.gov.pl zwróciła 403 dla klienta skryptowego,
  ten sam tekst z ELI).
  - ust. 3 pkt 3 lit. a (s. 26): instalowanie na obiektach budowlanych instalacji radiokomunikacyjnych „… oraz antenowe
    konstrukcje wsporcze, o wysokości większej niż 3 m i niewiększej niż 12 m” — **zgłoszenie** (art. 30);
  - ust. 4 pkt 3 lit. a (s. 27): „… o wysokości niewiększej niż 3 m” — bez pozwolenia i bez zgłoszenia;
  - ust. 1 pkt 37 lit. b: wolno stojące maszty bezodciągowe dla urządzeń radiokomunikacyjnych ≤ 7 m (nie dachy).
- Rozp. MI z 12.01.2021 (Dz.U. 2021 poz. 264): § 35, § 36, § 46 — bez zmian względem r1.
- Wykaz UKE: bez wysokości anteny i azymutów; 419 wierszy, 124 lokalizacje w Białymstoku; operatorzy A/B/C.

## 5. Kadry (obejrzane)
- Ortofoto: 16 wycinków r1 + **7 nowych 0,05 m/px** (`ortho_dobra_c` — **przecentrowany**, cały dach skrzydła NW;
  `ortho_kopernika_s/_n`; `shadow_*` ×4 — środek = maszt z LIDAR + 6 m w kierunku cienia).
  Przecentrowanie: środek wycinka liczony z położenia urządzeń w LIDAR (prawdziwa pozycja), z zapasem na przechył
  budynku w mozaice (ESTIMATED z widocznej elewacji: Dobra 3 ok. 3 m przy 17 m wysokości, Zwierzyniecka 4 do ok. 7 m przy 35 m). `ortho_dobra_z` (r1) zostaje,
  ale jest zastąpiony przez `ortho_dobra_c`.
- LIDAR: 6 map wysokości + 23 profile boczne (×2 widoki).
- Naziemne: 9 Commons (jeden tytuł okazał się duplikatem — usunięty, zapis w logu).

## 6. Luki
1. **Kadry naziemne dachów z masztami: brak.** Commons API zwracało HTTP 429 naprzemiennie z 200
   (`out/commons_log.json` — wszystkie próby z czasem; przerwy ≥ 6 s, po 429 — 60 s, UA generyczny, tylko domeny
   Wikimedia), 3 przebiegi 13:32–14:00 UTC. Pobrano 9 z 15 tytułów; 4 nadal 429 (m.in. oba kadry ul. Zwierzynieckiej), 1 brak pliku, 1 duplikat — K67-082.
2. Godzina nalotu ortofoto — tylko z azymutu cienia (± 20 min).
3. Przynależność telekom. elementów Kopernika i elementu N Zwierzyniecka — z rzutu, bez kadru z boku.
4. Karty szaf i anten 0,9/1,2 m — niezweryfikowane.

## 7. Samokontrola
r1: seed 20261115, 7/35 PASS. r2: `audit_20_percent.json` — próba 10/47 z wierszy K67-036…082 (seed 2026111502 + 2026111503): **10 PASS**; audyt K67-044 wykrył błąd w metodzie kontrolnej (klasa 6 zawiera ściany) — poprawiono metodę audytu, wynik pomiaru bez zmian.

## Odtworzenie
```
uv run --no-project --with pyproj python -I tools/skorowidz.py tools out/skorowidz.json
# LAZ (5+1 arkuszy, ~380 MB) — URL-e w out/skorowidz.json / manifeście; pobrane do katalogu roboczego (nie w gicie)
uv run --no-project --with "laspy[lazrs]" --with numpy --with pillow --with pyproj --with scipy python -I tools/lidar_roofs.py <laz_dir> out/
uv run --no-project --with "laspy[lazrs]" --with numpy --with pillow --with pyproj python -I tools/lidar_masts.py <laz_dir> out/
uv run --no-project --with pyproj --with pillow python -I tools/shadow_crops.py tools files/
python3 -I tools/sun.py
python3 -I tools/commons_fetch.py tools files/ out/commons_log.json
python3 -I build_manifest.py
```
