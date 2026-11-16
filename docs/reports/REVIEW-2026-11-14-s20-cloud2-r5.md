# Przegląd R5 street-trees (chmura #2, PR #63) — s20, 2026-11-14

**Werdykt: SCAL z erratą.**
- **Dane OSM odtworzyłem 1:1 na lokalnym ekstrakcie** `Data/raw/osm/podlaskie-261108.osm.pbf` (stan 2026-11-08; R5 używał ekstraktu z 2026-11-13). Skrypty R5 dały te same liczby drzew, szpalerów, żywopłotów i wszystkie statystyki rozstawu (§3).
- Łaska 2015, Dz.U., NIK i e-katalog zgadzają się ze źródłem.
- Na 12 obejrzanych kadrów jeden opis jest błędny (R5-169: tuje). Jeden paragraf rozporządzenia jest zły (R5-073: § 82, nie § 59).
- Allometria USDA jest nieodtworzona, bo plik zwraca 403.

Szczegóły i blok errat w §6. Nic nie blokuje scalenia.

- Gałąź `origin/research/cloud2-street-trees` @ `0d07a3a12`. `git diff --shortstat origin/main...`: 24 pliki, +8843, wszystkie w `research/cloud2/street-trees/` ✓.
- Manifest: 210 wierszy. Nic nie scalono, nic nie scommitowano, PR bez komentarza. Raport nie jest scommitowany.
- Brak wewnętrznej recenzji (`REVIEW.md`). Ten przegląd ją zastępuje.

## 1. Kompletność wg CLOUD2-PROMPT (R5)

| Wymóg | Wynik | Dowód |
|---|---|---|
| Gatunki dominujące (inwentaryzacje UM, BIP, open data, OSM natural=tree) | **TAK** | Łaska 2015, Tab. 1 (606 drzew); paleta UM 2017 (BIP); NIK 2024: brak inwentaryzacji ✓ (sprawdzone w PDF); OSM: `species` 3,2 % |
| Wysokości/korony wg wieku | **TAK (z zastrzeżeniem)** | Klasy H/obwodu Łaski n = 171 ✓. Tabela obwód → H/korona z USDA UTD (USA, nieodtworzona: 403, E4) |
| Rozstaw szpalerów | **TAK** | 111 rzędów OSM, odtworzone ✓ |
| Żywopłoty (tuje) | **TAK** | e-katalog ZSzP ✓, 11 frontów z kadrów; 1 opis błędny (E1) |
| Sezonowość | **TAK** | Czernecki i in. 2018 (CC BY), daty odczytane z wykresu ±3 dni (ESTIMATED, uczciwie) |
| Liczby do generatora (ADR 0163/0170) | **TAK** | README „Jak używać”; porównanie z kodem w §5 |
| Overpass: zapytanie i data | **odstępstwo, uczciwie opisane** | Overpass był nieosiągalny. Zapytanie równoważne jest w `sources.md`, ekstrakt PBF ma datę i sha. Odtworzenie lokalne potwierdza równoważność |
| Samokontrola 20 % | **TAK, z odstępstwem** | `Random(20261114).sample(sorted(ids), 42)` daje ten sam zbiór ✓. Kadry obejrzane ponownie na arkuszach 640 px zamiast 960 px (przyznane) |
| Licencje, zakaz Google | **TAK** | CC0 ×22, CC BY 3.0 ×4 i CC BY-SA ×28 jako „referencja”; Łaska i e-katalog tylko w cytatach. `sources.md` przyznaje, że kilka pierwszych zapytań do Commons miało w User-Agent nazwę organizacji repo. W kodzie jest teraz UA ogólny ✓ |
| Tylko własny katalog | **TAK** | diff jak wyżej |

## 2. Co obejrzałem sam (12 kadrów + 1 wycinek 3×)

Pobrałem przez `fetch.py`: 61 z 62 plików, sha256 zgodne. Brakuje tylko zip UTD (E4). Każdy kadr oglądałem osobno, ≤ 900 px.

| Kadr | Opis R5 | Ocena |
|---|---|---|
| kv7119879 (R5-146) | rząd ok. 7 młodych drzew za trawnikiem i ścieżką, paliki | ✓ |
| kv993061586 (R5-152) | niski strzyżony żywopłot liściasty wzdłuż chodnika, rowerzysta | ✓ |
| kv993066550 (R5-154) | młode drzewa z 3 palikami, stożkowe tuje przy niebieskim ogrodzeniu | ✓ |
| kv1326673765 (R5-163) | rząd ok. 5 młodych drzew o jasnym spodzie liści, duże srebrzyste drzewo | ✓ |
| cm20200726084244 (R5-167) | rząd młodych tui „poniżej ogrodzenia, korony się nie stykają” | ≈: tuje sięgają mniej więcej wysokości ogrodzenia panelowego i prawie się stykają (drobne, E3) |
| **cm20200726084948 (R5-169)** | „zwarta ściana tui, strzyżona od góry, wyższa od słupków o ok. 1/3” | **✗** Wycinek 3×: ściana sięga ok. **2×** wysokości murowanych słupków, choć stoi dalej od kamery, więc w rzeczywistości jest jeszcze wyższa. Wierzchołki to **pojedyncze stożki ‘Smaragd’, nie strzyżona płaszczyzna** (E1) |
| cm20200726085539 (R5-176) | wysoka ściana żywopłotu ok. 2× wysokość kombi, sumak, kolumnowe iglaki | ✓ |
| cm20200712161619 (R5-182) | Częstochowska: rzędy drzew w chodnikach, wierzchołki ok. 3. kondygnacji, kostka kamienna | ✓ |
| cm20210313102027 (R5-187) | Lipowa: bezlistne drzewa przy krawężniku, krata, stalowa osłona pnia, ławka, wiata | ✓ |
| cm20210522101909 (R5-188) | Lipowa w maju: pełne ulistnienie, osłony, ławki | ✓ |
| cm20230805102222 (R5-191) | rząd małych tui wystających nad drewniany płot na murku, jarząb z owocami | ✓ |
| px0e1d9bd7 (R5-195) | plac zabaw, bloki 5 i 11 kondygnacji, bezlistne drzewa, kolumnowe tuje do 1.–2. kondygnacji | ✓ |

