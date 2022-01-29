import ast
import numpy as np

from config import *
from unit import *


def search_last_player_data():
    maxlptime = 0
    data = None
    name = None
    rune = None
    for p in os.listdir(f'saves'):
        if p.endswith('.txt') and p.split('.txt')[0] + '.npy' in os.listdir(f'saves'):
            file = ast.literal_eval(open(f'saves\\{p}', 'r', encoding='utf-8').read())
            lptime = file['last_played']
            if lptime > maxlptime:
                maxlptime = lptime
                data = file
                name = p.split('.txt')[0]
                rune = np.load(f'saves\\{p.split(".txt")[0]}.npy')
    if data is None:
        data = {'units': [], 'inventory': [[]], 'storage': [[]], 'player_exp': 0, 'last_played': int(time.time()), 'stats': {}, 'pieces': []}
        name = alphanum_random(6)
        forcesave(f'saves\\{name}.txt', str(data))
        rune = np.zeros((22, 22), 'int')
        forcenpsave(f'saves\\{name}', rune)
    return data, name, rune


class Piece:
    def __init__(self, data):
        self.name = data[0]
        self.id = data[1]
        self.icon = pygame.image.load(f'pieces\\{self.id}.png')
        self.part = data[2]
        self.connections = data[3]
        if self.part == 'verb':
            self.text_name = data[4]


