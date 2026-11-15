# REVIEW 2026-11-15 — ADR 0189 Brama szpitala przy Żurawiej (`hospgate-0189` @ `88df4559f`)

Recenzent: niezależny agent-recenzent (`Reviewer`, nie autor), tylko odczyt. Kryterium nadrzędne D51: rozpoznawalność > materiały.
Materiał:
- [sbs-P11-129-Low-overcast-r4.jpg](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/hospgate-0189/artifacts/hospgate-0189/sbs/sbs-P11-129-Low-overcast-r4.jpg) (lewa połowa = `P11-129.jpg` CC0, prawa = render `Low/overcast`)
- [sbs-P11-129-High-overcast-r4.jpg](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/hospgate-0189/artifacts/hospgate-0189/sbs/sbs-P11-129-High-overcast-r4.jpg)
- [Low-overcast-r4/photo-P11-129c.png](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/hospgate-0189/artifacts/hospgate-0189/Low-overcast-r4/photo-P11-129c.png) (1920×1080) oraz [High-overcast-r4/photo-P11-129c.png](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/hospgate-0189/artifacts/hospgate-0189/High-overcast-r4/photo-P11-129c.png) (1920×1080)
- Zdjęcie referencyjne: [P11-129.jpg](file:///C:/Users/matma/Documents/Claude/kamion/research/_incoming/mistral-p11-dojlidy-photos-v2/files/P11-129.jpg)
- Statystyki i logi: `Low-overcast-r4/stats.txt`, `High-overcast-r4/stats.txt`, `Low-overcast-r1/stats.txt`, `import-r1.log`, `import-r4c.log`, `editmode-r4c.log`, `pytest-gis-r4.log`
- Dokumenty odniesienia: [REVIEW-2026-11-14-s20-mistral-m62.md](file:///C:/Users/matma/Documents/Claude/kamion/docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md) (§7), [REVIEW-2026-11-14-s20-mistral-m62-fix.md](file:///C:/Users/matma/Documents/Claude/kamion/docs/reports/REVIEW-2026-11-14-s20-mistral-m62-fix.md), [0189-brama-szpitala-masonry-gate.md](file:///C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/hospgate-0189/docs/adr/0189-brama-szpitala-masonry-gate.md), [06_GRAFIKA_ANTI_AI_SLOP.md](file:///C:/Users/matma/Documents/Claude/kamion/docs/06_GRAFIKA_ANTI_AI_SLOP.md).

Współrzędne pikseli w sekcji problemów podano dla natywnego kadru `1920×1080` (`photo-P11-129c.png`), o ile nie zaznaczono inaczej.
**Brak zrzutu z telefonu** — [06_GRAFIKA_ANTI_AI_SLOP.md](file:///C:/Users/matma/Documents/Claude/kamion/docs/06_GRAFIKA_ANTI_AI_SLOP.md) §5 pkt 2 wymaga renderu z edytora i zrzutu z telefonu; dla zmiany danych regionu akceptowalne do scalenia, do uzupełnienia przed bramką 3.

## Werdykt: SCAL

Wszystkie kluczowe ustalenia z [REVIEW-2026-11-14-s20-mistral-m62.md](file:///C:/Users/matma/Documents/Claude/kamion/docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md) §7 oraz `M62-FIX` zostały poprawnie wdrożone w rundzie `r4`, a kadr `photo-P11-129c` jest natychmiast rozpoznawalny względem zdjęcia `P11-129.jpg`. Nie stwierdzono żadnych błędów **P0** ani **P1** w zakresie ADR 0189, brak artefaktów magenty, a napisy na tablicach są neutralne (bez nazw i godła rzeczywistej instytucji). Budżety `Low` i `High` (`drawsEst`, `trisExact`, `WORLD_MEMORY`) mieszczą się w hipotezach `docs/06` §6 i nie wykazują regresji względem `r1`.

## Weryfikacja listy kontrolnej `M62 §7`

| Punkt | Wymaganie (`M62 §7` / `M62-FIX`) | Wynik `r4` | Dowód (`photo-P11-129c.png`, 1920×1080) |
|---|---|---|---|
| 1 | Mur z jasnej cegły (~6,2 m) z płaską betonową nakrywą, filarem końcowym bez daszka i 5 poziomymi bordowymi tablicami `2 + 3` | **PASS** | Mur `x≈0–440, y≈440–715`, tablice `x≈185–355, y≈485–585` w układzie `2 + 3` z neutralnymi napisami (`Oddział I/II`, `Poradnia`, `Pracownia`, `Administracja`). |
| 2 | Ganek po stronie N (prawa strona kadru): wspólne zadaszenie z ciemnej blachy na jasnej belce i 2 ceglanych filarach, `B-20 STOP` + niebieska tablica na filarze, niebieska tablica `IZBA PRZYJĘĆ` na osobnym białym słupku przed prawym filarem | **PASS** | Zadaszenie `x≈1340–1920, y≈300–375`, 2 filary (`x≈1440–1660`, `x≈1780–1865`), `STOP` (`x≈1495–1605, y≈425–535`), `WJAZD NA PODSTAWIE` (`x≈1480–1615, y≈550–615`), `IZBA PRZYJĘĆ` na białym słupku (`x≈1710–1835, y≈400–545`). |
| 3 | Własny szlaban po prawej (czerwona obudowa, biało-czerwone ramię z tabliczką `OPŁATA ZA WJAZD 3 zł`), słupek z latarenką + `C-2` + `B-33 „20”`, znak `B-2` w głębi na osobnym słupku | **PASS** | Obudowa `x≈1265–1315, y≈590–735`, ramię z tabliczką `x≈925–1005, y≈625–650`, latarenka + `C-2` (w górę i w prawo) + `B-33 „20”` + mała tabliczka `x≈1275–1355, y≈225–545`, `B-2` w głębi `x≈750–775, y≈490–515`. |
| 4 | Tło: niskie 1–2-kondygnacyjne żółte/beżowe budynki szpitalne (zamiast 4-kondygnacyjnego szarego bloku), 2 smukłe kominy, kolumnowe iglaki za lewym murem | **PASS** | Budynki beżowe `x≈430–1145, y≈395–580`, 2 kominy `x≈845–895, y≈235–425`, kolumnowe iglaki za murem `x≈0–460, y≈0–530` oraz pojedynczy smukły iglak w głębi `x≈640–745, y≈135–605`. |
| 5 | Budżet `Low` i `High` (`drawsEst`, `trisExact`, `WORLD_MEMORY`) bez regresji | **PASS** | Szczegóły poniżej; brak regresji względem `r1`, `WORLD_MEMORY` niższy o `0,2–0,3 MB`. |

## Oceny (1–10)

| Kategoria | Ocena | Uzasadnienie |
|---|---|---|
| Skala i proporcje | 8 | Układ bramy, szerokość przejazdu, wysokość muru, ganku, kominów i kolumnowego iglaka w głębi bardzo dobrze odpowiadają `P11-129.jpg`. Drobne różnice: podest ganku zbyt wysoki, ramię szlabanu sięga niemal całej szerokości jezdni. |
| Światło i ekspozycja | 7 | Overcast spokojny, neutralna paleta Podlasia bez przesycenia i bloomu. |
| Materiały | 7 | Atlas cegły, tablic i znaków czytelny i spójny; słabsze są płaskie czarne okna budynków w tle oraz sterylna ściana portierni za gankiem. |
| Zużycie i osadzenie | 7 | Cegła i asfalt mają subtelne zróżnicowanie; podest betonowy ganku oraz ściana portierni wyglądają jednak zbyt czysto w porównaniu ze zdjęciem. |
| Powtarzalność | 8 | Brak widocznego kafelkowania na murze i filarach; kolumnowe iglaki zróżnicowane na tle nieba. |
| Polskie realia | 9 | Poprawne `C-2`, `B-33 „20”`, `B-20`, `B-2`, biało-czerwony szlaban z opłatą 3 zł i typowa polska tablica informacyjna izby przyjęć bez naruszenia nazw własnych. |
| Czytelność / rozpoznawalność | 9 | Kadr `P11-129` jest rozpoznawalny na pierwszy rzut oka zarówno w `Low`, jak i `High`. |
| Artefakty (Low) | 8 | Brak magenty i mory; na `Low` (`renderScale=0.75`) widoczny jedynie lekki aliasing liści iglaków na tle nieba, w `High` ostry. |

## Problemy (lista P0 / P1 / P2)

Brak **P0** i brak **P1**.

### W zakresie ADR 0189 (`hospgate-0189`)
- **P2 — zbyt wysoki i sterylny podest betonowy pod gankiem** (`photo-P11-129c.png` `x≈1350–1920, y≈670–790`): na zdjęciu `P11-129.jpg` filary ganku stoją na niskim, nierównym stopniu/chodniku z kostki, natomiast w renderze tworzy go wysoki, idealnie gładki blok jasnoszarego betonu. Poprawka: obniżyć cokół/podest i nadać mu ciemniejszą/zużytą fakturę betonu.
- **P2 — długość ramienia szlabanu** (`photo-P11-129c.png` `x≈560–1275, y≈612–628`): w renderze ramię zamyka niemal całą szerokość jezdni aż do lewego krawężnika; na `P11-129.jpg` kończy się w ok. 2/3 szerokości jezdni, zostawiając przejście po lewej.
- **P2 — sterylna ściana portierni i sąsiedniej bryły za słupkiem znaków** (`photo-P11-129c.png` `x≈1650–1920, y≈380–650` oraz `x≈1245–1360, y≈450–565`): gładkie, jednolite szare płaszczyzny bez podziałów ani detalu okiennego/drzwiowego widoczne w prześwicie ganku i za znakiem `20`.

### Poza zakresem ADR 0189 (do backlogu / sąsiednie zadania)
- **P2 — brak chodnika z kostki betonowej pod lewym murem** (`photo-P11-129c.png` `x≈0–440, y≈680–950`): w `P11-129.jpg` przed murem biegnie chodnik z szarej kostki z czerwonym pasem; w renderze jest tam pas trawy.
- **P2 — płaskie czarne okna budynków szpitalnych w tle** (`photo-P11-129c.png` `x≈760–1085, y≈465–515`): brak ram, ościeży i odbić (spójne z ogólnym backlogiem `docs/06 §2`, poprawa względem usuniętego 4-kondygnacyjnego bloku jest jednak zasadnicza).
- **Brak zrzutu z telefonu** (`docs/06 §5 pkt 2`): do wykonania podczas najbliższej weryfikacji na urządzeniu (A16) przed bramką 3.

## Budżet i walidacja (`r4`)

- **Zestaw `masonry_gate` (`zurawia-hospital-gate`)**: `576` trójkątów, `1` materiał (`sign_MG4a8c94b1`), `1` draw call, atlas `1024×1024`.
- **Low (`photo-P11-129c`, `overcast`, `msaa=2`, `renderScale=0.75`)**:
  - `r1`: `objects=57`, `drawsEst=325`, `shadowDrawsEst=35`, `trisExact=448016` (+ instanced: `draws=76`, `instances=63`, `trianglesExact=11184`).
  - `r4`: `objects=58`, `drawsEst=329`, `shadowDrawsEst=38`, `trisExact=440709` (+ instanced: `draws=80`, `instances=64`, `trianglesExact=12158`).
  - Zmiana `r1 → r4`: `+4` `drawsEst` (+1,2%), `-7 307` `trisExact` (-1,6%) — brak regresji, w hipotezie `docs/06 §6`.
- **High (`photo-P11-129c`, `overcast`, `msaa=2`, `renderScale=1.0`)**:
  - `r4`: `objects=166`, `drawsEst=621`, `shadowDrawsEst=369`, `trisExact=915806` (+ instanced: `draws=171`, `instances=308`, `trianglesExact=36415`) — w hipotezie `docs/06 §6`.
- **`WORLD_MEMORY` (`import-r1.log` vs `import-r4c.log`)**:
  - `Low`: `97.7 MB` (`r1`) → `97.5 MB` (`r4c`, `-0.2 MB`).
  - `High`: `213.1 MB` (`r1`) → `212.8 MB` (`r4c`, `-0.3 MB`).
- **Testy**:
  - `editmode-r4c.log`: `587 total, 586 passed, 0 failed, 1 skipped (Skipped:Ignored)`.
  - `pytest-gis-r4.log`: `1239 passed, 3 skipped, 3 xfailed, 2 failed` (oba niepowodzenia dotyczą wyłącznie przestarzałego `Data/raw/derived/bialystok-industrial-c/world`, poza zakresem `hospgate-0189`).
