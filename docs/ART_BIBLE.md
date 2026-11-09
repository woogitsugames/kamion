# ART BIBLE — TRUCK SIM PL

Wiążące tło: `docs/06` (anti-slop), ADR 0005. Każda sekcja ma właściciela; zmienia ją tylko on (lub lider).

## Ciężarówka (właściciel: `truck-artist`)

### Charakter
- Narzędzie pracy, nie zabawka ani reklama: proporcje i szczegóły wynikają z funkcji (stopnie, uchwyty, lusterka, lampy obrysowe, przewody do naczepy). Każdy element ma powód, żeby tam być.
- Fikcyjna marka z polskim zakorzenieniem (propozycje: TRAKT / BIELIK / NAREW — wybór właściciela, `docs/plan/TRACK-A.md` §5). Zakaz nawiązań do kształtów grilla, świateł i kabin prawdziwych producentów.
- Język formy wybierany w A2 (koncepcje A/B/C). Po wyborze dopisz tu: dominujące linie, promienie zaokrągleń (w metrach), kąt szyby, motyw świateł.

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

### Wnętrze kabiny (A5)
- Charakter: miejsce pracy i odpoczynku zawodowego kierowcy — spokojne, ciemne u góry (deska nie odbija się w szybie), cieplejsza szarość niżej, jasna podsufitka. Zadbane, lekko używane; zero „gamingowych” akcentów, podświetleń RGB i błyszczącego plastiku.
- Neutralność marki: wspólna bryła dla A/B/C; od marki zależą tylko znak na piaście i kolor wstawek (`grafit` domyślny, `piasek`, `koniak`, `lupek`).
- Wartości materiałów (albedo liniowe / chropowatość, WORKING_VALUE — brak jeszcze tabeli pomiarowej z `docs/06` §3): góra deski soft-touch 0,042 / ~0,7; dół deski 0,15 / ~0,6; tworzywo ciemne 0,03 / ~0,6; skóra foteli 0,034 / ~0,55 (przetarcia 0,26); wieniec kierownicy 0,03 / ~0,55; podsufitka 0,30 / 0,88; dywanik gumowy 0,04 / ~0,8; metal satynowy 0,5 metal / ~0,35. Połysk tylko na szkle ekranów i lusterkach.
- Detal tam, gdzie patrzy kierowca: ziarno tworzyw (normal), przeszycia i perforacja foteli, symbole na przyciskach, kratki głośników i nawiewów, szczeliny podziału paneli, uszczelki. Drobny detal w teksturze, bryła w siatce; bevel tylko tam, gdzie łapie się światło.
- Zużycie sterowane maskami (atrybut `wear`, AO): lewa boczna poduszka fotela kierowcy, wieniec „na 10 i 14”, dywanik pod piętą i przy drzwiach, listwa progowa, kurz w zagłębieniach. Subtelnie — flota, nie wrak.
- Ekrany: realistyczne treści (prędkość, obroty z zieloną strefą ekonomii, bieg AMT, tempomat/ogranicznik, ciśnienie powietrza w 2 obwodach, paliwo/AdBlue, tachograf), spokojna paleta, bez sci-fi. Tekst fontem z otwartą licencją (Inter, OFL), polskie znaki.
- Rendery kontrolne wnętrza (Blender, A5): kamery `kierowca` (oczy kierowcy, 80° poziomo), `zegary`, `pasazer`, `lezanka`, `kierownica`, `fotel`; światło: pochmurne niebo + nisko stojące słońce (~9°); AgX bez looków, bez bloomu/winiety; JPEG 1600×900 ≤ 400 KB.
- Czerwone flagi wnętrza: kaptur zegarów zasłaniający ekran lub wyglądający jak postawiony telewizor; nawiewy/przyciski „wiszące” na powierzchni; jednolity czarny plastik bez ziarna; fotel jak klocek bez przeszyć i mechanizmu; kierownica bez przycisków i dźwigni; biała/odbijająca deska w szybie; brak tachografu i hamulca postojowego.
