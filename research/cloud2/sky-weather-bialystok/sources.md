# Źródła — R7 sky-weather-bialystok (dostęp: 2026-11-14)

| źródło | URL | licencja / status | użycie |
|---|---|---|---|
| IMGW-PIB, dane pomiarowo-obserwacyjne (synop miesięczne 1991–2023, terminowe 2014–2023, Opis.txt, formaty, wykaz stacji) | https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/ (lista plików z sha256: `imgw_files.csv`) | Regulamin udostępniania danych IMGW-PIB: nieodpłatnie, obowiązek podania źródła i informacji o przetworzeniu | zachmurzenie, usłonecznienie, mgła, widzialność, śnieg, parowanie zdjęć |
| Regulamin udostępniania danych IMGW-PIB | https://danepubliczne.imgw.pl/regulations | — | warunki licencji (R7-610…612) |
| IMGW-PIB, Normy klimatyczne 1991–2020 | https://klimat.imgw.pl/pl/climate-normals/{TSR_AVE,OPAD_SUMA,SNIEG_0,USL,ZACHM,D_POCHMURNE,D_POGODNE} | jw. | normy oficjalne (R7-001…007) |
| NOAA GML Solar Calculator — opis obliczeń | https://gml.noaa.gov/grad/solcalc/calcdetails.html | domena publiczna (rząd USA) | algorytm w tools_sun.py (wzory przepisane do nagłówka pliku; strony nie cytowano dosłownie) |
| astral 3.2 (PyPI) | https://pypi.org/project/astral/ | Apache-2.0 | niezależna kontrola słońca w audit.py |
| WMO, Guide to Instruments and Methods of Observation (WMO-No. 8), Vol. I, rozdz. 9 — wersja wstępna 2018 | https://old.wmo.int/extranet/pages/prog/www/IMOP/publications/CIMO-Guide/Prelim_2018_ed/8_I_9_en_MR_tc.pdf | dokument publiczny WMO | MOR, próg 0,05, Koschmieder 0,02 |
| CIE — opis normy ISO 15469:2004 / CIE S 011:2003 | https://cie.co.at/node/4086 | strona wydawcy; norma płatna, nie pobrano | zakres normy, niebo pochmurne jako osobny wzór |
| rcaiman (pakiet R), `data/cie_table.rda`, `R/data.R`, commit c2124fb | https://github.com/GastonMauroDiaz/rcaiman | GPL-3; tabela wg ISO 15469 za Li i in. 2016, doi:10.1016/j.energy.2016.02.054 | parametry a–e typów 1–5, wzory gradacji i indykatrysy |
| Lee & Hernández-Andrés 2005; Lee 2008; Lee & Hernández-Andrés 2003; Lee 1994; Lee & Mollner 2017; Hulburt 1953 | doi:10.1364/AO.44.005712; 10.1364/AO.47.00H106; 10.1364/AO.42.000445; 10.1364/AO.33.004629; 10.1364/AO.56.00G179; 10.1364/JOSA.43.000113 (abstrakty: https://api.openalex.org/works/https://doi.org/<DOI>) | abstrakty z OpenAlex (CC0); pełne teksty nie pobrane | barwa nieba pochmurnego i zmierzchu |
| Wikimedia Commons — 27 zdjęć (26 × CC0, autor Rakoon; 1 × CC BY-SA 4.0, autor MOs810) | strony plików w manifeście (`url_źródła`), miniatury 1280 px przez Special:FilePath | CC0 / CC BY-SA 4.0 (referencja, nie tekstura) | kadry nieba |
| Panoramax — 8 zdjęć (stanton, ZX_OSM_USER, BENCH_MAPPER) | https://api.panoramax.xyz/api/search?bbox=22.9,53.0,23.45,53.3&limit=1000&datetime=<zakres> (7 zapytań, 2026-11-14 ok. 17:10 UTC) | CC BY-SA 4.0 (referencja, nie tekstura) | kadry nieba z azymutem |
| Repo: ADR 0010, 0080, 0182, 0192; SkyModel.cs, EnvironmentLighting.cs | `docs/adr/`, `game/Assets/_Project/Rendering/Runtime/Sky/` | własne | stan obecny, hipoteza |

Nie użyto: Google/Bing/Apple/Yandex, Mapillary, obrazów NC/ND. Overpass nie był potrzebny.
