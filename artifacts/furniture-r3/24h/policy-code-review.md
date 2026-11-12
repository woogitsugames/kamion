# Niezależny przegląd poprawki polityki wiat

furniture_review przeczytał własny hook i siedem testów, bez uruchamiania narzędzi obliczeniowych ani edycji. Nie znalazł blokera dla bieżącej ścieżki importu: RegionImporter używa SaveAssets, klonowanie progów i maski cieni jest poprawne oraz idempotentne, a pozostałe prototypy pozostają nietknięte. Game.Editor referencjonuje Game.World, testy referencjonują Game.Editor.

Ograniczenia kontraktu wskazane przez recenzenta:

- To polityka przy zapisie, nie przy budowie danych. Odczyt przed SaveAssets oraz przyszła ścieżka omijająca callback nie zobaczy korekty.
- Wymagana jest obecność generic bus_shelter z odpowiadającą liczbą LOD. Brak dawcy kończy się wyjątkiem zamiast pozostawienia krótkiego fallbacku. Bieżący region zawiera obie rodziny; hook nie jest uniwersalną obsługą dowolnych regionów.
- Walidacja zakłada poprawność zastanej polityki generic; nie jest ogólnym walidatorem dowolnych progów.
- Test rzeczywistego zapisu, wyładowania i ponownego odczytu zabezpiecza trwałość. Normalny import powinien dodatkowo wykazać brak zmian innych polityk.

Rzeczywista próba focused przeszła 7/7; normalny import candidate2 także przeszedł. Audyt `shelter-policy-before2.json` / `shelter-policy-after2.json` porównał polityki, maski cieni, liczby LOD i instancji wszystkich 196 prototypów. Zmieniło się wyłącznie lodEndM nowego wariantu z 30/120 do 60/300 m. To audyt metadanych polityki, nie całego payloadu mesh.

Wyników 236 kadrów iteracji 1 i 118 krótkich liczników Low nie uznaje się za końcowy dowód widoczności ani budżetu. Ponowne kadry i pomiary są wymagane. Estymator Python w roads nie zna nowej rodziny; nie edytowano zakazanego źródła. Końcowy pomiar musi opierać się na faktycznych licznikach Unity, a luka estymatora wymaga jawnego zgłoszenia integratorowi.

Mechanizm callbacku: [dokumentacja Unity 6 OnWillSaveAssets](https://docs.unity3d.com/cn/6000.0/ScriptReference/AssetModificationProcessor.OnWillSaveAssets.html). W repo dowodami działania są rzeczywisty test save/reload i audyt po zwykłym imporcie, nie sama dokumentacja API.
