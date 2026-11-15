# Przegląd M57-FIX p14-office-tower (chmura B, PR #88) — s20, 2026-11-15

**Werdykt: SCAL, ale tylko przez checkout katalogu (§4); PR #56 zamknąć jako zastąpiony.** Wszystkie 12 punktów M57-FIX (`docs/owner/MISTRAL-FIXES-12.md`) zostały wykonane. Opisy, które sprawdziłem, zgadzają się z obrazem. Status NE i koloru SE pozostał uczciwie UNVERIFIED albo oznaczony jako konflikt źródeł.

- Gałąź `origin/research/mistral-p14-office-tower-fix-s21` @ `bfcb1d42d`. Wychodzi z głowy #56 (`502d574e9`), **bez rebase na main**. Względem #56: 22 pliki, +244/−158, tylko `research/mistral/p14-office-tower/`. Względem main pełny diff ma 1506 plików i −776 554 wierszy, a to są zmiany main nowsze niż baza gałęzi.
- Manifest ma 19 wierszy: SOURCED 11, UNVERIFIED 7, ESTIMATED 1. Audyt: seed 20261115, 6/19 (31,6 %), w tym 5 kadrów z wieżą, 4 PASS / 2 FIX.
- Licencje: Commons CC0/CC BY, KartaView CC BY-SA (referencja), GUGiK, OSM, UKE. Google nie użyto ✓. Napis firmowy na szczycie jest oznaczony „nie odtwarzamy” ✓.

## 1. Punkty M57-FIX
| # | Wymóg | Wynik |
|---|---|---|
| 1 | każdy kadr osobno, bez szablonów | **TAK**: P14-002…006 mają teraz osobne opisy |
| 2 | reguła strony ściany | **TAK**: jest w README razem z φ |
| 3 | 073045 = szczyt SW + ściana NW | **TAK**: φ ≈ 224°, ok. 125 m (ESTIMATED); drabinę usunięto; klimatyzatory pod oknami kolumny; płot z graffiti |
| 4 | NW = 6 grup pasmowych | **TAK**: 6 grup × 5–6 świateł; ułamki ESTIMATED. Wycinki zrobione z 3840 px zamiast 4608 (oryginał zwracał 429; uczciwie opisane) |
| 5 | ortofoto | **TAK**: cienie na NW, 4 podstawy X, przybudówek SE (P14-019); teza o nadbudówce usunięta |
| 6 | KV 993062122 i 1326673613 to fałszywe negatywy | **TAK**: SE opisana, 2 maszty kratowe, panele |
| 7 | KV 14055, kurs 123° | **TAK**: kurs z toru; zbiornik = OSM way/279896715 `man_made=gasometer` |
| 8 | maszty | **TAK**: 0,49 i 0,88 długości, 3–4 krótkie przy NE; obliczone 9–12 m (ESTIMATED) |
| 9 | parter | **TAK**: parter wieży UNVERIFIED, „witryny” należą do hali giełdy |
| 10 | audyt | **TAK**: nowy seed, stare „zaobserwowano” usunięte |
| 11 | pliki | **TAK**: pliki są w gałęzi (≤ 1600 px, `git add -f`), więc ZIP nie jest potrzebny |
| 12 | luki | **TAK** |
| — | „dopisz do #56, rebase na main” | **NIE**: powstał nowy PR na starej bazie (uzasadnione w opisie PR) |

## 2. Co obejrzałem sam (4 pliki, pojedynczo)
| Plik | Ocena |
|---|---|
| `20200711_073045.jpg` | ✓ Szczyt z napisem i kolumną okien jest po prawej, długa ściana z poziomymi pasmami po lewej (NW), po prawej niebo. Klimatyzatory przy oknach kolumny. Na pierwszym planie płot z graffiti. Jeden wysoki maszt kratowy w lewej części dachu |
| `20210328_115626_crop_tower.jpg` | ✓ NW frontalnie: na każdej kondygnacji 6 grup pasmowych. Wysoki maszt w ok. 0,5 długości i maszt przy prawym (SW) końcu. Krótsze maszty z panelami przy lewym (NE) końcu. Na pierwszym planie namioty giełdy |
| `kv_1326673613_crop_tower_x3.5.jpg` | ✓ Szczyt SW z napisem po lewej, SE po prawej. Przy narożniku S krótka grupa okien, przerwa, dłuższe pasmo. Odcień SE taki sam jak szczytu. 2 maszty kratowe, białe panele |
| `orto_tower_80m.jpg` | ✓ Cień budynku i masztów pada na NW. Widać jasną ścianę SE. 4 kratowe X na dachu. Przybudówek przy środku SE, niebieskie elementy, korytka wzdłuż osi |

## 3. Liczby
- Maszty 9–12 m: obliczenie (podziałka kondygnacji + poprawka na attykę) jest w README. Status ESTIMATED jest właściwy.
- Ułamki grup NW ESTIMATED, liczba grup SOURCED (3 kadry). Zgodne z moim oglądem 115626.
- Przybudówek SE: ortofoto ok. 5×8 m kontra BDOT 6,3×1,8 m. Konflikt jest pokazany jawnie (UNVERIFIED).

## 4. Integracja (dla lidera)
```
git checkout origin/research/mistral-p14-office-tower-fix-s21 -- research/mistral/p14-office-tower
```
Nie scalać gałęzi wprost: na starej bazie usuwa ok. 1500 plików main. Pliki `files/` są ignorowane przez `.gitignore:69`, więc po checkout trzeba sprawdzić, czy trafiły do indeksu. Jeśli nie, użyć `git add -f`. PR #56 zamknąć jako zastąpiony przez #88.

## 5. Wnioski dla gry (dach i ściany wieżowca, ADR 0180)
- NW: 6 grup pasmowych po 5–6 świateł na kondygnację, wąskie filary. SW: jedna kolumna z 10 okien + pas szklenia parteru; okładzina ochrowo-musztardowa z pionowym żebrowaniem; białe skrzydła w ciemnoszarym obramieniu.
- SE: przy narożniku S krótka grupa, przerwa, długie pasmo; kolor do wyboru (konflikt źródeł).
- Dach: 4 podstawy X (N, E, środek SE, W z odciągami); maszty 9–12 m w 0,49 i 0,88 długości od NE; 3–4 krótkie przy NE; panele wzdłuż SE; 10–14 niebieskich elementów (wentylatory); korytka wzdłuż osi. Bez napisu.
