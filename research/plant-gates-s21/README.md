# M63 / K63 — hala A (P11-094) i zakład B (P11-063): bryła, okładzina, bramy

Zadanie: `docs/owner/MISTRAL-TASKS-10.md` § M63 (sesja chmurowa s21; id `K63-NNN`; katalog `research/plant-gates-s21/`). Data: 2026-11-15.
Punktem wyjścia był częściowy wynik Mistrala P20 (`origin/research/mistral-p20-plant-gates`, commit `822bfe317`, katalog `research/mistral/p20-plant-gates/`). Każdy wiersz P20, który przenoszę, ma w kolumnie `p20` adnotację: „przejęte z P20-NNN, sprawdzone”, „FIX …” albo „nie sprawdzone”.
W opisach dla gry nie ma nazw firm: używam „hala A” i „zakład B”, a napisy firmowe opisuję jako „napis firmowy, nie odtwarzamy”. Nazwy własne pojawiają się wyłącznie w tytułach plików Commons i w tagach OSM, czyli jako identyfikatory źródeł.

Pliki:
- `manifest.csv`: 89 wierszy;
- `sources.md`, `audit_20_percent.json`, `STATUS.md`;
- `files/`: 16 kadrów ≤ 1600 px, 3 wycinki ortofoto, 2 mapy wysokości nDSM (ok. 5 MB);
- `tools/`: skrypty.

## 0. Najważniejsze wnioski dla gry

1. **Hala A to nie jedno pudełko.** Wg NMPT 2023 składa się z trzech brył (mapa `files/ndsm_A.png`):
   - **A1**: wysoka hala NE, **18,1 m** (17,7–18,8), dach płaski ze świetlikami co ~9,7 m;
   - **A3**: niższy pas po stronie NW/W, **12,5 m**;
   - **hala S** na południe od łącznika: **jeden dach dwuspadowy z kalenicą E–W**, okap 13,2–13,5 m, kalenica 15,4–15,5 m. P20 podzielił ją błędnie na dwa segmenty, „A2 14,3” i „A4 13,0”.

   LoD1 18,92 m dla całości (z gry; w s21 nie sprawdzałem) pasuje tylko do A1.
2. **Ściana z bramami (P11-094) jest od strony ul. Kuronia (NNE), nie od wschodu.** Ma 83,8 m (OSM): 0–65,8 m od narożnika E to wysoka część A1, a 65,8–83,8 m to niższa część A3 z oknami w dwóch poziomach. **To jest ten „schodek”.**
3. **Bramy w ścianie NNE: 2 sztuki.** Położenie i wymiary (szer. × wys.):

   | brama | położenie od narożnika E | ułamek ściany | szerokość | wysokość |
   |---|---|---|---|---|
   | 1 | 11,9–17,0 m | 0,17 | ~5,2 m | 5,5–6,4 m |
   | 2 | 51,1–57,8 m | 0,65 | ~6,7–7,4 m | ~6,8 m |

   - Bramy są szare, bez okienek, z gęstym poziomym podziałem. Czy to bramy segmentowe, czy rolowane, nie da się rozstrzygnąć z kadru (UNVERIFIED).
   - **Nie mają dojazdu**: przed bramami jest trawiasta skarpa i ogrodzenie (ortofoto + kadry). P20 podawał „płaski asfalt” i to jest błąd.
4. **Okładzina hali A:**
   - jasnoszare panele poziome z modułem ~1,0–1,1 m i ciemnym cokołem ~0,9 m;
   - w części A1 ściany NNE **nie ma pasa okien** (potwierdzam P20);
   - są 4 lampy na wysokości ~8,3 m.
   - Okna występują w części A3 oraz w pionowym pasie przy narożniku E na ścianie ESE.
5. **Zakład B:**
   - **hala główna**: antracytowa, **12,5 m**;
   - **niski pas NW wzdłuż Kuronii**: **5,7–6,3 m**, jasny u góry, ciemny dół, czerwony pas, na dachu ażurowa osłona HVAC; to jest „długa niższa biała hala”;
   - **blok biurowy od Mickiewicza**: 2 kondygnacje, **9,6–10,1 m**, z dwiema antracytowymi skrzyniami na napis firmowy, wyższymi od bloku. To one i hala za nimi dają wrażenie „ciemnej wyższej części frontowej”;
   - doki (≥ 2, numerowane, z czerwonymi osłonami) są na ścianie SE;
   - ogrodzenie ciemne panelowe, brama przesuwna kratownicowa.
6. **Ogrodzenie hali A:**
   - lekka jasnoszara siatka (panele druciane) na cienkich słupkach, u dołu skarpy, ok. 1,5–2,0 m;
   - **białego płotu panelowego nie ma**, **żywopłotu też nie** (P20 podał żywopłot błędnie).
