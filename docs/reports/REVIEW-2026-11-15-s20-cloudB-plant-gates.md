# Przegląd M63 plant-gates-s21 (chmura B, PR #86) — s20, 2026-11-15

**Werdykt: SCAL (z erratą, §5).** Wszystkie kryteria akceptacji M63 są spełnione:
- jest tabela segmentów wysokości A i B z metodą;
- dla A rozstrzygnięto, ile jest bram, gdzie stoją i jakie mają wymiary;
- każda ściana jest opisana albo oznaczona UNVERIFIED z powodem;
- obejrzano 45 kadrów;
- opisy dla gry nie zawierają marek.

Pakiet uczciwie przejmuje i poprawia częściowy P20: każdy przeniesiony wiersz ma adnotację `p20`, a 10 błędów P20 jest jawnie skorygowanych. Niespełniony jest punkt 6 zadania: zamiast „≥ 10 kadrów na obiekt” jest 7 kadrów A i 9 kadrów B. Luka jest opisana razem z wyczerpanymi źródłami.

- Gałąź `origin/research/plant-gates-s21` @ `adacb9ad8`: 37 plików, +1 235, wszystkie w `research/plant-gates-s21/` ✓.
- Manifest: 89 wierszy. User-Agent ogólny ✓. Google, Bing, Apple, Yandex i Mapillary nie były używane ✓. Kadry to Commons CC0 (Rakoon), do tego GUGiK i ODbL ✓.
- Audyt: seed 20261116, 18/89 wierszy, 18 PASS / 0 FIX. Kadry oglądano ponownie na **2 planszach kontrolnych**, nie pojedynczo, więc to słabszy dowód.

## 1. Kryteria M63
| Kryterium | Wynik |
|---|---|
| tabela segmentów A i B z metodą | **TAK**: nDSM = NMPT 2023 − NMT, komponenty + profile; A1 18,1 / A3 12,5 / hala S okap 13,2–13,5 i kalenica 15,4–15,5 m; B 12,5 / 9,6–10,1 / 5,7–6,3 m |
| A: ile bram, gdzie, wymiary | **TAK**: 2 bramy w ścianie NNE, w 0,17 i 0,65 długości od narożnika E; ~5,2 × 5,5–6,4 oraz ~6,7–7,4 × ~6,8 m (kalibracja kamery na narożnikach OSM) |
| okładzina każdej ściany | **TAK**: opisana albo UNVERIFIED z powodem (brak kadru) |
| ≥ 20 obejrzanych kadrów | **TAK**: 45 (16 przypisanych) |
| ≥ 10 kadrów A i ≥ 10 kadrów B (pkt 6) | **NIE**: A 7, B 9; luka udokumentowana |
| LoD1/LoD2/BDOT (pkt 1) | **NIE**: oznaczone UNVERIFIED („nie sprawdzone”, WFS bez dostępu) |
| bez marek w opisach dla gry | **TAK**: „hala A”, „zakład B”, „napis firmowy, nie odtwarzamy” |

## 2. Co obejrzałem sam (6 z 21 plików, pojedynczo; próba wybrana ręcznie, nie losowo)
| Plik | Ocena |
|---|---|
| `20230903_135016` (P11-094) | ✓ Na ścianie 2 szare bramy bez okienek, bez dojazdu: przed nimi trawiasta skarpa i niska jasna siatka. Jest uskok do niższej części z oknami po prawej i lampy na ścianie. Panele poziome, ciemny cokół. Na ścianie napis firmowy |
| `20230814_182855` (B) | ✓ Niski jasny pas z czerwonym pasem i oknami, za nim ciemna hala. Blok biurowy ma 2 ciemne skrzynie na napis wyższe od bloku. Na dachu osłona HVAC. Na pierwszym planie czerwono-żółte wygrodzenie drogowe |
| `ndsm_A.png` | ✓ A1 18–20 m (NE), pas A3 12–14 m (NW/W), hala S z kalenicą E–W (okap 12–14, kalenica 14–16 m), łącznik 10–12 m |
| `6724_…_November_2019` (K63-059) | ✓ Kuronia na E: po prawej B z czerwonym portalem, ciemna wyższa ściana, brama przesuwna i ogrodzenie panelowe; pochmurno, listopad |
| `20230903_135017` (K63-046, P11-095) | ✓ Brama 1 prawie od frontu, okna przy narożniku na ścianie ESE, parking w głębi, skarpa i ogrodzenie z siatki |
| `20240623_141331` (K63-053) | ✓ Zamknięta brama przesuwna z kratownicą, blok biurowy (jasna góra, ciemny dół, czerwony pas), antracytowa hala, z prawej drobne czerwone elementy przy dokach |

