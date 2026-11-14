# Przegląd M62-FIX (P19 brama i mur szpitala, kadr P11-129) — s20, 2026-11-14

**Werdykt: SCAL z erratą.** Wszystkie 9 punktów bloku M62-FIX (`docs/owner/MISTRAL-FIXES-12.md`) wykonano zgodnie z obrazem i OSM. Odczyt F01 pokrywa się z §4 i §7 przeglądu M62 punkt po punkcie. Opisy 21 obejrzanych kadrów są zgodne z obrazem (1 drobna nieścisłość). Kryterium „≥ 12 kadrów z ≥ 3 stron” jest **uczciwie oznaczone jako niespełnione** (1 kadr). Erraty są drobne, lider może je nanieść przy scaleniu (§6). Nic nie scalono i nic nie scommitowano. Nie dodałem komentarza w PR. Komentarz Mistrala w PR #53 zawiera surowe `git diff --stat` (5 plików, +390), dane ZIP i „M62-FIX gotowe” ✓.

## 1. Zakres i metoda

- PR #53, gałąź `origin/research/mistral-p19-hospital-gate` @ `93654923a` (merge `origin/main`; commit merytoryczny `3cde5554b`). Zmiany M62-FIX są w 4 commitach: `b971d1dc1`, `5be2683b8`, `95768c5da`, `3cde5554b`. `git diff --stat origin/main...` pokazuje tylko 5 plików w `research/mistral/p19-hospital-gate/` (+390 linii). Zamiast rebase użyto merge, co README jawnie podaje. Na zawartość nie wpływa.
- **ZIP:** `Downloads/mistral-p19-hospital-gate-files-fix.zip` = 8 442 280 B, sha256 `358bde306f9580bf42304a452f85a65daaf79daebd2be35f0f96508df21f3a64`. Zgadza się z komentarzem PR (nazwa, rozmiar, sha256). Archiwum ma 63 pliki. Wszystkie 62 sumy z `files/FILES.md` przechodzą `sha256sum -c` (FILES.md nie zawiera własnej sumy). `files/repo/*` jest identyczne z gałęzią (różnice tylko w CRLF).
- **Oględziny:** 21 kadrów (F01–F14, F16, F19, F20, F21, F24, X6733, X6740) i 7 wycinków F01 (signs, roof_ip, plaques, wall_left, wall_right, b2_bg, A_plate_ip_top), pomniejszonych do ≤ 960 px. Każdy plik czytałem osobno.
- **OSM:** ponownie przeliczyłem z `files/dane/map.osm`, w układzie lokalnym od węzła 2448457849. Seed audytu odtworzyłem przez `python -I`.

## 2. Punkty M62-FIX

