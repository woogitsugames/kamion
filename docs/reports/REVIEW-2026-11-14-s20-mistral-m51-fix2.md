# Przegląd s20 — Mistral M51-FIX-2 (P10 zieleń, `research/mistral-p10-greenery-3`)

Data: 2026-11-14 · recenzent: agent Claude (tylko do czytania, bez worktree) · gałąź `origin/research/mistral-p10-greenery-3` @ `a1767558e` (ostatnia zmiana treści `e9f4af246`; commity FIX-2: 7f56ea7be, 886fe8842, 8362181c9, 00363761d, e9f4af246 + merge main).
Odniesienia: blok M51-FIX-2 w `docs/owner/MISTRAL-FIXES-10.md`, przegląd `docs/reports/REVIEW-2026-11-13-s19-mistral-m51-m53-m50v2.md` §3.

## Werdykt: **SCAL z erratą**

Wszystkie 6 punktów FIX-2 jest zrobionych, a każdy sprawdziłem na obrazie albo w danych. Nakładki są teraz prawdziwym dowodem: niezależnie pobrany WMS GUGiK daje korelację 0,93–0,99 bez odbicia i ≤ 0,30 po odbiciu N–S. Pozostały tylko niespójności w opisach (errata poniżej) i znana luka danych: próg żywopłotów 13/20, uczciwie zgłoszony. FIX-2 nie wymagał dobicia tego progu.

**Zakres scalenia:** PR #49 (M51 v2) jest już scalony. „SCAL” dotyczy więc tylko delty FIX-2: 16 plików, wszystkie w `research/mistral/p10-greenery-3/` (+839/−212). `git merge-tree origin/main(e668a9588) a1767558e` przechodzi czysto. Cztery PNG są w LFS: `w1/w2/w3`, `nonveg_check`. Obiekty pobrałem `git lfs fetch` i są na zdalnym serwerze LFS. Komentarz PR #49 z 2026-11-14T17:03Z zawiera surowy `git diff --stat`.

## 1. Punkty bloku FIX-2

