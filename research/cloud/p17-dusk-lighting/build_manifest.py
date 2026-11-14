#!/usr/bin/env python3
"""Buduje manifest.csv z danych wpisanych niżej + frames_meta.json (metadane kadrów z API Commons).
Wysokość Słońca liczona z EXIF DateTimeOriginal (czas lokalny Europe/Warsaw - założenie) i współrzędnych
Commons przez sun.py. Uruchom: python3 build_manifest.py"""
import csv, json, os, datetime as dt
import sun

HERE = os.path.dirname(os.path.abspath(__file__))
ACCESS = "2026-11-14"
COLS = ["id", "kategoria", "element", "parametr", "wartość", "jednostka", "warunki", "wysokość_słońca_deg", "lat", "lon",
        "kierunek_deg", "data_godzina", "opis_co_widać", "url_źródła", "licencja", "autor", "data_dostępu", "status", "uwagi",
        "cytat", "plik", "url_pliku", "sha256", "url_oryginału", "sha1_oryginału"]

S_SCHLYTER = "https://stjarnhimlen.se/comp/radfaq.html"
S_FOTIOS = "https://pmc.ncbi.nlm.nih.gov/articles/PMC11469482/"
S_PATAT = "https://arxiv.org/abs/astro-ph/0604128"
S_SPIT = "https://pmc.ncbi.nlm.nih.gov/articles/PMC4895134/"
S_PIL = "https://www.performanceinlighting.com/ww/pl/en-13201-2-2015"
S_SENS = "https://pmc.ncbi.nlm.nih.gov/articles/PMC11435540/"
S_TED = "https://ted.europa.eu/pl/notice/-/detail/%s"
S_NOVAK = "https://files.cie.co.at/x051_2025/P0796_ID298TomasNovak_OA_with_cover.pdf"
S_BARA = "https://arxiv.org/abs/1706.04458"
S_WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
S_KIO = "https://orzeczenia.uzp.gov.pl/Home/PdfContent/20229?Kind=KIO"
S_AUG = "https://bip.um.augustow.pl/resource/16731/21519/Audyt+energetyczny+o%25C5%259Bwietlenia+ulicznego+Miasto+August%25C3%25B3w+z+instalacja+OZE+%2528002%2529.pdf"
S_BPN = "https://bpnt.bialystok.pl/wp-content/uploads/2026/03/BPN-T.261.1.66.2026-ZALACZNIK-NR-2-OPZ.docx"
S_PZ = "https://platformazakupowa.pl/file/get_new/6b204d06d94a54215924c0e37cf52f7a.pdf"
S_OVP = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"

rows = []
def add(kat, element, parametr, wartosc, jedn, warunki, status, url, lic, autor, uwagi="", cytat="", sun_deg="", lat="", lon="", dg="", opis=""):
    rows.append(dict(kategoria=kat, element=element, parametr=parametr, wartość=wartosc, jednostka=jedn, warunki=warunki,
                     wysokość_słońca_deg=sun_deg, lat=lat, lon=lon, kierunek_deg="", data_godzina=dg, opis_co_widać=opis,
                     url_źródła=url, licencja=lic, autor=autor, data_dostępu=ACCESS, status=status, uwagi=uwagi, cytat=cytat))

# ---------------------------------------------------------------- 1. NIEBO
SCH = [(0.0, "759"), (-3.0, "79.1"), (-4.0, "29.9"), (-5.0, "10.4"), (-6.0, "3.41"), (-7.0, "1.09"), (-8.0, "0.348"), (-12.0, "0.00806?")]
for el, v in SCH[:-1]:
    add("niebo", "natężenie oświetlenia poziomego", "E_h", v, "lx", "tabela „Solar illumination on horizontal surface” (bezchmurnie - nie podano wprost)",
        "SOURCED_SECONDARY", S_SCHLYTER, "tekst autora (FAQ, cytowane liczby)", "P. Schlyter",
        "Źródło wtórne (FAQ astronoma), wskazuje Seidelmann, Explanatory Supplement 1992, s. 490-493 - oryginału nie otwarto. Potwierdza stałą gry 3,4 lx.",
        "Solar altit degrees / log10 Lux / Lux: %.1f ... %s" % (el, v), sun_deg="%.1f" % el)
add("niebo", "natężenie oświetlenia poziomego", "E_h", "355", "lx", "bezchmurnie, Słońce na horyzoncie", "SOURCED", S_FOTIOS, "CC BY 4.0",
    "Fotios, Uttley i in. 2024 (PLOS ONE), Tabela 1 za Muneerem",
    "Rozbieżność ze Schlyterem (759 lx przy 0,0°) - różne konwencje (elewacja pozorna/geometryczna, model); traktować jako widełki.",
    "Horizontal surface under a cloudless sky: sun at horizon = 355 lx, sun at zenith = 103,000 lx", sun_deg="0.0")
add("niebo", "natężenie oświetlenia poziomego", "E_h", "4.3", "lx", "koniec zmierzchu cywilnego", "SOURCED", S_FOTIOS, "CC BY 4.0",
    "Fotios, Uttley i in. 2024 (PLOS ONE), Tabela 1 za Muneerem", "Druga wartość dla -6° obok 3,41 lx (Schlyter); widełki 3,4-4,3 lx.",
    "End of civil twilight: 4.3 lx", sun_deg="-6.0")
add("niebo", "natężenie oświetlenia poziomego", "E_h", "0.001", "lx", "koniec zmierzchu astronomicznego", "SOURCED", S_FOTIOS, "CC BY 4.0",
    "Fotios, Uttley i in. 2024 (PLOS ONE), Tabela 1 za Muneerem", "", "End of astronomical twilight: 0.001 lx", sun_deg="-18.0")
add("niebo", "natężenie oświetlenia poziomego", "E_h", "", "lx", "pochmurnie, Słońce -4…-8°", "UNVERIFIED", "", "", "",
    "Nie znaleziono otwartego źródła z pomiarem przy zachmurzeniu całkowitym (sprawdzono: Spitschan 2016 - tylko wykresy; DTIC, AMS MWR, colorimaginglab.ugr.es - niedostępne przez proxy).")
