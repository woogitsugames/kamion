# REVIEW 2026-11-13 s16b — końcowy świat s16 (main f61025117, render 0029eb520b), niezależna ocena D51

Krytyk: visual-critic (Opus). Materiał: `artifacts/world-int-s16b/pairs/Low-overcast|Low-clear/` (42 + 42), `cmp/` (11), `view/` (kamery kontrolne).
Porównanie trójkami zdjęcie | s16 (`world-int-s16/pairs`, render 64628d9f38) | s16b oraz powiększenia wycinków (znaki, filary, stożki).
Ocena zrobiona przed przeczytaniem raportu `WORLD-INTEGRATION-2026-11-13-s16b.md` i ADR 0159/0160. Wszystko z edytora (Low); **zrzutów z A16 brak**.
Klasyfikacja jak w REVIEW s16: R = kierowca znający miejsce rozpozna; P = układ ok, brak/zła kotwica albo element sprzeczny ze zdjęciem; N = układ nie ten.

## Werdykt
**Pełny pakiet 42 par: FAIL** (15 P). **Wyselekcjonowany pakiet 12 par dla właściciela: PASS warunkowy** — gotowy TAK, z zastrzeżeniem braku pomiaru i zrzutów na A16 (CLAUDE.md zasada 2).
Wszystkie trzy P0 z poprzedniej oceny zdjęte z poziomu N. Nie ma ani jednej pary N. Materiałowo nadal „gra mobilna z 2016” (sterylny beton, jasne spody pomostów, płaskie światło), ale wg D51 to nie blokuje bramki.

| | R | P | N |
|---|---|---|---|
| G3-A (22) | **12** | 10 | 0 |
| G3-B (20) | **15** | 5 | 0 |
| **Razem (42)** | **27** | **15** | **0** |
| poprzednio (s16) | 18 | 21 | 3 |

Agent 0160 (samoocena G3-A): 11 R / 11 P / 0 N — zgodne co do kierunku; różnica: 751431 (u mnie R, bo ściana z paneli weszła dopiero w s16b). Agent 0160 ocenił 339463 jako P — u mnie R.

## Kadry G3-A

