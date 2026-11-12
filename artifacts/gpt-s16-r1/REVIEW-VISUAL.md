# ADR0153 — niezależna ocena wizualna B

**Werdykt końcowy: PASS w zakresie statycznych porównań edytora przed/po dla optymalizacji ADR0153.** Nie znalazłem nowej widocznej regresji wymagającej poprawki przed akceptacją tego zakresu. To nie jest PASS dla telefonu, dynamicznego przejazdu ani fotograficznej jakości całego świata. Wcześniejsze PARTIAL z powodu zasłoniętych kamer zastępuje niniejsza ocena po obejrzeniu dodatkowych 160 par.

## Obejrzany materiał

- Wszystkie **40 arkuszy overviews**: po 10 dla Low-clear, Low-overcast, High-clear i High-overcast. Obejmują 114 kamer na warunek, łącznie 456 par przed/po.
- Szczegółowe oryginalne target-crops przy przejściach: auta 16 / 42,5 m Low i 37,5 / 127,5 m High; pojazdy placowe 20 / 50 m Low i 60 / 150 m High. Sprawdzono obie pogody, widoki bliskie 8 m oraz pełne pary najwyższego MAE.
- **Wszystkie 160 dodatkowych plików** w `clear/target-crops/{Low-clear,Low-overcast,High-clear,High-overcast}`: 40 kamer na warunek. Crop obejmuje 480 × 340 natywnych pikseli na stronę. To zwykły render świata, nie obraz maski. Nazwa kamery zawierająca High lub Low określa przygotowany dystans; rzeczywisty profil wynika z katalogu warunku.
- Obejrzano lokalne `real-cars-contact.jpg`, `r4-reference-review.jpg` i `wheel-photo-crop.png` oraz ich opisy pochodzenia. Fotografie służą ocenie konstrukcji i ogólnego wyglądu; inne światło, perspektywa i model pojazdu wykluczają kalibrację albedo. Nie kopiowałem referencji do worktree.
- Przeczytano metadane `projection-probe.json`, `glb-audit.json`, `CAMERAS.md`, `image-metrics.json`, dodatkowe `clear/CAMERAS.md` i `clear/camera-counts.json`. Nagłówek `final-editmode.xml` podaje 452 passed, 0 failed, 0 skipped. Nie uruchamiałem Unity, adb, generatora ani testów.

## Ustalenia dotyczące optymalizacji

**Bliski LOD0 i tablice: brak zaobserwowanej regresji.** Oryginalne `lod_car_hatch_white_008p0` we wszystkich czterech warunkach zachowuje tablicę BI3G87 na vanie na pierwszym planie; biały hatch obok zachowuje lakier i reflektory. Dodatkowe `clear_car_hatch_white_Low_015p9/016p1` renderowane High pokazują nadal odrębne, czytelne tablice vana i hatcha. SUV przy 8 m i w bliskich dodatkowych widokach utrzymuje ciemny lakier, okna, lampy i koła. Nie jest to pełny obrazowy test wszystkich numerów tablic na wszystkich instancjach.

**Auta Low 0→1 i 1→2: bez nowego pogorszenia względem baseline.** Dodatkowe `clear_car_hatch_white_Low_015p9/016p1` i `_042p4/042p6` oraz analogiczne SUV pokazują cele, które wcześniej zasłaniał budynek. Kontur i położenie kół są zgodne przed/po. W LOD2 widać uproszczenie nadwozia do bardziej pryzmatycznej bryły i uproszczenie kół, jednak występuje ono po obu stronach porównania. Brak nowych kolorowych plam UV, czarnych prostokątów na lakierze lub utraty całej bryły.

**Auta High: brak nowego artefaktu w natywnym kadrze.** `clear_car_hatch_white_High_037p4/037p6` i `_127p4/127p6` zachowują układ i kolor samochodów w obu pogodach. SUV przy 37,5 m jest dostatecznie widoczny do porównania konturu i kół. SUV przy 127,5 m jest bardzo mały: ocena `clear_car_suv_black_High_127p4/127p6` ogranicza się do braku widocznego artefaktu w natywnym kadrze. Nie deklaruję weryfikacji drobnego koloru ani szczegółowej sylwetki tego SUV-a na podstawie małej projekcji. Audyt zachowania geometrii jest osobnym dowodem technicznym.

