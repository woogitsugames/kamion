# Przegląd M67 rooftop-gsm-s21 (chmura B, PR #89) — s20, 2026-11-15

**Werdykt: FIX.** Pakiet jest uczciwy, nic nie zmyśla, a luki opisuje wprost. Mimo to **nie spełnia 2 z 5 kryteriów akceptacji M67**:
- nie ma rozkładu wysokości masztu nad dachem dla ≥ 5 dachów (jest 1, i to z M57);
- „≥ 15 obejrzanych kadrów” spełnia tylko ortofoto, kadrów naziemnych jest 0.

Punkt 3 (wygląd na tle nieba) w całości ma status UNVERIFIED. Katalog elementów, dane UKE i przepisy są dobre i przydatne.

- Gałąź `origin/research/rooftop-gsm-s21` @ `6b1a8b8d4`: 32 pliki, +1 120, wszystkie w `research/rooftop-gsm-s21/` ✓.
- Manifest: 35 wierszy. User-Agent ogólny ✓. Google nie użyto ✓. W polach `opis_co_widać` nie ma nazw producentów ani operatorów (sprawdzone regexem) ✓. Operatorzy są oznaczeni A/B/C.
- README wspomina „próbę obejścia przez obcy CDN obrazów”, która została zablokowana i nie była ponawiana. Dobrze, że to zgłoszono. Na przyszłość: limit 429 to sygnał, żeby zrobić przerwę albo zostawić WIP, a nie powód do obchodzenia.
- Audyt: seed 20261115, 7/35, 7 PASS.

## 1. Kryteria M67
| Kryterium | Wynik |
|---|---|
| katalog ≥ 8 typów z wymiarami i kolorem | **TAK**: 13 wierszy; anteny sektorowe 2688 / 1499 × 498 × 197 mm (karty), radiolinie Ø 0,3 / 0,6 m, RRU 425 × 296 × 130 mm, rama X ~12 m, koryta 0,4–0,5 m |
| ≥ 5 dachów z rozkładem wysokości masztu (min/mediana/max z metodą) | **NIE**: 5 dachów ma opisany rzut, ale wysokość tylko dla 1 dachu (M57) |
| ≥ 15 obejrzanych kadrów | **CZĘŚCIOWO**: 16 wycinków ortofoto, 0 kadrów naziemnych |
| odsyłacz do M57 bez powielania | **TAK** (ale wysokości trzeba zaktualizować do M57-FIX #88: 9–12 m) |
| brak nazw producentów w opisach | **TAK** |

## 2. Co obejrzałem sam (3 z 16 wycinków, pojedynczo)
| Plik | Ocena |
|---|---|
| `ortho_skor_z` (Skorupska 17, K67-014) | ✓ Rama X przez szerokość dachu, maszt w środku z odciągami, koryta kablowe wzdłuż attyk do narożników, drobne elementy przy narożnikach |
| `ortho_dobra_z` (Dobra 3) | **≈** Wycinek źle wycentrowany, bo budynek przechyla się w ortofoto: dach jest tylko w dolnym pasie kadru (wsporniki i talerze przy narożniku). Dobrze widać za to **cień budynku na trawie** z sylwetką urządzeń dachowych, a z niego da się policzyć wysokość (§4) |
| `ortho_waszyngtona36` (K67-021) | ✓ Dużo urządzeń HVAC i świetliki, masztów z antenami nie widać |

## 3. Źródła
Wykaz UKE (kolumny bez wysokości anteny) oraz progi art. 29 Pb: 3 m i 12 m. Cytat pochodzi ze strony wtórnej, ISAP nie sprawdzano, co pakiet uczciwie zaznacza. Rozporządzenie o przeszkodach lotniczych: § 35, § 36, § 46. Wszystkie pozycje mają URL. Nie sprawdzałem ich ponownie.

## 4. Wnioski dla gry (dach wieżowca, ADR 0180, inne dachy)
- Typowe dla gry: rama X ~12 m z masztem rurowym na odciągach (6–8 linek, kotwienie w promieniu 3–4 m); anteny panelowe jasnoszare matowe 2,7 × 0,5 × 0,2 m lub 1,5 × 0,5 × 0,2 m; czasze Ø 0,3–0,6 m, białe; RRU 0,43 × 0,30 × 0,13 m; koryta 0,4–0,5 m wzdłuż attyk; szafy 2 × 1 m.
- Maszt nad dachem: prawo daje górną granicę 12 m (zgłoszenie dla > 3 i ≤ 12 m). Wieżowiec według M57-FIX ma 9–12 m. Dla innych dachów: brak danych.
- Brak masztów na 8 z 13 sprawdzonych wysokich bloków. W grze nie stawiać masztów na każdym bloku.
- Nie ma potrzeby biało-czerwonego malowania (§ 46: zwolnienie, < 5 m ponad budynek). Światło przeszkodowe małej intensywności na szczycie, gdy < 45 m npt.

## 5. Blok FIX (do wklejenia autorowi)
```
M67-FIX (research/rooftop-gsm-s21, push do PR #89):
1. Wysokości masztów dla ≥ 5 dachów BEZ kadrów naziemnych: metoda cieni z ortofoto.
   - Data i godzina nalotu: skorowidz WFS gugik:SkorowidzOrtofomapy20xx dla arkusza (K1 #83 i M64 #84 tak zrobiły; M64: lot 2025-04-18, wys. Słońca 44,4°).
   - h_maszt_nad_dachem = (L_cień_masztu − L_cień_attyki) × tan(elewacja Słońca); cień mierzyć na płaskiej powierzchni (dach lub grunt), podać px, GSD, elewację.
   - Alternatywnie NMPT 2023 (0,5 m): max w promieniu 1 m od masztu − mediana dachu (maszt rurowy może zniknąć w siatce — wtedy tylko rama/kontener).
   - Podać min/mediana/max dla Skorupska 17, Dobra 3, Zwierzyniecka 4, Kopernika 5A/7, Hallera 19 + wieżowiec (M57-FIX #88: 9–12 m, nie 10–12).
2. Wycinki przecentrować z uwzględnieniem przechyłu budynku (ortho_dobra_z ma dach poza kadrem).
3. Kadry naziemne: po ustąpieniu 429 pobrać tytuły z sources.md (Antenna tower Cieszyńska/Kawaleryjska, Waszyngtona 36 2/3, Tysiąclecia 10A 1/2) — z przerwami ≥ 5 s, ogólny UA; NIE przez obce CDN. Opisać sylwetkę na tle nieba (pkt 3 zadania).
4. Art. 29 Pb — cytat potwierdzić w ISAP (tekst jednolity, URL + ust./pkt).
5. Kryteria w README/STATUS: wypisać jawnie SPEŁNIONE/NIESPEŁNIONE.
```
Nic nie scalono ani nie scommitowano.
