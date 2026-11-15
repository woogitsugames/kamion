# Przegląd K1 dk65-knyszyn-refs (chmura B, PR #83) — s20, 2026-11-15

**Werdykt: SCAL (z erratą nieblokującą, §6).** Najmocniejszy pakiet tej rundy. Metoda pomiaru przekroju jest opisana i odtwarzalna. Każda liczba ma status, a luki (brak zdjęć korytarza, typ latarni, zawartość wyspy ronda) są uczciwie oznaczone UNVERIFIED. Wszystkie 4 cytaty, które sprawdziłem u źródła, są zgodne.

- Gałąź `origin/research/dk65-knyszyn-refs` @ `b461860fe`. `git diff --stat origin/main...`: 126 plików, +13 604, wszystkie w `research/dk65-knyszyn-refs/` ✓.
- Manifest ma 136 wierszy: SOURCED 89, ESTIMATED 44, UNVERIFIED 3. ID się nie powtarzają. **sha256: 89/89 plików zgodnych** (sprawdził recenzent).
- User-Agent we wszystkich skryptach to `research-client/1.0 (generic)` ✓. Google, Bing, Apple i Yandex nie występują w manifeście, źródłach ani narzędziach ✓.

## 1. Kompletność (SESSIONS-S20-B-PROMPTS, K1 a–g)

| Wymóg | Wynik | Uwagi |
|---|---|---|
| (a) przekrój co ~1 km | **TAK** | 30 przekrojów z ortofoto GUGiK 0,1 m (arkusze 2025-05-25/27), profil + zoom 2×; pobocza, linie, zatoki, bariery. Rowy UNVERIFIED (uczciwie) |
| (b) skrzyżowania, rondo DK65×DW671 | **TAK / częściowo** | Ø osi 17,6 m z OSM. Średnica zewnętrzna, szerokość jezdni ronda i wyspa: UNVERIFIED (ortofoto jest sprzed budowy) |
| (c) S19 / wiadukt w Fastach: ZRID, mapy | **CZĘŚCIOWO** | Są: dokument MI z 10.12.2024, prasa (otwarcie 20.10.2026), ortofoto wiaduktu. **Brak ZRID i map GDDKiA**; komunikat GDDKiA z 14.10.2025 tylko z indeksu wyszukiwarki, oznaczony UNVERIFIED |
| (d) Ełcka | **TAK** | rozstaw linii 6,1–6,4 m (mediana 6,2), asfalt 7,0–9,0 m |
| (e) latarnie LED | **NIE (uczciwie)** | OSM: 0 `street_lamp`; zdjęcia z lat 2009–2012 pokazują słupy betonowe z wysięgnikiem. Typ, wysokość i rozstaw: UNVERIFIED |
| (f) Rynek | **TAK** | ortofoto + 24 kadry Commons; fontanna posadzkowa ok. 6×6 m, pomnik, kościół, pierzeje |
| (g) kolej i szpalery | **TAK** | odległości linii 38 od drogi, brak przejazdów na trasie, 3 szpalery; gatunki UNVERIFIED |
| tabela per kafel | **TAK** | 14 kafli |
| audyt 20 % | **TAK** | seed 20261115, 28 wierszy: 24 PASS, 4 FIX |
| zdjęcia ≥ 1 na kafel | **NIE (luka udokumentowana)** | Panoramax 0 na trasie, KartaView TLS, Mapillary bez tokenu; `data/query_log.json` |

## 2. Co obejrzałem sam (10 zdjęć + 4 wycinki ortofoto, osobno, ≤ 960 px)

