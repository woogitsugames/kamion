# Pliki binarne (files/*.jpg) — notka techniczna

Gałąź research/p7-s8-signs-2 zawiera całą treść tekstową paczki
(README.md, manifest.csv, asset_manifest.csv, mapillary_recheck.csv,
audit_20_percent.json, sources.md, LICENSE-DATA.md).

Plików binarnych (7 zdjęć JPG w files/, łącznie ~0,9 MB) nie wypchnięto do
gałęzi: zdalny commit wykonano narzędziem MCP github_app.push_files, które
przyjmuje wyłącznie treści tekstowe (UTF-8) — testem zweryfikowano, że bajty
>0x7F są podwójnie kodowane (mojibake), co uszkadza JPEG (próbny plik
files/P7-001.jpg wypchnięty w ten sposób był uszkodzony i został usunięty).
Pełne, nieuszkodzone pliki znajdują się w paczce gptpro-p7-s8-signs-2.zip
(dostarczonej oddzielnie zleceniodawcy) wraz z manifestem i audytem.

Pliki JPG są odtwarzalne: P7-001…P7-005, P7-007 = Mapillary thumb_1024
(klucze w manifest.csv, kolumna mapillary_key), P7-006 = Wikimedia Commons
Special:FilePath (File:7204 May 2021 in Białystok.jpg, ?width=1280, CC0).

SHA-256 plików (do weryfikacji po pobraniu z paczki):

- files/P7-001.jpg — 83680 B — sha256 bd20b709f06e00429523b4efabe6066a8db5df54422c076f844cfd82f77363ac — 1024×768 px — CC BY-SA 4.0 — richlv
- files/P7-002.jpg — 99920 B — sha256 ddc5d140524228816c94761395fd133d0e324ea42a30823764810581938d9f19 — 1024×768 px — CC BY-SA 4.0 — kino
- files/P7-003.jpg — 109678 B — sha256 5ad390a86d1ca2066904e2a8d8c18bda069bf47ecb741df3792b2a149e520181 — 1024×768 px — CC BY-SA 4.0 — richlv
- files/P7-004.jpg — 94851 B — sha256 6b305ffa1c59b2f161cbaae189a374160f04c4121a0988f298b8094903cee843 — 1024×768 px — CC BY-SA 4.0 — kino
- files/P7-005.jpg — 107148 B — sha256 a75271199e9f3c40d70f210f09a0c953242b894723182dc666ddf47f2888866b — 1024×768 px — CC BY-SA 4.0 — richlv
- files/P7-006.jpg — 220245 B — sha256 d506d84cef1fc3dfc8746ca16fe5041433007b7f22f11ae9ed8e85579cb3240d — 1280×853 px — CC0 — Rakoon
- files/P7-007.jpg — 120626 B — sha256 b6919dd73c0fcc62803b3807bce3bc8421435d33a7596ec5dfe2077b3724a921 — 1024×768 px — CC BY-SA 4.0 — quickness805
