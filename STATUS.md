# STATUS — D31 nav-golden-s23 (chmura D r8)
- Przyczyna: c-regen3 (#93, ADR 0226 `putry-ring-s-placement`) przesunęła oś krawędzi 157 (pierścień S Putry); skok węzeł→oś 2,900→1,196 m i rzut celu −0,283 m → Δ −1,987 m (zmierzone −1,986) na G04/G05/G24/G29; G26 −1,631; G36 +0,355. Koszt i manewry bez zmian.
- Wzorce `tools/nav-runner/Golden/golden_routes.json` odświeżone (6 × lengthM), dopisek ADR 0168. nav-runner 94/94; pytest navgraph 51 passed / 1 failed (inna przyczyna — dryf FP na końcach łańcuchów, nie Putry).
- NASTĘPNY KROK (lider): `dotnet test tools/nav-runner/Tests -c Release`; po kolejnej przebudowie C: `dotnet run -c Release --project tools/nav-runner/Runner -- --write-golden` i przegląd diffu.
