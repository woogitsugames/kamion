# Przegląd PR #64 — R4 bialystok-building-typology (typologia zabudowy: trasa C i Dojlidy) — s21 cloud D, 2026-11-15

**Werdykt: SCAL z erratą.** Pakiet jest rzetelny:
- **12 z 12 obejrzanych kadrów ma opis zgodny z obrazem.**
- Statystyki BDOT10k/LoD1 odtworzyłem z `buildings.geojson` na main co do sztuki i co do decymetra.
- Porównanie NMPT−NMT z LoD1 odtwarza się z CSV (20 bud., mediana +0,015 m).
- 8 cytatów (Wikipedia oldid, karta producenta blachy) zgadza się dosłownie.

Erratę uzasadniają trzy usterki:
- R4-075 ma status SOURCED, choć zdanie w Wikipedii ma znacznik „[potrzebny przypis]”.
- Brakuje kolorów bloków po termomodernizacji, które były wymogiem R4.
- Zdjęcia są w gicie (11 MB), wbrew zasadzie CLOUD2.

- Gałąź `origin/research/cloud2-bialystok-building-typology` @ `1b14f8d0a`. Baza `81c9baee7` jest 612 commitów za `origin/main`. `git diff --stat origin/main...` pokazuje 70 plików, wszystkie w `research/cloud2/bialystok-building-typology/` ✓.
- Manifest ma 150 wierszy. Wewnętrzny `REVIEW.md` daje PASS z uwagami P2.

## 1. Kompletność (CLOUD2-PROMPT R4 i blok „Dokończenie”: ≥ 30 kadrów, Dojlidy, opisy elewacji)
| Wymóg | Wynik | Dowód |
|---|---|---|
| Bloki: systemy, moduły | **TAK** | OWT-67/75, OW-T, W-70, system szczeciński, cytaty z oldid. Użycie W-70 i systemu szczecińskiego w Białymstoku oznaczone UNVERIFIED |
| Bloki: kolory po termomodernizacji | **NIE** | tylko 2 kadry bloków (R4-146, 147). README odsyła do `mistral/p3-buildings-2` |
| Biurowce, hale (okładziny, bramy, attyki), domy | **TAK** | 19 wierszy z kart producentów (płyta 1150 mm, T35, brama segmentowa 545 mm, śluza, dok 1,1 m) oraz opisy z kadrów |
| Liczby: kondygnacje, wysokości GUGiK | **TAK** | BDOT10k + LoD1 2024 + LoD2 2017 z `buildings.geojson` oraz 56 budynków NMPT−NMT z WCS GUGiK |
| ≥ 30 kadrów, w tym Dojlidy | **TAK** | 40 obejrzanych (37 z elewacją), z tego 16 z Dojlid (15 z elewacją) |
| Samokontrola 20 % z obejrzeniem | **TAK** | seed 20261114: 26/26. Seed 20261115: 5 z 24 nowych, 4 PASS / 1 FIX (R4-148) |
| Licencje, marki, Google | **TAK** | 23 × CC0 (Rakoon), 1 × CC BY-SA 3.0 (Henryk Borawski), Panoramax/KartaView CC BY-SA. Szyldy oznaczone „nie odtwarzamy”. Brak Google |
| UA generyczny | **TAK** | `research-client/1.0 (generic)`, `research-script/1.0 (generic)` |
| Zdjęć nie commitować | **NIE** | `.gitignore` celowo odwraca regułę: `!files/commons/`, `!files/jpg1600/`. W `files/` jest 11 MB |
| Tylko własny katalog | **TAK** | — |