| Kadr | D51 | s16→s16b | Trafione | Błędne (priorytet, pozycja) |
|---|---|---|---|---|
| 1259231 | P | P→P (lepiej) | pomost z czerwoną kapą, przyczółek, **doszła bariera W przez pierwszy plan** | **P1** brak dużej okrągłej podpory (zdjęcie x 0,1–0,25) — dominanta kadru |
| 1398898 | R | R→R | podpora x 0,33, bariera na żwirowej wyspie, łuk; fałszywa zielona tablica znikła | P2 podpora kwadratowa vs okrągła |
| 1406533 | P | P→P | rampa, bariery, latarnie | P1 brak bliskiej dwuramiennej latarni x 0,15; zdjęcie pod słońce — mało kotwic |
| 149248 | **R** | P→**R** | **żwirowa wyspa na pierwszym planie**, tablica ulicy daleko x 0,58 (zdjęcie x 0,55), pomost | P2 tablica nieco za duża |
| 177786 | **R** | P→**R** | **podpora z czerwonym pasem x 0,25–0,3** (zdjęcie 0,15–0,35), żwir, wieżowiec x 0,85 | P2 brak bariery W na pierwszym planie |
| 178689 | R | R→R | podpora, wieżowiec | P2 brak bariery na pierwszym planie |
| 201270 | **R** | P→**R** | **duża zielona tablica ulicy na pierwszym planie x 0,12–0,2** (zdjęcie 0,1–0,25), bariera po skosie, żwir, podpory | P2 niebieskie znaki x 0,78 nieco wyżej |
| 223210 | P | P→P | droga ekspresowa, bariery, bloki na horyzoncie x 0,15 | zdjęcie o zachodzie, kadr generyczny |
| 2818555 | **R** | P→**R** | **tablica ulicy x 0,53** (zdjęcie 0,55), żwirowa wyspa, łuk | P2 latarnia dwuramienna x 0,82 słabo czytelna |
| 2948595 | P | P→P | 2 pasy, podwójne bariery, latarnie w pasie dzielącym | brak kotwicy odróżniającej |
| 303305 | P | P→P | prosta, bariery | **P1** bloki na horyzoncie (zdjęcie x 0,12–0,2) → ściana lasu; P2 brak żółtej tablicy x 0,6 |
| 309664 | P | P→P | prosta, latarnie | zdjęcie pod słońce |
| 320215 | P | P→P | prosta | **P1** bloki → las (jak 303305); P2 słup przy kamerze na lewej krawędzi — bez zmian |
| 320326 | R | R→R | D-3 x 0,36, D-6 x 0,64, kostka, krawężnik | P2 plamy trawy z twardą krawędzią na żwirze |
| 3970163 | **R** | P→**R** | **tablica ulicy x 0,5 jak na zdjęciu**, żwir, krawężnik; kikut bariery znikł | P2 tablica dalej niż na zdjęciu |
| 454716 | P | P→P | prosta, bariery | **P1** bloki i topole z lewej → las |
| 482392 | R | R→R (lepiej) | **bariera W schodzi do gruntu** (koniec kikuta w powietrzu), znak F x 0,92, podpory | **P1** masywna podpora/ściana na lewej krawędzi (x 0–0,05) — nadal, na zdjęciu jej nie ma |
| 500263 | R | R→R | znak F, bariera na pierwszym planie, podpory | P2 znak x 0,62 vs 0,78 |
| 504348 | **R** | P→**R** | **tablica ulicy na lewej krawędzi pierwszego planu**, żwir, łuk | P2 czarny prostokąt na prawej krawędzi (x 0,88–1,0, y 0,7) — do identyfikacji; P2 pomost dalej |
| 751431 | **R** | P→**R** | **ściana z wielokątnych paneli z fugami** — jedyna kotwica kadru teraz trafiona, kapa, poręcz | P2 brak żółtego znaku x 0,87 |
| cm109685822 | **P** | N→**P** | droga skręca w prawo jak na zdjęciu, hala z lewej, budynek z prawej | **P1** pół kadru to parking z kostki z białymi liniami miejsc (zdjęcie: chodnik z płyt + trawnik); budynek z prawej beżowy 3-kondygnacyjny vs niebieski biurowiec |
| cm92458760 | **P** | N→**P** | **kominy EC x 0,73/0,98** (zdjęcie 0,77/0,95), słup kratowy x 0,5, wiadukt z lewej, niski budynek z prawej | **P1** brak ronda z klombem, przejścia, skupiska znaków (render: dwa słupy z tarczami tyłem x 0,66/0,93); **P1** bezokienny biały prostopadłościan x 0,1–0,3 — na zdjęciu pylon i drzewa; budynek EC szary zamiast niebieskiego |

## Kadry G3-B

| Kadr | D51 | s16→s16b | Trafione | Błędne |
|---|---|---|---|---|
| 150280 | R | R→R | kominy EC, czerwone budynki z prawej, latarnie | P2 znak po lewej odwrócony tyłem/inny kształt |
| 1528935 | **R** | P→**R** | **A-7 x 0,55** (zdjęcie 0,6), **większe drzewa liściaste z prawej**, niebieska hala, kreskowanie | P2 masa drzew nadal rzadsza niż na zdjęciu |
| 1801374 | P | P→P | ekran z prawej, łuk, domy z lewej | P1 brak dwuramiennej latarni x 0,68 i billboardu x 0,15; **P2** stożek świerka (x 0,27) już nie turkusowy, ale nadal czyta się jak półprzezroczysty zielony stożek |
| 182011 | P | P→P | ekran z prawej, domy | **P1** brak sygnalizatorów na wysięgnikach x 0,35–0,6 (kotwica skrzyżowania); P2 dwa stożki świerków jak wyżej; P2 szeroki trawnik/chodnik z lewej |
| 209622 | R | R→R | mur z blokami (już nie gładka płyta), opaska, przęsło | P2 faktura czyta się jak gabion/kamień łamany, nie bloki z fugą; P2 filary (niżej) |
| 2279538 | R | R→R | blok z lewej, portal na osi, niebieska hala | — |
| 275528 | R | R→R (**zamknięty P1**) | **oba A-30 z tabliczką x 0,17 / 0,83** (zdjęcie 0,22 / 0,82), portal z dwiema tablicami | — |
| 297817 | P | P→P | kominy, dwuramienne latarnie, droga rowerowa | **P1** brak dwóch dużych drzew liściastych z lewej (x 0–0,35) → niebieska hala i biały magazyn zajmują lewą 1/3; P2 portal na osi |
| 326454 | R | R→R | ekrany po obu stronach, biurowiec, słupki ekranu ciemne (były miętowe) | — |
| 3281350 | R | R→R | portal z lewej, latarnia na osi | P2 dwie tablice vs jedna |
| 339463 | **R** | N→**R** | **jezdnia prosto, ekran wzdłuż prawej krawędzi, wiadukt z lewej, zielone drogowskazy na osi** — P0 zamknięty | P1 brak strzałek na jezdni i drzew między wiaduktem a jezdnią; P2 filary |
| 3678296 | R | R→R | ekran, drzewa, latarnie | — |
| 381800 | R | R→R | U-3a, portal, latarnie | — |
| 4312632 | P | P→P | wiadukt z ekranem w poprzek | **P1** D-1 postawiony, ale tarcza widziana prawie z boku (cienki żółty pasek x 0,33) — na zdjęciu frontem; **P1** portal z zieloną tablicą na prawej krawędzi — na zdjęciu go nie ma |
| 468026 | R | R→R | wiadukt z ekranem, portal po prawej, doszedł żółty romb x 0,92 | P2 filary; P2 brak drzew |
| 494288 | R | R→R | łuk, ekran, latarnie, słupki ciemne | P1 bariera mostowa = W z czerwoną kapą (czyta się jak bieżnia) |
| 810525 | R | R→R | mur z blokami (był płaski), opaska, słupki ciemne | P2 faktura jak gabion |
| 810896 | R | R→R | bariera przez pierwszy plan, ekran daleko, sygnalizator | P2 karty liści |
| 837235 | R | R→R | U-3a, blok, portal, niebieska hala | — |
| 962702 | P | P→P (bez poprawy) | ogrodzenie, latarnia, hala | **P1** nowa bariera W stoi między kamerą a jezdnią (render: kamera na trawie za barierą); na zdjęciu kamera na jezdni, bariera za pasem trawy po lewej — poza albo bariera po złej stronie; P2 brak flag na latarni |

