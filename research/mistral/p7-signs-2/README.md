# P7 — signs-2: aktualizacja oznakowania (rondo Putry / Andersa / Tysiąclecia + nowe korytarze)

**Stan badania: ZAKOŃCZONE (13 listopada 2026 r.). Materiał referencyjny dla projektu Kamion.**

Gałąź: `research/mistral-p7-signs-2` od najnowszego `origin/main` (bazowy commit 8c65107f7f0090e0829f7dbd3638d14f6204ec1b).
Zdjęcia: **NIE w gicie** (katalog `files/` ignorowany przez `.gitignore`) — komplet w `mistral-p7-signs-2-files.zip`
(dostarczono jako załącznik/artefakt przy PR).

## Cel i zakres

1. Aktualny stan bramownic i tablic w rejonie ronda Putry / Andersa / al. Tysiąclecia (oba kierunki) —
   z uwzględnieniem zdjęć 2025–2026 tam, gdzie istnieją w dozwolonych źródłach; weryfikacja aktualności
   treści z 2024 r. (paczka G3).
2. Epoki bramownic Andersa 2019–2026: oś czasu zmian tablicy pasa 2 (Augustów / Kuźnica / Centrum) — `timeline_andersa.md`.
3. Nowe obszary: DK19 (do 15 km od miasta), DK65 (do Bobrownik), DK8 na północ (kierunek Porosły/Jurowce),
   S19 (nowe odcinki 2025–2026), S8 do węzła Białystok Zachód.
4. Manifest zgodny ze schematem research/gptpro/3-s8-signs/manifest.csv (bez konwersji do generatora).

## Wyniki (manifest v4 — 10 pozycji P7-001..P7-010)