7. **Znak przed kamerą P11-094** stoi ok. **6 m** od kamery, w azymucie ok. 230°, widoczny od tyłu (typ UNVERIFIED). W grze ustawić go w tej odległości.

## 1. Identyfikacja

| | hala A | zakład B |
|---|---|---|
| OSM | way 471492583: 14 boków, obwód 515,7 m, 13 712 m² (P20 ✓) | way 513010463: 6 boków, obwód 450,9 m, 11 173 m² (P20 ✓) |
| ściany OSM | ESE 133,9 m; NNE 83,8 m | NW 151,1 m (Kuronia); SE 138,8 m; W 69,8 m |
| działka (KIEG) | 206101_1.0021.767/20 ✓ | 206101_1.0021.767/29 ✓ |
| budynek EGiB | 1495_BUD wg P20 — UNVERIFIED (KIEG nie zwrócił warstwy budynków) | 1580_BUD wg P20 — UNVERIFIED |
| LoD1 2024 | 18,92 m wg P20 — UNVERIFIED (nie sprawdzone) | 12,72 m wg P20 — UNVERIFIED |
| BDOT10k (kod funkcji), kondygnacje | UNVERIFIED (jak w P20: WFS bez dostępu) | UNVERIFIED |

## 2. Tabela segmentów wysokości

Metoda: nDSM = NMPT 2023-09-15 (0,5 m, EVRF2007) − NMT 1 m (WCS, KRON86). Różnicy układów (~0,1–0,2 m) nie korygowałem. Liczyłem komponenty spójne nDSM > 4 m i ich mediany, a do tego profile co 5–10 m (`tools/py_heights.py`). P20 korzystał z NMPT z WCS. Jego mediany okien powtórzyłem i wyszły w granicach ±0,7 m.

| bryła | H [m] | metoda | P20 | status |
|---|---|---|---|---|
| A1 wysoka NE | 18,1 (17,7–18,8; spadek ku SW ~1 m) | komponent + profil | 18,19 ✓ | ESTIMATED |
| A3 pas NW/W | 12,5 | komponent; kadr P11-094: 0,69 × 18,4 = 12,7 | 12,43 ✓ | ESTIMATED |
| hala S | okap 13,2–13,5 / kalenica 15,4–15,5, kalenica E–W | profil N–S co 6 m | A2 14,32 + A4 12,97 ✗ | ESTIMATED |
| łącznik A1–hala S | 10–12 | komponent | — | ESTIMATED |
| B hala główna | 12,5 (12,5–12,9) | okna P20 powtórzone | 11,94–12,04 (≈) | ESTIMATED |
| B blok biurowy W | 9,6–10,1 | profil 4–10 m od lica | 10,97 ✗ (okno mieszane) | ESTIMATED |
| B niski pas NW | 5,7–6,3 | okno P20 | 5,24 (≈) | ESTIMATED |
| B aneks E | 9–11 | za mało komórek | 8,99 | UNVERIFIED |

## 3. Tabela ścian

| obiekt / ściana | okładzina | cokół | okna | inne | status |
|---|---|---|---|---|---|
| A — NNE (Kuronia) | jasnoszare panele poziome, moduł ~1,0–1,1 m | ciemnoszary ~0,9 m | brak w A1; w A3 dwa poziomy w pionowym pasie | napis firmowy (nie odtwarzamy); 4 lampy ~8,3 m | ESTIMATED / SOURCED |
| A — ESE (parking) | jak NNE | jak NNE | pionowy pas 2–3 okien przy narożniku E | napis firmowy; dalsza część ściany niewidoczna | SOURCED (część) / UNVERIFIED (reszta) |
| A — W ściana części A3 (plac) | — | — | — | na ortofoto naczepy przy ścianie (prawdopodobnie doki) | UNVERIFIED: brak kadru |
| A — hala S, ściany S i W | jasnoszara, ciemniejszy pas poziomy, przybudówki | — | — | linia dachu szczytu W wznosi się (dach dwuspadowy) | UNVERIFIED: kadry rozmyte, z auta |
| A — reszta ścian W | — | — | — | — | UNVERIFIED: brak kadrów |
| B — blok biurowy W/SW | góra kremowa, dół ciemnoszary (klinkier? UNVERIFIED) | — | pasmowe w ciemnych ramach | czerwony pas, 2 antracytowe skrzynie z napisem | SOURCED |
| B — niski pas NW | góra kremowa, dół ciemny | ciemny | rząd okien | czerwony pas, osłona HVAC na dachu, czerwony portal przy narożniku NE | SOURCED |
| B — hala główna | antracytowe panele (N: poziome; S: widoczne pionowe styki) | — | brak widocznych | napis firmowy na szczycie E | SOURCED |
| B — SE | antracyt | — | — | ≥ 2 doki z numerami i czerwonymi osłonami | ESTIMATED |

