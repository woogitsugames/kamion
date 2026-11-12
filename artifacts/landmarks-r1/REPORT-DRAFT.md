To jest szkic, nie raport zamkniętej rundy. Końcowy REPORT powstanie po after-budget.

Gałąź gpt-landmarks-r1, baza main 5f2aa277; commit źródeł do uzupełnienia po walidacji.
Remiza: 26 tui Low dostało wspólne gładkie normalne bez zwiększenia ich 552 trójkątów. Trzy iglaki mają ciemniejszą paletę CC0 i szerszy rdzeń; korony nadal proceduralne, więc ocena fotograficzna pozostaje PARTIAL.
Szkło hali ma ciemniejszy dół. W Low overcast lewa góra/dół Y 64,72/66,93 → 59,93/48,86, prawa 68,65/67,72 → 62,65/48,86. High pozostaje trochę jaśniejszy od orientacyjnego celu zdjęcia.
Pas zacieków biegnie od zakrzywionej obróbki, bez nowego materiału; pigment tynku D48 zachowany. Plama przy maszcie jest cieniem flagi, potwierdzonym ablacją i promieniem CPU, a nie błędem albedo.
Model ma 9344/2828/164 → 9584/2818/164 trójkąty. Po wykryciu przekroczenia Low o 32 zmniejszono przekrój rdzeni z 6 do 5 boków, zachowując wszystkie karty igliwia i poziomy korony; nie podniesiono limitu testu.
Pierwsze pełne porównanie: 192 pary, 112 obrazów pikselowo identycznych. Wszystkie kamery Low: draws siatek +0, instancji +0, suma trójkątów +0,0% w estymacie zaokrąglonym do tysiąca. Końcowe after-budget: OCZEKUJE.
Pełny GIS przed korektą budżetu: 493 passed, 2 failed, 1 xfailed. Pierwsza porażka dotyczyła limitu remizy i wymaga końcowego potwierdzenia w test_hero_building; druga to stale fidelity_qa dróg. Wszystkie 7 jego niezgodnych wejść jest nietkniętych od bazy, co dokumentuje stale-fidelity-proof.json.
Test remizy z kontrolą całego LOD1 przed regeneracją: 7/7; dwa pliki po regeneracji: OCZEKUJĄ NA HEAVY. EditMode: 261/261. Bez telefonu i bez deklaracji wyniku GPU A16 ani zamknięcia bramki 3.
Świeże 64 wpisy chunków i roads_qa przed korektą były identyczne z baseline. Końcowe potwierdzenie po korekcie: OCZEKUJE. Generator bez fallback=True; 1260,6 s zawiera 775 s pauzy ops-watchdog.
Pary zdjęcie/render do 960 px i pełne arkusze przed/po: docelowo review/after-budget oraz review/after-budget-all. Zdjęcie remizy: Commons 7197, Rakoon, CC0.
Nie zmieniono źródeł dróg, światła, shaderów, plików Claude ani innych dziedzin. Wspólny materials_spec ma zmianę tylko we wpisie fire_station; spodziewany konflikt integracji to ten wpis i wygenerowany spec/GLB remizy. Ogólne wygenerowane różnice zachować jako artefakty i regenerować po integracji, nie scalać szumu innych dziedzin.
Przekazanie: lider integruje gałąź i odtwarza materiały fire_station oraz świat pod slotem heavy, następnie importuje pod slotem Unity. Autor nie scala do main i nie pushuje. Następna runda gpt-landmarks-r2: schody oraz powierzchnie filarów DK8; po backlogu wrócić do organicznej sylwetki iglaków.
