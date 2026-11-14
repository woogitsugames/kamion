# BRAND-SWEEP-S20 — przegląd marek i logo (CLAUDE.md zasada 8)

Agent X2, sesja 20, gałąź `docs/brand-sweep-s20` od `f2d50b6a9`. Bez Unity, telefonów i `Data/raw` — tylko pliki w gicie.
Status: **SZKIC — inwentaryzacja** (tabela ustaleń w następnym commicie).

## Metoda (do powtórzenia)

Zakres: wszystkie śledzone pliki tekstowe (`git grep -I`) **poza** `research/**`, `artifacts/**` (treść — tylko nazwy plików,
§ „Nazwy plików”), `HANDOVER.md` oraz plikami lokalnego agenta 0201: `game/**/Vehicle/**/*.json`,
`tools/physics-runner/Tests/**`, `DrivingLabSceneBuilder.cs`, `ContactShadowCaster.cs`.

```bash
EXCL=(':!research/**' ':!game/**/Vehicle/**/*.json' ':!tools/physics-runner/Tests/**' ':!**/DrivingLabSceneBuilder.cs' \
      ':!**/ContactShadowCaster.cs' ':!artifacts/**' ':!HANDOVER.md')
# liczniki: case-sensitive i -i dla każdego wzorca z listy niżej
git grep -I -P -c  "<wzorzec>" -- . "${EXCL[@]}"
git grep -I -P -ci "<wzorzec>" -- . "${EXCL[@]}"
# trafienia z linią
git grep -I -P -n "<wzorzec>" -- . "${EXCL[@]}"
# nazwy plików z marką (w tym artifacts/)
git ls-files | grep -v '^research/' | grep -i -P 'scania|volvo|daf|mercedes|iveco|renault|krone|wielton|schmitz|kogel|man_|orlen|shell|circle|biedronka|lidl|mcdonald|bp_|moya|bison|rosti|adblue|bridgestone|michelin|zf_|traxon'
```

Lista wzorców (PCRE, case-sensitive; `-i` tylko jako licznik pomocniczy):

- Producenci pojazdów i części: `Scania` `Volvo` `\bMAN\b` `\bDAF\b` `Mercedes` `\bBenz\b` `Actros` `Iveco` `Renault`
  `K(ö|oe)gel` `\bKrone\b` `Schmitz` `Wielton` `Michelin` `Bridgestone` `Continental` `Goodyear` `Allison` `\bZF\b`
  `Eaton` `Voith` `Knorr` `WABCO` `\bBosch\b` `Cummins` `Jacobs` `Jake ?brake` `Webasto` `Garmin` `Kenworth` `Peterbilt`
  `Freightliner` `\bMack\b` `Tatra` `\bJelcz\b` `Solaris` `Autosan`; nazwy handlowe: `AdBlue` `TraXon` `I-Shift`
  `Intarder` `Opticruise` `PowerShift` `Tautliner` `Cargobull`; modele: `Golf|Passat|Octavia|…|Actros|TGX|XF|CF|FH|FM`.
- Stacje: `Orlen` `Lotos` `\bBP\b` `\bShell\b` `Circle ?K` `Statoil` `\bMoya\b` `\bAmic\b`.
- Handel i usługi: `Biedronka` `\bLidl\b` `Kaufland` `Auchan` `Carrefour` `(Ż|Z)abka` `\bNetto\b` `\bDino\b` `Stokrotka`
  `Leroy` `Castorama` `\bOBI\b` `Media ?Markt` `RTV ?Euro` `Rossmann` `\bHebe\b` `Pepco` `McDonald` `\bKFC\b`
  `Burger King` `InPost` `Paczkomat` `\bDPD\b` `\bDHL\b` `Poczta Polska`.
- Firmy lokalne / z OSM regionów: `Pronar` `Samasz` `Agrobud` `(Ż|Z)ubr` `Kompania Piwowarska` `Dojlidy` `Polmos`
  `Biaglass` `Fasty` `Biazet` `Enea` `PGE` `BKM` `PUHP` `Społem` `Rosti` `Bison|BISON` `Masterpress` `Bravilor` `Biawar`
  `Bieldruk` `Cefarm` `Arsenal` `Kwadrat` `Browar` `Redkom` `Mitex|MITEX` `Bocaro` `TEDi` `Sinsay` `KiK` `Giełda Rolna` `KAN`.
- Banki, telekomy, auta osobowe, inne: `\bOrange\b` `T-Mobile` `Polsat` `\bPKP\b` `\bPKO\b` `Pekao` `Santander` `mBank`
  `Toyota` `Volkswagen` `\bVW\b` `Skoda|Škoda` `\bOpel\b` `\bFord\b` `\bFiat\b` `Peugeot` `Citro(ë|e)n` `\bAudi\b`
  `\bBMW\b` `Hyundai` `\bKia\b` `Dacia` `Nissan` `\bHonda\b` `Samsung` `Galaxy` `Snapdragon` `Unity` `RMF` `Radio ?ZET`.