## 2. Obejrzane obrazy (12 z `files/commons/`, każdy osobno ≤ 960 px)
| Kadr | Licencja (Commons API dziś) | Ocena opisu |
|---|---|---|
| R4-127 `20230903_133850` | CC0, Rakoon ✓ | ✓ długa czerwona hala z płaskim dachem, biało-szara część biurowa, ogrodzenie panelowe. Na pierwszym planie dwujezdniowa ulica, szara asfaltowa DDR, chodnik z szarej kostki, latarnie dwuramienne. Czy panele są pionowe, nie rozstrzygnę przy 960 px (drobiazg) |
| R4-130 `20230903_134445` | CC0 | ✓ hala w budowie: słupy i rygle prefabrykowane, kratownice, dźwig wieżowy, czerwone słupki ogrodzenia |
| R4-132 `20230910_151311` | CC0 | ✓ biurowiec 4–5 kondygnacji z szarych paneli z pasami okien, białe hale, rząd tuj, czerwone słupki, szara DDR |
| R4-133 `20221103_151248` | CC0 | ✓ 3 kondygnacje, grafitowa attyka i pas parteru, beżowe ściany, pasy okien, parking |
| R4-135 `20230903_135728` | CC0 | ✓ hala szaroniebieska z żółtymi pasami i żółtą attyką z owalnym szyldem, kraty, siatka, blok w tle |
| R4-136 `8855_November_2022` | CC0, Rakoon ✓ | ✓ 2 kondygnacje w szachownicę jasnoszaro-średnioszaro-czerwoną, białe okna, obok parterowy budynek w beżu i brązie z bramą garażową, plac z kostki |
| R4-138 `20240623_130552` | CC0 | ✓ dom z cegły silikatowej, czerwona dachówka, PV, 2 kominy, ulica z szarej kostki, chodnik z czerwonej kostki, ogrodzenie z desek |
| R4-139 `20240623_130803` | CC0 | ✓ klinkier pomarańczowo-czerwony, okrągła wieżyczka, kute balustrady i brama, słupek z klinkieru, podjazd z kostki kamiennej, czerwona kostka |
| R4-141 `20210629_092231` | CC0 | ✓ biały biurowiec 4 kondygnacje, zaokrąglona szara bryła z przeszkleniem, budynek z szarych bloczków, ogrodzenie z czerwonej cegły z przęsłami, tuje |
| R4-143 `20210425_094546` | CC0, Rakoon ✓ | ✓ długi zakład z ciemnoniebieską okładziną i jasnymi pasami, czerwone słupki, bramownica kratowa po prawej |
| R4-146 `20220725_124141` | CC0 | ✓ blok 5 kondygnacji z białą elewacją i pasami balkonów, parking z kostki, pomarańczowe słupki, słup WN |
| R4-148 `20240530_122451` | CC0, Rakoon ✓ | ✓ jasnozielony/oliwkowy budynek z 7–8 rzędami okien nad parterową przybudówką, balustrada na dachu, komin w tle. Liczba „8–9 kondygnacji (ESTIMATED)” po FIX jest uczciwa |

Zgodność: **12/12**. Licencje: **5/5** zgodne z `extmetadata` (w tym CC BY-SA 3.0 dla R4-150). Marki z szyldów nie przechodzą do opisów dla gry ✓.

## 3. Liczby sprawdzone u źródła (8 + 2 odtworzenia)
- **Wikipedia, „Technologia wielkopłytowa” oldid 79506745:** „siatce o wymiarach 540 × 480 cm” ✓, „240, 360, 480 i 600 cm” ✓, „Wysokość kondygnacji mieszkalnych – 280 cm” ✓, „siatce 480 × 480 cm i 480 × 240 cm” ✓. „…280 cm jest wartością brutto” (R4-075) jest dosłownie, **ale w artykule ma znacznik „[potrzebny przypis]”**, co uzasadnia erratę E1.
- **Wikipedia, „OWT-67” oldid 72638965:** „nadziemna: 270 cm” ✓.
- **Karta producenta blachy T35:** „Profile Height 34 mm” ✓, „Effective width 1035 mm” ✓, „Maximum length 12000 mm” ✓.
- **Odtworzenie BDOT/LoD1** (mój skrypt, `buildings.geojson` na main @ `b95d3db54`, funkcja = „budynek wielorodzinny”/„jednorodzinny”): kafel C, bloki n = 50, kondygnacje 4: 25 / 3: 7 / 2: 7 / 6: 3 / 16: 3, LoD1 p10/p50/p90 = 8,9 / 14,9 / 39,6 m ✓. Domy n = 269, p50 7,7 m ✓. Dojlidy: bloki n = 12 (7,3 / 11,9 / 17,8) ✓, domy n = 172 ✓.
- **Odtworzenie NMPT−LoD1** z `data/nmpt_sample.csv`: n = 20, mediana +0,015 m, mediana |Δ| 0,195 m, mediana p95 − LoD1 = 0,73 m ✓. Wywołań WCS nie powtarzałem.

SOURCED / ESTIMATED: kondygnacje z kadrów i wysokości NMPT są oznaczone ESTIMATED, a brama 4,0 × 4,5 m jako WORKING_VALUE. Dok 1,2 m z zadania jest uczciwie UNVERIFIED (źródło podaje 1,1). Kody dachów LoD2 nie mają słownika, co README zgłasza.