| Kadr | Ocena opisu |
|---|---|
| P06 (Knyszyn: jezdnia bez linii, chodnik z czerwonej kostki, słupy betonowe z wysięgnikiem, domy drewniane) | ✓ |
| P07 (UM/biblioteka: 2 kondygnacje + lukarny, dach czerwony, portyk z żółtymi kolumnami) | ✓ |
| P10 (pomnik: brązowa figura na granitowym cokole, plac z szarej kostki) | ✓ |
| P14 (kościół: biała fasada, czerwony hełm, figura, czarne latarnie z dwoma kloszami) | ✓ |
| P22 (DK65 2009: czerwone barierki, przejście, wysepka z jałowcem, zielony drogowskaz) | ✓ |
| P25 (Supraśl, kratownicowy most kolejowy) | ✓ |
| P29 (2×1, oś podwójna ciągła przechodząca w przerywaną, znak ciągu pieszo-rowerowego po P, słupy z wysięgnikami po L) | ✓ |
| P44 (ulica, słupy betonowe, wieża kościoła) | **≈** — „oprawy na wysięgnikach po obu stronach”: wyraźnie widać je tylko po prawej/środkowej stronie |
| P02 (dom: część kremowa i część szaro-brązowa, przejście, chodnik z płyt) | ✓ (dach szary to właściwie łamany/mansardowy, drobiazg) |
| P31 (peron Fasty, budynek z wysokim dachem, latarnia peronowa z 2 oprawami, sieć trakcyjna) | ✓ |
| orto `km26.00_rot` (Obozowa, przekrój 6,8 m) | ✓ na podziałce (10 px = 1 m) linie krawędziowe ok. 69 px od siebie, czyli ~6,9 m, zgodnie z 6,8 m ±0,2 |

Próbę wybrał recenzent ręcznie (różne tematy), nie losował jej.
| orto `zoom_km12.50…14.00` | ✓ km 12,5 obie krawędziowe przerywane; km 13,0 zatoka L z przerywaną; km 13,5/14,0 ciągłe |
| orto `J_rondo_knyszyn_north` | ✓ skrzyżowanie skanalizowane, malowane wyspy, przejścia na 4 wlotach (stan 2025-05-27, nie rondo) |
| orto `J_s19_wiadukt_km10_3_north` | ✓ płyta na przyczółkach, objazd łukiem z biało-czerwonym wygrodzeniem |

## 3. Liczby i cytaty sprawdzone u źródła

| Pozycja | Pakiet | Recenzent |
|---|---|---|
| OSM way 1426801304 (rondo) | Ø osi ~17,6 m, r 8,4–9,1 m, edycja 2026-01-05 | API 0.6: 21 węzłów, r 8,44–9,11 m, Ø 17,54 m, timestamp 2026-01-05T11:42:10Z, `junction=roundabout ref=65` ✓ |
| MI 10.12.2024, „ruchem okrężnym … oświetlenia dedykowanego na przejściach” | cytat | tekst PDF zgodny ✓ |
| MI, „złożyła wniosek o ZRiD … w VII 2024” | cytat | zgodny ✓ |
| MI, „DK 65 … utraci status drogi krajowej” | cytat | zgodny ✓ |
| wartowiedziec.pl, „10,2 km … oddana do ruchu 20 października 2026” | cytat | zgodny ✓ (artykuł z 21.10.2026) |

Próbowałem też odtworzyć z wycinków `km*_rot.jpg` własny profil jasności (bez filtrowania cieni). Piki są zbyt zaszumione, żeby potwierdzić albo podważyć wynik ±0,2 m. Wizualnie rozstaw pasuje do skali kadru. Liczby przekroju pozostają **ESTIMATED**, jak w pakiecie.

## 4. Licencje
Zdjęcia z Commons: CC BY-SA 3.0/4.0 (40), CC0 (1), PD (1), z autorem i URL. Ortofoto: GUGiK, art. 40a PGiK. OSM: ODbL. Prasa: tylko cytaty. ✓. Wyjątek: 15 wierszy bez wpisanej licencji (zapytania i pomiar, bez pliku), patrz errata 6. Marki na zdjęciach (szyldy, reklama piwa) są oznaczone „nie odtwarzamy” ✓.

