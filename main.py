import pygame
from pygame import mixer
from pathlib import Path
import json


pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(50)

tfont = pygame.font.Font('extras/OpenDyslexic-Bold.otf', 40)
font = pygame.font.SysFont('Arial', 17)
bfont = pygame.font.SysFont('Arial', 15)
smfont = pygame.font.SysFont('Arial', 12)

wid = 1200
hgt = 540
scr = pygame.display.set_mode([wid, hgt])
pygame.display.set_caption('PIANO')

fps=60
clk = pygame.time.Clock()

notes = ['C','D','E','F','G','A','B']
octs = [4,5]
key_w=68
key_h=275
key_x=(wid - 14 *key_w) //2
key_y = 210

bg = (35,35,40)
white = (250,250,248)
edge = (46,46,46)
gray = (180, 180, 185)
amber = (221, 148, 22)

blk_w=40
blk_h=160
black = (25, 25, 30)
sharp = ['C#','D#','F#','G#','A#']
spots = [0,1,3,4,5]
wkeys = []
bkeys = []

for i in range(14):
    x = key_x+i * key_w
    rect = pygame.Rect(x, key_y, key_w, key_h)
    note = notes[i % 7]
    octv= octs[i//7]
    name = f'{note}{octv}'
    wkeys.append((name, rect))

for o, octv in enumerate(octs):
    for i, spot in enumerate(spots):
        x = key_x + (o*7+spot+1)* key_w
        x -= blk_w // 2
        rect = pygame.Rect(x, key_y, blk_w, blk_h)
        name = f'{sharp[i]}{octv}'
        bkeys.append((name, rect))

tones = ['C','C#','D','D#','E','F',
         'F#','G','G#','A','A#','B']
left= 'zsxdcvgbhnjm'
right= 'r5t6yu8i9o0p'
bind ={}
held=set()

for i, key in enumerate(left):
    code = pygame.key.key_code(key)
    bind[code]= f'{tones[i]}{octs[0]}'
for i, key in enumerate(right):
    code = pygame.key.key_code(key)
    bind[code]= f'{tones[i]}{octs[1]}'

root = Path(__file__).resolve().parent
snd = {}
for name, rect in wkeys + bkeys:
    file = name.replace('#','s')+ '.ogg'
    path = root / 'audio' / file
    snd[name] = mixer.Sound(str(path))

plays = {}
pedal = False
prev = set()
vol = 0.7
song =[]
folder = root / 'songs'
files = sorted(folder.glob('*.json')) #ily glob
pick = len(files)-1 if files else 0
msg = ''

rec = False
rec_at = 0
rec_prev = set()
playing = False
play_at =0
step =0
phold = set()

edit = False
typed = ''
target = None
btns = {
    'PREV': pygame.Rect(40, 18, 28, 36),
    'NEXT': pygame.Rect(82, 18, 28, 36),
    'RENAME': pygame.Rect(125, 18, 110, 28),
    'REC': pygame.Rect(560, 18, 78, 28),
    'STOP': pygame.Rect(648, 15, 40, 34),
    'PLAY': pygame.Rect(698, 15, 40, 34),
    'CLEAR': pygame.Rect(750, 18, 78, 28),
    'SAVE': pygame.Rect(838, 18, 78, 28),
    'LOAD': pygame.Rect(926, 18, 78, 28)
}
stop_at = -1000
def hush(ms=100):
    for chan in plays.values():
        chan.fadeout(ms)
    plays.clear()
    prev.clear()


tabs= ['PIANO', 'METRONOME', 'TUNER']
tab = 'PIANO'
tabrs ={}

for i, name in enumerate(tabs):
    x=20+i*145
    rect = pygame.Rect(x, 8, 135, 32)
    tabrs[name]= rect

run = True
while run:
    clk.tick(fps)
    
    for evt in pygame.event.get():
        act = None
        if edit and evt.type != pygame.QUIT:
            if evt.type == pygame.TEXTINPUT:
                for ch in evt.text:
                    if len(typed) < 24:
                        if ch.isalnum() or ch in ' _-':
                            typed += ch

            elif evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_BACKSPACE:
                    typed = typed[:-1]
                elif evt.key == pygame.K_ESCAPE:
                    edit = False
                    pygame.key.stop_text_input()
                    msg = 'Rename is cancelled'

                elif evt.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    name = typed.strip()
                    if not name:
                        msg = 'Please enter a name :D'
                    else:
                        dest = folder / f'{name}.json'
                        if dest.exists() and dest != target:
                            msg = 'That name already exists D:'
                        else:
                            try:
                                target.rename(dest)
                                files = sorted(folder.glob('*.json'))
                                pick = files.index(dest)
                                edit= False
                                pygame.key.stop_text_input()
                                msg = f'You just renamed your song to: {name}!'
                            except OSError:
                                msg = 'Could not rename the song :(('
            continue

        if evt.type == pygame.QUIT:
            run = False
        elif evt.type == pygame.KEYDOWN:
            if evt.key == pygame.K_SPACE:
                pedal = True
            if evt.key in bind:
                held.add(bind[evt.key])
            if evt.key in (pygame.K_EQUALS, pygame.K_PLUS):
                vol = min(1.0, round(vol + 0.1, 2))
            elif evt.key ==pygame.K_MINUS:
                vol = max(0.0, round(vol - 0.1, 2))
            for chan in plays.values():
                chan.set_volume(vol)
            if evt.key == pygame.K_TAB:
                act = 'STOP' if rec else 'REC'
            elif evt.key == pygame.K_RETURN:
                act = 'PLAY'
            elif evt.key == pygame.K_BACKSPACE:
                act = 'CLEAR'
        elif evt.type == pygame.KEYUP:
            if evt.key == pygame.K_SPACE:
                pedal = False
            if evt.key in bind:
                held.discard(bind[evt.key])
        elif evt.type == pygame.MOUSEBUTTONDOWN:
            if evt.button == 1:
                for name, rect in btns.items():
                    if rect.collidepoint(evt.pos):
                        act=name
                        break

        if act in ('REC','STOP','PLAY','CLEAR',):
            msg = ''

        if act == 'REC' and not rec:
            song.clear()
            rec_prev.clear()
            phold.clear()
            playing = False
            hush()
            rec = True
            rec_at = pygame.time.get_ticks()
        elif act == 'STOP':
            stop_at = pygame.time.get_ticks()
            if rec:
                now = pygame.time.get_ticks() - rec_at
                for name in sorted(rec_prev):
                    song.append((now, 'up', name))
                rec_prev.clear()
                rec = False
            elif playing:
                playing = False
                phold.clear()
                hush(150)
            
        elif act == 'PLAY' and song and not rec:
            playing = True
            play_at = pygame.time.get_ticks()
            step = 0
            phold.clear()
            hush()
        elif act == 'CLEAR':
            song.clear()
            rec_prev.clear()
            phold.clear()
            rec = False
            playing = False
            hush()
        elif act in ('PREV', 'NEXT'):
            files = sorted(folder.glob('*.json'))
            if not files:
                msg = 'No saved songs D:'
            else:
                if act == 'PREV':
                    pick = (pick - 1) % len(files)
                else:
                    pick = (pick + 1) % len(files)
                msg = f'Selected {files[pick].stem}'
                
        elif act == 'RENAME':
            if rec or playing:
                msg = 'Stoop recording or playback first!'
            elif not files:
                msg = 'Save a song firsttt :D'
            else: 
                target = files[pick]
                typed = target.stem[:24]
                held.clear()
                edit = True
                msg='Enter your new song name!'
                pygame.key.start_text_input()
        elif act == 'SAVE':
            if playing:
                msg = 'Stooop! playback first!!'
            else:
                if rec: 
                    now = pygame.time.get_ticks() - rec_at
                    for name in sorted(rec_prev):
                        song.append((now, 'up', name))
                    rec_prev.clear()
                    rec = False
                if not song:
                    msg = 'No song to save D:'
                else:
                    try:
                        folder.mkdir(exist_ok=True)
                        num= 1
                        path= folder / f'song_{num:03}.json'
                        while path.exists():
                            num += 1
                            path = folder / f'song_{num:03}.json'
                        with path.open('w', encoding='utf-8') as f:
                            json.dump(song, f, indent=2)
                        files = sorted(folder.glob('*.json'))
                        pick = files.index(path)
                        msg = f'{path.stem} is saved!! :D'
                    except OSError:
                        msg= 'Could not save the song :('

        if act == 'LOAD':
            if rec:
                msg = 'Stooop recordingg!'
            elif not files:
                msg = 'No saved songs :]'
            else:
                try:
                    with files[pick].open('r', encoding='utf-8') as f:
                        data=json.load(f) #the goat
                    valid = (
                        isinstance(data, list)
                        and all(
                            isinstance(item, list)
                            and len(item) ==3
                            and type(item[0]) is int
                            and item[0] >= 0
                            and item[1] in ('down','up')
                            and isinstance(item[2],str)
                            and item[2] in snd for item in data
                        )
                    )
                    if not valid:
                        msg = 'Invalid file D:'
                    else:
                        song = [tuple(item) for item in data]
                        playing = False
                        phold.clear()
                        hush()
                        msg=f'{files[pick].stem} has been loaded :DD'
                except (OSError, json.JSONDecodeError):
                    msg = 'Could not load song :('

    mouse = None
    if not edit and pygame.mouse.get_pressed()[0]:
        pos = pygame.mouse.get_pos()
        for name, rect in bkeys:
            if rect.collidepoint(pos):
                mouse = name
                break
        if mouse is None:
            for name, rect in wkeys:
                if rect.collidepoint(pos):
                    mouse = name
                    break

    want=held.copy()
    if mouse is not None:
        want.add(mouse)

    if rec:
        now= pygame.time.get_ticks() - rec_at
        for name in sorted(want - rec_prev):
            song.append((now, 'down', name))
        for name in sorted(rec_prev - want):
            song.append((now, 'up', name))
        rec_prev = want.copy()

    if playing:
        now = pygame.time.get_ticks() - play_at
        while step < len(song) and song[step][0] <= now:
            tm, act, name = song[step]
            if act == 'down':
                phold.add(name)
            if act == 'up':
                phold.discard(name)
            step += 1
        want.update(phold)
        if step >= len(song) and not phold:
            playing = False

    for name in want - prev:
        if name in plays:
            plays[name].fadeout(60)
        chan = snd[name].play()
        if chan is not None:
            chan.set_volume(vol)
            plays[name] = chan
    if not pedal:
        for name in list(plays):
            if name not in want:
                plays[name].fadeout(250)
                del plays[name]
    prev = want.copy()
    scr.fill(bg)

    for name, rect in btns.items():
        x, y = rect.center
        if name == 'PLAY':
            pts = [
                (x-7, y-10),
                (x-7, y+10),
                (x+10, y)
            ]
            col = (130, 220, 165) if playing else gray
            pygame.draw.polygon(scr, col, pts)

        elif name == 'STOP':
            if pygame.time.get_ticks() - stop_at < 450:
                col = amber
            else:
                col = gray
            pygame.draw.rect(
                scr, col, (x-9, y-9, 18, 18)
            )
        elif name in ('PREV', 'NEXT'):
            if name == 'PREV':
                pts = [
                    (x+5, y-9),
                    (x-4, y),
                    (x+5, y+9)
                ]
            else:
                pts = [
                    (x-5, y-9),
                    (x+4, y),
                    (x-5, y+9)
                ]

            pygame.draw.lines(scr, gray, False, pts, 3)

        else: 
            pygame.draw.rect(scr, (70,70,80), rect, border_radius=4)
            label = bfont.render(name, True, white)
            pos = label.get_rect(center=rect.center)
            scr.blit(label, pos)
        
    if pedal:
        txt= 'PEDAL ON'
        col=(165, 47, 47)

    else:
        txt = 'PEDAL OFF'
        col = gray
    label = font.render(txt, True, col)
    scr.blit(label, (key_x, 105))
    pygame.draw.circle(scr, col, (key_x-15, 114), 7) #((x,y), r)

    bar= pygame.Rect(wid - 205, 110, 150, 14)
    fill = bar.copy()
    fill.w = int(bar.w * vol)
    pygame.draw.rect(scr, (85, 85, 95), bar, border_radius=7)
    if fill.w > 0:
        pygame.draw.rect(
            scr, (186, 0, 97), fill, border_radius=7
        )
    label = font.render(f'VOL {round(vol* 100)}%', True, white)
    scr.blit(label, (bar.x - 115, 105))

    if msg:
        txt = msg
        col = (210, 125, 45)
    elif rec:
        txt = 'Recording'
        col = (255, 100, 110)
    elif playing:
        txt = 'Playing your song!'
        col = (130, 220, 165)
    elif song: 
        txt = 'Song is readyy :D'
        col = (130, 190, 245)
    else:
        txt = 'Ready to play!'
        col = white
    label = font.render(txt, True, col)
    pos = label.get_rect(center=(wid // 2, 114))
    scr.blit(label, pos)
    
    if edit:
        field = pygame.Rect(wid // 2-210, 146, 420, 40)
        pygame.draw.rect(
            scr, (65, 65, 75), field, border_radius=7
        )
        pygame.draw.rect(
            scr, (53, 152, 15), field, 2, border_radius=7
        )
        txt = font.render(typed + '|', True, white)
        scr.blit(txt, (field.x+12, field.y+10))
        hint = smfont.render(
            'ENTER = Rename     ESC = Cancel',
            True, gray
        )
        pos = hint.get_rect(center=(wid // 2, 196))
        scr.blit(hint, pos)

    for name, rect in wkeys: 
        color = (255, 250, 135) if name in want else white
        pygame.draw.rect(scr, color, rect, border_radius=4)
        pygame.draw.rect(scr, edge, rect, 2, border_radius=4)
        label = font.render(name, True, edge)
        pos = label.get_rect(
            center=(rect.centerx, rect.bottom - 22) 
        )
        scr.blit(label, pos)
    for name, rect in bkeys:
        color = (255, 250, 135) if name in want else black
        pygame.draw.rect(scr, color, rect, border_radius=4)
        txtcol = black if color != black else white
        label = smfont.render(name, True, txtcol)
        pos = label.get_rect(
            center=(rect.centerx, rect.bottom - 18)
        )
        scr.blit(label, pos)
    pygame.display.flip()
pygame.quit()
