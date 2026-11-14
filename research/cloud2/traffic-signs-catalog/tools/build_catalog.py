"""R1 traffic-signs-catalog: buduje catalog.csv (znaki A/B/C/D/F/T) z danych wyciągniętych z Dz.U. 2019 poz. 2310/2311.

Wejście (tekst z `pdftotext -layout` z markerami stron, patrz README §Metoda):
  python -I tools/build_catalog.py <2310_p.txt> <2311_p.txt> <out_dir>
Wynik: <out_dir>/catalog.csv

Kształt i barwy: akt 2310 nie opisuje barw słownie dla każdego znaku - barwy są na kolorowych wzorach (zał. do 2310,
s. 41-50 PDF) i w opisie kategorii; dlatego kolumny barw mają status ESTIMATED (odczyt wizualny wzoru, strona podana),
z wyjątkami opisanymi słownie w 2311 (np. T-34, B-42/B-24 symbol szary, D-18 symbol biały) - SOURCED.
"""
import csv, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

src2310, src2311, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
tmp = out / "files" / "_derived"
tmp.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, "-I", str(HERE / "parse_list_2310.py"), src2310, str(tmp / "list2310.json")], check=True)
subprocess.run([sys.executable, "-I", str(HERE / "parse_fig9.py"), src2311, str(tmp / "fig9.json")], check=True)
L = json.load(open(tmp / "list2310.json", encoding="utf-8"))
FIG = json.load(open(tmp / "fig9.json", encoding="utf-8"))

# rysunki w opisach szczegółowych 2311 ("Rys. 2.2.1.1. Znak A-1")
txt = open(src2311, encoding="utf-8").read()
parts = re.split(r"\n=== PDF p\.(\d+) ===\n", txt)
DESC = {}
for i in range(1, len(parts), 2):
    p = int(parts[i])
    for raw in parts[i + 1].splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        m = re.match(r"^Rys\. ([2-8]\.[0-9.]+?)\.? (?:\d+\) )?(?:Znak|Tabliczka|Tabliczki) ([A-Z]-\d+[a-z]?)\b", line)
        if m and m.group(2)[0] in "ABCDFT":
            DESC.setdefault(m.group(2), (m.group(1), p))

AM = {  # nowelizacje 2310 po t.j. 2019 (ELI DU/2021/433, DU/2021/2065, DU/2026/133)
    "B-19": ("zakaz wjazdu pojazdów o nacisku pojedynczej osi napędowej powyżej ..... t", "Dz.U. 2021 poz. 433 § 1 pkt 3 lit. a (PDF s. 2)"),
    "D-44": ("strefa płatnego parkowania lub śródmiejska strefa płatnego parkowania", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 2)"),
    "D-45": ("koniec strefy płatnego parkowania lub śródmiejskiej strefy płatnego parkowania", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 2)"),
    "T-1a": ("tabliczka wskazująca odległość znaku informacyjnego do początku (końca) drogi, odcinka drogi, pasa ruchu lub obiektu", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 3)"),
    "T-32": ("tabliczka wskazująca minimalny odstęp od poprzedzającego pojazdu po zatrzymaniu", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 3)"),
}
ADD = [  # (kod, nazwa, źródło nazwy, strona wzoru barwnego, plik wzoru)
    ("D-23b", "stacja paliwowa z punktem ładowania pojazdów elektrycznych lub hybrydowych", "Dz.U. 2021 poz. 2065 (dodany) + Dz.U. 2026 poz. 133 § 1 pkt 10 lit. a (nazwa, PDF s. 2)", "Dz.U. 2021 poz. 2065 PDF s. 3"),
    ("D-23c", "punkt ładowania pojazdów elektrycznych lub hybrydowych", "Dz.U. 2021 poz. 2065 (dodany) + Dz.U. 2026 poz. 133 § 1 pkt 10 lit. a (nazwa, PDF s. 2)", "Dz.U. 2021 poz. 2065 PDF s. 3"),
    ("D-34b", "zbiorcza tablica informacyjna", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 2)", "Dz.U. 2021 poz. 2065 PDF s. 3"),
    ("F-14d", "tablica wskaźnikowa na drodze ekspresowej umieszczana w odległości 300 m przed pasem wyłączania", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 2)", "Dz.U. 2021 poz. 2065 PDF s. 4"),
    ("F-14e", "tablica wskaźnikowa na drodze ekspresowej umieszczana w odległości 200 m przed pasem wyłączania", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 2)", "Dz.U. 2021 poz. 2065 PDF s. 4"),
    ("F-14f", "tablica wskaźnikowa na drodze ekspresowej umieszczana w odległości 100 m przed pasem wyłączania", "Dz.U. 2021 poz. 2065 § 1 pkt 10 lit. a (PDF s. 2)", "Dz.U. 2021 poz. 2065 PDF s. 4"),
    ("F-23", "środkowy pas wielofunkcyjny", "Dz.U. 2026 poz. 133 § 1 pkt 10 lit. a (PDF s. 2)", "Dz.U. 2026 poz. 133 PDF s. 3"),
    ("F-24", "zły kierunek", "Dz.U. 2026 poz. 133 § 1 pkt 10 lit. a (PDF s. 2)", "Dz.U. 2026 poz. 133 PDF s. 3"),
]
INSERT_AFTER = {"D-23b": "D-23a", "D-23c": "D-23b", "D-34b": "D-34a", "F-14d": "F-14c", "F-14e": "F-14d", "F-14f": "F-14e",
                "F-23": "F-22", "F-24": "F-23"}

