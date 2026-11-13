# ADR 0160 — G3-A: P0 układu kadrów i kotwice pierwszego planu (pozy, tablice, znaki)
Status: Proposed (agent g3a-0160, s16, gałąź `g3a-0160`), 2026-11-13. Do scalenia przez lidera; świat do przebudowy na main.

## Kontekst
Recenzja `docs/reports/visual/REVIEW-2026-11-13-s16-world-int.md` (D51): G3-A 5 R / 15 P / 2 N. P0: `cm109685822`,
`cm92458760` (G3-A) i `339463` (G3-B) pokazują inny układ niż zdjęcie. P1: brak kotwic pierwszego planu pod wiaduktem
Bieżeństwa (zielone tablice, wyspy żwirowe, podpory, bariery), brak A-30 (275528), sygnalizatorów (182011), D-1 (4312632),
A-7 (1528935). Pytanie: winna jest poza kamery czy świat?

## Metoda (dowody, bez zgadywania)
1. **Widok z góry świata vs ortofoto GUGiK vs OSM** (`artifacts/g3a-0160/tools/glbtop.py`): rasteryzacja chunków GLB
   (lod0, materiał na kolor) obok wycinka ortofoto 0,25 m i grafu dróg, z ostrosłupem kamery.
2. **Sondy póz** (`probes.py`, `plan_r1..r3.py`, `render.ps1`): kandydaci renderowani w jednym przebiegu Unity (Low, overcast),
   arkusze zdjęcie | sondy (`r*/sheet-*.jpg`). Wybór wzrokowy po kotwicach nazwanych w `choice.json`.
3. **Resekcja**: (a) cm92458760 — dwa kominy EC (OSM 628899553/4, `ec_chimneys.json`) na x 0,773 i 0,947 zdjęcia,
   11,1° rozstawu przy hfov 70; (b) seria richlv 2020-08-15 pod wiaduktem — heading z punktu zbiegu pomostu (oś 298,6°,
   poprawka na pochylenie 18–22°), pozycja z podpór (`resect.py`, `resect2.py`) i wzrokowo z sond.
4. Zapis: `sbs_authored_overrides.json` (east/north_delta, heading_delta, eye, horizon, hfov) → wpisy `sbs_cameras.json`
   / `sbs_references.json` liczone tym samym wzorem co `sbs_gate3.prepare()` (`finalize.py`, kontrola: sonda == produkcja
   < 2 mm, `verify_all()` bez rozbieżności). Wszystko WORKING_VALUE, nie pomiar w terenie.

## Przyczyny P0
<!-- TABELA_P0 -->

## Kotwice pierwszego planu
<!-- TABELA_KOTWICE -->

## Zmiany
<!-- ZMIANY -->

## Ocena 22 par G3-A (przed → po)
<!-- OCENA -->

## Do zrobienia w świecie (dla 0159 / lidera)
<!-- SWIAT -->

## Konsekwencje
- Pozy richlv dostają eye 0,9 (jak ADR 0143) i heading z pomostu: systematyczny błąd SfM heading +8…+15° w całej serii.
- Kotwice, które istniały w świecie, ale były poza kadrem, nie wymagały przebudowy (podpora 177786, sygnalizatory 182011).
- Nowe znaki są danymi (`overrides.yaml`, `kind: gate3_sign`) i przeżywają reimport.
