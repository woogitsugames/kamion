"""R1: manifest.csv (fakty liczbowe z cytatem i stroną PDF) + sizes.csv (tabele wymiarów do generatora znaków).

Użycie (z katalogu pakietu): python -I tools/build_manifest.py .
Wszystkie liczby przepisano ręcznie z PDF (tekst pdftotext + kontrola rastra strony, patrz README §Metoda).
Strona = numer strony w pliku PDF (dla 2311 cz. 1 i 2310 równy numerowi strony Dziennika Ustaw).
"""
import csv, math, sys
from pathlib import Path

OUT = Path(sys.argv[1])
ACC = "2026-11-14"
LIC = "akt normatywny - nie podlega prawu autorskiemu (art. 4 pkt 2 ustawy o prawie autorskim)"
ACTS = {  # klucz: (url ELI PDF, plik, sha256, autor/tytuł skrócony)
    "2311": ("https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text/O/D20192311-c1.pdf", "files/D20192311-c1.pdf",
             "f94925ec05a75ca8cc1cea478727592a3b1b4c9822cdc76b309420556b550543",
             "Minister Infrastruktury; t.j. rozp. z 3.07.2003 (Dz.U. 2019 poz. 2311), zał. 1"),
    "2310": ("https://api.sejm.gov.pl/eli/acts/DU/2019/2310/text/O/D20192310.pdf", "files/D20192310.pdf",
             "c9972e947cf244c13e1d56bb0c2a97a4d248a8066021ae0fbece1441ec710a9d",
             "MI i MSWiA; t.j. rozp. z 31.07.2002 (Dz.U. 2019 poz. 2310)"),
    "2021/433": ("https://api.sejm.gov.pl/eli/acts/DU/2021/433/text/O/D20210433.pdf", "files/D20210433.pdf",
                 "bcf1b019c5cef4f6b205cbbdc867eec1eb6763cd1937fbd5369e4232a43e5764", "MI i MSWiA; nowelizacja 2310"),
    "2021/2065": ("https://api.sejm.gov.pl/eli/acts/DU/2021/2065/text/O/D20212065.pdf", "files/D20212065.pdf",
                  "f1cdfe6e1ab0eff45ad46014dddedb167d2e7b2bf92a555fea73fe4d5b21e772", "MI i MSWiA; nowelizacja 2310"),
    "2021/2066": ("https://api.sejm.gov.pl/eli/acts/DU/2021/2066/text/O/D20212066.pdf", "files/D20212066.pdf",
                  "7bda04e7224cdae021155ea628471181e30c33686e6b3f1d1490d6d4987df3d7", "MI; nowelizacja 2311"),
    "2022/2377": ("https://api.sejm.gov.pl/eli/acts/DU/2022/2377/text/O/D20222377.pdf", "files/D20222377.pdf",
                  "4da83eeffbf400b384643e80d51cf677f8b847e8039e6ff39340dc55bc829248", "MI; nowelizacja 2311"),
    "2026/132": ("https://api.sejm.gov.pl/eli/acts/DU/2026/132/text/O/D20260132.pdf", "files/D20260132.pdf",
                 "6b62d655268234944a36ad4aadd93582656d383dc3cc761dd30d568d6334c3a6", "MI; nowelizacja 2311"),
    "2026/133": ("https://api.sejm.gov.pl/eli/acts/DU/2026/133/text/O/D20260133.pdf", "files/D20260133.pdf",
                 "6c7343fd63ec1664dce4f5f4f390a164cf8ab138b69e52d6439aa8a0c03976ad", "MI i MSWiA; nowelizacja 2310"),
}
ROWS = []


def F(kat, przedmiot, wart, jedn, cytat, akt, punkt, strona, status="SOURCED", metoda=None, uwagi="", grupa="", ksztalt=""):
    url, plik, sha, autor = ACTS[akt]
    ROWS.append({
        "id": f"R1-{len(ROWS) + 1:03d}", "kategoria": kat, "przedmiot": przedmiot, "wartość": wart, "jednostka": jedn,
        "status": status,
        "metoda": metoda or "odczyt tekstu PDF (pdftotext -layout) + kontrola rastra strony (110-300 dpi)",
        "cytat": cytat, "akt": ("Dz.U. %s poz. %s" % tuple(akt.split("/"))) if "/" in akt else f"Dz.U. 2019 poz. {akt}",
        "punkt": punkt, "strona_pdf": strona, "url_źródła": url, "url_pliku": url, "licencja": LIC, "autor": autor,
        "data_dostępu": ACC, "sha256": sha, "lat": "", "lon": "", "kierunek_deg": "", "opis_co_widać": "",
        "duplikat_sha256": "", "grupa_wielkości": grupa, "kształt": ksztalt, "uwagi": uwagi})


G = ["W", "D", "S", "M", "MI"]
GN = {"W": "wielkie", "D": "duże", "S": "średnie", "M": "małe", "MI": "mini"}
# ---------------- 1. wymiary podstawowe: tabela 1.1 (2311 PDF s. 9) ----------------
T11 = {"A": [1200, 1050, 900, 750, 600], "BC": [1000, 900, 800, 600, 400], "D_l": [1200, 900, 600, 600, 400],
       "D_h": ["1200+300n", "900+225n", "600+150n", "600+150n", "400+100n"]}
for i, g in enumerate(G):
    F("wymiary", "A - długość boku trójkąta", T11["A"][i], "mm", f"TABELA 1.1 […] {GN[g]} {g} {T11['A'][i]}", "2311", "zał. 1 pkt 1.2.1, tab. 1.1", 9, grupa=g, ksztalt="trójkąt")
for i, g in enumerate(G):
    F("wymiary", "B i C - średnica tarczy", T11["BC"][i], "mm", f"TABELA 1.1 […] B zakazu C nakazu średnica: {GN[g]} {T11['BC'][i]}", "2311", "zał. 1 pkt 1.2.1, tab. 1.1", 9, grupa=g, ksztalt="koło")
for i, g in enumerate(G):
    F("wymiary", "D - długość podstawy l", T11["D_l"][i], "mm", f"TABELA 1.1 […] D informacyjne długość podstawy: {GN[g]} {T11['D_l'][i]}", "2311", "zał. 1 pkt 1.2.1, tab. 1.1", 9, grupa=g, ksztalt="kwadrat/prostokąt")
    F("wymiary", "D - wysokość h (n = 0, 1, 2)", T11["D_h"][i], "mm", f"wysokość (n = 0, 1, 2) […] {T11['D_h'][i].replace('n', ' n')}", "2311", "zał. 1 pkt 1.2.1, tab. 1.1", 9, grupa=g, ksztalt="kwadrat/prostokąt")
# ---------------- tabela 2.1 A (PDF s. 49) ----------------
T21 = {"W": (1200, 72, 32, 40, 120), "D": (1050, 63, 28, 35, 105), "S": (900, 54, 24, 30, 90), "M": (750, 45, 20, 25, 75), "MI": (600, 36, 16, 20, 60)}
for g, (b, R, r, s, a) in T21.items():
    for nm, v in (("promień wyokrąglenia R (zewn.)", R), ("promień wyokrąglenia r (wewn.)", r), ("szerokość obrzeża s", s), ("moduł a", a)):
        F("wymiary", f"A - {nm}", v, "mm", f"Tabela 2.1. Wymiary znaków ostrzegawczych […] {GN[g]} {b} {R} {r} {s} {a}", "2311", "zał. 1 pkt 2.1.1, tab. 2.1", 49, grupa=g, ksztalt="trójkąt")