# ---- kształty (2311 pkt 2.1.1, 3.1.1, 4.1.1, 5.1.1 + rysunki konstrukcyjne; D/F/T - odczyt wzoru barwnego) ----
SHAPE_RULE = {"A": ("trójkąt", "SOURCED", "2311 pkt 2.1.1 PDF s. 49: „Znaki ostrzegawcze mają kształt trójkąta równobocznego”"),
              "B": ("koło", "SOURCED", "2311 pkt 3.1.1 PDF s. 96-97, rys. 3.1.1.1 (średnica d)"),
              "C": ("koło", "SOURCED", "2311 pkt 4.1.1 PDF s. 157: „Znaki nakazu, z wyjątkiem znaku C-17, mają kształt koła”"),
              "D": ("kwadrat lub prostokąt", "SOURCED", "2311 pkt 5.1.1 PDF s. 176: „Znaki informacyjne mają kształt kwadratu lub prostokąta”"),
              "F": ("prostokąt", "ESTIMATED", "odczyt wzoru barwnego 2310 PDF s. 48 (brak ogólnej reguły kształtu F w 2311 pkt 7.1)"),
              "T": ("prostokąt", "ESTIMATED", "odczyt wzoru barwnego 2310 PDF s. 49-50; wymiary tabl. 9.7.1 (2311 PDF s. 487)")}
SHAPE_EX = {
    "A-7": ("trójkąt odwrócony", "SOURCED", "2311 pkt 2.1.1 PDF s. 49: „z wyjątkiem znaku A-7, którego wierzchołek powinien być skierowany ku dołowi”"),
    "B-20": ("ośmiokąt", "SOURCED", "2311 pkt 3.1.1 PDF s. 96: „ośmiokątnego znaku B-20”"),
    "B-39": ("prostokąt (pionowy 900×1300)", "SOURCED", "2311 rys. 9.2.47 PDF s. 395"),
    "B-40": ("kwadrat (900×900)", "SOURCED", "2311 rys. 9.2.48 PDF s. 396"),
    "B-43": ("kwadrat (900×900)", "SOURCED", "2311 rys. 9.2.51 PDF s. 397"),
    "B-44": ("kwadrat (900×900)", "SOURCED", "2311 rys. 9.2.52 PDF s. 398"),
    "C-17": ("prostokąt (pionowy 900×1200)", "SOURCED", "2311 pkt 4.1.1 PDF s. 157 + rys. 9.3.13 PDF s. 404"),
    "D-1": ("romb (kwadrat obrócony o 45°)", "SOURCED", "2311 pkt 5.2.1.1 PDF s. 185: „Znaki D-1 umieszcza się tak, aby jedna przekątna była w położeniu poziomym”"),
    "D-2": ("romb (kwadrat obrócony o 45°)", "SOURCED", "2311 rys. 9.4.4 PDF s. 408"),
    "D-19": ("prostokąt poziomy (620×300)", "SOURCED", "2311 pkt 5.2.19 PDF s. 227 / Dz.U. 2022 poz. 2377 PDF s. 2: „długość podstawy 620 mm, wysokość 300 mm”"),
    "D-20": ("prostokąt poziomy (620×300)", "SOURCED", "jak D-19 (2311 pkt 5.2.19-5.2.20; rys. 9.4.29 s. 420: 600 wewnątrz obwódki)"),
    "D-42": ("prostokąt poziomy (1200×700; 1200×600 dopuszcz.)", "SOURCED", "2311 pkt 5.2.48.1 PDF s. 244 zm. Dz.U. 2022 poz. 2377 PDF s. 4"),
    "D-43": ("prostokąt poziomy (1200×700; 1200×600 dopuszcz.)", "SOURCED", "2311 pkt 5.2.48.1 PDF s. 244 zm. Dz.U. 2022 poz. 2377 PDF s. 4"),
    "F-13": ("pięciokąt - prostokąt zakończony grotem (strzała)", "SOURCED", "2311 rys. 9.6.17 PDF s. 481"),
}
# D/F/T: odczyt proporcji z wzorów barwnych 2310 (powiększenie 200 dpi) - ESTIMATED
VIS_SHAPE = {}
for c in "D-3 D-4a D-4b D-5 D-6 D-6a D-6b D-9 D-10 D-21a D-18 D-21 D-35 D-35a D-36 D-36a D-54 D-55 F-7 F-20 T-6a T-6b T-6c T-6d T-7 T-27".split():
    VIS_SHAPE[c] = "kwadrat"
