# ADR 0317 — przekrój mostu poza obiema jezdniami

Status: Accepted — naprawa zlecona przez właściciela, 2026-11-20, `bridge-kerb-cli`.
Powiązane: ADR 0076, 0117, 0306 (D94).

`network.structure_sides` nadpisywał wcześniejszy przekrój flush/tight pełnym
krawężnikiem i kapą mostu. Kapa jednej jezdni DK8 wchodziła na lewy pas drugiej.
Problem występuje również przy GAMEPLAY_LANE_WIDEN_M=0.

Przekrój BRIDGE używa końcowej osi i `hw_at`, osobno dla L/R każdej jezdni.
Od krawędzi asfaltowej wstęgi do krawężnika zostaje 0,30 m płaskiego asfaltu
(`BRIDGE_CLEAR_M`, GAMEPLAY/WORKING_VALUE, bez deklaracji pomiaru lub normy).
Odległość między równoległymi pomostami tej samej warstwy jest dzielona po połowie;
limit kapy zostawia również bufor 0,30 m. Wygładzanie nie może zwiększyć tego limitu.
Próby gęste co około 0,5 m i minimum w promieniu 4 m chronią odcinki między stacjami.
Podejście sąsiedniego mostu do 12 m od końca tagu bridge uczestniczy w sprawdzeniu,
ponieważ tagi obu jezdni mogą kończyć się w różnych miejscach. 4/12 m to WORKING_VALUE.

Gdy nie mieści się bufor, krawężnik i minimalna kapa 0,05 m, krawędź wewnętrzna
jest płaska. Nie zwężamy pasów ani nie przesuwamy osi, nie stawiamy krawężnika
w nakładających się nawierzchniach. Render, kolizja, kapy i specyfikacja hero używają
jednego profilu. Balustrady/ekrany/ściany z generatora mostu oraz bariery regułowe
nie mogą odtworzyć podniesionej krawędzi flush. Na kapie <0,30 m pomijamy osprzęt
krawędzi, a na kapie <0,90 m barierę drogową (konserwatywne WORKING_VALUE).

Zmiana jest globalna dla mostów. Wymaga regeneracji kafli i zależnych assetów hero,
jeżeli zmieni się hash specyfikacji. Walidacja tej gałęzi jest bez Unity i bez
build_world; raport: [bridge-kerb-cli-s24](../reports/bridge-kerb-cli-s24.md).
