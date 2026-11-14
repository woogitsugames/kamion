#!/usr/bin/env python3
"""Buduje manifest.csv pakietu R3 i weryfikuje, że każdy cytat SOURCED występuje dosłownie w pobranym dokumencie
(lub — dla wartości odczytanych z obrazu strony — że obraz kontrolny istnieje). Exit 1 przy braku cytatu.
Uruchom: python3 -I build_manifest.py  (wymaga files/ — najpierw fetch.py)"""
import csv, hashlib, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sources_def import S, D  # noqa: E402
from textcheck import find  # noqa: E402

ROWS = []
GAME = "game/Assets/_Project/Vehicle/Physics/Definitions/Data/"
VRD = "docs/VEHICLE_REFERENCE_DATA.md"
PV = "docs/PHYSICS_VALIDATION.md"


def r(kat, przedmiot, wart, jedn, status, metoda, cytat, src, gra="", gra_zr="", ocena="", rek="", uwagi="", img=""):
    ROWS.append(dict(kat=kat, przedmiot=przedmiot, wart=wart, jedn=jedn, status=status, metoda=metoda, cytat=cytat,
                     src=src, gra=gra, gra_zr=gra_zr, ocena=ocena, rek=rek, uwagi=uwagi, img=img))


Q = "cytat dosłowny z tekstu PDF (pdftotext), strona w kolumnie strona_pdf"
QI = "odczyt z obrazu strony PDF (pdftoppm, obraz obejrzany: {img}); liczby w PDF są grafiką"
P4 = "ponownie zweryfikowane w tekście skonsolidowanym; wcześniej w research/mistral/p4-truck-regulations {p4} — nie dubluję, potwierdzam"

# ---------------- 1. Masy i wymiary — przepisy (cytowane za P4, potwierdzone w tekście skonsolidowanym) -------------
r("przepisy_masy_wymiary", "Maks. długość pojazdu przegubowego", "16.50", "m", "SOURCED", P4.format(p4="P4-123"),
  "pojazd przegubowy 16,50 m", "EU9653", "16.47", "VEHICLE_REFERENCE_DATA §Fifth wheel (1.45+3.70−0.68+12.00)", "OK",
  "bez zmian", "96/53/WE zał. I pkt 1.1")
r("przepisy_masy_wymiary", "Maks. szerokość", "2.55", "m", "SOURCED", P4.format(p4="P4-124"),
  "a) wszystkie pojazdy z wyjątkiem pojazdów, o których mowa w lit. b) 2,55 m", "EU9653", "2.55", GAME + "curtainsider_tridem_13_6.trailer.json (floor size x)", "OK", "bez zmian",
  "zał. I pkt 1.2; cytat krótki — kontekst w P4-124")
r("przepisy_masy_wymiary", "Maks. wysokość", "4.00", "m", "SOURCED", P4.format(p4="P4-126"),
  "Maksymalna wysokość (wszelkich pojazdów) 4,00 m", "EU9653", "4.00 (dach naczepy)", VRD + " §Semi-trailer cargo bay",
  "OK", "bez zmian", "zał. I pkt 1.3")
r("przepisy_masy_wymiary", "Pierścień skrętu: promień zewnętrzny / wewnętrzny", "12.50 / 5.30", "m", "SOURCED",
  P4.format(p4="P4-127"), "12,50 m oraz promieniu wewnętrznym 5,30 m", "EU9653", "brak testu", PV,
  "brak w grze", "dodać scenariusz walidacyjny 'ring_12_5_5_3' (zestaw 40 t, prędkość pełzania) — sprawdzić, że ślad mieści się w pierścieniu",
  "zał. I pkt 1.5")
r("przepisy_masy_wymiary", "Maks. odległość sworzeń — tył naczepy", "12.00", "m", "SOURCED", P4.format(p4="P4-128"),
  "naczepy 12,00 m", "EU9653", "12.00 (13.6 − 1.6)", VRD + " §Semi-trailer (kingpin to front wall 1.6)", "OK", "bez zmian",
  "zał. I pkt 1.6")
r("przepisy_masy_wymiary", "Maks. masa zespołu 5-osiowego (ciągnik 2-osiowy + naczepa 3-osiowa)", "40", "t", "SOURCED",
  P4.format(p4="P4-129, P4-138 (PL: WT § 3 ust. 1 pkt 2)"), "a) dwuosiowe pojazdy silnikowe z przycze pami trzyosiowymi 40 ton", "EU9653", "40.0",
  VRD + " §Load cases laden40", "OK", "bez zmian", "zał. I pkt 2.2.2 lit. a; cytat to końcówka wiersza tabeli (podział wyrazu 'przycze-pami' w PDF)")
r("przepisy_masy_wymiary", "Maks. masa dwuosiowego pojazdu silnikowego", "18", "t", "SOURCED", P4.format(p4="P4-131"),
  "2.3.1 Dwuosiowe pojazdy silnikowe inne niż autobusy: 18 ton", "EU9653", "17.38 (6.62+10.76, laden40)", VRD + " §Load cases", "OK", "bez zmian",
  "zał. I pkt 2.3.1 (brzmienie po 2015/719: 'inne niż autobusy')")
r("przepisy_masy_wymiary", "Maks. nacisk pojedynczej osi nienapędzanej", "10", "t", "SOURCED", P4.format(p4="P4-132"),
  "Jednoosiowe 10 ton", "EU9653", "6.62 (oś przednia laden40)", VRD + " §Load cases", "OK", "bez zmian", "zał. I pkt 3.1")
r("przepisy_masy_wymiary", "Maks. nacisk osi napędowej", "11.5", "t", "SOURCED", P4.format(p4="P4-133"),
  "Oś napędowa pojazdów, określone w ppkt 11,5 tony", "EU9653", "10.76", VRD + " §Load cases", "OK (zapas 0.74 t)",
  "bez zmian", "zał. I pkt 3.4.1")
r("przepisy_masy_wymiary", "Maks. suma nacisków osi potrójnej naczepy, rozstaw 1,3 < d ≤ 1,4 m", "24", "t", "SOURCED",
  P4.format(p4="P4-134"), "ponad 1,3 m i do 1,4 m (1,3 < d ≤ 1,4) 24 tony", "EU9653", "22.62 (rozstaw 1.31 m)",
  VRD + " §Load cases / tridem axle positions", "OK", "bez zmian", "zał. I pkt 3.3.2")

# ---------------- 2. Ciągnik 4x2 — geometria i masy (karta producenta klasy) -------------------------------------
r("ciagnik_geometria", "Rozstaw osi ciągnika 4x2 (zakres oferty)", "3500–3800", "mm", "SOURCED", Q,
  "Wheelbase 3500 3600 3700 3800", "FH42T", "3700", GAME + "tractor_4x2_generic.vehicle.json (axles front z=3.7)", "OK",
  "bez zmian", "ciągnik klasy 13 l 4x2, zawieszenie tylne pneumatyczne")