| # | Wymaganie | Wynik |
|---|---|---|
| 1 | Kierunek wjazdu ~242°, ulica na E/NE, role dróg, maxspeed=40, szkic | ✓ 874174759 (Żurawia) → brama ma azymut 245,6° geogr. Brama → 874174701 ma 246,2°. W siatce EPSG:2180 wychodzi ~242° (zbieżność γ ≈ (23,19° − 19°) · sin 53,11° ≈ 3,35°). Way 883955523 = [brama, 3323248759, 874174759] (dojazd). Way 73881452 = [874174701, brama] (teren). Żurawia: maxspeed=40, hgv=no, maxweight=3.5 ✓. Szkic §6 jest przerysowany: kamera patrzy na SW, mur jest po lewej (SE), portiernia po prawej (N) ✓. |
| 2 | Kadry innych obiektów, zmyślone opisy, duplikaty, F09, URL F14 | ✓ F05/F06/F15/F16/F19 mają status REJECTED „inny obiekt” i nie występują w żadnym odczycie bramy. P19-056 opiera się teraz na F14 (kontekst ulicy). P19-057 opiera się na F01. Opisy F03 (wnętrze autobusu, kasownik), F12 i F13 (korytarze) oraz F16 (wejście z przezroczystym daszkiem do budynku z blachy) są zgodne z obrazem. F22 i F23 usunięto (0 wystąpień). F09 obejrzano, opis jest trafny. URL F14 poprawiony. |
| 3 | F01: jasna cegła, nakrywa, filar bez daszka, 5 tablic poziomych 2 + 3, wspólny daszek nad 2 filarami N, liczenie warstw | ✓ Wszystko zgodne z obrazem (wycinki plaques, wall_right, roof_ip). Wysokość muru: Mistral podaje 24 warstwy na lewym końcu i 26 przy filarze, czyli 1,80–1,95 m (moduł 75 mm, założenie zapisane). Uczciwie dodaje kontrolę kotwicą STOP (~80 mm, do ~2,1 m). Na wycinku wall_left liczę ~24–25 warstw ✓. |
| 4 | Znaki: C-2 / B-33 „20” / tabliczka na słupku, STOP na filarze, „WJAZD NA PODSTAWIE”, „OPŁATA ZA WJAZD 3 zł”, B-2 osobno w głębi, wysokości z kotwicą, tytuł 2311 | ✓ Zgodne z wycinkiem F01_signs (strzałka w górę, potem w prawo = C-2). Nowe wiersze P19-064 do 067. B-2 (P19-046) jest „osobno, ~20–30 m, własny słupek” ✓ (b2_bg). Wysokości ESTIMATED z kotwicami K1/K2. B-20: P19-064 podaje metodę (ośmiokąt ~278 px na 3840 px ≈ 345 px/m, dolna krawędź ~1,43 m nad asfaltem i ~1,26 m nad stopniem). Na F01 960 px sprawdziłem tylko wiarygodność proporcji (STOP ok. 70 px, dolna krawędź ok. 105–115 px nad stopą filara, co daje ~1,2–1,3 m). Pikseli 3840 px nie mierzyłem. Zakresy normowe są w osobnym wierszu SOURCED (P19-039). Tytuły 2310 i 2311 są w sources.md poprawne. |
| 5 | Tablica IP niebieska, osobny biały słupek, wysokość z kotwicą | ✓ P19-049/050 zgodne z obrazem: tablica przy białym słupku przed prawym filarem, dolna krawędź ~1,3 m, napis — nie odtwarzamy. |
| 6 | Chodnik = kostka, tło: niskie budynki, 2 kominy, bez „4 kondygnacji” | ✓ P19-054 i P19-057/058 zgodne z obrazem (b2_bg). „Min. 4 kondygnacje” usunięto. |
| 7 | Kryterium napisane wprost, bez „interpretacji właściciela”, lista źródeł | ✓ README §4.4 i §10: „Kryterium niespełnione: 1 kadr bramy (F01)”. Fraza „zaakceptowan…” nie występuje. Geosearch r = 300 m ma pełną listę 25 plików z odległościami, w promieniu ≤ 40 m jest tylko F01. Są też kategorie Commons (9 plików oraz 14 + 4 podkategorie), Panoramax 0 (z kontrolą pozytywną), KartaView 0 (z kontrolą pozytywną) i Openverse (1 wynik = F01, 3 × HTTP 504). Mapillary nie był sondowany (brak tokenu), co zapisano jawnie. 4 kadry serii Rakoon 2019 bez geotagu obejrzano (X6731/33/35/40). Opisy X6733 i X6740 sprawdziłem ✓. |
| 8 | ZIP z kadrami, nazwa, rozmiar i sha256 w PR | ✓ (§1) |
| 9 | Samokontrola: nowy seed, ≥ 20 %, porównanie z obrazem | ✓ Seed 20261114 daje 14 z 68 wierszy (20,6 %). Lista odtwarza się co do id. Wynik 12 zgodnych i 2 niezgodne, w tym 9 wierszy z kadru, porównanych na nowych wycinkach A_* (są w ZIP). Niezgodny P19-032 (latarenka) poprawiono. Niezgodny P19-048 Mistral uczciwie zostawił do decyzji lidera (wiersz z listy „nie ruszaj”). |

## 3. Kadry — opis Mistrala a obraz (21 obejrzanych)

Zgodne: F01, F02, F03, F04, F05, F06 (w tym osoba i niebieska naczepa), F07, F08, F09, F10, F11, F12, F13, F14, F16, F19, F21, F24, X6733, X6740. **Drobna nieścisłość: F20.** Mistral pisze „ulica osiedlowa z kostki”, a na zdjęciu jezdnia jest asfaltowa z łatami. Z kostki jest tylko chodnik. To kadr kontekstowy (229 m od bramy), nie trafia do żadnego odczytu bramy. **20/21 zgodnych.** W M62 było 6/14. Opisy nie są szablonowe: każdy ma szczegóły, których nie da się wymyślić bez obrazu (kasownik z naklejką, panel przywoławczy, naczepa za siatką, mikrofony).

**Statusy w manifeście (68 wierszy, przeczytane w całości kolumny status/uwagi):** ESTIMATED 46, SOURCED 14, ESTIMATED (geometria OSM) 3, UNVERIFIED 3, REJECTED 2. Jedyny SOURCED z URL F01 to P19-061 (pozycja kamery z EXIF), co jest poprawne. Wiersze wymiarów z F01 (P19-020, 030, 036, 064) mają w `uwagi` jawne kotwice i założenie modułu 75 mm. Pozostałości M62 (F19, F06, „pionowe”, „4 kondygnacje”) występują tylko w adnotacjach „POPRAWKA M62-FIX: usunięto…”.

**Nie sprawdzono:** F15, F17, F18, X6731, X6735 (nieobejrzane), strony PDF cytatów Dz.U. 2311 oraz piktogram C-2 w załączniku (C-2 potwierdzone tylko kształtem strzałki). Aktualność stanu z 2019-11-10 (opłata, tablica IP) jest UNVERIFIED. **Drugie kryterium M62** („≥ 2 niezależne odczyty” muru, słupa i daszka) również pozostaje niespełnione (1 kadr). README §10 podaje to wprost.

## 4. Licencje i zakazy

