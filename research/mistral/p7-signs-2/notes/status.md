# Notatki robocze — p7-signs-2 (FINAL — 2026-11-13)

Dziennik sesji badawczej. Wszystkie pliki robocze (harvesty, skrypty, zdjęcia źródłowe) poza repo — komplet
danych w `mistral-p7-signs-2-files.zip` (manifest, README, sources, timeline, notes, audit + `files/`).

## Commity (gałąź research/mistral-p7-signs-2, od main 8c65107)

1. `d2160a4` — .gitignore + README (szkielet)
2. `15efce1` — sources.md + notes/status.md
3. `3e55e02` — timeline_andersa.md (KOMPLETNY: epoki 2019–2026)
4. `e52a8f0` — manifest v1 (P7-001..004) + notes
5. `4b2dc62` — manifest v2 (P7-005: PUTRY_W_GANTRY potwierdzona 2019-08-15) + notes; skrypty audit/zip
6. `6a70fd3` — manifest v3 (P7-006..009: NB gantries poza G3, PUTRY_W_GANTRY ×2, Maczka W West) + notes
7. `68e5954` — manifest v4 FINAL (P7-010: PUTRY_S_ADVANCE), audit_20_percent.json, README final
8. (ten commit) — sources.md final (triage S-korytarza, praktyki 429/1920px) + notes/status.md final

## Przebieg prac (skrót)

- **Wizja (model obrazowy, ~55 przejść w 4 paczkach):** pytania otwarte (bez szablonów paneli), przejścia
  kontrolne pełnych kadrów + powiększeń. Wzajemnie sprzeczne odczyty → UNVERIFIED z pełną dokumentacją
  (P7-006 „E77 Gdańsk 120" odrzucone; P7-009 trzy sprzeczne transkrypcje odrzucone; P7-010 trzy sprzeczne
  transkrypcje odrzucone). Jedyny SOURCED: P7-004 (Commons CC0, 2024-05-30, podwójny zgodny odczyt).
- **Geotriage korytarzy:** skan 323 plików Commons >2022-07-25 po odległości od osi korytarzy (≤60 m) i od
  ronda (≤900 m) → 40 kandydatów; triage wzrokowy zamknięty — większość poza korytarzami lub bez oznakowania ronda.
- **S-korytarz (najazd południowy):** 5 nowych kadrów Commons 2022-07-25 (181–334 m od ronda) — jedyna
  tablica kierunkowa (132632 → P7-010, treść UNVERIFIED); 132504: zgłoszona „bramownica" NIEPOTWIERDZONA
  (wycinki pełnej rozdzielczości negatywne) — odrzucona.
- **EXIF:** wykryto błędny GPSImgDirection w serii WB 2019-09-01 (14–21° vs trajektoria/azymut 268°) —
  azymuty z Panoramax, udokumentowane (P7-009). Daty EXIF = czas lokalny; przeliczenia CEST→UTC oznaczone.
- **Ograniczenia narzędzi:** analyze_image ~20 wywołań na odpowiedź (budżet planowany w paczkach);
  commons API/upload 429 → backoff 10/20/30 s, pauzy 4–8 s; thumb API czasem 1920 px mimo iiurlwidth=1600
  → dodatkowe przeskalowanie w dół do ≤1600 px.

## Ostateczny stan

- Manifest: **10 pozycji** (P7-001..P7-010), 46 kolumn, UTF-8 BOM, schemat G3 + panoramax_id/sezon/pora_dnia.
- Grupy: PUTRY_N_GANTRY (3), TYSIACLECIA_N_E1 (1, SOURCED), PUTRY_W_GANTRY (3), TYSIACLECIA_NB_GANTRY (1,
  nowa poza G3), MACZKA_W_WEST (1, poza G3), PUTRY_S_ADVANCE (1, nowa poza G3).
- Audit 20%: seed `Kamion-P7-signs-2026-11-13-v1`, 2/10 (P7-001, P7-005), wszystkie testy OK.
- Stan bramownic ronda 2025–2026: UNVERIFIED (brak zdjęć korytarzy ronda 2025–2026 w dozwolonych źródłach) —
  opisane uczciwie w README.

## Dostawa

- ZIP `mistral-p7-signs-2-files.zip` (manifest, README, timeline, sources, notes, audit + files/ 11 zdjęć)
  — publikowany jako artefakt przy PR.
- PR nie-draft do main z opisem po polsku.