F("wymiary", "A-7 - dostępne grupy wielkości", "D, S", "", "Nie dotyczy znaków A-7, które mogą występować tylko jako znaki duże i średnie.", "2311", "zał. 1 pkt 2.1.1, tab. 2.1 przypis", 49, ksztalt="trójkąt odwrócony")
# ---------------- tabela 3.1 B (PDF s. 97) ----------------
T31 = {"W": (1000, 100, 10, 150, 100), "D": (900, 90, 9, 135, 90), "S": (800, 80, 8, 120, 80), "M": (600, 60, 6, 90, 60), "MI": (400, 40, 4, 60, 40)}
for g, (d, s, gg, p, a) in T31.items():
    for nm, v in (("szerokość obrzeża s (znaki zakazu)", s), ("szerokość obwódki g (znaki uchylające)", gg), ("szerokość ukośnego pasa p (znaki uchylające)", p), ("moduł a", a)):
        F("wymiary", f"B - {nm}", v, "mm", f"Tabela 3.1. Wymiary znaków zakazu i znaków uchylających zakaz […] {GN[g]} {d} {s} {gg} {p} {a}", "2311", "zał. 1 pkt 3.1.1, tab. 3.1", 97, grupa=g, ksztalt="koło")
F("wymiary", "B - kąt ukośnego pasa znaku uchylającego", 68, "°", "rys. 3.1.1.1 b) uchylających zakaz: kąt 68°", "2311", "zał. 1 rys. 3.1.1.1", 97, metoda="odczyt rysunku (raster 110 dpi)")
F("wymiary", "B-20 - średnica (koło wpisane w ośmiokąt)", "900 (D) / 800 (S)", "mm", "Wyszczególnione w tabeli wymiary średnicy dla ośmiokątnego znaku B-20 odnoszą się do średnicy koła wpisanego w ten ośmiokąt", "2311", "zał. 1 pkt 3.1.1", 96, grupa="D, S", ksztalt="ośmiokąt")
F("wymiary", "B-20 - grupy wielkości", "D, S (na drogach z grupą M: S)", "", "Znak ten nie występuje w grupie znaków wielkich, natomiast na drogach, na których stosuje się znaki z grupy małych, znak B-20 powinien mieć wymiar znaku średniego", "2311", "zał. 1 pkt 3.1.1", 96, ksztalt="ośmiokąt")
F("wymiary", "B-20 - szerokość białego obrzeża b", "a/3", "mm (a = moduł)", "b = a/3", "2311", "zał. 1 rys. 9.2.28", 385, metoda="odczyt rysunku konstrukcyjnego (raster 100 dpi)", ksztalt="ośmiokąt")
F("wymiary", "B-39 - wymiary tablicy", "900 × 1300 (R30, obwódka 9, B-35 Ø600)", "mm", "rys. 9.2.47: 900; 1300; Ø600; R30; 9", "2311", "zał. 1 rys. 9.2.47", 395, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 100 dpi)", ksztalt="prostokąt")
F("wymiary", "B-40 - wymiary tablicy", "900 × 900 (R30, obwódka 10, symbol Ø600)", "mm", "rys. 9.2.48: 900; 900; 600; R30; 10", "2311", "zał. 1 rys. 9.2.48", 396, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 90 dpi)", ksztalt="kwadrat")
F("wymiary", "B-43 - wymiary tablicy", "900 × 900 (R30, obwódka 10, B-33 Ø600)", "mm", "rys. 9.2.51: 900; 900; 600; R 30; 10; 150", "2311", "zał. 1 rys. 9.2.51", 397, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 300 dpi)", ksztalt="kwadrat")
F("liternictwo", "B-43 - wysokość cyfr na znaku B-33 (Ø600)", 270, "mm", "rys. 9.2.51: 270", "2311", "zał. 1 rys. 9.2.51", 397, metoda="odczyt wymiaru z rysunku konstrukcyjnego (raster 300 dpi)")
F("wymiary", "B-42 - szerokość pasa ukośnego", "a/2", "mm (a = moduł)", "rys. 9.2.50: a/2; a/10", "2311", "zał. 1 rys. 9.2.50", 397, metoda="odczyt rysunku konstrukcyjnego (raster 100 dpi)", ksztalt="koło")
# ---------------- tabela 4.1 C (PDF s. 157) ----------------
T41 = {"W": (1000, 10, 100), "D": (900, 9, 90), "S": (800, 8, 80), "M": (600, 6, 60), "MI": (400, 4, 40)}
for g, (d, gg, a) in T41.items():
    F("wymiary", "C - szerokość obwódki g", gg, "mm", f"Tabela 4.1. Wymiary znaków nakazu (mm) […] {GN[g]} {d} {gg} {a}", "2311", "zał. 1 pkt 4.1.1, tab. 4.1", 157, grupa=g, ksztalt="koło")
    F("wymiary", "C - moduł a", a, "mm", f"Tabela 4.1. Wymiary znaków nakazu (mm) […] {GN[g]} {d} {gg} {a}", "2311", "zał. 1 pkt 4.1.1, tab. 4.1", 157, grupa=g, ksztalt="koło")
F("wymiary", "C-17 - wymiary tablicy", "900 × 1200 (R30, obwódka 10, C-2 Ø400)", "mm", "rys. 9.3.13: 900; 1200; Ø400; R30; 10", "2311", "zał. 1 rys. 9.3.13", 404, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 100 dpi)", ksztalt="prostokąt")
# ---------------- tabela 5.1 D (PDF s. 178) ----------------
T51 = {"W": (1200, "l+300n", 880, 160, "300n+160", 12, 30, 120), "D": (900, "l+225n", 660, 120, "225n+120", 9, 30, 90),
       "S/M": (600, "l+150n", 440, 80, "150n+80", 6, 30, 60), "MI": (400, "l+100n", 300, 50, "100n+50", 4, 30, 40)}
for g, (l, h, s, b, c, gg, r, a) in T51.items():
    for nm, v in (("bok białego pola s", s), ("margines białego pola b", b), ("wysokość części dolnej c", c),
                  ("szerokość obwódki g = l/100", gg), ("promień naroża r", r), ("moduł a", a)):
        F("wymiary", f"D - {nm}", v, "mm", f"Tabela 5.1. Wymiary znaków informacyjnych (mm) […] {g} {l} {h} {s} {b} {c} {gg} {r} {a}", "2311", "zał. 1 pkt 5.1.1, tab. 5.1", 178, grupa=g, ksztalt="kwadrat/prostokąt")
