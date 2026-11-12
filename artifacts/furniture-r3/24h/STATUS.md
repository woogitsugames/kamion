# Stan furniture r3

Runda2 zamknięta5d7ff5c9, artifacts skopiowane do main:1908 plików,4,249GB,
robocopy exit1. Ta sama lokalizacja worktree, gałąźgpt-furniture-r3 z r2.
Scalono main889201d5 do tej gałęzi, bez merge do main/push.
Konfliktujące generatedJSON/GLB orazprops_meta przyjęto z main do regeneracji.
materials.py iLICENSES zachowują oba addytywne dopiski; fabrykaPBR połączyła się
bez konfliktu. Kod r2 nie wymaga ponownych zmian do rozpoczęcia baseline.

Zakresr3:przystanki,wiaty,kosze,słupki według Mapillary, bez barier drogowych.
Referencje przygotowane w artifacts/furniture-r2/24h/bus-reference-preview,
shortlista zawiera autorów/licencje/hashe. Czerwona wiata przy5802408812
potwierdzona zdjęciami2018 i2024; druga przyFabryceDywanów widoczna w2019.
Brak tagu shelter/bin nie dowodzi braku obiektu; brak widoczności zdjęcia również.

NASTĘPNY KROK:przygotować baseline po merge (cachePBR jeżeli nieaktualny,
build_world w heavyOwner gpt-furniture-r3, import/rendery w UnityOwnergpt-furniture),
potem poprawić największe udokumentowane odstępstwo wiaty. WIP po każdym kroku.

2026-11-12T11:01:04.0365756+01:00: przygotowano helpery r3 z identyfikatorem artefaktówr3 i właścicielemheavy bieżącej gałęzi. Przed baseline sprawdzeniecachePBR:nieaktualnychplikówMedium=0. Baseline kolejnoPBR,world,snapshot,import,220 kadrówclear/overcast. Brak nowych zmian geometrii przed baseline.

2026-11-12T11:02:26.9638208+01:00: korekta pipeline:cachePBRMedium aktualny(0stale), więc wycofano wyłącznie własny oczekujący etapPBR przed rozpoczęciem (PID68624/72788/49776, brak dzieci pracyPython). Nie przebudowywać bez potrzeby. Baseline wznowiony odworld; żaden generator nie był przerwany. Sloty cudzych właścicieli nietknięte.

2026-11-12T11:03:05.7729976+01:00: oprava usunięcia etapuPBR:poprzednia zamiana tekstowa nie pasowała do końców linii. Ponownie zatrzymano tylko własne procesy oczekujące, bez pracyPython, usunięto obie linie etapupbr i jawnie sprawdzono ich brak. Właściwe wznowienie odworld następuje teraz.
