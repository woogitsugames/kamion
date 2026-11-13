# 0178 — Barwa lamp sygnałowych o zmierzchu (hue-preserving limit)

Status: kandydat (gałąź `lamps-0178`), nie scalone. Data: 2026-11-13.

## Problem
Stop, kierunkowskazy i obrysówki ciężarówki/naczepy o zmierzchu renderowały się jako białe plamy z kolorową obwódką.
Przyczyna w `TruckExterior.shader` (ścieżka `_KAMION_TRUCK_LAMPS`): emisja = stan lampy × nity × `_KamionExposure`
bez żadnego ograniczenia poza DRL (ADR 0115). O zmierzchu ekspozycja daje wartości 10–100× powyżej zakresu ekranu.
Krzywa D23 (ADR 0016) przycina **każdy kanał osobno** (0,7 na High, 1,0 na Low bez postprocessu), a High dodatkowo
desaturuje wg luminancji (lum-vs-sat, `lookHighlightDesaturation` 0,4 powyżej ~0,32). Czerwony `(1, 0.03, 0.01)` przy
R = 20 ma G = 0,6 → po przycięciu R i rosnącym G rdzeń przechodzi w pomarańcz/biel; bursztyn `(1, 0.42, 0.02)` szybciej.
Bloomu w projekcie nie ma (docs/06 §2, `LookDevAssets`: bloom wyłączony) i ta decyzja go nie dodaje.

## Decyzja
1. **Wszystkie grupy lamp mają ograniczenie zachowujące barwę.** DRL (grupa 1) zostaje na swojej ścieżce ADR 0115
   (kompresja luminancji, biel, wyjście ≤ 0,8). Pozostałe grupy: `TruckLampHueLimit` — wspólny mnożnik RGB liczony od
   `m = max(r,g,b)`: tożsamość do kolana, potem `knee + o / (1 + o / (ceiling − knee))`, `o = m − knee`.
   Proporcje kanałów (chromatyczność) bez zmian, `max(r,g,b) < ceiling`. Parametry materiału `_LampHueKnee` = 0,4,
   `_LampHueCeiling` = 0,8 (WORKING_VALUE; 0 wyłącza). Ceiling 0,8 > clip High 0,7 → rdzeń lampy osiąga 100 % kanału
   dominującego na High; na Low ~90 % (sRGB 0,8). Bursztyn przy 0,8 ma luminancję 0,31 — poniżej progu desaturacji.
   Dzień: lampa poniżej kolana (ogon 1,3 kcd/m² w słońcu) — bez zmian.
2. **Barwy w obszarach ECE (w gamucie sRGB)** — `TruckLights.Red = (1, 0, 0)`, `Amber = (1, 0.25, 0)` (liniowe sRGB).
   - Czerwony: CIE x 0,640, y 0,330; R48 granica w stronę żółci y ≤ 0,335 (cytat granicy: dokument GRE
     ECE/TRANS/WP.29/GRE/2006/25 przytaczający definicje R48). Stary (1, 0.03, 0.01): y 0,339 — poza.
   - Bursztyn: x 0,533, y 0,415; pasmo 0,398 ≤ y ≤ 0,429 (Australian Design Rule 49/00, transpozycja wymagań uznanych
     za równoważne R48). Stary (1, 0.42, 0.02): y 0,440 — za żółto-zielony.
   - Granice „w stronę bieli/purpury” (z ≤ 0,007/0,008) leżą poza gamutem sRGB — UNVERIFIED w tekście R48, nieosiągalne.
   Tekst samego R48 nie został w tej sesji odczytany — liczby oznaczone jako cytowane pośrednio.
3. **Odblaski**: shader nie może ich odróżnić, jeśli eksport nada im grupę lampy. Stwierdzono: ciągnik
   `rear_lens_{s}_3` (pasek odblasku w lampie zespolonej, `lens_red`, `chassis.py`) dostaje w `a6_export.py`
   grupę TAIL_BRAKE z maską 1,0 → świeci jak stop. Naprawa w eksporcie (zakres 0175: grupa bez emisji dla odblasków).
   Naczepa: `reflex_*` / `tri_reflector` / `side_reflector` → NONE (bez emisji) — poprawnie.

## Koszt
Tylko piksele z `_KAMION_TRUCK_LAMPS` i grupą ≠ 0 (DRL bez zmian): 2× max, 1 dzielenie, kilka MAD. Bez tekstur,
przebiegów, wariantów, słów kluczowych. Czas GPU na A16: UNVERIFIED (pomiar telefonu — lider).

## Weryfikacja
- EditMode `TruckLampEncodingTests`: chromatyczność czerwieni/bursztynu w pasmach; GPU readback `TruckLampHueLimit`
  dla skali 0,1–200: max kanał ≤ 0,8, stosunki G/R i B/R zachowane, tożsamość poniżej kolana, wyłączenie = bez zmian.
- Visual QA WorldC High i Low, `-Lighting dusk`, kamery truck-rear34/34/34r/side/front, trailer-34, przed/po, z
  wymuszonym stopem i światłami awaryjnymi (`KAMION_QA_LAMPS=brake,hazard`, VisualQaRunner). Dowody i pomiar ROI:
  `artifacts/lamps-0178/`.
