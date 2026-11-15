# REVIEW 2026-11-15 s20 — ADR 0187 Ściana lasu, świerk, młodnik, płaszcz skraju, horyzont P11-056 (gałąź `forest-0187`)

Recenzent: niezależny `Reviewer` (nie autor), tylko odczyt. Kryterium nadrzędne: `docs/06_GRAFIKA_ANTI_AI_SLOP.md` oraz wymagania M68 (`docs/reports/REVIEW-2026-11-14-s20-cloud-m68.md` §6) i `REVIEW-2026-11-13-s20-0170.md` (P1-1, P1-2).
Materiał z rundy `after2` (`.claude/worktrees/forest-0187/artifacts/forest-0187/`):
- `pairs2/dojlidy-Low/` i `pairs2/dojlidy-High/` (`pair_photo-P11-056.jpg`, `pair_route-s0457.jpg`, `pair_route-s0761.jpg`, `pair_forest_wall_meadow.jpg`, `pair_forest_edge_near.jpg`, `pair_forest_interior_mixed.jpg`, `pair_forest_corridor.jpg`, `pair_edge-north.jpg`, `krywlany-runway.jpg` — pojedyncze ujęcie `after2`),
- `pairs2/c-Low/` (`pair_g3a_eye_s0262.jpg`, `pair_g3b_eye_s1482.jpg`, `pair_edge-north.jpg`),
- `compare2-{dojlidy,c,chz}-{Low,High}.tsv`, `logs/{import-base,after2-import}-*.log` (`WORLD_MEMORY`),
- referencje: `research/_incoming/mistral-p11-dojlidy-photos-v2b/files/P11-056.jpg`, `docs/reports/REVIEW-2026-11-14-s20-cloud-m68.md`.

**Brak zrzutu z telefonu (A16 Low)** — `docs/06_GRAFIKA_ANTI_AI_SLOP.md` §5 pkt 2 niespełniony; akceptowalne do warunkowego scalenia na etapie edytora, wymagane przed bramką.

## Werdykt: SCAL warunkowo

Gałąź `forest-0187` realizuje główne cele ADR 0187 i danych M68 bez P0 i bez regresji budżetu:
1. **Horyzont `photo-P11-056` (Low)** jest w **100 % domknięty** ciągłą, ciemną sylwetką drzew od lewej krawędzi aż po działki i prawą krawędź kadru — zniknęły patykowate sadzonki na tle nieba oraz białe bryły far-field widoczne w `base`.
2. **Skraj i wnętrze lasu (`forest_edge_near`, `forest_interior_mixed`, `forest_corridor`, `c-Low/edge-north`)** przeszły skok jakościowy: drzewostany mają naturalną wysokość 20–29 m (+ emergenty do 32 m), pojawił się właściwy świerk (`tree_spruce`), sosny mają odsłonięte pnie w dolnej 1/4–1/3 na niezasłoniętych odcinkach, podszyt jest gęsty i pozbawiony gołych patyków `pineyoung`, a krzewy skraju występują odcinkowo (~18 %).
3. **Budżet A/B i pamięć**: w regionie C `d_draws = 0` na wszystkich 129 kamerach (Low i High), `tris` +0,12 % / +0,19 %; w Dojlidach narzut minimalny (+1,48 % / +1,08 % tris, `WORLD_MEMORY` +2,8 do +4,3 MB).

Nie można jednak dać bezwarunkowego `SCAL`, ponieważ **ściany i narożniki HLOD** w `krywlany-runway` (Low) i `forest_wall_meadow` (Low i High) nadal miejscami tworzą ostre, pionowo ucięte krawędzie („tekturowa palisada”), a na profilu **High** w `photo-P11-056` i `krywlany-runway` nad horyzontem unoszą się oderwane ciemne plamy koron w mgle.

Warunki scalenia (lider):
1. Wpisać do backlogu poprawę narożników i lewitujących koron HLOD (P1 z tego raportu: `krywlany-runway` Low, `forest_wall_meadow`, artefakty koron na High w `photo-P11-056` i `krywlany-runway`) oraz P2 (`route-s0761` stożkowy szczyt, `route-s0457` prześwit dachu, `dojlidy/edge-north` drzewo przed kamerą).
2. Wykonać pomiar i zrzuty na telefonie (Samsung A16 Low) przed bramką etapu (`docs/06` §5 pkt 2).

## Oceny (1–10)

