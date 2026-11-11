# Zadanie dla GPT 6.1 Sol — pakiet S10-C (wieczór 11.11): kolejne rundy po recenzjach

Repo `C:\Users\matma\Documents\Claude\kamion`. Zasady, przygotowanie worktree i Definition of Done jak w `docs/owner/GPT-TASK-02-S10.md` i `GPT-TASK-03-S10.md` (obowiązują w całości). **Każdy worktree z AKTUALNEGO main** (od rana weszło: 0086, 0088, 0098, 0097, 0100, 0101, 0102, 0103, 0104, 0105, 0085 r2, 0106, 0107, 0110, 0113, 0087, 0090 — stare gałęzie są nieaktualne). Szczegóły uwag do każdego strumienia: `docs/owner/GPT-FEEDBACK-S10.md` + wskazana recenzja w `docs/reports/visual/`. Scala lider Claude po `REPORT.md` (pisz REPORT normalnym polskim tekstem ze spacjami — część poprzednich była nieczytelna).

Telefon: tylko lider/agenci Claude (blokada `artifacts/locks/PHONE_RUN` — gdy istnieje, nie startuj Unity). Nowe ważne fakty: A16 = profil Low dla bramki 3 (D49); na Low działają szybkie ścieżki szyby kabiny `_KAMION_GLASS_FAST` (0106) i lasu `ForestFastPath` (0113) — każda zmiana tych shaderów musi trafić także do szybkiej ścieżki. QualityProfile ma migracje 98/106/113 — nowe dopisuj jako kolejne revision, nie nadpisuj.

## Kolejność (priorytety bramki 3 z porównań zdjęcie|render, recenzja `REVIEW-2026-11-11-s10-gpt-JK.md`)

| # | Strumień | ADR | Gałąź | Co (skrót) | Recenzja źródłowa |
|---|---|---|---|---|---|
| 1 | **C r13 światło/post** | 0108 | `gpt-light-r13` | P0 przywróć RCAS na High (ablacja 0,25/0,5/0,75 — asfalt przed kabiną rozmyty −38–40 %); niebo bez chmur i płaska ekspozycja (~32 pary — priorytet nr 1 bramki); cienie przy niskim słońcu; biały lakier aut przepalony; komin pochylony | s10-0088-0098, s10-gpt-JK |
| 2 | **B r3 roślinność** | 0109 | `gpt-vegetation-r3` | trawa/pobocza: „trawnik golfowy” → żółtozielona nierówna z chwastami (~24 pary — nr 2); wariacja w skali metrów; korony Putry za jasne; żywopłoty; sosny „lizak”; tuje Low/High | s10-0088-0098 |
| 3 | **D r2 asfalt** | 0118 | `gpt-surface-wear-r2` | po recenzji 0099 (w toku u lidera, wynik dopiszę do GPT-FEEDBACK): asfalt za jasny i jednolity (~21 par — nr 3), koleiny, łaty, spękania, olej; Low nadal sterylny | s10-gpt-0099 (gdy gotowa) |
| 4 | J r2 side-by-side | 0111 | `gpt-sbs-gate3-r2` | 6 par z błędną pozą + `pose_confidence`; seria przesunięta 3–8 m; horyzont 2948; brak zdjęć na pierwszych ~300 m G3-A; **ponowny render wszystkich par na aktualnym main** | s10-gpt-JK |
| 5 | K r2 kabina/lusterka | 0112 | `gpt-cab-r2` | lusterka przednie/krawężnikowe pokazują wnętrze kabiny z góry; ramię zasłania ~25–30 % szkła; ramka szkła, smuga deski, podłokietnik, zużycie | s10-gpt-JK |
| 6 | L r2 wiadukt DK8 | 0119 | `gpt-viaduct-r2` | schody skarpowe donikąd + przecięte ekranem; filary płaskie jak plastik (rozrzut jasności 9–13 vs 19–24 na zdjęciu); kamera `dk8-east-north` ~497 draws | s10-gpt-HIL |
| 7 | F r2 TRAKT | 0115 | `gpt-truck-paint-r2` | lakier kredowy, dach biały w słońcu, szyba mleczna; DRL przycięty 255 na High; poprawki szyby także w `FragFast` | s10-gpt-0087-0090 |
| 8 | E r8 remiza | 0116 | `gpt-firestation-r8` | świerki ciemne/gęste, gradient szkła łuków, zacieki, plama przy maszcie, tuje Low | s10-gpt-0087-0090 |
| 9 | I r2 meble | 0120 | `gpt-furniture-r2` | podmurówka ogrodzenia za wysoka i płaska, siatka idealnie prosta; „stary betonowy” słup wygląda jak stalowy; tył znaku bez rdzy/brudu; NIE ruszać barier (Claude 0117) | s10-gpt-HIL |
| 10 | H r3 tło | 0121 | `gpt-edge-r3` | tło `edge-east/south` = kilka bloków na pustym polu, droga kończy się barierą bez przedłużenia; kadr z poziomu oczu, gdzie las Pietrasze zamyka horyzont | s10-gpt-HIL |
| — | G R4 osobówki | 0089 | `gpt-car-paint` | W TOKU (brud progów) — dokończyć | s10-gpt-0089 |

**NIE ruszać (Claude w toku):** `tools/worldgen/roads/*`, bariery, krawężniki, oznakowanie (0117 węzły r5); `streetscape/plots.py`, zestawy i geometria budynków, zacieki budynków (0114 zabudowa r7).

## Start każdej sesji (zmień tylko literę/numer)
```
Przeczytaj docs/owner/GPT-TASK-04-S10.md w C:\Users\matma\Documents\Claude\kamion i wykonaj strumień nr 1 (tylko ten). Uwagi szczegółowe: docs/owner/GPT-FEEDBACK-S10.md i wskazana recenzja.
```
Ostatni przydzielony ADR w projekcie: **0121**.
