# REVIEW — ADR 0193: Tarcza kontrastowa sygnalizatorów (M66) i kamera `photo_P11-094` (gałąź `sigplate-0193` @`51b9976da`)

Recenzent: niezależny agent `Reviewer` (nie autor), tylko odczyt.
Kryterium nadrzędne: zgodność z przepisami (Dz.U. 2019 poz. 2311 zał. 3, rys. 10.28a) i ustaleniami M66 (`docs/reports/REVIEW-2026-11-14-s20-cloud-m66.md` §2, §5), zamknięcie P2 z `docs/reports/REVIEW-2026-11-13-s19-0179.md` oraz brak regresji budżetowej Low/High.

Materiał przejrzany:
- `artifacts/sigplate-0193/sbs3/after-heads.jpg` (825×2112, arkusz 6 wariantów głowic: front, tył, 3/4)
- `artifacts/sigplate-0193/sbs3/after-C-sheet-Low.jpg`, `after-C-sheet-High.jpg` (960×540, montaż 2×2: `sig-mast-front`, `sig-mast-back`, `sig-pole-front`, `sig-pole-34`)
- `artifacts/sigplate-0193/sbs3/gate3-signal-Low.jpg`, `gate3-signal-High.jpg` (960×540, Rondo Putry / `sbs-g3-b-182011943700132`)
- `artifacts/sigplate-0193/sbs3/sbs-P11-063-Low.jpg`, `sbs-P11-063-High.jpg` (960×290, lewa połowa `x=0..479` ref, prawa `x=480..959` render `photo_P11-063`)
- `artifacts/sigplate-0193/sbs3/sbs-P11-094-Low.jpg`, `sbs-P11-094-High.jpg` (960×290, lewa połowa `x=0..479` ref, prawa `x=480..959` render `photo_P11-094`)
- Zdjęcia referencyjne: `research/_incoming/mistral-p11-dojlidy-photos-v2/files/P11-063.jpg`, `P11-094.jpg`
- Porównanie historyczne: `.claude/worktrees/sigplate-0193/artifacts/sigplate-0193/before-C-sheet.jpg`
- Logi i statystyki z worktree: `before-C.log`, `after-C3-{Low,High}.log`, `after-D3-{Low,High}.log`, `stats.txt` (Low & High), `import-{C3,D3}.log`, `editmode.log`, `pytest-gis.log`.

**Brak zrzutu z telefonu** — dla zmiany prototypu sygnalizatora i pozycji kamery kontrolnej akceptowalne do scalenia (jak w `REVIEW-2026-11-13-s19-0179.md` i `REVIEW-2026-11-14-s20-0196.md`); przed bramką na docelowym urządzeniu zrzut wymagany.

---

## Werdykt: SCAL

Wszystkie wymagania ADR 0193 oraz uwagi z M66 (`REVIEW-2026-11-14-s20-cloud-m66.md` §5) zostały spełnione poprawnie i zweryfikowane zarówno na arkuszu prototypów, jak i w scenach Low oraz High obu regionów (`bialystok-industrial-c` i `bialystok-dojlidy`):

1. **Tarcza kontrastowa wyłącznie na wysięgnikach (`signal_head`):** głowice nad jezdnią mają czarną tarczę `0,85 × 1,40 m` z zaokrąglonymi narożami `R70` i białą obwódką `40 mm` odsuniętą o `20 mm` czarnego marginesu od krawędzi zewnętrznej. Głowice boczne na słupie/maszcie (`signal_head_side`) oraz piesze (`signal_ped`) i rowerowe (`signal_bike`) są bez tarczy.
2. **Kolejność warstw i tył głowicy:** tarcza kontrastowa leży za czarną obudową (`280 mm`) i trzyczęściowymi daszkami (`220 mm`). Od tyłu widoczny jest wyłącznie jednolity czarny ekran z zaokrąglonymi narożami — bez białego/szarego prostokąta z `before-C-sheet.jpg` i bez z-fightingu. Soczewki mają poprawne normalne (`+y`) i świecą od strony kierowcy.
3. **Kamera `photo_P11-094` (D-6 i Rosti):** po rekalkulacji pozycji na `(784.3, 394.0)` znak D-6 stoi w skali i położeniu poziomym zgodnym ze zdjęciem referencyjnym `P11-094.jpg`, a narożnik i koniec ściany północnej hali Rosti pokrywają kadr z dokładnością kilku pikseli.
4. **Budżet Low i High:** brak regresji. `drawsEst` w scenach kontrolnych Low bez zmian (`104/474/487/496`), `trisExact` rośnie o zaledwie `+0,14%` do `+0,33%` na kamerę, a `WORLD_MEMORY` zmienia się o `+0,0–0,1 MB` (`furniture` bez zmian: `8,6 MB` w C, `7,8 MB` w Dojlidach).