for c in ("D-7 D-8 D-11 D-12 D-13 D-14 D-15 D-16 D-17 D-18a D-18b D-22 D-23 D-23a D-23b D-23c D-24 D-25 D-26 D-26a D-26b D-26c "
          "D-26d D-27 D-28 D-29 D-30 D-31 D-32 D-33 D-34 D-34a D-37 D-38 D-39 D-44 D-45 D-48 D-49 D-50 D-51 D-51a D-51b "
          "F-3 F-8 F-12 F-14a F-14b F-14c F-14d F-14e F-14f F-21 F-22 F-24 T-8 T-12 T-13 T-14 T-15 T-16 T-18 T-25a T-25b T-25c").split():
    VIS_SHAPE[c] = "prostokąt pionowy"
for c in ("D-13a D-34b D-39a D-40 D-41 D-46 D-47 D-52 D-53 F-1 F-2 F-2a F-4 F-6 F-9 F-10 F-11 F-15 F-16 F-17 F-18 F-19 F-23 "
          "T-1 T-1a T-1b T-2 T-3 T-3a T-4 T-5 T-9 T-10 T-11 T-17 T-19 T-20 T-21 T-23a T-23b T-23c T-23d T-23e T-23f T-23g "
          "T-24 T-26 T-28 T-30 T-32 T-33").split():
    VIS_SHAPE[c] = "prostokąt poziomy"
for c in "F-5 T-23h T-23i T-23j T-29 T-31 T-34".split():
    VIS_SHAPE[c] = "prawie kwadrat (prostokąt)"

# ---- barwy: (tło, obrzeże/obwódka, symbol/napis) ----
CAT_COL = {"A": ("żółte", "czerwone obrzeże", "czarny"),
           "B": ("białe", "czerwone obrzeże", "czarny"),
           "C": ("niebieskie", "biała cienka obwódka", "biały"),
           "D": ("niebieskie", "biała obwódka", "biały (lub czarny na białym polu)"),
           "F": ("niebieskie", "biała obwódka", "biały"),
           "T": ("białe", "czarna obwódka", "czarny")}
