# Niezależna kontrola przygotowania r3

Recenzent sbs_visual_review, tylko odczyt. Ranking rozdziela historyczny D51 r1, recenzję 0125 i brak własnego renderu r3. Odróżnia dodanie obiektów od czytelności. Generator przygotowuje 18 hipotez C, zachowuje FOV i kierunek/pitch, zapisuje tylko artefakty.

Pierwszy przegląd wykrył dwie luki wrappera: kontrola zgodności importu przed oczekiwaniem na slot oraz brak ścisłego związania planu z wejściami. Poprawiono je przed uruchomieniem. Plan zawiera SHA kamer próbnych; Assert-ProbeInputs porównuje aktualny świat i materiały z importem także po Acquire i po renderze, kontroluje plan, receipt, produkcyjne kamery/referencje i zdjęcia. Plan i receipt są migawkami, wspólny HEAD blokuje mieszanie grup.

Ponowny przegląd: PASS poprawek w sprawdzonym zakresie, bez nowego konkretnego blockera. Recenzent nie uruchamiał generatorów, testu kontraktu ani renderów i nie ocenił świata.

Osobny wykonany przez autora check-provenance.ps1 używa funkcji wyciągniętej przez AST z rzeczywistego wrappera i małych prywatnych plików. Potwierdził akceptację zgodnych wejść i osiem odrzuceń po zmianie pliku; wyniki i SHA wrappera w provenance-contract-results.json. To sprawdza zabezpieczenie przed niezgodnymi wejściami, nie dowodzi poprawnego importu ani klatek Unity. Generacja bazowa jeszcze czeka na heavy.