## Sprawdzenie regresji z REVIEW s16
- **Turkusowe stożki (1801374, 182011):** już nie turkusowe (paleta świerka ściemniona, ADR 0159 §8), ale obiekt nadal widoczny jako gładki półprzezroczysty zielony stożek z kart (powiększenie Low-clear). Raport s16b pisze „bez różnic” — przeoczone. Spadek z P1 do **P2**.
- **Bariery w powietrzu:** 482392 i 297817 zamknięte (bariera schodzi do gruntu), w 3970163 kikut znikł. Nowy problem: 962702 bariera po złej stronie kamery (P1).
- **Żółte filary (209622, 468026, 4312632, 339463, kamery route-putry):** sprawdzone na zdjęciach w parach. **Agent 0159 ma rację co do barwy**: na 468026 i 209622 filary są ciepłe, ochrowo-brązowe (w cieniu pomostu), na 339463 beżowe. Szary beton byłby błędem. Ale render je przejaskrawia: nasycona musztardowa żółć, jasne głowice, brak cienia pod płytą — na zdjęciu ciemne, matowe, brązowawe. Z P1 do **P2**: jasność ok. −40 %, nasycenie ok. −30 %, głowice tym samym kolorem, okluzja pod pomostem.
- **Znaki 0160:** A-30 ×2 (275528) **trafione**; A-7 (1528935) **trafione**; D-1 (4312632) **postawiony, ale obrócony** — P1 otwarty (agent to zgłasza).
- **Kotwice pierwszego planu G3-A:** tablice ulic na właściwych stacjach (201270, 504348, 3970163, 2818555; fałszywa z 149248 usunięta), żwirowe wyspy (149248, 177786, 2818555, 504348, 3970163), podpora 177786, bariera 1259231 — **weszło**. Otwarte: podpora 1259231, ściana na lewej krawędzi 482392.
- Ekrany: słupki ciemne zamiast miętowych (326454, 494288) — zysk. Mury z fakturą (209622, 810525) i panele (751431) — zysk.

Awanse: 149248, 177786, 201270, 2818555, 3970163, 504348, 751431, 1528935 (P→R); 339463 (N→R); cm109685822, cm92458760 (N→P); w 275528 zamknięty P1 (A-30).
Regresje twarde: brak. Nowy P1: 962702 (bariera po złej stronie, bez zmiany klasy).

