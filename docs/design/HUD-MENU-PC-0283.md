# HUD, menu i lusterka na PC — projekt (ADR 0283, D84)

Cel: HUD i menu na poziomie gier symulacyjnych ciężarówek, ale **własnym stylem** — bez kopiowania cudzych układów,
ikon, kolorów marek i fontów. Punkt wyjścia to to, czym jest prawdziwy wyświetlacz w ciężarówce: matowy, prawie czarny
ekran w desce, ciepła biel cyfr, kontrolki w kolorach ISO 2575 tylko wtedy, gdy coś znaczą. Kabina jest prędkościomierzem
(żywe ekrany `CabScreens`), ekran ma tylko to, czego z miejsca kierowcy nie widać.

Makiety (rysunki układu, liczone z tych samych liczb co kod; generator `python tools/ui/hud_mockups_0283.py`):

| Plik | Co pokazuje |
|---|---|
| `hud-0283-minimal-16x9.svg` | HUD minimalny (widok zza, graybox bez ekranów kabiny); obrys wolnego widoku drogi |
| `hud-0283-extended-16x9.svg` | tryb rozszerzony (klawisz I), dwa ostrzeżenia, awaryjne, przycisk „Panel” |
| `hud-0283-cab-16x9.svg` | widok z kabiny z żywymi zegarami: tylko rząd kontrolek |
| `hud-0283-ultrawide-32x9.svg` | 32:9 — treść HUD 16:9 na środku, widok 3D na całą szerokość |
| `hud-0283-settings-mirrors.svg` | ustawienia, zakładka „Lusterka” z podglądem układu |

## 1. Zasady (anti-slop, docs/06 §2 i §7)
- Płaskie, matowe pola; **zero** gradientów, poświaty, rozmycia tła, neonów, emoji, „gamingowych” krojów.
- Jeden akcent (bursztyn) = fokus i znacznik sekcji. Kolor kontrolki = znaczenie (czerwony stop, bursztyn usterka,
  zielony funkcja włączona, niebieski drogowe).
- Inter Regular + SemiBold (OFL). Liczby duże i krótkie (68 j prędkość), jednostki mniejsze i wyciszone.
- Stan „wybrane” bez polegania na kolorze: odwrócenie (jasne pole, ciemny tekst SemiBold).
- Każda para kolorów ≥ WCAG AA (tabela w ADR 0283), półprzezroczyste tła liczone nad białym niebem w świetle liniowym.
- Teksty w tabelach (`HudTexts`, `PcSettingsTexts`), po polsku, bez marek, liczby z przecinkiem.

## 2. HUD monitora (jednostki treści 2560 × 1440 — każdy monitor 16:9…32:9)

```
 +--------------------------------------------------------------------------------------------------+
 | +--------+                       [ KAMERA COFANIA 560x316 (tylko na R) ]                 +--------+ |
 | |        |                                                                                |        | |
 | | lustro |          . . . . . . . . wolny widok drogi (40 % szer.) . . . . . . .         | lustro | |
 | |  lewe  |          .                                                          .         | prawe  | |
 | | 42 % H |          .                                                          .         | 42 % H | |
 | | (30-60)|          .                                                          .         | (30-60)| |
 | +--------+          .                                                          .         +--------+ |
 |                     .                                                          .                    |
 |                     . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                    |
 |                         [<-] [ NISKIE CIŚNIENIE ][ USTERKA ABS ]          [->]   <- rząd kontrolek |
 |                         +-------------------------------------------------+      720 x 52          |
 |                         | 1300 obr/min |  Zwalniacz R2  | Tempomat 40 km/h |  <- wiersz rozszerzony|
 |                         |------------------------------------------------- |      (klawisz I)      |
 |                         |      87 km/h |   D9   | 1 ====-- 8,1 bar          |  <- pasek 720 x 112  |
 |                         |              |        | 2 ====-- 8,0 bar          |                [Panel]|
 |                         +-------------------------------------------------+                       |
 +--------------------------------------------------------------------------------------------------+
```

- **Minimalny** (domyślnie): pasek (prędkość, bieg, obwody 1 i 2) + rząd kontrolek (strzałki zawsze na miejscu, szare gdy
  zgaszone — nic nie skacze).
- **Rozszerzony** (I): + obroty z paskiem (bursztyn > 1900 obr/min), zwalniacz (bursztyn gdy ≠ 0), tempomat zjazdu, przycisk
  „Panel” (laboratorium: zestaw, ABS, kamera cofania).
- **Kabina z żywymi ekranami** (auto): tylko rząd kontrolek; strzałki pojawiają się tylko gdy migają, kafle tylko gdy jest
  ostrzeżenie. Graybox placu (bez ekranów) → pasek.
- Ostrzeżenia (maks. 3, od najcięższego): ZWOLNIJ POSTOJOWY · NISKIE CIŚNIENIE · HAMOWANIE NACZEPY · POSTOJOWY ·
  USTERKA ABS · ABS NACZEPY · ABS.