COL = {
    "A-7": ("żółte", "czerwone obrzeże", "brak symbolu"),
    "A-29": ("żółte", "czerwone obrzeże", "czarna obudowa sygnalizatora; światła czerwone, żółte, zielone"),
    "B-2": ("czerwone", "brak osobnego obrzeża (cienka biała krawędź)", "poziomy biały pas"),
    "B-13": ("białe", "czerwone obrzeże", "czarny samochód + pomarańczowo-czerwony wybuch"),
    "B-13a": ("białe", "czerwone obrzeże", "pomarańczowy prostokąt (tablica ADR) na czarnym podwoziu"),
    "B-14": ("białe", "czerwone obrzeże", "pomarańczowa cysterna, czarne podwozie, niebieskie fale"),
    "B-20": ("czerwone", "białe obrzeże", "biały napis STOP"),
    "B-21": ("białe", "czerwone obrzeże", "czarny symbol + czerwony pas ukośny"),
    "B-22": ("białe", "czerwone obrzeże", "czarny symbol + czerwony pas ukośny"),
    "B-23": ("białe", "czerwone obrzeże", "czarny symbol + czerwony pas ukośny"),
    "B-29": ("białe", "czerwone obrzeże", "czarny symbol + czerwony pas ukośny"),
    "B-24": ("białe", "czarna cienka obwódka", "szary symbol + czarny pas ukośny"),
    "B-25": ("białe", "czerwone obrzeże", "czerwony samochód (lewy) + czarny samochód"),
    "B-26": ("białe", "czerwone obrzeże", "czerwony samochód ciężarowy (lewy) + czarny samochód"),
    "B-27": ("białe", "czarna cienka obwódka", "szare samochody + czarny pas ukośny"),
    "B-28": ("białe", "czarna cienka obwódka", "szare pojazdy + czarny pas ukośny"),
    "B-30": ("białe", "czarna cienka obwódka", "szary róg + czarny pas ukośny"),
    "B-31": ("białe", "czerwone obrzeże", "czarna strzałka w dół + czerwona strzałka w górę"),
    "B-34": ("białe", "czarna cienka obwódka", "szare cyfry + czarny pas ukośny"),
    "B-35": ("niebieskie", "czerwone obrzeże", "czerwony pas ukośny"),
    "B-36": ("niebieskie", "czerwone obrzeże", "czerwone skrzyżowane pasy"),
    "B-37": ("niebieskie", "czerwone obrzeże", "czerwony pas ukośny + jedna biała pionowa kreska"),
    "B-38": ("niebieskie", "czerwone obrzeże", "czerwony pas ukośny + dwie białe pionowe kreski"),
    "B-39": ("białe (tablica)", "czarna obwódka", "znak B-35 + czarny napis"),
    "B-40": ("białe (tablica)", "czarna obwódka", "szary symbol koła z krzyżem (jak B-36) + czarny pas ukośny"),
    "B-42": ("białe", "czarna cienka obwódka", "czarny pas ukośny"),
    "B-43": ("białe (tablica)", "czarna obwódka", "znak B-33 (czerwone obrzeże, czarne cyfry)"),
    "B-44": ("białe (tablica)", "czarna obwódka", "szary symbol B-43 + czarny pas ukośny"),
    "C-13a": ("niebieskie", "biała cienka obwódka", "biały symbol + czerwony pas ukośny"),
    "C-15": ("niebieskie", "biała cienka obwódka", "białe cyfry + czerwony pas ukośny"),
    "C-16a": ("niebieskie", "biała cienka obwódka", "biały symbol + czerwony pas ukośny"),
    "C-17": ("białe (tablica)", "czarna obwódka", "pomarańczowy prostokąt + czarne podwozie; niebieski znak C-2 z białą strzałką"),
    "C-18": ("niebieskie", "biała cienka obwódka", "białe koło z czarnym łańcuchem"),
    "C-19": ("niebieskie", "biała cienka obwódka", "białe koło z czarnym łańcuchem + czerwony pas ukośny"),
    "D-1": ("żółty kwadrat wewnętrzny", "białe obrzeże (romb), czarna cienka linia", "brak"),
    "D-2": ("żółty kwadrat wewnętrzny", "białe obrzeże (romb), czarna cienka linia", "czarny pas ukośny"),
    "D-4a": ("niebieskie", "biała obwódka", "biały symbol, czerwona poprzeczka"),
    "D-4b": ("niebieskie", "biała obwódka", "biały symbol, czerwona poprzeczka"),
    "D-5": ("niebieskie", "biała obwódka", "czerwona strzałka w dół + biała strzałka w górę"),
    "D-6": ("niebieskie", "biała obwódka", "biały trójkąt, czarny symbol pieszego"),
    "D-6a": ("niebieskie", "biała obwódka", "biały trójkąt, czarny symbol rowerzysty"),
    "D-6b": ("niebieskie", "biała obwódka", "biały trójkąt, czarne symbole"),
    "D-21": ("niebieskie", "biała obwódka", "białe pole: czarne łóżko + czerwony krzyż"),
    "D-22": ("niebieskie", "biała obwódka", "białe pole: czerwony krzyż"),
    "D-23": ("niebieskie", "biała obwódka", "białe pole: czarny dystrybutor + zielony element"),
    "D-23b": ("niebieskie", "biała obwódka", "białe pole: czarny dystrybutor + zielony punkt ładowania „EV”"),
    "D-23c": ("niebieskie", "biała obwódka", "białe pole: zielony punkt ładowania „EV”"),
    "D-42": ("białe", "czarna obwódka", "czarna sylweta miejscowości"),
    "D-43": ("białe", "czarna obwódka", "czarna sylweta + czerwony pas ukośny"),
    "D-44": ("białe (tablica)", "czarna obwódka", "niebieski znak D-18 + czarny napis"),
    "D-45": ("białe (tablica)", "czarna obwódka", "szary symbol D-44 + czerwony pas ukośny"),
    "D-46": ("białe", "czarna obwódka", "czarny napis „Droga wewnętrzna”"),
    "D-47": ("białe", "czarna obwódka", "czarny napis + czerwony pas ukośny"),
    "D-48": ("niebieskie", "biała obwódka", "biały napis + żółty trójkąt z czerwonym obrzeżem i czarnym symbolem"),
    "D-52": ("białe", "czarna obwódka", "czarny napis i symbol"),
    "D-53": ("białe", "czarna obwódka", "czarny napis i symbol + czerwony pas ukośny"),
    "D-54": ("białe", "czarna obwódka", "czarny napis „Strefa”, zielone koło z zielonym samochodem"),
    "D-55": ("białe", "czarna obwódka", "jak D-54 + czerwony pas ukośny"),
    "F-1": ("niebieskie", "biała obwódka", "białe napisy; czerwone koło z białym orłem"),
    "F-2": ("niebieskie", "biała obwódka", "białe napisy; czerwone koło z białym orłem"),
    "F-2a": ("niebieskie", "biała obwódka", "białe napisy; czerwone koło z białym orłem"),
    "F-5": ("niebieskie", "biała obwódka", "biała strzałka i napis + znak B (białe tło, czerwone obrzeże)"),
    "F-6": ("niebieskie", "biała obwódka", "biały schemat + znak A (żółty, czerwone obrzeże)"),
    "F-7": ("niebieskie", "biała obwódka", "białe pola + czarny schemat drogi ze strzałką"),
    "F-12": ("niebieskie", "biała obwódka", "biały symbol pojazdu z czarnym napisem masy; biała strzałka"),
    "F-8": ("żółte", "czarna obwódka", "czarny schemat i napisy + znak B-1"),
    "F-9": ("żółte", "czarna obwódka", "czarna strzałka i napis „Objazd”"),
    "F-14a": ("niebieskie", "biała obwódka", "białe cyfry i białe pasy ukośne"),
    "F-14b": ("niebieskie", "biała obwódka", "białe cyfry i białe pasy ukośne"),
    "F-14c": ("niebieskie", "biała obwódka", "białe cyfry i biały pas ukośny"),
    "F-14d": ("zielone", "biała obwódka", "białe cyfry i białe pasy ukośne"),
    "F-14e": ("zielone", "biała obwódka", "białe cyfry i białe pasy ukośne"),
    "F-14f": ("zielone", "biała obwódka", "białe cyfry i biały pas ukośny"),
    "F-17": ("niebieskie", "biała obwódka", "białe strzałki + czerwona poprzeczka"),
    "F-18": ("niebieskie", "biała obwódka", "białe strzałki; biały symbol pojazdu z czerwonym krzyżem"),
    "F-21": ("żółte", "czarna obwódka", "czarne strzałki i symbole"),
    "F-22": ("żółte", "czarna obwódka", "czarne strzałki + znak B (białe tło, czerwone obrzeże)"),
    "F-24": ("żółto-zielone (fluorescencyjne)", "czarna obwódka", "czarne napisy „STOP”, „Zły kierunek”, czarna dłoń, znak B-2"),
    "T-1": ("żółte", "czarna obwódka", "czarny"),
    "T-1a": ("niebieskie", "biała obwódka", "biały"),
    "T-1b": ("niebieskie", "biała obwódka", "biały"),
    "T-16": ("żółte", "czarna obwódka", "czarny pojazd z czerwonym polem „STRAŻ”"),
    "T-23h": ("białe", "czarna obwódka", "pomarańczowy prostokąt + czarne podwozie"),
    "T-23i": ("białe", "czarna obwódka", "czarny samochód + pomarańczowo-czerwony wybuch"),
    "T-23j": ("białe", "czarna obwódka", "pomarańczowa cysterna, niebieskie fale"),
    "T-27": ("żółte (lub fluor. żółto-zielone)", "czarna obwódka", "czarna postać, czerwono-biały lizak"),
    "T-28": ("niebieskie", "biała obwódka", "biały napis „Płatna”"),
    "T-30": ("białe", "czarna obwódka", "szare pole + czarny kontur samochodu"),
    "T-33": ("białe", "czarna obwódka", "czerwona gaśnica, czarny napis S.O.S. i słuchawka"),
    "T-34": ("pomarańczowe", "biała ramka", "czarny symbol urządzenia"),
}
for c in "T-2 T-3 T-4 T-5 T-6a T-6b T-6c T-6d T-7 T-8 T-9 T-10 T-11 T-12 T-13 T-14 T-15 T-17 T-18 T-19".split():
    COL.setdefault(c, ("żółte", "czarna obwódka", "czarny"))
