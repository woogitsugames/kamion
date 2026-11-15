# Przegląd M64 krywlany-airfield-s21 (chmura B, PR #84) — s20, 2026-11-15

**Werdykt: SCAL (z erratą, §5).** Pakiet dobrze uzupełnia M58 i niczego z niego nie dubluje (tabela uzgodnienia w §7 README). Geometria widoku ma jawne wzory, NMPT jako powierzchnię przeszkód i 8 punktów z wynikiem liczbowym. Kamery kontrolne mają współrzędne WGS84, EPSG:2180 i lokalne. Jedyny niespełniony wymóg ilościowy, **≥ 12 kadrów z dróg i od płotu** (jest 10), jest jawnie opisany jako luka razem z przebiegiem wyszukiwania.

- Gałąź `origin/research/krywlany-airfield-s21` @ `e3b02be5d`: 56 plików, +5 728, wszystkie w `research/krywlany-airfield-s21/` ✓. Inny katalog niż w bloku (`research/mistral/p21-…`), ale zgodnie z K4 z SESSIONS-S20-B-PROMPTS.
- Manifest: 92 wiersze (SOURCED 41, ESTIMATED 36, UNVERIFIED 15). User-Agent ogólny ✓. Google, Bing, Apple, Yandex i Mapillary nie były używane ✓.
- Licencje: Rakoon CC0 (21), kadry 2011–2012 CC BY-SA 3.0 z dopiskiem „referencja, nie tekstura”, GUGiK, ODbL, AIP (tylko fakty) ✓.
- Audyt: seed 20261115, 19/92 wierszy, 17 PASS / 2 FIX. Ponownie przeliczono geometrię R2 i F3.

## 1. Kryteria akceptacji M64
| Kryterium | Wynik |
|---|---|
| 8 punktów widokowych z liczbą i wzorem | **TAK**: R1–R5, F1–F3, wzory w §3, `tools/viewgeo.py`; dodatkowo skan płotu (63 punkty) |
| ≥ 3 kamery z WGS84 i azymutem | **TAK**: 4 kamery (`krywlany_runway` potwierdzona, `_alt`, `road_p11_080`, `road_truck`) |
| nawierzchnia: AIP + ortofoto z arkuszem | **TAK**: AIP CONC/ASPH; arkusz N-34-107-C-b-3-4 z 2025-04-18, GSD 0,05 m |
| obiekty z pozycją i id | **TAK**: hangary, LPR, wiatrowskazy, brama, parking, hala namiotowa (brak w OSM, UNVERIFIED) |
| ≥ 12 kadrów z dróg i od płotu | **CZĘŚCIOWO**: z dróg 10, łącznie 18; luka opisana (Panoramax 0, KartaView 0, Commons wyczerpany) |
| brak dublowania M58 | **TAK** |

## 2. Co obejrzałem sam (7 z 31 plików, pojedynczo; próba wybrana ręcznie, nie losowo)
| Plik / wiersz | Ocena |
|---|---|
| `20200726_082250` (K64-068, rondo) | ✓ Wyspa trawiasta, biało-czerwone tablice prowadzące, w tle za płotem hangar z ciemnym dachem, pole, las |
| `20230814_175446` (K64-065, Dywizjonu 303 na E) | ✓ Latarnie dwuramienne, droga rowerowa i chodnik z kostki, zielony płot panelowy, skoszona trawa, biały budynek w oddali. **≈** „dwujezdniowa”: w kadrze widać jedną jezdnię 2-pasową i pas po lewej (do sprawdzenia) |
| `Krywlany_…_Stary_hangar` (K64-026/078) | ✓ Ciemny dach dwuspadowy, szary drewniany szczyt z pasem okien, niebieskie wrota z desek, szybowce w środku, trawa z kwiatami |
| `ortho_windsock1_005` (K64-032) | ✓ Biały pierścień, cień masztu z rękawem, jasny stożek u podstawy |
| `20200726_082324` (K64-067, P11-080) | ✓ Biało-czerwone słupki z łańcuchami, płot panelowy, skoszona trawa, mały żółty i mały biały samolot, stary hangar z ciemnym dachem, szopa z czerwonobrązową ścianą. Przęsła w pasie dzielącym są raczej pomarańczowo-czerwone niż „żółte” (drobiazg) |
| `20230814_174527` (K64-066, rondo) | ✓ Wyspa z trawą, A-7, C-12, tablice prowadzące, banery na płocie, linia lasu („rząd słupków” w 800 px słabo czytelny) |
| `ortho_rwy_mid_005` (K64-002) | ✓ Jednolity jasnoszary asfalt z podłużnymi pasmami, górna linia krawędziowa, kreska osi, groty przy lewej krawędzi; łat brak |