for el, mag, L in [(-5, "11.84", "2.0"), (-6, "13.30", "0.52"), (-7, "14.65", "0.15"), (-8, "15.88", "0.048")]:
    add("niebo", "luminancja nieba w zenicie", "L_zenit (pasmo V)", L, "cd/m²", "bezchmurnie, bez Księżyca, ESO Paranal 2635 m n.p.m., |odl. zenitalna| ≤ 40°",
        "ESTIMATED", S_PATAT, "arXiv (preprint A&A 455, 385)", "Patat, Ugolnikov, Postylyakov 2006",
        "Metoda: wielomian z Tabeli 1 (V: a0=11.84, a1=1.518, a2=-0.057; ζ=90°-elewacja) → %s mag/arcsec²; przeliczenie L[cd/m²]=10,8e4·10^(-0,4·m_V) (przybliżenie stosowane w fotometrii nieba, pasmo V ≠ V(λ)). Wg autorów nisko położone stanowisko ma ok. 30 %% jaśniej. Dopasowanie ważne dla ζ 95-105°." % mag,
        "a0 + a1(ζ−95) + a2(ζ−95)², with ζ expressed in degrees and the surface brightness in mag arcsec−2", sun_deg=str(el))
add("niebo", "luminancja nieba w zenicie", "różnica wysokość/nizina", "ok. 30", "%", "Paranal vs stanowisko nisko położone, pasmo V", "SOURCED", S_PATAT,
    "arXiv (preprint A&A)", "Patat i in. 2006", "Dla Białegostoku (ok. 150 m n.p.m.) wartości z Paranal mnożyć ok. ×1,4 (ESTIMATED).",
    "Paranal V twilight sky brightness is about 30% lower")
add("niebo", "luminancja nieba przy horyzoncie", "L_horyzont", "1", "cd/m²", "bezchmurnie, 15 min po zachodzie", "SOURCED_SECONDARY", S_SCHLYTER,
    "tekst autora (FAQ)", "P. Schlyter", "Rząd wielkości; strona Słońca/przeciwna nie rozróżniona; 15 min po zachodzie w Białymstoku ≈ Słońce -2,5…-3° (sun.py).",
    "Clear sky 15 min after sunset (horiz) 1 [Nit = cd/m2]")
add("niebo", "luminancja nieba przy horyzoncie", "L_horyzont", "0.1", "cd/m²", "bezchmurnie, 30 min po zachodzie", "SOURCED_SECONDARY", S_SCHLYTER,
    "tekst autora (FAQ)", "P. Schlyter", "30 min po zachodzie w Białymstoku ≈ Słońce -4,5…-5,5° zależnie od pory roku (sun.py).",
    "Clear sky 30 min after sunset (horiz) 0.1 [Nit = cd/m2]")
add("niebo", "luminancja nieba przy horyzoncie", "L_horyzont", "10", "cd/m²", "pochmurnie, zachód Słońca", "SOURCED_SECONDARY", S_SCHLYTER,
    "tekst autora (FAQ)", "P. Schlyter", "Rząd wielkości.", "Sunset at horizon, overcast 10 [Nit = cd/m2]", sun_deg="0")
add("niebo", "luminancja nieba: horyzont od strony Słońca vs przeciwnej", "L", "", "cd/m²", "Słońce -3…-8°", "UNVERIFIED", "", "", "",
    "Koomen i in. 1952 (JOSA 42, 353) ma takie tabele, ale jedyny znaleziony PDF nie jest autoryzowaną kopią - nie użyto.")
add("niebo", "barwa oświetlenia (chromatyczność)", "przebieg", "najbardziej niebieskie przy ok. -12° (wieś), ok. -6° (miasto)", "", "pomiar spektroradiometryczny, lipiec 2014, USA: wieś i Filadelfia",
    "SOURCED", S_SPIT, "CC BY 4.0", "Spitschan, Aguirre, Brainard, Sweeney 2016 (Sci. Rep. 6:26756)",
    "W mieście „dołek” niebieski wypada wcześniej, bo poniżej ok. -8° dominuje światło sztuczne. Liczb CCT w tekście brak (tylko wykresy).",
    "the illumination is bluest during nautical twilight with a minimum at around −12°")
add("niebo", "barwa oświetlenia (chromatyczność)", "miasto vs wieś", "zmierzch w mieście przesunięty ku czerwieni", "", "jw.", "SOURCED", S_SPIT, "CC BY 4.0",
    "Spitschan i in. 2016", "", "The average twilight chromaticity is shifted towards higher, more reddish values in the City location")
add("niebo", "łuna miejska", "próg dominacji światła sztucznego", "-8", "° (elewacja Słońca)", "Filadelfia, dach budynku", "SOURCED", S_SPIT, "CC BY 4.0", "Spitschan i in. 2016",
    "Dla gry: poniżej -8° barwę nieba nad miastem ustala łuna, nie zmierzch.", "dominated by light pollution starting at a solar elevation of about −8° during nautical twilight", sun_deg="-8")
add("niebo", "CCT nieba: horyzont od strony Słońca vs zenit", "CCT", "", "K", "Słońce -6°", "UNVERIFIED", "", "", "",
    "Brak liczby w otwartym źródle (Lee & Hernández-Andrés 2003, Appl. Opt. - PDF niedostępny przez proxy). Jakościowo z kadrów: C60 s10, o07, b01 (opis).")

# ---------------------------------------------------------------- 2. ULICE
for cls, L, uo, ul, ti in [("M1", "2.00", "0.40", "0.70", "10"), ("M2", "1.50", "0.40", "0.70", "10"), ("M3", "1.00", "0.40", "0.60", "15"),
                           ("M4", "0.75", "0.40", "0.60", "15"), ("M5", "0.50", "0.35", "0.40", "15"), ("M6", "0.30", "0.35", "0.40", "20")]:
    add("ulica", "klasa oświetleniowa %s (EN 13201-2:2015)" % cls, "L_śr min; Uo min; Ul min; fTI max", "%s; %s; %s; %s" % (L, uo, ul, ti), "cd/m²; -; -; %",
        "wartości eksploatacyjne, nawierzchnia sucha", "SOURCED_SECONDARY", S_PIL, "strona producenta (streszczenie normy; treści normy nie kopiowano)", "Performance in Lighting",
        "Kontrola krzyżowa: M1 2 / M2 1,5 / M6 0,3 cd/m² - Sensors 2024 (CC BY, %s); M6: Lm ≥ 0,30, Uo ≥ 0,35, Ul ≥ 0,40, TI ≤ 20 %% - wydruk DIALux w dokumentacji przetargowej (%s, s. 6)." % (S_SENS, S_PZ),
        "%s | %s | %s | %s | %s" % (cls, L.replace(".", ","), uo.replace(".", ","), ul.replace(".", ","), ti))