## 4. Wnioski dla gry (plik, liczba)
| Element | Gra dziś | R4 | Działanie |
|---|---|---|---|
| Wysokość kondygnacji bloku na fasadzie (`tools/worldgen/streetscape/buildings_mesh.py`, `STOREY_H["block"] = 2.8`) | 2,8 m | OWT-75 i W-70: 280 cm brutto (SOURCED, R4-074/077); OWT-67: 270 cm | ✓ bez zmian |
| Wysokość budynku bez LoD1/LoD2 (`tools/worldgen/buildings.py`, `STOREY_M = 3.0`, `BASE_M = 1.0`, WORKING_VALUE) | n × 3,0 + 1,0, czyli blok 4 kondygnacje = 13,0 m, dom 2 kondygnacje = 7,0 m | LoD1/kondygnacja p50 (z dachem): bloki 3,6 (C) i 3,5 (Dojlidy), domy 3,92 i 3,97 (`data/stats.json`), czyli blok 4 kondygnacje ≈ 14,4 m, dom ≈ 7,8 m | **P2 (wyliczenie recenzenta):** fallback zaniża o 0,8–1,4 m. Propozycja `BASE_M = 2.0` (WORKING_VALUE z p50 R4). Dotyczy tylko budynków bez LoD1/LoD2 (`src = bdot10k_storeys`), więc wpływ jest mały |
| Paleta hal w strefie Dojlid (`facade_atlas.py` / `facade_kit.py`) | — | 6 hal na kadrach: dominują białe i jasnoszare z płaskim dachem i szarym cokołem, 1 czerwona; przybudówki biurowe grafitowe lub szaro-białe | P2 dla world-buildera Dojlid: proporcja kolorów hal ~5 : 1 jasne : czerwone (ESTIMATED, n = 6, jeden autor) |
| Ogrodzenia stref przemysłowych | `props.py` ma U-12 z czerwonymi słupkami (inny obiekt) | panelowe ogrodzenia z **czerwonymi słupkami** na 5 kadrach (R4-130, 131, 132, 134, 143) | P2: sprawdzić, czy generator ogrodzeń działek przemysłowych (`furniture.py` → fences) ma wariant „panel + czerwony słupek” |
| Biurowce | — | 3–5 kondygnacji, ciemna attyka, pasy okien (R4-132, 133, 141) | referencja kamer QA dla Dojlid |
| Rytm okładzin hal | — | płyta 1,15 m (SOURCED), arkusz T35 1,035 m, sekcja bramy 0,545 m, dok 1,1 m | do UV i rytmu w `facade_kit.py`. ADR nie jest potrzebny |

## 5. Errata (przy scaleniu albo w następnej paczce, nie blokuje)
1. **E1:** R4-075 („280 cm = brutto”): zmienić status na `UNVERIFIED (Wikipedia, zdanie z [potrzebny przypis])`. Treść R4-074/077 (280 cm) zostaje SOURCED.
2. **E2 (proces, decyzja lidera):** zdjęcia w gicie (`files/commons/` 24, `files/jpg1600/` 16, 11 MB). Do wyboru `git rm -r --cached …/files/commons …/files/jpg1600` z przywróceniem `files/*` w `.gitignore` (`fetch.py` pobiera i sprawdza sha256) albo świadoma akceptacja, bo atrybucja jest w `INDEX.csv` i manifeście.
3. **E3 (luka, następna paczka):** kolory bloków po termomodernizacji przy trasie C. Wskazać, które wiersze `mistral/p3-buildings-2` to pokrywają, albo dodać ≥ 5 kadrów bloków Białostoczka (Panoramax/KartaView).
4. **E4:** README „Kadry Commons”, R4-127: „pionowe panele” zmienić na „panele (kierunek nierozstrzygalny przy 960 px)”. Możliwe pokrycie z `mistral/p11-dojlidy-photos` (P2-4 wewnętrznej recenzji): sprawdzić tytuły.

## 6. Dla lidera
- **Scalić PR #64.** E1 i E2 rozstrzygnąć przy scaleniu.
- Do gry: `BASE_M` w fallbacku wysokości (P2) oraz paleta hal i ogrodzenie z czerwonym słupkiem dla Dojlid (P2). ADR nie jest potrzebny, wystarczy zmiana WORKING_VALUE z odnośnikiem do R4.
