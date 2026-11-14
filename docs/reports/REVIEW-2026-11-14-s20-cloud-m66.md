# Przegląd M66 cloud (C66, sygnalizatory świetlne w Białymstoku: tarcze, komory, daszki, warianty) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Wniosek o tarczach jest jednoznaczny i zgadza się z przepisem oraz z kadrami, które obejrzałem sam:
- głowica **nad jezdnią** ma czarną tarczę z białą obwódką;
- głowica **na maszcie lub słupku obok jezdni** nie ma tarczy;
- **białej tarczy nie ma nigdzie.**

Przepisowe wymiary tarczy (850 × 1400 mm, obwódka 40 mm, margines 20 mm, R70) sprawdziłem na rysunku 10.28 Dz.U. Errata dotyczy drobnych statusów i pokrycia trasy C (§4). W §5 jest lista konkretnych rozbieżności z gałęzią Argona `sigplate-0193`, która w obecnej postaci zakłada tarczę na **każdą** głowicę.

- PR #69, gałąź `origin/research/cloud-p23-traffic-signals` @ `864ed388c`. Diff `origin/main...` ma 7 plików, wszystkie w `research/cloud/p23-traffic-signals/` (+546 linii).
- Manifest ma 108 wierszy: 30 przepisów, 35 skrzyżowań (18 skrzyżowań + 17 wariantów), 12 wymiarów, 31 kadrów. Kolumny bloku M66 są kompletne, doszły `url_pliku` i `sha256`.
- Nic nie scalono, nic nie scommitowano, PR bez komentarza. Ten raport nie jest scommitowany.

## 1. Kryteria M66 punkt po punkcie

| # | Wymóg (MISTRAL-TASKS-10 §M66) | Wynik | Dowód recenzenta |
|---|---|---|---|
| 1 | Przepisy zał. 3 Dz.U. 2019 poz. 2311: kształt, komory, Ø, wysokości, tarcza (cytat + strona); WR-D/GDDKiA | **TAK / WR-D nie** | 4 cytaty i rys. 10.28 sprawdzone (§3). WR-D: „nie sprawdzono” (C66-030, UNVERIFIED — uczciwie) |
| 2 | ≥ 12 skrzyżowań z pozycją i cechami; trasa C i okolice | **TAK (18) / trasa C częściowo** | Na trasie C są Rondo Putry, Al. Tysiąclecia/Sokólska, Al. Tysiąclecia/Radzymińska oraz Mickiewicza/Kuronia (P11-063). Brak Sokólska/Wysockiego, Maczka i Andersa poza rondem (README §9) |
| 3 | Wymiary elementów z kart lub norm, inaczej ESTIMATED | **CZĘŚCIOWO** | Tarcza: przepis (SOURCED). Komora: ESTIMATED z proporcji do soczewki 300 mm (jeden odczyt). Głębokość i grubość: UNVERIFIED. Kart katalogowych brak |
| 4 | ≥ 20 kadrów (≥ 5 z tarczą, ≥ 5 bez, ≥ 3 piesi, ≥ 3 na wysięgniku) | **TAK** | 31 kadrów (26 KartaView + 5 Commons), progi spełnione (README §6) |
| — | Wniosek „tarcza: tak/nie/mieszanie” z liczbą i ułamkiem | **TAK** | Nad jezdnią 15/18 (15/15 tam, gdzie widać). Obok jezdni 0/11. Policzyłem ponownie z tabeli §3 — zgadza się |
| — | Warianty → liczba → kadr | **TAK (17)** | S-2, S-6/S-1a i głowica boczna z tarczą mają 0 w próbie, co jest zapisane jawnie |
| — | Kadry: opis, pozycja, kierunek z API, ≤ 40 m od węzła | **TAK** | KartaView: `Heading` z API, kontrola namiarem do węzła (≤ 27°). Commons: UNVERIFIED. Odległości 2,9–33,3 m |
| — | Samokontrola ≥ 20 %, seed | **TAK** | `random.Random(20261114).sample(ids, 22)` odtwarza listę z audytu ✓. 4 poprawki, każda z wycinkiem 5× |
| — | Licencje, zakaz Google, marki | **TAK** | KartaView: CC BY-SA 4.0 jako referencja. Commons: CC0. Marki w kadrach oznaczone „tylko referencja”. Google i Mapillary nie były używane |
| — | fetch.py | **TAK** | `python -I fetch.py` u mnie: **33/33 OK, 74 568 231 B, 0 błędów**. Dla 5 plików Commons sha256 dotyczy miniatur 1920 px (README §9) |

## 2. Co obejrzałem sam (16 obrazów)

- **Kadry:**
  - C66-031 w całości oraz dwa wycinki 3×: głowica nad jezdnią i głowica boczna.
  - C66-032.
  - C66-034 w całości oraz wycinek 3× dwóch głowic nad jezdnią.
  - C66-037, C66-047, C66-049 (w całości oraz wycinek 5×), C66-051, C66-056, C66-057.
  - C66-061 (= P11-063) oraz lokalne P11-077 (ten sam rejon; tylko skraj głowicy w rogu, tarczy nie da się ocenić).