for cls, e in [("C2", "20.0"), ("C3", "15.0"), ("C4", "10.0"), ("C5", "7.50")]:
    add("ulica", "klasa oświetleniowa %s (strefy konfliktowe, np. ronda)" % cls, "E_śr min; Uo min", "%s; 0.40" % e, "lx; -", "wartości eksploatacyjne", "SOURCED_SECONDARY", S_PIL,
        "strona producenta (streszczenie normy)", "Performance in Lighting", "Dla ronda Putry właściwa jest klasa C (nie M); która - UNVERIFIED.", "%s | %s | 0,40" % (cls, e.replace(".", ",")))
add("ulica", "ul. gen. Andersa / Al. Tysiąclecia PP / ul. gen. Maczka / rondo Putry / Sokólska / Wysockiego / Kombatantów", "klasa oświetleniowa przypisana ulicy", "", "",
    "", "UNVERIFIED", "", "", "", "Nie znaleziono otwartego dokumentu z klasą dla tych ulic (TED: ogłoszenia bez parametrów; KIO 3018/24, 2732/23, 3524/23, 4185/24 - bez klas; SWZ ZDM z załącznikami niedostępne przez proxy). Analog: DK w Augustowie - klasa M3 w audycie miejskim (BIP Augustów).")
add("ulica", "analog: droga krajowa w mieście (Augustów, ul. 29 Listopada)", "klasa oświetleniowa", "M3", "", "audyt oświetlenia, słupy 8-9 m, nawierzchnia asfalt, szer. 7 m", "ANALOG",
    S_AUG, "dokument urzędowy (BIP)", "Miasto Augustów", "Inne miasto woj. podlaskiego; tylko jako punkt odniesienia rzędu wielkości.", "augustow 29 listopada … asfalt 7 DK M3 po obu stronach")
TED_ROWS = [
 ("ul. gen. Andersa", "281034-2023", "2023-05-12", "ogłoszenie o zamówieniu ZDM-XIV.271.31.2023 „Dostawa i montaż opraw oświetleniowych na terenie Miasta Białegostoku (I)”", "Gen. W. Andersa, Al. 1000-lecia Państwa Polskiego"),
 ("Al. Tysiąclecia Państwa Polskiego", "281034-2023", "2023-05-12", "jw.", "Gen. W. Andersa, Al. 1000-lecia Państwa Polskiego"),
 ("ul. gen. Maczka", "281034-2023", "2023-05-12", "jw.", "Gen. S. Maczka"),
 ("ul. gen. Andersa", "697205-2023", "2023-11-17", "ogłoszenie o udzieleniu zamówienia ZDM-XIV.271.32.2023 „… (II)”", "Gen. Nikodema Saulika, Gen. S. Sosabowskiego, Gen. W. Andersa"),
 ("ul. W. Wysockiego", "697205-2023", "2023-11-17", "jw.", "W. Wysockiego"),
 ("ul. W. Wysockiego", "73896-2024", "2024-02-05", "ogłoszenie o zamówieniu „… (I)” 2024", "12) na ul. W. Wysockiego, 13) na ul. W. Raginisa od ul. W. Wysockiego do ul. M. M. Kolbego"),
]
for ulica, pn, data, co, cyt in TED_ROWS:
    add("ulica", ulica, "wymiana opraw na LED (przetarg ZDM Białystok)", "tak - ulica wymieniona w przedmiocie zamówienia", "", "%s; publikacja TED %s" % (co, data),
        "SOURCED", S_TED % pn, "ogłoszenie urzędowe (TED)", "Miasto Białystok - Zarząd Dróg Miejskich",
        "Obecność frazy potwierdzona zapytaniem pełnotekstowym API TED (api.ted.europa.eu/v3/notices/search, FT ~ \"…\" AND publication-number=…); pełnego tekstu ogłoszeń 2023 nie dało się pobrać (strona TED: HTTP 202/pusta) - zakres odcinków i liczba opraw UNVERIFIED. „energooszczędnych opraw ledowych”.",
        cyt)
add("ulica", "ul. gen. Andersa / Al. 1000-lecia PP / ul. gen. Maczka", "udzielenie zamówienia (I) 2023", "ogłoszenie o udzieleniu 658997-2023", "", "publikacja TED 2023-10-30",
    "SOURCED", S_TED % "658997-2023", "ogłoszenie urzędowe (TED)", "Miasto Białystok - ZDM",
    "Montaż nastąpił więc najwcześniej na przełomie 2023/2024 (data faktycznej wymiany UNVERIFIED). Zgodne z kadrem C60 r07 (02.2022: światło żółtopomarańczowe na Al. Tysiąclecia).", "Miasta Białegostoku (I) … Gen. W. Andersa")
add("ulica", "ul. Sokólska / ul. Kombatantów / rondo Putry", "wymiana opraw na LED", "", "", "ogłoszenia TED ZDM Białystok 2023-2026 (31 szt.)", "UNVERIFIED", "https://api.ted.europa.eu/v3/notices/search", "", "",
    "Zapytania pełnotekstowe o „Sokólskiej”, „Kombatantów”, „Putry” w ogłoszeniach z frazą „opraw … Białegostoku” - 0 trafień. Stan (sód/LED) nieznany.")
add("ulica", "oprawy LED - Białystok (miasto)", "temperatura barwowa opraw ulicznych ZDM", "", "K", "", "UNVERIFIED", S_KIO, "orzeczenie KIO (urzędowe)", "KIO",
    "Wyrok KIO 3018/24 (przetarg ZDM-XIV.271.13.2024) podaje z warunków technicznych tylko: zakres temperatur pracy -40…+50 °C, ENEC/ENEC+, Zhaga-D4i, zabezpieczenie termiczne modułu; CCT nie pada.",
    "zakres temperatury pracy opraw był od -40ºC do +50ºC udokumentowany w certyfikacie ENEC oraz ENEC+")
