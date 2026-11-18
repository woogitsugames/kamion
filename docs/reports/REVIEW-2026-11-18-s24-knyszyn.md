# REVIEW 2026-11-18 — Knyszyn po knyszyn-r24 (deski Klattów, rondo DK65), visual-critic (agent regen-c-s24)

**Werdykt: FAIL (anti-slop docs/06 §2) · PASS warunkowy dla rozpoznawalności D51 (układ ronda i ulic).**
Obejrzano 11 renderów `artifacts/knyszyn-r24/small/*.jpg` (edytor, High clear; brak zrzutu z buildu Windows — §5.2 niespełnione) i 14 zdjęć właściciela `Data/raw/refs/owner-knyszyn-2026-11-15` (tylko oglądanie; arkusz `artifacts/regen-c-s24/knyszyn-refs-sheet.jpg`). **Wśród zdjęć właściciela nie ma Domu Klattów** — deski oceniane wyłącznie wg docs/06 i typologii, nie side-by-side.

## Dom Klattów (look-dom-klattow-after, klattow-crop-after, klattow_before_after)
Zysk r24 realny: deski mają teraz wiarygodną długość i nie czytają się jak cegła/klepka (porównanie before/after). Ale bryła nadal jest makietą:
- **P1-1 płaska elewacja drewniana bez detalu Podlasia:** brak desek narożnych, opasek okiennych (nadokienników), okiennic, deskowania pionowego w szczycie (szczyt ma te same poziome deski co ściana), listwy cokołowej. To są cechy, po których dom drewniany podlaski się rozpoznaje — bez nich to „tekstura drewna na pudełku”. Poprawka: generator fasady `wood_siding`/`wood_planks` — narożniki 0,12–0,15 m, opaski 0,10 m, szczyt pionowo (wymiary `WORKING_VALUE`, zweryfikować na zdjęciu domu — poprosić właściciela o 2–3 zdjęcia Kościelnej).
- **P1-2 kafelkowanie desek widoczne:** w klattow-crop-after jasne/ciemne pasy powtarzają się w regularnym rytmie, końce desek wyrównane w pionie co kafel; ściana w słońcu 161,137,110 vs w cieniu 82,77,71 (zmierzone sRGB) — kontrast OK, wariacja nie. Poprawka: losowe przesunięcie końców desek per rząd, wariacja tonu per deska (mapa ID), warstwa zacieku pod okapem i przy cokole.
- **P2-1 dach sterylny:** dachówka jednolita 178,122,104, sat 35 %, bez gąsiorów na kalenicy, bez zabrudzeń przy kominie i rynnie; deska czołowa/podbitka jaskrawo biała, idealnie prosta — „plastik”. Poprawka: gąsiory jako osobny mesh, podbitka w kolorze drewna/szarym, maska brudu wg ekspozycji.
- **P2-2 okna za małe i za rzadkie dla tak długiej ściany** (2 okna na ~20 m od ulicy; skala UNVERIFIED — brak zdjęcia), okno w szczycie bez ramy.
- **P2-3 płot sztachetowy przesycony:** 101,59,48, sat 48 % — najbardziej nasycony element kadru obok nieba; ten sam typ płotu powtarza się w tykocka-into-town po obu stronach ulicy (powtarzalność §2). Odbarwić ku szaremu drewnu, 2–3 warianty płotu (siatka, panel, deski poziome) na ulicy.

## Rondo DK65 (rondo-owner-10/11, rondo-dk65-above/top) vs 9/10/11.webp
- Układ zgodny: 4 wloty, wyspa centralna, wysepki dzielące, przejścia przy wlotach — rozpoznawalne z drona (D51 OK).
- **P1-3 tymczasowa zapora drogowa (biało-czerwona) w poprzek wlotu DK65 NW** (dk65-outlet-nw, rondo-dk65-above) — w miasteczku czyta się jak błąd/plac budowy; jeśli to koniec świata, przesunąć poza zasięg widoku z ronda lub zastąpić fizyczną granicą poza zabudową.
- **P2-4 wyspa centralna jaskrawo biała, płaska, z trzema kropkami zieleni;** na 10.webp opaska jest beżowa/piaskowa z kostki, środek z nasadzeniami i ozdobą. Wysepki dzielące na zdjęciu mają jasne krawężniki i kostkę — w renderze szare, płaskie.
- **P1-4 teren: jednolity szum „na wszystkim”** (rondo-owner-11, rondo-dk65-top): pagórkowate plamy jasne/ciemne o tej samej skali od ronda po horyzont, pola bez miedz, upraw, rowów; na 11.webp pola są gładkie, pasowe, z wyraźnymi miedzami. To czerwona flaga §2 pkt 1.
- **P2-5 drzewa-kępki** (dk65-outlet-nw): bryłowate, jednolite „brokuły” z prześwitami, część pojedynczo na polu; na zdjęciach dominują duże liściaste przy działkach. Zabudowa mieszkalna OK, ale ogrody puste (brak drzew owocowych, aut, podjazdów).

## Ulica (tykocka-into-town)
Najlepszy kadr: skala jezdni, chodniki, linie nN, latarnie wiarygodne. Uwagi: chodniki z kostki szarej o widocznym kafelkowaniu w pierwszym planie, brak zużycia nawierzchni; elewacje tynkowane sterylne; wszystkie płoty ten sam typ (P2-3).

## Światło / niebo
Niebo 88,138,190, sat 42 % z cumulusami „z pudełka”, wszystkie kadry w tym samym słońcu — wygląd gry, nie zdjęcia z telefonu. Zdjęcia właściciela 1–8: lekko przymglone, chłodniejsze. Nie blokuje (poza zakresem r24), ale wymaga wariantu overcast w kamerach Knyszyna.

## Oceny (1–10)
rozpoznawalność D51 6 · skala 6 · materiały 4 (deski 5) · światło 4 · zużycie/osadzenie 3 · powtarzalność 4 · polskie realia 6 · artefakty 6.

## Do zrobienia przed PASS
P1-1…P1-4 + render z buildu Windows + kamera na wysokości oczu przed Domem Klattów z drugiej strony ulicy + prośba do właściciela o zdjęcia Domu Klattów (Kościelna) z frontu i z ukosa.
