import pygame
import os
import sqlite3
from PIL import Image, ImageFilter
import time
import ast
import matplotlib.pyplot as plt
from perlin_noise import PerlinNoise
import numpy as np

from config import *
from animation import *
from gui import *
from runestone import *
from unit import *

maps = {}


class Map: # TODO: refactor
    def __init__(self, planet, part, texture):
        self.planet = planet
        self.part = part
        self.texture = pygame.image.load(texture).convert_alpha()


def add_planet(name, num):
    maps[name] = tuple((Map(name, i+1, f'textures/maps/{name}{i+1}.png') for i in range(num)))


def load_block(i):
    part = pygame.image.load(f'blocks\\{i}.png')
    part = pygame.transform.scale(part, (TILE_SIZE, TILE_SIZE))
    data = ast.literal_eval(open(f'blocks\\{i}.txt', 'r', encoding='utf-8').read())
    data['tex'] = part
    offset = data['offset'] if 'offset' in data else None
    return data['id'], data, offset


def search_last_level():
    maxlptime = 0
    maxlplevel = 0
    for planet in os.listdir(f'leveldata'):
        for level in os.listdir(f'leveldata\\{planet}'):
            if level.endswith(".txt") and level.split('.txt')[0] + '.npy' in os.listdir(f'leveldata\\{planet}'):
                file = ast.literal_eval(open(f'leveldata\\{planet}\\{level}', 'r', encoding='utf-8').read())
                lptime = file['last_played']
                levelid = file['id']
                if lptime > maxlptime:
                    maxlptime = lptime
                    maxlplevel = levelid
    return maxlplevel


@njit(fastmath=True)
def getmp(pos, camera, camera_bind, camera_bind_cords, camera_bind_offset, tile_size, chunk_size_px, map_size, chunkmap_size):
    cbox, cboy = camera_bind_offset
    if camera_bind:
        if pos[0] < 100:
            cbox -= CAMERA_SPEED
            if cbox < -HALF_WINDOW[0] / tile_size:
                cbox = -HALF_WINDOW[0] / tile_size
        if pos[1] < 100:
            cboy -= CAMERA_SPEED
            if cboy < -HALF_WINDOW[1] / tile_size:
                cboy = -HALF_WINDOW[1] / tile_size
        if pos[0] > FULL_WINDOW[0] - 100:
            cbox += CAMERA_SPEED
            if cbox > HALF_WINDOW[0] / tile_size:
                cbox = HALF_WINDOW[0] / tile_size
        if pos[1] > FULL_WINDOW[1] - 100:
            cboy += CAMERA_SPEED
            if cboy> HALF_WINDOW[1] / tile_size:
                cboy = HALF_WINDOW[1] / tile_size
        camera = (camera_bind_cords[0] + cbox, camera_bind_cords[1] + cboy)
        # if self.camera.x < 0:
        #     self.camera.x = 0
        # if self.camera.x > self.size.x:
        #     self.camera.x = self.size.x
        # if self.camera.y < 0:
        #     self.camera.y = 0
        # if self.camera.y > self.size.y:
        #     self.camera.y = self.size.y
    else:
        one, two = camera
        if pos[0] < 200:
            one = camera[0] - CAMERA_SPEED
            if one < 0:
                one = 0
        if pos[1] < 200:
            two = camera[1] - CAMERA_SPEED
            if two < 0:
                two = 0
        if pos[0] > FULL_WINDOW[0] - 200:
            one = camera[0] + CAMERA_SPEED
            if one > map_size[0]:
                one = map_size[0]
        if pos[1] > FULL_WINDOW[1] - 200:
            two = camera[1] + CAMERA_SPEED
            if two > map_size[1]:
                two = map_size[0]
        if not camera == (one, two):
            camera = (one, two)
    mp = (int(HALF_WINDOW[0] - camera[0] * tile_size), int(HALF_WINDOW[1] - camera[1] * tile_size))
    if mp[0] > 0:
        mp = 0, mp[1]
    if mp[1] > 0:
        mp = mp[0], 0
    if mp[0] < -map_size[0] * tile_size + FULL_WINDOW[0]:
        mp = -map_size[0] * tile_size + FULL_WINDOW[0], mp[1]
    if mp[1] < -map_size[1] * tile_size + FULL_WINDOW[1]:
        mp = mp[0], -map_size[1] * tile_size + FULL_WINDOW[1]
    mchunks = [(i, j, mp[0] + chunk_size_px * i, mp[1] + chunk_size_px * j)
               for i in range(chunkmap_size[0]) if -chunk_size_px <= mp[0] + chunk_size_px * i < FULL_WINDOW[0]
               for j in range(chunkmap_size[1]) if -chunk_size_px <= mp[1] + chunk_size_px * j < FULL_WINDOW[1]]
    return camera, (cbox, cboy),  mp, mchunks


