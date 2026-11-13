# P1B — uzupełnienie luk paczki P1: zdjęcia tras (Białystok)

**Gałąź:** `research/mistral-p1-route-photos-2` (od najnowszego `main` @ 26f62c3ddcd52430d607c6b3fc78a3f070562897)
**Autor badania:** Vibe (Mistral) — paczka M46/P1B
**Data:** 2026-11-13

Paczka uzupełnia **wyłącznie luki** paczki P1 (141 kadrów, rejon Białostoczek/Jaroszówka/Pietrasze, Białystok 1:1).
Zdjęcia NIE są w repo: katalog `files/` jest ignorowany (patrz `.gitignore`); archiwum `mistral-p1-route-photos-2-files.zip` (37 plików JPG ≤1600 px) dostarczono poza git — lokalizacja w opisie PR.

## 0. Ważne ustalenia wstępne
- **Manifest P1 (`research/gptpro/p1-route-photos/manifest.csv`) nie istnieje w repo** — sprawdzono drzewo main, gałęzie, PR i wyszukiwanie kodu. Deduplikację wykonano **wewnątrz zbioru P1B** po id źródła (KartaView/Commons) i URL; dla Panoramax porównywano po `panoramax_id` i URL (zbiór pusty — patrz sources.md §3).
- **Panoramax: 280 kadrów w obszarze, żaden nie wypełnia luk** (korytarze Andersa/Tysiąclecia/Maczka latem 2019 oraz rejon zachodni 2026) → w `manifest.csv` kolumna `panoramax_id` pusta.
- **Mapillary: pominięty — brak tokenu API (UNVERIFIED), nie zgadywano kluczy. Openverse: 0 wyników** dla wszystkich nazw ulic (patrz sources.md §4–5).
- **Google Maps / Street View / Earth / 3D Tiles: nie użyto w żadnym kroku.**

## 1. Manifest
`manifest.csv` — 47 wierszy (33 OK, 3 REFERENCJA, 11 ODRZUCONE z powodami). Kolumny zgodne z P1:
`id, ulica, punkt_opis, lat, lon, kierunek_deg, data_zdjęcia, sezon, pora_dnia, panoramax_id, jakość_1_5, odrzucone_powód, url_źródła, licencja, autor, data_dostępu, status, uwagi`.
- **Pozycje WGS84** z 6 miejscami po przecinku (KartaView 2.0 API / EXIF Commons).
- **Kierunek_deg**: z pola `heading` KartaView (azymut kamery, stopnie) albo `UNVERIFIED` (Commons bez EXIF GPSImgDirection).
- **Sezon**: liście / bez liści / śnieg (data + weryfikacja wizualna — model wizyjny na miniaturach; 18/37 plików sprawdzonych wizualnie, reszta: sesje jednorodne, patrz §5).
- **Licencje**: KartaView = CC BY-SA 4.0 (referencja, nie tekstura; atrybucja autora w kolumnie `autor`); Commons = CC0. Żadnych licencji NC/ND w zbiorze.
- **Przypisanie do ulicy**: dystans equirectangular (R=6371000) do lokalnego XY, punkt–odcinek z clampem t∈[0,1]; próg **≤25 m do osi way OSM** (ways z OSM API map.json, 45 kafli; dla dwujezdniowych struktur osobne ways). Kadry ≤25 m od osi dwóch ulic (wspólna jezdnia Kombatantów/Sokólska) przypisano do najbliższej osi z adnotacją.

## 2. Tabela pokrycia (dodatki P1B: ulica × kierunek × ujęcia × sezony)

### Luka 1 — ulice z zerem zdjęć (cel: ≥3 ujęcia, oba kierunki)
| Ulica | Ujęcia P1B | Kierunki | Sezony | Status luki |
|---|---|---|---|---|
| Stefana Batorego | 3 (kierowca, KV) | tylko NW ~300° | liście (VI 2021, VIII 2019) | **częściowo** — brak kierunku SE |
| Brzeska | 0 | — | — | **pozostaje** (0 kadrów we wszystkich źródłach ≤60 m) |
| Buska | 0 | — | — | **pozostaje** (0 kadrów, jw.) |
| Olsztyńska | 2 (Commons, poziom drogi) | UNVERIFIED | śnieg + bez liści (XII 2022) | **częściowo** — 2/3 ujęcia, jeden punkt, brak azymutu |

