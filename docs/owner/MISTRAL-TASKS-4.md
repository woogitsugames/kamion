# Zadania dla Mistral Vibe Code — runda 4 (s15, 2026-11-12)

Repo: `woogitsugames/kamion`. **5 sesji, każda dostaje jeden blok poniżej (skopiuj całość).** Środowisko jak w rundach 2–3: GitHub, bez Unity, telefonów i `Data/raw`, LFS widoczne tylko jako wskaźniki. Zadania wynikają z recenzji rundy 3 (`docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md`) i z ADR 0150 (mapa/GPS).

**Wspólne zasady (są w każdym prompcie):** gałąź `mistral/<nr>-<nazwa>` od `main`, na końcu PR do `main` (nie draft), raport po polsku w opisie PR. Nie pushujesz na `main` i nie scalasz. Nie zmieniasz `Data/**/generated/**`, `*.glb`, `*_meta.json`, `game/ProjectSettings/**`, `game/Packages/**`, `.gitattributes`, LFS. Nie zmyślasz: liczba zmierzona, zacytowana (z paragrafem/stroną) albo `UNVERIFIED`. Źródła wtórne (blogi, kalkulatory, serwisy ubezpieczeniowe) nie potwierdzają przepisów. Zakaz Google Maps, Street View, Earth, 3D Tiles. Na koniec napisz w sesji „M<nr> gotowe” z numerem PR.

---

## M21 — GPS: ograniczenia dla ciężarówek w grafie tras

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/21-nav-truck-limits od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku w opisie PR. Nie zmyślaj.

