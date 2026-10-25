import pygame
from pygame import mixer

pygame.init()
pygame.mixer.set_num_channels(50)
font = pygame.font.Font('extras/ExtraBlur.ttf', 40)
mfont = pygame.font.Font('extras/OpenDyslexic-Bold.otf', 28)
sfont = pygame.font.Font('extras/GeistPixel-Regular-VariableFont_ELSH.ttf', 16)
wid = 960
hgt = 360
scr = pygame.display.set_mode([wid, hgt])
pygame.display.set_caption('PIANO')
bg = (35,35,40)
fps=60
clk = pygame.time.Clock()

run = True
while run:
    clk.tick(fps)
    
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            run = False
    scr.fill(bg)
    pygame.display.flip()
pygame.quit()