## 4. Tabela bram

| obiekt | brama | położenie | szer. × wys. [m] | typ / panele / okienka / kolor | rampa / dojazd | status |
|---|---|---|---|---|---|---|
| A | 1 | ściana NNE, 11,9–17,0 m od narożnika E (0,17) | ~5,2 × 5,5–6,4 | gęsty podział poziomy; segmentowa lub rolowana (UNVERIFIED); bez okienek; szara | **brak**: trawiasta skarpa | ESTIMATED |
| A | 2 | ściana NNE, 51,1–57,8 m (0,65) | ~6,7–7,4 × ~6,8 | jw. | **brak** | ESTIMATED |
| A | ? | ściana W części A3 | — | prawdopodobnie doki (naczepy na ortofoto) | plac | UNVERIFIED |
| B | ≥ 2 doki | ściana SE przy narożniku E | UNVERIFIED | ciemne obudowy z numerami, czerwone osłony | plac od SE | ESTIMATED |

- **Metoda dla bram A** (`tools/gates_calib.py`): kalibracja kamery P11-094 na dwóch narożnikach OSM. Wychodzi f = 1170 px przy szerokości 1600 px, czyli HFOV 68,7°, typowo dla telefonu. Pozycje to przecięcie promieni z linią ściany; druga kalibracja (narożnik z NMPT) różni się o ≤ 3 m.
- **Wysokość** liczę ze stosunku pikseli brama/ściana na tej samej pionowej linii, razy 18,4 m (nDSM przy ścianie NNE). Kontrola: wysokość bramy to 5,2–5,9 modułu panelu.
- **Typowe wymiary bram** z kart katalogowych (cytaty w K63-034/035): maksymalnie 8000 × 6000 mm, sekcja 545 mm. Wynik ~6,4 m jest na granicy katalogu. Niepewność wysokości wynosi ±10 %.

## 5. Otoczenie

- **A:** szczegóły w wierszach K63-036…K63-039.
  - ogrodzenie: lekka jasnoszara siatka, 1,5–2,0 m, ok. 8–10 m od ściany NNE, przy chodniku;
  - trawiasta skarpa od cokołu do chodnika, 2 młode drzewka, bez żywopłotu;
  - latarnia z łukowym wysięgnikiem przy jezdni;
  - znak ok. 6 m przed kamerą P11-094.
- **B:**
  - ciemne ogrodzenie panelowe;
  - brama przesuwna kratownicowa od ul. Mickiewicza (2019 i 2024);
  - biało-czerwono-żółte wygrodzenia w pasie Kuronii są drogowe, nie zakładu.

## 6. Najlepsze kadry dla artysty (3 + 3)

- **A:**
  1. P11-094 (`20230903_135016`): cała ściana NNE z bramami, lampami, uskokiem A3 i skarpą;
  2. P11-095 (`20230903_135017`): brama 1 prawie od frontu, ogrodzenie, okna przy narożniku;
  3. P11-122 (`8866`, listopad, wieczór): ściana ESE od parkingu (uwaga: GPS EXIF wypada wewnątrz budynku).
- **B:**
  1. `20230814_182855`: niski jasny pas i ciemna hala za nim, blok biurowy ze skrzyniami napisu. Rozstrzyga pytanie o „ciemną wyższą część”;
  2. `20240623_141331`: blok biurowy od S, hala, doki, brama przesuwna;
  3. `20230814_182816`: okładzina hali, osłona HVAC, czerwony portal.

## 7. Co przejęto z P20, co odrzucono i dlaczego

**Przejęte (sprawdzone):**
- obrysy OSM A i B (P20-001, -013), co do metra;
- działki 767/20 i 767/29;
- A1 18,19 m (P20-004) i A3 12,43 m (P20-006);
- B hala ≈ 12 m (P20-017…019) oraz niski pas NW (P20-020, z korektą +0,5 m);
- okładzina A jako panele poziome, moduł ~1 m, bez pasa okien w A1, bez wyraźnej attyki (P20-024…027, -030);
- napis firmowy (P20-031);
- 2 bramy bez okienek, szare (P20-038, -041, -042);
- 4 lampy (P20-032, z poprawką wysokości);
- ogrodzenie z siatki i brak białego płotu panelowego (P20-051, -053);
- cytaty z kart katalogowych (P20-049, -050; pierwszy poprawiony do brzmienia z pliku);
- odrzucenie kadru P11-093 (P20-063).

