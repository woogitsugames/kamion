# Przegląd PR #43 (Mistral M46/P1B — luki zdjęć trasy P1) — s17, 2026-11-13

## NASTĘPNY KROK (dla sesji przejmującej)
Przegląd ZAKOŃCZONY. Lider: wkleić blok **M46-FIX** (koniec `docs/owner/MISTRAL-FIXES-8.md`) do nowej sesji Mistrala; PR #43 NIE scalać. Do kamer kontrolnych można już teraz wziąć kadry z §5 (z poprawionym przypisaniem obiektu).

## 1. Werdykt
**ODRZUCONY do poprawy (M46-FIX).** Metadane z KartaView/Commons są wierne źródłu (3/3 KartaView i 2/2 Commons sprawdzone na żywo: pozycja, azymut, data co do sekundy), ale **przypisanie kadrów do ulic jest systematycznie błędne**: 26 z 33 kadrów „OK” pokazuje inną ulicę niż w manifeście. Przyczyna: reguła „≤ 25 m od osi way” bez sprawdzenia, czy azymut kamery biegnie wzdłuż tej ulicy → kadry z przejazdu arterią przypisano bocznym ulicom przy wlotach. To ten sam błąd co P11 (opisy pisane bez patrzenia): `punkt_opis` („przy nr 2”, „przy parkingu”, „na krawędzi ringu”) nie odpowiada temu, co widać na zdjęciach, mimo deklaracji „36/37 sprawdzonych modelem wizyjnym”.

## 2. Metoda
- `git fetch`; `gh pr diff 43 --name-only` → tylko `research/mistral/p1-route-photos-2/` (5 plików: .gitignore, README, manifest 47 wierszy, sources, audit) ✓. Zdjęcia: ZIP nie było w `Downloads` przy starcie; lider dostarczył rozpakowane 36 JPG w `research/_incoming/mistral-p1-route-photos-2/` (P1B-016 brak, P1B-037/039–047 celowo bez plików).
- Geometria: lokalny `Data/raw/osm/podlaskie-261108.osm.pbf` (pyosmium, 4631 ways drogowych w bbox 53.135–53.170 N, 23.095–23.185 E; Overpass zwracał 502/timeout). Dla każdego kadru: odległość punkt–odcinek do najbliższych ways + różnica azymutu kamery i kierunku odcinka (mod 180°).
- API na żywo: KartaView `2.0/photo/?id=` (219382225, 1326673621, 219381783), Commons `extmetadata` (2 pliki). Bez Google, bez Mapillary.
- Duplikaty z P1: po nazwie pliku Commons/URL wobec `research/gptpro/p1-route-photos/manifest.csv` (origin/main).
- **Próba:** `random.Random(461113).sample(36 plików, 10)` = 27,8 %: P1B-001, 003, 005, 010, 018, 019, 020, 021, 024, 027 + celowo dobrane 004, 007, 012, 034, 035. **Obejrzane wszystkie 15 JPG.**

## 3. Wyniki
### 3.1 Geometria OSM (wszystkie kadry KartaView)
| Kadry | Manifest mówi | OSM + zdjęcie pokazuje |
|---|---|---|
| P1B-017…033 (17) | Bitwy, Białostoczek, Kombatantów, Sokólska, Motoszko, Wileńska, Skidelska | **Al. Tysiąclecia** (0–6 m od osi, Δ azymutu 0–8°; do „swojej” ulicy Δ 61–90°). Jedna sekwencja KV 1155711 (telenavdrives, 23.03.2018, jazda na S/SSE). |
| P1B-001…003 (3) | ul. Stefana Batorego | **Andersa** (trunk, 2–8 m, Δ 1–4°); Batorego 12–21 m, Δ 74–77°. Na zdjęciu dwujezdniowa arteria, drogowskaz „19 Kuźnica / 65 Ełk”, limit 70. |
| P1B-010…015 (6), 016 | wloty/wyloty ronda Pamięci Bieżeństwa | **estakada Andersa NAD rondem** (`bridge`, 3–6 m, Δ 0–1°). Na zdjęciach 010/012 tylko jezdnia estakady i bariery; ringu nie widać. |
| P1B-006…009 (4) | wiadukt Al. Tysiąclecia | ✓ zgodne (006–007 na `bridge`, 008–009 zaraz za nim). „P1B-009 = jezdnia B” — fałsz: ta sama sekwencja i azymut 142° co 006–008 (sequenceIndex 3665 → jezdnia A). |