F("wymiary", "D-1, D-2 - szerokość obwódki g", "l/50", "mm", "Dla znaków D-1 i D-2 wymiar g wynosi 1/50 l, a dla znaków D-42–D-47 wymiar g wynosi 1/60 l.", "2311", "zał. 1 tab. 5.1 przypis", 178, ksztalt="romb")
F("wymiary", "D-42–D-47 - szerokość obwódki g", "l/60", "mm", "dla znaków D-42–D-47 wymiar g wynosi 1/60 l", "2311", "zał. 1 tab. 5.1 przypis", 178)
F("wymiary", "D-1 - bok znaku powtarzanego wzdłuż drogi", 400, "mm", "Wzdłuż drogi z pierwszeństwem powtarza się znaki D-1 o zmniejszonej do 400 mm długości boku", "2311", "zał. 1 pkt 5.2.1.1", 185, ksztalt="romb")
F("wymiary", "D-42/D-43 - wymiary", "1200 × 700", "mm", "Znaki D-42 i D-43 mają wymiary: długość podstawy 1200 mm, wysokość 700 mm.", "2022/2377", "§ 1 pkt 1 lit. b (zał. 1 pkt 5.2.48.1)", 4, ksztalt="prostokąt")
F("wymiary", "D-42/D-43 - wysokość dopuszczalna na jednojezdniowych drogach powiatowych i gminnych", 600, "mm", "Na jednojezdniowych drogach powiatowych i gminnych dopuszcza się znaki D-42 i D-43 o wysokości 600 mm.", "2022/2377", "§ 1 pkt 1 lit. b (zał. 1 pkt 5.2.48.1)", 4, uwagi="t.j. 2019 (PDF s. 244) miał 530 mm - zmienione nowelizacją 2022", ksztalt="prostokąt")
F("wymiary", "D-19 - wymiary", "600 × 300 (R30; napis TAXI 210)", "mm", "rys. 9.4.27: 600; 300; 210; R30", "2311", "zał. 1 rys. 9.4.27", 420, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 100 dpi)", ksztalt="prostokąt")
F("wymiary", "D - znaki jednej wielkości / zmniejszone", "D-19, D-20, D-39, D-40, D-41", "", "Dotyczy to znaków: D-19, D-20, D-39, D-40 i D-41.", "2311", "zał. 1 pkt 5.1.1", 176)
# ---------------- F (rysunki) ----------------
F("wymiary", "F-12 - wymiary", "600 × 750", "mm", "rys. 9.6.16: 600; 750", "2311", "zał. 1 rys. 9.6.16", 481, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 100 dpi)", ksztalt="prostokąt")
F("wymiary", "F-13 - wymiary", "wys. 400; korpus 650 + grot 200", "mm", "rys. 9.6.17: 400; 650; 200", "2311", "zał. 1 rys. 9.6.17", 481, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 100 dpi)", ksztalt="strzała")
F("wymiary", "F-22 - wymiary", "1400 × 1960 (R30)", "mm", "rys. 9.6.30: 1400; 1960; R30", "2311", "zał. 1 rys. 9.6.30", 487, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 110 dpi)", ksztalt="prostokąt")
F("wymiary", "F, G, T - zasada wymiarowania", "wymiary w opisach szczegółowych", "", "Wymiary znaków kategorii F, G i tabliczek T oraz szczegółowe wymiary wszystkich znaków podane są w opisach szczegółowych.", "2311", "zał. 1 pkt 1.2.1", 9)
# ---------------- tabela 9.7.1 T (PDF s. 487) ----------------
T971 = {"wielkie i duże": (162, 132, 350, 10, 30, 70, 84, 80, 54, 125, 27), "średnie i małe": (132, 102, 250, 10, 30, 20, 49, 65, 44, 82, 22)}
SYM = ["d", "d1", "h", "c", "r", "z", "l", "g", "g1", "k", "gr"]
MEAN = {"d": "wysokość cyfr/liter dużych d", "h": "wysokość tabliczki h", "r": "promień naroża r", "gr": "grubość liter gr",
        "c": "odstęp obwódki c", "d1": "d1", "z": "z", "l": "l", "g": "g (odstęp napisu od krawędzi)", "g1": "g1", "k": "k"}
for g, vals in T971.items():
    for s, v in zip(SYM, vals):
        F("wymiary" if s not in ("d", "d1", "gr") else "liternictwo", f"T (tabliczki) - {MEAN[s]}", v, "mm",
          f"Tabela 9.7.1. Wymiary tabliczek do znaków drogowych […] {g} " + " ".join(map(str, vals)), "2311", "zał. 1 pkt 9.7, tab. 9.7.1", 487, grupa=g,
          ksztalt="prostokąt", uwagi="" if s in ("d", "h", "r", "gr", "c", "g") else "znaczenie symbolu tylko z rys. 9.7.1 - UNVERIFIED interpretacja")
# ---------------- zasady doboru grupy wielkości (PDF s. 7-8) ----------------
F("grupa_wielkości", "W - zastosowanie", "autostrady, przy jezdniach głównych", "", "a) znaki wielkie (W) – na autostradach, umieszczane przy jezdniach głównych,", "2311", "zał. 1 pkt 1.2.1 lit. a", 7, grupa="W")
F("grupa_wielkości", "D - zastosowanie", "ekspresowe (jezdnie główne); dwujezdniowe poza obszarem zabudowanym; dwujezdniowe w obszarze zabudowanym > 60 km/h", "",
  "b) znaki duże (D): – na drogach ekspresowych, umieszczane przy jezdniach głównych, – na drogach dwujezdniowych poza obszarem zabudowanym, – na drogach dwujezdniowych w obszarze zabudowanym, na których dopuszczalna prędkość jest większa niż 60 km/h", "2311", "zał. 1 pkt 1.2.1 lit. b", 7, grupa="D")
F("grupa_wielkości", "S - zastosowanie", "łącznice A/S; dwujezdniowe w obszarze zabudowanym ≤ 60 km/h; jednojezdniowe krajowe i wojewódzkie; powiatowe (bez drogowskazów tablicowych)", "",
  "c) znaki średnie (S): – na łącznicach […] – na drogach dwujezdniowych w obszarze zabudowanym, na których dopuszczalna prędkość jest mniejsza lub równa 60 km/h, – na jednojezdniowych drogach krajowych i wojewódzkich, – na drogach powiatowych, z wyjątkiem drogowskazów tablicowych", "2311", "zał. 1 pkt 1.2.1 lit. c", "7-8", grupa="S")
F("grupa_wielkości", "M - zastosowanie", "drogi gminne; drogowskazy tablicowe na powiatowych", "", "d) znaki małe (M): – na drogach gminnych, – drogowskazy tablicowe na drogach powiatowych,", "2311", "zał. 1 pkt 1.2.1 lit. d", 8, grupa="M")
F("grupa_wielkości", "MI - zastosowanie", "słupki przeszkodowe; obszar zabudowany przy braku miejsca; strefa zamieszkania i tempo 30; drogi rowerowe/piesze", "",
  "e) znaki mini (MI): – na słupkach przeszkodowych i tablicach kierujących, – na drogach w obszarze zabudowanym, gdy warunki drogowe nie pozwalają na stosowanie znaków większych […] – na drogach położonych w strefie zamieszkania oraz strefie ograniczonej prędkości do 30 km/h", "2311", "zał. 1 pkt 1.2.1 lit. e", 8, grupa="MI")
F("grupa_wielkości", "roboty drogowe - grupa wielkości", "+1 grupa (na autostradach: W)", "", "Przy oznakowaniu robót prowadzonych w pasie drogowym stosuje się znaki o jedną grupę wielkości wyższą niż stosowane na danym odcinku drogi (z wyjątkiem robót prowadzonych w pasie drogowym autostrad, gdzie stosuje się znaki wielkie).", "2311", "zał. 1 pkt 1.2.1", 8)
F("grupa_wielkości", "A-7, B-20 - grupa wielkości", "jak na drodze z pierwszeństwem, min. S", "", "Znaki A-7, B-20 powinny mieć taką samą grupę wielkości jak znaki na drodze z pierwszeństwem przejazdu, jednak nie mniejszą niż grupa wielkości znaków średnich.", "2311", "zał. 1 pkt 1.2.1", 8)
F("grupa_wielkości", "C-9, C-10, C-11 - grupa wielkości", "dopuszczalnie niższa", "", "Znaki nakazu C-9, C-10, C-11, w zależności od warunków widoczności, mogą być stosowane w grupach wielkości niższych niż obowiązujące na danej drodze.", "2311", "zał. 1 pkt 1.2.1", 8)
# ---------------- 2. barwy: tabela 1.3 / 1.4 (PDF s. 11) ----------------
T13 = {"biała": ((0.355, 0.355), (0.305, 0.305), (0.285, 0.325), (0.335, 0.375), 0.35, 0.27),
       "żółta": ((0.545, 0.454), (0.487, 0.423), (0.427, 0.483), (0.465, 0.534), 0.27, 0.16),
       "czerwona": ((0.735, 0.265), (0.674, 0.236), (0.569, 0.341), (0.655, 0.345), 0.05, 0.03),
       "zielona": ((0.007, 0.703), (0.248, 0.409), (0.177, 0.362), (0.026, 0.399), 0.04, 0.03),
       "niebieska": ((0.078, 0.171), (0.150, 0.220), (0.210, 0.160), (0.137, 0.038), 0.01, 0.01),
       "pomarańczowa": ((0.610, 0.390), (0.535, 0.375), (0.506, 0.404), (0.570, 0.429), 0.15, 0.14),
       "brązowa": ((0.455, 0.397), (0.523, 0.429), (0.479, 0.373), (0.558, 0.394), 0.03, 0.03),
       "szara": ((0.350, 0.360), (0.300, 0.310), (0.285, 0.325), (0.335, 0.375), 0.12, 0.12)}
