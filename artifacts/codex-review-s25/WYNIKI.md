# Wyniki recenzji s25

Sprawdziłem 9 scaleń na `main` do `590851327`, poprawki lidera i trzy gałęzie oczekujące. [Pełna recenzja](REVIEW.md)

- **4 ważne i 5 drobnych znalezisk.** W próbie OSM/BDOT liczba części przewodów wzrosła z 3 do 9 przy oczekiwanych 6. W próbie WN audyt zgłosił 2 podłączone wieże, a eksport wyemitował 0 przewodów. Wznowienie fidelity może przedwcześnie oznaczyć kafel jako gotowy. Zachowanie A2C w prepassie jednopróbkowym pozostaje **UNVERIFIED** na GPU.
- Sadowa po poprawce ma 1 koniec zamiast 0 po stronie dk65-05. Odzyskany łańcuch ma **0,04884 m** i trym **0/0**. Osobna próba przy narożniku bbox nadal gubi krótkie cięcie.
- **231/231 GIS PASS**, w tym **62/62** w obowiązkowych zestawach budżetowych. Dodatkowo **7/7** przypadków gałęzi przeszło w pamięci. [GIS](gis-tests.txt) · [Testy gałęzi](probe-branches.txt)
- Obejrzałem istniejące PNG clear/overcast. Bez Unity i nowych renderów, eksportu pełnych kafli, zmian kodu ani wygenerowanych danych. Kompilacja C#/HLSL, przejazd przez szew i pomiar materiałów pozostają **UNVERIFIED**. [HUD i pomnik przed/po](archiwum-przed-po.png) · [Kadry High](archiwum-szew-high.png)
- Zmienione pliki w gałęzi to `STATUS.md`, `REVIEW.md` i `WYNIKI.md`. Dowody są także w nadrzędnym `artifacts/codex-review-s25/`.
- Następny krok lidera: sprawdzić poprawki przęseł, audytu WN i A2C przed falą 15. Do wznowienia fali 14 zweryfikować wpisy sukcesu poprzednich etapów kafla. `git show codex-review-s25:artifacts/codex-review-s25/REVIEW.md`