Nie stwierdzono żadnych blokerów P0 ani P1 w zakresie ADR 0193.

---

## Weryfikacja wymagań punkt po punkcie

| Wymaganie (M66 §5 / 0179 P2 / ADR 0193) | Wynik | Dowód wizualny i techniczny |
|---|---|---|
| Tarcza `0,85 × 1,40 m` R70, biała obwódka `40 mm` z marginesem `20 mm` **tylko** na `signal_head` (wysięgnik) | **PASS** | `after-heads.jpg` (`y≈40..320` vs `y≈385..655`), `after-C-sheet-{Low,High}.jpg`, `gate3-signal-{Low,High}.jpg` |
| Głowice boczne (`signal_head_side`), piesze (`signal_ped`), rowerowe (`signal_bike`) **bez tarczy** | **PASS** | `after-heads.jpg` (rzędy 2, 5, 6), `after-C-sheet` (`x≈392..410`, `x≈225..250`, `x≈703..758`), `gate3-signal` (`x≈302..313`, `x≈550..563`), `sbs-P11-063` (`x≈710..725`, `x≈828..855`) |
| Tarcza **za** czarną obudową `280 mm` i daszkami `220 mm`; tył czarny bez białego prostokąta i z-fightingu | **PASS** | `after-heads.jpg` (widok 3/4 `x≈620..765` i tył `x≈330..495`), `after-C-sheet-{Low,High}.jpg` (`sig-mast-back` `x≈695..735, y≈115..165`), `sbs-P11-063-{Low,High}.jpg` (`x≈758..796, y≈55..112`) |
| Pochylenie głowic nad jezdnią `7°` w dół | **PASS** | `after-heads.jpg` (widok 3/4 rzędów 1, 3, 4 wyraźnie pochylony względem rzędów 2, 5, 6) |
| Kamera `photo_P11-094`: D-6 i narożnik Rosti zgodne z `P11-094.jpg` | **PASS** | `sbs-P11-094-{Low,High}.jpg`: D-6 na `x≈630..647` (`x_rel≈150..167/480`) vs ref `x≈158..166/480`; narożnik hali `x≈585` (`x_rel≈105/480`) vs ref `x≈100/480`; koniec ściany N `x≈875..915` vs ref `x≈395..435` |
| Budżet Low i High (`drawsEst`, `trisExact`, `instancedTrisExact`, `WORLD_MEMORY`) bez regresji | **PASS** | Zgodność liczb ADR 0193 z `stats.txt` i `import-{C3,D3}.log` (tabela poniżej) |

---

## Oceny w zakresie ADR 0193 (1–10)

| Kategoria | Ocena | Uzasadnienie |
|---|---|---|
| Skala i proporcje | 9 | Tarcza `0,85 × 1,40 m` z narożami `R70` i obwódką `40/20 mm` zgodna z rys. 10.28a Dz.U.; obudowa i daszki `220 mm` w dobrych proporcjach; D-6 w `P11-094` w odpowiedniej skali. |
| Polskie realia | 9 | Rozdział głowica wysięgnikowa z tarczą vs boczna bez tarczy zgodny z próbą M66 (15/15 vs 0/11); czarna tarcza z białą obwódką za obudową; pochylenie `7°`. |
| Czytelność / rozpoznawalność | 8 | Głowice na Rondo Putry (`gate3-signal`) i w scenie C czytelne z przodu i od tyłu zarówno na Low, jak i High; soczewki świecą wyraźnie. |
| Artefakty (Low / High) | 9 | Brak z-fightingu na styku tarczy, obudowy i obwódki; brak białego pudła od tyłu (`P11-063`, `sig-mast-back`); obwódka nie migocze na Low. |

---

## Obserwacje i problemy (z podziałem na zakres)

