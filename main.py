import pygame
from pygame import mixer
from pathlib import Path
import json
import numpy as np
import sounddevice as sd
from queue import Queue, Full, Empty
import math

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(50)
pygame.mixer.set_reserved(1)

tfont = pygame.font.Font('extras/OpenDyslexic-Bold.otf', 40)
tabft = pygame.font.Font('extras/OpenDyslexic-Bold.otf', 13)
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
key_h=260
key_x=(wid - 14 *key_w) //2
key_y = 250

bg = (35,35,40)
white = (250,250,248)
edge = (46,46,46)
gray = (180, 180, 185)
amber = (221, 148, 22)
red = (214, 30, 30)
green = (124, 169, 0)

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
    'PREV': pygame.Rect(276, 149, 34, 32),
    'NEXT': pygame.Rect(322, 149, 34, 32),
    'RENAME': pygame.Rect(368, 149, 105, 32),
    'REC': pygame.Rect(485, 149, 74, 32),
    'STOP': pygame.Rect(571, 149, 42, 32),
    'PLAY': pygame.Rect(625, 149, 42, 32),
    'CLEAR': pygame.Rect(679, 149, 74, 32),
    'SAVE': pygame.Rect(765, 149, 74, 32),
    'LOAD': pygame.Rect(851, 149, 74, 32)
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
    x=20 + i * 145
    rect = pygame.Rect(x, 18, 135, 38)
    tabrs[name]= rect