- **Rysunek:** Dz.U. s. 802, rys. 10.28 (render pymupdf 150 dpi).
- **Zgodność z opisami:** wszystko się zgadza. Szczegóły:
  - **C66-031 (wycinek):** czarna tarcza z białą obwódką i cienkim czarnym marginesem na zewnątrz, zgodnie z rys. 10.28. Proporcja wys./szer. ~1,6. **Tarcza leży ZA obudową**: obudowa z soczewkami i daszkami wystaje przed tarczę. Głowica boczna na maszcie nie ma tarczy.
  - **C66-034 (wycinek):** tarcze nad jezdnią są ciemne, bez białej obwódki, tylko nieco szersze od obudowy (×~1,4). Opis po audycie się zgadza.
  - **C66-049 (wycinek 5×):** głowica nad jezdnią ma ciemny zaokrąglony obrys z jasną otoczką. To może być owalna tarcza, ale też obudowa z zaokrąglonymi narożami i halo kompresji JPEG. ESTIMATED zostaje, uwaga w errata 2.
  - **C66-057:** tarcze ażurowe od tyłu, opis trafny.
  - **C66-056:** słupki ocynkowane z dwukomorowym S-5.
  - **C66-061 (P11-063):** głowica na maszcie bez tarczy, wysięgnik wychodzi poza kadr. Status UNVERIFIED dla tarczy nad jezdnią jest więc poprawny.

## 3. Liczby i cytaty sprawdzone u źródła (7)

Plik: `api.sejm.gov.pl/eli/acts/DU/2019/2311/text/I/D20192311-c2.pdf`, sha256 `8abcce24…5c4` (zgodny z manifestem), pdftotext + render.

| # | Cytat / liczba | Strona | Wynik |
|---|---|---|---|
| 1 | „Integralnym elementem sygnalizatora mocowanego nad jezdnią jest ekran kontrastowy” | s. 715 | ✓ |
| 2 | „Ekran musi być barwy czarnej z białą obwódką” | s. 715 | ✓ |
| 3 | nad jezdnią Ø300 → ekran 850 mm; obok jezdni zalecane 650 mm; Ø200 → 520 mm | s. 716 | ✓ |
| 4 | rys. 10.28 a: **850 (650*) × 1400 mm**, obwódka **40**, margines **20**, naroże **R70** | s. 802 (render) | ✓ |
| 5 | „wystająca część daszka ochronnego miała długość co najmniej 200 mm” (zalecenie) | s. 709 | ✓ |
| 6 | sygnalizatory nad jezdnią pochylić „o kąt 5 do 10°” ku nadjeżdżającym | s. 755 | ✓ |
| 7 | czoło komory czarne lub ciemnozielone, tył czarny/ciemnozielony/szary | s. 708 | ✓ |

## 4. Errata (do naniesienia przy scaleniu — nie blokuje)

```
M66-ERRATA (cloud p23), recenzja s20 2026-11-14:
1. C66-089 (wysięgnik 8,8 m, Rondo Putry) status SOURCED → ESTIMATED: źródłem jest ADR 0172 (pomiar z ortofoto 2024 w repo),
   nie dokument ani pomiar tej paczki.
2. C66-073 / C66-049 / C66-095: dopisać w uwagach „na wycinku 5× możliwe też: obudowa z zaokrąglonymi narożami + halo
   kompresji; tarcza owalna niepotwierdzona” (status ESTIMATED bez zmian; wariant „owalna” = 1 wystąpienie niepewne).
3. README §1 i §9: P11-063 – lokalny kadr P11-077 (research/_incoming/mistral-p11-dojlidy-photos-v2) też nie pokazuje głowicy
   nad jezdnią; luka bez zmian (sesja zdjęciowa właściciela albo Mapillary z własnym tokenem).
4. README §9: dopisać, że trasa C bez kadrów to 3 z 7 wymienionych w zadaniu skrzyżowań (Sokólska/Wysockiego, Maczka, Andersa);
   wniosek o tarczach jest regułą z próby miejskiej, nie pomiarem tych skrzyżowań.
```

## 5. Co M66 daje grze — ADR 0193 (Argon, gałąź `sigplate-0193`, niescalona)

Kod porównałem z `origin/sigplate-0193` @ `ff4909ba7`, ostatnim stanem po ponownym fetch (wcześniej czytałem `a633e24ff`; `props.py` i miejsca stawiania są identyczne). Sprawdzone pliki to `tools/worldgen/streetscape/props.py` (`SIGNAL_VARIANTS`, `_signal_head`) i miejscami stawiania w `furniture.py` i `gate3_landmarks.py`.