def findClearSpaceForUnits(tilemap, sizes, place):
    tilemap = tilemap.copy()
    size = tilemap.shape
    res = []
    for x, y in sizes:
        dst = 0
        while True:
            dirs = []
            for i in range(dst):
                dirs += [(place[0]-(dst-i), place[1]+i), (place[0]+(dst-i), place[1]-i), (place[0]+i, place[1]+(dst-i)), (place[0]-i, place[1]-(dst-i))]
            dirs = [place] if not dirs else dirs[::-1]
            breakFlag = False
            for i,j in dirs:
                flag = True
                for iy in range(y):
                    if not flag:
                        break
                    if not 0 <= i - iy < size[1]:
                        flag = False
                        break
                    for jx in range(x):
                        if not 0 <= j + jx < size[0] or tilemap[i+iy][j+jx]:
                            flag = False
                            break
                if flag:
                    ri = random.randint(0, 50) / 50
                    res.append((i+ri, j))
                    for iy in range(y):
                        for jx in range(x):
                            tilemap[i+iy][j+jx] = -1
                    breakFlag = True
            dst += 1
            if breakFlag or dst > size[0]:
                break
    return res


def findRandomSpaceForUnits(tilemap, sizes, place, radius):
    tilemap = tilemap.copy()
    size = tilemap.shape
    res = []
    dirs = [place]
    for dst in range(1, radius+1):
        for i in range(dst):
            dirs += [(place[0] - (dst - i), place[1] + i), (place[0] + (dst - i), place[1] - i),
                     (place[0] + i, place[1] + (dst - i)), (place[0] - i, place[1] - (dst - i))]
    for x, y in sizes:
        v = 0
        while v < len(dirs):
            i, j = random.choice(dirs)
            flag = True
            for iy in range(y):
                if not flag:
                    break
                if not 0 <= i - iy < size[1]:
                    flag = False
                    break
                for jx in range(x):
                    if not 0 <= j + jx < size[0] or tilemap[i + iy][j + jx]:
                        flag = False
                        break
            if flag:
                ri = random.randint(0, 50) / 50
                res.append((i + ri, j))
                for iy in range(y):
                    for jx in range(x):
                        tilemap[i + iy][j + jx] = -1
                break
            v += 1

    return res


