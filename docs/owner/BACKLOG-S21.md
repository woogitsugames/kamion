# BACKLOG S21 — jeden backlog otwartych punktów

- **Data:** 2026-11-14. **Baza:** `origin/main` @ `6dc816c` („docs: cloud3 prompts (X1/X2/Y1/Y2)”).
- **Zakres źródeł:** wszystkie recenzje `docs/reports/REVIEW-*.md` z sesji s15–s20 (53 pliki); sekcje „Otwarte/Open/Konsekwencje” wszystkich `docs/adr/*.md` (wyciąg lidera s21); follow-upy s19–s20 z `HANDOVER.md` (wyciąg lidera s21). Recenzje czytane sekcjami: werdykt, P0/P1/P2, otwarte, follow-up, „fakty dla agentów”; tabele liczb pominięte.
- **Wierszy:** 95. Dokument tylko porządkuje istniejące ustalenia — nic tu nie jest nowym pomiarem.

## Legenda

- **Źródła (skróty):** `R:<tag>:<linie>` = `docs/reports/REVIEW-2026-11-1x-<tag>.md` (np. `R:s20-0183:12` = `docs/reports/REVIEW-2026-11-14-s20-0183.md:12`); `A:<nnnn>:<linie>` = `docs/adr/<nnnn>-*.md`; `H:<linie>` = `HANDOVER.md` na `6dc816c`; `G:<n>` = `docs/reports/GATE-<n>.md`. Linie sprawdzone `grep -n`/`awk NR` na bazie.
- **Priorytet:** P0/P1/P2 dosłownie z recenzji/ADR. `*` = recenzja/ADR nie nadaje priorytetu — nadany przez autora backlogu (wpływ na bramkę → P1, reszta P2). `↑` = źródła różnią się, wzięty najwyższy.
- **Status:** `otwarte` — brak dowodu zamknięcia; `w toku (gałąź)` — gałąź na `origin` albo zlecenie w HANDOVER; `prawdopodobnie zamknięte (dowód)` — późniejsza recenzja/ADR/HANDOVER/commit na `origin/main` mówi, że naprawione; `do weryfikacji` — późniejsze źródło sugeruje zmianę, ale bez jednoznacznego zamknięcia.
- **Wielkość:** S ≤ ½ dnia agenta, M ≈ 1 agent-sesja, L > 1 sesji / wiele agentów (szacunek autora backlogu, `WORKING_VALUE`).
- **Obszary:** świat C (region `bialystok-industrial-c`), Dojlidy (region `bialystok-dojlidy`), ciężarówka (model/oświetlenie zestawu), fizyka, rendering (oświetlenie, niebo, shadery, noc), audio, UI (HUD, nawigacja), perf (telefon, pomiary, GC), research (źródła, paczki Mistral/GPT, licencje).

## Backlog