for c in "D-8 D-10 D-38 D-41 D-51b".split():
    COL.setdefault(c, ("niebieskie", "biała obwódka", "biały symbol + czerwony pas ukośny"))
D_WHITE_FIELD = set("D-15 D-16 D-17 D-24 D-25 D-26 D-26a D-26b D-26c D-26d D-27 D-28 D-29 D-30 D-31 D-32 D-33 D-34 D-23a D-37 D-34a".split())
VERBAL = {  # barwa opisana słownie w akcie
    "T-34": "2311 pkt 6.3.7.9 PDF s. 291: „tło barwy pomarańczowej z białą ramką tarczy tabliczki i symbol […] barwy czarnej”",
    "B-24": "2311 pkt 3.2.43 PDF s. 155: „znak z symbolem barwy szarej odwoływanego zakazu, np. B-24”",
    "D-18": "2311 pkt 5.2.18 PDF s. 222: „symbol pojazdu barwy białej” (wariant z symbolem pojazdu)",
}
PAT_PAGE = {"A": "41", "B": "42", "C": "43", "D": "44", "F": "48", "T": "49"}

MANUAL_DESC = {**{f"T-23{x}": ("3.2.34.2 (Tabliczki T-23a–j)", 141) for x in "abcdefghij"},
               "T-31": ("3.2.14.2a", 116), "T-30": ("5.2.18.2–5.2.18.10 (T-30a–i)", 223)}