class Level:
    planets = {1: 'Earth'}
    blocks = {}
    blocks_offset = {}
    for i in os.listdir(f'blocks'):
        if i.endswith('.png'):
            blockid, block, offset = load_block(i.split('.png')[0])
            blocks[blockid] = block
            if offset:
                blocks_offset[blockid] = offset
    #  TODO:
    #   расширить тайлсет новыми блоками
    #   задний уровень: подуровень со стенами и декорациями
    #   AI

    def __init__(self, id, runa, gui, dialogs, **kwargs):
        self.id = id
        self.bck = pygame.image.load('textures\\bck.png').convert_alpha() # Временный бекграунд
        self.bck = pygame.transform.scale(self.bck, FULL_WINDOW)
        if id == 0: # для проецирования последней сыгранной карты на фоне в меню
            self.id = search_last_level()
        self.kwargs = kwargs
        self.size = Vector(TEST_MAP_SIZE_X, TEST_MAP_SIZE_Y)
        self.chunk_size = 20
        self.chunkmap_size = Vector(math.ceil(TEST_MAP_SIZE_X/self.chunk_size), math.ceil(TEST_MAP_SIZE_Y/self.chunk_size))
        self.tilemap = np.zeros((self.size.x, self.size.y), 'int')
        self.block_data = {}
        self.spawn = tuple((Vector(20+2*i, 10) for i in range(7)))
        self.enemy_spawn = tuple((Vector(30+i, 10) for i in range(7)))
        self.camera = (0, 0)
        self.camera_bind = None
        self.camera_bind_offset = (0, 0)
        self.camera_scale = 1
        self.tile_size = TILE_SIZE
        self.chunk_size_px = TILE_SIZE * self.chunk_size
        self.nsc = [[pygame.Surface((self.chunk_size * TILE_SIZE, self.chunk_size * TILE_SIZE), pygame.SRCALPHA, 32) for _ in range(self.chunkmap_size.y)] for _ in range(self.chunkmap_size.x)]
        self.sc = [[j for j in i] for i in self.nsc]
        self.projectiles = []
        self.ticks = 0
        self.mp = (0,0)
        self.mchunks = ()
        self.selected_unit = None
        self.selected_skill = None
        self.selected_item = None
        self.allvision = False
        self.units = []
        self.sp = DamageTable()
        self.gui = gui
        self.runa = runa
        self.dialogs = dialogs
        self.dropped = []

    def load(self, regen=False):
        self.runa.load(self)
        self.gui.load(self)
        self.dialogs.load(self)
        if self.id == 0:
            return self
        planet = self.id // 1000000
        level = self.id % 1000000 // 1000
        var = self.id % 1000
        folder = Level.planets[planet]
        if not os.path.exists(f'leveldata\\{folder}'):
            os.mkdir(f'leveldata\\{folder}')
        fn = f'{level}-{var}'
        if 'editor' in self.kwargs and self.kwargs['editor']:
            fn += 'editor'
        if f'{fn}.npy' not in os.listdir(f'leveldata\\{folder}') or f'{fn}.txt' not in os.listdir(f'leveldata\\{folder}') or regen:
            self.generate_terrain()
            self.save_terrain()
        else:
            self.tilemap = np.load(f'leveldata\\{folder}\\{fn}.npy')
        self.render_terrain()
        allies = self.runa.load_units()
        self.spawn = tuple((Vector(i) for i in findClearSpaceForUnits(self.tilemap, [i.size.cort() for i in allies], (10, 10))))
        enemies = [Unit('Rock', self, e=True) for _ in range(50)]
        self.enemy_spawn = tuple((Vector(i) for i in findRandomSpaceForUnits(self.tilemap, [i.size.cort() for i in enemies], (40, 10), 10)))
        self.units[:] = allies + enemies
        return self

    def vision(self, team='ally'):
        if self.allvision:
            return self.units
        crs = [(u.cords.x, u.cords.y-u.size.y/2, u.sight) for u in self.units if u.team == team and not u.dead]
        return [i for i in self.units if i.team == team or i.dead or not get_bit(i.status, 1) and circleCollMany(crs, i.hitbox()) or get_bit(i.status, 0)]
        # TODO: сделать остальную область чёрной?

    def paint(self, sc, objs, odata):
        [sc.blit(self.sc[i][j], (x,y)) for i, j, x, y in self.mchunks]

        v = self.vision()
        for b in v:
            b.blit(sc)

        projectiles_trash = []
        for i, a in enumerate(self.projectiles):
            anim = a.animate(sc)
            if anim is False:
                projectiles_trash.append(a)
        self.projectiles[:] = [a for a in self.projectiles if a not in projectiles_trash]

        sc.blits(((d.icon, (cords.x * self.tile_size + self.mp[0] - d.icon.get_width() // 2, cords.y * self.tile_size + self.mp[1] - d.icon.get_height())) for d,cords in self.dropped))

        for b in v:
            b.blit_dmgvs(sc)

        self.gui.blit(sc)

    def move_camera(self, pos):
        if self.camera_bind:
            self.camera, self.camera_bind_offset, self.mp, self.mchunks = getmp(pos, self.camera,
                         True, self.camera_bind.cords.cort(), self.camera_bind_offset,
                         self.tile_size, self.chunk_size_px, self.size.cort(), self.chunkmap_size.cort())
        else:
            self.camera, self.camera_bind_offset, self.mp, self.mchunks = getmp(pos, self.camera,
                         False, (0,0), self.camera_bind_offset, self.tile_size, self.chunk_size_px,
                         self.size.cort(), self.chunkmap_size.cort())

    def paint_bckgr(self, sc):
        sc.blit(self.bck, (0,0))
        if self.id == 0:
            return

    def play(self):
        aidx, eidx = 0, 0
        self.selected_unit = self.units[0] if self.units else None
        self.camera_bind = self.selected_unit if self.selected_unit else None
        self.camera_bind_offset = (0, 0)
        self.selected_skill = None
        self.selected_item = None
        for i,u in enumerate(self.units):
            if u.team == 'ally':
                u.cords = self.spawn[aidx]()
                aidx += 1
            elif u.team == 'enemy':
                u.cords = self.enemy_spawn[eidx]()
                eidx += 1

    def find_upper_space(self, unit, ofs=-0.1):
        ycord = unit.cords.y-unit.size.y+ofs
        if ycord < 0:
            return False
        ycord = int(ycord)
        for i in range(int(unit.cords.x-unit.size.x/2+0.25), int(unit.cords.x+unit.size.x/2-0.25)+1):
            if not self.tilemap[i][ycord] == 0:
                return False
        return True

    def find_under_space(self, unit, ofs=0.1):
        ycord = int(unit.cords.y+ofs)
        if ycord >= self.size.y:
            return False
        for i in range(int(unit.cords.x-unit.size.x/2+0.25), int(unit.cords.x+unit.size.x/2-0.25)+1):
            if not self.tilemap[i][ycord] == 0:
                return False
        return True

    def find_left_space(self, unit, ofs=-0.1):
        xcord = unit.cords.x-unit.size.x/2+ofs
        if xcord < 0:
            return False
        xcord = int(xcord)
        for j in range(int(unit.cords.y-unit.size.y+0.25), int(unit.cords.y-0.25)+1):
            if not self.tilemap[xcord][j] == 0:
                return False
        return True

    def find_right_space(self, unit, ofs=0.1):
        xcord = int(unit.cords.x+unit.size.x/2+ofs)
        if xcord >= self.size.x:
            return False
        for j in range(int(unit.cords.y-unit.size.y+0.25), int(unit.cords.y-0.25)+1):
            if not self.tilemap[xcord][j] == 0:
                return False
        return True

    def tick(self):
        self.ticks += 1
        if self.id > 0 and self.ticks % 360 == 0:
            self.save_terrain()

    def generate_terrain(self):
        start_time = time.time()
        # noise1 = PerlinNoise(octaves=3)
        # noise2 = PerlinNoise(octaves=6)
        # noise3 = PerlinNoise(octaves=12)
        # noise4 = PerlinNoise(octaves=24)
        #
        # xpix, ypix = self.size.x, self.size.y
        # pic = []
        # for i in range(ypix):
        #     row = []
        #     for j in range(xpix):
        #         noise_val = noise1([i / xpix, j / ypix])
        #         noise_val += 0.5 * noise2([i / xpix, j / ypix])
        #         noise_val += 0.25 * noise3([i / xpix, j / ypix])
        #         noise_val += 0.125 * noise4([i / xpix, j / ypix])
        #         row.append(noise_val)
        #     pic.append(row)
        #
        # for i in range(self.size.x):
        #     for j in range(self.size.y):
        #         if pic[j][i] < 0:
        #             self.tilemap[i][j] = 1
        #         else:
        #             self.tilemap[i][j] = 0
        self.tilemap = np.concatenate((np.zeros((self.size.x, 40), 'int'), np.ones((self.size.x, self.size.y-40), 'int')), axis=1)

        # plt.imshow(pic, cmap='gray')
        # plt.show()
        # print(time.time()-start_time)

    def save_terrain(self):
        folder = Level.planets[self.id // 1000000]
        fn = f'leveldata\\{folder}\\{self.id % 1000000 // 1000}-{self.id % 1000}'
        if 'editor' in self.kwargs and self.kwargs['editor']:
            fn += 'editor'
        forcenpsave(fn, self.tilemap)
        leveldata = {'last_played': int(time.time()), 'id': self.id}
        forcesave(f'{fn}.txt', str(leveldata))

    def render_terrain(self):
        self.nsc = [[pygame.Surface((self.chunk_size * TILE_SIZE, self.chunk_size * TILE_SIZE), pygame.SRCALPHA, 32) for _ in range(self.chunkmap_size.y)] for _ in range(self.chunkmap_size.x)]
        for i in range(self.size.x):
            xcord = i % self.chunk_size * TILE_SIZE
            xchunk = i//self.chunk_size
            for j in range(self.size.y):
                ycord = j % self.chunk_size * TILE_SIZE
                ychunk = j // self.chunk_size
                # if self.tilemap[i][j] in Level.blocks_offset:
                #     offset = Level.blocks_offset[self.tilemap[i][j]]
                #     self.nsc.blit(Level.blocks[self.tilemap[i][j]]['tex'], (xcord + offset[0], ycord + offset[1]))
                # else:
                self.nsc[xchunk][ychunk].blit(Level.blocks[self.tilemap[i][j]]['tex'], (xcord, ycord))
        self.sc = [[j for j in i] for i in self.nsc]

    def update_chunk(self, cords):
        xchunk, ychunk = cords[0]//self.chunk_size, cords[1]//self.chunk_size
        usc = pygame.Surface((self.chunk_size * TILE_SIZE, self.chunk_size * TILE_SIZE), pygame.SRCALPHA, 32)
        for i in range(self.chunk_size):
            xcord = i * TILE_SIZE
            xtile = i + xchunk * self.chunk_size
            for j in range(self.chunk_size):
                ycord = j * TILE_SIZE
                ytile = i + ychunk * self.chunk_size
                # if tilemap[i][j] in Level.blocks_offset:
                #     offset = Level.blocks_offset[tilemap[i][j]]
                #     nsc.blit(Level.blocks[tilemap[i][j]]['tex'], (xcord + offset[0], ycord + offset[1]))
                # else:
                usc.blit(Level.blocks[self.tilemap[xtile][ytile]]['tex'], (xcord, ycord))
        self.nsc[xchunk][ychunk] = usc
        chunksize = int(self.chunk_size * TILE_SIZE * self.camera_scale)
        self.sc[xchunk][ychunk] = pygame.transform.scale(usc, (chunksize, chunksize))

    def drop_rescale(self):
        for i, _ in self.dropped:
            i.icon = pygame.transform.scale(Item.icons[i.name], (int(self.tile_size*0.7), int(self.tile_size*0.7)))

    def make_scale(self, scale=None):
        if scale is not None:
            self.camera_scale = scale
        self.tile_size = int(TILE_SIZE * self.camera_scale)
        self.chunk_size_px = self.tile_size * self.chunk_size
        chunksize = int(self.chunk_size * TILE_SIZE * self.camera_scale)
        self.sc = [[pygame.transform.scale(j, (chunksize, chunksize)) for j in i] for i in self.nsc]
        self.drop_rescale()