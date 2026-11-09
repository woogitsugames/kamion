# ART BIBLE — TRUCK SIM PL

Wiążące tło: `docs/06` (anti-slop), ADR 0005. Każda sekcja ma właściciela; zmienia ją tylko on (lub lider).

## Ciężarówka (właściciel: `truck-artist`)

### Charakter
- Narzędzie pracy, nie zabawka ani reklama: proporcje i szczegóły wynikają z funkcji (stopnie, uchwyty, lusterka, lampy obrysowe, przewody do naczepy). Każdy element ma powód, żeby tam być.
- Fikcyjna marka z polskim zakorzenieniem (propozycje: TRAKT / BIELIK / NAREW — wybór właściciela, `docs/plan/TRACK-A.md` §5). Zakaz nawiązań do kształtów grilla, świateł i kabin prawdziwych producentów.
- Język formy: **koncepcja B + marka TRAKT** (decyzja właściciela 2026-11-09). Szczegóły w „Zewnętrze (A3/A4)” niżej.

### Skala i wymiary
- 1 unit = 1 m. Wymiary tylko z `art-source/truck/dims.json` (statusy SOURCED/DERIVED/WORKING_VALUE). Każdy render koncepcyjny ma figurę 1,80 m i siatkę 1 m; wymiary bryły są mierzone automatycznie, nie „na oko”.
- Ograniczenia twarde: szerokość nadwozia ≤ 2,55 m (lusterka poza limitem), wysokość ≤ 4,00 m. Najbardziej wysunięty do przodu element to zderzak albo lusterko klasy VI — nie osłona przeciwsłoneczna.

### Materiały (zasady)
- Lakier: kolory przygaszone, średnie jasności (np. stalowy niebieski, butelkowa zieleń, ochra); bez nasyconych „gamingowych” barw i bez metalicznego połysku wszędzie. Coat tylko na lakierze.
- Tworzywa zderzaka/narożników: ciemnoszare, matowe (roughness ≥ 0,55), nie czarne jak smoła.
- Guma opon: albedo ~0,025, roughness ~0,85 — nigdy błyszcząca.
- Chrom: oszczędnie (emblemat, ewentualnie listwa). Felgi: stal lakierowana lub aluminium szczotkowane.
- Wartości PBR finalne: tabela referencyjna albedo/roughness z `docs/06` §3 (gdy powstanie) — koncepcje A2 używają wartości roboczych z `tools/blender/truck/concepts.py` (`CLAY`, `SEMANTIC`, `PAINTS`).

### Standard renderów kontrolnych (A2–A3, Blender)
- Kamery stałe: 3/4 przód (perspektywa, 42 mm, wysokość oczu 1,65 m), bok lewy (ortho), przód (ortho), 3/4 tył (perspektywa), + wariant lakieru 3/4 przód.
- Światło neutralne: jednolite tło studyjne + jedno słońce z miękkim cieniem; AgX bez looków; bez bloomu, winiety, aberracji, DOF.
- Materiał „clay” (szary 0,5) dla oceny bryły; szkło, opony i klosze zachowują funkcjonalne kolory, żeby bryła była czytelna.
- Wyjście: JPEG 1600×900, ≤ ~400 KB; podpis w kadrze (koncepcja, widok, skala).

### Czerwone flagi specyficzne dla ciężarówki
- Koła za małe/za duże względem kabiny (opona 1,08 m przy kabinie 3,95 m — stosunek ~1:3,7).
- Kabina „pudełko od zapałek” bez szczelin drzwi, uchwytów i stopni; stopnie, do których nie da się wejść.
- Lusterka bez ramion albo „wiszące w powietrzu”; brak lusterka przedniego/krawężnikowego.
- Siodło na złej wysokości, brak przewodów do naczepy, pusta rama bez zbiorników.
- Zbyt czyste i symetryczne podwozie w finalnym modelu (A4+): zbiornik paliwa po jednej stronie, akumulatory/SCR po drugiej.