AMEND_FIG = {  # rysunki konstrukcyjne dodane nowelizacjami 2311
    "D-23b": "rys. 9.4.35a (Dz.U. 2021 poz. 2066 PDF s. 16)",
    "D-34b": "rys. 9.4.1, 9.4.2 (Dz.U. 2021 poz. 2066 PDF s. 15)",
    "F-14d": "rys. 9.6.18 (Dz.U. 2021 poz. 2066 PDF s. 17)",
    "F-14e": "rys. 9.6.19 (podpis zm. Dz.U. 2021 poz. 2066 PDF s. 17)",
    "F-14f": "rys. 9.6.20 (Dz.U. 2021 poz. 2066 PDF s. 17)",
    "F-23": "rys. 9.6.31 (Dz.U. 2026 poz. 132 PDF s. 15)",
    "F-24": "rys. 9.6.32 (Dz.U. 2026 poz. 132 PDF s. 15)",
}
AMEND_DESC = {
    "D-23b": "rys. 5.2.24.3 (Dz.U. 2021 poz. 2066 PDF s. 8)",
    "D-23c": "rys. 5.2.24.4 (Dz.U. 2021 poz. 2066 PDF s. 8)",
    "D-34b": "rys. 5.1.1a.1 (Dz.U. 2021 poz. 2066 PDF s. 3)",
    "F-14d": "rys. 7.2.14.4 (Dz.U. 2021 poz. 2066 PDF s. 14)",
    "F-14e": "rys. 7.2.14.5 (Dz.U. 2021 poz. 2066 PDF s. 14)",
    "F-14f": "rys. 7.2.14.6 (Dz.U. 2021 poz. 2066 PDF s. 14)",
    "F-23": "rys. 7.2.23.1 (Dz.U. 2026 poz. 132 PDF s. 12)",
    "F-24": "rys. 7.2.24.1 (Dz.U. 2026 poz. 132 PDF s. 12)",
}
rows = []
names = {r["code"]: r for r in L}
order = [r["code"] for r in L]
for code, *_ in ADD:
    order.insert(order.index(INSERT_AFTER[code]) + 1, code)