## 3. Weryfikacja OSM na `Data/raw/osm`

Uruchomienie: `uv run --project tools/worldgen python -I tools/osm_extract_trees.py Data/raw/osm/podlaskie-261108.osm.pbf <out>`, potem `row_spacing.py` i `osm_stats.py` z gałęzi R5, bez zmian.

| Wielkość | R5 (PBF 2026-11-13) | Recenzent (PBF 2026-11-08) |
|---|---|---|
| relacja granicy | 2910925 | 2910925 |
| `natural=tree` / `tree_row` / `barrier=hedge` | 2549 / 35 / 138 | **2549 / 35 / 138** |
| drzewa ≤ 15 m od osi / rzędy / drzewa w rzędach | 1537 / 111 / 911 | **1537 / 111 / 911** |
| odstęp (800): p10 / mediana / p90 | 4,28 / 7,13 / 15,57 | **identyczne** |
| mediana odstępu per rząd (111): p10 / mediana / p90 | 4,57 / 7,98 / 12,39 | **identyczne** |
| pień od osi: mediana (p10–p90) | 6,31 (4,01–11,37) | **identyczne** |
| pień od krawężnika (szac.): mediana (p25–p75) | 2,47 (1,45–3,96) | **identyczne** |
| `species` / `leaf_type` | 82 / 1533 | 82 / 1534 (edycje z 5 dni) |
| trasa C / Dojlidy | 1 / 5 drzew | 1 / 5 ✓ |

## 4. Inne liczby sprawdzone u źródła (6)

