Obserwacja źródeł przed świeżym triage (bez zmiany gry)

SkyModel.HorizonColorExposed uśrednia 32 kierunki na wysokości y=0.05 i mnoży przez ekspozycję. EnvironmentLighting przekazuje wynik do _SkyFogColor, WorldAtmosphere.DisplaySkyFog, RenderSettings.fogColor i analitycznych refleksów. Sky.shader ma osobne mieszanie dolnej półkuli i przejścia chmur z _SkyFogColor. Sam obrót foto nie zmienia tego koloru.

Aktualna baza źródeł obejmuje spektralny model 12 pasm i wielokrotne rozpraszanie; komentarz o dawnym zielono-szarym RGB modelu opisuje poprzednią wersję, nie dowodzi ponownego wystąpienia tamtego błędu. Nie zastępować tego modelu kolorem dobranym ze zdjęcia bez ablacji.

Stara para R5 High-sbs-g3-a-2948595898752384.jpg oraz pełny High-clear PNG zostały ponownie obejrzane przez rodzica: szeroki szary pas łączy dolne chmury z linią odległych obiektów; nie widać dawnego ostrego klina. Zdjęcie ma inne warunki i może mieć filtr szyby. Nie jest pomiarem fotometrycznym ani świeżą bazą R6.

Jeśli SkyOnlyNoClouds nadal pokaże pas, kolejna kontrolowana próba może rozdzielić turbidity i visibility, z osobnymi wartościami faktycznego modelu, bez globalnego EV. Obecnie nie dodano tych opcji ani nie wybrano wartości. WorldNoGroundHaze nie zastępuje takiej kontroli.