fmt = lambda p: f"{p[0]:.3f};{p[1]:.3f}".replace(".", ",")
for col, (p1, p2, p3, p4, b1, b2) in T13.items():
    pts = " | ".join(fmt(p) for p in (p1, p2, p3, p4))
    F("barwa_CIE", f"barwa {col} - narożniki pola tolerancji (x;y) 1-4, folia typu 1 i 2", pts, "CIE 1931 xy",
      f"Tabela 1.3 […] {col.capitalize()} x {p1[0]} {p2[0]} {p3[0]} {p4[0]} y {p1[1]} {p2[1]} {p3[1]} {p4[1]}".replace(".", ","), "2311", "zał. 1 pkt 1.3.1, tab. 1.3", 11)
    F("barwa_CIE", f"barwa {col} - min. współczynnik luminancji β, folia typu 1", b1, "-", f"Tabela 1.3 […] {col.capitalize()} […] {str(b1).replace('.', ',')} {str(b2).replace('.', ',')}", "2311", "zał. 1 pkt 1.3.1, tab. 1.3", 11)
    F("barwa_CIE", f"barwa {col} - min. współczynnik luminancji β, folia typu 2", b2, "-", f"Tabela 1.3 […] {col.capitalize()} […] {str(b1).replace('.', ',')} {str(b2).replace('.', ',')}", "2311", "zał. 1 pkt 1.3.1, tab. 1.3", 11)
F("barwa_CIE", "warunki pomiaru barwy", "45°/0°, obserwator 2°, iluminant D65", "", "Pomiary przeprowadzone sferycznym spektrokolorytmetrem w geometrii pomiaru 45°/0° dla 2° obserwatora, przy zastosowaniu standardowego, polichromatycznego źródła światła CIE D65", "2311", "zał. 1 tab. 1.3 uwaga", 11)
T14 = {"szara": ((0.305, 0.315), (0.350, 0.360), (0.340, 0.370), (0.295, 0.325), "0,08–0,10"), "czarna": ((0.300, 0.270), (0.385, 0.335), (0.345, 0.395), (0.360, 0.310), "≤ 0,02")}
for col, (p1, p2, p3, p4, beta) in T14.items():
    F("barwa_CIE", f"powłoka kryjąca {col} - narożniki pola tolerancji (x;y) 1-4", " | ".join(fmt(p) for p in (p1, p2, p3, p4)), "CIE 1931 xy",
      f"Tabela 1.4 […] {col.capitalize()} x {p1[0]} {p2[0]} {p3[0]} {p4[0]} y {p1[1]} {p2[1]} {p3[1]} {p4[1]}".replace(".", ","), "2311", "zał. 1 pkt 1.3.1, tab. 1.4", 11)
    F("barwa_CIE", f"powłoka kryjąca {col} - współczynnik luminancji β", beta, "-", f"Tabela 1.4 […] {col.capitalize()} […] {beta}", "2311", "zał. 1 pkt 1.3.1, tab. 1.4", 11)
F("barwa_CIE", "odpowiedniki RAL", "brak w akcie", "", "(akt podaje wyłącznie współrzędne CIE x,y i β - tab. 1.3, 1.4; słowo „RAL” nie występuje w zał. 1)", "2311", "zał. 1 pkt 1.3", 11, status="SOURCED", metoda="przeszukanie pełnego tekstu zał. 1 (grep 'RAL') - 0 trafień w tym kontekście")
F("barwa_CIE", "PN-EN 12899-1 - współrzędne barw", "nie sprawdzono (norma płatna)", "", "", "2311", "-", "-", status="UNVERIFIED", metoda="norma PKN niedostępna otwarcie; akt odsyła do „odpowiedniej normy” (pkt 1.3.2 w brzmieniu Dz.U. 2022 poz. 2377)")
# sRGB pochodne (ESTIMATED): środek ciężkości narożników, Y = β_min folii typu 1 (dolna granica jasności)
def xyY_to_srgb(x, y, Y):
    X, Z = x * Y / y, (1 - x - y) * Y / y
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z; g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z; b = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    enc = lambda c: 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)
    return tuple(int(round(min(255, max(0, enc(max(0.0, c)))))) for c in (r, g, b))
SRGB = {}
for col, (p1, p2, p3, p4, b1, b2) in T13.items():
    cx = sum(p[0] for p in (p1, p2, p3, p4)) / 4; cy = sum(p[1] for p in (p1, p2, p3, p4)) / 4
    SRGB[col] = (cx, cy, b1, xyY_to_srgb(cx, cy, b1))
    F("barwa_sRGB_pochodna", f"barwa {col} - sRGB z centroidu pola i β_min typu 1", "#%02X%02X%02X" % SRGB[col][3], "sRGB 8-bit",
      f"centroid x={cx:.3f} y={cy:.3f}, Y={b1}", "2311", "pochodna tab. 1.3", 11, status="ESTIMATED",
      metoda="obliczenie: centroid 4 narożników (x,y) z tab. 1.3, Y = β_min folii typu 1, konwersja xyY→XYZ→sRGB (D65, IEC 61966-2-1); to DOLNA granica jasności, realne folie są jaśniejsze")
# ---------------- odblaskowość (PDF s. 12) ----------------
R5 = {"biała": (70, 250), "żółta": (50, 170), "czerwona": (14.5, 45), "zielona": (9, 45), "niebieska": (4, 20), "brązowa": (1.0, 12), "pomarańczowa": (25, 100)}
for col, (t1, t2) in R5.items():
    F("odblask", f"R' min. {col}, α=0,2°, β1=5°, folia typu 1", t1, "cd/(lx·m²)", f"Tabela 1.5 […] 0,2° 5° […] {col} {str(t1).replace('.', ',')}", "2311", "zał. 1 pkt 1.3.2, tab. 1.5", 12)
    F("odblask", f"R' min. {col}, α=0,2°, β1=5°, folia typu 2", t2, "cd/(lx·m²)", f"Tabela 1.6 […] 0,2° 5° […] {col} {t2}", "2311", "zał. 1 pkt 1.3.2, tab. 1.6", 12)
F("odblask", "folia pryzmatyczna - wymagania R'", "jak typ 2", "", "Dla folii pryzmatycznych obowiązują wymagania jak dla folii typu 2.", "2022/2377", "§ 1 pkt 1 lit. a (zał. 1 pkt 1.3.2)", 1)
# ---------------- 5. folie (tab. 1.2, PDF s. 10) ----------------
T12 = [("obok jezdni", "autostrady i drogi ekspresowe", "2"), ("obok jezdni", "drogi krajowe dwujezdniowe", "2"),
       ("obok jezdni", "drogi krajowe jednojezdniowe międzynarodowe", "2"), ("obok jezdni", "inne krajowe jednojezdniowe", "1(*)"),
       ("obok jezdni", "drogi wojewódzkie", "1(*)"), ("obok jezdni", "drogi powiatowe i gminne", "1(*)"),
       ("nad jezdnią", "autostrady i drogi ekspresowe", "pryzmatyczna"), ("nad jezdnią", "pozostałe kategorie dróg", "2")]
for pos, road, typ in T12:
    F("folia", f"typ folii - {pos}, {road}", typ, "typ", f"Tabela 1.2. Typy folii odblaskowej […] {pos} […] {road}: {typ}", "2311", "zał. 1 pkt 1.2.2, tab. 1.2", 10, metoda="odczyt tabeli-rastra (110 dpi)")