r("ciagnik_masy", "Masa własna ciągnika 4x2 (olej, woda, AdBlue, 0 l paliwa, bez kierowcy)", "6845–6870", "kg", "SOURCED", Q,
  "Kerb Weight 6845 6855 6865 6870", "FH42T", "6900 bez paliwa (7500 − 600 kg paliwa)",
  GAME + "tractor_4x2_generic.vehicle.json massElements", "OK (+0.5 %)", "bez zmian",
  "karta: 'Kerb weight can vary ± 3%'; warunki: 'Chassis weight includes oil, water, AdBlue, 0 litres fuel and without driver.'")
r("ciagnik_masy", "Nacisk osi przedniej ciągnika solo (bez paliwa)", "5030", "kg", "SOURCED", Q,
  "Front Axle 5030 5030 5030 5030", "FH42T", "≈4515 bez paliwa (4806 z 600 kg paliwa w z=1.8 m; 600×1.8/3.7=292 kg na przód)",
  VRD + " §Mass and geometry (static axle loads, DERIVED)", "poza zakresem (−10 %, tolerancja karty ±3 %)",
  "przesunąć ~0.5 t mas w przód (np. engine_gearbox z=3.3→3.6 m albo cab mass 1300→1500 kg); docelowo solo: przód ≈ 5.0–5.3 t, tył ≈ 1.8–2.1 t (z paliwem)",
  "jedno źródło (jedna karta); rozkład zależy od kabiny i zbiorników — traktować jako kierunek, nie twardą wartość")
r("ciagnik_masy", "Nacisk osi tylnej ciągnika solo (bez paliwa)", "1815–1840", "kg", "SOURCED", Q,
  "Rear Axle 1815 1825 1835 1840", "FH42T", "≈2385 bez paliwa (2694 z paliwem)", VRD + " §Mass and geometry",
  "poza zakresem (+30 %)", "jak wyżej — rozkład gry 64/36 %, karta 73/27 %", "")
r("ciagnik_masy", "Dop. masa całkowita ciągnika / zestawu (rejestracyjna)", "18000 / 40000", "kg", "SOURCED", Q,
  "Gross Combination Weight 40000 44000", "FH42T", "40000", VRD + " §Load cases", "OK", "bez zmian",
  "karta: Plated 18000 GVW / 40000 GCW; Design 20500 / 44000")
r("ciagnik_masy", "Dop. nacisk osi przedniej / tylnej (rejestracyjny)", "7500 / 11500", "kg", "SOURCED", Q,
  "Front Axle 7500 7500", "FH42T", "6620 / 10760 (laden40)", VRD + " §Load cases", "OK", "bez zmian",
  "tył: 'Rear Axle 11500 13000' (plated/design)")
r("ciagnik_geometria", "Średnica zawracania krawężnik–krawężnik (WB 3500/3600/3700/3800)", "12700 / 13100 / 13400 / 13700",
  "mm", "SOURCED", Q, "Turning Circle Diameter Kerb to Kerb 12700 13100 13400 13700", "FH42T",
  "≈13400 dla WB 3.7 (ESTIMATED, wiersz niżej)", GAME + "tractor_4x2_generic.vehicle.json steering", "OK",
  "bez zmian", "karta: 'Turning diameters are theoretically calculated.'")
r("ciagnik_geometria", "Średnica zawracania ciągnika gry (obliczona)", "13.4", "m", "ESTIMATED",
  "geometria: kąt wirtualny 40° względem osi tylnej, WB 3.70, rozstaw przód 2.04, opona 0.315: R_zew = hypot(3.70, 3.70/tan40°+1.02) + 0.1575·cos → 6.70 m",
  "", "", "13.4", GAME + "tractor_4x2_generic.vehicle.json (maxRoadWheelAngleDeg 40, Ackermann 1.0)", "OK (vs 13.4 m karty dla WB 3700)",
  "bez zmian", "obliczenie kinematyczne bez znoszenia opon")
r("ciagnik_geometria", "Położenie siodła (EC 96/53) przed osią tylną", "375", "mm", "SOURCED", Q,
  "Fifth Wheel Position (EC Directive 96/53) 375 375 375 375", "FH42T", "680", GAME + "tractor_4x2_generic.vehicle.json fifthWheel z=0.68",
  "poza zakresem (+305 mm; jedno źródło)",
  "zostawić 0.68 m (ADR 0019: limit 16.50 m przy zwisie przednim 1.45 m) albo skrócić zwis przedni modelu; przy 0.375 m oś napędowa dostaje ~+1 t (sprawdzić 11.5 t)",
  "wartość producenta dla jego zwisu przedniego; dla gry liczy się suma ≤ 16.50 m")
r("ciagnik_geometria", "Rozstaw kół osi przedniej (oś 7,5–10 t, felga 22,5\")", "2046–2153", "mm", "SOURCED", Q,
  "B = track width 2046-2153 mm", "MBPT", "2040", GAME + "tractor_4x2_generic.vehicle.json front trackWidth", "na granicy (−6 mm)",
  "opcjonalnie 2.05–2.10 m", "oś przednia ciężka 'F 7.5-F 10'")
r("ciagnik_geometria", "Rozstaw kół osi tylnej napędowej 13 t (środki par bliźniaczych)", "1802–1910", "mm", "SOURCED", Q,
  "B = track width 1802-1910 mm", "MBPT", "1820", GAME + "tractor_4x2_generic.vehicle.json rear trackWidth", "OK", "bez zmian",
  "oś 'R 440', 13 t, single reduction/hypoid")
r("ciagnik_masy", "Masa osi napędowej 13 t (bez kół)", "680", "kg", "SOURCED", Q, "Axle weight* 680 kg", "MBPT",
  "1300 (oś + bliźniaki + hamulce)", GAME + "tractor_4x2_generic.vehicle.json rear_axle_duals_brakes", "OK (spójne: 680 + 4 koła)",
  "bez zmian", "'* varies depending on configuration'")
r("ciagnik_zawieszenie", "Zawieszenie przednie ciągnika 4x2 (standard)", "resory paraboliczne 2-piórowe", "-", "SOURCED", Q,
  "FST-PAR 2 leaf parabolic springs - normal stiffness", "FH42T", "parabolic_leaf", GAME + "tractor_4x2_generic.vehicle.json front suspension", "OK",
  "bez zmian", "■ = wyposażenie standardowe w karcie")
r("ciagnik_zawieszenie", "Zawieszenie tylne ciągnika 4x2", "pneumatyczne (3 poziomy jazdy)", "-", "SOURCED", Q,
  "Air suspension with 3 driving levels", "FH42T", "air_4_bellows, poziomowanie", GAME + "tractor_4x2_generic.vehicle.json rear", "OK",
  "bez zmian", "")
r("ciagnik_zawieszenie", "Zawieszenie kabiny (przód, standard)", "mechaniczne sprężyny", "-", "SOURCED", Q,
  "Front cab suspension - Mechanical spring", "FH42T", "3-DOF sprężysto-tłumiący (generyczny)", VRD + " §Cab suspension", "OK (model generyczny)",
  "bez zmian", "tył kabiny: mechaniczne (std) lub pneumatyczne (opcja) — 'RCABS-A Rear cab suspension - Air'")
