from pathlib import Path
from urllib.request import urlretrieve

tones= [
    'C','C#','D','D#','E','F',
    'F#','G','G#','A','A#','B'
]
octs = [4,5]
url = 'https://cdn.jsdelivr.net/npm/tonejs-instrument-piano-ogg@1.1.0/'
folder = Path(__file__).resolve().parent / 'audio'
folder.mkdir(exist_ok=True)

for octv in octs:
    for note in tones:
        name = f'{note}{octv}'
        file= name.replace('#', 's') + '.ogg'
        path = folder / file
        if not path.exists():
            print(f'Downloading {name}...')
            urlretrieve(url + file, path) 
print('All piano sounds are dowloaded!! :D')