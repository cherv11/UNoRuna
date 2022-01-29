import os
import math
import random
import pygame
import re
import time
import numpy as np
from numba import njit
from collections import defaultdict
import string



WINDOW = 1900, 1000
FULL_WINDOW = 1920, 1080
HALF_WINDOW = tuple((i//2 for i in FULL_WINDOW))
FPS = 60

TILE_SIZE = 47
MAP_X_OFFSET = 116
MAP_Y_OFFSET = 259
MAP_SIZE_X = 36
MAP_SIZE_Y = 16
TEST_MAP_SIZE_X = 500
TEST_MAP_SIZE_Y = 250
CAMERA_SPEED = 20/TILE_SIZE
GRAVITY = 1 / FPS / 3
JUMP_SPEED = -0.11
FLYING_ACCEL_TO_SPEED = 0.1
DAMAGE_VALUE_TIME = 60
DAMAGE_VALUE_TRANSPARENT_START = 45
DAMAGE_VALUE_TRANSPARENT_TIME = DAMAGE_VALUE_TIME - DAMAGE_VALUE_TRANSPARENT_START
DAMAGE_VALUE_VSPEED = 150/FPS
DAMAGE_BAR_TIME = 180
DAMAGE_BAR_FRESH_START = 60
DAMAGE_BAR_FRESH_END = 120
DAMAGE_BAR_FRESH_TIME = DAMAGE_BAR_FRESH_END - DAMAGE_BAR_FRESH_START
DAMAGE_BAR_TRANSPARENT_TIME = 20
DAMAGE_BAR_TRANSPARENT_START = DAMAGE_BAR_TIME - DAMAGE_BAR_TRANSPARENT_TIME
UNIT_BAR_SIZE = (300, 55)


YELLOW = (255, 255, 0)
YELLANGE = (255, 192, 0)
ORANGE = (255, 128, 0)
BLUE = (0, 0, 225)
LIGHT_BLUE = (135, 208, 250)
RED = (255, 0, 0)
DARK_RED = (128, 0, 0)
GREEN = (64, 255, 64)
LIGHT_GREEN = (128, 255, 128)
BLACK = (0, 0, 0)
BROWN = (96, 38, 0)
GREY = (128, 128, 128)
GREEN_MASK = (0, 255, 29)
DMGCOLORS = {'n': (0, 0, 0), 'a': (128, 128, 128), 'w': (28, 56, 128), 'f': (224, 60, 30), 'e': (60, 224, 60), 'd': (96, 38, 220), 'l': (240, 240, 60), 'h': (118, 255, 122)}

INGAME_GUI = ((0, 60), (132, 0), (1016, 0), (516, 966))
MAIN_GUI = (175, 300)
MAIN_CIRCLE = (MAIN_GUI[0]+316, MAIN_GUI[1]+316, 316)
NAME_POS = (47, 24)
NAME_SIZES = (856, 276)
MAIN_CIRCLE_RSPEED = 22/60
MAIN_ELEMENTS_RSPEED = MAIN_CIRCLE_RSPEED*math.pi/180
BUTTON_PLAY = (322, 300)
BUTTON_PLAY_CIRCLE = (200,)

GUI_ICON_SIZE = (101, 101)
GUI_SMALL_ICON_SIZE = (50, 51)
GUI_CUR_AVATAR = (7, 172)
GUI_SKILLS = ((7, 367), (7, 476), (7, 585), (7, 694))
GUI_ITEMS = ((4, 816), (59, 816), (4, 871), (59, 871), (4, 926), (59, 926))
GUI_ALLIES = ((184, 7), (293, 7), (402, 7), (511, 7), (620, 7), (729, 7), (838, 7))
GUI_ENEMIES = ((1066, 7), (1175, 7), (1284, 7), (1393, 7), (1502, 7), (1611, 7), (1720, 7))
GUI_BAR_POSES = ((7, 282), (7, 307), (7, 332))
GUI_BAR_SIZE = (101, 22)
GUI_BAR_TRIANGLE = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (0, 12), (0, 13), (0, 14), (0, 15), (0, 16), (0, 17), (0, 18), (0, 19), (0, 20), (0, 21), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17), (1, 18), (1, 19), (1, 20), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (2, 16), (2, 17), (2, 18), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16), (3, 17), (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (7, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7), (7, 8), (7, 9), (7, 10), (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 8), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), (10, 0), (10, 1), (10, 2), (10, 3), (10, 4), (11, 0), (11, 1), (11, 2), (11, 3), (12, 0), (12, 1))
GUI_BAR_TRIANGLE_RIGHT = ((88, 21), (89, 19), (89, 20), (89, 21), (90, 18), (90, 19), (90, 20), (90, 21), (91, 16), (91, 17), (91, 18), (91, 19), (91, 20), (91, 21), (92, 14), (92, 15), (92, 16), (92, 17), (92, 18), (92, 19), (92, 20), (92, 21), (93, 12), (93, 13), (93, 14), (93, 15), (93, 16), (93, 17), (93, 18), (93, 19), (93, 20), (93, 21), (94, 11), (94, 12), (94, 13), (94, 14), (94, 15), (94, 16), (94, 17), (94, 18), (94, 19), (94, 20), (94, 21), (95, 9), (95, 10), (95, 11), (95, 12), (95, 13), (95, 14), (95, 15), (95, 16), (95, 17), (95, 18), (95, 19), (95, 20), (95, 21), (96, 7), (96, 8), (96, 9), (96, 10), (96, 11), (96, 12), (96, 13), (96, 14), (96, 15), (96, 16), (96, 17), (96, 18), (96, 19), (96, 20), (96, 21), (97, 5), (97, 6), (97, 7), (97, 8), (97, 9), (97, 10), (97, 11), (97, 12), (97, 13), (97, 14), (97, 15), (97, 16), (97, 17), (97, 18), (97, 19), (97, 20), (97, 21), (98, 4), (98, 5), (98, 6), (98, 7), (98, 8), (98, 9), (98, 10), (98, 11), (98, 12), (98, 13), (98, 14), (98, 15), (98, 16), (98, 17), (98, 18), (98, 19), (98, 20), (98, 21), (99, 2), (99, 3), (99, 4), (99, 5), (99, 6), (99, 7), (99, 8), (99, 9), (99, 10), (99, 11), (99, 12), (99, 13), (99, 14), (99, 15), (99, 16), (99, 17), (99, 18), (99, 19), (99, 20), (99, 21), (100, 0), (100, 1), (100, 2), (100, 3), (100, 4), (100, 5), (100, 6), (100, 7), (100, 8), (100, 9), (100, 10), (100, 11), (100, 12), (100, 13), (100, 14), (100, 15), (100, 16), (100, 17), (100, 18), (100, 19), (100, 20), (100, 21))
GUI_BAR_RECTANGLE_OFFSET = 13