r("ciagnik_zawieszenie", "Zawieszenie kabiny (inny producent)", "4 miechy pneumatyczne", "-", "SOURCED", Q,
  "Suspension cab 4 bellow air suspension", "DAFXF", "3-DOF", VRD + " §Cab suspension", "OK", "bez zmian", "")

# ---------------- 3. Siodło i naczepa --------------------------------------------------------------------------
r("naczepa", "Wysokość sprzęgu (siodła) naczepy kurtynowej — warianty", "950–1180", "mm", "SOURCED", Q,
  "COUPLING HEIGHT 950 mm 980 mm 1.050 mm - 1.100 mm - 1.150 mm 1.100 mm - 1.150 mm - 1.180 mm", "KASS26", "1150",
  GAME + "tractor_4x2_generic.vehicle.json fifthWheel y / trailer kingpinHeight", "OK", "bez zmian",
  "950/980 = wersje mega (niskie), 1100–1180 = standard")
r("naczepa", "Masa własna naczepy kurtynowej standard (K.SCS M / X+)", "6240", "kg", "SOURCED", Q,
  "TARE WEIGHT 6.240 kg 6.240 kg 6.560 kg", "KASS26", "7000", GAME + "curtainsider_tridem_13_6.trailer.json massElements",
  "OK (górna część zakresu 4975–7810 kg)", "rozważyć 6.3–6.6 t dla 'standard'; 7.0 t odpowiada wersji wzmocnionej",
  "trzy pierwsze kolumny tabeli: K.SCS M, K.SCS X+, K.SCX")
r("naczepa", "Masa własna naczepy kurtynowej — rozpiętość rodziny modeli", "5630–7810", "kg", "SOURCED", Q,
  "TARE WEIGHT 6.240 kg 6.240 kg 6.560 kg 7.400 kg 7.500 kg 5.630 kg", "KASS26", "7000", "", "OK", "",
  "maks. 7.810 kg w dalszej kolumnie (model 54 t)")
r("naczepa", "Masa własna naczepy S.CS UNIVERSAL (od)", "5990", "kg", "SOURCED", Q,
  "The new generation starts from an unladen weight of 5,990 kg.", "SCB", "7000", "", "OK (gra cięższa o 1 t)", "j.w.", "")
r("naczepa", "Masa własna wersji lekkiej (X-LIGHT, od)", "4975", "kg", "SOURCED", Q, "Unladen… weight from… 4,975 kg", "SCB", "7000", "",
  "poza wariantem (gra nie modeluje wersji lekkiej)", "brak", "dolna granica rynku")
r("naczepa", "Dop. nacisk zespołu osi naczepy (3 × 9 t)", "27000", "kg", "SOURCED", Q, "AXLE LOAD 27.000 kg", "KASS26",
  "22620 (laden40)", VRD + " §Load cases", "OK", "bez zmian", "w ruchu w UE limit 24 t (zał. I pkt 3.3.2) — techniczne 27 t")
r("naczepa", "Dop. obciążenie sworznia (siodła)", "12", "t", "SOURCED", Q, "KING-PIN CAPACITY 12 ton", "KASS26",
  "9.88", VRD + " §Load cases laden40 kingpin", "OK", "bez zmian", "")
r("naczepa", "Rozstaw osi naczepy (sworzeń → środek zespołu osi)", "7700", "mm", "SOURCED", Q, "WHEELBASE 7.700 mm", "KASS26",
  "7700 (oś 2 z=−7.70)", GAME + "curtainsider_tridem_13_6.trailer.json axles", "OK (dokładnie)", "bez zmian", "")
r("naczepa", "Sworzeń → pierwsza oś naczepy", "6390", "mm", "ESTIMATED", "7700 (karta) − 1310 (rozstaw osi, wiersz niżej, UNVERIFIED)", "", "",
  "6390", GAME + "curtainsider_tridem_13_6.trailer.json axle1 z=−6.39", "OK", "bez zmian", "zależy od rozstawu 1.31 m")
r("naczepa", "Rozstaw osi w zespole trójosiowym", "1310", "mm", "UNVERIFIED",
  "nie znaleziono otwartej karty z tą liczbą; przedział prawny 1,3 < d ≤ 1,4 m potwierdzony (wiersz 96/53 pkt 3.3.2)", "", "",
  "1310", GAME + "curtainsider_tridem_13_6.trailer.json", "OK (w przedziale prawnym)", "bez zmian", "")
r("naczepa", "Wysokość wewnętrzna (przód) naczepy standard K.SCX", "2690–2710", "mm", "SOURCED", Q,
  "INTERNAL HEIGHT (Front) 2.900 mm - 2.950 mm 2.750 mm - 2.800 mm 2.690 mm - 2.710 mm", "KASS26",
  "2580 pod górną listwą / ≈2660 pod łukami", VRD + " §Semi-trailer cargo bay", "nieco poniżej (−3…−4 %)",
  "dla wizualu ok; dla ładunku 2.6–2.7 m", "kolumny: K.SCS M (mega), K.SCS X+, K.SCX")
r("naczepa", "Dop. masa całkowita naczepy (rejestracyjna, standard)", "39000", "kg", "SOURCED", Q, "GROSS WEIGHT 39.000 kg", "KASS26",
  "32500 (7000 + 25500 ładunku)", VRD + " §Load cases", "OK", "bez zmian", "")

# ---------------- 4. Silnik ---------------------------------------------------------------------------------------
for src, kw, rpm_p, nm, rpm_t, q_p, q_t in [
    ("D13K500", "368", "1530–1800", "2500", "980–1270", "Max power output at 1530–1800 rpm…500 hp (368 kW)", "Max torque at 980–1270 rpm…2500 Nm"),
    ("D13K460", "338", "1400–1800", "2300", "900–1400", "Max power output at 1400–1800 rpm… 460 hp(338 kW)", "Max torque at 900–1400 rpm… 2300Nm"),
]:
    r("silnik", f"Moc maks. silnika R6 12,8 l ({kw} kW) i zakres obrotów", f"{kw} @ {rpm_p}", "kW @ rpm", "SOURCED", Q, q_p, src,
      "368 @ 1530–1800", GAME + "diesel_r6_13l_368kw.engine.json", "OK", "bez zmian", "")
    r("silnik", f"Moment maks. silnika R6 12,8 l ({kw} kW)", f"{nm} @ {rpm_t}", "Nm @ rpm", "SOURCED", Q, q_t, src,
      "2500 @ 980–1270", GAME + "diesel_r6_13l_368kw.engine.json torqueCurve", "OK", "bez zmian", "")
r("silnik", "Obroty maks.", "2100", "rpm", "SOURCED", Q, "Max revs… 2100 rpm", "D13K500", "2100 (governor od 1900)",
  GAME + "diesel_r6_13l_368kw.engine.json", "OK", "bez zmian", "karta: 'Max revs ... 2100 rpm'")