- Widżet GPS (ADR 0150): lewy dolny róg pod lewym lusterkiem (gdy lusterko zjedzie w dół — obok niego), nigdy w wolnym
  widoku drogi; znika przy telemetrii deweloperskiej.
- 1080p: pasek 540×84 px, prędkość 51 px, okienko lusterka 249×454 px (było 178×324).

## 3. Lusterka
- Na zewnętrznych krawędziach (tam, gdzie w polu widzenia są lusterka kl. II), nie przy zegarach; nigdy w wolnym widoku
  drogi; aspekt szkła z tekstury (nie rozciągane); ramka matowa 6 j.
- Ustawienia: rozmiar 30–60 %, położenie w pionie 0–100 %, odsunięcie od krawędzi 0–100 %, podgląd układu na żywo.
- Regulacja widoku (oba lusterka główne): na zewnątrz/do środka ±6°, w dół/w górę ±3° — mniej własnej naczepy w obrazie.
- Graybox placu: celowanie 7,5 % na zewnątrz (bok naczepy ~5–14 % szerokości zamiast ~25–33 %).

```
 lusterko lewe (kl. II, 0,55 : 1)        lusterko prawe
 +-------------+                         +-------------+
 |  niebo    |b|                         |b|  niebo    |
 |           |o|                         |o|           |
 |-----------|k|                         |k|-----------|
 |  pobocze  | |   b = bok naczepy       | |  pas obok |
 |  droga    | |   (wąski pas przy       | |  droga    |
 +-------------+    wewnętrznej krawędzi) +-------------+
```

## 4. Ustawienia (jeden ekran, zakładki)

```
 USTAWIENIA                                                   Są niezastosowane zmiany.
 [ Grafika ][ Sterowanie ][ Dźwięk ][ Rozgrywka ][## Lusterka ##]
 Q / E lub LB / RB: zakładki · Enter / A: wybór · Esc / B: wróć
 | OKIENKA LUSTEREK
 Okienka lusterek            [ wyłączone ][## włączone ##]
 Rozmiar                     [-]          48 %           [+]
 Położenie w pionie          [-]           0 %           [+]
 Odsunięcie od krawędzi      [-]          20 %           [+]
 Podgląd układu (monitor 16:9)   +------------------------+
                                 |##                    ##|
                                 |##                    ##|
                                 |         ====           |
                                 +------------------------+
 | REGULACJA LUSTEREK
 Na zewnątrz / do środka     [-]        +1,5°            [+]
 W dół / w górę              [-]         0,0°            [+]
 [ Przywróć domyślne ]                    [ Anuluj ] [## Zastosuj ##]
```

| Zakładka | Zawartość |
|---|---|
| Grafika | Rozdzielczość, Tryb okna, Synchronizacja pionowa, Limit klatek; Jakość grafiki |
| Sterowanie | opis; „Kierownica, pedały, kamera…” (stosuje zmiany i przechodzi); „Przypisania klawiszy i pada…” (w jeździe) |
| Dźwięk | Głośność ogólna, Silnik, Otoczenie, Sygnały kabiny |
| Rozgrywka | Skala HUD; Szczegóły HUD; HUD w widoku z kabiny; Kontrolki dotykowe; Jednostki (km/h) |
| Lusterka | Okienka lusterek; Rozmiar; Położenie w pionie; Odsunięcie; podgląd; regulacja na zewnątrz / w dół |

Obsługa (stały układ, `MenuCommandMap`): klawiatura strzałki/Tab, Enter, Esc, Q/E; pad krzyżak/gałka, A, B, LB/RB;
mysz klik, prawy = wstecz, kółko = przewijanie. Fokus = bursztynowa ramka 3 j, najechanie = wyciszona ramka. Gdy ekran
jest otwarty, jest właścicielem fokusu → bramka #131 blokuje jazdę (strzałki, E/Q, bumpery nie sterują ciężarówką).

## 5. Menu startowe
Nagłówki SemiBold w kolorze tekstu z bursztynowym znacznikiem (były blade), tytuł SemiBold, wybrany segment odwrócony,
na PC jeden przycisk „Ustawienia” (zakładki), „Region niedostępny w tej wersji gry” zamiast „…w tym APK”, stopka „W
jeździe Esc (pad: Start) wraca tutaj”.

## 6. Do zrobienia na buildzie (lider, pętla wizualna)
Zrzuty kamer `lab-chase-hud`, `lab-cab-eye`, `lab-cab-mirror`, `lab-reverse-hud` (DrivingLab) w 1920×1080, 2560×1080,
5120×1440 przy edytorze przełączonym na Win64; menu startowe i każda zakładka ustawień z `Kamion-okno.cmd`; krytyk wg docs/06.
Komendy w opisie PR / raporcie D40.