### świat C (29)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-001 | świat C | Wymiary znaków pionowych (romb/kwadrat, B-20, folia typ 2, U-4a, tabliczki T) + regeneracja i visual QA kamer znaków | R:s15-mistral-r3:68-70; R:s16-mistral-r4:11,72 | P2* | otwarte (wymiary scalone #24 — R:s16-mistral-r4:11; U-4a/tabliczki T i QA bez dowodu) | S |
| B-002 | świat C | `p21_hatch` 0,24/0,39 i 0,60/0,98 m — decyzja właściciela, potem zdjąć xfail | R:s15-mistral-r3:71-73 | P2* | otwarte (P-11 i łącznice scalone #25 — R:s16-mistral-r4:12) | S |
| B-003 | świat C | Zdublowane zapory edge-west — poprawka w C# `WorldEdgeBuilder.ReadExits`; zdjęcie xfail wolnych końców barier po regeneracji | R:s16-mistral-r5:90-91 | P2* | otwarte | S |
| B-004 | świat C | Walidator świata: „drzewa w jezdni” (53) sprawdzić na kamerach | R:s16-mistral-r6:115 | P2* | otwarte | S |
| B-005 | świat C | D51 „ulice domów wyraźnie gęściej zielone” niespełnione na Low/A16; korony „parasol na gołym pniu” zamiast lipy/klonu | R:s16-codex-0154:10,40-41,59 | P1* | otwarte | M |
| B-006 | świat C | Tablice Putry: ujednolicić epokę (2024+): bramownica A — jedna tablica 3-wierszowa z „675 Centrum”, bez wysięgnika B; portal N/C — dodać mały środkowy panel „↑ 675 Centrum”, jeśli brak | R:s16-gptpro-g2-g3:76; R:s16-research-pack-02:209-211; R:s17-mistral-r8-p7:7-8,16 | P1* | otwarte (brak dowodu wykonania) | S |
| B-007 | świat C | Kamery kontrolne: wysokość kadrów Panoramax (~1,3–1,5 m) vs oko kierowcy ~2,5 m; kadry 2019 tylko do geometrii; nowe kadry P1B-007/020/019/027/018/010/003 | R:s16-research-pack-02:203-206; R:s17-mistral-r8-p1b:49-61 | P2* | otwarte | S |
| B-008 | świat C | Sygnalizacja i meble wg P9/M50: `signal_pole` 4,3 m, wysięgnik ≥ 5,50 m, żerdź 12,0 m, hydrant 0,65 m, szafki, stojak U 0,80×0,80, słupki biało-czerwone ~1 m (WORKING_VALUE/proxy) | R:s16-research-pack-02:214-221; R:s17-mistral-r8-p6p8p9p5:77,177 | P2* | otwarte (część mogła wejść w 0162/0193 — brak dowodu w recenzjach) | M |
| B-009 | świat C | Graf: skrajnia domyślna 4,50/5,00 m (brak B-16 pod Putry/Wolnej Ukrainy/Żołnierzy Wyklętych/S8), reguła sprzeczności tagów, e-TOLL, korekta G10 „B-20 = STOP” | R:s16-research-pack-02:223-227; R:s17-mistral-r8-p6p8p9p5:52 | P2* | otwarte | S |
| B-010 | świat C | Zieleń Al. Tysiąclecia po przebudowie: młode palikowane drzewa (~5/100 m), horyzont = niski pas drzew + słupy WN, zadrzewiona skarpa N od bloków; Andersa — mieszanka klonów (nie aleja) | R:s16-research-pack-02:229-234; R:s17-mistral-r8-p10:55-59 | P2* | otwarte (las/horyzont częściowo w 0170/0187 — patrz wiersze lasu) | M |
| B-011 | świat C | Budynki: dachy skośne domów z OSM `roof:shape`/reguł; drewniane domy podlaskie tylko `authored_overrides`; kolory bloków OWT Białostoczek (ESTIMATED); nie używać kolumn P3/M53 kondygnacje/kolor_srgb | R:s16-research-pack-02:236-241; R:s17-mistral-r8-p3:3,23-38 | P2* | otwarte | L |
| B-012 | świat C | Oznakowanie poziome wg zał. 2: P-3a/P-5/P-6 kreska 4,00/przerwa 2,00, linia 0,12; P-3b 1,00/1,00; P-12 0,50; P-13 0,50×0,70; P-14 0,75×0,50 | R:s17-mistral-r8-p6p8p9p5:122,158-160 | P2* | otwarte (porównać z generatorem) | S |
| B-013 | świat C | Wieżowiec Andersa: pasma SE nadal 20–45 ciemniejsze od ściany, ściana SE w cieniu (152 vs ~249), ton szczytu SW kremowy zamiast oliwkowego | R:s19-0180-r2:73-77; R:s20-0190:35,39,78; H:166 | P2 | otwarte | M |
| B-014 | świat C | Wieżowiec — dach i detale: bębny radiolinii jak „lizaki”, pozycja wysokiego masztu (0,3 vs 0,45 szczytu), biały pręt W, klimatyzatory; żaluzje jak kratka; ciemne okna seriami; ściana NW w idealnej siatce | R:s20-0190:50-92,117-123 | P2 | otwarte | M |
| B-015 | świat C | Wieżowiec wg M57: ściana NW = reguła pasmowa 6 grup ×~5 okien, maszt kratowy ~11 m w środku dachu, maszty ~5 m przy N i E, przybudówka SE, korekta ADR 0180 | H:84 | P2* | w toku (tower3-0200 zlecone, brak gałęzi na origin — H:102) | M |
| B-016 | świat C | Wieżowiec LOD: skok LOD0/LOD1 ściany NW, białe łaty LOD1 NW, beżowe „rolety” rytmiczne, rama okna szczytu, szczyt w LOD1 bez kolumny okien (dorastanie okien na telefonie) | R:s19-0180-r2:60-72; R:s20-gate3-phone:65; H:41 | P2 | do weryfikacji (0190 scalone, `FAR_PLAIN_U`, rama obustronna — H:70,73; R:s20-0190:36) | S |
| B-017 | świat C | Las na horyzoncie (6BC0) = palisada pni z płaskim wierzchem, brak wystających topól | R:s20-0170:15; H:35 | P1 | w toku (`forest-0187`, Argon — H:79) | L |
| B-018 | świat C | Świerk/korona ≤ 3 m od kamery = płaska kurtyna: dolna spódnica do gruntu, szew osi kart, wariant z geometrią gałęzi < 4 m | R:s20-0170:16-21 | P1 | otwarte | M |
| B-019 | świat C | Tuja = grzebień identycznych „lizaków”, rozciągnięty bok żywopłotu (UV); wariant niestrzyżony (R5); „kępy liści na gołym pniu” w prototypach ulic | R:s20-0170:23-29; R:s20-gate3-phone:72; H:98 | P2 | otwarte | M |
| B-020 | świat C | Wyspa EC cm92458760: nawierzchnia azylu czerwona kostka w wiązaniu cegiełkowym (dziś szara siatka), obrys wyspy ~1–2 m za szeroki, słup z D-3+D-6 frontem na latarni dwuramiennej, rytm latarni Y wzdłuż wjazdu | R:s20-0172:46-59 | P1 | otwarte | M |
| B-021 | świat C | 182011: strzałki kierunkowe i linia zatrzymania wg ortofoto; ekran akustyczny przezroczysty zielonkawy z ciemnym cokołem (dziś czarna ściana) | R:s20-0172:60-65 | P1 | otwarte | S |
| B-022 | świat C | 0172 P2: A-7 za szeroki (0,9 vs 0,72), C-12 → UNVERIFIED, D-6b + tabliczka, tablica ulicy na wysięgniku latarni, latarnia bez cokołu, tyły tarcz z ramą, rabata-pudło, spód wiaduktu czarny | R:s20-0172:67-81 | P2 | otwarte | S |
| B-023 | świat C | Chodnik na „wiszącej” płycie z widocznym spodem przy ekranach (`g3b_rondo_putry_approach`) — skarpa/dociągnięcie terenu | R:s20-gate3-phone:60; H:63 | P1 | otwarte (research zlecony GPT Chrome G3 — H:80) | M |
| B-024 | świat C | Szew muru oporowego `g3b_ext34_s1482`: zielona czapa ponad terenem + samotny panel ekranu; mur kamień/gabion zamiast płyt, czerwony pas jako półka, brak rzędu młodych drzew | R:s20-gate3-phone:61,71; H:63 | P1 | otwarte | M |
| B-025 | świat C | Bramka 3 P2 z telefonu: granatowa elewacja za nasycona, linia środkowa przez zebrę, łata na jezdni s1382, wyspa ronda Bieżeństwa jako jasny dysk, „kopce z cegły” rabat, te same białe vany, brak niebieskiej tablicy pod wiaduktem s0412 | R:s20-gate3-phone:66-73; H:63 | P2 | otwarte | M |
| B-026 | świat C | Zieleń znaków `signs.py:30` `GREEN = (0,112,72)` poza polem tab. 1.3 Dz.U. (margines −0,030) — ADR wyboru (a) (0,120,90) albo (b) WORKING_VALUE; przed decyzją visual-qa + zdjęcie zielonej tablicy z Białegostoku | R:s20-cloud2-r1:77-81; H:97 | P2* | otwarte | S |
| B-027 | świat C | Generator znaków: D-19/D-20 = 620×300 mm; wysokość montażu 2,20 m także nad chodnikiem, F poza zabudową ≥ 2,00 | R:s20-cloud2-r1:82-84 | P2* | otwarte (zgodność `standards.py` potwierdzona — R:s20-cloud2-r1:83) | S |
| B-028 | świat C | Drzewa uliczne wg R5: przewaga klonu w rzędach (~70/30 zamiast 50/50), odsunięcie pnia 2,5 m, nie generować dojrzałych szpalerów przy Andersa/Maczka, wariant tui niestrzyżony, profil sezonu (bezlistny 5 XI–20 IV) | R:s20-cloud2-r5:84-91; H:98 | P2* | otwarte | M |
| B-029 | świat C | Estakada A Putry: przęsło SW 94,8 m (i NE 48,8 m) bez podpór = błąd generatora (pominięte rzędy) → `pier_lines_en` w `viaduct_underdeck.json`; słupy prostokątne fazowane (nie owalne); opisy „round piers” do korekty | R:s20-mistral-m56:3; R:s20-mistral-m56-fix:3; H:57,91 | P1 | w toku (ADR 0198 piers zlecone, brak gałęzi — H:95,102) | M |

### Dojlidy (21)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-030 | Dojlidy | Kafle K01/K04 i bramy firm (node OSM) — szerokości/promienie ESTIMATED (G03 8,0 … G14 7,0 m); konflikty dojazdu KAN (Mickiewicza maxweight=8) i BIAFORM (rondo Meyera hgv=no) — zlecenia nie przez te odcinki bez decyzji | R:s16-research-pack-02:196-201; R:s17-mistral-r8-p6p8p9p5:29 | P2* | otwarte | M |
| B-031 | Dojlidy | Hangar Aeroklubu (L10) ~360 m poza kaflem 0166 w `landmarks_d51.authored.json` → tło albo usunąć | R:s17-mistral-r8-p11-p12:99,125 | P2* | otwarte (brak dowodu) | S |
| B-032 | Dojlidy | Wyposażenie: latarnie dwuramienne (Y), wiaty stare/nowe UNVERIFIED, progi z A-11a; kamery kontrolne P11-001/063/094/056/129 (nie P11-084/091/092/064) | R:s17-mistral-r8-p11-p12:103-111 | P2* | otwarte | M |
| B-033 | Dojlidy | K3 (P11-001): okładzina kasetowa z poziomymi fugami (dziś pionowe panele), szczyt bez pasm/z podziałami okien | R:s19-0179:32; R:s20-0185:33,42,82,120 | P1 | otwarte (0185 scalone częściowo — R:s20-0185:33) | S |
| B-034 | Dojlidy | Rosti (P11-094): moduł paneli hali zgodny z 16 pasami, okładzina z poziomych paneli zamiast bloczków, bez rzędu czarnych okienek; cokół 0,8–1 m; czarna obróbka attyki | R:s19-0179:50-52; R:s20-0185:48,74-86,121; R:s20-0196:81 | P1 | otwarte (wysokość 16,9 m zamknięta warunkowo — R:s20-0185:29) | M |
| B-035 | Dojlidy | Zacieki pod attyką powtarzają się co moduł — siła zacieków per materiał | R:s19-0179:55; R:s20-0185:66-68,122 | P1↑ | do weryfikacji (0196 `runoff_shuffle`: „brak rytmu modułu” — R:s20-0196:77-78) | S |
| B-036 | Dojlidy | Drzwi osobowe hali 1,2–1,7 m nad gruntem — próg liczony z terenu | R:s20-0185:70,123 | P1 | otwarte | S |
| B-037 | Dojlidy | Ogrodzenie i wjazd Kuronia 3 (P11-001): ~1,5–1,8 m grafitowe z bramą przesuwną, przebieg z BDOT/OSM, wjazd z kostki z przerwą; słupki płotu P11-094 szare, nie białe | R:s19-0179:30; R:s20-0185:79 | P1 | otwarte | S |
| B-038 | Dojlidy | DDR z czerwonego asfaltu i przejazdy rowerowe (P11-001, P11-056) — wg M65: przejazdy białe, Dojlidy szare, czerwone tylko rejon Putry | R:s19-0179:31,47,97; H:99 | P1 | w toku (`ddr-0188`, Argon — H:79) | M |
| B-039 | Dojlidy | Kadr P11-063: kalibracja pozy kamery (sygnalizator w środku), ciągła ściana krzewów 2,5–3 m, 3–4 dojrzałe drzewa 9–11 m na narożniku | R:s19-0179:37-39,88-89,95 | P1 | w toku (`dojgreen-0186`, Argon — H:79) | M |
| B-040 | Dojlidy | Sygnalizator z dużą białą tarczą za komorą (placeholder) — tarcza 0,85×1,40 tylko nad jezdnią, za obudową; D-6 za blisko kamery w P11-094 | R:s19-0179:41,54; H:99 | P2 | w toku (`sigplate-0193`, Argon — H:79) | S |
| B-041 | Dojlidy | Bravilor (dominanta P11-063): ciemna wyższa część frontowa + długa niska biała — `building_part` | R:s19-0179:42 | P2 | otwarte | S |
| B-042 | Dojlidy | Las przy trasie Krywlany: pnie z oderwanymi kulami liści, ściany lasu z pionową krawędzią bez podszytu; horyzont P11-056 = szare prostopadłościany i sadzonki-patyki | R:s19-0179:45,64,66,100,102; R:s20-0196:90-93 | P1 | w toku (`forest-0187`, Argon — H:79) | L |
| B-043 | Dojlidy | Brama szpitala P11-129: mur z cegły, ceglane słupy z daszkiem, STOP, B-33 „20”, C-2 (nie C-1), tablica izby przyjęć; placeholdery bloków w tle | R:s19-0179:58; H:49,90 | P2 (P0 dla bramki 3) | w toku (`hospgate-0189`, Argon; M62+FIX scalone — H:90) | M |
| B-044 | Dojlidy | Plamy na asfalcie jako jasne rozmyte „splaty”, jednorodne smugi na placu; asfalt pasa w plamy | R:s19-0179:59,63; R:s20-0196:97 | P2 | w toku (`stains-0194`, Argon — H:79) | M |
| B-045 | Dojlidy | Pas startowy Krywlany: kamera `krywlany_runway` pokazuje „łąkę z wstęgą asfaltu, nie lotnisko”; oś pasa s 0,5–27,9, napis „27 L”, szerokości 1,25/0,85/0,35, ogrodzenie lotniska zielone, wały z NMT 2018; trawa z widocznym kaflem | R:s19-0179:65,101; R:s20-0196:85-101; H:99 | P1 | w toku (`dojfix-0202` — H:102) | M |
| B-046 | Dojlidy | Kuronia 2 (P11-005): hala wystaje ponad front (relacja wysokości blok/hala → M63), okna jako płaskie niebiesko-szare kwadraty, poza kamery `kuronia2_front` niezgodna ze zdjęciem, brak czerwonej linii/daszku wejścia | R:s20-0196:20,41-62 | P1 | otwarte | M |
| B-047 | Dojlidy | Rosti: bramy segmentowe za małe (~40 % wys. ściany na zdjęciu) i bez obróbki | R:s20-0196:69-74 | P2 | otwarte | S |
| B-048 | Dojlidy | Słupki U-12 z łańcuchem: biel łańcucha ginie na jasnym bruku, dolny łańcuch za mały kontrast, „paciorki” i brak łańcucha na Low (lodBias 0,5), migotanie do oceny na A16; faktura „jeden szum”, brak AO stopy; rząd przesunięty 3,5 m na bruk | R:s20-0183:20-38 | P1 | otwarte (r4 scalone, kolor łańcucha naprawiony — H:74) | M |
| B-049 | Dojlidy | U-12b wg M58: wys. 1,10 m, rozstaw 2,0 m, pasy 25 cm, łańcuch jednobarwny w przęśle, rząd 14 m ~2 m bliżej jezdni | H:99 | P2* | w toku (`dojfix-0202` — H:102) | S |
| B-050 | Dojlidy | Las Krywlany wg M68: overrides PTLZ w kafelku (BDOT ≠ BDL: `12617d4f`, `1ac1a146`), okap 24–29 m, emergenty 3 % 29–32 m, MIX (świerk 0,05), płaszcz i podszyt (leszczyna, bez sosny), sylwetka ±10 % co 8–16 m, liczby horyzontu P11-056; atrybucja BDL w `docs/LICENSES.md` | R:s20-cloud-m68:167-198 | P1* | w toku (`forest-0187`, Argon — R:s20-cloud-m68:167) | L |

### ciężarówka (5)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-051 | ciężarówka | Zgodność modelu z tabelą wymagań P4/M44: ciągnik bez konturu R104/tablic wyróżniających/R58/R73, z odblaskami bocznymi i obrysowymi; naczepa — kontur R104 z tyłu, tablice R70, odblaski trójkątne, RUPD/R73; lusterka R46 (pola widzenia kl. II/IV/V/VI); tablica 520×114 R10 | R:s16-research-pack-02:243-249; R:s17-mistral-r8-p4:65-94 | P1* | otwarte (brak audytu modelu względem tabeli w recenzjach) | M |
| B-052 | ciężarówka | Lampy 0181: brak gładkiego klosza PMMA (matowe „nadruki kropek”, na telefonie „płaska naklejka”), rogi komór na Low, rozlew światła tablicy na ramkę, pomarańczowe kreski na krawędzi obudowy; szary quad za przednią szybą | R:s20-0181:48-64; R:s20-gate3-phone:50,69; H:42 | P2 | otwarte | M |
| B-053 | ciężarówka | Stop vs pozycyjne nierozróżnialne (205 vs 207 R) — stop:pozycyjne ≥ 5:1 po limiterze 0178, rozdzielić TAIL_BRAKE naczepy, bursztyn (1,0.22,0) + test obszaru R48, test tablicy ≥ 2,5 cd/m², lampa naczepy 520×170 vs 425×142 | R:s20-0181:53-57; H:85,95 | P1↑ | w toku (ADR 0197 zlecone w CODE-SESSION-PROMPT, brak gałęzi — H:95,102) | M |
| B-054 | ciężarówka | Marki w danych gry: `amt12_od_traxon_class.gearbox.json`, `diesel_r6_13l_368kw.engine.json`, `tractor_4x2_generic.vehicle.json`, `DrivingLabSceneBuilder.cs:271`, testy physics-runner, komentarz `ContactShadowCaster.cs:58` | R:s20-cloud2-r3:57,104; H:97 | P1* | w toku (truckdata-0201, brak gałęzi — H:102; X2 przegląd marek — H:103) | S |
| B-055 | ciężarówka | Brud naczepy wg M61: główny produkt (kadry) niesprawdzalny — M61-FIX (7/24 kadrów bez drzwi naczepy); do tego czasu nie zmieniać koloru brudu | R:s20-mistral-m61:3; H:100 | P2* | otwarte (M61-FIX u Mistrala — H:100) | S |

### fizyka (5)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-056 | fizyka | Decyzja właściciela: `maxLaunchGear` 4 vs 2 i `clutchMaxTorque` 4000 Nm (źródła nie rozstrzygają) | R:s15-mistral-r3:74-75 | P2* | otwarte | S |
| B-057 | fizyka | `reverse_dock_s_maneuver_comb` kończy złożeniem na odboju (91,2–91,6°); `reverse_grade6pct_comb` cofa ~8,2 km/h przy celu 4 km/h | R:s16-mistral-r5:92-93 | P2* | otwarte | M |
| B-058 | fizyka | F1: tolerancja miękkiego ogranicznika przegubu (0,6–3,3° nadmiaru) albo sztywniejszy stop; F2: wstrzykiwanie energii przy wywrotce (275 km/h w powietrzu) | R:s16-mistral-r6:108-109 | P1* | otwarte (przyczyna F2 niepotwierdzona) | M |
| B-059 | fizyka | Opona i masy wg R3: promień toczenia 0,51 → ~0,524 m (`tire_315_80_r22_5.tire.json:5`, `WheelGroup.cs`), naciski 65/35 → ~73/27 (−0,5 t przód), sztywność pionowa 1,0e6 → 0,88e6 N/m, tara naczepy 7,0 → 6,2–6,6 t; każda zmiana z ADR + physics-validation | R:s20-cloud2-r3:99-103; H:97 | P1* | w toku (truckdata-0201 zlecone, brak gałęzi na origin — H:102) | M |
| B-060 | fizyka | Errata docs: `docs/VEHICLE_REFERENCE_DATA.md:22` (v²/115, N3 40 km/h), `docs/PHYSICS_VALIDATION.md:110` (pkt 2.4.1, ≤ 52,4 m z 40 km/h), `docs/04_FIZYKA.md:19` 315/70 → 315/80; nowe scenariusze PV 60→0 ≤ 36,7 m, 72→0 ≤ 60,9 m, awaria obwodu, postój 18 % | R:s20-cloud2-r3:94-98; H:97 | P1* | w toku (truckdata-0201, brak gałęzi — H:102) | S |

### rendering (8)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-061 | rendering | Płoty panelowe: siatka znika od ~10 m albo mory na Low — alpha-to-coverage dla `fence_mesh` zamiast wyboru mora/zanik | R:s19-0179:51; R:s20-0185:13-20,57-65,116-124; H:88 | P1 | otwarte (linia `mipMapsPreserveCoverage` cofnięta, `InstanceImporter.cs:678` — H:88) | M |
| B-062 | rendering | Brud naczepy: osad drogowy ciepły zamiast neutralnej sadzy, próg/RUPD/klosze brudniejsze; zacieki z belki jak blacha falista (gęstość ×0,3–0,4, klastry); pręty ryglowe czyste | R:s19-0182:23-36,58-61; H:100 | P1 | do weryfikacji (0182 r5 scalone — H:107; M61-FIX otwarte — H:100) | M |
| B-063 | rendering | Czytelność ciężarówki o zmierzchu na telefonie (plandeka/ciągnik toną w czerni) — zmierzyć na A16 + ocena właściciela, ew. EV100 3,5–3,7 | R:s19-0182:44-46,84 | P1 | otwarte | S |
| B-064 | rendering | Lampy tylne nie oświetlają otoczenia (belka, asfalt bez czerwonego odbicia) | R:s19-0182:56-57 | P2 | otwarte | S |
| B-065 | rendering | Koralowo-różowy najniższy pas nieba o zmierzchu (`ApplyTwilightChroma` w LP_Dusk) i martwy szary pas przejścia | R:s19-0182:51-53; R:s20-0191-0192:29; H:53,98 | P2 | w toku (dusk-cal-0199 zlecone, brak gałęzi — H:102) | S |
| B-066 | rendering | Noc 0191+0192: słup łukowej latarni świeci na High („neonowe ramię”), tuje driver_andersa z twardą krawędzią, pojazdy Low bez światła latarni, wieżowiec nocą piętrami jak „pasek LED”, kamuflażowe łaty kostki na Low, sód+LED decyzja właściciela | R:s20-0191-0192:22,30-32; H:53 | P1↑ | otwarte (P0/P1 krytyka naprawione w night-int — H:53) | M |
| B-067 | rendering | Postrzępione cienie cienkich obiektów na Low (wysięgnik sygnalizatora, latarnie) — kreskowane smugi na jezdni | R:s20-gate3-phone:62; H:63 | P1 | otwarte | M |
| B-068 | rendering | Niebo wg R7: brak ciepłego pasa przy pełnym zachmurzeniu (`SkyModel.HorizonColorExposed()` — opis potwierdzony, przyczyna obalona), LP_Clear widzialność 20 → ~40 km, LP_Overcast słońce 41° vs zimowe 8 km — wybrać sezon presetu; azymut zmierzchu 300° → 238–245° (decyzja właściciela); mgiełka 0080 tylko zimą | R:s20-cloud2-r7:34,93-103; H:93,98 | P2* | otwarte (decyzja właściciela o sezonie) | S |

### audio (2)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-069 | audio | Test oktawy `comb_estimate`, który pada na starym kodzie bez WAV | R:s15-mistral-r3:67 | P2* | prawdopodobnie zamknięte (#30 M26 SCAL, legacy 17/17 FAIL — R:s16-mistral-r5:15) | S |
| B-070 | audio | Brak wolnych nagrań retardera, hamulca silnikowego, osuszacza, AMT, R6 13 l (3 negatywy) → syntezować/ElevenLabs; wzorzec przerwy momentu AMT z B8R (0,75–1,0 s, −13…−16 dB) | R:s16-gptpro-zips:60-66; R:s16-research-pack-02:289; R:s17-mistral-r8-p6p8p9p5:98,185 | P2* | otwarte | M |

### UI (6)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-071 | UI | HUD: telemetria dev i overlay diagnostyki nadal alokują przy zmianie treści (etykiety jazdy już 0 GC) | R:s15-mistral-r3:76-79; R:s16-mistral-r4:15,76-77 | P2* | otwarte (HUD jazdy zamknięty #22 M23 — R:s16-mistral-r4:15) | S |
| B-072 | UI | Regeneracja `bialystok-industrial-c_route.bytes` (KRTG v2, osie M28, flagi M27) + visual QA paska pasów i linii trasy na telefonie | R:s16-mistral-r4:69-71; R:s16-mistral-r5:84-87 | P2* | otwarte (brak dowodu regeneracji w recenzjach) | S |
| B-073 | UI | Planer C# liczy koszt z `GeomLength`, nie `length_m` (różnica do 5,64 m/krawędź) | R:s16-mistral-r5:88-89 | P2* | otwarte | S |
| B-074 | UI | `hgv=destination` nie zwalnia krawędzi startowej; `hgv:conditional` nieobsługiwane (0 w regionie C) | R:s16-mistral-r4:78-79 | P2* | otwarte (dotyczy kolejnych regionów) | S |
| B-075 | UI | Nawigacja: `HasExit` liczy wszystkie wyloty ronda; `RouteTracker.Update` ETA O(n) co klatkę (koszt na telefonie niezmierzony); 6 komunikatów głosowych na manewr do oceny na ucho; brak raportu NAV-RUNNER | R:s16-mistral-r6:110-114 | P2* | otwarte | M |
| B-076 | UI | Przystanki: 52 węzły OSM ↔ kody GTFS (nazwy/numery słupków) | R:s16-research-pack-02:220 | P2* | otwarte | S |

### perf (7)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-077 | perf | Testy `ZeroGc_*` nawigacji mierzą `GC.GetAllocatedBytesForCurrentThread()` (w edytorze 0) — przepisać na `Recorder("GC.Alloc")` | R:s16-mistral-r4:74-75; R:s16-mistral-r5:98 | P2* | otwarte | S |
| B-078 | perf | Rozszerzyć testy `Recorder("GC.Alloc")` na fizykę, audio i kamerę w PlayMode (audyt GC M32 niezweryfikowany pomiarem) | R:s16-mistral-r5:96-97 | P2* | otwarte | M |
| B-079 | perf | Pomiar A16 po 0153 (LOD aut): GPU p50/p95/p99 trasy ADR 0136 r2, pop aut 16/42,5 m, kolor atlasu po ASTC, PSS/hitching | R:s16-codex-0153:58-62 | P2* | otwarte (brak osobnego pomiaru w recenzjach) | S |
| B-080 | perf | Pomiar A16 po 0155: shadow pass i migotanie w ruchu przy wiadukcie | R:s16-codex-0155:62 | P2* | otwarte | S |
| B-081 | perf | Zrzuty A16 Low kadrów `g3a_eye_s0012`, `g3a_eye_s0062`, `stretch-02` (warunek 0190) oraz `kuronia2_front`, `photo_P11-094` (warunek 0196) | R:s20-0190:15,119; R:s20-0196:23 | P1 | do weryfikacji (G3-A A16 na edb5524993, kamery 57/57 — H:89,96; Dojlidy bez zrzutów) | S |
| B-082 | perf | Koszt GPU nocy (0191 +~32 ALU/px Low, 0192 +~40 ALU okna, +1 draw glare) niezmierzony na A16/S24+; plamy latarni niewidoczne w `truck-34_dusk` na Low (zamierzone?) | R:s20-0191-0192:33; R:s20-gate3-phone:52,70; H:53 | P1 | otwarte | S |
| B-083 | perf | GPU A16 bez zapasu: P8 pomiar GPU przy stałym zegarze/cyklach; A/B `androidBlitType` 0 vs 2 (Auto) przez `ProjectSetup.ApplyAll` + ADR; MSAA 2× na Mali-G57 sprawdzić RenderDoc (sprzeczność z ADR 0013); czego nie robić na Low | R:s20-cloud2-r8:26,78-87; H:93,97 | P1* | otwarte | M |

### research (12)

| id | obszar | opis | źródło(a) | prio | status | wielk. |
|---|---|---|---|---|---|---|
| B-084 | research | `docs/LICENSES.md`: CC BY-SA wycinków Mapillary/Panoramax/KartaView tylko jako referencja; ujednolicić licencję KartaView (CC BY vs CC BY-SA) | R:s16-gptpro-g2-g3:78; R:s17-mistral-r8-p10:46 | P2* | otwarte | S |
| B-085 | research | Źródła: GRRF-56-3 (inny dostęp), limity z art. 20 PoRD, obecna podstawa dla końców barier (GDDKiA); Dz.U. 2021 poz. 438 a zał. 2 | R:s16-mistral-r5:94-95; R:s16-mistral-r4:73 | P2* | otwarte | S |
| B-086 | research | M30 (r5) nadal bez PR | R:s16-mistral-r6:119 | P2* | otwarte (brak wzmianki w późniejszych recenzjach) | S |
| B-087 | research | PR #41 (M44) przed scaleniem: CMS zamiast kl. II/IV (R46 Rev.6), pełna lista zmian 2026/891 | R:s17-mistral-r8-p4:96-120 | P2* | otwarte | S |
| B-088 | research | Luki zdjęć referencyjnych: Batorego 0, Brzeska/Buska 0, Maczka zima 0, rondo Bieżeństwa z poziomu kierowcy 0, 9 ulic osiedla 0, lato 9 ulic osiedla 0, stan 2025–2026 bramownicy A/portalu N, tablice S19 — sesja zdjęciowa właściciela | R:s16-research-pack-02:282-295; R:s17-mistral-r8-p1b:37-47,68; R:s17-mistral-r8-p10:49-53; R:s17-mistral-r8-p7:9,11 | P2* | otwarte | M |
| B-089 | research | M51 `crowns.geojson` odbite lustrzanie N–S w kaflach 1024 m; filtr r ≤ 6,5 m wycina drzewostany — nie używać bez korekty | R:s17-mistral-r8-p10:7-9,38-41,56 | P1* | do weryfikacji (patrz recenzja M51-FIX-2 s20) | S |
| B-090 | research | M52 r2: kadry nadal niezgodne (M52-FIX-3/4: 10/26 kadrów błędnych, 11 par duplikatów md5); nowe etykiety P-7a/P-7c, P-21a/b, P-23, P-25 niesprawdzone | R:s18-mistral-fixes-r8:11,90; H:30 | P2* | otwarte (FIX-4 u Mistrala — H:72) | S |
| B-091 | research | M53 zabudowa: po erracie 28 przyjętych (< 30), M53-FIX-2; licencja Borawskiego ujednolicić; `crowns.geojson` M51 — filtrować fałszywe korony (autobusy, dachy) | R:s19-mistral-m51-m53-m50v2:11,89,125,135 | P2* | otwarte (M53-FIX-2 w toku u Mistrala — H:81) | S |
| B-092 | research | R9 (następny region): FIX — drogi < primary, budynki, zera Commons (429), User-Agent z nazwą projektu w 7 skryptach; nazewnictwo „obrzeża: S8 Choroszcz–Białystok Zachód, S19, Trasa Generalska, DK8/19 N”; manifesty GUGiK powiatu 2002 | R:s20-cloud2-r9:3-8,104-115; H:98 | P2* | otwarte (blok FIX do wklejenia chmurze #2 — H:98) | M |
| B-093 | research | Mistral FIX w kolejce: M57-FIX (wieżowiec), M59-FIX (lampy, ZIP brak), M60 #57 (zamknąć albo zawęzić — decyzja właściciela), M52-FIX-4; M64–M69 do zlecenia | R:s20-mistral-m57:3; R:s20-mistral-m59:3; R:s20-mistral-m60:3; H:72,91,100 | P2* | otwarte | M |
| B-094 | research | M52: rozbieżność P-13 0,2333 vs 0,2625 w README/M52-020; czerwony pas za barierą estakady (jar-11) | R:s20-mistral-m52-fix3:67-70 | P2* | otwarte | S |
| B-095 | research | Errata M47 (znaki P11): P11-131 `punkt_opis` „Żurawia —” przy ulica=UNVERIFIED; P11-129 raczej C-2, nie C-1 | R:s20-mistral-m47-fix2:3; H:40,49 | P2* | otwarte (M47-FIX-2+3 scalone — H:40) | S |

