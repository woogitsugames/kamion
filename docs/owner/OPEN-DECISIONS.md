# Otwarte decyzje właściciela i lidera (stan 2026-11-16, s23)

Zebrane z: `docs/adr/*.md` (sekcje „Otwarte”, „Pytania do właściciela”, „do decyzji”), ADR w otwartych PR (#112 0273,
#113 0228, #115 0231, #117 0243, #123 0238, #139 0227, #143 0275, #144 0274), raportów `docs/reports/*s22*`, `*s23*`,
`REVIEW-2026-11-1[56]-*`, `INTEGRATION-*`, `VERIFY-*`, `HANDOVER.md` (SESJA 22–23), `docs/owner/BACKLOG-S21.md`.
Każdą pozycję sprawdzono z `docs/11_DECYZJE_WLASCICIELA.md` (D1–D75). Rozstrzygnięte są na dole, a nie w indeksie.
Stan PR z `gh api repos/woogitsugames/kamion/pulls?state=all` (16.11): #112 #113 #115 #117 #123 #139 #141 #142 #143 #144
otwarte. #114 zamknięty bez scalenia. #138 zamknięty, a jego zawartość weszła przez rail-dk65-s22.

**Priorytety:** P1 blokuje bramkę albo integrację, P2 dotyczy jakości, P3 kosmetyki lub odległego etapu.
**Kto decyduje:** W = właściciel, L = lider. Pozycje L są tu po to, żeby właściciel mógł je przejąć albo potwierdzić.
**Format:** każda pozycja ma 2–3 opcje z krótką etykietą, gotowe do pytania klikalnego (AskUserQuestion). Rekomendowana
opcja jest zawsze pierwsza na liście w pytaniu (opcja A).

## Indeks (posortowany po priorytecie)

| ID | P | Kategoria | Pytanie (skrót) | Rekom. | Kto | Zdjęcia / pomiar W |
|---|---|---|---|---|---|---|
| OD-001 | P1 | PC / wydajność | Sprzęt referencyjny klas min / zalecany | A | W | tak (sprzęt) |
| OD-002 | P1 | fizyka / bramka 2 | Feel test bramki 2: kiedy i na czym | A | W | tak (jazda) |
| OD-003 | P1 | integracja / Knyszyn | #139 Rynek: przejęcie gałęzi Codexa i +64 draws Low | A | W | nie |
| OD-004 | P1 | integracja / świat | Streaming kafli (#114) przed paczkami (#112)? | A | L | nie |
| OD-005 | P1 | świat / szwy | Rodzina profilu na szwach DK8 i Kleeberga (FAIL 1,0 m) | A | L | nie |
| OD-006 | P1 | świat / szwy | Szew dk65-11 i knyszyn-s (czerwony test 0,26 m na stronę) | A | L | nie |
| OD-007 | P2 | świat / Knyszyn | Wymiary ronda DK65 × Tykocka (0274) | A | L / W | opcjonalnie (pomiar) |
| OD-008 | P2 | świat / kolej | `approach_speed_kmh` 90 na DW671 przed przejazdem | A | W | tak (zdjęcie / wizja) |
| OD-009 | P2 | świat / kolej | Wyposażenie 4–5 przejazdów kolejowych dk65 | A | L / W | opcjonalnie |
| OD-010 | P2 | świat / DK65 | Szerokość Knyszyńskiej w dk65-01 (`width 6.0`) | A | L | nie |
| OD-011 | P2 | świat / szwy | Długości przejść szerokości (0275 RATIO / MIN / MAX) | A | L | nie |
| OD-012 | P2 | PC / pamięć | Budżety pamięci świata na PC (0273) | A | L / W | nie |
| OD-013 | P2 | świat / mapa | Skala korytarza Białystok–Knyszyn wobec D2 | A | W | nie |
| OD-014 | P2 | wejście / PC | Kierownica z FFB: wtyczka SDL3 i test na sprzęcie | A | W / L | tak (kierownica) |
| OD-015 | P2 | fizyka | Muśnięcie kabina–naczepa po ciasnym skręcie (0228) | A | W | po feel teście |
| OD-016 | P2 | fizyka | `maxLaunchGear` 4 czy 2 i `clutchMaxTorque` 4000 Nm | A | W | po feel teście |
| OD-017 | P2 | świat / zieleń | Gatunki drzew w szpalerach DK65 (0222) | A | L / W | opcjonalnie |
| OD-018 | P2 | świat / Knyszyn | Latarnie Knyszyna: typ słupa, DK65 przy wjeździe | A | W | tak (zdjęcie) |
| OD-019 | P2 | świat / Knyszyn | Wiaty targowicy: wymiary (WORKING_VALUE) | A | W | opcjonalnie |
| OD-020 | P2 | świat / woda | Woda w pierścieniu (Narew, Nareśl), w C i Dojlidach | A | L / W | nie |
| OD-021 | P2 | PC / grafika | Cienie drzew za kartami LOD1 na PC | A | L | pomiar GTX 660 |
| OD-022 | P2 | prawo | Adres publikacji bazy pochodnej ODbL (R-P0-2) | A | W | nie |
| OD-023 | P3 | świat / C | Maszty wieżowca Andersa 38 | A | L | nie |
| OD-024 | P3 | świat / pierścień | Latarnie w Mońkach: LED czy reguła | A | W | opcjonalnie |
| OD-025 | P3 | świat / C | Barwa 4000 K LED na ulicach C z K69 | A | W | nie |
| OD-026 | P3 | świat / DK65 | Plac budowy DK65: materiał, strona, płoty, Kozińce | A | W | tak (zdjęcie) |
| OD-027 | P3 | świat / DK65 | Szerokości Fasty S 6,5 m i mostu na Supraśli 7,5 m | A | L | nie |
| OD-028 | P3 | świat / kolej | Barwa podsypki toru (render 0,81 vs ortofoto 0,44) | A | L / W | opcjonalnie |
| OD-029 | P3 | UI / PC | Kierunkowskazy w HUD na monitorze | A | W | nie |
| OD-030 | P3 | UI / audio | Suwak „Silnik” a dźwięk opon i wiatru | A | W | odsłuch |
| OD-031 | P3 | UI / sterowanie | Położenie i rozdzielczość okienek lusterek | A | W | ocena na buildzie |
| OD-032 | P3 | start | Start 90 m za zaporą, `BehindClosureM` 25 m | A | W | ocena na buildzie |
| OD-033 | P3 | świat / C | Udział bloków nieocieplonych 30 % (0238) | A | L | nie |
| OD-034 | P3 | świat / C | E-14 za rondem Putry i barwa zieleni tablic E | A | L | nie |
| OD-035 | P3 | światło | Noc: kompensacja −0,405 EV i zegar okien biur 22:00 | A | W | nie |
| OD-036 | P3 | wydajność / A16 | Warianty profilu Low A16 (skala, LOD bias, far clip) | A | W | nie |
| OD-037 | P3 | build / PC | Mono czy IL2CPP, tryb okna, ikona, etykieta `-dirty` | A | L | nie |
| OD-038 | P3 | prawo | Mapillary §12, BDL, zarządzenie 973/21 Białystok | A | W | nie |
| OD-039 | P3 | biznes | Kanał dystrybucji PC, model DLC, mody, wersja telefonu | A | W | nie |
| OD-040 | P3 | marka | Nazwa gry i znak TRAKT (D17) | A | W | nie |
| OD-041 | P3 | proces | Zamknięcie zastąpionych PR (#93, #106, #100, #92) | A | L / W | nie |
| OD-042 | P3 | proces / dysk | Sprzątanie poza projektem i limit worktree z `Library` | A | W | nie |
| OD-043 | P3 | audio | Odsłuch A/B dźwięku silnika 0232 / ElevenLabs REGEN-04 | A | W | odsłuch |

Razem: **P1 = 6, P2 = 16, P3 = 21** (43 pozycje).

---

## P1 — blokuje bramkę albo integrację

### OD-001 · P1 · PC / wydajność — sprzęt referencyjny PC
- **Pytanie:** Na jakim sprzęcie mierzymy klasy „min” i „zalecany” z D74, żeby raporty PC mogły zaliczać bramki?
- **Opcje:**
  - **A — Emulacja na RTX 5070:** pomiar na maszynie deweloperskiej z ograniczeniem rozdzielczości, tieru i limitu FPS
    zostaje uznany za metodę zastępczą. Raporty dostają `gate_eligible`, a ryzyko klasy iGPU zostaje.
  - **B — Wskazany prawdziwy sprzęt:** właściciel wskazuje albo pożycza PC klasy GTX 660 / HD 630 i GTX 1660. To pomiar
    zgodny z D74, ale wymaga dostępu do sprzętu (D9: 0 zł).
  - **C — Tylko informacyjnie do premiery:** bramki PC dalej bez zaliczenia (`referenceMachines: []`). Etapy 4–7 nie
    dostają liczb zaliczających.
- **Rekomendacja:** A teraz, a B przed obietnicą wymagań sprzętowych. Bez tej decyzji żaden raport PC nie jest bramkowy
  (`docs/03:25-27`), a D74 i tak wymaga pomiaru na iGPU przed obietnicą.
- **Źródło:** `docs/adr/0266-bramki-budzety-pc.md:17,64-67`; `docs/03_ETAPY_I_BRAMKI.md:25-27`; `docs/adr/0269-tiery-grafiki-pc.md:133`;
  `docs/adr/0271-dystrybucja-pc.md:62`; D74.
- **Zdjęcia / pomiar właściciela:** tak, przy B (sprzęt). Przy A potrzebna tylko zgoda.

### OD-002 · P1 · fizyka / bramka 2 — feel test właściciela
- **Pytanie:** Kiedy i na czym właściciel robi feel test bramki 2 (ruszanie pod górę z 40 t, hamowanie, rondo R50,
  cofanie pod rampę)?
- **Opcje:**
  - **A — Teraz, exe PC, pad lub klawiatura:** test na najnowszym exe (`Kamion-knyszyn.cmd`) zamyka bramkę 2 zgodnie
    z `docs/03:95`. Uwagi trafiają do strojenia 0201b, 0228 i 0264.
  - **B — Po kierownicy z FFB:** test dopiero z kierownicą (OD-014). Wynik jest bliższy docelowemu, ale bramka 2 czeka
    na sprzęt.
  - **C — Dalej odłożony:** bramka 2 zostaje otwarta. Parametry feelingu (pad, przegub, AMT) zostają WORKING_VALUE.
- **Rekomendacja:** A. Bramka 3 jest zaliczona (D57), więc warunek odłożenia z D70 już nie obowiązuje, a 4 ADR czekają
  na ten test.
- **Źródło:** `docs/owner/BACKLOG-S21.md:113,204` (B-075); `docs/adr/0201b-naciski-osi-73-27-strojenie-zawieszenia-amt.md:144`;
  PR #113 `docs/adr/0228-…:170-171`; `docs/adr/0264-pad-klawiatura-rebinding.md:105`; `docs/03_ETAPY_I_BRAMKI.md:95`; D70.
- **Zdjęcia / pomiar właściciela:** tak (jazda + lista uwag; instrukcja `docs/owner/FEEL-TEST.md`).

### OD-003 · P1 · integracja / Knyszyn — #139 Rynek (Codex)
- **Pytanie:** Czy lider przejmuje gałąź `knyszyn-rynek-0227` lokalnie i przyjmuje wzrost Low na kamerze
  `dk65-inlet-south` 240 → 304 draw calls?
- **Opcje:**
  - **A — Przejąć i przyjąć +64 draws Low:** sprzątanie artefaktów, bramkowanie QA modułów 0227, przebudowa knyszyn.
    Wzrost przyjęty jak D62, bo telefon jest drugorzędny (D73). Kontrola na A16 przy następnym APK.
  - **B — Przejąć, ale budżet neutralny:** to samo, z wymogiem zejścia do ≤ 240 draws. Trzeba łączyć siatki albo
    ograniczyć mały detal Rynku.
  - **C — Zamrozić do powrotu Codexa:** Rynek (miasto właściciela, D64) czeka. Gałąź się starzeje względem main.
- **Rekomendacja:** A. Rynek to główny brak rozpoznawalności Knyszyna, a High (~1,25 mln tris) mieści się w budżecie.
- **Źródło:** `HANDOVER.md:259`; `docs/reports/REVIEW-2026-11-16-s23-code-139.md:47,82`; PR #139
  `docs/adr/0227-knyszyn-rynek.md:16,147`.
- **Zdjęcia / pomiar właściciela:** nie (zgoda na przejęcie worktree Codexa wymagana wg `HANDOVER.md:259`).

### OD-004 · P1 · integracja / świat — streaming kafli przed paczkami regionów
- **Pytanie:** Czy streaming kafli `streaming-0235` (#114 zamknięty bez scalenia) wraca jako nowy PR przed #112
  (paczki regionów, ADR 0273)?
- **Opcje:**
  - **A — Nowy PR streaming, potem #112:** kolejność z ADR 0273 („#112 → #114”). Daje przejazd korytarzem bez zapór
    na szwach (`docs/03` Etap 7).
  - **B — Tylko #112:** paczki jako dystrybucja, bez streamingu. Sceny `_Tile` nie powstaną, kod paczek zostaje niepodpięty.
  - **C — Oba po bramce 4:** korytarz dalej jako osobne sceny z zaporami (ADR 0229).
- **Rekomendacja:** A, po bieżącej przebudowie C i świata. Bez streamingu #112 nie ma czego ładować, a cel D64
  (korytarz do Knyszyna) wymaga ciągłej jazdy.
- **Źródło:** `docs/reports/PR-TRIAGE-2026-11-16-s23.md:84-85`; PR #112 `docs/adr/0273-…:86-90`;
  `docs/adr/0229-wybor-regionu-w-buildzie-i-menu.md:99-100`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-005 · P1 · świat / szwy — rodzina profilu jezdni na szwach DK8 i Kleeberga
- **Pytanie:** Która strona szwu ma rację, gdy jeden kafel daje pobocze wiejskie, a drugi krawężnik płaski: DK8
  `w257367422` (industrial-c | maczka) i `w261104557` (kleeberga | knyszynska)? Krawędź asfaltu różni się o 1,0 m
  (FAIL w raporcie szwów).
- **Opcje:**
  - **A — Pomiar ortofoto i override per way:** `ortho_xsec.py` na obu odcinkach, ten sam wpis w obu kaflach.
    Zgodne z „nie zmyślaj”.
  - **B — Krawężnik w obu kaflach:** reguła miejska wygrywa. To proste rozwiązanie, ale może być nieprawdziwe poza
    zabudową.
  - **C — Pobocze w obu kaflach:** reguła „fast” wygrywa. Tak samo proste, ale może być nieprawdziwe w mieście.
- **Rekomendacja:** A. Oba szwy leżą na trasach startowych (C i korytarz).
- **Źródło:** PR #143 `docs/adr/0275-przejscia-szerokosci-na-szwach-kafli.md:106-108`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-006 · P1 · świat / szwy — szew dk65-11 i knyszyn-s
- **Pytanie:** Jak zamknąć czerwony test `test_dk65_seam_knyszyn_0233` (asfalt 7,3 m w dk65-11 wobec 6,78 m
  w knyszyn-s, skok 0,26 m na stronę)?
- **Opcje:**
  - **A — Przejście klinem z #143 (0275):** wierność pomiarowi w knyszyn-s zostaje (decyzja lidera). Test przechodzi
    na geometrii z klinem.
  - **B — Opaska `dk65-opaska-k1` także w knyszyn-s:** brak skoku, ale 342 m knyszyn-s odchodzi od pomiaru 6,7–7,1 m.
  - **C — Tolerancja testu 0,3 m:** szybkie, ale osłabia test (zakaz osłabiania testów w INTEGRATION).
- **Rekomendacja:** A. Jest zgodne z decyzją lidera z 16.11 05:5x i już zaimplementowane w #143.
- **Źródło:** `docs/reports/INTEGRATION-2026-11-16-rail-xsec.md:37,91`; `HANDOVER.md:250`; PR #143 ADR 0275.
- **Zdjęcia / pomiar właściciela:** nie.

---

## P2 — jakość

### OD-007 · P2 · świat / Knyszyn — wymiary ronda DK65 × Tykocka
- **Pytanie:** Skąd biorą się ostateczne wymiary ronda (promienie krawężników, szerokość pasa i opaski, Ø wyspy, długości
  wysepek N i S, odsunięcie przejść), które w 0274 są WORKING_VALUE / ESTIMATED?
- **Opcje:**
  - **A — Lider skaluje zdjęcia 9–11:** skala z szerokości pasa wlotu albo długości samochodu, potem override
    i `swept_path.py`. Wynik jest powtarzalny, choć niegeodezyjny.
  - **B — Pomiar właściciela na miejscu:** taśma albo kroki, 5–6 liczb. Najdokładniej, ale wymaga wyjścia na rondo.
  - **C — Zostają wartości D75:** pierścień 5,0 m + opaska 3,2 m (przejezdność). Wymiary wysepek pozostają szacunkiem.
- **Rekomendacja:** A. Zdjęcia już są, a D75 i tak każe przedkładać przejezdność nad wierność, więc pomiar właściciela
  nie jest konieczny.
- **Źródło:** PR #144 `docs/adr/0274-rondo-knyszyn-krawezniki-rozdzial-dk65-wyspa.md:14,47,59-61,88-89`;
  `docs/adr/0218-rondo-knyszyn-opaska-dla-naczepy.md:236-238`; D75.
- **Zdjęcia / pomiar właściciela:** opcjonalnie (B).

### OD-008 · P2 · świat / kolej — prędkość dojazdu DW671 do przejazdu
- **Pytanie:** Czy na DW671 przed przejazdem przez linię 38 obowiązuje > 60 km/h (`approach_speed_kmh: 90`, A-9 150 m),
  czy ograniczenie „50” z Mapillary (2019, 57 m od przejazdu) zaczyna się wcześniej?
- **Opcje:**
  - **A — Zostaje 90 (A-9 150 m):** stan obecny (WORKING_VALUE, decyzja lidera s22). Zgodne z polami na zdjęciach
    Mapillary.
  - **B — ≤ 60 km/h:** krótszy przedział odległości znaków z § 3 ust. 2 (wartości do odczytu z aktu). Ma sens tylko,
    jeśli B-33 stoi przed całym dojazdem.
  - **C — Wizja lokalna / zdjęcie:** właściciel albo nowy kadr Mapillary potwierdza odległość A-9 i istnienie B-33.
- **Rekomendacja:** A do czasu C. To jedyna wartość, która przesuwa całe oznakowanie dojazdu, a obecne źródło jest
  z 2019.
- **Źródło:** `docs/adr/0268-oznakowanie-dojazdu-do-przejazdow-kolejowych.md:82-91`; `Data/Regions/dw671-tykocin-01/overrides.yaml:66-73`;
  `docs/reports/INTEGRATION-2026-11-16-rail-xsec.md:86`; `HANDOVER.md:228`.
- **Zdjęcia / pomiar właściciela:** tak (C), w przeciwnym razie zostaje A.

### OD-009 · P2 · świat / kolej — wyposażenie przejazdów dk65 (UNVERIFIED)
- **Pytanie:** Jaką kategorię i wyposażenie mają przejazdy Dzikowska, Św. Franciszka, Białostocka i droga bez nazwy
  (dziś domyślnie A-10 bez tablicy, kategoria z tagów OSM)?
- **Opcje:**
  - **A — Kadry Mapillary / Panoramax per przejazd → override:** `kind: rail_crossing` z cytatem kadru. Bez zgadywania.
  - **B — Rejestr przejazdów PLK:** kategoria urzędowa, jeśli dostępna publicznie (licencja do sprawdzenia).
  - **C — Zostaje domyślne:** A-10 bez tablicy. Ryzyko błędnej kategorii na trasie DK65.
- **Rekomendacja:** A. Te przejazdy są w kaflach korytarza D67. Tablicę „Sygnalizacja automatyczna” (wzór UNVERIFIED)
  rozstrzygnąć tym samym kadrem.
- **Źródło:** `docs/adr/0223-linia-38-dk65-wlaczenie-torowiska.md:182-184`; `docs/adr/0268-…:202,208-209`.
- **Zdjęcia / pomiar właściciela:** opcjonalnie (zdjęcie przejazdu przyspiesza A).

### OD-010 · P2 · świat / DK65 — szerokość Knyszyńskiej w dk65-01
- **Pytanie:** Czy `width: 6.0` na Knyszyńskiej (way 234919333 i sąsiednie w dk65-01, asfalt 6,16 m przy pomiarze
  6,65–7,4 m) poprawić do 6,6 m jak D66?
- **Opcje:**
  - **A — 6,6 m w dk65-01 i bialystok-knyszynska:** razem z `edge_line_spacing 6.2`, ten sam wpis w obu kaflach
    (inaczej skok na szwie).
  - **B — Zostaje 6,0 m:** brak przebudowy, ale asfalt jest węższy od pomiaru o 0,5–1,2 m.
  - **C — Pomiar odcinkowy `ortho_xsec`:** profil `width` per odcinek. Dokładniej, ale drożej.
- **Rekomendacja:** A. To ta sama reguła co D66 z tego samego badania K1.
- **Źródło:** `docs/adr/0272-pobocze-drog-zamiejskich-jako-dane.md:170,185-186`; `docs/adr/0220-dk65-k1-przekroj-linie-krawedziowe-zatoki.md:105-106`;
  `docs/adr/0205-korytarz-dk65-kafel-dk65-01.md:80-82`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-011 · P2 · świat / szwy — długości przejść szerokości (0275)
- **Pytanie:** Czy przyjmujemy `RATIO` / `MIN_LEN_M` / `MAX_LEN_M` klinów z ADR 0275 (ESTIMATED)?
- **Opcje:**
  - **A — Przyjąć po renderze szwów:** lider ogląda 7 szwów po `build_world`. Korekta tylko, gdy klin razi.
  - **B — Pomiar klinów na ortofoto:** 3–5 realnych zwężeń DK65 jako wzór. Wartości stają się pomiarem.
  - **C — Kliny tylko w znanych stykach:** zamiast połowy w każdym kaflu profil `width` tam, gdzie w terenie zmienia
    się nawierzchnia (jak km 25,32).
- **Rekomendacja:** A. Przejścia są małe (≤ 0,5 m na stronę) i odwracalne, a B można zrobić przy szlifie (D63).
- **Źródło:** PR #143 `docs/adr/0275-…:105,110-111`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-012 · P2 · PC / pamięć — budżety pamięci świata (0273)
- **Pytanie:** Czy przyjmujemy budżety świata PC Low 640 / Medium 800 / High 1450 / Ultra 2000 MB i cel working set
  ≤ 4 GB (8 GB RAM) / ≤ 6 GB (12 GB RAM) jako WORKING_VALUE do pierwszego pomiaru?
- **Opcje:**
  - **A — Przyjąć jako WORKING_VALUE:** liczby wyprowadzone z danych (3 najgorsze kafle + przypięty + 10 %), weryfikacja
    `stream-report.py --gate`.
  - **B — Zaostrzyć na Low:** np. tylko 2 kafle rezydentne. Mniej RAM, ale krótszy look-ahead przy 90 km/h.
  - **C — Bez budżetu do pomiaru:** brak bramki pamięci na PC. Ryzyko na klasie 8 GB.
- **Rekomendacja:** A. Wartości mają jawne wyprowadzenie i test EditMode, a pomiar i tak rozstrzygnie (OD-001).
- **Źródło:** PR #112 `docs/adr/0273-swiat-streaming-kafli-paczki-jako-dystrybucja.md:55-75`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-013 · P2 · świat / mapa — skala korytarza Białystok–Knyszyn
- **Pytanie:** D2 mówi „trasy między miastami skrócone”, a korytarz DK65 (dk65-01…11) jest budowany 1:1. Czy to wyjątek?
- **Opcje:**
  - **A — Korytarz do Knyszyna 1:1 jako wyjątek:** to miasto właściciela (D64). Współczynnik skali obowiązuje od
    następnych tras (Etap 7).
  - **B — Skrócić także ten korytarz:** zgodne z D2, ale wymaga przebudowy 11 kafli i łamie wierność „ta sama droga”.
  - **C — Wszystko 1:1:** zmiana D2. Duży koszt mapy przy każdym kolejnym mieście.
- **Rekomendacja:** A. Zachowuje to, co już jest zbudowane i zaakceptowane, a decyzję o skali zostawia na Etap 7.
- **Źródło:** `docs/11_DECYZJE_WLASCICIELA.md:8,25` (D2, „Współczynnik skali tras”); `docs/03_ETAPY_I_BRAMKI.md:120`; D64.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-014 · P2 · wejście / PC — kierownica z FFB
- **Pytanie:** Czy dodajemy natywną wtyczkę SDL3 (zlib) do FFB i czy właściciel ma kierownicę do testu?
- **Opcje:**
  - **A — SDL3 teraz + test na kierownicy właściciela:** lider zakłada `Plugins/x86_64/`. FFB działa na większości baz
    (UNVERIFIED per model).
  - **B — Windows.Gaming.Input:** bez obcej biblioteki, ale wymaga warstwy C++/WinRT i obsługuje mniej baz.
  - **C — Po premierze PC:** kierownica bez FFB (oś + pedały działają, ADR 0263). FFB przychodzi jako aktualizacja
    (`docs/10` §3a pkt 6).
- **Rekomendacja:** A, jeśli właściciel ma kierownicę. W przeciwnym razie C, bo bez sprzętu nie da się sprawdzić efektu.
- **Źródło:** `docs/adr/0263-kierownica-pedaly-ffb.md:50-53`; `docs/10_ARCHITEKTURA_I_DLC.md:83`; D56.
- **Zdjęcia / pomiar właściciela:** tak (model kierownicy, test).

### OD-015 · P2 · fizyka — muśnięcie kabina–naczepa
- **Pytanie:** Czy akceptujemy krótki kontakt kabina–naczepa po hamowaniu z 13–20 km/h przy 55–60° (≤ 0,61 mm,
  w 1. kroku 71–79 kN, 40 t)?
- **Opcje:**
  - **A — Akceptować, scenariusz z progiem w CI:** `max_coupling_contact_force_kn ≤ 100`. Nie blokuje feel testu.
  - **B — Zmienić wymiary:** odstęp tyłu kabiny od sworznia 2,07 m, ograniczone długością 16,50 m. Dotyka modelu 3D.
  - **C — Tłumienie kołysania ciągnika:** zmienia feeling i złotą telemetrię.
- **Rekomendacja:** A, a wrócić do tematu po feel teście (OD-002), jeśli „stuk” będzie odczuwalny.
- **Źródło:** PR #113 `docs/adr/0228-przegub-kontakt-kabina-naczepa-ladowanie.md:160-165`;
  `docs/reports/REVIEW-2026-11-16-s23-code-H3.md:78-87`.
- **Zdjęcia / pomiar właściciela:** po feel teście.

### OD-016 · P2 · fizyka — bieg ruszania i moment sprzęgła
- **Pytanie:** Czy AMT ma ruszać maksymalnie z 4. czy z 2. biegu (`maxLaunchGear`) i czy zostaje `clutchMaxTorque`
  4000 Nm (źródła nie rozstrzygają)?
- **Opcje:**
  - **A — Zostaje 4 / 4000 Nm, ocena w feel teście:** bez zmian do OD-002.
  - **B — Bieg 2:** wolniejsze, „ciężkie” ruszanie z 40 t. Zmienia golden telemetry 0–80.
  - **C — Zależnie od masy:** 2 przy 40 t, 4 solo. Wymaga ADR fizyki.
- **Rekomendacja:** A. Decyzja feelingowa, więc rozstrzyga ją feel test.
- **Źródło:** `docs/owner/BACKLOG-S21.md:108` (B-070).
- **Zdjęcia / pomiar właściciela:** po feel teście.

### OD-017 · P2 · świat / zieleń — gatunki szpalerów DK65 (UNVERIFIED)
- **Pytanie:** Jakie gatunki mają szpalery wzdłuż DK65 i Ełckiej (dziś klon 0,35 / lipa 0,30 / brzoza 0,20 / olsza 0,15,
  bez źródła)?
- **Opcje:**
  - **A — Kadry Mapillary / Panoramax wzdłuż DK65:** ocena gatunku po pokroju i korze na 5–10 odcinkach, z cytatem.
  - **B — Zdjęcia właściciela DK65 / Ełckiej:** najpewniejsze dla trasy, którą właściciel zna.
  - **C — Zostaje WORKING_VALUE:** szpalery wyglądają „ogólnie”. Gatunek wpływa na sylwetkę z daleka.
- **Rekomendacja:** A, a B tylko jeśli właściciel i tak jedzie tą trasą. Szpalery są głównym obrazem korytarza za miastem.
- **Źródło:** `docs/adr/0222-szpalery-dk65.md:12,83,143`.
- **Zdjęcia / pomiar właściciela:** opcjonalnie.

### OD-018 · P2 · świat / Knyszyn — latarnie Knyszyna
- **Pytanie:** Jaki typ słupa mają latarnie w Knyszynie i czy DK65 między granicą miasta a rondem ma latarnie (dziś
  z reguły, niezweryfikowane)?
- **Opcje:**
  - **A — Zdjęcie właściciela (dzień lub noc):** typ słupa, wysięgnik, rozstaw. Rozstrzyga oba pytania naraz.
  - **B — Betonowe z wysięgnikiem jednostronnym:** wg K1 (zdjęcia 2009–2012), mogą być nieaktualne.
  - **C — Zostaje reguła generatora:** stalowe ocynkowane, WORKING_VALUE.
- **Rekomendacja:** A. Knyszyn to miasto właściciela (D64: zdjęcia mile widziane), a latarnie są w każdym kadrze ulicy.
- **Źródło:** `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md:124-126`; `docs/adr/0204-region-knyszyn-miasto-i-wlot-dk65.md:64,101`;
  `docs/adr/0209-region-knyszyn-w-wylot-dk65-na-monki.md:63`.
- **Zdjęcia / pomiar właściciela:** tak.

### OD-019 · P2 · świat / Knyszyn — wiaty targowicy
- **Pytanie:** Czy wymiary 4 wiat targowicy (słupy, wysokości, przekroje, nachylenie dachu, pawilon) mogą zostać
  WORKING_VALUE z ortofoto 2025 i zdjęć 12–14?
- **Opcje:**
  - **A — Zostają z ortofoto + zdjęć:** układ 3+1 już zgodny (r26/r28). Korekta tylko na podstawie par zdjęcie–render.
  - **B — Pomiar właściciela:** wysokość okapu, rozstaw słupów, 3–4 liczby. Najlepsza wierność.
  - **C — Ocena na renderze r28 bez zmian:** właściciel ogląda `compare/r28/High-clear/14-owner-render.jpg` i mówi
    „jest / nie jest”.
- **Rekomendacja:** A + C. Rozpoznawalność ocenia się z poziomu oczu (zdjęcie 14), a liczby z B są drugorzędne.
- **Źródło:** PR #139 `docs/adr/0227-knyszyn-rynek.md:20,136-138,143,173`; `HANDOVER.md:219,255`.
- **Zdjęcia / pomiar właściciela:** opcjonalnie (B); C to ocena renderu.

### OD-020 · P2 · świat / woda — woda w pierścieniu, w C i Dojlidach
- **Pytanie:** W których regionach włączyć etap wody (`water=True`): Narew i Nareśl w pierścieniu (most na Narwi
  194,8 m), Biała w C, strumienie Dojlid, stawy Tykocina?
- **Opcje:**
  - **A — Pierścień i Tykocin teraz, C i Dojlidy później:** nowe kafle bez linii bazowej, a C ma budżet 2 mln na granicy.
  - **B — Wszędzie teraz:** nowa linia bazowa determinizmu i fidelity C, presja na budżet C.
  - **C — Nigdzie poza dk65-02/03:** most na Narwi bez wody pod spodem.
- **Rekomendacja:** A. Most nad suchym korytem byłby rażący, a C nie ma zapasu trójkątów (stretch_04 ~1,99 mln).
- **Źródło:** PR #115 `docs/adr/0231-pierscien-monki-tykocin-jasionowka-definicja-z-grubsza.md:76`;
  `docs/adr/0210-etap-wody-rzeki-stawy.md:110-111`; `docs/adr/0213-woda-dk65-03-kolor-brzegi.md:168`;
  `docs/adr/0212-linie-krawedziowe-dk65-knyszyn-i-kafle-monki-tykocin.md:81-82`.
- **Zdjęcia / pomiar właściciela:** nie (kolor wody: `0213:157-158` prosi o zdjęcie z brzegu Supraśli, opcjonalnie).

### OD-021 · P2 · PC / grafika — cienie drzew za kartami LOD1
- **Pytanie:** Czy drzewa dalej niż koniec LOD1 (impostory, HLOD lasu) mają rzucać cień na PC?
- **Opcje:**
  - **A — Osobny caster LOD1 tylko dla passu cieni:** cień dalej bez overdraw kart w widoku głównym. Wymaga pomiaru
    na klasie GTX 660.
  - **B — Wyższy `treeCardLodScale` na PC:** prosty, ale z kosztem kart także w widoku głównym.
  - **C — Zostaje:** pas 30–100 m bez cieni drzew na Medium, mimo deklaracji 100 m w `[PC_TIER]`.
- **Rekomendacja:** A, po OD-001. Brak cieni drzew w średnim planie widać na każdym kadrze korytarza.
- **Źródło:** `docs/adr/0269-tiery-grafiki-pc.md:137`; `docs/reports/FIX-2026-11-16-pc-shadows-s23.md:30-34`.
- **Zdjęcia / pomiar właściciela:** pomiar na sprzęcie klasy min.

### OD-022 · P2 · prawo — adres bazy pochodnej ODbL (R-P0-2)
- **Pytanie:** Gdzie publikujemy dane pochodne z OSM (graf dróg, pliki `.bytes` nawigacji) wymagane przez ODbL przed
  publicznym wydaniem?
- **Opcje:**
  - **A — Publiczne repo (D18) / katalog w wydaniu:** adres w ekranie „Informacje” i `attributions.txt`. Bramka
    `--release` się odblokowuje.
  - **B — Osobna strona projektu:** niezależna od repo, wymaga utrzymania.
  - **C — Najpierw opinia prawna:** zgodnie z „Opinia prawna dot. ODbL” z `docs/11` Otwarte. Wydanie publiczne czeka.
- **Rekomendacja:** A, a opinię prawną (C) zostawić przed sprzedażą. Repo i tak jest publiczne, a bloker dotyczy tylko
  wydania.
- **Źródło:** `docs/adr/0271-dystrybucja-pc.md:22,60`; `docs/owner/ATTRIBUTION-SCREEN-DRAFT.md:22,91`;
  `docs/11_DECYZJE_WLASCICIELA.md:27`.
- **Zdjęcia / pomiar właściciela:** nie.

---

## P3 — kosmetyka lub odległy etap

### OD-023 · P3 · świat / C — maszty wieżowca Andersa 38
- **Pytanie:** Co z masztami bez potwierdzenia: środkowym (10–12 m ESTIMATED, brak na Mapillary 2020) i narożnika S
  (6,5 m, brak na 073045 i ortofoto)?
- **Opcje:**
  - **A — Usunąć maszt S, środkowy zostaje:** środkowy widać na kadrze 115626, S nie ma żadnego potwierdzenia.
  - **B — Oba zostają:** stan obecny, ESTIMATED.
  - **C — Nowe kadry Mapillary / Panoramax 2023+:** decyzja po przeglądzie. Właściciel nie robi zdjęć (D43).
- **Rekomendacja:** A, bo „nie zmyślaj”: zostaje tylko to, co widać na zdjęciu.
- **Źródło:** `docs/adr/0200-wiezowiec-nw-pasma-maszt-srodkowy-przybudowka.md:29-32,114-116`.
- **Zdjęcia / pomiar właściciela:** nie (D43).

### OD-024 · P3 · świat / pierścień — latarnie w Mońkach
- **Pytanie:** Czy D65 p.8 (białe LED) obejmuje też Mońki (`lamp_policy: led`)?
- **Opcje:** **A — LED jak trasa DK65:** jednolicie z korytarzem. · **B — Reguła domyślna:** sód / generator.
  · **C — Wg kadrów Mapillary:** per ulica.
- **Rekomendacja:** A, potem korekta wg C przy szlifie. W lecie za dnia różnica jest niewidoczna, a jednolitość ułatwia
  dane.
- **Źródło:** PR #115 `docs/adr/0231-…:72-74`; D65 p.8.
- **Zdjęcia / pomiar właściciela:** opcjonalnie.

### OD-025 · P3 · świat / C — 4000 K LED na ulicach C z K69
- **Pytanie:** Czy globalne `k_Led` 4000 K (D68 p.3 dotyczy tylko Knyszyna) stosować także na Andersa, Maczka
  i Al. Tysiąclecia, gdzie podaje je K69?
- **Opcje:** **A — Tak, na ulicach z K69:** zgodnie z researchem. · **B — Bez zmian w C:** obecne barwy zostają.
- **Rekomendacja:** A. Źródło K69 istnieje, a zmiana dotyczy tylko nocy.
- **Źródło:** `docs/adr/0216-lato-i-biale-led-dk65-knyszyn.md:121-123`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-026 · P3 · świat / DK65 — plac budowy DK65
- **Pytanie:** Jaki materiał (piasek / kruszywo / pierwsza warstwa asfaltu), po której stronie, z płotami czy bez,
  i czy są latarnie w Kozińcach?
- **Opcje:** **A — Zdjęcie właściciela ze Studziennej / DK65:** rozstrzyga wszystko naraz. · **B — Zostaje `road_gravel`
  bez płotów:** WORKING_VALUE (D64: „uproszczona strefa”).
- **Rekomendacja:** A, gdy właściciel będzie przejeżdżał. Do tego czasu B, bo D63 każe najpierw zrobić z grubsza.
- **Źródło:** `docs/adr/0215-d65-elcka-6p9-i-jezdnia-w-budowie-dk65-05.md:94-95`; `docs/adr/0214-korytarz-dk65-kafle-06-11-place-budowy.md:121-122`.
- **Zdjęcia / pomiar właściciela:** tak (A).

### OD-027 · P3 · świat / DK65 — szerokości w Fastach i na moście
- **Pytanie:** Czy Fasty S (6,5 m z BDOT) i most na Supraśli (7,5 m) zostają, czy mierzymy je ortofoto?
- **Opcje:** **A — Pomiar `ortho_xsec`:** jak przy K1. · **B — Zostaje BDOT:** niska pewność.
- **Rekomendacja:** A. Pomiar jest tani, a skok szerokości 6,5 → 7,5 → 6,6 m widać przy jeździe.
- **Źródło:** `docs/adr/0207-korytarz-dk65-kafle-02-05.md:124`; `docs/adr/0215-…:100`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-028 · P3 · świat / kolej — barwa podsypki
- **Pytanie:** Czy przyciemnić podsypkę toru do proporcji z ortofoto (tor / asfalt 0,44 zamiast 0,81–0,83)?
- **Opcje:** **A — Wg ortofoto 0,44:** pomiar z danych. · **B — Zostaje:** WORKING_VALUE. · **C — Zdjęcie właściciela.**
- **Rekomendacja:** A. To pomiar, a nie gust.
- **Źródło:** `docs/adr/0217-torowisko-i-przejazdy-kolejowe.md:217`.
- **Zdjęcia / pomiar właściciela:** opcjonalnie.

### OD-029 · P3 · UI / PC — kierunkowskazy w HUD na monitorze
- **Pytanie:** Czy na PC w HUD ma być wskaźnik kierunkowskazów (strzałki), czy tylko w kabinie 3D?
- **Opcje:** **A — Kontrolka w klastrze 2D:** czytelne w widoku zewnętrznym. · **B — Tylko kabina 3D:** bez zmian.
- **Rekomendacja:** A. W kamerze zewnętrznej gracz nie widzi zegarów kabiny.
- **Źródło:** `docs/adr/0265-hud-ui-pc.md:66-67`; `docs/reports/FIX-2026-11-15-pc-fix-s23.md:87`; `docs/reports/REVIEW-2026-11-15-s22-code-131.md:51-52`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-030 · P3 · UI / audio — suwak „Silnik”
- **Pytanie:** Suwak „Silnik” nie ścisza opon ani wiatru. Wystarczy podpis, czy potrzebny jest osobny kanał „Pojazd”?
- **Opcje:** **A — Podpis „Silnik (bez opon i wiatru)”:** natychmiast. · **B — Osobny kanał „Pojazd”:** po odsłuchu.
- **Rekomendacja:** A teraz, a B po odsłuchu właściciela (OD-043).
- **Źródło:** `docs/adr/0270-menu-ustawien-pc.md:96`; `docs/reports/REVIEW-2026-11-15-s22-code-136.md:52`;
  `docs/reports/FIX-2026-11-15-pc-fix-s23.md:91`.
- **Zdjęcia / pomiar właściciela:** odsłuch.

### OD-031 · P3 · UI / sterowanie — okienka lusterek
- **Pytanie:** Czy okienka lusterek zostają obok zestawu wskaźników (ADR 0079) i w rozdzielczości 168 px (0,60 teksela
  na piksel)?
- **Opcje:** **A — Zostają:** bez kolizji z przyciskiem deweloperskim. · **B — Przy krawędziach (jak słupki A):**
  kolizja z telemetrią. · **C — Wyższa rozdzielczość `rq_mirror_res 1.33`:** ostrzej, ale drożej.
- **Rekomendacja:** A. Ocena przy feel teście (OD-002).
- **Źródło:** PR #117 `docs/adr/0243-kierownica-270-900-lusterka-okienka.md:81-85,120-121`.
- **Zdjęcia / pomiar właściciela:** ocena na buildzie.

### OD-032 · P3 · start — start 90 m za zaporą
- **Pytanie:** Czy start 90 m za zamknięciem i bufor `BehindClosureM` 25 m (WORKING_VALUE) są w porządku na exe?
- **Opcje:** **A — Zostają:** potwierdzone zrzutami 20/20 + 7 exe. · **B — Dłużej (np. 150 m):** krótkie trasy dk65-09/11
  stracą resztę odcinka.
- **Rekomendacja:** A. Kafle dk65-09 i dk65-11 mają tylko 352 / 378 m trasy.
- **Źródło:** `docs/adr/0262-start-poza-zaporami.md:128-129,134`.
- **Zdjęcia / pomiar właściciela:** ocena na buildzie.

### OD-033 · P3 · świat / C — udział bloków nieocieplonych
- **Pytanie:** Udział bloków nieocieplonych `panel_concrete` 30 % nie ma źródła (w próbie M53 było 0 z 9). Co z nim robimy?
- **Opcje:** **A — Policzyć na kadrach Mapillary trasy C:** wartość z próby. · **B — Obniżyć do ~10 %:** bliżej M53,
  ESTIMATED. · **C — Zostaje 30 %.**
- **Rekomendacja:** A. Wymóg „nie zmyślaj”, a liczenie jest tanie.
- **Źródło:** PR #123 `docs/adr/0238-typologia-zabudowy-bialegostoku.md:70`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-034 · P3 · świat / C — E-14 za Putry i zieleń tablic
- **Pytanie:** Czy postawić E-14 za rondem Putry bez znanych kilometrów i czy zmienić zieleń tablic (0,112,72) na
  wartość z tolerancji Dz.U.?
- **Opcje:** **A — E-14 nie stawiamy do kadru z bliska, zieleń (0,120,90):** zgodne z „nie zmyślaj” i z tab. 1.3.
  · **B — E-14 bez kilometrów, zieleń bez zmian.**
- **Rekomendacja:** A.
- **Źródło:** `docs/adr/0236-drogowskazy-trasy-c-wg-normy-i-r2.md:90-91,98`; `docs/owner/BACKLOG-S21.md:49` (B-026).
- **Zdjęcia / pomiar właściciela:** nie.

### OD-035 · P3 · światło — noc
- **Pytanie:** Czy noc zostaje z kompensacją −0,405 EV (czytelne lampy) i zegarem `LP_Night` 22:00 (biura 0,05)?
- **Opcje:** **A — Zostaje:** wygląd przeglądowy. · **B — −3 EV (fizyczna auto-ekspozycja):** lampy +32 %, przepalenia.
- **Rekomendacja:** A. D51 każe dopracować światło później.
- **Źródło:** `docs/adr/0199-kalibracja-zmierzchu-i-nocy.md:75-76`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-036 · P3 · wydajność / A16 — warianty profilu Low
- **Pytanie:** Czy zmieniać widoczne parametry Low na A16 (skala renderu, LOD bias, far clip) po A/B z 0241?
- **Opcje:** **A — Odłożyć do wersji telefonowej:** D73: telefon drugorzędny. · **B — Pomiar i zmiana teraz.**
- **Rekomendacja:** A.
- **Źródło:** `docs/adr/0241-gpu-ab-a16-low.md:125-127`; D50, D73.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-037 · P3 · build / PC — ustawienia playera Windows
- **Pytanie:** Mono czy IL2CPP na wydanie, `fullscreenMode` i domyślna rozdzielczość, ikona i nazwa produktu, wpis
  batchingu Standalone (etykieta `-dirty`)?
- **Opcje:** **A — Mono do testów, A/B IL2CPP przed wydaniem, wpis batchingu do ProjectSettings teraz.**
  · **B — IL2CPP od razu:** dłuższe buildy.
- **Rekomendacja:** A. Etykieta `-dirty` przy każdym buildzie myli identyfikację exe.
- **Źródło:** `docs/adr/0261-build-windows.md:91-92,96,98`; `docs/adr/0271-dystrybucja-pc.md:62`;
  `docs/reports/INTEGRATION-2026-11-15-int-pc-s23.md:155`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-038 · P3 · prawo — Mapillary, BDL, dane Miasta
- **Pytanie:** Czy przed sprzedażą zlecić opinię prawną dla Mapillary §12, BDL cz. V lit. b i zarządzenia 973/21
  (`LEGAL_REVIEW_REQUIRED`)?
- **Opcje:** **A — Tak, razem z ODbL przed sprzedażą:** jedna opinia. · **B — Ograniczyć do referencji poza buildem:**
  stan obecny, bez opinii.
- **Rekomendacja:** A, ale dopiero przed Etapem 8. Teraz te dane służą tylko jako referencje.
- **Źródło:** `docs/adr/0230-legalnosc-atrybucje-dane-miasta.md:53,64-67`; `docs/adr/0242-dojlidy-rozpoznawalnosc-wysokosci-z-nmpt.md:86`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-039 · P3 · biznes — dystrybucja PC i DLC
- **Pytanie:** Kanał dystrybucji PC, model DLC (płatne / darmowe / cross-buy), mody i zakres wersji telefonowej?
- **Opcje:** **A — Decyzja przed Etapem 8:** kod trzyma tylko `entitlementId`. · **B — Teraz:** wpływa na format paczek
  (#112) i DRM.
- **Rekomendacja:** A, zgodnie z `docs/11` Otwarte („przed Etapem 8”).
- **Źródło:** `docs/10_ARCHITEKTURA_I_DLC.md:72-85`; `docs/adr/0266-bramki-budzety-pc.md:66-67`; `docs/11_DECYZJE_WLASCICIELA.md:24`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-040 · P3 · marka — nazwa gry i TRAKT
- **Pytanie:** Kiedy sprawdzamy znak TRAKT (EUIPO / UPRP) i ustalamy nazwę gry?
- **Opcje:** **A — Przed publikacją (Etap 8).** · **B — Teraz:** zmiana nazwy później byłaby droga (logo, badge na piaście D19).
- **Rekomendacja:** B, jeśli zajmie mniej niż godzinę (bezpłatne wyszukiwarki). W przeciwnym razie A.
- **Źródło:** `docs/11_DECYZJE_WLASCICIELA.md:23,34` (Otwarte, D17).
- **Zdjęcia / pomiar właściciela:** nie.

### OD-041 · P3 · proces — zamknięcie zastąpionych PR
- **Pytanie:** Czy zamknąć #93 (po scaleniu `putry-ring-0198b-rebased`), #106 (zastąpiony #143), #100 (Codex refs, WIP)
  i #92 (FIX bez wykonawcy)?
- **Opcje:** **A — Zamknąć #93 i #106 po scaleniu następców, #100 i #92 zostawić do powrotu Codex / Mistral.**
  · **B — Zamknąć wszystkie cztery teraz.**
- **Rekomendacja:** A.
- **Źródło:** `docs/reports/PR-TRIAGE-2026-11-16-s23.md:102`; `HANDOVER.md:261,265`; stan PR z API (wszystkie cztery open).
- **Zdjęcia / pomiar właściciela:** nie.

### OD-042 · P3 · proces / dysk — sprzątanie poza projektem
- **Pytanie:** Czy właściciel przegląda `.codex` (140 GB), wyłącza hibernację (25,5 GB), odinstalowuje Unity 6000.6
  (15 GB), przegląda `lw-wt-*` (~100 GB) i czy przyjmujemy zasadę „najwyżej 3 worktree z `Library`”?
- **Opcje:** **A — Tak, zasada §6 raportu + przegląd pozycji 1, 3, 9, 10.** · **B — Tylko zasada worktree.**
  · **C — Bez zmian.**
- **Rekomendacja:** A. Dysk zapełniał się ok. 340 GB w 4 h przy 5–6 ciężkich worktree.
- **Źródło:** `docs/reports/CLEANUP-2026-11-15-s23.md:171-204,206-212`.
- **Zdjęcia / pomiar właściciela:** nie.

### OD-043 · P3 · audio — odsłuch A/B silnika
- **Pytanie:** Czy po odsłuchu A/B (ADR 0232, sterowanie fizyką) zostawiamy nagrania ElevenLabs bez zmian, czy
  zamawiamy REGEN (1800 obr/min o oktawę za nisko, crossfade 1200/1500 z jednego nagrania)?
- **Opcje:** **A — Odsłuch na exe, potem decyzja.** · **B — REGEN teraz.**
- **Rekomendacja:** A. To decyzja ucha właściciela (D21).
- **Źródło:** `docs/owner/BACKLOG-S21.md:145` (B-097); PR #107 (scalony, ADR 0232).
- **Zdjęcia / pomiar właściciela:** odsłuch.

---

## Już rozstrzygnięte (usunąć z ADR jako otwarte albo dopisać odsyłacz)

| ADR / plik:linia | Punkt „otwarty” | Rozstrzygnięcie |
|---|---|---|
| `0199-kalibracja-zmierzchu-i-nocy.md:77` | sezon presetu, azymut 300° vs zima | **D68** (1) 300°, (2) lato wszędzie |
| `0216-lato-i-biale-led-dk65-knyszyn.md:119-121` | azymut 311° vs 300° | **D68** (1) zostaje 300° |
| `0216-…:121-122` | lato także w C i Dojlidach | **D68** (2); scalone c-regen-s22 (#120) |
| `0216-…:123` (część Knyszyn) | LED 4000 K | **D68** (3); część „C” → OD-025 |
| `0203-trasa-bialystok-knyszyn-plan-kafli-i-kafel-maczka.md:110-113` | wariant A/B; objazdy budowy | **D65** p.1 (A), p.4 (bez objazdu) |
| `0204-region-knyszyn-miasto-i-wlot-dk65.md:59-62` | rondo DK65 × DW671; budowa | **D65** p.2 (rondo), p.4, p.6 |
| `0204-…:63` | położenie fontanny | `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md` (fontanna posadzkowa w zachodnim parku) + ADR 0227 (#139) |
| `0204-…:95-96` | rondo za małe dla 16,5 m | **D75** (2) + ADR 0218 §5c (rondo kompaktowe, scalone) |
| `0207-korytarz-dk65-kafle-02-05.md:120,127-128` | S19 w Fastach; nowa jezdnia dk65-05 | **D65** p.3 (otwarty), p.6 (nieotwarta) |
| `0207-…:121`, `0214-…:117` | szerokość Ełckiej 7,6 / 6,9 m | **D66** 6,6 m |
| `0214-korytarz-dk65-kafle-06-11-place-budowy.md:121-122` (część) | latarnie na 1392B | **D69** (1) bez latarni; Kozińce → OD-026 |
| `0218-rondo-knyszyn-opaska-dla-naczepy.md:236-238` (część) | materiał opaski; przejezdność | **D71** (2), **D75** (1)(2); pomiar → OD-007 |
| `0217-torowisko-i-przejazdy-kolejowe.md:204-206` | które kafle dostają tor | decyzja lidera wykonana: rail-fix-s21 + rail-dk65-s22 scalone (`HANDOVER.md:213,263`) |
| `0262-start-poza-zaporami.md:136` | dk65-06 start na wlocie ronda | decyzja właściciela 16.11 (`HANDOVER.md:255`), `start_s_m: 340` (`INTEGRATION-2026-11-16-rail-xsec.md:19`) |
| `0272-pobocze-drog-zamiejskich-jako-dane.md:145-169` | szerokość DK65 dk65-06…11 | decyzja lidera: wariant A `dk65-opaska-k1` 7,3 m (`HANDOVER.md:248`), wdrożone |
| `0260-windows-platforma-glowna.md:24` | referencyjny PC i FPS | częściowo **D74** (klasy, FPS WORKING_VALUE); maszyna → OD-001 |
| `0261-build-windows.md:93` | kierownica FFB | ADR 0263 scalony (#132); natywne FFB → OD-014 |
| `BACKLOG-S21.md:114` (B-076) | 270°/900°, lusterka | **D70** |
| `BACKLOG-S21.md:170` (B-112) | ≤ 12 klatek > 40 ms | **D69** (2) |
| `BACKLOG-S21.md:172` (B-114) | „bramka Samsung A = Low” | **D49**, potem **D73** |
| `BACKLOG-S21.md:132` (B-089, część) | azymut zmierzchu | **D68** (1) |
| `BACKLOG-S21.md:110` (B-072 F1) | tolerancja ogranicznika przegubu | **D59** ≤ 3,5° |
| `docs/11_DECYZJE_WLASCICIELA.md:26` | zakup / pożyczenie flagowca | S24+ jest dostępny (D36, `HANDOVER.md:2`), a telefon jest drugorzędny (**D73**) |
| `0201b-…:144`, B-075 | feel test „na telefonie” | **D73** przenosi feel test na PC (`docs/03:95`); termin → OD-002 |

**Decyzje właściciela z HANDOVER bez wpisu w `docs/11`** (proponuję D76–D79):
(1) pierścień #115 wchodzi do d67-full (`HANDOVER.md:265`); (2) start dk65-06 za rondem, ekran przypisań pada zostaje
(wskaźnik/Esc), tempo Fable bez zmian (`HANDOVER.md:255`); (3) targowica Knyszyn = 4 wiaty potwierdzone przez właściciela,
korekta id OSM (`HANDOVER.md:219,255`); (4) decyzja lidera „wierność pomiarowi > ciągłość na szwie dk65-11 | knyszyn-s”
(`HANDOVER.md:250`).
