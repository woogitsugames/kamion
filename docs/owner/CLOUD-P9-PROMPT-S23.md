# Zlecenie dla sesji „P” (Claude Pro) — runda 9 (s23, 16.11 wieczór) — do 3 agentów, MODEL: Opus

Wklej do sesji P:
```
Runda 9. Zasady jak dotąd (bez Unity, telefonów i Data/raw; do 3 agentów, Opus; każdy na swojej gałęzi z origin/main; NIE scalasz; raport ≤ 15 linii z komendami i „Gotowe do scalenia po weryfikacji lidera: TAK/NIE”). Runda 8 scalona do main (recenzje #168 #169, szkic ADR D3D11) — dziękuję; P1 przekazane agentom integrującym. Nie dotykaj: generated/*, tools/worldgen/*, Data/Regions/*, game/**.

P25 kontrola jakości researchu Mistrala „pętla S8” (scalony do main: research/mistral-s8-loop-s23/) — gałąź qa-mistral-s8-s23, docs/reports/QA-2026-11-16-mistral-s8.md: wylosuj 25 liczb/faktów (przekroje xsec, węzły, MOP, znaki, cele) i sprawdź każdy niezależnie z OSM API 0.6 / GUGiK WMS / BDOT10k / Dz.U. (tylko te źródła; ZERO Google). Tabela: fakt, wartość Mistrala, twoja wartość, źródło, zgodne TAK/NIE. Ocena: czy można na tym budować kafle (D63) i co trzeba poprawić.
P26 druga recenzja scalonego #171 (D42, physics-determinism-s23, już w main) — gałąź review-171-s23, docs/reports/REVIEW-2026-11-16-pr171.md: zmiana w game/Assets/_Project/Vehicle/Physics/TrailerModel.cs (zahamowane koła naczepy trzymają ugięcie przy momencie napędowym ciągnika) — czy fizycznie poprawna, przypadki brzegowe (cofanie, jazda w dół, hamulec postojowy bez napędu, koło w powietrzu), czy nie ukrywa innego błędu; ScenarioRunner Lazy<Defs> — wątki. Uruchom `dotnet test tools/physics-runner/Tests -c Release` (w pętli ≥ 50) i podaj liczby.
P27 lista testów dla właściciela do następnego buildu PC (gałąź playtest-s23, docs/owner/TEST-GRY-S23.md): krótka, klikalna checklista (≤ 25 punktów) co sprawdzić w nowym exe: pełny ekran / Alt+Enter / okno zmienialne (alt-window), HUD i ustawienia z zakładkami + większe lusterka (#166), Koniec mapy na krawędzi korytarza (#163), ciągła jazda korytarzem, kabina (prawdziwy model), naczepa 7,63 m (skręt na rondzie), noc/zmierzch, dźwięk, -force-d3d11 vs domyślne. Każdy punkt: jak wywołać, czego oczekiwać, co zgłosić (zrzut/Player.log). Wyczytaj z kodu/skryptów (plik:linia w komentarzu HTML).
Na końcu podsumowanie.
```
