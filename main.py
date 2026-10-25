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

run = True
while run:
    clk.tick(fps)
    
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            run = False
    scr.fill(bg)
    
    for i in range(14):
        x = key_x + i*key_w
        y=key_y
        rect = pygame.Rect(x,y, key_w, key_h)
        pygame.draw.rect(scr, white, rect, border_radius=4)
        pygame.draw.rect(scr, edge,rect, 2, border_radius=4)

        note = notes[i%7]
        octv = octs[i//7]
        name= f'{note}{octv}'
        label = font.render(name, True, edge)
        pos = label.get_rect(center=(rect.centerx, rect.bottom - 22))
        scr.blit(label, pos)

        for o, octv in enumerate(octs):
            for i, spot in enumerate(spots):
                x = key_x+(o*7 +spot+1)* key_w
                x -= blk_w // 2
                rect = pygame.Rect(x, key_y, blk_w, blk_h)
                pygame.draw.rect(scr, black, rect, border_radius=4)
                name = f'{sharp[i]}{octv}'
                label = smfont.render(name, True, white)
                pos = label.get_rect(
                    center=(rect.centerx, rect.bottom - 18)
                )
                scr.blit(label, pos)
    pygame.display.flip()
pygame.quit()