## 5. Wnioski dla gry (kafle DK65, ADR 0205/0207/0212/0215)
- **Rozstaw linii krawędziowych (oś–oś): 6,0–6,4 m, mediana 6,2 m (n = 25, km 8,8–25,0)**; Obozowa w Knyszynie 6,8 m. Asfalt z opaskami: 7,0–9,0 m. Pas ruchu: 2,9–3,4 m. Pobocze żwirowe: 0,6–1,2 m.
- Ełcka/Studzienna: rozstaw osi linii krawędziowych 6,2 m (ESTIMATED), asfalt z opaskami 7,0–9,0 m. Parametr `width` w ADR 0207/0215 to szerokość jezdni, a linia krawędziowa ma 0,12 m i odsunięcie 0,12 m od krawędzi (ADR 0215 p.1). Przy tej definicji rozstaw 6,2 m odpowiada jezdni ok. **6,5–6,6 m**. Zatem 6,9 m (D65, WORKING_VALUE) jest szersze o ok. 0,3 m, a 7,6 m o ok. 1 m, ale oba mieszczą się w szerokości asfaltu z opaskami. To porównanie liczb, nie werdykt: gdyby zaszła potrzeba zmiany, decyduje właściciel (D65 p.5).
- Linie krawędziowe przerywane na km 11,5; 12,5; 18; 20; 21,65; 22, w pozostałych miejscach ciągłe. Zatoki autobusowe: km 13,0 L, 14,5 P, 19,0 P (peron, żółta barierka), 25,0 P. Bariery stalowe: km 21,0 (przepust) i 27,0 (most).
- **Rondo DK65×DW671: Ø osi 17,6 m (OSM, przeliczone przez recenzenta)**, 4 wloty jednopasowe z wysepkami. Średnica zewnętrzna i wyspa: UNVERIFIED. (Wniosek recenzenta, niepochodzący z pakietu: przy tej średnicy ciągnik z naczepą 13,6 m prawdopodobnie potrzebuje przejezdnego pierścienia wewnętrznego. Do sprawdzenia w ADR.)
- Rondo S19/DK65 na km 16,66: Ø osi ~44 m (OSM, na ortofoto go nie ma). Rondo S16: Ø osi ~41 m, w budowie. S19 otwarta 20.10.2026; stara DK65 traci kategorię krajowej.
- **Latarnie: na DK65 poza terenem zabudowanym brak (0 w OSM, brak cieni na ortofoto km 17–25).** W Knyszynie: słupy betonowe z linią napowietrzną i oprawą na wysięgniku, jednostronnie. Przy kościele: stylizowane czarne, z dwoma kloszami. Wysokość, rozstaw i LED: UNVERIFIED (LED białe według D65 p.8).
- Kolej 38 po lewej stronie: 111 m (km 9) → ≥ 487 m (od km 12). Na trasie nie ma przejazdów kolejowych.

## 6. Errata (nieblokująca; do wklejenia autorowi)
```
1. manifest: data_zdjęcia w formacie ISO (K1-072, K1-073 „Taken on 23 August” — rok?; K1-084 „Taken on 28 May 200…”; K1-086 „19 July 2009, 15:23” → 2009-07-19).
2. K1-101 (P44): „oprawy na wysięgnikach po obu stronach” → „po jednej stronie (P/środek kadru); po L słup bez widocznej oprawy”.
3. (c) dopisać jako lukę: brak ZRID/map GDDKiA dla S19 Krynice–Białystok Zach. i wiaduktu w Fastach (tylko MI + prasa).
4. STATUS WIP1 mówi „obejrzane (miniatury 2×2)” — potwierdzić w README, że opisy powstały z kadrów pojedynczych ≥ 960 px, albo przejrzeć ponownie.
6. 15 wierszy z pustą licencją (K1-046…059 pokrycie zdjęciami, K1-006) — wpisać „zapytanie API / pomiar własny; dane OSM ODbL / GUGiK”.
5. tools/*.py: twarde ścieżki /tmp/… i /workspace/… — sparametryzować (argv) do odtworzenia lokalnie.
```
Nic nie scalono ani nie scommitowano.