class Runa:
    pieces = {d[1]: Piece(d) for d in ast.literal_eval(open('pieces\\pieces.txt', 'r', encoding='utf-8').read())}
    checks = ((0, 1), (-1, 0), (0, -1), (1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1))

    def __init__(self):
        self.level = None
        self.runestone_rune = pygame.image.load(f'textures\\GUI\\runestone_rune.png').convert_alpha()
        self.runestone_pieces = pygame.image.load(f'textures\\GUI\\runestone_pieces.png').convert_alpha()

        data, self.name, self.runestone = search_last_player_data()
        self.size = self.runestone.shape
        self.tile_size = min([RUNESTONE_SIZE[1]//(self.size[0]-1), RUNESTONE_SIZE[0]//(self.size[1]-1)])
        self.sc = pygame.Surface((self.tile_size*(self.size[1]-1)+10, self.tile_size*(self.size[0]-1)+10), pygame.SRCALPHA, 32)
        self.runestone_rune_scaled = pygame.transform.scale(self.runestone_rune, (self.tile_size*(self.size[1]-1)+20, self.tile_size*(self.size[0]-1)+20))
        [pygame.draw.aaline(self.sc, BLACK, (0, (i+0.5)*self.tile_size+5), (self.sc.get_width(), (i+0.5)*self.tile_size+5)) for i in range(self.size[0])]
        [pygame.draw.aaline(self.sc, BLACK, ((i+0.5)*self.tile_size+5, 0), ((i+0.5)*self.tile_size+5, self.sc.get_height())) for i in range(self.size[1])]

        self.units = data['units']
        self.inventory = data['inventory']
        self.storage = data['storage']
        self.exp = data['player_exp']
        self.stats = GameStats().load(data['stats'])
        self.pieces = data['pieces']
        self.ticks = 0
        self.piece_lock = None
        self.piece_lock_return = None

    def load(self, level):
        self.level = level

    def save(self):
        self.units = [u.save() for u in self.level.units if u.game_id]
        maxlpdata = {'units': self.units, 'inventory': self.inventory, 'storage': self.storage, 'player_exp': self.exp, 'last_played': int(time.time()), 'stats': self.stats.save(), 'pieces': self.pieces}
        forcesave(f'saves\\{self.name}.txt', str(maxlpdata))
        forcenpsave(f'saves\\{self.name}', self.runestone)

    def paint_runestone(self, sc, pos):
        sc.blit(self.runestone_rune_scaled, RUNESTONE_RUNE)
        sc.blit(self.runestone_pieces, RUNESTONE_PIECES)
        sc.blit(self.sc, RUNESTONE_MAP)
        for i, p in enumerate(self.pieces):
            piece = pygame.transform.scale(Runa.pieces[p].icon, RUNESTONE_PIECE)
            d, m = divmod(i, 5)
            sc.blit(piece, (RUNESTONE_PIECE_FIRST[0]+m*RUNESTONE_PIECE[0]+(m-1)*RUNESTONE_PIECE_GAP, RUNESTONE_PIECE_FIRST[1]+d*RUNESTONE_PIECE[0]+(d-1)*RUNESTONE_PIECE_GAP))
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                if self.runestone[i][j] > 0:
                    piece = pygame.transform.scale(Runa.pieces[self.runestone[i][j]].icon, (3*self.tile_size, 3*self.tile_size))
                    sc.blit(piece, (RUNESTONE_MAP[0]+(j-1.5)*self.tile_size+5, RUNESTONE_MAP[1]+(i-1.5)*self.tile_size+5))
        if self.piece_lock:
            piece = pygame.transform.scale(Runa.pieces[self.piece_lock].icon, RUNESTONE_PIECE)
            sc.blit(piece, (pos[0]-piece.get_width()//2, pos[1]-piece.get_height()//2))

    def hold_piece(self, pos):
        if RUNESTONE_PIECES[0] < pos[0] < RUNESTONE_PIECES_END[0] and RUNESTONE_PIECES[1] < pos[1] < RUNESTONE_PIECES_END[1]:
            for i, p in enumerate(self.pieces):
                d, m = divmod(i, 5)
                cords = (RUNESTONE_PIECE_FIRST[0] + m * RUNESTONE_PIECE[0] + (m - 1) * RUNESTONE_PIECE_GAP, RUNESTONE_PIECE_FIRST[1] + d * RUNESTONE_PIECE[0] + (d - 1) * RUNESTONE_PIECE_GAP)
                if cords[0] < pos[0] < cords[0]+RUNESTONE_PIECE[0] and cords[1] < pos[1] < cords[1]+RUNESTONE_PIECE[1]:
                    self.piece_lock = p
                    self.piece_lock_return = True
                    self.pieces.remove(self.piece_lock)
                    return
        if RUNESTONE_MAP[0] < pos[0] < RUNESTONE_MAP[0]+self.tile_size*(self.size[1]-1)+10 and RUNESTONE_MAP[1] < pos[1] < RUNESTONE_MAP[1]+self.tile_size*(self.size[0]-1)+10:
            i, j = int(((pos[1]-RUNESTONE_MAP[1]-5)/self.tile_size)+0.5), int(((pos[0]-RUNESTONE_MAP[0]-5)/self.tile_size)+0.5)
            i, j = self.find_piece(i, j)
            if i is not False:
                self.piece_lock = self.runestone[i][j]
                self.piece_lock_return = True
                self.runestone[i][j] = 0
                for oi, oj in Runa.checks:
                    si, sj = i + oi, j + oj
                    self.runestone[si][sj] = 0

    def place_piece(self, pos):
        if RUNESTONE_MAP[0] < pos[0] < RUNESTONE_MAP[0]+self.tile_size*(self.size[1]-1)+10 and RUNESTONE_MAP[1] < pos[1] < RUNESTONE_MAP[1]+self.tile_size*(self.size[0]-1)+10:
            i, j = int(((pos[1]-RUNESTONE_MAP[1]-5)/self.tile_size)+0.5), int(((pos[0]-RUNESTONE_MAP[0]-5)/self.tile_size)+0.5)
            i, j = self.check_place_for_piece(i, j)
            if i is not False:
                i, j = self.expand_runestone(i, j)
                self.runestone[i][j] = self.piece_lock
                self.piece_lock_return = False
                for oi, oj in Runa.checks:
                    si, sj = i + oi, j + oj
                    self.runestone[si][sj] = -1
        if self.piece_lock_return is True:
            self.pieces.append(self.piece_lock)
            self.piece_lock_return = None
        self.contract_runestone()
        self.piece_lock = None

    def check_place_for_piece(self, i, j):
        if self.runestone[i][j]:
            return False, False
        colls = []
        for oi, oj in Runa.checks:
            si, sj = i+oi, j+oj
            if si < 0 or sj < 0 or si >= self.size[0] or sj >= self.size[1]:
                continue
            if self.runestone[si][sj]:
                colls.append((si, sj))
        if colls:
            i, j = self.check_place_for_piece(colls[0][0], colls[0][1])
        return i, j

    def find_piece(self, i, j):
        if not self.runestone[i][j]:
            return False, False
        if self.runestone[i][j] > 0:
            return i, j
        for oi, oj in Runa.checks:
            si, sj = i + oi, j + oj
            if si < 0 or sj < 0 or si >= self.size[0] or sj >= self.size[1]:
                continue
            if self.runestone[si][sj] > 0:
                return si, sj
        return False, False

    def expand_runestone(self, i, j):
        oldsize = self.size
        if i < 2:
            self.runestone = np.concatenate((np.zeros((2 - i, self.size[1]), 'int'), self.runestone), axis=0)
            self.size = self.runestone.shape
            i = 2
        if j < 2:
            self.runestone = np.concatenate((np.zeros((self.size[0], 2 - j), 'int'), self.runestone), axis=1)
            self.size = self.runestone.shape
            j = 2
        if i > self.size[0]-3:
            self.runestone = np.concatenate((self.runestone, np.zeros((i - self.size[0] + 3, self.size[1]), 'int')), axis=0)
            self.size = self.runestone.shape
        if j > self.size[1]-3:
            self.runestone = np.concatenate((self.runestone, np.zeros((self.size[0], j - self.size[1] + 3), 'int')), axis=1)
            self.size = self.runestone.shape
        if self.size != oldsize:
            self.tile_size = min([RUNESTONE_SIZE[1] // (self.size[0] - 1), RUNESTONE_SIZE[0] // (self.size[1] - 1)])
            self.sc = pygame.Surface((self.tile_size * (self.size[1] - 1) + 10, self.tile_size * (self.size[0] - 1) + 10), pygame.SRCALPHA, 32)
            self.runestone_rune_scaled = pygame.transform.scale(self.runestone_rune, (self.tile_size * (self.size[1] - 1) + 20, self.tile_size * (self.size[0] - 1) + 20))
            [pygame.draw.aaline(self.sc, BLACK, (0, (i + 0.5) * self.tile_size + 5), (self.sc.get_width(), (i + 0.5) * self.tile_size + 5)) for i in range(self.size[0])]
            [pygame.draw.aaline(self.sc, BLACK, ((i + 0.5) * self.tile_size + 5, 0), ((i + 0.5) * self.tile_size + 5, self.sc.get_height())) for i in range(self.size[1])]
        return i, j

    def contract_runestone(self, rec=False):
        oldsize = self.size
        if self.size[1] > 22 and not any((i[1] for i in self.runestone)):
            self.runestone = np.delete(self.runestone, 1, axis=1)
            self.size = self.runestone.shape
            self.contract_runestone(True)
        if self.size[0] > 22 and not any(self.runestone[1]):
            self.runestone = np.delete(self.runestone, 1, axis=0)
            self.size = self.runestone.shape
            self.contract_runestone(True)
        if self.size[1] > 22 and not any((i[self.size[1]-2] for i in self.runestone)):
            self.runestone = np.delete(self.runestone, self.size[1]-2, axis=1)
            self.size = self.runestone.shape
            self.contract_runestone(True)
        if self.size[0] > 22 and not any(self.runestone[self.size[0]-2]):
            self.runestone = np.delete(self.runestone, self.size[0]-2, axis=0)
            self.size = self.runestone.shape
            self.contract_runestone(True)
        if not rec and self.size != oldsize:
            self.tile_size = min([RUNESTONE_SIZE[1] // (self.size[0] - 1), RUNESTONE_SIZE[0] // (self.size[1] - 1)])
            self.sc = pygame.Surface((self.tile_size * (self.size[1] - 1) + 10, self.tile_size * (self.size[0] - 1) + 10), pygame.SRCALPHA, 32)
            self.runestone_rune_scaled = pygame.transform.scale(self.runestone_rune, (self.tile_size * (self.size[1] - 1) + 20, self.tile_size * (self.size[0] - 1) + 20))
            [pygame.draw.aaline(self.sc, BLACK, (0, (i + 0.5) * self.tile_size + 5), (self.sc.get_width(), (i + 0.5) * self.tile_size + 5)) for i in range(self.size[0])]
            [pygame.draw.aaline(self.sc, BLACK, ((i + 0.5) * self.tile_size + 5, 0), ((i + 0.5) * self.tile_size + 5, self.sc.get_height())) for i in range(self.size[1])]

    def tick(self): # TODO: Надписи о словах на основе dmgvs
        self.ticks += 1
        if self.ticks % 7200 == 0:
            self.save()

    def load_units(self):
        return [Unit(u[0], self.level).load(*u[1:]) for u in self.units]

    # TODO: Руна меняет цвет после полного прохождения игры, первый раз она синяя, должен быть ещё белый где-то на 4 прохождении
    #  За получение героев первый раз даётся кусочек Руны
    #  playerdata: {units: [(zalgo, lvl, perks, items: [(name, gid, stats)])], inventory: [[]], player_exp}

    # TODO: внести сюда идеи с сервера Dev

    # TODO: переписать на rotoscale и пр.


class MiniRuna:
    def __init__(self, level, size, pieces, solution, tilemap=None):
        self.level = level
        self.pieces = pieces
        self.solution = solution

        self.runestone = tilemap if tilemap else np.zeros(size, 'int')
        self.size = self.runestone.shape
        self.tile_size = 100
        self.sc = pygame.Surface((self.tile_size * self.size[1], self.tile_size * self.size[0]), pygame.SRCALPHA, 32)
        [pygame.draw.aaline(self.sc, BLACK, (0, i * self.tile_size), (self.sc.get_width(), i * self.tile_size)) for i in range(1, self.size[0])]
        [pygame.draw.aaline(self.sc, BLACK, (i * self.tile_size, 0), (i * self.tile_size, self.sc.get_height())) for i in range(1, self.size[1])]

        self.ticks = 0
        self.piece_lock = None
        self.piece_lock_return = None

    def paint_runestone(self, sc, pos, mp):
        ssc = pygame.transform.rotozoom(self.sc, 0, self.level.camera_scale)
        sc.blit(ssc, mp)
        tile_size = self.tile_size*self.level.camera_scale
        piece_size = tile_size*3, tile_size*3
        piece_first = mp[0]+ssc.get_width()+20*self.level.camera_scale, mp[1]+10*self.level.camera_scale
        piece_gap = 10*self.level.camera_scale
        for i, p in enumerate(self.pieces):
            piece = pygame.transform.scale(Runa.pieces[p].icon, piece_size)
            d, m = divmod(i, 5)
            sc.blit(piece, (piece_first[0] + m * piece_size[0] + (m - 1) * piece_gap, piece_first[1] + d * piece_size[0] + (d - 1) * piece_gap))
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                if self.runestone[i][j] > 0:
                    piece = pygame.transform.scale(Runa.pieces[self.runestone[i][j]].icon, piece_size)
                    sc.blit(piece, (mp[0] + (j - 1) * tile_size, mp[1] + (i - 1) * tile_size))
        if self.piece_lock:
            piece = pygame.transform.scale(Runa.pieces[self.piece_lock].icon, piece_size)
            sc.blit(piece, (pos[0] - piece.get_width() // 2, pos[1] - piece.get_height() // 2))

    def hold_piece(self, pos, mp):
        tile_size = self.tile_size*self.level.camera_scale
        piece_size = tile_size*3, tile_size*3
        piece_first = mp[0]+self.sc.get_width()*self.level.camera_scale+20*self.level.camera_scale, mp[1]+10*self.level.camera_scale
        piece_gap = 10*self.level.camera_scale
        piece_last = piece_first[0]+math.ceil(len(self.pieces)/5)*piece_size[0]+(math.ceil(len(self.pieces)/5)-1)*piece_gap, piece_first[1]+5*piece_size[1]+4*piece_gap
        if piece_first[0] < pos[0] < piece_last[0] and piece_first[1] < pos[1] < piece_last[1]:
            for i, p in enumerate(self.pieces):
                d, m = divmod(i, 5)
                cords = (piece_first[0] + m * piece_size[0] + (m - 1) * piece_gap, piece_first[1] + d * piece_size[1] + (d - 1) * piece_gap)
                if cords[0] < pos[0] < cords[0] + piece_size[0] and cords[1] < pos[1] < cords[1] + piece_size[1]:
                    self.piece_lock = p
                    self.piece_lock_return = True
                    self.pieces.remove(self.piece_lock)
                    return
        if mp[0] < pos[0] < mp[0] + tile_size * self.size[1] and mp[1] < pos[1] < mp[1] + tile_size * self.size[0]:
            i, j = int((pos[1] - mp[1]) / tile_size), int((pos[0] - mp[0]) / tile_size)
            i, j = self.find_piece(i, j)
            if i is not False:
                self.piece_lock = self.runestone[i][j]
                self.piece_lock_return = True
                self.runestone[i][j] = 0
                for oi, oj in Runa.checks:
                    si, sj = i + oi, j + oj
                    self.runestone[si][sj] = 0

    def place_piece(self, pos, mp):
        tile_size = self.tile_size * self.level.camera_scale
        if mp[0] < pos[0] < mp[0] + tile_size * self.size[1] and mp[1] < pos[1] < mp[1] + tile_size * self.size[0]:
            i, j = int((pos[1] - mp[1]) / tile_size), int((pos[0] - mp[0]) / tile_size)
            i, j = self.check_place_for_piece(i, j)
            if i is not False:
                self.runestone[i][j] = self.piece_lock
                self.piece_lock_return = False
                for oi, oj in Runa.checks:
                    si, sj = i + oi, j + oj
                    self.runestone[si][sj] = -1
        if self.piece_lock_return is True:
            self.pieces.append(self.piece_lock)
            self.piece_lock_return = None
        self.piece_lock = None

    def check_place_for_piece(self, i, j):
        if i < 0 or j < 0 or i >= self.size[0] or j >= self.size[1]:
            return False, False
        if self.runestone[i][j]:
            return False, False
        colls = []
        for oi, oj in Runa.checks:
            si, sj = i + oi, j + oj
            if si < 0 or sj < 0 or si >= self.size[0] or sj >= self.size[1]:
                colls.append((oi, oj))
            elif self.runestone[si][sj]:
                colls.append((oi, oj))
        if colls:
            i, j = self.check_place_for_piece(i - colls[0][0], j - colls[0][1])
        return i, j

    def find_piece(self, i, j):
        if not self.runestone[i][j]:
            return False, False
        if self.runestone[i][j] > 0:
            return i, j
        for oi, oj in Runa.checks:
            si, sj = i + oi, j + oj
            if si < 0 or sj < 0 or si >= self.size[0] or sj >= self.size[1]:
                continue
            if self.runestone[si][sj] > 0:
                return si, sj
        return False, False

    def tick(self): # TODO: Надписи о словах на основе dmgvs
        self.ticks += 1

