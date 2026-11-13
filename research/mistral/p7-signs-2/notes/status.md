# Notatki robocze — p7-signs-2 (aktualizacja 2026-11-13, commit godzinowy #4)

## Korekty i nowe ustalenia (od commitu #2)

1. **Kadry su91 2025-10-03 NIE SĄ na korytarzu DK65.** Geotag: 53.13650/23.24966 — wieś Grabówka
   (gmina Grabówka), ul. Jodłowa; model wizyjny potwierdza: polana z krzyżem i kamieniem pamiątkowym,
   zero elementów drogowych. Wcześniejsza etykieta "Grabówka DK65" była błędna (wieś Grabówka ≠ osiedle
   Grabówka przy DK65 w Białymstoku). **Brak zdjęć korytarzowych 2025/2026 na DK65/DK19/DK8 utrzymuje się.**
2. **Seria Commons 2022-10-16 wykluczona** — ścieżki leśne (model wizyjny: las, brak jezdni).
3. **Seria Rakoon 2024-05-30 z węzła Jurowce/Wasilków (DK8 N, 18 plików CC0)** — po triage: zdjęcia
   przyrody/leśne, bez tablic. Wykorzystana do weryfikacji pokrycia korytarza DK8 N.
4. **NOWA obserwacja P7-004 (SOURCED, CC0):** tablica E-1 na al. Tysiąclecia ~200 m za rondem Putry
   (geotag 53.16095/23.15193), data 2024-05-30 12:26:44 (DateTimeOriginal = nazwa pliku — zweryfikowane):
   "8 E 67 | Korycin 35 | Suchowola 49 | Augustów 87 | Suwałki 126 | Kaunas 243".
   Strzałki rozbieżne między odczytami (prosto vs w prawo) → UNVERIFIED. Pierwsza w pełni czytelna
   tablica korytarza DK8 N z 2024 w dozwolonym źródle (G3 nie dokumentował tego miejsca).
5. **Kadry Panoramax 2019 bramownic ronda:** obecność konstrukcji potwierdzona na najazdzie północnym
   (8176a172/74817897/d0fe5072), teksty paneli NIECZYTELNE → manifest P7-001..003 (UNVERIFIED).
   Liczba paneli w odpowiedziach modelu mogła być sugerowana szablonem pytania → liczba paneli UNVERIFIED.
6. **a68677d0 (2020-11-24, Maczka WB):** brak bramownicy w kadrze — spójne z geometrią
   (bramownice Maczka W leżą za kamerą na tym azymucie). Nie wchodzi do manifestu.
7. **Kwerendy geosearch Commons poza rondem:** DK65 SE — brak plików <4 km od korytarza;
   Andersa E / DK19 N — serie z 2023-2024 w odległości ≥1.7 km od jezdni (zawansowane do triage, niski priorytet).

## Manifest v1 (ten commit): P7-001..P7-004 (46 kolumn = schemat G3 + panoramax_id/sezon/pora_dnia)

## Kolejka
- [ ] dokończyć triage Commons 2024/2025 (112303, 103324, 084848, 104925, 090715, 161011...)
- [ ] NB wyjazd z ronda (07820d85..390ca2c2): czy jest bramownica/tablice po rondzie N
- [ ] łącznica Maczka→rondo (844e35c7, 35224dcb, 6fc62548): wycinki górnej połowy — bramownica PUTRY_W_GANTRY?
- [ ] 122501 (błąd odczytu pliku — ponowić)
- [ ] audit_20_percent.json (seed: Kamion-P7-signs-2026-11-13-v1) po finalizacji manifestu
- [ ] ZIP (python zipfile) + artifacts publish + README final + PR