add("ulica", "analog: oprawy LED na parkingu i ciągach pieszo-jezdnych (Białostocki Park Naukowo-Technologiczny)", "temperatura barwowa; strumień; moc", "4000 ± 200; ≥ 16500; 95-150", "K; lm; W",
    "OPZ dostawy 28 opraw, 2026", "ANALOG", S_BPN, "dokument urzędowy (zamówienie publiczne)", "BPN-T Białystok",
    "Nie ZDM i nie ulica trasy - punkt odniesienia dla „LED neutralny 4000 K” w Białymstoku. Strumień 16,5 klm > założenie gry 8-12 klm (ADR 0191).",
    "Temperatura barwowa światła: 4000 K ± 200 K. … Strumień świetlny oprawy przynajmniej 16 500 lm")
ORTHO = [
 ("ul. gen. Andersa (odc. 53.14638,23.18185 → 53.14785,23.17833)", "41.6", "6", "40.3; 40.9; 42.4; 43.1; 43.3; 39.5", "rząd słupów w pasie dzielącym jezdnie główne; oprawa na wysięgniku (jasna kreska + cień słupa); dodatkowe rzędy na pasach bocznych: 38,7 m i 42 m (po 1 odstępie). 4 słupy potwierdzone w wycinkach 3× z kafla 0,05 m/px.", "53.14712", "23.18009"),
 ("ul. gen. Maczka (odc. 53.15942,23.13476 → 53.15933,23.13045)", "40.4", "6", "40.5; 40.2; 40.0; 39.5; 40.5; 41.0", "słupy w pasie dzielącym, kreska oprawy po obu stronach słupa (prawdopodobnie dwa wysięgniki - ESTIMATED z kształtu).", "53.15938", "23.13261"),
 ("Al. Tysiąclecia PP, odc. południowy (53.14560,23.15714 → 53.14300,23.15749)", "34.8", "7", "36.7; 33.6; 35.4; 35.0; 33.6; 34.2; 34.8", "słupy w pasie dzielącym (trawnik), kreska oprawy po obu stronach (dwa wysięgniki - ESTIMATED z kształtu).", "53.14430", "23.15731"),
 ("ul. Sokólska (odc. 53.15032,23.15357 → 53.14897,23.15133)", "32.4", "5", "32.4; 28.3; 35.5; 32.5; 26.3", "jednostronnie; słupy rozpoznane tylko po cieniach (opraw nie widać) - niska pewność.", "53.14964", "23.15245"),
]
for ul, med, n, vals, uw, la, lo in ORTHO:
    add("ulica", ul, "rozstaw słupów oświetleniowych (mediana)", med, "m", "ortofoto GUGiK HighResolution, kafel 0,1 m/px, n=%s odstępów" % n, "ESTIMATED", S_WMS,
        "GUGiK (dane publiczne, PZGiK)", "GUGiK",
        "Metoda: kafel WMS obrócony do osi odcinka (strip.py), pozycje słupów odczytane z obrazu 960 px (±0,3 m na odczyt, ±1 m na identyfikację podstawy), odstępy kolejnych słupów w jednym rzędzie: %s m. %s Parametry zapytania WMS i współrzędne słupów: ortho_lamp_spacing.csv." % (vals, uw),
        lat=la, lon=lo)
add("ulica", "ul. Kombatantów", "rozstaw słupów oświetleniowych (mediana)", "32.6", "m", "węzły OSM highway=street_lamp, n=3 odstępy (31,3-33,4 m), lamp_mount=bent_mast, light:count=1", "ESTIMATED",
    S_OVP, "ODbL", "© autorzy OpenStreetMap", "Metoda: lampspacing.py (odległość do najbliższej lampy w kierunku osi ulicy, ENU). Zapytanie i data w sources.md. Na pozostałych ulicach trasy OSM ma ≤ 5 węzłów latarni.")
add("ulica", "ulice trasy", "wysokość montażu opraw", "", "m", "", "UNVERIFIED", "", "", "",
    "Nie powtarzam research/mistral/p9-furniture-3 i G5-010 (ZDM PFU: oprawy „do 11 m”). Wysokości dla konkretnych ulic nadal brak; z ortofoto długość cienia bez znanej godziny nalotu nie daje wysokości.")
add("ulica", "Białystok", "załączanie latarni (zegar astronomiczny / próg lx)", "", "", "", "UNVERIFIED", "", "", "",
    "Brak otwartego dokumentu ZDM/PGE dla Białegostoku. Obserwacje z kadrów (wiersze kategorii kadr): latarnie świecą przy Słońcu -3,2° (b08), -3,7° (r04), -4,1° (b01), -5,4° (s10).")
add("ulica", "analog: Augustów (audyt miejski)", "załączanie / wyłączanie wg zegara astronomicznego", "10 min po zachodzie / 20 min przed wschodem", "", "założenie audytu energetycznego", "ANALOG",
    S_AUG, "dokument urzędowy (BIP)", "Miasto Augustów", "10 min po zachodzie w Białymstoku ≈ Słońce -1,5…-2,3° (sun.py; latem płycej). W audycie także: redukcja mocy o 30 % w godz. 24-04, 4000 h świecenia rocznie.",
    "załączaniem oświetlenia ulicznego 10 min. po zachodzi słońca i wyłączaniem oświetlenia 20 min. przed wschodem słońca")

# ---------------------------------------------------------------- 3. OKNA - literatura
add("okna", "bloki mieszkalne (osiedle Výškovice, Ostrawa, CZ)", "maksymalny odsetek okien świecących", "50", "%", "badanie terenowe, liczenie okien w porach największej obecności mieszkańców", "SOURCED",
    S_NOVAK, "CC BY-NC 4.0 - tylko referencja, pliku nie pobrano do paczki", "Novak, Valicek, Gasparovsky, Raditschova, Brzobohaty 2025 (CIE x051:2025)",
    "Wartość maksymalna przyjęta do modelu (9331 okien), nie przebieg godzinowy. Gra: mieszkania 0,40→0,50.",
    "the maximum number of light emitting windows in buildings was established at 50 %")
add("okna", "bloki mieszkalne (jw.)", "średnia luminancja okna świecącego", "6", "cd/m²", "pomiar; okna z firanami/zasłonami, model lambertowski", "SOURCED", S_NOVAK,
    "CC BY-NC 4.0 - tylko referencja", "Novak i in. 2025", "Gra (ADR 0192): 15 cd/m² × ekspozycja → 2,5× więcej niż pomiar.",
    "The average luminance of a light emitting window in a block of flats was found to be 6 cd∙m-2")
