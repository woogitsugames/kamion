# 03 — Etapy i bramki jakości

Zasady:
- Etapy są sekwencyjne, ale **tor artystyczny ciężarówki (A) biegnie równolegle** z torem jazdy (F) od Etapu 1.
- Bramka = raport po polsku dla właściciela (`docs/reports/GATE-N.md`): co zrobione, liczby z urządzenia, zrzuty/nagrania **z telefonu**, znane braki, decyzje do podjęcia.
- Nie przeskakujesz bramki, żeby wygenerować więcej treści. Jeśli wynik nie spełnia celu: profiluj, zawęź, popraw.
- Po każdej bramce: tag w git, aktualizacja `docs/STATUS.md` i `docs/ROADMAP.md`.
- Terminy: nie podawaj sztywnych dat. Mierz i raportuj koszt (np. godziny pracy agentów na km drogi) od Etapu 4.

---

## Etap 0 — Fundament
**Zakres:** audyt, manifest i instalacja (`docs/02`), repo + LFS + `.gitignore`, struktura z `docs/10`, projekt Unity 6.3 URP, asmdef-y, ustawienia Android (ARM64, IL2CPP, Vulkan, target API zgodny z aktualnym wymogiem Google Play — sprawdź), `scripts/build-android.ps1` (batchmode `-executeMethod`, poprawny exit code, log, SHA256 APK, `-Install` → `adb install` + start + logcat), `scripts/doctor.ps1`, scena `Boot` z ekranem diagnostycznym (wersja, API grafiki, GPU, RAM, FPS, temp. jeśli dostępna), **harness visual QA** (render kamer do PNG w edytorze + zrzut z telefonu przez `adb exec-out screencap`), konfiguracja MCP i Superpowers, ADR 0001–0005, `CLAUDE.md` uzupełniony o komendy.
**Bramka:** APK zainstalowany i uruchomiony na Samsungu A, logcat bez wyjątków, pusta scena: zmierzone FPS/frame time; PNG z harnessu obejrzany przez Ciebie; `doctor` zielony; build odtwarzalny jedną komendą z czystego klonu.

## Etap 1 — Laboratorium jazdy: ciągnik (tor F)
**Zakres:** graybox ciągnika o **prawdziwych wymiarach i masach** (dokumentacja parametrów w `docs/VEHICLE_REFERENCE_DATA.md` z źródłami), solver z `docs/04` warstwy 1–4, telemetria CSV + overlay debug, plac testowy (płaski asfalt, okręgi o znanym promieniu (np. 25 m i 50 m), ósemka, podjazd 6% i 12%, krawężnik 8–15 cm, koleiny, różne nawierzchnie), sterowanie dotykowe v0 + gyro v0, kamera kabiny v0.
**Bramka:** testy z `docs/04` §6 dla ciągnika solo zielone w tolerancjach; brak dryfu na postoju, brak oscylacji, krawężnik nie teleportuje; 3 przejazdy 0–80 km/h powtarzalne ±3%; wszystko na telefonie. „Koła są nudne i stabilne” = sukces.

## Etap 2 — Naczepa, pneumatyka, pełny układ napędowy (tor F)
**Zakres:** naczepa firankowa (pusta / 24 t ładunku), siodło jako stabilny constraint, hamulce pneumatyczne ciągnik+naczepa z opóźnieniem, ABS, retarder, hamulec silnikowy, AMT 12-biegowa + tryb manual, sprzęgło, zawieszenie kabiny, cofanie z kamerą naczepy.
**Bramka:** pełny pakiet walidacyjny `docs/04` §6 (pusty i 40 t), jackknife możliwy przy błędzie kierowcy, brak eksplozji solvera, golden telemetry w `tests/golden/`; **feel test właściciela na telefonie** (ruszanie pod górę z 40 t, hamowanie awaryjne, rondo, cofanie pod rampę) z listą uwag i ich realizacją.

## Tor A (równolegle od Etapu 1) — Ciężarówka premium
Szczegóły w `docs/07`. Kroki z mini-bramkami do akceptacji właściciela:
A1 brief + referencje + wymiary → A2 **3 koncepcje sylwetki** (rendery kontrolne) → wybór właściciela → A3 blockout w skali z kabiną i pozycją oczu kierowcy → A4 high-poly zewnętrze → A5 kabina high → A6 low-poly + UV + bake + materiały → A7 LOD + kolizje + import + rendery w Unity i na telefonie → A8 naczepa.
**Bramka toru A (przed Etapem 5):** checklista `docs/07` §6 zaliczona, zrzuty z telefonu, budżet trójkątów/draw calli/pamięci spełniony na profilu Medium (Samsung A).