- Tagi OSM i logo: `brand:wikidata` `\bbrand\b` `\boperator\b` `logo` `emblem` `herb` `godło` `Straż|STRAŻ` `PSP`.

Dodatkowo (poza grep): skrypt Pythona (`python -I`, tylko odczyt) wypisał wszystkie wartości kluczy `name`, `brand`,
`operator`, `shop`, `amenity`, `destination`, `destination:lanes` ze śledzonych `*.json`/`*.geojson` w `Data/`,
`art-source/`, `game/`, `tools/`, `docs/reports/{world-validator,map}`, osobno atrybuty krawędzi `roads.graph.json`
(`name`, `ref`, `destination`) i `strings` z wysyłanych plików nawigacji
`game/Assets/_Project/UI/Resources/CabDisplay/Nav/*.bytes`. Ścieżkę „czy napis trafia na ekran” śledziłem w kodzie
(konsumenci `buildings.geojson`, `streetscape_sources.json`, `roads.graph.json`; generatory tekstur z `ImageDraw.text`,
`render_text_texture`, `TextMesh`, `UnityEngine.UI.Text`, `CabDisplayText`).

## Inwentaryzacja (liczba linii, case-sensitive / `-i`; tylko wzorce z ≥ 1 trafieniem)

| wzorzec | CS | -i | uwaga |
|---|---:|---:|---|
| Scania | 25 | 25 | docs (referencje zdjęć, recenzje) |
| Volvo | 61 | 63 | docs (źródło S1, referencje, recenzje, decyzje D30/D34) |
| `\bMAN\b` | 8 | 168 | CS: 3 to zmienna `MAN` (manifest) w kodzie; -i: słowo „man” |
| `\bDAF\b` | 11 | 11 | docs |
| Mercedes / Benz / Actros | 4 / 3 / 1 | | docs |
| Iveco | 2 | 119 | -i: fałszywe (podciąg) |
| Renault | 3 | 3 | docs |
| Krone | 4 | 4 | docs, ADR 0122 |
| Wielton | 7 | 9 | docs |
| Bridgestone | 5 | 5 | docs (źródło S7) |
| `\bZF\b` | 23 | 273 | CS: docs + zmienna `ZF` w `build_interior.py`; -i: „zf” w innych słowach |
| Voith / Bosch | 1 / 3 | | docs (źródła literaturowe) |
| Peterbilt / Freightliner / Mack / Jelcz / Solaris | 2 / 2 / 3 / 2 / 1 | | docs |
| Orlen | 4 | 4 | docs (recenzje M52) |
| `\bBP\b` | 8 | 59 | `fidelity_qa.json`, `streetscape_sources.json`, docs |
| `\bShell\b` | 8 | 244 | 2 × docs-recenzje; reszta „shell” (powłoka) |
| Circle K | 10 | 10 | `buildings.geojson`, `streetscape_sources.json`, raporty |
| Moya | 3 | 3 | `buildings.geojson`, raport walidatora |
| Biedronka | 6 | 6 | `buildings.geojson`, recenzje |
| Netto | 4 | 19 | wszystkie: słowo „netto” |
| Pepco | 1 | 1 | `docs/REFERENCES.md` |
| McDonald | 2 | 2 | `buildings.geojson` |
| DPD / Poczta Polska / Pronar | 2 / 4 / 1 | | recenzje |
| Dojlidy | 87 | 481 | głównie nazwa dzielnicy/regionu (fałszywe); „Browar Dojlidy” osobno |
| Fasty | 4 | 4 | nazwa osiedla (fałszywe) |
| Orange | 4 | 57 | „orange peel”, kolor (fałszywe) |
| PKP | 2 | 2 | recenzje |
| Toyota / Ford | 2 / 1 | | recenzja ZIP-ów |
| `\bVW\b` | 11 | 39 | zmienna `VW` w `meshing.py` (fałszywe) |
| Samsung | 60 | 61 | docs/skrypty (telefony testowe) |
| `\bbrand\b` | 79 | 79 | komentarze „no brand”, własna marka TRAKT |
| `\boperator\b` | 43 | 43 | C# `operator`, tag OSM w `streetscape_sources.json` |
| AdBlue | — | 48 | kod UI kabiny, generatory Blendera, docs |

Zero trafień: Kögel, Schmitz, Michelin, Goodyear, Allison, Knorr, WABCO, Cummins, Jacobs, Webasto, Garmin, Kenworth, Tatra,
Autosan, Lotos, Statoil, Amic, Lidl, Kaufland, Auchan, Carrefour, Żabka, Dino, Stokrotka, Leroy Merlin, Castorama, OBI,
Media Markt, RTV Euro AGD, Rossmann, Hebe, KFC, Burger King, Paczkomat, DHL, Samasz, Agrobud, Żubr, Kompania Piwowarska,
Polmos, Biaglass, T-Mobile, Polsat, PKO, Pekao, Santander, mBank (CS), Volkswagen, Opel, Fiat, Peugeot, Citroën, Audi, BMW,
Hyundai, Kia, Dacia, Nissan, Honda, `brand:wikidata`.