add("okna", "bloki mieszkalne (jw.)", "średnia powierzchnia okna; strumień na okno", "1.44; 27", "m²; lm", "model", "SOURCED", S_NOVAK, "CC BY-NC 4.0 - tylko referencja", "Novak i in. 2025", "",
    "average surface of the light emitting window (1.44 m2)")
add("okna", "reklamy podświetlane (jw.)", "średnia luminancja", "50", "cd/m²", "pomiary lokalne i wcześniejsze", "SOURCED", S_NOVAK, "CC BY-NC 4.0 - tylko referencja", "Novak i in. 2025",
    "Punkt odniesienia dla szyldów/witryn na trasie.", "The average luminance of the advertisements was determined … to be 50 cd∙m-2")
add("okna", "światło z okien mieszkań w funkcji godziny (A Coruña, ES)", "przebieg", "maksimum na początku nocy astronomicznej, potem jednostajny spadek do ok. 04:00", "", "rozkład składowych jasności nieba w zenicie", "SOURCED",
    S_BARA, "arXiv (preprint Lighting Res. Technol.)", "Bará, Rodríguez-Arós, Pérez, Tosar, Lima, Sánchez de Miguel, Zamorano 2017",
    "Tylko kształt krzywej (bez odsetka okien). Zgodne z kierunkiem gry (udział rośnie do nocy), ale gra nie ma spadku po 22-23.",
    "residential lights diminish steadily from the end of the astronomical twilight after sunset until about 04:00 h")
add("okna", "budynki mieszkalne i biurowe w Polsce", "odsetek okien oświetlonych w funkcji godziny (dane krajowe)", "", "%", "", "UNVERIFIED", "", "", "",
    "Nie znaleziono otwartego polskiego badania z odsetkiem okien; profile obciążenia taryfy G nie przekładają się wprost na okna. Zastępczo: zliczenia z 13 kadrów Białegostoku (kategoria okna, niżej).")

# ---------------------------------------------------------------- 4. KADRY
FR = json.load(open(os.path.join(HERE, "frames_meta.json"), encoding="utf-8"))
DNI = ["pon.", "wt.", "śr.", "czw.", "pt.", "sob.", "niedz."]
def frame(key, kat, element, opis, status="VERIFIED_WIZJA", parametr="", wartosc="", jedn="", warunki="", uwagi=""):
    m = FR[key]
    loc = dt.datetime.strptime(m["exif_dto"], "%Y:%m:%d %H:%M:%S")
    la, lo = m.get("lat"), m.get("lon")
    e, az = sun.elevation_local(loc, la if la else sun.LAT, lo if lo else sun.LON)
    uw = "Kadr %s. Czas z EXIF DateTimeOriginal (API Commons), przyjęto czas lokalny Europe/Warsaw; %s; azymut Słońca %.0f°. Ekspozycja %s s, ISO %s (telefon, automatyka - jasność kadru nie jest miarą luminancji). Kierunek kadru: brak w EXIF/API. Oglądano miniaturę 1920 px (oryginał %sx%s px, %s B - pobieranie oryginałów blokowane HTTP 429)." % (
        key, DNI[loc.weekday()], az, m.get("exp"), m.get("iso"), m["w"], m["h"], m["bytes_oryg"])
    if not la: uw += " Brak współrzędnych w Commons - elewacja liczona dla centrum Białegostoku."
    if uwagi: uw = uwagi + " " + uw
    r = dict(kategoria=kat, element=element, parametr=parametr, wartość=wartosc, jednostka=jedn, warunki=warunki, wysokość_słońca_deg="%.1f" % e,
             lat="" if not la else "%.6f" % la, lon="" if not lo else "%.6f" % lo, kierunek_deg="UNVERIFIED", data_godzina=loc.strftime("%Y-%m-%d %H:%M:%S"),
             opis_co_widać=opis, url_źródła=m["descurl"], licencja=m["license"], autor="Rakoon (Wikimedia Commons)", data_dostępu=ACCESS, status=status, uwagi=uw, cytat="",
             plik="C60-%s.jpg" % key, url_pliku=m["url_thumb"], sha256=m["sha256"], url_oryginału=m["url_oryg"], sha1_oryginału=m["sha1_oryg"])
    rows.append(r)

# --- ulice (plamy światła, barwa, halo)
frame("r07", "kadr", "Al. Tysiąclecia PP w rejonie ul. Kombatantów (lokalizacja ESTIMATED: współrzędne Commons + przekrój zgodny z ortofoto) - wieczór, mokro",
      "Mokra dwujezdniowa ulica z trawiastym pasem dzielącym; w pasie słupy z dwiema oprawami na wysięgnikach, szereg ginie w perspektywie. Światło opraw żółtopomarańczowe; każda oprawa ma okrągłą poświatę i promieniste smugi (obiektyw). Na mokrym asfalcie pod każdą latarnią podłużna jasna smuga odbicia skierowana do kamery, między smugami nawierzchnia wyraźnie ciemniejsza; suchej plamy rozproszonej nie da się ocenić (mokro). Chodnik z kostki po prawej jaśniejszy pod wiatą. Po lewej stacja paliw z pylonem cenowym i pawilony z neonami (marek nie odtwarzamy). Niebo czarne, bez łuny w kadrze.",
      parametr="plamy / barwa / halo", wartosc="smugi odbić pod latarniami: tak; ciemne przerwy: tak; barwa: żółtopomarańczowa; halo: tak")
frame("r09", "kadr", "Al. Tysiąclecia PP w rejonie ul. Kombatantów (lokalizacja ESTIMATED jw.) - widok w poprzek jezdni na parking galerii, wieczór, mokro",
      "Na pierwszym planie mokra jezdnia z liniami przerywanymi i strzałką; za nią pas z żółtymi barierkami i druga jezdnia, dalej parking z autami i długi pawilon handlowy z podświetlanymi szyldami i wielkoformatową reklamą (marek nie odtwarzamy). Dwie latarnie parkingowe z białym światłem i poświatą; na jezdni kolorowe odbicia szyldów (fiolet, czerwień). Jezdnia na pierwszym planie ciemna, bez wyraźnej plamy latarni; niebo czarne.",
      parametr="plamy / barwa / halo", wartosc="plama na jezdni: niewidoczna (kadr w poprzek, mokro); barwa lamp parkingu: biała; halo: tak")