**Poprawione:**
- „A2” i „A4” to nie segmenty, tylko jeden dach dwuspadowy hali S (P20-005, -007, -011).
- Ściana z bramami jest **NNE** (Kuronia), nie „wschodnia”. Pozycje bram P20 (0,60 / 0,80 „od końca N”) wzięto z obrazu bez perspektywy. Po kalibracji wychodzi 0,17 i 0,65 od narożnika E (P20-044, -047).
- Wymiary bram 4,5–5,0 × 4,5–5,0 → ~5,2–7,4 × 5,5–6,8 m. Podziału „~5 pionowych paneli” nie ma, podział jest poziomy, a typ jest UNVERIFIED (P20-039, -040, -043, -046).
- „Płaski asfalt przed bramami” → trawiasta skarpa, brak dojazdu (P20-048).
- „Okna: BRAK” nie dotyczy części A3 ani ściany ESE przy narożniku (P20-028).
- Żywopłotu nie ma (P20-057).
- Wysokości ogrodzenia ~2,0 m nie dało się ustalić z kadru 134854 (129 m, a na nim widać wygrodzenie przy jezdni); z bliskich kadrów wychodzi 1,5–2,0 m (P20-052).
- B front 10,97 → 9,6–10,1 m (okno P20 mieszało front z halą). „Ciemniejsza wyższa część” to hala główna i skrzynie napisów, a nie blok frontowy (P20-016, -023).
- Kadry 8865 i 8870 P20 przypisał do A jako UNVERIFIED. Po obejrzeniu: 8865 to samochód nauki jazdy (hali A nie widać), 8870 to inna hala → odrzucone (P20-070, -071).

**Odrzucone lub nie przejęte:**
- „Seria B z 2019 r.” (14 kadrów): obejrzałem wszystkie. **B pokazują tylko 2** (6721, 6724). Pozostałe to domy, przystanek, szkoła, biurowiec, skrzyżowania, a 6726 pokazuje zbiornik sąsiedniego obiektu.
- Element 16,65 m (P20-008) to urządzenia dachowe, nie segment.
- LoD1 i id budynków EGiB P20: nie sprawdzone → UNVERIFIED.
- Kadry odrzucone przez P20, których nie oglądałem ponownie (8872, 8873, 8877, 8880, 124730, 124756, 151306, 151248), nie są ani przejęte, ani liczone.

## 8. Luki

1. **Kadry ≥ 10 na obiekt:**
   - A ma tylko **7** kadrów obejrzanych i przypisanych: 3 dobre z bliska, 2 dalekie, 2 rozmyte z auta;
   - B ma **9**;
   - łącznie obejrzałem **45** kadrów (16 przypisanych, 29 odrzuconych), więc kryterium „≥ 20 obejrzanych” jest spełnione.
   - Źródła: Panoramax i KartaView 0 zdjęć w rejonie (sondy M64/P20), Openverse to lustro Commons, Mapillary bez tokenu.
2. **Ściany A:** W, S i fragmenty ESE bez kadrów z bliska; doki przy części A3 znane tylko z ortofoto.
3. **Typ bram A** (segmentowa czy rolowana) i ich dokładna wysokość (±0,5 m).
4. **LoD1, LoD2, BDOT10k, EGiB budynki** — bez dostępu albo niesprawdzone.
5. **Kierunki kadrów** bez EXIF: tylko P11-094 ma azymut z kalibracji (242,5°).
6. **Doki B:** liczba ≥ 2, wymiary UNVERIFIED.

## 9. Samokontrola

`random.Random(20261116).sample(ids, ceil(89/5) = 18)` → 18 wierszy, **18 PASS, 0 FIX**. Co zrobiłem:
- ponownie obejrzałem 16 kadrów (2 plansze kontrolne) i wycinek bramy;
- policzyłem bramy drugą kalibracją;
- powtórzyłem zapytania OSM i KIEG;
- sprawdziłem, że GPS EXIF kadru 8866 leży w obrysie budynku.

Błędy znalezione przed audytem poprawiłem w trakcie budowy manifestu: pora roku dla 3 września i odległość kadru P11-063. Linki z próby: 13 × HTTP 200/206; pliki `upload.wikimedia.org` dały 429 (limit Commons), ich sha1 są w manifeście.

## 10. Licencje

- Kadry: Commons CC0 (Rakoon).
- Ortofoto, NMPT i NMT: GUGiK (PZGiK).
- OSM: ODbL.
- Karty katalogowe: cytaty faktów; nazwy producentów występują tylko w URL źródła, nie w opisach dla gry.
- Google, Bing, Apple, Yandex i Mapillary nie były używane.