addmap = {a[0]: a for a in ADD}
for i, code in enumerate(order, 1):
    cat = code[0]
    if code in addmap:
        _, name, nsrc, pat = addmap[code]
    else:
        r = names[code]
        name = re.sub(r"(\w)- (\w)", r"\1\2", r["name"])
        nsrc = f"2310 zał. „Spis wzorów”, PDF s. {r['page_2310']}"
        if code in AM:
            name, nsrc = AM[code][0], AM[code][1] + f" (pierwotnie 2310 PDF s. {r['page_2310']})"
        pg = PAT_PAGE[cat]
        if cat == "D" and code >= "D-46" and code[2:].split("a")[0].isdigit() and int(re.match(r"D-(\d+)", code).group(1)) >= 46:
            pg = "45"
        if cat == "T" and int(re.match(r"T-(\d+)", code).group(1)) >= 30:
            pg = "50"
        pat = f"2310 PDF s. {pg}"
        if code == "D-39":
            pat += "; nowy rysunek: Dz.U. 2022 poz. 2372 PDF s. 2"
    shape, sh_status, sh_src = SHAPE_EX.get(code, SHAPE_RULE[cat])
    if code in VIS_SHAPE and code not in SHAPE_EX:
        shape, sh_status, sh_src = VIS_SHAPE[code], "ESTIMATED", f"odczyt proporcji wzoru barwnego ({pat}); reguła kategorii: {SHAPE_RULE[cat][2]}"
    col = COL.get(code, CAT_COL[cat])
    if cat == "D" and code in D_WHITE_FIELD and code not in COL:
        col = ("niebieskie", "biała obwódka", "białe pole z czarnym symbolem/napisem")
    col_status = "SOURCED (tylko element z cytatu), reszta ESTIMATED" if code in ("B-24", "D-18") else "SOURCED" if code in VERBAL else "ESTIMATED"
    col_src = VERBAL.get(code, f"odczyt wizualny barwnego wzoru ({pat}); brak słownego opisu barw w akcie")
    f9 = FIG.get(code, [])
    if code in ("C-1", "C-3", "C-9", "C-10"):
        f9 = [{"rys": "9.3.1", "page": 398, "caption": "Konstrukcja znaku C-5 (wzór do kopiowania C-1, C-3, C-9, C-10 po obrocie strzałki)"}]
    if code == "D-13a":
        f9 = FIG.get("D-13", [])
    if code == "F-3":
        f9 = FIG.get("F-3a", []) + FIG.get("F-3b", [])
    if code == "T-30":
        f9 = [x for k in sorted(FIG) if k.startswith("T-30") for x in FIG[k]]
    rys = "; ".join(f"rys. {f['rys']} (PDF s. {f['page']})" for f in f9) or "UNVERIFIED (brak osobnego rysunku w rozdz. 9)"
    if code in AMEND_FIG:
        rys = AMEND_FIG[code]
    d = DESC.get(code) or MANUAL_DESC.get(code)
    desc = f"rys. {d[0]} (PDF s. {d[1]})" if d else AMEND_DESC.get(code, "")
    rows.append({
        "kat_id": f"R1-K{i:03d}", "kod": code, "kategoria": cat, "nazwa": name, "źródło_nazwy": nsrc,
        "kształt": shape, "status_kształtu": sh_status, "źródło_kształtu": sh_src,
        "tło": col[0], "obrzeże_obwódka": col[1], "symbol_napis": col[2], "status_barw": col_status, "źródło_barw": col_src,
        "wzór_barwny_strona": pat,
        "rys_opisu_2311": desc,
        "rys_konstrukcyjny_2311": rys,
        "grupy_wielkości": ("D, S" if code in ("A-7", "B-20") else
                             "W, D, S, M, MI" if cat in "ABC" and code not in SHAPE_EX else
                             "W, D, S, M, MI (l+n·Δ)" if cat == "D" and code not in SHAPE_EX else
                             "wielkie/duże; średnie/małe (tabl. 9.7.1)" if cat == "T" else "wg rysunku konstrukcyjnego"),
    })
with open(out / "catalog.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r["kategoria"] for r in rows), Counter(r["status_kształtu"] for r in rows))