r("silnik", "Pojemność skokowa", "12.8", "dm3", "SOURCED", Q, "12.8-litre, in-line, six- cylinder", "D13K500", "13 l (opis)",
  VRD + " §Engine", "OK", "bez zmian", "")
r("silnik", "Zakres ekonomiczny / optymalny obrotów", "950–1400 / 1100–1300", "rpm", "SOURCED", Q,
  "Economy revs range… 950–1400 rpm Optimum rev range… 1100–1300 rpm", "D13K500", "1158 rpm przy 85 km/h na 12. biegu", VRD + " §Gearbox final drive", "OK", "bez zmian",
  "pełne wiersze: 'Economy revs range ... 950–1400 rpm', 'Optimum rev range ... 1100–1300 rpm'")
r("silnik", "Hamulec silnikowy (dekompresyjny + przepustnica) przy 2300 rpm", "375", "kW", "SOURCED", Q,
  "Engine braking effect (VEB+) at 2300 rpm…375 kW", "D13K500", "375 kW (1557 Nm @ 2300)", GAME + "diesel_r6_13l_368kw.engine.json engineBrakeCurve",
  "OK", "bez zmian", "")
r("silnik", "Hamulec wydechowy (sama przepustnica) przy 2300 rpm", "200", "kW", "SOURCED", Q,
  "Exhaust brake effect (EPG) at 2300 rpm…200 kW", "D13K500", "nie modelowany osobno", VRD + " §Engine", "brak w grze",
  "opcjonalnie stopień 'tylko przepustnica' = 200 kW na dźwigni", "")
r("silnik", "Moc / moment MX-13 (klasa 480 KM)", "355 kW @ 1600; 2500 Nm @ 900–1125", "kW/Nm", "SOURCED", Q,
  "2500 Nm at 900 – 1125 rpm (Multi-Torque)", "DAFXF", "368 kW; 2500 Nm @ 980–1270", GAME + "diesel_r6_13l_368kw.engine.json",
  "OK", "bez zmian", "karta: '355 kW/483 hp at 1600 rpm'; drugi poziom '2350 Nm at 900 – 1365 rpm'; 12.9 l")
r("silnik", "Moc / moment OM 471 (375 kW)", "375 kW @ 1600; 2500 Nm @ 1100", "kW/Nm", "SOURCED", Q,
  "Rated power [kW/hp] 310/422 330/449 350/476 375/510 390/530", "MBPT", "368 kW; 2500 Nm", GAME + "diesel_r6_13l_368kw.engine.json",
  "OK", "bez zmian", "wiersz momentu: 'Maximal torque [Nm] 2100 2200 2300 2500 2600' przy 1100 rpm; moc przy 1600 rpm")
r("silnik", "Hamulec silnikowy rodziny ciężkich silników R6 (maks.)", "do 480", "kW", "SOURCED", Q,
  "Powerful and dynamic engine brakes with up to 480 kW", "MBPT", "375 kW", GAME + "diesel_r6_13l_368kw.engine.json", "OK (w zakresie)",
  "bez zmian", "dotyczy rodziny OM 470/471/473 (10,7–15,6 l)")
r("silnik", "Masa silnika na sucho (12,8 l)", "≈1100", "kg", "SOURCED", Q, "Dry weight (base engine)… approx. 1100 kg", "D13K500",
  "1500 (silnik + skrzynia)", GAME + "tractor_4x2_generic.vehicle.json engine_gearbox", "OK (1100 + skrzynia ~280 kg + osprzęt)", "bez zmian", "")

# ---------------- 5. Retarder -------------------------------------------------------------------------------------
r("retarder", "Retarder zintegrowany ze skrzynią — moment / moc maks.", "4000 / 600", "Nm / kW", "SOURCED", Q,
  "ZF-Intarder with up to 4,000 Nm/600 kW braking torque/power", "TRAXON", "4000 / 600", GAME + "tractor_4x2_generic.vehicle.json retarder",
  "OK", "bez zmian", "")
r("retarder", "Retarder olejowy (inny producent) — moment / moc / obroty maks.", "3500 / 700 / 5200", "Nm / kW / rpm", "SOURCED", Q,
  "3500 700 5200 Max. braking torque [Nm] Max. braking power [kW] Max. rotation [min -1]", "MBPT", "4000 / 600",
  GAME + "tractor_4x2_generic.vehicle.json retarder", "OK (zakres 3500–4000 Nm, 600–700 kW)", "bez zmian", "")

# ---------------- 6. Skrzynia biegów i most -------------------------------------------------------------------------
tx = ["12.92", "9.98", "7.69", "5.94", "4.57", "3.53", "2.83", "2.19", "1.68", "1.30", "1.00", "0.77"]
for i, v in enumerate(tx, 1):
    r("skrzynia", f"AMT 12 OD (TraXon 12TX2610) — bieg {i}", v, "-", "SOURCED", Q,
      "2610 12.92 9.98 7.69 5.94 4.57 3.53 2.83 2.19 1.68 1.30 1.00 0.77 12.03 9.29 2.64 2.04", "TRAXON", v,
      GAME + "amt12_od_traxon_class.gearbox.json forwardRatios", "OK", "bez zmian", "")
r("skrzynia", "AMT 12 OD (TraXon) — wsteczny R1 / R2 / R3 / R4", "12.03 / 9.29 / 2.64 / 2.04", "-", "SOURCED", Q,
  "2610 12.92 9.98 7.69 5.94 4.57 3.53 2.83 2.19 1.68 1.30 1.00 0.77 12.03 9.29 2.64 2.04", "TRAXON", "12.03 (tylko R1)",
  GAME + "amt12_od_traxon_class.gearbox.json reverseRatio", "OK", "opcjonalnie R2 = 9.29", "")
r("skrzynia", "TraXon 12TX2610 — maks. moment wejściowy", "2600", "Nm", "SOURCED", Q, "12 TX 2610 SO max. 2,600", "TRAXON", "2500 (silnik)",
  "", "OK", "bez zmian", "")
at = ["14.94", "11.73", "9.04", "7.09", "5.54", "4.35", "3.44", "2.70", "2.08", "1.63", "1.27", "1.00"]
for i, v in enumerate(at, 1):
    r("skrzynia_alt", f"AMT 12 direct drive (I-Shift AT2612) — bieg {i}", v, "-", "SOURCED",
      QI.format(img="files/_view/at2612-3.png, s. 3"), f"Ratios AT2612 (wykres słupkowy: {' '.join(at)}; R1–R4 17.48 13.73 4.02 3.16)",
      "AT2612", tx[i - 1], GAME + "amt12_od_traxon_class.gearbox.json", "alternatywa (direct drive)", "brak (gra = OD)", "", img="at2612-3.png")