### Luka 2 — drugi sezon (P1: bez liści → szukano liści/śniegu; P1: liście → szukano zimy)
| Obiekt | Ujęcia P1B | Sezon | Status luki |
|---|---|---|---|
| Grodzieńska, Kowieńska, Wołkowyska, Świsłocka, Lidzka | 0 wypełniających (kandydaci: KV 2018-03 i Commons 2024-04 — obie opcje „bez liści”, odrzucone) | — | **pozostaje** — brak liści/śniegu we wszystkich dozwolonych źródłach |
| Wiadukt Al. Tysiąclecia nad torami | 4 (kierowca: jezdnia A ×3, jezdnia B ×1) | **bez liści** (2018-03-23) | **WYPEŁNIONE** |
| Wiadukty Maczka nad torami (A/B) | 0 bezlistnych (kandydaci VI/VIII/X-2016+, VIII-2019, VI-2021 — liście, odrzucone) | — | **pozostaje** |
| Mosty Maczka nad Białą (A/B) | 0 bezlistnych (jw.) | — | **pozostaje** |
| Łącznica DK8 (węzeł Andersa/Maczka) | 0 bezlistnych (jw.) | — | **pozostaje** |

### Luka 3 — Rondo Pamięci Bieżeństwa 1915 r. (cel: 1 kadr kierowcy na wlot/wylot, z azymutem)
| Slot | Kadr(y) P1B | Azymut | Status |
|---|---|---|---|
| Wlot Andersa od SE | P1B-010, 011, 014 | 301–303° | ✓ |
| Wylot Andersa w NW | P1B-012, 015 | 301–302° | ✓ |
| Jezdnia ronda/bypass (dodatkowe) | P1B-013, 016 | 301° / 357,6° | ✓ (kadry dodatkowe) |
| Wlot Andersa od NW | brak | — | **pozostaje** (brak kadrów azymut ~122–180 na tym odcinku) |
| Wylot Andersa w SE | brak | — | **pozostaje** |
| Wlot Bitwy Białostockiej | brak | — | **pozostaje** (brak kadrów kierowcy na ramieniu Bitwy) |
| Wylot Bitwy Białostockiej | brak | — | **pozostaje** |
| Referencja piesza (Commons CC0) | P1B-034 | UNVERIFIED | referencja |

### Luka 4 — poziom kierowcy dla ulic z kadrami tylko pieszymi (cel: ≥2 kadry z jezdni z azymutem)
| Ulica | Kadry P1B (kierowca) | Kierunek | Sezon | Status |
|---|---|---|---|---|
| Bitwy Białostockiej | 2 | S (~175–176°) | bez liści (2018-03) | ✓ |
| Białostoczek | 3 | S/SSE (~165–177°) | bez liści | ✓ |
| Kombatantów | 3 | SSE (~155–159°) | bez liści | ✓ |
| Michała Motoszko | 2 | SSE (~169–172°) | bez liści | ✓ |
| Wileńska | 2 | SSE (~156–157°) | bez liści | ✓ |
| Sokólska | 3 | SSE (~160–163°) | bez liści | ✓ |
| Skidelska | 2 | SSE (~156–158°) | bez liści | ✓ |
| Władysława Bełzy | 0 (referencja piesza P1B-036) | — | — | **pozostaje** |
| Sitarska | 0 (referencja piesza P1B-035) | — | — | **pozostaje** |

## 3. Luki pozostałe (podsumowanie z dowodami)
1. **Brzeska, Buska**: 0 kadrów KV/Pmax/Commons w promieniu ≤60 m od osi (przeszukano 4373 kadrów KV, 280 Pmax, geosearch Commons w obszarze) — do pozyskania wyłącznie nową sesją terenową.
2. **Olsztyńska**: tylko 2 kadry piesze Commons (XII 2022, CC0); brak poziomu kierowcy i azymutu.
3. **Batorego**: wyłącznie kierunek NW (3 kadry z wlotu od Andersy); brak kadru SE.
4. **Grodzieńska, Kowieńska, Wołkowyska, Świsłocka, Lidzka**: brak kadrów z liśćmi/śniegiem (KV: tylko 2018-03-23 bez liści; Commons: 2024-04-01 = przed rozwojem liści).
5. **Wiadukty Maczka nad torami, mosty Maczka nad Białą, łącznica DK8**: brak kadrów bezlistnych (dostępne wyłącznie VII–X 2016, VIII 2019, VI 2021 — wszystkie sezon liściowy; weryfikacja dat ± weryfikacja wizualna próbek).
6. **Rondo**: brak kadrów kierowcy dla 4 slotów (wlot Andersa NW, wylot Andersa SE, wlot/wylot Bitwy) — pełna analiza pozycja+azymut wszystkich kadrów KV ≤250 m od ronda (3 sesje: 2016-08, 2019-08, 2021-06; azymuty wyłącznie 298–359°).
7. **Sitarska, Bełzy**: brak kadrów poziomu kierowcy (Commons wyłącznie piesze; KV 0 kadrów ≤25 m).