frame("r08", "kadr", "parking galerii handlowej w rejonie ul. Kombatantów (lokalizacja wg współrzędnych Commons) - wieczór",
      "Parking z kostki, rząd zaparkowanych aut tyłem do kamery, za nimi pawilon z podświetlanymi szyldami i billboardem (marek nie odtwarzamy). Pośrodku słup z oprawą: światło białe z zielonkawą poświatą i smugami. Kostka pod latarnią nieznacznie jaśniejsza, ku pierwszemu planowi ciemnieje do prawie czerni; mokre odbicia na dachach aut. Niebo czarne.",
      parametr="plamy / barwa / halo", wartosc="plama: słaba, zanik ku pierwszemu planowi; barwa: biała; halo: tak")
frame("s10", "kadr", "parking parku handlowego przy ul. Wysockiego (nazwa ulicy na szyldzie) - zmierzch, bezchmurnie",
      "Bezchmurne niebo o zmierzchu: przy horyzoncie po lewej jasny pas żółtawo-brzoskwiniowy, wyżej przejście przez blady róż-lawendę do niebieskiego w górze kadru; brak magenty przy samym horyzoncie. Ciemna linia lasu. Dwie latarnie parkingowe z płaskimi oprawami świecą białym światłem (bliższa z dużą okrągłą poświatą). Nawierzchnia z czerwonej kostki i przejście dla pieszych bez wyraźnej plamy - jasność z nieba jeszcze dorównuje latarniom. Pawilon z podświetlanym szyldem i witrynami (marek nie odtwarzamy), auta z zapalonymi światłami pozycyjnymi.",
      parametr="niebo / plamy / barwa / halo", wartosc="horyzont: żółtawo-brzoskwiniowy → lawenda → niebieski; plamy: niewidoczne przy -5,4°; barwa lamp: biała; halo: tak")
frame("s06", "kadr", "ul. Lipowa (śródmieście) - noc, sucho",
      "Deptakowa część ulicy: jasne płyty chodnika po prawej, jezdnia z kostki po lewej, młode drzewa w kratach. Szereg latarni po obu stronach, światło pomarańczowe (sodowe), każda oprawa z okrągłą poświatą. Na płytach widać łagodne przejścia jasności: jaśniej pod latarniami, ciemniej między nimi, bez ostrych krawędzi plam; elewacje kamienic oświetlone ciepło do wysokości 2-3 kondygnacji. W osi ulicy podświetlona biało wieża kościoła. Witryny po lewej świecą bielą. Niebo czarne.",
      parametr="plamy / barwa / halo", wartosc="plamy: łagodne, widoczne na jasnych płytach; ciemne przerwy: słabe; barwa: pomarańczowa; halo: tak")
frame("s11", "kadr", "ul. Lipowa - noc, śnieg i lód na chodniku",
      "Chodnik z ubitym śniegiem i lodem wzdłuż kamienic po lewej, zaparkowane auta po prawej. Latarnia dwuramienna z dwiema kulistymi oprawami: światło pomarańczowe, bardzo duża poświata i promienie; kolejne latarnie w głębi. Na lodzie pod latarnią jasna, błyszcząca plama odbicia, dalej chodnik ciemnieje; elewacja po lewej zalana ciepłym światłem. Niebo czarne.",
      parametr="plamy / barwa / halo", wartosc="plama odbicia na lodzie: tak; barwa: pomarańczowa; halo: bardzo duże")
frame("s12", "kadr", "ul. Lipowa - noc, mokra kostka, iluminacja świąteczna",
      "Jezdnia z mokrej kostki kamiennej, rząd aut zaparkowanych po prawej przy kamienicach. Latarnie na łukowych wysięgnikach: światło pomarańczowe z poświatą. Na mokrej kostce pod latarniami jasne, ziarniste odbicia; między nimi ciemniej. Nad jezdnią girlandy i drzewa oplecione białoniebieskimi lampkami (dodatkowe źródło, w grze nieobecne). W oddali reflektory nadjeżdżającego auta. Niebo czarne z lekką brunatną łuną.",
      parametr="plamy / barwa / halo", wartosc="odbicia pod latarniami: tak; ciemne przerwy: tak; barwa: pomarańczowa; halo: tak",
      uwagi="Iluminacja świąteczna zawyża jasność sceny.")
frame("s02", "kadr", "ul. Lipowa 12 - wieczór, iluminacja świąteczna",
      "Jezdnia z kostki, przejeżdżające auto rozmyte ruchem, rząd zaparkowanych aut. Latarnie na łukowych wysięgnikach świecą pomarańczowo z dużą poświatą; drzewa oplecione białoniebieskimi lampkami, napis świetlny nad ulicą. Chodnik z płyt po prawej równomiernie jasny (suma latarni i lampek), plam pojedynczych latarni nie da się wydzielić. Kamienice 3-kondygnacyjne, w oknach pięter ciemno. Niebo ciemnobrunatne.",
      parametr="plamy / barwa / halo", wartosc="plamy: nie do wydzielenia (iluminacja); barwa latarni: pomarańczowa; halo: tak")
frame("s04", "kadr", "ul. Lipowa - wieczór, mokry chodnik, resztki śniegu",
      "Chodnik z płyt z pasem kostki, mokry, z resztkami śniegu; po lewej elewacja z roletą i zielonym neonem apteki nad wejściem (zielona poświata na ścianie i schodach). Po prawej jezdnia z autami (zapalone reflektory), drzewa z białoniebieskimi lampkami, latarnie z pomarańczowym światłem i poświatą. W osi podświetlona wieża kościoła. Mokre płyty odbijają światła witryn i latarni podłużnymi smugami. Niebo czarne.",
      parametr="plamy / barwa / halo", wartosc="smugi odbić na mokrych płytach: tak; barwa latarni: pomarańczowa; halo: tak")
frame("s07", "kadr", "ul. Lipowa - wieczór, śnieg na trawniku, mokra jezdnia",
      "Mokra jezdnia, przystanek z autobusem w głębi, piesi na chodniku po lewej. Na pierwszym planie słup z łukowym wysięgnikiem i oprawą świecącą pomarańczowo, z dużą poświatą; drzewa z białoniebieskimi lampkami. Na mokrej jezdni odbicia świateł aut i latarni; pryzmy śniegu jasne. Kamienica po prawej oświetlona ciepło, w oknach pięter ciemno poza fioletową witryną na parterze. Niebo czarne.",
      parametr="plamy / barwa / halo", wartosc="odbicia: tak; barwa latarni: pomarańczowa; halo: duże")