### W zakresie ADR 0193 — brak P0/P1, drobne P2 (nieblokujące)
- **P2 — brak piktogramów na soczewkach `signal_ped` i `signal_bike`** (`after-heads.jpg`, rzędy 5–6, `y≈1320..1920`): jednolita zielona tarcza bez sylwetki pieszego/roweru. Już odnotowane w ADR (`Otwarte`) jako poza zakresem generycznego prototypu S-1 (i przy 0 instancjach w scenie).
- **P2 — brak detalu uchwytu mocującego między ramieniem wysięgnika a tarczą** (`after-C-sheet-High.jpg`, `sig-mast-back` `x≈705..725, y≈115..125`): ramię kończy się prostą rurą tuż przy górnej krawędzi tarczy bez obejmy/wysięgu montażowego. Z dystansu ulicy praktycznie niezauważalne.
- **P2 — orientacja lica znaku D-6 w `photo_P11-094`** (`sbs-P11-094-High.jpg`, `x≈630..647, y≈173..255`): w renderze widać niebieskie lico znaku D-6 zwrócone w stronę kamery, podczas gdy na zdjęciu referencyjnym `P11-094.jpg` (`x≈158..166, y≈156..253`) w tym miejscu widać szary tył znaku (lico zwrócone w drugą stronę / równolegle do przejścia). Kwestia reguły stawiania znaków przy przejściu w generatorze, poza zakresem kalibracji kamery.

### Poza zakresem ADR 0193 (istniejący backlog z `0179` / `0185` / `0196`, odnotowane dla porządku)
- **`sbs-P11-063-{Low,High}.jpg`:** kadr przesunięty w prawo względem zdjęcia (maszt sygnalizatora w środku `x≈700..795` zamiast przy prawej krawędzi), brak czerwonego asfaltu DDR na pierwszym planie, przerwy w krzewach, młode drzewka na narożniku zamiast dojrzałych drzew, biały płot z morą na hali Kuronia 2 w tle (`x≈850..959`).
- **`sbs-P11-094-{Low,High}.jpg`:** biały płot panelowy z morą przed halą Rosti (`x≈480..950, y≈200..225`), zacieki pod attyką na nowej hali, brak ciemnej obróbki bram.
- **`gate3-signal-High.jpg`:** oderwany pas korony drzewa po lewej na horyzoncie (`x≈115..200, y≈255..270`).

---

## Weryfikacja budżetu i testów (niezależnie sprawdzone w logach)

### Kamery sceny (`stats.txt`, `before-C` vs `after-C3` Low/High oraz `after-D3` Low/High)
| Kamera | `drawsEst` (before → C3 Low / High) | `trisExact` (before → C3 Low / High) | `instanced draws` (before → C3 Low / High) | `instanced trisExact` (before → C3 Low / High) |
|---|---|---|---|---|
| `sig-mast-back` | 104 → 104 / 104 | 198 095 → 198 759 / 388 353 | 48 → 52 / 59 | 2 989 → 3 229 / 4 576 |
| `sig-mast-front` | 474 → 474 / 955 | 560 096 → 560 963 / 2 539 778 | 114 → 125 / 320 | 14 093 → 14 189 / 41 826 |
| `sig-pole-34` | 487 → 487 / 784 | 596 890 → 598 438 / 2 636 222 | 97 → 109 / 187 | 10 432 → 10 516 / 30 272 |
| `sig-pole-front` | 496 → 496 / 1 013 | 605 599 → 606 466 / 2 740 800 | 117 → 129 / 307 | 15 560 → 15 594 / 39 615 |
| `sbs-g3-b-182011943700132` | — → 203 / 272 | — → 184 064 / 745 691 | — → 147 / 211 | — → 36 073 / 51 315 |
| `photo_P11-063` | — → 329 / 601 | — → 340 146 / 1 702 445 | — → 129 / 204 | — → 16 982 / 92 681 |
| `photo_P11-094` | — → 202 / 535 | — → 293 717 / 1 644 693 | — → 95 / 187 | — → 17 417 / 64 640 |

### `WORLD_MEMORY` (`import-C3.log`, `import-D3.log`)
- `bialystok-industrial-c` Low: `render_meshes=83.3 MB`, `instances=22.6 MB`, `collision_src=17.1 MB`, `total=123.1 MB` (`furniture=8.6 MB`).
- `bialystok-industrial-c` High: `render_meshes=226.2 MB`, `instances=22.6 MB`, `collision_src=17.1 MB`, `total=265.9 MB` (`furniture=8.6 MB`).
- `bialystok-dojlidy` Low: `render_meshes=64.5 MB`, `instances=18.2 MB`, `collision_src=15.5 MB`, `total=98.2 MB` (`furniture=7.8 MB`).
- `bialystok-dojlidy` High: `render_meshes=179.8 MB`, `instances=18.2 MB`, `collision_src=15.5 MB`, `total=213.5 MB` (`furniture=7.8 MB`).

### Testy automatyczne (z logów w `artifacts/sigplate-0193/`)
- `editmode.log`: `581 total, 580 passed, 0 failed, 1 skipped (Skipped:Ignored)`.
- `pytest-gis.log`: `1168 passed, 1 failed, 2 xfailed` — jedyny błąd to `tests/gis/test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage`, niezwiązany z `sigplate-0193`.
