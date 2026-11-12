# ADR0153 — niezależna ocena wizualna B

**Wynik bieżący: PARTIAL.** W obejrzanych widocznych celach nie stwierdziłem nowej blokującej regresji od konsolidacji materiałów. Pełna akceptacja wszystkich przejść pozostaje otwarta z powodu zasłoniętych celów i braku czytelnego kadru kratki agregatu. Raport czeka na zapowiedziane uzupełnienie kamer. To ocena statycznych renderów edytora, bez orzeczenia o telefonie ani dynamicznym przejeździe.

## Zakres rzeczywiście obejrzany

- Wszystkie **40 arkuszy overviews**: po10 dla Low-clear, Low-overcast, High-clear i High-overcast; pokazują114kamer na warunek, łącznie456par przed/po.
- Szczegółowe target-crops: Low SUV15.9/16.1 i42.4/42.6m, tractor19.9/20.1 i49.9/50.1m, trailer19.9/20.1 i49.9/50.1m; High SUV37.4/37.6 i127.4/127.6m, tractor59.9/60.1 i149.9/150.1m, trailer59.9/60.1 i149.9/150.1m. Te zestawy obejrzano w obu pogodach. Dodatkowo bliskie8m hatch/SUV/trailer we wszystkich czterech warunkach.
- Pełne pary najwyższych MAE, w szczególności Low-overcast: stretch-05-docks, trailer049p9/050p1/059p9/060p1, tractor008p0/019p9/020p1, g3a_eye_s0112, hatch127p4/127p6, g3a_ext34_s0338; również High-clear hatch008p0 i High-overcast route-onramp-andersa-above.
- Lokalne fotografie real-cars-contact.jpg, r4-reference-review.jpg oraz wheel-photo-crop.png, wraz z opisem pochodzenia. Oglądanie wyłącznie do oceny; nie kopiowałem referencji do worktree.
- Sprawdzono metadane projection-probe.json, glb-audit.json, CAMERAS.md, image-metrics.json i nagłówek final-editmode.xml. XML podaje452passed/0failed/0skipped; nie uruchamiałem testów.

## Wyniki dla widocznych celów

1. **Bliski LOD0 i tablice — brak zaobserwowanej regresji.** W lod_car_hatch_white_008p0 w obu tierach/pogodach przedni van zachowuje czytelną tablicę BI3G87, pasek i położenie znaków; biały samochód obok zachowuje lakier i reflektory. SUV008p0 zachowuje ciemny lakier, okna, lampę tylną i położenie kół. Nie jest to pełny test zmienności wszystkich tablic na instancjach.
2. **SUV0→1 — bez nowego pogorszenia widocznego na parach.** Low015p9/016p1 i High037p4/037p6 pokazują ten sam pojazd z częściowo zasłoniętym przodem. Nowy LOD1 utrzymuje sylwetkę, ciemne szyby, lampę i podobny kolor. Wyraźna zmiana felg na jaśniejsze występuje już w baseline.
3. **Ciągnik Low0→1 — bez nowego ubytku geometrii.** Tractor019p9/020p1 zachowuje kabinę, zbiornik, czarne podwozie i oddzielne koła. Skok szczegółowej okrągłej felgi do jasnego wielokąta jest taki sam w baseline. Kolor niebieski i lokalizacja okien pozostają spójne przed/po.
4. **Naczepy w dokach — drobne różnice odpowiedzi, bez błędów atlasu.** W stretch-05-docks i trailer049p9/050p1 Low-overcast widać małe zmiany jasności dolnych ram/podpór i drzwi. Nie znalazłem nowych kolorowych plam, czarnych prostokątów na karoserii, odwróconych powierzchni ani znikających kół. Najwyższy MAE0.269 w stretch-05-docks nie oznacza dużej widocznej degradacji całego kadru.
5. **Widoki drogowe i kabinowe — brak widocznej zmiany kompozycji.** Wszystkie overviews zachowują ten sam układ obiektów. Pary kabiny i lusterek nie ujawniają pogorszenia elementów bliskich. Mała skala overview ogranicza ocenę drobnych detali.
6. **Kratka agregatu — niepotwierdzona obrazem.** W obecnym zestawie nie rozpoznaję wystarczająco dużego i niezasłoniętego frontu reefer_grille. Poprawka kodu ma statyczny przegląd, lecz nie dostaje tutaj PASS wizualnego.

## Luki dowodowe wymagające uzupełnienia

- **Hatch:**015p9/016p1 oraz037p4/037p6 i042p4/042p6 mają cel zasłonięty budynkiem; crop pokazuje ścianę/okna.127p4/127p6 również nie pokazuje auta.
- **SUV1→2:**042p4/042p6 Low pokazuje ścianę,127p4/127p6 High pokazuje fragment trawnika/budynku. Nie można ocenić poppingu sylwetki ani kolorów tego przejścia.
- **Tractor:**049p9/050p1 Low oraz059p9/060p1 i149p9/150p1 High pokazują zasłaniającą zabudowę/plac zamiast pojazdu. Native selectedLod nie dowodzi widoczności.
- **Trailer High1→2:**149p9/150p1 pokazuje okno budynku zamiast celu. Przy19.9/20.1Low crop obejmuje bardzo wąski fragment boku naczepy; nadaje się do lokalnej odpowiedzi materiału, nie do oceny całej sylwetki.
- Potrzebny wyraźny widok agregatu oraz przynajmniej jedna para widocznego końcowego LOD aut. Zapowiedziane dodatkowe kamery mogą zamknąć te luki.

## Problemy obecne już w baseline

- SUV i ciągnik zmieniają jasność i geometrię felg przy0→1; szczególnie Low016p1 i020p1. Referencja koła ma ciemną zagłębioną miskę i drobny osprzęt, którego jasne uproszczone wielokąty LOD1 nie oddają. To istniejący koszt uproszczenia, nie nowa regresja atlasu.
- Bliskie SUV008p0 ma wyraźnie płaskie powierzchnie i uproszczone koła; fotografia samochodów pokazuje bardziej złożone odbicia i kształt obręczy. Przed/po nie wykazuje pogorszenia od tej zmiany.
- Szklane powierzchnie pojazdów są bardzo ciemne, a auta/plandeki bywają podobne między instancjami. Sam ten pakiet nie potwierdza fotograficznej jakości całego świata; fotografie nie mają zgodnego światła/perspektywy do kalibracji albedo.

## Ograniczenia

Obrazy są statycznymi renderami edytora. Nie oceniam migotania w ruchu, temporalnego poppingu, ASTC na telefonie, FPS ani kosztu GPU na A16. Liczniki SceneStats to estymacja CPU; spadek batchy instancji i brak wzrostu trójkątów nie są pomiarem telefonu. Testy i audyt geometrii wspierają integralność danych, lecz nie zastępują oglądania widocznego celu.
