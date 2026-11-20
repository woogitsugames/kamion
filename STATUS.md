# qa-d94-cli — stan

Zmiany: konfiguracja przekrojów GIS per moduł; route_links używa domyślnego D94 generatora, pomiary nadal 0. Referencje K1/0212 przesuwane o 2 × GAMEPLAY_LANE_WIDEN_M bez zmiany tolerancji.
W toku: pytest dotkniętych modułów i QA obu zgłoszonych szwów; nowe regresje prawdziwych końców oraz progów 0/0,1/0,25.
NASTĘPNY KROK: `Get-Content artifacts/qa-d94-cli/pytest.log -Tail 60`
Unity i przebudów kafli nie uruchamiano; praca wyłącznie w tym worktree, bez push.