### Zewnętrze (A3/A4) — TRAKT, koncepcja B
- **Bryła**: wysoka kabina sypialna, szyba pochylona 19° i zawinięta na narożniki, przód dolny prawie pionowy (spadek 3 cm na 0,76 m). Narożniki w rzucie R 0,32 m (dół) → 0,34 (podszybie) → 0,40 (góra szyby) → 0,46 m (dach); dach R 0,40 m; lekkie zwężenie ku górze (połowa szerokości 1,245 → 1,20 m); zintegrowany daszek jako 3–4 cm wysunięcie krawędzi dachu nad szybą. Profile w `tools/blender/truck/exterior/body.py` (`CFG`).
- **Podział**: kabina (lakier) siedzi na osłonie na ramie (tworzywo) — linia uchylania 1,225 m; osłona = zderzak + narożniki z nadkolem (R 0,60 m, obrzeże 35 mm) + skrzynki stopni. Nigdy „pudełko nad kołem”.
- **Twarz marki**: grill = litera T (górna belka ±0,84 m, „droga” zwężająca się ku górze: ±0,80 → ±0,50 m), przedłużony w zderzaku do tablicy; listwy poziome z delikatnym opadem na końcach. Reflektory: kliny pod końcami belki, krawędź wewnętrzna równoległa do „drogi”. **Podpis świateł dziennych = pozioma belka + ukośna krawędź drogi** w każdym reflektorze; nie używać kształtów innych producentów (ukośna belka, L, C, sześciokąt, gwiazda, lew, gryf).
- **Marka**: emblemat z `art-source/truck/brand/trakt.svg` (chrom, kreski pasa ruchu ciemne), napis TRAKT ciemnym chromem nad grillem (litery z kresek z SVG, rozstrzelone). Chrom tylko na emblemacie.
- **Malowania**: biel flotowa (albedo liniowe ~0,78, chropowatość bazy 0,32 + lakier bezbarwny 0,03) i ciemna zieleń butelkowa (0,020/0,040/0,034, lekki metalik 0,35). Kolejne malowania: przygaszone, średnio lub bardzo ciemne, bez nasyconych barw.
- **Tworzywa zewnętrzne** albedo ~0,037, chropowatość 0,62, mikroziarno; satynowe (ramiona lusterek, listwy grilla) ~0,03 / 0,36; guma 0,018 / 0,82; rama czarny półpołysk 0,022 / 0,45; aluminium zbiornika szczotkowane 0,30 (anizotropia), felgi 0,17; szyby cienkie z rantem frit.
- **Lusterka**: domyślnie klasyczne (kl. II + IV na ramieniu, V po prawej, VI nad prawym narożnikiem), czasze w kolorze nadwozia; wariant kamer w generatorze. Lusterko kl. VI zawsze.
- **Koła**: aluminium 22.5×9.00, 10 śrub, przód ET +120 mm z kołpakiem; tył bliźniaki tarczami do siebie (głęboka czasza z piastą). Opony bez marki, własny bieżnik (przód zygzak, tył bloki), napisy rozmiar/indeks/M+S/3PMSF.
- **Asymetria podwozia**: lewa — zbiornik paliwa (aluminium, opaski) + AdBlue; prawa — skrzynka oczyszczania spalin z osłoną perforowaną i wylotem w dół + akumulatory. Kładka z blachy ryflowanej, spirale na wieszaku.
- **Budżet**: LOD0 zewnętrza ≤ ~100 tys. trójkątów (High), 6 slotów materiałów; szczegóły ≤ 1 cm (szczeliny, śruby, ryflowanie) docelowo w normalnych (A6).
- **Rendery kontrolne A3/A4**: 3/4 przód (42 mm, oczy 1,65 m), bok i przód (ortho), 3/4 tył prawa strona, zbliżenia (reflektor, nadkole/stopnie, tył kabiny/siodło, koła tylne); dwa oświetlenia — „pochmurno” (pełne GI) i „jak URP” (płaskie otoczenie + słońce, bez odbić rozproszonych); proceduralny plac logistyczny jako tło; JPEG 1600×900 ≤ 400 KB.
- **Czerwone flagi zewnętrza (dodatkowe)**: szerokość > 2,55 m przez dodatki (deflektory, uchwyty — mierzyć!), szkło jako jednostronna powierzchnia refrakcyjna (soczewka/„bańka”), fazowanie na bryłach po cięciu (kolce), kieszenie lamp z lakierem na ściankach, napisy lustrzane w rzucie z przodu.

### Wnętrze kabiny (A5)
- Charakter: miejsce pracy i odpoczynku zawodowego kierowcy — spokojne, ciemne u góry (deska nie odbija się w szybie), cieplejsza szarość niżej, jasna podsufitka. Zadbane, lekko używane; zero „gamingowych” akcentów, podświetleń RGB i błyszczącego plastiku.
- Neutralność marki: wspólna bryła dla A/B/C; od marki zależą tylko znak na piaście i kolor wstawek (`grafit` domyślny, `piasek`, `koniak`, `lupek`).
- Wartości materiałów (albedo liniowe / chropowatość, WORKING_VALUE — brak jeszcze tabeli pomiarowej z `docs/06` §3): góra deski soft-touch 0,042 / ~0,7; dół deski 0,15 / ~0,6; tworzywo ciemne 0,03 / ~0,6; skóra foteli 0,034 / ~0,55 (przetarcia 0,26); wieniec kierownicy 0,03 / ~0,55; podsufitka 0,30 / 0,88; dywanik gumowy 0,04 / ~0,8; metal satynowy 0,5 metal / ~0,35. Połysk tylko na szkle ekranów i lusterkach.
- Detal tam, gdzie patrzy kierowca: ziarno tworzyw (normal), przeszycia i perforacja foteli, symbole na przyciskach, kratki głośników i nawiewów, szczeliny podziału paneli, uszczelki. Drobny detal w teksturze, bryła w siatce; bevel tylko tam, gdzie łapie się światło.
- Zużycie sterowane maskami (atrybut `wear`, AO): lewa boczna poduszka fotela kierowcy, wieniec „na 10 i 14”, dywanik pod piętą i przy drzwiach, listwa progowa, kurz w zagłębieniach. Subtelnie — flota, nie wrak.
- Ekrany: realistyczne treści (prędkość, obroty z zieloną strefą ekonomii, bieg AMT, tempomat/ogranicznik, ciśnienie powietrza w 2 obwodach, paliwo/AdBlue, tachograf), spokojna paleta, bez sci-fi. Tekst fontem z otwartą licencją (Inter, OFL), polskie znaki.
- Rendery kontrolne wnętrza (Blender, A5): kamery `kierowca` (oczy kierowcy, 80° poziomo), `zegary`, `pasazer`, `lezanka`, `kierownica`, `fotel`; światło: pochmurne niebo + nisko stojące słońce (~9°); AgX bez looków, bez bloomu/winiety; JPEG 1600×900 ≤ 400 KB.
- Czerwone flagi wnętrza: kaptur zegarów zasłaniający ekran lub wyglądający jak postawiony telewizor; nawiewy/przyciski „wiszące” na powierzchni; jednolity czarny plastik bez ziarna; fotel jak klocek bez przeszyć i mechanizmu; kierownica bez przycisków i dźwigni; biała/odbijająca deska w szybie; brak tachografu i hamulca postojowego.