ato = ["11.73", "9.21", "7.09", "5.57", "4.35", "3.41", "2.70", "2.12", "1.63", "1.28", "1.00", "0.78"]
for i, v in enumerate(ato, 1):
    r("skrzynia_alt", f"AMT 12 overdrive (I-Shift ATO2612F) — bieg {i}", v, "-", "SOURCED",
      QI.format(img="files/_view/ato2612f-3.png, s. 3"), f"Ratios ATO2612F (wykres słupkowy: {' '.join(ato)}; R1–R4 13.73 10.78 3.16 2.48)",
      "ATO2612F", tx[i - 1], GAME + "amt12_od_traxon_class.gearbox.json", "OK (OD 0.77 vs 0.78)", "bez zmian", "", img="ato2612f-3.png")
iS = ["11.639", "7.035", "4.400", "2.645", "1.599", "1.000"]
iL = ["9.020", "5.452", "3.410", "2.050", "1.239", "0.775"]
g330 = [x for p in zip(iS, iL) for x in p]
for i, v in enumerate(g330, 1):
    r("skrzynia_alt", f"AMT 12 overdrive (G 330-12) — bieg {i}", v, "-", "SOURCED",
      "cytat z tabeli iS/iL (s. 29, obraz obejrzany: files/_view/mb29_crop.png); kolejność biegów = przeplot iS/iL (splitter) — ESTIMATED układ, liczby SOURCED",
      "iS 11.639 7.035 4.400 2.645 1.599 1.000 12.774 2.093 15.02", "MBPT", tx[i - 1], GAME + "amt12_od_traxon_class.gearbox.json",
      "OK (OD 0.775)", "bez zmian", "iL: 9.020 5.452 3.410 2.050 1.239 0.775; R 12.774 / 9.900", img="mb29_crop.png")
r("most", "Przełożenie mostu — ciągnik z AMT OD 0.77 (6x4, 60 t GCM)", "3.61", "-", "SOURCED", Q, "Rear axle ratio 3.61 : 1.00", "DAFXF",
  "3.40", GAME + "tractor_4x2_generic.vehicle.json driveline.finalDriveRatio", "OK", "bez zmian", "skrzynia 'TraXon 12 speed 12TX2610, 12.92 – 0.77'")
r("most", "Przełożenie mostu — AMT direct 1.00 (6x2, 40 t)", "2.38", "-", "SOURCED", Q, "Rear axle ratio 2.38 : 1.00", "DAFCF",
  "3.40 (przy OD 0.77 ≡ 2.62 przy direct)", GAME + "tractor_4x2_generic.vehicle.json", "OK (całkowite 2.38 vs 2.62)", "bez zmian",
  "skrzynia 'TraXon 12 speed 12TX2210, 16.69 – 1.00'")
r("most", "Przełożenie mostu 13 t dostępne dla ciągnika dalekobieżnego", "3.70", "-", "SOURCED", Q, "3.70:1", "RSS1344C",
  "3.40", "", "OK (zakres 2.38–3.70)", "bez zmian", "karta dotyczy wersji osi dla napędu elektrycznego; tylko 3.70 oznaczone dla FH")
r("most", "Obroty silnika przy 85 km/h, 12. bieg 0.77, most 3.40, r_dyn opony", "1127 (r_dyn 0.524) / 1158 (r gry 0.51)", "rpm", "ESTIMATED",
  "n = v/(2π·r)·i_b·i_m·60; v = 23.61 m/s; r_dyn = obwód toczenia 3294 mm/2π (Dunlop 315/80R22.5 SP346)", "", "", "1158",
  VRD + " §Gearbox Final drive", "OK (w 1100–1300 rpm)", "po zmianie r na 0.524 obroty spadną o 2.7 % — nadal w paśmie optimum", "")

# ---------------- 7. Opony ----------------------------------------------------------------------------------------
def tyre(size, src, quote, od, slr, circ, gra_r, rec, extra=""):
    rd = float(circ) / (2 * math.pi) / 1000
    r("opony_geometria", f"{size} — średnica / promień statyczny / obwód toczenia", f"{od} / {slr} / {circ}", "mm", "SOURCED", Q,
      quote, src, gra_r, rec, "", "", extra)
    return rd
rd = {}
rd["315/80 Dunlop"] = tyre("315/80 R22.5 156/150 L (Dunlop SP346)", "DUNLOP", "1084 315 502 3294 8.50 8000 13400", "1084", "502", "3294",
                           "r = 0.51", GAME + "tire_315_80_r22_5.tire.json radius", "ciśn. nominalne 8,50 bar; oś pojedyncza 8000 kg, bliźniacza 13400 kg")
rd["315/80 BS-M"] = tyre("315/80 R22.5 156/150 K (Bridgestone M-STEER 001)", "BSM", "315/80 R 22.5 156/150 K 311 1092 507 3319", "1092", "507", "3319",
                         "r = 0.51", GAME + "tire_315_80_r22_5.tire.json radius", "obwód '@ 90 km/h (Tol. ± 2%)'")
rd["315/80 BS-R"] = tyre("315/80 R22.5 156/150 L (Bridgestone R-STEER 002)", "BSR", "314 1077 500 3272", "1077", "500", "3272",
                         "r = 0.51", GAME + "tire_315_80_r22_5.tire.json radius")
rd["315/70 Dunlop"] = tyre("315/70 R22.5 154/150 L (Dunlop SP344)", "DUNLOP", "1014 315 471 3095 9.00 7500 13400", "1014", "471", "3095",
                           "brak (gra używa 315/80)", "docs/04 §2.4 wymienia 315/70", "ciśn. 9,00 bar; oś 7500 / 13400 kg")
rd["315/70 Nokian"] = tyre("315/70 R22.5 154/150 L (Nokian E-Truck Drive)", "NOKIAN", "STATIC LOADED RADIUS 474 mm", "1027", "474", "3122",
                           "brak (gra używa 315/80)", "", "karta: 'OVERALL DIAMETER 1027 mm', 'ROLLING CIRCUMFERENCE 3122 mm'")
rd["315/70 BS-R"] = tyre("315/70 R22.5 156/150 L (Bridgestone R-STEER 002)", "BSR", "313 1017 469 3091", "1017", "469", "3091",
                         "brak (gra używa 315/80)", "")
rd["385/65 Dunlop"] = tyre("385/65 R22.5 160 K (Dunlop SP346)", "DUNLOP", "1077 380 499 3293 9.00 9000", "1077", "499", "3293",
                           "r = 0.515", GAME + "tire_385_65_r22_5.tire.json radius", "ciśn. 9,00 bar; oś pojedyncza 9000 kg")
rd["385/65 BS-M"] = tyre("385/65 R22.5 160 K (Bridgestone M-STEER 001)", "BSM", "385/65 R 22.5 160 K 378 1086 502 3302", "1086", "502", "3302",
                         "r = 0.515", GAME + "tire_385_65_r22_5.tire.json radius")
rd["385/65 BS-E"] = tyre("385/65 R22.5 160 K (Bridgestone ECOPIA H-TRAILER 002)", "BSE", "379 1078 498 3277", "1078", "498", "3277",
                         "r = 0.515", GAME + "tire_385_65_r22_5.tire.json radius")