GUI_MBARS_ALLIES = ((187, 117), (187, 131), (187, 145)), ((296, 117), (296, 131), (296, 145)), ((405, 117), (405, 131), (405, 145)), ((514, 117), (514, 131), (514, 145)), ((623, 117), (623, 131), (623, 145)), ((732, 117), (732, 131), (732, 145)), ((841, 117), (841, 131), (841, 145))
GUI_MBARS_ENEMIES = ((1069, 117), (1069, 131), (1069, 145)), ((1178, 117), (1178, 131), (1178, 145)), ((1287, 117), (1287, 131), (1287, 145)), ((1396, 117), (1396, 131), (1396, 145)), ((1505, 117), (1505, 131), (1505, 145)), ((1614, 117), (1614, 131), (1614, 145)), ((1723, 117), (1723, 131), (1723, 145))
GUI_MBAR_SIZE = (95, 11)
GUI_MBAR_TRIANGLE = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3), (4, 0), (4, 1))
GUI_MBAR_TRIANGLE_RIGHT = ((89, 9), (89, 10), (90, 7), (90, 8), (90, 9), (90, 10), (91, 5), (91, 6), (91, 7), (91, 8), (91, 9), (91, 10), (92, 4), (92, 5), (92, 6), (92, 7), (92, 8), (92, 9), (92, 10), (93, 2), (93, 3), (93, 4), (93, 5), (93, 6), (93, 7), (93, 8), (93, 9), (93, 10), (94, 1), (94, 2), (94, 3), (94, 4), (94, 5), (94, 6), (94, 7), (94, 8), (94, 9), (94, 10))
GUI_MBAR_RECTANGLE_OFFSET = 6

RUNESTONE_SIZE = 1196, 1038
RUNESTONE_RUNE = 16, 12
RUNESTONE_MAP = 21, 17
RUNESTONE_PIECES = 1285, 12
RUNESTONE_PIECES_END = 1902, 1070
RUNESTONE_PIECE_FIRST = 1320, 50
RUNESTONE_PIECE = 100, 100
RUNESTONE_PIECE_GAP = 17

