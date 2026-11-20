# ADR 0315 — korytarz DK8 na północ: Białystok → węzeł Wasilków → w stronę Korycina

Status: Proposed (agent s8-north-s24, 2026-11-20). Numer wzięty jako następny wolny po 0313 z pominięciem 0314
(zarezerwowany przez lidera dla krywlany-s24) — lider może przenumerować.

Powiązane: D93 pkt 4, D95 pkt 4 (następny region po Krywlanach: S8/DK8 dalej, Wasilków/Korycin), D63 (najpierw przejezdne),
ADR 0203 (siatka 2048 m), 0209 (pin NMT), 0285/0292 (linki i korytarze), 0300 (route_obstacles), 0302 (nawigacja).

## Kontekst
Zlecenie: przedłużyć korytarz `bialystok-s8` o kafle na północ „w stronę Wasilkowa/Korycina”.
**Ustalenie z przypiętego pbf (2026-11-08):** S8 kończy się na węźle Białystok Zachód (`dk8-s8-jeroniki`/`dk65-01`).
Ekspresówka na północ od `dk65-02` (S19 Księżyno – Białystok Północ – Wasilków) ma w OSM `highway=construction`
(siatka (−4,2), (−3,2), (−1,3), (0,3)) — nie ma przejezdnej S8/S19 z korytarza S8 do Wasilkowa. Jedyna przejezdna
droga to **DK8 (ref 8;19, Al. Tysiąclecia Państwa Polskiego → Białostocka)**, wychodząca z kafla C przez jego północny
szew; w Wasilkowie (węzeł bezkolizyjny, koniczyna) DK19 odchodzi na wschód (Sokółka), DK8 idzie dalej na
północny zachód (Korycin, Augustów).

## Decyzja
1. **4 kafle w kolumnie i = 0 siatki ADR 0203** (`tools/worldgen/qa/dk8_north_plan.py`, plan
   `docs/reports/map/dk8_north_plan.{json,png}`; wejścia i wyjścia tras = przecięcia jezdni DK8 z krawędziami kafla
   policzone z przypiętego pbf, te same co w build_region):
   `dk8-wasilkow-01` (0,1), `dk8-wasilkow-02` (0,2), `dk8-wasilkow-03` (0,3, węzeł Wasilków),
   `dk8-korycin-01` (0,4, DK8 wychodzi zachodnim szwem do (−1,4)). Powiat wg udziału powierzchni (PRG): 01 = 2002
   (57,8 %) + 2061, pozostałe 2002. Pin NMT 2025 jak C (ADR 0209), łańcuchowo na północ.
2. **Link `c-dk8-north-to-wasilkow`** (kafel C, `replaces_route` jak `c-andersa-to-wygoda`): trasa C kończy się na
   jezdni DK8 w stronę północy ~330 m przed szwem, a w tym punkcie zaczyna się link `any` `c-dk8-to-maczka` (na zachód);
   dla celu `wasilkow` link zastępuje trasę C i jedzie dalej DK8 do wejścia trasy `dk8-wasilkow-01`.
   Korytarz `bialystok-wasilkow` (cel `-route_to wasilkow`), trip nawigacji „Wasilków (DK8)” (`tools/ui/build_nav_trips.py`).
3. **Katalog:** grupa „DK8 Wasilków”, 4 wpisy po S8.
4. **`gugik_index`:** ponawianie zapytań WFS przy zerwanym połączeniu / przekroczeniu czasu (3 próby, 15/45/120 s);
   warstwa, która nie odpowiada po próbach, jest traktowana jak brak warstwy, ale zapisywana w
   `Data/SourceManifests/<kafel>.gugik-availability.json` → `unavailable_layers` (raport, nie cisza). Przyczyna:
   20.11 warstwa `SkorowidzOrtofomapy2026` dla bbox kafli 01/02 zrywała połączenie przy każdej próbie; ortofoto jest
   tylko referencją (docs/05 §3), NMT/BDOT/LoD z tego nie zależą.

## Konsekwencje / otwarte
- DK8 biegnie 150–300 m od zachodniej krawędzi kolumny i = 0: zabudowa i łącznice po zachodniej stronie drogi są
  ucięte krawędzią kafla (w 01 węzeł z ul. do Dziesięcin częściowo w (−1,1)); widok zastępuje far-field. Kafle (−1,j)
  — później, jeśli właściciel uzna to za widoczne (D63).
- Dalszy ciąg do Korycina: kafel (−1,4) i dalej na NW (DK8 w (−1,5), (−2,6..10)).
- S19 Białystok Północ – Wasilków: po oddaniu do ruchu (nowy pbf) — pętla S8 → S19 → Wasilków.

## Liczby
Uzupełniane w trakcie (STATUS: `docs/status/s8-north-s24-STATUS.md`).
