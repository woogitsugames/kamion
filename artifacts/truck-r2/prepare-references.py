"""Downsize locally provided reference photographs; no game assets are written."""
from pathlib import Path
from PIL import Image

out = Path(__file__).resolve().parent / 'references'
source = Path('C:/Users/matma/Documents/Claude/kamion/Data/photos/nowe')
out.mkdir(exist_ok=True)
jobs = [
    ('curtain-yellow-working.jpg', 'trailer_Tony_Powell_Transport_ML02_PNZ_DAF_CF_artic_curtainsider_Port_of_Teignmouth_24_April_2012.jpg', 'Barry Lewis', 'CC BY 2.0', 'https://commons.wikimedia.org/wiki/File:Tony_Powell_Transport_(ML02_PNZ)_DAF_CF_artic_curtainsider,_Port_of_Teignmouth,_24_April_2012.jpg'),
    ('curtain-blue-working.jpg', 'trailer_Richard_Westbury_Volvo_FH460_artic_curtainsider_Port_of_Teignmouth_29_March_2012.jpg', 'Barry Lewis', 'CC BY 2.0', 'https://commons.wikimedia.org/wiki/File:Richard_Westbury_Volvo_FH460_artic_curtainsider,_Port_of_Teignmouth,_29_March_2012.jpg'),
    ('tractor-rear-working.jpg', 'Volvo_Truck_FH-Semi-trailer_truck-03ASD.jpg', 'Asurnipal', 'CC BY-SA 4.0', 'https://commons.wikimedia.org/wiki/File:Volvo_Truck_FH-Semi-trailer_truck-03ASD.jpg'),
]
lines = ['# Źródła zdjęć rundy 2', '',
         'Autorzy i licencje według docs/REFERENCES.md. Pliki wejściowe są dostarczonymi lokalnymi zdjęciami, a nie obrazami AI. Zmiana: wyłącznie zmniejszenie do maksymalnie 960 px; zachowano kolory i orientację. Zdjęcia nie trafiają do gry.', '',
         'Porównania są jakościowe: inne modele pojazdów, pozycje kamer, stan zużycia i światło. Nie stanowią kalibracji fotometrii ani jasności białego lakieru.', '']
for target, filename, author, licence, url in jobs:
    with Image.open(source / filename) as original:
        preview = original.convert('RGB')
        preview.thumbnail((960, 960), Image.Resampling.LANCZOS)
        preview.save(out / target, quality=94)
    lines.append(f'- `{target}`: {author}, {licence}. [Źródło]({url}). Lokalny plik wejściowy: `{filename}`.')
lines += ['', 'Licencje: [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Kopia zdjęcia Asurnipala zachowuje CC BY-SA 4.0.']
(out / 'CREDITS.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
print('Prepared three photo references, maximum dimension 960 px.')
