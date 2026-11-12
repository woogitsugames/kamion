# ElevenLabs — głos nawigacji GPS po polsku (prompt pack)

Wersja s16, 2026-11-12, lider. Do wygenerowania przez właściciela w ElevenLabs (plan Pro). To nie są efekty dźwiękowe, tylko **Text to Speech** (zamiana tekstu na mowę).
Nawigacja w grze (ADR 0150 + Mistral r4) zna manewry: prosto, lekko/ostro/zwykle w prawo i w lewo, zawracanie, rondo, cel; od r4 także pasy ruchu i limity ciężarówki. Komunikaty są złożone z gotowych zdań: odległość i manewr nagrane razem, bo sklejane osobno brzmią jak automat, a nazwa ulicy jako osobna końcówka.

## 1. Głos (raz)

Zalecam **Voice Design** (nowy, własny głos z opisu) zamiast głosu z biblioteki. Taki głos nie należy do konkretnego lektora, więc nie ma ryzyka praw osób trzecich ani cofnięcia głosu z biblioteki.

- ElevenLabs → Voices → **Voice Design** (lub „Create a voice”), opis (po angielsku, tak lepiej działa):
  `Calm, clear native Polish female voice, around 35 years old, neutral standard Polish accent, steady medium pace, friendly but neutral in-car navigation announcer, close studio microphone, dry with no reverb, no background noise.`
- Wygeneruj podgląd tekstem: `Za trzysta metrów skręć w prawo w ulicę Generała Władysława Andersa.` Wybierz najlepszy z wariantów i zapisz głos jako **Kamion GPS**.
- Jeśli wolisz głos męski — ten sam opis z `male`, ok. 40 lat. Wybór należy do Ciebie; ważne, żeby cały pakiet był jednym głosem.
- Bez naśladowania znanych nawigacji, aktorów i marek (CLAUDE.md, zasada 8).

## 2. Ustawienia Text to Speech (dla wszystkich partii)

| Ustawienie | Wartość |
|---|---|
| Głos | **Kamion GPS** (z pkt 1) |
| Model | **Eleven Multilingual v2** (najstabilniejszy dla polskiego i obsługuje pauzy `<break>`; v3 jest bardziej ekspresyjny, ale mniej powtarzalny i nie obsługuje `<break>`) |
| Stability | **65 %** |
| Similarity | **75 %** |
| Style exaggeration | **0 %** |
| Speaker boost | **Włączone** |
| Speed | **1,0** |
| Format pobrania | najwyższy dostępny — **WAV 44,1 kHz**, jeśli jest; inaczej MP3 320/192 kbps |

Wartości stability/similarity to punkt startowy (`WORKING_VALUE`), nie dane producenta. Jeśli głos „pływa” między partiami — podnieś stability do 75 %.

## 3. Jak generować

- Każda partia poniżej to **jeden blok tekstu do wklejenia w całości**. Zdania są rozdzielone pauzą `<break time="1.5s" />` — potem rozetnę plik po ciszy i nazwę każde zdanie automatycznie wg kolejności w tej tabeli. **Nie zmieniaj kolejności zdań.**
- Każdą partię wygeneruj **2 razy** (warianty). Zachowaj oba, nawet słabsze (D54).
- **Zapis:** `C:\Users\matma\Documents\Claude\kamion\art-source\audio\elevenlabs\gps\<ID partii> (n).wav`, np. `GPS_B01 (1).wav`, `GPS_B01 (2).wav`. Utwórz folder `gps`, jeśli go nie ma.
- Zanotuj w `notes.txt` w tym folderze: plan, datę, nazwę głosu i model (do `docs/LICENSES.md`).
- Liczby są zapisane słownie celowo — tak polski głos czyta je z dobrą odmianą.

## 4. Koszt

Multilingual v2: ok. 1 kredyt za znak (`UNVERIFIED` — sprawdź licznik przed generacją). Wszystkie partie razem to ok. 7 000 znaków, czyli ok. **7 000 kredytów za jeden przebieg, ok. 14 000 za dwa warianty** (przy 600 000 kredytów w planie).

---

## Partie

### GPS_B01 — „Teraz” (manewr natychmiast)
```
Teraz skręć w prawo. <break time="1.5s" /> Teraz skręć w lewo. <break time="1.5s" /> Teraz trzymaj się prawej. <break time="1.5s" /> Teraz trzymaj się lewej. <break time="1.5s" /> Teraz skręć ostro w prawo. <break time="1.5s" /> Teraz skręć ostro w lewo. <break time="1.5s" /> Teraz zawróć. <break time="1.5s" /> Teraz wjedź na rondo. <break time="1.5s" /> Teraz zjedź z ronda.
```

