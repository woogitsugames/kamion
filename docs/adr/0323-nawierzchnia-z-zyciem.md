# ADR 0323 — Nawierzchnia z życiem: kostka Tykocina, łaty, zalewki, spękania, koleiny ronda, bariery

Status: propozycja (gałąź `road-surface-s24`, nie scalone). Źródło: krytyk fala 6
(`artifacts/critic-s24-wave6/CRITIC.md`, top-5 pkt 1; wiersze 2.1, 2.2, 2.3, 2.4, 2.8).

## Kontekst

1. **Tykocin (2.1).** `road_sett` i `apron_sett` nie miały `texture_set`, więc importer brał stary shader
   „Kamion/World Surface” z proceduralną teksturą Voronoja „Sett” na kaflu 1,6 m: beżowo-różowe komórki 0,3–0,6 m.
   OSM w kaflu `tykocin`: `surface=sett` 2,4 km (Złota, Sokołowska, Puchalskiego, pl. Czarnieckiego; BDOT10k „kostka
   kamienna”), `cobblestone` / `unhewn_cobblestone` 3,5 km (BDOT10k „bruk”). Ulice są więc naprawdę kamienne — błędny
   był materiał i skala, nie rodzaj nawierzchni. Zdjęcia Commons `cs153250600`, `cs202183436` (K. Popławski, CC BY
   4.0): szara kostka granitowa ok. 8–10 cm układana w wachlarze.
2. **Asfalt (2.2).** Warstwa spękań 16 m miała fizyczne rozwarcie 1–5 mm, czyli poniżej jednego teksela na każdym
   tierze (High 7,8 mm, Medium 15,6 mm) — z kabiny nie było widać nic. Łaty po ADR 0322: prostokąty z postrzępioną
   krawędzią, mało i równomiernie. Zalewek poza teksturą nie było. Zdjęcia Commons DW671 (`cs11749508` Tatary,
   `cs7403215`): długie ciemne pasy napraw wzdłuż śladów kół, wykruszona krawędź, miejscami brak malowania.
3. **Koleiny ronda (2.3).** Płyta ronda kompaktowego (Knyszyn DK65 × DW671) niosła w UV1 współrzędną pasa liczoną od
   prostych osi ramion, interpolowaną na trójkątach 2,5 m: równoległe pasy przecinały łuk wlotu i biegły pod wysepką.
4. **Bariery (2.4, 2.8).** `barrier_steel` 0,50 / metal 0,9 / szorstkość zestawu 0,56 — zakrzywiona prowadnica
   odbijała sondę nieba jasnymi smugami (chrom), także przy zachmurzeniu.

## Decyzja

1. **Kostka.** Dwa zestawy ze skanów CC0 Poly Haven (ADR 0063, D40): `sett_granite` (`cobblestone_03`, podziałka
   mierzona autokorelacją i skalowana do 95 mm — kostka 8/10 ze spoiną; `road_sett`, `apron_sett`) oraz
   `cobble_fieldstone` (`cobblestone_floor_08`, rozmiar fizyczny skanu 2,0 m; nowy materiał `road_cobble` dla
   `cobblestone` / `unhewn_cobblestone`). Oba segmentowane na elementy (`elements_per_tile`), więc importer nadaje im
   prawdziwy kafel. Układ wachlarzowy NIE jest odtworzony (rzędy). Wartości WORKING_VALUE.
2. **Zalewki i spękania jako geometria** (`roads/decals.py: seal_cracks`): miękkie pasy istniejącego materiału
   `decal_tyre` (bez nowego shadera): spękania poprzeczne (cała jezdnia / połowa / zanikające), podłużne (szew osi,
   0,3–0,7 m od krawędzi, ślad koła), 70 % zalane (7–12 cm geometrii, ok. 60 % ciemne), reszta włosowate. Meandrują
   (trzy sinusy 1,2–9 m + szum). Gęstość × klasa drogi × **stan odcinka** (`condition`: co 250 m dobry 0,25 /
   przeciętny 1,0 / zły 2,4; udziały 30/45/25 %). Ten sam mnożnik stanu dostały łaty. Bez mostów, rond, nowego
   asfaltu, kostki, betonu. Wszystkie stawki WORKING_VALUE (brak danych SOSN/DSN w repo).
3. **Łaty** (`WorldPBR _DECAL_PATCH`): dwa rodzaje z ziarna łaty — plama remontera (55 %: obrys stadionu zjedzony
   szumem 0,3–0,9 m do 0,4 × rozmiar, miękka krawędź) i łata cięta piłą (45 %: prawie proste cięcia + ręcznie lana
   zalewka 30–90 mm, z przerwami); 40 % plam też ma zalewkę. Ton świeżej 0,60, starej 0,82, rozrzut ±10 % na łatę.
   30 % łat w śladzie koła to długie pasy 8–25 m.
4. **Warstwa spękań**: szerokości pozorne (rozwarcie + wykruszone, zabrudzone krawędzie): 8–16 mm długie, 5–9 mm
   odgałęzienia, 6–10 mm siatka; strefy siatkowe częstsze; aureola mocniejsza (0,12 → 0,22). W `_ROADWEAR`:
   **zniszczenie krawędzi** — zewnętrzne 0,6–1,8 m jezdni (UV1.y) dostaje pełną siłę spękań w odcinkach 5–20 m
   (szum w przestrzeni obiektu), +7 % jasności (wypłukane lepiszcze).
5. **Wytarte linie** (`_DECAL_PAINT`): linie podłużne mają odcinki 3–12 m wytarte do asfaltu (szum w przestrzeni
   obiektu; brak danych o przejazdach przez linię). Świeża farba na nowym asfalcie bez zmian.
6. **Koleiny ronda kompaktowego**: płyta nie ma kolein z shadera (UV1.x całkowite); ślady kół to pasy `decal_tyre`
   wzdłuż toru jazdy: pas ramienia → projektowany pas wlotu/wylotu (`lay_lanes`) → oś pierścienia, plus jeden tor
   dookoła pierścienia; dwa pasy na tor, ±0,84 m. Kończą się na wjeździe na pierścień; pod wysepkami nie ma nic
   (pasy są drapowane tylko na jezdni).
7. **Bariery**: albedo 0,42, `set_metal` 0,55, nowy klucz manifestu `set_smooth` 0,6 (RegionImporter →
   `_SmoothnessScale`; szorstkość ok. 0,74). Odstępstwo od sugestii krytyka (metal 1, szorstkość 0,45–0,6): te
   wartości już obowiązywały i dawały chrom; stary ocynk ma patynę rozpraszającą dyfuzyjnie.

## Konsekwencje

- Reimport wszystkich regionów (shader, materiały) i przebudowa regionów dla nowych decali / materiałów; dowód tylko
  dla `tykocin`, `dw671-tykocin-01`, `knyszyn`.
- `apron_sett` (fartuchy rond w Białymstoku) dostaje zestaw `sett_granite` — zmiana wyglądu poza kaflami dowodu,
  nieoglądana.
- Zwykłe (niekompaktowe) ronda i wysepki dzielące na wstęgach nadal mają koleiny z UV1 osi — nie ruszane.
- Koszt: patrz „Wyniki”.

## Wyniki

(uzupełniane po renderach)