Licencje: CC0 (Rakoon), CC BY 3.0 pl (PUW, „referencja, nie tekstura”), ODbL, GUGiK, Dz.U. Google występuje tylko w zdaniu „ZAKAZ — nieużyte” (sources.md, README §2). W manifeście nie ma ani jednego wystąpienia. Napisy instytucji z tablic (kliniki, izba przyjęć, napisy F15/F16) mają adnotację „nie odtwarzamy”. Lustro Overpass `maps.mail.ru` serwuje dane OSM (ODbL), więc to jest OK.

## 5. Czy dane wystarczą dla hospgate-0189 mimo 1 kadru

**Tak, dla widoku od ulicy.** Gracz podjeżdża Żurawią i widzi bramę dokładnie z perspektywy F01. F01 rozstrzyga wszystkie elementy rozpoznawalności: jasny mur, 5 bordowych tablic, wspólny daszek z ciemnej blachy, STOP na filarze, słupek C-2/„20”, niebieską tablicę IP, szlaban z tabliczką opłaty, B-2 w głębi, niskie budynki i dwa kominy. OSM daje geometrię: węzeł bramy, światło 6,1–6,6 m, portiernię, ogrodzenie i oś Żurawiej 16,4 m. Wymiary mają jeden odczyt (ESTIMATED), co wystarcza do kryterium rozpoznawalności (D51/bramka 3).

Ograniczenia, które hospgate-0189 musi oznaczyć jako `WORKING_VALUE`:
- strona wewnętrzna muru i filarów, tył portierni (brak kadru);
- pełny mur ceglany **tylko na odcinku widocznym w F01** (od filara końcowego do lewej krawędzi kadru, ~5–8 m, WORKING_VALUE). Na F14 i F19 ogrodzenie od strony szpitala ma jasne słupki ceglane z przęsłami stalowymi lub z siatki, nie mur pełny. Rodzaj i długość dalszego ciągu wzdłuż fence 883955509 = WORKING_VALUE; nie stawiać pełnego muru wzdłuż całego fence;
- głębokość daszka (występ) oraz jego zasięg w prawo: ciemna blacha biegnie za drugi filar do krawędzi kadru (F01, roof_ip), więc koniec daszka po stronie portierni jest nieznany;
- rozmiar znaków tej instalacji (B-20 średni, C-2 i B-33 po 600 mm to założenie);
- odległość B-2 (~20–30 m z perspektywy).

**Uwaga o układzie:** `tools/worldgen/build_region.py` zapisuje osie jako „X = east (EPSG:2180 x), Z = north (EPSG:2180 y)” (ADR 0003). W scenie trzeba więc użyć **~242°** (siatka), nie 245,6° (geogr.).

## 6. Errata do naniesienia przy scaleniu (lider, bez rundy FIX)

1. **P19-048:** lusterko 14123795058 = **+13,8 E, −3,1 N** (przeliczone przeze mnie: +13,83 / −3,05; zgodne z audytem Mistrala i przeglądem M62 §5). Manifest podaje +14,0 / −2,3. To errata do **naszego** przeglądu M62: w §5 oznaczyliśmy lusterko jako „zgodne”, choć manifest podawał −2,3, i dlatego wiersz trafił na listę „nie ruszaj”.
2. **P19-006 / P19-007** (lista „nie ruszaj”): w manifeście są +0,68 / +3,52 (3000014175) i +1,42 / −3,02 (8220895799). README §3 i P19-031 podają +0,9 / +3,4 i +1,2 / −3,1. Przeliczyłem z `map.osm`: **+0,88 / +3,45** i **+1,24 / −3,07**. Różnice wynoszą ≤ 0,2 m, ale wartości trzeba ujednolicić do przeliczonych.
3. **F20** (README §4.1): „ulica osiedlowa z kostki” zmienić na „ulica osiedlowa asfaltowa z łatami, chodnik z kostki”.
4. Do wiadomości: merge zamiast rebase jest ujawniony w README i nie zmienia diffu.

## 7. Dla lidera

- **Scalić PR #53** z erratą §6 (lider nanosi ją sam albo w commicie po scaleniu). Kryterium ≥ 12 kadrów pozostaje otwarte. Uzupełnią je zdjęcia właściciela z ≥ 3 stron albo Mapillary po udostępnieniu tokenu. Warto dopisać to do listy przypomnień dla właściciela.
- **hospgate-0189:** dane z §7 przeglądu M62 są teraz potwierdzone w manifeście. Do przekazania: wysokości znaków (B-20 ~1,3 m, B-33 ~1,7 m, C-2 ~2,5 m, dolne krawędzie), mur 1,80–1,95 m + nakrywa 0,06 m, spód daszka ~2,7 m, wierzch ~3,0–3,1 m, tablice 0,65 × 0,26 m, kierunek 242° w siatce. Ograniczenia z §5.
- **Errata M47-FIX-2 (P11-129):** C-2 potwierdzone kształtem strzałki na wycinku F01_signs (strzałka w górę, potem w prawo). Piktogramu z załącznika nie porównywałem. W `research/mistral/p11-dojlidy-photos/manifest.csv` (wiersz P11-129) jest „C-1/C-2”. Należy zawęzić do C-2 i odwołać uwagę „C-1” z naszego przeglądu M47-FIX-2.