for size, keys, gra, f in [("315/80 R22.5", ["315/80 Dunlop", "315/80 BS-M", "315/80 BS-R"], "0.510", "tire_315_80_r22_5.tire.json"),
                           ("385/65 R22.5", ["385/65 Dunlop", "385/65 BS-M", "385/65 BS-E"], "0.515", "tire_385_65_r22_5.tire.json"),
                           ("315/70 R22.5", ["315/70 Dunlop", "315/70 Nokian", "315/70 BS-R"], "brak", "")]:
    lo, hi = min(rd[k] for k in keys), max(rd[k] for k in keys)
    ocena = "brak w grze" if gra == "brak" else ("OK" if lo <= float(gra) <= hi else f"poza zakresem ({(float(gra) / lo - 1) * 100:+.1f} % vs min)")
    r("opony_geometria", f"{size} — promień dynamiczny (toczenia) r = obwód/2π", f"{lo:.3f}–{hi:.3f}", "m", "ESTIMATED",
      "obliczony z obwodów toczenia 3 kart (wiersze wyżej)", "", "", gra, (GAME + f) if f else "", ocena,
      "ustawić radius ≈ 0.52 m (kinematyka/prędkościomierz); promień statyczny 0.50–0.51 m do kontaktu" if gra != "brak" else "jeśli gra przejdzie na 315/70: r ≈ 0.494 m",
      "gra używa jednego promienia dla geometrii i kinematyki (VRD)")
r("opony_nosnosc", "Indeks nośności 154 / 150 (oś pojedyncza / bliźniacza)", "3750 / 3350", "kg na oponę", "ESTIMATED",
  "Dunlop: 315/70 154/150 — oś pojedyncza 7500 kg, bliźniacza 13400 kg → /2 i /4", "", "", "", "", "", "", "")
r("opony_nosnosc", "Indeks nośności 156 / 150", "4000 / 3350", "kg na oponę", "ESTIMATED",
  "Dunlop: 315/80 156/150 — 8000 / 13400 kg na oś → /2 i /4", "", "", "Fz0 = 30 kN (3.06 t)", GAME + "tire_315_80_r22_5.tire.json nominalLoadN",
  "OK (Fz0 < nośność)", "bez zmian", "potwierdza S6 (wcześniej UNVERIFIED w VRD)")
r("opony_nosnosc", "Indeks nośności 160 (385/65)", "4500", "kg na oponę", "ESTIMATED", "Dunlop: 385/65 160 K — oś pojedyncza 9000 kg → /2",
  "", "", "Fz0 = 35 kN; laden 78.5 kN/oś = 4.0 t/oponę", GAME + "tire_385_65_r22_5.tire.json", "OK", "bez zmian", "")
r("opony_nosnosc", "Indeks nośności 164 (385/65 HL)", "5000", "kg na oponę", "ESTIMATED", "Dunlop: 385/65 SP246 164 K — oś 10000 kg → /2",
  "", "", "", "", "", "", "")
r("opony_nosnosc", "Nośność 315/70 154 vs ciśnienie (oś pojedyncza)", "5780 @ 650 … 7500 @ 900", "kg @ kPa", "SOURCED", Q,
  "Single 120 5780 5960 6130 6310 6480 6650 6830 7000 7160 7330 7500", "NOKIAN", "", "", "", "",
  "tabela 650–900 kPa co 25 kPa; 'not more than 9.0 bar should be used'")
r("opony_sztywnosc", "Sztywność pionowa opony 315/80 R22.5 @ 850 kPa", "880.3", "kN/m", "SOURCED", Q,
  "315/80R22.5 156/150 850 39.2 880.3", "KARIS", "1000", GAME + "tire_315_80_r22_5.tire.json radialStiffness", "poza zakresem (+14 %)",
  "rozważyć 0.88e6 N/m (dane producenta opon via praca); obecne 1.0e6 to sieczna z promienia statycznego", "tab. 7, za Nokian Tyres")
r("opony_sztywnosc", "Sztywność pionowa opony 385/65 R22.5 @ 900 kPa", "1033.4", "kN/m", "SOURCED", Q,
  "385/65R22.5 160 900 44.1 1033.4", "KARIS", "1100", GAME + "tire_385_65_r22_5.tire.json radialStiffness", "OK (+6 %)", "opcjonalnie 1.03e6", "")
r("opony_sztywnosc", "Sztywność pionowa opony 315/70 R22.5 @ 900 kPa", "941.3", "kN/m", "SOURCED", Q,
  "315/70R22.5 156/150 900 39.2 941.3", "KARIS", "brak", "", "brak w grze", "", "")
r("opony_sily", "Współczynnik sztywności bocznej (cornering coefficient) CCy0", "7.4", "(N/rad)/N", "SOURCED", Q,
  "CCy0 Cornering coefficient [(N/rad)/N] 7.4", "KARIS", "7.0", GAME + "tire_*.tire.json corneringStiffnessPerLoad", "OK (−5 %)",
  "bez zmian", "wartość użyta w modelu PBS (praca dyplomowa) — nie pomiar; jedno źródło")
r("opony_sily", "Długość relaksacji (boczna)", "0.4", "m", "SOURCED", Q, "Lr Relaxation length [m] 0.4", "KARIS", "0.50",
  GAME + "tire_*.tire.json relaxationLengthY", "OK (+25 %, wartość robocza w obu)", "bez zmian", "praca: 'set to standard value of 0.4'")
r("opony_sily", "Maks. współczynnik siły bocznej (sucho)", "0.8", "-", "SOURCED", Q, "uy0 Maximum lateral force coefficient [-] 0.8", "KARIS", "0.8",
  GAME + "tire_*.tire.json peakMu", "OK", "bez zmian", "")
r("opony_sily", "Gradient współczynnika tarcia z obciążeniem", "−0.2", "-", "SOURCED", Q, "ugy Maximum lateral force gradient [-] -0.2", "KARIS", "−0.08",
  GAME + "tire_*.tire.json muLoadSensitivity", "różna definicja (nieporównywalne wprost)", "brak", "")
r("opony_sily", "Współczynniki MF B,C,D,E dla opon ciężarowych z pomiaru", "—", "-", "UNVERIFIED",
  "nie znaleziono otwartej publikacji z dopasowaniem MF do opony 22.5\" (Deep Blue/UMTRI za Cloudflare, MDPI 403); TNO/MF-Tyre — dane płatne", "", "",
  "Cx 1.65, Cy 1.35, Ey −0.5", GAME + "tire_*.tire.json", "brak źródła", "pozostaje WORKING_VALUE", "")
r("opony_toczenie", "Klasa A efektywności paliwowej, opony C3 (RRC)", "≤ 4.0", "N/kN (= kg/t)", "SOURCED", Q, "A RRC ≤ 6,5 RRC ≤ 5,5 RRC ≤ 4,0", "EU740",
  "", "", "", "", "zał. I część A, kolumna C3")
