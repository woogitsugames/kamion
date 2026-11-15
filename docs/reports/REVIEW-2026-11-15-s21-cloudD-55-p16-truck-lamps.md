# Przegląd PR #55 — M59/P16 lampy ciężarówki (wersja pierwotna) — s21 cloud D, 2026-11-15

**Werdykt: ZAMKNIJ — zastąpiony przez PR #92.** #92 (`research/mistral-p16-truck-lamps-fix-s21`) zawiera wszystkie 7 commitów #55 (głowa `73ccbe930`) i dokłada FIX: przeklasyfikowanie kadrów, erratę E1–E9 i nowy audyt. Scalenie #55 wprowadziłoby do repo tezy obalone w przeglądzie s20, m.in. „13 kadrów z lampką nad tablicą” i „zespoły 3-komorowe z gładkim kloszem” na kadrach, na których tyłu pojazdu nie widać. Nic z #55 nie przepada, bo fotometria jest w #92 bez zmian merytorycznych.

- Gałąź `origin/research/mistral-p16-truck-lamps` @ `73ccbe930`. Ostatnia aktualizacja PR: 2026-11-14 16:39. Baza `b67b949d8` jest 711 commitów za `origin/main`.
- `git diff --stat origin/main...` daje 5 plików, wszystkie w `research/mistral/p16-truck-lamps/` (README, manifest 106 wierszy, sources, audit, `.gitignore`) ✓.
- Wcześniejsze przeglądy: `REVIEW-2026-11-14-s20-mistral-m59.md` (FIX) i `REVIEW-2026-11-15-s20-mistral-m59-fix.md` (#92, FIX r2).

## 1. Kompletność (MISTRAL-TASKS-9 §M59)
| Kryterium | #55 | Stan w #92 |
|---|---|---|
| Fotometria R148/R150/R48 z cytatami | TAK (71/78 cytatów dosłownie, s20) | to samo, plus errata E1–E9 |
| Budowa lamp z kadrów | NIE (tezy bez pokrycia w obrazach) | wycofane, UNVERIFIED |
| ≥ 15 zbliżeń ECE + ≥ 5 lampek tablicy | NIE (3 kadry ECE, 0 lampek ciężarówek) | NIE (bez zmian) |
| Licencje, Google | kadry OK; karty producentów w ZIP (niewidziane) | `files/` bez kart ✓ |
| Tylko własny katalog | TAK | TAK |

## 2. Obrazy i liczby
- Kadry #55 i #92 to te same pliki Commons (P16-201…223). Obejrzałem **12 z nich** (201, 202, 204, 205, 206, 208, 209, 212, 216, 218, 219, 221; szczegóły w raporcie #92 §2). **Opis z #55 (kolumna `wartość`) zgadza się z obrazem w 2 z 12** (218 i częściowo 219). Przykłady niezgodności: 201 i 202 to lampy L konceptu, a nie „zespół 7-komorowy pionowy”; 208, 209 i 212 to okrągłe lampy USA; 206 ma klosz z optyką, a nie gładki. To potwierdza wynik s20, który objął 23 z 23 kadrów.
- Licencje: 8 z 8 sprawdzonych dziś przez Commons `extmetadata` (CC0, CC BY, CC BY-SA 3.0 pl / 4.0) zgadza się z manifestem.
- Liczby: 7 cytatów R148 i R48 sprawdziłem dosłownie w Cellar XHTML PL (P16-020, 030/031, 032, 033, 035, F1 i 5.9.2, 5.11.3, R48 2.11.1.3). Wynik 7 z 7 ✓ (tabela w raporcie #92 §3). Errata E1–E9 jest wprowadzona tylko w #92.

## 3. Wnioski dla gry
Tylko przez #92 (raport #92 §4): stop : pozycyjne w `TruckLights.cs` daje 15,4 : 1 (≥ 5 : 1 ✓). Bursztyn `(1, 0.28, 0)` leży poza obszarem R48 §2.11.1.3, a cały ten obszar leży poza gamutem sRGB. Do poprawy jest podstawa w ADR 0178. Z #55 nie wynika nic ponad #92.

## 4. Dla lidera
- **Zamknąć PR #55 bez scalania**, z komentarzem „zastąpiony przez #92”. Gałąź można usunąć po scaleniu albo zamknięciu #92, bo jej commity są w historii #92.
- Bloku FIX dla #55 nie ma, bo poprawki idą do #92 (blok r2 w raporcie #92 §6).