| Grupa | Pozycje | Źródło / data | Status odczytu |
|---|---|---|---|
| PUTRY_N_GANTRY (najazd N ronda) | P7-001..003 | Panoramax stanton 2019-09-01 | konstrukcja potwierdzona; teksty **UNVERIFIED** (nieczytelne, 2560 px) |
| TYSIACLECIA_N_E1 (tablica ~200 m ZA rondem) | P7-004 | Commons Rakoon CC0 2024-05-30 | **SOURCED**: `8 E 67 \| Korycin 35 \| Suchowola 49 \| Augustów 87 \| Suwałki 126 \| Kaunas 243`; strzałki UNVERIFIED |
| PUTRY_W_GANTRY (łącznica Maczka→rondo, jazda E) | P7-005, P7-007, P7-008 | Panoramax stanton 2019-08-15 | konstrukcja potwierdzona z 3 kątów (nowa data: +11 dni po epoce G3 2019-08-04); teksty **UNVERIFIED** |
| TYSIACLECIA_NB_GANTRY (za rondem, kier. węzeł S8/S19) | P7-006 | Panoramax stanton 2019-08-15 | **nowa lokalizacja, poza G3** — 2 bramownice z tablicami w oddali; teksty **UNVERIFIED** (odczyt „E77 Gdańsk 120" odrzucony jako sugestia modelu) |
| MACZKA_W_WEST (Maczka W, ~530 m za rondem) | P7-009 | Panoramax stanton 2019-09-01 | konstrukcja z tablicami potwierdzona (3 przejścia); treści **UNVERIFIED** (3 wzajemnie sprzeczne odczyty — wszystkie odrzucone) |
| PUTRY_S_ADVANCE (najazd S ronda) | P7-010 | Commons Rakoon CC0 2022-07-25 | **nowa grupa, poza G3** — tablica kierunkowa na słupie potwierdzona (zielone tło, 2 przejścia); treść **UNVERIFIED** (3 sprzeczne transkrypcje; zgodność tylko: destynacje Augustów/Ełk/Lublin) |

Jedyny w pełni odczytany (SOURCED) tekst w tej paczce to **P7-004**. Pozostałe obecności konstrukcji/tablic
są potwierdzone, ale transkrypcje oznaczono UNVERIFIED — zgodnie z zasadą „nie zmyślać": przy wzajemnie
sprzecznych odczytach modelu wizyjnego odrzucano wszystkie treści (odnotowując sprzeczności w kolumnie uwag).

## Stan 2025–2026 — uczciwie o lukach

- **Bramownice samego ronda Putry w 2025–2026: UNVERIFIED.** W dozwolonych źródłach (Panoramax, Commons,
  Openverse, BIP/GDDKiA/ZDiT) nie ma zdjęć ulicznych korytarzy ronda nowszych niż 2024-08-15 (G3, Mapillary —
  referencja) i 2024-05-30 (P7-004, Commons). Zdjęcia Panoramax z 2025–2026 w rejonie dotyczą ulic bocznych
  (Jarzębinowa, Swobodna, Karakule) lub DK65 SE od Grabówki — poza rondem.
- Seria Commons 2025 (2025-02-08, 2025-03-02, 2025-04-02) po triage geotagów i wzrokowym: kadry miejskie
  0,9–1,3 km od ronda, **poza korytarzami** — wykluczone (udokumentowane w sources.md).
- Dokumenty 2025–2026 (wymiana tablic ZDiT: Ciołkowskiego/Suchowolca; DK65 Fasty; otwarcie S19 Krynice–
  Białystok Zachód) potwierdzają zmiany oznakowania w korytarzach, ale **nie dotyczą bezpośrednio bramownic
  ronda Putry** — szczegóły i linki w `sources.md` i `timeline_andersa.md`.
- Numerów zarządzeń ZDiT dotyczących epok bramownic Andersa NIE ZNALEZIONO w dostępnych BIP — udokumentowane
  jako brak (timeline_andersa.md).

## Metoda

- Źródła wyłącznie dozwolone: Panoramax (CC BY-SA 4.0 — **referencja, nie tekstura**), Wikimedia Commons
  (CC0/CC BY-SA per plik), OSM (geometria/refs), BIP/GDDKiA/ZDiT (dokumenty, art. 4 pr. aut.).
  **Bez Google** (Maps/Street View/Earth/3D Tiles — nieużyte). Mapillary bez tokenu (tylko referencje G3);
  KartaView niedostępne z tego środowiska.
- Odczyty modelem wizyjnym: pytania otwarte (bez szablonów paneli — ograniczenie sugestii), przejścia
  kontrolne na pełnych kadrach i powiększonych wycinkach; sprzeczne odczyty → UNVERIFIED z pełną
  dokumentacją sprzeczności w uwagach.
- Geotriage kandydatów: odległość od osi korytarzy (Tysiąclecia N-S, Andersa E, Maczka W) ≤60 m i odległość
  od ronda ≤900 m (systematyczny skan `commons_near_new`, 323 pliki >2022-07-25).
- Pliki w `files/`: dłuższy bok ≤1600 px (przeskalowanie wyłącznie w dół), bez retuszu; sha256 w manifeście.
- Azymuty: view:azimuth z Panoramax; krzyżowo z EXIF GPSImgDirection i trajektorią GPS. Wykryto błędne
  EXIF GPSImgDirection w serii WB 2019-09-01 (14–21° przy trajektorii zachodniej i azymucie 268°) — EXIF
  odrzucony, udokumentowane w manifeście (P7-009).

## Samokontrola (audit 20%)

`audit_20_percent.json`: losowanie 20% pozycji deterministyczne — `random.Random("Kamion-P7-signs-2026-11-13-v1")
.sample(ids, k)` (seed jawny, powtarowalny). 2 z 10 pozycji (P7-001, P7-005). Testy: obecność pliku i sha256,
rozmiar ≤1600 px, dozwolony status, licencja, spójność url/grupa_źródeł, UNVERIFIED-bez-treści. Wynik: **wszystkie OK**.

## Struktura

| Plik | Zawartość |
|---|---|
| `README.md` | Niniejszy opis, metoda, wyniki, braki. |
| `manifest.csv` | Spis obserwacji P7-001..P7-010 (46 kolumn, UTF-8 BOM, schemat G3 + panoramax_id/sezon/pora_dnia). |
| `sources.md` | Źródła, licencje, daty dostępu, kwerendy, praktyki (429/thumbnaile), triage. |
| `timeline_andersa.md` | Oś czasu epok bramownic Andersa 2019–2026. |
| `audit_20_percent.json` | Samokontrola 20% z jawnym seedem. |
| `notes/status.md` | Dziennik roboczy (commity godzinowe). |
| `files/` | Zdjęcia P7-001..P7-010 (+P7-004_kontekst) — NIE w gicie, komplet w ZIP przy PR. |

## Braki i ograniczenia

- Mapillary: brak tokenu autoryzacyjnego — materiał tylko jako referencja (G3).
- KartaView: API nieodpowiada z tego środowiska.
- Openverse: kwerendy w rejonie Białegostoku nie zwróciły zdjęć bramownic ronda poza Commons.
- Zdjęcia uliczne korytarzy ronda 2025–2026: nie istnieją w dozwolonych źródłach (patrz wyżej) —
  aktualny stan bramownic ronda wymaga weryfikacji w terenie lub po publikacji nowych materiałów.