### GPS_B02 — „Za sto metrów”
```
Za sto metrów skręć w prawo. <break time="1.5s" /> Za sto metrów skręć w lewo. <break time="1.5s" /> Za sto metrów trzymaj się prawej. <break time="1.5s" /> Za sto metrów trzymaj się lewej. <break time="1.5s" /> Za sto metrów skręć ostro w prawo. <break time="1.5s" /> Za sto metrów skręć ostro w lewo. <break time="1.5s" /> Za sto metrów zawróć. <break time="1.5s" /> Za sto metrów wjedź na rondo.
```

### GPS_B03 — „Za dwieście metrów”
```
Za dwieście metrów skręć w prawo. <break time="1.5s" /> Za dwieście metrów skręć w lewo. <break time="1.5s" /> Za dwieście metrów trzymaj się prawej. <break time="1.5s" /> Za dwieście metrów trzymaj się lewej. <break time="1.5s" /> Za dwieście metrów skręć ostro w prawo. <break time="1.5s" /> Za dwieście metrów skręć ostro w lewo. <break time="1.5s" /> Za dwieście metrów zawróć. <break time="1.5s" /> Za dwieście metrów wjedź na rondo.
```

### GPS_B04 — „Za trzysta metrów”
```
Za trzysta metrów skręć w prawo. <break time="1.5s" /> Za trzysta metrów skręć w lewo. <break time="1.5s" /> Za trzysta metrów trzymaj się prawej. <break time="1.5s" /> Za trzysta metrów trzymaj się lewej. <break time="1.5s" /> Za trzysta metrów skręć ostro w prawo. <break time="1.5s" /> Za trzysta metrów skręć ostro w lewo. <break time="1.5s" /> Za trzysta metrów zawróć. <break time="1.5s" /> Za trzysta metrów wjedź na rondo.
```

### GPS_B05 — „Za pięćset metrów”
```
Za pięćset metrów skręć w prawo. <break time="1.5s" /> Za pięćset metrów skręć w lewo. <break time="1.5s" /> Za pięćset metrów trzymaj się prawej. <break time="1.5s" /> Za pięćset metrów trzymaj się lewej. <break time="1.5s" /> Za pięćset metrów skręć ostro w prawo. <break time="1.5s" /> Za pięćset metrów skręć ostro w lewo. <break time="1.5s" /> Za pięćset metrów zawróć. <break time="1.5s" /> Za pięćset metrów wjedź na rondo.
```

### GPS_B06 — „Za kilometr” i „Za dwa kilometry”
```
Za kilometr skręć w prawo. <break time="1.5s" /> Za kilometr skręć w lewo. <break time="1.5s" /> Za kilometr trzymaj się prawej. <break time="1.5s" /> Za kilometr trzymaj się lewej. <break time="1.5s" /> Za kilometr wjedź na rondo. <break time="1.5s" /> Za dwa kilometry skręć w prawo. <break time="1.5s" /> Za dwa kilometry skręć w lewo. <break time="1.5s" /> Za dwa kilometry trzymaj się prawej. <break time="1.5s" /> Za dwa kilometry trzymaj się lewej. <break time="1.5s" /> Za dwa kilometry wjedź na rondo.
```

### GPS_B07 — rondo: numer zjazdu
```
Na rondzie zjedź pierwszym zjazdem. <break time="1.5s" /> Na rondzie zjedź drugim zjazdem. <break time="1.5s" /> Na rondzie zjedź trzecim zjazdem. <break time="1.5s" /> Na rondzie zjedź czwartym zjazdem. <break time="1.5s" /> Na rondzie zjedź piątym zjazdem. <break time="1.5s" /> Na rondzie zawróć. <break time="1.5s" /> Na rondzie jedź prosto.
```

### GPS_B08 — „a następnie” (drugi manewr tuż po pierwszym)
```
a następnie skręć w prawo. <break time="1.5s" /> a następnie skręć w lewo. <break time="1.5s" /> a następnie trzymaj się prawej. <break time="1.5s" /> a następnie trzymaj się lewej. <break time="1.5s" /> a następnie wjedź na rondo. <break time="1.5s" /> a następnie zawróć. <break time="1.5s" /> a następnie jesteś u celu.
```

