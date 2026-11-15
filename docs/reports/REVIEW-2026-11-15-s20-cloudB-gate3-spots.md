# Przegląd G3 gate3-spots-s21 (chmura B, PR #81) — s20, 2026-11-15

**Werdykt: SCAL (z erratą kosmetyczną, §5).** Pakiet odpowiada na 4 pytania bramki 3 z kadrów otwartych. Minimum 6 kadrów na punkt jest spełnione (a = 6, b = 9, c = 9, d = 6). Wnioski dla gry są konkretne: co usunąć i co dodać. Pakiet słusznie zauważa, że „kopce z cegły” z recenzji P2-7 dotyczą ronda Bieżeństwa, a nie Putry.

- Gałąź `origin/research/gate3-spots-s21` @ `3e6c69f70`: 70 plików, +3 076, wszystkie w `research/gate3-spots-s21/` ✓.
- Manifest ma 38 wierszy: SOURCED 31, ESTIMATED 7. Tworzą go 30 kadrów, 4 wycinki ortofoto i 4 wiersze OSM. **sha256 zgodne we wszystkich plikach** (sprawdził recenzent).
- Licencje: CC BY-SA 4.0 (24), CC0 (4), CC BY 3.0 (2), GUGiK, ODbL. Autor i URL są w manifeście ✓. Nie ma Google, Bing, Apple ani Yandex ✓. User-Agent `research-client/1.0 (generic)` ✓.
- Audyt: seed 20261115, 8/38 wierszy, 6 PASS i 2 FIX (poprawione).

## 1. Kompletność (GPT-CHROME-RESEARCH-S20 p. 1, K2)
| Punkt | Wynik | Pewność wg pakietu, ocena recenzenta |
|---|---|---|
| a) chodnik przy wiadukcie, dojazd do Putry | **TAK**: chodnik na gruncie, trawa ~3,5 m, 2 ekrany przesunięte, szczelina na chodnik 2,5 m | wysoka ✓ |
| b) koniec muru z czerwonym pasem i ekranu | **TAK**: mur maleje do zera z niweletą, kapa schodzi do terenu, ekran NE kończy się pełnym przęsłem na słupie | średnio-wysoka ✓; lico muru NW z pozycji kamery gry UNVERIFIED (uczciwie) |
| c) tablica E przy s0412 | **TAK**: brak tablicy E w 6 kadrach z pasa kamery; niebieska tablica to F-10 dla łącznicy 177861600 (ADR 0144) | wysoka dla „brak E” ✓ |
| d) wyspa Putry | **TAK**: trawa ze żwirową obwódką 2,5–3,5 m, pod pomostami żwir z barierą W, brak kopców | wysoka ✓ |
| ≥ 6 kadrów na punkt, daty, kierunek geograficzny | **TAK** | kurs KartaView liczony z GPS klatek; azymut Panoramax/Commons oznaczony UNVERIFIED, gdy go nie liczono |

## 2. Co obejrzałem sam (6 z 30 kadrów = 20 %, pojedynczo, ≤ 800 px)
| Kadr | Ocena |
|---|---|
| G3-001 (łącznica, po prawej krawężnik, chodnik z kostki na poziomie terenu, trawa, ekran; po lewej estakada) | ✓ |
| G3-009 (Andersa na NW, po prawej ekran zaczynający się przęsłem, żółta barierka) | ✓ (detal przęsła w tej rozdzielczości słabo widoczny) |
| G3-017 (rampa SE schodzi, czerwony pas na koronie opada do ziemi, ścieżka rowerowa czerwona, żółta barierka) | ✓ |
| G3-021 (pomost NE, brak tablic nad jezdnią i na barierach, czerwony pas po lewej) | ✓ |
| G3-028 (Bieżeństwa: niskie strzyżone rabaty krzewów o czerwonobrązowych liściach w pasach trawy, czerwony gzyms) | ✓ |
| G3-034 (wyjazd na N: po lewej krawężnik, pas żwiru, trawa z suchymi placami, słupy sygnalizatorów) | ✓ |

## 3. Liczby i fakty sprawdzone u źródła
| Pozycja | Pakiet | Recenzent (OSM API 0.6, 2026-11-15) |
|---|---|---|
| way 177861600 | tertiary_link, oneway, lanes=2, `turn:lanes=through\|right`, `destination=Warszawa;Ełk` | identycznie ✓ (dodatkowo `destination:ref=19;65`) |
| way 319142225 | ekran `barrier=wall wall=noise_barrier` | ✓ |
| sha256 wszystkich plików | — | zgodne ✓ |

Wymiary z ortofoto (trawa 3,5 m, peron 4,6 m, obwódka żwiru 2,5–3,5 m, wyspa ok. 30 m) mają status **ESTIMATED** ±0,5–1 m. Nie mierzyłem ich ponownie.

## 4. Wnioski dla gry (follow-up bramki 3, P1-1, P1-2, P2-7, P2-10, P2-12)
- **P1-1:** usunąć „wiszącą płytę” chodnika. Chodnik ma leżeć na terenie, teren trzeba dociągnąć do krawężnika i stopy ekranu. Między krawężnikiem a ekranem ma być trawa ~3,5 m. Ekran z białym cokołem na ziemi; 2 linie ekranu przesunięte, ze szczeliną 2,5 m na chodnik.
- **P1-2:** mur rampy NW kończy się klinem do zera razem z niweletą, czerwona kapa schodzi do terenu, ekran rampy kończy się razem z murem. Ekran NE (319142225, 142,7 m) kończy się pełnym przęsłem na słupie z cokołem. Na nosie klina bariera W zawinięta łukiem.
- **P2-12:** **nie dodawać tablicy E** na wiadukcie ani pod nim. Sprawdzić tylko F-10 przy 177861600 (53.152180, 23.166981), licem na SE.
- **P2-7:** wyspa Putry to trawa ze żwirową obwódką, a pod pomostami żwir z barierą W. „Kopce” przy Bieżeństwie zastąpić niskimi rabatami krzewów.

## 5. Errata (kosmetyczna, nieblokująca)
```
1. licencja: ujednolicić zapis „CC-BY-SA-4.0” → „CC BY-SA 4.0” (G3-002, 003, 031, 032).
2. data nalotu ortofoto (G3-007/018/029/037) — do ustalenia ze skorowidza WFS gugik:SkorowidzOrtofomapy20xx (K1 #83 tak zrobił: 2025-05-25/27 dla sąsiednich arkuszy); teraz „UNVERIFIED”.
3. G3-001 pokazuje też bramownicę z tablicami E67 przy łącznicy do Putry — dopisać w uwagach (przydatne dla R2/oznakowania, nie dotyczy s0412).
```
Nic nie scalono ani nie scommitowano.