| Kategoria | Ocena | Uzasadnienie |
|---|---|---|
| Skala i proporcje | 8 | Drzewostany K1 poprawnie podniesione do 20–29 m (BDL/NMPT M68), wyraźna różnica wysokości względem `base` i naturalna relacja do pasów ruchu oraz płotu. |
| Światło i ekspozycja | 7 | Ciemna sylwetka horyzontu w `P11-056` dobrze osadzona w tonie podlaskiego overcastu; w `forest_interior_mixed` pojedyncze pnie brzóz lekko zbyt jasne. |
| Materiały | 7 | Nowe prototypy świerka i poprawione krzewy/brzozy wyglądają spójnie z bliska; z daleka na High fragmenty koron w mgle tracą ciągłość. |
| Zużycie i osadzenie | 7 | Pnie sosen dobrze osadzone, podszyt bez lewitujących kęp `pineyoung`; wyjątek: oderwane plamy koron nad ścianą w `forest_wall_meadow` i `photo-P11-056` High. |
| Powtarzalność | 7 | Odcinkowy płaszcz krzewów (~18 %) i zróżnicowanie składu (sosna/brzoza/świerk/podszyt) przełamują monotonię; jedynie w `forest_wall_meadow` powtarzają się gęste pionowe słupy. |
| Polskie realia | 8 | Bory sosnowe z domieszką brzozy i świerka w `forest_edge_near` i `c-Low/edge-north` wyglądają wiarygodnie polsko; horyzont `P11-056` zgodny ze zdjęciem. |
| Czytelność / rozpoznawalność | 8 | `P11-056` rozpoznawalny natychmiast jako ciągła linia drzew zamiast pustego pola z białymi blokami; `route-s0761` wiarygodnie zalesiony. |
| Artefakty (Low / High) | 5 | Ostre pionowe cięcia narożników HLOD (`krywlany-runway` Low, `forest_wall_meadow`) oraz lewitujące fragmenty koron w mgle na High (`P11-056`, `krywlany-runway`). |

## Weryfikacja wymagań i problemy

### 1. Horyzont `photo-P11-056` (`pair_photo-P11-056.jpg`, `pair_route-s0457.jpg`, `pair_route-s0761.jpg`)
- **Low — PASS:** W `pairs2/dojlidy-Low/pair_photo-P11-056.jpg` (prawa połowa `after2`, od lewej krawędzi połowy aż za przejście dla pieszych do prawej krawędzi) horyzont jest w 100 % domknięty ciągłą, ciemną linią drzew (`allotment-gardens`, `wood-north-west-of-the-meadow`, `wood-north-of-krywlany-skatepark`). Białe bryły far-field zniknęły, brak prześwitów nieba na linii styku z gruntem. Zgodne ze zdjęciem referencyjnym `P11-056.jpg`.
- **P1 (w zakresie ADR 0187) — oderwane ciemne plamy koron na High (`pairs2/dojlidy-High/pair_photo-P11-056.jpg`):** W prawej połowie `after2`, nad białym płotem po lewej oraz na prawo od niebieskiego znaku D-6 (nad czerwonym autem), pojedyncze ciemne fragmenty koron/impostorów unoszą się w mgle ponad zamgloną sylwetką pasa drzew. Na Low efekt nie występuje.
- **P2 (w zakresie ADR 0187) — prześwit białego dachu w `pair_route-s0457.jpg`:** W prawej połowie `after2` (na lewo od latarni przy zakręcie drogi, tuż nad linią drzew) nadal minimalnie prześwituje górny pas białego budynku far-field.
- **P2 (w zakresie ADR 0187) — ostry stożkowy szczyt w `pair_route-s0761.jpg`:** W prawej połowie `after2` (Low i High, przy prawej krawędzi kadru nad zielonym ogrodzeniem) ponad równą linię koron wystaje pojedynczy nienaturalnie ostry, trójkątny szczyt.

### 2. Ściana lasu, skraj i wnętrze (`forest_wall_meadow`, `forest_edge_near`, `forest_interior_mixed`, `forest_corridor`)
- **Skraj i wnętrze — PASS:** `pairs2/dojlidy-High/pair_forest_edge_near.jpg`, `pair_forest_interior_mixed.jpg` i `pair_forest_corridor.jpg` (prawa połowa `after2`) potwierdzają realizację założeń M68 §6: widoczna wysokość 20–29 m (+ emergenty), naturalne korony świerka (`tree_spruce`), odsłonięte pnie sosen w dolnej 1/4–1/3 na części krawędzi z bogatym podszytem liściastym w głębi, brak patykowatych `pineyoung` oraz odcinkowy pas krzewów.
- **P1 (w zakresie ADR 0187) — płaska „tekturowa” krawędź i dziura z lewitującymi koronami w `pair_forest_wall_meadow.jpg` (Low i High):**
  - W prawej połowie `after2` (zarówno Low, jak i High): środkowo-lewy blok lasu (nad linią energetyczną i białym płotem) ma **idealnie pionową, uciętą pod kątem 90° lewą krawędź**, a w jego środkowej części (zagłębienie sylwetki) widać prześwit pod **lewitującymi w powietrzu ciemnymi plamami koron**.
  - Wysoki blok lasu na środku/po prawej stronie połowy `after2` ma z lewej strony bardzo ostrą, pionową ścianę z gęstymi ciemnymi pasami — w tym miejscu ściana nadal czyta się jako pionowa palisada/kurtyna HLOD, a nie miękki narożnik lasu.

