# Pliki binarne (files/*.jpg) — notka techniczna

Gałąź research/p10-street-greenery-2 zawiera całą treść tekstową paczki
(README.md, manifest.csv, sources.md, audit_20_percent.json).

Plików binarnych (13 zdjęć JPG w files/, łącznie ~5 MB) **nie wypchnięto do
gałęzi**: zdalny commit wykonano narzędziem MCP github_app.push_files,
które przyjmuje wyłącznie treści tekstowe i koduje je jako UTF-8 — testem
zweryfikowano, że bajty >0x7F są podwójnie kodowane, co uszkodziłoby JPEG
(UTF-8 → base64 → blob). Pełne, nieuszkodzone pliki binarne znajdują się
w paczce gptpro-p10-street-greenery-2.zip (dostarczonej oddzielnie zleceniodawcy),
wraz z manifestem (licencje: wszystkie CC0 1.0, autor: Rakoon) i sumami kontrolnymi.

SHA-256 plików (do weryfikacji po pobraniu z paczki):

- files/P10-101.jpg — 514381 B — sha256 4b25601ea1da04cf4a2ef15e5cb3074b4111b9883cef29025f56b5ef6b4f6b7e
- files/P10-102.jpg — 331352 B — sha256 01cfb7b91cdb65803ce20d269076364a15f976126d59da757b12a58c17df9439
- files/P10-103.jpg — 307364 B — sha256 26d470a187fea15ef17e1cecd74636a1e2e88600c5b0c1474e22c71dab6a60da
- files/P10-104.jpg — 374107 B — sha256 67891c8d64f50185ccd5f2e5674e482306503e88814b463db20ce0337441540d
- files/P10-105.jpg — 404270 B — sha256 bbe3c3b71a40d93368c7faaee1326296584575c25d6d7e8bf31f80c09e32ff32
- files/P10-106.jpg — 419037 B — sha256 74541fe8d9185628cec1280863a5b30f9c5faed700865165687feae527e38af5
- files/P10-107.jpg — 498848 B — sha256 70c8d6105bb5ed577e4a6601a607c18e9ca260cdb8b47fab108eaaeb6028e282
- files/P10-109.jpg — 267355 B — sha256 01486b174e31312b1fdb6786de96f89d930b8ef66b598e266f4faefede368885
- files/P10-110.jpg — 213926 B — sha256 135fa080bc1258733ff554325cf28a99e9d000baa8aad5c7818649a6f5f34e1c
- files/P10-111.jpg — 326482 B — sha256 5bd85c55ce3ee6fc447d0ac272e3e80ff9919e6c861219cedff5ebc806d88459
- files/P10-112.jpg — 689746 B — sha256 b472fa913ca4bb6ca2b3b15a1b0ade38ed1e87ae8505dbe68e2c388f21b1e856
- files/P10-113.jpg — 528909 B — sha256 fd9c393c00eb46a1f166e6f1f184fc4592885346e84b5489157b875aa6096c7e
- files/P10-114.jpg — 265270 B — sha256 3899690207b21faf47fe16cec17b7a73d11b4c67f56858a12fd7d82fc784ae4c