r("opony_toczenie", "Klasa B, opony C3 (RRC)", "4.1–5.0", "N/kN", "SOURCED", Q, "4,1 ≤ RRC ≤ 5,0", "EU740", "5.0 (385/65)",
  GAME + "tire_385_65_r22_5.tire.json rollingResistanceCoeff", "OK (klasa B)", "bez zmian", "")
r("opony_toczenie", "Klasa C, opony C3 (RRC)", "5.1–6.0", "N/kN", "SOURCED", Q, "5,1 ≤ RRC ≤ 6,0", "EU740", "5.5 (315/80)",
  GAME + "tire_315_80_r22_5.tire.json rollingResistanceCoeff", "OK (klasa C)", "bez zmian", "")
r("opony_toczenie", "Klasa D / E, opony C3 (RRC)", "6.1–7.0 / ≥ 7.1", "N/kN", "SOURCED", Q, "6,1 ≤ RRC ≤ 7,0", "EU740", "", "", "", "", "E: 'RRC ≥ 7,1'")
r("opony_toczenie", "Klasa A przyczepności na mokrym, opony C3 (G)", "≥ 1.25", "-", "SOURCED", Q, "1,25 ≤ G", "EU740", "wet scale 0.625",
  VRD + " §Tire (wet asphalt friction scale)", "nieporównywalne (G to indeks względny do opony wzorcowej)", "brak", "")
r("opony_toczenie", "Etykieta UE przykładowej opony napędowej 315/70", "RR C, wet grip C, 73 dB", "-", "SOURCED", Q, "ROLLING RESISTANCE C", "NOKIAN",
  "", "", "", "", "")

# ---------------- 8. Hamowanie -----------------------------------------------------------------------------------
img_r13 = "r13p43-043.png"
r("hamowanie", "UN R13 N3 typ-0, silnik odłączony: prędkość próby", "60", "km/h", "SOURCED", QI.format(img="files/_view/r13p43-043.png, s. 43"),
  "N3 ... v ... 60 km/h (tabela pkt 2.1.1 zał. 4)", "R13R3", "", "", "", "", "wersja: Rev.3 (1996, seria 08); nowsze serie nieotwarte (unece.org 403)", img=img_r13)
r("hamowanie", "UN R13 N3 typ-0, silnik odłączony: droga hamowania", "s ≤ 0.15 v + v²/130", "m", "SOURCED", QI.format(img="files/_view/r13p43-043.png, s. 43"),
  "s ≤ 0.15v + v²/130 (M2…N3)", "R13R3", "", "", "", "", "w tekście PDF wzór jest grafiką (pdftotext go nie zwraca)", img=img_r13)
r("hamowanie", "UN R13 N3 typ-0, silnik odłączony: MFDD", "≥ 5.0", "m/s²", "SOURCED", QI.format(img="files/_view/r13p43-043.png, s. 43"),
  "dm ≥ 5.0 m/s²", "R13R3", "7.07–7.48 (80→0 sucho, ABS)", PV + " tabela, wiersz 5 brake_80_0_dry", "OK", "bez zmian",
  "status w VRD S5 był UNVERIFIED — teraz SOURCED (Rev.3); gra spełnia z zapasem", img=img_r13)
r("hamowanie", "UN R13 N3 typ-0, silnik podłączony: prędkość / droga / MFDD", "90 km/h; s ≤ 0.15 v + v²/103.5; ≥ 4.0", "km/h; m; m/s²", "SOURCED",
  QI.format(img="files/_view/r13p43-043.png, s. 43"), "V = 80% Vmax but not exceeding ... 90 km/h; 0.15v + v²/103.5; 4.0 m/s²", "R13R3", "brak testu 90→0", PV,
  "brak w grze", "dodać scenariusz brake_90_0_engine_connected (40 t): s ≤ 0.15·90 + 90²/103.5 = 91.8 m", "mianownik w PDF złożony graficznie jako 'v²/103 .5' — odczyt 103,5", img=img_r13)
r("hamowanie", "UN R13: siła na pedale (M2–N3)", "≤ 70", "daN", "SOURCED", QI.format(img="files/_view/r13p43-043.png, s. 43"), "F ≤ ... 70 daN", "R13R3",
  "", "", "", "", "", img=img_r13)
r("hamowanie", "UN R13 — droga hamowania z 80 km/h przy wymaganiu typ-0 N3", "≤ 61.2", "m", "ESTIMATED", "0.15·80 + 80²/130 = 12.0 + 49.2 (ekstrapolacja wzoru 60 km/h na 80 km/h)",
  "", "", "34.9 / 39.0 / 40.5", PV + " wiersz 5 brake_80_0_dry (ABS)", "OK", "bez zmian", "to tolerancja już użyta w PHYSICS_VALIDATION")
r("hamowanie", "UN R13: naczepa (O3/O4) — min. suma sił hamowania, laden i unladen", "45", "% maks. statycznego obciążenia kół", "SOURCED", Q,
  "semi-trailer, laden and unladen : 45", "R13R3", "", "", "brak testu naczepy osobno", "opcjonalnie test 'trailer_only_braking' (zR ≥ 0.45)",
  "zał. 4 pkt 3.1.2.1; O4: 'Test conditions and performance requirements are the same as for vehicles of categories O2 and O3' (pkt 3.1.3.1)")
r("hamowanie", "UN R13: ciśnienie w przewodach sprzęgających przy pełnym hamowaniu", "6.5–8.5", "bar", "SOURCED", Q,
  "must be between 6.5 and 8.5 bar at the coupling heads of the supply line and the control line", "R13R3", "zasilający 8.5 / sterujący 7.5",
  VRD + " §Air brake system", "OK", "bez zmian", "")
r("hamowanie", "UN R13: czas zadziałania (najmniej korzystna oś)", "≤ 0.6", "s", "SOURCED", Q,
  "the braking force on the least favourably placed axle reaches the level corresponding to the prescribed performance must not exceed 0.6 seconds",
  "R13R3", "0.25 / 0.31 / 0.53–0.54", PV + " wiersz 5 brake_response_static", "OK", "bez zmian", "pkt 5.2.1.? / zał. 4 pkt 4.1.1")
r("hamowanie", "UN R13 zał. 6: ciśnienie w siłowniku 75 % po aktywacji 0,2 s (pojazd silnikowy)", "≤ 0.6", "s", "SOURCED", Q,
  "reaches 75 per cent of its asymptotic value shall not exceed 0.6 seconds", "R13R3", "0.25 / 0.31", PV + " brake_response_static", "OK", "bez zmian", "")
r("hamowanie", "UN R13 zał. 6: głowica sprzęgająca przewodu sterującego — 10 % / 75 %", "0.2 / 0.4", "s", "SOURCED", Q, "10 0.2 75 0.4", "R13R3",
  "brak osobnego pomiaru na głowicy", "", "brak w grze", "opcjonalnie telemetria ciśnienia na głowicy żółtej", "")