FILTER_ALLIES = [1]
FILTER_ENEMIES = [2]
FILTER_SELF = [3]
FILTER_SUMMONS = [4]
FILTER_WALKING = [5]
FILTER_FLYING = [6]
FILTER_SWIMMING = [7]
FILTER_WALLS = [8]
FILTER_CAVES = [9]
FILTER_MELEE = [10]
FILTER_RANGED = [11]
FILTER_UNITS = [12]

MIN_HP = 1
MIN_MANA = 1
MIN_SPEED = 1
MIN_SIGHT = 1
MIN_ATTACK_SPEED = 30
MIN_SIZE_PERCENT = 0.1

# Ability provides
# Three bits for provide type, four for type value, one for percent
# Values of one type is separated

PROVIDE_DMG = 0b00100010
PROVIDE_DMG_PERCENT = 0b00100011
PROVIDE_ATTACK_SPEED = 0b00100100
PROVIDE_ATTACK_SPEED_PERCENT = 0b00100101
PROVIDE_ACCURACY = 0b00101000
PROVIDE_ACCURACY_PERCENT = 0b00101001
PROVIDE_MULTISHOT = 0b00100110
PROVIDE_MULTISHOT_PERCENT = 0b00100111
PROVIDE_ATTACK_TYPE = 0b00101010
PROVIDE_ATTACK = 0b00101100

PROVIDE_HP = 0b01000010
PROVIDE_HP_PERCENT = 0b01000011
PROVIDE_MANA = 0b01000100
PROVIDE_MANA_PERCENT = 0b01000101
PROVIDE_ARMOR = 0b01000110
PROVIDE_ARMOR_PERCENT = 0b01000111
PROVIDE_SPEED = 0b01001000
PROVIDE_SPEED_PERCENT = 0b01001001
PROVIDE_SIZE = 0b01001010
PROVIDE_SIZE_PERCENT = 0b01001011
PROVIDE_SIGHT = 0b01001100
PROVIDE_SIGHT_PERCENT = 0b01001101

PROVIDE_STRENGTH = 0b01100010
PROVIDE_STRENGTH_PERCENT = 0b01100011
PROVIDE_RADIUS = 0b01100110
PROVIDE_RADIUS_PERCENT = 0b01100111
PROVIDE_ADURATION = 0b01100100
PROVIDE_ADURATION_PERCENT = 0b01100101
PROVIDE_MANACOST = 0b01101000
PROVIDE_MANACOST_PERCENT = 0b01101001
PROVIDE_CASTSPEED = 0b01101010
PROVIDE_CASTSPEED_PERCENT = 0b01101011
PROVIDE_REDUCTION = 0b01101100
PROVIDE_REDUCTION_PERCENT = 0b01101101
PROVIDE_SUPER = 0b01101110
PROVIDE_SUPER_PERCENT = 0b01101111

PROVIDE_STATUS = 0b11100010
PROVIDE_SPELL_CASTING = 0b11100100
PROVIDE_SPELL_STARTING = 0b11100110

# Statuses
# 1 means locking ability to jump, move, cast, attack and use passive abs
# the last two are providing invisible and forbids to be invisible
# The default status is 0
# 7 bits: jmcapiv
STATUS_DEAD = 0b1111101
STATUS_STUN = 0b1111000
STATUS_ROOT = 0b0100001
STATUS_SILENCE = 0b0010000
STATUS_DISARM = 0b0001000
STATUS_BREAK = 0b0000101
STATUS_INVISIBLE = 0b0000010
STATUS_VISIBLE = 0b0000001
STATUS_PSYCHOSIS = 0b0011101


def get_bit(value, n):
    return value >> n & 1


def set_bit(value, n):
    return value | (1 << n)


def clear_bit(value, n):
    return value & ~(1 << n)


def longsplit(mes, n):
    mes = [i for i in mes]
    l = len(mes)
    if l <= n:
        return mes[:n]
    c = math.ceil(l/n)
    res = []
    for i in range(c-1):
        res += mes[:n]
        mes = mes[n:]
    res += mes
    return res


@njit(fastmath=True)
def chance(a, b=100):
    if random.randint(1, b) <= a:
        return True
    return False


def search_unit_folder(data):
    for i in os.listdir('units'):
        if data in os.listdir(f'units\\{i}'):
            return f'units\\{i}\\{data}'