## 3. Liczby sprawdzone u źródła
| Pozycja | Pakiet | Recenzent (OSM API, 2026-11-15) |
|---|---|---|
| stary hangar, way 304300294 | 21,6 × 40,6 m | boki 21,7 / 40,7 m, `aeroway=hangar` ✓ |
| pas, way 958211700 | 1350 × 30 m (AIP, M58) | `ref=09R/27L length=1350 width=30 surface=asphalt` ✓ (OSM podaje asphalt, AIP CONC/ASPH) |

Liczb z AIP (strip 1470 × 150, 900 × 225) nie sprawdzałem ponownie; w pakiecie mają cytat ze stroną, a audyt pobrał kartę ponownie. NMPT (korona 1,2–1,6 %, spadek 0,34 %, kalenica 8,5 m) oznaczono jako ESTIMATED z metodą ✓.

## 4. Wnioski dla gry (ADR 0196 i follow-up 0179)
- **Z dróg publicznych pasa praktycznie nie widać** (R1/R4/R5 zasłonięte; R2/R3/F2 na granicy: < 1 px, a trawa ≥ 0,1 m zasłania). Dowód pasa daje tylko kamera przy płocie NE: `krywlany_runway` (53.101282, 23.185276, heading 252,5°, oko 1,7 m) jest potwierdzona, 31/31 przekroju, ok. 16 px przy fov 14°. Dodać `krywlany_runway_alt` (53.101691, 23.184993, ~240°).
- Teren: spłaszczyć nasypy ~2 m z NMT 2018 przy pasie (w NMPT 2023 ich nie ma), inaczej kamera pasa dostaje fałszywą przesłonę.
- Pas: jasnoszary, jednolity, bez łat `asphalt_worn`; korona 1,2–1,6 %, spadek 0,34 % (W→E w górę). Droga kołowania W: 15,4 m, żółta oś, bez linii krawędziowych.
- Z drogi widoczny jest tylko **stary hangar** 21,7 × 40,7 m, okap ~4 m, kalenica ~8,5 m, ciemna papa, szczyt z szarych desek, niebieskie wrota. Do tego rękaw wiatrowskazu przy hangarze, pierścień Ø 17,4 m, maszt 3,8–4,5 m.
- Hali namiotowej (ok. 30 × 20,5 m) nie stawiać bez nowego dowodu.

## 5. Errata (nieblokująca)
```
1. README §6/STATUS: wpisać wprost w kryteriach „≥ 12 kadrów z dróg/płotu: 10 — NIESPEŁNIONE (luka źródeł)”; jest, ale tylko w Lukach.
2. K64-065: sprawdzić „dwujezdniowa” (w kadrze 20230814_175446 widać jedną jezdnię 2-pasową + pas z lewej).
3. 5 wierszy z pustą licencją (wiersze geometrii/kamer) — wpisać „pomiar własny (ESTIMATED), dane GUGiK/OSM”.
4. Hala namiotowa: dopisać do „Luk” prośbę o zdjęcie właściciela (D64: właściciel może zrobić zdjęcia).
```
Nic nie scalono ani nie scommitowano.