F("folia", "wyjątek (*) - znaki zawsze na folii typu 2", "A-7, B-2, B-20, D-6, D-6a, D-6b", "", "W przypadku znaków A-7, B-2, B-20, D-6, D-6a, D-6b obowiązuje stosowanie folii odblaskowych typu 2.", "2311", "zał. 1 tab. 1.2 przypis (*)", 10)
F("folia", "roboty w pasie drogowym", "typ 2 lub pryzmatyczna", "", "Do wykonywania lic znaków stosowanych do oznakowania robót prowadzonych w pasie drogowym stosuje się folię odblaskową typu 2 lub folię pryzmatyczną.", "2311", "zał. 1 pkt 1.2.2", 10)
F("folia", "znaki nad jezdnią na A/S", "pryzmatyczna", "", "Do wykonywania lic znaków umieszczanych nad jezdnią na autostradach i drogach ekspresowych stosuje się folię pryzmatyczną.", "2311", "zał. 1 pkt 1.2.2", 10)
F("folia", "odblaskowo-fluorescencyjna żółto-zielona/pomarańczowa - dopuszczenie", "A-10, A-14, A-17, A-30, T-27; D-6/6a/6b, T-27 (tło żółto-zielone; pomarańczowe w czasowej org.); D-51, D-51a (żółto-zielone)", "",
  "Dopuszcza się stosowanie folii pryzmatycznej odblaskowo-fluorescencyjnej żółto-zielonej lub pomarańczowej do wykonania lic znaków odblaskowych: A-10, A-14, A-17 i A-30 oraz tabliczki T-27 […] D-6, D-6a i D-6b oraz tabliczki T-27 […] D-51 i D-51a", "2021/2066", "§ 1 pkt 1 lit. a (zał. 1 pkt 1.2.2 akapit ostatni)", 1)
F("folia", "rewers tarczy", "barwa szara", "", "Odwrotna strona tarczy znaku i tabliczki, jeżeli nie jest wykorzystana do umieszczenia znaku dla jadących z przeciwnego kierunku, powinna mieć barwę szarą.", "2021/2066", "§ 1 pkt 1 lit. a (zał. 1 pkt 1.2.2)", 1)
F("folia", "T-34 - typ folii", "typ 2", "", "Lico tabliczki powinno być wykonane z folii odblaskowej typu 2.", "2311", "zał. 1 pkt 6.3.7.9", 291)
# ---------------- 3. liternictwo ----------------
T18 = {"I": (42, 28, 7, 56, 14, 70), "II": (72, 48, 12, 96, 24, 120), "III": (102, 68, 17, 136, 34, 170), "IV": (132, 88, 22, 176, 44, 220),
       "V": (162, 108, 27, 216, 54, 270), "VI": (210, 140, 35, 280, 70, 350), "VII": (282, 188, 47, 376, 94, 470),
       "VIII": (348, 232, 58, 464, 116, 580), "IX": (420, 280, 70, 560, 140, 700)}
for g, (d, m, gr, w, i, p) in T18.items():
    F("liternictwo", f"grupa liter {g} - wysokość liter dużych i cyfr d", d, "mm", f"Tabela 1.8. Wielkość liter i cyfr […] {g} {d} {m} {gr} {w} {i} {p}", "2311", "zał. 1 pkt 1.4.2, tab. 1.8", 16, grupa=g, metoda="odczyt tabeli-rastra (110 dpi)",
      uwagi=f"m={m}, gr={gr}, w={w}, i={i}, p={p} mm (ten sam wiersz tabeli)")
F("liternictwo", "proporcje pisma", "d = 6 gr; m = 4 gr; w = 8 gr; i = 2 gr; p = 10 gr", "gr", "wysokość liter dużych i cyfr d = 6 gr, – zasadnicza wysokość liter małych m = 4 gr, – wysokość wiersza pisma w = 8 gr, – minimalna odległość między wierszami, tzw. interlinia i = 2 gr, – wysokość pasa pisma p = w + i = 10 gr.", "2311", "zał. 1 pkt 1.4.1", 15)
F("liternictwo", "odstęp międzyliterowy o", "1,5 gr (folia pryzmatyczna: 1,8 gr)", "gr", "Odstęp międzyliterowy i między cyframi […] wynosi „o” = 1,5 gr. Jednak dla napisów wykonywanych z folii odblaskowej pryzmatycznej […] „o” = 1,8 gr.", "2311", "zał. 1 pkt 1.4.2", 15)
F("liternictwo", "odstęp międzywyrazowy h", "4,5 gr (= 3 o)", "gr", "Odstęp międzywyrazowy wynosi h = 3 o = 4,5 gr.", "2311", "zał. 1 pkt 1.4.2", 15)
F("liternictwo", "odstęp napisu od obwódki (poziomo)", "min. 2 gr", "gr", "Odstęp poziomy między napisem a obwódką powinien wynosić co najmniej 2 gr", "2311", "zał. 1 pkt 1.4.2", 15)
F("liternictwo", "szerokości znaków pisma", "tab. 1.10 (np. A 4,34; O 5,00; a 3,75; cyfra 0 3,40 gr)", "gr", "Tabela 1.10 […] A 4,34 […] O 5,00 […] a 3,75 […] 0 3,40", "2311", "zał. 1 pkt 1.4.2, tab. 1.10", 18)
F("liternictwo", "krój pisma - definicja w akcie", "wzory liter i cyfr pkt 1.4.3 (rysunki na siatce gr), bez nazwy kroju", "", "Wszelkie napisy na znakach, tabliczkach do znaków oraz na tablicach umieszczonych na potrzeby ruchu drogowego wykonuje się literami i cyframi odpowiadającymi wzorom podanym w punkcie 1.4.3", "2026/132", "§ 1 pkt 1 lit. a (zał. 1 pkt 1.4.1)", 1)
F("liternictwo", "nazwa kroju „Drogowskaz”", "nie występuje w akcie", "", "", "2311", "-", "-", status="UNVERIFIED", metoda="przeszukanie tekstu 2310 i 2311 (grep 'Drogowskaz' jako nazwy kroju, 'krój', 'czcionk') - 0 trafień; nazwa potoczna, źródło nieustalone")
F("liternictwo", "Tabela 1.9 - grupy liter: B znaki zakazu (W/D/S/M)", "VI–III / VI–II / V–II / IV–I", "grupa liter", "B - znaki zakazu (*) VI, V, IV, III | VI, V, IV, III, II | V, IV, III, II | IV,III, II, I", "2311", "zał. 1 tab. 1.9", 17, metoda="odczyt tabeli-rastra (200 dpi, obrót 90°)", uwagi="(*) nie dotyczy B-33 i B-34")
F("liternictwo", "Tabela 1.9 - grupy liter: D znaki informacyjne (W/D/S/M)", "V–III / V–II / IV–I / IV–I", "grupa liter", "D - znaki informacyjne V, IV, III | V, IV, III, II | IV, III, II, I | IV, III, I", "2311", "zał. 1 tab. 1.9", 17, metoda="odczyt tabeli-rastra (200 dpi, obrót 90°)")
F("liternictwo", "Tabela 1.9 - grupy liter: F znaki uzupełniające (wszystkie grupy)", "II, I", "grupa liter", "F - znaki uzupełniające II, I | II, I | II, I | II, I", "2311", "zał. 1 tab. 1.9", 17, metoda="odczyt tabeli-rastra (200 dpi, obrót 90°)")
F("liternictwo", "Tabela 1.9 - grupy liter: T tabliczki (W/D/S/M)", "V, IV / V, IV / IV, III / IV, III", "grupa liter", "T - tabliczki do znaków V, IV | V, IV | IV, III | IV, III", "2311", "zał. 1 tab. 1.9", 17, metoda="odczyt tabeli-rastra (200 dpi, obrót 90°)")
F("liternictwo", "napisy na tabliczkach pod znakami zakazu - wysokość", "72 lub 42", "mm", "Napisy na tabliczkach, w zależności od długości tekstu, powinny mieć wysokość 72 lub 42 mm, przy czym napis powinien być tak skomponowany, aby szerokość tabliczki nie była większa od średnicy znaku.", "2311", "zał. 1 pkt 3.1.2", 99)
F("liternictwo", "B-39 - wysokość napisów", "102 (litery duże), 68 (małe), 72 (wiersz „w godz.”)", "mm", "rys. 9.2.47: 102; 68; 102; 68; 102; 72", "2311", "zał. 1 rys. 9.2.47", 395, metoda="odczyt wymiarów z rysunku konstrukcyjnego (raster 100 dpi)")
F("liternictwo", "dokładność liczb na znakach zakazu", "szer./wys. 0,1 m; długość 1 m; masa/nacisk 0,5 t", "", "Liczby określające […] szerokość lub wysokość pojazdu powinny być podawane z dokładnością do 0,1 m […] Długość pojazdu podaje się w metrach całkowitych […] masę i nacisk osi – w tonach z dokładnością do 0,5 t", "2311", "zał. 1 pkt 3.1.2", 99)
# ---------------- 4. montaż ----------------
H = [("A, B, C, D, F, G - poza obszarem zabudowanym", "min. 2,00", "A – ostrzegawcze min. 2,00"),
     ("A, B, C, D, F, G - poza obszarem zabudowanym, kilka znaków na jednej konstrukcji, brak ruchu pieszego", "min. 1,50", "(min. 1,50)5) […] 5) Dla kilku znaków umieszczanych na jednej konstrukcji wsporczej przy braku ruchu pieszego."),
     ("A, B, C, D, F, G - obszar zabudowany", "min. 2,00", "na obszarach zabudowanych […] min. 2,00 (2,20)6)"),
     ("A, B, C, D, F, G - obszar zabudowany, znak na chodniku albo nad chodnikiem", "min. 2,20", "6) W przypadku umieszczenia znaku na chodniku albo nad chodnikiem."),
     ("E-1, E-2, E-14 - poza obszarem zabudowanym", "min. 1,00", "E – tablice przeddrogowskazowe E-1 min. 1,00"),
     ("E-1, E-2, E-14 - obszar zabudowany (w pasie zieleni/na poboczu: min. 1,00)", "min. 2,00 (2,20 na chodniku)", "min. 2,00 (2,20)6) (min. 1,00)4) […] 4) Dla znaków umieszczanych w pasie zieleni poza chodnikiem lub na poboczu."),
     ("E-13, E-15, E-16, E-17a, E-18a, E-4, E-5–E-12, E-19a–E-22 - obszar zabudowany", "2,00 (2,20) – 2,50", "min. 2,00 (2,20)6) – 2,50"),
     ("E - drogowskazy w kształcie strzały duże (E-3)", "min. 0,70", "E – drogowskazy w kształcie strzały – duże min. 0,70 min. 0,70"),
     ("znaki nad jezdnią", "min. 5,00", "Znaki umieszczone nad jezdnią2) min. 5,00 min. 5,00"),
     ("znaki na urządzeniach BRD lub za nimi", "0,90–1,20", "Znaki umieszczone na urządzeniach bezpieczeństwa ruchu lub za tymi urządzeniami7) 0,90–1,20"),
     ("F-11 (wyjątek)", "5,00", "1) Z wyjątkiem znaków F-11 (5,00 m) i F-14a, b, c, d, e, f (min. 0,50 m)."),
     ("F-14a–f (wyjątek)", "min. 0,50", "F-14a, b, c, d, e, f (min. 0,50 m)"),
     ("G-1 (wyjątek)", "1,00 ulice / 0,50 pozostałe", "3) Z wyjątkiem znaków G-1 (1,00 m – na ulicach; 0,50 m – na pozostałych drogach).")]
