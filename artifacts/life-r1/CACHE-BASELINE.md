# Rendery skopiowanego cache main

Katalog main-cache-before zawiera 368 oryginalnych PNG (92 kamery × cztery warunki) wyrenderowanych ze scen skopiowanych z main. Początkowo katalog nazywał się before. Zachowano go bez zmiany plików po wykryciu, że pierwsza regeneracja kandydata R4 zmienia 159 z 192 produktów raw względem zapisanego manifestu.

Sama różnica hashów nie rozstrzyga, które dane są przyczyną (geometria, materiały lub metadane), i nie dowodzi samodzielnie nieaktualności cache. Sprawdzi to osobna regeneracja niezmienionej bazy Main i porównanie z canonical-main-manifest.json. Wcześniejsze określenie starego cache było wstępną hipotezą.

Ten zestaw dokumentuje zastany cache. Nie służy do przypisania kosztu ani wyglądu zmianom osobówek R4. Właściwe porównanie r1 będzie korzystać z kanonicznych katalogów before i after, utworzonych po regeneracji i imporcie obu stanów z tej samej bazy 5f2aa277. Wstępne miniatury baseline-*.jpg w katalogu rundy również pochodzą ze skopiowanego cache.

Dane rozbieżności: raw-vs-main-base.json. Pełny manifest bazy: canonical-main-manifest.json odczytany przez git cat-file; częściowy main-base-manifest.json ze zbytecznego odczytu git show nie jest używany.
