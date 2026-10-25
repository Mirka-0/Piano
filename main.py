import pygame
from pygame import mixer

pygame.init()
pygame.mixer.set_num_channels(50)
tfont = pygame.font.Font('extras/ExtraBlur.ttf', 40)
font = pygame.font.Font('extras/OpenDyslexic-Bold.otf', 17)
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
    pygame.display.flip()
pygame.quit()