for przedm, v, cyt in H:
    F("montaż_wysokość", f"wysokość dolnej krawędzi - {przedm}", v, "m", cyt, "2022/2377", "§ 1 pkt 1 lit. a (zał. 1 pkt 1.5.3, tab. 1.11 w nowym brzmieniu)", 2,
      uwagi="tab. 1.11 w t.j. 2019 (PDF s. 37) zmieniona: Dz.U. 2021 poz. 2066 i 2022 poz. 2377 (przypis 6: „albo nad chodnikiem”; F-14d–f)")
F("montaż_wysokość", "punkt odniesienia wysokości", "dolna krawędź (najniższy punkt) znaku; w obszarze zabudowanym na ulicach liczy się tabliczkę pod znakiem", "",
  "Wysokość umieszczania znaków (dolnej krawędzi lub najniżej położonego jej punktu) podano w tabeli 1.11 […] Na ulicach w obszarach zabudowanych przez niżej umieszczony znak rozumieć należy również dodatkowe tabliczki pod znakami.", "2311", "zał. 1 pkt 1.5.3", 32)
F("montaż_wysokość", "nad drogą dla rowerów", "min. 2,50", "m", "w przypadku znaków umieszczanych nad drogą dla rowerów, wysokość umieszczenia znaku powinna wynosić nie mniej niż 2,50 m", "2311", "zał. 1 pkt 1.5.3", 30)
F("montaż_wysokość", "na drodze dla rowerów (z ruchem pieszym: 2,2)", "min. 1,0 (2,2)", "m", "Dopuszcza się umieszczanie znaków na drogach dla rowerów na wysokości nie mniejszej niż 1 m (do najniższej krawędzi znaku), przy czym w przypadku ruchu pieszego wysokość ta powinna wynosić nie mniej niż 2,2 m.", "2311", "zał. 1 pkt 1.5.3", "30-31")
F("montaż_odległość_boczna", "droga z poboczem - od krawędzi korony", "min. 0,5", "m", "odległość znaku od krawędzi korony drogi była nie mniejsza niż 0,5 m", "2311", "zał. 1 pkt 1.5.3", 30)
F("montaż_odległość_boczna", "pobocze gruntowe (gdy nie poza koroną) - od krawędzi jezdni", "min. 0,50", "m", "na drogach z poboczami gruntowymi – na poboczu w odległości nie mniejszej niż 0,50 m od krawędzi jezdni", "2311", "zał. 1 pkt 1.5.3 lit. a", 30)
F("montaż_odległość_boczna", "pobocze twarde (pas awaryjny) - od krawędzi pobocza", "min. 0,50", "m", "w odległości nie mniejszej niż 0,50 m od krawędzi pobocza bitumicznego", "2311", "zał. 1 pkt 1.5.3 lit. b", 30)
F("montaż_odległość_boczna", "szeroki nasyp - maks. od krawędzi jezdni", "maks. 5", "m", "W przypadku szerokiego nasypu znaki można umieszczać w koronie drogi w odległości nie większej niż 5 m od krawędzi jezdni.", "2311", "zał. 1 pkt 1.5.3", 30)
F("montaż_odległość_boczna", "pas dzielący - od zewnętrznej krawędzi opaski", "min. 0,50", "m", "Znaki w pasie dzielącym jezdnie dróg dwujezdniowych umieszcza się w odległości nie mniejszej niż 0,50 m od zewnętrznej krawędzi opaski", "2311", "zał. 1 pkt 1.5.3", 30)
F("montaż_odległość_boczna", "ulice - od krawędzi jezdni", "0,50–2,00", "m", "Znaki na ulicach umieszcza się w odległości 0,50–2,00 m od krawędzi jezdni (rys. 1.5.6 lit. c).", "2311", "zał. 1 pkt 1.5.3", 31)
F("montaż_odległość_boczna", "od osi skrajnego toru tramwajowego", "min. 1,95", "m", "Minimalna odległość umieszczenia znaków od osi skrajnego toru linii tramwajowej biegnącej wzdłuż drogi wynosi 1,95 m", "2311", "zał. 1 pkt 1.5.3", 31)
F("montaż_odległość_boczna", "droga dla rowerów - od krawędzi", "min. 0,50", "m", "Na drodze dla rowerów znaki umieszcza się w odległości nie mniejszej niż 0,50 m od krawędzi tej drogi", "2311", "zał. 1 pkt 1.5.3", 30)
F("montaż_odległość_boczna", "sposób pomiaru odległości bocznej", "poziomo od krawędzi jezdni do najbliższego punktu tarczy; krawężnik miejski wlicza się do chodnika", "",
  "Odległość znaku od jezdni mierzy się w poziomie od krawędzi jezdni (wystający krawężnik drogowy typu miejskiego wlicza się do chodnika) do najbliższego skrajnego punktu tarczy znaku", "2311", "zał. 1 pkt 1.5.3", 32)
