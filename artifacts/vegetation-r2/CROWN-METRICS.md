# Pomiary koron ? te same ROI i maska

Rec709 na sRGB8 po redukcji do <=960px. Maska zachowuje piksele <16; ?r?d?owe SHA i wsp??rz?dne s? w JSON. Zmiana geometrii zmienia liczb? pr?bek w masce. Zdj?cia maj? inne ekspozycje/sezon, nie s? dok?adnym celem albedo.

| Profil / ?wiat?o | Kamera | p10 przed ? po | p50 przed ? po | <16% przed ? po |
|---|---|---:|---:|---:|
| Low-overcast | dk8-dk19-exit | 18.644 ? 33.140 | 31.147 ? 42.495 | 5.427 ? 0.000 |
| Low-overcast | driver-andersa-to-putry | 41.859 ? 43.933 | 67.503 ? 69.146 | 0.000 ? 0.000 |
| Low-overcast | route-putry-approach | 49.218 ? 49.713 | 63.993 ? 72.203 | 0.000 ? 0.000 |
| Low-clear | dk8-dk19-exit | 30.359 ? 43.852 | 48.358 ? 62.633 | 0.000 ? 0.000 |
| Low-clear | driver-andersa-to-putry | 43.789 ? 47.207 | 65.558 ? 69.770 | 0.000 ? 0.000 |
| Low-clear | route-putry-approach | 60.147 ? 63.641 | 93.269 ? 96.903 | 0.000 ? 0.000 |
| High-overcast | dk8-dk19-exit | 21.504 ? 35.849 | 34.786 ? 46.064 | 0.861 ? 0.070 |
| High-overcast | driver-andersa-to-putry | 46.787 ? 47.722 | 73.290 ? 74.503 | 0.000 ? 0.000 |
| High-overcast | route-putry-approach | 56.709 ? 56.565 | 73.491 ? 82.928 | 0.000 ? 0.000 |
| High-clear | dk8-dk19-exit | 34.147 ? 47.635 | 52.072 ? 65.205 | 0.000 ? 0.000 |
| High-clear | driver-andersa-to-putry | 48.139 ? 50.426 | 71.927 ? 75.413 | 0.000 ? 0.000 |
| High-clear | route-putry-approach | 71.718 ? 69.495 | 103.598 ? 106.976 | 0.000 ? 0.000 |

Putry overcast: wzrost mediany o oko?o12,8% w obu profilach; p10 pozostaje bliskie bazowemu. To ujawniona zmiana rozk?adu, nie twierdzenie o niezmienionej jasno?ci zdrowych koron.
Druga fotografia ma mask? tylko5,3% obszaru ROI ? ma ograniczon? warto?? kalibracyjn?.
