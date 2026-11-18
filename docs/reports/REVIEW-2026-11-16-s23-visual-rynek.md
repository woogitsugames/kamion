# Recenzja wizualna offline — Rynek Knyszyna, targowica i rondo DK65 × Tykocka (s23, sesja P r6)

Gałąź oceniana: `origin/knyszyn-rynek-0227` @ `8366950d4` (PR #139 + #144, integracja rynek-s23).
Standard: `docs/06_GRAFIKA_ANTI_AI_SLOP.md` §2 (czerwone flagi) i §5 (checklista bramki wizualnej), uwagi właściciela
`docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`. Recenzent nie jest autorem zmian (§5 pkt 4).

## Werdykt: **FAIL** (bramka wizualna §5 niespełniona; ocena z dokumentów, nie z obrazów)

**Rendery r1/r2 nie są w gicie.** Raport integracji wskazuje `artifacts/rynek-s23/vqa/`, `vqa-r2/`, `view/` i `view-r2/`
(69 kamer na wariant, 1920×1080), ale `git ls-tree -r origin/knyszyn-rynek-0227 artifacts/rynek-s23` jest pusty.
W gałęzi nie ma też żadnego innego renderu Rynku, targowicy ani ronda z r1/r2. Jedyne obrazy z Knyszyna to
`artifacts/spawn-fix-0262/renders/_sheets/knyszyn.jpg`: start na DK65 sprzed r2, bez Rynku i bez ronda. Ten kadr obejrzałem —
nie pokazuje ocenianych miejsc, więc nie ma wpływu na werdykt.

Ocena opiera się więc na:
- opisie oględzin lidera w `docs/reports/INTEGRATION-2026-11-16-rynek-s23.md` §6–§7 (gałąź);
- ADR 0227 i 0274 (gałąź);
- uwagach właściciela w `KNYSZYN-OWNER-FEEDBACK-S21.md`.

Zdjęcia właściciela (`Data/raw/refs/owner-knyszyn-2026-11-15/`) są poza gitem z założenia, więc pary zdjęcie | render widział
tylko lider. Werdykt PASS wymaga obejrzenia renderów (CLAUDE.md zasada 4: „nigdy »skrypt przeszedł, więc wygląda dobrze«”),
dlatego bez nich jest FAIL. Nawet przy dobrych renderach lista P1 niżej (znane rozbieżności ze zdjęciami, opisane przez
samego integratora) daje FAIL.

## Lista poprawek

| P | Miejsce | Problem (źródło) | Flaga docs/06 | Propozycja |
|---|---|---|---|---|
| **P0** | proces | Brak renderów r2 w repo: recenzji §5 pkt 3–4 nie da się wykonać poza maszyną lidera (INTEGRATION §4: „rendery … `artifacts/rynek-s23/`”, katalog nieśledzony) | — | Dodać do gita podglądy ≤ 960 px dla kadrów: 03, 05 (park), 12, 14 (targowica), `rondo-dk65-top`, `rondo-dk65-from-south`, `dk65-inlet-south` (Low i High clear), np. `docs/reports/visual/rynek-s23/`. Zdjęć właściciela nie dodawać. Potem ponowić recenzję. |
| **P0 (do weryfikacji)** | rondo, widok `rondo-dk65-from-south` | „Widać wysoką krawędź jezdni po prawej (uskok teren / droga) — do sprawdzenia” (INTEGRATION §7) | §2: błędne wskazówki skali; obiekty pod/nad terenem (§5 pkt 5) | Zmierzyć różnicę wysokości krawędzi asfaltu i terenu w GLB (sonda jak `qa/seam_section.py`). Uskok > 0,15 m przy jezdni (wyższy niż krawężnik) to błąd geometrii, nie kosmetyka: poprawić przejście teren–droga (`terrain_walls`) przed scaleniem. Jeśli ≤ 0,15 m i to krawężnik — zejdzie do P2. |
| **P1** | targowica, kadr 12 | Trzy wiaty stykają się okapami; na zdjęciu właściciela 12 stoją osobno, z przerwami (INTEGRATION §7; feedback: „4 długie, otwarte zadaszenia … osobne, z przerwami”, układ 3+1) | §2: idealna symetria / „generyczny” układ | Odstępy między wiatami z ortofoto GUGiK 2025 (obrysy z PR #139) jako dane override (`gap_m` WORKING_VALUE, jeśli ortofoto nie rozstrzyga). Długości wiat skrócić tak, żeby zachować skrajne krawędzie. |
| **P1** | targowica, narożnik przy wjeździe | Brak żółtego pawilonu z ciemnym czterospadowym dachem (szalet/kasa) z parkingiem z płyt — w tym miejscu stoi szary budynek (INTEGRATION §7; feedback „W narożu przy wjeździe mały żółty pawilon…”) | §2: „generyczna” zabudowa zamiast lokalnej | Pawilon jako authored prop / override budynku (żółty tynk, dach czterospadowy grafit, wymiary ESTIMATED z ortofoto), parking z płyt betonowych. |
| **P1** | park Rynku, kadry 03 i 05 | Korony lip: „płaskie karty i ciemne pionowe szwy” (INTEGRATION §6). Dojrzałe lipy 15–20 m to główny element kadru z poziomu oczu (feedback „Park na Rynku”) | §2: rozmyte / sztuczne bryły; powtarzalne drzewa obok siebie | Korony lip jako bryły objętościowe (kilka przecinających się kart z normalnymi sferycznymi albo mesh LOD0 z `make_trees.py`), bez pionowych szwów; zróżnicować skalę i obrót w rzędzie. Sprawdzić w kadrze 05 Low i High. |
| **P1** | rondo DK65 × Tykocka | Średnica zewnętrzna: ok. 26 m z długości aut na zdjęciu 9, w grze 22,6 m z OSM; generator nie ma klucza nadpisania promienia (INTEGRATION §7, OPEN-DECISIONS OD-046) | §2: błędne wskazówki skali (rozpoznawalność, D51) | Decyzja OD-046 (A: pomiar + klucz `ring_r_m`, osobny ADR). Do tego czasu oznaczyć w ADR 0274 jako znany błąd skali. Wszystkie inne wymiary ronda (przeskalowane wg zdjęcia przy Ø 22,6 m) trzeba będzie przeliczyć — wysepka N `length_m` 32 też zależy od tej skali. |
| **P2** | rondo, wysepka E | Na zdjęciu 9 ok. 19 m, w modelu krótka (z OSM) (INTEGRATION §7) | §2: skala | Override długości wysepki E jak dla N/S (`carriageway_split`), wartość ESTIMATED ze zdjęcia, po rozstrzygnięciu OD-046. |
| **P2** | targowica, wyspa przy wjeździe | „Zbyt zielona”; na zdjęciu wyspy z ziemią/nasadzeniami o łukowych krawędziach, młode drzewka z podporami (INTEGRATION §7; feedback) | §2: sterylność / ten sam materiał wszędzie | Materiał gleby + kilka młodych drzewek z palikami, łukowa krawędź z kostki. |
| **P2** | park Rynku | Pomnik króla = PROXY_NOT_APPROVED, wierzba i strumienie fontanny ESTIMATED / WORKING_VALUE / OPEN (ADR 0227; INTEGRATION §7) | §2: „zabawkowe” obiekty, jeśli proxy jest widoczne z bliska | Zostawić jako jawne proxy do akceptacji właściciela. Sucha fontanna posadzkowa jest zgodna ze zdjęciem 4 („suchy plac z fontanną posadzkową”), więc to nie błąd. |
| **P2** | proces | `stage.py` wywołuje generatory `knyszyn_*` na sztywno; wpisy „trial” lip w overrides (recenzja #139 P2-2, P2-4; INTEGRATION §7) | — | Rejestr generatorów sterowany z overrides; usunąć wpisy trial przed scaleniem albo opisać w ADR 0227 jako aktywne. |

Co jest zgodne ze zdjęciami wg oględzin integratora (do potwierdzenia na obrazach): park z trawnikami i lipami zamiast
lasu sosnowego (największy błąd z s21 usunięty), kościół w osi alei, urząd z pomnikiem, układ targowicy 3+1 z PV
i pasami czerwonej kostki, długi budynek i płot panelowy, rondo z długimi wysepkami N/S, P-13/P-10 i wyspą z piaskiem
i kamieniami (INTEGRATION §6).

## Kryterium właściciela (feedback s21, pkt 1)
Sukces = właściciel rozpoznaje miejsce **z kabiny / z wysokości oczu**, nie z góry. Ocena „lepiej niż było” z INTEGRATION
§1 tego nie potwierdza. Po poprawkach P0–P1: pakiet par zdjęcie | render (kadry 03, 05, 12, 14, 9–11) z wysokości
1,7–2,5 m do oceny właściciela (AskUserQuestion: rozpoznaję / częściowo / nie).

## Komendy dla lidera (po dodaniu podglądów, Windows)
```
pwsh scripts/visual-qa.ps1 -Scene World_knyszyn -Tier Low -Lighting clear -OutputDir artifacts/rynek-s23/vqa-r3/Low-clear
pwsh scripts/visual-qa.ps1 -Scene World_knyszyn -Tier High -Lighting clear -OutputDir artifacts/rynek-s23/vqa-r3/High-clear
```
(Nazwa sceny wg `RegionScenes` — użyć tej samej, co łańcuch rynek-s23 przy r2.) Potem skopiować podglądy ≤ 960 px wybranych kadrów do `docs/reports/visual/rynek-s23/` i ponowić recenzję.