F("montaż_odległość_boczna", "znak wspólnie z sygnalizatorem na ulicy - od krawędzi jezdni", "0,50–1,00", "m", "rys. 1.5.7 i): 0,50 ÷ 1,00; min. 2,20", "2311", "zał. 1 rys. 1.5.7 lit. i", 35, metoda="odczyt rysunku (raster 110 dpi)")
F("montaż_kąt", "odchylenie tarczy od prostopadłej do osi jezdni - odcinek prosty", "ok. 5 (w kierunku jezdni)", "°", "Odchylenie tarczy znaków powinno wynosić około 5° w kierunku jezdni.", "2311", "zał. 1 pkt 1.5.2", 29)
F("montaż_kąt", "odchylenie tarczy - łuk w prawo", "0–5", "°", "rys. 1.5.5 b) na łuku poziomym w prawo: 0÷5°", "2311", "zał. 1 rys. 1.5.5 lit. b", 30, metoda="odczyt rysunku (raster 110 dpi)")
F("montaż_kąt", "odchylenie tarczy - łuk w lewo", "5–10", "°", "rys. 1.5.5 c) na łuku poziomym w lewo: 5-10°", "2311", "zał. 1 rys. 1.5.5 lit. c", 30, metoda="odczyt rysunku (raster 110 dpi)")
for v, cond in (("50", "o dopuszczalnej prędkości powyżej 90 km/h"), ("20", "o dopuszczalnej prędkości powyżej 60 km/h"), ("10", "na pozostałych drogach")):
    F("montaż_odstęp", f"min. odstęp kolejnego znaku - drogi {cond}", v, "m", f"Następny znak powinien być umieszczony za poprzedzającym w odległości co najmniej: […] {v} m na drogach {cond}" if v != "10" else "– 10 m na pozostałych drogach.", "2311", "zał. 1 pkt 1.5.2", 28)
F("montaż_konstrukcja", "maks. wysokość betonowej części konstrukcji nad gruntem", 0.15, "m", "Nie wykonuje się z betonu tych części konstrukcji wsporczych, które wystają powyżej poziomu gruntu więcej niż 0,15 m.", "2022/2377", "§ 1 pkt 1 lit. a (zał. 1 pkt 1.5.2)", 2)
F("montaż_konstrukcja", "A-7 na wspólnym słupku", "maks. 1 dodatkowy znak (A, B, C lub D-2, D-6, D-6a, D-6b)", "", "Łącznie ze znakiem A-7 może być umieszczony na tym samym słupku tylko jeden znak ostrzegawczy albo znak zakazu albo znak nakazu albo znak informacyjny: D-2, D-6, D-6a, D-6b", "2311", "zał. 1 pkt 1.5.2", 29)
F("montaż_konstrukcja", "maks. liczba znaków na jednym słupku/wysięgniku", "2 lub 3", "szt.", "Jeżeli ze względu na warunki lokalne istnieje konieczność zastosowania dwóch lub trzech znaków na jednym słupku lub wysięgniku", "2311", "zał. 1 pkt 1.5.2", 29)
F("montaż_strona", "obowiązkowe powtórzenie po lewej stronie", "drogi dwujezdniowe z >1 pasem: A, B (bez B-35–B-38), G, D-6, D-6a, D-6b", "",
  "jako powtórzenie znaków umieszczonych po prawej stronie na drogach dwujezdniowych, których jezdnie posiadają więcej niż jeden pas ruchu, przy czym jako obowiązkowe dotyczy to znaków kategorii A, B (z wyjątkiem znaków B-35 do B-38), G oraz znaków D-6, D-6a, D-6b", "2311", "zał. 1 pkt 1.5.1 pkt 3 lit. b", 28)
# odległości znaków ostrzegawczych
F("odległość_ostrzegawcze", "A - od miejsca niebezpiecznego, v_dop > 60 km/h", "150–300", "m", "a) 150–300 m na drogach o dopuszczalnej prędkości powyżej 60 km/h,", "2311", "zał. 1 pkt 2.1.2 lit. a", 50)
F("odległość_ostrzegawcze", "A - od miejsca niebezpiecznego, pozostałe drogi", "do 100", "m", "b) do 100 m na pozostałych drogach, z wyjątkiem znaku A-7", "2311", "zał. 1 pkt 2.1.2 lit. b", 50)
for v, d in (("≥ 100 km/h", "300"), ("90 km/h", "250–300"), ("80 km/h", "200–250"), ("70 km/h", "150–200"), ("≤ 60 km/h", "50–100")):
    F("odległość_ostrzegawcze", f"A - zalecana odległość, v_dop {v}", d, "m", f"Zaleca się, aby odległość znaku od miejsca niebezpiecznego […] dla v {v.replace(' km/h', '')} km/h {d.replace('–', ' m–')} m".replace("dla v ≥ 100 km/h 300 m", "dla v ≥ 100 km/h 300 m"), "2311", "zał. 1 pkt 2.1.2", 50)
F("odległość_ostrzegawcze", "A - odległość < 50 m", "tylko wyjątkowo", "", "W odległości mniejszej od 50 m można umieszczać znak ostrzegawczy tylko wyjątkowo, np. na ulicach staromiejskich", "2311", "zał. 1 pkt 2.1.2", 50)
F("odległość_ostrzegawcze", "T-1 - dokładność podanej odległości", 10, "m", "Rzeczywistą odległość podaje się w metrach, z dokładnością do 10 m.", "2311", "zał. 1 pkt 2.1.3", 50)
F("odległość_ostrzegawcze", "T-2 - stosowanie i dokładność", "odcinek > 0,5 km; dokładność 0,5 km", "km", "na odcinku drogi o długości przekraczającej 0,5 km. Długość tego odcinka podaje się w km z jedną cyfrą po przecinku z dokładnością do 0,5 km.", "2311", "zał. 1 pkt 2.1.4", 51)
F("odległość_ostrzegawcze", "A-7 - maks. odległość od skrzyżowania, v_dop > 60 km/h", "50", "m", "nie dalej niż: – 50 m – na drogach o dopuszczalnej prędkości powyżej 60 km/h,", "2311", "zał. 1 pkt 2.2.8", 64)
F("odległość_ostrzegawcze", "A-7 - maks. odległość od skrzyżowania, pozostałe drogi", "25", "m", "– 25 m – na pozostałych drogach.", "2311", "zał. 1 pkt 2.2.8", 64)
F("odległość_ostrzegawcze", "A-7 + T-1 - znak uprzedzający, v_dop > 60 km/h", "150–300", "m", "Na drogach o dopuszczalnej prędkości powyżej 60 km/h znak A-7 należy poprzedzić w odległości od 150 do 300 m znakiem A-7 z tabliczką T-1.", "2311", "zał. 1 pkt 2.2.8", 64)
F("odległość_ostrzegawcze", "B-20 - maks. odległość od skrzyżowania w obszarze zabudowanym", "25", "m", "Znak B-20 umieszcza się możliwie najbliżej skrzyżowania i nie dalej niż 25 m od niego w obszarze zabudowanym.", "2311", "zał. 1 pkt 3.2.21", 126)
F("odległość_ostrzegawcze", "B-20 - znak uprzedzający A-7 z tabliczką „Stop”, v_dop > 60 km/h", "150–300", "m", "znak B-20 powinien być poprzedzony w odległości 150–300 m znakiem A-7 z tabliczką z napisem „Stop” i podaniem odległości", "2311", "zał. 1 pkt 3.2.21", 126)
F("odległość_ostrzegawcze", "C-1…C-12 - maks. odległość od krawędzi jezdni drogi poprzecznej", "25", "m", "Znaki wskazujące wymagany sposób jazdy na skrzyżowaniu umieszcza się w rejonie skrzyżowania, jednak nie dalej niż 25 m od krawędzi jezdni drogi poprzecznej.", "2311", "zał. 1 pkt 4.1.1", 158)
F("odległość_ostrzegawcze", "D o obiektach - znaki poprzedzające poza obszarem zabudowanym", "powiatowe 1 km lub 500 m; woj./krajowe 2 km i 500 m; A/S 10 i 5 km", "", "– 1 km lub 500 m na drogach powiatowych, – 2 km i 500 m na drogach wojewódzkich i krajowych, – 10 i 5 km na drogach ekspresowych i autostradach.", "2021/2066", "§ 1 pkt 1 lit. b (zał. 1 pkt 5.1.1)", 2)
F("odległość_ostrzegawcze", "T-20 - maks. długość odcinka zakazu", 500, "m", "obowiązuje pomiędzy skrzyżowaniami na odcinku o długości do 500 m, to dopuszcza się umieszczanie pod znakiem tabliczki T-20", "2311", "zał. 1 pkt 3.1.3", 100)
F("odległość_ostrzegawcze", "D-42/D-43 - min. odstęp końca i początku obszaru zabudowanego", 300, "m", "byłaby mniejsza niż 300 m, to na tym odcinku nie umieszcza się znaków D-42 i D-43", "2022/2377", "§ 1 pkt 1 lit. b (zał. 1 pkt 5.2.48.1)", 4)
# ---------------- C-1 vs C-2 ----------------
F("rozstrzygnięcie", "C-1 - piktogram", "strzałka pozioma w prawo (strzałka C-5 obrócona o 90°)", "", "Wzór znaku na siatce kwadratów może być wykorzystany do kopiowania znaków C-1, C-3, C-5, C-9 i C-10 po dokonaniu obrotu osi strzałki o 135° i 90° w prawo lub w lewo.", "2311", "zał. 1 rys. 9.3.1", 398,
  metoda="odczyt tekstu + obejrzenie rys. 4.2.1.1 (PDF s. 158) i wzoru 2310 PDF s. 43 (raster 80-110 dpi)", uwagi="nazwa: „nakaz jazdy w prawo przed znakiem” (2310 PDF s. 31)")
