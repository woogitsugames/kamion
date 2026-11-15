# ADR 0211 — tunel / płyta nad wykopem (OSM `tunnel=yes`): rondo Szymańskiego nad DK8, ściany oporowe wykopu
Status: Proposed (agent world-builder, s20, gałąź `tunnel-0211`, baza main a594ef2aa), 2026-11-15.
Powiązane: ADR 0206 (kafel `bialystok-kleeberga`, `keep_tunnel_cut`, override `bridge` łuków ronda), ADR 0110 (pasy
zieleni scalane z terenem), ADR 0064 (bake oświetlenia gruntu: `bridge` = bryła), ADR 0146 (ściany ramp).

## Kontekst
ADR 0206 przywrócił przejezdność DK8 pod rondem prof. Szymańskiego (teren trzymany pod jezdnią tunelową), ale bez
konstrukcji: wyspa i chodniki ronda były otwarte na wykop, łuki ronda (pomosty) od spodu jednostronne, wykop miał
trawiaste „ściany” z NMT. Pomiary (dev dump, `artifacts/tunnel-0211/probe_*.py`):
- NMT (klasa grunt LiDAR) przechodzi przez całą konstrukcję na poziomie wykopu — w obrysie płyty 75 % węzłów NMT jest
  < 1 m nad jezdnią DK8; wyspa ronda w terenie po conform też jest na dnie wykopu. Powierzchnie na poziomie terenu nad
  płytą (jezdnia ronda, płyty skrzyżowań, chodniki) stoją 5,75–6,2 m nad DK8; skarpy 5,3–5,7 m.
- Ortofoto 2024 0,25 m (`artifacts/tunnel-0211/ortho/rondo_240.jpg`): płyta nad całym skrzyżowaniem, portale przy
  zewnętrznych przejściach, pionowe ściany wykopu (ostry pas cienia) po obu stronach na całej widocznej długości
  (> 120 m od portali), między jezdniami bariera.

## Decyzja
Nowy etap generatora `tools/worldgen/roads/tunnels.py` (wywołany w `build_world` po podporach mostów, przed chunkami
terenu; **zastępuje** `keep_tunnel_cut`). Dla dróg `tunnel` ≠ `no`/`building_passage` (bez service/footway/…):
1. **Płyta**: obrys F = otoczka wypukła pasów jezdni tunelowych od portalu do portalu, do tyłu ścian zewnętrznych
   (tu 1682 m²). Zamknięta bryła w warstwie `bridge` (cień, bake nieba/słońca): wierzch (beton, 0,15 m pod gruntem),
   spód (`bridge_soffit`) na stałym prześwicie nad jezdnią, czoła portali, balustrada stalowa na krawędzi portalu
   (poza jezdniami). Prześwit = min(max(5 percentyl pokrycia − 0,80, 4,70), 5,00) → **4,70 m** (skrajnia pionowa
   4,70 m — rozporządzenie MI z 24.06.2022 w sprawie przepisów techniczno-budowlanych dróg publicznych; paragraf
   UNVERIFIED; grubość 0,80 m WORKING_VALUE).
2. **Grunt na płycie**: wysokość terenu nad F interpolowana (liniowo, poza otoczką najbliższy) z próbek „na poziomie
   terenu” w F + 8 m: pomosty ronda (−0,25 m), inne jezdnie/płyty skrzyżowań (−0,08 m), teren ≥ 4,5 m nad DK8 (górne
   krawędzie skarp); nie niżej niż jezdnia + 4,70 + 0,80; wypełniane tylko węzły poniżej poziomu terenu. Komórki
   terenu 1 m nad F i za ścianami są emitowane jako pas zieleni scalany z terenem (`…:vg`, ADR 0110 — ten sam shader,
   maski i płaszczyzny trójkątów terenu, bez szwu na granicy), węzły terenu pod nim schodzą na dno (jezdnia − 0,35).
   Kolizja trawy (`collision_grass`) nad F i za ścianami (kolizja terenu jest tam obniżona).
3. **Ściany**: zewnętrzne ściany tunelu (dno → spód płyty + 0,3), ściana środkowa między jezdniami (WORKING_VALUE,
   czoła na portalach), **ściany oporowe wykopu** wzdłuż obu zewnętrznych krawędzi DK8 poza portalami wszędzie, gdzie
   skarpa za licem ≥ 1,0 m nad stopą (przerwy ≤ 14 m domykane; ściana przerywa się tylko na drodze zjeżdżającej do
   wykopu). Lico 0,3 m za końcem profilu pobocza (wygładzone: bez uskoków przy zmianie krawężnik/pobocze), prefabrykaty
   `ramp_wall_panels`, tylna ściana (cień na jezdnię), oczep 0,5 m z kapinosem, balustrada 1,10 m tam, gdzie spadek
   ≥ 1 m, opaska betonowa od profilu pobocza do lica, kolizja `collision_fence`. Grunt za oczepem dociągnięty do
   wierzchu ściany (zasyp skarpy wykopu z NMT na 2 m za licem).
4. **LOD terenu ≥ 4 m** (`terrain_lod2` = kolizja terenu): pas do lico + 4,5 m trzymany na dnie
   (`chunks.build_chunks(low_cut=…)`), żeby trójkąt 4 m kolizji nie tworzył niewidzialnej rampy przed ścianą.
5. Łuki ronda nad F tracą `soffit/fascia/parapet/abutment/pier/screen` (niesie je płyta); instancje pod spodem płyty:
   należące do jezdni tunelowej (src łańcucha lub stoją na jezdni/poboczu) — wysokie (latarnie, drzewa, tablice,
   sygnalizatory, słupki znaków) usuwane; pozostałe (wyspa, chodniki) podnoszone o różnicę gruntu; pod pomostem — usuwane.
6. Regiony bez takich dróg (C, Dojlidy, maczka): `plan` → None, `build` → `({}, None)`, nic się nie zmienia (test).

## Budżet (wycinek kafla; A = 0206 r4, B = 0211)
_uzupełniane po r1_

## Walidacja
_uzupełniane po r1_

## Otwarte
- visual-critic nie uruchomiony (subagent nie tworzy subagentów) — do zlecenia przez lidera na `artifacts/tunnel-0211/vqa-*/`.
- Brak oświetlenia tunelu (oprawy) i znaków w tunelu; materiał ścian (prefabrykaty) WORKING_VALUE — brak zdjęć
  z poziomu jezdni.
- LOD2/3 terenu (300–700 m): pas 4,5 m za ścianami na dnie — z daleka cienka linia (1–2 px).