## 4. 10 najlepszych kadrów P1B (propozycja do kamer kontrolnych)
| # | id | obiekt | sesja | azymut | uwagi |
|---|---|---|---|---|---|
| 1 | P1B-010 | Rondo — wlot Andersa SE | TMishaaa 2021-06-23 | 303,17° | kierowca, jakość 4/5 |
| 2 | P1B-012 | Rondo — wylot Andersa NW | TMishaaa 2021-06-23 | 301,89° | kierowca, na krawędzi ringu |
| 3 | P1B-007 | Wiadukt Al. Tysiąclecia, jezdnia A | telenavdrives 2018-03-23 | 142° | bez liści — drugi sezon |
| 4 | P1B-008 | Wiadukt Al. Tysiąclecia, jezdnia A | telenavdrives 2018-03-23 | 143° | bez liści |
| 5 | P1B-001 | Stefana Batorego — wlot od Andersy | TMishaaa 2021-06-23 | 298,64° | kierowca, liście |
| 6 | P1B-017 | Bitwy Białostockiej (zach. koniec) | telenavdrives 2018-03-23 | 176° | kierowca, bez liści |
| 7 | P1B-019 | Białostoczek | telenavdrives 2018-03-23 | 177° | kierowca, bez liści |
| 8 | P1B-022 | Kombatantów | telenavdrives 2018-03-23 | 159° | kierowca, bez liści |
| 9 | P1B-025 | Sokólska | telenavdrives 2018-03-23 | 161° | kierowca, bez liści |
| 10 | P1B-030 | Wileńska | telenavdrives 2018-03-23 | 156° | kierowca, bez liści |

## 5. Kontrola jakości i ograniczenia
- **Priorytet selekcji**: 2023+ → spełnione tylko częściowo (najnowsze dostępne kadry kierowcy w rejonie: 2021-06, 2019-08, 2018-03; jedyny materiał 2023+ to piesze serie Commons 2022-12 i 2024-04). Wszystkie wybrane: **dzień, bez dużych pojazdów zasłaniających**; jakość 3–4/5 (drobne rozmycia/brudy obiektywu odnotowane w uwagach: P1B-005, 006, 018).
- **Weryfikacja wizualna**: 18/37 plików sprawdzonych modelem wizyjnym w sesji badania (wszystkie luki 1–3 + próbka luki 4); pozostałe kadry pochodzą z tych samych sekwencji (sesja telenavdrives 2018-03-23, kadry co ~1 s, warunki jednorodne — zweryfikowane kadry sąsiadujące) albo z dat EXIF (Commons). Wyniki w `audit_20_percent.json`.
- **Samokontrola 20%**: jawnie zasiadowany wybór (LCG, seed 20261113, Fisher-Yates, 10 z 47 wierszy = 21,3%) — ponowna weryfikacja pozycji/azymutu/daty wobec API źródła + sprawdzenie obrazu tam, gdzie plik pobrano. Wynik: `audit_20_percent.json`.
- **Wymogi formalne**: JPG ≤1600 px (KartaView lth 1280×720, Commons thumb 1280×720) ✓; pozycje 6 dp ✓; licencje komercyjne ✓ (CC BY-SA 4.0 = referencja/tekstura z atrybucją; CC0 bez ograniczeń).

## 6. Struktura
```
research/mistral/p1-route-photos-2/
├── README.md            (ten plik)
├── .gitignore           (ignoruje files/ i *.zip)
├── manifest.csv          (47 wierszy: OK/REFERENCJA/ODRZUCONE)
├── sources.md           (źródła, licencje, metody, endpointy)
├── audit_20_percent.json (samokontrola 20%, seed 20261113)
└── files/               (NIE w repo — 37× JPG w ZIP poza gitem)
```