**Ciągnik i plandeka: brak dodatkowego poppingu od atlasu.** Widoczne `clear_tractor_blue_Low_019p9/020p1` i `_049p9/050p1` oraz `clear_tractor_blue_High_059p9/060p1` i `_149p9/150p1` utrzymują kontur, osobne koła, zbiornik i kolor kabiny przed/po w obu pogodach. Analogiczne kamery `clear_trailer_curtain_0_*` zachowują plandekę, ramy, podpory i koła. Przy High 149,9/150,1 m naczepa i ciągnik pozostają obecne i nie pojawia się dodatkowy skok wyglądu przy aliasie LOD2.

**Agregat chłodni: wzór kratki zachowany w granicach rozdzielczości.** `clear_trailer_reefer_0_Low_020p1` w Low-clear pokazuje subtelne poziome żaluzje po zmianie, z prawidłowo ciemnym polem w jasnej obudowie. High `clear_trailer_reefer_0_High_060p1` w obu pogodach zachowuje ciemną kratkę oraz obrys agregatu; przy tym dystansie jest ona za mała do oceny każdej listewki. Nie widzę zamiany na jednolitą jasną plamę, fragment tablicy ani plamę innej komórki atlasu. Usunięcie dolnego panelu kontrolnego przy LOD1 występuje również w baseline. Alias przy High 150 m nie zmienia widocznego wyglądu chłodni.

**Najwyższy MAE i widoki ogólne: bez nowego blokera.** Sprawdzono szczegółowo Low-overcast `stretch-05-docks` (MAE 0,269), `lod_trailer_curtain_0_049p9/050p1/059p9/060p1`, `lod_tractor_blue_008p0/019p9/020p1`, `g3a_eye_s0112`, `g3a_ext34_s0338` i hatch przy 127,5 m. Widać małe różnice jasności dolnych ram, podpór i detali naczep. Nie znalazłem nowych dziur, odwróconych powierzchni, wyraźnego znikania geometrii ani dużej degradacji całego kadru. Widoki kabiny, lusterek i dróg zachowują kompozycję oraz bliskie elementy.

## Problemy obecne już w baseline

1. Koła SUV-a i ciągnika wyraźnie zmieniają jasność i szczegółowość przy 0→1. Ciągnik otrzymuje jasne wielokątne felgi i płaski szary zbiornik; plandeka traci część drobnego osprzętu. Widać to przed oraz po, szczególnie przy Low 20 m. Fotografia koła pokazuje ciemną zagłębioną miskę i drobny osprzęt, których uproszczenie nie zachowuje.
2. Bliskie SUV-y mają płaskie powierzchnie, uproszczone koła i ciemne szyby. Referencje aut pokazują bogatsze odbicia i konstrukcję obręczy. Ten pakiet nie ustanawia fotograficznej jakości całego modelu.
3. W dodatkowych renderach Low kamery nazwane `*_High_149p9/150p1` pokazują zniknięcie odległego ciągnika/naczepy przy 150,1 m po obu stronach. To zastane zachowanie tego Low kadru, nie nowa regresja atlasu ani test High 150 m. W rzeczywistych renderach High cele są obecne po obu stronach tego przejścia.
4. Nad odległym światem widoczne są zawieszone prostokątne elementy oraz uproszczona roślinność, np. w dodatkowych High kadrach SUV-a przy 127,5 m. Występują już w baseline, poza zakresem tej optymalizacji.

## Granice akceptacji

Pierwotnych zasłoniętych kamer hatcha, SUV-a i ciągnika nie uznano za dowód widoczności. Ich użyteczne przejścia uzupełniają nowe kamery. Maska GPU posłużyła autorowi do wyboru pozycji; sama nie jest podstawą niniejszego PASS.

PASS dotyczy **braku zaobserwowanego pogorszenia względem baseline w dostarczonych statycznych renderach edytora**. Nie obejmuje migotania w ruchu, temporalnego poppingu, urządzeniowej kompresji ASTC, FPS, temperatur ani kosztu GPU na A16. SceneStats jest estymacją CPU; spadek batchy instancji nie zastępuje pomiaru telefonu. Nie stwierdzono konkretnej nowej regresji wizualnej wymagającej poprawki kodu w ocenionym pakiecie.