## Etap 3 — Referencyjna próbka jakości (bramka anty-slop)
**Zakres:** 300–500 m prawdziwej ulicy ze strefy przemysłowej (ręcznie dopracowane, ale już z danych GUGiK/OSM), fragment finalnej kabiny, kalibrowane oświetlenie dzienne, asfalt i oznakowanie poziome, pobocze, krawężniki, latarnie, 2–3 budynki hero + bryły z LoD2, roślinność, niebo; lusterka.
**Bramka:** porównanie side-by-side z **zdjęciami właściciela z tego miejsca** w tych samych ujęciach; checklista `docs/06` §5 zaliczona; zmierzony koszt na Samsungu A (Medium) i oszacowany zapas dla High; **akceptacja kierunku artystycznego przez właściciela**. Bez tego nie skalujemy mapy.

## Etap 4 — Pipeline świata na 2×2 km
**Zakres:** `tools/worldgen` (Python) + importer Unity (`docs/05`): ingest z manifestem → graf dróg → przekroje i skrzyżowania → teren z NMT → budynki LoD1/LoD2 + fasady → roślinność (BDOT10k + modele drzew GUGiK) → oznakowanie z tagów → kolizje osobno → chunki → Addressables. Raport QA danych.
**Bramka:** regeneracja 2×2 km jedną komendą, ręczne poprawki przeżywają reimport, zestaw przejeżdża całość bez wpadnięcia pod teren, zero dziur w kolizjach, odchyłka osi drogi od źródła w zadanej tolerancji, raport `low_confidence`.

## Etap 5 — Vertical slice: strefa przemysłowa + wylot (2–3 km)
**Zakres:** finalna ciężarówka i naczepa w grze, 2–3 km na poziomie Etapu 3, baza/magazyn z rampą, pętla jednego zlecenia, zapis/wznowienie (także po zabiciu procesu), nieliczny ruch AI (bezpieczne zachowania, priorytety, ronda), sygnalizacja świetlna, audio bazowe (`docs/08`), HUD + GPS z własnego grafu + nazwy ulic, menu i ustawienia jakości, dzień/zmierzch, deszcz (przyczepność + mokry asfalt), streaming + floating origin.
**Bramka:** właściciel przejeżdża slice 3× z rzędu bez soft-locka; 30 min jazdy na Samsungu A bez crasha, z raportem p50/p95/p99 frame time, pamięci, temperatury; raport wizualny z telefonu (dzień, zmierzch, deszcz, kabina noc); lista elementów nadal tymczasowych. **Pierwsza rzecz, którą wolno nazwać „grą”.**

## Etap 6 — Cały Białystok 1:1
**Zakres:** dzielnica po dzielnicy (kolejność do ustalenia po analizie danych), każda przechodzi bramkę jakości jak Etap 3/4 (w skali). Narzędzia produkcyjne: generatory typologii zabudowy białostockiej (bloki z wielkiej płyty, kamienice, domy jednorodzinne, drewniane domy na Bojarach, hale, galerie handlowe), autoring obiektów charakterystycznych (Pałac Branickich, katedra, ratusz, Rynek Kościuszki, stadion, dworzec PKP — model własny na bazie danych i zdjęć właściciela), sygnalizacja i oznakowanie całej sieci, pełny ruch AI z autobusami miejskimi, piesi (prosto, później), HLOD/impostory.
**Bramka per dzielnica:** checklista jakości, koszt produkcji zmierzony (godz./km², godz./obiekt hero), brak regresji wydajności, ciągłość sieci na granicach chunków i dzielnic.

## Etap 7 — Obrzeża + pierwsza trasa skrócona + test DLC
**Zakres:** miejscowości wokół Białegostoku 1:1, pierwszy odcinek trasy między miastami w skali skróconej (ADR skali po teście 2–3 wariantów współczynnika), strefy przejściowe miasto↔trasa, drugi region pack technicznie odrębny (dowód systemu DLC: instalacja/usunięcie bez reinstalacji gry, granica regionów, zapis w usuniętym regionie → bezpieczny fallback).
**Bramka:** przejazd Białystok → miejscowość obok przez granicę paczek bez przycięcia; testy DLC z `docs/10` zielone.

## Etap 8 — Polerowanie i testy zamknięte
Profile jakości per urządzenie (strojenie High/Ultra na flagowcu), test termiczny 30 min, AAB + Play Asset Delivery, testy wewnętrzne w Play Console (bez publikacji bez zgody właściciela), crash reporting, lokalizacja PL/EN, onboarding sterowania.

## Etap 9+ — Podlasie → Polska → kraje DLC; iOS
Rozszerzanie regionami tą samą procedurą. iOS: pierwszy próbny build możliwie wcześnie (po Etapie 2), jeśli pojawi się Mac (ewentualnie chmurowy) — dla wykrycia problemów platformowych; pełny port po Etapie 8.