| element | 0193 dziś | M66 / Dz.U. | działanie |
|---|---|---|---|
| **gdzie jest tarcza** | `plate=True` dla `signal_head`, `signal_head2`, `signal_head1`, `signal_ped`. Ten sam prototyp `signal_head_<lit>` stoi na wysięgniku (`furniture.py:865`, `gate3_landmarks.py:488`) i na słupku obok jezdni (`furniture.py:868/874`, `gate3_landmarks.py:492`) | nad jezdnią TAK (15/15), obok jezdni NIE (0/11), piesi S-5 bez tarczy (C66-031/056) | **wariant bez tarczy dla głowic na słupku i dla `signal_ped`** (np. `signal_head_side`); tarcza tylko w miejscach na wysięgniku |
| rozmiar tarczy | margines 90 mm wokół obudowy → ok. **0,56 × 1,30 m** | **0,85 × 1,40 m** nad jezdnią (rys. 10.28; proporcja 1,6 z kadru C66-080 ✓) | `ph` = 0,425, `pz` = 0,70 (stałe, nie od obudowy) |
| obwódka | 25 mm, kolor `signal_border` [0,62 0,55 0,20] (żółtawy), przy samej krawędzi | **biała 40 mm**, **20 mm czarnego marginesu na zewnątrz**, naroża R70 (SOURCED). Żółtej nie widziano | biel (jak `marking_white`), 0,040 m, wcięta o 0,020 m |
| położenie tarczy | **przed** obudową (y 0,085–0,097), soczewki na licu tarczy | tarcza **za** obudową; obudowa z daszkami wystaje przed tarczę (wycinek C66-031) | tarcza za tylną ścianą obudowy. Tył czarny jest OK; sam ADR 0193 dowodzi, że błędem było jasne pudło za obudową, a nie położenie |
| daszek | `L` = 0,17 m | ≥ 0,20 m (zalecenie s. 709); z kadrów 0,6–0,8 wys. komory ≈ 0,21–0,28 m (ESTIMATED) | 0,22 m (WORKING_VALUE) |
| obudowa | szer. 0,38 m, wys. 3 komór 1,12 m (rozstaw Ø + 60 mm), głęb. 0,17 m | szer. ~0,37 m, wys. ~1,04 m (~0,345 na komorę), ESTIMATED z jednego kadru; głębokość UNVERIFIED | szerokość zgodna; wysokość może zostać (różnica 7 % w granicy ±15 % odczytu) |
| pochylenie głowic nad jezdnią | brak | 5–10° ku nadjeżdżającym (s. 755) | 7° w osi poprzecznej przy stawianiu na wysięgniku (WORKING_VALUE w przedziale przepisu) |
| obudowa — kolor | czarna (`signal_housing`) | czoło czarne lub ciemnozielone; w kadrach wszystkie czarne ✓ | bez zmian |
| Ø soczewek | 300 (S-1), 200 (`signal_ped`, `signal_bike`) | 300 / 200 (s. 702–704) ✓ | bez zmian |
| maszt / słupek | (ADR 0069/0172) | rura okrągła ocynkowana; słupek boczny ~Ø100 mm, słup ramy ~Ø220 mm (ESTIMATED ±15–30 %) | do porównania z `signal_pole` (bez zmiany w 0193) |
| wysokość głowicy bocznej | środek na z + 2,9 m → spód ~2,34 m | skrajnia pionowa 2,0 / 2,2 / 2,7 m (tabela 7.1, s. 757, wg M66) | ✓ w przedziale |
| wysokość głowicy nad jezdnią | środek z + 5,55 m → spód obudowy ~4,99 m (tarcza 1,30 m: ~4,90 m) | 4,5 / 4,7 / 5,5 m (normalna) | ✓; po tarczy 1,40 m spód tarczy ~4,85 m — nadal w przedziale |

ADR 0193 zostawia kolor obwódki jako „UNVERIFIED”. Teraz jest on **SOURCED (biała)**. Dla kadru P11-063 (Mickiewicza/Kuronia, w recenzji 0179 skarga na białą tarczę) wynika z tego, że głowica na maszcie przy kamerze ma być **bez tarczy**. Głowica na wysięgniku ma czarną tarczę z białą obwódką według reguły z próby, bo samego wysięgnika nie widać w żadnym kadrze.

Koszt zmian: tarcza bez głowic bocznych to mniej trójkątów (z 68 głowic regionu C część stoi na słupkach). Jeden dodatkowy prototyp (wariant bez tarczy) daje 0 nowych materiałów.

## 6. Dla lidera

- **Scalić PR #69.** Diff dotyczy tylko `research/cloud/p23-traffic-signals/`. Errata 1–4 nanieść przy scaleniu.
- **Przekazać Argonowi (0193) tabelę §5 przed scaleniem `sigplate-0193`.** Najważniejsze są trzy zmiany:
  1. tarcza tylko na wysięgniku;
  2. 0,85 × 1,40 m z białą obwódką 40 mm wciętą o 20 mm;
  3. tarcza za obudową.

  Po zmianach render kontrolny P11-063, Rondo Putry i kadru z ramą (np. odpowiednik C66-032).