| # | Liczba R5 | Źródło | Wynik |
|---|---|---|---|
| 1 | Łaska Tab. 1: klon zwyczajny 10/30/131/124 = 295 | PDF (sciendo, OA) | ✓ wiersz *Acer platanoides*; tekst: „Acer platanoides L. (295 specimens)” |
| 2 | klon jesionolistny 53, jesion wyniosły 8 (korekta P10-004) | jw. | ✓ tekst: „Acer negundo L. (53”; wiersz *Fraxinus excelsior* - 6 1 1 = 8. Blok antropofitów w PDF jest przesunięty kolumnowo, więc liczby 53 nie da się odczytać z wiersza tabeli, ale tekst ją potwierdza |
| 3 | klasy H (n = 171): 4,7 / 32,7 / 53,8 / 3,5 / 5,3 %; obwód 24 / 56 / 13,5 / 6,5 % | Łaska, tabele klas wysokości i obwodu (Total = 171) | ✓ |
| 4 | skrajnia 4,50 m (jezdnia GP/G/Z/L/D) i 2,50 m (chodnik) | Dz.U. 2022 poz. 1518 § 80 ust. 1 | ✓ dosłownie |
| 5 | do 2022: pas zieleni ≥ 3,0 m, pień ≥ 3,0 m od krawędzi jezdni | Dz.U. 2016 poz. 124 § 53 ust. 1 i 3 | ✓ dosłownie |
| 6 | ‘Smaragd’: 2,5 × 0,7 m po 10 latach, co 0,5–0,6 m | e-katalogroslin.pl/plants/7170 | ✓ dosłownie |
| — | NIK: brak kompleksowej inwentaryzacji | PDF NIK, pkt 2.1 | ✓ |
| — | R5-073: „jedyne wystąpienie słowa drzewa: § 59 ust. 4” | Dz.U. 2022/1518, s. 22 | **✗ to § 82 ust. 4** (strona 22 się zgadza) — E2 |

## 5. Co R5 daje grze (pliki, liczby)

Generator: `tools/worldgen/streetscape/vegetation.py`.

| Element | Dziś w kodzie | Wg R5 | Działanie |
|---|---|---|---|
| Rozstaw rzędu BDOT `OT_OIPR_L` | stały 8,0 m (`np.arange(2.0, L, 8.0)`, l. 297) | mediana per rząd **7,98 m** (p10 4,6; p90 12,4); 7,1 m to mediana wszystkich odstępów, gdzie liczą się też luki | **bez zmian** (8 m zgodne). Opcjonalnie rozrzut per rząd 6,5–10 m (p25–p75) |
| Gatunek rzędu | `["linden","maple"][seed % 2]`, czyli rzędy 50/50 | wśród klon + lipa przy głównych ulicach: klony 331 vs lipa 49 (≈ 87:13, z samosiewami). Miks proponowany przez R5: klon 45 %, lipa 20 % (≈ 70:30) | do rozważenia (WORKING_VALUE): przewaga klonu w rzędach, np. 70/30. Łaska liczy wszystkie drzewa w pasie, łącznie z samosiewami, nie tylko rzędy sadzone. Rzędy lipowe (Lipowa, JP II) zostawić lipowe |
| Wysokość drzew w rzędach | `HEIGHT` maple 8–16 m, linden 9–18 m (wspólna z lasem) | przy ulicach: 5,1–10 m to 53,8 %, 2,1–5 m to 32,7 %, > 10 m tylko 8,8 % (Łaska, n = 171) | **nie przenosić wprost na rzędy.** Tab. 3 Łaski obejmuje wszystkie drzewa w transektach przy głównych drogach, także młode samosiewy (klasa 0–2 m); R5 podaje lipy w rzędach 16–17 m. Do sprawdzenia przez world-builder: czy rzędy `OT_OIPR_L` przy drogach regionu C/Dojlidy na kadrach mają 8–18 m. Las bez zmian |
| Odsunięcie pnia od krawężnika | — | mediana 2,5 m (p25 1,5; p75 4,0); śródmieście w chodniku ≈ 1 m z kratą i osłoną | do reguł `claim_street_crowns` / rzędów |
| Trasa C | — | 0 rzędów OSM, 1 drzewo. Na kadrach krótkie rzędy młodych drzew z palikami **za ścieżką** i masy zadrzewień za ekranami | nie generować dojrzałych szpalerów przy Andersa/Maczka |
| Tuja (ADR 0170) | 2,4–3,6 m, narożnik do 4,0 m, szer. 0,8–1,2 m | ‘Smaragd’ 2,5 × 0,7 m po 10 latach, ‘Brabant’ 3,5 × 1,5 m; R5-169 (poprawiony) ≈ 2× słupek ≈ 3 m, wierzchołki stożkowe | wysokości bez zmian. Dodać wariant **niestrzyżony, z pojedynczymi stożkami** (‘Smaragd’), nie tylko z płaskim grzbietem |
| Sezon | — | bezlistny 5 XI–20 IV, rozwój 20 IV–15 V, lato 15 V–25 IX, jesień 25 IX–5 XI (WORKING_VALUE; kadry: 13 III gołe, 20–22 V pełne, 6–11 XI gołe) | do profilu sezonu, gdy powstanie |
| Platan | — | brak we wszystkich źródłach | nie dodawać |

## 6. Errata (blok do wklejenia autorowi; nie blokuje scalenia)

```
R5 street-trees — errata po przeglądzie lidera (REVIEW-2026-11-14-s20-cloud2-r5.md)
E1 (P1) R5-169 (cm20200726084948): „zwarta ściana żywotników (strzyżona od góry, wyższa od słupków
   ogrodzenia o ok. 1/3)” → „zwarta ściana żywotników ‘Smaragd’ z pojedynczymi stożkowymi wierzchołkami
   (nie strzyżona płasko), sięgająca ok. 2× wysokości murowanych słupków ogrodzenia (stoi dalej od kamery
   niż słupki — rzeczywista proporcja jeszcze większa)”. Popraw zestawienie wysokości żywotnika
   w README §4 („ściana 2,0–3,0 m”), jeśli liczono z tego kadru.
E2 (P2) R5-073 i README Luki p. 8: cytat „Przeszkodami w polu widoczności nie są pojedyncze drzewa…”
   to § 82 ust. 4 Dz.U. 2022 poz. 1518 (s. 22), nie § 59.
E3 (P2) R5-167 (cm20200726084244): „wysokość poniżej ogrodzenia, korony jeszcze się nie stykają” →
   „wysokość zbliżona do ogrodzenia panelowego, korony prawie się stykają”.
E4 (P2) fetch.py: files/docs/utd/RDS-2016-0005.zip — HTTP 403 z curl (fs.usda.gov), więc fetch kończy
   się exit 1 (61/62). Dopisz w README/fetch.py, że plik wymaga pobrania przeglądarką, albo podaj
   mirror i sha256. Do tego czasu tabela obwód→H/korona jest nieodtworzona — oznacz w README.
E5 (P2) README „Jak używać”: „rozstaw 7 m” → „rozstaw per rząd: mediana 8,0 m (p25 6,7, p75 9,8);
   7,1 m to mediana wszystkich odstępów (z lukami)”.
```

## 7. Uwagi procesowe
- Brak `REVIEW.md` w katalogu pakietu. Ten przegląd go zastępuje.
- `data/osm_roads.json` (4 MB) jest scommitowany. To pochodna ODbL, dopuszczalna. Można by go zastąpić skryptem i lokalnym PBF, ale nie jest to warunek.
