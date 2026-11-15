# Przetargi LED Miasta Białystok w TED — źródło decyzji o głowicach LED (ADR 0216b)

`ted_notices.json` — 19 ogłoszeń TED (Tenders Electronic Daily, Urząd Publikacji UE) Miasta Białystok o „dostawie i
montażu energooszczędnych opraw ledowych”, 2024-02-05 … 2026-10-29: publiczne API TED Search v3
(`POST https://api.ted.europa.eu/v3/notices/search`, zapytanie `FT~"opraw" AND buyer-city="Białystok" AND
publication-date>=20220101`), pobrane 2026-11-15. Pominięto nazwy wykonawców i produktów oraz ogłoszenie o naprawie
tunelu (nazwy produktów). `cn-standard` = ogłoszenie o zamówieniu, `can-standard` = ogłoszenie o udzieleniu zamówienia
(umowa zawarta). Ogłoszenia z 2023 (Andersa, al. 1000-lecia, Maczka: TED 658997-2023, platforma e-zamówień 93688)
są w `research/night-lamps-s21` (K69 §4) i tu się nie powtarzają.

Co z tego wynika dla regionów gry (`tools/worldgen/qa/lamp_family_audit.py`, rachunek reguły generatora na danych w
repo):

| region | ulice ze starymi słupami (głowica sodowa) w grze | w ogłoszeniu o udzieleniu zamówienia | decyzja |
|---|---|---|---|
| `bialystok-dojlidy` | Myśliwska, Sępia, Kormoranów, Adama Mickiewicza, Franciszka Karpińskiego, Spadochroniarzy | TED 769998-2024 (2024-12-17), poz. 14, 15, 16, 18, 19, 24 | głowica LED (override `lamp-policy-led-tender-0216b`) |
| `bialystok-dojlidy` | Borsucza, Grabowa, Jaskółcza, Krecia, Królicza, Praw Kobiet, Szpacza, Wiewiórcza, Zajęcza, Żurawia, ulice bez nazwy | brak w żadnym ogłoszeniu | bez zmian (sód), UNVERIFIED |
| `bialystok-industrial-c` | Michała Motoszko, Skidelska, Buska, Sokólska, Łańcucka, Olsztyńska, Świsłocka, Władysława Bełzy, Białostoczek, Grodzieńska, Kombatantów, ulice bez nazwy | brak w żadnym ogłoszeniu (Andersa, Maczka, al. 1000-lecia są w przetargu 2023, ale mają słupy LED reguły, nie stare) | bez zmian (sód), UNVERIFIED |

Ograniczenia: ogłoszenie podaje ulicę, nie odcinek (Mickiewicza jest też w zamówieniu III, TED 32657-2025 — odcinek
w Dojlidach z dokumentu nie wynika) ani daty montażu; stan w terenie w 2026 jest UNVERIFIED (brak nocnych zdjęć po
wymianie, K69 §7 p. 1). OSM nie pomaga: w obu kaflach 0 węzłów z `light:method` / `lamp_type` innym niż `electric`
(`research/night-lamps-s21/osm-street-lamps.json`, 11 latarń w C, 0 w Dojlidach).