def select_next_unit(level, pos):
    level.selected_unit.mousepos = (pos[0]-level.mp[0], pos[1]-level.mp[1])
    rolls = 1
    idx = level.units.index(level.selected_unit) + 1
    idx = 0 if idx == len(level.units) else idx
    while not level.units[idx].canbecontrolled or level.units[idx].dead and rolls <= len(level.units):
        idx += 1
        idx = 0 if idx == len(level.units) else idx
        rolls += 1
    level.selected_unit = level.units[idx]
    level.camera_bind = level.selected_unit
    level.camera_bind_offset = (0, 0)
    level.selected_skill = None
    level.selected_item = None


def select_prev_unit(level, pos):
    level.selected_unit.mousepos = (pos[0]-level.mp[0], pos[1]-level.mp[1])
    rolls = 1
    idx = level.units.index(level.selected_unit) - 1
    idx = len(level.units) - 1 if idx == -1 else idx
    while not level.units[idx].canbecontrolled or level.units[idx].dead and rolls <= len(level.units):
        idx -= 1
        idx = len(level.units) - 1 if idx == -1 else idx
        rolls += 1
    level.selected_unit = level.units[idx]
    level.camera_bind = level.selected_unit
    level.camera_bind_offset = (0, 0)
    level.selected_skill = None
    level.selected_item = None


@njit(fastmath=True)
def accuracy(a, ang):
    if a >= 100:
        return ang
    if chance(a):
        return ang
    b = random.randint(0, 100-a)/100*math.pi
    c = random.randint(0, 1)
    ang = ang+b if c else ang-b
    return ang


@njit(fastmath=True)
def meleeaccuracy(a, top, bot):
    if a >= 100:
        return top, bot
    if chance(a):
        return top, bot
    b = random.randint(0, 100-a)/100*math.pi
    c = random.randint(0, 1)
    top = top+b if c else top-b
    bot = bot+b if c else bot-b
    return top, bot


@njit(fastmath=True)
def getrange(axy, bxy):
    ax, ay = axy
    bx, by = bxy
    return math.sqrt((bx-ax)**2+(by-ay)**2)


def find_provides(unit, prv, prvp):
    s, sp = {}, {}
    for i in unit.modifiers:
        if prv in i.provides:
            if i.name in s:
                if i.stackable:
                    s[i.name] += i.provides[prv]
                elif i.provides[prv] > s[i.name]:
                    s[i.name] = i.provides[prv]
            else:
                s[i.name] = i.provides[prv]
    for i in unit.modifiers:
        if prvp in i.provides:
            if i.name in sp:
                if i.stackable:
                    sp[i.name] += i.provides[prvp]
                elif i.provides[prvp] > sp[i.name]:
                    sp[i.name] = i.provides[prvp]
            else:
                sp[i.name] = i.provides[prvp]
    return s, sp


@njit(fastmath=True)
def circleColl(center, rad, box):
    if rad < 0:
        return False
    tx, ty = center
    tx = box[0] if tx < box[0] else box[1] if tx > box[1] else tx
    ty = box[2] if ty < box[2] else box[3] if ty > box[3] else ty
    return (center[0]-tx)**2+(center[1]-ty)**2 < rad**2


def circleCollMany(centers_rads, box):
    for tx, ty, r in centers_rads:
        c = tx, ty
        tx = box[0] if tx < box[0] else box[1] if tx > box[1] else tx
        ty = box[2] if ty < box[2] else box[3] if ty > box[3] else ty
        if (c[0]-tx)**2+(c[1]-ty)**2 < r**2:
            return True
    return False


def ti(func):
    def wr(*args, **kwargs):
        t = time.perf_counter()
        a = func(*args, **kwargs)
        print(time.perf_counter()-t)
        return a
    return wr


def deepsum(items):
    s = items[0]
    for i in items[1:]:
        s += i
    return s


def deepmax(items):
    s = items[0]
    for i in items[1:]:
        if i > s:
            s = i
    return s


def alphanum_random(length):
    letters_and_digits = string.ascii_letters + string.digits
    rand_string = ''.join(random.sample(letters_and_digits, length))
    return rand_string


def forcenpsave(fname, map):
    if not os.path.exists('temp'):
        os.mkdir('temp')
    code = alphanum_random(5)
    np.save(f'temp\\{code}', map)
    os.replace(f'temp\\{code}.npy', fname+'.npy')


def forcesave(fname, data):
    if not os.path.exists('temp'):
        os.mkdir('temp')
    code = alphanum_random(5)
    file = open(f'temp\\{code}.txt', 'w', encoding='utf-8')
    file.write(data)
    file.close()
    os.replace(f'temp\\{code}.txt', fname)
