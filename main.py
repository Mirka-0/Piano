import pygame
from pygame import mixer

pygame.init()
pygame.mixer.set_num_channels(50)
tfont = pygame.font.Font('extras/OpenDyslexic-Bold.otf', 40)
font = pygame.font.SysFont('Arial', 17)
wid = 960
hgt = 360
scr = pygame.display.set_mode([wid, hgt])
pygame.display.set_caption('PIANO')
bg = (35,35,40)
fps=60
clk = pygame.time.Clock()
notes = ['C','D','E','F','G','A','B']
octs = [4,5]
key_w=58
key_h=225
key_x=(wid - 14 *key_w) //2
key_y = 100
white = (250,250,248)
edge = (60,60,65)
blk_w=36
blk_h=135
black = (25, 25, 30)
sharp = ['C#','D#','F#','G#','A#']
spots = [0,1,3,4,5]
smfont = pygame.font.SysFont('Arial', 12)
wkeys = []
bkeys = []

for i in range(14):
    x = key_x+i * key_w
    rect = pygame.Rect(x, key_y, key_w, key_h)
    note = notes[i % 7]
    octv= octs[i//7]
    name = f'{note}{octv}'
    wkeys.append((name, rect)) #now bob knows where the white keys are!

for o, octv in enumerate(octs):
    for i, spot in enumerate(spots):
        x = key_x + (o*7+spot+1)* key_w
        x -= blk_w // 2
        rect = pygame.Rect(x, key_y, blk_w, blk_h)
        name = f'{sharp[i]}{octv}'
        bkeys.append((name, rect)) #now the 24 keys have their own rectangles
run = True
while run:
    clk.tick(fps)
    
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            run = False
    mouse = None
    if pygame.mouse.get_pressed()[0]:
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
    scr.fill(bg)

    for name, rect in wkeys: 
        color = (185,218,245) if name == mouse else white
        pygame.draw.rect(scr, color, rect, border_radius=4)
        pygame.draw.rect(scr, edge, rect, 2, border_radius=4)
        label = font.render(name, True, edge)
        pos = label.get_rect(
            center=(rect.centerx, rect.bottom - 22)
        )
        scr.blit(label, pos)
    for name, rect in bkeys:
        color = (75, 113, 162) if name == mouse else black
        pygame.draw.rect(scr, color, rect, border_radius=4)
        label = smfont.render(name, True, white)
        pos = label.get_rect(
            center=(rect.centerx, rect.bottom - 18)
        )
        scr.blit(label, pos)
    pygame.display.flip()
pygame.quit()
