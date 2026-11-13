# Notatki robocze — p7-signs-2 (aktualizacja 2026-11-13, commit godzinowy #6)

## Zmiany w tym commicie — manifest v3 (9 wierszy, P7-006..009)

Wyniki drugiej paczki odczytów modelu wizyjnego (budżet ~20 wywołań na odpowiedź — wymagane przejścia kontrolne):

1. **P7-006** (7196532e, 2019-08-15 17:32:44, NB za rondem): DWIE bramownice z tablicami w oddali na
   al. Tysiąclecia za rondem (kier. węzeł S8/S19 Jurowce) — **lokalizacja poza manifestem G3, nowa**.
   Pierwsze przejście zgłosiło czytelne treści (E77, Gdańsk 120 km) — odczyty kontrolne ich NIE
   potwierdziły → przyjęto tylko obecność konstrukcji; treści UNVERIFIED. Odrzucone sugestie odnotowano.
2. **P7-007/008** (35224dcb, 6fc62548, 2019-08-15 17:32:20/24): bramownica PUTRY_W_GANTRY nad wjazdem
   Maczka→rondo — obecność potwierdzona z dwóch dodatkowych kątów; treści UNVERIFIED.
3. **P7-009** (13bb273f, 2019-09-01 12:22:51, Maczka W ~530 m za rondem): konstrukcja z tablicami
   obecna; TRZY odczyty wzajemnie sprzeczne (E67/16/Warszawa 43 vs E75/65 Warszawa 155/E77 Gdańsk/8)
   → wszystkie treści odrzucone jako sugestia modelu; obecność = jedyne potwierdzenie.
   Odkryto przy okazji: EXIF GPSImgDirection dla serii WB 2019-09-01 jest błędny (14-21° przy
   trajektorii wyraźnie zachodniej i view:azimuth 268°) — azymut z Panoramax, EXIF odrzucony.
4. Kandrowie negatywni: 239c71e8/781cedd1/0c07d3f9 (WB, brak tablic w kadrach), 07820d85/6ded8ec0/
   a228a704/390ca2c2 (NB, brak tablic w kadrach), 9ff60a64 i 5f92573a (odczyty niejednoznaczne —
   wzmianki w P7-006 i tu), Commons 122501 (geotag 1,1 km SE od ronda, jedna nieczytelna tablica
   przydrożna — poza korytarzami).

## Nowe odkrycie do triage'u (następna paczka): korytarz Tysiąclecia S
Systematyczny skan geotagów Commons (meta/commons_near_new.json) wykazał nietriage'owane serie
NA OSI korytarza Tysiąclecia południowego (dojazd od Centrum):
- 2022-07-25 (Rakoon, 13 plików, 1323-1328xx, lat 53.155-53.157, 180-450 m od ronda),
- 2024-04-01 (10 plików, 1107-1109xx/112303/112827, lat 53.153-53.156, 280-620 m),
- 2024-05-30 122602 (405 m), 2024-06-26 103324 (434 m).
Kandydaci wykluczeni po geotagach: 20241113 104925/094758, 20240219 084848, 20250208 090715,
20241229 113359, 20250402 161011 (wszyscy >400 m od osi korytarzy). Seria 2022-10-16 pozostaje
wykluczona (las, weryfikowane wcześniej); pliki z lat >=53.1586 na osi Andersa E sprawdzić przy okazji.

## Stan prac (bez zmian)
- Skrypty gotowe: make_audit.py (seed `Kamion-P7-signs-2026-11-13-v1`), make_zip.py.
- Po finalnym manifeście: regeneracja audit_20_percent.json, finalny README.md + sources.md, ZIP, PR (nie-draft).

## Kolejka
- [ ] triage S-korytarza (Commons 2022-07-25, 2024-04-01, 122602, 103324) — czy widoczne bramownice/tablice najazdu S ronda
- [ ] ewentualne P7-010+ + regeneracja manifestu/audytu
- [ ] finalny README.md + sources.md (stan 2025-2026 ronda: UNVERIFIED)
- [ ] make_zip.py → mistral-p7-signs-2-files.zip → publikacja artefaktem
- [ ] PR nie-draft do main + surowy git diff --stat