### 3.2 Próba obejrzanych JPG (10 losowych + 5 celowych)
- **001, 003** — Andersa przy wlocie Batorego (nie Batorego). **010, 012** — estakada Andersa (nie ring; „na krawędzi ringu” zmyślone).
- **018** — skrzyżowanie Al. Tysiąclecia z Bitwy/Radzymińską ze światłami (budynek „MITEX”). **019, 020, 021** — Al. Tysiąclecia przed **łukowym wiaduktem kolejowym z 1955 r.** (drogowskaz „Centrum / 676 Supraśl / Wysokie Maz.”), nie ul. Białostoczek „przy nr 2”. **024** — jezdnia serwisowa/pas wzdłuż Al. Tysiąclecia (stacja Orlen, billboard). **027** — skrzyżowanie Al. Tysiąclecia z Sokólską/Kombatantów (sygnalizacja, Circle K) — nie Sokólska.
- **005** (Olsztyńska) — miejsce OK, ale silne rozmycie ruchu, kadr boczny z okna pojazdu → jakość 2, nie 3 „drobne rozmycie”. **004** — Olsztyńska, lekki śnieg, z poziomu jezdni ✓ (dobry kadr). **007** — wiadukt Al. Tysiąclecia, bez liści, bariery z ekranami ✓. **034** — widok z przejścia na ring ronda pod estakadą ✓ (ale duplikat P1-004). **035** — elewacja domu, opis uczciwy (bezużyteczny).
- **Wynik:** 9/10 losowych z błędnie przypisaną ulicą/obiektem, 1/10 z zaniżoną wadą jakości.

### 3.3 Inne błędy
- README/sources: „manifest P1 nie istnieje w repo” — **fałsz** (`research/gptpro/p1-route-photos/manifest.csv` jest w bazie gałęzi 26f62c3d). Skutek: duplikaty z P1 — **P1B-034=P1-004, P1B-036=P1-033, P1B-037=P1-052, P1B-042=P1-053**.
- Autor „Hollyfeld” (P1B-037, 039–042) — **zmyślony**; Commons API: Rakoon, CC0.
- `audit_20_percent.json` sprawdzał tylko zgodność metadanych z API (10/10 PASS) — nie przypisanie do ulicy ani treść zdjęcia; dlatego przeoczył błąd główny.
- Licencje: KartaView CC BY-SA 4.0 (referencja) i Commons CC0 — poprawnie; NC/ND brak ✓. JPG 1280×720 ≤ 1600 px ✓.

## 4. Luki z zadania M46
| Luka | Stan wg PR | Stan faktyczny |
|---|---|---|
| 1. Batorego | częściowo (3) | **NIE** — 0 kadrów (są z Andersa) |
| 1. Olsztyńska | częściowo (2) | **częściowo** — 2 kadry Commons (004 dobry, 005 rozmyty), bez azymutu, nie z fotela kierowcy |
| 1. Brzeska, Buska | pozostaje | **NIE** (wynik negatywny wiarygodny: 0 w KV/Pmax/Commons) |
| 2. Ulice willowe (liście/śnieg) | pozostaje | **NIE** (wynik negatywny wiarygodny; uwaga: P1 ma już śnieg/liście z poziomu pieszego dla części ulic) |
| 2. Wiadukt Al. Tysiąclecia — zima | wypełnione | **ZAMKNIĘTA** (006–009, 23.03.2018, bez liści; tylko jezdnia A; sprzed przebudowy 2021/22 → geometria tak, oznakowanie nie) |
| 2. Maczka (wiadukty, mosty), łącznica DK8 — zima | pozostaje | **NIE** |
| 3. Rondo Bieżeństwa — kierowca na wlotach/wylotach | 3 sloty ✓ | **NIE** (0/8 slotów; kadry z estakady nad rondem; ring obsługują łącznice i Bitwy — sloty trzeba przedefiniować) |
| 4. Poziom kierowcy dla 9 ulic | 7/9 ✓ | **NIE** (0/9; 17 kadrów to Al. Tysiąclecia) |

## 5. Najlepsze nowe kadry do kamer kontrolnych (obejrzane, z poziomu kierowcy, przypisanie poprawione)
| id | Obiekt (faktyczny) | lat, lon | azymut | data / sezon |
|---|---|---|---|---|
| P1B-007 | wiadukt Al. Tysiąclecia nad torami, jezdnia A | 53.164496, 23.150108 | 142° | 2018-03-23, bez liści |
| P1B-020 | Al. Tysiąclecia — łukowy wiadukt kolejowy 1955 | 53.142129, 23.157632 | 165° | 2018-03-23, bez liści |
| P1B-019 | Al. Tysiąclecia — dojazd do wiaduktu 1955, drogowskaz 676 | 53.142291, 23.157583 | 177° | 2018-03-23 |
| P1B-027 | Al. Tysiąclecia × Sokólska/Kombatantów (sygnalizacja) | 53.150993, 23.154613 | 160° | 2018-03-23 |
| P1B-018 | Al. Tysiąclecia × Bitwy Białostockiej/Radzymińska | 53.145710, 23.157239 | 175° | 2018-03-23 |
| P1B-010 | estakada Andersa nad rondem Bieżeństwa (na NW) | 53.151587, 23.168466 | 303° | 2021-06-23, liście |
| P1B-003 | Andersa przy wlocie Batorego, drogowskaz DK19/DK65 | 53.149631, 23.173610 | 301° | 2019-08-25, liście |
| P1B-004 | Olsztyńska, jezdnia (Commons CC0, z jezdni) | 53.149151, 23.151119 | UNVERIFIED | 2022-12-03, śnieg |

Uwaga: kadry Al. Tysiąclecia 2018 są sprzed przebudowy 2021/22 — używać do geometrii wiaduktów/skrzyżowań, nie do oznakowania i zieleni.
