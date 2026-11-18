# Przegląd M67 rooftop-gsm-s21 po FIX (PR #89, ponowny), s20, 2026-11-15

**Werdykt: SCAL** (z 1 drobną erratą opisu, która nie blokuje). Sprawdzałem tylko 5 punktów bloku FIX z `REVIEW-2026-11-15-s20-cloudB-rooftop-gsm.md` §5. Wszystkie są wykonane. Kadry naziemne dachów z masztami nadal są „częściowo”, bo Commons zwracał 429; jest to zgłoszone jawnie i obejście przez obce CDN nie było ponawiane.

- Gałąź `origin/research/rooftop-gsm-s21` @ `efda3890a`. 4 commity po `6b1a8b8d4`; ostatni zmienia status wysokości z LIDAR z MEASURED na ESTIMATED, bo to dolna granica (słusznie).
- `git diff --stat origin/main...origin/…`: 118 plików, +5 431, **wszystkie `A` w `research/rooftop-gsm-s21/`**, 0 poza katalogiem i 0 usunięć ✓. Gałąź jest 128 commitów za main. Zwykły merge PR jest bezpieczny; checkout katalogu też wystarczy.
- Licencje: Commons CC BY-SA 3.0/4.0, CC BY 3.0, CC0 (atrybucja K67-073…081). GUGiK ortofoto i LIDAR są otwarte. Google: brak ✓.

## 1. Punkty FIX
| # | Punkt | Wynik |
|---|---|---|
| 1 | wysokości dla ≥ 5 dachów (cień / NMPT), min/mediana/max, wieżowiec 9–12 m | **TAK, lepiej niż w FIX**. Zamiast NMPT 0,5 m użyto chmury LAZ z nalotu 2025-04-18 (12 p/m²). Wzór: Z_max w walcu 1 m minus dominanta dachu; niepewność ±0,15 m, wartość jest dolną granicą. Wyniki: Skorupska 17 **4,3 / 4,5 / 11,6**, Dobra 3 **7,7 / 8,6 / 9,6**, Zwierzyniecka 4 **8,6** (n = 1), Kopernika 5A/7 **2,5 / 2,7 / 3,4**, wieżowiec (kontrola) 4,5 / 5,1 / 10,9. Hallera 19 to zmierzony negatyw. Metodę cieni wykonano jako kontrolę (Zwierzyniecka: h > 5,6 m przy el 41,8°, zgodne z LIDAR); dla 3 dachów uczciwie oznaczono ją jako nieczytelną. Do gry przyjęto 9–12 m według M57-FIX ✓. Dodatkowo: sygnał dla M57, że przy środku krawędzi SE jest element 5,25 m, a nie 10–12 m (K67-054) |
| 2 | przecentrowanie wycinków | **TAK**: `ortho_dobra_c` liczony z pozycji LIDAR z zapasem na przechył; 6 nowych wycinków |
| 3 | kadry naziemne bez obcego CDN, sylwetka na tle nieba | **CZĘŚCIOWO, uczciwie**. Pobrano 9 z 15 tytułów (log 429 z czasami, przerwy ≥ 6 s i 60 s, tylko domeny Wikimedia). Pobrane kadry to: wieża Cieszyńska, Waszyngtona 36 (×3, negatyw), Tysiąclecia 10A (×2, negatyw), 3 ulice bez celu. Dachów z masztami z boku: 0 (Zwierzyniecka 2× nadal 429). Sylwetkę zastępczo opisano z profili LIDAR |
| 4 | art. 29 Pb z tekstu urzędowego | **TAK**: t.j. Dz.U. 2026 poz. 524 z API ELI Sejmu (sha256 podany; ISAP 403). Ust. 3 pkt 3 lit. a „> 3 m i ≤ 12 m” → zgłoszenie; ust. 4 pkt 3 lit. a „≤ 3 m” → bez zgłoszenia |
| 5 | kryteria jawnie SPEŁNIONE/NIESPEŁNIONE | **TAK**: README §0, tabela z dowodami |