Uwaga: wiersze wymiarów K63-016/040/042/043/044 mają puste `opis_co_widać` (wskazują kadr w innej kolumnie). Dopisać krótki opis albo „patrz K63-0NN” (errata 5).

## 3. Liczby
- Nie przeliczałem ponownie wysokości nDSM. Metodę (mediany komponentów i profile) opisano, P20 dał zgodny wynik ±0,7 m, wszystko ma status **ESTIMATED** ✓.
- Kalibracja bram (f = 1170 px, HFOV 68,7°, druga kalibracja różni się o ≤ 3 m) jest wiarygodna. Rozmieszczenie bram na kadrze P11-094 zgadza się z perspektywą.
- Cytaty z kart katalogowych (maks. 8000 × 6000 mm, sekcja 545 mm) mają URL, a w opisach nie ma nazw producentów ✓.

## 4. Wnioski dla gry (follow-up 0179, `building_part`)
- Hala A to **3 bryły**, a nie jedno pudełko: A1 18,1 m z płaskim dachem i świetlikami co ~9,7 m; A3 12,5 m; hala S z dachem dwuspadowym (okap 13,2–13,5, kalenica 15,4–15,5 m, kalenica E–W). Wcześniejszą wysokość z LoD1 (18,92 m) stosować tylko do A1.
- Ściana z bramami jest **NNE (Kuronia)**, 83,8 m długości. Odcinek 0–65,8 m od narożnika E to A1, a 65,8–83,8 m to A3 z oknami w 2 poziomach (to jest „schodek”).
- Bramy: 2, szare, bez okienek, z podziałem poziomym, **bez dojazdu** (skarpa trawiasta). Cokół ~0,9 m, panele w module ~1,0–1,1 m, 4 lampy na ~8,3 m.
- Ogrodzenie A: lekka siatka 1,5–2,0 m u stopy skarpy, ~8–10 m od ściany. Bez białego płotu panelowego i bez żywopłotu. Znak ~6 m przed kamerą P11-094.
- Zakład B: hala główna antracytowa 12,5 m; niski jasny pas NW 5,7–6,3 m z czerwonym pasem i osłoną HVAC; blok biurowy 9,6–10,1 m z 2 ciemnymi skrzyniami bez napisu; doki na SE; ciemne ogrodzenie panelowe, brama przesuwna.

## 5. Errata (nieblokująca)
```
1. Kryterium „≥ 10 kadrów A / ≥ 10 B” wpisać wprost jako NIESPEŁNIONE (A 7, B 9) w STATUS i w opisie PR.
2. LoD1 2024 (GUGiK opendata, arkusz 2061/2002 — patrz R9) — pobrać i sprawdzić 18,92 / 12,72 m; dziś UNVERIFIED „nie sprawdzone”, choć dane są publiczne.
3. Audyt: ponowne obejrzenie z 2 plansz kontrolnych — dla 5 kadrów z próby otworzyć pojedynczo i dopisać w audit_20_percent.json.
5. K63-016/040/042/043/044: puste opis_co_widać → „patrz wiersz kadru K63-0NN”.
4. Prośba o zdjęcia właściciela: ściany W/S hali A i doki (luka 2) — wpisać do docs/owner/OWNER-REMINDERS lub listy zdjęć.
```
Nic nie scalono ani nie scommitowano.
