import os
import math
import random
import pygame
import sqlite3
from PIL import Image

from config import *
from maps import *
from animation import *
from unit import *
from runestone import *

pygame.init()
sc = pygame.display.set_mode(FULL_WINDOW, pygame.SCALED)
clock = pygame.time.Clock()

font30 = pygame.font.SysFont('calibri', 30)
font36 = pygame.font.SysFont('calibri', 36)

Item.init()
runa = Runa()
gui = GUI()
dialogs = Dialogs()
level = Level(0, runa, gui, dialogs).load()



animations = []
game_mode = ''


# TODO: меню инвентаря, руны, кузницы, синтезатора предметов и юнитов, переключение между ними по вкладкам сверху
#  в главном меню отображаются сегменты всей руны в уменьшенном масштабе, менять при изменении руны
def change_mode(mode, option=0):
    global animations
    global game_mode
    global level
    if game_mode == 'runestone':
        runa.save()

    if mode == 'mainmenu':
        animations = [Animation('name.png', NAME_POS, speed=1/54, start=random.randrange(6), scale=NAME_SIZES, duration=-1),
                      Animation('main.png', MAIN_GUI, speed=1/60, duration=-1, rotate=MAIN_CIRCLE_RSPEED, changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2, MAIN_CIRCLE[1]-o.get_height()//2), folder='textures\\GUI', single=True),
                      Animation('fire.png', MAIN_GUI, speed=1/60, duration=-1, scale=(0, 170), changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+MAIN_CIRCLE[2]*math.cos(i*MAIN_ELEMENTS_RSPEED-2*math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+MAIN_CIRCLE[2]*math.sin(i*MAIN_ELEMENTS_RSPEED-2*math.pi/3)), folder='textures\\GUI', single=True),
                      Animation('dark.png', MAIN_GUI, speed=1/60, duration=-1, scale=(0, 130), changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+MAIN_CIRCLE[2]*math.cos(i*MAIN_ELEMENTS_RSPEED-math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+MAIN_CIRCLE[2]*math.sin(i*MAIN_ELEMENTS_RSPEED-math.pi/3)), folder='textures\\GUI', single=True),
                      Animation('earth.png', MAIN_GUI, speed=1/60, duration=-1, scale=(0, 180), changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+MAIN_CIRCLE[2]*math.cos(i*MAIN_ELEMENTS_RSPEED), MAIN_CIRCLE[1]-o.get_height()//2+MAIN_CIRCLE[2]*math.sin(i*MAIN_ELEMENTS_RSPEED)), folder='textures\\GUI', single=True),
                      Animation('water.png', MAIN_GUI, speed=1/60, duration=-1, scale=(0, 130), changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+MAIN_CIRCLE[2]*math.cos(i*MAIN_ELEMENTS_RSPEED+math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+MAIN_CIRCLE[2]*math.sin(i*MAIN_ELEMENTS_RSPEED+math.pi/3)), folder='textures\\GUI', single=True),
                      Animation('light.png', MAIN_GUI, speed=1/60, duration=-1, scale=(0, 190), changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+MAIN_CIRCLE[2]*math.cos(i*MAIN_ELEMENTS_RSPEED+2*math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+MAIN_CIRCLE[2]*math.sin(i*MAIN_ELEMENTS_RSPEED+2*math.pi/3)), folder='textures\\GUI', single=True),
                      Animation('air.png', MAIN_GUI, speed=1/60, duration=-1, scale=(180, 0), changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+MAIN_CIRCLE[2]*math.cos(i*MAIN_ELEMENTS_RSPEED+math.pi), MAIN_CIRCLE[1]-o.get_height()//2+MAIN_CIRCLE[2]*math.sin(i*MAIN_ELEMENTS_RSPEED+math.pi)), folder='textures\\GUI', single=True),
                      Animation('button_play.png', MAIN_GUI, speed=1/60, duration=-1, changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+BUTTON_PLAY_CIRCLE[0]*math.cos(i*MAIN_ELEMENTS_RSPEED-2*math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+BUTTON_PLAY_CIRCLE[0]*math.sin(i*MAIN_ELEMENTS_RSPEED-2*math.pi/3)), button={'prs_name': 'button_play_pressed.png', 'folder': 'textures\\GUI', 'change_mode': 'ingame', 'particles': [Particles('sparkle', changexy=lambda o,x,y,i: (x-15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(-20, 0, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2)), Particles('sparkle', changexy=lambda o,x,y,i: (x+15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(0, 20, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2))]}, folder='textures\\GUI', single=True),
                      Animation('button_inventory.png', MAIN_GUI, speed=1/60, duration=-1, changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+BUTTON_PLAY_CIRCLE[0]*math.cos(i*MAIN_ELEMENTS_RSPEED-1*math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+BUTTON_PLAY_CIRCLE[0]*math.sin(i*MAIN_ELEMENTS_RSPEED-1*math.pi/3)), button={'prs_name': 'button_inventory_pressed.png', 'folder': 'textures\\GUI', 'change_mode': 'inventory', 'particles': [Particles('sparkle', changexy=lambda o,x,y,i: (x-15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(-20, 0, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2)), Particles('sparkle', changexy=lambda o,x,y,i: (x+15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(0, 20, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2))]}, folder='textures\\GUI', single=True),
                      Animation('button_rune.png', MAIN_GUI, speed=1/60, duration=-1, changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+BUTTON_PLAY_CIRCLE[0]*math.cos(i*MAIN_ELEMENTS_RSPEED), MAIN_CIRCLE[1]-o.get_height()//2+BUTTON_PLAY_CIRCLE[0]*math.sin(i*MAIN_ELEMENTS_RSPEED)), button={'prs_name': 'button_rune_pressed.png', 'folder': 'textures\\GUI', 'change_mode': 'runestone', 'particles': [Particles('sparkle', changexy=lambda o,x,y,i: (x-15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(-20, 0, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2)), Particles('sparkle', changexy=lambda o,x,y,i: (x+15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(0, 20, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2))]}, folder='textures\\GUI', single=True),
                      Animation('button_smith.png', MAIN_GUI, speed=1/60, duration=-1, changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+BUTTON_PLAY_CIRCLE[0]*math.cos(i*MAIN_ELEMENTS_RSPEED+1*math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+BUTTON_PLAY_CIRCLE[0]*math.sin(i*MAIN_ELEMENTS_RSPEED+1*math.pi/3)), button={'prs_name': 'button_smith_pressed.png', 'folder': 'textures\\GUI', 'change_mode': 'smith', 'particles': [Particles('sparkle', changexy=lambda o,x,y,i: (x-15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(-20, 0, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2)), Particles('sparkle', changexy=lambda o,x,y,i: (x+15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(0, 20, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2))]}, folder='textures\\GUI', single=True),
                      ]
    if mode == 'ingame':
        animations = []
        level = Level(option, runa, gui, dialogs).load()
        level.make_scale(0.81)
        level.play()
    if mode == 'levelmap':
        animations = [Animation('button_inventory.png', MAIN_GUI, speed=1/60, duration=-1, changexy=lambda o,x,y,i: (MAIN_CIRCLE[0]-o.get_width()//2+BUTTON_PLAY_CIRCLE[0]*math.cos(i*MAIN_ELEMENTS_RSPEED-2*math.pi/3), MAIN_CIRCLE[1]-o.get_height()//2+BUTTON_PLAY_CIRCLE[0]*math.sin(i*MAIN_ELEMENTS_RSPEED-2*math.pi/3)), button={'prs_name': 'button_inventory_pressed.png', 'folder': 'textures\\GUI', 'change_mode': 'ingame', 'changelevel': 1001001, 'particles': [Particles('sparkle', changexy=lambda o,x,y,i: (x-15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(-20, 0, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2)), Particles('sparkle', changexy=lambda o,x,y,i: (x+15/(i+1), y-i//2), pos='mouse_attach', spawn=0.3, random_offset=(0, 20, -20, 20), random_scale=(0.6, 1.2), random_rotate=(0, 180), random_speed=(0.6, 1.2))]}, folder='textures\\GUI', single=True)]
    if mode == 'inventory':
        animations = []
    if mode == 'runestone':
        animations = []
    if mode == 'smith':
        animations = []
    game_mode = mode


change_mode('mainmenu')
# change_mode('ingame')


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
                if game_mode == 'ingame':
                    change_mode('levelmap')
                elif game_mode == 'levelmap':
                    change_mode('mainmenu')
                elif game_mode == 'inventory':
                    change_mode('mainmenu')
                elif game_mode == 'runestone':
                    change_mode('mainmenu')
                elif game_mode == 'smith':
                    change_mode('mainmenu')
                elif game_mode == 'mainmenu':
                    exit()
            if game_mode == 'ingame':
                if level.selected_unit:
                    if event.key == pygame.K_SPACE:
                        level.selected_unit.jump()
                    if event.key == pygame.K_q:
                        level.selected_unit.cast(1)
                    if event.key == pygame.K_w:
                        level.selected_unit.cast(2)
                    if event.key == pygame.K_e:
                        level.selected_unit.cast(3)
                    if event.key == pygame.K_r:
                        level.selected_unit.cast(4)
                    if event.key == pygame.K_z:
                        select_prev_unit(level, pos)
                    if event.key == pygame.K_c:
                        select_next_unit(level, pos)
                if not level.selected_unit and level.units:
                    if event.key == pygame.K_z or event.key == pygame.K_c:
                        level.selected_unit = level.units[0]
                        level.selected_skill = None
                        level.selected_item = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_mode == 'ingame':  # TODO: сделать два варианта: игровой и отлодочный, буфер масштабов в словарь
                if event.button == 5:
                    if level.camera_scale > 0.2:
                        level.camera_scale *= 0.9
                        level.make_scale()
                elif event.button == 4:
                    if level.camera_scale < 5:
                        level.camera_scale /= 0.9
                        level.make_scale()
                else:
                    gui.fetch_click(event.button, pos)
            elif game_mode == 'runestone':
                if event.button == 1:
                    runa.hold_piece(pos)

        if event.type == pygame.MOUSEBUTTONUP:
            if game_mode == 'runestone':
                if runa.piece_lock and event.button == 1:
                    runa.place_piece(pos)

    if game_mode == 'mainmenu':
        level.paint_bckgr(sc)

    if game_mode == 'runestone':
        level.paint_bckgr(sc)
        level.runa.paint_runestone(sc, pos)

    if game_mode == 'ingame':
        if level.selected_unit:
            if keys[pygame.K_a]:
                level.selected_unit.moveleft()
            if keys[pygame.K_d]:
                level.selected_unit.moveright()
            if keys[pygame.K_SPACE]:
                level.selected_unit.flyup()
            if keys[pygame.K_s]:
                level.selected_unit.flydown()
            if pressed[0]:
                level.selected_unit.attack()
        level.move_camera(pos)
        level.tick()
        for idx,u in enumerate(level.units):
            u.tick(sc, pos)
        level.paint(sc, (), ())
        sc.blit(font30.render(str(int(clock.get_fps())), True, (0, 0, 0)), (1850, 10))
        sc.blit(font30.render(str(level.camera_scale), True, (0, 0, 0)), (1750, 10))

    runa.tick()

    animations_trash = []
    for i,a in enumerate(animations):
        kw = {'pos': pos, 'pressed': pressed} if a.button else {}
        anim = a.animate(sc, **kw)
        if anim is False:
            animations_trash.append(a)
        elif anim:
            for k,v in anim.items():
                if k == 'change_mode':
                    change_mode(v['mode'], v['changelevel'])
    animations[:] = [a for a in animations if a not in animations_trash]

    pygame.display.flip()
    clock.tick(FPS)