Uwaga do statystyki: Zwierzyniecka ma n = 1, a wieżowiec jest kontrolą. Pełny rozkład min/mediana/max daje więc 3 dachy, a 5 dachów ma pomiar. Wystarcza to do gry; nie traktuję tego jako blokady.

## 2. Co obejrzałem sam (5 plików, każdy osobno)
| Plik | Ocena |
|---|---|
| `ortho_dobra_c.jpg` | ✓ Cały dach skrzydła NW w kadrze (poprawa względem `ortho_dobra_z`). Maszt z urządzeniami w narożniku NW, koryto kablowe w poprzek dachu do platformy z szafami w środku, drugi zespół przy węźle skrzydeł, PV na sąsiednim skrzydle |
| `shadow_zwierzyniecka4.jpg` | ✓/≈ Maszt z odciągami na podwyższonej części dachu (promieniste linki); budynek wyraźnie przechylony w mozaice, co zgadza się z „do ok. 7 m przy 35 m”. Długości cienia nie mierzyłem ponownie |
| `out/lidar_skorupska17.png` | ✓ Skupisko w środku dachu (c12 11,6) i narożniki c1 4,4 / c29 4,8–4,9 / c2x 4,4. Zgadza się z tabelą: maszt na ramie X i wsporniki 4,35–4,75 (c29 na mapie ma 4,9, czyli h2 lub zaokrąglenie; drobiazg) |
| `out/prof_dobra3_c11_zS.png` | ✓ Pionowy, rzadki ciąg punktów z gęstszą głowicą w górnych ~1,5 m, szczyt 9,55 m (h2 9,16). Wygląda wiarygodnie dla cienkiej rury przy 12 p/m² |
| `commons_Antenna_tower…Cieszynska_.jpg` | **≈** Wieża kratowa w pasy czerwono-białe, zmierzch, różowy pas przy horyzoncie, światła w oknach ✓. **Ale** opis „wszystkie elementy czytają się jako ciemnoszare sylwetki” jest niezgodny z tym kadrem: górna część wieży, panele i czasze są **jasne** (biel i jasna szarość) na tle niebieskiego nieba. Dla gry jest odwrotnie, niż pisze README §3: o zmierzchu panele są jasnoszare, nie ciemne |

## 3. Wnioski dla gry (dach wieżowca ADR 0180 + inne dachy)
- **Dwie klasy wysokości nad dachem**: maszt główny **7,5–11,5 m** (4 dachy) oraz wsporniki i maszty przy attyce **2,5–5,3 m** (każdy dach ze stacją). Wieżowiec: **9–12 m** (M57-FIX).
- Stacje są tylko na części bloków: 8 z 13 wysokich bloków nie ma masztów. Hallera 19 bez urządzeń > 1,3 m.
- Oznakowanie przeszkodowe: szczyt masztu ≥ 45 m npt (Zwierzyniecka 4 ≈ 45,7 m, wieżowiec ≈ 51,9 m) → § 36, światła średniej intensywności; reszta < 45 m → § 35, mała intensywność. To ESTIMATED; czy światła są zamontowane, jest UNVERIFIED.
- Kolor i odczyt na tle nieba: panele jasnoszare matowe (RAL 7035), czasze białe. Elementy ≤ 0,1 m (pręty, kable, odciągi) znikają w odległości, dlatego w LOD-ach bez linek.

## 4. Errata (nieblokująca)
```
K67 errata (research/rooftop-gsm-s21): commons_opisy.json + README §3, kadr Cieszyńska:
„wszystkie elementy czytają się jako ciemnoszare sylwetki” → „górna część wieży, panele i czasze jasne (biel/jasna szarość)
na tle niebieskiego nieba zmierzchu; ciemniejsze tylko elementy w cieniu własnym”. Opcjonalnie: po ustąpieniu 429 dociągnąć
2 kadry ul. Zwierzynieckiej (luka 1).
```
Nic nie scalono ani nie scommitowano.
