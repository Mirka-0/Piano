import pygame
import justpi
from pygame import mixer

pygame.init()
pygame.mixer.set_num_channels(50)
font = pygame.font.Font('extras/ExtraBlur.ttf', 40)
mfont = pygame.font.Font('extras/OpenDyslexic-Bold.otf', 28)
sfont = pygame.font.Font('extras/GeistPixel-Regular-VariableFont_ELSH.ttf', 16)
smollfont = pygame.font.Font('extras/augiepixel.ttf', 10)
fps=60
timer = pygame.time.Clock()
width = 52*35
height = 400
scr = pygame.display.set_mode([width, height])
pygame.display.set_caption('PIANO')
run=True
while run:
    timer.tick(fps)
    scr.fill('gray')
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    pygame.display.flip()
pygame.quit()