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
