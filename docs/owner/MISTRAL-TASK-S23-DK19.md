# Zlecenie Mistral Vibe (headless, lider s23) — pakiet badawczy trasy DK19 Piastowska–Branickiego (D81)

Pracujesz dla projektu Kamion (realistyczny symulator ciężarówki, Unity 6 URP, Windows; świat z OSM + GUGiK). Jesteś w osobnym git worktree tego repo. Po polsku.

Przeczytaj: CLAUDE.md, docs/11_DECYZJE_WLASCICIELA.md (D63, D81), docs/owner/MAP-DECISIONS-2026-11-16.md (sekcja a), docs/adr/0278-*.md (plan mapy: kafle bialystok-mickiewicza, bialystok-bojary, bialystok-wygoda), docs/adr/0272-*.md i tools/worldgen/qa/ortho_xsec.py + docs/reports/ortho-xsec-0272/ (metoda pomiaru przekrojów z ortofoto), docs/adr/0279-*.md (oznakowanie).

CEL: dane referencyjne dla trasy ciężarówki C ↔ Dojlidy przez DK19: Andersa → Sosabowskiego → Piastowska → pl. Antonowicza → Branickiego → rondo Meyera → Ciołkowskiego → Dywizjonu 303 (ok. 8,3 km), żeby lider mógł zbudować kafle 5–7 „najpierw przejezdne” (D63).

ZAKAZY: zero Google Maps/Street View/Earth (i innych widoków ulic poza Mapillary). Źródła tylko: OpenStreetMap (Overpass/API 0.6, ODbL), GUGiK (WMS ortofoto, NMT, BDOT10k), Mapillary (CC BY-SA, z id i autorem), dokumenty UM Białystok/BIP, Dz.U. Do repo NIE wrzucaj zdjęć (tylko linki/id/metadane), żadnych plików > 5 MB. Bez nazw firm/marek (tylko funkcja obiektu). Każda liczba: zmierzona (narzędzie + dane wejściowe w repo), zacytowana albo ESTIMATED/UNVERIFIED. NIE zmieniaj kodu gry, tools/worldgen ani Data/Regions — tylko nowy katalog research.

ZAKRES:
1. Graf trasy z OSM: lista way id po kolei, klasy dróg, liczba pasów, `maxspeed`, `hgv`/`maxweight`/zakazy, rondo Meyera (zakaz prosto w Nowowarszawską 3,5 t, wymuszony skręt w Ciołkowskiego) — `research/mistral-dk19-s23/route.json`.
2. Przekroje z ortofoto GUGiK co 200–300 m: jezdnie, pasy, pas dzielący, chodniki, ścieżki rowerowe, zatoki autobusowe — metodą ortho_xsec (jeśli narzędzie nie zadziała bez Data/raw, opisz i zmierz WMS-em ręcznie skryptem w katalogu research) — `research/mistral-dk19-s23/xsec/`.
3. Skrzyżowania i ronda na trasie: typ, sygnalizacja, liczba pasów na wlotach, promienie (ESTIMATED z ortofoto), czy zestaw 16,5 m skręci bez wjazdu na krawężnik (jakościowo) — `junctions.json`.
4. Oznakowanie ważne dla ciężarówki (B-5, B-18, B-19, B-20, B-33, D-42/D-43, strefy tonażowe, zakazy skrętu) z OSM `traffic_sign` + Mapillary (detekcje) — `signs.json`.
5. Raport `research/mistral-dk19-s23/RAPORT.md` (≤ 40 linii): co zrobione, liczby, czego nie ustalono, ryzyka, lista UNVERIFIED do potwierdzenia przez właściciela (np. zdjęcia znaków na Piastowskiej).

GIT: commituj po każdym punkcie (krótkie komunikaty po polsku, stopka „Co-Authored-By: Mistral Vibe”), na końcu `git push -u origin HEAD` z bieżącej gałęzi. Nie twórz PR, nie scalaj, nie zmieniaj main.