Kontekst: ADR 0150 (docs/adr/0150-map-minimap-gps.md) — generator tools/worldgen/navgraph/build_route_graph.py zamienia graf dróg regionu na plik gry game/Assets/_Project/UI/Resources/CabDisplay/Nav/<region>_route.bytes; routing A* w C# w game/Assets/_Project/Core/Navigation/. Otwarte: „limity masy/wysokości ciężarówki w routingu”. Nasz pojazd: zestaw ~40 t (D53), wysokość i długość — z danych pojazdu w repo (game/Assets/_Project/Vehicle/Physics/Definitions/Data/*.json, docs/VEHICLE_REFERENCE_DATA.md); jeśli brak — WORKING_VALUE z uzasadnieniem.
Zadanie: (1) sprawdź, jakie tagi OSM ograniczeń są dostępne w krawędziach grafu regionu (maxweight, maxweight:hgv, maxaxleload, maxheight, maxlength, hgv=destination/no, hgv:conditional) — czytaj tylko z plików już w repo (graf regionu w Data/Regions/**; nie modyfikuj ich); policz, ile krawędzi ma każdy tag. (2) Rozszerz format pliku trasy o te limity (wersja formatu +1, zgodność wstecz w parserze Python i w czytniku C#), w generatorze; wartości z jednostkami OSM znormalizuj (t, m) z testami parsowania („3.5”, „3.5 t”, „12'6\"”, „none”, „default”). (3) W C# routingu: krawędź z limitem poniżej parametrów pojazdu = niedozwolona (z wyjątkiem hgv=destination dla celu na tej krawędzi). (4) Testy: pytest dla generatora (parsowanie, zgodność pliku z regeneracją jak w istniejącym teście), testy EditMode NUnit dla routingu w game/Assets/_Project/Tests/EditMode/ (wzoruj się na NavRoutingTests) — nie uruchomisz Unity, więc napisz je starannie; lider uruchomi. (5) Raport: liczby tagów, decyzje, co UNVERIFIED. NIE regeneruj pliku .bytes w repo (lider zrobi to w integracji) — chyba że istniejący test wymaga zgodności; wtedy opisz.
```

## M22 — GPS: wskazówki pasów ruchu z `turn:lanes`

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/22-nav-lanes od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku w opisie PR. Nie zmyślaj.

Kontekst: ADR 0150 (mapa/GPS). Generator tools/worldgen/navgraph/build_route_graph.py; 174 krawędzie grafu mają tagi turn:lanes (wg ADR). Baner manewru w HUD pokazuje strzałkę, odległość i ulicę; brakuje pasów.
Zadanie: (1) w generatorze dodaj dane pasów dla krawędzi z turn:lanes / turn:lanes:forward / :backward (kierunek krawędzi!), lanes, lanes:forward/backward — format pliku wersja +1, zgodność wstecz (parser Python + czytnik C#). Parsowanie wartości OSM wg wiki OSM Key:turn (left, slight_left, through, slight_right, right, merge_to_left/right, reverse, none, puste, wielokrotne „left;through”) z testami pytest. (2) W C#: dla następnego manewru wyznacz, które pasy prowadzą w wybranym kierunku (dopasowanie kierunku skrętu do wartości pasa), i wystaw to w stanie nawigacji (np. tablica bitów pasów dozwolonych/zalecanych) — bez alokacji GC w pętli jazdy (prealokowane bufory). (3) Rysowanie: dodaj pod banerem manewru prosty pasek pasów (strzałki per pas, zalecane jaśniej) w istniejącym komponencie HUD nawigacji — w stylu obecnego HUD (patrz zrzuty artifacts/gps-map/ jeśli są w repo, docs/06 anti-slop: wygląd jak prawdziwa nawigacja ciężarowa, bez marek). (4) Testy pytest + EditMode NUnit (wzoruj się na NavRoutingTests/NavHudTests; lider uruchomi Unity). Nie regeneruj .bytes w repo (lider). Raport: ile krawędzi ma pasy, przykłady 3 skrzyżowań z mapy (nazwa ulic) z wynikiem dopasowania.
```

## M23 — HUD bez alokacji, wersja bez TextMeshPro (ponowienie M20)

```
Repo woogitsugames/kamion (Unity 6 C#). Pracuj na gałęzi mistral/23-hud-zero-alloc-text od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS, plików .asmdef. Raport po polsku w opisie PR. Nie zmyślaj liczb.

Kontekst: PR #19 (M20) odrzucony: użył TextMeshPro, a projekt nie ma TMP Essential Resources (UiFonts.DefaultTmp → NullReferenceException, HUD się nie buduje), zmienił asmdef i wygląd tekstu. Recenzja: docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md (pkt 5 „osobne zadania”). Decyzja lidera: wariant (b) — zostajemy przy UnityEngine.UI.Text.
Zadanie: w game/Assets/_Project/** (bez Editor/) usuń alokacje GC z aktualizacji etykiet HUD/overlay w czasie jazdy, BEZ TextMeshPro i bez zmian asmdef: (1) aktualizuj Text.text tylko gdy zmienia się wyświetlana (zaokrąglona) wartość; (2) dla wartości o skończonym zbiorze (prędkość 0–150 km/h, bieg, obroty co 10/50, gyro ±90,0° co 0,1, ciśnienia co 0,1 bar itd.) użyj tablic gotowych stringów budowanych raz przy starcie (bez boxingu, bez string.Format/interpolacji w pętli); (3) z PR #19 wolno wziąć bez TMP: tabelę stringów obrotów, etykiety przycisków diagnostyki tylko przy zmianie, helpery TextBuffer, test HudTextAllocTests (gałąź mistral/20-hud-zero-alloc, commit 9608e6a94 i okolice) — dostosuj do Text. Wygląd tekstu identyczny jak na main (ten sam font, rozmiar, format liczb, np. „12.5 bar”). (4) Test PlayMode liczący wywołania GC.Alloc (Recorder / ProfilerRecorder „GC.Alloc”, nie GetAllocatedBytesForCurrentThread — w edytorze zwraca 0) dla 500 aktualizacji ze zmiennymi wartościami: 0 alokacji w nowej ścieżce. Nie uruchomisz Unity — pisz starannie, kompiluj w głowie (using, przestrzenie nazw jak w istniejącym kodzie); lider uruchomi kompilację, testy i pomiar.
```

## M24 — znaki pionowe: wymiary wg tabeli 5.1 + duplikat `concrete_pole`

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/24-signs-sizes od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku w opisie PR. Nie zmyślaj.

Kontekst: recenzja rundy 3 (docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md, pkt 2) i raport M9 (docs/reports/AUDIT-SIGNS*… z PR #15): w generatorze znaków SIGN_SIZE["square"] i ["diamond"] = 0,80 m, a tabela 5.1 załącznika nr 1 rozporządzenia (Dz.U. 2019 poz. 2311) podaje 0,60 m dla wielkości średniej; ośmiokąt B-20 = 0,80 m mierzone między bokami vs narożnikami (0,80/cos(π/8)); klasa folii typ 2 dla A-7/B-2/B-20/D-6; U-4a i tabliczki T do weryfikacji (zał. 4 / rozdz. 9). Osobno: duplikat klucza concrete_pole w tools/worldgen/streetscape/materials.py (l. ~108 [0.36,0.36,0.34] i ~163 [0.33,0.33,0.31]) — działa późniejszy.
Zadanie: (1) zweryfikuj w źródle pierwotnym (isap.sejm.gov.pl, PDF Dz.U. 2019 poz. 2311 — podaj stronę PDF i numer tabeli/rysunku) każdy wymiar, który zmieniasz, i dla jakiej grupy wielkości (mała/średnia/duża) oraz jakiej klasy drogi (nasze drogi: DK8 ekspresowa/ruch szybki, ulice miejskie — ustal z danych regionu w repo, które klasy wielkości obowiązują, cytując przepis); (2) popraw stałe w generatorze znaków (znajdź gdzie: grep SIGN_SIZE w tools/worldgen) z komentarzem-źródłem; (3) concrete_pole: usuń wcześniejszy duplikat, zostaw działającą wartość (bez zmiany wyglądu), dodaj test pytest, że w słowniku nie ma zduplikowanych kluczy (np. przez ast); (4) testy pytest dla wymiarów (zdejmij xfail, jeśli M9 dodał je dla tych pozycji). NIE regeneruj świata (lider). Raport: tabela przed/po z cytatem i stroną.
```

## M25 — oznakowanie poziome: P-11 i zmiany załącznika nr 2 po 2019

```
Repo woogitsugames/kamion. Pracuj na gałęzi mistral/25-markings-p11 od main, na końcu PR do main (nie draft). NIE pushuj na main, NIE scalaj. Nie zmieniaj Data/**/generated/**, *.glb, *_meta.json, game/ProjectSettings/**, game/Packages/**, .gitattributes, LFS. Raport po polsku w opisie PR. Nie zmyślaj.

Kontekst: recenzja rundy 3 (docs/reports/REVIEW-2026-11-12-s15-mistral-r3.md, pkt 3) i raport M18 (PR #20, docs/reports/AUDIT-MARKINGS*…): w generatorze oznakowania P11_SQUARE/P11_GAP = 0,40 m, a załącznik nr 2 podaje 0,50 m (do potwierdzenia); tekst jednolity Dz.U. 2019 poz. 2311 nie zawiera późniejszych zmian załącznika nr 2 — Dz.U. 2021 poz. 2066, Dz.U. 2022 poz. 2377, Dz.U. 2026 poz. 132 (sprawdź, czy istnieją i co zmieniają). p21_hatch (P-21) czeka na decyzję właściciela — NIE zmieniaj, zostaw xfail.
Zadanie: (1) w isap.sejm.gov.pl potwierdź wymiar P-11 (strona PDF, rysunek) i popraw P11_SQUARE/P11_GAP w generatorze (grep w tools/worldgen) z komentarzem-źródłem, zdejmij odpowiedni xfail; (2) dla każdego z trzech rozporządzeń zmieniających: czy zmienia załącznik nr 2, które znaki P i jakie wymiary — tabela z cytatem ≤ 25 słów i stroną; jeśli któraś zmiana dotyczy wymiaru w naszym generatorze — popraw i dodaj test; jeśli rozporządzenie nie istnieje pod tym numerem — napisz to wprost; (3) pochylenie łącznic ≤ 6 % (§ 62 ust. 2 PTB 2022 wg recenzji — ustal sam w ISAP pełny tytuł i numer Dz.U. tego rozporządzenia, nie zgaduj): sprawdź cytat i dodaj test pytest na danych geometrii łącznic w repo (bez modyfikacji danych), który raportuje (xfail, nie fail) odcinki powyżej 6 %. NIE regeneruj świata. Raport po polsku z tabelą przed/po.
```