F("rozstrzygnięcie", "C-2 - piktogram", "strzałka w górę zakręcająca w prawo", "", "Rys. 9.3.2. Konstrukcja znaku C-2 (dla C-4 odbicie lustrzane)", "2311", "zał. 1 rys. 9.3.2 i rys. 4.2.2.1", "159, 399",
  metoda="obejrzenie rys. 4.2.2.1 (PDF s. 159), rys. 9.3.2 (PDF s. 399), wzoru 2310 PDF s. 43 (raster 80-110 dpi)", uwagi="nazwa: „nakaz jazdy w prawo za znakiem”; „Znak C-2 […] obowiązku skręcenia w prawo za znakiem” (PDF s. 159)")
F("tytuły_aktów", "Dz.U. 2019 poz. 2310 - tytuł", "Obwieszczenie MI i MSWiA z 31.10.2019 - t.j. rozporządzenia w sprawie znaków i sygnałów drogowych (rozp. z 31.07.2002)", "",
  "w sprawie ogłoszenia jednolitego tekstu rozporządzenia Ministrów Infrastruktury oraz Spraw Wewnętrznych i Administracji w sprawie znaków i sygnałów drogowych", "2310", "tytuł", 1, uwagi="znaczenie znaków + spis i barwne wzory (zał.); nowelizacje: 2021/433, 2021/2065, 2022/2372, 2026/133")
F("tytuły_aktów", "Dz.U. 2019 poz. 2311 - tytuł", "Obwieszczenie MI z 9.09.2019 - t.j. rozporządzenia MI z 3.07.2003 w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń BRD i warunków ich umieszczania na drogach", "",
  "w sprawie ogłoszenia jednolitego tekstu rozporządzenia Ministra Infrastruktury w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń bezpieczeństwa ruchu drogowego i warunków ich umieszczania na drogach", "2311", "tytuł", 1,
  uwagi="zał. 1 = znaki pionowe (wymiary, barwy, folie, montaż); zał. 2 poziome; zał. 3 sygnały; zał. 4 urządzenia BRD (§ 1, PDF s. 5); nowelizacje: 2020/862, 2021/438, 2021/2066, 2022/2377, 2026/132")

# ---------------- dopisane po samokontroli (stałe id wcześniejszych wierszy) ----------------
F("wymiary", "D - bok kratki białego pola s1", "s/8", "mm", "Tabela 5.1 […] s1 1/8 s", "2311", "zał. 1 pkt 5.1.1, tab. 5.1", 178, metoda="odczyt tabeli-rastra (150 dpi, audyt)")
# ---------------- zapis ----------------
cols = list(ROWS[0])
with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(ROWS)
# sizes.csv - płaska tabela dla generatora
S = []
def srow(grp_sign, ksz, g, param, v, src):
    S.append({"znaki": grp_sign, "kształt": ksz, "grupa": g, "parametr": param, "wartość_mm": v, "źródło": src})
for i, g in enumerate(G):
    b, R, r, s, a = T21[g]
    for p, v in (("bok b", b), ("R zewn.", R), ("r wewn.", r), ("obrzeże s", s), ("moduł a", a)):
        srow("A (A-7 tylko D, S)", "trójkąt (A-7 odwrócony)", g, p, v, "2311 tab. 1.1 s. 9; tab. 2.1 s. 49")
for g in G:
    d, s, gg, p, a = T31[g]
    for pn, v in (("średnica d", d), ("obrzeże s", s), ("obwódka uchylającego g", gg), ("pas ukośny p", p), ("moduł a", a)):
        srow("B (B-20 tylko D, S)", "koło (B-20 ośmiokąt, d = koło wpisane)", g, pn, v, "2311 tab. 3.1 s. 97")
for g in G:
    d, gg, a = T41[g]
    for pn, v in (("średnica d", d), ("obwódka g", gg), ("moduł a", a)):
        srow("C (bez C-17)", "koło", g, pn, v, "2311 tab. 4.1 s. 157")
for g, (l, h, s, b, c, gg, r, a) in T51.items():
    for pn, v in (("podstawa l", l), ("wysokość h", h), ("białe pole s", s), ("margines b", b), ("część dolna c", c), ("obwódka g", gg), ("promień r", r), ("moduł a", a)):
        srow("D", "kwadrat/prostokąt (D-1, D-2 romb)", g, pn, v, "2311 tab. 1.1 s. 9; tab. 5.1 s. 178")
for g, vals in T971.items():
    for s_, v in zip(SYM, vals):
        srow("T (tabliczki)", "prostokąt", g, s_, v, "2311 tab. 9.7.1 s. 487")
for nm, ksz, dims, src in (("B-39", "prostokąt", "900×1300; R30; obwódka 9; B-35 Ø600", "rys. 9.2.47 s. 395"), ("B-40", "kwadrat", "900×900; R30; obwódka 10; symbol Ø600", "rys. 9.2.48 s. 396"),
                           ("B-43", "kwadrat", "900×900; R30; obwódka 10; B-33 Ø600; cyfry 270", "rys. 9.2.51 s. 397"), ("B-44", "kwadrat", "900×900; symbol Ø600; cyfry 270", "rys. 9.2.52 s. 398"),
                           ("C-17", "prostokąt", "900×1200; R30; obwódka 10; C-2 Ø400", "rys. 9.3.13 s. 404"), ("D-1 (powtórzenie)", "romb", "bok 400", "pkt 5.2.1.1 s. 185"),
                           ("D-19/D-20", "prostokąt", "600×300; R30", "rys. 9.4.27/29 s. 420"), ("D-42/D-43", "prostokąt", "1200×700 (600 na jednojezdniowych powiatowych/gminnych)", "Dz.U. 2022 poz. 2377 s. 4"),
                           ("F-12", "prostokąt", "600×750", "rys. 9.6.16 s. 481"), ("F-13", "strzała", "wys. 400; 650 + grot 200", "rys. 9.6.17 s. 481"), ("F-22", "prostokąt", "1400×1960; R30", "rys. 9.6.30 s. 487")):
    srow(nm, ksz, "jedna", "wymiary", dims, "2311 " + src)
with open(OUT / "sizes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(S[0]), lineterminator="\n"); w.writeheader(); w.writerows(S)
print(len(ROWS), "manifest rows;", len(S), "sizes rows")
for col, (cx, cy, Y, rgb) in SRGB.items():
    print(col, f"x={cx:.4f} y={cy:.4f} Y={Y}", "#%02X%02X%02X" % rgb)