## P0 / P1
- **P0 (proces):** APK Low na A16 + zrzuty z telefonu dla kadrów pakietu (min. 275528, 320326, 201270, 150280, 494288). Bez tego bramka 3 nie jest zamknięta. Na świecie P0 brak.
- **P1:**
  1. cm92458760 — rondo z klombem, przejście, znaki frontem; zidentyfikować/usunąć biały prostopadłościan x 0,1–0,3.
  2. cm109685822 — yard_behaton: chodnik z płyt + trawnik zamiast parkingu z liniami.
  3. 4312632 — obrót tarczy D-1 frontem do jezdni; zweryfikować portal na prawej krawędzi.
  4. 182011 — sygnalizatory na wysięgnikach.
  5. 297817 — dwa duże drzewa liściaste z lewej; 1801374 — latarnia x 0,68.
  6. 303305 / 320215 / 454716 — sylwetka bloków na horyzoncie zamiast lasu.
  7. 962702 — bariera po złej stronie kamery (poza albo geometria).
  8. 1259231 — okrągła podpora na pierwszym planie; 482392 — ściana na lewej krawędzi.
  9. 494288 — bariera mostowa DK8 (nadal W z kapą jak bieżnia).
  10. 339463 — strzałki na jezdni.
- **P2:** filary (jasność/nasycenie/okluzja); stożki świerków (karty); faktura murów jak gabion; czarny prostokąt w 504348; podpory kwadratowe vs okrągłe; łaty trawy na żwirze 320326.

## Pakiet dla właściciela (12 par, różne miejsca)
Wariant: **Low-clear** (zdjęcia słoneczne); dla 326454 Low-overcast (zdjęcie pochmurne).

| # | Kadr | Miejsce / kotwica |
|---|---|---|
| 1 | g3-b-275528677534382 | portal z dwiema tablicami + oba A-30 z tabliczką |
| 2 | g3-a-320326319617139 | pod wiaduktem: D-3 + D-6, kostka, krawężnik |
| 3 | g3-a-201270605169291 | zielona tablica ulicy na pierwszym planie, bariera, żwir, pomost |
| 4 | g3-a-177786140912399 | podpora z czerwonym pasem + wieżowiec |
| 5 | g3-a-500263111404933 | znak F pod wiaduktem, bariera na pierwszym planie |
| 6 | g3-a-751431972202262 | ściana oporowa z wielokątnych paneli, kapa |
| 7 | g3-b-150280503737744 | kominy EC, czerwone budynki |
| 8 | g3-b-1528935774382039 | A-7 przy włączeniu, niebieska hala, drzewa |
| 9 | g3-b-837235577143499 | Andersa: U-3a, blok, niebieska hala, portal |
| 10 | g3-b-326454015490067 | ekrany po obu stronach, biurowiec |
| 11 | g3-b-494288258686575 | łuk z ekranem i latarniami dwuramiennymi |
| 12 | g3-b-339463879238809 | wiadukt + ekran + drogowskazy (dawny P0) — opcjonalnie, filary do komentarza |

Rezerwa: 3970163, 2818555, 2279538, 3678296, 381800. Nie pokazywać: oba cm*, 4312632, 962702, 182011, 297817, kadry generyczne pod słońce.

**Pakiet gotowy: TAK** (12 par powyżej) — zastrzeżenia: brak pomiaru i zrzutów na A16; to Low z edytora; G3-A ma 12/22 R, więc pakiet jest
wyselekcjonowany, nie reprezentatywny dla całości; materiały i światło świadomie odłożone (D51).

## Oceny 1–10
| Kategoria | s16 | s16b | Uwagi |
|---|---|---|---|
| Rozpoznawalność D51 — G3-B | 7 | **8** | 15/20 R; A-30, A-7, 339463 trafione |
| Rozpoznawalność D51 — G3-A | 4 | **6** | 12/22 R; pierwszy plan pod wiaduktem trafiony; kadry ekspresówki generyczne, horyzont bez bloków |
| Skala i proporcje | 6 | 7 | tablice i znaki na właściwych stacjach i w skali |
| Światło i ekspozycja | 3 | 3 | jasne spody pomostów, brak AO |
| Materiały | 3 | 4 | panele, mury, ciemne słupki ekranów; filary przejaskrawione |
| Zużycie i osadzenie | 3 | 3 | sterylnie |
| Powtarzalność | 6 | 6 | — |
| Polskie realia | 6 | 7 | A-30/A-7/D-3/D-6/F/U-3a OK; D-1 obrócony, brak sygnalizatorów 182011 |
| Artefakty | 5 | 6 | kikuty zamknięte; stożki z kart, bariera po złej stronie 962702 |
