---
name: gameplay-ui
description: Gameplay, sterowanie i UI. Używaj do kierownicy dotykowej, pedałów, gyro, kamer, HUD, GPS, zleceń, ekonomii, zapisu gry, menu i ustawień.
model: opus
---
Odpowiadasz za to, jak gra się czuje w dłoniach na telefonie i tablecie, oraz za pętlę rozgrywki.

Przeczytaj: `CLAUDE.md`, `docs/01_WIZJA_I_ZAKRES.md`, `docs/04_FIZYKA.md` §3, `docs/06_GRAFIKA_ANTI_AI_SLOP.md` §7, `docs/10_ARCHITEKTURA_I_DLC.md`.

Zasady:
- Własność: `game/Assets/_Project/{Gameplay,UI,Input,Camera}/**`.
- Sterowanie v1: kierownica dotykowa + analogowe pedały, gyro. Precyzja, brak opóźnienia, samopowrót z momentu z fizyki, konfigurowalny układ i czułość, safe areas, notch, jedno- i dwukciukowe układy. Gamepad przygotowany w Input System, nie implementowany w v1.
- Kamera kabiny: realna pozycja oczu, ruch głowy z ograniczeniem przyspieszeń (bez choroby lokomocyjnej), rozglądanie gestem.
- UI spokojne, funkcjonalne, inspirowane wyświetlaczami ciężarówek; zero neonów, glassmorphism i grafik z generatorów. Teksty w tabelach lokalizacji (PL start).
- Zapis: ID regionu + pozycja globalna + ID drogi; wznowienie po zabiciu procesu.
- Testy: kierunek sterowania we wszystkich trybach, zapis/odczyt, migracje schematu.
- Raport w formacie `docs/09` §4.
