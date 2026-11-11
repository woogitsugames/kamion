# S10 C / ADR0098 — zakończone
Gałąź `gpt-light-r12`; zweryfikowany kod `9e7e0b45`, baza `4f7da66c`; main bez zmian źródłowych, bez merge/push.
Świeży build/import, Fab15 bez fallbacku, 192 pliki GLB/instances zgodne z manifestem; snapshot i `final-source-proof.json`.
Dithering nieba przed LUT wyłączony tylko post; końcowy URP pozostaje. High RCAS=0 z jawnym override; Low polityka bez zmian.
Pełna macierz 59 kamer × Low/High × clear/overcast przed i po: `before/`, `after/`; 22 lowsun oraz 6 końcowych Medium dodatkowo.
RMS nieba High 3 px clear 1.827→0.555, overcast 1.198→0.615; końcowa macierz, nie korzystniejszy wynik wybranej ablacji.
Clear shoulder1.2: szczyt domu RGB254.671/243.840/212.340→240.836/229.444/195.223, redp95=241, 0% RGB≥250 w ROI; spełnia przybliżone ~240.
Asfalt High clear RGB103.541/101.891/97.860→103.774/102.114/98.085; overcast luka niebo–droga Low116/High119, zdjęcia116–121.
Bias Med/High0.4/0.3, High kaskady0.20/0.55 bez zwiększania map/liczby; jawny kp_glass_block odbiornik8cm, cast/geometria bez zmian.
Glass: błąd szerokiego trójkąta13.62→1.00LSB vs realtimeOff, rzeczywisty cień ram6.59LSB pozostaje, kontakt naczepy MAXdiff0.
Skala70% proxy: farba edge2.218→2.551px, windowgradient−15%, kontrast cyfry128→126; czytelna, rzeczywista miękkość ujawniona (`floor/`).
Wszystkie 4 `stats.txt` byte-identyczne (236 kamer); Low ma rzadkie różnice krawędzi roślin, bez twierdzenia identyczności PNG (`low-pixel-regression.json`).
Pod mostem świeży sky-vis0.043 vs otoczenie1, model ambient0.330 vs1; istniejące AO/chmury/mgła zachowane, bez nowego algorytmu (`bridge-ambient-proof.json`).
GIS355PASS/2xfail; pełny EditMode221/221 PASS, 0 failed/skipped, w tym9 nowych testów; `EditMode.xml`, `verification.json`.
Macierz używała tego samego cache pojazdu; dopiero potem uzupełniono brakujący ignoredFBX i przebudowano fixture truck/trailer dla zielonych testów.
Obejrzane wszystkie arkusze≤960px i referencje; samokrytyka `SELF-CRITICISM.md`; niezależny root PASS `REVIEW.md`.
KP clear ROI diagnostycznie RGB≥250 1.68→0%; nie zastępuje kalibracji materiału należącej do lidera ADR0101 (`kp-clip-diagnostic.json`).
UNVERIFIED: telefon GPU/termika/deviceEASU; liczby CPU i proxy nie są pomiarem GPU; wymagany końcowy wspólny test integracji A/B/F/lidera.
Konflikty addytywne: `WorldSurface.shader`, mały setter `RegionImporter`, `ProjectSetup` migracja98, `QualityProfile`/`RenderOverrides`; zachowano tile/weather/runoff/macro/panel/splash.
Dowody skopiowane do main `artifacts/light-r12/` przez robocopy `/E /XJ`, bez `/MIR`; canonical `world_manifest.json` pozostawiony lokalnie z odświeżonymi SHA.
