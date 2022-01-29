import os
import math
import random
import pygame
import sqlite3
from PIL import Image

from config import *
from maps import *


pygame.init()
sc = pygame.display.set_mode(FULL_WINDOW)
clock = pygame.time.Clock()

font30 = pygame.font.SysFont('calibri', 30)
font36 = pygame.font.SysFont('calibri', 36)

runa = Runa()
gui = GUI()
dialogs = Dialogs()
level = Level(1001001, runa, gui, dialogs, editor=True).load()

cur_block_id = 1

while True:
    sc.fill(pygame.Color('white'))
    pos = pygame.mouse.get_pos()
    pressed = pygame.mouse.get_pressed()
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 5:
                if level.camera_scale > 0.2:
                    level.camera_scale *= 0.9
                    level.tile_size = int(TILE_SIZE * level.camera_scale)
                    level.chunk_size_px = level.tile_size * level.chunk_size
                    chunksize = int(level.nsc[0][0].get_width() * level.camera_scale)
                    level.sc = [[pygame.transform.scale(j, (chunksize, chunksize)) for j in i] for i in level.nsc]
            elif event.button == 4:
                if level.camera_scale < 5:
                    level.camera_scale /= 0.9
                    level.tile_size = int(TILE_SIZE * level.camera_scale)
                    level.chunk_size_px = level.tile_size * level.chunk_size
                    chunksize = int(level.nsc[0][0].get_width() * level.camera_scale)
                    level.sc = [[pygame.transform.scale(j, (chunksize, chunksize)) for j in i] for i in level.nsc]

    bcords = int((pos[0] - level.mp[0]) / level.tile_size), int((pos[1] - level.mp[1]) / level.tile_size)
    if pressed[0] or pressed[2]:
        if 0 <= bcords[0] < level.size.y and 0 <= bcords[1] < level.size.x:
            level.tilemap[bcords[0]][bcords[1]] = cur_block_id if pressed[0] else 0
            level.update_chunk(bcords)

    level.move_camera(pos)
    level.tick()
    level.paint(sc, (), ())
    sc.blit(font30.render(str(bcords), True, (0, 0, 0)), (1680, 10))
    sc.blit(font30.render(str(int(clock.get_fps())), True, (0, 0, 0)), (1850, 10))
    pygame.display.flip()
    clock.tick(FPS)