| # | żądanie | stan na gałęzi | weryfikacja recenzenta | ocena |
|---|---|---|---|---|
| 1 | M51-214 usunąć, M51-112 = „brak żywopłotu” | manifest ma 59 wierszy i nie ma 214. Uwaga M51-112: „po prawej trawnik, zaparkowane samochody… brak żywopłotu”. `hedge_viewings.walk_123946.zywoplot_m51_fix2=false` | obejrzałem `frames/M51-112.jpg`: ścieżka rowerowa, żółte barierki, po prawej trawnik i rząd aut przed blokiem, żywopłotu brak | ✓ |
| 2 | dołożyć kadry 119–126 / 219–222 (Commons 123952…132717), poprawić ZAWARTOSC | ZIP v3: `frames/M51-101…133` (33) i `viewings/` (36). 119–126 = 123952, 132358, 132511, 132717, 125403, 125410, 125414, 125438. 219 → 125403, 220 → 125414, 221 → 123959, 222 → 124049. `ZAWARTOSC_v3.txt` zastępuje v2 i ma sekcję wyjaśniającą `walk_*` | 121 plików, z czego 120 ma sumę SHA-256 w `ZAWARTOSC_v3.txt`: **120/120 OK**, a 121. plikiem jest sam ZAWARTOSC. Kopia ZAWARTOSC w gicie i w ZIP jest identyczna. `metadane/manifest.csv` = manifest gałęzi 1:1. Wszystkie 10 kadrów z listy FIX obejrzane, opisy w §2 | ✓ |
| 3 | 227/231 → szpaler/zadrzewienie; 232 = 1,0–1,5 m; 229/230 = rabata | kolumna `obiekt`: 219, 227, 231 = „szpaler/zadrzewienie (NIE żywopłot)”; 221, 222, 226, 229, 230 = „rabata ozdobna (NIE żywopłot)”. 232 `wysokość_m` = 1.0-1.5. Liczonych odcinków żywopłotu jest 13 | obejrzałem 131202 (rząd ok. 6 iglaków w głębi za parkingiem), 125821 (ściana zadrzewienia za placem zabaw), 131327 (przedogródek: krzewy, malwy, funkie), 131342 (tablica „…52”, niskie nasadzenia przy elewacji), M51-130 (siatka z Roto/ROCKWOOL, zarośla ~1–1,5 m pod drzewami). Wszystko zgodne z nowymi typami. Mistral sam przeniósł dodatkowo 219, 221, 222 i 226, i to też zgadza się z obrazem | ✓ |
| 4 | nakładki north-up, skala px/300 m, kółka na koronach | obraz pobrany prosto z WMS GUGiK (0,25 m, 2024-05-27), 1200 px w ZIP i 960 px w gicie. Żółte osie OSM jako kontrola rejestracji. Pasek 50 m | **korelacja z WMS pobranym przeze mnie z tych samych bboxów** (EPSG:2180, `overlays_check.json`): W1 0,99 (git 960 px: 0,982) wobec −0,07 po odbiciu N–S, W2 0,978 / 0,04, W3 0,932 / 0,30. Pasek 50 m = 201 px na 1200 px (4 px/m ✓). Osie OSM leżą na jezdniach, znaczniki pokrywają cały kadr. W1: zielony autobus na jezdni alei bez znacznika ✓ | ✓ |
| 5 | filtr nie-roślinności (autobus 53,1556 N 23,1524 E) | `tools/filter_nonveg.py`: (A) jezdnia OSM + wydłużenie/prostokątność/V, (B) V > 140. Usunięte 14 obiektów (A: 4, B: 10), lista w `nonveg_removed.geojson`, wycinki w `nonveg_check.png` | C01782 (23,15246 E, 53,15545 N, 18 m od punktu z przeglądu) usunięty. Najbliższa pozostała korona leży **48,0 m** dalej (moje przeliczenie). Na `nonveg_check.png` wszystkie 14 wycinków to autobusy, pojazdy albo elementy dachów ✓ | ✓ |
| 6 | M51-301 zgodne z README | M51-301 = 2520 iglaste / 2724 liściaste = 5244 (po filtrze). Stan przed filtrem 2738 jest podany w README | `crowns.geojson`: 5244, Counter `typ` = 2724/2520 ✓ | ✓ |

## 2. Obejrzane kadry i nakładki (22, wszystkie ≤ 960 px)

Kadry, z opisem z manifestu porównanym z obrazem:
- **M51-112**, opis zgodny (pkt 1).
- **M51-119**: blok nr 56 z szyldami przedszkola „Elfiki” i żłobka „Elfy”, czerwone auto, skuter, znak P ✓.
- **M51-120**: pełne ogrodzenie z paneli na słupkach z bloczków, młode drzewka na trójnogach, pieszy ✓.
- **M51-121**: INTRATEL, AUTO KOMIS PREMIUM, słupki BNP Paribas, litery K-O-M na siatce ✓.
- **M51-122**: siatka na czerwonych słupkach, pylon Shell, budynek z cegły, Galeria Łazienek / Bocaro z małymi iglakami przy elewacji ✓.
- **M51-123** (= 219): wierzby nad żółtą barierką, ekrany akustyczne Andersa ✓.
- **M51-124**: wierzby, kwitnąca tawuła, czarna barierka ✓.
- **M51-125** (= 220): znaki 70 i „prosto”, różowe krzewy pod drzewami po prawej ✓.
- **M51-126**: rów z betonowym wylotem, kamień polny, niebieska rura ✓.
- **walk_123959** (221): blok z gabinetem ortholux, kule krzewów przy elewacji ✓.
- **walk_124049** (222): blok nr 58, pojedyncze niskie krzewy ✓.
- **walk_131202** (227), **walk_125821** (231), **walk_131327** (229), **walk_131342** (230), **M51-130** (232): opisy w §1 pkt 3, zgodne.
- **walk_131205** (228): blok nr 54, po lewej kwitnące krzewy ~1–1,5 m ✓. Pas swobodnych krzewów, liczony jako żywopłot. Słusznie tylko przy definicji „pas krzewów”.