bpm = 100
m_on = False
beat = 0
bmin = 15
bmax = 400
bdrag = False
bbar = pygame.Rect( wid // 2 - 220, 366, 440, 14)

m_at = 0
tpb = 4
accent = True
units = ['Redonda','Blanca','Negra','Corchea', 'Semicorchea', 'Fusa', 'Semifusa']
uvals = (4, 2, 1, 1/2, 1/4, 1/8, 1/16)
unit = 2
subvals = (1, 2, 3, 4)
subtxt = ('OFF', 'Corcheas', 'Tresillos', 'Semicorcheas')
sidx =0
sub = 0
ufiles = {
    'Redonda': 'redonda.png',
    'Blanca': 'blanca.png',
    'Negra': 'negra.png',
    'Corchea': 'corchea.png',
    'Semicorchea': 'semicorchea.png',
    'Fusa': 'fusa.png',
    'Semifusa': 'semifusa.png'
}
rfiles = [
    'negra.png',
    'corchea_2.png',
    'tresillo_corchea.png',
    'semicorchea_2.png'
]
def getimg(file):
    if file is None:
        return None
    path = root / 'extras' / file
    if not path.exists():
        return None
    img = pygame.image.load(str(path)).convert_alpha()
    size=39
    w, h= img.get_size()
    scale=min((size-2)/ w, (size-2)/h)
    w= max(1, round(w*scale))
    h= max(1,round(h*scale))
    img = pygame.transform.smoothscale(img, (w, h))
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    pos = img.get_rect(center=(size//2, size // 2))
    canvas.blit(img, pos)
    return canvas
uimg = {name: getimg(file) for name, file in ufiles.items()}
rimg = [getimg(file) for file in rfiles]
m_bt = {
    'GO': pygame.Rect(525, 404, 150, 42),
    'SUB': pygame.Rect(265, 466, 120, 56),
    'BAR': pygame.Rect(410, 473, 180, 42),
    'ACC': pygame.Rect(610, 473, 180, 42),
    'UNIT': pygame.Rect(835, 456, 90, 56)
}
def dtab():
    for name, rect in tabrs.items():
        if name == tab:
            col = (0, 159, 150)
        else:
            col = (70, 70, 80)
        pygame.draw.rect(scr, col, rect, border_radius=7)
        label = tabft.render(name, True, white)
        pos = label.get_rect(center=rect.center)
        scr.blit(label, pos)
sel_at = -3000
msg_at = 0
oldmsg =''

m_tick = mixer.Sound(str(root / 'audio' / 'nrm.wav'))
m_acc = mixer.Sound(str(root / 'audio' / 'accent.wav'))
m_ch = mixer.Channel(0)
m_ch.set_volume(0.65)

def tname(bpm):
    if bpm < 24:
        return 'Larghissimo'
    if bpm < 40:
        return 'Grave'
    if bpm < 60:
        return 'Largo'
    if bpm < 66:
        return 'Larghetto'
    if bpm < 76:
        return 'Adagio'
    if bpm < 108:
            return 'Andante'
    if bpm < 120:
            return 'Moderato'
    if bpm < 124:
            return 'Allegretto'
    if bpm < 156:
            return 'Allegro'
    if bpm < 176:
            return 'Vivace'
    if bpm < 200:
            return 'Presto'
    return 'Prestissimo'
abc = ['C', 'C#','D', 'D#', 'E', 'F',
       'F#', 'G', 'G#', 'A', 'A#', 'B']
sol = ['Do', 'Do#','Re', 'Re#', 'Mi', 'Fa',
       'Fa#', 'Sol', 'Sol#', 'La', 'La#' 'Si']
ref = 440
style = 0
freq = 0.0
micon = False
micmsg = ''
tbtn = {'DOWN': pygame.Rect(400, 430, 90, 43), 'UP': pygame.Rect(505, 430, 90, 43), 'NAMES': pygame.Rect(615, 430, 200, 43)}
mic = None
micq = Queue(maxsize=4)
level = 0.0
rate =0
errtxt = ''
micbt = pygame.Rect(510, 390, 180, 48)    
def mic_cb(data, frames, tm, stat):
    try:
        micq.put_nowait(data[:, 0].copy())
    except Full:
        pass
def endmic():
    global mic, level
    if mic is not None:
        mic.stop()
        mic.close()
        mic = None
    level = 0.0
    while True:
        try:
            micq.get_nowait()
        except Empty:
            break
def gentnt(hz, ref, style):
    if hz <= 0:
        return '-', 0.8
    midi= round(69+12*math.log2(hz/ref))
    if midi < 0 or midi >127:
        return 'OUT', 0.0
    names = abc if style == 0 else sol
    note = names[midi%12]
    octv=midi // 12-1
    name = f'{note}{octv}'
    ideal = ref*2**((midi-69)/12)
    cents = 1200*math.log2(hz/ideal)
    return name, cents
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
        if tab != 'PIANO':
            if evt.type in (pygame.KEYDOWN, pygame.KEYUP):
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
                for name, rect in tabrs.items():
                    if rect.collidepoint(evt.pos):
                        if rec:
                            msg = 'Stooop reconding first!!'
                        elif tab != name:
                            m_on = False
                            beat = 0
                            tab = name
                            m_ch.stop()
                            playing = False
                            pedal = False
                            held.clear()
                            phold.clear()
                            hush()
                            msg = ''
                        break
                if tab == 'PIANO':
                    for name, rect in btns.items():
                        if rect.collidepoint(evt.pos):
                            act = name
                            break
                elif tab == 'METRONOME':
                    if bbar.inflate(28, 28).collidepoint(evt.pos):
                        bdrag = True
                    for name, rect in m_bt.items():
                        col = (70, 70, 80)
                        if rect.collidepoint(evt.pos):
                            if name == 'MINUS':
                                bpm = max(40, bpm - 5)
                                if m_on:
                                    m_at = pygame.time.get_ticks() + 60000 / bpm
                            elif name == 'PLUS':
                                bpm = min(240, bpm + 5)
                                if m_on:
                                    m_at = pygame.time.get_ticks() + 60000 / bpm
                            elif name == 'GO':
                                m_on = not m_on
                                beat = 0
                                sub = 0
                                m_at = pygame.time.get_ticks()
                                if not m_on:
                                    m_ch.stop()
                            elif name == 'BAR':
                                vals = (2, 3, 4, 6)
                                idx= vals.index(tpb)
                                tpb= vals[(idx+1)% len(vals)]
                                beat = 0
                                sub = 0
                                if m_on:
                                    m_at = pygame.time.get_ticks()
                            elif name == 'ACC':
                                accent = not accent
                            elif name == 'UNIT':
                                unit = (unit+1) % len(units)
                                beat = 0
                                sub = 0
                                if m_on:
                                    m_at = pygame.time.get_ticks()
                            elif name == 'SUB':
                                sidx = (sidx+1) % len(subvals)
                                sub = 0
                                beat = 0
                                if m_on:
                                    m_at = pygame.time.get_ticks()
                            break
                elif tab == 'TUNER':
                    for name, rect in tbtn.items():
                        if rect.collidepoint(evt, pos):
                            if name == 'DOWN':
                                ref = max(415, ref-1)
                            elif name == 'UP':
                                ref = min(466, ref+1)
                            elif name == 'NAMES':
                                style = 1-style
                            break
                    if micbt.collidepoint(evt.pos):
                        if mic is None:
                            try:
                                info = sd.query_devices(kind='input')
                                rate = int(info['default_samplerate'])
                                mic = sd.InputStream(samplerate=rate, channels=1, blocksize=2048, callback=mic_cb)
                                mic.start()
                                errtxt= ''
                            except (sd.PortAudioError, ValueError, OSError) as err:
                                errtxt = f'Mic error D: {str(err)[:55]}'
                                endmic()
                        else:
                            endmic()
                        
        elif evt.type == pygame.MOUSEBUTTONUP:
            if evt.button == 1:
                bdrag = False
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
                msg = ''
                sel_at = pygame.time.get_ticks()
                
        elif act == 'RENAME':
            if rec or playing:
                msg = 'Stoop recording or playback first!'
            elif not files:
                msg = 'Save a song firsttt :D'
            else: 
                target = files[pick]
                typed = target.stem[:24]
                held.clear()
                pedal = False
                hush()
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
            files = sorted(folder.glob('*.json'))
            if files:
                pick %= len(files)
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
    if bdrag and tab == 'METRONOME':
        mx = pygame.mouse.get_pos()[0]
        rate = (mx-bbar.x)/ bbar.w
        rate = max(0, min(1, rate))
        new = round(bmin + rate *(bmax-bmin))
        if new != bpm:
            bpm =new
            if m_on:
                count = subvals[sidx]
                gap = 60000 * uvals[unit] / (bpm*count)
                m_at = pygame.time.get_ticks() + gap
    now = pygame.time.get_ticks()
    if tab == 'METRONOME' and m_on:
        if now >= m_at:
            count = subvals[sidx]
            if sub == 0:
                beat = beat%tpb+1
                if beat == 1 and accent:
                    m_ch.play(m_acc)
                    m_ch.set_volume(0.8)
                else:
                    m_ch.play(m_tick)
                    m_ch.set_volume(0.65)
            else:
                m_ch.play(m_tick)
                m_ch.set_volume(0.25)
            sub =(sub+1)% count
            gap = 60000 * uvals[unit]/ (bpm * count)
            m_at += gap
            if m_at < now:
                m_at = now + gap
    if msg != oldmsg:
        msg_at = now
        oldmsg = msg

    if msg and now - msg_at > 2500:
        msg = ''
        oldmsg = ''

    mouse = None
    if tab != 'PIANO':
        scr.fill(bg)
        dtab()
        if tab == 'METRONOME':
            txt = tfont.render(str(bpm), True, white)
            scr.blit(txt, txt.get_rect(center=(wid//2, 190)))
            txt = font.render(tname(bpm), True, gray)
            scr.blit(txt, txt.get_rect(center=(wid//2, 235)))
            img = uimg[units[unit]]
            if img is not None:
                scr.blit(img, img.get_rect(center=(wid // 2, 135)))
            gap = 72
            start = wid // 2 - (tpb - 1) * gap // 2
            for i in range(tpb):
                x = start + i * gap
                y= 280
                if m_on and beat== i +1:
                    col =(246, 197, 3)
                else:
                    col = (70, 70, 80)
                pygame.draw.circle(scr, col, (x, y), 27)
                num = font.render(str(i+1), True, white)
                pos = num.get_rect(center=(x,y))
                scr.blit(num, pos)
            rate = (bpm - bmin) / (bmax-bmin)
            pygame.draw.rect(scr, (75, 75, 85), bbar, border_radius=7)
            fill = bbar.copy()
            fill.w = round(bbar.w * rate)
            if fill.w > 0:
                pygame.draw.rect(scr, (0, 80, 124), fill, border_radius=7)
            hx= round(bbar.x + bbar.w*rate)
            hand= pygame.Rect(hx -13, bbar.centery - 14, 26, 28)
            pygame.draw.rect(scr, (131, 182, 233), hand, border_radius=10)
            lo = smfont.render(str(bmin), True, gray)
            hi = smfont.render(str(bmax), True, gray)
            scr.blit(lo, lo.get_rect(midright=(bbar.x - 12, bbar.centery)))
            scr.blit( hi, hi.get_rect(midleft=(bbar.right + 12, bbar.centery)))
            for name, rect in m_bt.items():
                col = (70, 70, 80)
                if name == 'GO':
                    txt = 'PAUSE' if m_on else 'START'
                    if m_on:
                        col = (186, 0, 97)
                elif name == 'BAR':
                    txt = f'{tpb} BEATS/BAR'
                elif name == 'ACC':
                    txt = 'ACCENT IS ON!' if accent else 'ACCENT OFF!'
                    if accent:
                        col = (124, 169, 0)
                elif name == 'UNIT':
                    txt = units[unit].upper()
                elif name == 'SUB':
                    txt = 'RHYTHM' if sidx else 'NO RHYTHM D:'
                pygame.draw.rect(scr, col, rect, border_radius=7)
                if name == 'SUB':
                    label = bfont.render('RHYTHM', True, white)
                    pos=label.get_rect(midleft=(rect.x + 10, rect.centery))
                    scr.blit(label, pos)
                    img = rimg[sidx]
                    if img is not None:
                        scr.blit(img, img.get_rect(center=(rect.right - 24, rect.centery)))
                elif name == 'UNIT':
                    img = uimg[units[unit]]
                    if img is not None:
                        pos = img.get_rect(center=rect.center)
                        scr.blit(img, pos)
                    else:
                        label = bfont.render('D:', True, white)
                        pos = label.get_rect(center=rect.center)
                        scr.blit(label, pos)
                else:
                    label = bfont.render(txt, True, white)
                    pos = label.get_rect(center=rect.center)
                    scr.blit(label, pos)
        elif tab == 'TUNER':
            title = tfont.render('TUNER', True, white)
            pos = label.get_rect(center=(wid // 2, 105))
            scr.blit(title, pos)
            if freq > 0:
                name, cents = gentnt(freq, ref, style)
                if abs(cents) <= 5:
                    info = 'IN TUNEE :D'
                    col = green
                elif cents < 0:
                    info = 'TOO FLAT D:'
                    col = amber
                else:
                    info = 'TOO SHARP'
                    col = red
                hz = f'{freq:.1f} Hz'
                info += f' ({cents:+.1f} cents)'
            else:
                name = '--'
                cents = 0
                hz = 'No pitch detected :('
                info = micmsg if micmsg else 'Microphone is OFF'
                col = gray
            txt = tfont.render(name, True, white)
            scr.blit(txt, txt.get_rect(center=(wid//2, 200)))
            txt = font.render(hz, True, gray)
            scr.blit(txt, txt.get_rect(center=(wid//2, 250)))
            txt = font.render(info, True, col)
            scr.blit(txt, txt.get_rect(center=(wid//2, 290)))
            meter = pygame.Rect(360, 330, 480, 12)
            pygame.draw.rect(scr, (70, 70, 80), meter, border_radius=6)
            zone = pygame.Rect(meter.centerx - 24, meter.y, 48, 12)
            pygame.draw.rect(scr, green, zone, border_radius=4)
            if freq > 0:
                val =max(-50, min(50, cents))
                x = meter.centerx + int(val * meter.w/100)
                pygame.draw.circle(scr, (255, 214, 0), (x, meter.centery), 11)
            txt = smfont.render('FLAT', True, gray)
            scr.blit(txt, (meter.x, 352))
            txt = smfont.render('SHARP', True, gray)
            scr.blit(txt, (meter.right - 35, 352))

            txt = font.render(f'A4 = {ref} Hz', True, white)
            pos = txt.get_rect(center=(wid//2, 390))
            scr.blit(txt, pos)
        pygame.display.flip()
        continue

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
    dtab()

    for name, rect in btns.items():
        if edit:
            continue
        x, y = rect.center
        if name == 'PLAY':
            pts = [
                (x-7, y-10),
                (x-7, y+10),
                (x+10, y)
            ]
            col = green if playing else gray
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
            col = red if name == 'REC' and rec else (70,70,80)
            pygame.draw.rect(scr, col, rect, border_radius=4)
            label = bfont.render(name, True, white)
            pos = label.get_rect(center=rect.center)
            scr.blit(label, pos)
        
    if pedal:
        txt= 'PEDAL ON'
        col=(214, 30, 30)

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
        col = amber
    elif rec:
        txt = 'Recording'
        col = red
    elif playing:
        txt = 'Playing your song!'
        col = green
    elif files and pygame.time.get_ticks() - sel_at < 3000:
        txt = f'Song is {files[pick].stem}'
        col = (130, 190, 245)
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
            scr, gray, field, 2, border_radius=7
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
        color = (255, 214, 0) if name in want else white
        pygame.draw.rect(scr, color, rect, border_radius=4)
        pygame.draw.rect(scr, edge, rect, 2, border_radius=4)
        label = font.render(name, True, edge)
        pos = label.get_rect(
            center=(rect.centerx, rect.bottom - 22) 
        )
        scr.blit(label, pos)
    for name, rect in bkeys:
        color = (255, 214, 0) if name in want else black
        pygame.draw.rect(scr, color, rect, border_radius=4)
        txtcol = black if color != black else white
        label = smfont.render(name, True, txtcol)
        pos = label.get_rect(
            center=(rect.centerx, rect.bottom - 18)
        )
        scr.blit(label, pos)
    pygame.display.flip()
pygame.quit()
