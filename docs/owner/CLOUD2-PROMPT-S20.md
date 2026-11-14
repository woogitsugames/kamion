# Prompt dla DRUGIEJ sesji Claude Code w chmurze (do 10 agentów Fable/Opus, tylko GitHub) — s20

Wklej całość poniżej. Pakiety R1–R9 są nowe (nie dublują Mistrala, GPT, Argona ani pierwszej sesji chmurowej).

```
Pracujesz w repo GitHub woogitsugames/kamion (Kamion — realistyczny mobilny symulator ciężarówki z naczepą, Białystok 1:1; Unity URP, Android: telefony Samsung A16 (MT6789) i S24+). NIE masz Unity, telefonów ani lokalnych danych Data/raw — tylko git/GitHub i internet. Jesteś zespołem badawczym: do 10 subagentów naraz (Fable do zbierania i porównywania obrazów/danych, Opus do weryfikacji, liczb, norm i recenzji). Dostarczasz RZETELNE, sprawdzalne dane referencyjne dla agentów budujących grę. Nie zmieniasz kodu gry ani danych regionów.

NAJPIERW przeczytaj (origin/main): CLAUDE.md, docs/01..docs/11 (szczególnie 03 etapy, 04 fizyka, 05 mapa/dane, 06 grafika i anti-slop, 07 ciężarówka), docs/owner/AGENT-RULES.md (p. 5–6), docs/owner/MISTRAL-TASKS-10.md (część wspólna na górze = format wyników: README.md, manifest.csv, sources.md, audit_20_percent.json) oraz recenzje, za co odrzucamy research: docs/reports/REVIEW-2026-11-14-s20-mistral-m62.md, REVIEW-2026-11-14-s20-mistral-m56.md, REVIEW-2026-11-13-s20-mistral-m47-fix2.md (opisy niezgodne z obrazem, SOURCED bez źródła, kierunki magnetyczne, samokontrola bez obrazów, zmyślone liczby).

PAKIETY (jeden subagent-wykonawca na pakiet, równolegle; każdy we własnej gałęzi od najnowszego origin/main: research/cloud2-<slug>, katalog research/cloud2/<slug>/, id wierszy R<n>-NNN):
R1 traffic-signs-catalog — znaki pionowe wg Dz.U. 2019 poz. 2310 (załączniki) i warunków technicznych (Dz.U. 2019 poz. 2311): maszynowy katalog (CSV) wszystkich znaków A/B/C/D/F/T: wymiary tarcz w grupach wielkości (mała/średnia/duża/wielka), kolory (współrzędne CIE/odpowiedniki RAL z normy), krój pisma (Drogowskaz), wysokości i odległości montażu, folie odblaskowe. Cytaty z punktów rozporządzenia.
R2 direction-signs-route-c — tablice kierunkowe E-* na trasie C (ul. gen. Andersa, rondo Putry, Al. Tysiąclecia, Bieżeństwa): lokalizacje (OSM/zdjęcia), treść, układ, wymiary, sposób montażu (bramownice, wysięgniki). Lokalizacje kamer: Data/Regions/bialystok-industrial-c/sbs_cameras.json i generated/control_cameras.json.
R3 truck-parameters — ciągnik siodłowy 4x2 (fikcyjny, klasa ~460–500 KM) + naczepa kurtynowa 13,6 m: zakresy realnych parametrów z otwartych źródeł (karty techniczne producentów jako dane techniczne bez marek w opisach do gry, normy, publikacje): masy osi, rozstaw, wysokość siodła, moment/obroty, przełożenia skrzyni 12-biegowej, przełożenie mostu, promień dynamiczny opon 315/70R22.5 i 385/65R22.5, współczynniki opon (publikacje Pacejka/MF-Tyre dla opon ciężarowych), opóźnienia hamowania EBS, retarder. Porównaj z docs/04 i ADR fizyki (docs/adr) — tabela „gra vs źródło”.
R4 bialystok-building-typology — typologia zabudowy Białegostoku przy trasie C i w Dojlidach: bloki wielkiej płyty (systemy, wymiary modułów, kolory po termomodernizacji), biurowce, hale magazynowe/produkcyjne (okładziny, bramy, attyki), domy. Zdjęcia + liczby (kondygnacje, wysokości z GUGiK LoD/NMPT jeśli dostępne przez publiczne usługi).
R5 street-trees — drzewa uliczne Białegostoku: gatunki dominujące (inwentaryzacje UM, BIP, open data, OSM natural=tree), typowe wysokości/korony wg wieku, rozstaw szpalerów, żywopłoty (tuje!), sezonowość. Liczby do generatora zieleni (docs/adr/0163*, 0170*).
R6 pavements-kerbs — nawierzchnie i drobna infrastruktura: typy kostki (wymiary, kolory, wzory układania), krawężniki/obrzeża (wymiary norm), wpusty/studzienki, łaty i spękania asfaltu, czerwony asfalt DDR — zdjęcia z bliska z trasy C i Dojlid + normy.
R7 sky-weather-bialystok — klimat światła Białegostoku: zachmurzenie i nasłonecznienie per miesiąc (IMGW open data), wysokość słońca w kluczowych porach, typowe niebo pochmurne (opis + zdjęcia CC), mgła/zamglenie; liczby do profilu nieba i mgły (gra ma „koralowy pas horyzontu” jako błąd — docs/adr/0192*).
R8 mobile-gpu-a16 — MediaTek Helio G99 / MT6789 (A16) i Snapdragon 8 Gen 3 (S24+): GPU (Mali-G57 MC2 / Adreno 750) — przepustowość, limity Vulkan, koszt typowych technik (alpha-test vs alpha-blend, MSAA, cienie, overdraw), zalecenia ARM/Qualcomm/Unity dla URP mobile, znane problemy sterowników. Cel: gra ma p95 GPU 34,5 ms przy budżecie 33,3 ms na A16 Low — zbierz konkretne, cytowane techniki oszczędności z szacunkiem zysku (UNVERIFIED gdzie brak pomiaru).
R9 next-region-ring — dostępność otwartych danych dla następnego regionu (obrzeża Białegostoku: ring S8/DK8/DK19, węzły): OSM kompletność, GUGiK (ortofoto rok, NMT, BDOT10k, LoD), zdjęcia (Commons/Panoramax/KartaView/Mapillary pokrycie), lista punktów rozpoznawalnych do bramki — raport planistyczny.
Dodatkowo 1 subagent-RECENZENT (Opus): po każdym pakiecie, zanim otworzysz PR, recenzuje go jak w plikach REVIEW-* (werdykt, P0/P1/P2), a wykonawca poprawia P0/P1. Recenzję zapisz w katalogu pakietu jako REVIEW.md.

ZASADY TWARDE:
- Źródła wyłącznie otwarte: OSM (Overpass — zapisz zapytanie i datę), GUGiK (publiczne usługi), Wikimedia Commons, Openverse (CC0/BY/BY-SA), Panoramax, KartaView, Mapillary (tylko z własnym tokenem — nigdy go nie zapisuj), ISAP/Dz.U., UNECE, IMGW, BIP/UM Białystok, dokumentacje producentów (dane techniczne, cytat + link), publikacje naukowe (DOI). ZAKAZ: Google Maps/Street View/Earth/3D Tiles (także pośrednio), Bing, Apple, Yandex, obrazy bez licencji.
- Bez zmyślania: każda liczba = cytat + link, albo pomiar (ESTIMATED + metoda), albo UNVERIFIED. Opis kadru = tylko to, co widać na obejrzanym obrazie (pobierz, ≤ 960 px, detale w wycinku 3×). Kierunek kadru = azymut geograficzny. Duplikaty (sha256) oznacz. Samokontrola 20 % z jawnym seedem i PONOWNYM obejrzeniem obrazów.
- W opisach do gry bez marek i logo.
- Zdjęć ani PDF-ów nie commituj (files/ w .gitignore). W manifeście: url strony, url pliku, licencja, autor, sha256; w katalogu fetch.py, który pobiera pliki do files/ i weryfikuje sha256.
- Zmieniaj wyłącznie swój katalog research/cloud2/<slug>/.

ZAPIS CIĄGŁY: po każdym kroku commit + push na gałąź pakietu i STATUS.md (co zrobione, liczby, NASTĘPNY KROK) — sesja może zostać przerwana.

NA KOŃCU każdego pakietu: commit + push, PR do main (tytuł „research(cloud2): R<n> <slug>”, w opisie: liczba wierszy, obejrzanych kadrów, wynik samokontroli i recenzji, luki, rozmiar plików do pobrania; zakończ „🤖 Generated with [Claude Code](https://claude.com/claude-code)”). NIE scalaj — scala lider po własnej recenzji. Po wszystkich PR napisz podsumowanie: numery PR, gałęzie, co niekompletne.
```

## Dokończenie (wklej w tę samą sesję chmury #2 po 19:20)
```
Lider: możesz znowu uruchamiać agentów (do 10). Dokończ pakiety-drafty według ich STATUS.md: R2 (#62: ≥ 20 kadrów, dodaj ul. gen. Andersa), R4 (#64: ≥ 30 kadrów, w tym Dojlidy; opisy elewacji), R6 (#65: obejrzyj 31 pobranych kadrów i opisz). Potem recenzja (osobny agent-recenzent, jak wcześniej) dla R2, R4, R5, R6, R7, R9; popraw P0/P1. Zdejmij draft z PR po ukończeniu. W commitach stopka: „Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>” lub odpowiednia dla modelu — bez zmyślonych nazw. W nagłówkach HTTP (User-Agent) tylko ogólna nazwa klienta, bez nazw organizacji/repo. Na końcu krótkie podsumowanie PR.
```