Nakładki:
- **w1_skarpa**: osiedle przy alei. Kółka leżą na drzewach w ogrodach, na skarpie N i na podwórkach. Kilka małych znaczników trafia w skraje dachów i trawniki. Mistral sam zgłasza to jako ograniczenie ExG.
- **w2_max_korony**: ogródki działkowe i tory. Znaczniki leżą na drzewach działkowych, ale część na płatach trawy lub gołej ziemi. Cyjan ma długie proste linie N–S przez działki (artefakt, opisany).
- **w3_max_zwarta**: las iglasty. Cyjan obrysowuje płaty drzewostanu, a jedna długa ukośna linia przecina kadr (artefakt). Koron jest mało, co jest poprawne, bo las trafia do warstwy zwartej.
- **nonveg_check**: 14/14 to nie roślinność ✓.

## 3. Liczby, źródła, licencje

- **Żywopłoty: 13 odcinków**, wysokość wszędzie ESTIMATED z odniesieniem (płot, siatka, barierka, słupek). 212, 215 i 218 mają typ jawnie oznaczony UNVERIFIED (uwagi s19). Bez nich zostaje 10. Z G7 razem 25 odcinków, każdy z obejrzanego kadru.
- **Korony:** w danych jest tylko `r_m` (0,71–6,49 m, mediana 1,15) i heurystyczny `typ`. **Brak wysokości i rozstawu.** Gatunki, obwody i rozstaw z przetargu Strabag są UNVERIFIED (skany bez OCR). Tylko 74 drzewa / 109 krzewów / 20 600 m² / ~385 mb mają status SOURCED (komunikat UM).
- **Licencje:** kadry z Commons (Rakoon) według `commons_meta_v3.json` to 65× CC0 i 4× CC BY 3.0 (113, 114, 133 oraz kopia 065239 w `viewings/`), wszystkie z dopiskiem „referencja, nie tekstura”. Ortofoto: CC BY 4.0. OSM: ODbL. Google pojawia się tylko w deklaracjach zakazu (`git grep -i google` w katalogu gałęzi i w metadanych ZIP). Nie ma żadnego URL ani źródła Google.
- **Samokontrola z obrazami:** w FIX-2 wszystkie 10 kadrów z listy FIX i 8 kadrów reklasyfikowanych obejrzano ponownie. Pola `m51_fix2_obejrzane_2026_11_14` / `zywoplot_m51_fix2` są w 20 z 37 wpisów `hedge_viewings.json`, opisy zgadzają się z obrazem. **Losowanie `audit_20_percent.json` nie było powtórzone po FIX-2** (nadal 60 wierszy, data 2026-11-13). Dopuszczalne, bo każdy zmieniony wiersz obejrzano osobno.

## 4. Errata do REVIEW-NOTE (przy scaleniu, nie blokuje)

