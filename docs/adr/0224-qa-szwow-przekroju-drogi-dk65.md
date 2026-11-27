# ADR 0224 — QA szwów kafli: przekrój drogi na wspólnej krawędzi (łańcuch DK65 Białystok → Knyszyn)
Status: Proposed (chmura D, zadanie D3, gałąź `seams-0224`; bez Unity i bez `Data/raw`), 2026-11-15. Do scalenia przez lidera.
Powiązane: K1 `research/dk65-knyszyn-refs/README.md`, ADR 0205 (linie krawędziowe klasy < GP), 0207 (kafle 02–05),
0212 (Knyszyn 6,8 vs 7,1 m), 0214 (kafle 06–11, `dk65-xsec-k1`, szew 10/11 xfail), 0215 (PR #80), 0220 (PR #98,
`edge_line_spacing`), 0216 (latarnie knyszyn*), raport `docs/reports/SEAMS-DK65-2026-11-15.md`.

## Kontekst
Kafle 2048 m budują drogi niezależnie (graf przycięty do bbox + overrides per kafel). Testy szwów 0207/0214 porównują
wpisy overrides na wayu trasy, ale nie przekrój, który generator faktycznie stawia na krawędzi (szerokość po taperach,
linie, pobocza, położenie osi), i nie obejmują dróg bocznych ani kafli Knyszyn/Mońki/Tykocin. K1 wymaga na szwie
`dk65-10/11 ↔ knyszyn-s` rozstawu linii 6,0–6,4 m.

## Decyzja
1. **Narzędzie `tools/worldgen/qa/seams.py`** (CLI `python -m tools.worldgen.qa.seams`, funkcje `run`, `crossings`,
   `compare_pair`, `shared_edge`, `table`): dla każdej pary kafli ze wspólną krawędzią buduje sieć generatora tym samym kodem
   co `pipeline.build_network` (+ `assign_sides`, 1. przebieg), bierze końce łańcuchów na linii szwu (±0,05 m), paruje po
   `osm_way` i położeniu (≤ 5 m) i porównuje 14 parametrów z kolumną źródła (`derived:network`, `generated:roads_qa`,
   `graph:z_terrain`, `rule:ADR0220`). Tolerancja ±0,10 m (TOL_M). Referencje K1/0212 na drodze trasy (`REFERENCE`).
   Statusy OK / FAIL / N/D / UWAGA (kikut < 15 m lub droga wzdłuż szwu — nieporównywalne). Deterministyczne (test).
2. **Porównanie z PR bez scalania**: `--compare-ref <ref>` czyta `overrides.yaml` z ref tylko dla kafli, które ref zmienia
   względem `origin/main` (merge base) = „checkout + ten PR”. Kod generatora = checkout; klucz `edge_line_spacing` (PR #98)
   modelowany regułą z `markings.edge_lines` 0220 (oś = min(s/2, hw − 0,12)), gdy override go niesie.
3. **Wysokość osi**: nawierzchni drogi nie ma w `generated/*.json` — narzędzie porównuje `z_terrain` (NMT) węzła brzegowego
   i mówi to wprost; `z_terrain` jest `null` na krawędziach S/E każdego kafla (`terrain.sample`: `i + 1 >= n`), więc wiersz
   = N/D z notą o roczniku NMT. Poprawka próbkowania = propozycja P6 (osobne zadanie, zmienia grafy wszystkich regionów).
4. **Zastosowany override (A1)**: `dw671-tykocin-01` `seam-knyszyn-s-field-road-98071886` `{width: 5.7, lamps: false}` —
   ciągłość z `knyszyn-s` (BDOT10k 5,7 m, `rural-roads-unlit`); kafel bez pracy lokalnej.
5. **Propozycje bez zmian w danych** (kafle 0216 / PR #80 albo zmiana wymaga obu stron): P1 `dk65-xsec-k1` dosłownie w
   `dk65-11` + `knyszyn-s` (szew K1), P2 `width 6.6` na 234919333 w `bialystok-knyszynska` + `dk65-01`, P3
   `edge_line_spacing 6.2` w `dk65-06` (1560819273), P4 latarnie Obozowej / P4b nowa jezdnia DK65 05↔06, P5
   `edge_line_spacing 6.8` w knyszyn* + `dk65-monki-01`, P6 `terrain.sample` na krawędzi. Bloki YAML w raporcie §5.

## Wynik (checkout `seams-0224`)
17 szwów, 62 drogi (16 trasy), **32 FAIL**, 5 UWAGA. Po #98: 25 (znika 7: referencja K1 na 02/03, 03/04, 04/05 i lewa
strona 05/06); po #80: 29 (szerokość/pasy/rozstaw 05/06). Szew K1 `dk65-10/11` (6,2 | 7,1 m, Δ 0,9) i `dk65-11/knyszyn-s`
(7,1 | 7,1, poza K1) — bez zmian po obu PR; symulacja #98 + #80 + P1 + P2 + P3 + P5: 32 → 6 FAIL (3 × roads_qa do przebudowy,
P4, P4b). Szwy 06–10 i 01/02: zgodne we wszystkich parametrach (Δ osi 0,000 m).

## Konsekwencje
- Każda przyszła korekta przekroju kafla korytarza ma szybki sprawdzian szwów bez `Data/raw` (~35 s na łańcuch).
- `bialystok-industrial-c` / `bialystok-dojlidy` nie graniczą z łańcuchem (raport `not_adjacent`).
- Test `tests/gis/test_seams_0224.py`: syntetyczne pary (zgodne, 0,2 m, granica 0,1 m, bez drogi, droga urwana, reguła
  0220, determinizm) + dane z gita (≥ 1 droga trasy na każdym szwie DK65; strona dk65-10 szwu K1 = 6,2 m; pełny K1 na
  10/11 i 11/knyszyn-s = `xfail(strict)` do P1).

## Otwarte
1. P1 wymaga zgody/zakończenia 0216 (knyszyn-s) i zmiany testów 0214 (lista w raporcie §5).
2. P6 (próbkowanie NMT na krawędzi) — osobne zadanie, regeneracja grafów.
3. Render szwów po przebudowie (zasada 4) — lider: WorldC, kamery nad szwami 10/11 i 05/06.

## Uzupełnienie po fali 13

Audyt najpierw rezerwuje pary z tym samym `osm_way` w obrębie całego szwu, a następnie dopasowuje pozostałe końce
w granicy 5 m. Na szwie dk65-04 / dk65-05 koniec Sadowej (`w176274699`) mógł wcześniej zająć jedyny koniec
Szkolnej (`w244403508`) po stronie dk65-05. Po rozdzieleniu dróg Szkolna ma zgodny przekrój, a audyt osobno zgłasza
brak końca Sadowej w sieci. W jej grafie po stronie dk65-05 jest fragment 0,048 m, poniżej filtra 0,05 m w `network.load`.
Ocena przejezdności tego połączenia wymaga kontroli siatki i kolizji skrzyżowania.
