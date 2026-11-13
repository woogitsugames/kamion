# Notatki robocze — p7-signs-2 (aktualizacja 2026-11-13, commit godzinowy #5)

## Zmiany w tym commicie

1. **P7-005 dodany do manifestu** — bramownica PUTRY_W_GANTRY potwierdzona na kadrze Panoramax
   stanton 844e35c7-bcd0-43e7-a8ac-16931cf7e96b z **2019-08-15 17:32:16** (EXIF; GPSImgDirection 113.34°,
   lat/lon 53.159087/23.150860, łącznica Maczka→rondo, jazda E). Nowa data względem G3-P017..P020
   (2019-08-04) — potwierdza istnienie bramownicy 11 dni później. Treści paneli NIECZYTELNE (2560 px,
   kadr z ~30-60 m) → UNVERIFIED; nie zgadywano. Model wizyjny zgłosił strzałki na panelach
   (lewo/prosto/prawo) i sygnalizację na konstrukcji — NIEPOTWIERDZONE, zaznaczono w uwagach.
2. **Przebrany triage Commons 20240530_122501** (poprzednio błąd odczytu): GPS 53.149066/23.156008,
   CC0, DateTimeOriginal 2024-05-30 12:25:02 — pobrany ponownie (thumb 1600px), w kolejce do wizji
   (lokalizacja ~1,1 km SE od ronda — prawdopodobnie poza korytarzami zadania).
3. **Skrypty gotowe**: make_audit.py (samokontrola 20%, seed `Kamion-P7-signs-2026-11-13-v1`,
   random.Random(seed).sample — testy: sha256, rozmiar ≤1600px, status, licencja, spójność url/grupa,
  UNVERIFIED-bez-treści) i make_zip.py (pakuje manifest+README+timeline+sources+notes+audit+files/
   do mistral-p7-signs-2-files.zip). Audit wygenerowany tymczasowo na 5 wierszach (P7-001: OK) —
   do regeneracji po finalnej wersji manifestu.
4. Ograniczenie narzędzia wizyjnego (~20 wywołań na odpowiedź) — kolejne transkrypcje
   (NB wyjazd 07820d85..390ca2c2, WB wyjście 239c71e8..13bb273f, 35224dcb/6fc62548, triage
   Commons 2024/2025: 112303, 103324, 084848, 104925, 094758, 090715, 161011, 113359, 122501)
   w kolejnym etapie; wyniki pójdą do manifestu jako P7-006+.

## Wcześniejsze ustalenia (commit #4, bez zmian)
- Kadry su91 2025-10-03 NIE SĄ na korytarzu DK65 (wieś Grabówka, ul. Jodłowa — polana z krzyżem).
- Seria Commons 2022-10-16 wykluczona (las). Seria Rakoon 2024-05-30 z węzła Jurowce — las/staw, bez tablic.
- P7-004 (SOURCED, CC0): tablica E-1 al. Tysiąclecia ~200 m za rondem, 2024-05-30:
  8 E 67 | Korycin 35 | Suchowola 49 | Augustów 87 | Suwałki 126 | Kaunas 243 (strzałki UNVERIFIED).
- P7-001..003 (Panoramax stanton 2019-09-01, najazd N): bramownica obecna, teksty NIECZYTELNE → UNVERIFIED.
- a68677d0 (2020-11-24): brak bramownicy w kadrze — poza manifestem.
- Kwerendy Commons: DK65 SE brak plików <4 km; Andersa E/DK19 N serie ≥1.7 km od jezdni (niski priorytet).

## Kolejka
- [ ] transkrypcje wizyjne (batch 2): NB, WB, 35224dcb, 6fc62548, triage Commons 2024/2025, 122501
- [ ] ewentualne P7-006+ do build_manifest.py + files/
- [ ] finalny README.md + sources.md (opisać brak zdjęć ulicznych 2025-2026 ronda → stan UNVERIFIED)
- [ ] regeneracja audit_20_percent.json na finalnym manifeście
- [ ] make_zip.py + publikacja ZIP (artefakt) + PR (nie-draft) + surowy git diff --stat