1. **Rozdzielczość JPG:** pliki w ZIP v3 mają 1920×1080 (`pobrano_url` = miniatura `1920px-`). README, ZAWARTOSC_v3 i `sources.md` piszą „1600 px”. Wymóg briefu „≤ 1600 px” jest formalnie przekroczony, co dla referencji nie ma znaczenia.
2. **`sources.md` jest nieaktualny:** nagłówek KartaView ma „CC BY 4.0”, a README „CC BY-SA 4.0 (ujednolicono)”; obowiązuje CC BY-SA 4.0. Dalej: liczniki „51× CC0 / 3× CC BY 3.0” (w v3 jest 65 / 4), seed audytu „20261113” (obowiązuje 20261114), bbox Panoramax z literówką (`23.158` zamiast `53.158`).
3. **`hedge_viewings.json`:** stare pola `zywoplot`, `typ` i `wys` zostały z v2. Przykład: 131202 ma `zywoplot: true` i `3-4 m`. Wiążące są pola `*_m51_fix2` i manifest. Konsument danych musi czytać `zywoplot_m51_fix2`, a gdzie go nie ma, kolumnę `obiekt` z manifestu. README mówi o 36 obejrzeniach, plik ma 37 kluczy (doszedł `walk_123946`).
4. **Drobne:** README podaje „27 poligonów zwartej zieleni w W1”, a `overlays_check.json` 28. Audyt 20 % jest z v2 (patrz §3).
5. **Ograniczenia, które zostają:** ciemne pojazdy poza jezdnią główną nie są filtrowane (UNVERIFIED). Znaczniki mogą trafiać w trawniki (ExG bez nDSM). Warstwa `compact_greenery` ma proste artefakty krawędzi i przed użyciem trzeba ją przyciąć poligonami jezdni i budynków.
6. **Próg ≥ 20 żywopłotów jest niespełniony (13).** Skidelska, Wileńska i Łańcucka mają 0 letnich kadrów z wnętrza ulicy. To luka źródeł, nie błąd pracy.

## 5. Co dane dają grze

- **ADR 0163 (zieleń ulic domów, `plot_kit` / `plantings`):** z 13 odcinków M51 i 12 z G7 da się zbudować tabelę typów żywopłotu przy alei i ulicach zbiorczych. Liściaste strzyżone mają 1,0–1,5 m, żywotnik 1,5–2,0 m, pasy swobodnych krzewów 1,0–3,0 m. Osobne klasy to **rabata przy elewacji bloku** (0,5–1,5 m, kule i byliny: 221, 222, 229, 230) i **szpaler/zadrzewienie** (> 3–6 m: 219, 227, 231). To uzasadnia dodanie w generatorze klasy „rabata przyblokowa” obok żywopłotu, zamiast ciągłego pasa ~1,2 m przy blokach. Wszystkie wysokości mają status ESTIMATED, więc wpisujemy je jako WORKING_VALUE.
- **ADR 0170 (korony przy kamerze / las):** `crowns.geojson` (5244, po filtrze) to drugie, ostrzejsze źródło pozycji drzew dla kafla Al. Tysiąclecia (EPSG:2180 776971–779019 / 595199–597247), obok `plot_canopy.json`. Ma tylko promień i heurystyczny typ, bez wysokości. Wysokość dalej liczymy z D/(W/H) według G7. Rozstawu nie ma (UNVERIFIED). `filter_nonveg.py` (jezdnia OSM + V > 140) warto przenieść do `tools/worldgen` jako post-filtr każdej detekcji z ortofoto: w industrial-c zielone autobusy BKM dają fałszywe korony na jezdniach.
- **ADR 0186 (Dojlidy, Argon, `dojgreen-0186`):** kafel M51 **nie obejmuje Dojlid** (leży przy Al. Tysiąclecia), więc pozycje koron nie przechodzą. Przenosi się tylko **metoda**: north-up WMS z kontrolą korelacji, filtr nie-roślinności, rozdział korona / zwarta zieleń. Przenosi się też **typologia**: zarośla wierzbowe przy rowach i ekranach Andersa (123/219, 126) są dobrym wzorcem dla pasów przy drogach przemysłowych, a pas swobodnych krzewów pod drzewami przy siatce z banerami (232) dla płotów zakładów. Wysokości narożnika P11-063 (9–11 m) trzeba brać z własnego pomiaru 0186, nie z M51.

## 6. Blok do `docs/owner/MISTRAL-FIXES-12.md`

Nie dotyczy: werdykt to SCAL z erratą, nie FIX.