frame("s08", "kadr", "przystanek w śródmieściu z widokiem na biały kościół z wieżą - zmierzch, zachmurzenie",
      "Kadr pionowy: plac z czerwonej kostki z przystankiem (wiata, słupek informacyjny), kilka osób. Kostka zalana pomarańczowym światłem latarni spoza kadru; cienie ludzi i kosza długie, miękkie. W tle biały kościół z wieżą podświetlony chłodną bielą. Niebo zachmurzone, ciemnogranatowe z jaśniejszymi brzegami chmur - bez ciepłej poświaty. Po prawej latarnia z pomarańczowym światłem i mokra jezdnia z odbiciami.",
      parametr="niebo / barwa", wartosc="niebo pochmurne przy -7,9°: ciemnogranatowe, bez różu; barwa latarni: pomarańczowa")
frame("b07", "kadr", "osiedle bloków 5-kond. (lokalizacja wg współrzędnych Commons) - latarnia przy ciągu pieszym, noc",
      "Słup z oprawą na krótkim wysięgniku przed parterowym pawilonem: światło białe, zimne, z poświatą. Pod latarnią wyraźna jasna plama na trawniku, chodniku i białej ścianie pawilonu; poza zasięgiem ok. kilku metrów trawnik i ścieżka przechodzą w czerń. Elewacja bloku oświetlona tylko w dolnej części. Niebo brunatne (łuna).",
      parametr="plamy / barwa / halo", wartosc="plama: wyraźna, ostry zanik; barwa: biała zimna; halo: tak")
frame("b06", "kadr", "ulica osiedlowa wzdłuż długiego bloku 5-kond. - noc",
      "Długi blok w skrócie perspektywicznym, wzdłuż niego zaparkowane auta i samochód dostawczy na pierwszym planie. Przy bloku oprawa na słupie świeci jaskrawą bielą z dużą poświatą - oświetla ścianę bloku i dostawczaka; dalej wzdłuż ulicy kolejne, słabsze punkty światła. Niebo jednolicie pomarańczowobrunatne (łuna miejska na niskich chmurach). Jezdnia w cieniu aut - plam nie widać.",
      parametr="plamy / barwa / halo / niebo", wartosc="plama na elewacji: tak; na jezdni: zasłonięta; barwa: biała; halo: duże; niebo: pomarańczowobrunatna łuna")
frame("r01", "kadr", "ul. Wysockiego - kadr ODRZUCONY jako zmierzch",
      "Mokra jezdnia po deszczu, niebo jasne, zachmurzone, latarnie zgaszone - światło dzienne.", status="REJECTED",
      uwagi="Nazwa pliku sugeruje 21:09 (Słońce -2,8°), ale EXIF podaje 18:14 - dzień. Wniosek metodyczny: znacznik czasu w nazwie plików tego autora bywa czasem wysłania; używać tylko EXIF.")

# --- okna (zliczenia)
def okna(key, element, lit, total, opis, uw=""):
    frame(key, "okna", element, opis, status="ESTIMATED", parametr="okna zapalone / widoczne", wartosc="%d/%d = %d %%" % (lit, total, round(100.0 * lit / total)), jedn="szt.; %",
          uwagi="Zliczenie ręczne z kadru 1920 px (i wycinka 1,5-2×); niepewność ok. ±2 zapalone, ±10 %% mianownika. " + uw)
okna("r04", "blok 4-kond., ul. Hallera 42, os. Dziesięciny I (adres z tytułu pliku Commons) - zmierzch", 8, 40,
     "Blok 4-kondygnacyjny w skrócie perspektywicznym, elewacja kremowa z zielonymi pasami, drzewo na pierwszym planie, niebieskie auto na drodze osiedlowej. Zapalone okna świecą ciepłą żółcią/pomarańczem (część przez żaluzje i rolety); większość okien ciemna, z jasnymi firanami. W głębi świeci pojedyncza oprawa. Niebo jasnoszare, zachmurzone.",
     "Okna dalekiej części elewacji pod ostrym kątem pominięte.")
okna("b01", "blok 5-kond. z numerem 43 na elewacji (lokalizacja wg współrzędnych Commons) - zmierzch, bezchmurnie", 9, 32,
     "Blok 5-kondygnacyjny widziany od narożnika: ściana szczytowa z jednym pionem okien i długa elewacja w skrócie. Zapalone okna żółtopomarańczowe; na szczycie 3 z 5, na elewacji długiej 4 z ok. 22; w niskim budynku po lewej 2 z 5. Latarnia na łukowym wysięgniku nad chodnikiem świeci ciepłą bielą z rozległą poświatą na tle nieba. Niebo bezchmurne, równomiernie niebieskie, przy dolnej krawędzi jaśniejsze, bez różu.",
     "Latarnia świeci przy Słońcu -4,1°.")
okna("b03", "blok 5-kond. z balkonami (adres ul. Kard. St. Wyszyńskiego widoczny na sąsiednim budynku) - część mieszkalna", 12, 50,
     "Prawa część kadru: blok mieszkalny 5-kondygnacyjny z balkonami (wypełnienia żółte i czerwone), parter usługowy z witrynami. Zapalone okna rozrzucone pojedynczo, po 2-4 na kondygnację; barwa od ciepłej żółci po chłodną biel (jedno okno jaskrawobiałe), część za firanami świeci słabo. Elewację oświetlają latarnie uliczne (pomarańczowe) - ciemne okna z jasnymi firanami wyglądają na szare, nie czarne. Mokra jezdnia z odbiciami, auta na parkingu.")
frame("b03", "okna", "budynek biurowy spółdzielni (lewa część tego samego kadru)",
      "Lewa część kadru: 4-kondygnacyjny budynek biurowy z napisem instytucji na attyce (nie odtwarzamy). Okna trójdzielne w regularnej siatce; zapalone całymi pomieszczeniami na 2. i 3. kondygnacji (zimna biel świetlówek), najwyższa kondygnacja ciemna; parter częściowo oświetlony. Latarnia uliczna z pomarańczowym światłem i dużą poświatą przed budynkiem.",
      status="ESTIMATED", parametr="okna zapalone / widoczne", wartosc="7/21 = 33 %", jedn="szt.; %",
      uwagi="Ten sam plik co wiersz wyżej (jeden kadr, dwa budynki). Zliczenie ręczne; ±2. Piątek 16:32 - koniec godzin pracy.")