r("hamowanie", "UN R13 zał. 6: naczepa — od 0,65 bar na głowicy do 75 % w siłowniku", "≤ 0.4", "s", "SOURCED", Q,
  "cent of its asymptotic value must not exceed 0.4 seconds", "R13R3", "≈0.53 od pedału (dwa opóźnienia 0.15+0.20)", VRD + " §Air brake system",
  "OK (jeśli ~0.15 s do głowicy)", "bez zmian", "")
r("hamowanie", "UN R13 (02): hamulec pomocniczy kat. N — MFDD", "≥ 2.2", "m/s²", "SOURCED", Q, "deceleration dm = 2.2 m/s2", "R13JP", "33.1 m z 60 km/h po pęknięciu obwodu",
  PV + " air_leak_rear_circuit", "OK", "bez zmian", "już jako S5 w VRD — potwierdzenie")
r("hamowanie", "UN R13 (02): hamulec postojowy utrzymuje pojazd na pochyleniu", "18", "%", "SOURCED", Q, "18 per cent up or down-gradient", "R13JP",
  "12 % (zestaw, park_12pct)", PV + " wiersz 1", "OK", "dodać test 18 % dla ciągnika solo", "")
r("hamowanie", "FMVSS 121 (USA): ciągnik 2-osiowy obciążony + niehamowana naczepa kontrolna, 60 mph (96.6 km/h)", "250", "ft (= 76.2 m, przeliczenie 0.3048)", "SOURCED", Q,
  "60 280 310 250 310 335 235 613 720", "FMVSS121", "≈ 50 (ESTIMATED: 80→0 MFDD 7.1–7.5 → 96.6 km/h)", PV, "OK (spełnia z zapasem)", "bez zmian",
  "kolumna (3) 'Loaded Tractors with Two Axles ... Tested with an Unbraked Control Trailer'; bobtail (6) 235 ft = 71.6 m")
r("hamowanie", "Zmierzone drogi hamowania 80→0 zestawu 40 t z EBS (publikacje pomiarowe)", "—", "m", "UNVERIFIED",
  "źródła pomiarowe zablokowane w tej sesji: NHTSA DOT HS 812 176 i 809 700 (403 Akamai), ROSA P dot_32424 (403), MDPI app13095336 (403) — tylko link, nie pobrano", "", "",
  "34.9–40.5 m", PV, "brak źródła", "pozyskać w sesji lokalnej (przeglądarka) — NHTSA 812176 tabele stop distance 60 mph", "")

# ---------------- 9. Zawieszenie ---------------------------------------------------------------------------------
r("zawieszenie", "Częstotliwość własna masy resorowanej (model ciężarówki, symulacja)", "1.32", "Hz", "SOURCED", Q,
  "The first peak corresponds to the natural frequency of the sprung mass, which is 1.32 Hz", "VARGH", "1.3 (tył) / 1.5 (przód, naczepa)",
  VRD + " §Suspension", "OK", "bez zmian", "praca dyplomowa — symulacja (nie pomiar); jedno źródło")
r("zawieszenie", "Częstotliwość własna masy nieresorowanej (model ciężarówki)", "12.05", "Hz", "SOURCED", Q,
  "The natural frequency of the un-sprung mass, which is 12.05 Hz", "VARGH", "nie wyznaczana", "", "brak w grze", "opcjonalnie sprawdzić w teście koleiny", "")
r("zawieszenie", "Ugięcia / skoki zawieszenia ciągnika i naczepy (karty)", "—", "mm", "UNVERIFIED",
  "w otwartych kartach znaleziono tylko tolerancję wysokości: 'Height can vary ± 20 mm for leaf and ± 10 mm for air suspension' (FH 42T 3A) — skok nie podany",
  "", "", "0.18 / 0.20", VRD + " §Suspension travel", "brak źródła", "pozostaje WORKING_VALUE", "")


# ---------------- zapis + weryfikacja --------------------------------------------------------------------------
IMG_PAGE = {"at2612-3.png": 3, "ato2612f-3.png": 3, "r13p43-043.png": 43, "mb29_crop.png": 29}
COLS = ["id", "kategoria", "przedmiot", "wartość", "jednostka", "status", "metoda", "cytat", "url_źródła", "url_pliku", "licencja",
        "autor", "data_dostępu", "sha256", "lat", "lon", "kierunek_deg", "opis_co_widać", "duplikat_sha256", "uwagi",
        "strona_pdf", "plik", "wartość_w_grze", "źródło_w_grze", "ocena", "rekomendacja"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    out, errors, shas = [], [], {}
    for n, x in enumerate(ROWS, 1):
        rid = f"R3-{n:03d}"
        src = S.get(x["src"]) if x["src"] else None
        page = ""
        fpath = ""
        if src:
            fpath = os.path.join(HERE, "files", src["file"])
            if not os.path.exists(fpath):
                errors.append(f"{rid}: brak pliku {src['file']} (uruchom fetch.py)")
            else:
                shas.setdefault(src["file"], sha(fpath))
                if x["img"]:
                    page = IMG_PAGE[x["img"]]
                    if not os.path.exists(os.path.join(HERE, "files", "_view", x["img"])):
                        errors.append(f"{rid}: brak obrazu kontrolnego {x['img']}")
                    if x["src"] == "MBPT":  # tabela MB ma też warstwę tekstu
                        if find(src["file"], "11.639 7.035 4.400 2.645 1.599 1.000") != 29:
                            errors.append(f"{rid}: tabela MB nie na s. 29")
                else:
                    page = find(src["file"], x["cytat"])
                    if page is None:
                        errors.append(f"{rid}: CYTAT NIE ZNALEZIONY w {src['file']}: {x['cytat']!r}")
                        page = ""
        elif x["status"] == "SOURCED":
            errors.append(f"{rid}: SOURCED bez źródła")
        out.append({
            "id": rid, "kategoria": x["kat"], "przedmiot": x["przedmiot"], "wartość": x["wart"], "jednostka": x["jedn"],
            "status": x["status"], "metoda": x["metoda"], "cytat": x["cytat"],
            "url_źródła": src["url"] if src else "", "url_pliku": src["dl"] if src else "",
            "licencja": src["lic"] if src else "", "autor": src["autor"] if src else "", "data_dostępu": D,
            "sha256": shas.get(src["file"], "") if src else "", "lat": "n/d", "lon": "n/d", "kierunek_deg": "n/d",
            "opis_co_widać": (f"strona PDF {page} wyrenderowana i obejrzana; widać tabelę/wykres z liczbami z kolumny wartość" if x["img"] else ""),
            "duplikat_sha256": "", "uwagi": x["uwagi"], "strona_pdf": page, "plik": src["file"] if src else "",
            "wartość_w_grze": x["gra"], "źródło_w_grze": x["gra_zr"], "ocena": x["ocena"], "rekomendacja": x["rek"],
        })
    with open(os.path.join(HERE, "manifest.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    st = {}
    for o in out:
        st[o["status"]] = st.get(o["status"], 0) + 1
    print(f"wierszy: {len(out)}; statusy: {st}; dokumentów: {len(shas)}")
    for e in errors:
        print("BŁĄD", e)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