### 3. Narożniki lasów (`krywlany-runway`, `edge-north`)
- **P1 (w zakresie ADR 0187) — ostry, „urwany” narożnik HLOD w `pairs2/dojlidy-Low/krywlany-runway.jpg`:** Po lewej stronie kadru (za zielonym kopcem, nad jasnoturkusowym pasem) ściana lasu nadal urywa się **ostrą, pionową linią 90°** dokładnie tak, jak opisano w `REVIEW-2026-11-14-s20-0196.md`. Parametr `CORNER_DROP = 0.80` w `forest_hlod.py` nie zlikwidował tego artefaktu na Low.
- **P1 (w zakresie ADR 0187) — lewitujące fragmenty koron w `pairs2/dojlidy-High/krywlany-runway.jpg`:** Na High narożnik po lewej jest nieco bardziej schodkowy, ale w lewej części kadru nad linią ściany unoszą się w mgle oderwane ciemne strzępy koron.
- **`pairs2/c-Low/pair_edge-north.jpg` — PASS:** W regionie C (`after2`, prawa połowa) domieszka świerków dobrze wtapia się w bór sosnowo-brzozowy po obu stronach jezdni, brak ostrych ucięć HLOD.
- **P2 (w zakresie ADR 0187 / kamer) — drzewo przed obiektywem w `pairs2/dojlidy-Low/pair_edge-north.jpg`:** W połowie `after2` nowo wygenerowane drzewo stoi tuż przed kamerą, zasłaniając lewą połowę kadru i podbijając `tris` na tej kamerze o +109,75 %.

### 4. Poza zakresem ADR 0187 (odnotowane, nie blokują)
- **Ogrodzenia panelowe z morą / białe ściany płotu** (`route-s0761`, `forest_wall_meadow`) — zakres `0185`.
- **Jasnoturkusowy pas u podstawy kopca w `krywlany-runway`** — niezidentyfikowany element terenu/ogrodzenia z wcześniejszych recenzji (`0196`).
- **Świerk i tuja z `plot_kit` < 3 m od kamery** (`REVIEW-2026-11-13-s20-0170.md` P1-2, P2-1/2) — osobny atlas, poza zakresem `0187`.

## Budżet A/B i pamięć (`compare2-*.tsv`, `WORLD_MEMORY`)

| Zestaw | `draws` (baza → po) | Najgorszy Δ `draws` | `trisK` (baza → po) | `WORLD_MEMORY` total (baza → po) |
|---|---|---|---|---|
| `bialystok-industrial-c` Low (129) | 21 338 → 21 338 | **0** (na wszystkich 129 kamerach) | 22 696 → 22 724 (+0,12 %) | 123,0 → 125,8 MB (+2,8 MB) |
| `bialystok-industrial-c` High (129) | 35 880 → 35 880 | **0** (na wszystkich 129 kamerach) | 52 830 → 52 932 (+0,19 %) | 265,8 → 268,7 MB (+2,9 MB) |
| `bialystok-dojlidy` Low (47) | 5 959 → 6 048 | +12 (`photo-P11-063`: 317 → 329) | 10 234 → 10 385 (+1,48 %) | 97,7 → 102,0 MB (+4,3 MB) |
| `bialystok-dojlidy` High (47) | 11 384 → 11 533 | +11 (`cab-gate`, `route-s0761`, `route-s1066`) | 22 314 → 22 554 (+1,08 %) | 213,1 → 217,2 MB (+4,1 MB) |

- **Ocena budżetu — PASS (edytor):** Zero regresji `draws` w C; w Dojlidach najcięższe kamery na Low (`photo-P11-001`: 342 draws / 473,8 tys. tris; `route-s1066`: 393 draws / 289,1 tys. tris) pozostają w hipotezie `docs/06` §6 (≤ 300–400 draws, ≤ 400–600 tys. tris). Narzut pamięci `WORLD_MEMORY` pomijalny (+2,8–4,3 MB). Telefon (A16 Low) niezmierzony.