okna("b04", "bloki 5-kond. (lokalizacja wg współrzędnych Commons) - noc", 17, 62,
     "Droga osiedlowa z zaparkowanymi autami między blokami; bliski blok po lewej i elewacja po prawej zalane zielonkawym światłem latarni (balans bieli telefonu), dalszy blok w głębi częściowo za drzewem. Zapalone okna ciepłe (żółć, pomarańcz, pojedyncze różowe), w bliskim bloku świecą też wąskie okna klatki schodowej (3 kondygnacje). Niebo brunatnofioletowe.",
     "Mianownik niepewny: ciemne okna za drzewem niewidoczne, przyjęto rytm elewacji (ok. 30 okien); w części dobrze widocznej 5/32.")
okna("b05", "kamienica/blok 4-kond. z balkonami w śródmieściu - noc, montaż iluminacji", 2, 34,
     "Budynek 4-kondygnacyjny z balkonami, parter usługowy z witrynami; przed nim podnośnik koszowy i drzewa z białymi lampkami, śnieg na autach. Elewacja jasna od latarni ulicznych; prawie wszystkie okna pięter ciemne z jasnymi firanami, jedno świeci pomarańczowo, jedno niebieskawo. Niebo czarne.",
     "Sobota 18:52 - bardzo mało zapalonych okien od strony ulicy (budynek z lokalami usługowymi, możliwe pokoje od podwórza).")
okna("b06", "długi blok 5-kond. przy ulicy osiedlowej - wieczór", 10, 45,
     "Opis sceny jak w wierszu kadru ulicznego b06. Zapalone okna: trójdzielne okno na najwyższej kondygnacji blisko kamery (jasna żółć), kilka okien pośrodku elewacji (biel i żółć), pojedyncze w dalszej części; pozostałe ciemne.",
     "Ten sam plik co wiersz kategorii kadr. Dalsza część elewacji pod ostrym kątem - mianownik szacowany z rytmu.")
okna("b07", "blok 5-kond. i sąsiedni blok w głębi - wieczór", 8, 17,
     "Opis sceny jak w wierszu kadru b07. Zapalone okna: trójdzielne na najwyższej kondygnacji (żółć), okno z czerwoną zasłoną (świeci czerwono), dwa pomarańczowe na parterze po lewej, dwa-trzy w bloku w głębi po prawej; reszta ciemna.",
     "Ten sam plik co wiersz kategorii kadr. Odsetek ZAWYŻONY: ciemne okna na nieoświetlonej elewacji są niewidoczne i nie weszły do mianownika.")
okna("b08", "blok 8-kond. z lokalami w parterze (os. Słoneczne Tarasy - wg kategorii Commons) - zmierzch, zachmurzenie", 7, 110,
     "Duży blok 8-kondygnacyjny z balkonami o szklanych balustradach i czerwonych panelach, parter usługowy z oświetlonymi witrynami i szyldami (marek nie odtwarzamy). Zapalonych okien pojedyncze sztuki (żółte), głównie w środkowej części; ogromna większość ciemna. Latarnia po lewej już świeci (ciepła biel/pomarańcz, poświata), sygnalizator czerwony. Niebo zachmurzone, szaroniebieskie.",
     "Słońce -3,2°: latarnie włączone, okna prawie nie. Kadr lekko poruszony.")
okna("s01", "budynek urzędowo-biurowy 4-kond., ul. Lipowa 51 (wg kategorii Commons) - zmierzch (grudzień, czwartek 15:57)", 5, 22,
     "Kadr pionowy: budynek z boniowanym parterem i wejściem po schodach, przed nim drzewa i zielona neonowa choinka. Na piętrach zapalone pojedyncze pokoje (ciepła biel), reszta okien ciemna; parter i wejście jasno oświetlone. Niebo ciemnoniebieskie z chmurami. Mokra jezdnia i przejście dla pieszych z zieloną poświatą neonu.")
okna("s03", "ten sam budynek urzędowo-biurowy - po godzinach (marzec, czwartek 18:44)", 1, 30,
     "Ten sam budynek co s01, kadr poziomy: elewacja podświetlona od dołu punktowo (jasne plamy między oknami), wejście z jasnym daszkiem. Okna pięter ciemne; w jednym widać kolorowy ekran. Kiosk i parking na pierwszym planie, słupki biało-czerwone. Niebo granatowe.",
     "Po godzinach pracy biurowiec praktycznie ciemny (iluminacja elewacji ≠ okna).")
okna("o01", "pawilony handlowo-usługowe 2-kond. - zmierzch, zachmurzenie", 2, 10,
     "Zespół 2-kondygnacyjnych pawilonów ze świetlikami na dachach; parter z oświetlonymi witrynami (ciepła biel, kolorowe wystawy), okna piętra w większości ciemne. Plac z mokrej kostki bardzo ciemny, odbija światła witryn; piesza postać i auto tyłem. Niebo całkowicie zachmurzone: jednolity ciemny granat bez żadnej ciepłej poświaty.",
     "Wzorzec nieba pochmurnego przy Słońcu ok. -5°.")
okna("o07", "biurowiec z przeszkloną elewacją (dom techniki) - zmierzch, bezchmurnie (środa 17:55)", 6, 11,
     "Budynek 3-kondygnacyjny: duże przeszklone pola. Górny rząd szklanych pól ciemny (odbija niebo), środkowy rząd w całości zapalony ciepłą bielą (widać rośliny i meble), po lewej jedno okno zapalone i jedno ciemne, parter - oświetlone witryny. Niebo bezchmurne, głęboki błękit jaśniejszy ku dołowi po lewej.",
     "Jednostka = pole przeszklenia, nie okno.")

# ---------------------------------------------------------------- zapis
for i, r in enumerate(rows, 1):
    r["id"] = "C60-%03d" % i
with open(os.path.join(HERE, "manifest.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in COLS})
print("wierszy:", len(rows), "z plikiem:", sum(1 for r in rows if r.get("plik")), "unikalnych plików:", len({r["plik"] for r in rows if r.get("plik")}))
