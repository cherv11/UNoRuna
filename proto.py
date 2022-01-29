import pygame
import numpy as np

from config import *


def load_proj_anim(name, folder):
    return tuple((pygame.image.load(f'{folder}\\{name}\\{i}').convert_alpha() for i in os.listdir(f'{folder}\\{name}')))


class Vector:
    def __init__(self, x=0, y=0):
        if isinstance(x, (list, tuple)):
            self.x, self.y = x
            return
        self.x = x
        self.y = y

    def __call__(self):
        return Vector(self.x, self.y)

    def getlen(self):
        return math.sqrt(self.x**2+self.y**2)

    def setlen(self, l):
        self.normalize()
        self.x *= l
        self.y *= l

    def normalize(self):
        l = self.getlen()
        self.x /= l
        self.y /= l

    def cort(self):
        return self.x, self.y

    def toint(self):
        self.x = int(self.x)
        self.y = int(self.y)
        return self

    def angle(self):
        nvec = self()
        nvec.normalize()
        ang = math.asin(nvec.y*-1)
        ang = math.pi - ang if nvec.x < 0 else ang
        return ang

    def __add__(self, other):
        return Vector(self.x+other.x, self.y+other.y)

    def __sub__(self, other):
        return Vector(self.x-other.x, self.y-other.y)

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        return False

    def __gt__(self, other):
        if self.getlen() > other.getlen():
            return True
        return False

    def __mul__(self, other):
        return Vector(self.x*other, self.y*other)

    def __truediv__(self, other):
        return Vector(self.x/other, self.y/other)

    def __floordiv__(self, other):
        return Vector(self.x//other, self.y//other)

    def __str__(self):
        return f'({self.x}, {self.y})'


class Provides:
    def __init__(self, *args):
        self.provides, self.values = tuple(zip(*args)) or ((), ())

    def __contains__(self, item):
        if item in self.provides:
            return True
        return False

    def __getitem__(self, item):
        return self.values[self.provides.index(item)]

    def __call__(self):
        res = Provides()
        res.provides = self.provides
        res.values = self.values
        return res

    def __mul__(self, other):
        res = Provides()
        res.provides = self.provides
        res.values = tuple((i*other for i in self.values))
        return res


class DamageTable:
    bigkeys = ('normal', 'air', 'water', 'fire', 'earth', 'dark', 'light')
    keys = ('n', 'a', 'w', 'f', 'e', 'd', 'l')

    def __init__(self, n=0, a=0, w=0, f=0, e=0, d=0, l=0):
        if isinstance(n, str):
            if n.isdigit():
                n = float(n)
            else:    # Эта штука не принимает дробные числа из файла
                dl = re.findall(r'\d+n|\d+a|\d+w|\d+f|\d+e|\d+d|\d+l', n)
                n = 0
                for i in dl:
                    if 'n' in i:
                        n = int(i.split('n')[0])
                    if 'a' in i:
                        a = int(i.split('a')[0])
                    if 'w' in i:
                        w = int(i.split('w')[0])
                    if 'f' in i:
                        f = int(i.split('f')[0])
                    if 'e' in i:
                        e = int(i.split('e')[0])
                    if 'd' in i:
                        d = int(i.split('d')[0])
                    if 'l' in i:
                        l = int(i.split('l')[0])
        self.values = (n, a, w, f, e, d, l)

    def __call__(self):
        return DamageTable(*self.values)

    def __getitem__(self, item):
        if item in DamageTable.keys:
            return self.values[DamageTable.keys.index(item)]
        return self.values[DamageTable.bigkeys.index(item)]

    def __iter__(self):
        self.a = -1
        return self

    def __next__(self):
        if self.a < 6:
            self.a += 1
            return DamageTable.keys[self.a], self.values[self.a]
        else:
            raise StopIteration

    def __add__(self, other):
        if isinstance(other, DamageTable):
            return DamageTable(*tuple((v+other[i] for i,v in self)))
        return DamageTable(*tuple((i+other for i in self.values)))

    def __mul__(self, other):
        if isinstance(other, DamageTable):
            return DamageTable(*tuple((v*other[i] for i,v in self)))
        return DamageTable(*tuple((i*other for i in self.values)))

    def __truediv__(self, other):
        if isinstance(other, DamageTable):
            return DamageTable(*tuple((v/other[i] for i,v in self)))
        return DamageTable(*tuple((i/other for i in self.values)))

    def __gt__(self, other):
        if self.sum() > other.sum():
            return True
        return False

    def __str__(self):
        return f'DamageTable{self.values}'

    def sum(self):
        return sum(self.values)

    def add(self, value, key):
        values = list(self.values)
        if key in DamageTable.keys:
            values[DamageTable.keys.index(key)] += value
        else:
            values[DamageTable.bigkeys.index(key)] += value
        self.values = tuple(values)


class UnitStats:
    def __init__(self):
        self.shoots = 0
        self.hits = 0
        self.received_hits = 0
        self.dist = 0
        self.flydist = 0
        self.jumps = 0
        self.kills = 0
        self.deaths = 0
        self.casts = 0
        self.ultimates = 0
        self.damage = 0
        self.raw_damage = 0
        self.blocked_damage = 0
        self.received_damage = 0

    def __str__(self):
        return f'shoots={self.shoots}, hits={self.hits}, jumps={self.jumps}, dist={self.dist}, kills={self.kills}, casts={self.casts}, dmg={self.damage}, raw={self.raw_damage}'

    def load(self, data):
        self.shoots = data[0]
        self.hits = data[1]
        self.received_hits = data[2]
        self.dist = data[3]
        self.flydist = data[4]
        self.jumps = data[5]
        self.kills = data[6]
        self.deaths = data[7]
        self.casts = data[8]
        self.ultimates = data[9]
        self.damage = data[10]
        self.raw_damage = data[11]
        self.blocked_damage = data[12]
        self.received_damage = data[13]

    def save(self):
        return [self.shoots, self.hits, self.received_hits, self.dist, self.flydist, self.jumps, self.kills,
                self.deaths, self.casts, self.ultimates, self.damage, self.raw_damage, self.blocked_damage,
                self.received_damage]


class GameStats:
    def __init__(self):
        self.shoots = defaultdict(int)
        self.hits = defaultdict(int)
        self.received_hits = defaultdict(int)
        self.dist = defaultdict(int)
        self.flydist = defaultdict(int)
        self.jumps = defaultdict(int)
        self.kills = defaultdict(int)
        self.deaths = defaultdict(int)
        self.casts = defaultdict(int)
        self.ultimates = defaultdict(int)
        self.damage = defaultdict(int)
        self.raw_damage = defaultdict(int)
        self.blocked_damage = defaultdict(int)
        self.received_damage = defaultdict(int)

    def __str__(self):
        team = 'ally'
        return f'shoots={self.shoots[team]}, hits={self.hits[team]}, jumps={self.jumps[team]}, dist={self.dist[team]}, kills={self.kills[team]}, casts={self.casts[team]}, dmg={self.damage[team]}, raw={self.raw_damage[team]}'

    def load(self, data):
        for k, v in data.items():
            self.shoots[k] = v[0]
            self.hits[k] = v[1]
            self.received_hits[k] = v[2]
            self.dist[k] = v[3]
            self.flydist[k] = v[4]
            self.jumps[k] = v[5]
            self.kills[k] = v[6]
            self.deaths[k] = v[7]
            self.casts[k] = v[8]
            self.ultimates[k] = v[9]
            self.damage[k] = v[10]
            self.raw_damage[k] = v[11]
            self.blocked_damage[k] = v[12]
            self.received_damage[k] = v[13]
        return self

    def save(self):
        return {k: [self.shoots[k], self.hits[k], self.received_hits[k], self.dist[k], self.flydist[k], self.jumps[k],
                    self.kills[k], self.deaths[k], self.casts[k], self.ultimates[k], self.damage[k], self.raw_damage[k],
                    self.blocked_damage[k], self.received_damage[k]] for k in self.dist.keys()}

    def shoot(self, unit):
        self.shoots[unit.team] += 1
        unit.stats.shoots += 1

    def hit(self, unit_from, unit_to):
        self.hits[unit_from.team] += 1
        unit_from.stats.hits += 1
        self.received_hits[unit_to.team] += 1
        unit_to.stats.received_hits += 1

    def move(self, unit, dist):
        self.dist[unit.team] += dist
        unit.stats.dist += dist
        if unit.canfly:
            self.flydist[unit.team] += dist
            unit.stats.flydist += dist

    def jump(self, unit):
        self.jumps[unit.team] += 1
        unit.stats.jumps += 1

    def dmg(self, unit_from, unit_to, value, raw_value):
        self.damage[unit_from.team] += value
        unit_from.stats.damage += value
        self.raw_damage[unit_from.team] += raw_value
        unit_from.stats.raw_damage += raw_value
        self.received_damage[unit_to.team] += value
        unit_to.stats.received_damage += value
        self.blocked_damage[unit_to.team] += raw_value - value
        unit_to.stats.blocked_damage += raw_value - value

    def dead(self, unit_from, unit_to):
        self.kills[unit_from.team] += 1
        unit_from.stats.kills += 1
        self.deaths[unit_to.team] += 1
        unit_to.stats.deaths += 1

    def cast(self, unit, ability):
        self.casts[unit.team] += 1
        unit.stats.casts += 1
        if ability.ultimate:
            self.ultimates[unit.team] += 1
            unit.stats.ultimates += 1


class Projectile:
    anims = {}

    def __init__(self, caster, ability, spawn_point, fspeed, tex, **kwargs):
        self.caster = caster
        self.ability = ability
        self.level = self.caster.level
        self.units = self.caster.units
        self.spawn_point = spawn_point
        self.pos = spawn_point()
        self.distance = 0
        self.speed = fspeed
        self.accel = kwargs['accel'] if 'accel' in kwargs else Vector(0, GRAVITY)
        self.tex = pygame.image.load(tex).convert_alpha()
        self.ticks = 0
        self.collisions = []
        self.collision_cd = kwargs['collision_cd'] if 'collision_cd' in kwargs else FPS
        self.destroyed = False
        self.stopped = False
        if 'size' in kwargs:
            self.size = kwargs['size']*TILE_SIZE
            self.size.toint()
            self.tex = pygame.transform.scale(self.tex, self.size.cort())
        else:
            self.size = Vector(self.tex.get_width(), self.tex.get_height())
        self.duration = kwargs['duration'] if 'duration' in kwargs else 0
        self.baseduration = self.duration
        self.stopbyUnitCollisions = kwargs['stopbyUnitCollisions'] if 'stopbyUnitCollisions' in kwargs else 0
        self.stopbyMapCollisions = kwargs['stopbyMapCollisions'] if 'stopbyMapCollisions' in kwargs else 0
        self.destroybyUnitCollisions = kwargs['destroybyUnitCollisions'] if 'destroybyUnitCollisions' in kwargs else 0
        self.destroybyMapCollisions = kwargs['destroybyMapCollisions'] if 'destroybyMapCollisions' in kwargs else 0
        self.ricochetbyUnitCollisions = kwargs['ricochetbyUnitCollisions'] if 'ricochetbyUnitCollisions' in kwargs else 0
        self.ricochetbyMapCollisions = kwargs['ricochetbyMapCollisions'] if 'ricochetbyMapCollisions' in kwargs else 0

        self.destroyAnimation = []
        if 'destroyAnimation' in kwargs:
            if kwargs['destroyAnimation'] not in Projectile.anims:
                Projectile.anims[kwargs['destroyAnimation']] = load_proj_anim(kwargs['destroyAnimation'], caster.texture_folder)
            self.destroyAnimation = Projectile.anims[kwargs['destroyAnimation']]

    def animate(self, sc):
        if self.destroyed is False:
            tex = self.tex
            if not self.stopped:
                oldpos = self.pos
                self.speed += self.accel
                self.pos += self.speed
                dv = self.pos - oldpos
                self.distance += dv.getlen()
                if self.speed.x or self.speed.y:
                    ang = math.asin(self.speed.y / self.speed.getlen())
                    ang = math.pi - ang if self.speed.x < 0 else ang
                    ang = ang/math.pi*180
                    tex = pygame.transform.rotate(self.tex, ang)
            tex = pygame.transform.scale(tex, (int(tex.get_width() * self.level.camera_scale), int(tex.get_height() * self.level.camera_scale)))
            sc.blit(tex, (self.pos.x*self.level.tile_size+self.level.mp[0]-tex.get_width()//2, self.pos.y*self.level.tile_size+self.level.mp[1]-tex.get_height()//2))
            self.collide(tex)
            self.ticks += 1
            if self.duration > 0 and self.ticks > self.duration * FPS:
                self.destroyed = True
        else:
            if self.destroyed is True:
                self.destroyed = -1
                self.ability.onProjectileDestroy(self)
            self.destroyed += 1
            if self.destroyed >= len(self.destroyAnimation):
                return False
            if not self.stopped:
                oldpos = self.pos
                self.speed += self.accel
                self.pos += self.speed
                dv = self.pos - oldpos
                self.distance += dv.getlen()
            tex = self.destroyAnimation[self.destroyed]
            tex = pygame.transform.scale(tex, self.size.cort())
            self.collide(tex)
            self.ticks += 1
            tex = pygame.transform.scale(tex, (int(tex.get_width() * self.level.camera_scale), int(tex.get_height() * self.level.camera_scale)))
            sc.blit(tex, (self.pos.x * self.level.tile_size + self.level.mp[0] - tex.get_width() // 2, self.pos.y * self.level.tile_size + self.level.mp[1] - tex.get_height() // 2))

    def collide(self, tex):
        box = (self.pos.x-tex.get_width()/4/TILE_SIZE, self.pos.x+tex.get_width()/4/TILE_SIZE, self.pos.y-tex.get_height()/4/TILE_SIZE, self.pos.y+tex.get_height()/4/TILE_SIZE)
        # left right top bottom
        if box[0] < 0 or box[1] >= self.level.size.x or box[2] < 0 or box[3] >= self.level.size.y:
            if self.destroyed is False:
                self.destroyed = True
            self.stopped = True
            return
        if self.destroyed is False:
            for i in self.units:
                if box[0] < i.cords.x+i.size.x/2 and box[1] > i.cords.x-i.size.x/2 and box[2] < i.cords.y and box[3] > i.cords.y-i.size.y:
                    f = True
                    for u, t in self.collisions:
                        if self.ticks - t < self.collision_cd and u == i:
                            f = False
                            break
                    if not f:
                        continue
                    unitcoll = self.ability.onProjectileHit(self, i)
                    if unitcoll:
                        self.collisions.append((i, self.ticks))
                        if self.stopbyUnitCollisions and len(self.collisions) >= self.stopbyUnitCollisions:
                            self.stopped = True
                        if self.ricochetbyUnitCollisions and len(self.collisions) % self.ricochetbyUnitCollisions == 0:
                            self.ricochetbyUnitCollisions -= 1
                            self.speed = Vector(-self.speed.x, -self.speed.y)
                        if self.destroyed is False and self.destroybyUnitCollisions and len(self.collisions) >= self.destroybyUnitCollisions:
                            self.destroyed = True
                            break
        mapcollision = False
        if not self.level.tilemap[int(box[0])][int(box[2])] == 0:
            mapcollision = (int(box[0]), int(box[2]))
        if not self.level.tilemap[int(box[1])][int(box[2])] == 0:
            mapcollision = (int(box[1]), int(box[2]))
        if not self.level.tilemap[int(box[0])][int(box[3])] == 0:
            mapcollision = (int(box[0]), int(box[3]))
        if not self.level.tilemap[int(box[1])][int(box[3])] == 0:
            mapcollision = (int(box[1]), int(box[3]))
        if not mapcollision is False:
            self.ability.onProjectileCollide(self, mapcollision)
            if self.destroyed is False and self.destroybyMapCollisions:
                self.destroybyMapCollisions -= 1
                if self.destroybyMapCollisions == 0:
                    self.destroyed = True
            if self.stopbyMapCollisions:
                self.stopbyMapCollisions -= 1
                if self.stopbyMapCollisions == 0:
                    self.stopped = True
            if self.ricochetbyMapCollisions:
                self.ricochetbyMapCollisions -= 1
                self.speed = Vector(-self.speed.x, -self.speed.y)