### GPS_B09 — pasy ruchu (dane z Mistral r4)
```
Trzymaj się prawego pasa. <break time="1.5s" /> Trzymaj się lewego pasa. <break time="1.5s" /> Trzymaj się środkowego pasa. <break time="1.5s" /> Jedź jednym z dwóch prawych pasów. <break time="1.5s" /> Jedź jednym z dwóch lewych pasów. <break time="1.5s" /> Zmień pas na prawy. <break time="1.5s" /> Zmień pas na lewy.
```

### GPS_B10 — stan trasy i cel
```
Wyznaczono trasę. <break time="1.5s" /> Wyznaczam nową trasę. <break time="1.5s" /> Zjechałeś z trasy. <break time="1.5s" /> Zawróć, jeśli to możliwe. <break time="1.5s" /> Jedź prosto. <break time="1.5s" /> Jedź prosto przez kilometr. <break time="1.5s" /> Jedź prosto przez dwa kilometry. <break time="1.5s" /> Jedź prosto przez pięć kilometrów. <break time="1.5s" /> Cel jest po prawej stronie. <break time="1.5s" /> Cel jest po lewej stronie. <break time="1.5s" /> Jesteś u celu. <break time="1.5s" /> Nie można wyznaczyć trasy do tego miejsca.
```

### GPS_B11 — ciężarówka: limity i prędkość
```
Trasa omija drogi zamknięte dla ciężarówek. <break time="1.5s" /> Uwaga, na trasie ograniczenie wysokości. <break time="1.5s" /> Uwaga, na trasie ograniczenie masy. <break time="1.5s" /> Uwaga, ograniczenie prędkości. <break time="1.5s" /> Przekraczasz dozwoloną prędkość. <break time="1.5s" /> Uwaga, rondo przed tobą. <break time="1.5s" /> Uwaga, ostry zakręt.
```

### GPS_B12 — nazwy ulic, część 1 (końcówki po manewrze)
```
w ulicę Generała Władysława Andersa. <break time="1.5s" /> w ulicę Generała Stanisława Maczka. <break time="1.5s" /> w aleję Tysiąclecia Państwa Polskiego. <break time="1.5s" /> w ulicę Bitwy Białostockiej. <break time="1.5s" /> w ulicę Białostoczek. <break time="1.5s" /> w ulicę Kombatantów. <break time="1.5s" /> w ulicę Michała Motoszko. <break time="1.5s" /> w ulicę Stefana Batorego. <break time="1.5s" /> w ulicę Władysława Bełzy. <break time="1.5s" /> w Wileńską. <break time="1.5s" /> w Sokólską. <break time="1.5s" /> w Grodzieńską.
```

### GPS_B13 — nazwy ulic, część 2
```
w Brzeską. <break time="1.5s" /> w Buską. <break time="1.5s" /> w Kowieńską. <break time="1.5s" /> w Lidzką. <break time="1.5s" /> w Olsztyńską. <break time="1.5s" /> w Racławicką. <break time="1.5s" /> w Sitarską. <break time="1.5s" /> w Skidelską. <break time="1.5s" /> w Wołkowyską. <break time="1.5s" /> w Łańcucką. <break time="1.5s" /> w Świsłocką.
```

### GPS_B14 — ronda i kierunki
```
na rondzie Putry. <break time="1.5s" /> na rondzie Pamięci Bieżeństwa. <break time="1.5s" /> w kierunku Warszawy. <break time="1.5s" /> w kierunku Augustowa. <break time="1.5s" /> w kierunku Ełku. <break time="1.5s" /> w kierunku Sokółki. <break time="1.5s" /> w kierunku centrum.
```

---

## Co dalej (lider / agent audio)

1. Rozcięcie partii po ciszy (narzędzie w `tools/audio/`), nazwy klipów wg tabel powyżej, kontrola liczby zdań w każdej partii (jeśli ElevenLabs połknął pauzę — partia do powtórki), normalizacja głośności (−16 LUFS, `WORKING_VALUE`), przycięcie ciszy, wybór lepszego wariantu.
2. Moduł głosu nawigacji: wybór zdania z manewru i odległości (progi 2 km / 1 km / 500 / 300 / 200 / 100 m / „Teraz”, dopasowane do prędkości), końcówka z nazwą ulicy, gdy jest w pakiecie, kolejka bez nakładania, ściszanie silnika na czas komunikatu, zero alokacji w pętli jazdy, wyłącznik w ustawieniach.
3. Do sprawdzenia w kodzie: czy nawigacja liczy numer zjazdu z ronda (`Maneuver.Roundabout`) — jeśli nie, używamy „wjedź na rondo” + „Na rondzie jedź prosto/zawróć” do czasu dodania numeru.
4. Wpis w `docs/LICENSES.md` (plan, data, głos z Voice Design).
