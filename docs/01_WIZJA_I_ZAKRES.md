# 01 — Wizja i zakres

## Fantazja gracza
Siedzę w kabinie nowoczesnej ciężarówki, w prawdziwym Białymstoku. Wyjeżdżam z bazy w strefie przemysłowej, ulice mają prawdziwe nazwy, skrzyżowania i ronda są tam, gdzie w rzeczywistości. Czuję masę zestawu przy ruszaniu, nurkowanie kabiny przy hamowaniu, pracę naczepy na rondzie. Wieczorem zapalają się latarnie, a po deszczu asfalt się błyszczy. Dostarczam ładunek, a potem wyjeżdżam za miasto na trasę.

## Dlaczego ta gra ma sens (pozycjonowanie)
Google Play jest pełen symulatorów ciężarówek, które przegrywają w trzech miejscach. My mamy wygrać we wszystkich trzech:

| Typowa gra truck na Google Play | My |
|---|---|
| Arcade'owa fizyka, „ciężarówka jak osobówka”, brak masy | Własny solver: opony, zawieszenie z kabiną, pneumatyka, retarder, naczepa na siodle, walidowane liczbami |
| Plastikowa grafika, powtarzalne tekstury, generyczne miasta | Spójny art direction, materiały ze skanów CC0 i zdjęć, kalibrowane światło, prawdziwe miejsce |
| Wymyślone mapy albo „Europa” z pudełek | Białystok 1:1 z GUGiK/OSM: prawdziwe ulice, budynki, teren LiDAR |
| Sterowanie dotykowe toporne | Kierownica dotykowa i gyro projektowane i strojone jak element fizyki |
| Natrętne reklamy, pay-to-win | Model premium/DLC (decyzja biznesowa później) |

## Zakres pierwszej wersji (vertical slice)
- **1 ciągnik 4×2** własnej fikcyjnej marki (nazwa do zaproponowania przez sesję, do akceptacji właściciela) z pełną, działającą kabiną.
- **1 naczepa** firankowa (kurtynowa) 13,6 m, pusta i z ładunkiem.
- **Strefa przemysłowa Białegostoku + wylot na trasę**: 2–3 km dopracowane do poziomu „pokazowego”, z bazą/magazynem, skrzyżowaniem, rondem, odcinkiem drogi wylotowej.
- **Jedna pełna pętla zlecenia**: wybór → podpięcie naczepy → jazda → manewr pod rampą → dostawa → wypłata → zapis.
- Dzień + zmierzch, sucho + deszcz (deszcz zmienia przyczepność).
- Sterowanie: kierownica dotykowa + pedały, gyro.
- Kamery: kabina (główna), zewnętrzna, od naczepy (cofanie), lusterka.

## Kolejność rozwoju treści
1. Strefa przemysłowa + wylot (vertical slice)
2. **Cały Białystok 1:1** (dzielnicami, każda przechodzi te same bramki jakości)
3. Obrzeża i wyloty: Wasilków, Choroszcz, Zabłudów, Supraśl, Juchnowiec Kościelny… (1:1 w miejscowościach)
4. Trasy podlaskie (skrócone między miastami): S8, DK8, DK19, DK65, S19… i miasta: Łomża, Suwałki, Augustów, Bielsk Podlaski, Hajnówka, Sokółka, przejścia graniczne
5. Reszta Polski — regionami
6. Kraje jako DLC (naturalny pierwszy kandydat: Litwa przez Budzisko — Via Baltica)

## Poza zakresem (świadomie, na razie)
Multiplayer, modding, edytor dla graczy, licencjonowane marki ciężarówek, monetyzacja/sklep (tylko abstrakcja uprawnień), Android Auto, port iOS (do czasu zielonej pętli zlecenia na Androidzie — ale kod od dnia 1 bez zależności Android-only).

## Czego nie obiecujemy
„Grafiki jak ETS2 na każdym telefonie” ani „całej Polski 1:1”. Obiecujemy: najlepszy spójny obraz, jaki utrzyma dane urządzenie przez 30 minut jazdy, i prawdziwe miasta 1:1 — dodawane stopniowo, bez obniżania jakości.
